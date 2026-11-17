"""Compare material opacity on the same paused native animation frames."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,os
import av,numpy as np
from PIL import Image,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-aura-v9'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
BEFORE=CACHE/'opacity-before/WAR_01';AFTER=CACHE/'final/design/WAR_01'
FONT=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
def font(size,bold=False):return ImageFont.truetype(str(FONT/('msyhbd.ttc' if bold else 'msyh.ttc')),size)
def text(d,xy,s,size=23,fill='#e2e8ed',bold=False,anchor='lm'):d.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor)
def frame(index):
 out=Image.new('RGB',(1440,712),'#171d22');d=ImageDraw.Draw(out)
 text(d,(22,27),'剑气透明状态 · 目标局部同帧对照',28,bold=True)
 text(d,(1418,27),'0.5× 动作细节',19,'#adbfca',anchor='rm')
 text(d,(22,73),'较实的波前（对照）',24,'#c4cbd0',True)
 text(d,(742,73),'半透明剑气（更新）',24,'#cadfeb',True)
 for col,folder in enumerate([BEFORE,AFTER]):
  with Image.open(folder/f'{index:03d}.jpg') as im:out.paste(im.convert('RGB').crop((400,40,730,295)).resize((704,540),Image.Resampling.LANCZOS),(8+720*col,104))
 text(d,(22,679),'波前、波身和尾流都保留透明混合，人物与地面可以透出。',22)
 return out
for index in range(72):assert (BEFORE/f'{index:03d}.jpg').exists() and (AFTER/f'{index:03d}.jpg').exists()
for index in [14,18,22]:
 before=np.asarray(Image.open(BEFORE/f'{index:03d}.jpg').convert('RGB'));after=np.asarray(Image.open(AFTER/f'{index:03d}.jpg').convert('RGB'))
 assert np.array_equal(before[:,:210],after[:,:210]),'Background changed'
 assert np.any(before[:,250:750]!=after[:,250:750]),'Opacity did not affect energy'
frame(18).save(OUT/'transparency-comparison.jpg',quality=96,subsampling=0)
frames=[frame(i).resize((1008,498),Image.Resampling.LANCZOS) for i in range(72)]
duration=[(round((i+1)*100/15)-round(i*100/15))*10 for i in range(72)]
frames=frames[18:]+frames[:18];duration=duration[18:]+duration[:18]
sample=Image.new('RGB',(504,249*3))
for row,index in enumerate([0,24,48]):sample.paste(frames[index].resize((504,249)),(0,row*249))
palette=sample.quantize(255,method=Image.Quantize.MEDIANCUT)
indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
indexed[0].save(OUT/'transparency-comparison.gif',save_all=True,append_images=indexed[1:],duration=duration,loop=0,optimize=True,transparency=255,disposal=1)
im=Image.open(OUT/'transparency-comparison.gif');milliseconds=0
for i in range(im.n_frames):im.seek(i);im.load();milliseconds+=im.info.get('duration',0)
assert milliseconds==4800
report={'method':'Same animation frame; change only the wave material opacity uniform, render at dt=0, then restore semi-transparent material.',
 'comparison':[{'waveOpacity':1,'label':'denser reference'},{'waveOpacity':.55,'label':'semi-transparent update'}],
 'backgroundMatch':True,'milliseconds':milliseconds,'frames':im.n_frames}
(BASE/'opacity-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
