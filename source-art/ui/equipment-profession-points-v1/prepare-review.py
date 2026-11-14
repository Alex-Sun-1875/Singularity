"""Static design artifacts only. Does not write to the Cocos project."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SKILLS = ROOT / 'src/cocos/assets/resources/ui/combat-relief'
SANS = 'C:/Windows/Fonts/msyh.ttc'
SANS_BOLD = 'C:/Windows/Fonts/msyhbd.ttc'
GOLD = '#DAAE65'
INK = '#EDE4CB'
TEAL = '#75C5B9'
MUTED = '#B8AF9B'

FILES = [
    ('01-equipment-current', '装备 · 当前职业', '默认显示本职业与通用装备；武器 / 防具 / 首饰独立筛选。'),
    ('02-equipment-all', '装备 · 全部装备', '仅扩大浏览范围；其他职业装备可预览，再前往职业页切换。'),
    ('03-profession-preview', '职业选择 · 预览', '当前与预览分别标记；点击确认才切换，不重置既有加点。'),
    ('04-attribute-points', '加点 · 属性', '四项属性同时可见；先调整草稿，核对收益后统一应用。'),
    ('05-skill-points', '加点 · 技能', '展示升级收益与逐级成本；各职业共享技能点，属性点独立。'),
]

def read(slug):
    return Image.open(HERE / (slug + '-generated.png')).convert('RGB')

def icon(image, number, box):
    art = Image.open(SKILLS / f'rpg-bow-0{number}.png').convert('RGBA')
    art = art.resize((box[2]-box[0], box[3]-box[1]), Image.Resampling.LANCZOS)
    image.paste(art, box[:2], art)

images = {slug: read(slug) for slug, _, _ in FILES}
current = images['01-equipment-current']
all_gear = images['02-equipment-all']

# Keep the exact same hero and worn slots in both inventory filter states.
# Only this concept sheet is modified; no source or runtime art is replaced.
left = current.crop((4, 71, 571, 738))
left = left.resize((557, 667), Image.Resampling.LANCZOS)
all_gear.paste(left, (4, 71))

# Add the shared necklace from the current-profession view: 12 visible items,
# including all eight shown by that filter. Generated original had only 11.
necklace = current.crop((914, 454, 1064, 624))
necklace = necklace.resize((139, 131), Image.Resampling.LANCZOS)
all_gear.paste(necklace, (1053, 535))

# Reuse approved skill identities instead of generated illustrative substitutes.
profession = images['03-profession-preview']
for i, x in enumerate((1298, 1432, 1566, 1700), start=1):
    icon(profession, i, (x, 432, x+118, 550))

skills = images['05-skill-points']
for i, cy in enumerate((210, 321, 426, 530, 639), start=1):
    icon(skills, i, (590, cy-44, 678, cy+44))

# Native cloud image resolution is retained. 2532x1170 is an export size,
# not a claim that source pixels contain additional generated detail.
for slug, _, _ in FILES:
    images[slug].save(HERE / (slug + '.png'))
    images[slug].resize((2532,1170), Image.Resampling.LANCZOS).save(HERE / (slug + '-iphone14.png'))

def font(size, bold=False):
    return ImageFont.truetype(SANS_BOLD if bold else SANS, size)

def text(draw, value, x, y, size=22, color=INK, bold=False):
    draw.text((x,y), value, font=font(size,bold), fill=color)

def rule(draw, x0, y, x1):
    draw.line((x0,y,x1,y),fill='#5E482D',width=1)

def wrap(draw, value, x, y, width, size=20, color=MUTED, line=32):
    chunk=''
    for char in value:
        if draw.textlength(chunk+char,font=font(size))>width and chunk:
            text(draw,chunk,x,y,size,color)
            y+=line
            chunk=char
        else:
            chunk+=char
    if chunk:
        text(draw,chunk,x,y,size,color)
    return y+line

# A two-column review board: first row compares the inventory states,
# second row compares profession selection and attributes, third row
# places skills beside the interaction decisions.
BOARD_W, PAD, GAP, COL = 2200, 54, 44, 1024
HEADER, CARD_H, ROW_GAP = 158, 594, 38
board = Image.new('RGB',(BOARD_W,HEADER+3*CARD_H+2*ROW_GAP+56),'#110E0B')
d = ImageDraw.Draw(board)
text(d,'装备、职业与加点',PAD,38,40,GOLD,True)
text(d,'UI 视觉提案 v1  /  iPhone 14 横屏 844 × 390',PAD,99,22,MUTED)
text(d,'静态设计稿 · 未接入游戏',BOARD_W-410,68,22,TEAL)
rule(d,PAD,139,BOARD_W-PAD)

for idx,(slug,title,note) in enumerate(FILES):
    col,row=idx%2,idx//2
    x=PAD+col*(COL+GAP)
    y=HEADER+row*(CARD_H+ROW_GAP)
    text(d,title,x,y,28,GOLD,True)
    thumb=images[slug].resize((COL,474),Image.Resampling.LANCZOS)
    board.paste(thumb,(x,y+48))
    wrap(d,note,x,y+538,COL,21,INK,32)

x,y=PAD+COL+GAP,HEADER+2*(CARD_H+ROW_GAP)
text(d,'交互约定',x,y,28,GOLD,True)
items=[
    ('筛选与职业分开', '每次进入装备页默认“当前职业”；“全部装备”只展示已持有装备，不会触发换装或换职业。'),
    ('预览与确认分开', '浏览职业卡片保留当前状态；确认切换前说明武器与技能配置的变化，通用装备继续保留。'),
    ('点数与草稿分开', '属性点和技能点独立；技能点由所有职业共享。调整先预览，应用后生效；未保存离开需提示。'),
    ('安全区与触控', '以844×390逻辑视口细化；点击区至少48×48，独立目标间距8。需继续校准顶栏、筛选与列表密度。'),
]
ty=y+54
for heading,body in items:
    text(d,heading,x,ty,24,TEAL,True)
    ty=wrap(d,body,x,ty+38,COL,21,INK,32)+22
text(d,'本轮审阅：结构、文案与示例点数。用户美术确认待进行。',PAD,board.height-42,19,MUTED)
board.save(HERE/'00-overview.png')
board.resize((1540,round(board.height*1540/BOARD_W)),Image.Resampling.LANCZOS).save(HERE/'00-overview-preview.jpg',quality=93)

manifest={
    'created':'2026-11-11',
    'stage':'static_ui_proposal_not_implemented',
    'generator':'built-in cloud OpenAI image_gen',
    'reference':'style-reference.jpg',
    'generated_source_resolution':list(current.size),
    'device_baseline':{'logical_viewport':[844,390],'physical_export':[2532,1170],'density':3},
    'postprocess':'Pillow: synchronized inventory portrait/worn slots, added missing common necklace, reused approved unique BOW skill icons, resized and composed overview',
    'local_model_used':False,
    'runtime_files_modified':False,
    'new_dependencies':False,
    'checks':{
        'class_names':'four existing combat families only',
        'equipment_filter':'current family plus common; all means all owned gear',
        'attribute_points':'Lv11 gives30; current18/16/10/12 spends16 leaving14; draft21/16/10/14 spends21 leaving9',
        'hp_example':'without equipment HP bonuses:170+4*(12-10)=178; preview170+4*(14-10)=186',
        'strength_example':'0.8% per point above10;18=6.4%,21=8.8%',
        'skill_points':'Lv11 chapter2 gives12; three skills rank2 spend3 leaving9; one rank2→3 costs2 leaving7',
        'bow_02':'rank2→3: targets3→4; radius4m→5m',
        'unique_skill_icons':'existing rpg-bow-01 through05 reused'
    },
    'art_review':{
        'status':'reviewed_as_visual_proposal_user_review_pending',
        'reviewed':'dark-gold direction, four classes, distinct preview/current state, two independent point pools, numeric consistency, inventory state consistency',
        'refinement_required':'Pixel-level alignment, font scale, exact48px touch regions and8px gaps, safe-area/platform-capsule layout, scroll behavior, skill-list density, all9 worn-slot presentation.',
        'scope':'generated hero/item paintings illustrate the proposal; production must reuse approved character, item icons and shared UI components.'
    },
    'deliverables':[]
}
for slug, title, note in FILES:
    fp=HERE/(slug+'.png')
    manifest['deliverables'].append({'file':fp.name,'title':title,'note':note,'sha256':hashlib.sha256(fp.read_bytes()).hexdigest(),'prompt':slug+'-prompt.txt'})
(HERE/'provenance.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'saved':str(HERE),'screens':len(FILES),'overview':str(HERE/'00-overview.png'),'generated_size':current.size,'runtime_modified':False},ensure_ascii=False))
