"""Repair locomotion using existing frame inventory, palette and native packer.

No local inference, downloads or new dependencies. Candidate preparation and
visual acceptance are separate; --install is added only for reviewed output.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ACTOR = ROOT / 'src/cocos/assets/resources/flat2d/characters/raphael'
sys.path.insert(0, str(HERE.parent / 'local-qwen21-unified-v3'))
import prepare
import appearance


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


gear = module('repair_existing_gear', HERE.parent / 'attack-identity-v5/static_gear.py')
packer = module('repair_existing_packer', HERE.parent / 'attack-identity-v5/pack.py')
Y, X = np.mgrid[:768, :512]
M = json.loads((ACTOR / 'manifest.json').read_text('utf-8-sig'))
FRAMES = prepare.inventory(M)
SHEETS = {}
CACHE = {}
HEADS = {}
TARGETS = {}
DONORS = {}


def world(action, direction, phase=0):
    record = prepare.find(FRAMES, action, direction, phase)
    key = record['image'], record['index']
    if key not in CACHE:
        if record['image'] not in SHEETS:
            SHEETS[record['image']] = Image.open(ACTOR / record['image']).convert('RGBA')
        CACHE[key] = prepare.canvas(record, SHEETS)
    return CACHE[key].copy(), record


def translated(image, dx, dy=0):
    return image.convert('RGBa').transform(image.size, Image.Transform.AFFINE,
        (1, 0, -dx, 0, 1, -dy), Image.Resampling.BICUBIC).convert('RGBA')


def equipment(image, record):
    copied = copy.deepcopy(record)
    if 'explore_' in record['action']:
        copied['refs'].append(dict(action='explore_idle_' + gear.weapon_id(record)))
    return gear.make_equipment_mask(image, copied, None)


def cloth_pixels(image):
    a = np.asarray(image)
    rgb = a[..., :3].astype(float)
    r, g, b = np.moveaxis(rgb, -1, 0)
    neutral = (rgb.max(-1) - rgb.min(-1) < 38) & (r - g < 18) & (g - b < 16)
    return (a[..., 3] > 64) & neutral


def head_target(action, direction):
    key = action, direction
    if key not in TARGETS:
        count = M['actions'][action].get('frames', 1)
        positions = []
        for phase in range(count):
            im, record = world(action, direction, phase)
            positions.append(appearance.hair(im, record)[0]['center'])
        state = 'run' if 'run' in action else 'walk'
        reference, _ = world('explore_idle_W01', direction)
        idle_head = appearance.hair(reference)[0]['center']
        target = np.median(positions, axis=0)
        if state == 'walk':
            target[0] = idle_head[0]
        TARGETS[key] = target, positions
    return TARGETS[key]


def back_walk_candidate(phase):
    image, record = world('explore_walk_W01', 'up', phase)
    cloud = Image.open(HERE / 'back-walk-cloud.png').convert('RGBA')
    width = cloud.width / 4
    patch = cloud.crop((round(phase * width), 0, round((phase + 1) * width), cloud.height))
    patch = patch.convert('RGBa').resize((268, 364), Image.Resampling.LANCZOS).convert('RGBA')
    layer = Image.new('RGBA', image.size)
    layer.paste(patch, (122, 380))
    # The model's coat, hands and thigh pixels are excluded. Only the calves
    # and boots enter this candidate; remove the old ankle silhouette as well.
    weight = np.clip((Y - 571) / 14, 0, 1)
    before, edited = np.asarray(image).astype(float), np.asarray(layer).astype(float)
    mix = before * (1 - weight[..., None]) + edited * weight[..., None]
    candidate = Image.fromarray(np.uint8(np.clip(np.round(mix), 0, 255)))
    return candidate, record


def corrected(action, direction, phase):
    image, record = world(action, direction, phase)
    state = 'run' if 'run' in action else 'walk'
    key = gear.weapon_id(record)
    canonical_action = 'explore_' + state + '_W01'
    donor, donor_record = world(canonical_action, direction, phase)
    if state == 'walk' and direction == 'up':
        donor, donor_record = back_walk_candidate(phase)
    if True:
        # Retarget the already authored complete W01 leg cycle. No bone warp
        # or bent-ankle deformation: the original leg pixels move rigidly.
        target, positions = head_target(action, direction)
        head = np.asarray(positions[phase])
        # Small authored bob remains, but accidental support-foot registration
        # cannot throw the whole head down on a flight/passing frame.
        bob = [2, 0, -2, 0, 2, 0, -2, 0][phase] if state == 'run' else [0, -1, 0, -1][phase]
        dy = float(target[1] + bob - head[1])
        source_protect = equipment(image, record)
        image = translated(image, 0, dy)
        old = np.asarray(image).copy()
        lower = np.asarray(donor).copy()
        protect = np.asarray(translated(Image.fromarray(source_protect.astype('uint8') * 255).convert('RGBA'), 0, dy))[..., 0] > 127
        donor_gear = equipment(donor, donor_record)
        seed = ndi.binary_closing(cloth_pixels(donor) & (Y >= 346), iterations=3)
        labels, _ = ndi.label(seed)
        components = []
        for label, bounds in enumerate(ndi.find_objects(labels), 1):
            if bounds and bounds[0].stop > 400 and np.count_nonzero(labels[bounds] == label) > 140:
                components.append(label)
        pants = ndi.binary_dilation(ndi.binary_fill_holes(np.isin(labels, components)), iterations=3)
        valid = (lower[..., 3] > 0) & (pants | (Y >= 420)) & ~donor_gear
        lower[~valid] = 0
        # Preserve the source's held shafts/bows, hands and coat hems. All old
        # leg pixels, including old boot edges, are removed below the seam.
        rr, gg, bb = np.moveaxis(old[..., :3].astype(float), -1, 0)
        skin = (rr > gg + 20) & (gg > bb + 8) & (rr > 145) & (Y < 494)
        coat = (rr > gg + 14) & (rr > bb + 12) & (gg - bb < 15) & (Y < 466)
        keep = protect | ndi.binary_dilation(skin, iterations=10) | coat
        remove = (Y >= 389) & ~keep
        old[remove] = 0
        image = Image.alpha_composite(Image.fromarray(lower), Image.fromarray(old))
    reference, _ = world('explore_idle_W01', direction)
    image, grade = appearance.grade(image, reference)
    target, positions = head_target(action, direction)
    head = np.asarray(positions[phase])
    origin = [256 + float(head[0] - target[0]), 712]
    grade['registration'] = dict(before=head.tolist(), target=target.tolist(), origin=origin,
                                 upperBodyTranslationY=float(target[1] + bob - head[1]))
    return image, record, grade


def pilot():
    items = [('explore_run_W07', 'right', 8), ('explore_walk_W01', 'up', 4)]
    board = Image.new('RGB', (8 * 180, 4 * 292), '#22211f')
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 14)
    reports = []
    for row, (action, direction, count) in enumerate(items):
        for phase in range(count):
            before, _ = world(action, direction, phase)
            after, record, grading = corrected(action, direction, phase)
            reports.append(dict(action=action, direction=direction, phase=phase, grade=grading))
            for i, image in enumerate((before, after)):
                y = (row * 2 + i) * 292
                thumb = image.resize((180, 270), Image.Resampling.LANCZOS)
                board.paste(thumb, (phase * 180, y + 22), thumb)
                draw.text((phase * 180 + 3, y), f'{"BEFORE" if i == 0 else "CANDIDATE"} {direction} {phase}', font=font, fill='white')
            if action == 'explore_walk_W01':
                after.save(HERE / f'back-walk-candidate-{phase}.png')
    board.save(HERE / 'pilot.jpg', quality=94)
    (HERE / 'pilot-grading.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def movement(name):
    return name in ('walk', 'run') or name.startswith(('walk_', 'run_', 'explore_walk_', 'explore_run_'))


def prepare_candidate():
    candidate = HERE / 'candidate-runtime'
    if (HERE / 'prepare-report.json').is_file():
        previous = json.loads((HERE / 'prepare-report.json').read_text('utf-8'))
        if previous['sourceManifestSHA256'] != digest(ACTOR / 'manifest.json'):
            raise ValueError('Current runtime changed since preparation; do not grade installed frames twice.')
    groups = {}
    for name, action in M['actions'].items():
        if not movement(name):
            continue
        count = action.get('frames', 1)
        images = tuple(action.get('frameImages', [action.get('image', M['image'])] * count))
        key = images, tuple(action.get('frameIndices', range(count)))
        groups.setdefault(key, dict(action=name, aliases=[], images=images, count=count))['aliases'].append(name)
    jobs = [(group, direction, phase) for group in groups.values()
            for direction in M['directions'] for phase in range(group['count'])]
    # Warm loader/palette caches once before the image jobs use existing SciPy
    # and Pillow operations concurrently. No model or external service runs here.
    touched = {name for group in groups.values() for name in group['images']}
    for image in touched:
        SHEETS[image] = Image.open(ACTOR / image).convert('RGBA')
    for group in groups.values():
        for direction in M['directions']:
            head_target(group['action'], direction)
    references = {direction: world('explore_idle_W01', direction)[0] for direction in M['directions']}
    for reference in references.values():
        appearance.grade(reference, reference)
    old_pixels = {}
    items = {name: [] for name in touched}
    original_hashes = {name: digest(ACTOR / name) for name in touched}
    meta_hashes = {name: digest(str(ACTOR / name) + '.meta') for name in touched}
    for record in FRAMES.values():
        if record['image'] not in touched or not any(not movement(v['action']) for v in record['refs']):
            continue
        x, y, w, h = record['rect']
        crop = SHEETS[record['image']].crop((x, y, x+w, y+h))
        old_pixels[record['image'], record['index']] = hashlib.sha256(crop.tobytes()).hexdigest()
        items[record['image']].append(dict(record=record, crop=crop, origin=record['origin'], factor=None))
    results = []

    def work(job):
        group, direction, phase = job
        image, record, grading = corrected(group['action'], direction, phase)
        native = image.convert('RGBa').resize((320, 480), Image.Resampling.LANCZOS).convert('RGBA')
        array = np.asarray(native).copy()
        array[array[..., 3] < 8] = 0
        native = Image.fromarray(array)
        bounds = native.getchannel('A').getbbox()
        bounds = [max(0, bounds[0]-2), max(0, bounds[1]-2), min(320, bounds[2]+2), min(480, bounds[3]+2)]
        crop = native.crop(bounds)
        origin = [grading['registration']['origin'][0]*.625-bounds[0], 445-bounds[1]]
        index = 16 + M['directions'].index(direction)*4 + phase % 4
        name = group['images'][phase]
        return dict(group=group, image=name, index=index, direction=direction, phase=phase,
                    crop=crop, origin=origin, grading=grading)

    print(f'Preparing {len(jobs)} direction/phase frames in {len(touched)} existing atlases', flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = {pool.submit(work, job): job for job in jobs}
        for future in as_completed(pending):
            result = future.result()
            results.append(result)
            name, index = result['image'], result['index']
            record = dict(image=name, index=index)
            items[name].append(dict(record=record, crop=result['crop'], origin=result['origin'], factor=1))
            if len(results) % 48 == 0 or len(results) == len(jobs):
                print(f'Prepared {len(results)}/{len(jobs)}', flush=True)
    geometry, factors = {}, copy.deepcopy(M.get('frameScaleFactors', {}))
    png_hashes = {}
    for name, entries in sorted(items.items()):
        positions, size, method = packer.shelf_placements(entries)
        atlas = Image.new('RGBA', size)
        for entry in entries:
            record = entry['record'];index = record['index'];rect = positions[index]
            atlas.paste(entry['crop'], tuple(rect[:2]))
            geometry[name, index] = dict(rect=rect, origin=entry['origin'], bounds=packer.alpha_bounds(entry['crop']))
            key = packer.image_key(name)
            array = factors.setdefault(key, [])
            while len(array) <= index:
                array.append(1)
            if entry['factor'] is not None:
                array[index] = entry['factor']
        path = candidate / name
        path.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(path, optimize=True)
        png_hashes[name] = digest(path)
    updated = copy.deepcopy(M)
    phase_results = {(r['group']['action'], r['direction'], r['phase']): r for r in results}
    alias_groups = {name: group for group in groups.values() for name in group['aliases']}
    for name, action in updated['actions'].items():
        old = M['actions'][name]
        primary = old.get('image', M['image'])
        images = list(dict.fromkeys(old.get('frameImages', [primary])))
        if not any(image in touched for image in images):
            continue
        group = alias_groups.get(name)
        if group:
            action.update(frameIndices=[16 + phase % 4 for phase in range(group['count'])],
                          columns=4, worldUnitsPerPixel=.004)
            action.pop('row', None)
            action.pop('absoluteFrameIndices', None)
            action['originMethod'] = 'Locomotion v3: complete stride; head registered; original leg anatomy and foot/flight anchors.'
        by_image = copy.deepcopy(old.get('frameRectsByImage', {}))
        for image in images:
            if image not in touched:
                continue
            rectangles = [[0, 0, 1, 1] for _ in range(32)]
            for (sheet, index), value in geometry.items():
                if sheet == image:
                    rectangles[index] = value['rect']
            by_image[packer.image_key(image)] = rectangles
        action['frameRectsByImage'] = by_image
        action['perFrameRects'] = copy.deepcopy(by_image[packer.image_key(primary)])
        origins, alpha = {}, [[0, 0, 0, 0] for _ in range(32)]
        for direction in M['directions']:
            origins[direction] = []
            for phase in range(old.get('frames', 1)):
                if group:
                    result = phase_results[group['action'], direction, phase]
                    physical = result['image'], result['index']
                else:
                    r = prepare.find(FRAMES, name, direction, phase)
                    physical = r['image'], r['index']
                value = geometry[physical]
                origins[direction].append(value['origin'])
                if physical[0] == primary:
                    alpha[physical[1]] = value['bounds']
        action['perFrameOrigins'] = origins
        action['alphaBounds'] = alpha
        action['sourcePNGs'] = [str(candidate / image) for image in images]
        action['sourcePNGSHA256s'] = [png_hashes.get(image, digest(ACTOR / image)) for image in images]
    updated['frameScaleFactors'] = factors
    new_frames = prepare.inventory(updated)
    for physical, expected in old_pixels.items():
        value = geometry[physical]
        x, y, w, h = value['rect']
        with Image.open(candidate / physical[0]) as atlas:
            crop = atlas.convert('RGBA').crop((x, y, x+w, y+h))
        if hashlib.sha256(crop.tobytes()).hexdigest() != expected:
            raise ValueError('Protected idle pixels changed: ' + str(physical))
    write_json(candidate / 'manifest.json', updated)
    write_json(HERE / 'baseline-manifest.json', M)
    write_json(HERE / 'frame-report.json', [dict(action=r['group']['action'], aliases=r['group']['aliases'],
               image=r['image'], index=r['index'], direction=r['direction'], phase=r['phase'],
               grading=r['grading']) for r in results])
    report = dict(status='candidate prepared; art acceptance pending', sourceManifestSHA256=digest(ACTOR/'manifest.json'),
        candidateManifestSHA256=digest(candidate/'manifest.json'), frames=len(results), actions=len(alias_groups),
        pngCount=len(png_hashes), sourcePNGs=original_hashes, candidatePNGs=png_hashes, metadataSHA256s=meta_hashes,
        protectedIdlePhysicalFrames=len(old_pixels), newPhysicalFrames=len(new_frames),
        cloudGeneration=dict(tool='OpenAI image_gen', output='back-walk-cloud.png', sha256=digest(HERE/'back-walk-cloud.png'),
                             prompt='back-walk.prompt.txt', scope='four rear-walk calves/boots only'))
    write_json(HERE / 'prepare-report.json', report)
    print(json.dumps({key: report[key] for key in ['status','frames','actions','pngCount','protectedIdlePhysicalFrames']}), flush=True)


def install():
    report = json.loads((HERE / 'prepare-report.json').read_text('utf-8'))
    review = json.loads((HERE / 'art-review.json').read_text('utf-8'))
    if review.get('status') != 'accepted' or review.get('candidateManifestSHA256') != report['candidateManifestSHA256']:
        raise ValueError('A matching candidate art review is required')
    if digest(ACTOR/'manifest.json') != report['sourceManifestSHA256']:
        raise ValueError('Runtime manifest changed since preparation')
    for image, expected in report['sourcePNGs'].items():
        if digest(ACTOR/image) != expected or digest(str(ACTOR/image)+'.meta') != report['metadataSHA256s'][image]:
            raise ValueError('Source or metadata changed: ' + image)
        if digest(HERE/'candidate-runtime'/image) != report['candidatePNGs'][image]:
            raise ValueError('Candidate changed since preparation: ' + image)
    for image in report['candidatePNGs']:
        (ACTOR/image).write_bytes((HERE/'candidate-runtime'/image).read_bytes())
    (ACTOR/'manifest.json').write_bytes((HERE/'candidate-runtime/manifest.json').read_bytes())
    write_json(HERE/'install-report.json', dict(status='installed; runtime verification pending',
        manifestSHA256=digest(ACTOR/'manifest.json'), pngCount=len(report['candidatePNGs']), metadataPreserved=True))
    print('Installed reviewed locomotion frames; all existing metadata/UUIDs retained.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', action='store_true')
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        prepare_candidate()
    elif args.install:
        install()
    else:
        pilot()
