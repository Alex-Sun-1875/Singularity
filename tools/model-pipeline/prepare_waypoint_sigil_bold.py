"""Prepare the heavier cloud-edited rune seal; preserve the accepted first version."""
from pathlib import Path
import importlib.util
import json
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'source-art/maps/waypoints-bold-v2'
OUTPUT = ROOT / 'src/cocos/assets/resources/flat2d/waypoints-v1'


def main():
    spec = importlib.util.spec_from_file_location('map_prepare', Path(__file__).with_name('prepare_map_terrain.py'))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    raw = SOURCE / 'raw/ancient-sigil-bold-v2.png'
    pixels = np.asarray(Image.open(raw).convert('RGBA')).copy()
    strength = np.clip((pixels[:, :, 1].astype(float) - 150) / 75, 0, 1)
    strength = strength * strength * (3 - 2 * strength)
    pixels[:, :, 3] = np.rint(pixels[:, :, 3] * strength).astype('uint8')
    alpha = pixels[:, :, 3]
    ys, xs = np.where(alpha > 32)
    bounds = (max(0, int(xs.min()) - 5), max(0, int(ys.min()) - 5),
              min(pixels.shape[1], int(xs.max()) + 6), min(pixels.shape[0], int(ys.max()) + 6))
    ink = Image.fromarray(pixels).crop(bounds)
    ink.thumbnail((896, 896), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    canvas.alpha_composite(ink, ((1024 - ink.width) // 2, (1024 - ink.height) // 2))
    stroke = canvas.getchannel('A')
    contour = Image.new('RGBA', canvas.size, (73, 38, 143, 0))
    contour.putalpha(stroke.filter(ImageFilter.MaxFilter(3)).point(lambda a: round(a * .82)))
    glow = Image.new('RGBA', canvas.size, (122, 67, 232, 0))
    glow.putalpha(stroke.filter(ImageFilter.GaussianBlur(4)).point(lambda a: round(a * .92)))
    result = Image.alpha_composite(Image.alpha_composite(glow, contour), canvas)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / 'ancient-sigil-bold-v2.png'
    result.save(target)
    helper.texture_meta(target, alpha=True)
    previous = Image.open(OUTPUT / 'ancient-sigil.png').convert('RGBA')
    metrics = lambda image: {
        'alphaAbove128Fraction': round(float((np.asarray(image)[:, :, 3] > 128).mean()), 6),
        'meanAlpha': round(float(np.asarray(image)[:, :, 3].mean()), 4),
        'maximumBorderAlpha': int(max(np.asarray(image)[0, :, 3].max(), np.asarray(image)[-1, :, 3].max(),
                                      np.asarray(image)[:, 0, 3].max(), np.asarray(image)[:, -1, 3].max())),
    }
    record = {
        'method': 'Pillow/NumPy deterministic alpha cleanup, proportional padded layout, violet contour and tight halo',
        'raw': helper.image_record(raw), 'runtime': helper.image_record(target),
        'alphaExtraction': 'smoothstep((green - 150) / 75) multiplied by original alpha',
        'cropBounds': list(bounds), 'maximumInkSize': [896, 896],
        'contour': {'rgb': [73, 38, 143], 'maxFilterPixels': 3, 'alphaMultiplier': .82},
        'halo': {'rgb': [122, 67, 232], 'gaussianRadiusPixels': 4, 'alphaMultiplier': .92},
        'previousPixelMetrics': metrics(previous), 'newPixelMetrics': metrics(result),
        'sampler': 'clamp-to-edge, linear, no mip', 'artAcceptance': 'processed-sample-and-runtime-pending',
    }
    helper.write_json(SOURCE / 'processing.json', record)
    for name, color in [('gray', (105, 107, 102, 255)), ('dark', (30, 33, 31, 255))]:
        preview = Image.new('RGB', (1024, 556), color[:3])
        for index, image in enumerate([previous, result]):
            sample = Image.new('RGBA', image.size, color)
            sample.alpha_composite(image)
            preview.paste(sample.convert('RGB').resize((512, 512), Image.Resampling.LANCZOS), (index * 512, 0))
        from PIL import ImageDraw
        ImageDraw.Draw(preview).text((18, 526), 'PREVIOUS', fill='white')
        ImageDraw.Draw(preview).text((530, 526), 'BOLD V2', fill='white')
        preview.save(SOURCE / ('comparison-' + name + '.jpg'), quality=92)
    print(json.dumps(record, ensure_ascii=False))


if __name__ == '__main__':
    main()
