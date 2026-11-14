"""Render actual registered candidate cycles and report head registration.

This is an authoring review of the real native frame rectangles, scales and
origins, not a gameplay unit test or an art acceptance by itself.
"""
from pathlib import Path
import importlib.util
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent/'local-qwen21-unified-v3'))
import prepare
import appearance

ROOT = HERE.parents[3]
CURRENT = ROOT/'src/cocos/assets/resources/flat2d/characters/raphael'
STAGE = HERE/'candidate-runtime'
BASE = json.loads((HERE/'baseline-manifest.json').read_text('utf-8'))
M = json.loads((STAGE/'manifest.json').read_text('utf-8'))
FRAMES = prepare.inventory(M)
OLD = prepare.inventory(BASE)
SHEETS = {}
FONT = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 14)


def canvas(action, direction, phase=0, old=False):
    frames = OLD if old else FRAMES
    record = prepare.find(frames, action, direction, phase)
    path = CURRENT/record['image'] if old or not (STAGE/record['image']).exists() else STAGE/record['image']
    key = str(path)
    if key not in SHEETS:
        SHEETS[key] = Image.open(path).convert('RGBA')
    return prepare.canvas(record, {record['image']:SHEETS[key]}), record


def main():
    folder = HERE/'review'
    folder.mkdir(exist_ok=True)
    metrics = []
    for weapon in ['W01','W02','L01','W07','W08','L02','W11']:
        for carry in ['explore', 'held']:
            idle = 'explore_idle_'+weapon if carry == 'explore' else 'idle_'+weapon
            walk = 'explore_walk_'+weapon if carry == 'explore' else 'walk_'+weapon
            run = 'explore_run_'+weapon if carry == 'explore' else 'run_'+weapon
            columns = [(idle,0)]+[(walk,i) for i in range(4)]+[(run,i) for i in range(8)]
            board = Image.new('RGB', (13*144,4*238), '#22211f')
            draw = ImageDraw.Draw(board)
            for row, direction in enumerate(M['directions']):
                for col, (action,phase) in enumerate(columns):
                    image, record = canvas(action,direction,phase)
                    thumb=image.resize((144,216),Image.Resampling.LANCZOS)
                    board.paste(thumb,(col*144,row*238+20),thumb)
                    draw.line((col*144,row*238+220,(col+1)*144,row*238+220),fill='#508e8e')
                    draw.text((col*144+2,row*238+1),f'{direction} {"idle" if col==0 else "walk" if col<5 else "run"}{phase}',font=FONT,fill='white')
                for action in [walk,run]:
                    before, after = [], []
                    for phase in range(M['actions'][action]['frames']):
                        im,r=canvas(action,direction,phase)
                        old,oldr=canvas(action,direction,phase,True)
                        after.append(appearance.hair(im,r)[0]['center'])
                        before.append(appearance.hair(old,oldr)[0]['center'])
                    metrics.append(dict(action=action,direction=direction,
                        beforeHeadRangePixels400=np.ptp(before,axis=0).tolist(),
                        afterHeadRangePixels400=np.ptp(after,axis=0).tolist(),
                        afterHeadMeanPixels400=np.mean(after,axis=0).tolist()))
            board.save(folder/f'{weapon}-{carry}.jpg',quality=94)
            print('Rendered',weapon,carry,flush=True)
    (HERE/'head-registration.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    print('Head range (400px per metre):',np.max([r['afterHeadRangePixels400'] for r in metrics],axis=0).tolist(),flush=True)


if __name__ == '__main__':
    main()
