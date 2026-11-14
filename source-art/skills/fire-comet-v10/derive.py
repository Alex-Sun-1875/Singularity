"""Deterministic atlas adaptation; preserves the generated head and alpha.
The four phases displace only tail pixels, not the incandescent head.
"""
from pathlib import Path
from PIL import Image
import hashlib
import json
import numpy as np
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RES = ROOT / 'src/cocos/assets/resources/vfx/production'
source = HERE / 'generated-comet.png'
image = Image.open(source).convert('RGBA')
image = image.convert('RGBa').resize((480, 160), Image.Resampling.LANCZOS).convert('RGBA')
cell = Image.new('RGBA', (512, 192))
cell.alpha_composite(image, (16, 16))
array = np.asarray(cell).astype(np.float32) / 255
array[:, :, :3] *= array[:, :, 3:4]
yy, xx = np.mgrid[:192, :512]
tail = np.clip((400 - xx) / 330, 0, 1)
tail = tail * tail * (3 - 2 * tail)
atlas = Image.new('RGBA', (2048, 192))
for frame in range(4):
    y = np.clip(yy + 4 * tail * np.sin(xx / 34 - frame * np.pi / 2), 0, 191)
    low = np.floor(y).astype(int)
    high = np.minimum(191, low + 1)
    weight = (y - low)[:, :, None]
    result = array[low, xx] * (1 - weight) + array[high, xx] * weight
    result[:, :, :3] /= np.maximum(result[:, :, 3:4], 1 / 255)
    atlas.alpha_composite(Image.fromarray(np.uint8(np.clip(result, 0, 1) * 255)), (frame * 512, 0))
output = RES / 'fire-comet-v10.png'
atlas.save(output)
meta = output.with_suffix('.png.meta')
if not meta.exists():
    data = json.loads((RES / 'fire-core-v7.png.meta').read_text(encoding='utf-8'))
    uid = str(uuid.uuid4())
    data['uuid'] = uid
    texture = data['subMetas']['6c48a']
    texture['uuid'] = uid + '@6c48a'
    texture['displayName'] = 'fire-comet-v10'
    texture['userData']['imageUuidOrDatabaseUri'] = uid
    data['userData']['redirect'] = uid + '@6c48a'
    meta.write_text(json.dumps(data, indent=2), encoding='utf-8')
record = {
    'generation': {'provider': 'OpenAI built-in image_gen', 'status': 'completed', 'prompt': 'prompt.txt', 'original': source.name, 'transparentRequested': True, 'references': [], 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()},
    'processing': {'method': 'Pillow premultiplied-alpha resize and NumPy deterministic tail displacement; generated head unchanged', 'frames': 4, 'frameSize': [512, 192], 'headAnchor': [.835, .5], 'output': str(output.relative_to(ROOT)), 'pngBytes': output.stat().st_size, 'rawTextureBytes': 2048 * 192 * 4, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()},
    'artReview': {'source': 'rounded incandescent head and long tapered flame tail reviewed; no bare stone, no smoke', 'runtime': 'pending'},
}
(HERE / 'provenance.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(record['processing']))
