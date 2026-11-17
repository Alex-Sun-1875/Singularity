"""Compose native Cocos design captures without changing their playback timing."""
import argparse
import hashlib
import json
import os
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import av
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
CACHE=HERE.parents[2]/'src/.tmp/warrior-cross-v5/final'
MEDIA=HERE/'media'
FPS=30
SHOTS={
 'BASIC_WAR':('普攻三连','横扫起手 / 纵劈交错','横向刀光先展开，纵向刀锋稍后切入，命中时短暂共存。'),
 'WAR_01':('断空斩','近身交叉连斩','两次挥剑保留各自节奏，前一道残影与后一道刀面衔接。'),
 'WAR_02':('破军突袭','突进十字斩','突进结束后，横刃掠过胸线，纵刃斜向下切入交汇处。'),
 'WAR_04':('裂地审判','落刃 / 横向冲击','纵刃落向真实落点，触地时展开一条短促的横向冲击。'),
 'WAR_05':('破晓裁决','三段交错 / 重劈收尾','三段刀光前后衔接，末段突出纵向重劈与横向余刃。'),
}
INK='#dfc18b'

@lru_cache(maxsize=12)
def font(size,bold=False):
 return ImageFont.truetype(str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/('msyhbd.ttc' if bold else 'msyh.ttc')),size)

def label(draw,xy,text,size=22,fill='#ebe6d9',bold=False,anchor='lm'):
 draw.text(xy,text,font=font(size,bold),fill=fill,anchor=anchor)

def report(variant,shot):
 return json.loads((CACHE/variant/shot/'capture.json').read_text(encoding='utf8'))

def verify():
 for shot in SHOTS:
  previous,design=[report(variant,shot) for variant in ('previous','design')]
  for key in ['gameHash','frames','events']:
   assert previous[key]==design[key],(shot,key)
  for key in ['origin','targets','geometry','skillGeometry']:
   assert previous['info'].get(key)==design['info'].get(key),(shot,key)
  assert previous['presentation']['camera']==design['presentation']['camera'],shot
  assert len(design['overlapFrames'])>=2,(shot,'No simultaneous cutting planes')
  for data in [previous,design]:
   assert not data['errors'] and data['info']['player']['skeletons'],shot
   assert len(list((CACHE/data['variant']/shot).glob('[0-9][0-9][0-9].jpg')))==data['frames'],shot

def template(shot,compare):
 name,change,hint=SHOTS[shot]
 width,height=(1920,626) if compare else (960,574)
 out=Image.new('RGB',(width,height),'#171c1e')
 d=ImageDraw.Draw(out)
 label(d,(24,30),'战士 / '+name,29,INK,True)
 label(d,(width-24,31),'纵横交错 · 动态设计稿',19,'#b7b8ad',anchor='rm')
 if compare:
  label(d,(24,73),'上一稿',21,'#b7b8ad',True)
  label(d,(968,73),'本轮设计',21,INK,True)
  label(d,(1100,73),change,19)
  d.line((24,559,1896,559),fill='#4b4e45')
  label(d,(24,591),hint,22)
  label(d,(1896,590),'同机位 / 原速 / 30 fps',17,'#b7b8ad',anchor='rm')
 else:
  label(d,(18,548),hint,17)
 return out

def frame(shot,index,compare,base):
 out=base.copy()
 variants=('previous','design') if compare else ('design',)
 for col,variant in enumerate(variants):
  with Image.open(CACHE/variant/shot/f'{index:03d}.jpg') as source:
   size=(928,454) if compare else (960,470)
   out.paste(source.convert('RGB').resize(size,Image.Resampling.LANCZOS),(24+944*col,96) if compare else (0,57))
 return out

