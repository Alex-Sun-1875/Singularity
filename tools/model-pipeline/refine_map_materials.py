"""Prepare v2 painted map materials with existing Pillow/numpy tools.

Cloud generation is separate: inputs and full prompts live in generation.json.
No downloads, generative processing, geometry or gameplay changes here.
Run: python tools/model-pipeline/refine_map_materials.py
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'source-art/maps/material-refinement-v2'
RUNTIME = ROOT / 'src/cocos/assets/resources/flat2d/terrain-v1'
spec = importlib.util.spec_from_file_location('terrain_pipeline', Path(__file__).with_name('prepare_map_terrain.py'))
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)

# User direction: brighter, greener, aligned with stonebridge-valley startup
# artwork. Art targets, not physical measurements or automatic whole-image match.
PALETTE = {
    'meadow': ((101, 145, 60), 1.03),
    'earth': ((145, 130, 102), .96),
    'forest': ((116, 123, 76), .98),
    'wet-earth': ((108, 122, 80), .96),
    'bedrock': ((145, 148, 136), .95),
    'cobble': ((151, 150, 136), .94),
    'flagstone': ((146, 148, 137), .96),
    'wood': ((136, 116, 83), .98),
    'water': ((61, 134, 145), .92),
}

# Follow-up: keep the bright meadow's luminance/detail while softening its
# overly vivid yellow-green. Other surfaces and foliage retain their pixels.
SURFACE_CHROMA = {'meadow': .80}


def write_json(path: Path, data: dict):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def prepare(raw: Image.Image, target: tuple[int, int, int], contrast: float, chroma: float = 1):
    image = raw.convert('RGB').resize((512, 512), Image.Resampling.LANCZOS)
    pixels = np.asarray(image).astype(np.float32)
    # Remove part of accidental broad illumination from generated albedos.
    # This is deterministic color processing, not a new painted detail layer.
    broad = np.asarray(image.filter(ImageFilter.GaussianBlur(64))).astype(np.float32)
    mean = pixels.mean(axis=(0, 1))
    pixels -= (broad - broad.mean(axis=(0, 1))) * .45
    pixels = (pixels - mean) * contrast + np.asarray(target)
    if chroma != 1:
        luminance = pixels @ np.asarray([.2126, .7152, .0722])
        pixels = luminance[:, :, None] + chroma * (pixels - luminance[:, :, None])
    toned = Image.fromarray(np.clip(np.rint(pixels), 0, 255).astype(np.uint8), 'RGB')
    return pipeline.repair_wrap(toned)


def main():
    sources = json.loads((ART / 'generation.json').read_text(encoding='utf-8'))
    records = []
    for key, (target, contrast) in PALETTE.items():
        raw_path = ART / sources['textures'][key]['rawFile']
        chroma = SURFACE_CHROMA.get(key, 1)
        image, wrap = prepare(Image.open(raw_path), target, contrast, chroma)
        output = RUNTIME / (key + '-v2.png')
        image.save(output, optimize=True)
        pipeline.texture_meta(output)
        # Retain the existing project compression preset as well as sampler
        # settings; generation never changes platform texture policy.
        meta_path = output.with_suffix('.png.meta')
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        previous = json.loads((RUNTIME / (key + '.png.meta')).read_text(encoding='utf-8'))
        if 'compressSettings' in previous['userData']:
            meta['userData']['compressSettings'] = deepcopy(previous['userData']['compressSettings'])
            write_json(meta_path, meta)
        records.append({'key': key, 'raw': pipeline.image_record(raw_path),
                        'runtime': pipeline.image_record(output),
                        'meanRgbTarget': target, 'contrast': contrast, 'lumaPreservingChroma': chroma,
                        'broadIlluminationRemoval': .45, 'wrap': wrap})
    write_json(ART / 'processed.json', {
        'status': 'processed; tiling and actual scene visual review recorded separately',
        'tools': 'existing Pillow/numpy and prepare_map_terrain.py metadata/wrap helpers',
        'runtimePolicy': '512 RGB; Repeat; linear mip; anisotropy 4; existing compression preset',
        'materials': records,
    })
    # Reuse the original accepted tree pixels, lifting only foliage RGB in its
    # existing three rectangles. Alpha, trunks and other props stay exact.
    tree_source = ROOT / 'src/cocos/assets/resources/flat2d/world/world-props-natural-v3.png'
    rgba = np.asarray(Image.open(tree_source).convert('RGBA')).copy()
    original = rgba.copy()
    legacy = json.loads(pipeline.LEGACY.read_text(encoding='utf-8'))
    selected = np.zeros(rgba.shape[:2], dtype=bool)
    for key in ['oak', 'birch', 'pine']:
        x, y, w, h = legacy['sprites'][key]['rect']
        crop = rgba[y:y+h, x:x+w]
        rgb = crop[:, :, :3].astype(np.float32)
        weight = np.clip((rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2]) - 3) / 30, 0, 1) * (crop[:, :, 3] > 8)
        color = ImageEnhance.Color(Image.fromarray(crop[:, :, :3], 'RGB')).enhance(1.12)
        bright = np.asarray(ImageEnhance.Brightness(color).enhance(1.08)).astype(np.float32)
        crop[:, :, :3] = np.clip(np.rint(rgb * (1-weight[:, :, None]) + bright * weight[:, :, None]), 0, 255).astype(np.uint8)
        selected[y:y+h, x:x+w] = True
    assert np.array_equal(rgba[:, :, 3], original[:, :, 3])
    assert np.array_equal(rgba[~selected], original[~selected])
    tree_output = RUNTIME / 'world-props-bright-v2.png'
    Image.fromarray(rgba, 'RGBA').save(tree_output, optimize=True)
    pipeline.texture_meta(tree_output, alpha=True)
    tree_meta_path = tree_output.with_suffix('.png.meta')
    tree_meta = json.loads(tree_meta_path.read_text(encoding='utf-8'))
    old_tree_meta = json.loads((RUNTIME / 'world-props-muted.png.meta').read_text(encoding='utf-8'))
    if 'compressSettings' in old_tree_meta['userData']:
        tree_meta['userData']['compressSettings'] = deepcopy(old_tree_meta['userData']['compressSettings'])
        write_json(tree_meta_path, tree_meta)
    write_json(ART / 'processed-foliage.json', {
        'source': pipeline.image_record(tree_source), 'runtime': pipeline.image_record(tree_output),
        'method': 'original oak/birch/pine green RGB only; saturation 1.12; brightness 1.08; existing soft green-dominance mask',
        'alphaPreserved': True, 'pixelsOutsideTreeRectanglesPreserved': True,
        'artReference': 'src/cocos/assets/resources/ui/loading/stonebridge-valley.png',
        'status': 'pixel processing verified; art and actual scene review separate',
    })
    manifest_path = RUNTIME / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['version'] = 'painted-terrain-materials-v2'
    manifest['status'] = 'processed-art; see material-refinement-v2/runtime-review.json for visual validation'
    for record in records:
        key, runtime = record['key'], record['runtime']
        manifest['images']['terrain-' + key] = {
            'resource': 'flat2d/terrain-v1/' + key + '-v2',
            'dimensions': runtime['dimensions'], 'sha256': runtime['sha256'],
        }
    manifest['groundSources'] = ['flat2d/terrain-v1/' + key + '-v2' for key in PALETTE]
    manifest['images']['world-props-natural-v3'] = {
        'resource': 'flat2d/terrain-v1/world-props-bright-v2',
        'dimensions': list(Image.open(tree_output).size), 'sha256': pipeline.sha256(tree_output),
    }
    manifest['provenance'] = 'source-art/maps/material-refinement-v2/processed.json'
    manifest['limits'][1] = 'Nine v2 painted ground textures are RGB 512 square with repeat/linear mip sampling; local preparation adjusts broad illumination, palette and narrow opposing edge pixels.'
    manifest['limits'][4] = 'Pixel edge continuity does not itself establish visually seamless patterns; 3x3 tiling and normal camera review remain separate.'
    manifest['limits'][3] = 'Tree foliage reuses the original natural-v3 atlas with selective brightness/saturation in oak/birch/pine green pixels; alpha and all non-tree sprites remain exact.'
    for reference in ['source-art/maps/material-refinement-v2/generation.json',
                      'source-art/maps/material-refinement-v2/processed-foliage.json',
                      'source-art/maps/terrain-production-v1/processed-textures.json']:
        if reference not in manifest['additionalProvenance']:
            manifest['additionalProvenance'].append(reference)
    write_json(manifest_path, manifest)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)
    board = Image.new('RGB', (1000, 1100), '#202623')
    draw = ImageDraw.Draw(board)
    draw.text((18, 14), 'PAINTED TERRAIN / MATERIAL REFINEMENT V2', font=font, fill='#E1DDD2')
    for index, key in enumerate(PALETTE):
        x, y = 18 + index % 3 * 328, 54 + index // 3 * 346
        image = Image.open(RUNTIME / (key + '-v2.png'))
        board.paste(image.resize((310, 310), Image.Resampling.LANCZOS), (x, y))
        draw.text((x, y + 314), key, font=font, fill='#E1DDD2')
        tiled = Image.new('RGB', (1536, 1536))
        for z in range(3):
            for col in range(3):
                tiled.paste(image, (col * 512, z * 512))
        tiling_dir = ART / 'tiling'
        tiling_dir.mkdir(exist_ok=True)
        tiled.resize((900, 900), Image.Resampling.LANCZOS).save(tiling_dir / (key + '.jpg'), quality=90)
    board.save(ART / 'materials-preview.jpg', quality=92)
    print(json.dumps({'materials': len(records), 'runtimeBytes': sum(r['runtime']['bytes'] for r in records)}, indent=2))


if __name__ == '__main__':
    main()
