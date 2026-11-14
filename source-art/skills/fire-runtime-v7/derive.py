"""Deterministic extraction. Pyro artwork: cloud image_gen; core: CC0 dirkwybe."""
from pathlib import Path
from PIL import Image
import numpy as np
import json, hashlib

SOURCE=Path(__file__).resolve().parent
ROOT=SOURCE.parents[2]
DEST=ROOT/'src/cocos/assets/resources/vfx/production'
image=Image.open(SOURCE/'generated-atlas.png').convert('RGBA')
assert image.size==(1536,1024)
a=np.asarray(image).copy();alpha=a[:,:,3].astype(float)
# User revision: no black smoke. Retain luminous orange/red combustion and the
# tiny ivory core; discard neutral soot and dark ash before deriving low rolls.
rgb=a[:,:,:3].astype(float)/255
value=rgb.max(axis=2);minimum=rgb.min(axis=2)
saturation=(value-minimum)/np.maximum(value,.001)
def eased(v):
    v=np.clip(v,0,1)
    return v*v*(3-2*v)
fire=eased((saturation-.50)/.28)*eased((value-.32)/.24)
ivory=eased((minimum-.68)/.18)*eased((value-.80)/.15)
smoke_free=np.maximum(fire,ivory)
smoke_free[(value<.30)|((saturation<.42)&(minimum<.68))]=0
# The selector removes soot; it is not an extra transparency layer over flame.
# Restore dense coverage to confidently selected fire while keeping the rejected
# neutral/dark pixels at exactly zero and feathering only the uncertain edges.
smoke_free=eased((smoke_free-.04)/.40)
alpha*=smoke_free
for row in range(4):
    for col in range(4):
        edge=np.minimum(np.arange(384),np.arange(384)[::-1])/3
        top=np.minimum(np.arange(256),np.arange(256)[::-1])/3
        floor=np.clip((248-np.arange(256))/8,0,1)
        alpha[row*256:(row+1)*256,col*384:(col+1)*384]*=np.clip(np.minimum(edge[None,:],top[:,None]),0,1)*floor[:,None]
a[:,:,3]=np.uint8(alpha);a[a[:,:,3]==0]=0
main=Image.fromarray(a);main.save(DEST/'fire-pyro-v7.png',optimize=True)

low=Image.new('RGBA',(512,768))
for side in range(2):
    for frame in range(16):
        u=.03 if side==0 else .53
        cell=main.crop((round((frame%4+u)*384),round((frame//4+.48)*256),round((frame%4+u+.44)*384),round((frame//4+.94)*256)))
        a=np.asarray(cell).copy();h,w=a.shape[:2];x=np.minimum(np.arange(w),np.arange(w)[::-1]);y=np.arange(h)
        mask=np.clip(x/(w*.18),0,1)[None,:]*np.clip(y/(h*.23),0,1)[:,None]*np.clip((h-1-y)/(h*.09),0,1)[:,None]
        mask=mask*mask*(3-2*mask);a[:,:,3]=np.uint8(a[:,:,3]*mask);a[a[:,:,3]==0]=0
        cell=Image.fromarray(a);cell.thumbnail((124,87),Image.Resampling.LANCZOS);index=frame+side*16
        low.alpha_composite(cell,(index%4*128+(128-cell.width)//2,index//4*96+90-cell.height))
low.save(DEST/'fire-low-rolls-v7.png',optimize=True)

original=Image.open(SOURCE.parent/'fire-runtime-v6/explosion0003-sheet_300x300.png').convert('RGBA')
core=Image.new('RGBA',(512,128))
for i,frame in enumerate([0,2,4,7]):
    cell=original.crop((frame%8*300,frame//8*300,frame%8*300+300,frame//8*300+300));a=np.asarray(cell)
    y,x=np.where((a[:,:,3]>30)&(a[:,:,:3].max(axis=2)>40))
    cell=cell.crop((max(0,x.min()-5),max(0,y.min()-5),min(300,x.max()+6),min(300,y.max()+6)))
    cell.thumbnail((112,112),Image.Resampling.LANCZOS);core.alpha_composite(cell,(i*128+(128-cell.width)//2,(128-cell.height)//2))
a=np.asarray(core).copy();yy,xx=np.mgrid[:128,:128];radius=np.sqrt((xx-63.5)**2+(yy-63.5)**2)/64
hot=np.clip((.42-radius)/.22,0,1);hot=hot*hot*(3-2*hot)
for i in range(4):
    rgb=a[:,i*128:(i+1)*128,:3].astype(float);warm=rgb*np.array([1,.56,.14])
    a[:,i*128:(i+1)*128,:3]=np.uint8(warm*(1-hot[:,:,None])+rgb*hot[:,:,None])
Image.fromarray(a).save(DEST/'fire-core-v7.png',optimize=True)
files=[]
for name in ['fire-pyro-v7','fire-low-rolls-v7','fire-core-v7']:
    p=DEST/(name+'.png');im=Image.open(p)
    files.append(dict(file=str(p.relative_to(ROOT)).replace('\\','/'),size=im.size,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),uncompressedBytes=im.width*im.height*4))
(SOURCE/'processing.json').write_text(json.dumps(dict(method='Pillow/Numpy deterministic soot/ash alpha removal, dense fire/ivory coverage, edge masks, crop, anchor alignment, radial colour balance and Lanczos resize. No generative edits.',revision='No black smoke; selected orange/red flame has dense alpha coverage instead of inheriting the soft soot-selection weight. Only uncertain edges are feathered.',files=files,totalPngBytes=sum(f['bytes'] for f in files),uncompressedBytes=sum(f['uncompressedBytes'] for f in files)),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(files=len(files),pngBytes=sum(f['bytes'] for f in files))))
