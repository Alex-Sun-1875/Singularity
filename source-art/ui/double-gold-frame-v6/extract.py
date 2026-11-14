"""Build a reusable nine-slice from the user's approved gold frame pixels."""
from pathlib import Path
import json
import uuid
import hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'src/cocos/assets/resources/ui/quiet-bronze'
reference = Image.open(HERE / 'reference-design.png').convert('RGBA')
box = (241, 93, 666, 599)
panel = reference.crop(box)
w, h = panel.size
size, corner = 512, 48
frame = Image.new('RGBA', (size, size))
for src, dst in [((0, 0, corner, corner), (0, 0)), ((w-corner, 0, w, corner), (size-corner, 0)), ((0, h-corner, corner, h), (0, size-corner)), ((w-corner, h-corner, w, h), (size-corner, size-corner))]:
    frame.paste(panel.crop(src), dst)
frame.paste(panel.crop((58, 0, 138, corner)).resize((size-2*corner, corner), Image.Resampling.LANCZOS), (corner, 0))
frame.paste(panel.crop((58, h-corner, 138, h)).resize((size-2*corner, corner), Image.Resampling.LANCZOS), (corner, size-corner))
frame.paste(panel.crop((0, 80, corner, 160)).resize((corner, size-2*corner), Image.Resampling.LANCZOS), (0, corner))
frame.paste(panel.crop((w-corner, 80, w, 160)).resize((corner, size-2*corner), Image.Resampling.LANCZOS), (size-corner, corner))

def rounded_mask(inset, radius):
    mask = Image.new('L', (size*4, size*4))
    ImageDraw.Draw(mask).rounded_rectangle((inset*4, inset*4, (size-inset)*4-1, (size-inset)*4-1), radius=radius*4, fill=255)
    return np.array(mask.resize((size, size), Image.Resampling.LANCZOS)).astype(float)

outer = rounded_mask(1, 30)
inner = rounded_mask(18, 22)
frame.putalpha(Image.fromarray(np.clip(outer-inner, 0, 255).astype('uint8')))
frame.save(HERE / 'double-gold-frame-v6.png')

# The blank material is sampled separately; labels and switches stay live UI.
sample = reference.crop((490, 478, 522, 510)).convert('RGB')
material = Image.new('RGBA', (size, size))
for y in range(0, size, sample.height):
    for x in range(0, size, sample.width):
        tile = ImageOps.mirror(sample) if (x//sample.width)%2 else sample
        if (y//sample.height)%2: tile = ImageOps.flip(tile)
        material.paste(tile, (x, y))
material = material.filter(ImageFilter.GaussianBlur(.6))
material.putalpha(Image.fromarray(outer.astype('uint8')))
material.save(HERE / 'double-gold-inset-v6.png')

crest = reference.crop((399, 45, 517, 117)).convert('RGB')
pixels = np.array(crest).astype(float)
light = pixels @ np.array([.299, .587, .114])
warmth = (pixels[:, :, 0] - pixels[:, :, 2]) / np.maximum(1, pixels[:, :, 0])
alpha = np.clip((light-38)/65, 0, 1) * np.clip((warmth-.11)/.15, 0, 1) * 255
crest = Image.fromarray(np.dstack([pixels, np.round(alpha)]).astype('uint8'))
# The generated draft's head axis is x=449, not the crop midpoint x=458.
# Retain the fuller left branches and mirror them about the head, then center
# the complete metal ornament in its fixed runtime slot. Text is separate.
half = Image.new('RGBA', (59, 72))
half.alpha_composite(crest.crop((0, 0, 50, 72)), (9, 0))
crest = Image.new('RGBA', (118, 72))
crest.paste(half, (0, 0))
crest.paste(ImageOps.mirror(half), (59, 0))
crest.save(HERE / 'double-gold-stag-v6.png')

rule = reference.crop((275, 213, 395, 231)).convert('RGB')
pixels = np.array(rule).astype(float)
light = pixels @ np.array([.299, .587, .114])
alpha = np.clip((light-38)/65, 0, 1)*255
rule = Image.fromarray(np.dstack([pixels, np.round(alpha)]).astype('uint8'))
rule.save(HERE / 'double-gold-tab-rule-v6.png')
thumb = reference.crop((591, 258, 632, 299))
mask = Image.new('L', (164, 164))
ImageDraw.Draw(mask).ellipse((12, 12, 152, 152), fill=255)
thumb.putalpha(mask.resize((41, 41), Image.Resampling.LANCZOS))
thumb.save(HERE / 'double-gold-toggle-thumb-v6.png')

# Preserve the softly engraved row rule rather than rasterizing a subpixel line.
rule = reference.crop((284, 312, 631, 320)).convert('RGB')
pixels = np.array(rule).astype(float)
light = pixels @ np.array([.299, .587, .114])
alpha = np.clip((light-31)/52, 0, 1)*255
Image.fromarray(np.dstack([pixels, np.round(alpha)]).astype('uint8')).save(HERE / 'double-gold-divider-v6.png')

# The left track end is unobstructed. Mirror it to remove the baked thumb;
# an annular mask removes all baked label pixels. State/fill remains live UI.
track = Image.new('RGBA', (104, 48))
left = reference.crop((531, 255, 583, 303))
track.paste(left, (0, 0))
track.paste(ImageOps.mirror(left), (52, 0))
outer_track = Image.new('L', (416, 192))
inner_track = Image.new('L', (416, 192))
ImageDraw.Draw(outer_track).rounded_rectangle((0, 0, 415, 191), radius=96, fill=255)
ImageDraw.Draw(inner_track).rounded_rectangle((20, 20, 395, 171), radius=76, fill=255)
ring = np.clip(np.array(outer_track).astype(float)-np.array(inner_track), 0, 255).astype('uint8')
track.putalpha(Image.fromarray(ring).resize((104, 48), Image.Resampling.LANCZOS))
track.save(HERE / 'double-gold-toggle-track-v6.png')

template = (OUT / 'unified-gold-panel-v13.png.meta').read_text(encoding='utf-8')
exports = []
for name in ['double-gold-frame-v6', 'double-gold-inset-v6', 'double-gold-stag-v6', 'double-gold-tab-rule-v6', 'double-gold-toggle-thumb-v6', 'double-gold-divider-v6', 'double-gold-toggle-track-v6']:
    data = (HERE / (name+'.png')).read_bytes()
    (OUT / (name+'.png')).write_bytes(data)
    meta = OUT / (name+'.png.meta')
    if not meta.exists():
        meta.write_text(template.replace('7c24294c-9712-4a7e-bdf4-833e199b18b9', str(uuid.uuid4())).replace('unified-gold-panel-v13', name), encoding='utf-8')
    exports.append({'id': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
(HERE / 'provenance.json').write_text(json.dumps({'date': '2026-11-11', 'source': 'User-attached design image, retained as reference-design.png', 'method': 'Local deterministic crop, nine-slice pixel composition and alpha extraction; no new generated image.', 'panelBounds': box, 'cornerInsetPixels': corner, 'runtimeFramePixelScale': 1, 'inputGeometrySeparateFromSkinPixels': True, 'exports': exports, 'exportBytes': sum(x['bytes'] for x in exports), 'artReview': 'Recorded separately in art-review.json'}, indent=2), encoding='utf-8')
