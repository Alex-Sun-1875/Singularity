"""Compose actual Cocos captures at the original 30 fps; no retiming."""
from pathlib import Path
import json,subprocess,hashlib,io
from PIL import Image,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent;OUT=BASE/'runtime'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
records={p:json.loads((OUT/p/'frames.json').read_text())for p in ['before','after']}
groups={p:{s:[r for r in d['rows']if r['scenario']==s]for s in ['walk','run']}for p,d in records.items()}
assert all(len(a)==60 for d in groups.values()for a in d.values())
assert all(r['skins']==16 for d in records.values()for r in d['rows']);assert all(not d['errors']for d in records.values())
rates={p:{s:sum(r['animationSpeed']for r in rows[8:])/52 for s,rows in d.items()}for p,d in groups.items()}
assert 1.43<rates['after']['run']<1.46 and .99<rates['before']['run']<1.01
W=660;H=1040

def board(f):
 im=Image.new('RGB',(W,H),'#20272a');d=ImageDraw.Draw(im);d.text((14,10),'走跑调整 · 两侧均为游戏正常速度',font=font,fill='#e4d8c0')
 for row,p in enumerate(['before','after']):
  for col,s in enumerate(['walk','run']):
   x=col*330;y=46+row*497;d.text((x+12,y),('调整前'if p=='before'else'调整后')+' · '+('步行'if s=='walk'else'跑步'),font=font,fill='#c9bdab'if row==0 else'#90ddce')
   speed={'before':{'walk':1.728,'run':3.6},'after':{'walk':1.6,'run':5.2}}[p][s]
   note=f'{speed:g} 米/秒'
   if s=='run':note+=f' · {round(120/(groups[p][s][10]["clipDuration"]/rates[p][s]))} 步/分'
   d.text((x+12,y+29),note,font=small,fill='#bbc4c4')
   picture=Image.open(OUT/p/groups[p][s][f]['file']).crop((20,40,350,480)).convert('RGB');im.paste(picture,(x,y+57))
 return im
frames=[board(f)for f in range(60)];palette=Image.new('RGB',(W*6,H))
for i in range(6):palette.paste(frames[i*10],(i*W,0))
palette=palette.quantize(colors=256,method=Image.Quantize.MEDIANCUT);indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE)for f in frames]
gif=OUT/'locomotion-comparison.gif';indexed[0].save(gif,save_all=True,append_images=indexed[1:],duration=[30,30,40]*20,loop=0,optimize=True,disposal=1);frames[12].save(OUT/'locomotion-comparison.jpg',quality=95)
encoder='C:/Users/Alexa/AppData/Local/ms-playwright/ffmpeg-1011/ffmpeg-win64.exe';video=gif.with_suffix('.webm')
p=subprocess.Popen([encoder,'-hide_banner','-loglevel','error','-y','-f','image2pipe','-r','30','-c:v','mjpeg','-i','pipe:0','-c:v','libvpx','-pix_fmt','yuv420p','-crf','10','-b:v','2200k','-deadline','good','-cpu-used','4',str(video)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
for frame in frames:
 b=io.BytesIO();frame.save(b,format='JPEG',quality=94);p.stdin.write(b.getvalue())
p.stdin.close();error=p.stderr.read();assert p.wait()==0,error.decode(errors='replace')
with Image.open(gif)as g:
 duration=0
 for i in range(g.n_frames):g.seek(i);duration+=g.info['duration']
 assert duration==2000
report={'source':'Actual Cocos native actor','sampleSeconds':1/30,'framesPerSide':60,'playbackSeconds':2,'gifDurationMilliseconds':duration,'animationRates':rates,'runCycleSeconds':{p:groups[p]['run'][10]['clipDuration']/rates[p]['run']for p in groups},'files':[{'name':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}for f in [gif,video]],'errors':[]}
(OUT/'preview-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
