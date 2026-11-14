"""Adapt the approved body proportion to each exploration run phase locally.

Reuses the existing SciPy premultiplied RGBA resampler.  Each frame keeps its
own pose, arms, hands, boots, sword corridor and world-space foot anchor.  This
is deterministic adaptation of the reviewed Qwen keyframes, not fresh model
inference.  Importing or applying this module does not write original copies.
"""
from pathlib import Path
import importlib.util
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
spec = importlib.util.spec_from_file_location("approved_body_guide", V2 / "body/prepare-body.py")
guide = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guide)
SIZE = (512, 768)
YY, XX = np.indices((768, 512), dtype=float)

# Per-pose registration from the existing native frames, in the established
# 400px/world canvas.  These are translations, never independent bbox fits.
# Hair registration uses the main silver crown component, not the sword hilt.
HEAD_OFFSETS = {
    "down": [(0, 0), (5, 12), (5, 5), (8, -10), (-12, -21), (-8, -8), (-1, -12), (2, -20)],
    "up": [(0, 0), (2, 1), (4, -14), (1, -17), (5, -16), (7, -16), (7, -23), (4, -32)],
}
WAIST_OFFSETS = {"down": [0, 8, -15, -30, -22, -12, -28, -42],
                 "up": [0, 4, -20, -27, -7, -5, -21, -33]}

# Two actual leather boot envelopes per phase. The original alpha, including
# soles and fingers, is retained within these independent foreground layers.
# Order is screen-left then screen-right; no mirrored pose is substituted.
BOOT_BOXES = {
    "down": [
        [(185,547,245,635),(226,614,301,726)],
        [(189,563,245,667),(231,607,303,727)],
        [(165,532,225,630),(213,575,291,700)],
        [(168,493,228,598),(233,549,308,666)],
        [(214,589,296,721),(269,527,340,620)],
        [(207,586,297,725),(265,533,338,620)],
        [(220,567,307,692),(272,489,350,636)],
        [(209,540,282,655),(284,482,351,592)],
    ],
    "up": [
        [(202,624,273,725),(263,535,332,678)],
        [(210,623,274,725),(263,563,330,726)],
        [(201,500,271,632),(284,568,353,721)],
        [(204,465,274,599),(290,511,360,658)],
        [(195,526,268,674),(254,615,321,722)],
        [(201,566,273,722),(257,615,326,721)],
        [(173,562,247,712),(242,491,316,625)],
        [(164,509,246,656),(253,463,325,586)],
    ],
}


def polygon(points):
    mask = Image.new("L", SIZE)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return np.asarray(mask) > 0


def boxes_mask(boxes):
    mask = Image.new("L", SIZE)
    draw = ImageDraw.Draw(mask)
    for x0, y0, x1, y1 in boxes:
        draw.rectangle((x0, y0, x1-1, y1-1), fill=255)
    return np.asarray(mask) > 0


def translate_mask(mask, dx, dy):
    source = Image.fromarray(np.uint8(mask) * 255)
    output = Image.new("L", SIZE)
    output.paste(source, (int(dx), int(dy)))
    return np.asarray(output) > 0


def shifted_polygon(poly, dx, dy, mirror_axis=None):
    return [(int((2*mirror_axis-x if mirror_axis is not None else x)+dx), int(y+dy)) for x,y in poly]


def phase_arms(direction, phase):
    key = "front" if direction == "down" else "back"
    arms = guide.SPECS[key]["arms"]
    dx, dy = HEAD_OFFSETS[direction][phase]
    # Forearms follow their actual swing; shoulder bob alone is insufficient.
    if direction == "down":
        offsets = [[(0,0),(0,0)],[(4,10),(4,3)],[(2,-8),(2,-27)],[(8,-25),(8,-58)],
                   [(-2,-9),(-2,-16)],[(2,-2),(2,-6)],[(5,-20),(5,-32)],[(7,-39),(7,-57)]]
        axis = 260 if phase >= 4 else None
    else:
        offsets = [[(0,0),(0,0)],[(2,2),(2,1)],[(4,-40),(4,-14)],[(1,-58),(1,-17)],
                   [(5,-12),(5,-5)],[(9,-12),(9,-5)],[(10,-34),(10,-23)],[(8,-50),(8,-32)]]
        axis = 250 if phase >= 4 else None
    result = np.zeros((768,512), bool)
    for poly, (ox,oy) in zip(arms, offsets[phase]):
        result |= polygon(shifted_polygon(poly, ox, oy, axis))
    # A 3px guard covers native bicubic AA and small sleeve silhouette changes.
    result = ndimage.binary_dilation(result, iterations=3)
    if direction == "down" and phase == 1:
        # This phase's extended right forearm clears the moving coat corner.
        # A p0-derived generous lower-left arm corner would retain a 2px strip
        # of the old hem as a disconnected fragment after the waist lift.
        result[(XX < 344) & (YY > 413)] = False
    return result


