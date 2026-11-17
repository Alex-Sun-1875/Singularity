"""Lower V6 cello layers a further 2dB, retaining V5 mastering gains."""
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
spec=importlib.util.spec_from_file_location('_v7_cello_balance',ROOT/'src/cocos/tools/music-embers-story-v6/make_low_string_balance.py')
balance=importlib.util.module_from_spec(spec);sys.modules[spec.name]=balance;spec.loader.exec_module(balance)

if __name__=='__main__':
    balance.OUT=ROOT/'source-art/audio/embers-story-v7'
    balance.CELLO_DB=-5.
    balance.CELLO_GAIN=10**(balance.CELLO_DB/20)
    balance.main('embers-story-light','embers-story-light-showcase','余烬叙事融合·轻弦版')
    comparisons=[]
    for mode in ('explore','combat'):
        previous=json.loads((ROOT/f'source-art/audio/embers-story-v6/music-{mode}-score.json').read_text(encoding='utf-8'))['notes']
        current=json.loads((balance.OUT/f'music-{mode}-score.json').read_text(encoding='utf-8'))['notes']
        assert len(previous)==len(current)
        changed=0
        for old,new in zip(previous,current):
            assert {k:v for k,v in old.items() if k!='level'}=={k:v for k,v in new.items() if k!='level'}
            if old['instrument'].startswith('cello-'):
                assert abs(new['level']-old['level']*10**(-2/20))<1e-12
                changed+=1
            else:assert new['level']==old['level']
        comparisons.append(dict(mode=mode,loweredCelloNotes=changed,relativeToV6Db=-2,otherNoteDataUnchanged=True))
    path=balance.OUT/'manifest.json';manifest=json.loads(path.read_text(encoding='utf-8'))
    manifest['balanceChange']['relativeToV6Db']=-2
    manifest['balanceChange']['previousVersionComparison']=comparisons
    balance.base.music.helpers.write_json(path,manifest)
    balance.base.music.helpers.write_json(balance.OUT/'balance-check.json',dict(status='passed',comparisons=manifest['balanceChange']['scoreComparison'],previousVersionComparison=comparisons))
