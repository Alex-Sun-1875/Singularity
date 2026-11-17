"""Deterministic extraction of the selected jet and reuse of existing fire art."""
from pathlib import Path
import json,uuid,hashlib
from PIL import Image,ImageFilter,ImageDraw
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
DEST=ROOT/'src/cocos/assets/resources/vfx/production'
(HERE/'assets').mkdir(parents=True,exist_ok=True);(HERE/'media').mkdir(exist_ok=True)
reference=Image.open(HERE.parent/'fire-selected-reference-v18/user-selected-effect.jpg').convert('RGB')
def isolate(box,ellipse=False):
 im=reference.crop(box);p=np.asarray(im,dtype=np.float32)/255
 warm=p[:,:,0]-p[:,:,2]
 a=np.clip((warm-.16)/.38,0,1)*np.clip((p[:,:,0]-.59)/.27,0,1)
 if ellipse:
  y,x=np.mgrid[:im.height,:im.width];r=np.sqrt(((x-im.width/2)/(im.width*.49))**2+((y-im.height/2)/(im.height*.48))**2)
  a*=np.clip((1.04-r)/.06,0,1)
 # Remove the neutral ground contribution before recovering flame chroma;
 # keeping the flattened JPEG's G/R ratio turns airy orange strokes yellow.
 rgb=np.empty_like(p);rgb[:,:,0]=1;rgb[:,:,1]=np.clip((p[:,:,1]-p[:,:,2])/np.maximum(p[:,:,0]-p[:,:,2],.01),.28,.88);rgb[:,:,2]=.045
 return Image.fromarray(np.uint8(np.clip(np.dstack([rgb,a]),0,1)*255))
plume=isolate((447,260,548,405))
p=np.asarray(plume).copy();y,x=np.mgrid[:plume.height,:plume.width]
half=3+plume.width*.49*(y/max(1,plume.height-1))**.65
p[:,:,3]=np.uint8(p[:,:,3]*np.clip((half-np.abs(x-plume.width/2))/3,0,1))
p[:,:,3]=np.uint8(p[:,:,3]*np.clip((plume.height-1-y)/(plume.height*.055),0,1))
plume=Image.fromarray(p).resize((256,384),Image.Resampling.LANCZOS)
atlas=Image.new('RGBA',(1024,1536))
for frame in range(16):
 phase=frame*np.pi*2/16;y,x=np.mgrid[:384,:256]
 displacement=np.sin(phase+y*.065)*(1-y/384)**1.5*3.5
 p=np.asarray(plume).copy();sample=np.clip(np.rint(x+displacement).astype(int),0,255)
 p=p[np.arange(384)[:,None],sample]
 p[:,:,3]=np.uint8(p[:,:,3]*(.94+.055*np.sin(phase+y*.025)))
 atlas.paste(Image.fromarray(p),(frame%4*256,frame//4*384))
seal=Image.new('RGBA',(512,512));d=ImageDraw.Draw(seal);ink=(255,161,47,240)
for radius in [231,217]:d.ellipse((256-radius,256-radius,256+radius,256+radius),outline=ink,width=7)
for turn in range(3):
 angle=turn*np.pi*2/3;points=[]
 segments=[[(0,0),(-50,-65),(-180,-58),(-132,-160)],[(-132,-160),(-50,-214),(72,-147),(0,0)]]
 for controls in segments:
  for t in np.linspace(0,1,48):
   p=sum(np.array(c)*w for c,w in zip(controls,[(1-t)**3,3*(1-t)**2*t,3*(1-t)*t*t,t**3]))
   points.append((256+p[0]*np.cos(angle)-p[1]*np.sin(angle),256+p[0]*np.sin(angle)+p[1]*np.cos(angle)))
 d.line(points,fill=ink,width=6,joint='curve')
d.ellipse((246,246,266,266),outline=ink,width=4)
glow=seal.filter(ImageFilter.GaussianBlur(4));glow.putalpha(glow.getchannel('A').point(lambda a:round(a*.35)));seal=Image.alpha_composite(glow,seal)
assets={'fire-ground-jets-v22':atlas,'fire-jet-seal-v22':seal,'fire-meteor-seal-v22':Image.open(HERE.parent/'reference-seals-v3/assets/FIR.png').convert('RGBA')}
for name,im in assets.items():
 im.save(HERE/'assets'/(name+'.png'),optimize=True);im.save(DEST/(name+'.png'),optimize=True)
 meta=DEST/(name+'.png.meta')
 if not meta.exists():
  template=(DEST/'thunder-reference-strip-v1.png.meta').read_text(encoding='utf8');old=json.loads(template)['uuid']
  meta.write_text(template.replace(old,str(uuid.uuid4())).replace('thunder-reference-strip-v1',name),encoding='utf8')
for name in ['fire-pyro-v7','fire-low-rolls-v7','fire-bolt-v9']:
 (DEST/(name+'.png')).write_bytes((HERE.parent/'fire-spells-design-v5/assets'/(name+'.png')).read_bytes())
plume.save(HERE/'assets/selected-plume-extracted.png')
sheet=Image.new('RGB',(768,512),'#6d665e')
sheet.paste(plume,(50,70),plume);seal=assets['fire-jet-seal-v22'].resize((350,170));sheet.paste(seal,(375,265),seal)
sheet.save(HERE/'media/extraction-check.jpg',quality=93)
record={'source':'../fire-selected-reference-v18/user-selected-effect.jpg','method':'Warm emissive alpha extraction with neutral-background chroma removal; preserve selected plume shape. Sixteen small periodic warps animate the plume. Small arrays rebuild the selected simple double ring and three broad curls as deterministic paths, with no JPEG flame contamination on the ground. Existing v5 lifecycle/bolt assets reused. No new generative model.','jetCrop':[447,260,548,405],'generatedImages':False,'assets':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'assets').glob('*.png')}}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False),flush=True)
