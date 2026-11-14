"""Rebuild the small native Line masks; uses the project's existing Pillow."""
from pathlib import Path
from PIL import Image
import hashlib
import json
import math
import uuid

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'assets/resources/vfx/production'


def meta(path, importer):
    target = Path(str(path) + '.meta')
    if target.exists():
        return
    key = str(uuid.uuid4())
    data = {'ver': '2.0.1', 'importer': importer, 'imported': True,
            'uuid': key, 'files': ['.json'], 'subMetas': {}, 'userData': {}}
    if importer == 'image':
        texture = key + '@6c48a'
        data.update(ver='1.0.27', files=['.json', '.png'], subMetas={
            '6c48a': {'importer': 'texture', 'uuid': texture,
                      'displayName': path.stem, 'id': '6c48a', 'name': 'texture',
                      'userData': {'wrapModeS': 'clamp-to-edge', 'wrapModeT': 'clamp-to-edge',
                                   'minfilter': 'linear', 'magfilter': 'linear', 'mipfilter': 'none',
                                   'anisotropy': 0, 'isUuid': True,
                                   'imageUuidOrDatabaseUri': key, 'visible': False},
                      'ver': '1.0.22', 'imported': True, 'files': ['.json'], 'subMetas': {}}},
                    userData={'type': 'texture', 'fixAlphaTransparencyArtifacts': False,
                              'hasAlpha': True, 'redirect': texture})
    target.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


DEST.mkdir(parents=True, exist_ok=True)
white = DEST / 'ribbon-white-v1.png'
Image.new('RGBA', (4, 4), (255, 255, 255, 255)).save(white)
soft = DEST / 'ribbon-soft-v1.png'
mask = Image.new('RGBA', (4, 256))
edge = math.exp(-0.5 / 0.34**2)
for y in range(256):
    cross = 2 * y / 255 - 1
    alpha = round(255 * max(0, (math.exp(-0.5 * (cross / 0.34)**2) - edge) / (1 - edge)))
    for x in range(4):
        mask.putpixel((x, y), (255, 255, 255, alpha))
mask.save(soft)
for path in (white, soft):
    meta(path, 'image')
record = DEST / 'ribbon-masks-v1.source.json'
record.write_text(json.dumps({
    'source': 'src/cocos/tools/make-ribbon-masks.py',
    'generationProvider': 'Deterministic project code using existing Pillow; no model or download',
    'licenseNote': 'Original procedural project assets, with no third-party source imagery',
    'assets': [{'file': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                'size': list(Image.open(p).size)} for p in (white, soft)],
    'formula': 'RGB=255 everywhere. white alpha=255; soft alpha=round(255*(exp(-0.5*(x/0.34)^2)-exp(-0.5/0.34^2))/(1-exp(-0.5/0.34^2))), x=2*y/255-1',
    'integration': 'Cocos builtin-particle-trail: white masks for straight-alpha blue body/cold white core; separate soft mask for additive halo. UV.y is the ribbon cross section.',
    'runtimeReview': 'pending real renderer capture',
    'artReview': 'Mathematical kernel verified separately from combat art acceptance'
}, indent=2) + '\n', encoding='utf-8')
meta(record, 'json')
print('Generated white and Gaussian ribbon masks')
