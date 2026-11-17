from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageFilter
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
(HERE/'assets').mkdir(parents=True,exist_ok=True)
source=Image.open(ROOT/'source-art/skills/fire-selected-reference-v18/user-selected-effect.jpg').convert('RGB')
box=(425,222,570,467);crop=source.crop(box);c=np.asarray(crop,dtype=float)/255
y,x=np.mgrid[box[1]:box[3],box[0]:box[2]];r,g,b=c.transpose(2,0,1)
warm=(r-b>55/255)&(g-b>27/255)&(r>160/255)
actor=(x<454)&(y>350)
unknown=np.asarray(Image.fromarray(np.uint8(warm|actor)*255).filter(ImageFilter.MaxFilter(5)))>0
background=c.copy();known=~unknown
for _ in range(250):
 if known.all():break
 total=np.zeros_like(c);count=np.zeros(known.shape)
 for dy,dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
  valid=np.roll(known,(dy,dx),(0,1));total+=np.roll(background,(dy,dx),(0,1))*valid[:,:,None];count+=valid
 new=(~known)&(count>0);background[new]=total[new]/count[new,None];known[new]=True
positive=np.maximum(c-background,0)/np.maximum(1-background,1/255)
negative=np.maximum(background-c,0)/np.maximum(background,1/255)
alpha=np.clip(np.maximum(positive,negative).max(axis=2),0,1)
soft=np.asarray(Image.fromarray(np.uint8(warm)*255).filter(ImageFilter.GaussianBlur(.6)),dtype=float)/255
# The actor is excluded while estimating stone, but glowing ring pixels crossing
# that region must remain. Suppress only the actual dark staff/clothing pixels.
soft[actor&(r<.72)&(g<.52)]=0
premul=np.clip(c-background*(1-alpha[:,:,None]),0,alpha[:,:,None])*soft[:,:,None]
alpha*=soft;fg=np.clip(premul/np.maximum(alpha[:,:,None],1e-6),0,1)
rgba=np.dstack([fg,alpha]);Image.fromarray(np.uint8(rgba*255)).save(HERE/'assets/reference-light-matte.png')
Image.fromarray(np.uint8(background*255)).save(HERE/'assets/estimated-reference-background.png')
np.savez(HERE/'assets/reference-matte.npz',fg=fg,alpha=alpha,premul=premul,background=background,original=c,box=box)
fire=(y<395)&(y>250)&(x>450)&(x<548)&(alpha>.10)
current=np.asarray(Image.open(ROOT/'source-art/skills/fire-jet-native-sequence-v24/assets/reference-flame-registered.png').convert('RGBA'),dtype=float)/255
live=current[:,:,3]>.10
def stats(rgb,alpha,mask):
 v=rgb[mask];a=alpha[mask];ratio=v[:,1:]/np.maximum(v[:,0,None],1e-5)
 return {'pixels':int(mask.sum()),'rgbQuantiles':np.quantile(v,[.1,.5,.9],axis=0).tolist(),'greenBlueRatio':np.quantile(ratio,[.1,.5,.9],axis=0).tolist(),'alphaQuantiles':np.quantile(a,[.1,.5,.9]).tolist(),'meanAlpha':float(a.mean())}
out={'referenceFire':stats(fg,alpha,fire),'currentFlame':stats(current[:,:,:3],current[:,:,3],live)}
(HERE/'analysis.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
