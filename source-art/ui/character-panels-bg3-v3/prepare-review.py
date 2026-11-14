"""Compare approved design, previous runtime and current runtime at one scale."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont,ImageChops,ImageStat
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
CAPTURES=PROJECT/'src/cocos/test-results/ui-alignment-v3'
BASELINE=PROJECT/'src/cocos/temp/ui-alignment-v3-baseline'
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
labels=[('character-preview','人物','../character-panels-bg3-v1/screens/01-character.png'),('equipment','装备','../character-panels-bg3-v1/screens/02-equipment.png'),('skills','技能','../character-panels-bg3-v1/screens/03-skills.png'),('forge-preview','强化','../character-panels-bg3-v2/screens/01-preview.png')]
board=Image.new('RGB',(1688,848),'#15100b');records=[]
for index,(name,title,reference) in enumerate(labels):
    current=CAPTURES/('mobile-'+name+'.png')
    im=Image.open(current).convert('RGB').resize((844,390),Image.Resampling.LANCZOS)
    x,y=index%2*844,index//2*424
    ImageDraw.Draw(board).text((x+14,y+5),title+' · 本轮游戏运行截图',font=FONT,fill='#d6bd85');board.paste(im,(x,y+34))
    compare=Image.new('RGB',(844,1272),'#15100b')
    for row,(path,label) in enumerate([(ROOT/reference,'确认的设计稿'),(BASELINE/('mobile-'+name+'.png'),'上一轮运行画面'),(current,'此次对齐后的运行画面')]):
        ImageDraw.Draw(compare).text((14,row*424+5),label,font=FONT,fill='#d6bd85')
        compare.paste(Image.open(path).convert('RGB').resize((844,390),Image.Resampling.LANCZOS),(0,row*424+34))
    compare.save(ROOT/'review'/(name+'-comparison.jpg'),quality=96)
    reference_image=Image.open(ROOT/reference).convert('RGBA').resize((844,390),Image.Resampling.LANCZOS)
    Image.blend(reference_image,im.convert('RGBA'),.5).save(ROOT/'review'/(name+'-overlay.png'))
    records.append({'screen':name,'file':current.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(current.read_bytes()).hexdigest()})
board.save(ROOT/'review/runtime-panels-v3.jpg',quality=96)
(ROOT/'runtime-review.json').write_text(json.dumps({'method':'Same-scale source/previous/current contact sheets; 50% overlays expose positional differences. Runtime images are unretouched Cocos captures.','viewport':[844,390],'user_art_acceptance':'pending','platform_acceptance':'TapTap real device pending','captures':records},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Prepared four measured comparisons, overlays and current runtime overview.')
