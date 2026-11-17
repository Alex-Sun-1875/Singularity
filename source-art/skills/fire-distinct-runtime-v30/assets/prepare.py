"""Extract approved v29 lance and connected fire flow, no model inference."""
from pathlib import Path
import hashlib, json, uuid, sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RES = ROOT/'src/cocos/assets/resources/vfx/production'
REF = ROOT/'source-art/skills/fire-distinct-shapes-design-v29/fire-distinct-shapes-v29.png'
PREVIEW = '--preview-only' in sys.argv
HERE.mkdir(parents=True, exist_ok=True)
source = Image.open(REF).convert('RGB')
boxes = {'lance':(334,174,571,244),'field':(1090,488,1338,651)}

def smooth(x):
    x = np.clip(x,0,1)
    return x*x*(3-2*x)

def blur(a, radius):
    return np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).filter(ImageFilter.GaussianBlur(radius)), dtype=float)/255

def matte(im):
    p = np.asarray(im,dtype=float)/255
    warm = p[...,0]-p[...,2]
    known = 1-smooth((warm-.055)/.070)
    denom = blur(known,14)
    average = np.median(p[known>.5],axis=0)
    background = np.stack([blur(p[...,c]*known,14)/np.maximum(denom,.015) for c in range(3)],axis=2)
    background = np.where((denom<.015)[...,None],average,background)
    # The stone joints must not survive as dark lines in an emissive texture.
    # Fit their neutral channel correlation from unlit pixels, then solve the
    # red/blue difference. This cancels the actual high-frequency floor grain,
    # unlike subtracting only a blurred ground estimate.
    clean=known>.65
    rfit=np.polyfit(p[...,2][clean],p[...,0][clean],1)
    gfit=np.polyfit(p[...,2][clean],p[...,1][clean],1)
    rfit[0]=np.clip(rfit[0],.65,1.5)
    gfit[0]=np.clip(gfit[0],.65,1.4)
    contrast=p[...,0]-rfit[0]*p[...,2]-rfit[1]
    blue=np.full_like(contrast,.18)
    for unused in range(3):
        alpha=np.clip(contrast/np.maximum(1-rfit[0]*blue-rfit[1],.2),0,.96)
        green=(p[...,1]-gfit[0]*p[...,2]-gfit[1])/np.maximum(alpha,1e-6)+gfit[0]*blue+gfit[1]
        blue=np.clip(.045+.59*(green-.37),.035,.38)
    alpha *= smooth((contrast-.006)/.085)
    # A minimum-light matte rejects the residual stone-grid grain; the broad
    # bright ribbons and their soft .1+ haze remain continuous.
    alpha *= smooth((alpha-.018)/.13)
    foreground=np.stack([np.ones_like(green),green,blue],axis=2)
    foreground=np.clip(foreground,0,1)
    # Keep the accepted luminous gold/orange, suppress cold ground samples.
    foreground[...,0] = np.maximum(foreground[...,0],foreground[...,1])
    foreground[...,1] = np.minimum(foreground[...,1],foreground[...,0]*.86)
    foreground[...,2] = np.minimum(foreground[...,2],foreground[...,0]*.42)
    premul = foreground*alpha[...,None]
    pma = np.concatenate([premul,alpha[...,None]],axis=2)
    return pma, background

def rgba(a):
    rgb = a[...,:3]/np.maximum(a[...,3,None],1e-6)
    return Image.fromarray(np.uint8(np.clip(np.concatenate([rgb,a[...,3,None]],axis=2),0,1)*255))

def from_image(im):
    a=np.asarray(im,dtype=float)/255
    a[...,:3]*=a[...,3,None]
    return a

