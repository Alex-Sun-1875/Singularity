"""Save native built-in image outputs and measure them without editing pixels."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
JOBS = {j['image']: j for j in json.loads((HERE/'generation-jobs.json').read_text(encoding='utf-8'))['jobs'] if j['worker']=='art'}
spec = importlib.util.spec_from_file_location('art_native_geometry', HERE.parent/'weapon-carry-v1/measure-install.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

status_path = HERE/'worker-art-status.json'
status = json.loads(status_path.read_text(encoding='utf-8')) if status_path.exists() else {'worker':'art','images':{}}
for item in json.load(sys.stdin):
    job = JOBS[item['image']]
    raw, source = Path(item['raw']), Path(job['outputPath'])
    source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(raw, source)
    previous = status['images'].get(item['image'], {})
    attempts = previous.get('attempts', [])
    prompt_path = source.with_suffix('.prompt.txt')
    if attempts and 'promptFile' not in attempts[-1] and prompt_path.exists():
        previous_prompt = source.with_suffix(f'.attempt-{len(attempts)}.prompt.txt')
        shutil.copyfile(prompt_path, previous_prompt)
        attempts[-1]['promptFile'] = str(previous_prompt)
        attempts[-1]['promptSHA256'] = sha(previous_prompt)
    attempt_prompt = source.with_suffix(f'.attempt-{len(attempts)+1}.prompt.txt')
    attempt_prompt.write_text(item['prompt'], encoding='utf-8')
    prompt_path.write_text(item['prompt'], encoding='utf-8')
    attempts = attempts + [{'rawOutputPath':str(raw),'sha256':sha(raw),'kind':item.get('kind','head-identity-edit'),'promptFile':str(attempt_prompt),'promptSHA256':sha(attempt_prompt)}]
    provenance = {'tool':'built-in image_gen','sourcePath':str(source),'rawOutputPath':str(raw),
        'pixelEdits':False,'editTarget':job['editTarget'],'editTargetSHA256':sha(job['editTarget']),
        'identityMaster':job['masterPath'],'identityMasterSHA256':sha(job['masterPath']),
        'promptFile':str(prompt_path),'promptSHA256':sha(prompt_path),'sha256':sha(source),
        'rawSourceSHAEqual':sha(raw)==sha(source), 'worker':'art','attempts':attempts,
        'scope':'head/face/hair only; original body, equipment and action phase retained',
        'visualReview':item['visualReview']}
    write(source.with_suffix('.provenance.json'), provenance)
    error, geometry = None, None
    try:
        alpha = helper.alpha(source)
        if list(alpha.shape[::-1]) != job['size']:
            raise ValueError(f"Native size changed: {list(alpha.shape[::-1])} expected {job['size']}")
        geometry = helper.native_geometry(alpha, job['layout'])
    except (ValueError, OSError) as exc:
        error = str(exc)
    record = {'sourcePath':str(source),'sha256':sha(source),'rawOutputPath':str(raw),
        'attempts':attempts,'nativeGeometryError':error,'frameCount':len(geometry['rects']) if geometry else None,
        'nativeGeometry':'passed' if geometry else 'failed','visualReview':item['visualReview'],
        'status':'complete-native-checked' if geometry else 'needs-native-transparency-repair', 'pixelEdits':False}
    status['images'][item['image']] = record
    status['completedCount'] = sum(r['status']=='complete-native-checked' for r in status['images'].values())
    status['totalAssigned'] = len(JOBS)
    write(status_path, status)
    print(json.dumps({'image':item['image'],'status':record['status'],'error':error,'frameCount':record['frameCount']}, ensure_ascii=False))
