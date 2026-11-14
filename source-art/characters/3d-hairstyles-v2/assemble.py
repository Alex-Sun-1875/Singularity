from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent;OUT=BASE/'runtime';phase='redesigned';font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',27);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21)
styles=[('curly','银白卷发'),('dante','但丁'),('nero','尼禄'),('vergil','维吉尔')]
def portrait(folder,angle,size=(360,450)):
 return Image.open(folder/f'head-{angle}.png').convert('RGB').crop((200,80,824,860)).resize(size,Image.Resampling.LANCZOS)
sheet=Image.new('RGB',(1440,1080),(39,46,50));d=ImageDraw.Draw(sheet);d.text((20,12),'游戏内实际渲染 · 正侧面对照',font=font,fill='#ede3d5')
for row,angle in enumerate([35,90]):
 for col,(sid,label)in enumerate(styles):
  y=52+row*510;d.text((col*360+18,y),label+(' · 正侧'if row==0 else' · 侧面'),font=small,fill='#c9d8d2');sheet.paste(portrait(OUT/phase/sid,angle),(col*360,y+38))
sheet.save(OUT/'hairstyles-redesigned.jpg',quality=95)
full=Image.new('RGB',(1440,1590),(39,46,50));d=ImageDraw.Draw(full);d.text((20,12),'游戏内实际渲染 · 额前 / 耳侧 / 后颈',font=font,fill='#ede3d5')
for row,angle in enumerate([35,90,180]):
 for col,(sid,label)in enumerate(styles):
  y=52+row*510;d.text((col*360+18,y),label+(' · 正侧',' · 侧面',' · 背面')[row],font=small,fill='#c9d8d2');full.paste(portrait(OUT/phase/sid,angle),(col*360,y+38))
full.save(OUT/'hairstyles-all-views.jpg',quality=95)
back=Image.new('RGB',(1440,560),(39,46,50));d=ImageDraw.Draw(back);d.text((20,12),'游戏内实际渲染 · 后颈收尾',font=font,fill='#ede3d5')
for col,(sid,label)in enumerate(styles):
 d.text((col*360+18,57),label,font=small,fill='#c9d8d2');back.paste(portrait(OUT/phase/sid,180),(col*360,95))
back.save(OUT/'hairstyles-back.jpg',quality=95)
compare=Image.new('RGB',(1440,1080),(39,46,50));d=ImageDraw.Draw(compare);d.text((20,12),'相同镜头 · 上：上一版 / 下：本次',font=font,fill='#ede3d5')
for row in range(2):
 for col,(sid,label)in enumerate(styles):
  folder=BASE.parent/'3d-hairstyles-v1/runtime/after'/sid if row==0 else OUT/phase/sid;y=52+row*510;d.text((col*360+18,y),label,font=small,fill='#c9d8d2');compare.paste(portrait(folder,35),(col*360,y+38))
compare.save(OUT/'hairstyles-before-after.jpg',quality=95)
frames=[]
for angle in range(0,360,45):
 frame=Image.new('RGB',(1120,390),(39,46,50));d=ImageDraw.Draw(frame)
 for i,(sid,label)in enumerate(styles):
  frame.paste(portrait(OUT/phase/sid,angle,(280,350)),(i*280,40));d.text((i*280+12,8),label,font=small,fill='#ede3d5')
 frames.append(frame)
frames[0].save(OUT/'hairstyles-turntable.gif',save_all=True,append_images=frames[1:],duration=360,loop=0,optimize=True)
print('Assembled actual in-engine head views')
