from pathlib import Path
from PIL import Image
import numpy as np
import json, hashlib

SOURCE=Path(__file__).resolve().parent
ROOT=SOURCE.parents[2]
DEST=ROOT/'src/cocos/assets/resources/vfx/production/fire-explosion-v6.png'
source=Image.open(SOURCE/'explosion0003-sheet_300x300.png').convert('RGBA')
atlas=Image.new('RGBA',(1536,1344))
for frame in range(56):
    cell=source.crop((frame%8*300+45,frame//8*300+45,frame%8*300+255,frame//8*300+255))
    a=np.asarray(cell).copy();rgb=a[:,:,:3].astype(float)/255
    hot=np.clip((rgb.min(axis=2)-.74)/.18,0,1)**2
    warm=rgb*np.array([1,.65,.28]);rgb=warm*(1-hot[:,:,None])+rgb*hot[:,:,None]
    a[:,:,:3]=np.uint8(np.clip(rgb*255,0,255))
    # Dark late ash fades without leaving opaque black slabs. Preserve original
    # generated alpha throughout; only suppress nearly black residue at the end.
    attenuation=np.clip(rgb.max(axis=2)/.055,0,1)
    edge=np.minimum(np.arange(210),np.arange(210)[::-1])/6
    attenuation*=np.clip(np.minimum(edge[:,None],edge[None,:]),0,1)
    a[:,:,3]=np.uint8(a[:,:,3]*attenuation)
    cell=Image.fromarray(a).resize((188,188),Image.Resampling.LANCZOS)
    atlas.alpha_composite(cell,(frame%8*192+2,frame//8*192+2))
atlas.save(DEST,optimize=True)
p=SOURCE/'provenance.json';r=json.loads(p.read_text(encoding='utf-8'))
r.update(runtimeBytes=DEST.stat().st_size,runtimeSha256=hashlib.sha256(DEST.read_bytes()).hexdigest(),
         processing='Fixed 210x210 crop per source cell, preserving common centre and native aspect; warm red/orange balance with luminance-gated ivory core; nearly-black ash and 6px edge alpha fade; Lanczos to 188px inside 192px cells with transparent 2px guards; no generative edits.',
         uncompressedTextureBytes=1536*1344*4)
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(DEST.stat().st_size)
