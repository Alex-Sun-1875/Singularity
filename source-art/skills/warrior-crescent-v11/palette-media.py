"""Render and verify four colour treatments of the exact same native crescent frames."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,os
import av,numpy as np
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
CACHE=ROOT/'src/.tmp/warrior-crescent-v11/colour-study'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
PALETTES={
 'A':{'name':'雾银蓝','front':[.91,.97,1],'body':[.40,.62,.77]},
 'B':{'name':'浅香槟金','front':[1,.96,.87],'body':[.77,.63,.42]},
 'C':{'name':'淡青玉','front':[.91,1,.97],'body':[.40,.70,.65]},
 'D':{'name':'浅银紫','front':[.97,.93,1],'body':[.66,.55,.80]},
}
FONT=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'

def text(d,xy,s,size=24,fill='#e2e8ed',bold=False,anchor='lm'):
 f=ImageFont.truetype(str(FONT/('msyhbd.ttc' if bold else 'msyh.ttc')),size)
 d.text(xy,s,font=f,fill=fill,anchor=anchor)

report=json.loads((CACHE/'final/design/WAR_01/capture.json').read_text(encoding='utf8'))
baseline=json.loads((ROOT/'src/.tmp/warrior-crescent-v11/final/design/WAR_01/capture.json').read_text(encoding='utf8'))
assert not report['errors'] and report['info']['player']['skeletons']
assert report['events']==baseline['events'] and report['presentation']['camera']==baseline['presentation']['camera']
assert report['style']['opacityScale']==.55
assert all(abs(angle-24)<.02 for sample in report['crossGeometrySamples'] for angle in sample['acuteAnglesDegrees'])
count=report['frames'];assert count==72
for key in PALETTES:
 assert len(list((CACHE/'palettes'/key/'WAR_01').glob('[0-9][0-9][0-9].jpg')))==count,key

checks=[]
for index in [16,18,22]:
 arrays={k:np.asarray(Image.open(CACHE/'palettes'/k/'WAR_01'/f'{index:03d}.jpg').convert('RGB')) for k in PALETTES}
 for key in ['B','C','D']:
  assert np.array_equal(arrays['A'][:,:210],arrays[key][:,:210]),'Scenery or pose changed outside effect'
  assert np.any(arrays['A'][:,400:710]!=arrays[key][:,400:710]),'Colour did not change'
 checks.append({'frame':index,'farSceneryIdentical':True,'allPalettesDifferentInEffectRegion':True})

def frame(index,slow=False):
 out=Image.new('RGB',(1440,1408),'#171d22');d=ImageDraw.Draw(out)
 text(d,(22,29),'月牙剑气 · 四组淡色候选',31,bold=True)
 text(d,(1418,29),'0.5× 动态对照' if slow else '原速 / 30 fps',20,'#aebfca',anchor='rm')
 for cell,(key,data) in enumerate(PALETTES.items()):
  x=(cell%2)*720;y=70+(cell//2)*650
  colour=tuple(round(v*255) for v in data['front'])
  text(d,(x+20,y+20),key+' · '+data['name'],27,colour,True)
  with Image.open(CACHE/'palettes'/key/'WAR_01'/f'{index:03d}.jpg') as im:
   out.paste(im.convert('RGB').crop((350,0,740,325)).resize((704,587),Image.Resampling.LANCZOS),(x+8,y+46))
 text(d,(22,1385),'相同动作、月牙形状与透明度，仅比较配色。',22)
 return out

frame(18).save(OUT/'colour-options.jpg',quality=96,subsampling=0)
with av.open(str(OUT/'colour-options.mp4'),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
 stream=movie.add_stream('libx264',rate=30);stream.width,stream.height=1080,1056;stream.pix_fmt='yuv420p';stream.options={'crf':'17','preset':'veryfast'};stream.codec_context.thread_count=3
 for index in range(count):
  sample=av.VideoFrame.from_image(frame(index).resize((1080,1056),Image.Resampling.LANCZOS));sample.pts=index;sample.time_base=Fraction(1,30)
  for packet in stream.encode(sample):movie.mux(packet)
 for packet in stream.encode():movie.mux(packet)

frames=[frame(index,True).resize((1008,986),Image.Resampling.LANCZOS) for index in range(count)]
durations=[(round((i+1)*100/15)-round(i*100/15))*10 for i in range(count)]
frames=frames[18:]+frames[:18];durations=durations[18:]+durations[:18]
sampler=Image.new('RGB',(504,493*3))
for row,index in enumerate([0,24,48]):sampler.paste(frames[index].resize((504,493)),(0,row*493))
palette=sampler.quantize(255,method=Image.Quantize.MEDIANCUT)
indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
indexed[0].save(OUT/'colour-options.gif',save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=True,transparency=255,disposal=1)
im=Image.open(OUT/'colour-options.gif');milliseconds=0
for i in range(im.n_frames):im.seek(i);im.load();milliseconds+=im.info.get('duration',0)
assert milliseconds==4800
with av.open(str(OUT/'colour-options.mp4')) as movie:
 s=movie.streams.video[0];assert s.average_rate==30 and sum(1 for _ in movie.decode(s))==72
data={'palettes':PALETTES,'method':'For each native simulation frame, replace only the per-vertex colour ramp and render with dt=0. Geometry, alpha, transforms, animation pose and gameplay time are unchanged.',
 'opacity':.55,'targetScreenCrossAngle':24,'sameNativeSkillEvents':True,'sameCamera':True,'fixedSceneryChecks':checks,
 'gif':{'frames':im.n_frames,'milliseconds':milliseconds,'playback':'.5x'},'video':{'frames':72,'fps':30,'seconds':2.4},
 'captureInputs':report['reviewInputs'],'artAcceptance':'Colour selection pending user review','productionIntegration':False}
data['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('colour-options.*')}
(BASE/'colour-verification.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'palettes':4,'gifFrames':im.n_frames,'milliseconds':milliseconds}))
