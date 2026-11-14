"""Install generated run PNG bytes verbatim; measure alpha only for metadata.

This installer never saves, draws, crops, resizes or alters a PNG. Pillow crops
below are temporary alpha measurements. Only run/run_bow/run_staff are updated.
"""
from pathlib import Path
import hashlib, json, shutil, statistics, uuid, sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
SOURCE = Path(__file__).parent
DEST = ROOT / 'src/cocos/assets/resources/flat2d/characters/raphael'
DIRECTIONS = ['down', 'right', 'up', 'left']
THRESHOLD = 32
ACTION_FIRST = [('run','run-v3'), ('run_bow','run-bow-v3'), ('run_staff','run-staff-v3')]
only_action = next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--action=')), None)
assert only_action is None or only_action in dict(ACTION_FIRST), only_action
selected_actions = [(a,n) for a,n in ACTION_FIRST if only_action is None or a == only_action]
selected_names = {n+s for a,n in selected_actions for s in ['', '-b']}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def rel(path):
    return Path(path).relative_to(ROOT).as_posix()

def largest_run_midpoint(alpha, y):
    values = [x for x in range(alpha.width) if alpha.getpixel((x, y)) > THRESHOLD]
    runs = []
    for x in values:
        if not runs or x != runs[-1][-1] + 1:
            runs.append([x])
        else:
            runs[-1].append(x)
    longest = max(runs, key=len)
    return (longest[0] + longest[-1]) / 2

def measure(path, frame_rects=None):
    image = Image.open(path)
    assert image.mode == 'RGBA' and image.size == (1536, 1024), (path, image.mode, image.size)
    alpha = image.getchannel('A')
    frames = []
    for row in range(4):
        for column in range(4):
            rect = frame_rects[row*4+column] if frame_rects else [column*384, row*256, 384, 256]
            assert rect[2:] == [384,256] and rect[0] >= 0 and rect[1] >= 0 and rect[0]+384 <= image.width and rect[1]+256 <= image.height, rect
            a = alpha.crop((rect[0], rect[1], rect[0]+384, rect[1]+256))
            box = a.point(lambda p: 255 if p > THRESHOLD else 0).getbbox()
            assert box, (path, row, column, 'empty')
            left, top, right, bottom = box
            margin = min(left, top, 384-right, 256-bottom)
            assert margin >= 1, (path, row, column, 'clipped', box)
            # The longest opaque run in the waist/pelvis band measures body
            # centre, rather than alternating grounded boot or low prop tips.
            band = [round(top+(bottom-top)*.47), round(top+(bottom-top)*.60)]
            centre = round(statistics.median(largest_run_midpoint(a, y) for y in range(*band)))
            head_band = [max(0, centre-36), 0, min(384, centre+52), 70]
            head = a.crop(tuple(head_band)).point(lambda p: 255 if p > THRESHOLD else 0).getbbox()
            assert head
            head_top = head[1]
            hair_y = min(69, head_top+12)
            head_x = largest_run_midpoint(a, hair_y)
            sole_pixels = [x for y in range(max(top,bottom-5),bottom) for x in range(384) if a.getpixel((x,y)) > THRESHOLD]
            lowest_boot_x = statistics.median(sole_pixels)
            edges = [a.crop((0,0,384,1)), a.crop((0,255,384,256)), a.crop((0,0,1,256)), a.crop((383,0,384,256))]
            border_max = max(edge.getextrema()[1] for edge in edges)
            frames.append({'direction': DIRECTIONS[row], 'column': column, 'alphaBounds': list(box),
                'rawSoleY': bottom, 'bodyCentreX': centre, 'bodyCentreBand': band,
                'headSearchBand': head_band, 'headTopY': head_top,
                'headXAtTopPlus12': head_x, 'minimumMargin': margin, 'cellBorderMaxAlpha': border_max})
            frames[-1]['lowestBootCentreX'] = lowest_boot_x
            frames[-1]['lowestBootRelativeToPelvisX'] = lowest_boot_x-centre
    result = {'size': list(image.size), 'frameSize': [384,256], 'alphaExtrema': list(alpha.getextrema()), 'frames': frames}
    if frame_rects:
        result['frameRects'] = frame_rects
    return result

