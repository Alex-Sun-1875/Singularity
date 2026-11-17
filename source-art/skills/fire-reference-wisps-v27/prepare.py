"""Animate selected-reference wisps by upward transport, no generated column."""
from pathlib import Path
import json,hashlib,uuid,sys
import numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];DEST=ROOT/'src/cocos/assets/resources/vfx/production'
PREVIEW='--preview-only' in sys.argv
for p in ['assets','media']:(HERE/p).mkdir(parents=True,exist_ok=True)
reference=ROOT/'source-art/skills/fire-selected-reference-v18/user-selected-effect.jpg'
source=Image.open(reference).convert('RGB');source.crop((438,237,558,459)).save(HERE/'assets/selected-flame-and-seal.png')
ref=np.load(ROOT/'source-art/skills/fire-reference-colour-v26/assets/reference-matte.npz')
prem=ref['premul'];alpha=ref['alpha'];box=ref['box'];field=np.dstack([prem,alpha])

def sample(a,sx,sy):
 sx=np.clip(sx,0,a.shape[1]-1.001);sy=np.clip(sy,0,a.shape[0]-1.001)
 ix=sx.astype(int);iy=sy.astype(int);tx=(sx-ix)[:,:,None];ty=(sy-iy)[:,:,None]
 return a[iy,ix]*(1-tx)*(1-ty)+a[iy,ix+1]*tx*(1-ty)+a[iy+1,ix]*(1-tx)*ty+a[iy+1,ix+1]*tx*ty
def smooth(n):
 n=np.clip(n,0,1);return n*n*(3-2*n)

# Actual nearest flame in the selected final reference. Source pixels below
# the rear ring are excluded; extend its final flame-only rows down to the
# ground anchor, so the upright layer never contains a vertical magic circle.
W,H,FOOT=192,288,264;SCALE=1.65;TOP=242;SOURCE_FOOT=393
yy,xx=np.mgrid[:H,:W];sx=497.5+(xx-95.5)/SCALE;displayY=SOURCE_FOOT+(yy-FOOT)/SCALE
sy=displayY
base=sample(field,sx-box[0],sy-box[1])
cone=5+np.clip((displayY-TOP)/(SOURCE_FOOT-TOP),0,1)*47
ownership=smooth((cone-np.abs(sx-497.5))/4)
ownership*=smooth((displayY-TOP)/6)*(1-smooth((displayY-SOURCE_FOOT)/8))
base*=ownership[:,:,None]
centre=np.exp(-((xx-95.5)/(2.8+2.8*np.clip(yy/FOOT,0,1)))**2)*smooth((yy-35)/35)
# Replace the long saturated centre with neighbouring original flame detail.
# Do not erase a vertical stripe: the plume needs continuous translucent volume.
oldA=base[:,:,3].copy();near=(sample(base,xx-9,yy)+sample(base,xx+9,yy))*.5
base=base*(1-.85*centre[:,:,None])+near*(.85*centre[:,:,None])
currentA=base[:,:,3].copy();newA=np.minimum(np.maximum(currentA,oldA*.25*centre)*1.10,.90)
base[:,:,:3]*=(newA/np.maximum(currentA,1e-6))[:,:,None];base[:,:,3]=newA
rgb=base[:,:,:3]/np.maximum(base[:,:,3,None],1e-6)
# Background separation can leave a few cold boundary samples; real warm light
# in this reference has red >= green >= blue. Preserve its local hue otherwise.
rgb[:,:,0]=np.maximum(rgb[:,:,0],rgb[:,:,1]);rgb[:,:,1]=np.minimum(rgb[:,:,1],rgb[:,:,0]*.85);rgb[:,:,2]=np.minimum(rgb[:,:,2],rgb[:,:,1])
base[:,:,:3]=rgb*base[:,:,3,None]
registered=Image.fromarray(np.uint8(np.clip(np.dstack([rgb,base[:,:,3]]),0,1)*255));registered.save(HERE/'assets/original-wisps-registered.png')

