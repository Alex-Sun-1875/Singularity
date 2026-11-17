"""Rectify the selected image's actual seal pixels; never regenerate its motif."""
from pathlib import Path
import json,hashlib,uuid
import numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
DEST=ROOT/'src/cocos/assets/resources/vfx/production'
for name in ['assets','media']:(HERE/name).mkdir(parents=True,exist_ok=True)
source=ROOT/'source-art/skills/fire-selected-reference-v18/user-selected-effect.jpg'
im=Image.open(source).convert('RGB');rgb=np.asarray(im,dtype=np.float32)
# The nearest unobstructed ring in the selected final image. Both rings and
# all visible inner strokes are sampled from this same patch, without tracing.
cx,cy,rx,ry=497.5,425.5,55.5,26.5
crop=im.crop((437,394,559,458));crop.save(HERE/'assets/selected-original-seal.png')
red,green,blue=rgb.transpose(2,0,1)
warm=np.clip((red-blue-35)/100,0,1)*np.clip((green-blue-20)/65,0,1)
mask=np.clip((green-105)/105,0,1)*np.clip((red-175)/65,0,1)*warm
# Affine inverse projection: a circular texture becomes the selected ellipse
# again when shown at the reference's ground angle. Canvas padding retains glow.
yy,xx=np.mgrid[:512,:512];nx=(xx-255.5)/231;ny=(yy-255.5)/231
sx=cx+nx*rx;sy=cy+ny*ry
x0=sx.astype(int);y0=sy.astype(int);tx=sx-x0;ty=sy-y0
alpha=mask[y0,x0]*(1-tx)*(1-ty)+mask[y0,x0+1]*tx*(1-ty)+mask[y0+1,x0]*(1-tx)*ty+mask[y0+1,x0+1]*tx*ty
radius=np.hypot(nx,ny);alpha*=np.clip((1.08-radius)/.055,0,1)
# Use the original warm light's palette; colour-free ground and the dark staff
# contribute no mask. No new curves, extra spokes, central circle or glyphs.
stroke=Image.fromarray(np.uint8(np.clip(alpha,0,1)*255)).filter(ImageFilter.GaussianBlur(.45))
seal=Image.new('RGBA',(512,512),(255,230,143,0));seal.putalpha(stroke)
halo=Image.new('RGBA',seal.size)
for radius,gain in [(11,.32),(3,.42)]:
 layer=Image.new('RGBA',seal.size,(255,136,35,0));layer.putalpha(stroke.filter(ImageFilter.GaussianBlur(radius)).point(lambda a:round(a*gain)));halo=Image.alpha_composite(halo,layer)
seal=Image.alpha_composite(halo,seal)
name='fire-jet-seal-v25';seal.save(HERE/'assets'/(name+'.png'),optimize=True);seal.save(DEST/(name+'.png'),optimize=True)
meta=DEST/(name+'.png.meta')
if not meta.exists():
 data=(DEST/'fire-jet-seal-v24.png.meta').read_text(encoding='utf8');old=json.loads(data)['uuid'];meta.write_text(data.replace(old,str(uuid.uuid4())).replace('fire-jet-seal-v24',name),encoding='utf8')
old=Image.open(DEST/'fire-jet-seal-v24.png').convert('RGBA')
out=Image.new('RGB',(1320,600),'#272d29');d=ImageDraw.Draw(out)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23)
for x,title in [(20,'选定原图 · 实际像素'),(460,'上一版 · 重绘产生偏差'),(900,'本次 · 原图像素透视还原')]:d.text((x,20),title,font=font,fill='#f0c48b')
out.paste(crop.resize((400,210),Image.Resampling.NEAREST),(20,100))
for x,img in [(460,old),(900,seal)]:
 plane=img.resize((400,196),Image.Resampling.LANCZOS);out.paste(plane,(x,108),plane)
 d.text((x,330),'正上方纹样',font=font,fill='#f0c48b');flat=img.resize((220,220),Image.Resampling.LANCZOS);out.paste(flat,(x+70,365),flat)
out.save(HERE/'media/original-vs-redrawn-vs-restored.jpg',quality=96,subsampling=0)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'method':'deterministic original-pixel colour matte + affine ellipse rectification, no generated or redrawn motif','source':str(source.relative_to(ROOT)),'sourceSha256':sha(source),'ellipse':{'centre':[cx,cy],'radii':[rx,ry]},'textureCoreRadius':231,'output':str((DEST/(name+'.png')).relative_to(ROOT)),'outputSha256':sha(DEST/(name+'.png')),'preserved':'two original rings, original visible inner curves and original small front loop, including their natural irregularities','knownLimit':'Selected final image is a 1280x626 composite. Upright flame covers the rear centre of the seal; these original visible root pixels remain, without inventing hidden strokes. No independent original vector layer exists.','fill':'v24 shader translucent orange-gold inner fill retained','generation':'none in v25','artAcceptance':'native review pending; user acceptance pending'}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