def phase_hands(direction, phase):
    # Tight enough for sword intersection checks; generous enough to protect
    # complete original cuffs and all skin, not just a hue-selected finger core.
    if direction == "down":
        boxes = [
            [(204,278,288,358),(331,364,390,435)],
            [(208,289,293,370),(344,366,392,436)],
            [(211,263,296,347),(335,330,395,402)],
            [(221,242,309,329),(344,298,406,371)],
            [(132,351,204,423),(264,257,348,340)],
            [(137,362,212,434),(271,277,356,357)],
            [(143,327,219,407),(279,253,365,340)],
            [(150,296,226,373),(279,232,371,321)],
        ][phase]
    else:
        boxes = [
            [(129,347,190,423),(329,283,384,343)],
            [(130,349,194,427),(331,284,386,344)],
            [(131,302,198,384),(332,270,391,333)],
            [(128,281,199,367),(331,266,391,331)],
            [(113,268,188,340),(322,338,392,421)],
            [(120,268,195,344),(326,338,398,424)],
            [(122,250,197,328),(328,312,401,400)],
            [(120,231,195,311),(324,291,401,381)],
        ][phase]
    return boxes_mask(boxes), boxes


def weapon_protection(direction, phase):
    dx, dy = HEAD_OFFSETS[direction][phase]
    key = "front" if direction == "down" else "back"
    lines = guide.SPECS[key]["weapon_lines"]
    mask = Image.new("L", SIZE)
    draw = ImageDraw.Draw(mask)
    for points,width in lines:
        draw.line([(x+dx,y+dy) for x,y in points], fill=255, width=width+6, joint="curve")
    return np.asarray(mask) > 0


def replace_head(image, direction, phase):
    """Identical approved standing head, translated with natural phase bob."""
    key = "front" if direction == "down" else "back"
    body_spec = guide.SPECS[key]
    dx, dy = HEAD_OFFSETS[direction][phase]
    reference = Image.open(V2 / f"body/{key}/reference-standing-rgba.png").convert("RGBA")
    source = np.asarray(reference).copy()
    source_mask = polygon(body_spec["source_head"])
    source[~source_mask] = 0
    shifted = Image.new("RGBA", SIZE)
    hx,hy = body_spec["head_shift"]
    shifted.alpha_composite(Image.fromarray(source), (hx+dx,hy+dy))
    new_head = np.asarray(shifted)
    old_head = translate_mask(polygon(body_spec["old_head"]), dx, dy)
    original = np.asarray(image)
    result = original.copy()
    result[old_head] = 0
    result = np.asarray(Image.alpha_composite(Image.fromarray(result), shifted)).copy()

    # Same original-run neck repair as the reviewed keyframes, but the pixels
    # come from this phase's own original, never from a copied p0 torso.
    neck_spec_path = V2 / "body/head-neck-repair.py"
    spec = importlib.util.spec_from_file_location("phase_neck_repair", neck_spec_path)
    neck_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(neck_module)
    ns = neck_module.SPECS[key]
    if key == "front":
        core = (new_head[...,3] > 0) & (YY <= 185+dy)
        layer = original.copy()
    else:
        rgb = new_head[...,:3].astype(int)
        neutral = (rgb.max(-1)-rgb.min(-1)<45)&(rgb.max(-1)>35)
        core = (new_head[...,3]>0)&((YY<=178+dy)|((YY<=183+dy)&neutral))
        moved = Image.new("RGBA", SIZE)
        moved.alpha_composite(image,(0,7))
        moved = np.asarray(moved)
        collar = translate_mask(polygon([(220,175),(274,175),(283,185),(282,203),(272,212),(220,212),(211,201),(212,185)]), dx,dy)
        blend=np.minimum(ndimage.distance_transform_edt(collar)/3,1)
        blend*=np.clip((YY-dy-177)/5,0,1)*np.clip((214+dy-YY)/7,0,1)
        blend*=moved[...,3]/255
        layer=np.uint8(np.clip(np.rint(original*(1-blend[...,None])+moved*blend[...,None]),0,255))
        layer[...,3]=np.maximum(layer[...,3],original[...,3])
    allowed=translate_mask(polygon(ns["polygon"]),dx,dy)
    feather=np.minimum(ndimage.distance_transform_edt(allowed)/2,1)
    feather*=np.clip((YY-dy-ns["start_y"])/(ns["full_y"]-ns["start_y"]),0,1)
    feather*=np.clip((ns["end_y"]+dy-YY)/(ns["end_y"]-ns["fade_y"]),0,1)
    feather[core]=0
    a=feather[...,None]
    result=np.uint8(np.clip(np.rint(result*(1-a)+layer*a),0,255))
    # Preserve hair/face/jaw core exactly, including native alpha.
    result[core]=new_head[core]
    protect=ndimage.binary_dilation(old_head|(new_head[...,3]>0),iterations=4)
    return Image.fromarray(result), protect, {"translation_from_phase0_xy":[dx,dy],
        "standing_head_scale":1,"approved_head_core_exact":bool(np.array_equal(result[core],new_head[core])),
        "neck_pixels_source":"this phase's original running collar, with rear collar translated 7px"}


