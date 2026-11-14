"""Measure native generated PNGs and create an action overlay; never write pixels.

Reuses the project's connected-component crops, sole diagnostics, and lower-body
alpha registration. Runtime copies are byte-identical to built-in imagegen output.
"""
from pathlib import Path
from collections import deque
from PIL import Image
import ast, copy, hashlib, json, statistics
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
ACTOR = ROOT / 'src/cocos/assets/resources/flat2d/characters/raphael'
REF = ROOT / 'source-art/characters/2d-concepts'
REQUESTS = json.loads((HERE / 'generation-requests.json').read_text(encoding='utf-8'))
MANIFEST_PATH = ACTOR / 'manifest.json'
MANIFEST_BYTES = MANIFEST_PATH.read_bytes()
MANIFEST = json.loads(MANIFEST_BYTES)
DIRECTIONS = MANIFEST['directions']
BASELINE = json.loads((HERE.parent / 'male-bows/owned-actions.json').read_text(encoding='utf-8'))
MANIFEST['actions'] = BASELINE['actions']

for script in [REF / 'hero-v4-reactions/measure_metadata.py', REF / 'hero-v4-equipment/register-bow-reactions.py']:
    tree = ast.parse(script.read_text(encoding='utf-8'))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(script), 'exec'))

# The original accessory-only measurement searches +/-6px. Appearance edits can
# move complete sprites further without changing a pose. Reuse exactly that
# existing registration algorithm with a wider search and corresponding ROI guard.
registration_script = REF / 'hero-v4-equipment/register-bow-reactions.py'
registration_text = registration_script.read_text(encoding='utf-8')
registration_tree = ast.parse(registration_text)
registration_node = next(node for node in registration_tree.body if isinstance(node, ast.FunctionDef) and node.name == 'body_translation')
wide_source = ast.get_source_segment(registration_text, registration_node)
wide_source = wide_source.replace('def body_translation(', 'def body_translation_wide(').replace('range(-6,7)', 'range(-24,25)')
wide_source = wide_source.replace('max(8,l),max(8,t),min(old.shape[1]-8,r),min(old.shape[0]-8,b)', 'max(25,l),max(25,t),min(old.shape[1]-25,r),min(old.shape[0]-25,b)')
exec(compile(wide_source, '<existing-lower-body-registration-wider-window>', 'exec'))
full_source = wide_source.replace('def body_translation_wide(', 'def body_translation_full(').replace('range(-24,25)', 'range(-32,33)')
full_source = full_source.replace('max(25,l),max(25,t),min(old.shape[1]-25,r),min(old.shape[0]-25,b)', 'max(33,l),max(33,t),min(old.shape[1]-33,r),min(old.shape[0]-33,b)')
exec(compile(full_source, '<existing-lower-body-registration-full-window>', 'exec'))

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dump(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def rel(path):
    return Path(path).relative_to(ROOT).as_posix()

def body_height(alpha, rect, ground, index):
    # First standing column, hair near pelvis centre; bow tips lie outside this
    # central head band. Arrow tips are lower than the scalp in these sources.
    x, y, w, h = rect
    left, right = max(x, round(ground[0] - 36)), min(x + w, round(ground[0] + 36))
    top, bottom = y, min(y + h, y + round(h * .25))
    mask = alpha.crop((left, top, right, bottom)).point(lambda a: 255 if a >= 128 else 0)
    box = mask.getbbox()
    assert box, ('No head in body scale reference', index)
    return ground[1] - (top + box[1])

def image_name(path):
    return path.replace('hero-v5/', 'hero-v6/', 1)

def measure_native(path, square):
    if square:
        alpha = Image.open(path).getchannel('A')
        width,height = alpha.size
        # Low AA bridges can connect a sole to the next row's hair at16/255.
        # Existing connected-component measurement at64 locates16 independent
        # complete bodies; limit padding at the gap between adjacent bodies.
        comps = components(alpha.point(lambda a:255 if a >= 64 else 0),0,height)
        groups = [sorted([c for c in comps if min(3,int((c['bounds'][1]+c['bounds'][3])/2/(height/4)))==row],key=lambda c:c['bounds'][0]) for row in range(4)]
        assert len(comps)==16 and all(len(g)==4 for g in groups)
        rects,bounds,contacts,frames = [],[],[],[]
        for row,group in enumerate(groups):
            for col,component in enumerate(group):
                x0,y0,x1,y1 = component['bounds']
                l,t,r,b = max(0,x0-2),max(0,y0-2),min(width,x1+2),min(height,y1+2)
                for other in comps:
                    if other is component: continue
                    ol,ot,orr,ob = other['bounds']
                    if not (orr <= l or ol >= r):
                        if ob <= y0: t=max(t,(ob+y0)//2)
                        elif ot >= y1: b=min(b,(y1+ot)//2)
                    if not (ob <= t or ot >= b):
                        if orr <= x0: l=max(l,(orr+x0)//2)
                        elif ol >= x1: r=min(r,(x1+ol)//2)
                local=alpha.crop((l,t,r,b))
                ab=local.point(lambda a:255 if a>=16 else 0).getbbox()
                core=local.point(lambda a:255 if a>=128 else 0).getbbox()
                depth=max(5,round((core[3]-core[1])*.25)) if col>=2 else 5
                support=[(sx0,sx1,y) for y in range(max(t,t+core[3]-depth),t+core[3]) for sx0,sx1 in spans(alpha,y,l,r)]
                sx0,sx1,sy=min(s[0] for s in support),max(s[1] for s in support),max(s[2] for s in support)
                foreign=sum(1 for other in comps if other is not component for x,y in other['pixels'] if l<=x<r and t<=y<b)
                assert foreign==0, ('Neighbour body in crop',row,col,foreign)
                rect=[l,t,r-l,b-t];rects.append(rect);bounds.append(list(ab));contacts.append([(sx0+sx1)/2,sy])
                frames.append({'index':row*4+col,'rect':rect,'supportSpan':[sx0,sx1,sy],'foreignBodyPixelsInsideRect':foreign,
                               'componentThreshold':64,'contactMethod':'lower-quarter landing contact' if col>=2 else 'opaque bottom-five sole rows'})
        hist=alpha.histogram()
        return {'size':[width,height],'rects':rects,'alphaBounds':bounds,'contacts':contacts,'frames':frames,
                'alphaExtrema':list(alpha.getextrema()),'alphaZeroFraction':hist[0]/sum(hist),
                'blankSamples':[alpha.getpixel(p) for p in [(0,0),(width-1,0),(0,height-1),(width-1,height-1)]],
                'nativeCropPolicy':'16 independent alpha>=64 bodies, padding limited between neighbours; rendering alpha threshold16/255.'}
    # Keep native pixels past a nominal row line when a generative edit drifts
    # a sole by1..3px. The nearest genuinely empty alpha<16 interval separates
    # consecutive figures. No pixel crop/resample, and no neighbour is included.
    result = measure(path, False)
    alpha = Image.open(path).getchannel('A')
    arr = np.asarray(alpha)
    width, height = alpha.size
    cw, ch = width // 4, height // 4
    boundaries = []
    for col in range(4):
        occupied = (arr[:, col*cw:(col+1)*cw] >= 16).any(axis=1)
        splits = [0]
        for boundary in [ch, 2*ch, 3*ch]:
            gaps = []
            start = None
            for y in range(boundary-32, boundary+33):
                if not occupied[y] and start is None:
                    start = y
                if occupied[y] and start is not None:
                    gaps.append((start, y)); start = None
            if start is not None:
                gaps.append((start, boundary+33))
            assert gaps, ('Opaque row gutter', path.name, col, boundary)
            gap = min(gaps, key=lambda g: abs((g[0]+g[1])/2-boundary))
            splits.append((gap[0]+gap[1])//2)
        splits.append(height)
        boundaries.append(splits)
    rects, bounds, contacts, frames = [], [], [], []
    for row in range(4):
        for col in range(4):
            cell = [col*cw, boundaries[col][row], (col+1)*cw, boundaries[col][row+1]]
            bb = alpha.crop(tuple(cell)).point(lambda a: 255 if a >= 16 else 0).getbbox()
            assert bb
            l, t = max(cell[0],cell[0]+bb[0]-2), max(cell[1],cell[1]+bb[1]-2)
            r, b = min(cell[2],cell[0]+bb[2]+2), min(cell[3],cell[1]+bb[3]+2)
            local = alpha.crop((l,t,r,b))
            ab = local.point(lambda a:255 if a >= 16 else 0).getbbox()
            core = local.point(lambda a:255 if a >= 128 else 0).getbbox()
            assert ab and core
            support = [(x0,x1,y) for y in range(max(t,t+core[3]-5),t+core[3]) for x0,x1 in spans(alpha,y,l,r)]
            sx0,sx1,sy = min(s[0] for s in support),max(s[1] for s in support),max(s[2] for s in support)
            rect=[l,t,r-l,b-t]
            rects.append(rect);bounds.append(list(ab));contacts.append([(sx0+sx1)/2,sy])
            frames.append({'index':row*4+col,'rect':rect,'supportSpan':[sx0,sx1,sy],
                           'foreignBodyPixelsInsideRect':0,'alphaSeparatedCell':cell,
                           'contactMethod':'opaque bottom-five sole rows; diagnostic only'})
    result.update({'rects':rects,'alphaBounds':bounds,'contacts':contacts,'frames':frames,
                   'rowBoundariesByColumn':boundaries,'nativeCropPolicy':'Complete alpha>=16 figure between empty row gutters, not nominal-line clipping.'})
    return result

sheets = {}
records = []
names = {entry['name'] + '.png' for entry in REQUESTS['files']}
owned = {key: value for key, value in MANIFEST['actions'].items()
         if Path(value.get('image', '')).name in names}

for request in REQUESTS['files']:
    filename = request['name'] + '.png'
    path = HERE / filename
    target = ROOT / request['editTarget']
    runtime = ACTOR / 'hero-v6' / filename
    square = 'hit-death' in filename
    after = measure_native(path, square)
    before = measure(target, square)
    assert after['size'] == before['size']
    assert after['alphaExtrema'][0] == 0
    assert digest(path) == digest(runtime) == digest(request['generatedPath'])
    alpha_old = Image.open(target).getchannel('A')
    alpha_new = Image.open(path).getchannel('A')
    related = [(key, value) for key, value in owned.items()
               if Path(value['image']).name == filename or any(Path(p).name == filename for p in value.get('frameImages', []))]
    assert related, filename
    reference = related[0][1]
    original_rects = reference.get('frameRectsByImage', {}).get('hero-v5/' + filename.removesuffix('.png'), reference.get('perFrameRects'))
    registrations = []
    for index, rect in enumerate(original_rects):
        delta, score = body_translation(target, path, rect, index, square)
        if max(map(abs, delta)) == 6 or score < .8:
            delta, score = body_translation_wide(target, path, rect, index, square)
        if max(map(abs, delta)) == 24:
            delta, score = body_translation_full(target, path, rect, index, square)
        registrations.append({'index': index, 'bodyOnlyTranslationXY': delta,
                              'lowerBodyMaskIoU': score,
                              'rawSoleContactDeltaDiagnosticOnly': [after['contacts'][index][n] - before['contacts'][index][n] for n in (0, 1)]})
    sheets[filename] = {'image': 'hero-v6/' + filename, 'after': after, 'before': before,
                        'registrations': registrations, 'alphaOld': alpha_old, 'alphaNew': alpha_new}
    record = copy.deepcopy(request)
    raw_alpha = np.asarray(alpha_new)
    h, w = raw_alpha.shape
    corner_alpha = np.concatenate([raw_alpha[:8,:8].ravel(),raw_alpha[:8,-8:].ravel(),raw_alpha[-8:,:8].ravel(),raw_alpha[-8:,-8:].ravel()])
    vertical_alpha = np.concatenate([raw_alpha[:,round(w*i/4)-1:round(w*i/4)+2].ravel() for i in [1,2,3]])
    horizontal_alpha = np.concatenate([raw_alpha[round(h*i/4)-1:round(h*i/4)+2,:].ravel() for i in [1,2,3]])
    assert int(corner_alpha.max()) < 16, ('Opaque corner background', filename)
    if not square:
        assert int(vertical_alpha.max()) < 16, ('Opaque vertical gutter or foreign body', filename)
    record.update({'sourcePNG': rel(path), 'sourceSHA256': digest(path), 'runtimePNG': rel(runtime),
                   'runtimeSHA256': digest(runtime), 'generatedSHA256': digest(request['generatedPath']),
                   'editTargetPNG': rel(target), 'editTargetSHA256': digest(target),
                   'appearanceReferencePNG': request['reference'],
                   'appearanceReferenceSHA256': digest(ROOT / request['reference']),
                   'dimensions': after['size'], 'alphaExtrema': after['alphaExtrema'],
                   'alphaZeroFraction': after['alphaZeroFraction'],
                   'blankSamples': after['blankSamples'], 'bodyRegistration': registrations,
                   'nativeFrameRects': after['rects'], 'nativeAlphaBounds': after['alphaBounds'],
                   'groundContactsDiagnosticOnly': after['contacts'], 'pixelPostprocessing': False,
                   'alphaBelow16Fraction': float((raw_alpha < 16).mean()),
                   'corner8x8MaxAlpha': int(corner_alpha.max()),
                   'verticalGridMaxAlpha': int(vertical_alpha.max()),
                   'horizontalGridMaxAlphaDiagnosticOnly': int(horizontal_alpha.max()),
                   'bottom2RowsMaxAlpha': int(raw_alpha[-2:,:].max()),
                   'foreignBodyPixelsInsideNativeCrops': sum(f['foreignBodyPixelsInsideRect'] for f in after['frames']),
                   'rowBoundariesByColumn': after.get('rowBoundariesByColumn')})
    for rejected in record.get('rejectedAttempts', []):
        rejected['sha256'] = digest(rejected['generatedPath'])
    for stage in record.get('stages', []):
        stage['generatedSHA256'] = digest(stage['generatedPath'])
        for field in ['editTarget', 'reference']:
            if field in stage:
                stage[field + 'SHA256'] = digest(stage[field])
    records.append(record)

actions = {}
scale_records = {}
preserve_fields = ['frames', 'frameIndices', 'directionFrameIndices', 'fps', 'loop', 'phaseStarts', 'row', 'absoluteFrameIndices']
for key, original in owned.items():
    action = copy.deepcopy(original)
    filename = Path(original['image']).name
    sheet = sheets[filename]
    action['image'] = image_name(original['image'])
    action['perFrameRects'] = sheet['after']['rects']
    action['alphaBounds'] = sheet['after']['alphaBounds']
    action['alphaBoundsThreshold'] = 16
    action['sourcePNG'] = rel(HERE / filename)
    action['sourcePNGSHA256'] = digest(HERE / filename)
    origins = original.get('perFrameOrigins')
    if isinstance(origins, list):
        result = []
        for i, (point, old_rect, rect) in enumerate(zip(origins, original['perFrameRects'], action['perFrameRects'])):
            dx, dy = sheet['registrations'][i]['bodyOnlyTranslationXY']
            result.append([point[0] + old_rect[0] + dx - rect[0], point[1] + old_rect[1] + dy - rect[1]])
        action['perFrameOrigins'] = result
    else:
        assert isinstance(origins, dict), key
        action['frameImages'] = [image_name(name) for name in original['frameImages']]
        action['frameRectsByImage'] = {image_name(name): sheets[Path(name).name + '.png']['after']['rects']
                                      for name in original['frameRectsByImage']}
        result = {}
        phase_bounds = {}
        for row, direction in enumerate(DIRECTIONS):
            new_points = []
            bounds = []
            ground_dy = statistics.median(
                sheets[Path(name).name]['registrations'][row * 4 + original['frameIndices'][phase]]['bodyOnlyTranslationXY'][1]
                for phase, name in enumerate(original['frameImages']))
            for phase, point in enumerate(origins[direction]):
                name = original['frameImages'][phase]
                s = sheets[Path(name).name]
                index = row * 4 + original['frameIndices'][phase]
                old_rect = original['frameRectsByImage'][name.removesuffix('.png')][index]
                rect = s['after']['rects'][index]
                dx, dy = s['registrations'][index]['bodyOnlyTranslationXY']
                new_points.append([point[0] + old_rect[0] + dx - rect[0], point[1] + old_rect[1] + ground_dy - rect[1]])
                bounds.append(s['after']['alphaBounds'][index])
            result[direction] = new_points
            phase_bounds[direction] = bounds
        action['perFrameOrigins'] = result
        action['perPhaseAlphaBounds'] = phase_bounds
        action['sourcePNGs'] = [rel(HERE / Path(name + '.png').name) for name in original['frameRectsByImage']]
        action['sourcePNGSHA256s'] = [digest(ROOT / name) for name in action['sourcePNGs']]
        assert len(action['frameImages']) == 8
        assert all(name.startswith('hero-v6/') and not name.endswith('.png') for name in action['frameRectsByImage'])
    # Standing canonical frames determine one scale factor for the whole action.
    # Running retains accepted UPP: changing swing-foot elevation cannot alter scale.
    ratio = 1.0
    height_samples = []
    if not original.get('frameImages'):
        for i in [0, 8]:
            old_rect = original['perFrameRects'][i]
            old_point = original['perFrameOrigins'][i]
            old_ground = [old_rect[0] + old_point[0], old_rect[1] + old_point[1]]
            new_rect = action['perFrameRects'][i]
            new_point = action['perFrameOrigins'][i]
            new_ground = [new_rect[0] + new_point[0], new_rect[1] + new_point[1]]
            old_height = body_height(sheet['alphaOld'], old_rect, old_ground, i)
            new_height = body_height(sheet['alphaNew'], new_rect, new_ground, i)
            height_samples.append({'index': i, 'oldHeadToGround': old_height, 'newHeadToGround': new_height})
        # Hairstyle top changes are not an anatomical height change. Preserve
        # accepted source-body UPP rather than normalize to new ponytail hair.
        ratio = 1.0
    action['worldUnitsPerPixel'] = original['worldUnitsPerPixel'] * ratio
    action['originMethod'] = 'Original support-plane/pelvis origin transferred by existing lower-body alpha registration; crop offset converted explicitly. Alpha>=16 complete native crop. No single-boot reanchor, no image resampling.'
    for field in preserve_fields:
        assert action.get(field) == original.get(field), (key, field)
    actions[key] = action
    scale_records[key] = {'originalUPP': original['worldUnitsPerPixel'], 'newUPP': action['worldUnitsPerPixel'],
                          'heightSamples': height_samples, 'scaleRatio': ratio,
                          'policy': 'One body scale per whole action. Eight-phase running retains approved1.556m source-body scale.'}

assert MANIFEST_PATH.read_bytes() == MANIFEST_BYTES
dump('generation-record.json', {'version': 'male-bows-soft-geralt-v3', 'tool': 'built-in image_gen', 'files': records,
      'pixelPostprocessing': False, 'manifestInputSHA256': hashlib.sha256(MANIFEST_BYTES).hexdigest()})
dump('owned-actions.json', {'version': 'male-bows-soft-geralt-v3', 'actions': actions,
      'alphaThreshold': 16 / 255, 'manifestInputSHA256': hashlib.sha256(MANIFEST_BYTES).hexdigest(),
      'scaleMeasurements': scale_records, 'pixelPostprocessing': False,
      'originPolicy': 'Existing lower-body alpha registration; preserve approved origins and native crop semantics.',
      'temporalFieldsPreserved': preserve_fields})
print(json.dumps({'files': len(records), 'actions': len(actions), 'keys': list(actions),
 'alphaMinima': {r['name']: r['alphaExtrema'][0] for r in records},
 'minIoU': min(g['lowerBodyMaskIoU'] for r in records for g in r['bodyRegistration']),
 'maxTranslationXY': [max(abs(g['bodyOnlyTranslationXY'][n]) for r in records for g in r['bodyRegistration']) for n in [0,1]],
 'runImageMaps': {k: list(v['frameRectsByImage']) for k,v in actions.items() if 'frameRectsByImage' in v},
 'uppRange': [min(v['worldUnitsPerPixel'] for v in actions.values()), max(v['worldUnitsPerPixel'] for v in actions.values())]}, ensure_ascii=False, indent=2))
