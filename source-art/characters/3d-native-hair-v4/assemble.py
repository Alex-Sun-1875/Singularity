"""Present actual Cocos captures; do not use generated portrait mockups."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
BASE=Path(__file__).resolve().parent;OUT=BASE/'runtime'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',26);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
canvas=Image.new('RGB',(1400,1110),(37,44,48));d=ImageDraw.Draw(canvas)
d.text((24,16),'原生短发细化 · Cocos 实际渲染',font=font,fill='#e4dac6')
d.text((24,58),'保留脸型与原生短发；细发丝、灰银暗部和柔和高光参考 2D 设计',font=small,fill='#c3ccc9')
for i,(phase,label)in enumerate([('before','原先'),('after','本次')]):
    x=20+i*700;d.text((x+12,100),label,font=font,fill='#b9dfd3'if i else'#cfc7ba')
    pic=Image.open(OUT/phase/'head-35.png').convert('RGB').crop((200,135,920,855)).resize((660,660),Image.Resampling.LANCZOS)
    canvas.paste(pic,(x+10,140))
for i,(file,label)in enumerate([('head-0.png','正面发际线'),('head-90.png','侧面发束'),('head-180.png','背面与发根')]):
    x=20+i*460;pic=Image.open(OUT/'after'/file).convert('RGB').crop((230,155,790,515));pic.thumbnail((440,276),Image.Resampling.LANCZOS)
    canvas.paste(pic,(x+(440-pic.width)//2,828));d.text((x+10,804),label,font=small,fill='#c3ccc9')
canvas.save(OUT/'native-hair-comparison.jpg',quality=95)
frames=[]
for angle in range(0,360,45):
    pic=Image.open(OUT/'after'/f'body-{angle}.png').convert('RGB');frame=Image.new('RGB',(512,810),(37,44,48));frame.paste(pic,(0,42));ImageDraw.Draw(frame).text((15,8),'原生短发 · 实际八方向视图',font=small,fill='#e4dac6');frames.append(frame)
frames[0].save(OUT/'native-hair-turntable.gif',save_all=True,append_images=frames[1:],duration=220,loop=0,optimize=True)
if (OUT/'after/frames.json').exists():
    sequence=[]
    for i in range(60):
        frame=Image.new('RGB',(640,425),(37,44,48));draw=ImageDraw.Draw(frame)
        for col,(scenario,label)in enumerate([('run','跑步'),('bow','拉弓与射箭')]):
            pic=Image.open(OUT/'after'/f'{scenario}-{i:03}.jpg').convert('RGB').resize((320,384),Image.Resampling.LANCZOS);frame.paste(pic,(col*320,41));draw.text((col*320+10,8),label,font=small,fill='#e4dac6')
        sequence.append(frame)
    sequence[0].save(OUT/'native-hair-actions.gif',save_all=True,append_images=sequence[1:],duration=[30,30,40]*20,loop=0,optimize=True)
(OUT/'previews.json').write_text(json.dumps({'source':'Actual Cocos actor; same pose, camera and lighting; deterministic crop/scale/layout only','comparison':'native-hair-comparison.jpg','turntable':'native-hair-turntable.gif','actions':'native-hair-actions.gif'},indent=2)+'\n',encoding='utf-8')
print('Assembled native hair runtime previews')
