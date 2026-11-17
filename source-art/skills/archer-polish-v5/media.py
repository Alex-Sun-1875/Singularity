"""Deterministic typesetting of actual native Cocos captures, with gameplay equality checks."""
import hashlib,json,os,sys
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import av
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
CACHE=HERE.parents[2]/'src/.tmp/archer-polish-v5/final'
MEDIA=HERE/'media'
SHOTS={
 'BASIC_BOW':('普攻','箭尾小幅提亮，保留现有实体箭和射击动作。'),
 'BOW_02_R1':('连穿箭 · 1 级','沿实际转向保留短暂青绿残光，连续命中更容易辨认。'),
 'BOW_02_R3':('连穿箭 · 3 级','同一支箭连续转向，命中处短促闪亮，残迹随即淡出。'),
}
FPS=30
INTEGRATED='--integrated' in sys.argv
CANDIDATE='integrated' if INTEGRATED else 'refined'
def report(v,s):return json.loads((CACHE/v/s/'capture.json').read_text(encoding='utf8'))
@lru_cache(maxsize=12)
def font(n,b=False):return ImageFont.truetype(str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/('msyhbd.ttc' if b else 'msyh.ttc')),n)
def text(d,xy,t,n=22,c='#e8e9dc',b=False,anchor='lm'):d.text(xy,t,font=font(n,b),fill=c,anchor=anchor)
def verify():
 result=[]
 for s in SHOTS:
  a,b=report('current',s),report(CANDIDATE,s)
  if INTEGRATED:
   assert b['integrated'] and b['mainRequests']>0 and b['cleanup']=={'legs':0,'trails':0},s
   assert b['events']==report('refined',s)['events'],(s,'approved preview events')
   for name,digest in b['sourceHashes'].items():
    source=HERE.parents[2]/'src/cocos/assets/scripts/features/combat/runtime'/f'{name}.ts'
    assert digest==hashlib.sha256(source.read_bytes()).hexdigest(),(s,'source changed after capture',name)
   keys=['frames','events']
  else:
   assert b['reviewHash']==hashlib.sha256((HERE/'refine-modules.cjs').read_bytes()).hexdigest(),(s,'stale review capture')
   keys=['gameHash','sourceHashes','frames','events']
  for key in keys:assert a[key]==b[key],(s,key)
  for key in ['origin','targets','geometry','skillGeometry','loadout']:assert a['info'].get(key)==b['info'].get(key),(s,key)
  assert a['presentation']['camera']==b['presentation']['camera'],s
  for data in [a,b]:
   assert not data['errors'] and data['info']['player']['skeletons'],s
   assert len(list((CACHE/data['variant']/s).glob('*.jpg')))==data['frames'],s
   if s.startswith('BOW_02'):assert data['stats']['maxArrows']==1,s
  result.append({'shot':s,'frames':a['frames'],'redirects':sum(e.get('phase')=='redirect' for e in a['events']),'eventsEqual':True,'gameplayUnchanged':True,**({'maxCompletedLegs':b['maxArrowLegs'],'clearPassed':True,'bundleHash':b['gameHash']} if INTEGRATED else {})})
 return result
def template(s,compare):
 w,h=(1920,626) if compare else (960,574)
 out=Image.new('RGB',(w,h),'#171c1b');d=ImageDraw.Draw(out)
 text(d,(24,30),'弓箭手 / '+SHOTS[s][0],29,'#b6d9b5',True)
 text(d,(w-24,30),'当前 3D 场景 · '+('已接入实现' if INTEGRATED else '动态审阅'),18,'#abb5ab',anchor='rm')
 if compare:
  text(d,(24,74),'优化前' if INTEGRATED else '当前实现',21,'#b1bbb2',True)
  text(d,(968,74),'已接入' if INTEGRATED else '本轮微调',21,'#b6d9b5',True)
  d.line((24,560,1896,560),fill='#3c5147')
  text(d,(24,591),SHOTS[s][1],22)
  text(d,(1896,591),'同机位 / 原速',18,'#aab5aa',anchor='rm')
 else:text(d,(18,548),SHOTS[s][1],17)
 return out
