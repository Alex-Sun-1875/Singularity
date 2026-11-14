"""Register native accessory edits using existing alpha measurements; never write pixels."""
from pathlib import Path
from PIL import Image
import ast, copy, hashlib, json, shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCES = HERE / 'sources/advanced'
RUNTIME = ROOT / 'src/cocos/assets/resources/flat2d/characters/raphael/hero-v4'
META = HERE / 'metadata-advanced.json'
baseline = json.loads((HERE / 'metadata-advanced-before-quiver-v2.json').read_text(encoding='utf-8'))
data = json.loads(META.read_text(encoding='utf-8'))
assert data == baseline, 'Unexpected concurrent metadata change; stop before overwriting'

# Reuse the existing read-only alpha geometry functions without executing its installer.
tree = ast.parse((HERE / 'measure-advanced.py').read_text(encoding='utf-8'))
functions = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)], type_ignores=[])
exec(compile(functions, '<existing-alpha-functions>', 'exec'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def body_measure(mask, rect, row, col):
    # Narrow head search excludes the new quiver/arrow tips; lower-body reads exclude the bow.
    cx = col * 256 + [130, 126, 130, 116][row]
    ry = row * 384
    ys = [y for y in range(ry, ry + 100)
          if sum(bool(mask.getpixel((x, y))) for x in range(cx - 15, cx + 16)) >= 5]
    waist = []
    for y in range(ry + 155, ry + 185):
        xs = [x for x in range(cx - 30, cx + 31) if mask.getpixel((x, y))]
        if xs:
            waist.append((min(xs) + max(xs)) / 2)
    return {'headTop': min(ys), 'waistCoreX': sum(waist) / len(waist)}

report = {'scope': 'W08/L02 idle and walk quiver continuity only', 'images': {}, 'unchangedActions': []}
allowed_fields = {'image', 'perFrameRects', 'perFrameOrigins', 'alphaBounds', 'sourcePNG', 'sourcePNGSHA256'}
for item in ['W08', 'L02']:
    old_name = f'{item}-walk-readable.png'
    new_name = f'{item}-walk-readable-v2.png'
    old_path, new_path = SOURCES / old_name, SOURCES / new_name
    old_im, new_im = Image.open(old_path), Image.open(new_path)
    assert new_im.mode == 'RGBA' and new_im.size == old_im.size == (1024, 1536)
    old_alpha, new_alpha = old_im.getchannel('A'), new_im.getchannel('A')
    old_mask = old_alpha.point(lambda v: 255 if v > 32 else 0)
    new_mask = new_alpha.point(lambda v: 255 if v > 32 else 0)
    old_rects, old_bbs, _ = measure_rects(old_mask)
    rects, bbs, gutters = measure_rects(new_mask)
    old_action = baseline['actions']['walk_' + item]
    origins, absolute_ground, drift = [], [], []
    for idx, (rect, bb, old_rect, old_bb) in enumerate(zip(rects, bbs, old_rects, old_bbs)):
        row, col = divmod(idx, 4)
        old_foot, _ = feet(old_mask, old_bb, 15 if col == 0 else 65)
        new_foot, _ = feet(new_mask, bb, 15 if col == 0 else 65)
        # Same original registration, adjusted only by paired body/boot drift. No accessory scaling.
        dx = new_foot[0] - old_foot[0]
        dy = bbs[row * 4][3] - old_bbs[row * 4][3]
        old_abs = [old_action['perFrameRects'][idx][0] + old_action['perFrameOrigins'][idx][0],
                   old_action['perFrameRects'][idx][1] + old_action['perFrameOrigins'][idx][1]]
        point = [old_abs[0] + dx, old_abs[1] + dy]
        if point[1] > rect[1] + rect[3] - 1:
            rect[3] = min((row + 1) * 384, point[1] + 1) - rect[1]
        origin = [point[0] - rect[0], point[1] - rect[1]]
        assert 0 <= origin[0] <= rect[2] and 0 <= origin[1] <= rect[3]
        old_body, new_body = body_measure(old_mask, old_rect, row, col), body_measure(new_mask, rect, row, col)
        drift.append({'index': idx, 'bootMidpointDeltaX': dx, 'standingSoleDeltaY': dy,
                      'headTopDeltaY': new_body['headTop'] - old_body['headTop'],
                      'waistCoreDeltaX': round(new_body['waistCoreX'] - old_body['waistCoreX'], 3)})
        origins.append(origin)
        absolute_ground.append(point)
    digest = sha(new_path)
    shutil.copyfile(new_path, RUNTIME / new_name)
    assert sha(RUNTIME / new_name) == digest
    for key in ['idle_' + item, 'walk_' + item]:
        action = data['actions'][key]
        action.update({'image': 'hero-v4/' + new_name, 'perFrameRects': rects,
                       'perFrameOrigins': origins,
                       'alphaBounds': [[b[0]-r[0], b[1]-r[1], b[2]-r[0], b[3]-r[1]] for b,r in zip(bbs,rects)],
                       'sourcePNG': new_path.relative_to(ROOT).as_posix(), 'sourcePNGSHA256': digest})
        assert {k:v for k,v in action.items() if k not in allowed_fields} == {
            k:v for k,v in baseline['actions'][key].items() if k not in allowed_fields}
    edge = {'top': max(new_alpha.getpixel((x,0)) for x in range(1024)),
            'bottom': max(new_alpha.getpixel((x,1535)) for x in range(1024)),
            'left': max(new_alpha.getpixel((0,y)) for y in range(1536)),
            'right': max(new_alpha.getpixel((1023,y)) for y in range(1536))}
    record = {'sourcePNG': new_path.relative_to(ROOT).as_posix(), 'sourceSHA256': digest,
              'editTargetPNG': old_path.relative_to(ROOT).as_posix(), 'editTargetSHA256': sha(old_path),
              'accessoryReferencePNG': 'source-art/characters/2d-concepts/hero-v4/W07-walk-readable.png',
              'accessoryReferenceSHA256': sha(ROOT/'source-art/characters/2d-concepts/hero-v4/W07-walk-readable.png'),
              'sourceRuntimeSHAEqual': True, 'size': list(new_im.size), 'alphaExtrema': list(new_alpha.getextrema()),
              'outsideEdgeMaxAlpha': edge, 'absoluteGroundPoints': absolute_ground, 'pairedBodyDrift': drift,
              'transparentGutters': gutters, 'worldUnitsPerPixelPreserved': old_action['worldUnitsPerPixel'],
              'sourcePolicy': 'Native transparent imagegen output copied unchanged; PIL alpha reads only.',
              'editScope': 'Add brown leather quiver and feathered arrows only. Attack and all other poses unchanged.',
              'runtimeStatus': 'Requires final build and native transition review'}
    data['records'][new_name] = record
    report['images'][item] = record

changed = {'idle_W08', 'walk_W08', 'idle_L02', 'walk_L02'}
for key, action in baseline['actions'].items():
    if key not in changed:
        assert data['actions'][key] == action, key
        report['unchangedActions'].append(key)
for name, record in baseline['records'].items():
    assert data['records'][name] == record
    assert sha(ROOT / record['sourcePNG']) == record['sourceSHA256']
report['metadataBaselineSHA256'] = sha(HERE/'metadata-advanced-before-quiver-v2.json')
report['changedActions'] = sorted(changed)
META.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report['metadataSHA256'] = sha(META)
(HERE/'verification-quiver-v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({item: {'sha256':rec['sourceSHA256'], 'UPP':rec['worldUnitsPerPixelPreserved'],
                       'maxHeadDriftY':max(abs(x['headTopDeltaY']) for x in rec['pairedBodyDrift']),
                       'maxBootDriftX':max(abs(x['bootMidpointDeltaX']) for x in rec['pairedBodyDrift']),
                       'maxGroundDriftY':max(abs(x['standingSoleDeltaY']) for x in rec['pairedBodyDrift']),
                       'edge':rec['outsideEdgeMaxAlpha']} for item,rec in report['images'].items()},ensure_ascii=False))
