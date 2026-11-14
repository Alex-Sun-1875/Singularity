from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent;OUT=BASE/'runtime';font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',27);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21)
styles=[('curly','银白卷发'),('dante','但丁'),('nero','尼禄'),('vergil','维吉尔')]
canvas=Image.new('RGB',(1440,560),(39,46,50));draw=ImageDraw.Draw(canvas);draw.text((20,12),'四款发型 · 游戏内实际渲染',font=font,fill='#ede3d5')
for i,(style,label)in enumerate(styles):
 draw.text((i*360+18,57),label,font=small,fill='#c9d8d2');pic=Image.open(OUT/'after'/style/'head-35.png').convert('RGB').crop((200,80,824,860)).resize((360,450),Image.Resampling.LANCZOS);canvas.paste(pic,(i*360,100))
canvas.save(OUT/'hairstyles-comparison.jpg',quality=95)
comparison=Image.new('RGB',(1440,1080),(39,46,50));d=ImageDraw.Draw(comparison);d.text((20,10),'相同镜头 · 上：收窄前 / 下：本次',font=font,fill='#ede3d5')
for row,phase in enumerate(['width-before','after']):
 for i,(style,label)in enumerate(styles):
  y=50+row*510;d.text((i*360+18,y),label,font=small,fill='#c9d8d2');pic=Image.open(OUT/phase/style/'head-35.png').convert('RGB').crop((200,80,824,860)).resize((360,450),Image.Resampling.LANCZOS);comparison.paste(pic,(i*360,y+38))
comparison.save(OUT/'hairstyles-width-comparison.jpg',quality=95)
frames=[]
for angle in range(0,360,45):
 frame=Image.new('RGB',(960,340),(39,46,50));d=ImageDraw.Draw(frame)
 for i,(style,label)in enumerate(styles):
  pic=Image.open(OUT/'after'/style/f'head-{angle}.png').convert('RGB').crop((200,80,824,860)).resize((240,300),Image.Resampling.LANCZOS);frame.paste(pic,(i*240,40));d.text((i*240+12,8),label,font=small,fill='#ede3d5')
 frames.append(frame)
frames[0].save(OUT/'hairstyles-eight-views.gif',save_all=True,append_images=frames[1:],duration=220,loop=0,optimize=True)
print('Assembled actual four-style comparison and eight-direction preview',flush=True)
