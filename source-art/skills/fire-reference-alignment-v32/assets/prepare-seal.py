"""Sharpen the same selected v29 engraving; complete its hidden back segment
from the opposite visible repeat. Do not change the real circle or its radius.
"""
from pathlib import Path
import json,uuid,hashlib
import numpy as np
from PIL import Image,ImageFilter
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];RES=ROOT/'src/cocos/assets/resources/vfx/production'
source=RES/'fire-meteor-seal-v30.png'
a=np.asarray(Image.open(source).convert('RGBA'),dtype=float)/255
y,x=np.mgrid[:512,:512];nx=(x-255.5)/231;ny=(y-255.5)/231
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
hidden=1-smooth((np.hypot((nx+.01)/.43,(ny+.77)/.43)-.72)/.38)
back=a[::-1].copy();extra=np.maximum(0,back[...,3]*hidden*.93-a[...,3])
weight=extra/np.maximum(.001,a[...,3]+extra)
a[...,:3]=a[...,:3]*(1-weight[...,None])+back[...,:3]*weight[...,None]
a[...,3]+=extra
pma=a.copy();pma[...,:3]*=pma[...,3,None]
up=np.stack([np.asarray(Image.fromarray(np.float32(pma[...,i]),'F').resize((1024,1024),Image.Resampling.LANCZOS)) for i in range(4)],axis=-1)
alpha=Image.fromarray(np.uint8(np.clip(up[...,3],0,1)*255)).filter(ImageFilter.UnsharpMask(radius=1.15,percent=135,threshold=2))
rgb=up[...,:3]/np.maximum(.001,up[...,3,None])
out=Image.fromarray(np.uint8(np.clip(rgb,0,1)*255),'RGB').convert('RGBA');out.putalpha(alpha)
name='fire-meteor-seal-v32';target=RES/(name+'.png');out.save(target,optimize=True)
meta=json.loads(source.with_suffix('.png.meta').read_text(encoding='utf8'));old=meta['uuid'];identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/'+name))
target.with_suffix('.png.meta').write_text(json.dumps(meta,ensure_ascii=False,indent=2).replace(old,identity).replace('fire-meteor-seal-v30',name)+'\n',encoding='utf8',newline='\n')
record={'source':str(source.relative_to(ROOT)),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'method':'Existing reference engraving preserved; source-occluded rear segment completed only from the opposite visible repeated curve; premultiplied 2x resample and alpha unsharp. No new motifs, colour shift, circle squash or radius change.','size':[1024,1024],'visibleDiameterFraction':460/512,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'nativeReview':'pending'}
(HERE/'seal-provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(record))
