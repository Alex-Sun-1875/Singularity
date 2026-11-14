"""Lay out actual Cocos screenshots without retouching runtime pixels."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
OUT=PROJECT/'src/cocos/test-results/skills-alignment-v6'
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)

def board(path):
    image=Image.open(path).convert('RGB')
    if abs(image.width/image.height-844/390)>.02:
        height=image.width*390/844;y=(image.height-height)/2
        image=image.crop((0,round(y),image.width,round(y+height)))
    return image.resize((844,390),Image.Resampling.LANCZOS)

reference=board(HERE/'references/approved-skills.png')
old=board(HERE/'references/annotated-runtime.png')
fresh=board(OUT/'fresh-wide-skills.png')
current=board(OUT/'mobile-skills.png')
columns=[(reference,'原设计稿 · 示例配置'),(old,'用户标出的旧运行界面 · 1级'),(current,'修正后运行界面 · 16级审阅档')]
regions=[
    ('连续流派栏与技能点',[(18,40,582,104)]*3),
    ('技能类型标签',[(94,87,140,107),(100,112,146,133),(98,112,144,133)]),
    ('选中技能光框',[(18,82,170,159),(20,107,164,181),(18,106,170,185)]),
    ('右侧大图、类型和等级',[(610,40,831,134)]*3),
    ('机制说明与升级对比',[(610,136,831,197)]*3),
    ('升级预览与加减按钮',[(615,211,824,246)]*3),
    ('主动槽位编号饰框',[(149,272,203,301)]*3),
    ('底栏装饰线',[(194,350,454,376)]*3),
]
sheet=Image.new('RGB',(1260,54+len(regions)*190),'#18110b');d=ImageDraw.Draw(sheet)
for col,(_,title) in enumerate(columns):d.text((col*420+14,12),title,font=FONT,fill='#dfc78f')
for row,(title,rects) in enumerate(regions):
    for col,(image,_) in enumerate(columns):
        x=col*420;y=54+row*190;d.text((x+14,y+4),title,font=FONT,fill='#dfc78f');crop=image.crop(rects[col]);scale=min(390/crop.width,145/crop.height)
        crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS);sheet.paste(crop,(x+(420-crop.width)//2,y+35+(145-crop.height)//2))
sheet.save(HERE/'review/details-comparison.jpg',quality=97)
full=Image.new('RGB',(844,1696),'#18110b');d=ImageDraw.Draw(full)
for i,(image,title) in enumerate([columns[0],columns[1],(fresh,'修正后运行界面 · 1级新档'),columns[2]]):
    d.text((14,i*424+5),title,font=FONT,fill='#dfc78f');full.paste(image,(0,i*424+34))
full.save(HERE/'review/skills-comparison.jpg',quality=97)
current.save(HERE/'review/skills-runtime.jpg',quality=97);fresh.save(HERE/'review/skills-fresh.jpg',quality=97)
familySheet=Image.new('RGB',(1266,5*317),'#18110b');d=ImageDraw.Draw(familySheet)
for i,(key,title) in enumerate([('war','破军'),('bow','逐风'),('fir','烈焰'),('thu','雷霆'),('com','通用')]):
    image=board(OUT/f'mobile-{key}.png');image=image.resize((633,293),Image.Resampling.LANCZOS);d.text((10,i*317),title,font=FONT,fill='#dfc78f');familySheet.paste(image,(0,i*317+24));detail=board(OUT/f'mobile-{key}.png').crop((593,32,837,253));detail.thumbnail((605,293));familySheet.paste(detail,(650,i*317+24))
familySheet.save(HERE/'review/all-families.jpg',quality=96)
captures=[]
for name in ['fresh-mobile-skills.png','fresh-wide-skills.png','mobile-skills.png','desktop-skills.png','mobile-large-skills.png']+[f'mobile-{k}.png' for k in ['war','bow','fir','thu','com']]:
    path=OUT/name;captures.append({'file':path.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(HERE/'runtime-review.json').write_text(json.dumps({'method':'Unretouched Cocos screenshots; letterbox crop, scale and layout only. Detail crops follow corresponding elements; full panels share 844x390 scale.','regions':[{'name':title,'logical_rects_reference_old_new':rects} for title,rects in regions],'states':'Actual isolated level 1 and level 16 game states. Review level 16 allocation leaves five points; no user save edits.','user_art_acceptance':'pending','captures':captures},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared skill-page comparisons and five-family runtime views.')
