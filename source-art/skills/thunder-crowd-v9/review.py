"""Audit actual crowd cast events and package the unmodified native frames."""
import hashlib
import json
import math
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / 'src/.tmp/thunder-crowd-v9/final/refined'
MEDIA = HERE / 'media'
CASES = {'NETWORK_R1': '12 只怪物 · 雷网 1 级', 'NETWORK_R5': '12 只怪物 · 雷网 5 级', 'CHAIN_R5': '12 只怪物 · 连锁 5 级'}


@lru_cache(maxsize=16)
def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('msyhbd.ttc' if bold else 'msyh.ttc'), size)


def label(d, xy, text, size=22, fill='#e6e9ef', bold=False, anchor='lm'):
    d.text(xy, text, font=font(size, bold), fill=fill, anchor=anchor)


def read(case):
    return json.loads((CACHE / case / 'capture.json').read_text(encoding='utf8'))


def distance(a, b):
    return math.hypot(a['x'] - b['x'], a['z'] - b['z'])


def audit(case):
    r = read(case)
    assert not r['errors'] and len(r['info']['targets']) == 12
    for name, expected in r['reviewInputs'].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == expected, name
    assert len(list((CACHE / case).glob('*.jpg'))) == r['frames']
    enemies = {t['id']: t for t in r['info']['targets']}
    events = [x['event'] for x in r['logicEvents']]
    skill = r['shot']
    hits = [e for e in events if e['type'] == 'skill_hit' and e.get('skillId') == skill]
    graph = [e for e in events if e['type'] == 'skill_segment' and e.get('skillId') == skill and e.get('targetId') in enemies and e.get('to')]
    misses = {e['id'] for e in events if e['type'] == 'miss' and e.get('id') in enemies}
    damaged = {e['targetId'] for e in hits}
    missed = misses - damaged
    selected = {n for snapshot in r['castSnapshots'] for n in snapshot['targets'] if n in enemies}
    nodes = {e[k] for e in graph for k in ['sourceId', 'targetId'] if e.get(k) in enemies}
    selected |= nodes | misses
    rule = r['info']['rule']
    limit = rule['geometry'].get('totalTargetLimit', rule['targetLimit'])
    hop = rule['connectionRadiusMetres']
    assert len(selected) <= limit, (case, selected, limit)
    pairs, loops, direct = set(), [], []
    violations = []
    for enemy in selected:
        if distance(enemies[enemy], r['info']['aim']) > rule['geometry']['radiusMetres'] + .001:
            violations.append({'type': 'selectionOutsideRadius', 'target': enemy})
    for e in graph:
        source, target, segment = e.get('sourceId'), e['targetId'], e.get('segment', 0)
        if source not in enemies:
            continue
        pair = (segment, *sorted([source, target]))
        if pair in pairs:
            violations.append({'type': 'duplicatePair', 'pair': pair})
        pairs.add(pair)
        if source == target or distance(e['from'], e['to']) > hop + .001:
            violations.append({'type': 'invalidConnection', 'event': e})
        same_hit = any(h.get('segment', 0) == segment and h['targetId'] == target and distance(h['from'], e['from']) < 1e-6 for h in hits)
        row = {'segment': segment, 'source': source, 'target': target, 'from': e['from'], 'to': e['to']}
        (direct if same_hit else loops).append(row)
    for segment in {h.get('segment', 0) for h in hits}:
        ids = {h['targetId'] for h in hits if h.get('segment', 0) == segment}
        assert len(ids) <= limit
        assert all(sum(h['targetId'] == enemy and h.get('segment', 0) == segment for h in hits) == 1 for enemy in ids)
    relay = {e['sourceId'] for e in graph if e.get('sourceId') in missed}
    first_direct = [e for e in direct if e['segment'] == 0]
    first_loops = [e for e in loops if e['segment'] == 0]
    first_edges = first_direct + first_loops
    crossings = []
    cross = lambda u, v: u[0] * v[1] - u[1] * v[0]
    for i, a in enumerate(first_edges):
        for b in first_edges[i + 1:]:
            if {a['source'], a['target']} & {b['source'], b['target']}:
                continue
            p = np.array([a['from']['x'], a['from']['z']])
            q = np.array([b['from']['x'], b['from']['z']])
            u = np.array([a['to']['x'], a['to']['z']]) - p
            v = np.array([b['to']['x'], b['to']['z']]) - q
            determinant = cross(u, v)
            if abs(determinant) < 1e-9:
                continue
            t, s = cross(q - p, v) / determinant, cross(q - p, u) / determinant
            if .01 < t < .99 and .01 < s < .99:
                at = p + t * u
                crossings.append({'a': [a['source'], a['target']], 'b': [b['source'], b['target']], 'at': {'x': float(at[0]), 'z': float(at[1])}})
    endpoint_shift = max([math.dist(d['sourceFrom'], d['renderFrom']) + math.dist(d['sourceTo'], d['renderTo'])
                          for f in r['nativeAudit'] for d in f['draws'] if d['role'] == 'chain'], default=0)
    near_spectators = []
    peak = 22 if case.startswith('NETWORK') else 16
    for draw in r['nativeAudit'][peak]['draws']:
        if not draw['role'].endswith('Detail'):
            continue
        for enemy, target in enemies.items():
            if enemy in selected:
                continue
            separation = math.hypot(draw['renderTo'][0] - target['x'], draw['renderTo'][2] - target['z'])
            if separation < .45:
                near_spectators.append({'target': enemy, 'number': target['number'], 'role': draw['role'], 'distanceMetres': separation})
    assert endpoint_shift < 1e-6 and not violations, (case, endpoint_shift, violations)
    return {'case': case, 'rank': r['info']['skillRank'], 'monsterCount': 12, 'targetLimit': limit,
            'radiusMetres': rule['geometry']['radiusMetres'], 'connectionRadiusMetres': hop,
            'selected': sorted(selected), 'damaged': sorted(damaged), 'missed': sorted(missed),
            'missedRelayNodes': sorted(relay), 'firstBeatDamageEdges': first_direct, 'firstBeatVisualLoopEdges': first_loops,
            'firstBeatCrossings': crossings, 'connectionViolations': violations,
            'decorativeEndsNearUnselected': near_spectators,
            'renderEndpointShiftMetres': endpoint_shift, 'maxRenderedChains': max(sum(d['role'] == 'chain' for d in f['draws']) for f in r['nativeAudit'])}


