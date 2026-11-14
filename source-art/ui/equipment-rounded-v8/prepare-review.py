"""Export unretouched gear-frame comparisons from Cocos runtime screenshots."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
OUT=PROJECT/'src/cocos/test-results/equipment-rounded-v8'
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
def board(path):
    image=Image.open(path).convert('RGB')
    if abs(image.width/image.height-844/390)>.02:
        h=image.width*390/844;y=(image.height-h)/2;image=image.crop((0,round(y),image.width,round(y+h)))
    return image.resize((844,390),Image.Resampling.LANCZOS)
artifact=board(OUT/'mobile-artifact-equipped.png')
normal=board(OUT/'fresh-mobile-equipment.png')
legendary=board(OUT/'mobile-equipment.png')
artifact.save(HERE/'review/equipment-runtime.jpg',quality=97)
normal.save(HERE/'review/equipment-fresh.jpg',quality=97)
nativeArtifact=Image.open(OUT/'mobile-artifact-equipped.png').convert('RGB');nativeNormal=Image.open(OUT/'fresh-mobile-equipment.png').convert('RGB')
tiles=[('神器 · 内侧四角花纹',nativeArtifact,(324,112,380,162)),('传奇 · 简洁圆角框',nativeArtifact,(452,112,508,162)),('普通 · 简洁圆角框',nativeNormal,(324,112,380,162)),('主副手名称在框下',nativeArtifact,(110,270,220,332))]
detail=Image.new('RGB',(1200,300),'#18110b');d=ImageDraw.Draw(detail)
for i,(title,image,rect) in enumerate(tiles):
    x=i*300;d.text((x+12,8),title,font=FONT,fill='#dfc78f');factor=image.width/844;crop=image.crop(tuple(round(v*factor) for v in rect));scale=min(260/crop.width,228/crop.height);crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS);detail.paste(crop,(x+(300-crop.width)//2,42+(228-crop.height)//2))
detail.save(HERE/'review/frame-details.jpg',quality=97)
pages=[(board(PROJECT/'src/cocos/test-results/equipment-alignment-v5/fresh-mobile-equipment.png'),'上一版 · 1级'),(normal,'修正后 · 1级'),(legendary,'修正后 · 传奇已装备'),(artifact,'修正后 · 神器已装备')]
full=Image.new('RGB',(844,1696),'#18110b');d=ImageDraw.Draw(full)
for i,(image,title) in enumerate(pages):d.text((14,i*424+5),title,font=FONT,fill='#dfc78f');full.paste(image,(0,i*424+34))
full.save(HERE/'review/equipment-comparison.jpg',quality=97)
forge=board(OUT/'mobile-forge.png');forge.save(HERE/'review/forge-runtime.jpg',quality=97)
captures=[]
for name in ['fresh-mobile-equipment.png','fresh-wide-equipment.png','mobile-equipment.png','mobile-artifact-selected.png','mobile-artifact-equipped.png','desktop-artifact-equipped.png','mobile-large-artifact-equipped.png','mobile-forge.png']:
    p=OUT/name;captures.append({'file':p.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(HERE/'runtime-review.json').write_text(json.dumps({'method':'Actual Cocos runtime pixels; letterbox crop, scale and layout only.','rule':'All gear frames rounded; exactly four inner ornaments only for artifact quality, independent of selected state.','user_art_acceptance':'pending','captures':captures},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared rounded frame comparisons.')
