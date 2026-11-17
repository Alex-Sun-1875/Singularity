"""Typeset matched frames rendered by the current Cocos implementation and its review variant."""
import argparse
import hashlib
import json
import os
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import av
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
CACHE=HERE.parents[2]/'src/.tmp/current-vfx-refinement-v4/final'
MEDIA=HERE/'media'
FPS=30
SHOTS={
 'BASIC_WAR':('战士','普攻三连','刀面纵深','沿用现有扇刃网格，刀面向挥砍中心加深，侧弧收窄。'),
 'THU_01':('雷系','贯雷长矛','连续主弧','聚能集中在手部，出手主电弧连到当前命中点。'),
 'THU_02':('雷系','连锁雷弧','主次分明','一条主弧接入目标，后续沿现有连锁路径放电。'),
 'THU_05':('雷系','万钧雷潮','电网骨架','降低铺地碎弧亮度，让目标之间的主链更清楚。'),
 'FIR_01':('火系','赤焰枪','火核纵深','恢复现有图格的纵向比例，火核与尾焰共同随弹道前进。'),
 'FIR_02':('火系','焚星坠落','爆燃前后分层','拉开现有主焰团与前排焰团的距离，扩大前后衔接，柔化落点边缘。'),
 'FIR_05':('火系','焚天火海','火浪衔接','相邻焰片增加重叠、缩小播放相位差，沿现有条带范围形成连贯火浪。'),
}
PALETTE={'战士':'#dfc18b','雷系':'#b4bcff','火系':'#f7b175'}


@lru_cache(maxsize=12)
def font(size,bold=False):
 return ImageFont.truetype(str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/('msyhbd.ttc' if bold else 'msyh.ttc')),size)


def label(draw,xy,text,size=22,fill='#ebe6d9',bold=False,anchor='lm'):
 draw.text(xy,text,font=font(size,bold),fill=fill,anchor=anchor)


def report(variant,shot):
 return json.loads((CACHE/variant/shot/'capture.json').read_text(encoding='utf8'))


def verify():
 for shot in SHOTS:
  current,refined=[report(variant,shot) for variant in ('current','refined')]
  assert current['gameHash']==refined['gameHash'],shot
  assert current['frames']==refined['frames'],shot
  assert current['info']['origin']==refined['info']['origin'],shot
  assert current['info']['targets']==refined['info']['targets'],shot
  assert current['info']['geometry']==refined['info']['geometry'],shot
  assert current['info'].get('skillGeometry')==refined['info'].get('skillGeometry'),shot
  assert current['presentation']['camera']==refined['presentation']['camera'],shot
  assert current['events']==refined['events'],shot
  for data in [current,refined]:
   assert not data['errors'] and data['info']['player']['skeletons'],shot
   directory=CACHE/data['variant']/shot
   assert len(list(directory.glob('*.jpg')))==data['frames'],shot


def template(shot,compare):
 family,name,change,hint=SHOTS[shot]
 width,height=(1920,626) if compare else (960,574)
 out=Image.new('RGB',(width,height),'#181b1b')
 d=ImageDraw.Draw(out)
 label(d,(24,30),family+' / '+name,29,PALETTE[family],True)
 label(d,(width-24,31),'当前实现 · 局部优化',19,'#b7b8ad',anchor='rm')
 if compare:
  label(d,(24,73),'当前实现',21,'#b7b8ad',True)
  label(d,(968,73),'本轮优化',21,PALETTE[family],True)
  label(d,(1100,73),change,19)
  d.line((24,559,1896,559),fill='#4b4e45')
  label(d,(24,591),hint,22)
  label(d,(1896,590),'同机位 / 原速',17,'#b7b8ad',anchor='rm')
 else:
  label(d,(18,548),change+' · '+hint,17)
 return out


def frame(shot,index,compare,base):
 out=base.copy()
 variants=('current','refined') if compare else ('refined',)
 for col,variant in enumerate(variants):
  with Image.open(CACHE/variant/shot/f'{index:03d}.jpg') as source:
   size=(928,454) if compare else (960,470)
   image=source.convert('RGB').resize(size,Image.Resampling.LANCZOS)
   out.paste(image,(24+944*col,96) if compare else (0,57))
 return out


