"""Bake overlapping moving fire veins into the existing 16-frame field atlas.

Deterministic premultiplied compositing of the approved v30 pixels; no generation.
The runtime retains its original texture size, sampling count and connected mesh.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / 'fire-distinct-runtime-v30/assets/fire-field-flow-v30.png'
DEST = HERE / 'assets'
DEST.mkdir(exist_ok=True)
source = np.asarray(Image.open(SOURCE).convert('RGBA'), dtype=np.float32) / 255
height, width = source.shape[:2]
cw, ch = width // 4, height // 4
output = np.zeros_like(source)
y = np.arange(ch)
edge = np.clip(np.minimum(y, ch - 1 - y) / 5, 0, 1)
edge = (edge * edge * (3 - 2 * edge))[:, None, None]
for index in range(16):
    row, col = divmod(index, 4)
    frame = source[row * ch:(row + 1) * ch, col * cw:(col + 1) * cw]
    alpha = frame[..., 3:4]
    base = frame[..., :3] * alpha
    # Offset the same moving veins to occupy their neighbours' gaps. Neither
    # layer reverses U, changes phase, adds a separate card or introduces glow.
    for offset, opacity in [(91, .72), (-67, .42)]:
        layer = np.roll(frame, offset, axis=1)
        layer_alpha = layer[..., 3:4] * opacity * edge
        # Keep the original bright veins in front of the added underlayers.
        base = base + layer[..., :3] * layer_alpha * (1 - alpha)
        alpha = alpha + layer_alpha * (1 - alpha)
    color = np.divide(base, alpha, out=np.zeros_like(base), where=alpha > 1e-6)
    result = np.concatenate([color, alpha], axis=2)
    # v30 is periodic in U; preserve the atlas cell's matching seam pixels.
    seam = (result[:, 0] + result[:, -1]) * .5
    result[:, 0] = seam
    result[:, -1] = seam
    output[row * ch:(row + 1) * ch, col * cw:(col + 1) * cw] = result

output = np.round(np.clip(output, 0, 1) * 255).astype(np.uint8)
candidate = DEST / 'fire-field-flow-v38.png'
Image.fromarray(output).save(candidate, optimize=True)
Image.open(SOURCE).crop((0, 0, cw, ch)).save(DEST / 'frame-before.png')
Image.fromarray(output[:ch, :cw]).save(DEST / 'frame-after.png')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
record = {
    'operation': 'deterministic premultiplied underlayer compositing',
    'source': str(SOURCE.relative_to(ROOT)).replace('\\', '/'),
    'sourceSha256': sha(SOURCE), 'candidateSha256': sha(candidate),
    'newGeneration': False, 'layers': [{'offsetPixelsU': 91, 'opacity': .72}, {'offsetPixelsU': -67, 'opacity': .42}],
    'atlasPixels': [width, height], 'frames': 16,
    'runtimeBinding': 'src/cocos/assets/resources/vfx/production/fire-field-flow-v30.png',
    'textureSamplesPerFragment': 2, 'originalFrontVeinsPreserved': True,
    'artStatus': 'candidate; native scene capture and user review recorded separately',
}
(DEST / 'provenance.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, ensure_ascii=False))
