"""Deterministic Pillow layout and existing ffmpeg encoding of actual Cocos frames."""
from pathlib import Path
import json,io,subprocess,hashlib
from PIL import Image,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent;OUT=BASE/'runtime';SOURCE=OUT/'after-motion'
record=json.loads((SOURCE/'report.json').read_text(encoding='utf-8'));assert len(record['records'])==240 and not record['errors']
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
def board(frame,angle):
 im=Image.new('RGB',(640,520),'#20272a');d=ImageDraw.Draw(im)
 for col,clip in enumerate(['walk','run']):
  d.text((col*320+15,10),('步行'if clip=='walk'else'跑步')+' · '+('背面'if angle==180 else'侧面'),font=font,fill='#e3d6bd')
  im.paste(Image.open(SOURCE/f'{clip}-{angle}-{frame:03d}.png').convert('RGB').resize((320,400)),(col*320,80))
 return im
files=[]
for angle,label in [(180,'back'),(90,'side')]:
 frames=[board(i,angle)for i in range(60)];palette=Image.new('RGB',(640*6,520))
 for i in range(6):palette.paste(frames[i*10],(i*640,0))
 palette=palette.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
 indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE)for f in frames];gif=OUT/(label+'-walk-run.gif')
 indexed[0].save(gif,save_all=True,append_images=indexed[1:],duration=[30,30,40]*20,loop=0,optimize=True,disposal=1)
 frames[15].save(OUT/(label+'-walk-run.jpg'),quality=94)
 video=gif.with_suffix('.webm');encoder='C:/Users/Alexa/AppData/Local/ms-playwright/ffmpeg-1011/ffmpeg-win64.exe'
 p=subprocess.Popen([encoder,'-hide_banner','-loglevel','error','-y','-f','image2pipe','-r','30','-c:v','mjpeg','-i','pipe:0','-c:v','libvpx','-pix_fmt','yuv420p','-crf','10','-b:v','1800k','-deadline','good','-cpu-used','4',str(video)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 for f in frames:
  b=io.BytesIO();f.save(b,format='JPEG',quality=93);p.stdin.write(b.getvalue())
 p.stdin.close();err=p.stderr.read();assert p.wait()==0,err
 with Image.open(gif)as g:
  duration=0
  for i in range(g.n_frames):g.seek(i);duration+=g.info['duration']
 assert duration==2000
 files.extend({'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in [gif,video])
(OUT/'preview-review.json').write_text(json.dumps({'source':'Actual Cocos native actor; original 30 fps samples, no retiming','seconds':2,'gifDurationMilliseconds':2000,'walkMetresPerSecond':1.6,'runMetresPerSecond':5.2,'files':files},indent=2)+'\n',encoding='utf-8');print('PREVIEWS',json.dumps(files))