def video(filename,compare):
 chapters=[];start=0
 for shot in SHOTS:
  count=report('refined',shot)['frames']
  chapters.append({'id':len(chapters),'time_base':Fraction(1,FPS),'start':start,'end':start+count,'metadata':{'title':SHOTS[shot][0]+' · '+SHOTS[shot][1]}})
  start+=count
 with av.open(str(MEDIA/filename),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
  movie.set_chapters(chapters)
  stream=movie.add_stream('libx264',rate=FPS)
  stream.width,stream.height=(1920,626) if compare else (960,574)
  stream.pix_fmt='yuv420p';stream.codec_context.thread_count=3;stream.options={'crf':'16','preset':'veryfast'}
  index=0
  for shot in SHOTS:
   base=template(shot,compare)
   for local in range(report('refined',shot)['frames']):
    video_frame=av.VideoFrame.from_image(frame(shot,local,compare,base));video_frame.pts=index;video_frame.time_base=Fraction(1,FPS)
    for packet in stream.encode(video_frame):movie.mux(packet)
    index+=1
  for packet in stream.encode():movie.mux(packet)


def gif(shot,filename,poster):
 base=template(shot,True)
 count=report('refined',shot)['frames']
 frames=[frame(shot,i,True,base).resize((1152,376),Image.Resampling.LANCZOS) for i in range(count)]
 durations=[(round((i+1)*100/FPS)-round(i*100/FPS))*10 for i in range(count)]
 frames=frames[poster:]+frames[:poster];durations=durations[poster:]+durations[:poster]
 sample=Image.new('RGB',(576,188*3))
 for j,i in enumerate([0,min(9,count-1),count//2]):sample.paste(frames[i].resize((576,188)),(0,j*188))
 palette=sample.quantize(256,method=Image.Quantize.MEDIANCUT)
 indexed=[image.quantize(palette=palette,dither=Image.Dither.NONE) for image in frames]
 indexed[0].save(MEDIA/filename,save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=False)


def stills():
 selections=[('BASIC_WAR',14),('THU_02',16),('FIR_02',27)]
 plate=Image.new('RGB',(1440,1128),'#181b1b')
 for row,(shot,index) in enumerate(selections):
  image=frame(shot,index,True,template(shot,True)).resize((1440,470),Image.Resampling.LANCZOS)
  # The full comparison captions remain on individual stills. The overview uses cropped viewports.
  image.save(MEDIA/(shot.lower()+'-comparison.jpg'),quality=95,subsampling=0)
  d=ImageDraw.Draw(plate)
  label(d,(20,row*376+18),SHOTS[shot][0]+' / '+SHOTS[shot][1]+'  ·  '+SHOTS[shot][2],23,PALETTE[SHOTS[shot][0]],True)
  for col,variant in enumerate(['current','refined']):
   with Image.open(CACHE/variant/shot/f'{index:03d}.jpg') as source:
    panel=source.convert('RGB').resize((704,345),Image.Resampling.LANCZOS)
    plate.paste(panel,(8+col*720,row*376+31))
 plate.save(MEDIA/'comparison-overview.jpg',quality=94,subsampling=0)


def provenance():
 data={'source':'Current Cocos battle scene and existing render modules','stage':'S04','view':'Native 3D','fps':30,'camera':'Identical oblique camera for both variants',
       'gameHash':report('current','BASIC_WAR')['gameHash'],'shots':[],
       'reviewStatus':'Current implementation and candidate captured. Awaiting user art review.',
       'deliveryState':'Design review variant served in memory by the local recorder',
       'gameplayValidation':'Matched exact event logs, hit identities, damage, targets, geometry and cameras for every shot',
       'artInputs':'Existing production atlases and their original source. Deterministic extraction.',
       'meteorSealRule':'FIR_02 only, as defined in ../reference-seals-v3/usage.json'}
 for shot in SHOTS:
  sample=report('refined',shot)
  data['shots'].append({'skill':shot,'frames':sample['frames'],'seconds':sample['frames']/30,'geometry':sample['info'].get('skillGeometry',sample['info']['geometry']),
                        'hitEvents':[event for event in sample['events'] if event['type']=='hit'],'clips':sample['clips'],'reviewInputs':sample.get('reviewInputs',{})})
 data['files']={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.rglob('*') if p.is_file() and p.suffix in {'.py','.ts','.cjs','.md','.png','.jpg','.gif','.mp4'}}
 (HERE/'provenance.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['compare','single','previews','verify']);args=parser.parse_args()
 MEDIA.mkdir(exist_ok=True)
 verify()
 if args.mode=='compare':video('current-vs-refined.mp4',True)
 elif args.mode=='single':video('refined-full-size.mp4',False)
 elif args.mode=='previews':
  gif('THU_02','thunder-comparison.gif',16)
  gif('FIR_02','fire-comparison.gif',27)
  stills()
 else:provenance()
