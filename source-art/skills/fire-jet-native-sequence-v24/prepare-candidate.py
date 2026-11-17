"""Register generated RGBA frames; never recover fire from a scene JPEG."""
from pathlib import Path
import json,uuid,hashlib
from PIL import Image,ImageDraw,ImageFilter
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
DEST=ROOT/'src/cocos/assets/resources/vfx/production'
(HERE/'assets').mkdir(exist_ok=True);(HERE/'media').mkdir(exist_ok=True)
source=Image.open(HERE/'generated-sheet-01.png').convert('RGBA');sw,sh=source.size
frames=[];anchors=[];boxes=[]
for i in range(16):
 im=source.crop((i%4*sw//4,i//4*sh//4,(i%4+1)*sw//4,(i//4+1)*sh//4)).resize((256,384),Image.Resampling.LANCZOS)
 a=np.asarray(im)[:,:,3];strong=a>48;y,x=np.where(strong)
 if not len(x):raise ValueError('Empty generated frame')
 boxes.append((int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)))
 bottom=int(np.quantile(y,.995));lower=np.where((np.mgrid[:384,:256][0]>bottom-35)&strong,a.astype(float),0)
 anchor=float((lower*np.arange(256)[None,:]).sum()/max(1,lower.sum()))
 anchors.append((anchor,bottom));frames.append(im)
scale=min(220/max(b[2]-b[0] for b in boxes),330/max(a[1]-b[1] for a,b in zip(anchors,boxes)),1.0)
atlas=Image.new('RGBA',(1024,1536))
for i,(im,(ax,ay)) in enumerate(zip(frames,anchors)):
 p=np.asarray(im).copy();a=p[:,:,3].astype(float)
 # Remove only the near-zero atmosphere at cell edges, retaining true alpha.
 p[:,:,3]=np.uint8(np.clip((a-5)/250,0,1)*255)
 registered=Image.new('RGBA',(256,384));im=Image.fromarray(p).resize((round(256*scale),round(384*scale)),Image.Resampling.LANCZOS)
 registered.paste(im,(round(128-ax*scale),round(352-ay*scale)))
 p=np.asarray(registered).copy();yy,xx=np.mgrid[:384,:256]
 edge=np.minimum.reduce([xx,255-xx,yy,383-yy]);p[:,:,3]=np.uint8(p[:,:,3]*np.clip(edge/10,0,1))
 im=Image.fromarray(p);im.save(HERE/'assets'/f'frame-{i:02}.png');atlas.paste(im,(i%4*256,i//4*384))

# Keep the selected double rings / paired curls / front-rear diamonds.
seal=Image.new('RGBA',(512,512));d=ImageDraw.Draw(seal);gold=(255,198,77,255)
for r,w in [(231,8),(207,6)]:d.ellipse((256-r,256-r,256+r,256+r),outline=gold,width=w)
def curves(segments):
 pts=[]
 for c in segments:
  for t in np.linspace(0,1,64):
   q=sum(np.array(v)*w for v,w in zip(c,[(1-t)**3,3*(1-t)**2*t,3*(1-t)*t*t,t**3]));pts.append((256+q[0]*231,256+q[1]*231))
 d.line(pts,fill=gold,width=7,joint='curve')
curves([[(-.87,0),(-.63,.27),(-.36,-.25),(0,.03)],[(0,.03),(.36,-.25),(.63,.27),(.87,0)]])
curves([[(-.87,0),(-.67,-.42),(-.25,-.58),(0,-.05)],[(0,-.05),(.25,-.58),(.67,-.42),(.87,0)]])
d.line([(256,42),(256,470)],fill=(255,207,93,235),width=5)
for s in [-1,1]:
 cy=256+s*174;d.line([(256,cy-30),(271,cy),(256,cy+30),(241,cy),(256,cy-30)],fill=gold,width=7,joint='curve')
glows=Image.new('RGBA',seal.size)
for radius,gain in [(15,.38),(5,.60)]:
 glow=Image.new('RGBA',seal.size,(255,107,21,0));glow.putalpha(seal.getchannel('A').filter(ImageFilter.GaussianBlur(radius)).point(lambda a:round(a*gain)))
 glows=Image.alpha_composite(glows,glow)
seal=Image.alpha_composite(glows,seal)
for name,im in [('fire-ground-jets-v24',atlas),('fire-jet-seal-v24',seal)]:
 im.save(HERE/'assets'/(name+'.png'),optimize=True);im.save(DEST/(name+'.png'),optimize=True)
 meta=DEST/(name+'.png.meta')
 if not meta.exists():
  old='fire-ground-jets-v22' if 'ground-jets' in name else 'fire-jet-seal-v22';data=(DEST/(old+'.png.meta')).read_text(encoding='utf8');uid=json.loads(data)['uuid']
  meta.write_text(data.replace(uid,str(uuid.uuid4())).replace(old,name),encoding='utf8')
qa=Image.new('RGB',(1024,600),'#283231');draw=ImageDraw.Draw(qa)
for x in range(-600,1600,50):draw.line((x,0,x+600,600),fill='#3d4a47')
for i in range(4):
 im=Image.open(HERE/'assets'/f'frame-{i*4:02}.png');qa.paste(im,(i*256,60),im)
 footprint=seal.resize((210,112));qa.paste(footprint,(i*256+23,354),footprint)
qa.save(HERE/'media/rgba-on-range-grid.jpg',quality=94)
record={'mode':'built-in cloud image_gen','source':'generated-sheet-01.png','generation':'succeeded','artAcceptance':'not accepted yet; native range review pending','reference':'../fire-selected-reference-v18/user-selected-effect.jpg','processing':'16 true RGBA cells, fixed emitter-foot registration, uniform scale, near-zero alpha edge cleanup. Generated RGB/alpha preserved; no JPEG chroma extraction or baked gamma/opacity powers. Ground glyph reuses the selected paired-curl design with a soft halo.','cell':[256,384],'grid':[4,4],'footPixel':[128,352],'scale':scale,'rawAlpha':{'min':int(np.array(source)[:,:,3].min()),'max':int(np.array(source)[:,:,3].max())},'anchors':anchors,'assets':{n:hashlib.sha256((DEST/(n+'.png')).read_bytes()).hexdigest() for n in ['fire-ground-jets-v24','fire-jet-seal-v24']}}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'scale':scale,'bounds':boxes,'anchors':anchors,'alpha':record['rawAlpha']}))