generation = json.loads((SOURCE/'run-v3-generation.json').read_text(encoding='utf8'))
manifest_path = DEST/'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf8'))
records_path = SOURCE/'install-records.json'
records = json.loads(records_path.read_text(encoding='utf8'))
base_bounds = manifest['alphaBounds'][0]
base_height = (base_bounds[3]-base_bounds[1])*manifest['camera']['worldUnitsPerPixel']
design = ROOT/'assets/concepts/revision-v5/hero-v5-balanced.png'
template = json.loads((DEST/'run.png.meta').read_text(encoding='utf8'))
installed = {}
for selected in generation['selected']:
    name = selected['name']
    if name not in selected_names:
        continue
    generated = Path(selected['generated'])
    source = SOURCE/(name+'.png')
    runtime = DEST/source.name
    shutil.copyfile(generated, source)
    shutil.copyfile(source, runtime)
    assert generated.read_bytes() == source.read_bytes() == runtime.read_bytes()
    measure_record = measure(source, selected.get('frameRects'))
    meta_path = Path(str(runtime)+'.meta')
    if not meta_path.exists():
        meta = json.loads(json.dumps(template))
        old_uuid = meta['uuid']
        new_uuid = str(uuid.uuid4())
        serialized = json.dumps(meta, ensure_ascii=False, indent=2).replace(old_uuid, new_uuid).replace('"displayName": "run"', '"displayName": "'+name+'"')
        meta_path.write_text(serialized+'\n', encoding='utf8')
    installed[name] = {'generatedInput': str(generated), 'generatedInputSHA256': sha(generated),
        'sourcePNG': rel(source), 'sourcePNGSHA256': sha(source), 'runtimePNG': rel(runtime), 'runtimePNGSHA256': sha(runtime),
        'sourceDesign': rel(design), 'sourceDesignSHA256': sha(design),
        'generationTool': 'built-in image_gen.imagegen', 'pixelEditsAfterGeneration': False,
        'generationPromptRecord': rel(SOURCE/'run-v3-generation.json'),
        **measure_record, 'pngBytes': runtime.stat().st_size, 'estimatedRGBABytes': 1536*1024*4}
    if selected.get('alphaExtractionInput'):
        alpha_input = Path(selected['alphaExtractionInput'])
        installed[name]['imagegenAlphaExtractionInput'] = {'path': str(alpha_input), 'sha256': sha(alpha_input),
            'promptRecord': rel(SOURCE/'run-v3-generation.json')}

