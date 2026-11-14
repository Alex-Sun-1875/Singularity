"""Pack reviewed native frame edits without resampling other character pixels.

Prepare: python pack.py [--source ACTOR_DIR] [--edits EDITS_DIR]
Install the already reviewed candidate: python pack.py --install

Each edits/*.json may contain one edit, an array, or {"edits": [...]}.
An edit has image, index, cropPath, origin:[x,y], and optional newFactor.
cropPath is relative to that JSON file; origin is local to the native crop.
Preparation and pixel validation do not constitute visual/art approval.
"""
from pathlib import Path
import argparse
import collections
import copy
import hashlib
import importlib.util
import json
import math
import os
import shutil
import sys

sys.dont_write_bytecode = True
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DEFAULT_SOURCE = ROOT / 'src/cocos/assets/resources/flat2d/characters/raphael'
MAX_SIZE = 2048
PADDING = 2

# Reuse the project's authoritative physical-frame/alias inventory. Its module
# only imports existing image dependencies and has no execution side effects.
spec = importlib.util.spec_from_file_location(
    'identity_v5_existing_inventory', HERE.parent / 'local-qwen21-unified-v3/prepare.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    return prepare.digest(path)


def optional_digest(path):
    return digest(path) if Path(path).is_file() else None


def pixel_digest(crop):
    return hashlib.sha256(crop.tobytes()).hexdigest()


def within(root, name):
    path = (Path(root) / name).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError('Path escapes its asset directory: ' + str(name))
    return path


def image_key(name):
    return str(name).replace('\\', '/').removeprefix('./').removesuffix('.png')


def alpha_bounds(crop, threshold=16):
    bounds = crop.getchannel('A').point(lambda a: 255 if a >= threshold else 0).getbbox()
    return list(bounds) if bounds else [0, 0, 0, 0]


def source_inventory(source, manifest_path, manifest):
    frames = prepare.inventory(manifest)
    images = []
    for name in sorted({key[0] for key in frames}):
        path = within(source, name)
        with Image.open(path) as im:
            size = list(im.size)
        images.append(dict(image=name, sha256=digest(path), size=size,
                           metaSHA256=optional_digest(str(path) + '.meta')))
    return dict(source=str(source), manifest=str(manifest_path),
                manifestSHA256=digest(manifest_path),
                manifestMetaSHA256=optional_digest(str(manifest_path) + '.meta'),
                actions=len(manifest['actions']), physicalFrames=len(frames),
                images=images, frames=list(frames.values()))


def load_edits(directory, frames):
    names = {image_key(name): name for name, _ in frames}
    edits = {}
    if not directory.is_dir():
        raise ValueError('Missing edits directory: ' + str(directory))
    for path in sorted(directory.glob('*.json')):
        rows = read_json(path)
        if isinstance(rows, dict):
            rows = rows['edits'] if 'edits' in rows else [rows]
        if not isinstance(rows, list):
            raise ValueError('Expected edit object or list: ' + str(path))
        for row in rows:
            name = names.get(image_key(row['image']))
            index = row['index']
            if isinstance(index, bool) or not isinstance(index, int) or (name, index) not in frames:
                raise ValueError('Unknown physical frame: ' + str((row['image'], index)))
            key = name, index
            if key in edits:
                raise ValueError('Duplicate edit for ' + str(key))
            origin = row['origin']
            if not isinstance(origin, list) or len(origin) != 2 or any(
                    isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in origin):
                raise ValueError('origin must be two finite native-pixel coordinates: ' + str(key))
            factor = row.get('newFactor')
            if factor is not None and (isinstance(factor, bool) or not isinstance(factor, (int, float))
                                       or not math.isfinite(factor) or factor <= 0):
                raise ValueError('newFactor must be positive and finite: ' + str(key))
            crop_path = (path.parent / row['cropPath']).resolve()
            with Image.open(crop_path) as im:
                crop = im.convert('RGBA')
            # Leg calibration intentionally expands working canvases to avoid
            # clipping a moving head. Trim only fully transparent outer space
            # before packing, retaining every nonzero-alpha RGBA pixel and a
            # two-pixel filter gutter; compensate the local anchor exactly.
            before_size = list(crop.size)
            bounds = crop.getchannel('A').getbbox()
            trim = [0, 0, crop.width, crop.height]
            if bounds:
                trim = [max(0, bounds[0]-PADDING), max(0, bounds[1]-PADDING),
                        min(crop.width, bounds[2]+PADDING), min(crop.height, bounds[3]+PADDING)]
                crop = crop.crop(tuple(trim))
                origin = [origin[0]-trim[0], origin[1]-trim[1]]
            if min(crop.size) <= 0 or max(crop.size) + PADDING * 2 > MAX_SIZE:
                raise ValueError('Native crop exceeds atlas budget: ' + str(key))
            edits[key] = dict(crop=crop, origin=origin, newFactor=factor,
                              transparentWorkingCanvasTrim=dict(inputSize=before_size, box=trim),
                              cropPath=str(crop_path), cropSHA256=digest(crop_path),
                              editJSON=str(path), editJSONSHA256=digest(path))
    if not edits:
        raise ValueError('No edits found in ' + str(directory))
    return edits


def separated(rect, existing, gap=PADDING * 2):
    x, y, w, h = rect
    return all(x + w + gap <= ox or ox + ow + gap <= x or
               y + h + gap <= oy or oy + oh + gap <= y
               for ox, oy, ow, oh in existing)


def original_placements(items, columns, source_size):
    """Adapt the existing phase-packer's original-coordinate/gutter strategy."""
    for gutter in (0, 4, 8, 16, 32, 64, 96, 128, 192):
        raw = {}
        for item in items:
            r = item['record']
            # Retain the old atlas-space foot location as closely as possible.
            x = round(r['absolute_anchor'][0] - item['origin'][0])
            y = round(r['absolute_anchor'][1] - item['origin'][1])
            raw[r['index']] = (x + (r['index'] % columns) * gutter,
                               y + (r['index'] // columns) * gutter)
        left = max(PADDING, PADDING - min(x for x, _ in raw.values()))
        top = max(PADDING, PADDING - min(y for _, y in raw.values()))
        rects, placed = [], {}
        for item in items:
            x, y = raw[item['record']['index']]
            rect = [x + left, y + top, *item['crop'].size]
            if not separated(rect, rects):
                break
            rects.append(rect)
            placed[item['record']['index']] = rect
        else:
            width = max(source_size[0] + left, max(x + w + PADDING for x, y, w, h in rects))
            height = max(source_size[1] + top, max(y + h + PADDING for x, y, w, h in rects))
            if max(width, height) <= MAX_SIZE:
                return placed, (width, height), dict(method='original-coordinates-plus-gutter', gutter=gutter)
    return None


def shelf_placements(items):
    """Deterministic first-fit decreasing-height shelves; no rotation/resizing."""
    ordered = sorted(items, key=lambda item: (-item['crop'].height, -item['crop'].width,
                                            item['record']['index']))
    minimum = max(item['crop'].width + 2 * PADDING for item in ordered)
    solutions = []
    for width in sorted({minimum, MAX_SIZE, *range(512, MAX_SIZE + 1, 128)}):
        if width < minimum or width > MAX_SIZE:
            continue
        shelves, placed = [], {}
        for item in ordered:
            w, h = item['crop'].size
            shelf = next((s for s in shelves if s['height'] >= h + 2 * PADDING
                          and s['x'] + w + 2 * PADDING <= width), None)
            if shelf is None:
                y = sum(s['height'] for s in shelves)
                if y + h + 2 * PADDING > MAX_SIZE:
                    break
                shelf = dict(x=0, y=y, height=h + 2 * PADDING)
                shelves.append(shelf)
            placed[item['record']['index']] = [shelf['x'] + PADDING, shelf['y'] + PADDING, w, h]
            shelf['x'] += w + 2 * PADDING
        else:
            height = sum(s['height'] for s in shelves)
            used_width = max(s['x'] for s in shelves)
            solutions.append((used_width * height, max(used_width, height), used_width,
                              height, placed, len(shelves)))
    if not solutions:
        raise RuntimeError('Native crops cannot fit one 2048px atlas without resizing')
    _, _, width, height, placed, shelves = min(solutions, key=lambda s: s[:4])
    return placed, (width, height), dict(method='first-fit-decreasing-height-shelves', shelves=shelves)


def update_manifest(manifest, frames, geometry, edited_images, factors, candidate, hashes):
    updated = copy.deepcopy(manifest)
    refs = {(v['action'], v['direction'], v['phase']): (r['image'], r['index'])
            for r in frames.values() for v in r['refs']}
    for key, action in updated['actions'].items():
        old = manifest['actions'][key]
        primary = old.get('image', manifest['image'])
        names = list(dict.fromkeys(old.get('frameImages', [primary])))
        if not any(name in edited_images for name in names):
            continue
        # Always materialize per-image rects for a multi-image action. A crop
        # from page B must not accidentally use page A's newly packed geometry.
        by_image = copy.deepcopy(old.get('frameRectsByImage', {}))
        for name in names:
            rects = copy.deepcopy(by_image.get(image_key(name), old.get('perFrameRects', [])))
            for (image, index), g in geometry.items():
                if image != name:
                    continue
                while len(rects) <= index:
                    rects.append(None)
                rects[index] = g['rect']
            by_image[image_key(name)] = rects
        action['perFrameRects'] = copy.deepcopy(by_image[image_key(primary)])
        action['frameRectsByImage'] = by_image
        alpha = copy.deepcopy(old.get('alphaBounds', []))
        for (image, index), g in geometry.items():
            if image == primary:
                while len(alpha) <= index:
                    alpha.append([0, 0, 0, 0])
                alpha[index] = g['bounds']
        action['alphaBounds'] = alpha
        count = len(old.get('frameIndices', [])) or old.get('frames', 1)
        # Per-direction phase origins represent different page A/B crop sizes
        # even when their physical indices coincide. This is native runtime API.
        origins, phase_alpha = {}, {}
        for direction in manifest['directions']:
            origins[direction], phase_alpha[direction] = [], []
            for phase in range(count):
                physical = refs[key, direction, phase]
                origins[direction].append(geometry[physical]['origin'])
                phase_alpha[direction].append(geometry[physical]['bounds'])
        action['perFrameOrigins'] = origins
        action['perPhaseAlphaBounds'] = phase_alpha
        action['originMethod'] = 'Native phase crops; exact unedited RGBA pixels; explicit local foot anchors; isolated atlas gutters.'
        action['sourcePNGs'] = [str(candidate / name) for name in names]
        action['sourcePNGSHA256s'] = [hashes[name] for name in names]
    # Root defaults are retained for consumers other than FlatActors too.
    primary = manifest['image']
    if primary in edited_images:
        for field, geometry_field in [('perFrameOrigins', 'origin'), ('alphaBounds', 'bounds')]:
            if isinstance(updated.get(field), list):
                for (image, index), g in geometry.items():
                    if image == primary and index < len(updated[field]):
                        updated[field][index] = g[geometry_field]
    for (name, index), factor in factors.items():
        values = updated.setdefault('frameScaleFactors', {}).setdefault(image_key(name), [])
        while len(values) <= index:
            values.append(1.0)
        values[index] = factor
    updated['revision'] = 'concept-image-2d-attack-identity-v5'
    updated['attackIdentityPacking'] = dict(report=str(HERE / 'pack-report.json'),
        editedPhysicalFrames=len([g for g in geometry.values() if g['edited']]),
        editedAtlases=len(edited_images), uneditedPixelsPreserved=True,
        maximumAtlasSize=MAX_SIZE, artApproval='pending visual review', extraOriginalBackups=False)
    return updated


def apply_provenance(manifest, path, report_path):
    """Apply appearance metadata only; never accept geometry from provenance."""
    metadata = read_json(path) if path.is_file() else {}
    if not isinstance(metadata, dict):
        raise ValueError('provenance.json must be an object')
    revision = metadata.get('revision', 'concept-image-2d-attack-identity-v5')
    reference = HERE / 'attack-model-reference.png'
    default_design = reference.relative_to(ROOT).as_posix() if reference.is_file() else None
    design = metadata.get('sourceDesign', default_design)
    identity = metadata.get('identityReference', design)
    scope = metadata.get('identityReferenceScope',
        'User image 3 / W01 sword-attack character is the current appearance authority; '
        'align idle, stowed, movement and action drawings to its identity, clothing and body proportions.')
    authority = metadata.get('appearanceAuthority', dict(
        identity='user image 3 / current W01 sword-attack character',
        clothing='user image 3 / current W01 sword-attack character',
        scale='current W01 sword-attack reference; preserve each pose and native support anchor'))
    if not isinstance(authority, dict):
        raise ValueError('appearanceAuthority must be an object')
    note = metadata.get('historicalBaselineNote',
        'Previous standing-identity and body-scale-v4 records are retained as processing history. '
        'Their appearance authority is superseded by the user-selected image-3 sword-attack reference.')
    common = dict(appearanceAuthority=authority, identityReferenceScope=scope)
    for field, value in [('sourceDesign', design), ('identityReference', identity)]:
        if value is None:
            continue
        ref = Path(value)
        ref = ref.resolve() if ref.is_absolute() else (ROOT / ref).resolve()
        if not ref.is_file():
            raise ValueError('Missing appearance authority reference: ' + str(ref))
        common[field] = ref.relative_to(ROOT).as_posix() if ref.is_relative_to(ROOT) else str(ref)
        common[field + 'SHA256'] = digest(ref)
    manifest['revision'] = revision
    manifest.update(copy.deepcopy(common))
    manifest['appearanceBaselineHistory'] = dict(supersededBy=revision, note=note)
    for action in manifest['actions'].values():
        action.update(copy.deepcopy(common))
        # These are processing provenance, not the current art specification.
        for field in ('localQwenProcessing', 'identityRunAuthority'):
            if isinstance(action.get(field), dict):
                action[field]['appearanceAuthorityStatus'] = 'historical; superseded by ' + revision
    for field in ('bodyScaleCalibration', 'localQwenInstall'):
        if isinstance(manifest.get(field), dict):
            manifest[field]['appearanceAuthorityStatus'] = 'historical; superseded by ' + revision
            manifest[field]['currentAppearanceBaseline'] = note
    manifest['attackIdentityPacking']['report'] = str(report_path.resolve())
    manifest['attackIdentityPacking']['provenance'] = str(path.resolve()) if path.is_file() else None
    manifest['attackIdentityPacking']['provenanceSHA256'] = digest(path) if path.is_file() else None
    if isinstance(metadata.get('artApproval'), str):
        manifest['attackIdentityPacking']['artApproval'] = metadata['artApproval']
        approval = metadata.get('artApprovalReport')
        if approval:
            approval_path = (ROOT / approval).resolve()
            if not approval_path.is_file():
                raise ValueError('Missing art approval report: ' + str(approval_path))
            manifest['attackIdentityPacking']['artApprovalReport'] = approval
            manifest['attackIdentityPacking']['artApprovalReportSHA256'] = digest(approval_path)
    return manifest


def build(args):
    source = args.source.resolve()
    manifest_path = (args.manifest or source / 'manifest.json').resolve()
    candidate = args.output.resolve()
    if candidate.is_relative_to(source) or source.is_relative_to(candidate):
        raise ValueError('Candidate and runtime source must be separate directories')
    manifest = read_json(manifest_path)
    inv = source_inventory(source, manifest_path, manifest)
    frames = {(r['image'], r['index']): r for r in inv['frames']}
    edits = load_edits(args.edits.resolve(), frames)
    edited_images = {key[0] for key in edits}
    grouped = collections.defaultdict(list)
    for record in frames.values():
        grouped[record['image']].append(record)
    candidate.mkdir(parents=True, exist_ok=True)
    geometry, image_reports, factors = {}, [], {}
    for name, records in grouped.items():
        path, dest = within(source, name), within(candidate, name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(path) as im:
            original = im.convert('RGBA')
        items = []
        for r in sorted(records, key=lambda row: row['index']):
            edit = edits.get((name, r['index']))
            x, y, w, h = r['rect']
            crop = edit['crop'] if edit else original.crop((x, y, x + w, y + h))
            origin = edit['origin'] if edit else r['origin']
            items.append(dict(record=r, crop=crop, origin=origin, edited=bool(edit)))
            if edit and edit['newFactor'] is not None:
                factors[name, r['index']] = edit['newFactor']
        if name in edited_images:
            action = manifest['actions'][records[0]['action']]
            placement = original_placements(items, action.get('columns', manifest['columns']), original.size)
            placed, size, method = placement or shelf_placements(items)
            page = Image.new('RGBA', size)
            for item in items:
                rect = placed[item['record']['index']]
                # No mask: preserve all RGBA bytes, including antialiased alpha.
                page.paste(item['crop'], tuple(rect[:2]))
            page.save(dest)
        else:
            shutil.copyfile(path, dest)
            page, method = original, dict(method='original-file-byte-copy')
            placed = {r['index']: r['rect'] for r in records}
        meta = Path(str(path) + '.meta')
        if meta.is_file():
            shutil.copyfile(meta, str(dest) + '.meta')
        # Reopen the actual saved PNG, not just the in-memory page.
        with Image.open(dest) as im:
            saved = im.convert('RGBA')
        for item in items:
            r, crop = item['record'], item['crop']
            x, y, w, h = placed[r['index']]
            sample = saved.crop((x, y, x + w, y + h))
            if sample.size != crop.size or sample.tobytes() != crop.tobytes():
                raise RuntimeError('Packed crop changed RGBA bytes: ' + str((name, r['index'])))
            geometry[name, r['index']] = dict(rect=[x, y, w, h], origin=item['origin'],
                bounds=alpha_bounds(crop), edited=item['edited'], pixelSHA256=pixel_digest(crop))
        image_reports.append(dict(image=name, beforeSHA256=digest(path), afterSHA256=digest(dest),
                                  originalSize=list(original.size), size=list(saved.size), **method))
    hashes = {r['image']: r['afterSHA256'] for r in image_reports}
    updated = update_manifest(manifest, frames, geometry, edited_images, factors, candidate, hashes)
    updated = apply_provenance(updated, args.provenance.resolve(), args.report)
    candidate_manifest = candidate / 'manifest.json'
    write_json(candidate_manifest, updated)
    if Path(str(manifest_path) + '.meta').is_file():
        shutil.copyfile(str(manifest_path) + '.meta', str(candidate_manifest) + '.meta')
    candidate_frames = prepare.inventory(updated)
    if set(candidate_frames) != set(frames):
        raise RuntimeError('Physical frame coverage changed')
    for key, row in candidate_frames.items():
        if row['rect'] != geometry[key]['rect'] or row['origin'] != geometry[key]['origin']:
            raise RuntimeError('Alias geometry validation failed: ' + str(key))
    write_json(args.inventory, inv)
    write_json(candidate / 'inventory.json', dict(sourceManifestSHA256=inv['manifestSHA256'],
               manifestSHA256=digest(candidate_manifest), frames=list(candidate_frames.values())))
    edit_records = [dict(image=key[0], index=key[1], **{k: v for k, v in edit.items() if k != 'crop'})
                    for key, edit in edits.items()]
    report = dict(status='prepared', source=str(source), sourceManifest=str(manifest_path),
        candidate=str(candidate), sourceInventory=str(args.inventory.resolve()),
        candidateManifestSHA256=digest(candidate_manifest),
        generationStatus='No generation performed by this packer', artApproval=updated['attackIdentityPacking']['artApproval'],
        actions=len(updated['actions']), physicalFrames=len(frames), editedFrames=len(edits),
        editedAtlases=len(edited_images), extraOriginalBackups=False,
        invariants=dict(uneditedRGBAExact=True, aliasesConsistent=True, noResampling=True,
                        originalMetadataPreserved=True, maximumAtlasSize=MAX_SIZE),
        edits=edit_records, images=image_reports,
        frames=[dict(image=key[0], index=key[1], **g) for key, g in geometry.items()])
    write_json(args.report, report)
    print(json.dumps({k: report[k] for k in ('status', 'actions', 'physicalFrames', 'editedFrames', 'editedAtlases')}, ensure_ascii=False))


def install(args):
    report = read_json(args.report)
    inv = read_json(report['sourceInventory'])
    source, manifest_path, candidate = Path(inv['source']), Path(inv['manifest']), Path(report['candidate'])
    if digest(manifest_path) != inv['manifestSHA256']:
        raise RuntimeError('Runtime manifest changed after candidate preparation')
    if optional_digest(str(manifest_path) + '.meta') != inv['manifestMetaSHA256']:
        raise RuntimeError('Runtime manifest metadata changed')
    for row in inv['images']:
        path = within(source, row['image'])
        if digest(path) != row['sha256'] or optional_digest(str(path) + '.meta') != row['metaSHA256']:
            raise RuntimeError('Runtime source or metadata changed: ' + row['image'])
    if digest(candidate / 'manifest.json') != report['candidateManifestSHA256']:
        raise RuntimeError('Candidate manifest changed after validation')
    paths = []
    for row in report['images']:
        path = within(candidate, row['image'])
        if digest(path) != row['afterSHA256']:
            raise RuntimeError('Candidate atlas changed after validation: ' + row['image'])
        if row['beforeSHA256'] != row['afterSHA256']:
            paths.append((within(source, row['image']), path))
    paths.append((manifest_path, candidate / 'manifest.json'))
    # Stage only new bytes beside their target, then replace. No original-file
    # backups are made, and neither source nor candidate .meta is installed.
    staged = []
    try:
        for dest, src in paths:
            stage = dest.with_name(dest.name + '.identity-v5-stage')
            stage.write_bytes(src.read_bytes())
            staged.append((dest, stage, digest(src)))
        for dest, stage, expected in staged:
            os.replace(stage, dest)
            if digest(dest) != expected:
                raise RuntimeError('Installed bytes failed verification: ' + str(dest))
    finally:
        for _, stage, _ in staged:
            if stage.is_file():
                stage.unlink()
    for row in inv['images']:
        if optional_digest(str(within(source, row['image'])) + '.meta') != row['metaSHA256']:
            raise RuntimeError('Runtime metadata changed during installation')
    if optional_digest(str(manifest_path) + '.meta') != inv['manifestMetaSHA256']:
        raise RuntimeError('Manifest metadata changed during installation')
    report.update(status='installed', installedManifestSHA256=digest(manifest_path))
    write_json(args.report, report)
    print(json.dumps(dict(status='installed', replacedAtlases=len(paths) - 1,
                          extraOriginalBackups=False, metadataPreserved=True)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--manifest', type=Path, default=None)
    parser.add_argument('--edits', type=Path, default=HERE / 'edits')
    parser.add_argument('--output', type=Path, default=HERE / 'candidate-runtime')
    parser.add_argument('--inventory', type=Path, default=HERE / 'inventory.json')
    parser.add_argument('--report', type=Path, default=HERE / 'pack-report.json')
    parser.add_argument('--provenance', type=Path, default=HERE / 'provenance.json',
                        help='Optional appearance-authority metadata; cannot change action geometry')
    parser.add_argument('--install', action='store_true', help='Install the existing validated candidate; does not rebuild it')
    arguments = parser.parse_args()
    install(arguments) if arguments.install else build(arguments)
