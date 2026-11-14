"""Deterministic layout of actual Cocos body/ground captures."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent;OUT=BASE/'runtime';OLD=BASE.parent/'3d-locomotion-v8/runtime'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
def gif(frames,name):
 palette=Image.new('RGB',(1152*6,410))
 for i in range(6):palette.paste(frames[i*10],(i*1152,0))
 palette=palette.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
 indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE)for f in frames]
 indexed[0].save(OUT/name,save_all=True,append_images=indexed[1:],duration=[30,30,40]*20,loop=0,optimize=True,disposal=1)
for angle,label in [(90,'side'),(180,'back')]:
 frames=[]
 for i in range(60):
  im=Image.new('RGB',(1152,410),'#20272a');d=ImageDraw.Draw(im)
  for j,(folder,clip,text)in enumerate([(OLD,'walk','步行 · 调整前'),(OUT,'walk','步行 · 本版'),(OLD,'run','跑步 · 调整前'),(OUT,'run','跑步 · 本版')]):
   d.text((j*288+12,10),text,font=font,fill='#e3d6bd')
   part=Image.open(folder/'after-motion'/f'{clip}-{angle}-{i:03d}.png').convert('RGB').resize((288,360))
   im.paste(part,(j*288,50))
  frames.append(im)
 gif(frames,f'body-{label}-comparison.gif')
 frames[5].save(OUT/f'body-{label}-comparison.jpg',quality=93)
frames=[]
for i in range(60):
 im=Image.new('RGB',(1152,410),'#20272a');d=ImageDraw.Draw(im)
 for j,(clip,angle,text)in enumerate([('walk',90,'步行 · 侧面'),('walk',180,'步行 · 背面'),('run',90,'跑步 · 侧面'),('run',180,'跑步 · 背面')]):
  d.text((j*288+12,10),text,font=font,fill='#e3d6bd')
  im.paste(Image.open(OUT/'after-ground'/f'{clip}-{angle}-{i:03d}.png').convert('RGB').resize((288,360)),(j*288,50))
 frames.append(im)
gif(frames,'responsive-walk-run.gif');frames[5].save(OUT/'responsive-walk-run.jpg',quality=93)
(OUT/'body-preview-review.json').write_text(json.dumps({'source':'Actual native Cocos actor, normal speed; deterministic layout only','fps':30,'durationMilliseconds':2000,'walkSpeedMetresPerSecond':1.6,'runSpeedMetresPerSecond':5.2,'referenceRevision':'locomotion-v8','currentRevision':'locomotion-v9','movingGroundCaptures':240,'userApproved':False},indent=2)+'\n',encoding='utf-8')
print('RESPONSIVE_BODY_PREVIEWS_SAVED')
