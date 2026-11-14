"""Authoring-only CC0 terrain candidates. Never writes Cocos runtime assets."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image
from fetch_surfaces import download

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'source-art/materials/chapter-one-v3/terrain-library'
EXPORT = ROOT / 'assets/materials/chapter-one-v3/terrain-library'
CATALOG = ROOT / 'source-art/materials/chapter-one-v3/catalog-polyhaven-textures.json'
ASSETS = {'leafy-grass': 'leafy_grass', 'forest-earth': 'forest_ground_06'}
ROLES = {'albedo': ['diff', 'Diffuse', 'diffuse'], 'normal': ['nor_gl'],
         'roughness': ['rough', 'Rough'], 'ao': ['ao', 'AO']}


def main():
    SOURCE.mkdir(parents=True, exist_ok=True)
    EXPORT.mkdir(parents=True, exist_ok=True)
    if not CATALOG.exists():
        CATALOG.write_bytes(download('https://api.polyhaven.com/assets?t=textures'))
    catalog = json.loads(CATALOG.read_text(encoding='utf8'))
    records = []
    for name, asset in ASSETS.items():
        folder, target = SOURCE / name, EXPORT / name
        folder.mkdir(exist_ok=True)
        target.mkdir(exist_ok=True)
        metadata_file = folder / 'files.json'
        if not metadata_file.exists():
            metadata_file.write_bytes(download('https://api.polyhaven.com/files/' + asset))
        metadata = json.loads(metadata_file.read_text(encoding='utf8'))
        maps = []
        for role, candidates in ROLES.items():
            key = next(key for key in candidates if key in metadata)
            spec = metadata[key]['1k']['jpg']
            original = folder / (role + '.jpg')
            if not original.exists():
                original.write_bytes(download(spec['url']))
            payload = original.read_bytes()
            if hashlib.md5(payload).hexdigest() != spec['md5']:
                raise ValueError('Official MD5 mismatch: ' + asset + '/' + role)
            with Image.open(original) as image:
                image.verify()
            with Image.open(original) as image:
                size = list(image.size)
            shutil.copyfile(original, target / original.name)
            maps.append({'role': role, 'file': name + '/' + original.name,
                         'sourceUrl': spec['url'], 'officialMd5': spec['md5'],
                         'sha256': hashlib.sha256(payload).hexdigest(),
                         'size': size, 'bytes': len(payload),
                         'colorSpace': 'sRGB' if role == 'albedo' else 'linear'})
        dimensions = catalog[asset].get('dimensions')
        records.append({'id': name, 'sourceAsset': asset, 'maps': maps,
                        'sourcePage': 'https://polyhaven.com/a/' + asset,
                        'license': 'CC0-1.0', 'sourceDimensionsMillimetres': dimensions,
                        'tileMetres': [round(v / 1000, 4) for v in dimensions] if dimensions else None,
                        'normalConvention': 'OpenGL +Y', 'metallic': 0,
                        'selected': name != 'leafy-grass',
                        'notes': '未选色调对照：粉黄土占比和斑秃感过强，不能作为自然绿地定稿。' if name == 'leafy-grass' else '林间泥土候选，保持原色；后续与草地过渡并验收游戏镜头。',
                        'status': 'source-complete; offline and in-engine visual review required'})
        print('Verified four matched maps:', name, flush=True)
    green_entry = EXPORT / 'green-grass/entry.json'
    if green_entry.exists():
        green = json.loads(green_entry.read_text(encoding='utf8'))
        green['selected'] = True
        for entry in green['maps']:
            data = (EXPORT / entry['file']).read_bytes()
            if hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise ValueError('Green grass source copy changed: ' + entry['file'])
        records.append(green)
    manifest = {'credit': 'Powered by Poly Haven; Grass007 from ambientCG',
                'licenseSources': ['https://polyhaven.com/license', 'https://docs.ambientcg.com/license/'],
                'apiTerms': 'https://github.com/Poly-Haven/Public-API/blob/master/ToS.md',
                'processing': 'Official JPG/PNG bytes unchanged; no tint, resizing or generated PBR channels.',
                'runtimeInstalled': False, 'materials': records}
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    (SOURCE / 'manifest.json').write_text(text, encoding='utf8')
    (EXPORT / 'manifest.json').write_text(text, encoding='utf8')


if __name__ == '__main__':
    main()