def sample(a,x,y,wrap=False):
    if wrap:
        x=x%a.shape[1]
        valid=(y>=0)&(y<=a.shape[0]-1)
    else:
        valid=(x>=0)&(x<=a.shape[1]-1)&(y>=0)&(y<=a.shape[0]-1)
        x=np.clip(x,0,a.shape[1]-1.001)
    y=np.clip(y,0,a.shape[0]-1.001)
    ix=x.astype(int);iy=y.astype(int);tx=(x-ix)[...,None];ty=(y-iy)[...,None]
    nx=(ix+1)%a.shape[1] if wrap else ix+1
    q=a[iy,ix]*(1-tx)*(1-ty)+a[iy,nx]*tx*(1-ty)+a[iy+1,ix]*(1-tx)*ty+a[iy+1,nx]*tx*ty
    return q*valid[...,None]

records={}
for kind,box in boxes.items():
    crop=source.crop(box)
    crop.save(HERE/(kind+'-source.png'))
    pma,bg=matte(crop)
    rgba(pma).save(HERE/(kind+'-extracted.png'))
    np.savez_compressed(HERE/(kind+'-matte.npz'),premul=pma,background=bg,box=box)
    records[kind]=pma

# The fixed lance silhouette points +X. Its tip never moves; fine inner
# filaments feed toward the tip while complementary windows hide resets.
original=records['lance'][:,::-1].copy()
canvas=Image.new('RGBA',(256,96))
inner=rgba(original).resize((240,71),Image.Resampling.LANCZOS)
canvas.paste(inner,(8,12))
lance=from_image(canvas)
ly,lx=np.mgrid[:96,:256]
tip_region=(lx>235)&(lance[...,3]>.10)
ty,tx=np.where(tip_region)
tipx=float(tx.max())
near=tip_region&(lx>tipx-4)
tipy=float((ly[near]*lance[...,3][near]).sum()/lance[...,3][near].sum())
# Soft source edges stay source edges; a small dilation gives flowing detail
# room without inventing extra long wisps or changing the approved outline.
envelope=np.asarray(canvas.getchannel('A').filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(.7)),dtype=float)/255
pin=smooth((lx-205)/31)
lance_frames=[]
for i in range(16):
    p=i/16;q=(p+.43)%1
    w0=np.sin(np.pi*p)**2;w1=np.sin(np.pi*q)**2
    a=sample(lance,lx-p*18,ly)
    b=sample(lance,lx-q*27,ly)
    moving=(a*w0+b*w1)/max(w0+w1,.001)
    moving*=np.minimum(1,envelope/np.maximum(moving[...,3],1e-6))[...,None]
    out=lance*(.35+.65*pin[...,None])+moving*(.65*(1-pin))[...,None]
    lance_frames.append(rgba(out))

# A low, interconnected fire surface, not upright flames. Periodic stitching
# blends a 48px horizontal overlap from the same approved patch. Both moving
# samples always advance +U; no reverse lifecycle or ping-pong playback.
field=from_image(rgba(records['field']).resize((304,128),Image.Resampling.LANCZOS))
tile=field[:,:256].copy()
mix=smooth(np.arange(48)/47)[None,:,None]
tile[:,:48]=field[:,256:304]*(1-mix)+field[:,:48]*mix
fy,fx=np.mgrid[:128,:256]
tile*=smooth(np.minimum(fy,127-fy)/5)[...,None]
field_frames=[]
for i in range(16):
    p=i/16;q=(p+.43)%1
    w0=np.sin(np.pi*p)**2;w1=np.sin(np.pi*q)**2
    a=sample(tile,fx-p*19,fy,True)
    b=sample(tile,fx-q*29,fy,True)
    moving=(a*w0+b*w1)/max(w0+w1,.001)
    out=tile*.23+moving*.77
    # Native repeat samples inside each atlas cell, never across neighbours.
    edge=(out[:,0]+out[:,-1])*.5
    out[:,0]=edge;out[:,-1]=edge
    field_frames.append(rgba(out))

specs=[('fire-lance-v30',lance_frames,(256,96),'head +X',[(tipx+.5)/256,(tipy+.5)/96]),
       ('fire-field-flow-v30',field_frames,(256,128),'surface / periodic U',[.5,.5])]
