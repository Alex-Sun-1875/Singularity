"""Package actual Cocos captures; never paint lightning into recorded frames."""
import hashlib
import json
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import av
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MEDIA = HERE / 'media'
CACHES = {
    'previous': ROOT / 'src/.tmp/current-vfx-refinement-v4/final/refined',
    'revised': ROOT / 'src/.tmp/thunder-reference-v5/final/refined',
}
SHOTS = {'THU_01': '贯雷长矛', 'THU_02': '连锁雷弧', 'THU_05': '万钧雷潮'}
REFERENCE = HERE.parent / 'four-class-vfx-redesign-v1/references/user-selected-first-board-v5.png'
FPS = 30


@lru_cache(maxsize=12)
def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('msyhbd.ttc' if bold else 'msyh.ttc'), size)


def label(draw, xy, text, size=22, color='#e5e6ed', bold=False, anchor='lm'):
    draw.text(xy, text, font=font(size, bold), fill=color, anchor=anchor)


def report(variant, shot):
    return json.loads((CACHES[variant] / shot / 'capture.json').read_text(encoding='utf8'))


def verify_captures():
    for shot in SHOTS:
        a, b = [report(v, shot) for v in CACHES]
        for key in ['gameHash', 'frames', 'events']:
            assert a[key] == b[key], (shot, key)
        for key in ['origin', 'targets', 'geometry', 'skillGeometry']:
            assert a['info'].get(key) == b['info'].get(key), (shot, key)
        assert a['presentation'] == b['presentation'], shot
        for name, digest in b['reviewInputs'].items():
            assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, (shot, name)
        for variant, data in [('previous', a), ('revised', b)]:
            assert not data['errors'] and data['info']['player']['skeletons'], shot
            assert len(list((CACHES[variant] / shot).glob('*.jpg'))) == data['frames'], shot


def template(shot, compare=True):
    width, height = (1920, 626) if compare else (960, 574)
    out = Image.new('RGB', (width, height), '#181b20')
    d = ImageDraw.Draw(out)
    label(d, (24, 30), '雷系 / ' + SHOTS[shot], 29, '#c5ccff', True)
    label(d, (width - 24, 31), '2D 设计语言 · 3D 动态审稿', 19, '#a9afbd', anchor='rm')
    if compare:
        label(d, (24, 73), '上一版动态稿', 21, '#a9afbd', True)
        label(d, (968, 73), '按 2D 稿修订', 21, '#c5ccff', True)
        d.line((24, 559, 1896, 559), fill='#454a58')
        label(d, (24, 591), '白亮主干 · 浅蓝过渡 · 蓝紫柔光 · 不规则分叉', 22)
        label(d, (1896, 590), '同机位 / 原速', 17, '#a9afbd', anchor='rm')
    else:
        label(d, (20, 548), '白亮主干 · 浅蓝过渡 · 蓝紫柔光 · 不规则分叉', 19)
    return out


def frame(shot, index, compare=True):
    out = template(shot, compare)
    for col, variant in enumerate(CACHES if compare else ['revised']):
        with Image.open(CACHES[variant] / shot / f'{index:03d}.jpg') as src:
            size = (928, 454) if compare else (960, 470)
            out.paste(src.resize(size, Image.Resampling.LANCZOS), (24 + 944 * col, 96) if compare else (0, 57))
    return out


def video(filename, compare):
    chapters = []
    start = 0
    for shot in SHOTS:
        count = report('revised', shot)['frames']
        chapters.append({'id': len(chapters), 'time_base': Fraction(1, FPS), 'start': start,
                         'end': start + count, 'metadata': {'title': SHOTS[shot]}})
        start += count
    with av.open(str(MEDIA / filename), 'w', format='mp4', options={'movflags': '+faststart'}) as movie:
        movie.set_chapters(chapters)
        stream = movie.add_stream('libx264', rate=FPS)
        stream.width, stream.height = (1920, 626) if compare else (960, 574)
        stream.pix_fmt = 'yuv420p'
        stream.codec_context.thread_count = 3
        stream.options = {'crf': '16', 'preset': 'veryfast'}
        pts = 0
        for shot in SHOTS:
            for i in range(report('revised', shot)['frames']):
                vf = av.VideoFrame.from_image(frame(shot, i, compare))
                vf.pts, vf.time_base = pts, Fraction(1, FPS)
                for packet in stream.encode(vf):
                    movie.mux(packet)
                pts += 1
        for packet in stream.encode():
            movie.mux(packet)


