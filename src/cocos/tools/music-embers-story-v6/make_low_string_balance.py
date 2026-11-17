"""Lower only the V5 middle/low cello layers by 3dB at fixed mastering gain."""
from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
spec=importlib.util.spec_from_file_location('_soft_strings_v5',ROOT/'src/cocos/tools/music-embers-story-v5/make_music.py')
base=importlib.util.module_from_spec(spec);sys.modules[spec.name]=base;spec.loader.exec_module(base)
OUT=ROOT/'source-art/audio/embers-story-v6'
CELLO_DB=-3.
CELLO_GAIN=10**(CELLO_DB/20)
original_score=base.score


def score(mode):
    return [replace(n,level=n.level*CELLO_GAIN) if n.instrument.startswith('cello-') else n
            for n in original_score(mode)]


def main(track_prefix='embers-story-soft',preview_name='embers-story-soft-showcase',title='余烬叙事融合·中低弦减弱版'):
    before=json.loads((ROOT/'source-art/audio/embers-story-v5/manifest.json').read_text(encoding='utf-8'))
    gains={t['mode']:t['scalarGain'] for t in before['tracks'] if t['mode']!='aftermath'}
    base.music.FIXED_MASTER_GAINS=gains
    base.OUT=OUT;base.TRACK_PREFIX=track_prefix;base.PREVIEW_NAME=preview_name
    base.TITLE=title;base.score=score
    base.main()
    comparisons=[]
    for mode in ('explore','combat'):
        previous=json.loads((ROOT/f'source-art/audio/embers-story-v5/music-{mode}-score.json').read_text(encoding='utf-8'))['notes']
        current=json.loads((OUT/f'music-{mode}-score.json').read_text(encoding='utf-8'))['notes']
        if len(previous)!=len(current):raise ValueError('Score note count changed')
        changed=0
        for old,new in zip(previous,current):
            if {k:v for k,v in old.items() if k!='level'}!={k:v for k,v in new.items() if k!='level'}:
                raise ValueError('A note/timing/timbre/pan changed')
            if old['instrument'].startswith('cello-'):
                if abs(new['level']-old['level']*CELLO_GAIN)>1e-12:raise ValueError('Wrong cello gain')
                changed+=1
            elif new['level']!=old['level']:raise ValueError('Another instrument changed')
        comparisons.append(dict(mode=mode,loweredCelloNotes=changed,allOtherNoteDataUnchanged=True,fixedMasterGain=gains[mode]))
    path=OUT/'manifest.json';manifest=json.loads(path.read_text(encoding='utf-8'))
    manifest['balanceChange']=dict(instrumentPrefix='cello-',decibels=CELLO_DB,linearGain=CELLO_GAIN,
        scope='Long body, middle/low narrative answers and short low-string pulse only; flute, pluck, harp, violin, brass and drums keep previous score gains.',
        mastering='Exact V5 master gain reused per loop; no loudness-matching makeup gain.',scoreComparison=comparisons)
    base.music.helpers.write_json(path,manifest)
    base.music.helpers.write_json(OUT/'balance-check.json',dict(status='passed',comparisons=comparisons))


if __name__=='__main__':
    main()
