"""Package independently rendered 1/2/3-wave game captures; no synthesized game frames."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
from itertools import chain
import json, hashlib, re
import av
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-ultimate-matched-crescents-v38'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
CASES=[('training',1),('training',2),('training',3),('field',3)]
BANDS={1:'技能1级',2:'技能2–3级',3:'技能4–5级'}
FPS=30;FRAMES=108
MAIN=re.compile(r':ultimate-downcut:wave:(\d+)$')
@lru_cache(maxsize=12)
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if bold else 'msyh.ttc'),size)
def label(d,xy,s,size=23,fill='#dce5ec',bold=False):d.text(xy,s,font=font(size,bold),fill=fill)
@lru_cache(maxsize=8)
def report(scene,count,variant='proposal'):return json.loads((CACHE/scene/f'rank{count}'/variant/'capture.json').read_text(encoding='utf8'))
def raw_path(scene,count,index,variant='proposal'):return CACHE/scene/f'rank{count}'/variant/f'{index:03d}.jpg'
def main_indices(metric):return {int(match.group(1)) for layer in metric['warrior']['active'] if (match:=MAIN.search(layer['key']))}
def frame(scene,count,index,slow=False):
 im=Image.new('RGB',(1280,710),'#171d22');d=ImageDraw.Draw(im);rank=report(scene,count)['skillRank']
 label(d,(18,9),f'战士最终技 · 红线月牙·连续{count}道',27,bold=True)
 label(d,(860,14),('靶场' if scene=='training' else '普通地面')+f' / Lv{rank} / '+('0.5×' if slow else '原速'),20,fill='#acbbc7')
 with Image.open(raw_path(scene,count,index)) as shot:im.paste(shot.convert('RGB'),(0,48))
 label(d,(18,680),'沿参考红线重画 · 每道同形同高，仅位置与释放时间不同 · 尚未接入',20)
 return im
def comparison_frame(index):
 im=Image.new('RGB',(1800,536),'#171d22');d=ImageDraw.Draw(im)
 label(d,(18,7),'战士最终技 · 红线月牙，按等级连续 1 / 2 / 3 道',29,bold=True)
 for col,count in enumerate([1,2,3]):
  x=col*600;rank=report('training',count)['skillRank']
  label(d,(x+18,48),f'{count}道 · {BANDS[count]}（实录Lv{rank}）',23,bold=True)
  with Image.open(raw_path('training',count,index)) as shot:im.paste(shot.convert('RGB').crop((320,0,1180,570)).resize((600,398),Image.Resampling.LANCZOS),(x,82))
 label(d,(18,497),'同一刀气轮廓与高度 · 只改变道数、位置与释放时间 · 独立实录，尚未接入',20)
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
 for count in [1,2,3]:write_video(f'wave-count-{count}.mp4',(frame('training',count,i) for i in range(FRAMES)))
 write_video('three-waves-field.mp4',(frame('field',3,i) for i in range(FRAMES)))
 write_video('three-waves-slow.mp4',(frame('training',3,i,True) for i in range(32,90)),15)
def write_gif(name,pictures,rate,samples):
 w,h=pictures[0].size;sample=Image.new('RGB',(w//2,h//2*len(samples)))
 for row,index in enumerate(samples):sample.paste(pictures[index].resize((w//2,h//2)),(0,row*(h//2)))
 palette=sample.quantize(256,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 durations=[(round((i+1)*100/rate)-round(i*100/rate))*10 for i in range(len(indexed))]
 indexed[0].save(OUT/name,save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=True,disposal=1)
def gifs():
 pictures=[comparison_frame(i).resize((1350,402),Image.Resampling.LANCZOS) for i in range(FRAMES)]
 write_gif('wave-count-comparison.gif',pictures,30,[43,53,64])
 pictures=[]
 for index in range(32,90):
  im=Image.new('RGB',(960,688),'#171d22');d=ImageDraw.Draw(im)
  label(d,(16,10),'3道连续释放 · 同形同高红线月牙 / 0.5×',24,bold=True)
  with Image.open(raw_path('training',3,index)) as shot:im.paste(shot.convert('RGB').crop((320,0,1180,570)).resize((960,636),Image.Resampling.LANCZOS),(0,48))
  pictures.append(im)
 write_gif('three-wave-detail-slow.gif',pictures,15,[9,22,34])
def single_detail_gif():
 pictures=[]
 for index in range(35,78):
  im=Image.new('RGB',(960,688),'#171d22');d=ImageDraw.Draw(im)
  label(d,(16,10),'单道近景 · 沿红线重画，高前尖、深回弯 / 0.5×',24,bold=True)
  with Image.open(raw_path('training',1,index)) as shot:im.paste(shot.convert('RGB').crop((320,0,1180,570)).resize((960,636),Image.Resampling.LANCZOS),(0,48))
  pictures.append(im)
 write_gif('single-wave-crescent.gif',pictures,15,[5,13,22])
def stages():
 comparison_frame(53).save(OUT/'wave-count-overview.jpg',quality=95,subsampling=0)
 im=Image.new('RGB',(2160,1144),'#171d22');d=ImageDraw.Draw(im)
 label(d,(20,12),'三道红线月牙连续接出 · 同形同高，分别向前推进',31,bold=True)
 metrics={m['frame']:m for m in report('training',3)['metrics']}
 for i,(index,title) in enumerate([(35,'第1道形成'),(42,'第2道接出'),(48,'第3道接出'),(55,'先后向前推进'),(62,'分别消散'),(71,'后波继续前进')]):
  x=i%3*720;y=68+i//3*532;m=metrics[index]
  with Image.open(raw_path('training',3,index)) as shot:im.paste(shot.convert('RGB').crop((320,0,1180,570)).resize((712,472),Image.Resampling.LANCZOS),(x+4,y))
  label(d,(x+16,y+484),f'{title} · 活跃{len(main_indices(m))}道 · {(index+1)/30:.2f}s',22,bold=True)
 im.save(OUT/'three-wave-stages.jpg',quality=95,subsampling=0)
def verify():
 profile=json.loads((BASE/'swoosh-profile.json').read_text(encoding='utf8'))
 assert profile['rankWaveCounts']=={'1':1,'2':2,'3':2,'4':3,'5':3},'Rank-to-wave mapping differs from the user selection'
 summaries={};canonical_outline=None;canonical_height=None
 for scene,count in CASES:
  before,after=report(scene,count,'current'),report(scene,count)
  assert before['gameHash']==after['gameHash']
  assert before['skillRank']==after['skillRank'] and before['waveCount']==after['waveCount']==count
  assert profile['rankWaveCounts'][str(after['skillRank'])]==count
  hits=lambda r:[e for e in r['events'] if e['type'] in ['hit','skill_hit']]
  assert hits(before)==hits(after),'Gameplay hits differ at the same real skill rank'
  skill_hits=[e for e in after['events'] if e['type']=='skill_hit']
  assert skill_hits and {e['segment'] for e in skill_hits}=={0,1,2}
  assert before['frames']==after['frames']==FRAMES and not after['errors']
  assert len(list((CACHE/scene/f'rank{count}'/'proposal').glob('[0-9][0-9][0-9].jpg')))==FRAMES
  assert all(m['renderReady'] and not m['warrior']['droppedLayers'] and m['sharedMeshForAll'] for m in after['metrics'])
  active_action=[m for m in after['metrics'] if m['action']]
  assert all(m['pose']['state']!='idle' for m in active_action),'Native chain resets to idle mid-action'
  assert {'attack_sword','attack_sword_2','attack_sword_3'}<=set(after['clips'])
  per_wave={};snapshots=[];world_tip_y=[];world_tail_y=[]
  for m in after['metrics']:
   indices=main_indices(m)
   if not indices:continue
   phases={int(p['waveIndex']):p for p in m['phases']}
   normals={int(n['waveIndex']):n for n in m['waveNormals']}
   tips={int(t['waveIndex']):t for t in m['tipWidths']}
   shapes={int(s['waveIndex']):s for s in m['swooshMetrics']}
   assert indices==set(shapes) and indices<=set(phases) and indices==set(normals)==set(tips),'Wave-index measurements are not paired'
   snapshots.append(len(indices))
   for index in sorted(indices):
    p,n,tip,shape=phases[index],normals[index],tips[index],shapes[index]
    assert any(MAIN.search(l['key']) and int(MAIN.search(l['key']).group(1))==index and l['mode']=='matched-crescent-wave' for l in m['warrior']['active'])
    forward=p['forward'];position=p['position'];launch=p['launchFoot']
    assert abs(n['y'])<1e-5 and abs(n['x']*forward[0]+n['y']*forward[1]+n['z']*forward[2])<1e-5,'Wave is not upright in the cast plane'
    assert 0<=tip['start']<1e-5 and 0<=tip['end']<1e-5
    assert shape['material']==shape['effect']=='Isolated:MatchedCrescent:v38'
    assert shape['template']=='AuthoredRedCrescentV38'
    assert shape['frontLocalZ']>shape['tailLocalZ']+1
    assert shape['localHeightRange'][0]>=.04-1e-6 and shape['localTipY']>3.5
    assert all(abs(s-1)<1e-6 for s in shape['worldScale'])
    assert shape['headSectionWidth']>.65
    outline=shape['localOutlineSamples'];height=shape['localHeightRange']
    assert len(outline)==18 and all(len(point)==3 for point in outline)
    if canonical_outline is None:canonical_outline=outline;canonical_height=height
    assert outline==canonical_outline,'Wave geometry changes with ordinal or age'
    assert height==canonical_height,'Local wave height changes with ordinal or age'
    assert abs(position[1]-launch[1])<1e-6,'Wave height follows terrain instead of the cast origin'
    world_tip_y.append(shape['tipWorld'][1]);world_tail_y.append(shape['tailWorld'][1])
    assert abs(forward[0]**2+forward[2]**2-1)<1e-4
    dx,dz=position[0]-launch[0],position[2]-launch[2]
    assert abs(dx*forward[0]+dz*forward[2]-p['distance'])<1e-4
    assert abs(dx*forward[2]-dz*forward[0])<1e-4
    assert abs(p['formation']-1)<1e-6 and abs(p['scale']-1)<1e-6
    tail=shape['tailWorld'];assert abs(tail[0]-position[0])<1e-6 and abs(tail[2]-position[2])<1e-6,'Reference tail differs from the zero-offset wave origin'
    per_wave.setdefault(index,[]).append({'frame':m['frame'],'action':m['action'],'phase':p,'shape':shape})
  assert sorted(per_wave)==list(range(count)),'Distinct wave count differs from the requested count'
  assert max(snapshots)==count,'Sequential waves never overlap as expected'
  assert max(world_tip_y)-min(world_tip_y)<1e-6,'Tip world height changes between waves or ages'
  assert max(world_tail_y)-min(world_tail_y)<1e-6,'Tail world height changes between waves or ages'
  wave_summary=[];births=[]
  for index,rows in sorted(per_wave.items()):
   distances=[r['phase']['distance'] for r in rows]
   assert all(b+1e-6>=a for a,b in zip(distances,distances[1:]))
   assert distances[-1]-distances[0]>1.0,'One wave fails to travel visibly'
   after_action=[r for r in rows if r['action'] is None and r['phase']['age']<.85]
   assert len(after_action)>=2,'One wave has no continuing flight after recovery'
   post_travel=after_action[-1]['phase']['distance']-after_action[0]['phase']['distance']
   assert post_travel>.30,'One wave stops when the character recovers'
   birth=(rows[0]['frame']+1)/FPS-rows[0]['phase']['age'];births.append(birth)
   wave_summary.append({'waveIndex':index,'firstActiveFrame':rows[0]['frame'],'lastActiveFrame':rows[-1]['frame'],'estimatedStartSeconds':birth,'firstDistance':distances[0],'lastDistance':distances[-1],'postActionTravelBeforeAge085':post_travel,'scales':sorted({r['phase']['scale'] for r in rows}),'formations':sorted({r['phase']['formation'] for r in rows}),'localTipY':rows[0]['shape']['localTipY'],'localHeightRange':rows[0]['shape']['localHeightRange'],'minimumTailHeightAboveTerrain':min(r['shape']['tailHeight'] for r in rows),'maximumTailHeightAboveTerrain':max(r['shape']['tailHeight'] for r in rows),'minimumMeshHeightAboveTerrain':min(r['shape']['minVertexHeight'] for r in rows)})
  intervals=[b-a for a,b in zip(births,births[1:])]
  assert all(abs(interval-.22)<=.04+1e-6 for interval in intervals),'Release spacing is not continuous'
  summaries[f'{scene}/rank{count}']={'scene':scene,'waveCount':count,'skillRank':after['skillRank'],'gameHash':after['gameHash'],'frames':FRAMES,'sameRankGameplayHitsMatched':True,'skillHitCount':len(skill_hits),'nativeClips':after['clips'],'noMidActionIdle':True,'distinctWaveCount':len(per_wave),'maximumSimultaneousMainWaves':max(snapshots),'allAgesAndOrdinalsSameLocalOutline':True,'worldTipHeightRange':[min(world_tip_y),max(world_tip_y)],'worldTailHeightRange':[min(world_tail_y),max(world_tail_y)],'startIntervalsSeconds':intervals,'perWave':wave_summary,'maxLayers':max(len(m['warrior']['active']) for m in after['metrics'])}
 return profile,summaries
def proof(profile,summaries):
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
 assets=['swoosh-profile.json','swoosh.frag','build-flow.py','swoosh-flow.png','swoosh-flow.rgba']
 data={'status':'isolated matched red-outline crescent proposal; not integrated; user art acceptance pending','productionIntegration':False,'generatedFrames':False,'basis':'Current compiled game native actor chain and gameplay clock. Separately rendered real-rank cases are arranged in three columns; each case has its own same-rank current control.','revisionScope':'one fixed user-traced red-outline crescent template shared by all pulses; no ordinal scaling, age-driven reshaping or terrain-following height changes; rank mapping, release rhythm and forward trajectories retained','rankWaveCounts':profile['rankWaveCounts'],'representativeCases':[{k:r[k] for k in ['scene','waveCount','skillRank']} for r in summaries.values()],'releaseIntervalSeconds':profile['pulseInterval'],'individualWaveLifeSeconds':profile['waveLife'],'visualWindowSeconds':profile['visualDuration'],'geometryAndMaterial':'higher front tip and deeper return matching the reference; fixed geometry and world height for every pulse; v35 flow texture with isolated v38 material','sameShapeAndHeightValidation':'all 18 sampled local outline points and the local height range match across every active age and ordinal in all cases; scale and formation equal 1; tip and tail world heights are constant within each scene case','primaryMedia':'media/three-wave-detail-slow.gif','currentControls':{'recordingSource':'all eight current/proposal recordings freshly captured for v38','reason':'new shared camera centre=3.6 height=5.9; no old capture reuse; each current/proposal pair uses the same compiled game, viewport, real skill rank and deterministic clock','sameCompiledGameAndRankVerified':True},'nativeClipTracksModified':False,'damageRulesModified':False,'extraVisualWavesAddDamage':False,'sourceAssets':{n:hashlib.sha256((BASE/n).read_bytes()).hexdigest() for n in assets},'validation':summaries,'media':media,'taptapDevice':'not verified','files':{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.is_file()}}
 (BASE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(media,ensure_ascii=False))
if __name__=='__main__':
 profile,summaries=verify();gifs();single_detail_gif();movies();stages();proof(profile,summaries)
