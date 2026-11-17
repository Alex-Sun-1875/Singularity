"""Deterministically extract v29's comet sheath and moving tail; no generation."""
from pathlib import Path
import hashlib
import json
import math
import uuid
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SOURCE=ROOT/'source-art/skills/fire-distinct-shapes-design-v29/fire-distinct-shapes-v29.png'
PRODUCTION=ROOT/'src/cocos/assets/resources/vfx/production'
NAME='fire-meteor-reference-tail-v32'
CROP=(349,697,651,880)
NOSE=np.array([370-349,868-697],dtype=float)
CELL=(512,192)


def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)


def rgba(pma):
    return Image.fromarray(np.uint8(np.clip(np.dstack([pma[...,:3]/np.maximum(pma[...,3,None],1e-5),pma[...,3]]),0,1)*255),'RGBA')


def sample(a,x,y):
    valid=(x>=0)&(x<=a.shape[1]-1)&(y>=0)&(y<=a.shape[0]-1)
    x=np.clip(x,0,a.shape[1]-1.001);y=np.clip(y,0,a.shape[0]-1.001)
    ix=x.astype(int);iy=y.astype(int);tx=(x-ix)[...,None];ty=(y-iy)[...,None]
    return (a[iy,ix]*(1-tx)*(1-ty)+a[iy,ix+1]*tx*(1-ty)+a[iy+1,ix]*(1-tx)*ty+a[iy+1,ix+1]*tx*ty)*valid[...,None]


