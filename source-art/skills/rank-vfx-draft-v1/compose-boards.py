"""Deterministic Chinese labels around unchanged cloud concept-art pixels."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

ROOT = Path(__file__).resolve().parent
FONT = 'C:/Windows/Fonts/msyh.ttc'
BOLD = 'C:/Windows/Fonts/msyhbd.ttc'
BG, GOLD, INK, MUTED = '#24180f', '#f0cd86', '#eee5d0', '#c6ad8a'
BOARDS = [
    ('FIR_01', '赤焰枪', 'fire-bolt-ranks-raw.png', 'fire-bolt-ranks-v1.png', (80, 714),
     '上排：飞行弹体特写（非等比）　下排：命中场景', [
         ['爆燃半径 0.45m', '紧凑火核 · 命中附燃烧'],
         ['爆燃半径 0.60m', '焰壳卷曲 · 局部爆燃更饱满'],
         ['爆燃半径 0.75m', '对燃烧目标的直接命中 +5%'],
         ['半径 0.90m · 射程 16.5m', '火芯、焰壳、尾焰层次清楚'],
         ['半径 1.10m · 射程 18m', '对燃烧目标的直接命中 +10%']]),
    ('FIR_04', '炎墙封路', 'fire-wall-ranks-raw.png', 'fire-wall-ranks-v1.png', (112, 680),
     '持续条带火域：高亮焰底、橙红焰体、少烟和清楚的敌人轮廓', [
         ['4 × 1.2m · 3拍', '连续燃烧带 · 低位火舌'],
         ['5 × 1.35m · 3拍', '条带延长 · 焰体衔接更完整'],
         ['6 × 1.5m · 3拍', '直接命中燃烧目标 +5%'],
         ['7.5 × 1.7m · 4拍', '加入第四拍 · 前后焰层更清楚'],
         ['9 × 2m · 4拍', '直接命中燃烧目标 +10%']]),
    ('FIR_02', '焚星坠落', 'fire-burst-ranks-raw-v3.png', 'fire-burst-ranks-v3.png', (112, 680),
     '亮度与焰体已加强；本图展示主爆峰值，次爆为延后发生', [
         ['主爆半径 2.8m', '单次主爆 · 紧凑热核'],
         ['主爆半径 3.2m', '橙红焰体向外展开'],
         ['半径 3.6m · 两段爆燃', '主爆75% → 0.30s后次爆25%'],
         ['半径 4m · 选点 16.5m', '保留主次爆的时间分层'],
         ['半径 4.5m · 两段爆燃', '次爆命中可刷新自身既有燃烧', '燃烧持续上限保持原规则']]),
    ('WAR_01', '断空斩', 'war-ranks-raw.png', 'war-ranks-v1.png', (112, 680),
     '斩痕为连续动作的轨迹叠示；保持近身扇形与实剑接触', [
         ['110° · 2段', '短刃痕 · 局部接触火星'],
         ['120° · 2段', '前方覆盖扩展 · 钢刃轮廓更清楚'],
         ['130° · 3段', '加入第三斩 · 连斩轨迹分层'],
         ['140° · 3段', '末斩更稳 · 接触碎屑加强'],
         ['150° · 3段', '末刀命中：下次普攻 +20%', '3秒内一次']]),
    ('BOW_02', '连穿箭', 'bow-ranks-raw.png', 'bow-ranks-v2.png', (65, 728),
     '同一支箭顺序转向；虚线是历史轨迹叠示，不表示同时存在多支箭', [
         ['连续2敌 · 首击包络 3m', '单箭贯穿与转向'],
         ['连续3敌 · 首击包络 4m', '增加一处连续命中'],
         ['连续4敌 · 首击包络 5m', '后续命中伤害 80%'],
         ['连续5敌 · 首击包络 6m', '后续命中伤害 85%'],
         ['连续6敌 · 首击包络 7m', '后续命中伤害 90%']]),
    ('THU_02', '连锁雷弧', 'thu-ranks-raw.png', 'thunder-ranks-v1.png', (112, 680),
     '首击包络内的近邻连接；主干、支路与真实接触节点分别表达', [
         ['总目标2 · 半径 3m', '主干与短近邻连接'],
         ['总目标3 · 半径 4m', '小型近邻链'],
         ['总目标4 · 半径 5m', '出现清楚的分叉结构'],
         ['总目标6 · 半径 6.5m', '短支路组成近邻网'],
         ['总目标8 · 半径 8m', '完整近邻雷网 · 节点保持清楚']]),
]


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def centered(draw, text, x, y, size, color, bold=False, max_width=None):
    f = font(size, bold)
    while max_width and draw.textbbox((0, 0), text, font=f)[2] > max_width and size > 15:
        size -= 1
        f = font(size, bold)
    draw.text((x, y), text, font=f, fill=color, anchor='mt')


index = []
for skill, name, raw, output, (top, bottom), subtitle, notes in BOARDS:
    original = Image.open(ROOT / raw).convert('RGB')
    art = original.crop((0, top, original.width, bottom))
    header, footer, width = 116, 136, art.width
    result = Image.new('RGB', (width, art.height + header + footer), BG)
    result.paste(art, (0, header))
    draw = ImageDraw.Draw(result)
    draw.text((24, 10), f'{name}｜技能1—5级效果设计稿', font=font(30, True), fill=GOLD)
    draw.text((24, 51), subtitle, font=font(18), fill=INK)
    for rank, lines in enumerate(notes, 1):
        x = (rank - .5) * width / 5
        centered(draw, f'技能{rank}级', x, 84, 22, GOLD, True)
        for row, text in enumerate(lines):
            centered(draw, text, x, header + art.height + 13 + row * 26,
                     20 if row == 0 else 18, INK if row == 0 else MUTED,
                     row == 0, width / 5 - 22)
    note = '静态概念稿 · 待审阅 · 尚未接入游戏｜图像展示材质与层级，非精确判定范围或动画帧序列'
    centered(draw, note, width / 2, result.height - 30, 17, MUTED)
    result.save(ROOT / output)
    index.append({'skill': skill, 'name': name, 'file': output, 'raw': raw,
                  'raw_size': list(original.size), 'size': list(result.size),
                  'crop': [0, top, original.width, bottom], 'notes': notes,
                  'status': 'generated_candidate_pending_user_review'})

tile_w, gap = 1100, 16
tiles = []
for row in index:
    im = Image.open(ROOT / row['file'])
    im.thumbnail((tile_w, 600))
    tiles.append(im)
row_heights = [max(tiles[i].height, tiles[i + 1].height) for i in range(0, 6, 2)]
overview = Image.new('RGB', (tile_w * 2 + gap, sum(row_heights) + gap * 2 + 82), BG)
d = ImageDraw.Draw(overview)
d.text((24, 14), '技能等级效果 · 第一批设计稿', font=font(32, True), fill=GOLD)
d.text((24, 56), '每张图从左到右为技能1—5级；火系采用新的高亮、饱满焰体方向。', font=font(17), fill=INK)
y = 82
for row_no, height in enumerate(row_heights):
    for col in range(2):
        im = tiles[row_no * 2 + col]
        overview.paste(im, (col * (tile_w + gap), y))
    y += height + gap
overview.save(ROOT / 'boards-overview.jpg', quality=93)
(ROOT / 'boards-index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Composed {len(index)} annotated boards and overview: {overview.size}')
