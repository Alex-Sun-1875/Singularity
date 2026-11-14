"""Fetch credited CC0 surface originals and export compact Cocos textures.

Authoring tool only; the shipped game never calls the Poly Haven API.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import urllib.request
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'source-art/materials/natural-v1'
EXPORT = ROOT / 'src/cocos/assets/resources/surfaces'
ASSETS = {
    'wood': 'wood_floor_worn',
    'cobble': 'cobblestone_floor_04',
    'grass': 'grass_ground',
    'earth': 'forest_ground_04',
    'rock': 'rock_face',
    'plaster': 'plastered_wall',
    'leather': 'leather_white',
    'fabric': 'rough_linen',
    'roof': 'grey_roof_tiles',
    'metal': 'metal_plate',
}


def download(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'SwordAndFireAssetAuthoring/1.0'})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def export_surface(item):
    name, asset = item
    folder = SOURCE / asset
    folder.mkdir(parents=True, exist_ok=True)
    EXPORT.mkdir(parents=True, exist_ok=True)
    metadata_file = folder / 'files.json'
    if not metadata_file.exists():
        metadata_file.write_bytes(download('https://api.polyhaven.com/files/' + asset))
    metadata = json.loads(metadata_file.read_text(encoding='utf8'))
    maps = []
    for role, candidates in [('color', ['diff', 'Diffuse', 'diffuse']), ('normal', ['nor_gl'])]:
        key = next(key for key in candidates if key in metadata)
        spec = metadata[key]['1k']['jpg']
        original = folder / (role + '-1k.jpg')
        if not original.exists():
            original.write_bytes(download(spec['url']))
        actual = hashlib.md5(original.read_bytes()).hexdigest()
        if actual != spec['md5']:
            raise ValueError(f'Checksum mismatch for {asset}/{role}')
        target = EXPORT / f'{name}-{role}.jpg'
        with Image.open(original) as image:
            image.convert('RGB').resize((512, 512), Image.Resampling.LANCZOS).save(target, quality=93, subsampling=0)
        maps.append({'role': role, 'source': str(original.relative_to(ROOT)),
                     'export': str(target.relative_to(ROOT)), 'url': spec['url'],
                     'originalMd5': actual, 'exportSha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                     'exportSize': [512, 512], 'exportBytes': target.stat().st_size})
    print(f'Exported {name}: {asset}', flush=True)
    return {'name': name, 'asset': asset, 'sourcePage': 'https://polyhaven.com/a/' + asset,
            'license': 'CC0-1.0', 'maps': maps}


if __name__ == '__main__':
    SOURCE.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as executor:
        surfaces = list(executor.map(export_surface, ASSETS.items()))
    record = {'date': '2026-11-04', 'credit': 'Powered by Poly Haven',
              'licenseSource': 'https://polyhaven.com/license',
              'apiTerms': 'https://github.com/Poly-Haven/Public-API/blob/master/ToS.md',
              'processing': '512px runtime exports; source colors unchanged; OpenGL normal maps.',
              'surfaces': surfaces}
    (SOURCE / 'provenance.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf8')
    (EXPORT / 'provenance.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf8')
