"""Compare selection hues while preserving the reviewed v2 material and geometry."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import json

OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'selection-redesign-v2'/'compose-review.py'
# Reuse the art functions without running that script's composition or review writes.
scope={'__file__':str(SOURCE)}
exec(compile(SOURCE.read_text(encoding='utf-8').split('\noriginals=')[0],str(SOURCE),'exec'),scope)
UI,SKIN,FONT=scope['UI'],scope['SKIN'],scope['FONT']
inlay,tile=scope['material_inlay'],scope['tile']
OUT.mkdir(exist_ok=True)

palettes=[
 {'name':'冷铁灰','slug':'iron-grey','body':(37,38,39),'rim':(137,141,142),'highlight':(169,171,166)},
 {'name':'灰蓝','slug':'slate-blue','body':(26,35,46),'rim':(113,137,157),'highlight':(155,169,179)},
 {'name':'暗酒红','slug':'wine-red','body':(52,30,34),'rim':(163,121,126),'highlight':(185,156,148)},
 {'name':'烟棕','slug':'smoke-brown','body':(43,34,25),'rim':(153,136,109),'highlight':(179,163,137)},
 {'name':'当前青灰','slug':'current-grey-green','body':(28,40,32),'rim':(112,143,130),'highlight':(156,173,151)}
]

def font(size):return ImageFont.truetype(str(FONT),size)
def color_label_font(size):return ImageFont.truetype('C:/Windows/Fonts/simsun.ttc',size)
normal=Image.open(SKIN/'prep-skill-row-v5.png').convert('RGBA').resize((556,74),Image.Resampling.LANCZOS)
frame=Image.open(SKIN/'rpg-skill-icon-frame-v6.png').convert('RGBA').resize((59,59),Image.Resampling.LANCZOS)
icons=[]
for index in [1,2]:
    icon=Image.open(UI/f'combat-relief/rpg-war-{index:02d}.png').convert('RGBA')
    inset=round(icon.width*.047)
    icons.append(icon.crop((inset,inset,icon.width-inset,icon.height-inset)).resize((56,56),Image.Resampling.LANCZOS))

def skill_row(palette,selected=True):
    row=inlay(normal,selected,palette)
    row.alpha_composite(icons[0 if selected else 1],(20,9))
    row.alpha_composite(frame,(18,7))
    d=ImageDraw.Draw(row)
    d.text((100,25),'断空斩' if selected else '破军突袭',font=font(31),fill='#FFF0C9',anchor='lm')
    d.text((100,57),'单体' if selected else '群攻',font=font(21),fill='#B4A083',anchor='lm')
    d.text((534,37),'1级',font=font(25),fill='#D1BE98',anchor='rm')
    return row

# The equipped badge is deliberately identical across hues, to keep its meaning independent.
reference=Image.open(scope['SOURCES'][0]).crop(scope['CROP']).convert('RGB')
badge=ImageEnhance.Color(reference.crop((648,339,748,365)).convert('RGBA')).enhance(.72)

board=Image.new('RGB',(1600,1030),'#100D0A')
d=ImageDraw.Draw(board)
d.text((58,37),'选中配色对照',font=font(38),fill='#E5D5B4')
d.text((58,97),'同一套细铜边、材质与布局，仅比较选中底色和内边。',font=font(23),fill='#B9AA8D')
d.line((58,143,1542,143),fill='#493622',width=1)

for index,palette in enumerate(palettes[:4]):
    x=58+(index%2)*776
    y=175+(index//2)*295
    d.text((x,y),palette['name'],font=color_label_font(32),fill='#E5D5B4')
    sample=tile(132,148,True,palette)
    # Keep the badge shape/text unchanged, including its existing dark teal tone.
    sample.alpha_composite(badge,(16,119))
    board.paste(sample,(x,y+57),sample)
    selected=skill_row(palette,True);idle=skill_row(palette,False)
    board.paste(selected,(x+152,y+57),selected)
    board.paste(idle,(x+152,y+143),idle)
    pair=Image.new('RGB',(740,245),'#100D0A')
    pd=ImageDraw.Draw(pair);pd.text((12,12),palette['name'],font=color_label_font(28),fill='#E5D5B4')
    pair.paste(sample,(12,66),sample);pair.paste(selected,(164,66),selected);pair.paste(idle,(164,152),idle)
    pair.save(OUT/(palette['slug']+'.png'),optimize=True)

d.line((58,783,1542,783),fill='#493622',width=1)
d.text((58,819),'当前青灰',font=font(29),fill='#B9C9B9')
current=skill_row(palettes[4],True)
board.paste(current,(288,809),current)
d.text((58,934),'已穿戴标签、装备品质色与技能图标原色在各方案中保持一致。',font=font(22),fill='#B9AA8D')
d.text((1542,991),'配色候选 · 尚未接入游戏',font=font(18),fill='#9D8C73',anchor='rm')
board.save(OUT/'selection-color-comparison.png',optimize=True)

spec={'date':'2026-11-17','status':'candidate_pending_user_review','method':'Deterministic Pillow palette variants of the existing v2 material study. No new generation.',
      'source':'source-art/ui/selection-redesign-v2/','changed':'Selected surface and inner bevel hues only.',
      'preserved':['Geometry','Material grain','Antique bronze outer frame','Illustration colors','Equipped badge','Item quality colors','Skill labels and levels'],
      'palettes':palettes,'runtimeIntegration':'not_started'}
(OUT/'palettes.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT/'selection-color-comparison.png')
