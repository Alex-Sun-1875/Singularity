"""Register and split the ONE reviewed cloud refinement, without redrawing it.

The full-resolution colour/coverage holds clear engraving; half-resolution RGB
stores only its remaining translucent fire energy. E=RGB*A is preserved before
8-bit/half-resolution engineering quantisation. Writes source-art only.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'src/cocos').is_dir())
SOURCE=HERE/'cloud-complete-fire-sigil.png';N=1024;C=511.5;R=460.
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)=='5ac98e948709f17c50168949d7d30a67dab50aa5d80d128d03f0227222c88b06'
src=np.asarray(Image.open(SOURCE).convert('RGBA'),dtype=float)/255

def smooth(a):a=np.clip(a,0,1);return a*a*(3-2*a)
def sample(a,x,y):
    x=np.clip(x,0,a.shape[1]-1.001);y=np.clip(y,0,a.shape[0]-1.001)
    ix=x.astype(int);iy=y.astype(int);u=x-ix;v=y-iy
    return a[iy,ix]*(1-u)*(1-v)+a[iy,ix+1]*u*(1-v)+a[iy+1,ix]*(1-u)*v+a[iy+1,ix+1]*u*v
def blur(a,radius):
    return np.asarray(Image.fromarray(np.float32(a),'F').convert('L').filter(ImageFilter.GaussianBlur(radius)),float)

# Fit only the outer hot ridge. Choosing the outermost sufficiently strong
# local maximum prevents the inner of the double rims from biasing the fit.
energy=src[...,:3]*src[...,3,None]
angles=np.linspace(0,2*np.pi,360,endpoint=False);radii=np.linspace(530,610,401)
px=619+radii[None,:]*np.cos(angles[:,None]);py=619+radii[None,:]*np.sin(angles[:,None])
signal=sample(energy[...,1]+energy[...,2]*.2,px,py)
peaks=(signal[:,1:-1]>signal[:,:-2])&(signal[:,1:-1]>=signal[:,2:])&(signal[:,1:-1]>signal.max(1)[:,None]*.55)
index=np.where(peaks,np.arange(1,400)[None,:],0).max(1)
assert (index>0).all()
xx=px[np.arange(360),index];yy=py[np.arange(360),index]
design=np.stack([xx*xx,xx*yy,yy*yy,xx,yy],axis=1)
coef=np.linalg.lstsq(design,np.ones(360),rcond=None)[0]
quadratic=np.array([[coef[0],coef[1]/2],[coef[1]/2,coef[2]]])
centre=-.5*np.linalg.solve(quadratic,coef[3:])
scale=1+centre@quadratic@centre
values,vectors=np.linalg.eigh(quadratic/scale);axes=1/np.sqrt(values)
matrix=vectors@np.diag(axes)@vectors.T
# Symmetric affine stretch, not a rotation of the engraving.
affine=(matrix[0,0]/R,matrix[0,1]/R,centre[0]-(matrix[0,0]+matrix[0,1])*C/R,
        matrix[1,0]/R,matrix[1,1]/R,centre[1]-(matrix[1,0]+matrix[1,1])*C/R)
def register(channel):
    im=Image.fromarray(np.float32(channel),'F')
    return np.maximum(0,np.asarray(im.transform((N,N),Image.Transform.AFFINE,affine,Image.Resampling.BICUBIC),float))
alpha=np.clip(register(src[...,3]),0,1)
e=np.stack([register(energy[...,i]) for i in range(3)],axis=-1)
y,x=np.mgrid[:N,:N];radius=np.hypot((x-C)/R,(y-C)/R)
# Noise cleanup is confined to near-zero coverage and the soft outer halo.
alpha_purity=smooth((alpha-.002)/.007)
feather=1-smooth((radius-1.045)/.067)
e*= (alpha_purity*feather)[...,None];alpha*=alpha_purity*feather
rgb=np.clip(e/np.maximum(alpha[...,None],1e-8),0,1)
e=rgb*alpha[...,None]

# Relative fine ridges include low-brightness red engraving, while measured
# green/orange hot cores stay almost entirely in the 1024 coverage texture.
red=Image.fromarray(np.uint8(np.clip(e[...,0],0,1)*255+.5),'L')
red_soft=np.asarray(red.filter(ImageFilter.GaussianBlur(.82)),float)/255
relative=np.maximum(0,e[...,0]-red_soft)/np.maximum(e[...,0],.025)
fine=smooth((relative-.025)/.18)
hot=smooth((e[...,1]-.045)/.18)
line_weight=np.maximum(fine,hot)
fraction=np.clip(line_weight*.94,0,.94)
main_alpha=alpha*fraction
remaining=e*(1-fraction[...,None])
main=Image.fromarray(np.uint8(np.clip(np.concatenate([rgb,main_alpha[...,None]],axis=-1),0,1)*255+.5),'RGBA')
light_alpha=np.clip(remaining.max(axis=-1)/.20,0,1)
light=Image.fromarray(np.uint8(np.clip(np.concatenate([remaining,light_alpha[...,None]],axis=-1),0,1)*255+.5),'RGBA').resize((512,512),Image.Resampling.LANCZOS)
main_path=HERE/'fire-meteor-seal-colour-v35.png';light_path=HERE/'fire-meteor-seal-light-v35.png'
main.save(main_path,optimize=True);light.save(light_path,optimize=True)

# Rebuild exactly the production two-sampler shader from encoded bytes.
a=np.asarray(main,float)/255;l=np.asarray(light.resize((N,N),Image.Resampling.BILINEAR),float)/255
out_alpha=a[...,3]+l[...,3]*.006*(1-a[...,3])
premul=a[...,:3]*a[...,3,None]+l[...,:3]
ground=np.empty((N,N,3));ground[:]=np.array([39,45,42])/255
for row in range(0,N,64):ground[row:row+1]=np.array([49,55,51])/255
for col in range(0,N,64):ground[:,col:col+1]=np.array([49,55,51])/255
flat=np.clip(premul+ground*(1-out_alpha[...,None]),0,1)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
canvas=Image.new('RGB',(1512,1030),'#202420');d=ImageDraw.Draw(canvas)
d.text((18,12),'v35 完整独立红橙火纹层 / 1024清晰雕纹 + 512原色柔光',font=font,fill='#efb583')
d.text((18,47),'下图按实际双采样shader还原在暗绿灰地面上的结果；材质计算样张，非游戏实景。',font=small,fill='#d4b193')
im=Image.fromarray(np.uint8(flat*255+.5),'RGB')
canvas.paste(im.resize((800,800),Image.Resampling.LANCZOS),(12,106))
d.text((852,80),'后侧完整圈纹 / 清晰亮芯与红橙笔身',font=small,fill='#e3b98e')
canvas.paste(im.crop((238,26,795,583)).resize((620,620),Image.Resampling.LANCZOS),(850,111))
d.text((852,758),'同一纹理的地面透视示意',font=small,fill='#e3b98e')
canvas.paste(im.resize((620,226),Image.Resampling.LANCZOS),(850,790))
d.text((20,955),'原始内部纹样/明暗仅随全局圆形校准变换；无手绘补纹、无换色、无全局亮度增益。',font=small,fill='#d4b193')
d.text((20,984),'圆心/范围/地面UV不变；低吸收透明光场可与其他特效叠加，实际遮挡与重叠仍待Cocos实录。',font=small,fill='#d4b193')
preview=HERE/'seal-v35-cloud-material-final.jpg';canvas.save(preview,quality=96,subsampling=0)
Image.fromarray(np.uint8(flat*255+.5),'RGB').save(HERE/'seal-v35-cloud-material-front.png')
generation=json.loads((HERE/'cloud-generation.json').read_text(encoding='utf8'))
core=(line_weight>.80)&(e[...,0]>.20)
disc=(radius<1)&(line_weight<.1)
record={
 'revision':'v35-cloud-complete-fire-sigil-final','source':SOURCE.name,'sourceSha256':sha(SOURCE),
 'generation':generation,'prompt':'cloud-refinement-prompt.txt','preparationScript':'prepare-cloud.py',
 'registration':{'method':'Single symmetric ellipse-to-circle affine from 360 outermost hot-ridge samples; no local warp, path edit or engraving rotation.','sourceCentre':centre.tolist(),'sourceAxes':axes.tolist(),'sourceSymmetricMatrix':matrix.tolist(),'targetCentre':[C,C],'targetRadius':R,'visibleDiameterFraction':460/512,'orientation':'Image top=far, bottom=near. Existing ground UV/range/lift retained.'},
 'cleanup':{'alphaPurity':'Only source alpha .002..009 softened to remove near-zero transparent-edge red specks.','outerFeather':'Radial 1.045..1.112; complete hot rim at r1 remains untouched.'},
 'split':{'principle':'Registered original energy E=RGB*A. Main RGB retains raw artist colour; A=registered alpha*f, f<=.94 from original hot cores/coherent red ridges. Light RGB=E*(1-f), without fixed palette or gain.','sharpness':'Coherent hot cores retain94% in 1024 main; weak red ridges use relative source colour-energy contrast. The clear original is not blurred/sharpened or redrawn.','colour':'Original cloud vermilion/ember-red body, orange transition and local bright cores preserved; no return to yellow-gold palette.'},
 'resources':[{'name':main_path.name,'size':[1024,1024],'role':'RGB=registered raw artist colour; A=engraving optical coverage, mostly original clear-core energy','sha256':sha(main_path),'gpuBytes':4194304},{'name':light_path.name,'size':[512,512],'role':'RGB=remaining original premultiplied fire energy; A=only 0.006 weak absorption support, not direct output opacity','sha256':sha(light_path),'gpuBytes':1048576}],
 'totalGpuBytes':5242880,'formula':'coverage=colour.a*fade; alpha=coverage+light.a*.006*fade*(1-coverage); premul=colour.rgb*coverage+light.rgb*fade; blend ONE/ONE_MINUS_SRC_ALPHA. No fixed recolouring, no global gain.',
 'metrics':{'energyMeanAbsoluteQuantisationError':float(np.mean(np.abs(premul-e))),'hotCoreMainEnergyFractionMean':float(fraction[core].mean()),'hotCorePixels':int(core.sum()),'quietDiscMeanOutputAlpha':float(out_alpha[disc].mean()),'outputEnergyChannelSums':premul.sum(axis=(0,1)).tolist(),'sourceRegisteredEnergyChannelSums':e.sum(axis=(0,1)).tolist()},
 'preview':preview.name,'previewDeclaration':'Exact encoded two-texture production formula on diagnostic dark green-grey ground. This is a shader/material computation, not native Cocos/TapTap capture.',
 'review':{'cloudResult':'Root visually inspected source: complete, clear, original-type asymmetric long recurves and fire red/orange material. Generation success and art review recorded separately in cloud-generation.json.','local':'Pending view of this single engineering candidate.','production':'Not published.','native':'Pending root standard build/capture; user/device acceptance not claimed.'}}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'preview':str(preview),'registration':record['registration'],'metrics':record['metrics'],'resources':record['resources']},ensure_ascii=False))
