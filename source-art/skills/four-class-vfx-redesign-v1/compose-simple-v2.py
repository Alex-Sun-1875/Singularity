"""Review-only monochrome, coarse pictogram range circles; never writes runtime assets."""
from pathlib import Path
import runpy, math
from PIL import Image, ImageDraw, ImageFont, ImageOps

OUT=Path(__file__).resolve().parent
previous=runpy.run_path(str(OUT/'compose-review.py'))
base=previous['base']
ROOT=previous['ROOT']
controls=previous['controls']
S=Image.Resampling.LANCZOS
FONT=r'C:\Windows\Fonts\msyh.ttc'
BOLD=r'C:\Windows\Fonts\msyhbd.ttc'
(OUT/'simple-v2').mkdir(exist_ok=True)

def bezier(a,b,c,d,steps=24):
    return [((1-t)**3*a[0]+3*(1-t)**2*t*b[0]+3*(1-t)*t*t*c[0]+t**3*d[0],(1-t)**3*a[1]+3*(1-t)**2*t*b[1]+3*(1-t)*t*t*c[1]+t**3*d[1]) for t in [i/steps for i in range(steps+1)]]

def glyph(kind):
    mask=Image.new('L',(400,400)); d=ImageDraw.Draw(mask)
    if kind=='fire':
        parts=[((50,6),(54,30),(27,34),(27,57)),((27,57),(27,78),(39,90),(55,90)),((55,90),(76,90),(88,74),(81,54)),((81,54),(77,43),(70,36),(67,29)),((67,29),(70,48),(58,55),(56,40)),((56,40),(55,27),(58,18),(50,6))]
        pts=[p for part in parts for p in bezier(*part)]
        d.line([(round(x*4),round(y*4)) for x,y in pts],fill=255,width=28,joint='curve')
    elif kind=='thunder':
        pts=[(60,8),(25,52),(48,52),(38,91),(80,40),(55,40),(60,8)]
        d.line([(x*4,y*4) for x,y in pts],fill=255,width=28,joint='curve')
    else:
        d.rounded_rectangle((52,134,238,266),radius=65,outline=255,width=28)
        d.rounded_rectangle((162,134,348,266),radius=65,outline=255,width=28)
        mask=mask.rotate(35,Image.Resampling.BICUBIC,expand=False)
    return mask.crop(mask.getbbox())

GLYPHS={k:glyph(k) for k in ['fire','thunder','trap']}

def circle(kind,opacity=1.0,invalid=False):
    im=Image.new('RGBA',(640,640)); d=ImageDraw.Draw(im)
    col=(236,236,236,round(220*opacity))
    if invalid:
        for box,w in [((20,20,620,620),8),((43,43,597,597),6)]:
            for start in range(0,360,60): d.arc(box,start+6,start+47,fill=col,width=w)
        d.line((272,272,368,368),fill=col,width=11)
        d.line((368,272,272,368),fill=col,width=11)
        return im
    d.ellipse((20,20,620,620),outline=col,width=8)
    d.ellipse((43,43,597,597),outline=col,width=6)
    centres=[(320,320)]+[(320+172*math.cos(math.radians(a)),320+172*math.sin(math.radians(a))) for a in [-90,-30,30,90,150,210]]
    for i,(cx,cy) in enumerate(centres):
        target=(74,100) if kind!='trap' else (103,75)
        if i==0: target=tuple(round(n*1.13) for n in target)
        m=ImageOps.contain(GLYPHS[kind],target,S).point(lambda p:round(p*.75*opacity))
        stamp=Image.new('RGBA',m.size,(236,236,236,0));stamp.putalpha(m)
        im.alpha_composite(stamp,(round(cx-m.width/2),round(cy-m.height/2)))
    return im

for kind in GLYPHS:
    circle(kind).save(OUT/f'simple-v2/{kind}-double-ring.png')

# Editable geometric source for the diagram; monochrome only.
paths={'fire':'M50 6 C54 30 27 34 27 57 C27 78 39 90 55 90 C76 90 88 74 81 54 C77 43 70 36 67 29 C70 48 58 55 56 40 C55 27 58 18 50 6 Z','thunder':'M60 8 L25 52 L48 52 L38 91 L80 40 L55 40 Z'}
for kind,path in paths.items():
    (OUT/f'simple-v2/{kind}-glyph.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="{path}" fill="none" stroke="#ececec" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"/></svg>\n',encoding='utf-8')

