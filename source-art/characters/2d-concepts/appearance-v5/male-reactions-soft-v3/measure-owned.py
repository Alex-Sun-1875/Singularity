"""Reuse existing read-only alpha measurement for the revised head artwork."""
import ast
import copy
import hashlib
import json
import statistics
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
tree = ast.parse((HERE.parents[1]/'hero-v4-reactions/measure_metadata.py').read_text(encoding='utf-8'))
tree.body = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
exec(compile(tree, 'existing_measurement_helpers', 'exec'), globals())
old = json.loads((HERE.parent/'male-reactions/owned-actions.json').read_text(encoding='utf-8'))
actions, sheets = {}, {}
for kind, names in [('dodge', ['dodge']), ('hit-death', ['hit', 'death']), ('spell-interact', ['spell', 'interact'])]:
    path = HERE/f'hero-v4-{kind}-readable.png'
    im = Image.open(path)
    alpha = im.getchannel('A')
    w, h = im.size
    cw, ch = w/4, h/4
    mask = alpha.point(lambda v: 255 if v >= 16 else 0)
    hit = kind == 'hit-death'
    comps = components(mask, 0, h) if hit else []
    groups = [sorted([c for c in comps if min(3, int((c['bounds'][1]+c['bounds'][3])/2/ch)) == row], key=lambda c:c['bounds'][0]) for row in range(4)] if hit else []
    if hit:
        assert len(comps) == 16 and all(len(g) == 4 for g in groups), 'Need16 independent reaction bodies'
    rects, origins, bounds, frames = [], [], [], []
    for row in range(4):
        for col in range(4):
            cell = tuple(round(v) for v in (col*cw, row*ch, (col+1)*cw, (row+1)*ch))
            if hit:
                x0,y0,x1,y1 = groups[row][col]['bounds']
                l,t,r,b = max(0,x0-2),max(0,y0-2),min(w,x1+2),min(h,y1+2)
            else:
                bb = mask.crop(cell).getbbox()
                assert bb
                l,t,r,b = max(cell[0],cell[0]+bb[0]-2),max(cell[1],cell[1]+bb[1]-2),min(cell[2],cell[0]+bb[2]+2),min(cell[3],cell[1]+bb[3]+2)
            local = alpha.crop((l,t,r,b))
            core = local.point(lambda v:255 if v >=128 else 0).getbbox()
            ab = local.point(lambda v:255 if v >=16 else 0).getbbox()
            depth = max(5, round((core[3]-core[1])*.25)) if hit and col>=2 else 5
            supports = [(x0,x1,y) for y in range(max(t,t+core[3]-depth),t+core[3]) for x0,x1 in spans(alpha,y,l,r)]
            assert supports
            sx0,sx1,sy = min(v[0] for v in supports),max(v[1] for v in supports),max(v[2] for v in supports)
            origin = [(sx0+sx1)/2-l, sy-t]
            foreign = sum(1 for rr,g in enumerate(groups) for cc,c in enumerate(g) if (rr,cc)!=(row,col) for x,y in c['pixels'] if l<=x<r and t<=y<b) if hit else 0
            assert not foreign, 'Reaction crop intersects another figure'
            rects.append([l,t,r-l,b-t]);origins.append(origin);bounds.append(list(ab))
            frames.append({'index':row*4+col,'rect':rects[-1],'origin':origin,'alphaBounds':list(ab),'headToSupportPixels':origin[1]-core[1],'foreignBodyPixels':foreign})
    neutral = [0,4,8,12] if hit else [3,7,11,15] if kind=='spell-interact' else [0,3]
    height = statistics.median(frames[i]['headToSupportPixels'] for i in neutral)
    upp = 1.5562753036437247/height
    for name in names:
        action = copy.deepcopy(old['actions'][name])
        action.update(image='hero-v6/'+path.name,columns=4,frameWidth=cw,frameHeight=ch,perFrameRects=rects,perFrameOrigins=origins,alphaBounds=bounds,worldUnitsPerPixel=upp)
        actions[name] = action
    sheets[kind] = {'source':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':[w,h],'alphaExtrema':alpha.getextrema(),'canonicalHeightPixels':height,'worldUnitsPerPixel':upp,'frames':frames}
out = {'version':'appearance-v5-soft-geralt-v3-reactions','actions':actions,'sheets':sheets,'pixelEdits':False,'gameRulesChanged':False,'scalePolicy':'One fixed UPP for each source from neutral standing references; no normalization of crouching/falling phases.'}
(HERE/'owned-actions.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'actions':len(actions),'sheets':{k:{'height':v['canonicalHeightPixels'],'upp':v['worldUnitsPerPixel']} for k,v in sheets.items()}}))