def graph_image(case, result):
    r = read(case)
    out = Image.new('RGB', (1280, 850), '#171c24')
    d = ImageDraw.Draw(out)
    label(d, (25, 33), CASES[case] + ' · 怪物间实测连接图', 28, '#c7d2ff', True)
    label(d, (25, 73), '蓝线：伴随实际伤害的连线　金色虚线：补充视觉连线　红边节点：本次 MISS', 19)
    origin, aim = r['info']['origin'], r['info']['aim']
    dx, dz = aim['x'] - origin['x'], aim['z'] - origin['z']
    scale = math.hypot(dx, dz)
    fx, fz, sx, sz = dx / scale, dz / scale, dz / scale, -dx / scale

    def project(p):
        x, z = p['x'] - origin['x'], p['z'] - origin['z']
        return 470 + (x * sx + z * sz) * 62, 765 - (x * fx + z * fz) * 62

    targets = {t['id']: t for t in r['info']['targets']}
    for edge in result['firstBeatDamageEdges'] + result['firstBeatVisualLoopEdges']:
        a, b = project(edge['from']), project(edge['to'])
        if edge in result['firstBeatDamageEdges']:
            d.line((a, b), fill='#9ab9ff', width=3)
        else:
            length = math.dist(a, b)
            for step in range(0, int(length), 15):
                ta, tb = step / length, min(1, (step + 8) / length)
                d.line((a[0] + (b[0] - a[0]) * ta, a[1] + (b[1] - a[1]) * ta,
                        a[0] + (b[0] - a[0]) * tb, a[1] + (b[1] - a[1]) * tb), fill='#efbf75', width=2)
    selected = set(result['selected'])
    missed = set(result['missed'])
    for enemy, target in targets.items():
        x, y = project(target)
        color = '#ff8d8d' if enemy in missed else '#b7caff' if enemy in selected else '#6e7785'
        d.ellipse((x - 18, y - 18, x + 18, y + 18), fill='#26354c' if enemy in selected else '#1c222c', outline=color, width=3)
        label(d, (x, y), str(target['number']), 18, color, True, 'mm')
    px, py = project(origin)
    d.polygon([(px, py - 13), (px - 12, py + 10), (px + 12, py + 10)], fill='#e1c492')
    label(d, (px, py + 32), '施法者', 19, '#e1c492', anchor='mm')
    x = 920
    rows = ['规则与首拍记录', f"场内怪物：{len(targets)}", f"目标上限：{result['targetLimit']}",
            f"本次选中：{len(selected)}", f"受到伤害：{len(result['damaged'])}",
            f"MISS：{len(missed)}", f"伤害连线：{len(result['firstBeatDamageEdges'])}",
            f"补充视觉线：{len(result['firstBeatVisualLoopEdges'])}", f"直线几何交叉：{len(result['firstBeatCrossings'])}",
            f"MISS 中继节点：{len(result['missedRelayNodes'])}", f"连接半径：{result['connectionRadiusMetres']} 米"]
    for i, text in enumerate(rows):
        label(d, (x, 130 + i * 42), text, 24 if i == 0 else 21, '#c7d2ff' if i == 0 else '#e6e9ef', i == 0)
    label(d, (25, 818), '仅画怪物间事件连线；不是额外伤害或游戏内范围圈。电弧曲线的视觉交叠可能更多。', 18, '#a9b3c3')
    out.save(MEDIA / (case.lower() + '-connections.jpg'), quality=95, subsampling=0)