envelope=np.asarray(registered.getchannel('A').filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(3)),dtype=float)/255
envelope=np.clip(envelope*1.4,0,1)
root=1-smooth((FOOT-yy-5)/95)
transport=base*(1-smooth((yy-130)/(FOOT-130)))[:,:,None]
atlas=Image.new('RGBA',(W*8,H*4));frames=[]
for frame in range(32):
 phase=frame/32;phase2=(phase+.5)%1
 w0=np.sin(np.pi*phase)**2;w1=np.sin(np.pi*phase2)**2
 # Both samples travel only upward. Complementary phases fade at their resets.
 drift=np.sin(phase*np.pi*2+yy*.012)*1.2*(1-root)
 a=sample(transport,xx+drift,yy+phase*.68*FOOT)*np.sqrt(w0)
 b=sample(transport,xx-drift*.6,yy+phase2*.68*FOOT)*np.sqrt(w1)
 flow=a+b*(1-a[:,:,3,None]);flow*=envelope[:,:,None]*(1-root[:,:,None])*.96
 static=base*(.35+.65*root[:,:,None])
 out=flow+static*(1-flow[:,:,3,None])
 # Root remains grounded and the plume dies away softly at its outer borders.
 border=smooth(np.minimum.reduce([xx,W-1-xx,yy,H-1-yy])/5)
 out*=border[:,:,None];color=out[:,:,:3]/np.maximum(out[:,:,3,None],1e-6)
 rgba=Image.fromarray(np.uint8(np.clip(np.dstack([color,out[:,:,3]]),0,1)*255))
 rgba.save(HERE/'assets'/f'frame-{frame:02}.png');frames.append(rgba);atlas.paste(rgba,(frame%8*W,frame//8*H))
name='fire-ground-jets-v27';atlas.save(HERE/'assets'/(name+'.png'),optimize=True)
if not PREVIEW:atlas.save(DEST/(name+'.png'),optimize=True)
meta=DEST/(name+'.png.meta')
if not PREVIEW and not meta.exists():
 text=(DEST/'fire-ground-jets-v26.png.meta').read_text(encoding='utf8');old=json.loads(text)['uuid'];meta.write_text(text.replace(old,str(uuid.uuid4())).replace('fire-ground-jets-v26',name),encoding='utf8')
seal=np.asarray(Image.open(DEST/'fire-jet-seal-v26.png').convert('RGBA'),dtype=float)/255
gy,gx=np.mgrid[:512,:512];nx=(gx-255.5)/231;ny=(gy-255.5)/231;rad=np.hypot(nx,ny)
occluded=(1-smooth((ny+.50)/.14))*(1-smooth((rad-.68)/.08))*(1-smooth((np.abs(nx)-.58)/.12))
seal[:,:,3]*=1-.90*occluded
sealName='fire-jet-seal-v27';sealImage=Image.fromarray(np.uint8(np.clip(seal,0,1)*255));sealImage.save(HERE/'assets'/(sealName+'.png'),optimize=True)
if not PREVIEW:sealImage.save(DEST/(sealName+'.png'),optimize=True)
sealMeta=DEST/(sealName+'.png.meta')
if not PREVIEW and not sealMeta.exists():
 text=(DEST/'fire-jet-seal-v26.png.meta').read_text(encoding='utf8');old=json.loads(text)['uuid'];sealMeta.write_text(text.replace(old,str(uuid.uuid4())).replace('fire-jet-seal-v26',sealName),encoding='utf8')
preview=Image.new('RGB',(960,650),'#28312c');d=ImageDraw.Draw(preview);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
for i,index in enumerate([0,5,10,16,21,26]):
 x=i%3*320;y=i//3*325;d.text((x+15,y+5),f'{index:02} / 原图细火舌向上流动',fill='#efc184',font=font)
 im=np.asarray(frames[index],dtype=float)/255;a=im[:,:,3,None]
 lit=im[:,:,:3]*a*1.10+np.array([40,49,44])/255*(1-a*.90)
 preview.paste(Image.fromarray(np.uint8(np.clip(lit,0,1)*255)),(x+60,y+32))
preview.save(HERE/'media/wisp-sequence-preview.jpg',quality=95,subsampling=0)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'reference':str(reference.relative_to(ROOT)),'referenceSha256':sha(reference),'method':'Deterministic original-reference light matte and upward texture transport; no generated flame asset or local model','flameSource':'../fire-reference-colour-v26/assets/reference-matte.npz','sourceRegion':{'centreX':497.5,'top':TOP,'groundAnchorY':SOURCE_FOOT,'flameOnlyLastRow':393},'rootProcessing':'Flame-only crop ends above the source seal; no stretched root or upright ring is baked in. Neighbouring original wisps replace the long saturated centre, retaining continuous translucent volume rather than erasing a vertical stripe.','animation':'32 phases, two strictly upward moving source samples with complementary smooth fades, root pinned; no serpentine UV warp or central bright-core enhancement','compositing':'Premultiplied translucent flame with gentle light lift (1.10 colour / 0.90 opacity); circle retains normal-equivalent premultiplied compositing','cell':[W,H],'grid':[8,4],'footPixel':[95.5,FOOT],'seal':'Original ring, side curves and front motif retained; source upright-flame contamination inside the rear ring reduced. Warmer low-alpha glow and measured low/mid orange-gold fill cover the complete inner disk.','textures':{n:sha(HERE/'assets'/(n+'.png')) for n in [name,sealName]},'productionUpdated':not PREVIEW,'artAcceptance':'local sequence preview only; native and user acceptance pending','taptapDevice':'pending'}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(record,ensure_ascii=False))
