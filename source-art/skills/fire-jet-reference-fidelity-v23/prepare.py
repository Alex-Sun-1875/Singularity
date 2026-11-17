"""Recover the selected fine flame strands without repainting their shape."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
DEST=ROOT/'src/cocos/assets/resources/vfx/production'
(HERE/'assets').mkdir(exist_ok=True);(HERE/'media').mkdir(exist_ok=True)
source=HERE.parent/'fire-selected-reference-v18/user-selected-effect.jpg'
reference=Image.open(source).convert('RGB')
box=(445,242,549,430)
p=np.asarray(reference.crop(box),dtype=np.float32)/255
y,x=np.mgrid[:p.shape[0],:p.shape[1]];height,width=p.shape[:2]
warm=np.maximum(0,p[:,:,0]-p[:,:,2])
# Remove neutral stone in the same gamma-2 space as the engine texture helper.
# Preserve the source strand's red/green relationship, with a graded matte.
linear=p*p;chroma=np.maximum(0,linear-linear[:,:,2,None]);scale=np.maximum(chroma[:,:,0,None],.001)
rgb=np.sqrt(np.clip(chroma/scale,0,1));rgb[:,:,0]=1;rgb[:,:,2]=.04
alpha=np.clip((warm-.15)/.62,0,1)**1.3
hot=np.clip((p[:,:,0]-.72)/.28,0,1)**4*np.clip((warm-.15)/.15,0,1)
rgb=rgb*(1-hot[:,:,None])+p*hot[:,:,None]
rgb[:,:,1]=np.minimum(rgb[:,:,1],rgb[:,:,0])
alpha=np.maximum(alpha,hot)
vertical=np.median(np.stack([np.roll(alpha,i,axis=0) for i in range(-3,4)]),axis=0)
bottom=np.clip((y/height-.78)/.12,0,1)
alpha=alpha*(1-bottom)+np.minimum(alpha,vertical)*bottom
for rx,ry in [(55,27),(48,22)]:
 ring=np.abs(np.sqrt(((x+box[0]-497)/rx)**2+((y+box[1]-427)/ry)**2)-1)<.11
 continuation=np.minimum(np.roll(alpha,-5,axis=0),np.roll(alpha,5,axis=0))
 alpha=np.where(ring,np.minimum(alpha,continuation),alpha)
half=8+(width*.52-8)*(y/(height-1))**.55
alpha*=np.clip((half-np.abs(x-width/2))/7,0,1)
alpha*=np.clip((height-1-y)/3,0,1)
plume=Image.fromarray(np.uint8(np.clip(np.dstack((rgb,alpha)),0,1)*255)).resize((256,448),Image.Resampling.LANCZOS)
atlas=Image.new('RGBA',(1024,1792))
for frame in range(16):
 phase=frame*np.pi*2/16;yy,xx=np.mgrid[:448,:256]
 displacement=np.sin(phase+yy*.045)*(1-yy/448)**1.6*2.0
 data=np.asarray(plume).copy();sample=np.clip(np.rint(xx+displacement).astype(int),0,255)
 data=data[np.arange(448)[:,None],sample]
 atlas.paste(Image.fromarray(data),(frame%4*256,frame//4*448))

seal=Image.new('RGBA',(512,512));draw=ImageDraw.Draw(seal)
gold=(255,170,43,255)
for radius,stroke in [(231,8),(207,6)]:draw.ellipse((256-radius,256-radius,256+radius,256+radius),outline=gold,width=stroke)
def curve(segments):
 points=[]
 for controls in segments:
  for t in np.linspace(0,1,64):
   q=sum(np.array(c)*w for c,w in zip(controls,[(1-t)**3,3*(1-t)**2*t,3*(1-t)*t*t,t**3]))
   points.append((256+q[0]*231,256+q[1]*231))
 draw.line(points,fill=gold,width=5,joint='curve')
# Trace the selected paired curls and front/rear diamonds, not a three-leaf seal.
curve([[(-.87,0),(-.63,.27),(-.36,-.25),(0,.03)],[(0,.03),(.36,-.25),(.63,.27),(.87,0)]])
curve([[(-.87,0),(-.67,-.42),(-.25,-.58),(0,-.05)],[(0,-.05),(.25,-.58),(.67,-.42),(.87,0)]])
draw.line([(256,42),(256,470)],fill=(255,188,67,210),width=4)
for sign in [-1,1]:
 cy=256+sign*174
 draw.line([(256,cy-30),(271,cy),(256,cy+30),(241,cy),(256,cy-30)],fill=gold,width=5,joint='curve')
glow=Image.new('RGBA',seal.size,gold[:3]+(0,));glow.putalpha(seal.getchannel('A').filter(ImageFilter.GaussianBlur(10)).point(lambda a:round(a*.45)))
seal=Image.alpha_composite(glow,seal)
for name,im in [('fire-ground-jets-v22',atlas),('fire-jet-seal-v22',seal)]:
 # The current legacy-forward VFX presentation lifts stored display RGB.
 # Calibrate the native texture transfer; preserve authoring/QA display RGB.
 native=np.asarray(im).copy();native[:,:,:3]=np.uint8((native[:,:,:3].astype(np.float32)/255)**2*255)
 if name=='fire-ground-jets-v22':native[:,:,3]=np.uint8((native[:,:,3].astype(np.float32)/255)**1.8*255)
 native=Image.fromarray(native)
 native.save(HERE/'assets'/(name+'.png'),optimize=True)
 if '--preview-only' not in sys.argv:native.save(DEST/(name+'.png'),optimize=True)
plume.save(HERE/'assets/selected-strands.png')
qa=Image.new('RGB',(1000,720),'#797168');large=plume.resize((284,513),Image.Resampling.LANCZOS)
f=np.asarray(large).astype(np.float32)/255;bg=np.asarray(qa.crop((98,54,382,567))).astype(np.float32)/255
composite=np.sqrt(f[:,:,:3]**2*f[:,:,3,None]+bg**2*(1-f[:,:,3,None]))
qa.paste(Image.fromarray(np.uint8(np.clip(composite,0,1)*255)),(98,54))
projected=seal.resize((300,154),Image.Resampling.LANCZOS);qa.paste(projected,(90,490),projected)
qa.paste(reference.crop((434,242,560,458)).resize((344,590)),(600,60))
qa.save(HERE/'media/extraction-vs-reference.jpg',quality=95)
record={'source':str(source.relative_to(ROOT)),'referenceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'crop':box,'method':'Gamma-2 neutral-chroma removal and a graded matte preserve the selected strand shape and its empty gaps; no saturated linear matte, repeated curtains or filled floor disc. Lower vertical continuity suppresses photographed circle contamination. Sixteen subtle periodic offsets animate the same strand shape. Small seal traces double rings, paired inner curls and axial diamonds. No image generation.','generation':'none','artAcceptance':'Local inspection pending; user approval pending','assets':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (HERE/'assets').glob('*.png')}}
record['nativeRgbEncoding']='Stored RGB squared to compensate the measured current legacy-forward VFX transfer. The separate flame optical matte is recorded below; source/authoring comparison remains display RGB.'
record['nativeFlameOpticalAlpha']='Flame alpha raised to 1.8 to retain bright strand cores while opening the veils between them; seal alpha unchanged.'
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'crop':box,'atlas':atlas.size,'referenceSha256':record['referenceSha256']},ensure_ascii=False))
