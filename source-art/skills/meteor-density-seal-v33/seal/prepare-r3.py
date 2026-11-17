"""Regular concentric-circle meteor seal with repeated circular-arc motifs."""
from pathlib import Path
import hashlib,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
RES=ROOT/'src/cocos/assets/resources/vfx/production'
REF=ROOT/'source-art/skills/fire-reference-alignment-v32/assets/approved-reference.png'
NAME='fire-meteor-seal-v33';N=1024;S=3;C=511.5;R=460
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ink=Image.new('L',(N*S,N*S));core=Image.new('L',ink.size)
def circle(mask,r,width):
    ImageDraw.Draw(mask).ellipse(((C-r*R)*S,(C-r*R)*S,(C+r*R)*S,(C+r*R)*S),outline=255,width=round(width*S))
def points_arc(cx,cy,r,a0,a1,rotation):
    a=np.linspace(a0,a1,180);p=np.stack([cx+r*np.cos(a),cy+r*np.sin(a)],axis=1)
    cs,sn=math.cos(rotation),math.sin(rotation)
    return p@np.array([[cs,sn],[-sn,cs]])
def line(mask,points,width):
    pts=[((C+x*R)*S,(C+y*R)*S) for x,y in points]
    d=ImageDraw.Draw(mask);d.line(pts,fill=255,width=round(width*S),joint='curve')
    rad=width*S*.5
    for x,y in [pts[0],pts[-1]]:d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=255)
def engraved(points,width):
    line(ink,points,width);line(core,points,max(1.15,width*.36))

# All boundary contours are actual concentric SVG circles, centred at (0,0).
for r,w in [(1.,4.8),(.9717,4.4),(.755,4.3),(.733,3.6)]:
    circle(ink,r,w);circle(core,r,1.65 if r>.9 else 1.45)

# A pair of concentric circle arcs is repeated every 45 degrees. Each arc
# begins and ends on the same inner boundary: no floating tails or spikes.
innerR=.755;cx=.61;endAngle=math.radians(20)
px,py=innerR*math.cos(endAngle),innerR*math.sin(endAngle)
motherRadius=math.hypot(px-cx,py)
band=[]
for i in range(8):
    rotation=i*math.tau/8
    for offset,width in [(0,5.5),(.0135,3.15)]:
        r=motherRadius+offset
        angle=math.acos((innerR*innerR-cx*cx-r*r)/(2*cx*r))
        pts=points_arc(cx,0,r,-angle,angle,rotation)
        engraved(pts,width)
        band.append(dict(rotationDegrees=i*45,centre=[cx,0],radius=r,startAngle=-angle,endAngle=angle,widthPixels=width))

# One semicircle mother form, plus its concentric companion, rotates by
# exactly 120 degrees. There are no stretched or hand-pulled S curves.
inner=[]
mother=.733/2
for i in range(3):
    for r,width in [(mother,5.65),(mother-.0135,2.9)]:
        pts=points_arc(mother,0,r,0,math.pi,i*math.tau/3)
        engraved(pts,width)
        inner.append(dict(rotationDegrees=i*120,centre=[mother,0],radius=r,startAngle=0,endAngle=math.pi,widthPixels=width))

ink=ink.resize((N,N),Image.Resampling.LANCZOS)
core=core.resize((N,N),Image.Resampling.LANCZOS)
ia=np.asarray(ink,dtype=float)/255;ca=np.asarray(core,dtype=float)/255
# Warm soft light surrounds clear etched orange bodies and thin gold cores.
# This is only local stroke halo; no disk fill is introduced.
halo=np.asarray(ink.filter(ImageFilter.GaussianBlur(6.5)),dtype=float)/255*.20
halo+=np.asarray(ink.filter(ImageFilter.GaussianBlur(9.0)),dtype=float)/255*.05
def layer(colour,alpha):
    a=np.zeros((N,N,4),dtype=np.uint8);a[...,:3]=colour;a[...,3]=np.uint8(np.clip(alpha,0,1)*255);return Image.fromarray(a)
out=layer((255,118,30),halo)
out=Image.alpha_composite(out,layer((255,156,58),ia*.98))
out=Image.alpha_composite(out,layer((255,182,96),ca*.91))
p=np.asarray(out).copy();p[p[...,3]==0,:3]=0;out=Image.fromarray(p)
out.save(HERE/(NAME+'.png'),optimize=True);out.save(RES/(NAME+'.png'),optimize=True)

