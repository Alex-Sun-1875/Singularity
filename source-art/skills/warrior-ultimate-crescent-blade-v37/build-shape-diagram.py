"""Draw the exact direct-authored crescent edges, before animated air shading."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
base=Path(__file__).resolve().parent
profile=json.loads((base/'swoosh-profile.json').read_text())
def edge(u,inner):
 p=profile['inner' if inner else 'outer'][0];s=1-u
 return [s*s*s*p[0][j]+3*s*s*u*p[1][j]+3*s*u*u*p[2][j]+u*u*u*p[3][j] for j in (0,1)]
im=Image.new('RGB',(1120,690),'#171d22');draw=ImageDraw.Draw(im)
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
def project(p):return (int(125+(p[1]+2.5)*150),int(560-(p[0]+profile['planeLift'])*140))
outer=[edge(i/300,False) for i in range(301)];inner=[edge(i/300,True) for i in range(301)]
polygon=[project(p) for p in outer]+[project(p) for p in reversed(inner)]
draw.text((30,20),'长刀式月牙 · 完整外弧与内凹弧',font=font(30),fill='#e2e7eb')
draw.text((30,64),'只有起始短段靠近脚边，后半段按刀身弧度自然悬起',font=font(22),fill='#9daab5')
draw.polygon(polygon,fill='#c4d2dd');draw.line(polygon+[polygon[0]],fill='#edf2f6',width=2)
low=project(outer[0]);draw.ellipse((low[0]-5,low[1]-5,low[0]+5,low[1]+5),fill='#d4a56b')
draw.text((35,low[1]-50),'起始短段低起',font=font(23),fill='#d4a56b')
draw.line((75,560,1050,560),fill='#57625b',width=3)
draw.text((640,580),'月牙刀身离地舒展',font=font(24),fill='#d4a56b')
draw.line((780,635,1030,635),fill='#d4a56b',width=4)
draw.polygon([(1030,635),(1013,626),(1013,644)],fill='#d4a56b')
draw.text((470,616),'整道刀气向前飞行',font=font(24),fill='#d4a56b')
im.save(base/'shape-direction.png')
