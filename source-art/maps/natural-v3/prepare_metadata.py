"""Copy built-in ImageGen outputs unchanged and inspect alpha for native UVs.

No raster image is edited, resampled, recolored, or saved by Pillow here.
Run from any directory: python source-art/maps/natural-v3/prepare_metadata.py
"""
from pathlib import Path
import hashlib
import json
import shutil
import uuid
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).parent / 'sources.json'
WORLD = ROOT / 'src/cocos/assets/resources/flat2d/world'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

data = json.loads(SOURCE.read_text(encoding='utf-8'))
data['referenceRecords'] = [{'file': path, 'sha256': sha(Path(path))} for path in data['references']]
data['reusedAlbedos'] = [{'file': 'src/cocos/assets/resources/surfaces/pbr-v3/' + name + '-color.png', 'sha256': sha(ROOT / ('src/cocos/assets/resources/surfaces/pbr-v3/' + name + '-color.png')), 'license': 'CC0-1.0', 'provenance': 'src/cocos/assets/resources/surfaces/pbr-v3/provenance.json'} for name in ('wood', 'cobble', 'earth', 'rock', 'grass')]
original = json.loads((WORLD / 'manifest.json').read_text(encoding='utf-8'))
manifest = json.loads(json.dumps(original))
manifest['version'] = 'natural-world-v3'
manifest['status'] = 'source-ready-runtime-review-required'
manifest['coverage'] = '32 original areas; S01-T1 uses inn-natural-v3, other areas use original albedos and natural-v3 painted cutouts'
manifest['provenance'] = 'source-art/maps/natural-v3/sources.json'

for record in data['files']:
    target = Path(record['editTarget'])
    generated = Path(record['generatedPath'])
    source = ROOT / record['sourceFile']
    runtime = ROOT / record['runtimeFile']
    target_hash = sha(target)
    old_key = target.stem
    if old_key in original['images']:
        assert target_hash == original['images'][old_key]['sha256'], 'Original artwork changed: ' + old_key
    for destination in (source, runtime):
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists() or sha(destination) != sha(generated):
            shutil.copyfile(generated, destination)
    record['editTargetSha256'] = target_hash
    record['sha256'] = sha(generated)
    assert sha(source) == sha(runtime) == record['sha256']
    with Image.open(generated) as image:
        width, height = image.size
        record['dimensions'] = [width, height]
        record['imageMode'] = image.mode
        alpha = image.getchannel('A') if 'A' in image.getbands() else None
        record['alphaExtrema'] = list(alpha.getextrema()) if alpha else [255, 255]
        if record['transparent']:
            assert alpha is not None and alpha.getextrema()[0] == 0, 'Missing true alpha: ' + old_key
        if old_key in original['images']:
            new_key = record['name']
            manifest['images'].pop(old_key)
            manifest['images'][new_key] = {'resource': 'flat2d/world/' + new_key, 'dimensions': [width, height], 'sha256': record['sha256']}
            for name, sprite in original['sprites'].items():
                if sprite['image'] != old_key:
                    continue
                # Inspect only alpha within the source atlas's equal cell.
                old_width, old_height = original['images'][old_key]['dimensions']
                x, y, w, h = sprite['cell']
                left, top = round(x * width / old_width), round(y * height / old_height)
                right, bottom = round((x + w) * width / old_width), round((y + h) * height / old_height)
                bounds = alpha.crop((left, top, right, bottom)).point(lambda a: 255 if a > 32 else 0).getbbox()
                assert bounds, 'Empty sprite cell: ' + name
                x0, y0, x1, y1 = bounds
                x0, y0 = max(0, x0 - 2), max(0, y0 - 2)
                x1, y1 = min(right - left, x1 + 2), min(bottom - top, y1 + 2)
                manifest['sprites'][name] = {'image': new_key, 'rect': [left + x0, top + y0, x1 - x0, y1 - y0], 'cell': [left, top, right - left, bottom - top], 'source': 'Built-in ImageGen natural-v3 edit; native SpriteFrame alpha-bound crop only'}
    meta_path = Path(str(runtime) + '.meta')
    if not meta_path.exists():
        meta = json.loads(Path(str(target) + '.meta').read_text(encoding='utf-8'))
        old_uuid, new_uuid = meta['uuid'], str(uuid.uuid4())
        meta = json.loads(json.dumps(meta).replace(old_uuid, new_uuid))
        for sub in meta.get('subMetas', {}).values():
            if sub.get('importer') == 'texture':
                sub['displayName'] = record['name']
        write_json(meta_path, meta)

manifest['limits'].append('Natural-v3 edits preserve atlas cells and map layout by prompt and visual inspection; generated artwork is not claimed to be pixel-identical in silhouette or furniture detail. Alpha bounds were reinspected for every edited sprite.')
write_json(WORLD / 'manifest-natural-v3.json', manifest)
manifest_meta = WORLD / 'manifest-natural-v3.json.meta'
if not manifest_meta.exists():
    meta = json.loads((WORLD / 'manifest.json.meta').read_text(encoding='utf-8'))
    meta['uuid'] = str(uuid.uuid4())
    write_json(manifest_meta, meta)
write_json(SOURCE, data)
print(json.dumps({'copiedImages': len(data['files']), 'sprites': len(manifest['sprites']), 'dimensions': {r['name']: r['dimensions'] for r in data['files']}, 'originalArtworkHashesVerified': True}, ensure_ascii=False))
