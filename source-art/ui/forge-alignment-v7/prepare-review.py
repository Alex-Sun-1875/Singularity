"""Compare original art and unretouched workshop runtime captures."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
OUT=PROJECT/'src/cocos/test-results/forge-alignment-v7'
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
def board(path):
    image=Image.open(path).convert('RGB')
    if abs(image.width/image.height-844/390)>.02:
        h=image.width*390/844;y=(image.height-h)/2;image=image.crop((0,round(y),image.width,round(y+h)))
    return image.resize((844,390),Image.Resampling.LANCZOS)
reference=board(HERE/'references/approved-forge.png')
old=board(HERE/'references/annotated-runtime.png')
fresh=board(OUT/'fresh-wide-preview.png')
current=board(OUT/'mobile-preview.png')
columns=[(reference,'原稿 · 旧方案示例'),(old,'用户标出的旧运行界面 · 1级'),(current,'修正后运行界面 · 16级审阅档')]
regions=[('工坊页签',(300,38,545,107)),('装备插画与选中框',(24,105,240,166)),('完整房间与武器展示',(245,74,563,329)),('展示台与余火铭牌',(280,266,541,329)),('随机强化主预览',(575,72,824,200)),('费用材料图块',(583,204,825,269)),('余额与状态',(583,270,825,324)),('传承、确认和底栏',(18,343,828,384))]
sheet=Image.new('RGB',(1260,54+len(regions)*220),'#18110b');d=ImageDraw.Draw(sheet)
for col,(_,title) in enumerate(columns):d.text((col*420+14,12),title,font=FONT,fill='#dfc78f')
for row,(title,rect) in enumerate(regions):
    for col,(image,_) in enumerate(columns):
        x=col*420;y=54+row*220;d.text((x+14,y+4),title,font=FONT,fill='#dfc78f');crop=image.crop(rect);scale=min(390/crop.width,174/crop.height);crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS);sheet.paste(crop,(x+(420-crop.width)//2,y+35+(174-crop.height)//2))
sheet.save(HERE/'review/details-comparison.jpg',quality=97)
full=Image.new('RGB',(844,1696),'#18110b');d=ImageDraw.Draw(full)
for i,(image,title) in enumerate([columns[0],columns[1],(fresh,'修正后运行界面 · 1级新档'),columns[2]]):d.text((14,i*424+5),title,font=FONT,fill='#dfc78f');full.paste(image,(0,i*424+34))
full.save(HERE/'review/forge-comparison.jpg',quality=97);current.save(HERE/'review/forge-runtime.jpg',quality=97);fresh.save(HERE/'review/forge-fresh.jpg',quality=97)
services=Image.new('RGB',(1266,2*317),'#18110b');d=ImageDraw.Draw(services)
for i,(key,title) in enumerate([('pool','随机词条'),('result','强化结果'),('inheritance-preview','传承预览'),('craft','锻造')]):
    image=board(OUT/f'mobile-{key}.png').resize((633,293),Image.Resampling.LANCZOS);x=i%2*633;y=i//2*317;d.text((x+10,y),title,font=FONT,fill='#dfc78f');services.paste(image,(x,y+24))
services.save(HERE/'review/workshop-services.jpg',quality=97)
captures=[]
for name in ['fresh-mobile-preview.png','fresh-wide-preview.png','mobile-preview.png','desktop-preview.png','mobile-large-preview.png','mobile-pool.png','mobile-result.png','mobile-inheritance-preview.png','mobile-craft.png']:
    p=OUT/name;captures.append({'file':p.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(HERE/'runtime-review.json').write_text(json.dumps({'method':'Unretouched Cocos screenshots; letterbox crop, scale and layout only.','regions':[{'name':n,'logical_rect':r} for n,r in regions],'states':'Actual isolated level 1 and level 16 profiles. Costs and random affixes remain actual game data; reference fixed enhancement power is historical.','user_art_acceptance':'pending','captures':captures},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared workshop comparisons and service views.')
