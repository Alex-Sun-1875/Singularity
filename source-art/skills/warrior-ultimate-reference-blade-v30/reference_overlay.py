"""Check traced cubic contours against the supplied crop; deterministic layout only."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
PROFILE=json.loads((BASE/'shape-profile.json').read_text(encoding='utf8'))
def cubic(points,t):
    s=1-t
    return [s*s*s*points[0][i]+3*s*s*t*points[1][i]+3*s*t*t*points[2][i]+t*t*t*points[3][i] for i in range(2)]
def trace(name):
    values=[]
    for section in PROFILE[name]:
        values.extend(cubic(section['points'],i/80) for i in range(81))
    return values
def upright(p):
    b=PROFILE['basis'];dx=p[0]-b['origin'][0];dy=p[1]-b['origin'][1];scale=b['height']/b['axisLength']
    return ((dx*b['forward'][0]+dy*b['forward'][1])*scale+b['forwardShift'],
            b['height']-(dx*b['along'][0]+dy*b['along'][1]-b['startAlong'])*scale)
def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if bold else 'msyh.ttc'),size)
def label(draw,xy,text,size=22,fill='#dce5ec',bold=False):
    draw.text(xy,text,font=font(size,bold),fill=fill)

def main():
    canvas=Image.new('RGB',(1400,940),'#171d22');d=ImageDraw.Draw(canvas)
    label(d,(22,14),'参考刀身轮廓校对 · 同一组曲线用于动态小样',30,bold=True)
    label(d,(22,61),'用户参考局部 + 手描轮廓叠线',23,bold=True)
    label(d,(692,61),'竖直波面 · 银色轮廓示意',23,bold=True)
    crop=Image.open(BASE/PROFILE['source']).convert('RGB')
    canvas.paste(crop,(22,108))
    edges=trace('cuttingEdge');back=trace('bladeBack')
    for points,color in [(edges,'#62d8e9'),(back,'#f4cd77')]:
        d.line([(22+x,108+y) for x,y in points],fill=color,width=3)
    norm=[upright(p) for p in edges+back[::-1]]
    xmin,xmax=min(p[0] for p in norm),max(p[0] for p in norm)
    ymin,ymax=min(p[1] for p in norm),max(p[1] for p in norm)
    scale=min(590/max(.001,xmax-xmin),742/max(.001,ymax-ymin))
    center=(xmin+xmax)/2
    def screen(p):return (1010+(p[0]-center)*scale,116+(ymax-p[1])*scale)
    d.polygon([screen(p) for p in norm],fill='#ced8df')
    d.line([screen(upright(p)) for p in edges],fill='#62d8e9',width=2)
    d.line([screen(upright(p)) for p in back],fill='#f4cd77',width=2)
    label(d,(692,864),'仅校对外形；不是最终气浪材质或动画帧',19,fill='#aab9c4')
    label(d,(22,897),'青线：内侧刃线     金线：外侧刀背     保持长窄刀身、下部宽腹和回弯刀尖',20)
    canvas.save(BASE/'reference-shape-check.jpg',quality=95,subsampling=0)
    print('Saved reference-shape-check.jpg')

if __name__=='__main__':main()
