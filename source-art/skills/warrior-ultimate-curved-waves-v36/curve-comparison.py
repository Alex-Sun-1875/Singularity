"""Same-frame single-wave comparison, using only genuine v35/v36 game captures."""
from pathlib import Path
import importlib.util, json, sys
from PIL import Image, ImageDraw

sys.dont_write_bytecode=True
base=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('curved_media',base/'media.py')
media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)
cache=base.parents[2]/'src/.tmp'
sources=[cache/'warrior-ultimate-ranked-waves-v35/training/rank1/proposal',cache/'warrior-ultimate-curved-waves-v36/training/rank1/proposal']
def frame(index):
 im=Image.new('RGB',(1440,574),'#171d22');draw=ImageDraw.Draw(im)
 media.label(draw,(18,9),'下缘恢复自然弧度 · 单道同帧慢放',29,bold=True)
 for col,(source,title) in enumerate(zip(sources,['上一版 · 下缘被压平','这一版 · 低尾尖，完整勾弧'])):
  x=col*720;media.label(draw,(x+18,51),title,24,bold=True)
  with Image.open(source/f'{index:03d}.jpg') as shot:im.paste(shot.convert('RGB').crop((320,0,1180,570)).resize((720,477),Image.Resampling.LANCZOS),(x,86))
 return im
pictures=[frame(i) for i in range(35,80)]
media.write_video('curve-before-after.mp4',pictures,15)
media.write_gif('curve-before-after.gif',[im.resize((1152,460),Image.Resampling.LANCZOS) for im in pictures],15,[5,13,23])
frame(49).save(media.OUT/'curve-before-after.jpg',quality=95,subsampling=0)
proof={}
import av
with av.open(str(media.OUT/'curve-before-after.mp4')) as movie:
 stream=movie.streams.video[0];count=sum(1 for _ in movie.decode(stream));assert count==45 and stream.average_rate==15
 proof['curve-before-after.mp4']={'frames':count,'fps':15,'seconds':float(stream.duration*stream.time_base)}
with Image.open(media.OUT/'curve-before-after.gif') as im:
 duration=0
 for i in range(im.n_frames):im.seek(i);im.load();duration+=im.info.get('duration',0)
 assert duration==3000
 proof['curve-before-after.gif']={'frames':im.n_frames,'milliseconds':duration}
(base/'curve-comparison-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8')
print(json.dumps(proof))
