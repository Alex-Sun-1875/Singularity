"""Only actual Cocos frames, with deterministic crop/scale/layout."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
BASE=Path(__file__).resolve().parent;OUT=BASE/'runtime';phase=OUT/'after'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',27);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21)
canvas=Image.new('RGB',(1440,548),(39,46,50));draw=ImageDraw.Draw(canvas)
draw.text((22,12),'2D 设计卷发重建 · Cocos 实际渲染',font=font,fill='#ede3d5')
for i,(angle,label)in enumerate([(0,'正面'),(35,'斜侧面'),(90,'侧面'),(180,'背面')]):
 pic=Image.open(phase/f'head-{angle}.png').convert('RGB').crop((200,80,824,860)).resize((360,450),Image.Resampling.LANCZOS)
 canvas.paste(pic,(i*360,90));draw.text((i*360+20,57),label,font=small,fill='#c4d6d0')
canvas.save(OUT/'silver-curls-views.jpg',quality=95)
frames=[]
for angle in range(0,360,45):
 pic=Image.open(phase/f'body-{angle}.png').convert('RGB');frame=Image.new('RGB',(512,810),(39,46,50));frame.paste(pic,(0,42));ImageDraw.Draw(frame).text((15,8),'新卷发 · 实际八方向视图',font=small,fill='#ede3d5');frames.append(frame)
frames[0].save(OUT/'silver-curls-turntable.gif',save_all=True,append_images=frames[1:],duration=220,loop=0,optimize=True)
if (phase/'frames.json').exists():
 sequence=[]
 for i in range(60):
  frame=Image.new('RGB',(640,425),(39,46,50));d=ImageDraw.Draw(frame)
  for col,(scenario,label)in enumerate([('run','跑步'),('bow','拉弓与射箭')]):
   pic=Image.open(phase/f'{scenario}-{i:03}.jpg').convert('RGB').resize((320,384),Image.Resampling.LANCZOS);frame.paste(pic,(col*320,41));d.text((col*320+12,8),label,font=small,fill='#ede3d5')
  sequence.append(frame)
 sequence[0].save(OUT/'silver-curls-actions.gif',save_all=True,append_images=sequence[1:],duration=[30,30,40]*20,loop=0,optimize=True)
(OUT/'previews.json').write_text(json.dumps({'source':'Actual Cocos model/materials; deterministic crop, scale and layout only','views':'silver-curls-views.jpg','turntable':'silver-curls-turntable.gif','actions':'silver-curls-actions.gif'},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Assembled actual Cocos silver curl previews',flush=True)
