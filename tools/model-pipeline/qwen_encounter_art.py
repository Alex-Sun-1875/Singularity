"""Produce the encounter design plates on the installed local Qwen runtime.

Uses ComfyUI native nodes and the existing eight-step Turbo schedule. No model
downloads, third-party nodes, cloud inference, service restarts or /free calls.
The first plate is a pilot; --batch is used only after visual inspection.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shutil
import time
import urllib.request
from PIL import Image

PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT / 'source-art/encounters/qwen-world-v1'
COMFY = Path(r'F:\Models\ComfyUI_windows_portable\ComfyUI')
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
URL = 'http://127.0.0.1:8188'
SIGMAS = '1.0, 0.978453, 0.95418, 0.926626, 0.89508, 0.845148, 0.704534, 0.414568, 0'


def api(path, body=None):
    req = urllib.request.Request(URL + path, data=None if body is None else json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with HTTP.open(req, timeout=30) as response:
        return json.load(response)


def node(kind, **inputs):
    return {'class_type': kind, 'inputs': inputs}


def run(case):
    out = ROOT / 'results' / case['id']
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'result.json').exists():
        print('Already completed:', case['id'], flush=True)
        return
    graph = {
        '1': node('UNETLoader', unet_name='qwen_image_2.1_turbo_int8_convrot.safetensors', weight_dtype='default'),
        '2': node('CLIPLoader', clip_name='qwen3vl_8b_int8_convrot.safetensors', type='qwen_image', device='cpu'),
        '3': node('VAELoader', vae_name='qwen_image_2.1_vae_bf16.safetensors'),
        '8': node('TextEncodeQwenImage21', clip=['2', 0], vae=['3', 0], prompt=case['prompt'], negative_prompt='', resolution=1024),
        '9': node('QwenImage21Cache', model=['1', 0], device='cpu', dtype='default'),
        '10': node('CFGGuider', model=['9', 0], positive=['8', 0], negative=['8', 1], cfg=1),
        '11': node('RandomNoise', noise_seed=case['seed']),
        '12': node('KSamplerSelect', sampler_name='euler'),
        '13': node('ManualSigmas', sigmas=SIGMAS),
        '14': node('SamplerCustomAdvanced', noise=['11', 0], guider=['10', 0], sampler=['12', 0], sigmas=['13', 0], latent_image=['8', 2]),
        '15': node('VAEDecode', samples=['14', 0], vae=['3', 0]),
        '16': node('SaveImage', images=['15', 0], filename_prefix='qwen-world-v1/' + case['id']),
    }
    reference = None
    if case.get('reference'):
        reference = PROJECT / case['reference']
        target = COMFY / 'input/qwen-world-v1/style-reference.png'
        target.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(reference) as original:
            original.thumbnail((960, 960))
            canvas = Image.new('RGBA', (1024, 1024))
            canvas.alpha_composite(original.convert('RGBA'), ((1024-original.width)//2, (1024-original.height)//2))
            canvas.save(target)
        graph['4'] = node('LoadImage', image='qwen-world-v1/style-reference.png')
        graph['6'] = node('JoinImageWithAlpha', image=['4', 0], alpha=['4', 1])
        graph['8']['inputs']['images.image_1'] = ['6', 0]
        graph['8']['inputs']['resolution'] = 0
    (out / 'workflow-api.json').write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'prompt.txt').write_text(case['prompt'], encoding='utf-8')
    if (out / 'submission.json').exists():
        submission = json.loads((out / 'submission.json').read_text(encoding='utf-8'))
    else:
        submission = api('/prompt', {'prompt': graph, 'client_id': 'singularity-world-encounters'})
        (out / 'submission.json').write_text(json.dumps(submission, indent=2), encoding='utf-8')
    if submission.get('node_errors') or not submission.get('prompt_id'):
        raise RuntimeError(str(submission))
    prompt_id = submission['prompt_id']
    print('Queued:', case['id'], prompt_id, flush=True)
    started = time.monotonic()
    while time.monotonic()-started < 3600:
        records = api('/history/' + prompt_id)
        if prompt_id in records:
            history = records[prompt_id]
            (out / 'history.json').write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding='utf-8')
            if history.get('status', {}).get('status_str') != 'success':
                raise RuntimeError('Inspect failed job: ' + str(out / 'history.json'))
            item = history['outputs']['16']['images'][0]
            raw = COMFY / 'output' / item.get('subfolder', '') / item['filename']
            shutil.copy2(raw, out / 'raw.png')
            with Image.open(out / 'raw.png') as image:
                size, mode = list(image.size), image.mode
                preview = Image.new('RGB', image.size, '#202328')
                if mode == 'RGBA':
                    preview.paste(image, mask=image.getchannel('A'))
                else:
                    preview.paste(image)
                preview.thumbnail((768, 768))
                preview.save(out / 'preview.jpg', quality=90)
            report = {'id': case['id'], 'prompt_id': prompt_id, 'model': 'Qwen-Image-2.1-Turbo INT8 convrot', 'endpoint': URL,
                      'cloud_generation': False, 'new_model_inference': True, 'reference': str(reference) if reference else None,
                      'seed': case['seed'], 'steps': 8, 'cfg': 1, 'sampler': 'euler', 'size': size, 'mode': mode,
                      'seconds_waited_this_run': round(time.monotonic()-started, 2), 'completed_utc': datetime.now(timezone.utc).isoformat(),
                      'sha256': hashlib.file_digest((out / 'raw.png').open('rb'), 'sha256').hexdigest(),
                      'raw_postprocessed': False, 'runtime_installed': False, 'art_review': 'pending'}
            (out / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            print('Finished:', case['id'], size, mode, report['seconds_waited_this_run'], flush=True)
            return
        time.sleep(3)
    raise TimeoutError('Keep submission.json; inspect queue before retrying')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--case')
    parser.add_argument('--batch', action='store_true')
    args = parser.parse_args()
    cases = json.loads((ROOT / 'art-jobs.json').read_text(encoding='utf-8'))
    if not args.case and not args.batch:
        parser.error('Select --case for the pilot, then --batch after inspection')
    for case in cases:
        if args.batch or case['id'] == args.case:
            run(case)
