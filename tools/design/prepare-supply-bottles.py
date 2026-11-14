"""Prepare generated physical bottle cutouts for the existing equipment asset bundle."""
import hashlib
import json
from pathlib import Path
import uuid

from PIL import Image, ImageChops, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'source-art/props/supply-bottles-v1'
TARGET = ROOT / 'src/cocos/assets/resources/equipment/supplies-v1'
SIZE = 256


def stable_uuid(path):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'sword-and-fire:' + path.relative_to(ROOT).as_posix()))


def write_meta(path, template):
    meta = Path(str(path) + '.meta')
    if meta.exists():
        return
    data = json.loads(template.read_text(encoding='utf-8-sig'))
    old, new = data['uuid'], stable_uuid(path)
    text = json.dumps(data, ensure_ascii=False, indent=2).replace(old, new)
    if path.is_file():
        text = text.replace('potion-health', path.stem).replace('"repeat"', '"clamp-to-edge"')
    meta.write_text(text + '\n', encoding='utf-8')


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    write_meta(TARGET, ROOT / 'src/cocos/assets/resources/equipment.meta')
    results = []
    for name in ('health', 'focus'):
        source = SOURCE / 'raw' / (name + '.png')
        original = Image.open(source).convert('RGBA')
        alpha = original.getchannel('A')
        box = alpha.point(lambda value: 255 if value > 12 else 0).getbbox()
        if box is None:
            raise ValueError('Empty generated bottle: ' + name)
        bottle = original.crop(box)
        bottle.thumbnail((SIZE - 28, SIZE - 28), Image.Resampling.LANCZOS)
        plate = Image.new('RGBA', (SIZE, SIZE))
        plate.alpha_composite(bottle, ((SIZE - bottle.width) // 2, (SIZE - bottle.height) // 2 - 3))
        # A small local contact shadow grounds the authored bottle without an extra draw call.
        shade_alpha = ImageChops.offset(plate.getchannel('A'), 2, 5).filter(ImageFilter.GaussianBlur(2.5))
        shade_alpha = shade_alpha.point(lambda value: round(value * .3))
        final = Image.new('RGBA', (SIZE, SIZE))
        final.putalpha(shade_alpha)
        final = Image.alpha_composite(final, plate)
        output = TARGET / (name + '-bottle.png')
        final.save(output, optimize=True)
        write_meta(output, ROOT / 'src/cocos/assets/resources/ui/icons/potion-health.png.meta')
        results.append({'item': name, 'source': source.relative_to(ROOT).as_posix(),
                        'sourceSize': list(original.size), 'sourceCrop': list(box),
                        'output': output.relative_to(ROOT).as_posix(), 'outputSize': [SIZE, SIZE],
                        'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                        'bytes': output.stat().st_size, 'alphaExtrema': list(final.getchannel('A').getextrema())})
    manifest = {'date': '2026-11-12', 'generation': {'tool': 'OpenAI image_gen (cloud)',
                'status': 'completed', 'prompts': 'prompts.json'},
                'processing': {'script': 'tools/design/prepare-supply-bottles.py',
                'method': 'Alpha-aware crop and Lanczos resize; local translucent contact shadow; original generated alpha preserved.'},
                'artReview': {'status': 'raw bottle artwork accepted; scene integration pending',
                'notes': 'Physical corked glass/ceramic bottles; distinct body silhouettes and materials; no UI glyphs or emblems.'},
                'assets': results}
    (SOURCE / 'provenance.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(results, ensure_ascii=False))


if __name__ == '__main__':
    main()
