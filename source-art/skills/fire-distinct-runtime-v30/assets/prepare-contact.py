"""One approved short contact fan; no broad glow or copied character pixels."""
from pathlib import Path
import hashlib, json, uuid
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
RES=ROOT/'src/cocos/assets/resources/vfx/production'
REF=ROOT/'source-art/skills/fire-distinct-shapes-design-v29/fire-distinct-shapes-v29.png'
BOX=(955,204,1205,305)
source=Image.open(REF).convert('RGB').crop(BOX)
source.save(HERE/'contact-source.png')
p=np.asarray(source,dtype=float)/255
y,x=np.mgrid[:p.shape[0],:p.shape[1]]
def smooth(v):
    v=np.clip(v,0,1)
    return v*v*(3-2*v)

warm=p[...,0]-p[...,2]
signal=Image.fromarray(np.uint8(np.clip(warm,0,1)*255))
opened=np.asarray(signal.filter(ImageFilter.MinFilter(7)).filter(ImageFilter.MaxFilter(7)),dtype=float)/255
ridge=np.maximum(0,warm-opened)
colour=smooth((p[...,0]-.52)/.34)*smooth((warm-.18)/.32)
coreX,coreY=30,36
distance=np.hypot(x-coreX,y-coreY)
# Body lies at left/upper-left; the lower soldier begins around (60,65).
# Retain only the small impact nucleus and its rightwards fan, not armour.
root=smooth((13-distance)/3)
fan=smooth((x-29)/12)*(1-smooth((y-70)/6))
geometry=np.maximum(root,fan)
filaments=smooth((ridge-.025)/.26)*colour*.91
nucleus=np.exp(-((x-coreX)/5.8)**2-((y-coreY)/6.2)**2)*smooth((p[...,0]-.73)/.22)*smooth((p[...,1]-.42)/.32)*.94
alpha=np.maximum(filaments,nucleus)*geometry
edge=smooth(np.minimum.reduce([x,p.shape[1]-1-x,y,p.shape[0]-1-y])/2)
alpha*=edge
green=np.clip((p[...,1]-.12)/np.maximum(p[...,0]-.12,.01),.40,.88)
blue=np.clip(.05+.46*(green-.40),.05,.32)
rgb=np.stack([np.ones_like(green),green,blue],axis=2)
rgb[alpha<.002]=0
rgba=Image.fromarray(np.uint8(np.clip(np.concatenate([rgb,alpha[...,None]],axis=2),0,1)*255))
rgba.save(HERE/'contact-extracted.png')

# Uniformly enlarge the source crop with transparent padding. The authored
# nucleus remains fixed and all longer filaments spread toward local +X.
scale=1.8
size=(round(source.width*scale),round(source.height*scale))
origin=(16,5)
canvas=Image.new('RGBA',(512,192))
canvas.paste(rgba.resize(size,Image.Resampling.LANCZOS),origin)
# Use the bright centre within the known nucleus, not an unrelated particle.
region=(distance<7)&(alpha>.35)
weight=alpha*p[...,1]*region
cx=float((x*weight).sum()/weight.sum())
cy=float((y*weight).sum()/weight.sum())
anchor=[(origin[0]+(cx+.5)*size[0]/source.width)/512,(origin[1]+(cy+.5)*size[1]/source.height)/192]
name='fire-contact-fan-v30'
canvas.save(HERE/(name+'.png'),optimize=True)
canvas.save(RES/(name+'.png'),optimize=True)
meta=RES/(name+'.png.meta')
if not meta.exists():
    text=(RES/'fire-lance-v30.png.meta').read_text(encoding='utf8')
    old=json.loads(text)['uuid']
    meta.write_text(text.replace(old,str(uuid.uuid4())).replace('fire-lance-v30',name),encoding='utf8')

preview=Image.new('RGB',(1024,430),'#28312c')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
draw=ImageDraw.Draw(preview)
draw.text((12,10),'v29 已批短接触散焰 / 单纹理素材小样，非实景',font=font,fill='#eac187')
q=np.asarray(canvas,dtype=float)/255
for i,(bg,gain) in enumerate([([40,49,44],1),([86,80,70],1)]):
    a=q[...,3,None]
    out=q[...,:3]*a*1.10+np.array(bg)/255*(1-a*.90)
    preview.paste(Image.fromarray(np.uint8(np.clip(out,0,1)*255)),(i*512,52))
draw.text((12,267),f'anchorUV=({anchor[0]:.9f}, {anchor[1]:.9f}) / 核心固定，火丝向 +X 展开',font=font,fill='#eac187')
preview.paste(source.resize((500,202)),(12,305))
preview.save(HERE/'contact-material-preview.jpg',quality=95,subsampling=0)
record=dict(reference=str(REF.relative_to(ROOT)),referenceSha256=hashlib.sha256(REF.read_bytes()).hexdigest(),sourceRegion=BOX,
    method='Deterministic 7px warm-signal white top-hat preserves short bright filaments, a source-aligned <=13px star nucleus is retained, and geometric/body masks reject the left armour and lower soldier. No generated image or local inference.',
    layout=dict(name=name,size=[512,192],singleTexture=True,straightRGBA=True,headAnchorUV=anchor,sourceNucleusCentre=[cx+BOX[0],cy+BOX[1]],direction='+X fan; short star nucleus near the left',
        rendererPlacement='For UV-v down card with centred quad, position=(-[anchorU-.5]*width, [anchorV-.5]*height). Preserve nucleus at hit anchor; curve the positive-X fan only.'),
    output=dict(path=str((RES/(name+'.png')).relative_to(ROOT)),sha256=hashlib.sha256((RES/(name+'.png')).read_bytes()).hexdigest(),pngBytes=(RES/(name+'.png')).stat().st_size),
    review=dict(localSample='Inspected source crop and extracted contact on dark and mid-tone backgrounds: compact golden nucleus with short curved +X filaments; broad diffuse floor glow and identifiable character silhouettes removed.',actualCocos='pending',userArtAcceptance='approved source style; native contact not yet reviewed'))
(HERE/'contact-provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
