"""Audit and export unmodified Cocos game captures, with real release clocks."""
import hashlib
import importlib.util
import json
import math
from functools import lru_cache
from fractions import Fraction
from pathlib import Path

import av
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CACHE=ROOT/'src/.tmp/spell-windup-v13/final'
MEDIA=HERE/'media'
CASES={'FIR_01':'赤焰枪','FIR_02':'焚星坠落','THU_01':'贯雷长矛','THU_05':'万钧雷潮','THU_06':'雷光护幕'}
NAMES={**CASES,'FIR_03':'焰心护盾','FIR_04':'炎墙封路','FIR_05':'焚天火海','THU_02':'连锁雷弧','THU_04':'扇雷横扫'}
ALL=['FIR_01','FIR_02','FIR_03','FIR_04','FIR_05','THU_01','THU_02','THU_04','THU_05','THU_06']
spec=importlib.util.spec_from_file_location('labels',HERE.parent/'thunder-implementation-v11/review.py')
labels=importlib.util.module_from_spec(spec);spec.loader.exec_module(labels)

@lru_cache(maxsize=15)
def read(variant,case):return json.loads((CACHE/variant/case/'capture.json').read_text('utf8'))

def accents(f):
    # Effects submits the hand cast before NativeSkillVfx's contacts/wards.
    # Check its actual uploaded batch as well as its three rendered paths.
    if not any(d['key'].startswith('beam:cast:cast:') for d in f['field']['active']):return []
    paths=[d for d in f['draws'] if d['role']=='accent' and d['width']<.13]
    assert 1<=len(paths)<=3
    return paths

def flames(f):return [d for d in f['fire']['active'] if d['key'].startswith('cast:')]

def audit(case):
    r=read('after',case);frames=r['nativeAudit']
    assert r['errors']==[] and r['frames']==66
    for name,digest in r['reviewInputs'].items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
    releases=[e for e in r['logicEvents'] if e['event']['type']=='skill_release' and e['event']['skillId']==case]
    assert len(releases)==1
    released=releases[0]['frame']
    windup=[f for f in frames if f['action'] and not f['action']['emitted']]
    assert len(windup)>=3
    poses=[f['poseFraction'] for f in windup]
    assert len({round(n,4) for n in poses})>=3,('Frozen raising pose',case,poses)
    assert max(poses)<.37,('Native shoot starts before actual release',case,poses)
    gather=[f for f in windup if flames(f) or accents(f)]
    assert len(gather)==len(windup),('Missing hand gather',case)
    distances=[]
    for f in frames:
        drawings=flames(f) if case.startswith('FIR') else accents(f)
        a=f['action']
        if not a or a['elapsed']-a['releaseAt']>=.12:
            assert not drawings,('Hand accent survived its release window',case,f['frame'])
        hand=f['presentation']['castHand']
        for d in drawings:
            p=d['position'] if case.startswith('FIR') else dict(zip(['x','y','z'],d['renderTo']))
            distances.append(math.dist([p[k] for k in ['x','y','z']],[hand[k] for k in ['x','y','z']]))
    assert distances and max(distances)<.015,('Casting effect detached from palm',case,max(distances,default=-1))
    assert frames[-1]['action'] is None
    if case in CASES:
        before=read('before',case)
        assert before['logicEvents']==r['logicEvents'],('Gameplay changed between recordings',case)
    return {'case':case,'releaseFrame':released,'windupFrames':len(windup),'lastWindupFrame':windup[-1]['frame'],
            'palmMaximumDistanceMetres':max(distances),'nativeWindupPoseFractions':[poses[0],poses[-1]],
            'gameplayMatchesBefore':case in CASES,'frames':r['frames']}

def image(variant,case,index):
    with Image.open(CACHE/variant/case/f'{index:03d}.jpg') as raw:return raw.convert('RGB')

def frame(case,index,slow=False):
    r=read('after',case);f=r['nativeAudit'][index];out=Image.new('RGB',(1280,754),'#171c24');d=ImageDraw.Draw(out)
    labels.label(d,(22,30),NAMES[case]+' · 施法抬手',26,'#c7d2ff',True)
    labels.label(d,(1258,30),'半速观察' if slow else '当前 3D 实现 · 原速',18,'#a9b3c3',anchor='rm')
    out.paste(image('after',case,index),(0,64))
    a=f['action'];state='蓄能抬手' if a and not a['emitted'] else '推出释放' if a and a['elapsed']-a['releaseAt']<.12 else '连贯收势' if a else '待机'
    labels.label(d,(22,722),state+'  ·  '+('火焰聚拢施法掌心' if case.startswith('FIR') else '短弧向掌心收束')+'  ·  原技能释放时刻与命中规则',20)
    return out

