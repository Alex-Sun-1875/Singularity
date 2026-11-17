"""Engineering pass for the generated thick fire wave; no extra inference."""
from pathlib import Path
import hashlib,json,uuid
import numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
RES=ROOT/'src/cocos/assets/resources/vfx/production'
SOURCE=HERE/'fire-wave-cloud-original.png'
NAME='fire-meteor-roll-v31'
def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

original=Image.open(SOURCE).convert('RGBA')
p=np.asarray(original,dtype=float)/255
raw_alpha=p[...,3].copy()
rgb=p[...,:3]
gold=smooth((rgb[...,1]/np.maximum(rgb[...,0],1e-6)-.45)/.40)
# Preserve the newly requested dense body. This gentle optical remap does not
# isolate ridges, delete volume, colour-key the body, or create hollow regions.
alpha=raw_alpha*(.79+.09*gold)
alpha=.96*alpha+.04*np.asarray(Image.fromarray(np.uint8(np.clip(alpha,0,1)*255)).filter(ImageFilter.GaussianBlur(.55)),dtype=float)/255
premul=np.concatenate([rgb*alpha[...,None],alpha[...,None]],axis=2)

# Keep aspect through this resize; only the right/left overlap is merged.
W,H,OVERLAP,CONTENT_H,TOP=1024,512,128,461,56
wide=np.stack([np.asarray(Image.fromarray(premul[...,c].astype(np.float32)).resize((W+OVERLAP,CONTENT_H),Image.Resampling.LANCZOS),dtype=float) for c in range(4)],axis=2)
wide=np.maximum(wide,0)
wide[...,3]=np.minimum(wide[...,3],.9)
tile=wide[:,:W].copy()
t=smooth(np.arange(OVERLAP)/(OVERLAP-1))[None,:,None]
tile[:,:OVERLAP]=wide[:,W:W+OVERLAP]*(1-t)+wide[:,:OVERLAP]*t
out=np.zeros((H,W,4),dtype=float)
available=min(CONTENT_H,H-TOP)
out[TOP:TOP+available]=tile[:available]
y,x=np.mgrid[:H,:W]
# Authored lower silhouette is already uneven. Only fade the extreme padded
# border and tiny generated fringe; do not impose a horizontal solid cutoff.
edge=smooth(y/14)*smooth((H-1-y)/(15+3*np.sin(x*.018)+2*np.sin(x*.041)))
out*=edge[...,None]
seam=(out[:,0]+out[:,-1])*.5
out[:,0]=seam;out[:,-1]=seam
colour=out[...,:3]/np.maximum(out[...,3,None],1e-6)
rgba=np.concatenate([colour,out[...,3,None]],axis=2)
image=Image.fromarray(np.uint8(np.clip(rgba,0,1)*255))
image.save(HERE/(NAME+'.png'),optimize=True)
image.save(RES/(NAME+'.png'),optimize=True)
meta=RES/(NAME+'.png.meta')
if not meta.exists():
    data=json.loads((RES/'fire-lance-v30.png.meta').read_text(encoding='utf8'))
    identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/'+NAME+'.png'))
    data['uuid']=identity
    texture=data['subMetas']['6c48a']
    texture['uuid']=identity+'@6c48a';texture['displayName']=NAME
    texture['userData']['imageUuidOrDatabaseUri']=identity
    texture['userData']['wrapModeS']='repeat';texture['userData']['wrapModeT']='clamp-to-edge'
    data['userData']['redirect']=identity+'@6c48a'
    meta.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

q=np.asarray(image,dtype=float)/255
a=q[...,3]
occupied=a>.05
body=(y>H*.38)&(y<H*.90)&(a>.35)
warm=occupied&(q[...,0]-q[...,2]>.20)
bright=occupied&(q[...,0]>.85)&(q[...,1]>.55)&(q[...,0]-q[...,2]>.20)
metrics=dict(alphaMean=float(a.mean()),fractionAlphaAbove035=float((a>.35).mean()),fractionAlphaAbove065=float((a>.65).mean()),
    fractionAlphaAbove095=float((a>.95).mean()),bodyAlphaQuantiles=np.quantile(a[body],[.10,.50,.90]).tolist(),
    occupiedWarmFraction=float(warm.sum()/occupied.sum()),occupiedBrightGoldFraction=float(bright.sum()/occupied.sum()),
    occupiedRGBQuantiles255=np.round(np.quantile(q[occupied,:3],[.10,.50,.90],axis=0)*255,1).tolist(),
    oppositeUEdgeMaxPixelDifference=int(np.abs(np.asarray(image)[:,0].astype(int)-np.asarray(image)[:,-1].astype(int)).max()))

font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
preview=Image.new('RGB',(1120,830),'#28312c')
d=ImageDraw.Draw(preview)
d.text((12,10),'v31 云端厚火浪 / 保留橙金火体 + 周期U工程处理 / 素材小样，非实景',font=font,fill='#eac187')
def composite(bg):
    al=q[...,3,None]
    rgb=q[...,:3]*al*1.10+np.array(bg)/255*(1-al*.90)
    return Image.fromarray(np.uint8(np.clip(rgb,0,1)*255))
dark=composite([40,49,44]);mid=composite([86,80,70])
preview.paste(dark.resize((1060,530)),(30,42))
d.text((12,585),'重复接缝检视（两次连续U，缩略） / 用材质opacity控制叠层通透，未掏空body',font=small,fill='#eac187')
for i in range(2):preview.paste(mid.resize((540,270)),(20+i*540,610))
preview.save(HERE/'material-preview.jpg',quality=95,subsampling=0)
image.getchannel('A').save(HERE/'alpha-preview.png')
record=dict(generation=dict(tool='OpenAI image_gen built-in cloud tool',status='completed',localModelInference=False,prompt='prompt.txt',original=SOURCE.name,originalSize=original.size,originalSha256=sha(SOURCE)),
    processing='Deterministic Pillow/NumPy engineering only. Preserve full orange-gold body and broad folds; smooth alpha remap of original body to .79..88; premultiplied aspect-preserving resize, 128px same-source U overlap, soft upper/lower fringe and exact matching U edge pixels.',
    output=dict(name=NAME,path=str((RES/(NAME+'.png')).relative_to(ROOT)),size=[W,H],singleTexture=True,straightRGBA=True,sha256=sha(RES/(NAME+'.png')),pngBytes=(RES/(NAME+'.png')).stat().st_size,rgbaMemoryBytes=W*H*4),
    uv=dict(rootV=.9375,rootPixelY=480,usableU=[0,1],repeatU=True,repeatV=False,paddedTopV=TOP/H,mainBodyV=[.35,.915],tipSilhouetteV=[.10,.55],lowerSoftFringeV=[.90,1.0],
        instruction='Use fract(U) before sampling; clamp V. Root/foot at V=.9375 stays pinned while inner folds transport upward; retain the authored uneven lower soft silhouette.'),
    metrics=metrics,productionUpdated=True,
    review=dict(generation='successful',localMaterial='Original source and processed dark/mid-background material preview inspected: wide connected orange-gold body, broad rolling crests, no high-frequency body deletion; U repeat visually continuous. This is a material review only.',nativeCocos='pending capture and art review',userRuntimeAcceptance='pending',taptapDevice='pending'))
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
