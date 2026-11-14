"""Opaque flat-lay bottle artwork and tight contact shadows for terrain-conforming quads."""
import hashlib
import json
from pathlib import Path
import runpy

from PIL import Image, ImageChops, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'source-art/props/supply-bottles-v2'
TARGET = ROOT / 'src/cocos/assets/resources/equipment/supplies-v2'
write_meta = runpy.run_path(str(Path(__file__).with_name('prepare-supply-bottles.py')))['write_meta']


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    write_meta(TARGET, ROOT / 'src/cocos/assets/resources/equipment.meta')
    records = []
    for name in ('health', 'focus'):
        path = SOURCE / 'raw' / (name + '.png')
        image = Image.open(path).convert('RGBA')
        # Generated cutouts may have almost-opaque interiors and hidden RGB outside.
        # Make the bottle solid while retaining only silhouette antialiasing.
        image.putalpha(image.getchannel('A').point(lambda a: max(0, min(255, round((a - 64) * 255 / 136)))))
        box = image.getchannel('A').getbbox()
        if box is None:
            raise ValueError('Empty bottle: ' + name)
        bottle = image.crop(box)
        # The user requested a consistent bottle height across the three designs.
        target_height = 136
        target_width = round(bottle.width * target_height / bottle.height)
        if target_width > 240:
            raise ValueError('Bottle is too slender for the shared physical height: ' + name)
        bottle = bottle.resize((target_width, target_height), Image.Resampling.LANCZOS)
        bottle.putalpha(bottle.getchannel('A').point(lambda a: 255 if a >= 250 else a))
        plate = Image.new('RGBA', (256, 256))
        plate.alpha_composite(bottle, ((256 - bottle.width) // 2, (256 - bottle.height) // 2))
        # This local contact shadow is in the same horizontal plane as the prop.
        mask = plate.getchannel('A')
        contact = ImageChops.offset(mask, 0, 1).filter(ImageFilter.GaussianBlur(.7))
        soft = ImageChops.offset(mask, 1, 2).filter(ImageFilter.GaussianBlur(1.5))
        shadow = Image.new('RGBA', plate.size)
        shadow.putalpha(ImageChops.lighter(contact.point(lambda a: round(a * .55)), soft.point(lambda a: round(a * .24))))
        final = Image.alpha_composite(shadow, plate)
        output = TARGET / (name + '-bottle.png')
        final.save(output, optimize=True)
        write_meta(output, ROOT / 'src/cocos/assets/resources/ui/icons/potion-health.png.meta')
        records.append({'item': name, 'source': path.relative_to(ROOT).as_posix(), 'sourceSize': list(image.size),
                        'sourceSha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'output': output.relative_to(ROOT).as_posix(), 'outputSize': list(final.size),
                        'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'bytes': output.stat().st_size,
                        'bottleCoreOpaque': True, 'bottleHeightPixels': target_height, 'alphaExtrema': list(final.getchannel('A').getextrema())})
    result = {'date': '2026-11-12', 'generation': {'tool': 'OpenAI image_gen (cloud)', 'status': 'completed',
              'prompts': 'prompts.json', 'additionalPrompt': 'focus-height-prompt.txt', 'inputs': '512px references in refs/, reduced from v1 and the first v2 opaque cutouts'},
              'processing': {'script': 'tools/design/prepare-supply-bottles-v2.py',
              'method': 'Opaque bottle interiors, silhouette antialiasing, tight neutral contact shadow in the horizontal ground plane.'},
              'artReview': {'status': 'opaque flat-lay raw artwork accepted; scene validation pending'}, 'assets': records}
    (SOURCE / 'provenance.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(records))


if __name__ == '__main__':
    main()