def apply_body(image, record):
    image = image.convert("RGBA")
    state, direction, phase = record["state"], record["direction"], int(record["phase"])
    if state != "run" or direction not in ("down","up"):
        return image.copy(), {"applied":False,"reason":"only front/rear exploration run body proportions"}
    if image.size != SIZE:
        raise ValueError("Expected 512x768 world-scale canvas")
    original = np.asarray(image).copy()
    dx, dy = HEAD_OFFSETS[direction][phase]
    waist_dy = WAIST_OFFSETS[direction][phase]
    arms = phase_arms(direction,phase)
    hands,hand_boxes=phase_hands(direction,phase)
    boots = boxes_mask(BOOT_BOXES[direction][phase])
    weapon = weapon_protection(direction,phase)
    # Ask the sword adapter for its per-phase registered complete corridor when
    # available; keep the conservative current guard when run independently.
    if direction == "up":
        try:
            import sword_batch
            if hasattr(sword_batch,"weapon_mask"):
                weapon |= np.asarray(sword_batch.weapon_mask(image,record)) > 0
        except ImportError:
            pass
    headbase,headprotect,head_report=replace_head(image,direction,phase)
    hb=np.asarray(headbase).copy()
    fixed=arms|hands|boots|weapon
    hb[fixed]=original[fixed]
    protect=fixed|headprotect|(YY<205+dy)|(YY>=746)

    # A per-phase trunk envelope, plus that frame's own complete trouser
    # silhouette. Arms and leather foreground are excluded independently.
    trunk=polygon([(215+dx,205+dy),(309+dx,205+dy),(323+dx,330+waist_dy),
                   (349+dx,435+waist_dy),(171+dx,435+waist_dy),(203+dx,330+waist_dy)])
    domain=trunk | ((YY>=435+waist_dy)&(YY<730)&(XX>=100)&(XX<410))
    owner=domain&~protect
    cloth=owner&(hb[...,3]>128)
    _,nearest=ndimage.distance_transform_edt(~cloth,return_indices=True)
    # Occluders become a temporary nearest-cloth underlay only inside the
    # central torso/trouser domain, not a shifted silhouette of the arms.
    inferred_source=domain&protect
    underlay=hb.copy()
    underlay[inferred_source]=hb[nearest[0][inferred_source],nearest[1][inferred_source]]

    # Each leg meets its own unmoved boot. A smooth x blend avoids a vertical
    # discontinuity through the crotch while retaining different lift phases.
    boot_boxes=sorted(BOOT_BOXES[direction][phase],key=lambda b:(b[0]+b[2])/2)
    centers=[(b[0]+b[2])/2 for b in boot_boxes]
    midpoint=sum(centers)/2
    mix=np.clip((np.arange(512)-(midpoint-10))/20,0,1)
    ankle=boot_boxes[0][1]*(1-mix)+boot_boxes[1][1]*mix
    start=210+dy
    upper=330+waist_dy
    hem=435+waist_dy
    source_y=np.empty((768,512),float)
    for x in range(512):
        knots=[0,start,upper,hem,float(ankle[x]),768]
        dest=[0,start,upper-22,hem-22,float(ankle[x]),768]
        if not all(knots[i]<knots[i+1] and dest[i]<dest[i+1] for i in range(5)):
            raise ValueError(f"Invalid body mapping {direction} {phase}: {knots}")
        source_y[:,x]=np.interp(np.arange(768),dest,knots)
    warped=guide.remap_rgba(Image.fromarray(underlay),source_y)
    dest_owner=guide.warp(domain.astype(float),source_y,order=0)>.5
    dest_owner &= ~protect
    result=hb.copy()
    result[owner|dest_owner]=0
    result[dest_owner]=warped[dest_owner]
    result[protect]=hb[protect]
    # Register reusable protection metadata in memory only. Caller excludes PIL
    # masks from JSON provenance; no original frame or backup is written.
    record["hands_protection_mask"]=Image.fromarray(np.uint8(hands)*255)
    record["body_arms_protection_mask"]=Image.fromarray(np.uint8(arms)*255)
    record["body_boots_protection_mask"]=Image.fromarray(np.uint8(boots)*255)
    record["body_weapon_protection_mask"]=Image.fromarray(np.uint8(weapon)*255)
    record["body_warp_applied"]=True
    report={"applied":True,"method":"per-phase body-only premultiplied SciPy mapping; approved standing head at 1:1; original running foreground layers",
        "state":state,"direction":direction,"phase":phase,"waist_raise_px":22,
        "head":head_report,"hands_protection_boxes":hand_boxes,"boot_protection_boxes":BOOT_BOXES[direction][phase],
        "phase_waist_offset_from_p0":waist_dy,"fixed_boot_join_y":ankle[[0,511]].tolist(),
        "original_arms_hands_rgba_exact":bool(np.array_equal(original[arms|hands],result[arms|hands])),
        "original_boots_rgba_exact":bool(np.array_equal(original[boots],result[boots])),
        "original_weapon_rgba_exact":bool(np.array_equal(original[weapon],result[weapon])),
        "changed_pixels":int(np.any(result!=original,axis=-1).sum()),
        "foot_anchor_canvas_xy":[256,712],"world_scale_modified":False,
        "new_model_inference":False,"cloud_generation":False,
        "limitation":"Pose-specific deterministic continuation of reviewed Qwen keyframe; other phases are not individually regenerated."}
    return Image.fromarray(result),report


