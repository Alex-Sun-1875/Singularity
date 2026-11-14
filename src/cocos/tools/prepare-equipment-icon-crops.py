"""Copy authored equipment regions pixel-for-pixel into independently loadable PNGs.

Pillow is already used by the project's asset pipeline. Keep two source pixels
around every sampled rect for identical bilinear edges; no resizing or codec.
"""
import argparse
import copy
import hashlib
import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
ROOT = PROJECT / 'assets/resources/equipment/v3'
ARCHIVE = REPO / 'source-art/performance/equipment-icon-crops-v1'


def save(path, data):
    content = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if not path.exists() or path.read_text(encoding='utf8') != content:
        with tempfile.NamedTemporaryFile(dir=PROJECT / 'temp', delete=False) as temporary:
            temporary.write(content.encode('utf8'))
            name = Path(temporary.name)
        try:
            for attempt in range(10):
                try:
                    os.replace(name, path)
                    break
                except OSError:
                    if attempt == 9:
                        raise
                    time.sleep(.1)
        finally:
            name.unlink(missing_ok=True)


def main(write):
    original = ARCHIVE / 'manifest.json'
    if not original.exists():
        if not write:
            raise SystemExit('Run --write once to preserve the authored manifest.')
        ARCHIVE.mkdir(parents=True, exist_ok=True)
        original.write_bytes((ROOT / 'manifest.json').read_bytes())
    source = json.loads(original.read_text(encoding='utf8'))
    result = copy.deepcopy(source)
    result['images'] = {}
    records = []
    output = ROOT / 'runtime-icons'
    if write:
        output.mkdir(exist_ok=True)
        save(output.with_suffix('.meta'), {'ver': '1.2.0', 'importer': 'directory', 'imported': True,
             'uuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'singularity/equipment/v3/runtime-icons')),
             'files': [], 'subMetas': {}, 'userData': {}})
    for key, art in source['items'].items():
        resource = source['images'][art['image']]['resource']
        image_path = PROJECT / ('assets/resources/' + resource + '.png')
        with Image.open(image_path) as image:
            image = image.convert('RGBA')
            rects = [art['rect'], *art.get('slotRects', {}).values()]
            left = max(0, min(r[0] for r in rects) - 2)
            top = max(0, min(r[1] for r in rects) - 2)
            right = min(image.width, max(r[0] + r[2] for r in rects) + 2)
            bottom = min(image.height, max(r[1] + r[3] for r in rects) + 2)
            if any(x < 0 or y < 0 or w <= 0 or h <= 0 or x+w > image.width or y+h > image.height for x,y,w,h in rects):
                raise ValueError('Invalid source equipment rect: ' + key)
            cropped = image.crop((left, top, right, bottom))
            target = output / (key.lower() + '.png')
            texture_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'singularity/equipment/v3/runtime-icons/' + key))
            meta = json.loads(image_path.with_suffix('.png.meta').read_text(encoding='utf8'))
            meta['uuid'] = texture_uuid
            meta['userData'].pop('compressSettings', None)
            meta['userData']['redirect'] = texture_uuid + '@6c48a'
            texture = meta['subMetas']['6c48a']
            texture['uuid'] = texture_uuid + '@6c48a'
            texture['displayName'] = key.lower()
            texture['userData']['imageUuidOrDatabaseUri'] = texture_uuid
            texture['userData']['wrapModeS'] = texture['userData']['wrapModeT'] = 'clamp-to-edge'
            if write:
                if not target.exists() or Image.open(target).convert('RGBA').tobytes() != cropped.tobytes() or Image.open(target).size != cropped.size:
                    cropped.save(target, optimize=True)
                save(target.with_suffix('.png.meta'), meta)
            if not target.exists() or Image.open(target).convert('RGBA').tobytes() != cropped.tobytes() or Image.open(target).size != cropped.size:
                raise ValueError('Equipment crop pixel mismatch: ' + key)
            result['images'][key] = {'resource': 'equipment/v3/runtime-icons/' + key.lower(), 'width': cropped.width, 'height': cropped.height,
                                     'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
            entry = result['items'][key]
            entry['image'] = key
            entry['rect'] = [art['rect'][0]-left, art['rect'][1]-top, *art['rect'][2:]]
            if 'slotRects' in art:
                entry['slotRects'] = {slot: [r[0]-left, r[1]-top, *r[2:]] for slot, r in art['slotRects'].items()}
            records.append({'id': key, 'source': resource, 'sourceBounds': [left, top, right, bottom], 'width': cropped.width, 'height': cropped.height,
                            'rgbaBytes': cropped.width*cropped.height*4, 'pixelIdentical': True})
    if write:
        save(ROOT / 'manifest.json', result)
        save(ARCHIVE / 'validation.json', {'method': 'Lossless region copy with 2px source padding; original PNGs and manifest preserved.', 'images': records})
        profile_path = PROJECT / 'release/taptap.json'
        profile = json.loads(profile_path.read_text(encoding='utf8'))
        pack = next(p for p in profile['packs'] if p['name'] == 'equipment-art')
        pack['excludeFiles'] = sorted(set(pack.get('excludeFiles', [])) | {v['resource'].removeprefix('equipment/') + '.png' for v in source['images'].values()})
        save(profile_path, profile)
    print(json.dumps({'checked': len(records), 'pixelFailures': 0, 'allRgbaBytes': sum(r['rgbaBytes'] for r in records),
                      'initialOwnedRgbaBytes': sum(r['rgbaBytes'] for r in records if r['id'] in ['ART_SWORD_1', 'ART_BOW_1', 'ART_STAFF_1'])}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    main(parser.parse_args().write)