def main():
    source=Image.open(SOURCE).convert('RGB');crop=source.crop(CROP)
    p=np.asarray(crop,dtype=float)/255;r,g,b=p[...,0],p[...,1],p[...,2]
    known=(r-b<.115)&(r<.56)
    rf=np.polyfit(b[known],r[known],1);gf=np.polyfit(b[known],g[known],1)
    rf[0]=np.clip(rf[0],.65,1.5);gf[0]=np.clip(gf[0],.65,1.4)
    contrast=r-rf[0]*b-rf[1];blue=np.full_like(r,.15)
    for _ in range(3):
        alpha=np.clip(contrast/np.maximum(1-rf[0]*blue-rf[1],.2),0,.91)
        green=(g-gf[0]*b-gf[1])/np.maximum(alpha,1e-5)+gf[0]*blue+gf[1]
        blue=np.clip(.045+.59*(green-.37),.035,.36)
    alpha*=smooth((contrast-.015)/.10)*smooth((r-.30)/.55)
    alpha*=smooth((alpha-.025)/.10)
    colour=np.stack([np.ones_like(r),np.clip(green,.35,.84),np.clip(blue,.035,.36)],axis=-1)
    mask=Image.new('L',crop.size);d=ImageDraw.Draw(mask)
    # Tight original silhouette excludes the ground sigil, title and caster's
    # hand. It preserves the drawn fire around the real rock's dark interior.
    polygon=[(21,175),(8,151),(12,112),(32,81),(57,67),(76,45),(102,36),(136,14),(157,0),(302,0),(269,22),(244,34),(212,49),(175,69),(143,91),(126,113),(109,132),(92,146),(69,158),(45,168)]
    d.polygon(polygon,fill=255)
    mask=np.asarray(mask.filter(ImageFilter.GaussianBlur(.85)),dtype=float)/255
    alpha*=mask
    raw=np.dstack([colour,alpha]);raw_image=Image.fromarray(np.uint8(np.clip(raw,0,1)*255),'RGBA')
    # A tiny separate landmark is transformed with the exact same Pillow
    # operation, keeping the chosen reference nose an auditable fixed pivot.
    marker=Image.new('L',crop.size);ImageDraw.Draw(marker).ellipse((NOSE[0]-1,NOSE[1]-1,NOSE[0]+1,NOSE[1]+1),fill=255)
    angle=math.degrees(math.atan2(NOSE[1],NOSE[0]-278))
    rotated=raw_image.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    landmark=marker.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    bbox=rotated.getchannel('A').getbbox();rotated=rotated.crop(bbox);landmark=landmark.crop(bbox)
    scale=min((CELL[0]-36)/rotated.width,(CELL[1]-28)/rotated.height)
    size=(round(rotated.width*scale),round(rotated.height*scale))
    ox=18;oy=(CELL[1]-size[1])//2
    base_image=Image.new('RGBA',CELL);base_image.paste(rotated.resize(size,Image.Resampling.LANCZOS),(ox,oy))
    m=Image.new('L',CELL);m.paste(landmark.resize(size,Image.Resampling.BICUBIC),(ox,oy))
    ma=np.asarray(m,dtype=float);yy,xx=np.mgrid[:CELL[1],:CELL[0]]
    nose=np.array([(xx*ma).sum()/ma.sum(),(yy*ma).sum()/ma.sum()])
    a=np.asarray(base_image,dtype=float)/255;a[...,:3]*=a[...,3,None]
    pin=smooth((nose[0]-xx-38)/145)
    frames=[]
    for index in range(16):
        phase=index/16;other=(phase+.5)%1;weight=np.sin(math.pi*phase)**2
        def flowing(q):
            return sample(a,xx+q*18*pin,yy+np.sin(q*math.tau-xx*.035)*1.7*pin)
        moving=flowing(phase)*weight+flowing(other)*(1-weight)
        out=a*.38+moving*.62
        out[...,3]=np.minimum(out[...,3],.91)
        frames.append(rgba(out))
    atlas=Image.new('RGBA',(CELL[0]*4,CELL[1]*4))
    for i,frame in enumerate(frames):atlas.paste(frame,((i%4)*CELL[0],(i//4)*CELL[1]))
    output=PRODUCTION/(NAME+'.png');atlas.save(output,optimize=True)
    meta=json.loads((PRODUCTION/'fire-lance-v30.png.meta').read_text(encoding='utf8'))
    identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/'+NAME+'.png'))
    meta['uuid']=identity;sub=meta['subMetas']['6c48a'];sub['uuid']=identity+'@6c48a';sub['displayName']=NAME;sub['userData']['imageUuidOrDatabaseUri']=identity;meta['userData']['redirect']=identity+'@6c48a'
    output.with_suffix('.png.meta').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
    backgrounds=['#252d2a','#514b43'];board=Image.new('RGB',(1024,440),'#252d2a')
    for i,bg in enumerate(backgrounds):
        panel=Image.new('RGBA',CELL,bg);panel.alpha_composite(frames[3]);board.paste(panel.convert('RGB'),(i*512,35))
    board.paste(crop.resize((604,366)).crop((0,0,604,183)),(0,247))
    draw=ImageDraw.Draw(board);draw.text((14,10),'v29 comet sheath / tail: original nose pinned, floor and hand excluded',fill='#eed3ab');draw.text((14,422),f'+X nose UV: ({nose[0]/512:.12f}, {nose[1]/192:.12f}); texture sample, not native capture',fill='#eed3ab')
    board.save(HERE/'material-preview.png',optimize=True)
    movie=[]
    for frame in frames:
        bg=Image.new('RGBA',CELL,'#252d2a');bg.alpha_composite(frame);movie.append(bg.convert('RGB'))
    movie[0].save(HERE/'material-loop.webp',save_all=True,append_images=movie[1:],duration=62,loop=0,quality=94)
    record={'reference':SOURCE.relative_to(ROOT).as_posix(),'referenceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'method':'deterministic original-fire matte, contour exclusion, coordinate rotation and forward detail transport; no generation','crop':CROP,'sourceNose':NOSE.tolist(),'rotationDegrees':angle,'cell':CELL,'grid':[4,4],'frames':16,'nosePixel':nose.tolist(),'noseUV':(nose/np.array(CELL)).tolist(),'orientation':'+X points from tail toward leading nose','excluded':['ground sigil','caster hand','neutral terrain','most dark rock interior'],'output':output.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size,'review':{'materialSample':'pending visual inspection','nativeCocos':'pending','userArtAcceptance':'pending'}}
    (HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(record,ensure_ascii=False))


if __name__=='__main__':main()
