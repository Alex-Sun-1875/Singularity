"""One pending R4 reference-scroll seal. Production is never written here."""
from pathlib import Path
import hashlib,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops,ImageFont

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
REF=ROOT/'source-art/skills/fire-reference-alignment-v32/assets/approved-reference.png'
PROD=ROOT/'src/cocos/assets/resources/vfx/production/fire-meteor-seal-v33.png'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(PROD);N=1024;S=3;C=511.5;R=460
data=json.loads((HERE/'traced-paths.json').read_text(encoding='utf8'))
motifs=data['motifs'];inner=data['inner']
def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)
def cubic(points):
    a=[]
    for i in range(0,len(points)-1,3):
        p0,p1,p2,p3=map(np.asarray,points[i:i+4])
        for t in np.linspace(0,1,90):a.append((1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*p3)
    return np.asarray(a)
def draw_line(mask,points,width):
    pts=[((C+x*R)*S,(C+y*R)*S) for x,y in points]
    d=ImageDraw.Draw(mask);d.line(pts,fill=255,width=round(width*S),joint='curve')
    rad=width*S*.5
    for x,y in [pts[0],pts[-1]]:d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=255)
def ellipsebox(r):return ((C-r*R)*S,(C-r*R)*S,(C+r*R)*S,(C+r*R)*S)
ink=Image.new('L',(N*S,N*S));core=Image.new('L',ink.size)
bandInk=Image.new('L',ink.size);bandCore=Image.new('L',ink.size)
insideInk=Image.new('L',ink.size);insideCore=Image.new('L',ink.size)
for r,w in [(1.,4.8),(.9717,4.4),(.755,4.3),(.733,3.6)]:
    ImageDraw.Draw(ink).ellipse(ellipsebox(r),outline=255,width=round(w*S))
    ImageDraw.Draw(core).ellipse(ellipsebox(r),outline=255,width=round(1.7*S))
for paths in motifs.values():
    for index,p in enumerate(paths):
        pts=cubic(p);draw_line(bandInk,pts,5.2 if index==0 else 3.85);draw_line(bandCore,pts,1.85 if index==0 else 1.45)
for p in inner.values():
    p=[list(q) for q in p]
    # Preserve visible reference recurve geometry. A near-boundary end simply
    # meets the now-concentric circular border rather than floating inside it.
    for index in [0,-1]:
        r=math.hypot(*p[index])
        if .5<r<.733:p[index]=[n*.733/r for n in p[index]]
    pts=cubic(p);draw_line(insideInk,pts,5.0);draw_line(insideCore,pts,1.85)
    tangent=np.gradient(pts,axis=0);length=np.maximum(np.linalg.norm(tangent,axis=1),1e-6)
    near=pts+np.stack([-tangent[:,1]/length,tangent[:,0]/length],axis=1)*.0135
    draw_line(insideInk,near,2.7);draw_line(insideCore,near,1.0)
band=Image.new('L',ink.size);inside=Image.new('L',ink.size)
ImageDraw.Draw(band).ellipse(ellipsebox(.968),fill=255)
ImageDraw.Draw(band).ellipse(ellipsebox(.753),fill=0)
ImageDraw.Draw(inside).ellipse(ellipsebox(.756),fill=255)
ink=ImageChops.lighter(ink,ImageChops.multiply(bandInk,band));core=ImageChops.lighter(core,ImageChops.multiply(bandCore,band))
ink=ImageChops.lighter(ink,ImageChops.multiply(insideInk,inside));core=ImageChops.lighter(core,ImageChops.multiply(insideCore,inside))
ink=ink.resize((N,N),Image.Resampling.LANCZOS);core=core.resize((N,N),Image.Resampling.LANCZOS)
ia=np.asarray(ink,dtype=float)/255;ca=np.asarray(core,dtype=float)/255
halo=np.asarray(ink.filter(ImageFilter.GaussianBlur(6.5)),dtype=float)/255*.20+np.asarray(ink.filter(ImageFilter.GaussianBlur(9)),dtype=float)/255*.05
def layer(colour,alpha):
    a=np.zeros((N,N,4),dtype=np.uint8);a[...,:3]=colour;a[...,3]=np.uint8(np.clip(alpha,0,1)*255);return Image.fromarray(a)
