"""Side-elevation diagram of the actual upright hook profile and terrain anchor."""
from pathlib import Path
import json, math
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
im=Image.new('RGB',(1120,690),'#171d22');draw=ImageDraw.Draw(im)
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
belly=max(q[0] for q in outer)
def project(q,u):
 height=((belly-q[0])*profile['verticalScale']-belly*profile['verticalScale']*(1-smooth(u/profile['heightEnvelope']['tailEaseLength']))+profile['heightEnvelope']['arcLift']*math.sin(math.pi*u)**2)+profile['planeLift']
 return (int(150+(q[1]+2.8)*138),int(560-height*140))
draw.text((30,20),'恢复弧度 · 尾尖低起，刀腹自然上弯',font=font(30),fill='#e2e7eb')
draw.text((30,64),'侧视轮廓示意；完整弧线随刀气一起向前飞行',font=font(22),fill='#9daab5')
polygon=[project(q,i/300) for i,q in enumerate(outer)]+[project(q,i/300) for i,q in reversed(list(enumerate(inner)))]
draw.polygon(polygon,fill='#c4d2dd');draw.line(polygon+[polygon[0]],fill='#ecf2f6',width=2)
tail=project(outer[0],0);tip=project(outer[-1],1)
draw.ellipse((tail[0]-5,tail[1]-5,tail[0]+5,tail[1]+5),fill='#d4a56b')
draw.text((35,tail[1]-54),'尾尖从脚边起',font=font(24),fill='#d4a56b')
draw.text((740,115),'短尖向上',font=font(26),fill='#d4a56b')
draw.line((tip[0],tip[1]-12,tip[0],120),fill='#d4a56b',width=3)
draw.polygon([(tip[0],120),(tip[0]-7,132),(tip[0]+7,132)],fill='#d4a56b')
draw.line((80,560,1050,560),fill='#57625b',width=4)
draw.text((650,577),'刀腹保留自然弧度',font=font(24),fill='#d4a56b')
draw.line((780,635,1030,635),fill='#d4a56b',width=4)
draw.polygon([(1030,635),(1013,626),(1013,644)],fill='#d4a56b')
draw.text((430,616),'整体向前推进',font=font(24),fill='#d4a56b')
im.save(base/'shape-direction.png')
