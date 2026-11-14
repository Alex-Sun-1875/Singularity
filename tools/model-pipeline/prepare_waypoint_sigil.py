"""Prepare the cloud-painted waypoint texture using existing Pillow/Cocos helpers."""
from pathlib import Path
import importlib.util
import json
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'source-art/maps/waypoints-v1'
OUTPUT = ROOT / 'src/cocos/assets/resources/flat2d/waypoints-v1'


def main():
    spec = importlib.util.spec_from_file_location('map_prepare', Path(__file__).with_name('prepare_map_terrain.py'))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    raw = SOURCE / 'raw/ancient-sigil.png'
    image = Image.open(raw).convert('RGBA')
    pixels = np.asarray(image).copy()
    # Keep the painted luminous strokes while clearing the model's broad
    # lavender veil. Alpha extraction is deterministic; source RGB is retained.
    strength = np.clip((pixels[:, :, 1].astype(float) - 165) / 65, 0, 1)
    strength = strength * strength * (3 - 2 * strength)
    pixels[:, :, 3] = np.rint(pixels[:, :, 3] * strength).astype('uint8')
    ink = Image.fromarray(pixels).resize((1024, 1024), Image.Resampling.LANCZOS)
    glow = Image.new('RGBA', ink.size, (124, 96, 220, 0))
    glow.putalpha(ink.getchannel('A').filter(ImageFilter.GaussianBlur(5)).point(lambda a: round(a * .68)))
    result = Image.alpha_composite(glow, ink)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / 'ancient-sigil.png'
    result.save(target)
    helper.texture_meta(target, alpha=True)
    record = {
        'method': 'Pillow/NumPy deterministic stroke-alpha extraction and restrained violet halo; original preserved',
        'raw': helper.image_record(raw), 'runtime': helper.image_record(target),
        'alphaExtraction': 'smoothstep((green - 165) / 65) multiplied by original alpha',
        'halo': {'rgb': [124, 96, 220], 'gaussianRadiusPixels': 5, 'alphaMultiplier': .68},
        'sampler': 'clamp-to-edge, linear, no mip',
        'artAcceptance': 'processed-sample-review-pending-runtime',
    }
    helper.write_json(SOURCE / 'processing.json', record)
    for name, color in [('gray', (105, 107, 102, 255)), ('dark', (30, 33, 31, 255))]:
        preview = Image.new('RGBA', result.size, color)
        preview.alpha_composite(result)
        preview.convert('RGB').resize((512, 512), Image.Resampling.LANCZOS).save(SOURCE / ('sigil-' + name + '-preview.jpg'), quality=91)
    print(json.dumps(record, ensure_ascii=False))


if __name__ == '__main__':
    main()