if __name__ == "__main__":
    import runtime_frames
    manifest=runtime_frames.read_manifest()
    board=Image.new("RGB",(1536,768),"#303030")
    draw=ImageDraw.Draw(board)
    reports=[]
    # One necessary small before/after board: eight phase pairs per direction.
    for row,direction in enumerate(("down","up")):
        for phase in range(8):
            im,record=runtime_frames.canvas(manifest,"run",direction,phase)
            out,report=apply_body(im,record)
            reports.append(report)
            a=im.resize((96,144),Image.Resampling.LANCZOS)
            b=out.resize((96,144),Image.Resampling.LANCZOS)
            x=phase*192;y=row*384
            board.paste(a,(x,y+25),a);board.paste(b,(x+96,y+25),b)
            draw.text((x+4,y+4),f"{direction} p{phase} old/new",fill="white")
            # Neck/waist detail uses one low-resolution phase-local crop.
            detail=out.crop((145,165+HEAD_OFFSETS[direction][phase][1],380,450+WAIST_OFFSETS[direction][phase])).resize((172,178))
            bg=Image.new("RGBA",detail.size,"#303030");bg.alpha_composite(detail)
            board.paste(bg.convert("RGB"),(x+10,y+195))
    board.save(HERE/"body-batch-review.jpg",quality=90)
    (HERE/"body-batch-report.json").write_text(json.dumps(reports,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"frames":len(reports),"all_protected":all(r["original_arms_hands_rgba_exact"] and r["original_boots_rgba_exact"] and r["original_weapon_rgba_exact"] for r in reports),"review":str(HERE/"body-batch-review.jpg")},ensure_ascii=False))
