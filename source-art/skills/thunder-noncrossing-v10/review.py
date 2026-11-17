"""Audit the nearest, degree-two, noncrossing design preview and native frames."""
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
CACHE = ROOT / 'src/.tmp/thunder-noncrossing-v10/validated/refined'
MEDIA = HERE / 'media'
CASES = {'NETWORK_R1': '12 只怪物 · 连锁规则 1 级', 'NETWORK_R5': '12 只怪物 · 连锁规则 5 级', 'CHAIN_R5': '12 只怪物 · 连锁闪电 5 级'}


@lru_cache(maxsize=16)
def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('msyhbd.ttc' if bold else 'msyh.ttc'), size)


def label(d, xy, text, size=22, fill='#e6e9ef', bold=False, anchor='lm'):
    d.text(xy, text, font=font(size, bold), fill=fill, anchor=anchor)


def read(case):
    return json.loads((CACHE / case / 'capture.json').read_text(encoding='utf8'))


def distance(a, b):
    return math.hypot(a['x'] - b['x'], a['z'] - b['z'])


def curve_crossings(draws):
    paths = [d for d in draws if d['role'] in ['launch', 'chain']]
    found = []
    for i, left in enumerate(paths):
        a = np.array(left['screenPath'])
        for j, right in enumerate(paths[i + 1:], i + 1):
            b = np.array(right['screenPath'])
            p, q = a[:-1, None, :], b[None, :-1, :]
            u, v = np.diff(a, axis=0)[:, None, :], np.diff(b, axis=0)[None, :, :]
            cross = lambda x, y: x[..., 0] * y[..., 1] - x[..., 1] * y[..., 0]
            det = cross(u, v)
            safe = np.where(np.abs(det) > 1e-8, det, np.nan)
            t, s = cross(q - p, v) / safe, cross(q - p, u) / safe
            mask = (t > .001) & (t < .999) & (s > .001) & (s < .999)
            for row, col in np.argwhere(mask):
                point = a[row] + t[row, col] * (a[row + 1] - a[row])
                shared = [x for x in [a[0], a[-1]] for y in [b[0], b[-1]] if np.linalg.norm(x-y) < 2]
                if any(np.linalg.norm(point-junction) < 18 for junction in shared):
                    continue
                found.append({'paths': [i,j], 'roles': [left['role'],right['role']], 'at': point.tolist()})
    return found


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
    unreached = selected - damaged - missed
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
    degrees = {}
    for e in graph:
        beat = e.get('segment', 0)
        if e.get('sourceId') in enemies:
            key = (beat, e['sourceId'])
            degrees[key] = degrees.get(key, 0) + 1
        key = (beat, e['targetId'])
        degrees[key] = degrees.get(key, 0) + 1
    max_degree = max(degrees.values(), default=0)
    choices = r['chainChoices']
    assert choices and all(c['targetId'] == c['candidates'][0]['id'] for c in choices)
    assert all(all(a['distance'] <= b['distance'] + 1e-7 for a, b in zip(c['candidates'][1:] if c['targetedEntry'] else c['candidates'], c['candidates'][2:] if c['targetedEntry'] else c['candidates'][1:])) for c in choices)
    assert max_degree <= 2 and not crossings and not loops and not relay, (case, max_degree, crossings, loops, relay)
    visible_crossings = [{'frame': f['frame'], 'crossings': curve_crossings(f['draws'])} for f in r['nativeAudit']]
    visible_crossings = [f for f in visible_crossings if f['crossings']]
    assert not visible_crossings, (case, 'Visible curve crossings', visible_crossings[:2])
    assert endpoint_shift < 1e-6 and not violations, (case, endpoint_shift, violations)
    # Check actual pixels at the launch midpoint, rather than trusting draw calls.
    peak_draw = next(d for d in r['nativeAudit'][peak]['draws'] if d['role'] == 'launch')
    x, y = map(round, peak_draw['screenMid'])
    before = np.array(Image.open(CACHE / case / '000.jpg').convert('RGB'), dtype=np.int16)
    after = np.array(Image.open(CACHE / case / f'{peak:03d}.jpg').convert('RGB'), dtype=np.int16)
    delta = (after - before)[max(0,y-12):y+13,max(0,x-12):x+13]
    visible = int(np.count_nonzero(np.sum(np.maximum(delta, 0), axis=2) > 120))
    assert visible > 10, (case, 'Invisible launch despite draw calls', visible)
    return {'case': case, 'rank': r['info']['skillRank'], 'monsterCount': 12, 'targetLimit': limit,
            'radiusMetres': rule['geometry']['radiusMetres'], 'connectionRadiusMetres': hop,
            'selected': sorted(selected), 'damaged': sorted(damaged), 'missed': sorted(missed), 'notReachedWithoutCrossing': sorted(unreached),
            'firstBeatEntries': [e for e in graph if e.get('sourceId') not in enemies and e.get('segment',0)==0],
            'missedRelayNodes': sorted(relay), 'firstBeatDamageEdges': first_direct, 'firstBeatVisualLoopEdges': first_loops,
            'firstBeatCrossings': crossings, 'visibleCurveCrossings': visible_crossings, 'maxConnectionsPerTargetIncludingEntry': max_degree, 'launchMidpointVisiblePixels': visible, 'nearestChoiceCount': len(choices), 'connectionViolations': violations,
            'decorativeEndsNearUnselected': near_spectators,
            'renderEndpointShiftMetres': endpoint_shift, 'maxRenderedChains': max(sum(d['role'] == 'chain' for d in f['draws']) for f in r['nativeAudit'])}


