"""Inventory current player action artwork and prepare bounded local references."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ACTOR = ROOT / 'src/cocos/assets/resources/flat2d/characters/raphael'
MANIFEST = ACTOR / 'manifest.json'
DIRECTIONS = ['down', 'right', 'up', 'left']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(manifest):
    frames = {}
    for key, a in manifest['actions'].items():
        for di, direction in enumerate(manifest['directions']):
            for phase in range(a.get('frames', 1)):
                name = a.get('frameImages', [a.get('image', manifest['image'])] * a.get('frames', 1))[phase]
                column = a.get('frameIndices', list(range(a.get('frames', 1))))[phase]
                index = a.get('directionFrameIndices', [])[di] if a.get('directionFrameIndices') else column if a.get('absoluteFrameIndices') else a.get('row', di) * a.get('columns', manifest['columns']) + column
                rects = a.get('frameRectsByImage', {}).get(name.removesuffix('.png'), a.get('perFrameRects'))
                if rects is None:
                    raise ValueError('Missing semantic frame crops: ' + key)
                rect = rects[index]
                origins = a.get('perFrameOrigins', manifest.get('perFrameOrigins'))
                origin = origins[index] if isinstance(origins, list) else origins[direction][phase]
                record = dict(image=name, index=index, rect=rect, origin=origin,
                    absolute_anchor=[rect[0] + origin[0], rect[1] + origin[1]],
                    scale=400 * a.get('worldUnitsPerPixel', manifest['camera']['worldUnitsPerPixel']) * manifest.get('frameScaleFactors', {}).get(name.removesuffix('.png'), [1] * (index+1))[index],
                    direction=direction, di=di, phase=phase, action=key, refs=[])
                physical = (name, index)
                if physical in frames:
                    old = frames[physical]
                    if old['rect'] != rect or old['absolute_anchor'] != record['absolute_anchor'] or old['scale'] != record['scale']:
                        raise ValueError(f'Conflicting physical geometry: {physical}, {key}')
                else:
                    frames[physical] = record
                frames[physical]['refs'].append(dict(action=key, direction=direction, phase=phase))
    return frames


def canvas(record, sheets=None):
    sheet = sheets[record['image']] if sheets is not None else Image.open(ACTOR / record['image']).convert('RGBA')
    x, y, w, h = record['rect']
    crop = sheet.crop((x, y, x+w, y+h))
    s = record['scale']
    shift=record.get('editing_viewport_shift',[0,0])
    tx, ty = 256-record['origin'][0]*s+shift[0], 712-record['origin'][1]*s+shift[1]
    return crop.transform((512, 768), Image.Transform.AFFINE,
        (1/s, 0, -tx/s, 0, 1/s, -ty/s), Image.Resampling.BICUBIC)


def find(frames, action, direction, phase=0):
    return next(r for r in frames.values() if any(v == dict(action=action,direction=direction,phase=phase) for v in r['refs']))


def main():
    m = json.loads(MANIFEST.read_text(encoding='utf-8-sig'))
    frames = inventory(m)
    names = sorted({r['image'] for r in frames.values()})
    sheets = {n: Image.open(ACTOR/n).convert('RGBA') for n in names}
    record = dict(manifestSHA256=digest(MANIFEST), actionCount=len(m['actions']),
        physicalFrameCount=len(frames), images=[dict(image=n,sha256=digest(ACTOR/n),size=list(sheets[n].size),
        metaSHA256=digest(str(ACTOR/n)+'.meta')) for n in names], frames=list(frames.values()),
        authority={'identity':'current explore_idle_W01, matching user image 2',
        'clothing':'current attack_sword_W01, matching user image 1',
        'pose':'each original action phase; keep weapon, hands, support anchors and timing'})
    (HERE/'inventory.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    references=HERE/'references';references.mkdir(exist_ok=True)
    board=Image.new('RGB',(1120,820),'#28282a');d=ImageDraw.Draw(board)
    actions=['explore_idle_W01','idle_W01','attack_sword_W01','explore_run_W01','run_W01','dodge','spell','hit','death','attack_bow_W07']
    for col,action in enumerate(actions):
        for row,direction in enumerate(DIRECTIONS):
            phase=1 if action=='attack_sword_W01' else 0
            r=find(frames,action,direction,phase)
            im=canvas(r,sheets)
            thumb=im.resize((112,168),Image.Resampling.LANCZOS)
            board.paste(thumb,(col*112,row*205+30),thumb)
            d.text((col*112+2,row*205+3),action.replace('_W01','').replace('explore_','e_')[:15],fill='white')
            d.text((col*112+2,row*205+17),direction,fill='white')
    board.save(HERE/'current-action-review-small.jpg',quality=90)
    for direction in DIRECTIONS:
        for role,action,phase in [('identity','explore_idle_W01',0),('clothing','attack_sword_W01',1)]:
            canvas(find(frames,action,direction,phase),sheets).save(references/f'{role}-{direction}.png')
    print(json.dumps({k:record[k] for k in ['actionCount','physicalFrameCount']}|{'images':len(names)}))


if __name__ == '__main__':
    main()
