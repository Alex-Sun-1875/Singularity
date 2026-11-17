"""Pending warm disk underlay only; never writes a production input."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SOURCE=ROOT/'src/cocos/assets/resources/vfx/production/fire-meteor-seal-v33.png'
REF=ROOT/'source-art/skills/fire-reference-alignment-v32/assets/approved-reference.png'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source_hash=sha(SOURCE)
ink=Image.open(SOURCE).convert('RGBA')
N=1024;C=511.5;R=460
y,x=np.mgrid[:N,:N];r=np.hypot((x-C)/R,(y-C)/R)
def smooth(a):
    a=np.clip(a,0,1);return a*a*(3-2*a)
centre=np.exp(-(r/.50)**2)
band=np.exp(-((r-.84)/.14)**2)
edge=1-smooth((r-.94)/.06)
alpha=(.123+.022*centre+.034*band)*edge
rgb=np.stack([np.ones_like(r),(.47+.055*centre+.020*band),(.108+.040*centre+.018*band)],axis=2)
rgba=np.concatenate([rgb,alpha[...,None]],axis=2)
fill=Image.fromarray(np.uint8(np.clip(rgba,0,1)*255))
filled=Image.alpha_composite(fill,ink)
name='fire-meteor-seal-v33-background-pending-r1.png'
target=HERE/name
filled.save(target,optimize=True)
fill.save(HERE/'seal-underlay-only-pending-r1.png',optimize=True)

q=np.asarray(filled,dtype=float)/255;a=q[...,3,None]
# Grid is a local readability diagnostic only, never part of the PNG.
bg=Image.new('RGB',(N,N),'#28312c');bd=ImageDraw.Draw(bg)
for v in range(-N,N*2,96):
    bd.line((0,v,N,v+N*.58),fill='#84908a',width=2)
    bd.line((0,v,N,v-N*.58),fill='#84908a',width=2)
back=np.asarray(bg,dtype=float)/255
display=q[...,:3]*a*1.15+back*(1-a)
composite=Image.fromarray(np.uint8(np.clip(display,0,1)*255))
preview=Image.new('RGB',(1280,900),'#28312c');d=ImageDraw.Draw(preview)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
d.text((12,10),'v33 暖琥珀底光待用版 / 规则刻纹不改 · 全盘半透明 · 地面可见 / 素材样张，非实景',font=font,fill='#ffb660')
reference=Image.open(REF).convert('RGB');preview.paste(reference.crop((224,836,583,974)).resize((628,242)),(12,54))
d.text((12,310),'原稿圈内暖橙褐反光；本版仅新增光学底色，不烘焙地面纹理',font=small,fill='#eec98f')
preview.paste(composite.resize((628,628)),(646,54))
preview.paste(composite.resize((628,402)),(12,375))
d.text((12,810),'纹理正视仍为严格正圆；下左仅示正常相机投影，网格不进生产素材',font=small,fill='#eec98f')
preview.save(HERE/'seal-background-proposal-r1.jpg',quality=95,subsampling=0)
old=np.asarray(ink,dtype=np.int16);new=np.asarray(filled,dtype=np.int16);core=old[...,3]>.95*255
max_core_rgb_delta=int(np.abs(new[...,:3][core]-old[...,:3][core]).max())
record=dict(status='pending root confirmation after active build finishes; production untouched',
    source=dict(path=str(SOURCE.relative_to(ROOT)),sha256=source_hash,geometryAndLineColours='Approved R3 original-orange-gold line PNG retained as the unchanged top overlay; no geometry/path/palette edits.'),
    output=dict(pendingFile=name,sha256=sha(target),size=[N,N],pngBytes=target.stat().st_size),
    underlay=dict(colourRGBRange=dict(centre=[255,134,38],band=[255,125,32],outer=[255,120,28]),alpha=dict(centre=float(alpha[N//2,N//2]),band=float(alpha[int(C+.84*R),int(C)]),rangeBeforeOuterFade=[.123,.160]),radius=R,centre=[C,C],formula='Full radial disk: .123 + .022*exp(-(r/.50)^2) + .034*exp(-((r-.84)/.14)^2), with smooth edge fade .94..1.0. Same front/back coverage, no hole.'),
    compositing='Warm optical underlay beneath unchanged engraved line image; no baked grey ground, no opaque board, no new shader. The displayed test grid is only in the sample image.',
    sourceProductionHashStillUnchanged=sha(SOURCE)==source_hash,opaqueCoreMaximumRGBChangeFromUnderCompositing=max_core_rgb_delta,
    preview='seal-background-proposal-r1.jpg',review=dict(local='Unique sample inspected: complete warm amber optical disk, readable grid through front/back, no baked floor and no opaque board; approved regular line top layer retained.',native='pending after approved apply/build',user='pending'))
(HERE/'background-pending-provenance-r1.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
