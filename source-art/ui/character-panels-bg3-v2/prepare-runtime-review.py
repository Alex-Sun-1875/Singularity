"""Arrange actual browser captures for review; no generated or retouched UI pixels."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAPTURES = ROOT / 'src/cocos/test-results/random-forging-v2'
FONT = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 20)
records = []
board = Image.new('RGB', (1688, 848), '#15100b')
for index, (name, label) in enumerate([
    ('character-preview', '人物 · 游戏运行截图'),
    ('equipment', '装备 · 游戏运行截图'),
    ('skills', '技能 · 游戏运行截图'),
    ('forge-preview', '强化 · 游戏运行截图'),
]):
    source = CAPTURES / ('mobile-' + name + '.png')
    im = Image.open(source).convert('RGB')
    x, y = index % 2 * 844, index // 2 * 424
    ImageDraw.Draw(board).text((x + 14, y + 4), label, font=FONT, fill='#d6bd85')
    board.paste(im.resize((844, 390), Image.Resampling.LANCZOS), (x, y + 34))
    records.append({'file': source.relative_to(ROOT).as_posix(), 'size': list(im.size),
                    'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
board.save(HERE / 'review/runtime-panels-v2.jpg', quality=95)
comparison = Image.new('RGB', (844, 848), '#15100b')
for y, source, label in [
    (0, HERE / 'screens/01-preview.png', '已确认方向的设计稿 · 示例数值'),
    (424, CAPTURES / 'mobile-forge-preview.png', 'Cocos运行截图 · 实际存档数值'),
]:
    ImageDraw.Draw(comparison).text((14, y + 4), label, font=FONT, fill='#d6bd85')
    im = Image.open(source).convert('RGB')
    comparison.paste(im.resize((844, 390), Image.Resampling.LANCZOS), (0, y + 34))
comparison.save(HERE / 'review/forge-runtime-comparison-v2.jpg', quality=95)
(HERE / 'runtime-review.json').write_text(json.dumps({
    'method': 'Pillow resize and contact-sheet layout of unmodified browser captures',
    'generation_status': 'not generated; captured from the Cocos preview',
    'assistant_review': 'Checked full-body identity, shared materials, native values, no obvious overlap or missing icons; mobile geometry checked separately by browser review',
    'user_art_acceptance': 'pending',
    'platform_acceptance': 'TapTap real device pending',
    'captures': records,
}, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print('Prepared actual runtime review boards.')
