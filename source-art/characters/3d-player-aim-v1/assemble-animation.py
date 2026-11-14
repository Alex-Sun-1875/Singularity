"""Deterministic crop/scale/caption of actual Cocos captures, no generated art."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

base=Path(__file__).resolve().parent/'runtime'
source=base/'animation'
record=json.loads((source/'frames.json').read_text())
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
frames=[]
for row in record['rows']:
    picture=Image.open(source/row['file']).convert('RGB').resize((640,593),Image.Resampling.LANCZOS)
    frame=Image.new('RGB',(640,657),'#171717')
    frame.paste(picture,(0,64))
    draw=ImageDraw.Draw(frame)
    title='360° 连续转身' if row['section']=='turn' else '斜向拉弓 → 放箭 · 慢放'
    subtitle='现有3D模型 · 游戏内实际渲染' if row['section']=='turn' else ('右上方 45°' if row['screenDegrees']==45 else '左下方 225°')
    draw.text((16,8),title,font=font,fill='#ead7aa')
    draw.text((16,36),subtitle,font=small,fill='#bbb8b2')
    frames.append(frame)
# A single palette keeps the stationary background stable across GIF frames.
samples=[frames[i] for i in range(0,len(frames),max(1,len(frames)//18))]
sheet=Image.new('RGB',(640*len(samples),657))
for i,frame in enumerate(samples):sheet.paste(frame,(i*640,0))
palette=sheet.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
indexed=[frame.quantize(palette=palette,dither=Image.Dither.NONE) for frame in frames]
target=base/'player-3d-turn-and-shoot.gif'
indexed[0].save(target,save_all=True,append_images=indexed[1:],duration=50,loop=0,optimize=True,disposal=1)
poster=Image.new('RGB',(640*3,657))
for i,n in enumerate([37,73+20,73+30+2]):poster.paste(frames[n],(640*i,0))
poster.resize((1440,493),Image.Resampling.LANCZOS).save(base/'animation-contact.jpg',quality=93)
with Image.open(target) as animation:
    print(json.dumps({'file':str(target),'frames':animation.n_frames,'durationSeconds':sum(animation.seek(i) or animation.info['duration']/1000 for i in range(animation.n_frames)),'bytes':target.stat().st_size}))
