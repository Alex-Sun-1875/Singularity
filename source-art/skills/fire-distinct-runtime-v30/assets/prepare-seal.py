"""Conservative v29 circle extraction; only two known round rims rebuilt."""
from pathlib import Path
import json, hashlib, uuid
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
RES=ROOT/'src/cocos/assets/resources/vfx/production'
REF=ROOT/'source-art/skills/fire-distinct-shapes-design-v29/fire-distinct-shapes-v29.png'
im=Image.open(REF).convert('RGB')
box=(220,833,580,978)
p=np.asarray(im.crop(box),dtype=float)/255
warm=p[...,0]-p[...,2]
known=warm<.09
rfit=np.polyfit(p[...,2][known],p[...,0][known],1)
gfit=np.polyfit(p[...,2][known],p[...,1][known],1)
contrast=p[...,0]-rfit[0]*p[...,2]-rfit[1]
blue=np.full_like(contrast,.16)
for unused in range(3):
    alpha=np.clip(contrast/np.maximum(1-rfit[0]*blue-rfit[1],.2),0,.94)
    green=(p[...,1]-gfit[0]*p[...,2]-gfit[1])/np.maximum(alpha,1e-6)+gfit[0]*blue+gfit[1]
    blue=np.clip(.04+.55*(green-.37),.035,.35)
def smooth(a):
    a=np.clip(a,0,1)
    return a*a*(3-2*a)
# Isolate fine luminous engraving, not the source's baked diffuse floor light.
# A white top-hat removes broad orange reflection/grey haze while retaining
# the narrow local peaks of the actual lines. The warm difference also keeps
# neutral stone joints out. No full-disk opacity or floor-colour matte remains.
signal=Image.fromarray(np.uint8(np.clip(warm,0,1)*255))
opened=np.asarray(signal.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(9)),dtype=float)/255
ridge=np.maximum(0,warm-opened)
core=smooth((ridge-.030)/.36)*.88
halo=np.asarray(Image.fromarray(np.uint8(core*255)).filter(ImageFilter.GaussianBlur(.65)),dtype=float)/255
alpha=np.minimum(.90,core*.94+halo*.06)
rgb=np.stack([np.ones_like(alpha),np.clip(green,.50,.80),np.clip(blue,.06,.27)],axis=2)
field=np.concatenate([rgb*alpha[...,None],alpha[...,None]],axis=2)

def sample(a,x,y):
    x=np.clip(x,0,a.shape[1]-1.001);y=np.clip(y,0,a.shape[0]-1.001)
    ix=x.astype(int);iy=y.astype(int);tx=(x-ix)[...,None];ty=(y-iy)[...,None]
    return a[iy,ix]*(1-tx)*(1-ty)+a[iy,ix+1]*tx*(1-ty)+a[iy+1,ix]*(1-tx)*ty+a[iy+1,ix+1]*tx*ty

y,x=np.mgrid[:512,:512]
nx=(x-255.5)/231;ny=(y-255.5)/231
radius=np.hypot(nx,ny)
out=sample(field,398+nx*168-box[0],905.5+ny*60.5-box[1])
# Remove the actual meteor/flame pixels. Hidden engraving is left absent,
# rather than inventing the parts behind the approved concept's rock.
hidden=np.hypot((nx+.01)/.43,(ny+.77)/.43)
occlusion=1-smooth((hidden-.72)/.38)
out*=1-occlusion[...,None]
out*= (1-smooth((radius-.945)/.018))[...,None]
rgb=out[...,:3]/np.maximum(out[...,3,None],1e-6)
base=Image.fromarray(np.uint8(np.clip(np.concatenate([rgb,out[...,3,None]],axis=2),0,1)*255))
# The reference clearly shows two round outside rims. Rebuild only those
# unambiguous circles; do not manufacture missing inner curved engraving.
S=3
rim=Image.new('RGBA',(512*S,512*S))
d=ImageDraw.Draw(rim)
for r in (230,222):
    d.ellipse(((255.5-r)*S,(255.5-r)*S,(255.5+r)*S,(255.5+r)*S),outline=(255,157,47,218),width=round(2.0*S))
rim=rim.resize((512,512),Image.Resampling.LANCZOS)
glow=Image.new('RGBA',(512,512))
soft=rim.filter(ImageFilter.GaussianBlur(2.2))
soft.putalpha(soft.getchannel('A').point(lambda a:round(a*.22)))
base=Image.alpha_composite(base,soft)
base=Image.alpha_composite(base,rim)
name='fire-meteor-seal-v30'
old_path=HERE/'meteor-seal-before-lines.png'
if not old_path.exists() and (RES/(name+'.png')).exists():
    old_path.write_bytes((RES/(name+'.png')).read_bytes())
base.save(HERE/(name+'.png'),optimize=True)
base.save(RES/(name+'.png'),optimize=True)
meta=RES/(name+'.png.meta')
if not meta.exists():
    template=(RES/'fire-meteor-seal-v22.png.meta').read_text(encoding='utf8')
    old=json.loads(template)['uuid']
    meta.write_text(template.replace(old,str(uuid.uuid4())).replace('fire-meteor-seal-v22',name),encoding='utf8')

canvas=Image.new('RGB',(1000,480),'#28312c')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
d=ImageDraw.Draw(canvas)
d.text((12,10),'v29 大陨石法阵：原稿可见曲纹提取 + 双圆边重建 / 素材小样，非实景',font=font,fill='#eac187')
q=np.asarray(base,dtype=float)/255
flat=q[...,:3]*q[...,3,None]+np.array([40,49,44])/255*(1-q[...,3,None])
flat=Image.fromarray(np.uint8(np.clip(flat,0,1)*255))
canvas.paste(flat.resize((420,420)),(20,45))
canvas.paste(flat.resize((535,194)),(450,169))
canvas.save(HERE/'meteor-seal-preview.jpg',quality=95,subsampling=0)
record=dict(reference=str(REF.relative_to(ROOT)),sourceRegion=box,
    method='Deterministic warm-signal white top-hat (9px opening) isolates thin local engraving peaks and rejects baked diffuse floor glow/grey haze; ellipse deprojection of the visible linework. Only two unambiguous outside rims are rebuilt, not pixel-identical art.',
    deprojection=dict(sourceCentre=[398,905.5],sourceRadius=[168,60.5],targetCentre=[255.5,255.5],targetRadius=231),
    occlusion='Meteor/flame-covered rear-centre inner engraving removed conservatively. Hidden motifs left absent; no rock, flame column or characters in output.',
    texture=dict(name=name,size=[512,512],straightAlpha=True,outerVisibleDiameter=460,centreUV=[.5,.5],
        imageRow0='reference far/back arc; image bottom is reference near/front arc',
        groundSize='Existing drawMeteorSeal radius*2/(460/512) remains correct. For exact reference orientation, camera-aligned ground row0 should sample v0; the current world-aligned UV 1-row places image top along +worldZ.',
        sha256=hashlib.sha256((RES/(name+'.png')).read_bytes()).hexdigest()),
    alphaMetrics=dict(innerDiskMedian=float(np.median(q[...,3][radius<.70])),innerDiskMean=float(q[...,3][radius<.70].mean()),innerDiskFractionBelow002=float((q[...,3][radius<.70]<.02).mean())),
    productionUpdated=True,localReview='After reviewing native after-r1/FIR_02/034.jpg, replaced the diffuse-light matte with line-only high-frequency support. Local square/flattened preview inspected; complete two rims remain, hidden rear art is not invented. Native second-round verification pending.',nativeAcceptance='pending second-round Cocos capture',taptapDevice='pending')
(HERE/'meteor-seal-provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
