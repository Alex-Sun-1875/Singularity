from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
BASE=Path(__file__).resolve().parent;OUT=BASE/'runtime'
old=BASE.parent/'3d-locomotion-v4/runtime/after-motion';new=OUT/'after-motion'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
frames=[]
for i in range(60):
 im=Image.new('RGB',(640,520),'#20272a');d=ImageDraw.Draw(im)
 for col,(folder,label)in enumerate([(old,'调整前'),(new,'新 3D 跑姿')]):
  d.text((col*320+14,10),label,font=font,fill='#e3d6bd');im.paste(Image.open(folder/f'run-90-{i:03d}.png').convert('RGB'),(col*320,40))
 frames.append(im)
palette=Image.new('RGB',(3840,520))
for i in range(6):palette.paste(frames[i*10],(i*640,0))
palette=palette.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE)for f in frames]
indexed[0].save(OUT/'upright-run-before-after.gif',save_all=True,append_images=indexed[1:],duration=[30,30,40]*20,loop=0,optimize=True,disposal=1)
sheet=Image.new('RGB',(1280,1040),'#20272a')
for i in range(4):
 f=frames[i*5];sheet.paste(f.crop((0,0,320,520)),(i*320,0));sheet.paste(f.crop((320,0,640,520)),(i*320,520))
sheet.save(OUT/'upright-run-contact.jpg',quality=94)
print('BODY_SWAY_COMPARISON_SAVED')
