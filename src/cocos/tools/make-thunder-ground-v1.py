"""Deterministic soft ground haze and broken residual discharge masks.

No model, download, third-party pixels, or new runtime dependency. This follows
the project's existing Pillow mask workflow; the renderer uses Cocos unlit.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import hashlib
import json
import math
import random

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'assets/resources/vfx/production/thunder-ground-v1'
DEST.mkdir(parents=True, exist_ok=True)
SIZE = 256


def edge(x, y):
    radius = math.hypot(x, y)
    t = max(0., min(1., (1. - radius) / .24))
    return t*t*(3.-2.*t)


mist = Image.new('RGBA', (SIZE, SIZE))
for py in range(SIZE):
    y = (py/(SIZE-1)-.5)*2
    for px in range(SIZE):
        x = (px/(SIZE-1)-.5)*2
        lobes = 0.
        for cx, cy, sx, sy, value in [(-.18, -.11, .47, .31, .53),
                                     (.23, .13, .36, .43, .42),
                                     (-.16, .28, .32, .25, .27),
                                     (.06, -.35, .27, .24, .22)]:
            lobes += value*math.exp(-((x-cx)/sx)**2-((y-cy)/sy)**2)
        # Multi-frequency soft density preserves a loose irregular cloud rather
        # than a filled circle, ring, or a preselection glyph.
        density = .70+.14*math.sin(9*x+3*y)+.09*math.sin(15*y-5*x)+.045*math.sin(26*x+21*y)
        alpha = round(255*min(.80, lobes*density)*edge(x, y))
        mist.putpixel((px, py), (255, 255, 255, alpha))
mist.save(DEST/'haze.png')

for phase in range(4):
    rng = random.Random(54321+phase*91)
    core = Image.new('L', (SIZE, SIZE))
    broad = Image.new('L', (SIZE, SIZE))
    dc, db = ImageDraw.Draw(core), ImageDraw.Draw(broad)
    for stroke in range(7):
        angle = rng.uniform(0., math.tau)
        start = (rng.uniform(-.31, .31), rng.uniform(-.31, .31))
        reach = rng.uniform(.25, .57)
        points = []
        for index in range(12):
            t = index/11
            side = .10*math.sin(t*5.2+stroke)+rng.uniform(-.035, .035)*math.sin(math.pi*t)
            x = start[0]+math.cos(angle)*reach*t+math.sin(angle)*side
            y = start[1]+math.sin(angle)*reach*t-math.cos(angle)*side
            points.append(((x*.5+.5)*SIZE, (y*.5+.5)*SIZE))
        db.line(points, fill=rng.randint(90, 150), width=16)
        dc.line(points, fill=rng.randint(145, 215), width=3+(stroke%2))
    broad = broad.filter(ImageFilter.GaussianBlur(5.0))
    pixels = Image.new('RGBA', (SIZE, SIZE))
    for py in range(SIZE):
        y = (py/(SIZE-1)-.5)*2
        for px in range(SIZE):
            x = (px/(SIZE-1)-.5)*2
            alpha = round(min(230, core.getpixel((px, py))+broad.getpixel((px, py))*.68)*edge(x, y))
            pixels.putpixel((px, py), (255, 255, 255, alpha))
    pixels.save(DEST/f'residual{phase}.png')

files = [DEST/'haze.png']+[DEST/f'residual{i}.png'for i in range(4)]
(DEST/'source.json').write_text(json.dumps({
    'source': 'src/cocos/tools/make-thunder-ground-v1.py',
    'provider': 'Project procedural Pillow masks; no image model or download',
    'license': 'Original deterministic project artwork; no third-party pixels',
    'purpose': 'Soft blue-violet ground haze with broken residual electricity; no closed circle or damage geometry',
    'assets': [{'file': file.name, 'size': [SIZE, SIZE], 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()} for file in files],
    'generationStatus': 'deterministic generation succeeded',
    'artAcceptance': 'pending actual same-camera and motion review; successful mask generation is not combat art acceptance'
}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('Generated thunder ground haze and four residual masks')
