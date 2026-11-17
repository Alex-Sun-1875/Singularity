"""Package real Cocos frames and audit hit coverage, sparse links and aftermath."""
import hashlib
import importlib.util
import json
import math
from fractions import Fraction
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / 'src/.tmp/thunder-implementation-v11/validated/implemented'
MEDIA = HERE / 'media'
CASES = {'THU_01':'雷矛 · 短促主雷', 'CHAIN_R5':'连锁闪电 · 近邻传播', 'NETWORK_R5':'雷网 · 分叉爆发与地面雷晕'}
spec = importlib.util.spec_from_file_location('previous_review', HERE.parent/'thunder-noncrossing-v10/review.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


def read(case):
    return json.loads((CACHE/case/'capture.json').read_text('utf8'))


def label(draw, xy, text, size=22, fill='#e6e9ef', bold=False, anchor='lm'):
    previous.label(draw, xy, text, size, fill, bold, anchor)


def audit(case):
    r = read(case)
    assert not r['errors'] and r['variant']=='implemented'
    assert len(list((CACHE/case).glob('*.jpg')))==r['frames']
    for name, digest in r['reviewInputs'].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest, name
    enemies = {t['id']:t for t in r['info']['targets']}
    events = [e['event'] for e in r['logicEvents']]
    hits = [e for e in events if e['type']=='skill_hit' and e['skillId']==r['shot']]
    graph = [e for e in events if e['type']=='skill_segment' and e.get('targetId') in enemies]
    damaged = {e['targetId'] for e in hits}
    missed = {e['id'] for e in events if e['type']=='miss' and e.get('id') in enemies}-damaged
    assert damaged
    if case=='CHAIN_R5':
        assert len(damaged)==7 and len(missed)==1, (case,damaged,missed)
    if case=='NETWORK_R5':
        assert len(damaged)==11 and len(missed)==1, (case,damaged,missed)
        assert {e['segment'] for e in hits}=={0,1,2}
    assert len(graph)==len(hits), 'Decorative graph edges must not masquerade as hits'
    per_beat, degrees, pairs = {}, {}, set()
    hop = r['info']['rule'].get('connectionRadiusMetres',0)
    for e in graph:
        beat,target,source=e['segment'],e['targetId'],e.get('sourceId')
        key=(beat,target)
        assert key not in per_beat
        per_beat[key]=e
        assert source not in missed, ('MISS relay',source)
        degrees[key]=degrees.get(key,0)+1
        if source:
            degrees[(beat,source)]=degrees.get((beat,source),0)+1
            assert source in damaged and math.hypot(e['to']['x']-e['from']['x'],e['to']['z']-e['from']['z'])<=hop+.001
            pair=(beat,*sorted([source,target]))
            assert pair not in pairs
            pairs.add(pair)
    for beat in {e['segment'] for e in hits}:
        assert len([e for e in hits if e['segment']==beat])<=r['info']['rule']['targetLimit']
    strong = [(f['frame'],d) for f in r['nativeAudit'] for d in f['draws'] if d['role']=='launch' and d['alpha']>100]
    assert strong, 'Missing visible launch draw'
    if case=='THU_01':
        assert max(sum(d['role']=='launch' for d in f['draws']) for f in r['nativeAudit'])==1, 'Duplicate spear corridor and contact beam'
    peak,draw=max(strong,key=lambda item:item[1]['alpha'])
    before=np.array(Image.open(CACHE/case/'000.jpg').convert('RGB'),dtype=np.int16)
    after=np.array(Image.open(CACHE/case/f'{peak:03d}.jpg').convert('RGB'),dtype=np.int16)
    x,y=map(round,draw['screenMid'])
    patch=(after-before)[max(0,y-12):y+13,max(0,x-12):x+13]
    visible=int(np.count_nonzero(np.sum(np.maximum(patch,0),axis=2)>100))
    assert visible>10, ('Launch draw is invisible in native pixels',case,visible)
    aftermath=[f for f in r['nativeAudit'] if not f['action'] and not f['draws'] and any(p['alpha']>50 for p in f['ground']['active'])]
    assert aftermath, ('No residual after action and arcs finish',case)
    aftermath_frame=aftermath[len(aftermath)//2]['frame']
    residual=np.array(Image.open(CACHE/case/f'{aftermath_frame:03d}.jpg').convert('RGB'),dtype=np.int16)
    delta=residual-before
    purple=(residual[:,:,2]>residual[:,:,0]+8)&(residual[:,:,2]>residual[:,:,1]+4)&(delta[:,:,2]>delta[:,:,0]+10)
    residual_pixels=int(np.count_nonzero(purple))
    assert residual_pixels>(80 if case=='THU_01' else 250), ('Ground haze is too faint in native pixels',case,residual_pixels)
    if case!='THU_01':
        assert r['nativeAudit'][-1]['ground']['active']==[], ('Residual did not expire',case)
    crossings=[{'frame':f['frame'],'crossings':previous.curve_crossings([d for d in f['draws'] if d['alpha']>80])} for f in r['nativeAudit']]
    crossings=[f for f in crossings if f['crossings']]
    first_edges=[e for e in graph if e['segment']==0]
    return {'case':case,'monsters':len(enemies),'damaged':sorted(damaged),'missed':sorted(missed),
            'authoredBeats':r['info']['rule']['authoredDamageHits'],'damageEvents':len(hits),
            'maxConnectionsIncludingEntry':max(degrees.values()),'firstBeatEdges':first_edges,
            'extraVisualEdges':0,'missRelayNodes':[],'peakFrame':peak,'visibleLaunchPixels':visible,
            'aftermathFrame':aftermath_frame,'aftermathVisiblePixels':residual_pixels,
            'aftermathDurationObserved':len(aftermath)/30,'strongCurveCrossings':crossings}


def frame(case,index,result):
    out=Image.new('RGB',(1280,754),'#171c24')
    d=ImageDraw.Draw(out)
    label(d,(22,30),CASES[case],27,'#c7d2ff',True)
    label(d,(1258,30),'当前实现 · 实际 3D 录制',18,'#a9b3c3',anchor='rm')
    with Image.open(CACHE/case/f'{index:03d}.jpg') as source:
        out.paste(source.convert('RGB'),(0,64))
    label(d,(22,722),f"场内 {result['monsters']} 只 · 实际命中 {len(result['damaged'])} · MISS {len(result['missed'])} · 放电结束后保留地面雷晕",20)
    return out


def main():
    MEDIA.mkdir(exist_ok=True)
    results={case:audit(case) for case in CASES}
    hashes={read(case)['gameHash'] for case in CASES}
    assert len(hashes)==1, 'Mixed builds in the recording'
    counts=[read(case)['frames'] for case in CASES]
    for case,result in results.items():
        frame(case,result['peakFrame'],result).save(MEDIA/(case.lower()+'-impact.jpg'),quality=95,subsampling=0)
        frame(case,result['aftermathFrame'],result).save(MEDIA/(case.lower()+'-aftermath.jpg'),quality=95,subsampling=0)
    with av.open(str(MEDIA/'implemented-thunder.mp4'),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
        stream=movie.add_stream('libx264',rate=30)
        stream.width,stream.height,stream.pix_fmt=1280,754,'yuv420p'
        stream.codec_context.thread_count=3
        stream.options={'crf':'16','preset':'veryfast'}
        movie.set_chapters([{'id':i,'time_base':Fraction(1,30),'start':sum(counts[:i]),'end':sum(counts[:i+1]),'metadata':{'title':title}} for i,title in enumerate(CASES.values())])
        pts=0
        for case in CASES:
            for i in range(read(case)['frames']):
                vf=av.VideoFrame.from_image(frame(case,i,results[case]))
                vf.pts,vf.time_base=pts,Fraction(1,30)
                for packet in stream.encode(vf):movie.mux(packet)
                pts+=1
        for packet in stream.encode():movie.mux(packet)
    case='NETWORK_R5'
    frames=[frame(case,i,results[case]).resize((960,566),Image.Resampling.LANCZOS) for i in range(read(case)['frames'])]
    sample=Image.new('RGB',(480,849))
    for j,i in enumerate([results[case]['peakFrame'],results[case]['aftermathFrame'],0]):
        sample.paste(frames[i].resize((480,283)),(0,j*283))
    blues=[(r,g,b) for r,g,b in sample.get_flattened_data() if b>r+8 and b>g+4]
    electric=Image.new('RGB',(256,(len(blues)+255)//256))
    electric.putdata(blues+[blues[-1]]*(electric.width*electric.height-len(blues)))
    palette=sample.quantize(192,method=Image.Quantize.MEDIANCUT)
    electric=electric.quantize(64,method=Image.Quantize.MEDIANCUT)
    palette.putpalette(palette.getpalette()[:576]+electric.getpalette()[:192])
    indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    durations=[(round((i+1)*100/30)-round(i*100/30))*10 for i in range(len(frames))]
    indexed[0].save(MEDIA/'implemented-thunder.gif',save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=False)
    strip=ROOT/'src/cocos/assets/resources/vfx/production/thunder-reference-strip-v1.png'
    assert strip.read_bytes()==(HERE.parent/'thunder-chain-v8/approved-thunder-strip.png').read_bytes()
    with av.open(str(MEDIA/'implemented-thunder.mp4')) as movie:
        assert sum(1 for _ in movie.decode(video=0))==sum(counts)
    evidence={'scope':'Implemented current Cocos thunder skills; actual compiled build, no replacement gameplay/VFX injected',
              'platform':'Local Cocos Web validation, TapTap device validation pending',
              'userArtAcceptance':'Pending','compiledGameHash':read(case)['gameHash'],'cases':results,
              'assetSource':'Approved v8 reference strip, byte-identical; no new model generation',
              'sourceHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/cocos/assets/scripts/features/combat'/name for name in ['common/PureCombat.ts','runtime/NativeSkillVfx.ts','runtime/SkillEnergyStrokes.ts','runtime/ThunderArcField.ts','runtime/ThunderGroundAura.ts','runtime/Effects.ts']]},
              'files':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.rglob('*') if p.is_file() and p.name!='provenance.json' and '__pycache__' not in p.parts}}
    (HERE/'provenance.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({case:{'damaged':len(r['damaged']),'missed':len(r['missed']),'maxConnections':r['maxConnectionsIncludingEntry'],'aftermathSeconds':r['aftermathDurationObserved'],'curveCrossingFrames':len(r['strongCurveCrossings'])} for case,r in results.items()},ensure_ascii=False))


if __name__=='__main__':main()
