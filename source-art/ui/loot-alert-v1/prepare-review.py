"""Compose generated loot regions on the original screenshot for design review.

No runtime assets, game state or gameplay code are changed.
"""
from pathlib import Path
import hashlib
import json

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
BASE_PATH = REPO / 'test-results/hud-supplies/iphone14-collapsed.png'
base = Image.open(BASE_PATH).convert('RGB')
W, H = base.size
mask = Image.new('L', base.size)
md = ImageDraw.Draw(mask)
md.rounded_rectangle((808, 4, 1727, 240), 28, fill=255)
md.ellipse((1410, 475, 1665, 712), fill=255)
md.rounded_rectangle((1400, 690, 1685, 746), 10, fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(10))
mask.save(ROOT / 'review-edit-mask.png')

font_path = 'C:/Windows/Fonts/msyh.ttc'
bold_path = 'C:/Windows/Fonts/msyhbd.ttc'
def font(size, bold=False):
    return ImageFont.truetype(bold_path if bold else font_path, size)

outputs = {}
checks = {}
for quality in ['legendary', 'epic']:
    generated = Image.open(ROOT / f'{quality}-generated-v2.png').convert('RGB')
    generated = generated.resize(base.size, Image.Resampling.LANCZOS)
    composed = Image.composite(generated, base, mask)
    destination = ROOT / f'{quality}-v2.png'
    composed.save(destination)
    outputs[quality] = composed
    delta = ImageChops.difference(composed, base)
    delta.paste((0, 0, 0), (0, 0), mask)
    # Explicitly inspect every pixel outside the nonzero edit mask.
    outside = mask.point(lambda value: 255 if value == 0 else 0)
    protected_delta = Image.composite(ImageChops.difference(composed, base), Image.new('RGB', base.size), outside)
    checks[quality] = {'outside_edit_mask_unchanged': protected_delta.getbbox() is None}

base.save(ROOT / 'picked-up-v2.png')
outputs['picked'] = base

# Keep the three screens at their proper 844:390 ratio, with labels outside gameplay.
BW, SH = 1688, 780
header, row_label, gap, footer = 120, 68, 28, 84
BH = header + 3 * (row_label + SH + gap) + footer
board = Image.new('RGB', (BW + 80, BH), '#191715')
d = ImageDraw.Draw(board)
d.text((40, 27), '高级装备掉落 · 设计稿 v2', font=font(34, True), fill='#EDE4CB')
d.text((40, 76), '顶部默认展示 24 秒；拾取时顶部弹窗、地面光效与名称同步隐藏', font=font(23), fill='#AF9D85')
rows = [
    ('legendary', '传奇 · 最后一班岗', '短柔光 / 贴地暖光 / 少量上升光尘', '#F5A45D'),
    ('epic', '史诗 · 雷潮指环', '同一材质语言 / 紫色品质反馈', '#C4A5ED'),
    ('picked', '拾取后', '顶部与地面同步收起，恢复完整游戏画面', '#EDE4CB'),
]
y = header
for key, title, subtitle, color in rows:
    d.text((40, y + 9), title, font=font(27, True), fill=color)
    d.text((BW + 40, y + 14), subtitle, font=font(21), fill='#AF9D85', anchor='ra')
    board.paste(outputs[key].resize((BW, SH), Image.Resampling.LANCZOS), (40, y + row_label))
    y += row_label + SH + gap
d.text((40, y + 10), '美术设计提案 · 云端生成局部 + 原始游戏截图保护合成 · 尚未接入游戏', font=font(21), fill='#AF9D85')
board.save(ROOT / 'overview-v2.jpg', quality=94, subsampling=0)

# A focused before/after makes the light change reviewable without re-sending full screens.
crop_box = (1000, 205, 1280, 560)
old = Image.open(ROOT / 'legendary-generated-v1.png').convert('RGB').crop(crop_box)
new = Image.open(ROOT / 'legendary-generated-v2.png').convert('RGB').crop(crop_box)
detail = Image.new('RGB', (1180, 820), '#191715')
dd = ImageDraw.Draw(detail)
dd.text((30, 18), '光效优化对比', font=font(30, True), fill='#EDE4CB')
for i, (image, label) in enumerate([(old, '初稿 · 长直光束'), (new, '新版 · 短柔光与光尘')]):
    x = 30 + i * 580
    dd.text((x, 66), label, font=font(23), fill='#AF9D85')
    detail.paste(image.resize((560, 710), Image.Resampling.LANCZOS), (x, 104))
detail.save(ROOT / 'beam-comparison-v2.jpg', quality=94, subsampling=0)

files = ['legendary-generated-v1.png', 'legendary-generated-v2.png', 'epic-generated-v2.png', 'legendary-v2.png', 'epic-v2.png', 'picked-up-v2.png', 'overview-v2.jpg', 'beam-comparison-v2.jpg']
record = {
    'date': '2026-11-15',
    'status': 'design-proposal-not-integrated',
    'generation': {'provider': 'OpenAI image_gen', 'mode': 'built-in cloud tool', 'success': True, 'reference_reuse_or_upload_cache': 'not verified', 'seed': None},
    'source_screenshot': str(BASE_PATH.relative_to(REPO)).replace('\\', '/'),
    'canvas': {'pixels': [W, H], 'logical_viewport': [844, 390]},
    'agreed_behavior': {
        'top_notice_default_visible_seconds': 24,
        'pickup_cancels_remaining_top_notice_time': True,
        'pickup_hides': ['top_notice', 'ground_aura', 'ground_name', 'ground_item'],
        'uncollected_ground_item_retained': True,
        'no_warehouse_transfer_requested': True,
        'visible_duration_does_not_delay_pickup': True,
    },
    'art_review': {
        'generated_images_inspected': True,
        'long_laser_removed_in_v2': True,
        'quality_and_names_visually_checked': True,
        'preserve_source_hud': checks,
        'user_art_acceptance': 'pending',
        'runtime_layout_and_animation_acceptance': 'not performed; design only',
        'remaining_note': 'The faint elliptical base strokes are still more regular than the prompt requested; evaluate their appearance with animation before production.',
    },
    'files': {name: {'bytes': (ROOT/name).stat().st_size, 'sha256': hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name in files},
    'prompts': ['prompt.txt', 'prompt-vfx-v2.txt', 'prompt-epic-v2.txt'],
}
(ROOT/'provenance.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'canvas': [W, H], 'checks': checks, 'overview': str(ROOT/'overview-v2.jpg')}, ensure_ascii=False))
