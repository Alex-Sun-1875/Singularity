"""Deterministic textile/strand reuse from the accepted 2D design pixels."""
from pathlib import Path
from PIL import Image,ImageOps
import json,hashlib,numpy as np
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];OUT=BASE/'references';OUT.mkdir(exist_ok=True)
source=ROOT/'source-art/characters/2d-concepts/attack-identity-v5/masters';rows=[];panels=[]
for direction,rect,patch in [('down',(175,180,337,425),(175,329,235,413)),('up',(172,158,338,402),(280,296,338,396))]:
    path=source/('neutral-'+direction+'.png');im=Image.open(path).convert('RGBA');a=np.array(im);x0,y0,x1,y1=patch
    # Remove the source's painted bag from the cloth map: a real bag is fitted separately.
    a[y0:y1,x0:x1]=a[y0:y1,512-x1:512-x0][:,::-1];im=Image.fromarray(a).crop(rect)
    background=Image.new('RGBA',im.size,(72,35,43,255));background.alpha_composite(im)
    rgb=np.asarray(background.convert('RGB')).astype(float);r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    # Keep the 2D leaf embroidery while excluding painted skin, lighting and sleeves.
    gold=(r>80)&(g/r.clip(1)>.61)&(g/r.clip(1)<.93)&(b/g.clip(1)<.77)
    from scipy.ndimage import gaussian_filter
    gold=gaussian_filter(gold.astype(float),.55);gold=np.clip((gold-.17)/.65,0,1)
    color=np.array([65,28,41])[None,None,:]*(1-gold[:,:,None])+np.array([184,151,88])[None,None,:]*gold[:,:,None]
    panels.append(Image.fromarray(np.uint8(color)).resize((512,1024),Image.Resampling.LANCZOS))
    rows.append({'source':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'crop':rect,'bagPatchReusedFromOppositeCloth':patch})
atlas=Image.new('RGB',(1024,1024));atlas.paste(panels[0],(0,0));atlas.paste(panels[1],(512,0));atlas.save(OUT/'coat-design-atlas.png')
head=ROOT/'source-art/characters/2d-concepts/identity-reference-v1/head-identity-master.png';im=Image.open(head).convert('RGB').crop((176,695,462,904));detail=ImageOps.autocontrast(ImageOps.grayscale(im),cutoff=2).resize((512,512),Image.Resampling.LANCZOS);Image.merge('RGB',(detail,detail,detail)).save(OUT/'silver-curl-detail.png')
rows.append({'source':head.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(head.read_bytes()).hexdigest(),'crop':[176,695,462,904],'operation':'Back-hair grayscale micro-detail only; actual hair shape is 3D library geometry'})
(BASE/'design-provenance.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8');print('Prepared existing 2D cloth and hair detail')
