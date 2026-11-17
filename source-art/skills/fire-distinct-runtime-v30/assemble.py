"""Assemble approved native segments from their recorded builds, without VFX edits."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, shutil
import av
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('native_fire_media',HERE/'media.py')
media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def relative(path):return path.relative_to(ROOT).as_posix()

def load(folder):
 report=json.loads((folder/'capture.json').read_text(encoding='utf8'))
 shots={s['id']:json.loads((folder/(s['id']+'.json')).read_text(encoding='utf8')) for s in report['shots']}
 cache=ROOT/report['cache'];media.validate(report,list(shots.values()),cache)
 return {'folder':folder,'report':report,'shots':shots,'cache':cache}

def main():
 p=argparse.ArgumentParser();p.add_argument('--base-stage',default='final');p.add_argument('--meteor-stage',default='meteor-final');p.add_argument('--rank',type=int,default=1)
 args=p.parse_args();delivery=HERE/'delivery';delivery.mkdir(exist_ok=True)
 sources={}
 for empty in [False,True]:
  suffix=('-empty' if empty else '')+f'-r{args.rank}'
  sources[('base',empty)]=load(HERE/(args.base_stage+suffix))
  sources[('meteor',empty)]=load(HERE/(args.meteor_stage+suffix))
 reels={};all_hashes=set()
 for empty in [False,True]:
  choices=[('FIR_01',sources[('base',empty)]),('FIR_05',sources[('base',empty)]),('FIR_02',sources[('meteor',empty)])]
  name='fire-three-skills-empty.mp4' if empty else 'fire-three-skills-native.mp4'
  segments=[];offset=0
  for skill,source in choices:
   shot=source['shots'][skill];native=source['folder']/'media'/(skill+'.mp4');assert native.exists(),native
   digest=source['report']['gameHash'];all_hashes.add(digest)
   segments.append({'skillId':skill,'name':media.NAMES[skill],'timelineStartFrame':offset,'frames':shot['frames'],
                    'seconds':shot['frames']/media.FPS,'compiledSha256':digest,
                    'capture':relative(source['folder']/'capture.json'),'eventsAndMetrics':relative(source['folder']/(skill+'.json')),
                    'nativeMp4':relative(native),'nativeMp4Sha256':sha(native),'sourceCache':relative(source['cache']/skill),
                    'actualResults':media.summary(shot)})
   offset+=shot['frames']
  def frames():
   for skill,source in choices:
    shot=source['shots'][skill]
    for i in range(shot['frames']):
     raw=Image.open(source['cache']/skill/f'{i:03}.jpg').convert('RGB')
     if empty:raw=raw.crop((0,330,1500,1272))
     canvas=Image.new('RGB',(1280,868 if empty else 700),'#1d1916');draw=ImageDraw.Draw(canvas)
     media.label(draw,(20,16),media.NAMES[skill]+'  |  '+('实景录制局部 · 原镜头' if empty else '真实命中 · 完整画布与 HUD'),25)
     canvas.paste(raw.resize((1280,804 if empty else 636),Image.Resampling.LANCZOS),(0,64));yield canvas
  media.video(delivery/name,frames(),(1280,868 if empty else 700))
  with av.open(str(delivery/name)) as movie:decoded=sum(1 for _ in movie.decode(video=0))
  assert decoded==offset
  reels['empty' if empty else 'native']={'file':name,'sha256':sha(delivery/name),'frames':decoded,'seconds':decoded/media.FPS,
                                       'processing':'Actual canvas crop, resize, title only' if empty else 'Complete actual canvas resized; title outside canvas',
                                       'retimed':False,'segments':segments}
  print('Encoded',name,decoded,'native frames',flush=True)
 # Keep clear stills alongside the two main movies. These are existing native
 # frame crops/stage layouts, never generated replacement effects.
 stills=[(HERE/'final4-single-r1/media/FIR_01-contact-detail.jpg','FIR_01-contact-detail.jpg'),
         (sources[('base',True)]['folder']/'media/FIR_05-stages.jpg','FIR_05-stages.jpg'),
         (sources[('meteor',True)]['folder']/'media/FIR_02-stages.jpg','FIR_02-stages.jpg')]
 for source,name in stills:shutil.copy2(source,delivery/name)
 textures={};production=ROOT/'src/cocos/assets/resources/vfx/production'
 for name in ['fire-lance-v30','fire-contact-fan-v30','fire-field-flow-v30','fire-meteor-seal-v30','fire-ground-jets-v27','fire-jet-seal-v27','fire-flow-noise-v24']:
  asset=production/(name+'.png');textures[name]={'source':relative(asset),'sha256':sha(asset)}
 manifest={'type':'native-recorded-media-assembly','rank':args.rank,'fps':media.FPS,'reels':reels,
           'compiledBuilds':sorted(all_hashes),'allSegmentsSameCompiledBuild':len(all_hashes)==1,
           'buildNote':'FIR01/FIR05 reuse approved final4 footage; only FIR02 was re-recorded after the final5 presentation change. Each segment retains its own compiled hash.',
           'coreGameplayEvidence':relative(sources[('base',False)]['folder']/'verification.json'),
           'newMeteorEvidence':relative(sources[('meteor',False)]['folder']/'verification.json'),
           'rngNote':'The replacement meteor is a fresh isolated cast; its RNG sequence differs from the third cast of the full baseline. Actual hit results are recorded, without changing the seed.',
           'sourceSnapshots':{relative(s['folder']):s['report']['sourceHashes'] for s in sources.values()},
           'currentFinal5PngSourceSnapshot':textures,'sourceSnapshot':relative(HERE/'source-snapshot-final.json'),
           'stills':[name for _,name in stills],'postAddedEffects':False,'timingAlteration':False,
           'localVisualReview':'Historical v30 review superseded: user rejected the meteor blast density, volume and brightness. This is not a passed meteor art baseline.',
           'taptapDeviceValidation':'Pending; these are actual browser Cocos training-range captures.'}
 (delivery/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (delivery/'README.md').write_text('''# 火系技能实际动画

- `fire-three-skills-native.mp4`：三招真实命中，完整画布与HUD。
- `fire-three-skills-empty.mp4`：同默认镜头空地轮廓，片内标明“实景录制局部 · 原镜头”。
- 所有片段保留完整施法与退火，30fps原时序；只裁切、缩放、排标题，没有后期添加特效。
- FIR01/FIR05来自已通过本地审看的final4，FIR02来自仅调整陨石呈现的final5；逐段编译hash、原生完整MP4、事件、伤害和帧来源见manifest.json。合集并非全片来自同一个build。
- 完整五招回归已核对实际伤害/命中/冷却、暂停恢复、低动态与职业切换清理；补录陨石使用独立真实施放，随机序列与原第三招不同，不将命中数差异当作玩法规则变化。
- 当前为浏览器实景与本地美术审看；用户对实装美术的反馈、TapTap平台与真机验收仍待确认。
''',encoding='utf8')
 print(json.dumps({'delivery':relative(delivery),'compiledBuilds':sorted(all_hashes),'secondsPerReel':reels['native']['seconds'],'manifest':'manifest.json'},ensure_ascii=False))

if __name__=='__main__':main()
