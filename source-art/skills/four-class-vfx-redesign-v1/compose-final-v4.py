"""Final review-only composition: old pale-gold palette, decorated double rings, coherent motifs."""
from pathlib import Path
from shutil import copy2
import runpy, math
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parent
RAW=Path(r'C:\Users\Alexa\.codex\generated_images\01a1e07a-ae0c-79f3-83e9-6d9363988a5b')
previous=runpy.run_path(str(OUT/'compose-review.py'))
base=previous['base']
S=Image.Resampling.LANCZOS
FONT=r'C:\Windows\Fonts\msyh.ttc'
BOLD=r'C:\Windows\Fonts\msyhbd.ttc'
copy2(RAW/'exec-c40e615d-bf6c-4d4e-bf04-89794b349c61.png',OUT/'02-patterns-and-states-v4.png')
copy2(RAW/'exec-799ef4f1-3485-4647-aa07-f99b694709f9.png',OUT/'01-four-class-direction-v4.png')
copy2(RAW/'exec-84dad5f0-d3be-4880-b230-5d0149cf393f.png',OUT/'raw/02-monochrome-coherent-v3.png')

copy2(RAW/'exec-ebd09e33-7ce3-4353-b6ff-133a882efc53.png',OUT/'raw/fire-double-ring-transparent-generated.png')
# Use the generated transparent derivative directly; no stone-texture color-key extraction.
pattern=Image.open(OUT/'raw/fire-double-ring-transparent-generated.png').convert('RGBA')
pattern.save(OUT/'derived/fire-double-ring-gold-v4-review-only.png')

def ground(canvas,opacity):
    stamp=pattern.resize((720,360),S)
    stamp.putalpha(stamp.getchannel('A').point(lambda a:round(a*opacity)))
    canvas.alpha_composite(stamp,(1290,155))
    protect=Image.new('L',canvas.size)
    ImageDraw.Draw(protect).polygon([(1645,32),(1705,23),(1724,80),(1710,104),(1741,135),(1745,187),(1773,223),(1749,242),(1706,216),(1679,225),(1634,219),(1632,204),(1658,180),(1639,135),(1628,119),(1645,89)],fill=255)
    canvas.paste(base,(0,0),protect)

aim=base.copy();ground(aim,.9)
aim.convert('RGB').save(OUT/'03a-player-meteor-aim-v4.png')
descent=base.copy();ground(descent,1.)
descent.alpha_composite(previous['rotated'],(round(1650-previous['headx']),round(335-previous['heady'])))
descent.paste(base,(0,0),previous['protect_hud'])
descent.convert('RGB').save(OUT/'03b-player-meteor-descent-v4.png')

board=Image.new('RGB',(1600,1848),'#211a15');d=ImageDraw.Draw(board)
def text(x,y,t,size=23,bold=False):
    d.text((x,y),t,font=ImageFont.truetype(BOLD if bold else FONT,size),fill='#e4d3b0')
text(42,24,'双环职业纹带 · 横屏 UI 设计稿',39,True)
text(42,88,'沿用淡金／香槟金｜双圈之间有职业纹带｜圈内采用连贯粗纹样',23)
text(42,137,'A  施放前：卷焰纹带 + 连贯火焰旋流',27,True)
text(42,952,'B  陨石终极：落体与范围提示分层表现',27,True)
for im,y in [(aim,183),(descent,998)]:
    board.paste(im.convert('RGB').resize((1516,700),S),(42,y))
    d.rectangle((41,y-1,1558,y+700),outline='#947a4d',width=2)
text(42,895,'外圈与内圈清晰分开；职业纹样落在两圈之间，内部不重复铺图标。',22)
text(42,1712,'陨石拟移至右上终极位；保留既有七按钮布局，游戏数值与代码未改。',22)
d.line((42,1771,1558,1771),fill='#745c38',width=1)
text(42,1790,'实景截图的静态合成；原角色姿态保留，尚未接入游戏或进行动画验收。',20)
board.save(OUT/'03-mobile-ui-proposal-v4.png')

index=Image.new('RGB',(1600,800),'#211a15');di=ImageDraw.Draw(index)
di.text((28,22),'剑与火｜四职业特效与双环范围圈 · 当前设计提案',font=ImageFont.truetype(BOLD,32),fill='#e4d3b0')
for name,x in [('01-four-class-direction-v4.png',24),('02-patterns-and-states-v4.png',804)]:
    im=Image.open(OUT/name).convert('RGB');im.thumbnail((772,580),S)
    index.paste(im,(x+(772-im.width)//2,94+(580-im.height)//2))
di.text((28,700),'当前稿：淡金双环 + 职业纹带 + 连贯粗纹样｜陨石终极｜粗主干雷电',font=ImageFont.truetype(FONT,25),fill='#d8cbb7')
di.text((28,749),'2026-11-16 · 静态候选，待用户审阅 · 未实现',font=ImageFont.truetype(FONT,22),fill='#d8cbb7')
index.save(OUT/'00-review-index-v4.jpg',quality=94)
print('Saved current v4 boards and full-resolution UI composites.')
