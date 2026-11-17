"""Deterministic layout only; generated concept pixels come from cloud image_gen."""
from pathlib import Path
import hashlib, json
from PIL import Image, ImageDraw, ImageFont

base = Path(__file__).resolve().parent
board = Image.new('RGB', (1648, 590), '#171d22')
draw = ImageDraw.Draw(board)
def label(x, y, text, size=22, color='#dce5ec', bold=False):
    font = ImageFont.truetype('C:/Windows/Fonts/' + ('msyhbd.ttc' if bold else 'msyh.ttc'), size)
    draw.text((x, y), text, font=font, fill=color)

label(20, 12, '破晓裁决 · 层次气浪与下劈终结', 30, bold=True)
label(20, 63, '当前实录｜交叉终结', 23, bold=True)
label(844, 63, '增强概念｜从上往下劈斩', 23, bold=True)
for x, name in [(12, 'current-runtime-reference.jpg'), (836, 'ultimate-downcut-concept.png')]:
    with Image.open(base / name) as image:
        board.paste(image.convert('RGB').resize((800, 392), Image.Resampling.LANCZOS), (x, 102))
label(20, 507, '横扫留余波  →  上挑拉开纵深  →  下劈压落、落点爆发', 23, bold=True)
label(20, 551, '静态方案，尚未接入 · 右图为云端生成概念帧，动作、波形与比例需由实际动画小样验证', 18, '#a9bac7')
board.save(base / 'ultimate-proposal-comparison.jpg', quality=95, subsampling=0)

names = ['README.md', 'current-runtime-reference.jpg', 'ultimate-downcut-concept.png',
         'ultimate-enhanced-concept.png', 'ultimate-proposal-comparison.jpg',
         'prompt-initial.txt', 'prompt-downcut.txt', 'layout.py']
data = {
    'status': 'static concept proposal; user art acceptance pending; not implemented',
    'latestUserDirection': 'No charge-up. Emphasize layers and impact; finish with a downward sword slash.',
    'productionFilesChanged': False,
    'reference': 'Actual v22 compiled-game WAR_05 frame 040; stored as current-runtime-reference.jpg',
    'generation': {'tool': 'built-in cloud OpenAI image_gen',
                   'steps': ['current runtime frame -> layered crossing candidate',
                             'crossing candidate -> downward finishing slash concept after user steering'],
                   'currentCandidate': 'ultimate-downcut-concept.png',
                   'supersededCandidate': 'ultimate-enhanced-concept.png'},
    'localProcessing': 'Pillow resize and labeled side-by-side layout only; no local model inference',
    'review': {'generated': True, 'visuallyInspected': True, 'userAccepted': False,
               'animationVerified': False, 'collisionOrDamageVerified': False, 'deviceVerified': False},
    'files': {name: hashlib.sha256((base / name).read_bytes()).hexdigest() for name in names}
}
(base / 'provenance.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print('Saved comparison board and provenance; production untouched.')
