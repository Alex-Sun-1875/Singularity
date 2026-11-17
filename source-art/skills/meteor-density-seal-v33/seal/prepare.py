"""Visible-reference vector tracing of the meteor seal; no generated image."""
from pathlib import Path
import hashlib,json,math,uuid
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont,ImageChops

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
RES=ROOT/'src/cocos/assets/resources/vfx/production'
REF=ROOT/'source-art/skills/fire-reference-alignment-v32/assets/approved-reference.png'
HERE.mkdir(parents=True,exist_ok=True)
NAME='fire-meteor-seal-v33'
N=1024;S=3;C=511.5;R=460
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

# All points are in the deprojected reference's circular coordinate system.
# The near/front motif is at +Y; image row zero remains the far/back edge.
# Only the interrupted backs of the same three flowing curves are continued.
# This is a redraw of the visible path language, not a pixel-extraction claim.
motifs={
 'front-paired-flame':[
  [(-.31,.570),(-.20,.75),(-.06,.57),(.095,.65),(.20,.65),(.09,.70),(.055,.76),(.035,.80),(.09,.81),(.10,.83),(.075,.85),(.025,.865),(.005,.845)],
  [(-.265,.590),(-.16,.79),(-.04,.68),(.04,.76),(.11,.82),(.065,.84),(.015,.85)]],
 'front-left-paired-curls':[
  [(-.63,.49),(-.53,.48),(-.39,.54),(-.43,.65),(-.49,.78),(-.25,.75),(-.23,.68)],
  [(-.66,.48),(-.59,.50),(-.56,.56),(-.56,.63),(-.56,.69),(-.51,.71),(-.48,.68)]],
 'front-right-paired-curls':[
  [(.70,.20),(.65,.14),(.61,.18),(.655,.27),(.72,.40),(.46,.47),(.48,.57),(.51,.67),(.60,.61),(.60,.52)],
  [(.735,.27),(.71,.34),(.65,.34),(.68,.405),(.66,.49),(.58,.47),(.55,.49)]],
 'left-flow-pair':[
  [(-.88,-.09),(-.84,.06),(-.91,.13),(-.81,.23),(-.72,.28),(-.65,.23),(-.66,.335),(-.67,.39),(-.71,.405),(-.65,.455),(-.58,.50),(-.51,.46),(-.54,.43)],
  [(-.81,-.24),(-.76,-.15),(-.70,.03),(-.785,.18),(-.82,.25),(-.79,.30),(-.73,.29)]],
 'left-back-hook-pair':[
  [(-.715,-.24),(-.67,-.37),(-.875,-.30),(-.84,-.405),(-.825,-.46),(-.77,-.45),(-.79,-.37)],
  [(-.75,-.27),(-.71,-.36),(-.85,-.34),(-.83,-.405)]],
 'right-back-hook-pair':[
  [(.835,-.23),(.76,-.25),(.665,-.22),(.70,-.36),(.74,-.50),(.65,-.62),(.57,-.69)],
  [(.80,-.26),(.85,-.20),(.86,-.34),(.78,-.345),(.73,-.36),(.75,-.41),(.71,-.45)]],
 'far-left-stream-pair':[
  [(-.675,-.60),(-.73,-.71),(-.56,-.70),(-.51,-.79),(-.45,-.90),(-.27,-.85),(-.30,-.80),(-.35,-.755),(-.43,-.80),(-.40,-.84)],
  [(-.59,-.66),(-.58,-.79),(-.42,-.75),(-.38,-.73)]],
 'far-right-stream-pair':[
  [(.24,-.88),(.35,-.90),(.40,-.79),(.43,-.75),(.51,-.71),(.59,-.70),(.65,-.62)],
  [(.24,-.82),(.29,-.78),(.45,-.84),(.49,-.76),(.55,-.68),(.58,-.70),(.61,-.67)]]}
