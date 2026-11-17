"""Measured native-flame colour grade only; no geometry/alpha/intensity edit.

Fits a brightness-conditioned, temperature-rank-preserving colour lookup to
the actual .65s flame without a seal. Atlas is an independent palette check.
Only G/B bytes change; red intensity and alpha of both textures are retained.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent;ROOT=next(p for p in HERE.parents if (p/'src/cocos').is_dir())
BASE=ROOT/'source-art/skills/meteor-complete-sigil-v35/seal/r2'
PURE=ROOT/'source-art/skills/meteor-ignition-glow-v34/final-empty-r1/media/impact-0650ms.jpg'
BACKGROUND=PURE.with_name('impact-4600ms.jpg')
CURRENT=ROOT/'source-art/skills/meteor-complete-sigil-v35/final2-empty-r1/media/impact-0650ms.jpg'
SEAL_PREVIEW=ROOT/'source-art/skills/meteor-complete-sigil-v35/final2-empty-r1/early/FIR_02-seal-preview.jpg'
ATLAS=ROOT/'src/cocos/assets/resources/vfx/production/fire-meteor-burst-v32.png'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:np.asarray(Image.open(p).convert('RGBA'),dtype=float)/255
main0=read(BASE/'fire-meteor-seal-colour-v35r2.png');light0=read(BASE/'fire-meteor-seal-light-v35r2.png')
def sample(a,x,y):
    x=np.clip(x,0,a.shape[1]-1.001);y=np.clip(y,0,a.shape[0]-1.001)
    ix=x.astype(int);iy=y.astype(int);u=x-ix;v=y-iy
    if a.ndim==3:u=u[...,None];v=v[...,None]
    return a[iy,ix]*(1-u)*(1-v)+a[iy,ix+1]*u*(1-v)+a[iy+1,ix]*(1-u)*v+a[iy+1,ix+1]*u*v
fire=np.asarray(Image.open(PURE).convert('RGB'),float)/255
bg=np.asarray(Image.open(BACKGROUND).convert('RGB'),float)/255
fire_alpha=np.clip((fire[...,0]-bg[...,0])/np.maximum(1.10-bg[...,0],.2),0,1)
fire_energy=np.maximum(0,fire-bg*(1-fire_alpha[...,None]))
roi=np.zeros(fire.shape[:2],bool);roi[390:1065,55:1135]=True;roi[390:760,1060:1135]=False
warm=roi&(fire[...,0]-bg[...,0]>.03)&(fire[...,1]-bg[...,1]>.01)
fv=fire_energy[...,0];fc=fire_energy/np.maximum(fv[...,None],.001)
ft=(fc@np.array([.2126,.7152,.0722]))
warm&=(fv>.035)&(fc[...,1]<1.02)&(fc[...,2]<.90)
native_stats=[]
fy=fire_energy@np.array([.2126,.7152,.0722])
for label,lo,hi in [('low',.15,.35),('mid',.45,.65),('hot',.88,.98)]:
    lower,upper=np.quantile(fy[warm],[lo,hi]);mask=warm&(fy>=lower)&(fy<=upper)
    native_stats.append({'label':label,'nativeEnergyYQuantiles':[lo,hi],'sampleCount':int(mask.sum()),
      'displayRGBMedian':np.rint(np.median(fire[mask],axis=0)*255).astype(int).tolist(),
      'emittedNormalisedRGBMedian':np.median(fc[mask],axis=0).tolist(),'emittedRedMedian':float(np.median(fv[mask]))})

# The same shader phase samples atlas frames2/3 with blend.4 and RGB gain1.10.
atlas=read(ATLAS);h,w=atlas.shape[:2];cw=w//4;ch=h//4
f2=atlas[:ch,2*cw:3*cw];f3=atlas[:ch,3*cw:4*cw]
ae=(f2[...,:3]*f2[...,3,None]*.6+f3[...,:3]*f3[...,3,None]*.4)*1.10
aa=f2[...,3]*.6+f3[...,3]*.4;av=ae.max(axis=-1);ac=ae/np.maximum(av[...,None],.001);at=ac@np.array([.2126,.7152,.0722])
atlas_stats=[]
for label,lo,hi in [('low',.15,.35),('mid',.45,.65),('hot',.88,.98)]:
    lower,upper=np.quantile(at[aa>.25],[lo,hi]);mask=(aa>.25)&(at>=lower)&(at<=upper)
    atlas_stats.append({'label':label,'normalisedRGBMedian':np.median(ac[mask],axis=0).tolist(),'sampleCount':int(mask.sum())})

# Learn the total emitted colour, so low-alpha light-only regions receive the
# same flame-family correction as the opaque line cores.
lup=np.asarray(Image.fromarray(np.uint8(light0*255+.5),'RGBA').resize((1024,1024),Image.Resampling.BILINEAR),float)/255
old_energy=main0[...,:3]*main0[...,3,None]+lup[...,:3]
sv=old_energy[...,0]*.9;sc=old_energy/np.maximum(old_energy[...,0,None],.001);st=sc@np.array([.2126,.7152,.0722])
anchors=np.array([.06,.18,.32,.49,.66,.82,.96])
quantiles=np.linspace(.025,.975,31)
lookups=[];mapped=[]
for anchor in anchors:
    band=.11 if anchor<.8 else .13
    sm=(sv>max(.014,anchor-band))&(sv<anchor+band)
    tm=warm&(fv>max(.025,anchor-band))&(fv<anchor+band)
    assert sm.sum()>100 and tm.sum()>100
    source_q=np.quantile(st[sm],quantiles)
    target_q=np.quantile(ft[tm],quantiles)
    colours=[]
    for q in quantiles:
        lo,hi=np.quantile(ft[tm],[max(0,q-.022),min(1,q+.022)])
        take=tm&(ft>=lo)&(ft<=hi)
        colour=np.median(fc[take],axis=0)
        colours.append([1.,float(np.clip(colour[1],0,1)),float(np.clip(colour[2],0,.9))])
    colours=np.array(colours)
    # Temperature rank varies along the original engraving. No flat single
    # orange replaces its local hot/cool and light/dark transitions.
    g=np.interp(st,source_q,colours[:,1]);b=np.interp(st,source_q,colours[:,2])
    mapped.append(np.stack([np.ones_like(g),g,b],axis=-1))
    lookups.append({'emittedRedAnchorAtOpacity09':float(anchor),'sourceCount':int(sm.sum()),'nativeCount':int(tm.sum()),
      'sourceTemperatureQuantiles':source_q.tolist(),'nativeTemperatureQuantiles':target_q.tolist(),'nativeRGBQuantiles':colours.tolist()})
indices=np.clip(np.searchsorted(anchors,sv,side='right')-1,0,len(anchors)-2)
t=np.clip((sv-anchors[indices])/(anchors[indices+1]-anchors[indices]),0,1)
palette=np.empty_like(old_energy)
for i in range(len(anchors)-1):
    select=indices==i
    palette[select]=mapped[i][select]*(1-t[select,None])+mapped[i+1][select]*t[select,None]
main=main0.copy();main[...,1:3]=palette[...,1:3]*main0[...,0,None]
# Keep original light red/alpha bytes while energy-weighting the downsampled
# target chroma; no colour fringe or alpha/body density change is introduced.
weight=lup[...,0]
for channel in (1,2):
    num=np.asarray(Image.fromarray(np.float32(palette[...,channel]*weight),'F').resize((512,512),Image.Resampling.LANCZOS),float)
    den=np.asarray(Image.fromarray(np.float32(weight),'F').resize((512,512),Image.Resampling.LANCZOS),float)
    if channel==1:light=light0.copy()
    light[...,channel]=np.clip(num/np.maximum(den,.00001),0,1)*light0[...,0]
main_bytes=np.uint8(np.clip(main,0,1)*255+.5);light_bytes=np.uint8(np.clip(light,0,1)*255+.5)
assert np.array_equal(main_bytes[:,:,[0,3]],np.uint8(main0[:,:,[0,3]]*255+.5))
assert np.array_equal(light_bytes[:,:,[0,3]],np.uint8(light0[:,:,[0,3]]*255+.5))
main_path=HERE/'fire-meteor-seal-colour-v36.png';light_path=HERE/'fire-meteor-seal-light-v36.png'
Image.fromarray(main_bytes,'RGBA').save(main_path,optimize=True);Image.fromarray(light_bytes,'RGBA').save(light_path,optimize=True)
main=main_bytes/255;light=light_bytes/255

# Project the material into the actual camera/ground ellipse measured from
# the native seal-only frame. Reuse exactly ONE actual pure-flame .65s frame
# for both before/after. This is labelled computation, never new-native proof.
seal=np.asarray(Image.open(SEAL_PREVIEW).convert('RGB'),float)/255
angle=np.linspace(0,2*np.pi,720,endpoint=False);r=np.linspace(.975,1.025,201)
xx=594+570*np.cos(angle[:,None])*r;yy=817+363*np.sin(angle[:,None])*r
s=sample(seal[...,0]-bg[...,0],xx,yy)*np.exp(-(r[None,:]-1)**2/.0003)
pi=s.argmax(axis=1);xx=xx[np.arange(720),pi];yy=yy[np.arange(720),pi]
design=np.stack([xx*xx,yy*yy,xx,yy],axis=1);coef=np.linalg.lstsq(design,np.ones(720),rcond=None)[0]
cx=-coef[2]/(2*coef[0]);cy=-coef[3]/(2*coef[1]);scale=1+coef[0]*cx*cx+coef[1]*cy*cy
rx=np.sqrt(scale/coef[0]);ry=np.sqrt(scale/coef[1])
crop=(0,385,1220,1225);Y,X=np.mgrid[crop[1]:crop[3],crop[0]:crop[2]]
tx=511.5+(X-cx)/rx*460;ty=511.5+(Y-cy)/ry*460
base_fire=fire[crop[1]:crop[3],crop[0]:crop[2]];base_bg=bg[crop[1]:crop[3],crop[0]:crop[2]]
af=fire_alpha[crop[1]:crop[3],crop[0]:crop[2]]
def composite(m,l):
    a=sample(m,tx,ty);ll=sample(l,tx/2-.25,ty/2-.25)
    coverage=a[...,3]*.9;alpha=coverage+ll[...,3]*.006*.9*(1-coverage)
    pm=a[...,:3]*coverage[...,None]+ll[...,:3]*.9
    return np.clip(base_fire+(pm-base_bg*alpha[...,None])*(1-af[...,None]),0,1)
before=composite(main0,light0);after=composite(main,light)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
canvas=Image.new('RGB',(1760,1120),'#202420');d=ImageDraw.Draw(canvas)
d.text((18,12),'v36 与实际地火校色 / 同一原生纯火焰 .65s 帧叠加两版材质',font=font,fill='#e4c192')
d.text((18,44),'上排为按真实机位计算的候选合成，非新游戏实录；火焰、背景、圆环、alpha、红通道强度完全相同。',font=small,fill='#cdb49b')
for title,data,at in [('当前v35r2发射色：偏红',before,(16,102)),('v36：从实际火焰分位采色的橙/亮橙',after,(894,102))]:
    d.text((at[0],76),title,font=small,fill='#e8c099')
    im=Image.fromarray(np.uint8(data*255+.5),'RGB').resize((850,585),Image.Resampling.LANCZOS);canvas.paste(im,at)
d.text((18,712),'采样：v34 原生 impact +650ms（法阵已消失），减同机位 +4600ms 空地；ROI避开人物与UI。',font=small,fill='#d8b798')
d.text((18,742),'归一发射RGB，按原生火焰Y分位：暗 / 中 / 亮；burst-v32 atlas相位2→3、blend .4作独立核对。',font=small,fill='#d8b798')
for i,entry in enumerate(native_stats):
    px=20+i*570;colour=np.array(entry['emittedNormalisedRGBMedian']);rgb=np.uint8(np.clip(colour,0,1)*255)
    d.rectangle((px,785,px+85,840),fill=tuple(rgb));label={'low':'暗部','mid':'中间调','hot':'亮部'}[entry['label']]
    d.text((px+105,784),label+' 发射色 '+str([round(float(v),3) for v in colour]),font=small,fill='#e4c6a0')
    d.text((px+105,815),'实景RGB中位 '+str(entry['displayRGBMedian']),font=small,fill='#c6ad94')
d.text((18,870),'保持：两张图 R / A 字节完全不变；同心圆/纹样/亮暗排序/线芯与halo分层/时序不变；只改G/B色比。',font=small,fill='#dfbf9b')
actual=np.asarray(Image.open(CURRENT).convert('RGB'))[510:1160,50:1160]
canvas.paste(Image.fromarray(actual).resize((540,316),Image.Resampling.LANCZOS),(18,796)) if False else None
d.text((18,915),'取样方法：以 burst shader红通道1.10上界估计火焰覆盖，逐像素还原前景；温度排序映射保留原沿线深浅。',font=small,fill='#cbb298')
d.text((18,947),'纯火源：meteor-ignition-glow-v34/final-empty-r1/media/impact-0650ms.jpg；实际新色仍需标准构建复查。',font=small,fill='#cbb298')
preview=HERE/'seal-v36-native-flame-colour-final.jpg';canvas.save(preview,quality=96,subsampling=0)
new_lup=np.asarray(Image.fromarray(light_bytes,'RGBA').resize((1024,1024),Image.Resampling.BILINEAR),float)/255
new_energy=main[...,:3]*main[...,3,None]+new_lup[...,:3]
assert np.array_equal(new_energy[...,0],old_energy[...,0])
report=[]
for label,lo,hi in [('low',.12,.42),('mid',.45,.76),('hot',.82,1.08)]:
    m=(sv>=lo)&(sv<=hi)
    report.append({'label':label,'oldEmittedRGBNormalisedMedian':np.median(sc[m],axis=0).tolist(),'newEmittedRGBNormalisedMedian':np.median(new_energy[m]/np.maximum(new_energy[m,0,None],.001),axis=0).tolist()})
record={'revision':'v36-native-flame-colour-only','generation':'None this round. Deterministic RGB grade of v35r2; original cloud generation/prompt retained unchanged.',
 'sources':{str(p.relative_to(ROOT)):sha(p) for p in [BASE/'fire-meteor-seal-colour-v35r2.png',BASE/'fire-meteor-seal-light-v35r2.png',PURE,BACKGROUND,CURRENT,ATLAS]},
 'nativeSample':{'phaseSeconds':.65,'pureFireNoSeal':str(PURE.relative_to(ROOT)),'backgroundPhaseSeconds':4.6,'roi':[55,390,1135,1065],'excludedCharacterRectangle':[1060,390,1135,760],'coverageEstimate':'a=clamp((native.R-background.R)/(1.10-background.R),0,1); E=native-background*(1-a). Known burst shader R gain1.10; source red near1. This is engineering foreground estimation, not true renderer alpha readback.','groups':native_stats},
 'atlasCheck':{'phase':'4x4 frame2/3, blend.4, premultiply then shaderRGB1.10','groups':atlas_stats},
 'grade':{'method':'Brightness-conditioned temperature-rank quantile lookup learned only from pure native flame foreground. Along-line temperature ordering/bright-core variation retained; light-only halos receive same mapping. Main/light R and A bytes preserved exactly; G/B only.','intensityMetric':'max/red emitted energy remains byte-identical at every pixel; perceived luminance changes only as required by hue correction, no intensity/timing gain.','lookups':lookups,'sourceToNew':report},
 'projection':{'nativeGroundEllipseCentre':[float(cx),float(cy)],'radii':[float(rx),float(ry)],'factor':float(ry/rx),'sealOpacity':.9,'sourceTextureCentre':[511.5,511.5],'sourceTextureRadius':460.,'composite':'I_flame+(sealPremul-background*sealAlpha)*(1-estimatedFlameAlpha); same actual pure-flame frame in both panels. Not new native screenshot.'},
 'resources':[{'name':main_path.name,'size':[1024,1024],'role':'Same v35r2 main geometry/alpha/red intensity, native-fire-matched G/B','sha256':sha(main_path),'gpuBytes':4194304},{'name':light_path.name,'size':[512,512],'role':'Same v35r2 light geometry/alpha/red energy, native-fire-matched G/B','sha256':sha(light_path),'gpuBytes':1048576}],
 'effect':{'reuse':'fire-seal-v35r2.effect','sha256':sha(ROOT/'src/cocos/assets/resources/vfx/production/fire-seal-v35r2.effect'),'changed':False},
 'totalGpuBytes':5242880,'preview':preview.name,'review':{'local':'Pending inspection of this one actual-fire same-frame computation.','production':'Not published.','native':'Pending root build and same-phase actual capture; user acceptance not claimed.'}}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'preview':str(preview),'native':native_stats,'colourComparison':report,'resources':record['resources']},ensure_ascii=False))
