"""Deterministic full-body extraction of the user-selected v29 impact.

Retain its single nucleus and irregular outward/central curls. No generated
replacement, repeated petal, high-pass wire matte, or baked floor/actors.
"""
from pathlib import Path
import hashlib, json, uuid
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
RES=ROOT/'src/cocos/assets/resources/vfx/production'
SOURCE=HERE/'approved-reference.png'
BOX=(796,714,1388,1006)
ANCHOR=(1109,889)
W,H=512,256

def smooth(a):
 a=np.clip(a,0,1);return a*a*(3-2*a)

def rgba(a):
 rgb=a[...,:3]/np.maximum(a[...,3,None],1e-6)
 return Image.fromarray(np.uint8(np.clip(np.dstack((rgb,a[...,3])),0,1)*255),'RGBA')

def sample(a,x,y):
 valid=(x>=0)&(x<a.shape[1]-1)&(y>=0)&(y<a.shape[0]-1)
 x=np.clip(x,0,a.shape[1]-1.001);y=np.clip(y,0,a.shape[0]-1.001)
 ix=x.astype(int);iy=y.astype(int);fx=(x-ix)[...,None];fy=(y-iy)[...,None]
 return (a[iy,ix]*(1-fx)*(1-fy)+a[iy,ix+1]*fx*(1-fy)+a[iy+1,ix]*(1-fx)*fy+a[iy+1,ix+1]*fx*fy)*valid[...,None]

im=Image.open(SOURCE).convert('RGB').crop(BOX)
im.save(HERE/'burst-source.png')
p=np.asarray(im,dtype=np.float64)/255
r,g,b=p[...,0],p[...,1],p[...,2]
clean=(r-b<.09)&(r<.50)
rf=np.polyfit(b[clean],r[clean],1);gf=np.polyfit(b[clean],g[clean],1)
rf[0]=np.clip(rf[0],.65,1.5);gf[0]=np.clip(gf[0],.65,1.4)
contrast=r-rf[0]*b-rf[1]
blue=np.full_like(r,.16)
for _ in range(3):
 alpha=np.clip(contrast/np.maximum(1-rf[0]*blue-rf[1],.2),0,.97)
 green=(g-gf[0]*b-gf[1])/np.maximum(alpha,1e-5)+gf[0]*blue+gf[1]
 blue=np.clip(.045+.59*(green-.37),.035,.38)
alpha*=smooth((contrast-.006)/.07)
# Keep the broad fire body. Only reject neutral dark stone and faint residue;
# the old experiment's 2.5% body/high-pass filtering caused the wire effect.
alpha*=smooth((r-.33)/.35)*smooth((g-b-.025)/.08)
alpha=1-np.power(1-alpha,1.12)
colour=np.stack((np.ones_like(r),np.clip(green,.34,.90),blue),axis=-1)
# The source's hot gold nucleus has a nearly neutral bright centre. A chroma
# key alone would punch a dark star out of it, so recover it from source light.
yy,xx=np.mgrid[:im.height,:im.width]
dc=np.hypot(xx-(ANCHOR[0]-BOX[0]),yy-(ANCHOR[1]-BOX[1]))
hot=(1-smooth((dc-5)/15))*smooth((r-.58)/.33)
alpha=np.maximum(alpha,hot*.97)
source_hot=np.stack((np.ones_like(r),np.clip(g/np.maximum(r,.01),.65,1),np.clip(b/np.maximum(r,.01),.10,.85)),axis=-1)
colour=colour*(1-hot[...,None])+source_hot*hot[...,None]
mask=Image.new('L',im.size,255);draw=ImageDraw.Draw(mask)
# Original actors, label and rocks stay out of the light matte. No obscured
# flame is invented behind them; those source pixels remain transparent.
def poly(points):draw.polygon([(x-BOX[0],y-BOX[1]) for x,y in points],fill=0)
poly([(730,695),(979,695),(979,760),(730,760)])
poly([(747,760),(851,760),(900,783),(918,830),(900,865),(892,922),(854,939),(808,932),(747,939)])
poly([(1320,755),(1430,755),(1430,850),(1340,850),(1340,805)])
rock_mask=Image.new('L',im.size,0);rocks=ImageDraw.Draw(rock_mask)
for cx,cy,rx,ry in [(1017,810,9,12),(1168,817,8,11),(1206,883,10,8),(1102,924,13,9),(1132,937,8,7),(1057,954,7,8),(975,881,8,7),(1052,877,8,6)]:
 rocks.ellipse((cx-rx-BOX[0],cy-ry-BOX[1],cx+rx-BOX[0],cy+ry-BOX[1]),fill=255)
