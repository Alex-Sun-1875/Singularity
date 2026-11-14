"""Register cloud hairstyle edits, then restore the approved face and collar pixels."""
from pathlib import Path
import json
import numpy as np
from scipy import ndimage, optimize
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
DEST = Path(__file__).resolve().parents[3] / 'src/cocos/assets/resources/portraits'
base = Image.open(ROOT / 'curly-original.png').convert('RGB')
original = np.asarray(base)
face = Image.new('L', base.size)
ImageDraw.Draw(face).polygon([(174,212),(192,199),(224,199),(245,201),(266,196),(305,199),(327,211),(342,226),(346,257),(338,309),(311,345),(284,368),(258,381),(228,382),(205,371),(183,350),(169,325),(161,296),(159,259),(165,235)], fill=255)
outer = Image.new('L', base.size)
ImageDraw.Draw(outer).polygon([(34,24),(446,24),(466,145),(466,351),(420,399),(350,400),(300,360),(190,370),(145,400),(37,400),(20,320),(25,200)], fill=255)
hair_mask = np.asarray(outer.filter(ImageFilter.GaussianBlur(5)), dtype=np.float32) / 255
protect = np.asarray(face.filter(ImageFilter.GaussianBlur(3)), dtype=np.float32) / 255
hair_mask *= 1 - protect
core = ndimage.binary_erosion(np.asarray(face) == 255, iterations=3)
hair_mask[core] = 0
hair_mask[398:] = 0
Image.fromarray(np.uint8(hair_mask * 255)).save(ROOT / 'hair-edit-mask.png')
records = []
ys, xs = np.nonzero(core)
ys, xs = ys[::3], xs[::3]
gray = lambda rgb: np.asarray(rgb, dtype=np.float32) @ np.array([.299,.587,.114], dtype=np.float32)
target = gray(original)[ys,xs]
target = (target-target.mean())/target.std()
DEST.mkdir(parents=True, exist_ok=True)
base.save(DEST / 'raphael-hair-curly-v1.png')
for style in ['dante', 'nero', 'vergil']:
    generated = np.asarray(Image.open(ROOT / f'{style}-generated.png').convert('RGB').resize(base.size, Image.Resampling.LANCZOS))
    source_gray = gray(generated)
    def loss(p):
        sx, sy, xy, yx, dx, dy = p
        sample = ndimage.map_coordinates(source_gray, [yx*(xs-251)+sy*(ys-251)+251+dy, sx*(xs-251)+xy*(ys-251)+251+dx], order=1, mode='nearest')
        sample = (sample-sample.mean())/sample.std()
        return float(np.mean((sample-target)**2))
    fit = optimize.minimize(loss, [1,1,0,0,0,0], method='Powell', bounds=[(.98,1.02),(.98,1.02),(-.01,.01),(-.01,.01),(-8,8),(-8,8)], options={'maxiter': 100, 'ftol': 1e-7})
    sx, sy, xy, yx, dx, dy = fit.x
    warp = np.array([[sx,xy,251+dx-251*sx-251*xy],[yx,sy,251+dy-251*yx-251*sy]])
    score = 1-fit.fun/2
    if not (.94 < np.linalg.det(warp[:,:2]) < 1.06 and np.max(np.abs(warp[:,2])) < 20):
        raise ValueError(f'Unexpected portrait registration for {style}: {warp}')
    aligned = np.asarray(Image.fromarray(generated).transform(base.size, Image.Transform.AFFINE, tuple(warp.flat), Image.Resampling.BICUBIC))
    alpha = hair_mask[:,:,None]
    composite = np.uint8(np.round(aligned * alpha + original * (1-alpha)))
    image = Image.fromarray(composite)
    image.save(ROOT / f'{style}-composited.png')
    image.save(DEST / f'raphael-hair-{style}-v1.png')
    records.append({'id': style, 'registrationCorrelation': float(score), 'affine': warp.tolist(), 'protectedFaceChangedPixels': int(np.count_nonzero(np.any(composite[core] != original[core], axis=1))), 'collarChangedPixels': int(np.count_nonzero(np.any(composite[398:] != original[398:], axis=2))), 'size': list(image.size)})
(ROOT / 'composition-report.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
sheet = Image.new('RGB', (1004, 1064), (38,32,29))
draw = ImageDraw.Draw(sheet)
for index, style in enumerate(['curly', 'dante', 'nero', 'vergil']):
    x, y = (index % 2)*502, (index // 2)*532
    sheet.paste(Image.open(DEST / f'raphael-hair-{style}-v1.png'), (x,y+30))
    draw.text((x+15,y+8), style, fill=(229,205,155))
sheet.resize((754,799), Image.Resampling.LANCZOS).save(ROOT / 'comparison.jpg', quality=93)
print(json.dumps(records, indent=2))