board=Image.new('RGB',(1600,1110),(30,30,30));d=ImageDraw.Draw(board)
def text(x,y,t,size=23,bold=False,fill=(219,219,219)):
    d.text((x,y),t,font=ImageFont.truetype(BOLD if bold else FONT,size),fill=fill)
text(40,24,'技能范围圈 · 简化稿 v2',39,True)
text(40,87,'双层圆环  /  粗线图例  /  单色示意  /  去掉细纹与发光',25)
items=[('fire','陨石 · 火焰图例'),('thunder','雷系 · 闪电图例'),('trap','陷阱 · 束缚图例')]
for i,(kind,label) in enumerate(items):
    x=32+i*520
    d.rounded_rectangle((x,149,x+496,704),radius=10,fill=(39,39,39),outline=(70,70,70),width=1)
    text(x+26,169,label,27,True)
    stamp=circle(kind).resize((465,465),S)
    board.paste(stamp,(x+16,219),stamp)
text(40,734,'状态只改变明暗与显隐，双圈尺寸保持一致',25,True)
states=[('瞄准',.65,False),('锁定',1.,False),('淡出',.22,False),('不可施放',1.,True)]
for i,(label,op,invalid) in enumerate(states):
    x=42+i*390
    stamp=circle('fire',op,invalid).resize((235,235),S)
    board.paste(stamp,(x,789),stamp)
    text(x+256,881,label,23,True)
text(40,1055,'玩家施法范围示意 · 无颜色方案 · 静态设计候选 · 尚未实现',22)
board.save(OUT/'02-patterns-and-states-v2.png')

def put_ground(canvas,opacity):
    stamp=circle('fire',opacity).resize((720,360),S)
    canvas.alpha_composite(stamp,(1290,155))
    protect=Image.new('L',canvas.size)
    ImageDraw.Draw(protect).polygon([(1645,32),(1705,23),(1724,80),(1710,104),(1741,135),(1745,187),(1773,223),(1749,242),(1706,216),(1679,225),(1634,219),(1632,204),(1658,180),(1639,135),(1628,119),(1645,89)],fill=255)
    canvas.paste(base,(0,0),protect)

aim=base.copy();put_ground(aim,.9)
aim.convert('RGB').save(OUT/'03a-player-meteor-aim-v2.png')
descent=base.copy();put_ground(descent,1.)
rotated=previous['rotated'];headx=previous['headx'];heady=previous['heady']
descent.alpha_composite(rotated,(round(1650-headx),round(335-heady)))
mask=previous['protect_hud'];descent.paste(base,(0,0),mask)
descent.convert('RGB').save(OUT/'03b-player-meteor-descent-v2.png')

ui=Image.new('RGB',(1600,1848),(30,30,30));du=ImageDraw.Draw(ui)
def ui_text(x,y,t,size=23,bold=False):du.text((x,y),t,font=ImageFont.truetype(BOLD if bold else FONT,size),fill=(225,225,225))
ui_text(42,24,'双层范围圈 · 横屏 UI 简化稿 v2',39,True)
ui_text(42,88,'双圈边界 + 粗线火焰图例｜单色示意｜保留现有七按钮布局',23)
ui_text(42,137,'A  施放前：双圈与重复图例标示范围',27,True)
ui_text(42,952,'B  陨石终极：图例保持简洁，攻击特效独立表现',27,True)
for im,y in [(aim,183),(descent,998)]:
    ui.paste(im.convert('RGB').resize((1516,700),S),(42,y))
    du.rectangle((41,y-1,1558,y+700),outline=(115,115,115),width=2)
ui_text(42,895,'两圈之间不加装饰；圈内只用少量粗图例，地面保持可见。',22)
ui_text(42,1712,'陨石仍拟移至右上终极位；范围圈不使用职业配色或复杂法阵。',22)
du.line((42,1771,1558,1771),fill=(100,100,100),width=1)
ui_text(42,1790,'实景截图的静态合成；原角色姿态保留，尚未接入游戏或进行动画验收。',20)
ui.save(OUT/'03-mobile-ui-proposal-v2.png')
print('Saved monochrome double-ring v2 diagram, sources and UI composites.')
