#!/usr/bin/env python3
"""Summarize frames.json and optional WebKit events.json; never infer GPU time."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import statistics
import sys


def percentile(values, p):
    if not values:
        return None
    a = sorted(values)
    i = (len(a) - 1) * p
    return a[int(i)] + (a[min(int(i) + 1, len(a) - 1)] - a[int(i)]) * (i % 1)


def summarize(path):
    root = path if path.is_dir() else path.parent
    data = json.loads((root / 'frames.json' if path.is_dir() else path).read_text(encoding='utf-8-sig'))
    if isinstance(data, str):
        data = json.loads(data)
    frames = data['frames']
    elapsed = data['end'] - data['start']
    if elapsed <= 0 or len(frames) < 2 or any(not math.isfinite(x[0]) for x in frames):
        raise ValueError('Invalid or insufficient frame data')
    dt = [b[0] - a[0] for a, b in zip(frames, frames[1:])]
    if min(dt) < 0:
        raise ValueError('Non-monotonic frame clock')
    report = {'label': data['label'], 'durationMs': elapsed, 'frames': len(frames),
              'fps': len(frames) * 1000 / elapsed,
              'frameMs': {'p50': percentile(dt, .5), 'p95': percentile(dt, .95), 'p99': percentile(dt, .99), 'max': max(dt)},
              'tailWithoutFrameMs': max(0, elapsed - frames[-1][0]),
              'drawCallsMedian': statistics.median(x[1] for x in frames),
              'trianglesMedian': statistics.median(x[2] for x in frames),
              'gfxBytesLast': {'buffer': frames[-1][3], 'texture': frames[-1][4]},
              'baseline': data['baseline'], 'endState': data.get('endState'),
              'movingFrames': data['movingFrames'], 'actionFrames': data['actionFrames'],
              'truncated': data['truncated'], 'stopReason': data.get('stopReason'),
              'finalFrameRate': data.get('finalFrameRate'),
              'limits': ['GFX counters are allocations, not total host memory.', 'Frame time is not GPU duration.']}
    if (root / 'metadata.json').exists():
        metadata = json.loads((root / 'metadata.json').read_text(encoding='utf-8-sig'))
        report['profiled'] = metadata.get('profile')
        report['cleanup'] = metadata.get('cleanup')
        report['warnings'] = metadata.get('warnings', [])
        report['eventsDropped'] = metadata.get('eventsDropped')
    if (root / 'events.json').exists():
        events = json.loads((root / 'events.json').read_text(encoding='utf-8-sig'))
        cpu = [x['params']['event'] for x in events if x['method'] == 'CPUProfiler.trackingUpdate']
        if cpu:
            report['webInspectorCPU'] = {'samples': len(cpu), 'meanPercent': statistics.mean(x['usage'] for x in cpu),
                                       'timestampsAllZero': all(x.get('timestamp') == 0 for x in cpu),
                                       'scope': 'Selected WebInspector target, 100% = one core. Monitor window can extend beyond frame window; no per-frame alignment or time weighting.'}
        stacks = [s for e in events if e['method'] == 'ScriptProfiler.trackingComplete'
                  for s in e['params'].get('samples', {}).get('stackTraces', [])]
        if stacks:
            inclusive = Counter()
            for s in stacks:
                inclusive.update({(f.get('name'), f.get('url'), f.get('line'), f.get('column')) for f in s['stackFrames']})
            report['jsSamples'] = {'stacks': len(stacks), 'inclusiveTop': [
                {'name': key[0], 'url': key[1], 'line': key[2], 'column': key[3], 'samples': count,
                 'fraction': count / len(stacks)} for key, count in inclusive.most_common(25)],
                 'scope': 'Inclusive sample counts overlap; they are not elapsed milliseconds.'}
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('capture', type=Path, help='Capture directory or frames.json from collect.js')
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    result = json.dumps(summarize(a.capture), ensure_ascii=False, indent=2)
    if a.out:
        a.out.write_text(result + '\n', encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    print(result)


if __name__ == '__main__':
    main()
