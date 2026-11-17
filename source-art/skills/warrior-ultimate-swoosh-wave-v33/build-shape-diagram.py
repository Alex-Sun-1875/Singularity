"""Draw a direction diagram from the same cubic curves as the native VFX mesh."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

base=Path(__file__).resolve().parent
profile=json.loads((base/'swoosh-profile.json').read_text())
def smooth(x):
 q=max(0,min(1,x));return q*q*(3-2*q)
def edge(u,inner):
 split=profile['split'];t=u/split if u<=split else (u-split)/(1-split)
 points=profile['inner' if inner else 'outer'][0 if u<=split else 1]
 q=[(1-t)**3*points[0][j]+3*(1-t)**2*t*points[1][j]+3*(1-t)*t*t*points[2][j]+t**3*points[3][j] for j in (0,1)]
 q[0]*=profile['lateralScale'];q[1]+=profile['headForwardOffset']*smooth(u/.65)
 return q
outer=[edge(i/300,False) for i in range(301)]
inner=[]
for i in range(301):
 u=i/300;a=outer[i];b=edge(u,True);gate=.35+.65*smooth((u-.30)/.35)
 inner.append([a[j]+(b[j]-a[j])*gate for j in (0,1)])
im=Image.new('RGB',(1120,650),'#171d22');draw=ImageDraw.Draw(im)
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
project=lambda q:(int(150+(q[1]+2.8)*138),int(355-q[0]*100))
draw.text((30,20),'新版刀气轮廓 · 俯视朝向示意',font=font(30),fill='#e2e7eb')
draw.text((30,64),'实际曲线参数；此图只说明轮廓，动态中使用流动气浪材质',font=font(20),fill='#9daab5')
polygon=[project(q) for q in outer]+[project(q) for q in inner[::-1]]
draw.polygon(polygon,fill='#c4d2dd');draw.line(polygon+[polygon[0]],fill='#ecf2f6',width=2)
tail=project(outer[0]);draw.ellipse((tail[0]-5,tail[1]-5,tail[0]+5,tail[1]+5),fill='#d4a56b')
draw.text((45,420),'身体端 · 尖细长尾',font=font(23),fill='#d4a56b')
draw.line((150,410,tail[0],tail[1]+14),fill='#d4a56b',width=2)
draw.text((690,460),'前端 · 加宽勾腹 / 短尖刀头',font=font(23),fill='#d4a56b')
draw.line((650,535,1000,535),fill='#d4a56b',width=5)
draw.polygon([(1000,535),(982,524),(982,546)],fill='#d4a56b')
draw.text((720,565),'沿地面向前冲出',font=font(24),fill='#d4a56b')
im.save(base/'shape-direction.png')
