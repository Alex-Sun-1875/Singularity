"""Package actual Cocos proposal captures; no generated or interpolated animation frames."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import json, hashlib
import av
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-ultimate-swoosh-wave-v33'
PREVIOUS=CACHE.parent/'warrior-ultimate-ground-cross-v32'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
SCENES={'training':'当前靶场','field':'游戏地面'}
@lru_cache(maxsize=12)
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if bold else 'msyh.ttc'),size)
def label(d,xy,s,size=23,fill='#dce5ec',bold=False):d.text(xy,s,font=font(size,bold),fill=fill)
def report(scene,variant='proposal'):return json.loads((CACHE/scene/variant/'capture.json').read_text(encoding='utf8'))
def frame(scene,index,slow=False):
 im=Image.new('RGB',(1280,710),'#171d22');d=ImageDraw.Draw(im)
 label(d,(18,9),'破晓裁决 · 厚前头、细尖尾的勾形冲击波',27,bold=True)
 label(d,(910,14),SCENES[scene]+' / '+('0.5× 慢放' if slow else '原速'),20,fill='#acbbc7')
 with Image.open(CACHE/scene/'proposal'/f'{index:03d}.jpg') as shot:im.paste(shot.convert('RGB'),(0,48))
 label(d,(18,680),'第三段全新轮廓与气浪材质 · 原生角色动态小样，尚未接入',20)
 return im
def write_video(name,images,rate=30):
 with av.open(str(OUT/name),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
  stream=movie.add_stream('libx264',rate=rate);stream.width,stream.height=images[0].size;stream.pix_fmt='yuv420p';stream.options={'crf':'17','preset':'veryfast'};stream.codec_context.thread_count=3
  for i,image in enumerate(images):
   f=av.VideoFrame.from_image(image);f.pts=i;f.time_base=Fraction(1,rate)
   for p in stream.encode(f):movie.mux(p)
  for p in stream.encode():movie.mux(p)
def movies():
 pictures=[frame(scene,i) for scene in SCENES for i in range(report(scene)['frames'])]
 write_video('ultimate-motion-study.mp4',pictures)
 write_video('ultimate-slow.mp4',[frame('training',i,True) for i in range(27,82)],15)
 compare=[]
 for i in range(report('training')['frames']):
  im=Image.new('RGB',(1600,478),'#171d22');d=ImageDraw.Draw(im)
  label(d,(18,9),'当前游戏效果',24,bold=True);label(d,(818,9),'动态方案 · 纵向勾形冲击波',24,bold=True)
  for x,variant in [(0,'current'),(800,'proposal')]:
   with Image.open(CACHE/'training'/variant/f'{i:03d}.jpg') as shot:im.paste(shot.convert('RGB').resize((800,390),Image.Resampling.LANCZOS),(x,46))
  label(d,(18,446),'相同角色、动作、机位与时间 / 原速',20)
  label(d,(818,446),'隔离预览 / 未替换正式游戏效果',20)
  compare.append(im)
 write_video('current-vs-proposal.mp4',compare)
 previous_compare=[]
 for scene in SCENES:
  for i in range(report(scene)['frames']):
   im=Image.new('RGB',(1600,478),'#171d22');d=ImageDraw.Draw(im)
   label(d,(18,9),'上版 · 交错与横向月牙',24,bold=True);label(d,(818,9),'本版 · 细尾朝身、厚头前冲',24,bold=True)
   for x,source in [(0,PREVIOUS/scene/'proposal'),(800,CACHE/scene/'proposal')]:
    with Image.open(source/f'{i:03d}.jpg') as shot:im.paste(shot.convert('RGB').resize((800,390),Image.Resampling.LANCZOS),(x,46))
   label(d,(18,446),SCENES[scene]+' / 同角色、同机位、同时刻 / 原速',20)
   label(d,(818,446),'第三段重新设计 · 新轮廓、新密度与流动细节',20)
   previous_compare.append(im)
 write_video('previous-vs-swoosh.mp4',previous_compare)
def gif():
 pictures=[frame('training',i).resize((960,532),Image.Resampling.LANCZOS) for i in range(90)]
 sample=Image.new('RGB',(480,798))
 for row,i in enumerate([38,49,59]):sample.paste(pictures[i].resize((480,266)),(0,row*266))
 palette=sample.quantize(256,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 indexed[0].save(OUT/'ultimate-motion-study.gif',save_all=True,append_images=indexed[1:],duration=[(round((i+1)*100/30)-round(i*100/30))*10 for i in range(90)],loop=0,optimize=True,disposal=1)
def detail_gif():
 pictures=[]
 indices=list(range(32,78))
 for i in indices:
  im=Image.new('RGB',(960,688),'#171d22');d=ImageDraw.Draw(im)
  label(d,(16,10),'第三段 · 细尖尾朝身体，厚前头向前冲 / 0.5×',25,bold=True)
  with Image.open(CACHE/'training'/'proposal'/f'{i:03d}.jpg') as shot:im.paste(shot.convert('RGB').crop((320,0,1180,570)).resize((960,636),Image.Resampling.LANCZOS),(0,48))
  pictures.append(im)
 sample=Image.new('RGB',(480,1032))
 for row,i in enumerate([6,17,29]):sample.paste(pictures[i].resize((480,344)),(0,row*344))
 palette=sample.quantize(256,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 indexed[0].save(OUT/'wave-detail-slow.gif',save_all=True,append_images=indexed[1:],duration=[(round((i+1)*100/15)-round(i*100/15))*10 for i in range(len(indices))],loop=0,optimize=True,disposal=1)
def stages():
 im=Image.new('RGB',(1800,792),'#171d22');d=ImageDraw.Draw(im)
 label(d,(18,10),'前厚后细 · 非对称纵向勾形冲击波',30,bold=True)
 for i,(index,name) in enumerate([(35,'新勾形展开'),(38,'厚前头释放'),(43,'离体推进'),(49,'收招后前进'),(55,'细尖尾后拉'),(61,'移动消散')]):
  x=i%3*600;y=62+i//3*356
  with Image.open(CACHE/'training'/'proposal'/f'{index:03d}.jpg') as shot:im.paste(shot.convert('RGB').resize((596,291),Image.Resampling.LANCZOS),(x+2,y))
  label(d,(x+16,y+302),f'{name}  {(index+1)/30:.2f}s',23,bold=True)
 im.save(OUT/'motion-stages.jpg',quality=95,subsampling=0)
 frame('training',43).save(OUT/'combined-peak.jpg',quality=95,subsampling=0)
 # Every panel uses one fixed crop, so displacement is not produced by reframing.
 travel=Image.new('RGB',(2160,1144),'#171d22');d=ImageDraw.Draw(travel)
 label(d,(20,12),'细尾指向人物 · 厚前头持续前冲',31,bold=True)
 metrics={m['frame']:m for m in report('training')['metrics']}
 for i,index in enumerate([38,43,49,55,61,64]):
  x=i%3*720;y=68+i//3*532;m=metrics[index];p=m.get('phase') or {}
  with Image.open(CACHE/'training'/'proposal'/f'{index:03d}.jpg') as shot:travel.paste(shot.convert('RGB').crop((320,0,1180,570)).resize((712,472),Image.Resampling.LANCZOS),(x+4,y))
  state='动作中' if m['action'] else '已收招'
  distance=p.get('distance',0)
  label(d,(x+16,y+484),f'{(index+1)/30:.2f}s · 距出生点 {distance:.2f}m · {state}',22,bold=True)
 travel.save(OUT/'wave-travel-stages.jpg',quality=95,subsampling=0)
def verify():
 summaries={}
 for scene in SCENES:
  a,b=report(scene,'current'),report(scene)
  assert a['gameHash']==b['gameHash'],'Reused baseline comes from a different compiled game'
  hits=lambda r:[e for e in r['events'] if e['type'] in ['hit','skill_hit']]
  assert hits(a)==hits(b),'Gameplay events changed'
  assert not b['errors'] and b['frames']==90
  assert all(m['renderReady'] and not m['warrior']['droppedLayers'] for m in b['metrics'])
  drops=[m for m in b['metrics'] if m.get('swooshMetrics')]
  assert len(drops)>2,'No sustained redesigned swoosh wave'
  assert all(m.get('waveNormals') for m in drops),'Missing measured wave normals'
  assert all(abs(normal['y'])>.99999 for m in drops for normal in m['waveNormals']),'Wave plane is not parallel to the ground'
  assert all(m.get('tipWidths') for m in drops),'Missing measured mesh tip widths'
  tip_widths=[width[end] for m in drops for width in m['tipWidths'] for end in ['start','end']]
  assert all(0<=width<1e-5 for width in tip_widths),'Crescent ends do not converge to points'
  swooshes=[wave for m in drops for wave in m['swooshMetrics']]
  assert all(wave['frontLocalZ']>wave['tailLocalZ']+1 for wave in swooshes),'Thick head does not lead the fine tail'
  assert all(wave['minVertexHeight']>=.06-1e-6 and wave['maxVertexHeight']<=.20+1e-6 for wave in swooshes),'Swoosh does not stay near terrain'
  assert all(wave['material']=='Isolated:SwooshAir:v33' and wave['effect']=='Isolated:SwooshAir:v33' for wave in swooshes),'Redesigned air material is not active'
  formed=[wave for m in drops if m['phase']['age']>.1 for wave in m['swooshMetrics']]
  assert formed and all(wave['headSectionWidth']>1 for wave in formed),'Formed leading head is not broad enough'
  distances=[m['phase']['distance'] for m in drops]
  assert all(b+1e-6>=a for a,b in zip(distances,distances[1:])),'Wave moves backwards'
  assert distances[-1]-distances[0]>1.0,'Wave does not travel visibly'
  for m in drops:
   p=m['phase'];position,launch,forward=p['position'],p['launchFoot'],p['forward']
   assert abs(forward[0]**2+forward[2]**2-1)<1e-4
   dx,dz=position[0]-launch[0],position[2]-launch[2]
   assert abs(dx*forward[0]+dz*forward[2]-p['distance'])<1e-4,'Reported travel differs from world motion'
   assert abs(dx*forward[2]-dz*forward[0])<1e-4,'Wave leaves the cast direction'
   assert 0<=p['formation']<=1
   for wave in m['swooshMetrics']:
    tail=wave['tailWorld'];tail_back=(tail[0]-position[0])*forward[0]+(tail[2]-position[2])*forward[2]
    assert tail_back<0,'Fine tail does not point behind the moving head'
  after_action=[m for m in drops if m['action'] is None and m['phase']['age']<.85]
  assert len(after_action)>=2,'No traveling wave after action recovery'
  post_action_travel=after_action[-1]['phase']['distance']-after_action[0]['phase']['distance']
  assert post_action_travel>.30,'Wave stops when the actor recovers'
  assert all(any(l['key'].endswith(':ultimate-downcut') and l['mode']=='traveling-swoosh-wave' for l in m['warrior']['active']) for m in drops)
  active=[m for m in b['metrics'] if m['action']]
  assert all(m['pose']['state']!='idle' for m in active),'Action returns to idle mid-chain'
  assert {'attack_sword','attack_sword_2','attack_sword_3'}<=set(b['clips'])
  skill_hits=len([e for e in b['events'] if e['type']=='skill_hit']);assert skill_hits==5
  previous=json.loads((PREVIOUS/scene/'proposal'/'capture.json').read_text(encoding='utf8'))
  assert previous['gameHash']==b['gameHash'],'Previous comparison comes from a different compiled game'
  assert hits(previous)==hits(b),'Hits differ from the previous proposal'
  assert previous['frames']==b['frames']
  summaries[scene]={'gameHash':b['gameHash'],'frames':b['frames'],'nativeClips':b['clips'],'sameBeforeAfterHits':True,'samePreviousProposalHits':True,'skillHits':skill_hits,'redesignedWaveActiveFrames':len(drops),'wavePlaneParallelToGround':True,'minimumAbsoluteNormalY':min(abs(normal['y']) for m in drops for normal in m['waveNormals']),'bothHookTerminalsPointed':True,'maximumMeasuredTipWidthMetres':max(tip_widths),'minimumFrontToTailSpan':min(wave['frontLocalZ']-wave['tailLocalZ'] for wave in swooshes),'minimumFormedHeadSectionWidth':min(wave['headSectionWidth'] for wave in formed),'minimumVertexTerrainClearance':min(wave['minVertexHeight'] for wave in swooshes),'maximumVertexTerrainClearance':max(wave['maxVertexHeight'] for wave in swooshes),'newAirMaterialActive':True,'fineTailPointsBehindHead':True,'travelMonotonic':True,'travelAlongCastDirection':True,'firstActiveDistance':distances[0],'lastActiveDistance':distances[-1],'postActionTravelBeforeAge085':post_action_travel,'thirdShape':'asymmetrical forward-heavy swoosh; fine pointed tail toward the actor, broad leading hook advanced forward','maxLayers':max(len(m['warrior']['active']) for m in b['metrics']),'noMidActionIdle':True}
 return summaries
def proof(summaries):
 media={}
 for p in OUT.glob('*.mp4'):
  with av.open(str(p)) as movie:
   stream=movie.streams.video[0];count=sum(1 for _ in movie.decode(stream))
   media[p.name]={'frames':count,'fps':str(stream.average_rate),'seconds':float(stream.duration*stream.time_base),'size':[stream.width,stream.height]}
 assert media['ultimate-motion-study.mp4']['frames']==180
 assert media['current-vs-proposal.mp4']['frames']==90
 assert media['previous-vs-swoosh.mp4']['frames']==180
 assert media['ultimate-slow.mp4']['frames']==55
 with Image.open(OUT/'ultimate-motion-study.gif') as im:
  ms=0
  for i in range(im.n_frames):im.seek(i);im.load();ms+=im.info.get('duration',0)
  assert ms==3000
  media['ultimate-motion-study.gif']={'frames':im.n_frames,'milliseconds':ms}
 with Image.open(OUT/'wave-detail-slow.gif') as im:
  ms=0
  for i in range(im.n_frames):im.seek(i);im.load();ms+=im.info.get('duration',0)
  assert abs(ms-46/15*1000)<11
  media['wave-detail-slow.gif']={'frames':im.n_frames,'milliseconds':ms,'crop':[320,0,1180,570],'speed':0.5}
 sources=['swoosh-profile.json','swoosh.frag','build-flow.py','swoosh-flow.png','swoosh-flow.rgba']
 data={'status':'isolated redesigned swoosh motion proposal; not integrated; user art acceptance pending','productionIntegration':False,'generatedFrames':False,'basis':'Current compiled game native actor, three clips and session clock; the third-stage old crossing branches and old moon are replaced by one new horizontal asymmetrical swoosh mesh, new air-density fragment shader and deterministic 256-pixel flow texture. First two attacks and original native actor chain remain.','revisionScope':'complete third-stage visual redesign; native actor clips, shield and gameplay damage rules unchanged','designDirection':'thick leading hook advanced forward; fine pointed tail toward the actor; detached forward travel','profileParameters':'swoosh-profile.json','shaderSource':'swoosh.frag','flowTexture':'swoosh-flow.png','flowGeneration':'deterministic local build-flow.py; no image generation','sourceAssets':{name:hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in sources},'currentBaseline':{'reusedFrom':'v32 current recordings for training and field','reason':'same immutable compiled game, actor/camera setup, viewport and deterministic clock; original true frames reused without repainting, synthesizing or altering game content','sameCompiledGameVerified':True},'groundConformance':True,'nativeClipTracksModified':False,'presentationContactHold':'disabled for proposal WAR_05 to preserve continuous native motion sampling','damageRulesModified':False,'travelTailAddsDamage':False,'previousComparison':'v32 proposal and v33 proposal, same scene/frame/camera','validation':summaries,'media':media,'taptapDevice':'not verified','files':{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.is_file()}}
 (BASE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(media,ensure_ascii=False))
if __name__=='__main__':
 summaries=verify();movies();gif();detail_gif();stages();proof(summaries)
