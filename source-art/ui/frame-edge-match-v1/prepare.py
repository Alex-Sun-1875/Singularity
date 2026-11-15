"""Match shared nine-slice straight edges to the untouched approved corners."""
from pathlib import Path
import hashlib
import json
import runpy

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'source-art/ui/double-gold-frame-v6/double-gold-frame-v6.png'
OUTPUT = ROOT / 'src/cocos/assets/resources/ui/quiet-bronze/double-gold-frame-v6.png'
EDGE = 48


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


original = np.array(Image.open(SOURCE).convert('RGBA'))
matched = original.copy()
h, w = original.shape[:2]

# Each row/column follows its two corner tangents. Keep the authored alpha,
# corner pixels, dimensions and source-pixel border widths exactly unchanged.
tx = np.linspace(0, 1, w - 2 * EDGE + 2)[1:-1][None, :, None]
for rows in [slice(0, EDGE), slice(h - EDGE, h)]:
    left = original[rows, EDGE - 1:EDGE, :3].astype(float)
    right = original[rows, w - EDGE:w - EDGE + 1, :3].astype(float)
    matched[rows, EDGE:w - EDGE, :3] = np.rint(left * (1 - tx) + right * tx).astype('uint8')
ty = np.linspace(0, 1, h - 2 * EDGE + 2)[1:-1][:, None, None]
for columns in [slice(0, EDGE), slice(w - EDGE, w)]:
    top = original[EDGE - 1:EDGE, columns, :3].astype(float)
    bottom = original[h - EDGE:h - EDGE + 1, columns, :3].astype(float)
    matched[EDGE:h - EDGE, columns, :3] = np.rint(top * (1 - ty) + bottom * ty).astype('uint8')

assert np.array_equal(original[:, :, 3], matched[:, :, 3])
for y in [0, h - EDGE]:
    for x in [0, w - EDGE]:
        assert np.array_equal(original[y:y + EDGE, x:x + EDGE], matched[y:y + EDGE, x:x + EDGE])
Image.fromarray(matched).save(OUTPUT, optimize=True)
Image.fromarray(matched).save(HERE / 'double-gold-frame-matched.png', optimize=True)

# Use the existing native atlas recipe so Web and TapTap use identical pixels.
recipe = runpy.run_path(str(ROOT / 'src/cocos/tools/build-hud-render-assets.py'))
recipe['frame_pair_atlases']()
atlas_path = OUTPUT.parent / 'gold-frame-panel-atlas-v1.png'
atlas = Image.open(atlas_path).convert('RGBA')
assert atlas.crop((518, 2, 1030, 514)).tobytes() == matched.tobytes()
atlas_manifest_path = atlas_path.with_suffix('.provenance.json')
atlas_manifest = json.loads(atlas_manifest_path.read_text(encoding='utf-8'))
atlas_manifest['visualAcceptance'] = 'Source frame edge correction: source-art/ui/frame-edge-match-v1/art-review.json; Web screenshots recorded separately from TapTap device acceptance.'
atlas_manifest_path.write_text(json.dumps(atlas_manifest, indent=2) + '\n', encoding='utf-8')

def horizontal_peak(image, y, x):
    strip = image[y:y + 18, x:x + 1, :3].astype(float)
    return round(float((strip @ np.array([.2126, .7152, .0722])).max()), 2)

manifest = {
    'date': '2026-11-15',
    'method': 'Local deterministic RGB interpolation between adjacent corner tangents; no generated image.',
    'source': str(SOURCE.relative_to(ROOT).as_posix()),
    'sourceSha256': digest(SOURCE),
    'output': str(OUTPUT.relative_to(ROOT).as_posix()),
    'outputSha256': digest(OUTPUT),
    'atlasSha256': digest(atlas_path),
    'preserved': ['all four 48x48 corner RGBA pixels', 'all alpha values', '512x512 size', '48px slice insets', 'existing asset UUIDs'],
    'topOuterLipPeakLuminance': {
        'cornerLeft': horizontal_peak(original, 0, 47),
        'cornerRight': horizontal_peak(original, 0, 464),
        'middleBefore': horizontal_peak(original, 0, 256),
        'middleAfter': horizontal_peak(matched, 0, 256),
    },
    'atlasFrameMatchesSource': True,
    'artReview': 'Recorded separately in art-review.json',
}
(HERE / 'provenance.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(json.dumps(manifest, ensure_ascii=False))