output=[]
for name,seq,cell,mode,anchor in specs:
    atlas=Image.new('RGBA',(cell[0]*4,cell[1]*4))
    for i,frame in enumerate(seq):atlas.paste(frame,(i%4*cell[0],i//4*cell[1]))
    atlas.save(HERE/(name+'.png'),optimize=True)
    if not PREVIEW:
        atlas.save(RES/(name+'.png'),optimize=True)
        meta=RES/(name+'.png.meta')
        if not meta.exists():
            oldtext=(RES/'fire-pyro-v7.png.meta').read_text(encoding='utf8')
            old=json.loads(oldtext)['uuid']
            meta.write_text(oldtext.replace(old,str(uuid.uuid4())).replace('fire-pyro-v7',name),encoding='utf8')
    a=np.asarray(atlas,dtype=float)/255
    mask=a[...,3]>.01
    output.append(dict(name=name,cell=cell,grid=[4,4],frameCount=16,mode=mode,anchorUV=anchor,
        straightAlpha=True,pngBytes=(HERE/(name+'.png')).stat().st_size,rgbaMemoryBytes=atlas.width*atlas.height*4,
        meanOccupiedAlpha=float(a[...,3][mask].mean()),sha256=hashlib.sha256((HERE/(name+'.png')).read_bytes()).hexdigest()))

font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
preview=Image.new('RGB',(1024,660),'#28312c');d=ImageDraw.Draw(preview)
d.text((12,10),'v29 已批造型提取 / 细长火矛 + 互连低平火面 / 素材小样，非实景',font=font,fill='#eac187')
def composite(frame):
    a=np.asarray(frame,dtype=float)/255;alpha=a[...,3,None]
    return Image.fromarray(np.uint8(np.clip(a[...,:3]*alpha*1.10+np.array([40,49,44])/255*(1-alpha*.90),0,1)*255))
for j,i in enumerate([0,4,8,12]):
    preview.paste(composite(lance_frames[i]),(j*256,72))
    d.text((j*256+10,47),f'火矛 {i:02} / +X尖端固定',font=small,fill='#eac187')
for row,i in enumerate([0,5,10]):
    for repeat in range(4):preview.paste(composite(field_frames[i]),(repeat*256,235+row*140))
    d.text((12,212+row*140),f'整片连续火流 {i:02} / 横向重复检视',font=small,fill='#eac187')
preview.save(HERE/'material-preview.jpg',quality=95,subsampling=0)
movie=[]
for i in range(16):
    canvas=Image.new('RGB',(768,300),'#28312c');d=ImageDraw.Draw(canvas)
    d.text((12,8),'v29 原稿形状 / 仅素材循环，非实景',font=font,fill='#eac187')
    canvas.paste(composite(lance_frames[i]).resize((512,192)),(128,25))
    for r in range(3):canvas.paste(composite(field_frames[i]),(r*256,169))
    movie.append(canvas)
movie[0].save(HERE/'material-loop.webp',save_all=True,append_images=movie[1:],duration=83,loop=0,quality=92)

record=dict(method='Deterministic approved-design light matte extraction and forward texture transport. No new generation, no local inference.',
    reference=str(REF.relative_to(ROOT)),referenceSha256=hashlib.sha256(REF.read_bytes()).hexdigest(),
    sourceRegions=boxes,subjectProtection='Both crops inspected: no soldiers/player body inside selected region; lance cropped before fingertips, field is the unobstructed right area.',
    sourceBackground='Neutral-channel regression from unlit floor cancels stone joints and floor grain before optical-alpha solving; retain source filament green/red relation and correlated warm blue, with G<=.86R and B<=.42R. Gaussian estimate is archived only as a background diagnostic.',
    animation='16 phases. Inner detail moves toward lance head or +U field flow. Two forward samples with zero-weight resets, unequal .43 phase offset. Lance silhouette/head pinned; field U periodic.',
    outputs=output,productionUpdated=not PREVIEW,
    nativeAcceptance='pending native Cocos capture and user review',taptapDevice='pending',
    artStatus='Local source crops and three representative phase swatches visually reviewed: distinct narrow lance and connected low surface, no characters/floor-grid seams. Native motion and user acceptance remain pending.')
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
