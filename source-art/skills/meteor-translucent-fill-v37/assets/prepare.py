"""One narrow v37 change: 0.80 transparency and continuous faint orange fill.

No generation, palette research, geometry/lifecycle edits or production writes.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent;ROOT=next(p for p in HERE.parents if (p/'src/cocos').is_dir())
BASE=ROOT/'source-art/skills/meteor-flame-colour-v36/assets'
record0=json.loads((BASE/'provenance.json').read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:np.asarray(Image.open(p).convert('RGBA'),dtype=float)/255
main0=read(BASE/'fire-meteor-seal-colour-v36.png');light0=read(BASE/'fire-meteor-seal-light-v36.png')
main=main0.copy();light=light0.copy();TRANSPARENCY=.80
main[...,3]*=TRANSPARENCY;light[...,:3]*=TRANSPARENCY;light[...,3]*=TRANSPARENCY
atlas_path=ROOT/'src/cocos/assets/resources/vfx/production/fire-meteor-burst-v32.png'
atlas=read(atlas_path);h,w=atlas.shape[:2];cell=atlas[:h//4,2*(w//4):3*(w//4)]
energy=cell[...,:3]*cell[...,3,None]
signal=energy@np.array([.2126,.7152,.0722])
# Heavy low pass retains only natural broad intensity differences, never the
# original fire tongues, new scrolls or individual flame piles.
field_image=Image.fromarray(np.uint8(np.clip(signal,0,1)*255+.5),'L').resize((512,512),Image.Resampling.BILINEAR)
field=np.asarray(field_image.filter(ImageFilter.GaussianBlur(38)),dtype=float)/255
p10,p90=np.quantile(field,[.10,.90]);field=np.clip((field-p10)/max(.001,p90-p10),0,1)
field=.78+.40*field
y,x=np.mgrid[:512,:512];radius=np.hypot((x-255.5)*2,(y-255.5)*2)
INNER_RADIUS=332.5334167175263
def smooth(a):a=np.clip(a,0,1);return a*a*(3-2*a)
mask=1-smooth((radius-(INNER_RADIUS-22))/22)
main_support=np.asarray(Image.fromarray(np.uint8(main[...,3]*255+.5),'L').resize((512,512),Image.Resampling.BILINEAR),float)/255
# The fill is continuous in the whole inner disc, with a nonzero floor.
# Existing hot line cores receive less extra light so their colour/clarity
# remains visible instead of clipping under an added bright plate.
fill_strength=.18*field*mask*(1-.65*main_support)
native_groups=record0['nativeSample']['groups']
colour=(np.array(native_groups[0]['emittedNormalisedRGBMedian'])+np.array(native_groups[1]['emittedNormalisedRGBMedian']))*.5
fill=fill_strength[...,None]*colour[None,None,:]
light[...,:3]+=fill
light[...,3]+=mask*.12*(1-light[...,3])
main_bytes=np.uint8(np.clip(main,0,1)*255+.5);light_bytes=np.uint8(np.clip(light,0,1)*255+.5)
assert np.array_equal(main_bytes[...,:3],np.uint8(main0[...,:3]*255+.5))
main_path=HERE/'fire-meteor-seal-colour-v37.png';light_path=HERE/'fire-meteor-seal-light-v37.png'
Image.fromarray(main_bytes,'RGBA').save(main_path,optimize=True);Image.fromarray(light_bytes,'RGBA').save(light_path,optimize=True)
main=main_bytes/255;light=light_bytes/255

PURE=ROOT/record0['nativeSample']['pureFireNoSeal']
BACKGROUND=PURE.with_name('impact-4600ms.jpg')
fire=np.asarray(Image.open(PURE).convert('RGB'),float)/255;bg=np.asarray(Image.open(BACKGROUND).convert('RGB'),float)/255
fire_alpha=np.clip((fire[...,0]-bg[...,0])/np.maximum(1.10-bg[...,0],.2),0,1)
projection=record0['projection'];cx,cy=projection['nativeGroundEllipseCentre'];rx,ry=projection['radii']
crop=(0,385,1220,1225);Y,X=np.mgrid[crop[1]:crop[3],crop[0]:crop[2]]
tx=511.5+(X-cx)/rx*460;ty=511.5+(Y-cy)/ry*460
b=bg[crop[1]:crop[3],crop[0]:crop[2]];f=fire[crop[1]:crop[3],crop[0]:crop[2]];af=fire_alpha[crop[1]:crop[3],crop[0]:crop[2]]
def sample(a,x,y):
    x=np.clip(x,0,a.shape[1]-1.001);y=np.clip(y,0,a.shape[0]-1.001)
    ix=x.astype(int);iy=y.astype(int);u=(x-ix)[...,None];v=(y-iy)[...,None]
    return a[iy,ix]*(1-u)*(1-v)+a[iy,ix+1]*u*(1-v)+a[iy+1,ix]*(1-u)*v+a[iy+1,ix+1]*u*v
def material(m,l):
    a=sample(m,tx,ty);ll=sample(l,tx/2-.25,ty/2-.25)
    coverage=a[...,3]*.9
    alpha=coverage+ll[...,3]*.006*.9*(1-coverage)
    pm=a[...,:3]*coverage[...,None]+ll[...,:3]*.9
    return pm,alpha
pm0,a0=material(main0,light0);pm,a=material(main,light)
before_warning=np.clip(pm0+b*(1-a0[...,None]),0,1)
after_warning=np.clip(pm+b*(1-a[...,None]),0,1)
before_fire=np.clip(f+(pm0-b*a0[...,None])*(1-af[...,None]),0,1)
after_fire=np.clip(f+(pm-b*a[...,None])*(1-af[...,None]),0,1)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
canvas=Image.new('RGB',(1760,1370),'#202420');d=ImageDraw.Draw(canvas)
d.text((18,12),'v37 淡橙内底 + 整体更通透 / 同一原生背景的预警与叠火材质计算',font=font,fill='#e4c192')
d.text((18,43),'唯一候选，非新游戏实录；原橙色纹路与同心圆不变，主纹alpha与既有光能×0.80，中央连续淡橙底光。',font=small,fill='#cdb49b')
for title,data,at in [
 ('当前v36：预警',before_warning,(16,102)),('v37：预警，整片内圆有淡橙底色、地面仍可见',after_warning,(894,102)),
 ('当前v36：同一原生纯火焰 +650ms',before_fire,(16,740)),('v37：同一原生纯火焰 +650ms',after_fire,(894,740))]:
    d.text((at[0],at[1]-26),title,font=small,fill='#e8c099')
    im=Image.fromarray(np.uint8(data*255+.5),'RGB').resize((850,585),Image.Resampling.LANCZOS);canvas.paste(im,at)
preview=HERE/'seal-v37-translucent-fill-final.jpg';canvas.save(preview,quality=96,subsampling=0)
central=radius<INNER_RADIUS-30
record={'revision':'v37-translucent-orange-inner-fill','generation':'None. Deterministic processing only; original cloud source and v36 colour mapping unchanged.',
 'sources':{str(p.relative_to(ROOT)):sha(p) for p in [BASE/'fire-meteor-seal-colour-v36.png',BASE/'fire-meteor-seal-light-v36.png',atlas_path,PURE,BACKGROUND]},
 'transparency':{'mainAlphaScale':TRANSPARENCY,'existingLightRGBScale':TRANSPARENCY,'existingLightAbsorptionSupportScale':TRANSPARENCY,'mainRGB':'Byte-identical to accepted v36; same line colour ratios and geometry.','drawOpacity':'Existing runtime .9 and cue/lifetime unchanged.'},
 'innerFill':{'radius1024':INNER_RADIUS,'edgeFeatherPixels':22,'colourRGBNormalised':colour.tolist(),'reference':'Mean of already-confirmed v36 native pure-fire low/mid emitted chroma, no new palette analysis.',
 'strength':'0.18 * broadField(.78..1.18) * innerMask * (1-.65*scaledMainCoverage). Nonzero continuous whole-disc base, strongest cores protected from clipping.',
 'field':'Existing burst-v32 frame2 luminance, resized512 and Gaussian38px; only broad intensity variation, no new engraving or discrete flames.',
 'lightAbsorption':'Fill adds .12 mask support to light A; old shader multiplies support by only .006. Fill is additive light with very low ground absorption, not an opaque disc.',
 'centralFillRedMinMeanMax':[float(fill_strength[central].min()),float(fill_strength[central].mean()),float(fill_strength[central].max())]},
 'resources':[{'name':main_path.name,'size':[1024,1024],'role':'v36 RGB unchanged, main engraving alpha×.80','sha256':sha(main_path),'gpuBytes':4194304},{'name':light_path.name,'size':[512,512],'role':'v36 light RGB×.80 + continuous faint orange inner fill; low absorption support','sha256':sha(light_path),'gpuBytes':1048576}],
 'effect':{'reuse':'fire-seal-v35r2.effect','sha256':sha(ROOT/'src/cocos/assets/resources/vfx/production/fire-seal-v35r2.effect'),'changed':False},
 'totalGpuBytes':5242880,'preview':preview.name,'projection':projection,
 'previewDeclaration':'Both warning and same-actual-fire-phase panels use the existing camera ellipse and exact two-texture shader formula. Computational candidate only; not new native Cocos evidence.',
 'review':{'local':'Pending view of this one translucent-fill candidate.','production':'Not published.','native':'Pending root standard build and actual same-phase capture; user acceptance not asserted.'}}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'preview':str(preview),'fill':record['innerFill'],'resources':record['resources']},ensure_ascii=False))
