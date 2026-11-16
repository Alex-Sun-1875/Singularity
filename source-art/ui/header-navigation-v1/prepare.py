"""Navigation proposal only: composite existing project art with exact UI geometry."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ART = ROOT / 'src/cocos/assets/resources/ui/quiet-bronze'
S = 3
GOLD = '#DAB16B'
BRIGHT = '#F0D69A'
IVORY = '#EDE4CB'
MUTED = '#B6A88D'
DISABLED = '#766C59'
SERIF = ROOT / 'src/cocos/assets/resources/ui/quiet-bronze/rpg-serif-v2.ttf'
SANS = Path('C:/Windows/Fonts/msyh.ttc')


def font(size, serif=False):
    return ImageFont.truetype(str(SERIF if serif else SANS), round(size))


def txt(im, value, xy, size, color=IVORY, anchor='lt', serif=False):
    ImageDraw.Draw(im).text(xy, value, font=font(size, serif), fill=color, anchor=anchor)


def icon(im, kind, cx, cy, scale=3, state='idle'):
    """Same arrow path as the approved map; no font-dependent arrow or x glyph."""
    d = ImageDraw.Draw(im)
    colors = {'idle': GOLD, 'hover': BRIGHT, 'pressed': BRIGHT, 'disabled': DISABLED}
    color = colors[state]
    if state in ('hover', 'pressed'):
        face = 32 * scale
        d.rounded_rectangle((cx-face/2, cy-face/2, cx+face/2, cy+face/2),
                            radius=5*scale, fill='#32281B' if state == 'hover' else '#48351F')
    # 24-unit viewBox fitted inside a 20 logical px icon box.
    k = 20 * scale / 24
    def pt(x, y):
        return (cx + (x-12)*k, cy + (y-12)*k)
    paths = [[(14, 5), (7, 12), (14, 19)], [(7, 12), (20, 12)]] if kind == 'back' else [
        [(6, 6), (18, 18)], [(18, 6), (6, 18)]]
    width = max(1, round(1.8*scale))
    for path in paths:
        points = [pt(*p) for p in path]
        d.line(points, fill=color, width=width, joint='curve')
        for x, y in (points[0], points[-1]):
            r = width/2
            d.ellipse((x-r, y-r, x+r, y+r), fill=color)


def nine(source, width, height, corner=48, edge=48):
    src = Image.open(source).convert('RGBA')
    sw, sh = src.size
    dest = Image.new('RGBA', (width, height))
    sx, sy = [0, corner, sw-corner, sw], [0, corner, sh-corner, sh]
    dx, dy = [0, edge, width-edge, width], [0, edge, height-edge, height]
    for y in range(3):
        for x in range(3):
            tile = src.crop((sx[x], sy[y], sx[x+1], sy[y+1]))
            tile = tile.resize((dx[x+1]-dx[x], dy[y+1]-dy[y]), Image.Resampling.LANCZOS)
            dest.alpha_composite(tile, (dx[x], dy[y]))
    return dest


def panel(width, height):
    im = Image.new('RGBA', (round(width*S), round(height*S)), '#191713')
    im.alpha_composite(nine(ART / 'double-gold-inset-v6.png', *im.size, edge=48))
    im.alpha_composite(nine(ART / 'double-gold-frame-v6.png', *im.size, edge=48))
    return im


def rule(im, x, y, width, kind='title'):
    name = 'settings-title-rule-v11.png' if kind == 'title' else 'settings-row-rule-v11.png'
    line = Image.open(ART / name).convert('RGBA').resize((round(width*S), 6*S), Image.Resampling.LANCZOS)
    im.alpha_composite(line, (round(x*S), round(y*S-3*S)))


def header(width=480, mode='back', title='技能靶场', show_hit=False):
    im = panel(width, 108)
    txt(im, title, (width*S/2, 32*S), 20*S, GOLD, 'mm', True)
    cx = 36 if mode == 'back' else width-36
    icon(im, mode, cx*S, 32*S)
    rule(im, 20, 64, width-40)
    txt(im, '五靶直线阵', (24*S, 78*S), 14*S, IVORY)
    if show_hit:
        dashed(im, ((cx-24)*S, 8*S, (cx+24)*S, 56*S), '#A4C3B4', 2, 9)
    return im


def dashed(im, box, color, width=2, step=12):
    d = ImageDraw.Draw(im)
    x1, y1, x2, y2 = box
    for a in range(round(x1), round(x2), step*2):
        d.line((a, y1, min(a+step, x2), y1), fill=color, width=width)
        d.line((a, y2, min(a+step, x2), y2), fill=color, width=width)
    for a in range(round(y1), round(y2), step*2):
        d.line((x1, a, x1, min(a+step, y2)), fill=color, width=width)
        d.line((x2, a, x2, min(a+step, y2)), fill=color, width=width)


def full_screen():
    # This is the prior approved design fixture, not a new runtime screenshot.
    im = Image.open(ROOT / 'source-art/ui/map-redesign-v1/05-regional-iphone14.png').convert('RGBA')
    return im.resize((844*S, 390*S), Image.Resampling.LANCZOS)


def floating_screen(base):
    im = ImageEnhance.Brightness(base.convert('RGB')).enhance(.35).convert('RGBA')
    # Native capsule belongs to the host and stays legible above the game scrim.
    capsule = base.crop((744*S, 7*S, 838*S, 44*S))
    im.alpha_composite(capsule, (744*S, 7*S))
    x, y, w, h = 270, 60, 304, 270
    shadow = Image.new('RGBA', im.size)
    ImageDraw.Draw(shadow).rounded_rectangle((x*S-12, y*S+8, (x+w)*S+12, (y+h)*S+24),
                                            radius=24*S, fill=(0, 0, 0, 185))
    shadow = shadow.filter(ImageFilter.GaussianBlur(9*S))
    im.alpha_composite(shadow)
    p = panel(w, h)
    txt(p, '地图图例', (w*S/2, 32*S), 20*S, GOLD, 'mm', True)
    icon(p, 'close', (w-36)*S, 32*S)
    rule(p, 20, 64, w-40)
    entries = [('任务目标', '当前追踪的位置', '#EBC576'),
               ('传送阵', '已发现的传送地点', '#B8A2E2'),
               ('队伍位置', '你在地图中的位置', '#9AD6D6')]
    d = ImageDraw.Draw(p)
    for i, (label, detail, color) in enumerate(entries):
        yy = 78 + i*56
        cx, cy = 35*S, (yy+22)*S
        if i == 0:
            d.polygon([(cx, cy-10*S), (cx+8*S, cy), (cx, cy+10*S), (cx-8*S, cy)], outline=color, width=2*S)
            d.line((cx, cy-4*S, cx, cy+2*S), fill=color, width=2*S)
            d.ellipse((cx-S, cy+5*S, cx+S, cy+7*S), fill=color)
        elif i == 1:
            d.ellipse((cx-9*S, cy-9*S, cx+9*S, cy+9*S), outline=color, width=2*S)
            d.polygon([(cx, cy-12*S), (cx+12*S, cy), (cx, cy+12*S), (cx-12*S, cy)], outline=color, width=S)
        else:
            d.polygon([(cx, cy-10*S), (cx+8*S, cy+8*S), (cx, cy+4*S), (cx-8*S, cy+8*S)], fill=color)
        txt(p, label, (58*S, (yy+4)*S), 15*S)
        txt(p, detail, (58*S, (yy+28)*S), 11*S, MUTED)
        if i < 2:
            rule(p, 22, yy+49, w-44, 'row')
    im.alpha_composite(p, (x*S, y*S))
    return im


def rounded_paste(board, source, box, radius=18):
    x, y, w, h = box
    src = source.resize((w, h), Image.Resampling.LANCZOS).convert('RGB')
    mask = Image.new('L', (w, h))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w-1, h-1), radius, fill=255)
    board.paste(src, (x, y), mask)


def board_image(full, floating):
    b = Image.new('RGB', (2400, 1930), '#151613')
    d = ImageDraw.Draw(b)
    txt(b, 'SWORD AND FIRE  /  UI COMPONENT  /  2026.11.16', (64, 44), 23, '#98896D')
    txt(b, '窗口返回与关闭', (64, 96), 61, IVORY)
    txt(b, '根据 TapTap 原生胶囊的避让关系切换，两种入口共用同一套 Header。', (65, 184), 29, MUTED)
    columns = [(64, full, '01', '全屏窗口 · 左侧返回', '右上区域被原生胶囊占用，返回留在 Header 左侧。'),
               (1236, floating, '02', '浮层窗口 · 右上关闭', '窗口完整避开原生胶囊，关闭留在窗口右上角。')]
    for x, screen, number, title, caption in columns:
        txt(b, number, (x, 264), 25, GOLD)
        txt(b, title, (x+58, 256), 38)
        rounded_paste(b, screen, (x, 326, 1100, 508))
        txt(b, caption, (x, 860), 26, MUTED)
    d.line((64, 929, 2336, 929), fill='#3C382B', width=2)
    txt(b, '统一 Header 组件', (64, 970), 37)
    txt(b, '同一页面只保留一个入口，标题居中位置保持一致。', (555, 978), 26, MUTED)
    for x, mode in [(64, 'back'), (1236, 'close')]:
        im = header(mode=mode, show_hit=True)
        rounded_paste(b, im, (x, 1040, 1100, 248), 12)
        label = '返回 / 左侧' if mode == 'back' else '关闭 / 右侧'
        txt(b, label, (x, 1309), 26, GOLD)
        txt(b, '48×48 触区  ·  20×20 图标  ·  64 高 Header', (x+240, 1309), 26, MUTED)
    txt(b, '组件状态', (64, 1403), 34)
    txt(b, '默认不铺底；反馈只作用于图标附近，触区保持不变。', (310, 1410), 26, MUTED)
    states = [('idle', '默认'), ('hover', '悬停'), ('pressed', '按下'), ('disabled', '禁用')]
    for i, (state, title) in enumerate(states):
        x = 64 + i*586
        d.rounded_rectangle((x, 1477, x+514, 1661), radius=12, fill='#1E1D18')
        icon(b, 'back', x+90, 1569, scale=3, state=state)
        icon(b, 'close', x+225, 1569, scale=3, state=state)
        txt(b, title, (x+326, 1569), 29, MUTED if state == 'disabled' else IVORY, 'mm')
    d.line((64, 1720, 2336, 1720), fill='#3C382B', width=2)
    txt(b, '判定规则', (64, 1763), 28, GOLD)
    txt(b, '右上关闭触区与原生胶囊间距不足 8 → 左侧返回；间距足够 → 右上关闭。', (265, 1763), 29)
    txt(b, '单位均为逻辑像素。胶囊与安全区为布局示意，接入时读取运行时区域；此稿尚未接入游戏。',
        (64, 1844), 24, '#918977')
    return b


def svg_icon(kind):
    path = 'm14 5-7 7 7 7M7 12h13' if kind == 'back' else 'm6 6 12 12M18 6 6 18'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.16" stroke-linecap="round" stroke-linejoin="round"><path d="{path}"/></svg>\n'


def make_spec():
    sources = [
        'source-art/ui/map-redesign-v1/05-regional-iphone14.png',
        'source-art/ui/map-redesign-v1/index.html',
        'src/cocos/assets/resources/ui/quiet-bronze/double-gold-frame-v6.png',
        'src/cocos/assets/resources/ui/quiet-bronze/double-gold-inset-v6.png',
        'src/cocos/assets/resources/ui/quiet-bronze/settings-title-rule-v11.png',
        'src/cocos/assets/resources/ui/quiet-bronze/settings-row-rule-v11.png',
    ]
    return {
        'title': '窗口 Header 返回与关闭组件 · v1',
        'date': '2026-11-16',
        'status': 'design-proposal-pending-user-review',
        'scope': '仅设计稿与可复现的本地合成，不修改 Cocos 运行代码、不打包。',
        'userSteering': '与 TapTap 原生胶囊重叠的全屏/顶部窗口使用左侧返回；不重叠的窗口使用右上关闭。',
        'priorDesign': '旅途地图原稿采用细线直向左箭头；现有 rpg-return-arrow-v3 为弯曲回转箭头，与原稿不同。',
        'construction': 'Pillow 确定性排版、复用项目原始皮肤与设计截图；本轮未调用生成模型。',
        'componentProposal': {
            'name': 'GoldPanelHeader',
            'modes': ['back-left', 'close-right'],
            'shared': ['标题', '标题分隔线', '图标绘制', '触控尺寸', '状态反馈', '禁用状态'],
            'pageOwns': ['窗口位置', '运行时安全区与胶囊区域', '现有关闭/返回动作', '未保存提示与不可关闭状态'],
            'selection': '先验证候选右上关闭的完整48×48触区在安全区内，且与原生胶囊至少相隔8；符合则关闭，否则改用左侧返回并验证左侧完整触区。',
            'recompute': '窗口尺寸、横屏方向、安全区或胶囊区域变化时重新布局；不通过机型名称或 tap 全局对象猜测。',
            'singleEntry': '每个当前层级只提供一种入口；不同时显示左返回和右关闭，也不重复添加底部导航。',
            'actionSemantics': '只调整入口外观与位置，保留页面既有关闭或返回目标；退出靶场属于退出玩法的业务动作，继续保留。',
            'nativeControls': '胶囊继续由宿主提供，游戏不绘制可点击的仿制胶囊。',
        },
        'tokensLogical': {
            'headerHeight': 64, 'touchWidth': 48, 'touchHeight': 48,
            'iconBox': 20, 'iconStroke': 1.8, 'topInset': 8, 'sideInset': 12,
            'adjacentTouchGap': 8, 'capsuleClearance': 8, 'titleFont': 20,
            'titleSymmetricReserve': 68, 'feedbackVisibleFace': 32,
        },
        'states': {
            'idle': '裸图标；无常驻方形底板',
            'hover': '浅暗金32×32圆角反馈面，图标提亮',
            'pressed': '同位置加深反馈面，不移动或缩放布局',
            'disabled': '降低图标明度并拒绝输入；隐藏/取消后清除状态',
        },
        'scopeExamples': {
            'backWhenTopRightCollides': ['全屏地图', '全屏人物/装备/技能/锻造窗口', '顶部与胶囊相交的侧栏或大窗口'],
            'closeWhenClear': ['居中的设置/帮助窗口', '图例与普通提示窗口', '详情浮层', '右上触区避开胶囊的侧栏'],
            'rule': '页面名称仅为示例；最终按实际窗口与触区位置选择，不按页面名称写死。',
        },
        'preview': {
            'logicalViewport': [844, 390], 'density': 3,
            'fullScreen': '复用上一版地图原稿作为全屏使用示例，非本轮运行截图。',
            'floating': '在地图原稿上合成地图图例浮窗，演示右上关闭。',
            'headerDetails': '技能靶场相同标题分别展示返回、关闭两个模式；绿色虚线仅标注触区。',
            'hardware': '示意胶囊、安全区与地图数据沿用原设计夹具，不是本轮 TapTap 真机测量。',
        },
        'geometryReview': {
            'floatingCloseHit': [514, 68, 48, 48],
            'capsuleFixture': [748, 10, 86, 30],
            'floatingClear': True,
            'hypotheticalFullScreenCloseHit': [741, 8, 48, 48],
            'fullScreenCandidateIntersectsCapsule': True,
            'fullScreenUsesPriorMapLeftReturn': True,
        },
        'sources': [{'path': p, 'sha256': hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in sources],
        'review': {
            'generation': '所有PNG均由本地确定性合成完成。',
            'visual': '静态视觉复核记录见 review.json；用户确认待完成。',
            'runtime': '未接入。旋转、安全区、触控和各页面动作需要在接入后验收。',
        },
    }


if __name__ == '__main__':
    full = full_screen()
    floating = floating_screen(full)
    full.save(HERE / '01-fullscreen-back.png')
    floating.save(HERE / '02-floating-close.png')
    header(mode='back', show_hit=True).save(HERE / '03-header-back-detail.png')
    header(mode='close', show_hit=True).save(HERE / '04-header-close-detail.png')
    board_image(full, floating).save(HERE / '00-navigation-proposal.png')
    for kind in ['back', 'close']:
        (HERE / f'{kind}.svg').write_text(svg_icon(kind), encoding='utf-8')
    spec = make_spec()
    (HERE / 'design.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    thumb = Image.open(HERE / '00-navigation-proposal.png')
    thumb.thumbnail((1800, 1448))
    thumb.save(HERE / 'review-preview.jpg', quality=93)
    print(json.dumps({'outputs': ['00-navigation-proposal.png', '01-fullscreen-back.png', '02-floating-close.png',
                                 '03-header-back-detail.png', '04-header-close-detail.png', 'design.json', 'back.svg', 'close.svg'],
                      'canvas': [2400, 1930], 'runtimeChanges': False}, ensure_ascii=False))
