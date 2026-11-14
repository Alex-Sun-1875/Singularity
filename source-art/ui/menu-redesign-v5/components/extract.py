"""Extract approved concept pixels; no inference, downloads or dependencies added."""
from pathlib import Path
import json
import uuid
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RUNTIME = ROOT / 'src/cocos/assets/resources/ui/quiet-bronze'
V5 = Image.open(HERE.parent / 'menu-ui-proposal-v5.png').convert('RGB')
V3 = Image.open(HERE.parent.parent / 'menu-redesign-v3/menu-ui-proposal-v3.png').convert('RGB')

def symbol(source, box, name, crest=False):
    pixels = np.array(source.crop(box)).astype(float)
    luminance = pixels @ np.array([.299, .587, .114])
    alpha = np.clip((luminance - (44 if crest else 42)) / (34 if crest else 32), 0, 1) * 255
    alpha[(pixels[:, :, 0] < pixels[:, :, 1] * .94) | (pixels[:, :, 1] < pixels[:, :, 2] * 1.10)] = 0
    icon = Image.fromarray(np.dstack([pixels, np.round(alpha)]).astype('uint8'))
    if crest:
        icon = icon.resize((192, 103), Image.Resampling.LANCZOS)
    else:
        icon = icon.crop(icon.getbbox())
        factor = (112 if name.startswith('automation') else 106) / max(icon.size)
        icon = icon.resize(tuple(round(n * factor) for n in icon.size), Image.Resampling.LANCZOS)
        tile = Image.new('RGBA', (128, 128))
        tile.alpha_composite(icon, ((128 - icon.width) // 2, (128 - icon.height) // 2))
        icon = tile
    icon.save(HERE / (name + '.png'))
    icon.save(RUNTIME / (name + '.png'))

for name, box in [('automation-compass-v5', (426, 643, 455, 672)), ('automation-battle-v5', (504, 643, 532, 671)), ('automation-hunt-v5', (581, 643, 611, 672))]:
    symbol(V5, box, name)
for name, box in [('menu-music-v5', (726, 877, 754, 906)), ('menu-motion-v5', (727, 932, 754, 958)), ('menu-skillnames-v5', (727, 987, 754, 1014)), ('menu-settings-crest-v5', (819, 725, 890, 763))]:
    symbol(V3, box, name, name.endswith('crest-v5'))

grain_source = V3.crop((0, 0, 128, 38))
for name, size, radius in [('menu-panel-inset-v5', (512, 512), 36), ('menu-pill-inset-v5', (512, 128), 62)]:
    w, h = size
    grain = np.array(grain_source.resize(size, Image.Resampling.BICUBIC)).astype(float).mean(2)
    grain = (grain - grain.mean()) * .35
    pixels = np.zeros((h, w, 4), dtype='uint8')
    for y in range(h):
        t = y / max(1, h - 1)
        base = np.array([24 - 7 * t, 24 - 7 * t, 21 - 6 * t])
        pixels[y, :, :3] = np.clip(base[None, :] + grain[y, :, None], 0, 255)
    mask = Image.new('L', size)
    ImageDraw.Draw(mask).rounded_rectangle((3, 3, w - 4, h - 4), radius=radius, fill=255)
    pixels[:, :, 3] = np.array(mask)
    image = Image.fromarray(pixels)
    image.save(HERE / (name + '.png'))
    image.save(RUNTIME / (name + '.png'))

# Keep existing UUIDs stable when regenerating. Creator owns subsequent import data.
template = (RUNTIME / 'unified-gold-panel-v13.png.meta').read_text(encoding='utf-8')
for source in HERE.glob('*.png'):
    destination = RUNTIME / source.name
    if not destination.exists():
        continue
    meta = destination.with_suffix('.png.meta')
    if not meta.exists():
        meta.write_text(template.replace('7c24294c-9712-4a7e-bdf4-833e199b18b9', str(uuid.uuid4())).replace('unified-gold-panel-v13', source.stem), encoding='utf-8')
