"""Install measured hero artwork using existing FlatActors metadata; no pixel edits."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
TARGET = ROOT / 'src/cocos/assets/resources/flat2d/characters/raphael/manifest.json'
HERE = Path(__file__).parent
SOURCES = [HERE / 'metadata.json', HERE / 'metadata-partial.json',
           HERE.with_name('hero-v4-equipment') / 'metadata.json',
           HERE.with_name('hero-v4-reactions') / 'metadata.json',
           HERE / 'metadata-readable.json',
           HERE.with_name('hero-v4-equipment') / 'metadata-readable.json',
           HERE.with_name('hero-v4-reactions') / 'metadata-readable.json',
           HERE / 'metadata-families.json',
           HERE.with_name('hero-v4-equipment') / 'metadata-advanced.json',
           HERE.with_name('hero-v4-reactions') / 'metadata-advanced-runs.json',
           HERE.with_name('hero-v4-equipment') / 'metadata-bow-reactions.json']
FAMILIES = {'W01': 'sword', 'W02': 'sword', 'L01': 'sword',
            'W07': 'bow', 'W08': 'bow', 'L02': 'bow', 'W11': 'staff'}
FIELDS = {'image', 'frameImages', 'frameWidth', 'frameHeight', 'columns', 'origin',
          'frames', 'frameIndices', 'directionFrameIndices', 'absoluteFrameIndices',
          'row', 'perFrameRects', 'frameRectsByImage', 'perFrameOrigins',
          'alphaBounds', 'worldUnitsPerPixel', 'fps', 'phaseStarts', 'loop'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-all', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    manifest = read(TARGET)
    original = read(TARGET)
    incoming, provenance = {}, []
    for source in SOURCES:
        # The partial file is only used until its owner hands off the full file.
        if source.name == 'metadata-partial.json' and SOURCES[0].is_file():
            continue
        if not source.is_file():
            continue
        data = read(source)
        for name, action in data.get('actions', {}).items():
            if name in incoming and source.name != 'metadata-readable.json':
                raise SystemExit('Overlapping action ownership: ' + name)
            incoming[name] = {key: value for key, value in action.items() if key in FIELDS}
            if source.parent == HERE and source.name in ('metadata.json', 'metadata-partial.json'):
                # Original source measurement used1.8m/head-matched diagnostic
                # scales. Restore the established scene height for this preview.
                if name == 'idle':
                    incoming[name]['worldUnitsPerPixel'] = 1.556 / 485
                elif name == 'run':
                    incoming[name]['worldUnitsPerPixel'] = 1.556 / 353
        provenance.append({'path': str(source.relative_to(ROOT)),
                           'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    if not incoming:
        raise SystemExit('No measured actions were provided')
    actions = manifest['actions']
    for name, action in incoming.items():
        prior = actions.get(name)
        # Core duration/release rules remain unchanged. A new authored pose
        # order may require new visual phase starts (bow release is .75).
        if prior and name.startswith('attack_'):
            for field in ('fps', 'loop'):
                if field in prior:
                    action[field] = prior[field]
            if 'phaseStarts' not in action and 'phaseStarts' in prior:
                action['phaseStarts'] = prior['phaseStarts']
        actions[name] = action
    aliases = {'idle_W01': 'idle', 'run_W01': 'run', 'walk': 'walk_W01',
               'attack_sword': 'attack_sword_W01',
               'idle_bow': 'idle_W07', 'walk_bow': 'walk_W07',
               'attack_bow': 'attack_bow_W07', 'run_W07': 'run_bow',
               'idle_staff': 'idle_W11', 'walk_staff': 'walk_W11',
               'attack_staff': 'attack_staff_W11', 'run_W11': 'run_staff'}
    for alias, source in aliases.items():
        if source in incoming:
            actions[alias] = dict(actions[source])
    # Bow-only back equipment remains present during shared empty-hand actions.
    for item in ('W08', 'L02'):
        for state in ('hit', 'death', 'spell', 'interact', 'dodge'):
            source = state + '_W07'
            if source in incoming:
                actions[state + '_' + item] = dict(actions[source])
    required = ['idle', 'walk', 'run', 'idle_bow', 'walk_bow', 'run_bow',
                'idle_staff', 'walk_staff', 'run_staff', 'attack_sword',
                'attack_bow', 'attack_staff', 'hit', 'death', 'spell', 'interact', 'dodge']
    required += [f'{state}_{item}' for item, family in FAMILIES.items()
                 for state in ('idle', 'walk', 'run', 'attack_' + family)]
    required += [f'{state}_{item}' for item in ('W07', 'W08', 'L02')
                 for state in ('hit', 'death', 'spell', 'interact', 'dodge')]
    pending = []
    images = set()
    dimensions = {}
    for name in required:
        action = actions.get(name, {})
        names = action.get('frameImages') or [action.get('image', '')]
        if not all(image.startswith('hero-v4/') for image in names):
            pending.append(name)
            continue
        if action.get('frameWidth', 0) <= 0 or action.get('frameHeight', 0) <= 0:
            raise SystemExit('Missing explicit frame dimensions: ' + name)
        for image in names:
            if not (TARGET.parent / image).is_file():
                raise SystemExit('Missing source PNG for ' + name + ': ' + image)
            images.add(image)
            if image not in dimensions:
                with Image.open(TARGET.parent / image) as png:
                    dimensions[image] = png.size
            key = str(Path(image).with_suffix('')).replace('\\', '/')
            by_image = action.get('frameRectsByImage')
            if by_image is not None and key not in by_image:
                raise SystemExit('Native texture key missing from frameRectsByImage: ' + name + '/' + key)
            rects = by_image[key] if by_image else action.get('perFrameRects')
            if rects:
                width, height = dimensions[image]
                for rect in rects:
                    if (len(rect) != 4 or not all(math.isfinite(value) for value in rect)
                            or min(rect[:2]) < 0 or min(rect[2:]) <= 0
                            or rect[0] + rect[2] > width or rect[1] + rect[3] > height):
                        raise SystemExit('Native crop outside source PNG: ' + name + '/' + image + '/' + str(rect))
    if args.require_all and pending:
        raise SystemExit('Old body still selected by: ' + ', '.join(pending))
    manifest['revision'] = 'concept-image-2d-hero-v4'
    manifest['alphaThreshold'] = .025
    manifest['edgeWidth'] = .008
    manifest['sourceDesign'] = 'source-art/characters/2d-concepts/hero-v4-proportion/hero-v4-proportion-master-v1.png'
    if args.require_all:
        idle = actions['idle']
        for field in ('image', 'columns', 'frameWidth', 'frameHeight', 'origin',
                      'perFrameOrigins', 'alphaBounds'):
            if field in idle:
                manifest[field] = idle[field]
    report = {'completeBodyCoverage': not pending, 'pendingActions': pending,
              'installedActions': sorted(incoming), 'newImages': sorted(images),
              'metadataSources': provenance, 'pixelEdits': False,
              'gameRulesChanged': False, 'sourceImagesSha256': {
                  image: hashlib.sha256((TARGET.parent / image).read_bytes()).hexdigest()
                  for image in sorted(images)}}
    if not args.dry_run:
        backup = HERE / 'manifest-before-hero-v4.json'
        if not backup.is_file():
            backup.write_text(json.dumps(original, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        temporary = TARGET.with_suffix('.hero-v4.tmp')
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        temporary.replace(TARGET)
        (HERE / 'runtime-install.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
