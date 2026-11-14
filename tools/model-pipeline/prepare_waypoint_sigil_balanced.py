"""Thicken the original cloud-painted sigil without adding more rune bands."""
from pathlib import Path
import importlib.util
import json
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'source-art/maps/waypoints-balanced-v3'
OUTPUT = ROOT / 'src/cocos/assets/resources/flat2d/waypoints-v1'


def main():
    spec = importlib.util.spec_from_file_location('map_prepare', Path(__file__).with_name('prepare_map_terrain.py'))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    SOURCE.mkdir(parents=True, exist_ok=True)
    previous = Image.open(OUTPUT / 'ancient-sigil.png').convert('RGBA')
    pixels = np.asarray(previous)
    coverage = np.clip((pixels[:, :, 3].astype(float) - 38) / 162, 0, 1)
    coverage = coverage * coverage * (3 - 2 * coverage)
    core = Image.fromarray(np.rint(coverage * 255).astype('uint8'))
    result = Image.new('RGBA', previous.size, (0, 0, 0, 0))
    def layer(rgb, mask, opacity):
        image = Image.new('RGBA', previous.size, (*rgb, 0))
        image.putalpha(mask.point(lambda a: round(a * opacity)))
        result.alpha_composite(image)
    # The same two rings, branching star and sparse eight glyph clusters.
    # Fixed-width dilation gives them weight without generating more symbols.
    layer((126, 76, 226), core.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(4)), .72)
    layer((76, 43, 137), core.filter(ImageFilter.MaxFilter(7)), .78)
    layer((207, 174, 250), core.filter(ImageFilter.MaxFilter(5)), .96)
    layer((246, 230, 255), core.filter(ImageFilter.MaxFilter(3)), .93)
    painted = previous.copy()
    painted.putalpha(Image.fromarray(np.minimum(pixels[:, :, 3], np.asarray(core)).astype('uint8')))
    result.alpha_composite(painted)
    target = OUTPUT / 'ancient-sigil-balanced-v3.png'
    result.save(target)
    helper.texture_meta(target, alpha=True)
    metrics = lambda image: {
        'alphaAbove128Fraction': round(float((np.asarray(image)[:, :, 3] > 128).mean()), 6),
        'meanAlpha': round(float(np.asarray(image)[:, :, 3].mean()), 4),
    }
    record = {
        'method': 'Pillow/NumPy deterministic alpha dilation and layered violet strokes from the original accepted sigil',
        'source': helper.image_record(OUTPUT / 'ancient-sigil.png'), 'runtime': helper.image_record(target),
        'structure': 'Original two rings, central branching star and eight sparse glyph clusters retained; no added rune bands',
        'strokeLayers': {'outlineMaxFilter': 7, 'bodyMaxFilter': 5, 'highlightMaxFilter': 3},
        'halo': {'rgb': [126, 76, 226], 'radius': 4, 'opacity': .72},
        'previousPixelMetrics': metrics(previous), 'newPixelMetrics': metrics(result),
        'newImageGenerationCalls': 0, 'sampler': 'clamp-to-edge, linear, no mip',
        'artAcceptance': 'balanced-sample-and-runtime-review-pending',
    }
    helper.write_json(SOURCE / 'processing.json', record)
    for name, color in [('gray', (105, 107, 102, 255)), ('dark', (30, 33, 31, 255))]:
        preview = Image.new('RGB', (1024, 556), color[:3])
        for index, image in enumerate([previous, result]):
            sample = Image.new('RGBA', image.size, color)
            sample.alpha_composite(image)
            preview.paste(sample.convert('RGB').resize((512, 512), Image.Resampling.LANCZOS), (index * 512, 0))
        draw = ImageDraw.Draw(preview)
        draw.text((18, 526), 'PREVIOUS', fill='white')
        draw.text((530, 526), 'BALANCED: SAME SYMBOLS, BOLDER STROKES', fill='white')
        preview.save(SOURCE / ('comparison-' + name + '.jpg'), quality=92)
    print(json.dumps(record, ensure_ascii=False))


if __name__ == '__main__':
    main()
