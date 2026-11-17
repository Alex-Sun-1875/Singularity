"""Restore the visible previous review from its preserved native Cocos frames."""
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import av
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / 'src/.tmp/thunder-alignment-v7/previous-thicker'
MEDIA = HERE / 'media'
spec = importlib.util.spec_from_file_location('review_packaging', HERE.parent / 'thunder-fidelity-v6/media.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
review.MEDIA = MEDIA
review.CACHES = {'previous': CACHE, 'revised': CACHE}


def template(shot, compare=True):
    size = (1920, 626) if compare else (960, 574)
    out = Image.new('RGB', size, '#181b20')
    d = ImageDraw.Draw(out)
    review.label(d, (24, 30), '雷系 / ' + review.SHOTS[shot], 29, '#c5ccff', True)
    review.label(d, (size[0] - 24, 31), '已恢复上一版 · 设计预览', 19, '#a9afbd', anchor='rm')
    if compare:
        review.label(d, (24, 73), '上一版', 21, '#a9afbd', True)
        review.label(d, (968, 73), '恢复版本', 21, '#c5ccff', True)
        review.label(d, (24, 591), '两侧使用同一份已保存的原生录制，确认恢复画面一致。', 21)
    else:
        review.label(d, (20, 548), '恢复至此前能正常显示闪电的版本', 19)
    return out


review.template = template


def digest(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def main():
    MEDIA.mkdir(exist_ok=True)
    evidence = {'status': 'Restored at user request',
                'selection': 'The visible previous version shown on the left side of the comparison',
                'checkpoint': str(CACHE.relative_to(ROOT)),
                'deliveryState': 'Design preview only; no production game code was changed',
                'recording': 'Re-encoded preserved native Cocos checkpoint frames; no new runtime recording claimed',
                'withdrawnCandidate': 'withdrawn-review', 'shots': []}
    for shot in review.SHOTS:
        r = review.report('revised', shot)
        assert not r['errors'] and r['info']['player']['skeletons']
        assert len(list((CACHE / shot).glob('*.jpg'))) == r['frames']
        checks = {name: digest(HERE / name) == sha for name, sha in r['reviewInputs'].items()}
        assert all(checks.values()), (shot, checks)
        evidence['shots'].append({'skill': shot, 'frames': r['frames'], 'restoredInputEquality': checks})

    review.video('revised-full-size.mp4', False)
    shutil.copyfile(MEDIA / 'revised-full-size.mp4', MEDIA / 'restored-review.mp4')
    review.video('previous-vs-revised.mp4', True)

    shot, poster = 'THU_05', 22
    count = review.report('revised', shot)['frames']
    frames = [review.frame(shot, i, False).resize((768, 459), Image.Resampling.LANCZOS) for i in range(count)]
    durations = [(round((i + 1) * 100 / 30) - round(i * 100 / 30)) * 10 for i in range(count)]
    frames, durations = frames[poster:] + frames[:poster], durations[poster:] + durations[:poster]
    sample = Image.new('RGB', (384, 690))
    for j, i in enumerate([0, 9, count // 2]):
        sample.paste(frames[i].resize((384, 230)), (0, j * 230))
    colors = [(r, g, b) for r, g, b in sample.get_flattened_data() if b > r + 8 and b > g + 4]
    electric = Image.new('RGB', (256, (len(colors) + 255) // 256))
    electric.putdata(colors + [colors[-1]] * (electric.width * electric.height - len(colors)))
    palette = sample.quantize(192, method=Image.Quantize.MEDIANCUT)
    blue = electric.quantize(64, method=Image.Quantize.MEDIANCUT)
    palette.putpalette(palette.getpalette()[:576] + blue.getpalette()[:192])
    indexed = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    indexed[0].save(MEDIA / 'restored-preview.gif', save_all=True, append_images=indexed[1:], duration=durations, loop=0, optimize=False)
    shutil.copyfile(MEDIA / 'restored-preview.gif', MEDIA / 'thunder-comparison.gif')
    review.frame(shot, poster, False).save(MEDIA / 'restored-preview.jpg', quality=95, subsampling=0)
    shutil.copyfile(MEDIA / 'restored-preview.jpg', MEDIA / 'thunder-comparison.jpg')
    shutil.copyfile(MEDIA / 'restored-preview.jpg', MEDIA / 'reference-comparison.jpg')

    evidence['media'] = {}
    for name in ['restored-review.mp4', 'revised-full-size.mp4', 'previous-vs-revised.mp4']:
        with av.open(str(MEDIA / name)) as movie:
            stream = movie.streams.video[0]
            decoded = sum(1 for _ in movie.decode(video=0))
            assert decoded == 191 and stream.average_rate == 30
            evidence['media'][name] = {'frames': decoded, 'fps': 30, 'sha256': digest(MEDIA / name)}
    with Image.open(MEDIA / 'restored-preview.gif') as gif:
        elapsed = 0
        for i in range(gif.n_frames):
            gif.seek(i)
            elapsed += gif.info['duration']
        assert gif.n_frames == 77 and elapsed == 2570
    evidence['media']['restored-preview.gif'] = {'frames': 77, 'durationMs': 2570, 'sha256': digest(MEDIA / 'restored-preview.gif')}
    (HERE / 'restoration.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    (HERE / 'provenance.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'restored': True, 'skills': list(review.SHOTS), 'frames': 191, 'restoredInputEquality': True}))


if __name__ == '__main__':
    main()
