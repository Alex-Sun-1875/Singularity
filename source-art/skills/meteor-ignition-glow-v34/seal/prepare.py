"""Pack unchanged R4 engraving geometry; separate light from ground opacity.

This stage writes source-art only. apply-production.py publishes the inspected
single mask/effect during an explicitly acquired common build-lock window.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
HERE.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'source-art/skills/meteor-density-seal-v33/seal/prepare-colour-r4-pending.py'
REF=ROOT/'source-art/skills/fire-reference-alignment-v32/assets/approved-reference.png'
RES=ROOT/'src/cocos/assets/resources/vfx/production'
NAME='fire-meteor-seal-v34'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Reuse the complete exact R4 mask construction, stopping BEFORE any resize,
# material compositing, preview or file write from that historical script.
# The resulting curves/ring pixels therefore cannot drift into a new design.
text=SOURCE.read_text(encoding='utf8');prefix=text.split('ink=ink.resize',1)[0]
assert 'ink=ink.resize' in text and '.save(' not in prefix and '.write_text(' not in prefix
ns={'__file__':str(SOURCE),'__name__':'r4_geometry_readonly'}
exec(compile(prefix,str(SOURCE), 'exec'),ns)
N=1024;C=511.5;R=460
ink=ns['ink'].resize((N,N),Image.Resampling.LANCZOS)
core=ns['core'].resize((N,N),Image.Resampling.LANCZOS)
ia=np.asarray(ink,dtype=float)/255;ca=np.asarray(core,dtype=float)/255
def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)
def blurred(radius):return np.asarray(ink.filter(ImageFilter.GaussianBlur(radius)),dtype=float)/255
y,x=np.mgrid[:N,:N];r=np.hypot((x-C)/R,(y-C)/R)
# Visible stroke-local light is energy, not another broad opaque alpha wash.
halo=(blurred(6)*.56+blurred(16)*.82+blurred(34)*.95)
halo=np.minimum(.85,halo)*(1-smooth((r-1.02)/.08))
disc=(.82+.10*np.exp(-(r/.48)**2)+.08*np.exp(-((r-.84)/.13)**2))*(1-smooth((r-.94)/.06))
packed=Image.fromarray(np.uint8(np.clip(np.stack([ia,ca,halo,disc],axis=2),0,1)*255))
packed.save(HERE/(NAME+'.png'),optimize=True)
ink.save(HERE/'engraving-coverage.png')
core.save(HERE/'bright-core-coverage.png')
Image.fromarray(np.uint8(np.clip(halo,0,1)*255)).save(HERE/'halo-energy-weight.png')
Image.fromarray(np.uint8(np.clip(disc,0,1)*255)).save(HERE/'disc-energy-weight.png')

# Exact arithmetic shared with fire-seal-v34.effect. The only absorbing alpha
# is carved-line coverage plus at most 2.5% disk absorption. Halo/disc energy
# is reduced beneath high-coverage ink, retaining warm line colour/headroom.
BODY=np.array([236,148,65])/255;CORE=np.array([249,174,97])/255
DISC=np.array([.38,.18,.040]);HALO=np.array([.56,.27,.060])
def material(bg,fade=.90):
    q=np.asarray(packed,dtype=float)/255
    mix=np.clip(q[...,1]/np.maximum(q[...,0],1e-4),0,1)
    colour=BODY*(1-mix[...,None])+CORE*mix[...,None]
    glyph=np.minimum(.98,q[...,0]*fade*1.06)
    light=(q[...,3,None]*DISC+q[...,2,None]*HALO)*fade*(1-glyph[...,None])
    absorb=q[...,3]*fade*.025
    alpha=glyph+absorb*(1-glyph)
    premul=colour*glyph[...,None]+light
    return np.clip(premul+bg*(1-alpha[...,None]),0,1),premul,alpha

# A deterministic dark test grid illustrates transmitted terrain; it is not
# baked into the mask, a screen capture, or claimed native validation.
bg=Image.new('RGB',(N,N),'#28312c');bd=ImageDraw.Draw(bg)
for v in range(-N,N*2,96):
    bd.line((0,v,N,v+N*.58),fill='#84908a',width=2)
    bd.line((0,v,N,v-N*.58),fill='#84908a',width=2)
background=np.asarray(bg,dtype=float)/255
display,premul,alpha=material(background)
visible=Image.fromarray(np.uint8(display*255))
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
preview=Image.new('RGB',(1280,920),'#28312c');d=ImageDraw.Draw(preview)
d.text((12,10),'v34 / 原稿卷纹不改 · 刻线coverage与底光/辉光能量分离 / 材质计算样张，非实景',font=font,fill='#f9ae61')
reference=Image.open(REF).convert('RGB');preview.paste(reference.crop((224,836,583,974)).resize((628,242)),(12,54))
d.text((12,310),'原稿橙金参考；右/下按新shader、稳定预警fade=.90计算',font=small,fill='#edc38c')
preview.paste(visible.resize((628,628)),(646,54));preview.paste(visible.resize((628,402)),(12,375))
d.text((12,810),'单1024 RGBA是数据mask，不是颜色图：R刻线/G亮芯/B辉光/A整盘底光',font=small,fill='#edc38c')
d.text((12,839),'地面吸收约2%，主要增加暖橙金光能；高coverage线芯处抑光，避免剪红推黄',font=small,fill='#edc38c')
preview.save(HERE/'seal-v34-shader-material-preview.jpg',quality=95,subsampling=0)

flat=np.full((N,N,3),[40,49,44],dtype=float)/255
shown,_,outA=material(flat);quiet=(r<.85)&(ia<.005)
line=ia>.95
record=dict(version='v34-coverage-and-light-separated',reference=str(REF.relative_to(ROOT)),referenceSha256=sha(REF),
    geometry=dict(source=str(SOURCE.relative_to(ROOT)),sourceSha256=sha(SOURCE),prefixSha256=hashlib.sha256(prefix.encode()).hexdigest(),unchanged='Exact R4 construction prefix reused read-only; same concentric rings, band scrolls, inner long recurves, width, centre, 460/512 footprint and UV. No R3 trefoil.'),
    asset=dict(name=NAME,size=[N,N],dataMask=True,channels=dict(R='engraved-line coverage',G='warm bright-core coverage',B='6/16/34px stroke-local halo energy weight',A='complete circular disk light weight; NOT final output opacity'),sha256=sha(HERE/(NAME+'.png')),pngBytes=(HERE/(NAME+'.png')).stat().st_size,rgbaMemoryBytes=N*N*4),
    material=dict(blend='ONE / ONE_MINUS_SRC_ALPHA',body=BODY.tolist(),core=CORE.tolist(),discRadiance=DISC.tolist(),haloRadiance=HALO.tolist(),glyphCoverageBoost=1.06,maxGlyphCoverage=.98,maxDiscAbsorption=.025,
        formula='glyph=min(.98,R*fade*1.06); colour=mix(body,core,clamp(G/max(R,.0001))); light=(discRadiance*A+haloRadiance*B)*fade*(1-glyph); outputRGB=colour*glyph+light; outputAlpha=glyph+A*fade*.025*(1-glyph).',
        meaning='Disc and halo radiance add warm light with very low ground absorption. Their light is suppressed under solid lines. No global colour gain, gamma transform, extra texture, real-time light or extra draw.'),
    simulation=dict(fade=.90,backgroundRGB=[40,49,44],quietDiskRGBMedian255=np.round(np.median(shown[quiet],axis=0)*255,1).tolist(),quietDiskAbsorptionMedian=float(np.median(outA[quiet])),lineRGBP90_255=np.round(np.quantile(shown[line],.9,axis=0)*255,1).tolist(),
        note='CPU reconstruction of the exact shader math on a diagnostic grid, not native Cocos or a pixel-equivalence claim for the CG reference.'),
    preview='seal-v34-shader-material-preview.jpg',productionUpdated=False,review=dict(local='pending material preview inspection',native='pending root build/capture',user='pending'))
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
