"""Show the user's traced silhouette and a registration overlay on the red drawing."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
base=Path(__file__).resolve().parent
p=json.loads((base/'swoosh-profile.json').read_text())
outer=p['outerSamples'];inner=p['innerSamples']
im=Image.new('RGB',(1120,780),'#171d22');d=ImageDraw.Draw(im)
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
project=lambda q:(round(110+q[1]*155),round(650-(q[0]+p['planeLift'])*125))
poly=[project(q) for q in outer]+[project(q) for q in reversed(inner)]
d.text((30,20),'按红线重绘 · 三道共用同一月牙',font=font(30),fill='#e2e7eb')
d.text((30,66),'同形、同高度、同大小；只按释放时间向前错开位置',font=font(23),fill='#adb9c2')
d.polygon(poly,fill='#c4d2dd');d.line(poly+[poly[0]],fill='#edf2f6',width=2)
d.line((70,650,1050,650),fill='#57625b',width=3)
d.text((30,674),'低起始段',font=font(23),fill='#d4a56b')
d.text((680,674),'三道尖端高度一致',font=font(23),fill='#d4a56b')
d.line((700,735,1030,735),fill='#d4a56b',width=4)
d.polygon([(1030,735),(1013,726),(1013,744)],fill='#d4a56b')
d.text((400,715),'先后向前飞行',font=font(24),fill='#d4a56b')
im.save(base/'shape-direction.png')
ref=Image.open(base/'reference-red-outline.png').convert('RGB');dr=ImageDraw.Draw(ref)
def source_point(q):return (round(1268+q[1]*225-1240),round(1345-q[0]*210-550))
for curve in [outer,inner]:dr.line([source_point(q) for q in curve],fill='#67e1df',width=3)
ref.save(base/'reference-trace-overlay.png')