safe=np.asarray(mask.filter(ImageFilter.GaussianBlur(4)),dtype=float)/255
y,x=np.mgrid[:im.height,:im.width]
edge=smooth(x/8)*smooth((im.width-1-x)/8)*smooth(y/6)*smooth((im.height-1-y)/8)
alpha*=safe*edge
pma=np.dstack((colour*alpha[...,None],alpha))
# Deterministically interpolate only the few small stone occlusions from their
# immediate warm neighbours. Stones are not baked into and advected with fire.
removed=np.asarray(rock_mask,dtype=float)/255
known=1-removed
def gauss(a,radius):
 return np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).filter(ImageFilter.GaussianBlur(radius)),dtype=float)/255
denom=gauss(known,7)
fill=np.stack([gauss(pma[...,c]*known,7)/np.maximum(.01,denom) for c in range(4)],axis=-1)
repair=gauss(removed,1.1)
pma=pma*(1-repair[...,None])+fill*repair[...,None]
# Close only tiny dark tile-joint cuts inside an otherwise continuous warm
# flame. This removes baked ground grain without dropping the broad body or
# replacing the selected flame silhouette with high-pass light wires.
old_alpha=pma[...,3].copy()
closed=np.asarray(Image.fromarray(np.uint8(old_alpha*255)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5)),dtype=float)/255
new_alpha=np.maximum(old_alpha,closed*.82)
average_alpha=gauss(old_alpha,3)
average_colour=np.stack([gauss(pma[...,c],3)/np.maximum(.01,average_alpha) for c in range(3)],axis=-1)
old_colour=pma[...,:3]/np.maximum(1e-6,old_alpha[...,None])
amount=np.clip((new_alpha-old_alpha)/.18,0,1)
new_colour=old_colour*(1-amount[...,None])+average_colour*amount[...,None]
pma=np.dstack((new_colour*new_alpha[...,None],new_alpha))
base=rgba(pma).resize((W,H),Image.Resampling.LANCZOS)
base.save(HERE/'burst-extracted.png')
a=np.asarray(base,dtype=np.float64)/255;a[...,:3]*=a[...,3,None]
y,x=np.mgrid[:H,:W];cx=(ANCHOR[0]-BOX[0])/(BOX[2]-BOX[0])*W;cy=(ANCHOR[1]-BOX[1])/(BOX[3]-BOX[1])*H
dx=x-cx;dy=y-cy;dist=np.maximum(1,np.hypot(dx,dy));vx=dx/dist;vy=dy/dist
plume=np.exp(-((x-cx)/(W*.16))**2)*smooth((cy-y)/(H*.28))
vx*=1-plume*.82;vy=vy*(1-plume)-plume
mobile=smooth(dist/(W*.085))
atlas=Image.new('RGBA',(W*4,H*4))
for i in range(16):
 phase=i/16;other=(phase+.5)%1;blend=np.sin(phase*np.pi)**2
 def advect(t):
  wave=np.sin(x*.043+y*.029-i*2*np.pi/16)*1.25*mobile
  return sample(a,x-vx*t*8*mobile+wave*.25,y-vy*t*8*mobile+wave*.35)
 flowed=advect(phase)*blend+advect(other)*(1-blend)
 # Preserve the selected broad outline while the fire's body travels outward
 # and the central plume rises. Exact nucleus is pinned through every frame.
 pin=1-smooth(dist/(W*.035))
 flowed=flowed*(1-pin[...,None])+a*pin[...,None]
 atlas.paste(rgba(flowed),(i%4*W,i//4*H))
name='fire-meteor-burst-v32';target=RES/(name+'.png');atlas.save(target,optimize=True)
template=json.loads((RES/'fire-meteor-roll-v31.png.meta').read_text(encoding='utf8'))
identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/'+name))
old=template['uuid'];text=json.dumps(template,ensure_ascii=False,indent=2).replace(old,identity).replace('fire-meteor-roll-v31',name)
target.with_suffix('.png.meta').write_text(text+'\n',encoding='utf8',newline='\n')
board=Image.new('RGB',(1080,660),'#272e2b')
board.paste(im.resize((1040,513)),(20,12))
preview=base.resize((1040,520));board=Image.new('RGB',(1080,1080),'#272e2b')
board.paste(im.resize((1040,513)),(20,12));board.paste(preview,(20,550),preview)
board.save(HERE/'burst-extraction-review.jpg',quality=95)
meta={'source':'approved-reference.png','sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'crop':BOX,'anchorSourcePx':ANCHOR,
 'anchorUV':[(ANCHOR[0]-BOX[0])/(BOX[2]-BOX[0]),(ANCHOR[1]-BOX[1])/(BOX[3]-BOX[1])],
 'method':'Neutral-floor channel regression with full broad fire body; masks protect actors/text, small stone occlusions interpolated from immediate neighbours, 5px closing rejects baked dark tile joints; 16 forward-flow frames with pinned nucleus. Deterministic Pillow/NumPy, no new generation.',
 'asset':str(target.relative_to(ROOT)),'size':atlas.size,'cell':[W,H],'frames':16,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
 'review':{'extraction':'pending visual review','native':'pending','userAcceptance':'pending'}}
(HERE/'burst-provenance.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(meta,ensure_ascii=False))
