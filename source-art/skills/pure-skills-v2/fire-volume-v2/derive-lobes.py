"""Deterministic regional crops of the preserved OpenAI four-phase fire source.

Run from any directory. This creates no generated pixels or new artwork: each
region keeps its source aspect, is uniformly reduced into a transparent canvas,
and receives a smooth alpha edge so the cuts can overlap without rectangle seams.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib
import json
import math
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT / 'src/cocos/assets/resources/vfx/production/fire-volume-v2'
# Normalized within each preserved phase's nonempty bounds. These are different
# rolling fronts from the same source, never six copies of the whole cloud.
REGIONS = [
    ('rear-left', (0.00, .27, .54, .95)),
    ('rear-crown', (.39, .20, 1.00, .94)),
    ('pressure', (.18, .55, .84, 1.00)),
    ('front-left', (.04, .72, .47, 1.00)),
    ('front-right', (.52, .72, .98, 1.00)),
]

def smooth(t):
    t = max(0., min(1., t))
    return t*t*(3.-2.*t)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

frames = []
preview = Image.new('RGB', (4*300, len(REGIONS)*260), (50, 45, 39))
draw = ImageDraw.Draw(preview)
for lobe, (name, region) in enumerate(REGIONS):
    # A common canvas per lobe is based on the explosion phase. Phase crops are
    # contained inside it; no phase is stretched to match another phase's shape.
    peak = Image.open(OUT / 'phase1.png').convert('RGBA')
    bx, by, br, bb = peak.getbbox()
    ratio = ((br-bx)*(region[2]-region[0])) / ((bb-by)*(region[3]-region[1]))
    cw, ch = (320, round(320/ratio)) if ratio >= 1 else (round(320*ratio), 320)
    for phase in range(4):
        source_path = OUT / f'phase{phase}.png'
        source = Image.open(source_path).convert('RGBA')
        x, y, right, bottom = source.getbbox()
        w, h = right-x, bottom-y
        box = (round(x+w*region[0]), round(y+h*region[1]),
               round(x+w*region[2]), round(y+h*region[3]))
        crop = source.crop(box)
        a = crop.getchannel('A')
        # Most feather is at the vertical cuts; the original flame tongues at
        # the top and the common contact base remain legible.
        pixels = a.load()
        for py in range(crop.height):
            for px in range(crop.width):
                nx, ny = px/max(1, crop.width-1), py/max(1, crop.height-1)
                left = .015+.012*math.sin(ny*13+lobe)
                right = .985-.012*math.sin(ny*11+lobe*2)
                # The front/pressure cuts pass through opaque material. Their
                # upper edge therefore needs a broad, irregular alpha taper,
                # rather than a bright horizontal rectangle.
                top = (.035+.025*math.sin(nx*9+lobe)+.012*math.sin(nx*23)) if region[1] else 0
                top_fade = .18
                edge = (smooth((nx-left)/.16)*smooth((right-nx)/.16)
                        *smooth((ny-top)/top_fade)
                        *smooth((1-ny)/.035))
                pixels[px, py] = round(pixels[px, py]*edge)
        crop.putalpha(a)
        scale = min((cw-8)/crop.width, (ch-8)/crop.height)
        resized = crop.resize((max(1, round(crop.width*scale)), max(1, round(crop.height*scale))), Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA', (cw, ch))
        # A shared four-pixel transparent contact margin is the per-lobe foot.
        canvas.alpha_composite(resized, ((cw-resized.width)//2, ch-4-resized.height))
        target = OUT / f'lobe{lobe}-phase{phase}.png'
        canvas.save(target)
        meta_path = target.with_suffix('.png.meta')
        if not meta_path.exists():
            meta = json.loads((OUT/'phase1.png.meta').read_text(encoding='utf-8-sig'))
            ident = str(uuid.uuid4())
            meta['uuid'] = ident
            meta['userData']['redirect'] = ident+'@6c48a'
            sub = meta['subMetas']['6c48a']
            sub['uuid'] = ident+'@6c48a'
            sub['displayName'] = target.stem
            sub['userData']['imageUuidOrDatabaseUri'] = ident
            sub['userData']['wrapModeS'] = sub['userData']['wrapModeT'] = 'clamp-to-edge'
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        frames.append({'lobe': lobe, 'name': name, 'phase': phase,
                       'source': str(source_path.relative_to(ROOT)).replace('\\', '/'),
                       'sourceSha256': sha(source_path), 'sourceCrop': box,
                       'canvas': [cw, ch], 'footAnchor': [cw/2, ch-4],
                       'sha256': sha(target)})
        thumb = canvas.copy()
        thumb.thumbnail((280, 225), Image.Resampling.LANCZOS)
        preview.paste(thumb, (phase*300+(300-thumb.width)//2, lobe*260+22), thumb)
        draw.text((phase*300+8, lobe*260+6), f'{name} / phase {phase}', fill=(235, 222, 195))
preview.save(HERE/'lobe-source-review.jpg', quality=90)
record = {
    'date': '2026-11-08', 'operation': 'Pillow deterministic regional crops and alpha feather only',
    'provider': 'Derived from preserved OpenAI image_gen fire-volume-v2 output; no new generation',
    'originalSource': 'generated-sheet.png', 'originalSha256': sha(HERE/'generated-sheet.png'),
    'script': 'derive-lobes.py',
    'semantics': ['compression/start', 'explosion', 'rolling front', 'dissipation'],
    'artReview': 'five distinct source crops reviewed; runtime reviews are separately recorded; generation success is not acceptance',
    'userAcceptance': 'not claimed', 'frames': frames,
}
record_path = HERE/'lobe-provenance.json'
if record_path.exists():
    previous = json.loads(record_path.read_text(encoding='utf-8'))
    if 'runtimeReviews' in previous:
        record['runtimeReviews'] = previous['runtimeReviews']
record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'frames': len(frames), 'canvases': sorted({tuple(f['canvas']) for f in frames}), 'preview': str(HERE/'lobe-source-review.jpg')}))
