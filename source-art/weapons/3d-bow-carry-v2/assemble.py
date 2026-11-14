from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
BASE=Path(__file__).resolve().parent;OUT=BASE/'runtime';after=OUT/'after';before=OUT/'calibration'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',25);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
board=Image.new('RGB',(640,1070),(39,46,50));d=ImageDraw.Draw(board);d.text((16,9),'弓与箭筒贴背 · 上：之前 / 下：本次',font=font,fill='#ede3d5')
for row in range(2):
 for col,angle in enumerate([90,180]):
  image=Image.open(before/f'before-{angle}.png'if row==0 else after/f'W07-stowed-{angle}.png').convert('RGB').resize((320,480),Image.Resampling.LANCZOS);y=45+row*510;d.text((col*320+8,y),{35:'正侧',90:'侧面',180:'背面'}[angle],font=small,fill='#c9d8d2');board.paste(image,(col*320,y+25))
board.save(OUT/'bow-carry-before-after.jpg',quality=95)
items=json.loads((BASE.parent/'3d-design-v1/designs.json').read_text(encoding='utf-8'));names={r['id']:r['name']for r in items};ids=['W07','W08','W09','W10','DU2-04','DE02','L02']
allbows=Image.new('RGB',(1960,940),(39,46,50));d=ImageDraw.Draw(allbows);d.text((16,8),'七把弓 · 实际背负位置',font=font,fill='#ede3d5')
for row in range(2):
 for col,id in enumerate(ids):
  angle=180 if row==0 else 270 if id in ['W08','DU2-04']else 90;y=44+row*448;d.text((col*280+7,y),id+' '+names[id],font=small,fill='#c9d8d2');image=Image.open(after/f'{id}-stowed-{angle}.png').convert('RGB').resize((280,420),Image.Resampling.LANCZOS);allbows.paste(image,(col*280,y+25))
allbows.save(OUT/'all-bows-back-carry.jpg',quality=94)
motion=Image.new('RGB',(1280,1000),(39,46,50));d=ImageDraw.Draw(motion)
for row,id in enumerate(['W07','W08']):
 angle=90 if id=='W07'else 270
 for col,label in enumerate(['walk-25','run-75','draw','returned']):
  a=135 if label in ['draw','returned']else angle;im=Image.open(after/f'{id}-{label}-{a}.png').convert('RGB').resize((320,480),Image.Resampling.LANCZOS);motion.paste(im,(col*320,row*500+20));d.text((col*320+6,row*500+2),id+' '+label,font=small,fill='#ede3d5')
motion.save(OUT/'carry-motion-check.jpg',quality=94)
print('Assembled actual carry alignment and movement views')
