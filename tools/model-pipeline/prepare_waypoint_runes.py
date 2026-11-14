"""Deterministically prepare the cloud-generated v8 waypoint rune cutout."""
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageChops, ImageDraw
import hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'source-art/maps/waypoints-runes-v8'
OUT = ROOT / 'src/cocos/assets/resources/flat2d/waypoints-v1'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def mirror(image):
    left = image.crop((0, 0, image.width // 2, image.height))
    result = Image.new(image.mode, image.size)
    result.paste(left, (0, 0))
    result.paste(ImageOps.mirror(left), (image.width // 2, 0))
    return result

source = ART / 'rune-revised-generated.png'
original = Image.open(source).convert('RGBA')
# The cloud alpha is preserved as the input mask; no black/chroma-key removal.
image = original.resize((512, 512), Image.Resampling.LANCZOS)
mask = image.getchannel('A').point(lambda a: 0 if a < 8 else min(255, round(a * 1.18)))
# A single pixel of alpha dilation keeps the drawn strokes readable at game scale.
mask = mirror(mask.filter(ImageFilter.MaxFilter(3)))
mask = mask.point(lambda a: 0 if a < 10 else a)
image = mirror(image)
red, green, blue, _ = image.split()
core = Image.merge('RGBA', (red.point(lambda c: round(c * .92)), green.point(lambda c: round(c * .87)), blue, mask))
# Narrow, separately controllable bloom derived from the actual generated strokes.
glow_alpha = mask.filter(ImageFilter.GaussianBlur(3)).point(lambda a: round(a * .48))
glow = Image.new('RGBA', core.size, (135, 99, 235, 0))
glow.putalpha(mirror(glow_alpha))
OUT.mkdir(parents=True, exist_ok=True)
outputs = []
for name, image in [('rune-sigil-v8.png', core), ('rune-glow-v8.png', glow)]:
    path = OUT / name
    image.save(path)
    diff = ImageChops.difference(image, ImageOps.mirror(image))
    outputs.append({'file': str(path.relative_to(ROOT)).replace('\\', '/'), 'size': image.size, 'mode': image.mode, 'sha256': sha(path), 'horizontalMirrorMaxError': max(v[1] for v in diff.getextrema())})
canvas = Image.new('RGB', (900, 440), (53, 57, 62))
draw = ImageDraw.Draw(canvas)
for index, background in enumerate([(53, 57, 62), (139, 130, 108), (53, 66, 55)]):
    tile = Image.new('RGBA', (300, 440), background + (255,))
    for size, y in [(230, 25), (140, 285)]:
        tile.alpha_composite(core.resize((size, size), Image.Resampling.LANCZOS), ((300-size)//2, y))
    canvas.paste(tile.convert('RGB'), (index*300, 0))
canvas.save(ART / 'rune-art-review.jpg', quality=92)
record = {
    'style': 'bg3-inspired-rune-circle',
    'generation': {'provider': 'OpenAI built-in image_gen (cloud)', 'initial': {'file': 'rune-initial-generated.png', 'sha256': sha(ART/'rune-initial-generated.png'), 'prompt': 'prompt.txt', 'artReview': 'rejected-by-Codex-raised-emblem-appearance'}, 'revision': {'file': source.name, 'sha256': sha(source), 'prompt': 'revision-prompt.txt', 'artReview': 'representative-flat-stroke-sample-reviewed-runtime-pending'}},
    'reference': {'url': 'https://www.pcgamer.com/baldurs-gate-3-waypoints-fast-travel/', 'image': 'https://cdn.mos.cms.futurecdn.net/Cyw6vuKNEbRa5iKmWnC8wX.jpg', 'role': 'visual research; cropped screenshot supplied only to initial cloud generation; not shipped as a runtime asset'},
    'processing': {'script': 'tools/model-pipeline/prepare_waypoint_runes.py', 'operations': ['Pillow Lanczos 512px resize', 'original generated alpha retained as input', 'alpha cutoff 8 and 1.18 gain', 'one-pixel alpha dilation for distant readability', 'left-half exact horizontal mirroring', 'slight lavender color grading', 'separate 3px Gaussian narrow glow mask'], 'noLocalGenerativeInference': True},
    'outputs': outputs,
    'animation': 'Runtime glow modulation only; not a generated animation sequence',
    'acceptance': {'generationSucceeded': True, 'representativeArtReviewedByCodex': True, 'runtimeArtReview': 'pending', 'userApproval': 'not-claimed'}
}
(ART/'generation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'outputs':outputs, 'review':str(ART/'rune-art-review.jpg')},ensure_ascii=False))