y,x=np.mgrid[:N,:N];rad=np.hypot((x-C)/R,(y-C)/R)
centre=np.exp(-(rad/.48)**2);rim=np.exp(-((rad-.84)/.13)**2)
edge=1-smooth((rad-.94)/.06)
fill_a=(.070+.018*centre+.014*rim)*edge
fill_rgb=np.stack([np.ones_like(rad),.455+.025*centre+.012*rim,.117+.015*centre+.008*rim],axis=2)
filled=Image.fromarray(np.uint8(np.clip(np.concatenate([fill_rgb,fill_a[...,None]],axis=2),0,1)*255))
# The soft reflected light follows the actual engraved strokes, spreading
# locally before joining the very thin all-disk wash. It is not a uniform
# brown plate and contains no baked stone/grid image.
spread=np.asarray(ink.filter(ImageFilter.GaussianBlur(16)),dtype=float)/255*.45
spread+=np.asarray(ink.filter(ImageFilter.GaussianBlur(34)),dtype=float)/255*.30
spread=np.minimum(.09,spread)*edge
filled=Image.alpha_composite(filled,layer((255,140,45),spread))
filled=Image.alpha_composite(filled,layer((227,107,31),halo))
filled=Image.alpha_composite(filled,layer((236,148,65),ia*.99))
filled=Image.alpha_composite(filled,layer((249,174,97),ca*.94))
pixels=np.asarray(filled).copy();pixels[pixels[...,3]==0,:3]=0;filled=Image.fromarray(pixels)
name='fire-meteor-seal-v33-colour-r4-pending.png';filled.save(HERE/name,optimize=True)

# Proposed preview cancels the 1.15 RGB gain. No red-channel clipping or hue
# claim is inferred from flattened concept samples; native capture is required.
q=np.asarray(filled,dtype=float)/255;a=q[...,3,None]
bg=Image.new('RGB',(N,N),'#28312c');d=ImageDraw.Draw(bg)
for v in range(-N,N*2,96):
    d.line((0,v,N,v+N*.58),fill='#84908a',width=2);d.line((0,v,N,v-N*.58),fill='#84908a',width=2)
back=np.asarray(bg,dtype=float)/255
display=q[...,:3]*a+back*(1-a)
flat=Image.fromarray(np.uint8(np.clip(display,0,1)*255))
preview=Image.new('RGB',(1280,900),'#28312c');d=ImageDraw.Draw(preview)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
d.text((12,10),'R4 待用 / 同心圆边界 · 原稿卷纹与长回旋 · 暖橙金 · 取消全色gain / 非实景',font=font,fill='#f9ae61')
reference=Image.open(REF).convert('RGB');preview.paste(reference.crop((224,836,583,974)).resize((628,242)),(12,54))
d.text((12,310),'按原稿内卷主形修正过度规则化；只把圆形边界保持严格同心',font=small,fill='#ebc38c')
preview.paste(flat.resize((628,628)),(646,54));preview.paste(flat.resize((628,402)),(12,375))
d.text((12,810),'底光轻透、前半盘完整；网格仅验证通透，不进入生产素材',font=small,fill='#ebc38c')
preview.save(HERE/'seal-reference-original-scroll-colour-r4-final.jpg',quality=95,subsampling=0)
record=dict(status='pending root visual review; production not written',reference=str(REF.relative_to(ROOT)),sourcePathRecord='traced-paths.json',
    geometry='R2 visible-reference scrolls and long inner recurves restored; all boundary rings concentric exact circles, band motifs clipped between them. No R3 trefoil symbol.',
    palette=dict(core=[249,174,97],body=[236,148,65],halo=[227,107,31],fillRGBApprox=[255,116,30],haloRadii=[6.5,9]),
    fill='Very thin full radial warm wash alpha .070 baseline plus .018 centre/.014 rim; additional soft orange-gold spread follows engraved line mask at Gaussian 16/34px with alpha capped .09. Combined reflected light is stronger around engraving and softly spreads over the entire disk, including the front; no baked ground/opaque brown plate.',
    shaderRecommendation='Cancel global RGB*1.15; output raw display RGB premultiplied by alpha. Inspect native seal at same cue age before any separate glyph coverage or fill-emission correction. Current shaded terrain strongly affects the low-alpha fill; source RGB alone is not a matching proof.',
    shaderNotModified=True,currentProductionHash=before,productionStillUnchanged=sha(PROD)==before,
    output=dict(path=name,sha256=sha(HERE/name),pngBytes=(HERE/name).stat().st_size),currentPreview='seal-reference-original-scroll-colour-r4-final.jpg',
    review=dict(local='pending unique final diffuse-light sample inspection',native='pending after approved apply/build',user='pending'))
(HERE/'colour-r4-pending-provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
