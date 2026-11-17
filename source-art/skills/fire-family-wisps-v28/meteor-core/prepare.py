"""Derive a warm stone core from its UV-matching natural repository albedo.

Only deterministic colour remapping, resizing and comparison layout; no image
generation, new geometry, simulated gameplay, or changes to the selected flame.
"""
from pathlib import Path
import hashlib
import json
import uuid

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRODUCTION = ROOT / 'src/cocos/assets/resources/vfx/production'
NATURAL = ROOT / 'src/cocos/assets/resources/environment/textures/rocks-0-color.png'
RED = PRODUCTION / 'meteor-rock-v9.png'
OUTPUT = PRODUCTION / 'meteor-rock-warm-v28.png'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    natural = Image.open(NATURAL).convert('RGB')
    source = np.asarray(natural, dtype=np.float32) / 255
    gray = source @ np.array([.2126, .7152, .0722], dtype=np.float32)
    # The mesh UVs occupy the original atlas' first upper-left tile. Preserve
    # the complete atlas/UV layout instead of fitting a different rock photo.
    active = gray[:natural.height // 3, :natural.width // 3]
    low, high = np.percentile(active, [1, 99])
    level = np.clip((gray - low) / (high - low), 0, 1)
    stops = np.array([0, .18, .48, .80, 1], dtype=np.float32)
    palette = np.array([[31, 25, 20], [65, 47, 29], [119, 85, 42],
                        [181, 135, 67], [218, 173, 99]], dtype=np.float32)
    result = np.stack([np.interp(level, stops, palette[:, channel])
                       for channel in range(3)], axis=-1)
    # Retain tiny real colour variations without retaining the old green moss
    # or burnt-red bake. Dark cracks remain dark rather than becoming glow.
    chroma = source - gray[..., None]
    result += np.clip(chroma * 255, -18, 18) * .12
    # Leave the original unused black atlas region empty.
    result[gray < .003] = 0
    warm = Image.fromarray(np.uint8(np.clip(result, 0, 255))).resize(
        (512, 512), Image.Resampling.LANCZOS)
    warm.save(OUTPUT, optimize=True)

    meta = json.loads(RED.with_suffix('.png.meta').read_text(encoding='utf-8'))
    identity = str(uuid.uuid5(uuid.NAMESPACE_URL,
                            'singularity:vfx/production/meteor-rock-warm-v28.png'))
    meta['uuid'] = identity
    texture = meta['subMetas']['6c48a']
    texture['uuid'] = identity + '@6c48a'
    texture['displayName'] = OUTPUT.stem
    texture['userData']['imageUuidOrDatabaseUri'] = identity
    texture['userData']['wrapModeS'] = 'clamp-to-edge'
    texture['userData']['wrapModeT'] = 'clamp-to-edge'
    meta['userData']['redirect'] = identity + '@6c48a'
    OUTPUT.with_suffix('.png.meta').write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    board = Image.new('RGB', (960, 390), '#272d2b')
    draw = ImageDraw.Draw(board)
    font_path = Path('C:/Windows/Fonts/msyh.ttc')
    font = ImageFont.truetype(str(font_path), 21)
    small = ImageFont.truetype(str(font_path), 16)
    panels = [('UV匹配的原始岩石', natural), ('旧版染红岩核', Image.open(RED)),
              ('暗金橙热岩 · v28', warm)]
    for index, (title, image) in enumerate(panels):
        x = 20 + index * 320
        draw.text((x, 16), title, fill='#eed5ac', font=font)
        crop = image.crop((0, 0, round(image.width / 3),
                          round(image.height / 3))).resize(
                              (280, 280), Image.Resampling.LANCZOS)
        board.paste(crop, (x, 56))
    draw.text((20, 354), '贴图对照；保留原UV、岩纹与暗裂纹。实际Cocos材质画面另行验收。',
              fill='#d0c2ae', font=small)
    sample = HERE / 'texture-comparison.png'
    board.save(sample, optimize=True)

    provenance = {
        'method': 'deterministic Pillow/NumPy colour remapping and resizing; no generation',
        'source': {'path': str(NATURAL.relative_to(ROOT)).replace('\\', '/'),
                   'sha256': sha(NATURAL)},
        'mesh': {'path': 'src/cocos/assets/resources/vfx/production/meteor-rock-v9.json',
                 'unchanged': True, 'bounds': [-.5, .5],
                 'uvRange': [[.000207, .001112], [.313496, .332966]]},
        'license': 'Existing CC0 Poly Haven rock_moss_set_01; see combat-design-v9/provenance.json',
        'colour': {'sourceLuminancePercentiles': [float(low), float(high)],
                   'stops': stops.tolist(), 'srgbPalette': palette.tolist(),
                   'retainedChroma': .12},
        'outputs': [{'path': str(OUTPUT.relative_to(ROOT)).replace('\\', '/'),
                     'sha256': sha(OUTPUT), 'size': [512, 512],
                     'bytes': OUTPUT.stat().st_size},
                    {'path': 'texture-comparison.png', 'sha256': sha(sample)}],
        'material': {'effect': 'builtin-standard', 'mainColor': [255, 255, 255, 255],
                     'albedoScale': [1, 1, 1], 'roughness': .94,
                     'metallic': 0, 'specularIntensity': .12,
                     'emissiveScale': [.18, .16, .12]},
        'review': {'textureComparison': 'reviewed locally',
                   'actualCocosCapture': 'pending parent build and capture',
                   'userArtAcceptance': 'pending'},
    }
    (HERE / 'provenance.json').write_text(json.dumps(
        provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'texture': str(OUTPUT), 'sample': str(sample),
                      'sha256': sha(OUTPUT), 'bytes': OUTPUT.stat().st_size}))


if __name__ == '__main__':
    main()
