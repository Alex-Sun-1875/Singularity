"""Conservatively remove tiny disconnected head-edit remnants from native crops.

Default: prepare a 48-frame pilot only. --all is required for a complete pass.
--input-edits accepts existing edit JSONs; their absolute cropPath, origin and
newFactor are retained, and cleaned crops become another non-installed edit set.
No resampling, connected-body erasure, runtime installation or model inference.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
V3 = HERE.parent / 'local-qwen21-unified-v3'
V4 = HERE.parent / 'body-scale-v4'
spec = importlib.util.spec_from_file_location('head_edge_inventory', V3 / 'prepare.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)
CONNECTED = np.ones((3, 3), dtype=bool)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def pixel_hash(image):
    return hashlib.sha256(image.tobytes()).hexdigest()


def load_inputs(paths, frames):
    edits = {}
    for path in paths:
        path = path.resolve()
        rows = read(path)
        if isinstance(rows, dict):
            rows = rows.get('edits', [rows])
        for original in rows:
            row = copy.deepcopy(original)
            key = row['image'], row['index']
            if key not in frames:
                raise ValueError('Unknown input physical frame: ' + str(key))
            if key in edits:
                raise ValueError('Duplicate input physical frame: ' + str(key))
            row['cropPath'] = str((path.parent / row['cropPath']).resolve())
            if len(row['origin']) != 2 or not all(math.isfinite(v) for v in row['origin']):
                raise ValueError('Invalid origin: ' + str(key))
            edits[key] = row
    return edits


def effective_record(record, edit, manifest):
    result = copy.deepcopy(record)
    if edit:
        old_factor = manifest.get('frameScaleFactors', {}).get(record['image'].removesuffix('.png'), [])
        old_factor = old_factor[record['index']] if len(old_factor) > record['index'] else 1
        factor = edit.get('newFactor', old_factor)
        if not math.isfinite(factor) or factor <= 0:
            raise ValueError('Invalid newFactor')
        result['scale'] *= factor / old_factor
        result['origin'] = edit['origin']
    return result


def locate_hair(image, record, historical):
    """Search the COMPLETE crop, including sideways and out-of-window heads."""
    a = np.asarray(image)
    rgb = a[..., :3].astype(float)
    scale = record['scale']
    seed = (a[..., 3] >= 180) & (rgb.min(-1) > 100) & (rgb.max(-1) - rgb.min(-1) < 42)
    radius = max(1, round(1.3 / scale))
    seed = ndi.binary_opening(seed, iterations=radius)
    seed = ndi.binary_closing(seed, iterations=radius)
    labels, _ = ndi.label(seed, CONNECTED)
    prior = historical.get((record['image'], record['index']))
    prior_point = None
    if prior:
        center = np.asarray(prior['hair']['center'])
        prior_point = np.asarray(record['origin']) + (center - [256, 712]) / prior['oldScale']
    candidates = []
    for label, sl in enumerate(ndi.find_objects(labels), 1):
        if sl is None:
            continue
        yy, xx = sl
        w, h = (xx.stop - xx.start) * scale, (yy.stop - yy.start) * scale
        local = labels[sl] == label
        area = int(local.sum()) * scale * scale
        if area < 80 or area > 11000 or min(w, h) < 13 or max(w, h) > 160 or max(w / h, h / w) > 3.2:
            continue
        center = np.array([(xx.start + xx.stop) / 2, (yy.start + yy.stop) / 2])
        prior_distance = np.linalg.norm(center - prior_point) * scale if prior_point is not None else None
        # A spell glow or pale cuff can be larger/brighter than the hair. The
        # historical full-crop location is reliable enough to reject those,
        # while allowing substantial local head/upper-body pose corrections.
        if prior_distance is not None and prior_distance > 145:
            continue
        brightness = float(rgb[sl][local].mean())
        texture = float(rgb[sl][local].mean(-1).std())
        proximity = math.exp(-((np.linalg.norm(center - prior_point) * scale / 130) ** 2)) if prior_point is not None else 1
        score = area * (brightness / 145) ** 3 * max(.25, min(texture / 18, 2)) * (.15 + .85 * proximity)
        candidates.append((score, label, [xx.start, yy.start, xx.stop, yy.stop], center, prior_distance))
    if not candidates:
        return None
    score, label, box, center, prior_distance = max(candidates, key=lambda row: row[0])
    return dict(box=box, center=center, mask=labels == label, score=score,
                priorDistanceReviewPixels=float(prior_distance) if prior_distance is not None else None,
                method='full-native-crop silver-hair components; historical prior only ranks candidates')


def weapon_guard(array, scale):
    """Protect existing long neutral blade/shaft components near the head."""
    rgb = array[..., :3].astype(float)
    metal = (array[..., 3] >= 32) & (rgb.max(-1) - rgb.min(-1) < 36) & (rgb.mean(-1) > 115)
    metal = ndi.binary_closing(metal, iterations=max(1, round(1.5 / scale)))
    labels, _ = ndi.label(metal, CONNECTED)
    guard = np.zeros(array.shape[:2], bool)
    for label, sl in enumerate(ndi.find_objects(labels), 1):
        if sl is None:
            continue
        yy, xx = sl
        w, h = (xx.stop - xx.start) * scale, (yy.stop - yy.start) * scale
        if max(w, h) >= 65 and max(w / max(h, .01), h / max(w, .01)) >= 4:
            guard[sl] |= labels[sl] == label
    return ndi.binary_dilation(guard, iterations=max(1, round(6 / scale)))


def clean(image, record, historical, max_area=150, visible_islands=False):
    original = np.asarray(image).copy()
    a = original
    scale = record['scale']
    hair = locate_hair(image, record, historical)
    empty = np.zeros(a.shape[:2], bool)
    if hair is None:
        return image.copy(), empty, dict(status='source-preserved', reason='no reliable full-crop hair component', removed=[])
    cx, cy = hair['center']
    rgb = a[..., :3].astype(float)
    rr, gg, bb = np.moveaxis(rgb, -1, 0)
    yy, xx = np.mgrid[:image.height, :image.width]
    dx, dy = (xx - cx) * scale, (yy - cy) * scale
    distance = dx * dx + dy * dy
    wine = (rr > gg + 8) & (rr > bb + 10) & (gg - bb < 15) & (a[..., 3] >= 128)
    nearby_cloth = wine & (distance > 25 ** 2) & (distance < 170 ** 2)
    if nearby_cloth.sum() >= 8:
        weights = 1 / (distance[nearby_cloth] + 100)
        axis = np.array([(dx[nearby_cloth] * weights).sum(), (dy[nearby_cloth] * weights).sum()]) / weights.sum()
        axis /= max(np.linalg.norm(axis), .001)
    else:
        axis = np.array([0., 1.])
    along = dx * axis[0] + dy * axis[1]
    across = -dx * axis[1] + dy * axis[0]
    # An oriented head/neck neighborhood also handles lying frames. It does
    # not assume that every head is in an upright 512x768 viewport.
    near = (along >= -75) & (along <= 135) & (abs(across) <= 78) & (distance <= 145 ** 2)
    core = ndi.binary_dilation(hair['mask'], iterations=max(1, round(4 / scale)))
    weapons = weapon_guard(a, scale)
    # Label alpha>0, not merely alpha>=16: even faint bridges to the body
    # preserve a connected contour. Never cut a small shape off the main body.
    labels, count = ndi.label(a[..., 3] > 0, CONNECTED)
    sizes = np.bincount(labels.ravel())
    main_label = int(np.argmax(sizes[1:]) + 1) if count else 0
    removed, preserved, erase = [], [], np.zeros(a.shape[:2], bool)
    for label, sl in enumerate(ndi.find_objects(labels), 1):
        if sl is None or label == main_label:
            continue
        region = labels[sl] == label
        visible = region & (a[sl][..., 3] >= 16)
        visible_area = int(visible.sum()) * scale * scale
        full_area = int(region.sum()) * scale * scale
        if not visible.any() or visible_area > max_area or full_area > max_area * 2:
            continue
        if not np.all(near[sl][region]):
            continue
        yslice, xslice = sl
        bounds = [xslice.start, yslice.start, xslice.stop, yslice.stop]
        w, h = (xslice.stop - xslice.start) * scale, (yslice.stop - yslice.start) * scale
        values = rgb[sl][visible]
        med = np.median(values, axis=0)
        row = dict(component=label, nativeBox=bounds, visibleAreaReviewPixelsSquared=visible_area,
                   fullAlphaAreaReviewPixelsSquared=full_area, medianRGB=med.tolist(), maxAlpha=int(a[sl][..., 3][region].max()))
        reason = None
        if np.any(core[sl][region]):
            reason = 'silver-hair core/wisp proximity protected'
        elif np.any(weapons[sl][region]):
            reason = 'existing long blade/shaft proximity protected'
        elif max(w, h) > 42 or max(w / max(h, .01), h / max(w, .01)) > 3.6:
            reason = 'elongated or large accessory-like component protected'
        else:
            r, g, b = med
            neutral = max(med) - min(med) < 36 and 55 <= med.mean() <= 230
            skin = r > g + 8 and g > b + 3 and r > 65 and g > 45
            gold = r > g + 20 and g > b + 32
            if gold:
                reason = 'warm gold/ornament component protected'
            elif not (neutral or skin):
                reason = 'not a skin/neutral head-edit remnant'
        if reason:
            preserved.append(dict(row, reason=reason))
            continue
        erase[sl] |= region
        removed.append(dict(row, reason='tiny fully disconnected skin/neutral component in head/neck neighborhood'))
    # The shader discards alpha<16. Earlier head compositing left a few visible
    # fragments connected to the body only by that invisible alpha residue.
    # An explicit second pass may remove those rendered islands plus at most
    # two native pixels of their low-alpha halo, never visible main-body pixels.
    visible_labels, visible_count = ndi.label(a[..., 3] >= 16, CONNECTED)
    visible_sizes = np.bincount(visible_labels.ravel())
    visible_main_label = int(np.argmax(visible_sizes[1:]) + 1) if visible_count else 0
    visible_main = visible_labels == visible_main_label
    if visible_islands:
        for label, sl in enumerate(ndi.find_objects(visible_labels), 1):
            if sl is None or label == visible_main_label:
                continue
            region = visible_labels[sl] == label
            visible_area = int(region.sum()) * scale * scale
            if visible_area > max_area or np.all(erase[sl][region]) or not np.all(near[sl][region]):
                continue
            yslice, xslice = sl
            bounds = [xslice.start, yslice.start, xslice.stop, yslice.stop]
            w, h = (xslice.stop - xslice.start) * scale, (yslice.stop - yslice.start) * scale
            med = np.median(rgb[sl][region], axis=0)
            row = dict(component=label, nativeBox=bounds, visibleAreaReviewPixelsSquared=visible_area,
                       medianRGB=med.tolist(), maxAlpha=int(a[sl][..., 3][region].max()),
                       connectivityThreshold=16)
            r, g, b = med
            neutral = max(med) - min(med) < 36 and 55 <= med.mean() <= 230
            skin = r > g + 8 and g > b + 3 and r > 65 and g > 45
            gold = r > g + 20 and g > b + 32
            reason = None
            if np.any(core[sl][region]):
                reason = 'silver-hair core/wisp proximity protected'
            elif np.any(weapons[sl][region]):
                reason = 'existing long blade/shaft proximity protected'
            elif max(w, h) > 42 or max(w / max(h, .01), h / max(w, .01)) > 3.6:
                reason = 'elongated or large accessory-like component protected'
            elif gold or not (neutral or skin):
                reason = 'ornament or non-head material protected'
            if reason:
                preserved.append(dict(row, reason=reason))
                continue
            island = np.zeros(a.shape[:2], bool)
            island[sl] = region
            radius = max(1, min(2, round(2 / scale)))
            halo = ndi.binary_dilation(island, iterations=radius) & (a[..., 3] > 0) & (a[..., 3] < 16)
            halo &= ~ndi.binary_dilation(visible_main, iterations=1)
            selection = island | halo
            if np.any(selection & visible_main):
                raise RuntimeError('Rendered-island cleanup touched visible main body')
            erase |= selection
            removed.append(dict(row, reason='tiny rendered-disconnected head remnant; only invisible alpha bridge/halo also removed',
                                lowAlphaHaloNativePixels=int(halo.sum()), haloRadiusNativePixels=radius,
                                connectedAtAlphaAboveZero=bool(np.any((labels == main_label) & island))))
    result = a.copy()
    result[erase] = 0
    changed = np.any(result != a, axis=-1)
    if np.any(changed & ~erase) or np.any(erase & visible_main) or (not visible_islands and np.any(erase & (labels == main_label))):
        raise RuntimeError('Head cleanup escaped disconnected-component guard')
    return Image.fromarray(result), erase, dict(status='candidate' if removed else 'source-preserved',
        hairBox=hair['box'], hairCenter=hair['center'].tolist(), hairLocator=hair['method'],
        hairPriorDistanceReviewPixels=hair['priorDistanceReviewPixels'],
        neighborhoodAxis=axis.tolist(), removed=removed, preservedNearHeadComponents=preserved,
        changedNativePixels=int(changed.sum()), outsideRemovalMaskChanges=0,
        connectedVisibleMainBodyPixelChanges=0,
        rawMainComponentPixelsRemoved=int((erase & (labels == main_label)).sum()),
        visibleIslandPassEnabled=visible_islands, originalRGBA_SHA256=pixel_hash(image),
        candidateRGBA_SHA256=pixel_hash(Image.fromarray(result)))


def pilot_keys(frames):
    roles = [('attack_sword_W01', 0), ('attack_sword_W01', 1), ('attack_sword_W01', 3),
             ('idle_W08', 0), ('idle_L02', 0), ('explore_idle_W01', 0),
             ('walk_W01', 1), ('run_W01', 3), ('spell', 1), ('dodge', 2), ('hit', 1), ('death', 1)]
    keys = []
    for action, phase in roles:
        for direction in prepare.DIRECTIONS:
            record = next((r for r in frames.values() if any(v == dict(action=action, direction=direction, phase=phase) for v in r['refs'])), None)
            if record:
                keys.append((record['image'], record['index']))
    return list(dict.fromkeys(keys))


def make_board(rows, output):
    for page_number, start in enumerate(range(0, len(rows), 8)):
        selected = rows[start:start + 8]
        board = Image.new('RGB', (900, len(selected) * 145), '#25272a')
        draw = ImageDraw.Draw(board)
        for number, row in enumerate(selected):
            report, before, after, mask, record = row
            center = report.get('hairCenter', [before.width / 2, before.height / 4])
            size_world = 190
            size_native = size_world / record['scale']
            box = [center[0] - size_native / 2, center[1] - size_native / 2,
                   center[0] + size_native / 2, center[1] + size_native / 2]
            for column, image in enumerate([before, after, Image.fromarray(np.uint8(mask) * 255).convert('RGBA')]):
                picture = image.crop(box).resize((140, 140), Image.Resampling.NEAREST)
                x, y = column * 150, number * 145
                board.paste(picture, (x, y), picture)
            label = record['action'] + ' ' + record['direction'] + ' #' + str(record['index'])
            draw.text((460, number * 145 + 8), label[:54], fill='white')
            draw.text((460, number * 145 + 28), 'before / cleaned / removal mask', fill='#acbac5')
            draw.text((460, number * 145 + 48), f"removed {len(report['removed'])} isolated components", fill='#e1bd6b')
        board.save(output / f'head-edge-review-{page_number:02}.jpg', quality=91)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-edits', type=Path, nargs='*', default=[])
    parser.add_argument('--all', action='store_true', help='Explicitly process all 996 physical frames')
    parser.add_argument('--output', type=Path, default=None)
    parser.add_argument('--max-area', type=float, default=150, help='Maximum visible component area at 400px/world')
    parser.add_argument('--visible-islands', action='store_true',
                        help='Also remove rendered alpha>=16 islands with only invisible bridges; protect visible main body')
    args = parser.parse_args()
    manifest = read(prepare.MANIFEST)
    frames = prepare.inventory(manifest)
    input_edits = load_inputs(args.input_edits, frames)
    old = {(r['image'], r['index']): r for r in read(V4 / 'inventory.json')['frames']}
    historical = {}
    for row in read(V3 / 'head-locations.json')['frames']:
        key = row['image'], row['index']
        if key in old:
            historical[key] = dict(hair=row['hair'], oldScale=old[key]['scale'])
    output = (args.output or HERE / ('head-edge-cleaned' if args.all else 'head-edge-pilot')).resolve()
    (output / 'frames').mkdir(parents=True, exist_ok=True)
    keys = list(frames) if args.all else pilot_keys(frames)
    sheets, reports, edits, boards = {}, [], [], []
    source_manifest_sha = prepare.digest(prepare.MANIFEST)
    for key in keys:
        source_record = frames[key]
        incoming = input_edits.get(key)
        record = effective_record(source_record, incoming, manifest)
        if incoming:
            before = Image.open(incoming['cropPath']).convert('RGBA')
        else:
            name = source_record['image']
            if name not in sheets:
                sheets[name] = Image.open(prepare.ACTOR / name).convert('RGBA')
            x, y, w, h = source_record['rect']
            before = sheets[name].crop((x, y, x + w, y + h))
        after, mask, report = clean(before, record, historical, args.max_area, args.visible_islands)
        report.update(image=key[0], index=key[1], direction=record['direction'],
                      action=record['action'], refs=record['refs'], effectiveUPP=record['scale'] / 400,
                      inputCropPath=incoming['cropPath'] if incoming else None)
        reports.append(report)
        if report['removed']:
            filename = key[0].replace('/', '__').removesuffix('.png') + f'--{key[1]:02}.png'
            path = output / 'frames' / filename
            after.save(path)
            edit = copy.deepcopy(incoming) if incoming else dict(image=key[0], index=key[1], origin=record['origin'])
            edit.update(cropPath=str(path), sourceManifestSHA256=source_manifest_sha,
                        headEdgeCleanup=dict(report=str(output / 'report.json'), removedComponents=len(report['removed'])))
            edits.append(edit)
        elif incoming:
            edits.append(copy.deepcopy(incoming))
        if not args.all or report['removed']:
            boards.append((report, before, after, mask, record))
    if prepare.digest(prepare.MANIFEST) != source_manifest_sha:
        raise RuntimeError('Runtime manifest changed while preparing cleanup')
    make_board(boards[:64], output)
    write(output / 'edits.json', dict(edits=edits))
    summary = dict(status='candidate-only; visual review required', mode='all' if args.all else '48-frame pilot',
        framesExamined=len(keys), inputEdits=len(input_edits), outputEdits=len(edits),
        changedFrames=sum(bool(row['removed']) for row in reports),
        removedComponents=sum(len(row['removed']) for row in reports),
        removedNativePixels=sum(row.get('changedNativePixels', 0) for row in reports),
        maxVisibleAreaReviewPixelsSquared=args.max_area, sourceManifestSHA256=source_manifest_sha,
        visibleIslandPassEnabled=args.visible_islands,
        guard='eight-connected components; alpha>=16 visible main body, hair core, long weapons and gold ornaments protected; optional invisible halo limited to 1-2 native pixels',
        sourceAssetsModified=False, modelInference=False, artApproval='pending manual review',
        frames=reports)
    write(output / 'report.json', summary)
    print(json.dumps({key: summary[key] for key in ('mode', 'framesExamined', 'outputEdits', 'changedFrames', 'removedComponents', 'removedNativePixels')}))


if __name__ == '__main__':
    main()
