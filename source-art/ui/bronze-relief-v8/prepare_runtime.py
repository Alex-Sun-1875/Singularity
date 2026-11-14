"""Normalize the cloud-generated bronze sprites without repainting their material."""
from pathlib import Path
from PIL import Image, ImageEnhance
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
OUT = PROJECT / 'src/cocos/assets/resources/ui/quiet-bronze'
OUT.mkdir(parents=True, exist_ok=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(name, asset):
    source = ROOT / f'{name}-generated.png'
    image = Image.open(source).convert('RGBA')
    bounds = image.getchannel('A').point(lambda value: 255 if value >= 64 else 0).getbbox()
    # Correct the generated circle's slight ovalness and make its visible bounds
    # agree with Cocos' logical diameter. Preserve the generated material pixels.
    normalized = image.crop(bounds).resize((512, 512), Image.Resampling.LANCZOS)
    # User requested brighter metal on both map and skills, while retaining
    # the generated grooves and dark leather rather than flattening the sprite.
    original_alpha = normalized.getchannel('A')
    brighter = ImageEnhance.Brightness(normalized.convert('RGB')).enhance(1.48 if name == 'compass-frame' else 1.55).convert('RGBA')
    brighter.putalpha(original_alpha)
    if name == 'button-medallion':
        radial = Image.new('L', (512, 512))
        radial.putdata([round(max(0, min(1, (math.hypot(x-255.5, y-255.5)-182)/30))*255) for y in range(512) for x in range(512)])
        normalized = Image.composite(brighter, normalized, radial)
    else:
        normalized = brighter
    target = OUT / f'{asset}.png'
    normalized.save(target)
    return normalized, {'source': source.name, 'sourceSize': image.size,
                        'sourceSHA256': digest(source), 'alphaBodyBounds': bounds,
                        'asset': str(target.relative_to(PROJECT)),
                        'runtimeSize': normalized.size, 'sha256': digest(target)}


frame, frame_record = normalize('compass-frame', 'compass-frame-v8')
button, button_record = normalize('button-medallion', 'button-medallion-v8')

leather = button.crop((128, 128, 384, 384))
leather.putalpha(255)
leather_path = OUT / 'leather-inset-v8.png'
leather.save(leather_path)

rail = frame.copy()
alpha = rail.getchannel('A')
values = []
for y in range(512):
    for x in range(512):
        angle = math.degrees(math.atan2(255.5-y, x-255.5)) % 360
        fade = max(0, min(1, (angle-220)/4, (320-angle)/4)) if 220 <= angle <= 320 else 0
        values.append(round(alpha.getpixel((x, y))*fade))
mask = Image.new('L', (512, 512))
mask.putdata(values)
rail.putalpha(mask)
rail_path = OUT / 'compass-tool-rail-v8.png'
rail.save(rail_path)

record = {
    'version': 'bronze-relief-v8-with-ornament-revision',
    'ornamentReference': 'source-art/ui/bronze-relief-v8/reference-ornament-supply.png',
    'userRevision': 'Same double-metal border and curl/leaf motifs as supply reference, including skill buttons; brighter metal. Existing UiChrome vector ornaments reused above rendered material, without uniform ring overlays.',
    'date': '2026-11-08',
    'generator': 'Cloud OpenAI image_gen built-in tool; two representative sprite generations.',
    'prompts': 'source-art/ui/bronze-relief-v8/prompts.json',
    'reference': 'source-art/ui/bronze-relief-v8/reference-compass-crop.png',
    'referenceUse': 'User-provided style reference only; no reference pixels copied into runtime sprites.',
    'generationStatus': 'Both generations completed; original RGBA outputs retained.',
    'localProcessing': 'Pillow: alpha-body crop, slight circle aspect alignment, Lanczos512 resize; lower arc alpha mask derived from the same rendered rim. User-requested metal brightness: frame1.48x, button rim1.55x with radial protection of dark leather; no procedural repaint of relief.',
    'assets': [frame_record, button_record, {'asset': str(leather_path.relative_to(PROJECT)), 'derivedFrom': 'button-medallion-v8.png; central leather only', 'runtimeSize': [256, 256], 'sha256': digest(leather_path)}, {
        'asset': str(rail_path.relative_to(PROJECT)),
        'derivedFrom': 'compass-frame-v8.png', 'runtimeSize': [512, 512],
        'sha256': digest(rail_path), 'angularAlphaMaskDegrees': [220, 320]}],
    'artReview': {
        'generatedSample': 'Material relief, patina, leather grain and dark grooves inspected; selected for integrated pilot.',
        'runtime': 'Pending screenshot inspection at actual desktop/mobile size.',
        'userAcceptance': 'Not recorded.'},
}
(ROOT / 'provenance.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(record['assets'], ensure_ascii=False, indent=2))
