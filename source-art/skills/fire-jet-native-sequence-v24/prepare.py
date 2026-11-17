"""Approved design layers only: register RGBA, then animate a pinned flow field."""
from pathlib import Path
import json,hashlib,uuid
from PIL import Image,ImageFilter
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];DEST=ROOT/'src/cocos/assets/resources/vfx/production'
(HERE/'assets').mkdir(exist_ok=True);(HERE/'media').mkdir(exist_ok=True)
raw=Image.open(HERE/'reference-flame-layer-01.png').convert('RGBA');p=np.array(raw);a=p[:,:,3]
ys,xs=np.where(a>64);box=(xs.min(),ys.min(),xs.max()+1,ys.max()+1);im=raw.crop(box)
scale=min(216/im.width,330/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
base=Image.new('RGBA',(256,384));base.paste(im,(round(128-im.width/2),352-im.height));q=np.array(base).astype(float)/255
q[:,:,3]=np.clip((q[:,:,3]-5/255)/(1-5/255),0,1)
base=Image.fromarray(np.uint8(q*255));base.save(HERE/'assets/reference-flame-registered.png')
prem=q.copy();prem[:,:,:3]*=prem[:,:,3,None]
yy,xx=np.mgrid[:384,:256];lift=np.clip((352-yy)/330,0,1);pin=np.sin(np.pi*lift)**2
atlas=Image.new('RGBA',(1024,1536))
for frame in range(16):
 phase=frame*np.pi*2/16
 dx=(np.sin(phase+yy*.055)-np.sin(yy*.055))*7*pin
 dy=(np.sin(phase+yy*.045+xx*.012)-np.sin(yy*.045+xx*.012))*8*pin
 sx=np.clip(xx+dx,0,254.999);sy=np.clip(yy+dy,0,382.999);x0=sx.astype(int);y0=sy.astype(int);tx=(sx-x0)[:,:,None];ty=(sy-y0)[:,:,None]
 f=prem[y0,x0]*(1-tx)*(1-ty)+prem[y0,x0+1]*tx*(1-ty)+prem[y0+1,x0]*(1-tx)*ty+prem[y0+1,x0+1]*tx*ty
 f[:,:,:3]/=np.maximum(f[:,:,3,None],.0001)
 # Small rising brightness changes add flow while retaining the approved outline.
 f[:,:,3]*=(.94+.06*np.cos(phase+yy*.065))*np.clip(np.minimum.reduce([xx,255-xx,yy,383-yy])/10,0,1)
 rgba=Image.fromarray(np.uint8(np.clip(f,0,1)*255));rgba.save(HERE/'assets'/f'frame-{frame:02}.png');atlas.paste(rgba,(frame%4*256,frame//4*384))

# Keep the reconstructed reference paths themselves. Extract their luminous
# cores rather than drawing a different geometric motif over the reference.
sigil=Image.open(HERE/'reference-seal-layer-01.png').convert('RGBA');s=np.asarray(sigil).astype(float)/255
core=np.clip((s[:,:,1]-.90)/.08,0,1)**.8*np.clip((s[:,:,3]-.05)/.15,0,1)
core=np.clip((core-.04)/.96,0,1);mask=Image.fromarray(np.uint8(core*255)).filter(ImageFilter.MedianFilter(3));bbox=mask.point(lambda a:255 if a>100 else 0).getbbox()
if not bbox:raise ValueError('Missing seal strokes')
cx=(bbox[0]+bbox[2])/2;cy=(bbox[1]+bbox[3])/2;factor=462/max(bbox[2]-bbox[0],bbox[3]-bbox[1]);newsize=(round(sigil.width*factor),round(sigil.height*factor))
ink=Image.new('RGBA',sigil.size,(255,209,100,0));ink.putalpha(mask);ink=ink.resize(newsize,Image.Resampling.LANCZOS)
seal=Image.new('RGBA',(512,512));seal.paste(ink,(round(256-cx*factor),round(256-cy*factor)))
stroke=seal.getchannel('A').filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(.5))
# Alpha expansion needs coloured RGB underneath the expanded pixels as well.
# Reusing zero RGB from transparent resampling creates dark broken outlines.
seal=Image.new('RGBA',seal.size,(255,209,100,0));seal.putalpha(stroke)
halo=Image.new('RGBA',seal.size)
for radius,gain in [(13,.32),(4,.65)]:
 glow=Image.new('RGBA',seal.size,(255,117,24,0));glow.putalpha(seal.getchannel('A').filter(ImageFilter.GaussianBlur(radius)).point(lambda a:round(a*gain)));halo=Image.alpha_composite(halo,glow)
seal=Image.alpha_composite(halo,seal)
ny,nx=np.mgrid[:128,:128];noise=np.ones((128,128,4),dtype=np.uint8)*255;rng=np.random.default_rng(24017)
for channel in range(3):
 field=np.zeros((128,128))
 for frequency,gain in [(1,1),(2,.55),(4,.30),(8,.12)]:
  for _ in range(3):
   kx=int(rng.integers(1,frequency+2));ky=int(rng.integers(1,frequency+2));phase=float(rng.uniform(0,np.pi*2));field+=gain*np.sin((nx*kx+ny*ky)/128*np.pi*2+phase)
 noise[:,:,channel]=np.uint8((field-field.min())/(field.max()-field.min())*255)
for name,im in [('fire-ground-jets-v24',atlas),('fire-jet-seal-v24',seal),('fire-flow-noise-v24',Image.fromarray(noise))]:
 im.save(HERE/'assets'/(name+'.png'),optimize=True);im.save(DEST/(name+'.png'),optimize=True)
 meta=DEST/(name+'.png.meta')
 if not meta.exists():
  data=(DEST/'fire-ground-jets-v24.png.meta').read_text(encoding='utf8');old=json.loads(data)['uuid'];meta.write_text(data.replace(old,str(uuid.uuid4())).replace('fire-ground-jets-v24',name),encoding='utf8')
qa=Image.new('RGB',(900,580),'#283231')
for i in range(3):
 fire=Image.open(HERE/'assets'/f'frame-{i*5:02}.png');qa.paste(fire,(i*300+22,60),fire)
 footprint=seal.resize((250,128));qa.paste(footprint,(i*300+25,354),footprint)
qa.save(HERE/'media/reference-layers-preview.jpg',quality=95)
record={'backend':'built-in cloud image_gen extraction + deterministic Pillow/NumPy','reference':'../fire-selected-reference-v18/user-selected-effect.jpg','generationStatus':'layers extracted','artAcceptance':'original design selected; extraction and native implementation not yet accepted','unusedCandidate':'generated-sheet-01.png and prepare-candidate.py are not used by the production renderer','flameLayer':'reference-flame-layer-01.png','sigilLayer':'reference-seal-layer-01.png','frameProcessing':'16 continuous periodic flow-field samples from the same approved flame layer, fixed root and outline, premultiplied resampling. Native shader blends neighbouring frames and advects flame details upward. No JPEG chroma matte, gamma bake or opacity powers.','sealProcessing':'Luminous reference strokes include their near-white cores; original round curls and teardrop preserved, no diamonds or redrawn petals. Native shader adds a soft orange-gold translucent disk inside the outer ring, requested by the user, animated with the same flow clock.','cell':[256,384],'grid':[4,4],'footPixel':[128,352],'sourceCrop':[int(n) for n in box],'sourceHashes':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['reference-flame-layer-01.png','reference-seal-layer-01.png']},'assets':{n:hashlib.sha256((DEST/(n+'.png')).read_bytes()).hexdigest() for n in ['fire-ground-jets-v24','fire-jet-seal-v24','fire-flow-noise-v24']}}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'flameCrop':record['sourceCrop'],'sealBounds':bbox,'scale':scale}))
