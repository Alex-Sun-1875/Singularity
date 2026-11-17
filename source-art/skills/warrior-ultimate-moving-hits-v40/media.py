"""Package independently rendered 1/2/3-wave game captures; no synthesized game frames."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
from itertools import chain
import json, hashlib, re, shutil
import av
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-ultimate-moving-hits-v40'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
CASES=[('training',rank) for rank in range(1,6)]+[('field',5)]
BANDS={1:'技能1级',2:'技能2–3级',3:'技能4–5级'}
FPS=30;FRAMES=108
MAIN=re.compile(r':ultimate-downcut:wave:(\d+)$')
@lru_cache(maxsize=12)
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if bold else 'msyh.ttc'),size)
def label(d,xy,s,size=23,fill='#dce5ec',bold=False):d.text(xy,s,font=font(size,bold),fill=fill)
@lru_cache(maxsize=8)
def report(scene,rank):return json.loads((CACHE/scene/f'rank{rank}'/'capture.json').read_text(encoding='utf8'))
def raw_path(scene,rank,index):return CACHE/scene/f'rank{rank}'/f'{index:03d}.jpg'
def main_indices(metric):return {int(match.group(1)) for layer in metric['warrior']['active'] if (match:=MAIN.search(layer['key']))}
def hp_text(scene,rank,index):
 targets=report(scene,rank)['metrics'][index]['targets']
 return f'7m −{int(targets[0]["maxHp"]-targets[0]["hp"])}  ·  9m −{int(targets[1]["maxHp"]-targets[1]["hp"])}  ·  侧/后 −{int(targets[2]["maxHp"]-targets[2]["hp"])}/{int(targets[3]["maxHp"]-targets[3]["hp"])}'
def frame(scene,count,index,slow=False):
 im=Image.new('RGB',(1280,744),'#171d22');d=ImageDraw.Draw(im);rank=count;count=report(scene,rank)['waveCount']
 label(d,(18,9),f'战士最终技实装 · 逐波真实命中·连续{count}道',27,bold=True)
 label(d,(860,14),('靶场' if scene=='training' else '普通地面')+f' / Lv{rank} / '+('0.5×' if slow else '原速'),20,fill='#acbbc7')
 with Image.open(raw_path(scene,rank,index)) as shot:im.paste(shot.convert('RGB'),(0,48))
 label(d,(18,680),hp_text(scene,rank,index)+'  （累计实际掉血）',22,bold=True)
 label(d,(18,714),'7米／9米靶随波到达掉血 · 每波每敌独立一次 · 生产路径实录',19)
 return im
def comparison_frame(index):
 im=Image.new('RGB',(1800,544),'#171d22');d=ImageDraw.Draw(im)
 label(d,(18,7),'战士最终技实装 · 逐波真实命中，按等级连续 1 / 2 / 3 道',29,bold=True)
 for col,count in enumerate([1,2,3]):
  x=col*600;rank=[1,3,5][count-1]
  label(d,(x+18,48),f'{count}道 · {BANDS[count]}（实录Lv{rank}）',23,bold=True)
  with Image.open(raw_path('training',rank,index)) as shot:im.paste(shot.convert('RGB').crop((180,0,1280,624)).resize((600,340),Image.Resampling.LANCZOS),(x,82))
  label(d,(x+16,436),hp_text('training',rank,index),19,bold=True)
  label(d,(x+16,468),'累计实际 HP 损失 · 侧方/身后应为 0',18,fill='#9eb1bc')
 label(d,(18,511),'7米／9米路径靶 · 侧方与身后对照靶 · 数字直接读取真实目标 HP',20)
 return im
def write_video(name,images,rate=30):
 iterator=iter(images);first=next(iterator)
 with av.open(str(OUT/name),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
  stream=movie.add_stream('libx264',rate=rate);stream.width,stream.height=first.size;stream.pix_fmt='yuv420p';stream.options={'crf':'17','preset':'veryfast'};stream.codec_context.thread_count=3
  for i,image in enumerate(chain([first],iterator)):
   f=av.VideoFrame.from_image(image);f.pts=i;f.time_base=Fraction(1,rate)
   for packet in stream.encode(f):movie.mux(packet)
  for packet in stream.encode():movie.mux(packet)
def movies():
 write_video('wave-count-comparison.mp4',(comparison_frame(i) for i in range(FRAMES)))
 for count in [1,2,3]:write_video(f'wave-count-{count}.mp4',(frame('training',[1,3,5][count-1],i) for i in range(FRAMES)))
 write_video('three-waves-field.mp4',(frame('field',5,i) for i in range(FRAMES)))
 write_video('three-waves-slow.mp4',(frame('training',5,i,True) for i in range(32,90)),15)
def write_gif(name,pictures,rate,samples):
 w,h=pictures[0].size;sample=Image.new('RGB',(w//2,h//2*len(samples)))
 for row,index in enumerate(samples):sample.paste(pictures[index].resize((w//2,h//2)),(0,row*(h//2)))
 palette=sample.quantize(256,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 durations=[(round((i+1)*100/rate)-round(i*100/rate))*10 for i in range(len(indexed))]
 indexed[0].save(OUT/name,save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=True,disposal=1)
def gifs():
 pictures=[comparison_frame(i).resize((1350,408),Image.Resampling.LANCZOS) for i in range(FRAMES)]
 write_gif('wave-count-comparison.gif',pictures,30,[43,53,64])
 pictures=[]
 for index in range(32,90):
  im=Image.new('RGB',(960,664),'#171d22');d=ImageDraw.Draw(im)
  label(d,(16,10),'3道连续真实命中 · 7米／9米靶依次掉血 / 0.5×',24,bold=True)
  with Image.open(raw_path('training',5,index)) as shot:im.paste(shot.convert('RGB').crop((180,0,1280,624)).resize((960,544),Image.Resampling.LANCZOS),(0,48))
  label(d,(16,608),hp_text('training',5,index),23,bold=True)
  pictures.append(im)
 write_gif('three-wave-detail-slow.gif',pictures,15,[9,22,34])
def single_detail_gif():
 pictures=[]
 for index in range(35,78):
  im=Image.new('RGB',(960,664),'#171d22');d=ImageDraw.Draw(im)
  label(d,(16,10),'单道真实命中 · 到达前不扣血 / 0.5×',24,bold=True)
  with Image.open(raw_path('training',1,index)) as shot:im.paste(shot.convert('RGB').crop((180,0,1280,624)).resize((960,544),Image.Resampling.LANCZOS),(0,48))
  label(d,(16,608),hp_text('training',1,index),23,bold=True)
  pictures.append(im)
 write_gif('single-wave-crescent.gif',pictures,15,[5,13,22])
def stages():
 comparison_frame(53).save(OUT/'wave-count-overview.jpg',quality=95,subsampling=0)
 im=Image.new('RGB',(2160,1144),'#171d22');d=ImageDraw.Draw(im)
 label(d,(20,12),'三道刀气真实命中 · 7米／9米累计掉血随抵达增加',31,bold=True)
 metrics={m['frame']:m for m in report('training',5)['metrics']}
 for i,(index,title) in enumerate([(35,'第1道形成'),(42,'第2道接出'),(48,'第3道接出'),(55,'先后向前推进'),(62,'分别消散'),(71,'后波继续前进')]):
  x=i%3*720;y=68+i//3*532;m=metrics[index]
  with Image.open(raw_path('training',5,index)) as shot:im.paste(shot.convert('RGB').crop((180,0,1280,624)).resize((712,404),Image.Resampling.LANCZOS),(x+4,y))
  label(d,(x+16,y+420),f'{title} · 活跃{len(main_indices(m))}道 · {(index+1)/30:.2f}s',22,bold=True)
  label(d,(x+16,y+460),hp_text('training',5,index),22,bold=True)
 im.save(OUT/'three-wave-stages.jpg',quality=95,subsampling=0)
 for scene in ['training','field']:shutil.copyfile(CACHE/scene/'rank5'/'normal-hud.jpg',OUT/f'normal-hud-{scene}.jpg')
def verify_contacts(r,count):
 oracle=r['contactOracle'];path=oracle['targets'][:2];controls=oracle['targets'][2:]
 hits=[e for e in r['events'] if e['type']=='skill_hit']
 assert len(hits)==len(path)*count and all(e.get('waveIndex') in range(count) and e.get('phase')=='warriorWave' for e in hits)
 keys=[(e['castId'],e['waveIndex'],e['target']) for e in hits];assert len(keys)==len(set(keys)),'One pulse hits the same enemy twice'
 timing=[]
 for t in path:
  rows=sorted((e for e in hits if e['target']==t['id']),key=lambda e:e['waveIndex'])
  assert [e['waveIndex'] for e in rows]==list(range(count))
  assert t['expectedFirstAge'] is not None
  actual_times=[]
  for e in rows:
   assert abs(e['startedAt']-oracle['startedAt'])<1e-6
   contact=next(c for c in oracle['hitContacts'] if c['target']==e['target'] and c['waveIndex']==e['waveIndex'])
   assert contact['touchesSwept'] and contact['expectedFirstAge']-1e-5<=e['waveAge']<=contact['expectedFirstAge']+.020001,'Live displaced target is damaged outside the crest sweep'
   actual_times.append(e['startedAt']+.018+e['waveIndex']*.22+e['waveAge'])
  expected_first=oracle['startedAt']+.018+t['expectedFirstAge']
  for m in r['metrics']:
   target=next(s for s in m['targets'] if s['id']==t['id'])
   if m['time']<expected_first-1e-6:assert target['hp']==t['hp'],'Remote target loses HP before a wave reaches it'
  assert all(b>a for a,b in zip(actual_times,actual_times[1:]))
  last=next(s for s in r['metrics'][-1]['targets'] if s['id']==t['id'])
  real_hp_lost=sum(e.get('hpLost',e.get('value',0)) for e in r['events'] if e['type']=='hit' and e.get('id')==t['id'])
  assert abs(t['hp']-last['hp']-real_hp_lost)<1e-6 and real_hp_lost>0
  timing.append({'target':t['id'],'role':t['role'],'initialExpectedFirstAge':t['expectedFirstAge'],'actualWaveAges':[e['waveAge'] for e in rows],'actualHitTimes':actual_times,'actualContactPositions':[e['to'] for e in rows],'perHitExpectedAges':[next(c['expectedFirstAge'] for c in oracle['hitContacts'] if c['target']==e['target'] and c['waveIndex']==e['waveIndex']) for e in rows],'hpLost':real_hp_lost,'skillHitValues':[e['value'] for e in rows]})
 assert timing[0]['actualHitTimes'][0]<timing[1]['actualHitTimes'][0]
 for t in controls:
  assert t['expectedFirstAge'] is None and not any(e.get('target')==t['id'] for e in hits)
  assert all(next(s for s in m['targets'] if s['id']==t['id'])['hp']==t['hp'] for m in r['metrics'])
 signature=lambda p:sorted((e.get('waveIndex'),e.get('target'),e.get('value')) for e in p['events'] if e['type']=='skill_hit')
 assert len(r['frameStepProbes'])==2 and signature(r['frameStepProbes'][0])==signature(r['frameStepProbes'][1])
 assert len(signature(r['frameStepProbes'][0]))==len(path)*count
 life=r['lifecycle']
 hp=lambda m:[(t['id'],t['hp']) for t in m['targets']]
 if r['scene']=='field':assert hp(life['before'])==hp(life['paused'])==hp(life['restored'])
 else:
  assert all(pause[1]>=before[1] and restore[1]>=pause[1] for before,pause,restore in zip(hp(life['before']),hp(life['paused']),hp(life['restored'])))
 assert hp(life['engineBefore'])==hp(life['engineAfter'])
 assert hp(life['cleared'])==hp(life['clearedAdvanced']) and not life['clearedAdvanced']['pending'] and not life['clearedAdvanced']['waves']
 assert not r['naturalCleanup']['pending']
 return {'perPulsePerEnemyOnce':True,'realKnockbackRetained':True,'remoteHPUnchangedBeforeArrival':True,'sideAndBehindUnharmed':True,'finalBudgetFraction':.6,'damageFractionPerWave':.6/count,'pathTargets':timing,'coarseRenderStepCompared':.2,'nativeLogicalSubsteps':.02,'coarseAndFineHitSetsAndValuesMatch':True,'pauseHPNoDecrease':True,'fieldPauseHPStrictlyFrozen':r['scene']=='field','trainingAutoRefillObserved':r['scene']=='training' and hp(life['before'])!=hp(life['restored']),'noDamageAfterExplicitClearAndAdvance':True,'contactSettings':oracle['settings'],'contactSpan':oracle['span'],'defaultContactRange':oracle['range']}
def verify():
 summaries={};canonical=None;all_hashes=set()
 for scene,rank in CASES:
  r=report(scene,rank);count=[1,2,2,3,3][rank-1];all_hashes.add(r['gameHash'])
  assert r['productionOnly'] and not r['previewInjected'] and r['skillRank']==rank and r['waveCount']==count
  assert r['info']['fixtureLevel']==80 and r['frames']==108 and not r['errors']
  assert len(list((CACHE/scene/f'rank{rank}').glob('[0-9][0-9][0-9].jpg')))==108
  assert {'attack_sword','attack_sword_2','attack_sword_3'}<=set(r['clips'])
  assert all(m['pose']['state']!='idle' for m in r['metrics'] if m['action']),'Native actor chain interrupts to idle'
  hits=[e for e in r['events'] if e['type']=='skill_hit']
  assert hits and {e['segment'] for e in hits}=={2} and all(e.get('phase')=='warriorWave' for e in hits)
  assert r['castResult'] and 'skill_cast' in r['castResult']
  rows={};tips=[];tails=[]
  for m in r['metrics']:
   assert m['renderReady'] and not m['warrior']['droppedLayers'] and m['sharedMeshForAll']
   assert len(m['waves'])==len(main_indices(m))
   for w in m['waves']:
    assert w['castCount']==count and w['mode']=='ultimate-crescent'
    assert w['template']=='WarriorUltimateCrescentV38' and w['material']=='WarriorUltimateV38'
    assert w['effect'].split('/')[-1]=='warrior-ultimate-v38'
    assert all(abs(s-1)<1e-6 for s in w['worldScale'])
    assert w['localHeightRange'][0]>=.04 and w['localTipY']>3.5
    assert len(w['localOutlineSamples'])==18 and max(w['tipWidths'])<1e-5
    geometry=(w['localOutlineSamples'],w['localHeightRange'],w['localTipY'])
    if canonical is None:canonical=geometry
    assert geometry==canonical,'Production wave changes shape or local height by rank, ordinal or age'
    f=w['forward'];p=w['position'];o=w['launchFoot'];n=w['normal'];age=w['age']
    assert abs(n[1])<1e-5 and abs(sum(a*b for a,b in zip(n,f)))<1e-5
    assert abs(p[1]-o[1])<1e-6
    dx,dz=p[0]-o[0],p[2]-o[2]
    assert abs(dx*f[2]-dz*f[0])<1e-5
    smooth=lambda a:max(0,min(1,a))**2*(3-2*max(0,min(1,a)))
    distance=.15+2.65*smooth(age/.18)+3.10*max(0,min(1,(age-.18)/.84))
    assert abs(w['distance']-distance)<1e-4
    assert abs(w['tailWorld'][0]-p[0])<1e-6 and abs(w['tailWorld'][2]-p[2])<1e-6
    tips.append(w['tipWorld'][1]);tails.append(w['tailWorld'][1]);rows.setdefault(w['waveIndex'],[]).append((m,w))
  assert sorted(rows)==list(range(count)) and max(len(m['waves']) for m in r['metrics'])==count
  assert max(tips)-min(tips)<1e-6 and max(tails)-min(tails)<1e-6
  starts=[];per_wave=[]
  for i,entries in sorted(rows.items()):
   distances=[w['distance'] for _,w in entries]
   assert all(b+1e-6>=a for a,b in zip(distances,distances[1:]))
   after=[w for m,w in entries if m['action'] is None and w['age']<.85]
   assert len(after)>=2 and after[-1]['distance']-after[0]['distance']>.30
   starts.append(entries[0][0]['time']-entries[0][1]['age'])
   per_wave.append({'waveIndex':i,'firstFrame':entries[0][0]['frame'],'lastFrame':entries[-1][0]['frame'],'firstDistance':distances[0],'lastDistance':distances[-1],'postActionTravelBeforeAge085':after[-1]['distance']-after[0]['distance']})
  intervals=[b-a for a,b in zip(starts,starts[1:])];assert all(abs(x-.22)<1e-5 for x in intervals)
  natural=r['naturalCleanup'];assert not natural['waves'] and natural['castCacheSize']==0
  life=r['lifecycle'];a,b,c,d=(life[k] for k in ['before','paused','restored','advanced'])
  assert a['time']==b['time']==c['time'] and a['action']==b['action']==c['action']
  assert not b['warrior']['active'] and a['castOrigins']==b['castOrigins']==c['castOrigins']
  assert a['waveTransforms']==b['waveTransforms']
  assert len(c['waves'])==len(a['waves']) and c['cueCount']>0
  for x,y in zip(a['waves'],c['waves']):assert x['key']==y['key'] and max(abs(v-u) for v,u in zip(x['position'],y['position']))<1e-6
  assert d['time']>c['time'] and d['waves'][0]['distance']>c['waves'][0]['distance']
  e,f,g=(life[k] for k in ['engineBefore','engineAfter','engineResumed'])
  assert e['time']==f['time'] and e['waves']==f['waves'] and g['time']>f['time']
  cleared=life['cleared'];assert not cleared['warrior']['active'] and cleared['castCacheSize']==cleared['cueCount']==0
  assert life['poolCachesRetained']['meshesAfter']==life['poolCachesRetained']['meshCount']
  summaries[f'{scene}/rank{rank}']={'skillRank':rank,'waveCount':count,'skillHitCount':len(hits),'hitSegments':sorted({e['segment'] for e in hits}),'sameFixedGeometryAtAllRanksAndAges':True,'worldTipHeightRange':[min(tips),max(tips)],'worldTailHeightRange':[min(tails),max(tails)],'releaseIntervalsSeconds':intervals,'perWave':per_wave,'nativeClips':r['clips'],'noMidActionIdle':True,'naturalExpiryClean':True,'pauseMenu':life['pauseMenu'],'pauseClockAndTransformsHeld':True,'samePositionRestored':True,'continuedAfterResume':True,'enginePauseHeld':True,'explicitClearClean':True,'maximumLayers':max(len(m['warrior']['active']) for m in r['metrics']),'movingHits':verify_contacts(r,count)}
 assert len(all_hashes)==1
 exit=json.loads((CACHE/'training'/'exit-transition.json').read_text(encoding='utf8'))
 assert exit['sessionChanged'] and exit['trainingRangeReleased']
 assert exit['oldHP']==exit['oldHPAfter'] and exit['oldActiveAfter']==exit['oldCastOriginsAfter']==exit['newActiveAfter']==exit['newCastOriginsAfter']==exit['newGameplayCastsAfter']==0
 return summaries,next(iter(all_hashes))
def proof(summaries,game_hash):
 media={}
 expected={'wave-count-comparison.mp4':(108,30),'wave-count-1.mp4':(108,30),'wave-count-2.mp4':(108,30),'wave-count-3.mp4':(108,30),'three-waves-field.mp4':(108,30),'three-waves-slow.mp4':(58,15)}
 for name,(frames,rate) in expected.items():
  with av.open(str(OUT/name)) as movie:
   stream=movie.streams.video[0];count=sum(1 for _ in movie.decode(stream));assert count==frames and stream.average_rate==rate
   media[name]={'frames':count,'fps':str(stream.average_rate),'seconds':float(stream.duration*stream.time_base),'size':[stream.width,stream.height]}
 for name,source_frames,rate in [('wave-count-comparison.gif',108,30),('three-wave-detail-slow.gif',58,15),('single-wave-crescent.gif',43,15)]:
  with Image.open(OUT/name) as im:
   ms=0
   for i in range(im.n_frames):im.seek(i);im.load();ms+=im.info.get('duration',0)
   assert abs(ms-source_frames/rate*1000)<11
   media[name]={'frames':im.n_frames,'milliseconds':ms}
 sources=['capture.cjs','review-fixture.js','media.py']
 data={'status':'production moving-wave damage captured; visual review pending','productionIntegration':True,'generatedFrames':False,'gameHash':game_hash,'build':'src/cocos/build/concept-2d','profile':'normal test','captureBasis':'Only latest production bundle, its native WarriorSkillEffects and real combat clock. Disposable in-memory level-80 actor; no production dev bypass or persistent user context.','injectedScripts':['review-fixture.js'],'previewInjected':False,'customEffectsInjected':False,'rankWaveCounts':[1,2,2,3,3],'fiveActualRanksCovered':[1,2,3,4,5],'representativeMediaRanks':[1,3,5],'eachWaveDealsRealDamage':True,'totalFinalSegmentBudgetIncreased':False,'oldInstantFinalFanRemoved':True,'damageExplanation':'First two melee strikes retain .2/.2 damage. The final .6 budget is divided by the captured 1/2/2/3/3 pulse count; each pulse can damage each enemy once when its swept visible crest arrives. The old instant third fan is replaced.','primaryMedia':'media/three-wave-detail-slow.gif','validation':summaries,'lifecycleLimitation':'Field uses real pause/close; training uses its normal training-range paused branch. Actual leaveTrainingRange transition is separately recorded and verified clean.','hudImages':{'training':'src/.tmp/warrior-ultimate-moving-hits-v40/training/rank5/normal-hud.jpg','field':'src/.tmp/warrior-ultimate-moving-hits-v40/field/rank5/normal-hud.jpg'},'coarseStepCaveat':'GameSession.advance(.2) uses native logical steps <= .02; it is not an un-subdivided .2-second PureCombat sweep test','exitTransitionEvidence':'src/.tmp/warrior-ultimate-moving-hits-v40/training/exit-transition.json','taptapDevice':'not verified','media':media,'sourceFiles':{n:hashlib.sha256((BASE/n).read_bytes()).hexdigest() for n in sources},'files':{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.is_file()}}
 (BASE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(media,ensure_ascii=False))
if __name__=='__main__':
 summaries,game_hash=verify();gifs();single_detail_gif();movies();stages();proof(summaries,game_hash)
