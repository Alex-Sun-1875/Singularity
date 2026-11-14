"""Make the six user-marked regions directly comparable at a common scale."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
OUT=PROJECT/'src/cocos/test-results/ui-detail-v4'
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
def board(path):
 im=Image.open(path).convert('RGB')
 if abs(im.width/im.height-844/390)>.02:
  h=im.width*390/844;y=(im.height-h)/2;im=im.crop((0,round(y),im.width,round(y+h)))
 return im.resize((844,390),Image.Resampling.LANCZOS)
reference=board(ROOT/'references/approved-character.png')
before=board(ROOT/'references/annotated-runtime.png')
current=board(OUT/'fresh-wide-character.png')
columns=[(reference,'原设计稿 · 示例数值'),(before,'用户标出的旧运行界面'),(current,'修正后运行界面 · 1级真实状态')]
regions=[('导航高亮',(205,19,318,36)),('核心属性分隔线',(308,71,570,81)),('加号按钮',(527,94,562,123)),('战斗属性行',(594,76,822,102)),('构筑图标边框',(610,208,674,264)),('底栏装饰线',(190,350,454,376))]
sheet=Image.new('RGB',(1260,54+len(regions)*185),'#18110b');d=ImageDraw.Draw(sheet)
for col,(_,title) in enumerate(columns):d.text((col*420+14,12),title,font=FONT,fill='#dfc78f')
for row,(label,rect) in enumerate(regions):
 for col,(im,_) in enumerate(columns):
  y=54+row*185;x=col*420;d.text((x+14,y+4),label,font=FONT,fill='#dfc78f');crop=im.crop(rect);scale=min(390/crop.width,132/crop.height)
  crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS);sheet.paste(crop,(x+(420-crop.width)//2,y+36+(132-crop.height)//2))
sheet.save(ROOT/'review/six-details-comparison.jpg',quality=97)
full=Image.new('RGB',(844,848),'#18110b');d=ImageDraw.Draw(full)
for y,(im,title) in enumerate([(reference,'设计稿'),(current,'修正后游戏运行画面 · 1级')]):
 d.text((14,y*424+5),title,font=FONT,fill='#dfc78f');full.paste(im,(0,y*424+34))
full.save(ROOT/'review/character-comparison.jpg',quality=97)
current.save(ROOT/'review/character-runtime.jpg',quality=97)
records=[]
for name in ['fresh-wide-character.png','fresh-mobile-character.png','mobile-character-preview.png']:
 p=OUT/name;records.append({'file':p.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'runtime-review.json').write_text(json.dumps({'method':'Unretouched Cocos screenshots; letterbox crop, resize and side-by-side region layout only','regions':[{ 'name':n,'logical_rect':r } for n,r in regions],'states':'Fresh level 1 and developed level 16 profiles; numbers and unlocked skill counts remain actual game data','user_art_acceptance':'pending','captures':records},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Prepared six-detail and full-character comparisons.')
