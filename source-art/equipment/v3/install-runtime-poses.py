"""Merge measured equipment pose metadata; never modify image pixels or game rules."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'source-art/characters/2d-concepts/player-actions/equipment-v3/metadata.json'
TARGET = ROOT / 'src/cocos/assets/resources/flat2d/characters/raphael/manifest.json'
WEAPONS = {
    'W01': ('longsword', 'sword'), 'W02': ('oath', 'sword'), 'L01': ('storm', 'sword'),
    'W07': ('ashbow', 'bow'), 'W08': ('silverstag', 'bow'), 'L02': ('astralbow', 'bow'),
    'W11': ('graystaff', 'staff'),
}
POSE_FIELDS = ['image', 'columns', 'frameWidth', 'frameHeight', 'perFrameRects',
               'perFrameOrigins', 'alphaBounds', 'worldUnitsPerPixel']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    source = json.loads(SOURCE.read_text(encoding='utf-8-sig'))
    manifest = json.loads(TARGET.read_text(encoding='utf-8-sig'))
    actions = manifest['actions']
    run_before = {key: actions[key] for key in ['run', 'run_bow', 'run_staff']}
    installed, missing = [], []
    for item, (stem, family) in WEAPONS.items():
        walk_key, attack_key = stem + '-walk-v3', stem + '-attack-v3'
        if walk_key not in source or attack_key not in source:
            missing.append(item)
            continue
        walk, attack = source[walk_key], source[attack_key]
        for record in [walk, attack]:
            image = TARGET.parent / record['image']
            if not image.is_file() or len(record['perFrameRects']) != 16 or len(record['perFrameOrigins']) != 16:
                raise SystemExit('Incomplete pose: ' + str(image))
        metadata = lambda record: {field: record[field] for field in POSE_FIELDS if field in record}
        idle = {**metadata(walk), 'frames': 1, 'frameIndices': [0], 'fps': 1, 'loop': True}
        walking = {**metadata(walk), 'frames': 4, 'frameIndices': [1, 2, 3, 2], 'fps': 8, 'loop': True}
        template = actions['attack_' + family]
        attacking = {**template, **metadata(attack), 'frames': 4, 'frameIndices': [0, 1, 2, 3], 'loop': False}
        actions['idle_' + item] = idle
        actions['walk_' + item] = walking
        actions['attack_' + family + '_' + item] = attacking
        if item in ('W01', 'W07', 'W11'):
            suffix = '' if family == 'sword' else '_' + family
            actions['idle' + suffix] = dict(idle)
            actions['walk' + suffix] = dict(walking)
            actions['attack_' + family] = dict(attacking)
        installed.append(item)
    advanced_runs, missing_runs = [], []
    for item in ['W02', 'L01', 'W08', 'L02']:
        stem, family = WEAPONS[item]
        keys = [stem + '-run-v3', stem + '-run-v3-b']
        if any(key not in source for key in keys):
            missing_runs.append(item)
            continue
        first, second = [source[key] for key in keys]
        for record in [first, second]:
            if not (TARGET.parent / record['image']).is_file() or len(record['perFrameRects']) != 16:
                raise SystemExit('Incomplete run image: ' + record['image'])
        origins = {}
        for row, direction in enumerate(manifest['directions']):
            origins[direction] = first['perFrameOrigins'][row * 4:row * 4 + 4] + second['perFrameOrigins'][row * 4:row * 4 + 4]
        base = actions['run' if family == 'sword' else 'run_bow']
        actions['run_' + item] = {
            'image': first['image'], 'frameImages': [first['image']] * 4 + [second['image']] * 4,
            'frames': 8, 'frameIndices': [0, 1, 2, 3, 0, 1, 2, 3], 'columns': 4,
            'frameWidth': first['frameWidth'], 'frameHeight': first['frameHeight'],
            'fps': base['fps'], 'loop': True, 'worldUnitsPerPixel': first['worldUnitsPerPixel'],
            'frameRectsByImage': {Path(record['image']).stem: record['perFrameRects'] for record in [first, second]},
            'perFrameOrigins': origins,
        }
        advanced_runs.append(item)
    if args.require_all and (missing or missing_runs):
        raise SystemExit('Missing weapon poses: ' + ','.join(missing) + '; runs: ' + ','.join(missing_runs))
    if {key: actions[key] for key in run_before} != run_before:
        raise SystemExit('Installer changed run-owned actions')
    output = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
    temporary = TARGET.with_name(TARGET.name + '.equipment-merge.tmp')
    with temporary.open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(output)
    temporary.replace(TARGET)
    report = {'installed': installed, 'pending': missing, 'advancedRunsInstalled': advanced_runs,
              'pendingRuns': missing_runs, 'baseRunActionsUnchanged': True,
              'pixelEdits': False, 'inventoryOrRulesChanged': False}
    with (Path(__file__).parent / 'runtime-install.json').open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
