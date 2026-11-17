"""Package the representative native 3D study at original timing."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,os
import av
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
CACHE=HERE.parents[2]/'src/.tmp/warrior-impact-v6/final/design/WAR_01'
OUT=HERE/'media';OUT.mkdir(exist_ok=True)
data=json.loads((CACHE/'capture.json').read_text(encoding='utf8'))
assert not data['errors'] and data['info']['player']['skeletons']
assert data['stats']['maxBlades']>=3 and len(data['overlapFrames'])>=2
count=data['frames'];assert count==72
for i in range(count):assert (CACHE/f'{i:03d}.jpg').exists()

def font(size,bold=False):return ImageFont.truetype(str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/('msyhbd.ttc' if bold else 'msyh.ttc')),size)
def frame(i):
 out=Image.new('RGB',(960,574),'#171b1d');d=ImageDraw.Draw(out)
 d.text((20,12),'战士 · 新刀锋造型',font=font(27,True),fill='#e5c48b')
 d.text((940,26),'断空斩 / 动态小样',font=font(18),fill='#c5c1b5',anchor='rm')
 with Image.open(CACHE/f'{i:03d}.jpg') as im:out.paste(im.convert('RGB'),(0,57))
 d.text((20,543),'横斩切入 → 纵劈交汇 → 碎锋消散',font=font(18),fill='#ded8c8')
 d.text((940,549),'原速 / 30 fps',font=font(16),fill='#a8aa9f',anchor='rm')
 return out

movie=OUT/'warrior-new-motion.mp4'
with av.open(str(movie),'w',format='mp4',options={'movflags':'+faststart'}) as c:
 stream=c.add_stream('libx264',rate=30);stream.width,stream.height=960,574;stream.pix_fmt='yuv420p';stream.options={'crf':'16','preset':'veryfast'}
 for i in range(count):
  f=av.VideoFrame.from_image(frame(i));f.pts=i;f.time_base=Fraction(1,30)
  for p in stream.encode(f):c.mux(p)
 for p in stream.encode():c.mux(p)

frames=[frame(i).resize((768,459),Image.Resampling.LANCZOS) for i in range(count)]
durations=[(round((i+1)*100/30)-round(i*100/30))*10 for i in range(count)]
poster=22;frames=frames[poster:]+frames[:poster];durations=durations[poster:]+durations[:poster]
palette=frames[0].quantize(256,method=Image.Quantize.MEDIANCUT)
indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
indexed[0].save(OUT/'warrior-new-motion.gif',save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=False)

plate=Image.new('RGB',(1440,880),'#171b1d');d=ImageDraw.Draw(plate)
d.text((22,15),'战士 · 新造型动作分解',font=font(32,True),fill='#e5c48b')
for cell,(index,title) in enumerate([(14,'01  横斩起势'),(17,'02  刀锋前伸'),(22,'03  纵横交汇'),(27,'04  碎锋消散')]):
 x=(cell%2)*720;y=65+(cell//2)*400
 with Image.open(CACHE/f'{index:03d}.jpg') as im:plate.paste(im.convert('RGB').resize((704,345),Image.Resampling.LANCZOS),(x+8,y))
 d.text((x+22,y+357),title,font=font(23,True),fill='#d6b87f')
plate.save(OUT/'warrior-new-stages.jpg',quality=94,subsampling=0)
frame(poster).save(OUT/'warrior-new-peak.jpg',quality=95,subsampling=0)

with av.open(str(movie)) as c:
 stream=c.streams.video[0];decoded=sum(1 for _ in c.decode(stream));assert decoded==count and stream.average_rate==30
im=Image.open(OUT/'warrior-new-motion.gif');duration=0
for i in range(im.n_frames):im.seek(i);im.load();duration+=im.info.get('duration',0)
assert duration==2400
record={'status':'New design candidate, awaiting user art review','priorDirection':'warrior-cross-v5 rejected; none of its steel textures or sector surfaces are used',
 'imageGeneration':'Cloud OpenAI image_gen, built-in tool','imageSource':['keyframe.png','atlas-original.png'],'videoGenerationAttempt':'Maker video tool unavailable because current Cocos workspace is not a bound Maker project. No remote video task dispatched.',
 'animation':'Native Cocos 3D character actions and actual skill events, independent design renderer served only by recorder',
 'skill':'WAR_01','fps':30,'frames':count,'seconds':count/30,'decodedFrames':decoded,'gifMilliseconds':duration,'overlapFrames':data['overlapFrames'],
 'gameHash':data['gameHash'],'graphicsRequested':data.get('graphics'),'events':data['events'],'clips':data['clips'],'reviewInputs':data['reviewInputs'],
 'implementationState':'Design preview only; no production game integration','limitations':'Concept keyframe is a visual target; native preview remains a candidate. TapTap device performance not assessed.'}
record['files']={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.rglob('*') if p.is_file() and p.name!='provenance.json'}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'frames':decoded,'fps':30,'seconds':count/30,'overlapFrames':len(data['overlapFrames']),'output':str(movie)},ensure_ascii=False))
