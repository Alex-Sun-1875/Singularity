"""Compose only actual Cocos renders for the original-model comparison."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,io,subprocess
BASE=Path(__file__).resolve().parent;OUT=BASE/'runtime';font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
canvas=Image.new('RGB',(1280,840),(38,45,49));d=ImageDraw.Draw(canvas);d.text((18,12),'原模型细化 · 游戏实际渲染',font=font,fill='#e5d8bc');d.text((18,44),'原脸型与五官保留，肤色轻调、原发型波浪细修，服装新增织纹与金绣',font=small,fill='#bfc4c3')
for i,(phase,angle,label)in enumerate([('before',0,'原版'),('after',0,'本次 · 正面'),('after',90,'本次 · 侧面'),('after',180,'本次 · 背面')]):
    x=i*320;d.text((x+12,78),label,font=font,fill='#d5c7ad'if i==0 else'#a8d8cd');im=Image.open(OUT/phase/f'body-{angle}.png').convert('RGB').resize((320,480),Image.Resampling.LANCZOS);canvas.paste(im,(x,116))
for i,phase in enumerate(['before','after']):
    im=Image.open(OUT/phase/'head-35.png').convert('RGB').crop((70,80,480,470));im.thumbnail((270,216),Image.Resampling.LANCZOS);canvas.paste(im,(350+i*295,624));d.text((350+i*295,600),'原版近景'if i==0 else'本次近景',font=small,fill='#cfc6b4')
d.text((18,645),'原脸型、五官保留',font=font,fill='#cfc6b4');d.text((18,681),'肤色与原发型细修',font=small,fill='#b7c4c1')
canvas.save(OUT/'appearance-comparison.jpg',quality=96)
turn=[]
for angle in range(0,360,45):
    image=Image.open(OUT/'after'/f'body-{angle}.png').convert('RGB');header=Image.new('RGB',(512,812),(38,45,49));header.paste(image,(0,44));ImageDraw.Draw(header).text((12,10),'本次外观 · 实际八方向视图',font=font,fill='#d5cab4');turn.append(header)
palette=Image.new('RGB',(512*8,812))
for i,f in enumerate(turn):palette.paste(f,(i*512,0))
palette=palette.quantize(colors=256,method=Image.Quantize.MEDIANCUT);frames=[f.quantize(palette=palette,dither=Image.Dither.NONE)for f in turn];frames[0].save(OUT/'appearance-turntable.gif',save_all=True,append_images=frames[1:],loop=0,duration=220,optimize=True)
report={'comparison':'appearance-comparison.jpg','turntable':'appearance-turntable.gif','turntableSamples':8,'source':'Actual native Cocos actor, same pose/camera/light; deterministic crop/scale/layout only','cloudTexture':'../cloth-cloud.png','prompt':'../generation-prompt.txt'}
(OUT/'previews.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('Assembled actual runtime appearance comparison')
