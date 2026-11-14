"""Add Chinese labels outside untouched image_gen concept panels."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
BG, INK, GOLD, MUTED = '#24180f', '#eee5d0', '#f0cd86', '#c6ad8a'

def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc' if bold else 'C:/Windows/Fonts/msyh.ttc', size)

def label(draw, text, x, y, size=26, color=INK, bold=False):
    draw.text((x,y),text,font=font(size,bold),fill=color,spacing=14)

def board(raw, output, title, subtitle, columns, rows, footer):
    art=Image.open(ROOT/raw).convert('RGB')
    left,top,bottom=250,154,112
    canvas=Image.new('RGB',(art.width+left,art.height+top+bottom),BG)
    canvas.paste(art,(left,top))
    draw=ImageDraw.Draw(canvas)
    label(draw,title,28,15,40,GOLD,True)
    label(draw,subtitle,28,72,24,MUTED)
    for i,text in enumerate(columns):
        x=left+(i+.5)*art.width/len(columns)
        draw.text((x,115),text,font=font(28,True),fill=GOLD,anchor='mt')
    for i,text in enumerate(rows):
        y=top+i*art.height/len(rows)
        label(draw,text,20,y+24,26)
        draw.line((0,y,left,y),fill='#6e5130',width=1)
    label(draw,footer,28,top+art.height+18,23,MUTED)
    canvas.save(ROOT/output)
    preview=canvas.copy();preview.thumbnail((1392,1130));preview.save(ROOT/output.replace('.png','-preview.jpg'),quality=89)

board('fire-direction-raw-v1.png','fire-direction-v1.png',
      '火系技能｜明亮火芯、厚实橙焰、暗红外缘',
      '原创材质与轮廓提案 · 选取技能1 / 3 / 5级对照 · 画面非精确米制范围',
      ['技能1级','技能3级','技能5级'],
      ['赤焰枪\n单发火核\n飞行→命中叠示\n局部爆燃',
       '焚星坠落\n下落→主爆叠示\n3 / 5级另有\n0.30秒后次爆\n本图未叠画次爆',
       '炎墙封路\n连续焰底\n分段卷起的火舌\n条带随等级加长'],
      '云端image_gen静态概念稿 · 待用户审阅 · 未接入游戏\n热核只在峰值短亮；后续须另验动态退亮、遮挡与手机实机表现。')

board('melee-combo-raw-v1.png','melee-combo-v1.png',
      '近战三段连招｜斜劈 → 反手横斩 → 双手下劈',
      '拟定轻、轻、重节奏 · 三刀各有独立重心、轨迹与收招 · 下列时刻为待调试提案',
      ['预备','挥击','接触','收招 / 接下一刀'],
      ['第一刀｜斜劈\n0.00—0.38秒\n接触：0.12秒\n短而利落',
       '第二刀｜横斩\n0.38—0.76秒\n接触：0.50秒\n反向衔接',
       '第三刀｜下劈\n0.76—1.32秒\n接触：0.98秒\n双手发力与收势'],
      '按住或连点普攻接续三刀 · 每刀一次真实判定 · 第三刀收势后循环\n云端image_gen静态姿态提案，非已接入动画或可直接播放的序列帧；关节与帧间衔接待制作验证。')
