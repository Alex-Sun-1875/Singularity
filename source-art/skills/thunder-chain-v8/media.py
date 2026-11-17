"""Package and inspect native Cocos chain-arc captures."""
import hashlib
import importlib.util
import json
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MEDIA = HERE / 'media'
PREVIOUS = ROOT / 'src/.tmp/thunder-alignment-v7/previous-thicker'
CURRENT = ROOT / 'src/.tmp/thunder-chain-v8/final/refined'
SCENES = {'THU_02': '连锁雷弧', 'THU_05': '万钧雷潮'}
ALL = ['THU_01', *SCENES]
spec = importlib.util.spec_from_file_location('review_media', HERE.parent / 'thunder-fidelity-v6/media.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
review.MEDIA = MEDIA
review.CACHES = {'previous': PREVIOUS, 'revised': CURRENT}
review.SHOTS = SCENES


def report(root, shot):
    return json.loads((root / shot / 'capture.json').read_text(encoding='utf8'))


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def validate_captures():
    data = {'baseline': str(PREVIOUS.relative_to(ROOT)), 'shots': {}}
    for shot in ALL:
        a, b = report(PREVIOUS, shot), report(CURRENT, shot)
        for key in ['gameHash', 'frames', 'events', 'presentation']:
            assert a[key] == b[key], (shot, key)
        for key in ['origin', 'targets', 'geometry', 'skillGeometry']:
            assert a['info'].get(key) == b['info'].get(key), (shot, key)
        assert not b['errors'] and b['info']['player']['skeletons'], shot
        assert len(list((CURRENT / shot).glob('*.jpg'))) == b['frames']
        for name, digest in b['reviewInputs'].items():
            assert sha(HERE / name) == digest, (shot, name)
        for name in ['reference-profile.json', 'approved-thunder-strip.png']:
            assert a['reviewInputs'][name] == b['reviewInputs'][name], (shot, name)
        chains = [d for f in b['nativeAudit'] for d in f['draws'] if d['role'] == 'chain']
        launches = [d for f in b['nativeAudit'] for d in f['draws'] if d['role'] == 'launch']
        assert launches and all(abs(d['width'] - .51) < 1e-6 and d['textureBand'] == 0 for d in launches), shot
        endpoint_shift = max([np.linalg.norm(np.array(d[x]) - d[y]) for d in chains
                              for x, y in [('sourceFrom', 'renderFrom'), ('sourceTo', 'renderTo')]], default=0)
        if shot in SCENES:
            assert chains and endpoint_shift < 1e-6, shot
            assert all(abs(d['width'] - .30) < 1e-6 and d['textureBand'] == 0 for d in chains), shot
        data['shots'][shot] = {'frames': b['frames'], 'maxChains': max(sum(d['role'] == 'chain' for d in f['draws']) for f in b['nativeAudit']),
                                'maxEndpointShiftMetres': float(endpoint_shift), 'launchWidth': .51, 'chainWidth': .30}

    # THU_01 has no actor-to-actor links. Its complete replay must stay visually
    # equivalent to the restored version, not merely share gameplay parameters.
    deltas = []
    for i in range(report(CURRENT, 'THU_01')['frames']):
        a = np.asarray(Image.open(PREVIOUS / 'THU_01' / f'{i:03d}.jpg'), dtype=float)
        b = np.asarray(Image.open(CURRENT / 'THU_01' / f'{i:03d}.jpg'), dtype=float)
        deltas.append(float(np.abs(a - b).mean()))
    assert max(deltas) < 1.0, max(deltas)
    data['unchangedSingleTargetReplay'] = {'frames': len(deltas), 'maxMeanAbsoluteRGBDelta': max(deltas)}

    yy, xx = np.indices((470, 960))
    for shot, (peak, first, last) in {
        'THU_02': (16, (329, 308), (585, 154)),
        'THU_05': (22, (338, 330), (573, 163)),
    }.items():
        first, last = np.array(first), np.array(last)
        delta = last - first
        q = np.stack([xx - first[0], yy - first[1]], axis=-1)
        t = (q @ delta) / (delta @ delta)
        side = np.abs(q[..., 0] * delta[1] - q[..., 1] * delta[0]) / np.linalg.norm(delta)
        region = (t > .12) & (t < .72) & (side < 38)
        counts = []
        for root in [PREVIOUS, CURRENT]:
            image = np.asarray(Image.open(root / shot / f'{peak:03d}.jpg'), dtype=np.int16)
            idle = np.asarray(Image.open(root / shot / '000.jpg'), dtype=np.int16)
            visible = region & (image[..., 2] - idle[..., 2] > 14)
            visible &= (image[..., 2] - image[..., 0] > 10) | (image.min(axis=-1) > 235)
            counts.append(int(visible.sum()))
        assert counts[0] > 500 and .90 < counts[1] / counts[0] < 1.10, (shot, counts)
        data['shots'][shot]['launchVisibilityPixels'] = {'before': counts[0], 'after': counts[1], 'region': 'Mid-trunk, excluding the target network'}
    return data


def template(shot, compare=True):
    size = (1920, 626) if compare else (960, 574)
    out = Image.new('RGB', size, '#181b20')
    d = ImageDraw.Draw(out)
    review.label(d, (24, 30), '雷系 / ' + SCENES[shot], 29, '#c5ccff', True)
    review.label(d, (size[0] - 24, 31), '人物间连锁电弧 · 设计预览', 19, '#a9afbd', anchor='rm')
    if compare:
        review.label(d, (24, 73), '恢复版', 21, '#a9afbd', True)
        review.label(d, (968, 73), '连接同样式 · 更细', 21, '#c5ccff', True)
        review.label(d, (24, 591), '施法主弧保持恢复版；人物间采用相同白芯与蓝紫柔光，宽度约为主弧六成。', 21)
    else:
        review.label(d, (20, 548), '主弧保留 · 人物间连接同样式、更细 · 实际连锁目标', 18)
    return out


review.template = template


def previews():
    shot, poster = 'THU_05', 22
    count = report(CURRENT, shot)['frames']
    frames = [review.frame(shot, i, True).resize((1152, 376), Image.Resampling.LANCZOS) for i in range(count)]
    durations = [(round((i + 1) * 100 / 30) - round(i * 100 / 30)) * 10 for i in range(count)]
    frames, durations = frames[poster:] + frames[:poster], durations[poster:] + durations[:poster]
    sample = Image.new('RGB', (576, 564))
    for j, i in enumerate([0, 9, count // 2]):
        sample.paste(frames[i].resize((576, 188)), (0, j * 188))
    colors = [(r, g, b) for r, g, b in sample.get_flattened_data() if b > r + 8 and b > g + 4]
    electric = Image.new('RGB', (256, (len(colors) + 255) // 256))
    electric.putdata(colors + [colors[-1]] * (electric.width * electric.height - len(colors)))
    palette = sample.quantize(192, method=Image.Quantize.MEDIANCUT)
    blue = electric.quantize(64, method=Image.Quantize.MEDIANCUT)
    palette.putpalette(palette.getpalette()[:576] + blue.getpalette()[:192])
    indexed = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    indexed[0].save(MEDIA / 'chain-preview.gif', save_all=True, append_images=indexed[1:], duration=durations, loop=0, optimize=False)
    review.frame(shot, poster, True).save(MEDIA / 'chain-comparison.jpg', quality=95, subsampling=0)

    board = Image.new('RGB', (1400, 570), '#181b20')
    d = ImageDraw.Draw(board)
    review.label(d, (20, 30), '人物之间的连接 · 同样式，更细', 28, '#c5ccff', True)
    for col, (root, label) in enumerate([(PREVIOUS, '恢复版'), (CURRENT, '白芯与蓝紫柔光 · 约为主弧六成宽')]):
        review.label(d, (20 + col * 700, 75), label, 22, '#c5ccff', True)
        with Image.open(root / shot / f'{poster:03d}.jpg') as src:
            crop = src.crop((470, 10, 780, 220)).resize((680, 461), Image.Resampling.LANCZOS)
            board.paste(crop, (10 + col * 700, 100))
    board.save(MEDIA / 'chain-detail.jpg', quality=96, subsampling=0)


def main():
    MEDIA.mkdir(exist_ok=True)
    checks = validate_captures()
    review.video('chain-design.mp4', False)
    review.video('chain-comparison.mp4', True)
    previews()
    for name in ['chain-design.mp4', 'chain-comparison.mp4']:
        with av.open(str(MEDIA / name)) as movie:
            stream = movie.streams.video[0]
            frames = sum(1 for _ in movie.decode(video=0))
            assert frames == 134 and stream.average_rate == 30 and len(movie.chapters()) == 2
    with Image.open(MEDIA / 'chain-preview.gif') as gif:
        elapsed = 0
        for i in range(gif.n_frames):
            gif.seek(i)
            elapsed += gif.info['duration']
        assert gif.n_frames == 77 and elapsed == 2570
    evidence = {'status': 'Design review candidate', 'scope': 'Actor-to-actor chain arcs only',
                'productionState': 'No production game code changed', 'nativeCaptureValidation': checks,
                'artwork': 'Same approved atlas as the restored version; chain arcs now select its launch-style band at smaller width',
                'validationScope': 'Local Cocos Web capture; no TapTap device performance claim',
                'files': {str(p.relative_to(HERE)): sha(p) for p in HERE.rglob('*') if p.is_file() and p.name != 'provenance.json'}}
    (HERE / 'provenance.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(checks, ensure_ascii=False))


if __name__ == '__main__':
    main()
