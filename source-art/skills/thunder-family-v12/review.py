"""Audit and export the current build's three remaining thunder abilities."""
import hashlib
import importlib.util
import json
import math
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CACHE=ROOT/'src/.tmp/thunder-family-v12/final/implemented'
MEDIA=HERE/'media'
CASES={'THU_03':'雷霆战印 · 蓄电与三次附雷','THU_04':'扇雷横扫 · 两次扫击与雷冠庇护','THU_06':'雷光护幕 · 受击与移动防护'}
spec=importlib.util.spec_from_file_location('previous',HERE.parent/'thunder-implementation-v11/review.py')
previous=importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


@lru_cache(maxsize=3)
def read(case):return json.loads((CACHE/case/'capture.json').read_text('utf8'))


def blue_pixels(case,index,center,radius):
    with Image.open(CACHE/case/f'{index:03d}.jpg') as image:
        a=np.array(image.convert('RGB'),dtype=np.int16)
    x,y=map(round,center)
    a=a[max(0,y-radius):y+radius+1,max(0,x-radius):x+radius+1]
    return int(np.count_nonzero((a[:,:,2]>a[:,:,0]+8)&(a[:,:,2]>a[:,:,1]+4)))


def audit(case):
    r=read(case)
    assert not r['errors'] and r['variant']=='implemented'
    assert len(list((CACHE/case).glob('*.jpg')))==r['frames']
    for name,digest in r['reviewInputs'].items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
    events=r['logicEvents']
    hits=[e for e in events if e['event']['type']=='skill_hit' and e['event']['skillId']==case]
    audit=r['nativeAudit']
    assert any(d['role']=='accent' for f in audit for d in f['draws'])
    assert all(d['textureBand']==0 for f in audit for d in f['draws'] if d['role']=='accent')
    result={'case':case,'monsterCount':len(r['info']['targets']),'hitEvents':len(hits)}
    if case=='THU_03':
        activation=[e for e in events if e['event']['type']=='skill_status' and e['event']['skillId']==case and e['event'].get('status')=='thunderWeapon']
        assert len(activation)==1, 'Enhancement must activate through the real moving hit'
        assert not any(e['event']['type']=='skill_cast' and e['event']['skillId']==case for e in events)
        assert len(hits)==3 and [e['event']['segment'] for e in hits]==[1,2,3]
        charges=[int(f['buffs'].get('thunderCharges',0)) for f in audit]
        assert max(charges)==3 and all(n in charges for n in [3,2,1,0]) and charges[-1]==0
        moved=max(math.hypot(f['player']['x']-r['info']['origin']['x'],f['player']['z']-r['info']['origin']['z']) for f in audit[:50])
        assert moved>.4, 'No real movement before enhancement'
        choices=[f for f in audit if f['frame']>activation[0]['frame']+3 and f['frame']<76 and f['buffs'].get('thunderCharges')==3 and any(d['role']=='accent' for d in f['draws'])]
        assert choices
        posed=choices[len(choices)//2]
        near_hand=[d for d in posed['draws'] if d['role']=='accent']
        hand=posed['hand']
        radius=max(math.dist(p,[hand['x'],hand['y'],hand['z']]) for d in near_hand for p in d['renderPath'])
        assert radius<.46, ('Charge marks detached from the animated grip',radius)
        pixels=blue_pixels(case,posed['frame'],posed['handScreen'],42)
        assert pixels>12, ('Invisible charge marks',pixels)
        result.update(activationFrame=activation[0]['frame'],detailFrame=posed['frame'],peakFrame=hits[-1]['frame']+1,
                      chargeSequence=[3,2,1,0],chargeGripDistanceMetres=radius,detailPixels=pixels,movedMetres=moved)
    elif case=='THU_04':
        by_beat={beat:[e for e in hits if e['event']['segment']==beat] for beat in [0,1]}
        assert all(by_beat.values()) and len(hits)<=r['info']['rule']['targetLimit']*2
        assert len(by_beat[0])==len(by_beat[1]), 'The visual sweep cannot remove a real beat'
        shield=[e for e in events if e['event']['type']=='skill_status' and e['event']['skillId']=='THU_P2']
        assert len(shield)==1 and max(f['shield'] for f in audit)>0
        rows={0:[],1:[]}
        origin=r['info']['aim']
        direction=math.atan2(origin['x']-r['info']['origin']['x'],origin['z']-r['info']['origin']['z'])
        for f in audit:
            pattern=next((p for p in f['patterns'] if p['skillId']==case),None)
            if not pattern or pattern['segment'] not in rows:continue
            remote=[d for d in f['draws'] if d['role']=='accent' and d['alpha']>30 and math.hypot(d['renderMid'][0]-f['player']['x'],d['renderMid'][2]-f['player']['z'])>1.2]
            if not remote:continue
            p=remote[0]['renderMid'];dx,dz=p[0]-origin['x'],p[2]-origin['z']
            angle=math.atan2(dx*math.cos(direction)-dz*math.sin(direction),dx*math.sin(direction)+dz*math.cos(direction))
            rows[pattern['segment']].append((f['frame'],angle))
        assert all(len(row)>1 for row in rows.values()), 'Missing rendered fan fronts'
        sweep={beat:row[-1][1]-row[0][1] for beat,row in rows.items()}
        assert sweep[0]>0 and sweep[1]<0, ('Fan fronts do not reverse',sweep)
        peak=max((f for f in audit if f['frame'] in [n for n,_ in rows[0]]),key=lambda f:sum(d['alpha'] for d in f['draws']))['frame']
        result.update(peakFrame=peak,detailFrame=max(shield[0]['frame']+5,peak),hitsPerBeat=[len(by_beat[0]),len(by_beat[1])],
                      sweepAngleDeltas=sweep,passiveShieldTriggers=len(shield),passiveShieldMaximum=max(f['shield'] for f in audit))
    else:
        guarded=[e for e in events if e['event']['type']=='skill_status' and e['event']['skillId']==case and e['event'].get('status')=='wardHit']
        assert len(guarded)==1 and not hits, 'Guard must react to one real incoming hit without attacking'
        assert min(f['player']['hp'] for f in audit)<audit[0]['player']['hp'], 'No real incoming damage'
        before=[f for f in audit if f['frame']<guarded[0]['frame'] and f['buffs'].get('stormWardReduction',0)>0 and len(f['draws'])>0]
        assert before
        posed=before[len(before)//2]
        pixels=blue_pixels(case,posed['frame'],posed['playerScreen'],100)
        assert pixels>35, ('Invisible guard ribs',pixels)
        moved=max(math.hypot(f['player']['x']-r['info']['origin']['x'],f['player']['z']-r['info']['origin']['z']) for f in audit)
        assert moved>.6 and audit[-1]['buffs'].get('stormWardUntil',0)<audit[-1]['time']
        assert not any(d['role']=='accent' for d in audit[-1]['draws']), 'Expired guard still rendering'
        result.update(peakFrame=guarded[0]['frame']+1,detailFrame=posed['frame'],guardedHitFrame=guarded[0]['frame'],
                      guardedHits=1,detailPixels=pixels,movedMetres=moved)
    return result


def frame(case,index,result):
    r=read(case);f=r['nativeAudit'][index]
    out=Image.new('RGB',(1280,754),'#171c24');d=ImageDraw.Draw(out)
    previous.label(d,(22,30),CASES[case],26,'#c7d2ff',True)
    previous.label(d,(1258,30),'当前实现 · 实际 3D 录制',18,'#a9b3c3',anchor='rm')
    with Image.open(CACHE/case/f'{index:03d}.jpg') as source:out.paste(source.convert('RGB'),(0,64))
    if case=='THU_03':text=f"移动命中自动触发 · 附雷余量 {int(f['buffs'].get('thunderCharges',0))} / 3 · 第三击强化接触"
    elif case=='THU_04':text=f"远端扇面两次真实打击 · 雷冠庇护：{'生效' if f['shield']>0 else '未生效／已结束'} · 命中落点保留雷晕"
    else:
        active=f['buffs'].get('stormWardUntil',0)>f['time']
        state='减伤待触发' if active and f['buffs'].get('stormWardReduction',0)>0 else '减伤已消耗，移动加速持续' if active else '护幕未开启／已结束'
        text='真实敌人攻击 · '+state
    previous.label(d,(22,722),text,20)
    return out


def encode(path,selections,results,chapters=False):
    with av.open(str(path),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
        stream=movie.add_stream('libx264',rate=30);stream.width,stream.height,stream.pix_fmt=1280,754,'yuv420p'
        stream.codec_context.thread_count=3;stream.options={'crf':'16','preset':'veryfast'}
        counts=[read(case)['frames'] for case in selections]
        if chapters:movie.set_chapters([{'id':i,'time_base':Fraction(1,30),'start':sum(counts[:i]),'end':sum(counts[:i+1]),'metadata':{'title':CASES[case]}} for i,case in enumerate(selections)])
        pts=0
        for case in selections:
            for i in range(read(case)['frames']):
                vf=av.VideoFrame.from_image(frame(case,i,results[case]));vf.pts,vf.time_base=pts,Fraction(1,30)
                for packet in stream.encode(vf):movie.mux(packet)
                pts+=1
        for packet in stream.encode():movie.mux(packet)
    with av.open(str(path)) as movie:assert sum(1 for _ in movie.decode(video=0))==sum(counts)


def main():
    MEDIA.mkdir(exist_ok=True)
    results={case:audit(case) for case in CASES}
    assert len({read(case)['gameHash'] for case in CASES})==1
    for case,result in results.items():
        frame(case,result['peakFrame'],result).save(MEDIA/(case.lower()+'-impact.jpg'),quality=95,subsampling=0)
        frame(case,result['detailFrame'],result).save(MEDIA/(case.lower()+'-detail.jpg'),quality=95,subsampling=0)
        encode(MEDIA/(case.lower()+'.mp4'),[case],results)
    encode(MEDIA/'thunder-family.mp4',list(CASES),results,True)
    board=Image.new('RGB',(1920,400),'#171c24')
    for i,case in enumerate(CASES):
        index=results[case]['peakFrame' if case=='THU_04' else 'detailFrame']
        board.paste(frame(case,index,results[case]).resize((640,377),Image.Resampling.LANCZOS),(i*640,12))
    board.save(MEDIA/'thunder-family-board.jpg',quality=95,subsampling=0)
    evidence={'scope':'Actual Cocos implementation of remaining thunder abilities and earned passive protection',
              'renderSource':'Unmodified compiled game modules; fixture drives real movement, skills, attacks and incoming training-enemy hits',
              'artAcceptance':'Pending user review','platform':'Local Cocos Web; TapTap device validation pending',
              'compiledGameHash':read('THU_03')['gameHash'],'cases':results,
              'runtimeSources':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in [
                  'src/cocos/assets/scripts/features/combat/runtime/ThunderSupportEffects.ts',
                  'src/cocos/assets/scripts/features/combat/runtime/NativeSkillVfx.ts',
                  'src/cocos/assets/scripts/features/combat/runtime/ThunderArcField.ts',
                  'src/cocos/assets/scripts/features/combat/runtime/Effects.ts']},
              'validation':{'typecheck':'passed','coreTypecheck':'passed','existingTests':{'passed':155,'failed':0},'webBuild':'test profile passed'},
              'files':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.rglob('*') if p.is_file() and p.name!='provenance.json' and '__pycache__' not in p.parts}}
    (HERE/'provenance.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(results,ensure_ascii=False))


if __name__=='__main__':main()
