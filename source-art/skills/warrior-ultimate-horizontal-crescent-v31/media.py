"""Package actual Cocos proposal captures; no generated or interpolated animation frames."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import json, hashlib
import av
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-ultimate-horizontal-crescent-v31'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
SCENES={'training':'当前靶场','field':'游戏地面'}
@lru_cache(maxsize=12)
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if bold else 'msyh.ttc'),size)
def label(d,xy,s,size=23,fill='#dce5ec',bold=False):d.text(xy,s,font=font(size,bold),fill=fill)
def report(scene,variant='proposal'):return json.loads((CACHE/scene/variant/'capture.json').read_text(encoding='utf8'))
def frame(scene,index,slow=False):
 im=Image.new('RGB',(1280,710),'#171d22');d=ImageDraw.Draw(im)
 label(d,(18,9),'破晓裁决 · 水平双尖·不规则月牙刀气',27,bold=True)
 label(d,(910,14),SCENES[scene]+' / '+('0.5× 慢放' if slow else '原速'),20,fill='#acbbc7')
 with Image.open(CACHE/scene/'proposal'/f'{index:03d}.jpg') as shot:im.paste(shot.convert('RGB'),(0,48))
 label(d,(18,680),'角色下劈动作保持 · 刀气水平飞出，尚未接入',20)
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
  label(d,(18,9),'当前游戏效果',24,bold=True);label(d,(818,9),'动态方案 · 水平双尖月牙刀气',24,bold=True)
  for x,variant in [(0,'current'),(800,'proposal')]:
   with Image.open(CACHE/'training'/variant/f'{i:03d}.jpg') as shot:im.paste(shot.convert('RGB').resize((800,390),Image.Resampling.LANCZOS),(x,46))
  label(d,(18,446),'相同角色、动作、机位与时间 / 原速',20)
  label(d,(818,446),'隔离预览 / 未替换正式游戏效果',20)
  compare.append(im)
 write_video('current-vs-proposal.mp4',compare)
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
  label(d,(16,10),'第三段 · 水平双尖·不规则月牙刀气 / 0.5×',25,bold=True)
  with Image.open(CACHE/'training'/'proposal'/f'{i:03d}.jpg') as shot:im.paste(shot.convert('RGB').crop((320,0,1180,570)).resize((960,636),Image.Resampling.LANCZOS),(0,48))
  pictures.append(im)
 sample=Image.new('RGB',(480,1032))
 for row,i in enumerate([6,17,29]):sample.paste(pictures[i].resize((480,344)),(0,row*344))
 palette=sample.quantize(256,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 indexed[0].save(OUT/'wave-detail-slow.gif',save_all=True,append_images=indexed[1:],duration=[(round((i+1)*100/15)-round(i*100/15))*10 for i in range(len(indices))],loop=0,optimize=True,disposal=1)
def stages():
 im=Image.new('RGB',(1800,792),'#171d22');d=ImageDraw.Draw(im)
 label(d,(18,10),'水平双尖·不规则月牙刀气 · 保留原下劈动作',30,bold=True)
 for i,(index,name) in enumerate([(35,'交叉成形'),(38,'双尖刀气释放'),(43,'水平推进'),(49,'收招后前进'),(55,'细尾拉开'),(61,'移动消散')]):
  x=i%3*600;y=62+i//3*356
  with Image.open(CACHE/'training'/'proposal'/f'{index:03d}.jpg') as shot:im.paste(shot.convert('RGB').resize((596,291),Image.Resampling.LANCZOS),(x+2,y))
  label(d,(x+16,y+302),f'{name}  {(index+1)/30:.2f}s',23,bold=True)
 im.save(OUT/'motion-stages.jpg',quality=95,subsampling=0)
 frame('training',43).save(OUT/'combined-peak.jpg',quality=95,subsampling=0)
 # Every panel uses one fixed crop, so displacement is not produced by reframing.
 travel=Image.new('RGB',(2160,1144),'#171d22');d=ImageDraw.Draw(travel)
 label(d,(20,12),'刀气与地面平行 · 保留原推进与消散',31,bold=True)
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
  hits=lambda r:[e for e in r['events'] if e['type'] in ['hit','skill_hit']]
  assert hits(a)==hits(b),'Gameplay events changed'
  assert not b['errors'] and b['frames']==90
  assert all(m['renderReady'] and not m['warrior']['droppedLayers'] for m in b['metrics'])
  both=[m for m in b['metrics'] if m['crossAngles'] and any(l['key'].endswith(':ultimate-downcut') for l in m['warrior']['active'])]
  assert len(both)>2,'No sustained combined wave frames'
  drops=[m for m in b['metrics'] if m.get('waveNormals')]
  assert drops,'No active horizontal wave plane'
  assert all(abs(normal['y'])>.99999 for m in drops for normal in m['waveNormals']),'Wave plane is not parallel to the ground'
  assert all(m.get('tipWidths') for m in drops),'Missing measured mesh tip widths'
  tip_widths=[width[end] for m in drops for width in m['tipWidths'] for end in ['start','end']]
  assert all(0<=width<1e-5 for width in tip_widths),'Crescent ends do not converge to points'
  assert all(abs(angle-120)<.03 for m in b['metrics'] for angle in m['crossAngles'])
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
  after_action=[m for m in drops if m['action'] is None and m['phase']['age']<.85]
  assert len(after_action)>=2,'No traveling wave after action recovery'
  post_action_travel=after_action[-1]['phase']['distance']-after_action[0]['phase']['distance']
  assert post_action_travel>.30,'Wave stops when the actor recovers'
  assert all(any(l['key'].endswith(':ultimate-downcut') and l['mode']=='traveling-saber-wave' for l in m['warrior']['active']) for m in drops)
  active=[m for m in b['metrics'] if m['action']]
  assert all(m['pose']['state']!='idle' for m in active),'Action returns to idle mid-chain'
  assert {'attack_sword','attack_sword_2','attack_sword_3'}<=set(b['clips'])
  skill_hits=len([e for e in b['events'] if e['type']=='skill_hit']);assert skill_hits==5
  summaries[scene]={'gameHash':b['gameHash'],'frames':b['frames'],'nativeClips':b['clips'],'sameBeforeAfterHits':True,'skillHits':skill_hits,'simultaneousCrossDownFrames':len(both),'crossAngleDegrees':120,'wavePlaneParallelToGround':True,'minimumAbsoluteNormalY':min(abs(normal['y']) for m in drops for normal in m['waveNormals']),'bothMeshEndsPointed':True,'maximumMeasuredTipWidthMetres':max(tip_widths),'travelMonotonic':True,'travelAlongCastDirection':True,'firstActiveDistance':distances[0],'lastActiveDistance':distances[-1],'postActionTravelBeforeAge085':post_action_travel,'thirdShape':'horizontal irregular crescent with two pointed ends, thick front and fine trailing wake','maxLayers':max(len(m['warrior']['active']) for m in b['metrics']),'noMidActionIdle':True}
 return summaries
def proof(summaries):
 media={}
 for p in OUT.glob('*.mp4'):
  with av.open(str(p)) as movie:
   stream=movie.streams.video[0];count=sum(1 for _ in movie.decode(stream))
   media[p.name]={'frames':count,'fps':str(stream.average_rate),'seconds':float(stream.duration*stream.time_base),'size':[stream.width,stream.height]}
 assert media['ultimate-motion-study.mp4']['frames']==180
 assert media['current-vs-proposal.mp4']['frames']==90
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
 data={'status':'isolated horizontal-crescent motion proposal; not integrated; user art acceptance pending','productionIntegration':False,'generatedFrames':False,'basis':'Current compiled game native actor, three clips, pressure shader and session clock; v29 forward travel, material and 1.05-second timing retained. Only the released wave changes to a horizontal irregular crescent with pointed ends; original overhead actor motion and 120-degree crossing remain.','revisionScope':'released-wave contour and orientation only; v29 forward motion, shader and timing unchanged','designDirection':'horizontal irregular crescent, both ends pointed, thick front and fine trailing wake','profileParameters':'crescent-profile.json','waveGroundClearanceMetres':.18,'nativeClipTracksModified':False,'presentationContactHold':'disabled for proposal WAR_05 to preserve continuous native motion sampling','damageRulesModified':False,'travelTailAddsDamage':False,'validation':summaries,'media':media,'taptapDevice':'not verified','files':{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.is_file()}}
 (BASE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(media,ensure_ascii=False))
if __name__=='__main__':
 summaries=verify();movies();gif();detail_gif();stages();proof(summaries)
