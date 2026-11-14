"""Prepare cloud-painted map surfaces for the existing Cocos 3.8 presentation.

No generation, downloads, geometry or gameplay edits. Raw ImageGen outputs stay
unchanged. Reuses the image/texture metadata contract and deterministic UUID5
scheme from tools/materials/export_pbr_runtime_v3.py, without importing Blender.

python tools/model-pipeline/prepare_map_terrain.py --textures-only
python tools/model-pipeline/prepare_map_terrain.py --atlas-only
python tools/model-pipeline/prepare_map_terrain.py
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import uuid

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, __version__ as PILLOW_VERSION

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'source-art/maps/terrain-production-v1'
RAW = SOURCE / 'raw'
OUTPUT = ROOT / 'src/cocos/assets/resources/flat2d/terrain-v1'
LEGACY = ROOT / 'src/cocos/assets/resources/flat2d/world/manifest-natural-v3.json'
SIZE = 512
EDGE_BAND = 6
KEYS = ['flagstone', 'forest', 'cobble', 'earth', 'meadow', 'wet-earth', 'bedrock', 'wood', 'water']
SPRITES = ['rocks-a', 'rocks-b', 'rocks-c', 'rocks-d', 'rocks-e', 'rocks-f',
           'grass-a', 'grass-b', 'fern-a', 'fern-b', 'reed-a', 'reed-b']


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def uuid_for(path: Path) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'singularity:' + relative(path)))


def texture_meta(path: Path, *, alpha: bool = False) -> None:
    """Existing Cocos image/texture importer fields; only sampler roles differ."""
    uid = uuid_for(path)
    sub = uid + '@6c48a'
    data = {
        'ver': '1.0.27', 'importer': 'image', 'imported': True,
        'uuid': uid, 'files': ['.png', '.json'],
        'subMetas': {'6c48a': {
            'importer': 'texture', 'uuid': sub, 'displayName': path.stem,
            'id': '6c48a', 'name': 'texture', 'ver': '1.0.22',
            'imported': True, 'files': ['.json'], 'subMetas': {},
            'userData': {
                'wrapModeS': 'clamp-to-edge' if alpha else 'repeat',
                'wrapModeT': 'clamp-to-edge' if alpha else 'repeat',
                'minfilter': 'linear', 'magfilter': 'linear',
                'mipfilter': 'none' if alpha else 'linear',
                'anisotropy': 0 if alpha else 4, 'isUuid': True,
                'imageUuidOrDatabaseUri': uid, 'visible': False,
            },
        }},
        'userData': {'type': 'texture', 'fixAlphaTransparencyArtifacts': False,
                     'hasAlpha': alpha, 'redirect': sub},
    }
    write_json(path.with_suffix(path.suffix + '.meta'), data)


def json_meta(path: Path) -> None:
    write_json(path.with_suffix(path.suffix + '.meta'), {
        'ver': '2.0.1', 'importer': 'json', 'imported': True,
        'uuid': uuid_for(path), 'files': ['.json'], 'subMetas': {}, 'userData': {},
    })


def edge_difference(pixels: np.ndarray) -> dict:
    """RGB byte differences at the wrap, independent of any art-acceptance claim."""
    p = pixels.astype(np.int16)
    result = {}
    for axis, delta in [('horizontal', np.abs(p[:, 0] - p[:, -1])),
                        ('vertical', np.abs(p[0, :] - p[-1, :]))]:
        result[axis] = {'meanAbsoluteRgb': round(float(delta.mean()), 6),
                        'p95AbsoluteRgb': round(float(np.percentile(delta, 95)), 6),
                        'maximumAbsoluteRgb': int(delta.max())}
    return result


def repair_wrap(image: Image.Image) -> tuple[Image.Image, dict]:
    original = np.asarray(image.convert('RGB')).copy()
    before = edge_difference(original)
    # Already matched edges keep every resized source pixel. Otherwise only the
    # outer six pixels on each side mix with the opposing mirrored edge.
    repair = max(before[a]['meanAbsoluteRgb'] for a in before) > 1.5
    pixels = original.astype(np.float32)
    if repair:
        for axis in [1, 0]:
            source = pixels.copy()
            for inset in range(EDGE_BAND):
                weight = 1 - inset / (EDGE_BAND - 1)
                if axis == 1:
                    left, right = source[:, inset, :], source[:, -1-inset, :]
                    pixels[:, inset, :] = left * (1-weight/2) + right * (weight/2)
                    pixels[:, -1-inset, :] = right * (1-weight/2) + left * (weight/2)
                else:
                    top, bottom = source[inset, :, :], source[-1-inset, :, :]
                    pixels[inset, :, :] = top * (1-weight/2) + bottom * (weight/2)
                    pixels[-1-inset, :, :] = bottom * (1-weight/2) + top * (weight/2)
    processed = np.clip(np.rint(pixels), 0, 255).astype(np.uint8)
    interior = (slice(EDGE_BAND, -EDGE_BAND), slice(EDGE_BAND, -EDGE_BAND))
    outside_band_max = int(np.abs(processed[interior].astype(np.int16)-original[interior]).max())
    if outside_band_max:
        raise ValueError('Wrap repair changed pixels outside its edge band')
    stats = {
        'applied': repair, 'bandPixelsPerSide': EDGE_BAND if repair else 0,
        'method': 'opposing mirrored edge mix, weight 1 at border tapering to 0 at sixth pixel',
        'skipThresholdMeanAbsoluteRgb': 1.5,
        'before': before, 'after': edge_difference(processed),
        'changedPixelFraction': round(float(np.any(processed != original, axis=2).mean()), 6),
        'maximumChangeOutsideBand': outside_band_max,
        'artMeaning': 'edge pixel continuity only; shape continuity and repetition require visual review',
    }
    return Image.fromarray(processed, 'RGB'), stats


def image_record(path: Path) -> dict:
    with Image.open(path) as image:
        result = {'file': relative(path), 'dimensions': list(image.size), 'mode': image.mode,
                  'sha256': sha256(path), 'bytes': path.stat().st_size}
        image.verify()
    return result


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in ['C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/segoeui.ttf']:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def material_preview() -> None:
    tile, gap, margin, header, label = 256, 12, 16, 76, 36
    board = Image.new('RGB', (margin*2+tile*3+gap*2, header+(tile+label)*3+gap*2+margin), '#202320')
    draw = ImageDraw.Draw(board)
    draw.text((margin, 12), 'PAINTED TERRAIN / 512px RUNTIME MATERIALS', font=font(23), fill='#e6e2d6')
    draw.text((margin, 44), '2026-11-08 | processed pixels; runtime review pending', font=font(16), fill='#adb5aa')
    for index, key in enumerate(KEYS):
        image = Image.open(OUTPUT / (key+'.png')).convert('RGB').resize((tile, tile), Image.Resampling.LANCZOS)
        x = margin + index%3*(tile+gap)
        y = header + index//3*(tile+label+gap)
        board.paste(image, (x, y))
        draw.text((x+4, y+tile+5), key, font=font(20), fill='#e6e2d6')
    board.save(SOURCE / 'terrain-materials-preview.jpg', quality=93, subsampling=0)


def tiling_preview() -> None:
    keys = ['flagstone', 'forest', 'water', 'bedrock']
    single, margin, gap, header, label = 192, 16, 18, 80, 34
    panel = single*2
    board = Image.new('RGB', (margin*2+panel*2+gap, header+(panel+label)*4+gap*3+margin), '#202320')
    draw = ImageDraw.Draw(board)
    draw.text((margin, 10), '2x2 TILING / RESIZED RAW vs EDGE REPAIR', font=font(23), fill='#e6e2d6')
    draw.text((margin, 44), 'LEFT: resized raw | RIGHT: processed | no runtime validation', font=font(16), fill='#adb5aa')
    for row, key in enumerate(keys):
        raw = Image.open(RAW / (key+'.png')).convert('RGB').resize((SIZE, SIZE), Image.Resampling.LANCZOS)
        processed = Image.open(OUTPUT / (key+'.png')).convert('RGB')
        for col, (image, role) in enumerate([(raw, 'raw resized'), (processed, 'processed')]):
            tile = image.resize((single, single), Image.Resampling.LANCZOS)
            x, y = margin+col*(panel+gap), header+row*(panel+label+gap)
            for tx in range(2):
                for ty in range(2):
                    board.paste(tile, (x+tx*single, y+ty*single))
            draw.text((x+4, y+panel+4), key+' / '+role, font=font(18), fill='#e6e2d6')
    board.save(SOURCE / 'terrain-tiling-review.jpg', quality=94, subsampling=0)


def export_textures() -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    records = []
    for key in KEYS:
        source = RAW / (key+'.png')
        before_hash = sha256(source)
        with Image.open(source) as raw:
            raw_dimensions, raw_mode = list(raw.size), raw.mode
            resized = raw.convert('RGB').resize((SIZE, SIZE), Image.Resampling.LANCZOS)
        processed, edge_stats = repair_wrap(resized)
        target = OUTPUT / (key+'.png')
        processed.save(target, optimize=True)
        texture_meta(target)
        if sha256(source) != before_hash:
            raise ValueError('Raw source changed during processing: '+key)
        records.append({
            'key': key,
            'generated': {'file': relative(source), 'dimensions': raw_dimensions,
                          'mode': raw_mode, 'sha256': before_hash,
                          'records': ['source-art/maps/terrain-production-v1/generated-primary.json',
                                      'source-art/maps/terrain-production-v1/generated-secondary.json']},
            'processed': {**image_record(target), 'colorSpace': 'sRGB RGB8',
                          'resize': 'Pillow LANCZOS 512x512', 'edgeRepair': edge_stats,
                          'sampler': {'wrap': 'repeat', 'mipfilter': 'linear', 'anisotropy': 4}},
            'artReview': {'status': 'processed-candidate-runtime-review-required',
                          'generationSucceeded': True, 'runtimeValidated': False,
                          'physicalPhonePerformanceValidated': False},
        })
    material_preview()
    tiling_preview()
    record = {
        'date': '2026-11-08', 'script': relative(Path(__file__).resolve()),
        'tools': {'Pillow': PILLOW_VERSION, 'numpy': np.__version__},
        'rawPolicy': 'Read-only source pixels and byte hashes preserved; no generation, local inference or downloads.',
        'metadataContract': 'tools/materials/export_pbr_runtime_v3.py texture_meta; same namespace UUID5 scheme.',
        'processing': 'Resize RGB to 512 square; opposing mirrored-edge mix confined to outer 6 pixels when needed.',
        'textures': records,
        'previews': [image_record(SOURCE/'terrain-materials-preview.jpg'), image_record(SOURCE/'terrain-tiling-review.jpg')],
        'runtimeValidated': False,
    }
    write_json(SOURCE / 'processed-textures.json', record)
    return record


def read_props() -> tuple[dict, dict]:
    path = SOURCE / 'generated-props.json'
    if not path.exists():
        raise FileNotFoundError('Wait for the approved sprite metadata: '+relative(path))
    record = json.loads(path.read_text(encoding='utf-8'))
    # This adapter is finalized against the producer's actual JSON schema.
    sprites = record.get('crops')
    if not isinstance(sprites, dict):
        raise ValueError('generated-props.json must provide the producer crops mapping')
    if set(sprites) != set(SPRITES):
        raise ValueError('Expected exactly the twelve named terrain sprites')
    return record, sprites


def export_atlas() -> dict:
    record, sprites = read_props()
    source = ROOT / record['source']['path']
    if sha256(source) != record['source']['sha256']:
        raise ValueError('Selected generated atlas checksum changed')
    with Image.open(source) as atlas:
        if atlas.mode != 'RGBA':
            raise ValueError('Terrain atlas lacks a real RGBA channel: '+atlas.mode)
        alpha = np.asarray(atlas.getchannel('A'))
        if int(alpha.min()) != 0 or int(alpha.max()) != 255:
            raise ValueError('Terrain atlas must include transparent background and opaque object pixels')
        width, height = atlas.size
        dimensions = [width, height]
        stats = {'transparentPixelFraction': round(float((alpha == 0).mean()), 6),
                 'opaquePixelFraction': round(float((alpha == 255).mean()), 6),
                 'partialPixelFraction': round(float(((alpha > 0) & (alpha < 255)).mean()), 6)}
        for key, definition in sprites.items():
            x, y, w, h = definition['rect']
            if min(x, y) < 0 or min(w, h) <= 0 or x+w > width or y+h > height:
                raise ValueError('Sprite outside atlas: '+key)
            if not np.any(alpha[y:y+h, x:x+w] > 32):
                raise ValueError('Empty sprite crop: '+key)
            cx, cy, cw, ch = definition['cell']
            if x < cx or y < cy or x+w > cx+cw or y+h > cy+ch:
                raise ValueError('Sprite crop crosses its assigned grid cell: '+key)
    target = OUTPUT / 'terrain-props.png'
    shutil.copyfile(source, target)
    texture_meta(target, alpha=True)
    if sha256(source) != sha256(target):
        raise ValueError('Atlas export must preserve exact source pixels')
    result = {'date': '2026-11-08', 'generatedRecord': relative(SOURCE/'generated-props.json'),
              'generated': image_record(source), 'processed': image_record(target),
              'processing': 'Byte-for-byte RGBA atlas copy; no resize or pixel repaint.',
              'alpha': stats, 'sprites': deepcopy(sprites),
              'sampler': {'wrap': 'clamp-to-edge', 'mipfilter': 'none', 'anisotropy': 0},
              'runtimeValidated': False}
    write_json(SOURCE / 'processed-props.json', result)
    return result


def export_muted_trees() -> dict:
    """Select only green foliage inside three existing tree sprite rectangles."""
    legacy = json.loads(LEGACY.read_text(encoding='utf-8'))
    source = ROOT / 'src/cocos/assets/resources/flat2d/world/world-props-natural-v3.png'
    source_hash = sha256(source)
    with Image.open(source) as image:
        original = np.asarray(image.convert('RGBA')).copy()
    rgba = original.copy()
    rect_mask = np.zeros(original.shape[:2], dtype=bool)
    changed = {}
    for key in ['oak', 'birch', 'pine']:
        x, y, width, height = legacy['sprites'][key]['rect']
        rect_mask[y:y+height, x:x+width] = True
        crop = rgba[y:y+height, x:x+width]
        rgb = crop[:, :, :3].astype(np.float32)
        greenness = rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2])
        weight = np.clip((greenness-3)/30, 0, 1) * (crop[:, :, 3] > 8)
        reduced = np.asarray(ImageEnhance.Color(Image.fromarray(crop[:, :, :3], 'RGB')).enhance(.65)).astype(np.float32)
        luminance = reduced[:, :, 0]*.2126 + reduced[:, :, 1]*.7152 + reduced[:, :, 2]*.0722
        olive = np.array([121, 125, 84], dtype=np.float32)
        olive = olive / float(np.dot(olive, [.2126, .7152, .0722]))
        reduced = reduced*.92 + luminance[:, :, None]*olive[None, None, :]*.08
        result = rgb*(1-weight[:, :, None]) + reduced*weight[:, :, None]
        crop[:, :, :3] = np.clip(np.rint(result), 0, 255).astype(np.uint8)
        changed[key] = {'rect': [x, y, width, height], 'selectedPixelFraction': round(float((weight>0).mean()), 6)}
    if not np.array_equal(rgba[:, :, 3], original[:, :, 3]):
        raise ValueError('Tree processing must preserve all alpha pixels')
    if not np.array_equal(rgba[~rect_mask], original[~rect_mask]):
        raise ValueError('Tree processing changed other sprites')
    target = OUTPUT / 'world-props-muted.png'
    Image.fromarray(rgba, 'RGBA').save(target, optimize=True)
    texture_meta(target, alpha=True)
    if sha256(source) != source_hash:
        raise ValueError('Existing tree source was modified')
    result = {'date': '2026-11-08', 'source': image_record(source), 'processed': image_record(target),
              'method': 'Only green RGB pixels in oak/birch/pine rects; saturation 0.65, then 0.08 luma-preserving grey-olive blend; soft green-dominance mask.',
              'mask': 'weight=clamp((G-max(R,B)-3)/30,0,1), alpha>8; no operations outside the three crop rectangles',
              'treeRects': changed, 'alphaPreserved': True, 'otherSpritePixelsPreserved': True,
              'runtimeValidated': False, 'artReview': 'selective-color candidate; normal-camera acceptance pending'}
    write_json(SOURCE / 'processed-trees.json', result)
    # Preview is deterministic pixel scaling only, with source alpha composited
    # onto a neutral review background so changed foliage remains inspectable.
    board = Image.new('RGB', (960, 760), '#343934')
    draw = ImageDraw.Draw(board)
    draw.text((16, 10), 'TREE FOLIAGE / EXISTING vs MUTED', font=font(25), fill='#e6e2d6')
    for row, key in enumerate(['oak', 'birch', 'pine']):
        x, y, width, height = legacy['sprites'][key]['rect']
        for col, pixels in enumerate([original, rgba]):
            tile = Image.fromarray(pixels[y:y+height, x:x+width], 'RGBA')
            tile.thumbnail((420, 205), Image.Resampling.LANCZOS)
            px, py = 30+col*480, 62+row*230
            board.paste(tile, (px+(420-tile.width)//2, py), tile)
            draw.text((px, py+207), key+' / '+('existing' if col==0 else 'muted'), font=font(17), fill='#e6e2d6')
    board.save(SOURCE / 'tree-foliage-review.jpg', quality=93, subsampling=0)
    return result


def export_shipwreck() -> dict | None:
    path = SOURCE/'raw/shipwreck.png'
    if not path.exists():
        return None
    original = Image.open(path).convert('RGBA')
    alpha = original.getchannel('A')
    bounds = alpha.point(lambda value: 255 if value > 32 else 0).getbbox()
    if not bounds or alpha.getextrema()[0] != 0:
        raise ValueError('Shipwreck must retain actual transparent surroundings')
    left, top, right, bottom = bounds
    crop = (max(0,left-5),max(0,top-5),min(original.width,right+5),min(original.height,bottom+5))
    image = original.crop(crop)
    image.thumbnail((1024,1024),Image.Resampling.LANCZOS)
    target = OUTPUT/'shipwreck.png'
    image.save(target,optimize=True)
    texture_meta(target,alpha=True)
    result = {'date':'2026-11-08','generated':image_record(path),'processed':image_record(target),
              'method':'Pillow alpha-bound crop with 5px padding and proportional Lanczos resize; raw preserved',
              'sourceCrop':list(crop),'alphaThresholdForBounds':32,
              'sprite':{'image':'shipwreck','rect':[0,0,image.width,image.height]},
              'artReview':{'status':'initial-style-pass-runtime-pending','findings':['Muted aged timber, broken ribs and narrow silhouette match the approved environment style.','Actual zero alpha exists outside the hull and in interior gaps.'],'runtimeValidated':False},
              'provenance':'source-art/maps/terrain-production-v1/generated-shipwreck.json'}
    write_json(SOURCE/'processed-shipwreck.json',result)
    return result


def export_manifest() -> dict:
    manifest = json.loads(LEGACY.read_text(encoding='utf-8'))
    props = json.loads((SOURCE/'processed-props.json').read_text(encoding='utf-8'))
    for key in KEYS:
        path = OUTPUT / (key+'.png')
        entry = image_record(path)
        manifest['images']['terrain-'+key] = {'resource': 'flat2d/terrain-v1/'+key,
                                              'dimensions': entry['dimensions'], 'sha256': entry['sha256']}
    atlas = image_record(OUTPUT/'terrain-props.png')
    manifest['images']['terrain-props'] = {'resource': 'flat2d/terrain-v1/terrain-props',
                                          'dimensions': atlas['dimensions'], 'sha256': atlas['sha256']}
    for key, definition in props['sprites'].items():
        manifest['sprites'][key] = {**definition, 'image': 'terrain-props'}
    trees = image_record(OUTPUT/'world-props-muted.png')
    manifest['images']['world-props-natural-v3'] = {'resource': 'flat2d/terrain-v1/world-props-muted',
                                                   'dimensions': trees['dimensions'], 'sha256': trees['sha256']}
    if (OUTPUT/'shipwreck.png').exists():
        wreck = image_record(OUTPUT/'shipwreck.png')
        manifest['images']['shipwreck'] = {'resource':'flat2d/terrain-v1/shipwreck','dimensions':wreck['dimensions'],'sha256':wreck['sha256']}
        manifest['sprites']['shipwreck'] = {'image':'shipwreck','rect':[0,0,*wreck['dimensions']]}
        manifest['modelDimensions']['shipwreck'] = [7,1.3,2.6]
        manifest['sourceAssetFamilies']['shipwreck'] = 'shipwreck'
    for index, key in enumerate(SPRITES[:6]):
        manifest['sourceAssetFamilies']['rocks-'+str(index)] = key
    for index in range(4):
        manifest['sourceAssetFamilies']['grass-'+str(index)] = 'grass-'+('a' if index%2 == 0 else 'b')
        manifest['sourceAssetFamilies']['fern-'+str(index)] = 'fern-'+('a' if index%2 == 0 else 'b')
    manifest['version'] = 'painted-terrain-v1'
    manifest['status'] = 'processed-art-runtime-review-required'
    manifest['coverage'] = '97 area profiles use painted terrain and cutout families; the original 32 retain their terrain values. S01-T1 keeps its whole-map inn-readable-v4 painting. New campaign water, bridge and gorge geometry is reviewed separately.'
    manifest['groundSources'] = ['flat2d/terrain-v1/'+key for key in KEYS]
    manifest['groundLicenses'] = 'Project cloud-generated painted materials; generation records retained separately. Existing natural-v3 cutouts retain their own provenance; no new CC0-stock claim is made for generated terrain.'
    manifest['legacyProvenance'] = manifest.get('provenance')
    manifest['provenance'] = 'source-art/maps/terrain-production-v1/processed-textures.json'
    manifest['additionalProvenance'] = ['source-art/maps/terrain-production-v1/processed-props.json',
                                         'source-art/maps/terrain-production-v1/processed-trees.json',
                                         'source-art/maps/terrain-production-v1/prompts.json']
    if (SOURCE/'processed-shipwreck.json').exists():
        manifest['additionalProvenance'].append('source-art/maps/terrain-production-v1/processed-shipwreck.json')
    manifest['limits'] = [
        'Architecture retains compatible shared natural-v3 cutout families; it is not a unique illustration for every named building.',
        'Nine painted ground textures are RGB 512 square with repeat/linear mip sampling; only narrow opposing edge pixels are repaired locally.',
        'Twelve new rock/grass/fern/reed sprites preserve their full-resolution transparent atlas and separately inspected crop bounds.',
        'The compatible world-props atlas only selectively mutes green foliage in the three existing tree rectangles; all alpha and other sprites are unchanged.',
        'Pixel edge continuity does not itself establish visually seamless patterns; 2x2 tiling and normal camera review remain separate.',
        'Original 32 terrain values, geography, entrances and saved coordinates remain authoritative; new campaign landforms use the same tested terrain/navigation path.',
        'Processed source coverage does not establish playthrough completion, occlusion correctness or physical-phone performance.',
    ]
    target = OUTPUT / 'manifest.json'
    write_json(target, manifest)
    json_meta(target)
    return manifest


def verify_metadata() -> None:
    for key in KEYS:
        path = OUTPUT / (key+'.png')
        with Image.open(path) as image:
            if image.size != (SIZE, SIZE) or image.mode != 'RGB':
                raise ValueError('Invalid runtime texture: '+key)
        meta = json.loads(path.with_suffix('.png.meta').read_text(encoding='utf-8'))
        sampler = meta['subMetas']['6c48a']['userData']
        if meta['uuid'] != uuid_for(path) or sampler['wrapModeS'] != 'repeat' or sampler['mipfilter'] != 'linear' or sampler['anisotropy'] != 4:
            raise ValueError('Runtime sampler/UUID mismatch: '+key)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--textures-only', action='store_true')
    group.add_argument('--atlas-only', action='store_true')
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not args.atlas_only:
        export_textures()
    verify_metadata()
    if not args.textures_only:
        export_atlas()
        export_muted_trees()
        export_shipwreck()
        manifest = export_manifest()
        print(json.dumps({'textures': len(KEYS), 'spriteCount': len(manifest['sprites']),
                          'newSprites': len(SPRITES) + int('shipwreck' in manifest['sprites']), 'output': relative(OUTPUT),
                          'runtimeValidated': False}))
    else:
        print(json.dumps({'textures': len(KEYS), 'atlasPending': True,
                          'output': relative(OUTPUT), 'runtimeValidated': False}))


if __name__ == '__main__':
    main()