def frame(case, index, result, numbered=False):
    out = Image.new('RGB', (1280, 754), '#171c24')
    d = ImageDraw.Draw(out)
    label(d, (22, 30), CASES[case], 27, '#c7d2ff', True)
    label(d, (1258, 30), '当前 3D 录制 · 原速', 18, '#a9b3c3', anchor='rm')
    with Image.open(CACHE / case / f'{index:03d}.jpg') as source:
        out.paste(source.convert('RGB'), (0, 64))
    label(d, (22, 722), f"场内 12 只 · 目标上限 {result['targetLimit']} · 本次选中 {len(result['selected'])} · MISS {len(result['missed'])}", 21)
    if numbered:
        for target in read(case)['presentation']['targets']:
            x, y = target['label']
            color = '#ff9292' if target['id'] in result['missed'] else '#b5cbff' if target['id'] in result['selected'] else '#c8c9c8'
            d.ellipse((x - 13, y + 64 - 13, x + 13, y + 64 + 13), fill='#171c24', outline=color, width=2)
            label(d, (x, y + 64), str(target['number']), 16, color, True, 'mm')
    return out


def main():
    MEDIA.mkdir(exist_ok=True)
    results = {case: audit(case) for case in CASES}
    for case in CASES:
        graph_image(case, results[case])
        frame(case, 22 if case.startswith('NETWORK') else 16, results[case], True).save(MEDIA / (case.lower() + '-numbered.jpg'), quality=95, subsampling=0)
    for name in ['refine-modules.cjs', 'beam-batches.ts', 'approved-thunder-strip.png', 'reference-profile.json']:
        assert (HERE / name).read_bytes() == (HERE.parent / 'thunder-chain-v8' / name).read_bytes(), name
    with av.open(str(MEDIA / 'crowd-review.mp4'), 'w', format='mp4', options={'movflags': '+faststart'}) as movie:
        stream = movie.add_stream('libx264', rate=30)
        stream.width, stream.height, stream.pix_fmt = 1280, 754, 'yuv420p'
        stream.codec_context.thread_count = 3
        stream.options = {'crf': '16', 'preset': 'veryfast'}
        movie.set_chapters([{'id': i, 'time_base': Fraction(1, 30), 'start': i * 90, 'end': (i + 1) * 90, 'metadata': {'title': name}} for i, name in enumerate(CASES.values())])
        pts = 0
        for case in CASES:
            for index in range(read(case)['frames']):
                vf = av.VideoFrame.from_image(frame(case, index, results[case]))
                vf.pts, vf.time_base = pts, Fraction(1, 30)
                for packet in stream.encode(vf):
                    movie.mux(packet)
                pts += 1
        for packet in stream.encode():
            movie.mux(packet)
    case, poster = 'NETWORK_R5', 22
    frames = [frame(case, i, results[case]).resize((960, 566), Image.Resampling.LANCZOS) for i in range(90)]
    frames = frames[poster:] + frames[:poster]
    durations = [(round((i + 1) * 100 / 30) - round(i * 100 / 30)) * 10 for i in range(90)]
    durations = durations[poster:] + durations[:poster]
    sample = Image.new('RGB', (480, 849))
    for j, i in enumerate([0, 12, 40]):
        sample.paste(frames[i].resize((480, 283)), (0, j * 283))
    electric_pixels = [(r, g, b) for r, g, b in sample.get_flattened_data() if b > r + 8 and b > g + 4]
    electric = Image.new('RGB', (256, (len(electric_pixels) + 255) // 256))
    electric.putdata(electric_pixels + [electric_pixels[-1]] * (electric.width * electric.height - len(electric_pixels)))
    palette, blues = sample.quantize(192, method=Image.Quantize.MEDIANCUT), electric.quantize(64, method=Image.Quantize.MEDIANCUT)
    palette.putpalette(palette.getpalette()[:576] + blues.getpalette()[:192])
    indexed = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    indexed[0].save(MEDIA / 'crowd-preview.gif', save_all=True, append_images=indexed[1:], duration=durations, loop=0, optimize=False)
    with av.open(str(MEDIA / 'crowd-review.mp4')) as movie:
        assert sum(1 for _ in movie.decode(video=0)) == 270
        assert len(movie.chapters()) == 3
    evidence = {'scope': 'Crowd preview and audit of existing connection behavior; no rule changes',
                'renderSource': 'Native Cocos session, real casts, damage and graph events',
                'productionState': 'No production code changed', 'cases': results,
                'files': {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.rglob('*') if p.is_file() and p.name != 'provenance.json'}}
    (HERE / 'provenance.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: {'selected': len(v['selected']), 'damaged': len(v['damaged']), 'missed': len(v['missed']), 'damageEdges': len(v['firstBeatDamageEdges']), 'visualLoops': len(v['firstBeatVisualLoopEdges']), 'crossings': len(v['firstBeatCrossings']), 'missRelays': v['missedRelayNodes'], 'violations': len(v['connectionViolations'])} for k, v in results.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
