"""Read-only deterministic texture audit; these swatches are not game captures."""
from pathlib import Path
import hashlib, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RES = ROOT / 'src/cocos/assets/resources/vfx/production'
HERE.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 18)
small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 14)
specs = [('fire-pyro-v7', 4, 4, 7), ('fire-low-rolls-v7', 4, 8, 7),
         ('fire-bolt-v9', 4, 1, 2), ('fire-ground-jets-v27', 8, 4, 10)]
sheet = Image.new('RGB', (1100, 4 * 280 + 65), '#1d2420')
d = ImageDraw.Draw(sheet)
d.text((20, 16), '素材局部审查 / 仅确定性贴图合成，非实际游戏效果', fill='#eac187', font=font)
metrics = []
for row, (name, cols, rows, frame) in enumerate(specs):
    path = RES / (name + '.png')
    atlas = Image.open(path).convert('RGBA')
    w, h = atlas.width // cols, atlas.height // rows
    cell = atlas.crop((frame % cols * w, frame // cols * h,
                      (frame % cols + 1) * w, (frame // cols + 1) * h))
    p = np.asarray(cell, dtype=float) / 255
    a = p[:, :, 3]
    occupied = a > .01
    hot = np.minimum.reduce(p[:, :, :3], axis=2) > .72
    metrics.append(dict(name=name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        atlasSize=atlas.size, cellSize=cell.size, selectedFrame=frame,
        rgbaMemoryBytes=atlas.width * atlas.height * 4,
        meanOccupiedAlpha=float(a[occupied].mean()),
        opaqueFractionOfOccupied=float((a[occupied] > .75).mean()),
        whiteHotFractionOfOccupied=float(hot[occupied].mean())))
    top = 65 + row * 280
    d.text((20, top + 3), f'{name} / frame {frame}', fill='#eac187', font=font)
    d.text((20, top + 35), f'{w}×{h}; alpha>0.75: {metrics[-1]["opaqueFractionOfOccupied"]:.1%}', fill='#d6d3c7', font=small)
    cell.thumbnail((260, 225), Image.Resampling.LANCZOS)
    for col, gain in enumerate([.55, .80, 1.0]):
        dst = np.full((230, 265, 3), [40, 49, 44], dtype=float) / 255
        q = np.asarray(cell, dtype=float) / 255
        alpha = q[:, :, 3, None] * gain
        # v27's accepted gentle-light compositing, old rows use source-over.
        lift, absorption = (1.10, .90) if name.endswith('v27') else (1., 1.)
        left, y = (265-cell.width)//2, 230-cell.height
        dst[y:y+cell.height, left:left+cell.width] = q[:, :, :3]*alpha*lift + dst[y:y+cell.height, left:left+cell.width]*(1-alpha*absorption)
        sheet.paste(Image.fromarray(np.uint8(np.clip(dst, 0, 1)*255)), (290+col*270, top+35))
        d.text((305+col*270, top+7), f'opacity × {gain:.2f}', fill='#c7bd9c', font=small)
sheet.save(HERE/'texture-compositing-review.jpg', quality=94, subsampling=0)
(HERE/'metrics.json').write_text(json.dumps({'type':'Read-only texture metrics; not native visual validation', 'textures': metrics}, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps(metrics, ensure_ascii=False))