action_reports = {}
for action, first in selected_actions:
    sheets = [installed[first], installed[first+'-b']]
    origins, phase_bounds, evidence = {}, {}, {}
    for row, direction in enumerate(DIRECTIONS):
        phases = [*sheets[0]['frames'][row*4:row*4+4], *sheets[1]['frames'][row*4:row*4+4]]
        ground_y = round(statistics.median(frame['rawSoleY'] for frame in phases))
        origins[direction] = [[frame['bodyCentreX'], ground_y] for frame in phases]
        phase_bounds[direction] = [frame['alphaBounds'] for frame in phases]
        evidence[direction] = {'groundY': ground_y, 'rawSoleY': [f['rawSoleY'] for f in phases],
            'rawHeadTopY': [f['headTopY'] for f in phases],
            'correctedHeadCentreX': [f['headXAtTopPlus12']-f['bodyCentreX'] for f in phases],
            'bodyCentreX': [f['bodyCentreX'] for f in phases],
            'lowestBootRelativeToPelvisX': [f['lowestBootRelativeToPelvisX'] for f in phases],
            'minimumMargin': min(f['minimumMargin'] for f in phases),
            'maximumBorderAlpha': max(f['cellBorderMaxAlpha'] for f in phases)}
    front = [*sheets[0]['frames'][0:4], *sheets[1]['frames'][0:4]]
    height_px = statistics.median(origins['down'][i][1]-frame['headTopY'] for i, frame in enumerate(front))
    upp = base_height/height_px
    images = [first+'.png']*4 + [first+'-b.png']*4
    method = 'X: median longest opaque waist/pelvis alpha>32 run over 47-60% body band; Y: fixed median sole line across eight phases per direction, never per-frame boot tip.'
    manifest['actions'][action] = {'image': first+'.png', 'frameImages': images, 'columns': 4, 'frames': 8,
        'frameIndices': [0,1,2,3,0,1,2,3], 'fps': 14, 'loop': True,
        'perFrameOrigins': origins, 'originMethod': method,
        'alphaBounds': sheets[0]['frames'] and [f['alphaBounds'] for f in sheets[0]['frames']],
        'perPhaseAlphaBounds': phase_bounds, 'alphaBoundsThreshold': THRESHOLD,
        'worldUnitsPerPixel': upp, 'sourcePNG': sheets[0]['sourcePNG'], 'sourcePNGSHA256': sheets[0]['sourcePNGSHA256'],
        'sourcePNGs': [s['sourcePNG'] for s in sheets], 'sourcePNGSHA256s': [s['sourcePNGSHA256'] for s in sheets],
        'sourceDesign': rel(design), 'sourceDesignSHA256': sha(design),
        'bodyScaleReference': {'bodyHeightPixels': height_px, 'targetProjectedBodyHeightMetres': base_height,
            'method': 'One scale for A/B: median front head-top to fixed ground line over eight phases; side prop tips excluded.'},
        'generationPromptRecord': rel(SOURCE/'run-v3-generation.json'),
        'notes': 'Eight generated run drawings per direction across two unchanged source PNGs. Body-centre X removes source layout drift; fixed ground Y preserves small natural vertical motion. Browser loop review remains required.'}
    rect_maps = {Path(s['sourcePNG']).stem:s['frameRects'] for s in sheets if s.get('frameRects')}
    if rect_maps:
        manifest['actions'][action]['frameRectsByImage'] = rect_maps
    action_reports[action] = {'images': images, 'fps':14, 'worldUnitsPerPixel': upp, 'perFrameOrigins': origins,
        'originMethod': method, 'directions': evidence,
        'phaseIntent': ['right contact','right loading','right midstance/left passing','right toe-off/left low swing',
            'left contact','left loading','left midstance/right passing','left toe-off/right low swing'],
        'scopeNote': 'Phase names describe generation intent. This alpha-only measurement proves framing/anchor continuity, not joint timing or anatomical correctness; inspect actual playback.'}
    for name in [first, first+'-b']:
        installed[name]['actions'] = [action]
        installed[name]['worldUnitsPerPixel'] = upp
        installed[name]['perFrameOrigins'] = origins
        installed[name]['originMethod'] = method
        records[name] = installed[name]

manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
records_path.write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
previous_report_path = SOURCE/'run-v3-verification.json'
previous_report = json.loads(previous_report_path.read_text(encoding='utf8')) if previous_report_path.exists() else {}
report = {'date':'2026-11-06', 'pixelEditsAfterGeneration':False,
    'pngBytesEqualSourceAndRuntime':True, 'actions':action_reports,
    'sheets': {name:{k:v for k,v in data.items() if k != 'frames'} for name,data in installed.items()},
    'manualVisualNotes':['Compact bent elbows and a small forward lean replace the old spread arms.',
        'Side profiles have modest recovery/under-body passing poses. A side column3 wide swing was corrected after native playback review; rebuild validation remains required.',
        'Sword is held low away from the face. Bow and staff are actual carried props in their run variants.',
        'A/B phase identity and seam quality require runtime review; alpha metadata alone is not a gait-quality pass.']}
report['actions'] = {**previous_report.get('actions',{}), **report['actions']}
report['sheets'] = {**previous_report.get('sheets',{}), **report['sheets']}
report['lastUpdatedActions'] = [a for a,n in selected_actions]
correction_record = SOURCE/'run-v3-b-corrections.json'
if correction_record.exists():
    report['oppositeLegCorrection'] = json.loads(correction_record.read_text(encoding='utf8'))['visualReview']
passing_record = SOURCE/'run-v3-a-corrections.json'
if passing_record.exists():
    report['compactPassingCorrection'] = json.loads(passing_record.read_text(encoding='utf8'))['visualReview']
staff_record = SOURCE/'run-v3-staff-prop-corrections.json'
if staff_record.exists():
    report['staffPropCorrection'] = json.loads(staff_record.read_text(encoding='utf8'))['visualReview']
(SOURCE/'run-v3-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps({'actions':action_reports, 'sheetPNGBytes':{n:d['pngBytes'] for n,d in installed.items()}}, ensure_ascii=False, indent=2))
