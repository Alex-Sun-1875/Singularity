"""Read-only runtime geometry audit and scale-consistent local Klein inputs.

Only writes beside this script. All source and production PNGs remain untouched.
Uses the installed Pillow/NumPy stack; no network, model calls or new dependencies.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
ACTOR = ROOT / "src/cocos/assets/resources/flat2d/characters/raphael"
MANIFEST = ACTOR / "manifest.json"
M = json.loads(MANIFEST.read_text(encoding="utf-8"))
DIRECTIONS = M["directions"]
PPW = 400.0
CANVAS = (512, 768)
ANCHOR = (256, 712)
BACKGROUND = (228, 228, 228)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def bbox(mask):
    y, x = np.nonzero(mask)
    return None if not len(x) else [int(x.min()), int(y.min()), int(x.max()) + 1, int(y.max()) + 1]


def rounded(v):
    return round(float(v), 7)


def row_runs(row):
    a = np.r_[False, row, False].astype(np.int8)
    d = np.diff(a)
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


def metrics(im, origin, upp):
    a = np.asarray(im)
    mask = a[:, :, 3] >= 16
    b = bbox(mask)
    x0, y0, x1, y1 = b
    ox, oy = origin
    h = y1 - y0
    span = max(1, oy - y0)
    yy, xx = np.indices(mask.shape)
    # This rejects the carried sword extent by restricting to the pelvis axis.
    # It is still a silhouette proxy, not an anatomical landmark detector.
    centre = np.abs(xx - ox) < .13 / upp
    crown = bbox(mask & centre & (yy < y0 + .22 * span))
    cy = crown[1] if crown else y0
    candidates = []
    xr0 = max(0, int(ox - .26 / upp))
    xr1 = min(im.width, int(ox + .26 / upp) + 1)
    for y in range(int(y0 + .48 * span), min(im.height, int(y0 + .88 * span))):
        runs = [(l + xr0, r + xr0) for l, r in row_runs(mask[y, xr0:xr1]) if r - l >= 3]
        gaps = [(r, l2) for (l, r), (l2, r2) in zip(runs, runs[1:])
                if l2-r >= 2 and abs((r+l2)/2-ox)*upp <= .14]
        if gaps:
            candidates.append(y)
    split = next((y for y in candidates if y+1 in candidates and y+2 in candidates), None)
    rgb = a[:, :, :3].astype(float)
    hi = rgb.max(axis=2)
    lo = rgb.min(axis=2)
    lum = rgb @ np.array([.2126, .7152, .0722])
    silver = (mask & (a[:, :, 3] >= 128) & (lo > 95) & (hi-lo < 45)
              & (yy < y0 + .18*span) & (np.abs(xx-ox)*upp < .33))
    silver_rows = np.flatnonzero(silver.sum(axis=1) >= max(3, .015/upp))
    hair_y = int(silver_rows[0]) if len(silver_rows) else None
    chest = (mask & (yy >= cy + .21 * span) & (yy < cy + .43 * span)
             & (np.abs(xx-ox)*upp < .105) & (hi-lo < 55)
             & (rgb[:,:,2] >= .88*rgb[:,:,0]) & (lum > 30) & (lum < 195))
    chest_values = rgb[chest]
    lower = mask & (yy >= cy + .5*span)
    lower_y, lower_x = np.nonzero(lower)
    result = {
        "alpha16BoundsLocalXYXY": b,
        "alphaAnyBoundsLocalXYXY": bbox(a[:, :, 3] > 0),
        "alpha16BBoxWorldHeight": rounded(h*upp),
        "alpha16BBoxWorldWidth": rounded((x1-x0)*upp),
        "alphaTopAboveAnchorWorld": rounded((oy-y0)*upp),
        "centralAxisCrownTopAboveAnchorWorld": rounded((oy-cy)*upp),
        "brightNeutralHairTopLocalYProxy": hair_y,
        "brightNeutralHairTopAboveAnchorWorldProxy": None if hair_y is None else rounded((oy-hair_y)*upp),
        "lowestAlphaAboveAnchorWorld": rounded((oy-y1)*upp),
        "footAnchorLocalXY": list(origin),
        "silhouetteLegGapOnsetLocalY": split,
        "legGapToLowestAlphaWorldProxy": None if split is None else rounded((y1-split)*upp),
        "legGapToLowestAlphaOverCrownToAnchorProxy": None if split is None else rounded((y1-split)/span),
        "lowerHalfSilhouetteVerticalStdWorldProxy": rounded(np.std(lower_y)*upp),
        "lowerHalfSilhouetteHorizontalStdWorldProxy": rounded(np.std(lower_x)*upp),
        "chestCoolNeutralPixelCountProxy": len(chest_values),
        "chestCoolNeutralMedianRGBProxy": None if not len(chest_values) else np.median(chest_values,axis=0).astype(int).tolist(),
        "chestCoolNeutralMedianLumaProxy": None if not len(chest_values) else rounded(np.median(chest_values @ np.array([.2126,.7152,.0722]))),
    }
    return result


images = {}
all_metrics = []
inputs = []
snapshot = {str(MANIFEST): sha(MANIFEST)}
source_records = {}
action_keys = ["explore_idle_W01", "explore_walk_W01", "explore_run_W01", "idle_W01", "walk_W01", "run_W01"]
for action_key in action_keys:
    action = M["actions"][action_key]
    family = "explore" if action_key.startswith("explore_") else "held"
    state = action_key.split("_")[-2]
    count = len(action.get("frameIndices", [])) or action.get("frames", 1)
    upp = action.get("worldUnitsPerPixel", M["camera"]["worldUnitsPerPixel"])
    for di, direction in enumerate(DIRECTIONS):
        for ordinal in range(count):
            name = action.get("frameImages", [action["image"]]*count)[ordinal]
            p = ACTOR / name
            if name not in images:
                images[name] = Image.open(p).convert("RGBA")
                snapshot[str(p)] = sha(p)
                source_records[name] = {"runtimePath":str(p), "runtimeSHA256":snapshot[str(p)], "size":list(images[name].size)}
                source = next((Path(q) for q in action.get("sourcePNGs",[]) if Path(q).name == p.name), None)
                if source:
                    snapshot[str(source)] = sha(source)
                    source_records[name].update({"sourceArtPath":str(source),"sourceArtSHA256":snapshot[str(source)],"sourceMatchesRuntime":snapshot[str(source)]==snapshot[str(p)]})
            columns = action.get("columns", M.get("columns", 1))
            column = action.get("frameIndices", list(range(count)))[ordinal]
            index = action.get("directionFrameIndices", [])[di] if "directionFrameIndices" in action else di*columns+column
            rects = action.get("frameRectsByImage", {}).get(name, action.get("perFrameRects"))
            rect = rects[index]
            x,y,w,h = rect
            crop = images[name].crop((x,y,x+w,y+h))
            origins = action.get("perFrameOrigins", M.get("perFrameOrigins"))
            origin = origins[di if "directionFrameIndices" in action else index] if isinstance(origins,list) else origins[direction][ordinal]
            met = metrics(crop, origin, upp)
            row = {"action":action_key,"family":family,"state":state,"direction":direction,"phase":ordinal,
                   "image":name,"sourceSHA256":snapshot[str(p)],"worldUnitsPerPixel":upp,
                   "runtimeFrameIndex":index,"cropRectAbsoluteXYWH":rect,
                   "footAnchorAbsoluteXY":[x+origin[0],y+origin[1]],**met}
            all_metrics.append(row)
            if state not in ("idle", "run") or direction == "left" or ordinal not in (0,2,4):
                continue
            label = {"down":"front","up":"back"}.get(direction,direction)
            stem = f"{family}-{state}-{label}-p{ordinal}"
            native_path = HERE/f"{stem}-native.png"
            original_alpha_path = HERE/f"{stem}-original-alpha.png"
            crop.save(native_path)
            crop.getchannel("A").save(original_alpha_path)
            scale = upp * PPW
            inverse = (1/scale,0,origin[0]-ANCHOR[0]/scale,0,1/scale,origin[1]-ANCHOR[1]/scale)
            canvas_rgba = crop.transform(CANVAS,Image.Transform.AFFINE,inverse,Image.Resampling.BICUBIC)
            alpha_path = HERE/f"{stem}-alpha.png"
            canvas_rgba.getchannel("A").save(alpha_path)
            rgb_canvas = Image.new("RGB",CANVAS,BACKGROUND)
            rgb_canvas.paste(canvas_rgba,(0,0),canvas_rgba.getchannel("A"))
            input_path = HERE/f"{stem}.png"
            rgb_canvas.save(input_path)
            cb = bbox(np.asarray(canvas_rgba)[:,:,3] >= 16)
            entry={**row,"inputPath":str(input_path),"inputSHA256":sha(input_path),
                   "nativeCropPath":str(native_path),"nativeCropSHA256":sha(native_path),
                   "originalAlphaPath":str(original_alpha_path),"originalAlphaSHA256":sha(original_alpha_path),
                   "canvasAlphaPath":str(alpha_path),"canvasAlphaSHA256":sha(alpha_path),
                   "originalSourceMode":images[name].mode,"nativeCropSize":[w,h],
                   "canvasSize":list(CANVAS),"canvasRGBBackground":list(BACKGROUND),
                   "pixelsPerWorldUnit":PPW,"uniformScaleNativeToCanvas":scale,
                   "canvasAnchorXY":list(ANCHOR),"canvasAlpha16BBoxXYXY":cb,
                   "nativeToCanvasAffine":[scale,0,ANCHOR[0]-origin[0]*scale,0,scale,ANCHOR[1]-origin[1]*scale],
                   "canvasAlpha16BoundsTouchCanvas":any([cb[0]==0,cb[1]==0,cb[2]==CANVAS[0],cb[3]==CANVAS[1]])}
            inputs.append(entry)

summary=[]
for key in action_keys:
    for direction in DIRECTIONS:
        rows=[r for r in all_metrics if r['action']==key and r['direction']==direction]
        heights=np.array([r['alpha16BBoxWorldHeight'] for r in rows])
        crowns=np.array([r['centralAxisCrownTopAboveAnchorWorld'] for r in rows])
        hair=[r['brightNeutralHairTopAboveAnchorWorldProxy'] for r in rows if r['brightNeutralHairTopAboveAnchorWorldProxy'] is not None]
        legs=[r['legGapToLowestAlphaWorldProxy'] for r in rows if r['legGapToLowestAlphaWorldProxy'] is not None]
        summary.append({"action":key,"direction":direction,"worldUnitsPerPixel":rows[0]['worldUnitsPerPixel'],
                        "bboxHeightMedianWorld":rounded(np.median(heights)),"bboxHeightRangeWorld":[rounded(heights.min()),rounded(heights.max())],
                        "centralCrownAboveAnchorMedianWorld":rounded(np.median(crowns)),"centralCrownAboveAnchorRangeWorld":[rounded(crowns.min()),rounded(crowns.max())],
                        "brightNeutralHairTopAboveAnchorMedianWorldProxy":None if not hair else rounded(np.median(hair)),
                        "legGapToLowestAlphaMedianWorldProxy":None if not legs else rounded(np.median(legs)),
                        "phaseCount":len(rows)})

font_path=Path('C:/Windows/Fonts/arial.ttf')
font=ImageFont.truetype(str(font_path),12) if font_path.exists() else ImageFont.load_default()
thumb=(192,288)
overview=Image.new('RGB',(thumb[0]*6,(thumb[1]+26)*3),(244,244,244))
draw=ImageDraw.Draw(overview)
for e in inputs:
    if e['phase'] == 2:
        continue
    col=(0 if e['family']=='explore' else 3)+['down','right','up'].index(e['direction'])
    row=0 if e['state']=='idle' else (1 if e['phase']==0 else 2)
    x,y=col*thumb[0],row*(thumb[1]+26)
    draw.text((x+4,y+3),f"{e['family']} {e['state']} {e['direction']} p{e['phase']}",font=font,fill=(30,30,30))
    tile=Image.open(e['inputPath']).resize(thumb,Image.Resampling.LANCZOS)
    overlay=ImageDraw.Draw(tile)
    ay=round(ANCHOR[1]*thumb[1]/CANVAS[1]);ax=round(ANCHOR[0]*thumb[0]/CANVAS[0])
    overlay.line((0,ay,thumb[0],ay),fill=(200,194,194),width=1)
    overlay.line((ax-4,ay,ax+4,ay),fill=(215,55,60),width=1)
    overlay.line((ax,ay-4,ax,ay+4),fill=(215,55,60),width=1)
    overview.paste(tile,(x,y+26))
overview.save(HERE/'overview.jpg',quality=79,optimize=True)
overview_p2=Image.new('RGB',(thumb[0]*6,thumb[1]+26),(244,244,244))
draw_p2=ImageDraw.Draw(overview_p2)
for e in [entry for entry in inputs if entry['phase']==2]:
    col=(0 if e['family']=='explore' else 3)+['down','right','up'].index(e['direction'])
    x=col*thumb[0]
    draw_p2.text((x+4,3),f"{e['family']} run {e['direction']} p2",font=font,fill=(30,30,30))
    tile=Image.open(e['inputPath']).resize(thumb,Image.Resampling.LANCZOS)
    overview_p2.paste(tile,(x,26))
overview_p2.save(HERE/'overview-run-p2.jpg',quality=79,optimize=True)

report={"status":"read-only audit and local model input preparation; no generated outputs or production edits",
        "runtimeManifestPath":str(MANIFEST),"runtimeManifestSHA256":snapshot[str(MANIFEST)],
        "runtimeGeometryAuthority":"FlatActors.ts frame() and show(): rect pixels multiplied by a single action UPP; per-direction/per-phase foot origin offsets; no per-direction scaling.",
        "canvasPolicy":{"size":CANVAS,"backgroundRGB":BACKGROUND,"pixelsPerWorldUnit":PPW,"footAnchorXY":ANCHOR,
                         "standingTargetWorldHeight":1.556,"standingTargetCanvasPixels":622.4,
                         "policy":"Preserve actual installed world proportions across every image; single native-to-canvas scale = action UPP *400, never fit individual alpha bbox."},
        "proxyLimitations":["Alpha bbox includes weapons, pouches and bent limbs; crown axis may miss a leaning head.",
                            "Leg gap onset is a silhouette proxy constrained to48-88% crown-to-anchor, three sustained rows, not anatomical crotch/knee detection; folded/overlapped legs can hide it.",
                            "Lower-half silhouette moments measure projected spread/height, not actual thigh/shin length.",
                            "Chest median uses cool neutral pixels in a central normalized chest ROI; shadows, leather occlusion and pose affect it; no automatic artistic acceptance implied."],
        "sources":source_records,"inputs":inputs,"directionSummaries":summary,"allFrameMeasurements":all_metrics,
        "sourceSnapshotsUnchangedAfterPreparation":all(sha(p)==s for p,s in snapshot.items()),
        "sourceSHA256s":snapshot,"overviewPath":str(HERE/'overview.jpg'),"phase2OverviewPath":str(HERE/'overview-run-p2.jpg')}
(HERE/'inputs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({"manifestSHA256":report['runtimeManifestSHA256'],"inputCount":len(inputs),"frameCount":len(all_metrics),
                  "overviewBytes":(HERE/'overview.jpg').stat().st_size,"sourceSnapshotsUnchanged":report['sourceSnapshotsUnchangedAfterPreparation'],
                  "directionSummaries":summary},ensure_ascii=False,indent=2))
