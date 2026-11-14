"""Compare unretouched equipment screenshots at a common logical scale."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
OUT=PROJECT/'src/cocos/test-results/equipment-alignment-v5'
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)

def board(path):
    image=Image.open(path).convert('RGB')
    if abs(image.width/image.height-844/390)>.02:
        height=image.width*390/844;y=(image.height-height)/2
        image=image.crop((0,round(y),image.width,round(y+height)))
    return image.resize((844,390),Image.Resampling.LANCZOS)

reference=board(HERE/'references/approved-equipment.png')
old=board(HERE/'references/annotated-runtime.png')
fresh=board(OUT/'fresh-wide-equipment.png')
developed=board(OUT/'mobile-equipment.png')
columns=[(reference,'原设计稿 · 示例装备'),(old,'用户标出的旧运行界面'),(fresh,'修正后运行界面 · 1级新档')]
regions=[('防具和首饰槽',(40,72,285,292)),('人物脚下的主副手新位置',(110,274,222,330)),('连续分类栏',(308,48,572,113)),('物品插画和边框',(320,113,573,333)),('武器横向展示',(586,33,843,125)),('属性比较与来源',(596,127,835,330))]
sheet=Image.new('RGB',(1260,54+len(regions)*230),'#18110b');d=ImageDraw.Draw(sheet)
for col,(_,title) in enumerate(columns):d.text((col*420+14,12),title,font=FONT,fill='#dfc78f')
for row,(title,rect) in enumerate(regions):
    for col,(image,_) in enumerate(columns):
        x=col*420;y=54+row*230;d.text((x+14,y+4),title,font=FONT,fill='#dfc78f')
        crop=image.crop(rect);scale=min(390/crop.width,184/crop.height)
        crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
        sheet.paste(crop,(x+(420-crop.width)//2,y+36+(184-crop.height)//2))
sheet.save(HERE/'review/details-comparison.jpg',quality=97)
full=Image.new('RGB',(844,1272),'#18110b');d=ImageDraw.Draw(full)
for i,(image,title) in enumerate(columns):
    d.text((14,i*424+5),title,font=FONT,fill='#dfc78f');full.paste(image,(0,i*424+34))
full.save(HERE/'review/equipment-comparison.jpg',quality=97)
fresh.save(HERE/'review/equipment-runtime.jpg',quality=97)
developed.save(HERE/'review/equipment-developed.jpg',quality=97)
records=[]
for name in ['fresh-wide-equipment.png','fresh-mobile-equipment.png','mobile-equipment.png','desktop-equipment.png','mobile-large-equipment.png']:
    path=OUT/name;records.append({'file':path.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(HERE/'runtime-review.json').write_text(json.dumps({'method':'Unretouched Cocos screenshots; letterbox crop, scale and layout only','regions':[{'name':title,'logical_rect':rect} for title,rect in regions],'states':'Isolated level 1 and level 16 profiles; inventory, rarity and forging values remain actual game state.','requested_layout_change':'Both hand sockets moved to portrait feet, approximately logical x 138/194.3, y 300.','user_art_acceptance':'pending','captures':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared equipment comparison and actual runtime views.')
