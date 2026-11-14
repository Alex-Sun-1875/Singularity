"""Register measured appearance assets using existing native FlatActors fields.

Reads PNG dimensions only; source pixels are never rewritten.
"""
import copy
import hashlib
import json
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TARGET = ROOT / 'src/cocos/assets/resources/flat2d/characters/raphael/manifest.json'
OWNERS = ['male-sword-staff-soft-v3', 'male-bows-soft-v3', 'male-reactions-soft-v3']


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before = HERE / 'manifest-before-appearance-v5.json'
    if not before.exists():
        write(before, read(TARGET))
    manifest = read(before)
    old_actions = copy.deepcopy(manifest['actions'])
    incoming, provenance = {}, []
    for owner in OWNERS:
        source = HERE / owner / 'owned-actions.json'
        data = read(source)
        actions = data['actions']
        overlap = set(incoming) & set(actions)
        if overlap:
            raise SystemExit('Conflicting action ownership: ' + str(overlap))
        incoming.update(actions)
        provenance.append({'path': str(source.relative_to(ROOT)), 'sha256': sha(source)})
    if set(incoming) != set(old_actions):
        raise SystemExit('Action coverage mismatch: ' + str({'missing': sorted(set(old_actions)-set(incoming)), 'extra': sorted(set(incoming)-set(old_actions))}))
    images = {}
    for name, action in incoming.items():
        for field in ('fps', 'loop', 'frames', 'frameIndices', 'directionFrameIndices', 'phaseStarts', 'absoluteFrameIndices', 'row'):
            if old_actions[name].get(field) != action.get(field):
                raise SystemExit('Appearance changed animation semantics: ' + name + '/' + field)
        for image in set(action.get('frameImages') or [action.get('image')]):
            if not image or not image.startswith('hero-v6/'):
                raise SystemExit('Unreplaced old appearance: ' + name)
            path = TARGET.parent / image
            with Image.open(path) as png:
                width, height = png.size
                alpha_min, alpha_max = png.getchannel('A').getextrema()
                if png.mode != 'RGBA' or alpha_min >= 16:
                    raise SystemExit('Missing transparent RGBA source: ' + image)
                alpha = png.getchannel('A')
                histogram = alpha.histogram()
                empty_fraction = sum(histogram[:16])/sum(histogram)
                corner_boxes = [(0,0,12,12),(width-12,0,width,12),(0,height-12,12,height),(width-12,height-12,width,height)]
                corner_alpha = max(alpha.crop(box).getextrema()[1] for box in corner_boxes)
                if empty_fraction < .4 or corner_alpha >= 16:
                    raise SystemExit('Opaque background remains at native cutoff: ' + image)
            key = str(Path(image).with_suffix('')).replace('\\', '/')
            rects = action.get('frameRectsByImage', {}).get(key, action.get('perFrameRects', []))
            if action.get('frameRectsByImage') and key not in action['frameRectsByImage']:
                raise SystemExit('Missing native nested crop key: ' + key)
            for x, y, w, h in rects:
                if min(x, y) < 0 or min(w, h) <= 0 or x+w > width or y+h > height:
                    raise SystemExit('Crop outside atlas: ' + name + '/' + image)
            images[image] = {'sha256': sha(path), 'size': [width, height], 'alphaExtrema': [alpha_min, alpha_max], 'alphaBelow16Fraction': empty_fraction, 'cornerMaxAlpha': corner_alpha}
    if len(images) != 35:
        raise SystemExit('Expected 35 selected male atlases, received ' + str(len(images)))
    manifest['actions'] = incoming
    manifest['revision'] = 'concept-image-2d-appearance-v5'
    manifest['sourceDesign'] = str((HERE/'male-direction-soft-geralt-v3.png').relative_to(ROOT))
    manifest['sourceDesignSHA256'] = sha(HERE/'male-direction-soft-geralt-v3.png')
    manifest['alphaThreshold'] = 16/255
    idle = incoming['idle']
    for field in ('image', 'columns', 'frameWidth', 'frameHeight', 'origin', 'perFrameOrigins', 'alphaBounds'):
        if field in idle:
            manifest[field] = idle[field]
    manifest['camera']['worldUnitsPerPixel'] = idle['worldUnitsPerPixel']
    write(TARGET, manifest)
    report = {'revision': manifest['revision'], 'selectedImages': images, 'actionCount': len(incoming), 'metadataSources': provenance, 'sourceDesign': manifest['sourceDesign'], 'pixelEdits': False, 'gameRulesChanged': False, 'animationTimingChanged': False, 'alphaThreshold': manifest['alphaThreshold']}
    write(HERE/'runtime-install.json', report)
    print(json.dumps({'actions': len(incoming), 'atlases': len(images), 'revision': manifest['revision']}))


if __name__ == '__main__':
    main()
