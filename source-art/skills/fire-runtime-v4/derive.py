"""Deterministic RGBA extraction only; generation is recorded separately."""
from pathlib import Path
import hashlib, json, uuid
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
DEST = ROOT / 'src/cocos/assets/resources/vfx/production/fire-v4'
DEST.mkdir(parents=True, exist_ok=True)
atlas = Image.open(SOURCE / 'generated-atlas.png').convert('RGBA')
template = json.loads((DEST.parent / 'fire-flames-v3/phase1.png.meta').read_text())
report = []
for row, kind in enumerate(('projectile', 'blast', 'wall')):
    for frame in range(4):
        cell = atlas.crop((frame*atlas.width//4, row*atlas.height//3,
                           (frame+1)*atlas.width//4, (row+1)*atlas.height//3))
        a = np.asarray(cell).copy()
        if row == 0:
            # Match the hot head, not the varying tail silhouette.
            hot = (a[:,:,0] > 245) & (a[:,:,1] > 230) & (a[:,:,2] > 165) & (a[:,:,3] > 160)
            yy, xx = np.where(hot)
            anchor = (float(np.median(xx)), float(np.median(yy)))
            size, scale = 256, .88*256/cell.width
            target = (.76*size, .50*size)
        else:
            # Remove generator's isolated sparks underneath the flame baseline.
            baseline = round(cell.height*(.915 if row == 1 else .835))
            fade = np.clip((baseline+2-np.arange(cell.height))/8, 0, 1)
            a[:,:,3] = (a[:,:,3]*fade[:,None]).astype('uint8')
            anchor = (cell.width/2, baseline)
            size, scale = (384 if row == 1 else 256), .92*(384 if row == 1 else 256)/cell.width
            target = (.5*size, .90*size)
        # Preserve generated alpha; erase RGB in fully transparent texels.
        a[a[:,:,3] == 0] = 0
        cell = Image.fromarray(a).resize((round(cell.width*scale), round(cell.height*scale)), Image.Resampling.LANCZOS)
        output = Image.new('RGBA', (size,size))
        output.alpha_composite(cell, (round(target[0]-anchor[0]*scale), round(target[1]-anchor[1]*scale)))
        path = DEST / f'{kind}{frame}.png'
        output.save(path, optimize=True)
        meta_path = path.with_suffix('.png.meta')
        if not meta_path.exists():
            data = json.loads(json.dumps(template)); old = data['uuid']; new = str(uuid.uuid4())
            data = json.loads(json.dumps(data).replace(old,new).replace('phase1',path.stem))
            data['subMetas']['6c48a']['userData'].update(wrapModeS='clamp-to-edge',wrapModeT='clamp-to-edge')
            meta_path.write_text(json.dumps(data,indent=2)+'\n')
        report.append(dict(file=str(path.relative_to(ROOT)).replace('\\','/'),size=output.size,bytes=path.stat().st_size,
                           sha256=hashlib.sha256(path.read_bytes()).hexdigest(),anchor=target))
directory_meta = DEST.with_suffix('.meta')
if not directory_meta.exists():
    directory_meta.write_text(json.dumps(dict(ver='1.2.0',importer='directory',imported=True,uuid=str(uuid.uuid4()),files=[],subMetas={},userData={}),indent=2)+'\n')
(SOURCE/'processing.json').write_text(json.dumps(dict(sourceSize=atlas.size,method='Pillow/Numpy deterministic crop, anchor alignment, baseline fade, Lanczos resize; generated alpha preserved',files=report,totalPngBytes=sum(r['bytes'] for r in report)),indent=2)+'\n')
print(json.dumps(dict(files=len(report),totalPngBytes=sum(r['bytes'] for r in report))))
