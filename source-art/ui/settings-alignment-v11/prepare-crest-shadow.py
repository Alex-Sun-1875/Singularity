"""Deterministic antler underlay; keeps the approved symmetric gold art intact."""
import hashlib
import json
from pathlib import Path
import uuid

from PIL import Image, ImageFilter, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ASSETS = ROOT / 'src/cocos/assets/resources/ui/quiet-bronze'
source = ASSETS / 'double-gold-stag-v6.png'
crest = Image.open(source).convert('RGBA')
# Follow the antlers rather than adding a rectangular plate above the frame.
mask = crest.getchannel('A').point(lambda a: 255 if a >= 64 else 0)
# The frame already backs the lower metal. Avoid dark patches over its top rim.
fade = Image.new('L', mask.size)
for y in range(crest.height):
    for x in range(crest.width):
        fade.putpixel((x, y), round(mask.getpixel((x, y)) * max(0, min(1, (44-y)/4))))
mask = ImageOps.expand(fade, border=4)
mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(.75))
mask = mask.point(lambda a: round(a * .92))
material = Image.open(ASSETS / 'double-gold-inset-v6.png').convert('RGB')
shadow = Image.new('RGBA', mask.size, material.getpixel((material.width//2, material.height//2)))
shadow.putalpha(mask)
name = 'double-gold-stag-shadow-v11'
output = HERE / (name + '.png')
shadow.save(output)
data = output.read_bytes()
(ASSETS / output.name).write_bytes(data)
meta = ASSETS / (output.name + '.meta')
if not meta.exists():
    template = json.loads((ASSETS / 'double-gold-stag-v6.png.meta').read_text(encoding='utf-8'))
    text = json.dumps(template, ensure_ascii=False, indent=2)
    text = text.replace(template['uuid'], str(uuid.uuid4())).replace('double-gold-stag-v6', name)
    meta.write_text(text + '\n', encoding='utf-8')
(HERE / 'provenance.json').write_text(json.dumps({
    'source': str(source.relative_to(ROOT)),
    'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'method': 'Local alpha threshold 64, one-pixel dilation and 0.75px blur above the top rim; four-pixel transparent padding. Gold pixels and bilateral symmetry unchanged.',
    'purpose': 'Occlude bright world runes immediately behind the antler silhouette, without a rectangular backing.',
    'output': name, 'size': list(shadow.size), 'bytes': len(data),
    'sha256': hashlib.sha256(data).hexdigest(),
    'artReview': 'Pending rendered in-game review, separate from successful export.'
}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'{name}: {shadow.width}x{shadow.height}, {len(data)} bytes')
