"""One short native-speed GIF, using only the v41 production recording."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-ultimate-timing-v41/training/rank5'
r=json.loads((CACHE/'capture.json').read_text(encoding='utf8'))
old=json.loads((BASE.parents[2]/'src/.tmp/warrior-ultimate-moving-hits-v40/training/rank5/capture.json').read_text(encoding='utf8'))
first_old=[next(m for m in old['metrics'] if any(w['waveIndex']==i for w in m['waves'])) for i in range(3)]
launch_old=[m['time']-next(w['age'] for w in m['waves'] if w['waveIndex']==i) for i,m in enumerate(first_old)]
launch_new=[w['estimatedLaunch'] for w in r['firstAppearances']]
assert abs(launch_old[0]-launch_new[0])<1e-6,'First release timing changed'
advance=launch_old[2]-launch_new[2]
font=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',25)
frames=[]
for i in range(84):
 im=Image.new('RGB',(1280,680),'#171d22');d=ImageDraw.Draw(im)
 d.text((16,9),f'战士最终技 · 间隔 {r["parameters"]["pulseInterval"]:.2f}s · 第三道提前 {advance:.2f}s',font=font,fill='#dce5ec')
 with Image.open(CACHE/f'{i:03d}.jpg') as shot:im.paste(shot.convert('RGB'),(0,48))
 frames.append(im.resize((960,510),Image.Resampling.LANCZOS))
sample=Image.new('RGB',(480,255*3))
for row,index in enumerate([35,45,55]):sample.paste(frames[index].resize((480,255)),(0,row*255))
palette=sample.quantize(256,method=Image.Quantize.MEDIANCUT)
indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
durations=[(round((i+1)*100/30)-round(i*100/30))*10 for i in range(84)]
out=BASE/'timing-native.gif';indexed[0].save(out,save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=True,disposal=1)
with Image.open(out) as im:
 ms=0
 for i in range(im.n_frames):im.seek(i);im.load();ms+=im.info.get('duration',0)
 assert ms==2800
p=BASE/'provenance.json';proof=json.loads(p.read_text(encoding='utf8'))
proof['v40TimingComparison']={'firstLaunchUnchanged':True,'oldLaunches':launch_old,'newLaunches':launch_new,'thirdWaveAdvancedSeconds':advance}
proof['media']={'timing-native.gif':{'milliseconds':ms,'sourceFrames':84,'fps':30,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}}
p.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'milliseconds':ms,'firstLaunchUnchanged':True,'thirdWaveAdvancedSeconds':advance}))