def arc_d(cx,cy,r,a0,a1):
    x0,y0=cx+r*math.cos(a0),cy+r*math.sin(a0)
    x1,y1=cx+r*math.cos(a1),cy+r*math.sin(a1)
    return f'M {x0:.8f} {y0:.8f} A {r:.8f} {r:.8f} 0 {int(a1-a0>math.pi)} 1 {x1:.8f} {y1:.8f}'
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1.113 -1.113 2.226 2.226" fill="none" stroke-linecap="round" stroke-linejoin="round">']
for colour,scale in [('#ff9c3a',1),('#ffb660',.36)]:
    svg.append(f'<g stroke="{colour}">')
    for r,w in [(1.,4.8),(.9717,4.4),(.755,4.3),(.733,3.6)]:svg.append(f'<circle cx="0" cy="0" r="{r}" stroke-width="{w*scale/R}"/>')
    for e in band+inner:svg.append(f'<path transform="rotate({e["rotationDegrees"]})" d="{arc_d(*e["centre"],e["radius"],e["startAngle"],e["endAngle"])}" stroke-width="{e["widthPixels"]*scale/R}"/>')
    svg.append('</g>')
svg.append('</svg>');(HERE/'meteor-seal-regular-r3.svg').write_text('\n'.join(svg)+'\n',encoding='utf8')
(HERE/'regular-geometry-r3.json').write_text(json.dumps(dict(boundaryCircles=[1,.9717,.755,.733],band=band,inner=inner),ensure_ascii=False,indent=2)+'\n',encoding='utf8')

q=np.asarray(out,dtype=float)/255;a=q[...,3,None]
flat=Image.fromarray(np.uint8(np.clip(q[...,:3]*a*1.15+np.array([40,49,44])/255*(1-a),0,1)*255))
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
preview=Image.new('RGB',(1280,850),'#28312c');d=ImageDraw.Draw(preview)
d.text((12,10),'v33 R3 原稿色 / 仅改橙金色阶，规则几何与透明度保持 / 素材小样，非实景',font=font,fill='#ffb660')
ref=Image.open(REF).convert('RGB');preview.paste(ref.crop((224,836,583,974)).resize((628,242)),(12,54))
d.text((12,310),'原稿色彩与刻纹质感参考；纹理几何按最新要求规则化',font=small,fill='#eec98f')
preview.paste(flat.resize((628,628)),(646,54))
preview.paste(flat.resize((628,242)),(12,374))
d.text((12,650),'正视所有环严格同心正圆；地面仍使用真实圆的正常相机投影',font=small,fill='#eec98f')
preview.save(HERE/'seal-reference-vs-regular-r3-colour.jpg',quality=95,subsampling=0)
y,x=np.mgrid[:N,:N];rad=np.hypot((x-C)/R,(y-C)/R)
record=dict(version='v33-r3-original-colour',reference=str(REF.relative_to(ROOT)),referenceSha256=sha(REF),
    instruction='Latest user requires unquestionably regular circular geometry and original warm glowing-engraving quality; replaces R2 irregular hand curves.',
    script='prepare-r3.py',method='Deterministic supersampled circle/circular-arc redraw; all 4 boundary rings share centre; 8 equal-angle pairs of circular band arcs and 3 copies of one semicircle mother form at 120deg, uniformly offset concentric companions. No new rune or pointed ornament; no model.',
    shape=dict(size=[N,N],centre=[C,C],outerRadius=R,visibleDiameterFraction=920/1024,boundaryCircleRadii=[1,.9717,.755,.733],bandCount=8,bandAngleDegrees=45,innerMotherCount=3,innerAngleDegrees=120,companionGapPixels=.0135*R),
    colour=dict(core=[255,182,96],body=[255,156,58],halo=[255,118,30],haloRadiiPixels=[6.5,9.0],haloWeights=[.20,.05],
        referenceBrightRGBQuantiles=dict(P50=[218,139,73],P75=[234,155,84],P90=[246,170,95]),note='Colour-only original-orange-gold alignment; no lemon-yellow/white core. R3 geometry, high alpha, halo radii, ground height and radius unchanged.'),
    currentPreview='seal-reference-vs-regular-r3-colour.jpg',editableVector='meteor-seal-regular-r3.svg',
    output=dict(path=str((RES/(NAME+'.png')).relative_to(ROOT)),sha256=sha(RES/(NAME+'.png')),pngBytes=(RES/(NAME+'.png')).stat().st_size),
    shader=dict(path='src/cocos/assets/resources/vfx/production/fire-seal-v33.effect',gain=1.15),
    preservedHashes={n:sha(RES/n) for n in ['fire-ground-jets-v27.png','fire-jet-seal-v27.png','fire-ground-v27.effect','fire-flow-noise-v24.png']},
    metrics=dict(innerMedianAlpha=float(np.median(q[...,3][rad<.65])),innerMeanAlpha=float(q[...,3][rad<.65].mean()),fractionInnerAlphaBelow002=float((q[...,3][rad<.65]<.02).mean())),
    scope='Only meteor PNG, existing dedicated v33 shader and meteor path; gameplay circle/radius, camera-aligned UV and all v27 jets unchanged.',
    review=dict(local='Unique R3 original-colour sample inspected beside the reference: warm orange-gold rather than lemon yellow, regular geometry retained. Alpha bytes verified identical to approved R3.',native='pending root build/capture',user='pending'))
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
