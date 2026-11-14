"""Chinese labels and an honest scaled comparison, leaving generated pixels intact."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
BG,INK,GOLD,MUTED='#24180f','#eee5d0','#f0cd86','#c6ad8a'
def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc' if bold else 'C:/Windows/Fonts/msyh.ttc',size)
def text(draw,value,x,y,size=26,color=INK,bold=False):
    draw.text((x,y),value,font=font(size,bold),fill=color,spacing=13)
def save(im,name):
    im.save(ROOT/name)
    im.thumbnail((1400,1160))
    im.save(ROOT/name.replace('.png','-preview.jpg'),quality=90)

art=Image.open(ROOT/'contact-peaks-raw-v2.png').convert('RGB')
canvas=Image.new('RGB',(art.width,art.height+268),BG)
canvas.paste(art,(0,170));draw=ImageDraw.Draw(canvas)
text(draw,'近战连招强化版｜银白刀锋 → 交叉残痕 → 金白重劈',26,16,42,GOLD,True)
text(draw,'三刀接触峰值对照 · 特效亮度与层次逐刀递进 · 保持角色轮廓可见',26,76,27,MUTED)
for i,title in enumerate(['第一刀｜斜切刀光','第二刀｜交叉残痕','第三刀｜重劈爆点']):
    draw.text(((i+.5)*art.width/3,128),title,font=font(27,True),fill=GOLD,anchor='mt')
text(draw,'残痕、碎屑与低位尘环为表现提案，不增加命中或判定范围。',26,art.height+186,27)
text(draw,'云端image_gen静态概念稿 · 待用户审阅 · 尚未接入动画与试玩',26,art.height+226,25,MUTED)
save(canvas,'contact-peaks-v2.png')

art=Image.open(ROOT/'storyboard-raw-v2.png').convert('RGB')
left,top,bottom=250,154,112
canvas=Image.new('RGB',(art.width+left,art.height+top+bottom),BG)
canvas.paste(art,(left,top));draw=ImageDraw.Draw(canvas)
text(draw,'近战连招强化版｜轻、轻、重，亮起后迅速消散',28,16,40,GOLD,True)
text(draw,'保留三刀与既定姿态 · 加强刀光层次、交错残痕与末刀接触 · 静态分镜',28,74,25,MUTED)
for i,title in enumerate(['预备','挥击','接触峰值','收势 / 退亮']):
    draw.text((left+(i+.5)*art.width/4,115),title,font=font(28,True),fill=GOLD,anchor='mt')
for i,title in enumerate(['第一刀｜斜劈\n银白主刃\n细金边与短火星','第二刀｜横斩\n主刀光更亮\n上一刀淡残痕\n构成交错层次','第三刀｜下劈\n金白接触爆点\n方向性碎屑\n低位冲击尘环']):
    y=top+i*art.height/3
    text(draw,title,20,y+24,26)
    draw.line((0,y,left,y),fill='#6e5130',width=1)
text(draw,'三刀姿态与原节奏提案保留；残痕跟随实际刀路，收招后快速退亮。',28,top+art.height+16,25)
text(draw,'云端image_gen概念分镜，非可直接播放的序列帧；握剑、衔接与动态遮挡待接入验证。',28,top+art.height+58,24,MUTED)
save(canvas,'storyboard-v2.png')

# Both rows use the same displayed dimensions; the old source is only resized.
before=Image.open(ROOT/'references/contact-baseline.jpg').convert('RGB')
after=Image.open(ROOT/'contact-peaks-raw-v2.png').convert('RGB')
w=1536;h=round(after.height*w/after.width)
before=before.resize((w,h),Image.Resampling.LANCZOS)
after=after.resize((w,h),Image.Resampling.LANCZOS)
canvas=Image.new('RGB',(w,2*h+208),BG);draw=ImageDraw.Draw(canvas)
text(draw,'近战接触效果｜上一版与强化版',24,12,36,GOLD,True)
text(draw,'上一版（等比缩放）',24,64,25,MUTED)
canvas.paste(before,(0,104))
text(draw,'强化版：更厚刀光、交错残痕、末刀爆点',24,h+118,26,GOLD,True)
canvas.paste(after,(0,h+158))
text(draw,'同尺寸静态比较 · 不代表已接入动画、真实帧时序或新增伤害。',24,2*h+171,23,MUTED)
save(canvas,'before-after-v2.png')