def frame(s,i,compare,base):
 out=base.copy()
 for col,v in enumerate(('current',CANDIDATE) if compare else (CANDIDATE,)):
  with Image.open(CACHE/v/s/f'{i:03d}.jpg') as src:
   im=src.convert('RGB').resize((928,454) if compare else (960,470),Image.Resampling.LANCZOS)
   out.paste(im,(24+944*col,96) if compare else (0,57))
 return out
def video(name,compare):
 with av.open(str(MEDIA/name),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
  stream=movie.add_stream('libx264',rate=FPS);stream.width,stream.height=(1920,626) if compare else (960,574)
  stream.pix_fmt='yuv420p';stream.codec_context.thread_count=3;stream.options={'crf':'16','preset':'veryfast'}
  index=0
  for s in SHOTS:
   base=template(s,compare)
   for i in range(report(CANDIDATE,s)['frames']):
    f=av.VideoFrame.from_image(frame(s,i,compare,base));f.pts=index;f.time_base=Fraction(1,FPS)
    for packet in stream.encode(f):movie.mux(packet)
    index+=1
  for packet in stream.encode():movie.mux(packet)
def gif(s):
 base=template(s,True);count=report(CANDIDATE,s)['frames']
 frames=[frame(s,i,True,base).resize((1152,376),Image.Resampling.LANCZOS) for i in range(count)]
 sample=Image.new('RGB',(576,188*3))
 for j,i in enumerate([12,22,31]):sample.paste(frames[i].resize((576,188)),(0,j*188))
 palette=sample.quantize(256,method=Image.Quantize.MEDIANCUT)
 indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
 durations=[(round((i+1)*100/FPS)-round(i*100/FPS))*10 for i in range(count)]
 indexed[0].save(MEDIA/('chain-integrated.gif' if INTEGRATED else 'chain-comparison.gif'),save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=False)
def contact_sheet():
 sheet=Image.new('RGB',(1440,4*390),'#171c1b');d=ImageDraw.Draw(sheet)
 for row,(s,i) in enumerate([('BASIC_BOW',18),('BOW_02_R3',20),('BOW_02_R3',25),('BOW_02_R3',30)]):
  text(d,(16,row*390+20),SHOTS[s][0]+f'  {i/FPS:.2f}s  当前 / 微调',22,'#b6d9b5',True)
  for col,v in enumerate(['current',CANDIDATE]):
   with Image.open(CACHE/v/s/f'{i:03d}.jpg') as src:sheet.paste(src.resize((704,345),Image.Resampling.LANCZOS),(8+720*col,row*390+40))
 sheet.save(MEDIA/('integration-inspection.jpg' if INTEGRATED else 'inspection.jpg'),quality=95,subsampling=0)
def main():
 MEDIA.mkdir(exist_ok=True);checks=verify()
 records={s:{v:report(v,s) for v in ['current',CANDIDATE]} for s in SHOTS}
 (HERE/('integration-captures.json' if INTEGRATED else 'capture-records.json')).write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
 video('current-vs-integrated.mp4' if INTEGRATED else 'current-vs-polished.mp4',True)
 video('integrated-full-size.mp4' if INTEGRATED else 'polished-full-size.mp4',False);gif('BOW_02_R3');contact_sheet()
 outputs={}
 for file in MEDIA.glob('*.mp4'):
  with av.open(str(file)) as c:
   st=c.streams.video[0];frames=sum(1 for _ in c.decode(st));outputs[file.name]={'frames':frames,'fps':str(st.average_rate),'size':[st.width,st.height]}
 for file in MEDIA.iterdir():outputs.setdefault(file.name,{})['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
 (HERE/('integration-verification.json' if INTEGRATED else 'verification.json')).write_text(json.dumps({'checks':checks,'outputs':outputs},ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'checks':checks,'outputs':outputs},ensure_ascii=False))
if __name__=='__main__':main()
