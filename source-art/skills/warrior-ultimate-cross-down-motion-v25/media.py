"""Package actual Cocos proposal captures; no generated or interpolated animation frames."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import json, hashlib
import av
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-ultimate-cross-down-v25'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
SCENES={'training':'当前靶场','field':'游戏地面'}
@lru_cache(maxsize=12)
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if bold else 'msyh.ttc'),size)
def label(d,xy,s,size=23,fill='#dce5ec',bold=False):d.text(xy,s,font=font(size,bold),fill=fill)
def report(scene,variant='proposal'):return json.loads((CACHE/scene/variant/'capture.json').read_text(encoding='utf8'))
def frame(scene,index,slow=False):
 im=Image.new('RGB',(1280,710),'#171d22');d=ImageDraw.Draw(im)
 label(d,(18,9),'破晓裁决 · 交叉斩结合下劈',27,bold=True)
 label(d,(910,14),SCENES[scene]+' / '+('0.5× 慢放' if slow else '原速'),20,fill='#acbbc7')
 with Image.open(CACHE/scene/'proposal'/f'{index:03d}.jpg') as shot:im.paste(shot.convert('RGB'),(0,48))
 label(d,(18,680),'当前游戏角色、动作与材质 · 独立动态小样，尚未接入',20)
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
 write_video('ultimate-slow.mp4',[frame('training',i,True) for i in range(15,70)],15)
 compare=[]
 for i in range(report('training')['frames']):
  im=Image.new('RGB',(1600,478),'#171d22');d=ImageDraw.Draw(im)
  label(d,(18,9),'当前游戏效果',24,bold=True);label(d,(818,9),'动态方案 · 交叉＋下劈',24,bold=True)
  for x,variant in [(0,'current'),(800,'proposal')]:
   with Image.open(CACHE/'training'/variant/f'{i:03d}.jpg') as shot:im.paste(shot.convert('RGB').resize((800,390),Image.Resampling.LANCZOS),(x,46))
  label(d,(18,446),'相同角色、动作、机位与时间 / 原速',20)
  label(d,(818,446),'隔离预览 / 未替换正式游戏效果',20)
  compare.append(im)
 write_video('current-vs-proposal.mp4',compare)
def gif():
 pictures=[frame('training',i).resize((960,532),Image.Resampling.LANCZOS) for i in range(90)]
 sample=Image.new('RGB',(480,798))
 for row,i in enumerate([27,37,42]):sample.paste(pictures[i].resize((480,266)),(0,row*266))
 palette=sample.quantize(256,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 indexed[0].save(OUT/'ultimate-motion-study.gif',save_all=True,append_images=indexed[1:],duration=[(round((i+1)*100/30)-round(i*100/30))*10 for i in range(90)],loop=0,optimize=True,disposal=1)
def stages():
 im=Image.new('RGB',(1800,792),'#171d22');d=ImageDraw.Draw(im)
 label(d,(18,10),'当前角色连续动作 · 交叉与下劈在终结段同框',30,bold=True)
 for i,(index,name) in enumerate([(24,'横扫'),(30,'上挑'),(35,'交叉展开'),(38,'下劈压入'),(41,'组合爆发'),(47,'余波散开')]):
  x=i%3*600;y=62+i//3*356
  with Image.open(CACHE/'training'/'proposal'/f'{index:03d}.jpg') as shot:im.paste(shot.convert('RGB').resize((596,291),Image.Resampling.LANCZOS),(x+2,y))
  label(d,(x+16,y+302),f'{name}  {(index+1)/30:.2f}s',23,bold=True)
 im.save(OUT/'motion-stages.jpg',quality=95,subsampling=0)
 frame('training',40).save(OUT/'combined-peak.jpg',quality=95,subsampling=0)
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
  drops=[m for m in b['metrics'] if m.get('downAxes')]
  assert drops and all(abs(abs(a)-90)<.03 for m in drops for a in m['downAxes'])
  positions=[m['phase']['position'] for m in drops]
  assert max(p[0] for p in positions)-min(p[0] for p in positions)<1e-6
  assert max(p[2] for p in positions)-min(p[2] for p in positions)<1e-6
  assert positions[0][1]-positions[-1][1]>1.0
  active=[m for m in b['metrics'] if m['action']]
  assert all(m['pose']['state']!='idle' for m in active),'Action returns to idle mid-chain'
  assert {'attack_sword','attack_sword_2','attack_sword_3'}<=set(b['clips'])
  summaries[scene]={'gameHash':b['gameHash'],'frames':b['frames'],'nativeClips':b['clips'],'sameBeforeAfterHits':True,'skillHits':len([e for e in b['events'] if e['type']=='skill_hit']),'simultaneousCrossDownFrames':len(both),'crossAngleDegrees':120,'thirdAxisDegrees':90,'thirdHorizontalTravel':0,'maxLayers':max(len(m['warrior']['active']) for m in b['metrics']),'noMidActionIdle':True}
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
 data={'status':'isolated runtime motion proposal; not integrated; user art acceptance pending','productionIntegration':False,'generatedFrames':False,'basis':'Current compiled game, real native actor/three clips/pressure shader/meshes and session clock; ultimateWave and WAR_05 presentation contact-hold patched only inside disposable browser context.','nativeClipTracksModified':False,'presentationContactHold':'disabled for proposal WAR_05 to preserve continuous native motion sampling','damageRulesModified':False,'validation':summaries,'media':media,'taptapDevice':'not verified','files':{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.is_file()}}
 (BASE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(media,ensure_ascii=False))
if __name__=='__main__':
 summaries=verify();movies();gif();stages();proof(summaries)