def crop(variant,case,index):
    f=read(variant,case)['nativeAudit'][index];x,y=f['playerScreen'];x,y=round(x),round(y)
    return image(variant,case,index).crop((x-210,y-205,x+210,y+215))

def compare(case,index):
    out=Image.new('RGB',(1280,754),'#171c24');d=ImageDraw.Draw(out)
    labels.label(d,(22,29),CASES[case]+' · 同机位抬手局部对比',25,'#c7d2ff',True)
    for i,(variant,name) in enumerate([('before','调整前'),('after','调整后')]):
        out.paste(crop(variant,case,index).resize((620,620),Image.Resampling.LANCZOS),(i*640+10,64))
        labels.label(d,(i*640+26,709),name,22)
    return out

def encode(path,frames,width=1280,height=754):
    count=0
    with av.open(str(path),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
        stream=movie.add_stream('libx264',rate=30);stream.width=width;stream.height=height;stream.pix_fmt='yuv420p'
        stream.codec_context.thread_count=3;stream.options={'crf':'17','preset':'veryfast'}
        for im in frames:
            vf=av.VideoFrame.from_image(im);vf.pts=count;vf.time_base=Fraction(1,30);count+=1
            for packet in stream.encode(vf):movie.mux(packet)
        for packet in stream.encode():movie.mux(packet)
    with av.open(str(path)) as movie:assert sum(1 for _ in movie.decode(video=0))==count
    return count

def main():
    MEDIA.mkdir(exist_ok=True);results={case:audit(case) for case in ALL}
    assert len({read('after',case)['gameHash'] for case in ALL})==1
    assert len({read('before',case)['gameHash'] for case in CASES})==1
    def demonstration():
        for case in CASES:
            for i in range(66):yield frame(case,i)
            for i in range(7,min(65,results[case]['releaseFrame']+10)):
                im=frame(case,i,True)
                yield im;yield im
    encode(MEDIA/'spell-windup.mp4',demonstration())
    encode(MEDIA/'all-spells.mp4',(frame(case,i) for case in ALL for i in range(66)))
    def comparison():
        for case in CASES:
            for i in range(7,min(65,results[case]['releaseFrame']+10)):
                im=compare(case,i);yield im;yield im
    encode(MEDIA/'before-after.mp4',comparison())
    for case in CASES:frame(case,results[case]['lastWindupFrame']).save(MEDIA/(case.lower()+'-windup.jpg'),quality=95,subsampling=0)
    qa=Image.new('RGB',(1280,800),'#171c24');d=ImageDraw.Draw(qa)
    for row,case in enumerate(['FIR_02','THU_01']):
        for col,offset in enumerate([-2,-1,1,3]):
            i=results[case]['releaseFrame']+offset
            qa.paste(crop('after',case,i).resize((320,320),Image.Resampling.LANCZOS),(col*320,row*400+45))
            labels.label(d,(col*320+8,row*400+22),case+' / '+str(i),18)
    qa.save(MEDIA/'release-sequence.jpg',quality=95,subsampling=0)
    runtime=['features/actors/runtime/Actors.ts','features/actors/runtime/PlayerActionPresentation.ts','features/combat/runtime/Effects.ts','features/combat/runtime/NativeSkillVfx.ts','features/combat/runtime/SkillFireSprites.ts','features/combat/runtime/SpellCastEffects.ts','features/combat/runtime/ThunderArcField.ts']
    evidence={'artAcceptance':'Pending user review','platform':'Actual local Cocos Web capture; TapTap device validation pending',
              'validation':{'typecheck':'passed','coreTypecheck':'passed','existingTests':{'passed':155,'failed':0},'webBuild':'test profile passed'},
              'beforeGameHash':read('before','FIR_01')['gameHash'],'afterGameHash':read('after','FIR_01')['gameHash'],'cases':results,
              'runtimeSources':{p:hashlib.sha256((ROOT/'src/cocos/assets/scripts'/p).read_bytes()).hexdigest() for p in runtime},
              'files':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.rglob('*') if p.is_file() and p.name!='provenance.json' and '__pycache__' not in p.parts}}
    (HERE/'provenance.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(results,ensure_ascii=False))

if __name__=='__main__':main()
