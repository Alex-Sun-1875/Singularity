"""Recolour existing arrow UV islands with Pillow; no generated image or mesh edit.

Default input is the archived pre-revision atlas, making repeated runs identical.
After a fresh Blender export, pass --input <new-texture-folder> to reapply the finish.
"""
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input', type=Path, default=BASE / 'original')
parser.add_argument('--output', type=Path, default=ROOT / 'src/cocos/assets/resources/actors/props-native/textures')
args = parser.parse_args()
albedo = Image.open(args.input / 'arrow_albedo.png').convert('RGB')
orm = Image.open(args.input / 'arrow_orm.png').convert('RGB')
assert albedo.size == orm.size
counts = {'shaft': 0, 'head': 0, 'preserved': 0}
colours, channels = [], []
for (r, g, b), (ao, rough, metal) in zip(albedo.getdata(), orm.getdata()):
    if metal > 128:
        # Broadhead: satin steel, with its existing subtle baked variation.
        shade = round((r + g + b) / 3 - 193)
        colours.append(tuple(max(0, min(255, c + shade)) for c in (205, 216, 224)))
        channels.append((ao, max(98, min(126, rough + 32)), 140))
        counts['head'] += 1
    elif 0 < max(r, g, b) < 160 and metal < 32:
        # Reuse the narrow longitudinal grain as brushed, weathered silver.
        shade = round((.2126 * r + .7152 * g + .0722 * b - 50) * .3)
        colours.append(tuple(max(170, min(225, c + shade)) for c in (188, 197, 205)))
        channels.append((ao, max(120, min(150, 136 + shade)), 90))
        counts['shaft'] += 1
    else:
        # Ivory feathers and unused UV padding keep their original pixels.
        colours.append((r, g, b))
        channels.append((ao, rough, metal))
        counts['preserved'] += 1
assert counts['shaft'] > 1000 and counts['head'] > 1000, 'Expected original arrow atlas material islands'
args.output.mkdir(parents=True, exist_ok=True)
albedo.putdata(colours)
orm.putdata(channels)
albedo.save(args.output / 'arrow_albedo.png')
orm.save(args.output / 'arrow_orm.png')
record = {
    'revision': 'arrow-steel-v1', 'date': '2026-11-10',
    'method': 'Pillow deterministic UV-island palette and ORM adaptation',
    'source': 'Existing project-authored arrow atlas; original CC0 model provenance retained in props manifest',
    'generatedImage': False, 'counts': counts,
    'finish': 'Cold silver-grey weathered shaft, satin steel broadhead, original ivory fletching',
    'lighting': 'Moderate metal/diffuse mix for the existing scene without IBL; no emissive or additional light',
    'files': {n: hashlib.sha256((args.output / n).read_bytes()).hexdigest() for n in ['arrow_albedo.png', 'arrow_orm.png']},
    'artReviewRecord': 'art-review.json',
}
(BASE / 'production.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, ensure_ascii=False))
