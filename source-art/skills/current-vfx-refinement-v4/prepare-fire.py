"""Recover shaded flame volume from the current source art and feather its existing contact edges."""
from pathlib import Path
import json
import hashlib
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ASSETS=HERE/'assets'
RAW=ROOT/'source-art/skills/fire-runtime-v7/generated-atlas.png'
CURRENT=ROOT/'src/cocos/assets/resources/vfx/production/fire-pyro-v7.png'


def smooth(value):
    t=np.clip(value,0,1)
    return t*t*(3-2*t)


def main():
    ASSETS.mkdir(exist_ok=True)
    source=Image.open(RAW).convert('RGBA')
    current=Image.open(CURRENT).convert('RGBA')
    assert source.size==current.size==(1536,1024)
    atlas=Image.new('RGBA',source.size)
    for frame in range(16):
        x=frame%4*384
        y=frame//4*256
        box=(x,y,x+384,y+256)
        tile=np.asarray(source.crop(box)).copy()
        existing=current.crop(box).getchannel('A')
        # Fill enclosed transparent holes with the original shaded pixels, retaining the original contour.
        support=existing.point(lambda value:255 if value>12 else 0)
        support=support.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
        flood=Image.new('L',(386,258))
        flood.paste(support,(1,1))
        ImageDraw.floodfill(flood,(0,0),128)
        enclosed=Image.fromarray(np.uint8(np.asarray(flood)[1:-1,1:-1]!=128)*255)
        enclosed=enclosed.filter(ImageFilter.GaussianBlur(1.5))
        recovered=tile[:,:,3].astype(float)*np.asarray(enclosed,dtype=float)/255
        alpha=np.maximum(np.asarray(existing,dtype=float)*.96,recovered)
        yy,xx=np.indices(alpha.shape)
        side=(xx-192)/192
        floor=242-14*side*side+1.8*np.sin(side*7)
        alpha*=smooth((floor-yy)/20)
        alpha*=smooth(np.minimum(xx,383-xx)/5)
        alpha*=smooth(yy/5)
        tile[:,:,3]=np.uint8(np.clip(alpha,0,255))
        tile[tile[:,:,3]==0]=0
        atlas.alpha_composite(Image.fromarray(tile),(x,y))
    atlas.save(ASSETS/'fire-pyro-v7.png')
    # Keep the same 4 x 8 layout and bottom anchor while retaining more of the original roll detail.
    low=Image.new('RGBA',(1024,1536))
    for side in range(2):
        for frame in range(16):
            left=.03 if side==0 else .53
            col=frame%4
            row=frame//4
            box=(round((col+left)*384),round((row+.48)*256),round((col+left+.44)*384),round((row+.94)*256))
            tile=atlas.crop(box)
            data=np.asarray(tile).copy()
            h,w=data.shape[:2]
            yy,xx=np.indices((h,w))
            feather=smooth(np.minimum(xx,w-1-xx)/(w*.16))*smooth(yy/(h*.18))*smooth((h-1-yy)/(h*.14))
            data[:,:,3]=np.uint8(data[:,:,3]*feather)
            tile=Image.fromarray(data)
            ratio=min(248/tile.width,174/tile.height)
            tile=tile.resize((round(tile.width*ratio),round(tile.height*ratio)),Image.Resampling.LANCZOS)
            index=frame+side*16
            low.alpha_composite(tile,(index%4*256+(256-tile.width)//2,index//4*192+180-tile.height))
    low.save(ASSETS/'fire-low-rolls-v7.png')
    before=current.crop((384,256,768,512)).resize((576,384),Image.Resampling.LANCZOS)
    after=atlas.crop((384,256,768,512)).resize((576,384),Image.Resampling.LANCZOS)
    plate=Image.new('RGB',(1152,384),(120,111,93))
    plate.paste(before,(0,0),before)
    plate.paste(after,(576,0),after)
    plate.save(ASSETS/'fire-extraction-comparison.jpg',quality=94)
    data={
        'method':'Deterministic processing of the existing production image and its original source',
        'newGeneration':False,
        'sourceArt':str(RAW.relative_to(ROOT)),
        'currentAtlas':str(CURRENT.relative_to(ROOT)),
        'sourceSHA256':hashlib.sha256(RAW.read_bytes()).hexdigest(),
        'currentSHA256':hashlib.sha256(CURRENT.read_bytes()).hexdigest(),
        'processing':['Restore enclosed shadow detail inside the current flame silhouette','Round and feather the current foot edge','Retain existing keyframes and atlas layout','Increase low-roll cell resolution from 128 x 96 to 256 x 192'],
        'acceptance':'Awaiting visual review'
    }
    (HERE/'fire-processing.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')


if __name__=='__main__':main()
