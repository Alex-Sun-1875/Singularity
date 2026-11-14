"""Configure Cocos' native ASTC4 cooker with original PNG fallback, no resizing.

Only large opaque color sheets are compressed. Transparent sprites, UI chrome,
normal, ORM and roughness maps remain original after the codec quality audit.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import tempfile
import time
from pathlib import Path
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT / 'assets/resources'
PRESET = 'f87b536e-99d6-4ddd-ac2c-965255c1067a'


def write_json(path, data):
    content = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf8')
    if path.exists() and path.read_bytes() == content:
        return
    with tempfile.NamedTemporaryFile(dir=PROJECT / 'temp', delete=False) as temp:
        temporary = Path(temp.name)
        temp.write(content)
    try:
        for attempt in range(10):
            try:
                os.replace(temporary, path)
                break
            except OSError:
                if attempt == 9:
                    raise
                time.sleep(.1)
    finally:
        temporary.unlink(missing_ok=True)


def prepare(write=False):
    spec = importlib.util.spec_from_file_location('tap_resources', PROJECT / 'tools/prepare-taptap.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    profile = json.loads((PROJECT / 'release/taptap.json').read_text(encoding='utf8'))
    candidates = set()
    packs = {'painted-interiors', 'painted-props', 'painted-terrain', 'waystones',
             'hero-appearance', 'native-materials', 'hero-hairstyles'}
    for pack in profile['packs']:
        if pack['name'] not in packs:
            continue
        folder = ROOT / pack['path']
        excluded = set(module.pack_exclusions(pack))
        candidates.update(p for p in folder.rglob('*.png') if p.relative_to(folder).as_posix() not in excluded)
    for collection in profile['collections']:
        if collection['path'] != 'flat2d/characters':
            continue
        for folder in (ROOT / collection['path']).iterdir():
            if folder.is_dir() and folder.name not in collection.get('exclude', []):
                candidates.update(module.referenced_actor_images(folder))
    records = []
    preserved_alpha = []
    for image in sorted(candidates):
        if any(word in image.stem.lower() for word in ['normal', 'roughness', '-orm', '_orm']):
            continue
        with Image.open(image) as source:
            w, h = source.size
            opaque = source.convert('RGBA').getchannel('A').getextrema() == (255, 255)
        if w * h < 256 * 256:
            continue
        meta = image.with_suffix(image.suffix + '.meta')
        data = json.loads(meta.read_text(encoding='utf8'))
        if not opaque:
            preserved_alpha.append(image.relative_to(PROJECT).as_posix())
            if data.get('userData', {}).get('compressSettings', {}).get('presetId') == PRESET:
                del data['userData']['compressSettings']
                if write:
                    write_json(meta, data)
            continue
        data.setdefault('userData', {})['compressSettings'] = {'useCompressTexture': True, 'presetId': PRESET}
        records.append({'path': image.relative_to(PROJECT).as_posix(), 'width': w, 'height': h,
                        'sourceSha256': hashlib.sha256(image.read_bytes()).hexdigest()})
        if write:
            write_json(meta, data)
    if write:
        approved = {str((PROJECT / item['path']).resolve()) for item in records}
        for meta in ROOT.rglob('*.png.meta'):
            data = json.loads(meta.read_text(encoding='utf8'))
            if data.get('userData', {}).get('compressSettings', {}).get('presetId') == PRESET and str(meta.with_suffix('').resolve()) not in approved:
                del data['userData']['compressSettings']
                write_json(meta, data)
    settings = PROJECT / 'settings/v2/packages/builder.json'
    data = json.loads(settings.read_text(encoding='utf8'))
    options = {'astc_4x4': {'quality': 'exhaustive'}, 'png': {'quality': 100}}
    data.setdefault('textureCompressConfig', {}).setdefault('userPreset', {})[PRESET] = {
        'name': 'Mobile color ASTC4 exhaustive + original PNG',
        'options': {'web': options, 'miniGame': options},
    }
    if write:
        write_json(settings, data)
    result = {'preset': PRESET, 'format': 'ASTC 4x4', 'quality': 'exhaustive',
              'fallback': 'original PNG', 'sourceResolutionChanged': False,
              'excluded': ['transparent sprite/hair atlases', 'UI chrome', 'normal maps', 'ORM/roughness maps', 'small images'],
              'preservedAlphaImages': preserved_alpha,
              'count': len(records), 'images': records}
    if write:
        write_json(PROJECT / 'release/taptap-texture-compression.json', result)
    print(json.dumps({'count': len(records), 'written': write, 'preset': PRESET}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    prepare(parser.parse_args().write)
