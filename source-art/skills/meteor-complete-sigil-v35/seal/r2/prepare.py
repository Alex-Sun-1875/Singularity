"""One bounded v35 adjustment: concentric circles and monotone midtone lift.

SOURCE-ART ONLY. No production writes. The three organic recurves are not
redrawn. Monotone Hermite radial knots move only the three boundary annuli.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
ROOT=next(p for p in HERE.parents if (p/'src/cocos').is_dir())
PREPARE=BASE/'prepare-cloud.py'
prefix=PREPARE.read_text(encoding='utf8').split('# Relative fine ridges')[0]
assert '.save(' not in prefix and '.write_text(' not in prefix
ns={'__file__':str(PREPARE),'__name__':'read_only_registered_cloud'}
exec(compile(prefix,str(PREPARE),'exec'),ns)
old_e=ns['e'];old_alpha=ns['alpha'];N=1024;C=511.5;R=460.
smooth=ns['smooth'];sample2=ns['sample']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def sample(a,x,y):
    if a.ndim==2:return sample2(a,x,y)
    return np.stack([sample2(a[...,i],x,y) for i in range(a.shape[2])],axis=-1)
def circular_smooth(a,radius=2):
    # Tiny angular filtering removes subpixel peak-pick noise, not fire detail.
    offsets=np.arange(-radius*3,radius*3+1)
    w=np.exp(-offsets*offsets/(2*radius*radius));w/=w.sum()
    return sum(np.roll(a,int(o))*v for o,v in zip(offsets,w))
def fit_ellipse(x,y,weights):
    a=np.stack([x*x,x*y,y*y,x,y],axis=1)
    coef=np.linalg.lstsq(a*weights[:,None],weights,rcond=None)[0]
    q=np.array([[coef[0],coef[1]/2],[coef[1]/2,coef[2]]])
    centre=-.5*np.linalg.solve(q,coef[3:]);scale=1+centre@q@centre
    vals,vecs=np.linalg.eigh(q/scale);axes=1/np.sqrt(vals)
    return centre,vecs@np.diag(axes)@vecs.T,axes

angles=np.linspace(0,2*np.pi,720,endpoint=False)
cs=np.cos(angles);sn=np.sin(angles)
signal=old_e[...,1]+old_e[...,2]*.2
def radial_track(lo,hi,prior,sigma):
    r=np.arange(lo,hi+.001,.15)
    x=C+cs[:,None]*r;y=C+sn[:,None]*r
    s=sample2(signal,x,y)
    score=s*np.exp(-(r[None,:]-np.asarray(prior).reshape(-1,1))**2/(2*sigma*sigma))
    idx=score.argmax(axis=1)
    return circular_smooth(r[idx],1.15)
outer=radial_track(450,474,np.full(720,460.),6)
second=radial_track(435,452,np.full(720,444.5),4.5)
assert (outer-second>7).all()

# Fit the inner boundary independently of interior flame strokes; the prior
# follows the visible thin circle, not arbitrary maxima across the whole disc.
centre=np.array([511.5,489.]);matrix=np.diag([349.,330.]);offset=np.linspace(-15,15,151)
for iteration in range(4):
    base=np.stack([cs,sn],axis=1)@matrix.T+centre
    normals=np.stack([cs/matrix[0,0],sn/matrix[1,1]],axis=1)
    normals/=np.linalg.norm(normals,axis=1)[:,None]
    x=base[:,0,None]+normals[:,0,None]*offset;y=base[:,1,None]+normals[:,1,None]*offset
    s=sample2(signal,x,y);idx=(s*np.exp(-offset[None,:]**2/(2*7**2))).argmax(axis=1)
    xx=x[np.arange(720),idx];yy=y[np.arange(720),idx];strength=s[np.arange(720),idx]
    centre,matrix,axes=fit_ellipse(xx,yy,np.clip(strength,.05,1))
q=np.linalg.inv(matrix@matrix.T);direction=np.stack([cs,sn],axis=1)
delta=np.array([C,C])-centre
aa=np.einsum('ni,ij,nj->n',direction,q,direction)
bb=2*np.einsum('ni,ij,j->n',direction,q,delta);cc=delta@q@delta-1
prior=(-bb+np.sqrt(bb*bb-4*aa*cc))/(2*aa)
offset=np.linspace(-5,5,81)
rr=prior[:,None]+offset
s=sample2(signal,C+cs[:,None]*rr,C+sn[:,None]*rr)
idx=(s*np.exp(-offset[None,:]**2/(2*2.6**2))).argmax(axis=1)
inner=circular_smooth(rr[np.arange(720),idx],1.1)
inner_radius=float(axes.mean());second_radius=float(second.mean())

# Per-angle radial knots are strictly increasing. Unit slope at every knot
# retains the local engraving stroke thickness at the three corrected rims.
# The central recurves at r <= inner_radius-48 remain geometrically identical.
target=np.array([0.,inner_radius-48.,inner_radius,inner_radius+48.,424.,second_radius,460.,485.,724.])
assert (np.diff(target)>0).all()
source=np.broadcast_to(target[:,None],(len(target),720)).copy()
source[2]=inner;source[5]=second;source[6]=outer
assert (np.diff(source,axis=0)>0).all()
def hermite(r,angle_index):
    i=np.clip(np.searchsorted(target,r,side='right')-1,0,len(target)-2)
    x0=target[i];h=target[i+1]-x0;t=np.clip((r-x0)/h,0,1)
    y0=source[i,angle_index];y1=source[i+1,angle_index]
    value=(2*t**3-3*t*t+1)*y0+(t**3-2*t*t+t)*h+(-2*t**3+3*t*t)*y1+(t**3-t*t)*h
    derivative=((6*t*t-6*t)*y0+(3*t*t-4*t+1)*h+(-6*t*t+6*t)*y1+(3*t*t-2*t)*h)/h
    return value,derivative
test_r=np.linspace(0,724,5000)
test_ang=np.arange(720)[:,None]
_,derivative=hermite(test_r[None,:],test_ang)
assert float(derivative.min())>.05,'Radial mapping would fold'

y,x=np.mgrid[:N,:N];dx=x-C;dy=y-C;radius=np.hypot(dx,dy);angle=np.mod(np.arctan2(dy,dx),2*np.pi)
af=angle/(2*np.pi)*720;ai=np.floor(af).astype(int)%720;aj=(ai+1)%720;aw=af-np.floor(af)
ri,_=hermite(radius,ai);rj,_=hermite(radius,aj);source_radius=ri*(1-aw)+rj*aw
ratio=source_radius/np.maximum(radius,.001)
sx=C+dx*ratio;sy=C+dy*ratio
e=sample(old_e,sx,sy);alpha=sample2(old_alpha,sx,sy)

# Monotone energy lift: up to +28% for established low/mid energy. Above
# maxRGB .75 gain is exactly one, preserving hot-core colour and headroom.
maximum=e.max(axis=-1)
gain=1+.28*smooth((maximum-.015)/.10)*(1-smooth((maximum-.50)/.25))
gain=1+(gain-1)*smooth((alpha-.009)/.025)
lifted=e*gain[...,None]
# Raise optical support only when necessary to encode unchanged RGB ratios
# in RGBA8; low-contrast disc body remains additive in the light texture.
alpha=np.maximum(alpha,lifted.max(axis=-1))
rgb=np.clip(lifted/np.maximum(alpha[...,None],1e-8),0,1)
e=rgb*alpha[...,None]
red=Image.fromarray(np.uint8(np.clip(e[...,0],0,1)*255+.5),'L')
from PIL import ImageFilter
red_soft=np.asarray(red.filter(ImageFilter.GaussianBlur(.82)),float)/255
relative=np.maximum(0,e[...,0]-red_soft)/np.maximum(e[...,0],.025)
fine=smooth((relative-.025)/.18);hot=smooth((e[...,1]-.045)/.18)
fraction=np.clip(np.maximum(fine,hot)*.94,0,.94)
main_a=alpha*fraction;remaining=e*(1-fraction[...,None])
main=Image.fromarray(np.uint8(np.clip(np.concatenate([rgb,main_a[...,None]],axis=-1),0,1)*255+.5),'RGBA')
light_a=np.clip(remaining.max(axis=-1)/.20,0,1)
light=Image.fromarray(np.uint8(np.clip(np.concatenate([remaining,light_a[...,None]],axis=-1),0,1)*255+.5),'RGBA').resize((512,512),Image.Resampling.LANCZOS)
main_path=HERE/'fire-meteor-seal-colour-v35r2.png';light_path=HERE/'fire-meteor-seal-light-v35r2.png'
main.save(main_path,optimize=True);light.save(light_path,optimize=True)
effect=(BASE/'fire-seal-v35.effect').read_text(encoding='utf8').replace('v35','v35r2')
(HERE/'fire-seal-v35r2.effect').write_text(effect,encoding='utf8',newline='\n')

def compose(main,light):
    a=np.asarray(main,float)/255;l=np.asarray(light.resize((N,N),Image.Resampling.BILINEAR),float)/255
    out_a=a[...,3]+l[...,3]*.006*(1-a[...,3]);pm=a[...,:3]*a[...,3,None]+l[...,:3]
    return pm+ground*(1-out_a[...,None]),pm,out_a
ground=np.empty((N,N,3));ground[:]=np.array([39,45,42])/255
for row in range(0,N,64):ground[row:row+1]=np.array([49,55,51])/255
for col in range(0,N,64):ground[:,col:col+1]=np.array([49,55,51])/255
before,_,_=compose(Image.open(BASE/'fire-meteor-seal-colour-v35.png'),Image.open(BASE/'fire-meteor-seal-light-v35.png'))
after,pm,out_a=compose(main,light)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
canvas=Image.new('RGB',(1512,1040),'#202420');d=ImageDraw.Draw(canvas)
d.text((18,12),'v35r2 同心正圆校准 / 暗部与中间调温和提亮（实际shader计算，非实景）',font=font,fill='#efb583')
for label,data,px in [('当前v35：原亮度',before,18),('v35r2：局部圆环校准 + 红橙中调提亮',after,774)]:
    d.text((px,49),label,font=small,fill='#dfb497')
    im=Image.fromarray(np.uint8(np.clip(data,0,1)*255+.5),'RGB')
    canvas.paste(im.resize((720,720),Image.Resampling.LANCZOS),(px,78))
    canvas.paste(im.resize((720,219),Image.Resampling.LANCZOS),(px,812))
preview=HERE/'seal-v35r2-concentric-midtone-final.jpg';canvas.save(preview,quality=96,subsampling=0)

# Measure the encoded corrected hot ridges rather than only claiming that the
# mapping knots are circles. Keep no-source-color user acceptance separate.
def circle_error(image_energy,rad):
    rs=np.linspace(rad-3,rad+3,121)
    s=sample2(image_energy[...,1]+image_energy[...,2]*.2,C+cs[:,None]*rs,C+sn[:,None]*rs)
    peaks=rs[s.argmax(axis=1)]-rad
    return {'medianAbsPx':float(np.median(abs(peaks))),'p95AbsPx':float(np.quantile(abs(peaks),.95)),'maxAbsPx':float(abs(peaks).max())}
mid=(maximum>.08)&(maximum<.50)&(alpha>.04)
hot_pixels=maximum>.75
central=radius<=target[1]
reference_energy=sample(old_e,sx,sy)
measurable=reference_energy.max(axis=-1)>.01
normalised=e/np.maximum(e.sum(axis=-1)[...,None],1e-9)
reference_normalised=reference_energy/np.maximum(reference_energy.sum(axis=-1)[...,None],1e-9)
ratio_error=np.max(abs(normalised-reference_normalised)[measurable])
ramp=np.linspace(0,1,10001)
lift_ramp=ramp*(1+.28*smooth((ramp-.015)/.10)*(1-smooth((ramp-.50)/.25)))
minimum_lift_derivative=float(np.diff(lift_ramp).min()*10000)
assert minimum_lift_derivative>0
record={
 'revision':'v35r2-concentric-bounded-midtone','source':'../cloud-complete-fire-sigil.png','sourceSha256':sha(BASE/'cloud-complete-fire-sigil.png'),
 'sourceGeneration':'../cloud-generation.json','sourcePrompt':'../cloud-refinement-prompt.txt','basePreparationSha256':sha(PREPARE),
 'geometry':{'method':'Only three boundary annuli receive angularly tracked radial correction. Piecewise cubic Hermite inverse map has strictly increasing source knots and unit slope at every ring, retaining local stroke thickness.','targetCentre':[C,C],'targetRadii':[460.,second_radius,inner_radius],
 'currentInnerFitCentre':centre.tolist(),'currentInnerFitAxes':axes.tolist(),'centralGeometryLockedThroughRadius':float(target[1]),'targetRadialKnots':target.tolist(),
 'sourceKnotRanges':[[float(a.min()),float(a.max())] for a in source],'minimumDerivative':float(derivative.min()),'maxCentralCoordinateDisplacementPx':float(np.max(abs(source_radius[central]-radius[central]))),
 'circleChecksEncoded':{'outer':circle_error(pm,460.),'second':circle_error(pm,second_radius),'inner':circle_error(pm,inner_radius)},
 'scope':'No new design, no redraw of organic recurves; small radial attachment transitions near the inner boundary, central body unchanged. Ground circle/range/UV/lift untouched.'},
 'brightness':{'formula':'gain=1+.28*smooth((maxRGB-.015)/.10)*(1-smooth((maxRGB-.50)/.25)); near-zero alpha gated. Multiply all RGB energy channels equally. gain=1 exactly above maxRGB .75.','midGainMean':float(gain[mid].mean()),'midGainP50':float(np.median(gain[mid])),'maxGain':float(gain.max()),'hotMaxGainDeviation':float(np.max(abs(gain[hot_pixels]-1))),'maxRGBRatioErrorAbove001Energy':float(ratio_error),'minimumLiftCurveDerivative':minimum_lift_derivative,'monotoneEnergyCurve':True,'palette':'Original cloud red/orange/ember ratios, bright hot cores and along-line variation retained.'},
 'resources':[{'name':main_path.name,'size':[1024,1024],'role':'Registered raw fire RGB plus full-resolution optical line coverage','sha256':sha(main_path),'gpuBytes':4194304},{'name':light_path.name,'size':[512,512],'role':'Remaining warm RGB emission, A only0.006 weak absorption','sha256':sha(light_path),'gpuBytes':1048576}],
 'effect':{'name':'fire-seal-v35r2.effect','sha256':sha(HERE/'fire-seal-v35r2.effect'),'formula':'Unchanged: coverage=main.a*fade; alpha=coverage+light.a*.006*fade*(1-coverage); premul=main.rgb*coverage+light.rgb*fade; ONE/ONE_MINUS_SRC_ALPHA.'},
 'totalGpuBytes':5242880,'preview':preview.name,'previewDeclaration':'Side-by-side exact encoded shader computation on the same diagnostic dark green-grey grid. Not native Cocos/TapTap evidence.',
 'review':{'local':'Pending view of the one final circle/midtone candidate.','production':'Not published; current v35 capture inputs untouched.','native':'Pending root approval/build/actual capture; user acceptance not claimed.'}}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'preview':str(preview),'geometry':record['geometry'],'brightness':record['brightness'],'resources':record['resources']},ensure_ascii=False))