def previews():
    shot, poster = 'THU_02', 16
    count = report('revised', shot)['frames']
    frames = [frame(shot, i).resize((1152, 376), Image.Resampling.LANCZOS) for i in range(count)]
    durations = [(round((i + 1) * 100 / FPS) - round(i * 100 / FPS)) * 10 for i in range(count)]
    frames, durations = frames[poster:] + frames[:poster], durations[poster:] + durations[:poster]
    sample = Image.new('RGB', (576, 564))
    for j, i in enumerate([0, 9, count // 2]):
        sample.paste(frames[i].resize((576, 188)), (0, j * 188))
    # Reserve palette entries for the small blue effect; terrain otherwise uses
    # the whole GIF palette and turns the electric corona into grey bands.
    electric = [(r, g, b) for r, g, b in sample.getdata() if b > r + 8 and b > g + 4]
    assert electric
    electric_sample = Image.new('RGB', (256, (len(electric) + 255) // 256))
    electric_sample.putdata(electric + [electric[-1]] * (electric_sample.width * electric_sample.height - len(electric)))
    palette = sample.quantize(192, method=Image.Quantize.MEDIANCUT)
    electric_palette = electric_sample.quantize(64, method=Image.Quantize.MEDIANCUT)
    palette.putpalette(palette.getpalette()[:192 * 3] + electric_palette.getpalette()[:64 * 3])
    indexed = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    indexed[0].save(MEDIA / 'thunder-comparison.gif', save_all=True, append_images=indexed[1:],
                    duration=durations, loop=0, optimize=False)
    frame(shot, poster).save(MEDIA / 'thunder-comparison.jpg', quality=95, subsampling=0)

    board = Image.new('RGB', (1568, 444), '#181b20')
    d = ImageDraw.Draw(board)
    label(d, (24, 31), '雷系电弧 · 沿用 2D 设计语言', 30, '#c5ccff', True)
    label(d, (24, 71), '白亮主干向浅蓝、蓝紫柔光渐隐，保留相连的弯折和分叉。', 21)
    with Image.open(REFERENCE) as src:
        panels = [src.crop((774, 514, 1518, 958)).convert('RGB')]
    for variant in CACHES:
        with Image.open(CACHES[variant] / shot / f'{poster:03d}.jpg') as src:
            panels.append(src.crop((200, 0, 900, 430)).convert('RGB'))
    for col, (panel, title) in enumerate(zip(panels, ['2D 设计参考', '上一版 3D 动态稿', '本轮 3D 修订稿'])):
        x = 16 + col * 520
        label(d, (x + 8, 110), title, 22, '#c5ccff' if col != 1 else '#a9afbd', True)
        panel = ImageOps.contain(panel, (496, 298), Image.Resampling.LANCZOS)
        board.paste(panel, (x + (504 - panel.width) // 2, 134 + (298 - panel.height) // 2))
    board.save(MEDIA / 'reference-comparison.jpg', quality=96, subsampling=0)


def validate_media():
    total = sum(report('revised', shot)['frames'] for shot in SHOTS)
    result = {}
    for filename in ['previous-vs-revised.mp4', 'revised-full-size.mp4']:
        with av.open(str(MEDIA / filename)) as movie:
            stream = movie.streams.video[0]
            decoded = sum(1 for _ in movie.decode(video=0))
            assert decoded == total and stream.average_rate == FPS, filename
            assert len(movie.chapters()) == len(SHOTS), filename
            result[filename] = {'frames': decoded, 'fps': FPS, 'seconds': total / FPS,
                                'size': [stream.width, stream.height], 'chapters': len(movie.chapters())}
    with Image.open(MEDIA / 'thunder-comparison.gif') as gif:
        durations = []
        for i in range(gif.n_frames):
            gif.seek(i)
            durations.append(gif.info['duration'])
        assert gif.n_frames == 57 and sum(durations) == 1900
        result['thunder-comparison.gif'] = {'frames': gif.n_frames, 'durationMs': sum(durations)}
    return result


def provenance(validation):
    data = {'stage': 'Design review, awaiting user art approval', 'source': 'Actual current Cocos 3D scene',
            'gameHash': report('revised', 'THU_01')['gameHash'],
            'reference': str(REFERENCE.relative_to(ROOT)),
            'referenceSha256': hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
            'previousDraft': '../current-vfx-refinement-v4',
            'scope': 'Lightning presentation only, served by a disposable review recorder',
            'artDirection': 'White-hot trunk, pale blue transition, soft blue-violet corona, connected irregular forks',
            'renderer': 'Existing ThunderArcField dynamic mesh pool, one vertex-colored cross-section for each real arc path',
            'gameplayValidation': 'Exact event, origin, target, geometry and camera equality for all three captures',
            'generation': 'No image generation; native rendering and deterministic editorial layout only',
            'platformValidation': 'Local Web capture only; TapTap device art and performance review pending',
            'meteorSealRule': 'FIR_02 only', 'shots': [], 'mediaValidation': validation}
    for shot in SHOTS:
        r = report('revised', shot)
        data['shots'].append({'skill': shot, 'frames': r['frames'], 'events': r['events'],
                               'reviewInputs': r['reviewInputs'], 'camera': r['presentation']['camera']})
    data['files'] = {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in HERE.rglob('*') if p.is_file() and p.name != 'provenance.json'}
    (HERE / 'provenance.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


if __name__ == '__main__':
    MEDIA.mkdir(exist_ok=True)
    verify_captures()
    video('previous-vs-revised.mp4', True)
    video('revised-full-size.mp4', False)
    previews()
    validation = validate_media()
    provenance(validation)
    print(json.dumps(validation, ensure_ascii=False))
