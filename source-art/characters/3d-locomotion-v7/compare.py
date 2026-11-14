from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
BASE=Path(__file__).resolve().parent;OUT=BASE/'runtime';OLD=BASE.parent/'3d-locomotion-v6/runtime';font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
frames=[]
for i in range(60):
 im=Image.new('RGB',(640,520),'#20272a');d=ImageDraw.Draw(im)
 for col,(p,label)in enumerate([(OLD,'上一版 · 半速'),(OUT,'前倾跑姿 · 半速')]):
  d.text((col*320+14,10),label,font=font,fill='#e3d6bd');im.paste(Image.open(p/'after-motion'/f'run-90-{i:03d}.png').convert('RGB'),(col*320,40))
 frames.append(im)
frames=frames[20:]+frames[:20]
palette=Image.new('RGB',(3840,520))
for i in range(6):palette.paste(frames[i*10],(i*640,0))
palette=palette.quantize(colors=256,method=Image.Quantize.MEDIANCUT);indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE)for f in frames]
indexed[0].save(OUT/'lean-run-comparison-slow.gif',save_all=True,append_images=indexed[1:],duration=[70,60,70]*20,loop=0,optimize=True,disposal=1)
im=Image.new('RGB',(1280,1040),'#20272a');d=ImageDraw.Draw(im)
for row,(p,label)in enumerate([(OLD,'上一版'),(OUT,'前倾跑姿')]):
 for col,f in enumerate([.125,.25,.625,.75]):
  d.text((col*320+12,row*520+10),label+f' / {f:g}',font=font,fill='#e3d6bd');im.paste(Image.open(p/'after'/f'W07-run-{f}-90.png').convert('RGB'),(col*320,row*520+40))
im.save(OUT/'lean-run-keyframes.jpg',quality=94)
print('KNEE_LIFT_REVIEW_SAVED')