def video(filename,compare):
 chapters=[];start=0
 for shot in SHOTS:
  count=report('design',shot)['frames']
  chapters.append({'id':len(chapters),'time_base':Fraction(1,FPS),'start':start,'end':start+count,'metadata':{'title':SHOTS[shot][0]}})
  start+=count
 with av.open(str(MEDIA/filename),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
  movie.set_chapters(chapters)
  stream=movie.add_stream('libx264',rate=FPS)
  stream.width,stream.height=(1920,626) if compare else (960,574)
  stream.pix_fmt='yuv420p';stream.codec_context.thread_count=3;stream.options={'crf':'16','preset':'veryfast'}
  index=0
  for shot in SHOTS:
   base=template(shot,compare)
   for local in range(report('design',shot)['frames']):
    sample=av.VideoFrame.from_image(frame(shot,local,compare,base));sample.pts=index;sample.time_base=Fraction(1,FPS)
    for packet in stream.encode(sample):movie.mux(packet)
    index+=1
  for packet in stream.encode():movie.mux(packet)

def gif(shot,filename,poster):
 count=report('design',shot)['frames']
 base=template(shot,False)
 frames=[frame(shot,i,False,base).resize((768,459),Image.Resampling.LANCZOS) for i in range(count)]
 durations=[(round((i+1)*100/FPS)-round(i*100/FPS))*10 for i in range(count)]
 frames=frames[poster:]+frames[:poster];durations=durations[poster:]+durations[:poster]
 sample=Image.new('RGB',(384,230*3))
 for j,i in enumerate([0,min(9,count-1),count//2]):sample.paste(frames[i].resize((384,230)),(0,j*230))
 palette=sample.quantize(256,method=Image.Quantize.MEDIANCUT)
 indexed=[image.quantize(palette=palette,dither=Image.Dither.NONE) for image in frames]
 indexed[0].save(MEDIA/filename,save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=False)

def stills():
 # Representative frames are selected after viewing native engine captures.
 selections={'BASIC_WAR':14,'WAR_01':15,'WAR_02':20,'WAR_04':23,'WAR_05':36}
 plate=Image.new('RGB',(1440,1158),'#171c1e')
 d=ImageDraw.Draw(plate)
 label(d,(24,30),'战士 · 纵横交错',30,INK,True)
 label(d,(1416,30),'原生 3D 动态截帧 · 设计待审',18,'#b7b8ad',anchor='rm')
 for cell,shot in enumerate(['BASIC_WAR','WAR_02','WAR_04','WAR_05']):
  col,row=cell%2,cell//2
  index=selections[shot]
  image=frame(shot,index,False,template(shot,False)).resize((704,421),Image.Resampling.LANCZOS)
  plate.paste(image,(8+col*720,60+row*474))
  label(d,(24+col*720,502+row*474),SHOTS[shot][1],22,INK,True)
  frame(shot,index,True,template(shot,True)).save(MEDIA/(shot.lower()+'-comparison.jpg'),quality=94,subsampling=0)
 plate.crop((0,0,1440,1036)).save(MEDIA/'crossed-cuts-overview.jpg',quality=94,subsampling=0)

def provenance():
 data={'source':'Existing Cocos scene, native skeletons, actual combat events and current steel assets','fps':30,
  'gameHash':report('previous','BASIC_WAR')['gameHash'],'comparison':'Prior v4 blade-depth review versus crossed-cut design; same frozen current export',
  'reviewStatus':'Rejected by user on 2026-11-16. Completely redesign; do not reuse this effect.',
  'deliveryState':'Design preview overrides are served only inside the local recorder',
  'validation':'Exact gameplay event, target, geometry and camera match for every comparison. At least two frames with both cutting planes for every design shot.',
  'platformValidation':'Local HTML review only. TapTap device performance remains unverified.',
  'artInputs':'Existing production steel atlas and Cocos surfaces; no new generated imagery.',
  'meteorSealRule':'No warrior decorative seal. Ornate landing seal reserved for FIR_02.',
  'shots':[]}
 source_root=CACHE.parent/'sources'
 data['sourceSnapshotHashes']={str(p.relative_to(source_root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_root.rglob('*.ts')}
 for shot in SHOTS:
  sample=report('design',shot)
  data['shots'].append({'skill':shot,'name':SHOTS[shot][0],'frames':sample['frames'],'seconds':sample['frames']/FPS,'graphicsRequested':sample.get('graphics','ANGLE SwiftShader'),
   'overlapFrames':sample['overlapFrames'],'stats':sample['stats'],'clips':sample['clips'],
   'events':sample['events'],'reviewInputs':sample['reviewInputs']})
 data['files']={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.rglob('*') if p.is_file() and p.name!='provenance.json'}
 (HERE/'provenance.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['compare','single','previews','verify']);args=parser.parse_args()
 MEDIA.mkdir(exist_ok=True)
 verify()
 if args.mode=='compare':video('warrior-cross-comparison.mp4',True)
 elif args.mode=='single':video('warrior-cross-motion.mp4',False)
 elif args.mode=='previews':
  gif('BASIC_WAR','warrior-combo.gif',14)
  gif('WAR_02','warrior-cross.gif',20)
  gif('WAR_05','warrior-ultimate.gif',36)
  stills()
 else:provenance()