def graph_image(case, result):
    r = read(case)
    out = Image.new('RGB', (1280, 850), '#171c24')
    d = ImageDraw.Draw(out)
    label(d, (25, 33), CASES[case] + ' · 就近传播路径', 28, '#c7d2ff', True)
    label(d, (25, 73), '蓝线：传播路径　蓝点：实际命中　红边：MISS　灰点：未连到', 19)
    origin, aim = r['info']['origin'], r['info']['aim']
    dx, dz = aim['x'] - origin['x'], aim['z'] - origin['z']
    scale = math.hypot(dx, dz)
    fx, fz, sx, sz = dx / scale, dz / scale, dz / scale, -dx / scale

    def project(p):
        x, z = p['x'] - origin['x'], p['z'] - origin['z']
        return 470 + (x * sx + z * sz) * 62, 765 - (x * fx + z * fz) * 62

    targets = {t['id']: t for t in r['info']['targets']}
    entries = [{'from':origin,'to':e['to']} for e in result['firstBeatEntries']]
    for edge in entries + result['firstBeatDamageEdges'] + result['firstBeatVisualLoopEdges']:
        a, b = project(edge['from']), project(edge['to'])
        if edge in entries or edge in result['firstBeatDamageEdges']:
            d.line((a, b), fill='#9ab9ff', width=3)
            dx,dy=b[0]-a[0],b[1]-a[1]
            length=math.hypot(dx,dy)
            if length>35:
                mx,my=a[0]+dx*.60,a[1]+dy*.60
                ux,uy=dx/length,dy/length
                d.polygon([(mx+ux*8,my+uy*8),(mx-ux*7-uy*5,my-uy*7+ux*5),(mx-ux*7+uy*5,my-uy*7-ux*5)], fill='#9ab9ff')
        else:
            length = math.dist(a, b)
            for step in range(0, int(length), 15):
                ta, tb = step / length, min(1, (step + 8) / length)
                d.line((a[0] + (b[0] - a[0]) * ta, a[1] + (b[1] - a[1]) * ta,
                        a[0] + (b[0] - a[0]) * tb, a[1] + (b[1] - a[1]) * tb), fill='#efbf75', width=2)
    selected = set(result['selected'])
    damaged = set(result['damaged'])
    missed = set(result['missed'])
    for enemy, target in targets.items():
        x, y = project(target)
        color = '#ff8d8d' if enemy in missed else '#b7caff' if enemy in damaged else '#6e7785'
        d.ellipse((x - 18, y - 18, x + 18, y + 18), fill='#26354c' if enemy in damaged else '#1c222c', outline=color, width=3)
        label(d, (x, y), str(target['number']), 18, color, True, 'mm')
    px, py = project(origin)
    d.polygon([(px, py - 13), (px - 12, py + 10), (px + 12, py + 10)], fill='#e1c492')
    label(d, (px, py + 32), '施法者', 19, '#e1c492', anchor='mm')
    x = 920
    rows = ['规则与首拍记录', f"场内怪物：{len(targets)}", f"目标上限：{result['targetLimit']}",
            f"候选目标：{len(selected)}", f"受到伤害：{len(result['damaged'])}",
            f"MISS：{len(missed)}", f"伤害连线：{len(result['firstBeatDamageEdges'])}",
            f"最多连接：{result['maxConnectionsPerTargetIncludingEntry']} 条", f"直线几何交叉：{len(result['firstBeatCrossings'])}",
            f"MISS 中继节点：{len(result['missedRelayNodes'])}", f"连接半径：{result['connectionRadiusMetres']} 米"]
    for i, text in enumerate(rows):
        label(d, (x, 130 + i * 42), text, 24 if i == 0 else 21, '#c7d2ff' if i == 0 else '#e6e9ef', i == 0)
    label(d, (25, 818), '设计预览：近邻优先、最多两条、不交叉、不额外闭环。沿用当前角色动作与命中判定。', 18, '#a9b3c3')
    out.save(MEDIA / (case.lower() + '-connections.jpg'), quality=95, subsampling=0)


