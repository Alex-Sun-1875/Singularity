"""One faithful reference-pixel seal candidate; no hand-drawn engraving.

Writes source-art only. A single affine ellipse-to-circle correction preserves
the relative positions of every visible internal curve. Optical coverage and
reference-coloured diffuse light remain separate, without a fixed palette.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'src/cocos').is_dir())
REF=ROOT/'source-art/skills/fire-reference-alignment-v32/assets/approved-reference.png'
BOX=(216,821,578,981)
CENTRE=(395.48,901.09);RADII=(164.29,61.93)
N=1024;C=(N-1)/2;R=460.0
source=np.asarray(Image.open(REF).convert('RGB'),dtype=np.float32)/255
p=source[BOX[1]:BOX[3],BOX[0]:BOX[2]]
y,x=np.mgrid[BOX[1]:BOX[3],BOX[0]:BOX[2]]
nx=(x-CENTRE[0])/RADII[0];ny=(y-CENTRE[1])/RADII[1]
rr=np.hypot(nx,ny)

def smooth(v):
    v=np.clip(v,0,1);return v*v*(3-2*v)

def blur(a,sigma):
    k=np.arange(-int(np.ceil(sigma*3)),int(np.ceil(sigma*3))+1)
    kernel=np.exp(-k*k/(2*sigma*sigma));kernel/=kernel.sum()
    def axis(v,ax):
        widths=[(0,0)]*v.ndim;widths[ax]=(len(k)//2,len(k)//2)
        return np.apply_along_axis(lambda q:np.convolve(q,kernel,mode='valid'),ax,np.pad(v,widths,mode='reflect'))
    return axis(axis(a,0),1)

def sample(a,xx,yy):
    xx=np.clip(xx,0,a.shape[1]-1.001);yy=np.clip(yy,0,a.shape[0]-1.001)
    ix=xx.astype(int);iy=yy.astype(int);u=xx-ix;v=yy-iy
    if a.ndim==3:u=u[...,None];v=v[...,None]
    return a[iy,ix]*(1-u)*(1-v)+a[iy,ix+1]*u*(1-v)+a[iy+1,ix]*(1-u)*v+a[iy+1,ix+1]*u*v

occ=(1-smooth((y-873)/8))*smooth((x-348)/7)*(1-smooth((x-456)/7))

# Estimate the ordinary stone colour from visible, unsaturated neighbouring
# ground. The source's own cool-channel texture carries dark joints; no floor
# image is baked into either output resource.
known=(p[...,0]-p[...,2]<.15)&(p.max(2)<.50)&(rr>1.04)&(rr<1.30)
fit=[np.polyfit(p[...,2][known],p[...,i][known],1) for i in (0,1)]
neutral=(p[...,0]-p[...,2]<.155)&(p.max(2)<.53)
neutral&=~((x>358)&(x<466)&(y<880))
weight=blur(neutral.astype(float),12)
blue=blur(p[...,2]*neutral,12)/np.maximum(weight,.001)
fallback=float(np.median(p[...,2][known]))
blue=np.where(weight>.025,blue,fallback)
# Negative fine stone detail belongs to the substrate. Positive blue ridges
# can be part of actual gold engraving and are retained in the effect.
blue+=np.minimum(0,p[...,2]-blur(p[...,2],2.0))*(1-occ)
background=np.stack([fit[0][0]*blue+fit[0][1],fit[1][0]*blue+fit[1][1],blue],axis=-1)
background=np.clip(background,.025,.60)
excess=np.maximum(0,p-background)
warm=p[...,0]-p[...,2]-(background[...,0]-background[...,2])
support=smooth((warm-.003)/.030)
excess*=support[...,None]

# A local-only meteor matte, not a crop of an entire rear half. Its covered
# outer-band segment is completed from the reference's corresponding visible
# front-band pixels. Unknown interior engraving is conservatively absent.
edge=1-smooth((rr-1.015)/.025)
excess*=edge[...,None]
clean=excess*(1-occ[...,None])
donor=sample(excess,2*CENTRE[0]-x-BOX[0],2*CENTRE[1]-y-BOX[1])
band=smooth((rr-.80)/.06)
clean+=donor*(occ*band)[...,None]
# Hidden inner-disc light uses only surrounding valid ORIGINAL light samples,
# normalized across the invalid meteor silhouette. It contains no donor line
# shape or dark meteor texture, and never clears the covered disc to zero.
valid=(1-occ)*edge
fill=blur(excess*valid[...,None],15)/np.maximum(blur(valid,15)[...,None],.001)
clean+=fill*(occ*(1-band))[...,None]

# Preserve all reference colour energy. The light field is a smooth, bounded
# part of the same measured RGB energy, never a constant radial colour fill.
# K + L = clean exactly, before resource resampling/8-bit quantisation.
light=np.minimum(clean,blur(clean,2.6)*.84)
ink=np.maximum(0,clean-light)
coverage=np.max(ink/np.maximum(1-background,.20),axis=-1)
coverage=np.clip(coverage*1.22,0,.96)
foreground=background+ink/np.maximum(coverage[...,None],1e-7)
foreground=np.clip(foreground,0,1)
foreground[coverage<.001]=0

oy,ox=np.mgrid[:N,:N];u=(ox-C)/R;v=(oy-C)/R;rad=np.hypot(u,v)
sx=CENTRE[0]+u*RADII[0]-BOX[0];sy=CENTRE[1]+v*RADII[1]-BOX[1]
field=np.concatenate([foreground*coverage[...,None],coverage[...,None]],axis=-1)
out=sample(field,sx,sy)
clip=1-smooth((rad-1.017)/.025)
out*=clip[...,None]
colour=out[...,:3]/np.maximum(out[...,3,None],1e-7)
rgba=np.concatenate([colour,out[...,3,None]],axis=-1)
main=Image.fromarray(np.uint8(np.clip(rgba,0,1)*255+.5),'RGBA')
main_path=HERE/'fire-meteor-seal-colour-v34r2.png';main.save(main_path,optimize=True)

illum=sample(light,sx,sy)*clip[...,None]
foot=np.clip(np.max(illum,axis=-1)/.18,0,1)
light_rgba=np.concatenate([illum,foot[...,None]],axis=-1)
light_img=Image.fromarray(np.uint8(np.clip(light_rgba,0,1)*255+.5),'RGBA').resize((512,512),Image.Resampling.LANCZOS)
light_path=HERE/'fire-meteor-seal-light-v34r2.png';light_img.save(light_path,optimize=True)

# Exact material math, including the tiny light-field absorption, reconstructed
# from the encoded PNGs, not the pre-quantisation arrays.
a=np.asarray(main,dtype=np.float32)/255
l=np.asarray(light_img.resize((1024,1024),Image.Resampling.BILINEAR),dtype=np.float32)/255
alpha=a[...,3]+l[...,3]*.006*(1-a[...,3])
premul=a[...,:3]*a[...,3,None]+l[...,:3]
estimated_b=sample(background,sx,sy)
reconstruction=premul+estimated_b*(1-alpha[...,None])

# Reproject to exactly the original ellipse and crop coordinates. This makes
# placement/pattern differences assessable independently of native camera FOV.
xx=(nx*R+C);yy=(ny*R+C)
rp=sample(premul,xx,yy);ra=sample(alpha,xx,yy)
reproject=rp+background*(1-ra[...,None])
original=p.copy()
# Use original ground outside the effect support, plus original meteor pixels
# solely for the diagnostic same-camera comparison. They are absent in assets.
reproject=np.where((rr>1.055)[...,None],original,reproject)
reproject=reproject*(1-occ[...,None])+original*occ[...,None]
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
canvas=Image.new('RGB',(1512,1020),'#202420');d=ImageDraw.Draw(canvas)
d.text((20,12),'原稿逐像素法阵 / 同椭圆回投与材质计算候选（非游戏实景）',font=font,fill='#eec28e')
for title,data,px in [('原稿：原机位 / 原颜色',original,18),('提取素材：同机位回投 / 估计原石地',reproject,762)]:
    d.text((px,48),title,font=small,fill='#e4c5a0')
    im=Image.fromarray(np.uint8(np.clip(data,0,1)*255+.5),'RGB').resize((724,320),Image.Resampling.LANCZOS)
    canvas.paste(im,(px,77))
d.text((18,423),'正视：同一原稿像素去椭圆；非重新描摹',font=small,fill='#e4c5a0')
d.text((762,423),'材质在暗灰地面上的计算示意 / 不代表实景验收',font=small,fill='#e4c5a0')
ground=np.empty((1024,1024,3));ground[:]=np.array([39,45,42])/255
for row in range(0,1024,64):ground[row:row+1]=np.array([49,55,51])/255
for col in range(0,1024,64):ground[:,col:col+1]=np.array([49,55,51])/255
flat_a=Image.fromarray(np.uint8(np.clip(reconstruction,0,1)*255+.5),'RGB').resize((552,552),Image.Resampling.LANCZOS)
flat_b=Image.fromarray(np.uint8(np.clip(premul+ground*(1-alpha[...,None]),0,1)*255+.5),'RGB').resize((552,552),Image.Resampling.LANCZOS)
canvas.paste(flat_a,(92,456));canvas.paste(flat_b,(844,456))
preview=HERE/'seal-v34r2-reference-reprojection-cleared-final.jpg';canvas.save(preview,quality=96,subsampling=0)
Image.fromarray(np.uint8(np.clip(background,0,1)*255+.5),'RGB').save(HERE/'estimated-source-stone.png')

sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
record={
 'revision':'v34r2-direct-reference-rgb','source':str(REF.relative_to(ROOT)),'sourceSha256':sha(REF),
 'sourceCrop':BOX,'deprojection':{'centre':CENTRE,'radii':RADII,'targetCentre':[C,C],'targetRadius':R,'orientation':'image top=far side, bottom=near side; no V flip/rotation'},
 'method':'Single affine source-pixel correction. Neutral stone fitted from neighbouring unlit original pixels; actual RGB excess split into measured smooth light and residual engraving. No manual paths, fixed foreground palette, top-hat-only peak removal or uniform full-disk colour.',
 'floorFitRedGreenVsBlue':[v.tolist() for v in fit],
 'occlusion':'Entire meteor-covered rear-centre silhouette removed (source x348..463,y<881), including cool-channel substrate detail. Only rear outer band r>.80 locally uses 180-degree corresponding visible original front-band donor. Hidden interior linework is not invented; RGB light there is smoothly normalized-interpolated from surrounding valid original light samples. Diagnostic alone overlays original meteor for same-camera comparison.',
 'resources':[
  {'name':main_path.name,'size':[1024,1024],'role':'RGB=per-pixel background-decontaminated original foreground; A=optical engraving coverage; straight RGBA','sha256':sha(main_path),'gpuBytes':4194304},
  {'name':light_path.name,'size':[512,512],'role':'RGB=reference-coloured additive diffuse/near-stroke energy, not fixed palette; A=light support for 0.006 weak absorption, not direct output opacity','sha256':sha(light_path),'gpuBytes':1048576}
 ],'totalGpuBytes':5242880,'formula':'glyph=main.a*fade; light=lightTexture.rgb*fade; alpha=glyph+lightTexture.a*.006*fade*(1-glyph); premul=main.rgb*glyph+light; out=premul+ground*(1-alpha). ONE/ONE_MINUS_SRC_ALPHA. No gain or colour-space conversion.',
 'preview':preview.name,'previewDeclaration':'Exact encoded-PNG material formula; same-ellipse reprojection onto estimated source stone + original meteor as diagnostic only. Not native Cocos / TapTap evidence.',
 'metrics':{'mainCoverageP50P90P99':np.quantile(a[...,3][rad<1],[.5,.9,.99]).tolist(),'lightRMeanInside':float(l[...,0][rad<1].mean()),'sourceRoundtripMeanAbsoluteErrorNonOccluded':float(np.mean(np.abs(reproject-original)[(rr<1)&(occ<.01)]))},
 'review':{'local':'Pending view of this unique candidate','production':'Not published','native':'Pending root build/capture','user':'Previous v34 uniform-palette proposal rejected; this replacement is pending review','generation':'None; deterministic Pillow/NumPy from approved reference'}
}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
