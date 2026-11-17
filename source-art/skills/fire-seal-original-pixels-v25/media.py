"""Export actual normal-range frames; no replacement VFX or camera framing."""
from pathlib import Path
from fractions import Fraction
import json,hashlib
import av
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
CACHE=ROOT/'src/.tmp/fire-seal-original-pixels-v25';MEDIA=HERE/'media'
r=json.loads((HERE/'capture.json').read_text(encoding='utf8'))
FPS=30

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def video(path,frames,size):
 with av.open(str(path),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
  stream=movie.add_stream('libx264',rate=FPS);stream.width,stream.height=size
  stream.pix_fmt='yuv420p';stream.options={'crf':'16','preset':'veryfast'};stream.codec_context.thread_count=3
  for n,im in enumerate(frames):
   f=av.VideoFrame.from_image(im);f.pts=n;f.time_base=Fraction(1,FPS)
   for packet in stream.encode(f):movie.mux(packet)
  for packet in stream.encode():movie.mux(packet)

def verify():
 assert not r['errors'] and not r['consoleErrors']
 assert r['info']['area']=='TRAINING' and r['info']['cameraBound']
 assert r['info']['viewport']==[2560,1272] and r['info']['cameraHeight']==4.3
 assert r['info']['activeSlots']==['FIR_01','FIR_04','FIR_03','FIR_05']
 main=next((ROOT/'src/cocos/build/concept-2d/assets/main').glob('index.*.js'))
 assert sha(main)==r['gameHash']
 assert len(list(CACHE.glob('[0-9][0-9][0-9].jpg')))==240
 jets=[s for m in r['metrics'] for s in m['ground']['active'] if s['kind']=='jets']
 seals=[s for m in r['metrics'] for s in m['ground']['active'] if s['kind']=='smallSeal']
 assert jets and all(s['emitters']==5 and s['vertices']==540 and s['triangles']==800 for s in jets)
 assert seals and all(s['emitters']==5 and s['vertices']==245 for s in seals)
 assert not r['metrics'][-1]['ground']['active']
 assert r['lifecycle']['unchanged'] and not r['lifecycle']['cleared']['active']
 assert r['lifecycle']['pauseRestored']['active']
 one,two=[r['lifecycle'][n]['active'] for n in ['reducedMotionFirst','reducedMotionSecond']]
 assert next(s['frames'] for s in one if s['kind']=='jets')!=next(s['frames'] for s in two if s['kind']=='jets')
 clocks=[m['flowTime'][0] for m in r['metrics'] if m['flowTime']]
 assert all(b>a for a,b in zip(clocks,clocks[1:]))
 textures={};dest=ROOT/'src/cocos/assets/resources/vfx/production';build=ROOT/'src/cocos/build/concept-2d/assets'
 for name in ['fire-ground-jets-v24','fire-jet-seal-v25','fire-flow-noise-v24']:
  source=dest/(name+'.png');uid=json.loads((dest/(name+'.png.meta')).read_text(encoding='utf8'))['uuid']
  expected=Image.open(source).convert('RGBA').tobytes()
  files=list(build.glob(f'*/native/{uid[:2]}/{uid}.*.png'))
  assert any(Image.open(p).convert('RGBA').tobytes()==expected for p in files),name
  textures[name]=sha(source)
 return {'gameHash':r['gameHash'],'frames':240,'seconds':8,'normalRangeHUDAndCamera':True,'fiveEmitters':True,'curvedFrontAndBackSurfaces':True,'flameDetailAndFloorFlowUseGameTime':True,'pauseRestored':True,'reducedMotionStillAnimates':True,'clearedAtEnd':True,'hits':r['metrics'][-1]['hits'],'damage':r['metrics'][-1]['damage'],'runtimeErrors':r['errors'],'consoleErrors':r['consoleErrors'],'textures':textures,'sourceHashes':{name:sha(ROOT/name) for name in ['src/cocos/assets/scripts/features/combat/runtime/FireGroundEffects.ts','src/cocos/assets/resources/vfx/production/fire-ground-v24.effect']},'artAcceptance':'Native normal-range frames visually inspected; user acceptance pending','taptapDeviceValidation':'pending','gameplayChanges':'none in v25'}

def label(d,xy,value,size=23,color='#efbb7f'):
 d.text(xy,value,font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size),fill=color)

def main():
 checks=verify();MEDIA.mkdir(exist_ok=True)
 # The reference and actual camera keep their own perspective. Match only the
 # outer-ring width for a readable comparison; never warp the recorded frame.
 ref=Image.open(HERE/'assets/selected-original-seal.png').convert('RGB')
 native=Image.open(CACHE/'036.jpg').crop((455,1080,655,1201)).convert('RGB')
 comparison=Image.new('RGB',(1200,450),'#242a27');d=ImageDraw.Draw(comparison)
 label(d,(24,18),'法阵 / 选定原图与实际游戏',27)
 for x,title,im in [(24,'你选定的设计稿',ref),(632,'当前游戏中的法阵',native)]:
  label(d,(x,66),title)
  im=im.resize((544,round(im.height*544/im.width)),Image.Resampling.LANCZOS)
  comparison.paste(im,(x,114))
 label(d,(24,418),'只按外圈宽度对齐；原图与实录保留各自透视。',18,color='#d8cdbb')
 comparison.save(MEDIA/'reference-vs-native-seal.jpg',quality=96,subsampling=0)
 video(MEDIA/'normal-training-fire-jets.mp4',(Image.open(CACHE/f'{i:03}.jpg').convert('RGB') for i in range(240)),(2560,1272))
 Image.open(CACHE/'036.jpg').save(MEDIA/'normal-training-fire-jets.jpg',quality=95,subsampling=0)
 out=Image.new('RGB',(1536,870),'#1d1916');d=ImageDraw.Draw(out)
 for n,(i,title) in enumerate([(36,'持续上涌'),(55,'火舌翻卷'),(147,'结束后退火'),(168,'余焰淡出')]):
  x=n%2*768;y=n//2*435
  label(d,(x+18,y+10),f'{i/30:.2f}s  {title}')
  out.paste(Image.open(CACHE/f'{i:03}.jpg').resize((768,382),Image.Resampling.LANCZOS),(x,y+48))
 out.save(MEDIA/'normal-training-stages.jpg',quality=95,subsampling=0)
 # Clearly marked crop of the real frames, for viewing the movement at chat size.
 frames=[]
 for i in range(26,185,2):
  im=Image.open(CACHE/f'{i:03}.jpg').crop((420,460,1220,1210)).resize((640,600),Image.Resampling.LANCZOS)
  frames.append(im)
 frames[0].save(MEDIA/'fire-flow-detail.webp',save_all=True,append_images=frames[1:],duration=67,loop=0,quality=82,method=4)
 with av.open(str(MEDIA/'normal-training-fire-jets.mp4')) as clip:
  decoded=sum(1 for _ in clip.decode(video=0));assert decoded==240
 checks['media']={'videoFrames':decoded,'videoSize':[2560,1272],'frameAlteration':'none; video encodes native canvas JPEGs only','detailPreview':'crop and resize of same real frames'}
 (HERE/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(checks,ensure_ascii=False))

if __name__=='__main__':main()