inner={
 'central-long-recurve':[(.16,.565),(.18,.32),(-.11,.15),(-.06,-.05),(-.10,-.25),(.11,-.31),(.07,-.48),(.10,-.63),(.02,-.76),(-.07,-.84)],
 'left-long-return':[(-.66,.30),(-.73,.055),(-.60,-.205),(-.345,-.258),(-.13,-.31),(.13,-.22),(.36,-.365),(.50,-.45),(.56,-.59),(.54,-.71)],
 'right-long-return':[(.42,-.735),(.64,-.60),(.65,-.38),(.52,-.16),(.43,.015),(.24,.125),(.045,.10),(-.10,.08),(-.20,.005),(-.19,-.075)]}

# Keep the established motifs, but join nearby loose ends back to the inner
# boundary. Nothing is copied to the opposite side or added as a new symbol.
for paths in motifs.values():
    for points in paths:
        for index in (0,-1):
            px,py=points[index];d=math.hypot(px,py+.115)
            if abs(d-.752)<.105:
                points[index]=(px*.752/d,(py+.115)*.752/d-.115)

def cubic(points):
    assert (len(points)-1)%3==0
    result=[points[0]]
    for i in range(0,len(points)-1,3):
        a,b,c,d=[np.array(p,dtype=float) for p in points[i:i+4]]
        for t in np.linspace(0,1,70)[1:]:result.append(tuple((1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d))
    return result
def stroke(mask,points,width):
    d=ImageDraw.Draw(mask)
    p=[((C+x*R)*S,(C+y*R)*S) for x,y in cubic(points)]
    d.line(p,fill=255,width=round(width*S),joint='curve')
    r=width*S*.5
    for x,y in [p[0],p[-1]]:d.ellipse((x-r,y-r,x+r,y+r),fill=255)
def polyline(mask,points,width):
    p=[((C+x*R)*S,(C+y*R)*S) for x,y in points]
    ImageDraw.Draw(mask).line(p,fill=255,width=round(width*S),joint='curve')
def companion(points):
    p=np.asarray(cubic(points));t=np.gradient(p,axis=0);length=np.maximum(np.linalg.norm(t,axis=1),1e-6)
    normal=np.stack([-t[:,1]/length,t[:,0]/length],axis=1)
    return p+normal*.0135
def circle(mask,cx,cy,r,width):
    d=ImageDraw.Draw(mask)
    d.ellipse(((C+(cx-r)*R)*S,(C+(cy-r)*R)*S,(C+(cx+r)*R)*S,(C+(cy+r)*R)*S),outline=255,width=round(width*S))

ink=Image.new('L',(N*S,N*S));highlight=Image.new('L',(N*S,N*S))
bandInk=Image.new('L',ink.size);bandHigh=Image.new('L',ink.size)
innerInk=Image.new('L',ink.size);innerHigh=Image.new('L',ink.size)
# Two outer rings and the original narrow inner boundary, rather than the
# old eight-point/petal construction. Keep actual gameplay radius unchanged.
for radius,width in [(1.,3.0),(.9717,2.7)]:
    circle(ink,0,0,radius,width*1.6);circle(highlight,0,0,radius,1.25*1.6)
for radius,width in [(.752,2.7),(.732,2.15)]:
    circle(ink,0,-.115,radius,width*1.6);circle(highlight,0,-.115,radius,1.0*1.6)
for paths in motifs.values():
    for i,points in enumerate(paths):
        stroke(bandInk,points,(3.25 if i==0 else 2.4)*1.6)
        stroke(bandHigh,points,(1.20 if i==0 else .90)*1.6)
for points in inner.values():
    stroke(innerInk,points,3.15*1.6);stroke(innerHigh,points,1.15*1.6)
    polyline(innerInk,companion(points),2.20);polyline(innerHigh,companion(points),.95)
bandClip=Image.new('L',ink.size);insideClip=Image.new('L',ink.size)
bd=ImageDraw.Draw(bandClip);idraw=ImageDraw.Draw(insideClip)
def ellipse_box(cx,cy,r):return ((C+(cx-r)*R)*S,(C+(cy-r)*R)*S,(C+(cx+r)*R)*S,(C+(cy+r)*R)*S)
bd.ellipse(ellipse_box(0,0,.968),fill=255)
bd.ellipse(ellipse_box(0,-.115,.750),fill=0)
idraw.ellipse(ellipse_box(0,-.115,.754),fill=255)
ink=ImageChops.lighter(ink,ImageChops.multiply(bandInk,bandClip))
ink=ImageChops.lighter(ink,ImageChops.multiply(innerInk,insideClip))
highlight=ImageChops.lighter(highlight,ImageChops.multiply(bandHigh,bandClip))
highlight=ImageChops.lighter(highlight,ImageChops.multiply(innerHigh,insideClip))
ink=ink.resize((N,N),Image.Resampling.LANCZOS)
highlight=highlight.resize((N,N),Image.Resampling.LANCZOS)
ia=np.asarray(ink,dtype=float)/255;ha=np.asarray(highlight,dtype=float)/255
ga=np.asarray(ink.filter(ImageFilter.GaussianBlur(1.6)),dtype=float)/255*.22
ga+=np.asarray(ink.filter(ImageFilter.GaussianBlur(4.0)),dtype=float)/255*.035
ga=np.clip(ga,0,.24)
def layer(colour,alpha):
    rgb=np.zeros((N,N,4),dtype=np.uint8);rgb[...,:3]=colour;rgb[...,3]=np.uint8(np.clip(alpha,0,1)*255)
    return Image.fromarray(rgb)
out=layer((255,153,38),ga)
out=Image.alpha_composite(out,layer((255,172,52),ia*.98))
out=Image.alpha_composite(out,layer((255,196,96),ha*.88))
pixels=np.asarray(out).copy();pixels[pixels[...,3]==0,:3]=0;out=Image.fromarray(pixels)
out.save(HERE/(NAME+'.png'),optimize=True);out.save(RES/(NAME+'.png'),optimize=True)
meta=RES/(NAME+'.png.meta')
if not meta.exists():
    m=json.loads((RES/'fire-meteor-seal-v32.png.meta').read_text(encoding='utf8'))
    identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/'+NAME+'.png'))
    m['uuid']=identity;t=m['subMetas']['6c48a'];t['uuid']=identity+'@6c48a';t['displayName']=NAME;t['userData']['imageUuidOrDatabaseUri']=identity;m['userData']['redirect']=t['uuid']
    meta.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

# Editable geometry record and SVG are retained so the visible paths can be
# reviewed without repeating a model call or re-extracting blurred lighting.
(HERE/'traced-paths.json').write_text(json.dumps(dict(motifs=motifs,inner=inner),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def svg_path(points):
    text=f'M {points[0][0]} {points[0][1]}'
    for i in range(1,len(points),3):text+=' C '+' '.join(str(n) for point in points[i:i+3] for n in point)
    return text
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1.113 -1.113 2.226 2.226" fill="none" stroke="#ffc060" stroke-width=".0112" stroke-linecap="round" stroke-linejoin="round">',
 '<defs><mask id="band"><rect x="-2" y="-2" width="4" height="4" fill="black"/><circle cx="0" cy="0" r=".968" fill="white"/><circle cx="0" cy="-.115" r=".750" fill="black"/></mask><clipPath id="inner"><circle cx="0" cy="-.115" r=".754"/></clipPath></defs>']
svg += [f'<circle cx="0" cy="0" r="{r}"/>' for r in [1,.9717]]
svg += [f'<circle cx="0" cy="-.115" r="{r}"/>' for r in [.752,.732]]
svg += [f'<path mask="url(#band)" d="{svg_path(p)}"/>' for paths in motifs.values() for p in paths]
svg += [f'<path clip-path="url(#inner)" d="{svg_path(p)}"/>' for p in inner.values()]
svg += [f'<polyline clip-path="url(#inner)" stroke-width=".0048" points="'+ ' '.join(f'{x:.6f},{y:.6f}' for x,y in companion(p))+'"/>' for p in inner.values()]
svg.append('</svg>');(HERE/'meteor-seal-trace.svg').write_text('\n'.join(svg)+'\n',encoding='utf8')

font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
q=np.asarray(out,dtype=float)/255;a=q[...,3,None]
flat=Image.fromarray(np.uint8(np.clip(q[...,:3]*a*1.13+np.array([40,49,44])/255*(1-a),0,1)*255))
preview=Image.new('RGB',(1280,850),'#28312c');d=ImageDraw.Draw(preview)
d.text((12,10),'v33 法阵描摹 / 双外环 · 圈间成对流线卷纹 · 三条大回旋 / 素材小样，非实景',font=font,fill='#eec98f')
ref=Image.open(REF).convert('RGB');preview.paste(ref.crop((224,836,583,974)).resize((628,242)),(12,54))
d.text((12,305),'原稿：后上方部分被陨石遮挡；重绘以可见曲线连续语言补全',font=small,fill='#eec98f')
preview.paste(flat.resize((628,628)),(646,54))
preview.paste(flat.resize((628,242)),(12,374))
d.text((12,650),'保留真实圆形/radius；纹理对比不拉伸实际技能判定',font=small,fill='#eec98f')
preview.save(HERE/'seal-reference-vs-trace-r2.jpg',quality=95,subsampling=0)
y,x=np.mgrid[:N,:N];r=np.hypot((x-C)/R,(y-C)/R)
metric=dict(innerMedianAlpha=float(np.median(q[...,3][r<.65])),innerMeanAlpha=float(q[...,3][r<.65].mean()),fractionInnerAlphaBelow002=float((q[...,3][r<.65]<.02).mean()))
record=dict(reference=str(REF.relative_to(ROOT)),referenceSha256=sha(REF),referenceRegion=[224,836,583,974],
    method='Deterministic cubic-Bezier visible-reference tracing and clean vector redraw, supersampled 3x with Pillow. Complete double outside rims, paired flowing band curls and three long inner recurve paths; source-obscured rear portions are smooth continuations, not pixel-identical claims. No extraction of floor glow, no generation, no old upside-down copied texture.',
    shape=dict(size=[N,N],centre=[C,C],outerRadius=R,visibleDiameterFraction=920/1024,orientation='Image top is reference far/back, front flame motif at image bottom; preserve existing camera-aligned row0->v0 and circle/radius.'),
    colour=dict(broad=[255,172,52],brightCore=[255,196,96],glow=[255,153,38],broadOpacity=.98,coreOpacity=.88),
    refinement='Core strokes 1.6x thicker; each original long inner recurve receives one close thin companion. Band motifs are clipped between the same outer and inner boundary, near loose ends join the inner ring, front pointed tail shortened into its existing curl. No new motifs.',
    currentPreview='seal-reference-vs-trace-r2.jpg',
    output=dict(path=str((RES/(NAME+'.png')).relative_to(ROOT)),sha256=sha(RES/(NAME+'.png')),pngBytes=(RES/(NAME+'.png')).stat().st_size),
    shader=dict(path='src/cocos/assets/resources/vfx/production/fire-seal-v33.effect',colourGain=1.15,compositing='Raw artist display-colour premultiplied source-over; line-only emission, transparent inner ground.'),
    preservedHashes={n:sha(RES/n) for n in ['fire-ground-jets-v27.png','fire-jet-seal-v27.png','fire-ground-v27.effect','fire-flow-noise-v24.png']},
    metrics=metric,review=dict(local='R2 source comparison inspected at unique preview path: 1.6x fuller bright engraved strokes, three close companion curves, band confined between the boundary rings with shortened front curl. No diffuse inner-disk fill.',native='pending root build/capture',user='pending'),
    scope='Only meteor seal texture and dedicated shader/resource branch; approved v27 small jet seal/flame and unified shield are outside this change.')
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