def frame(case, index, result, numbered=False):
    out = Image.new('RGB', (1280, 754), '#171c24')
    d = ImageDraw.Draw(out)
    label(d, (22, 30), CASES[case], 27, '#c7d2ff', True)
    label(d, (1258, 30), '就近 · 最多两条 · 不交叉', 18, '#a9b3c3', anchor='rm')
    with Image.open(CACHE / case / f'{index:03d}.jpg') as source:
        out.paste(source.convert('RGB'), (0, 64))
    label(d, (22, 722), f"场内 12 只 · 目标上限 {result['targetLimit']} · 实际命中 {len(result['damaged'])} · MISS {len(result['missed'])} · 无合法延伸即停止", 20)
    if numbered:
        for target in read(case)['presentation']['targets']:
            x, y = target['label']
            color = '#ff9292' if target['id'] in result['missed'] else '#b5cbff' if target['id'] in result['damaged'] else '#c8c9c8'
            d.ellipse((x - 13, y + 64 - 13, x + 13, y + 64 + 13), fill='#171c24', outline=color, width=2)
            label(d, (x, y + 64), str(target['number']), 16, color, True, 'mm')
    return out


def comparison_image():
    before = ROOT / 'src/.tmp/thunder-crowd-v9/probe/refined/NETWORK_R5/022.jpg'
    after = CACHE / 'NETWORK_R5/022.jpg'
    out = Image.new('RGB', (1920, 610), '#171c24')
    d = ImageDraw.Draw(out)
    label(d, (24, 34), '原规则：近邻连通后额外补网', 27, '#c7d2ff', True)
    label(d, (984, 34), '约束试验：每个目标最多两条（非定稿）', 27, '#c7d2ff', True)
    for i, path in enumerate([before, after]):
        with Image.open(path) as source:
            out.paste(source.convert('RGB').resize((960,470),Image.Resampling.LANCZOS),(i*960,72))
    label(d, (24, 574), '同一 12 怪物场景 · 旧规则补线会交叉', 23)
    label(d, (984, 574), '虽减少交叉，却漏掉合法目标：不推荐统一采用', 23)
    out.save(MEDIA / 'crowd-comparison.jpg',quality=95,subsampling=0)


def main():
    MEDIA.mkdir(exist_ok=True)
    results = {case: audit(case) for case in CASES}
    for case in CASES:
        graph_image(case, results[case])
        frame(case, 22 if case.startswith('NETWORK') else 16, results[case], True).save(MEDIA / (case.lower() + '-numbered.jpg'), quality=95, subsampling=0)
    for name in ['approved-thunder-strip.png', 'reference-profile.json']:
        assert (HERE / name).read_bytes() == (HERE.parent / 'thunder-chain-v8' / name).read_bytes(), name
    comparison_image()
    counts = [read(case)['frames'] for case in CASES]
    starts = [sum(counts[:i]) for i in range(len(counts))]
    with av.open(str(MEDIA / 'crowd-review.mp4'), 'w', format='mp4', options={'movflags': '+faststart'}) as movie:
        stream = movie.add_stream('libx264', rate=30)
        stream.width, stream.height, stream.pix_fmt = 1280, 754, 'yuv420p'
        stream.codec_context.thread_count = 3
        stream.options = {'crf': '16', 'preset': 'veryfast'}
        movie.set_chapters([{'id': i, 'time_base': Fraction(1, 30), 'start': starts[i], 'end': starts[i]+counts[i], 'metadata': {'title': name}} for i, name in enumerate(CASES.values())])
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
    count = read(case)['frames']
    frames = [frame(case, i, results[case]).resize((960, 566), Image.Resampling.LANCZOS) for i in range(count)]
    frames = frames[poster:] + frames[:poster]
    durations = [(round((i + 1) * 100 / 30) - round(i * 100 / 30)) * 10 for i in range(count)]
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
        assert sum(1 for _ in movie.decode(video=0)) == sum(counts)
        assert len(movie.chapters()) == 3
    hashes={read(case)['gameHash'] for case in CASES}
    assert len(hashes)==1
    evidence = {'scope': 'Isolated design preview: nearest eligible next target, maximum degree two including caster entry, no crossing, no extra closure links, no MISS relay',
                'renderSource': 'Native Cocos session, real casts, damage and graph events',
                'productionState': 'No production code changed', 'compiledGameHash':next(iter(hashes)),
                'recommendationStatus':'Diagnostic only; reject universal degree-two traversal because it loses valid targets',
                'recommendedDirection':'Differentiate sequential chain from sparse branching pulse network; visual layout must not reduce the valid hit set; redesign timing and impact hierarchy',
                'artAcceptance':'Pending user review', 'platformValidation':'Local Cocos Web rendering only; no TapTap device claim',
                'nativeFrameCounts':dict(zip(CASES,counts)), 'cases': results,
                'captureLogs':{case:hashlib.sha256((CACHE/case/'capture.json').read_bytes()).hexdigest() for case in CASES},
                'files': {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.rglob('*') if p.is_file() and p.name != 'provenance.json' and '__pycache__' not in p.parts}}
    (HERE / 'provenance.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: {'selected': len(v['selected']), 'damaged': len(v['damaged']), 'missed': len(v['missed']), 'damageEdges': len(v['firstBeatDamageEdges']), 'visualLoops': len(v['firstBeatVisualLoopEdges']), 'crossings': len(v['firstBeatCrossings']), 'missRelays': v['missedRelayNodes'], 'violations': len(v['connectionViolations'])} for k, v in results.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
