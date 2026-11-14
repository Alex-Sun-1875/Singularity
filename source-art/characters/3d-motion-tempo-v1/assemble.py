"""Actual Cocos pose captures, composed at normal 30 fps without slow motion."""
from pathlib import Path
import json,hashlib,subprocess,io
from PIL import Image,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent;OUT=BASE/'runtime'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
scenarios=[('run','跑步'),('sword','挥剑'),('bow','拉弓 / 放箭'),('staff','法杖'),('dodge','翻滚')]
records={phase:json.loads((OUT/phase/'frames.json').read_text(encoding='utf-8'))for phase in ['before','after']}
groups={phase:{key:[r for r in data['rows']if r['scenario']==key]for key,label in scenarios}for phase,data in records.items()}
before=records['before']['rows'];after=records['after']['rows']
assert len(before)==len(after)==300
assert all((a['scenario'],a['frame'],a.get('action'),a.get('elapsed'),a.get('emitted'))==(b['scenario'],b['frame'],b.get('action'),b.get('elapsed'),b.get('emitted'))for a,b in zip(before,after))
rates={p:sum(x['animationSpeed']for x in groups[p]['run'][4:])/56 for p in ['before','after']}
assert .60<rates['before']<.63 and .99<rates['after']<1.01
assert min(x['elapsed']for x in groups['after']['bow']if x.get('action')=='bowAim'and x.get('bowDraw',0)>=1)<.45
assert all(r['skins']==13 for r in before+after)

def board(frame,keys,columns,cell=300):
    width=columns*cell;height=2*(cell*600//500+62)+52;im=Image.new('RGB',(width,height),'#20272a');d=ImageDraw.Draw(im)
    d.text((12,10),'3D 动作节奏 · 前后均为游戏正常速度',font=font,fill='#e4d8c0')
    for row,phase in enumerate(['before','after']):
        for col,(key,label)in enumerate(keys):
            x=col*cell;y=52+row*(cell*600//500+62);r=groups[phase][key][frame]
            d.text((x+8,y+4),('优化前 · 'if row==0 else'优化后 · ')+label,font=font,fill='#c9bdab'if row==0 else'#90ddce')
            note=f"步频 {rates[phase]:.2f}×"if key=='run'else'动作与原判定时点对应'
            d.text((x+8,y+32),note,font=small,fill='#b3bcbd')
            picture=Image.open(OUT/phase/r['file']).convert('RGB').resize((cell,cell*600//500),Image.Resampling.LANCZOS);im.paste(picture,(x,y+62))
    return im

def encode(name,keys,columns,cell):
    frames=[board(i,keys,columns,cell)for i in range(60)];palette=Image.new('RGB',(frames[0].width*6,frames[0].height))
    for i in range(6):palette.paste(frames[i*10],(i*frames[0].width,0))
    palette=palette.quantize(colors=256,method=Image.Quantize.MEDIANCUT);indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE)for f in frames]
    target=OUT/(name+'.gif');indexed[0].save(target,save_all=True,append_images=indexed[1:],duration=[30,30,40]*20,loop=0,optimize=True,disposal=1);frames[12].save(OUT/(name+'-poster.jpg'),quality=95)
    video=target.with_suffix('.webm');encoder=Path('C:/Users/Alexa/AppData/Local/ms-playwright/ffmpeg-1011/ffmpeg-win64.exe')
    process=subprocess.Popen([str(encoder),'-hide_banner','-loglevel','error','-y','-f','image2pipe','-r','30','-c:v','mjpeg','-i','pipe:0','-c:v','libvpx','-pix_fmt','yuv420p','-crf','10','-b:v','2200k','-deadline','good','-cpu-used','4',str(video)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for frame in frames:
            buffer=io.BytesIO();frame.save(buffer,format='JPEG',quality=94);process.stdin.write(buffer.getvalue())
    except BrokenPipeError:
        raise RuntimeError(process.stderr.read().decode(errors='replace'))
    process.stdin.close();error=process.stderr.read();code=process.wait()
    if code:raise RuntimeError(error.decode(errors='replace'))
    with Image.open(target)as gif:
        duration=0
        for i in range(gif.n_frames):gif.seek(i);duration+=gif.info['duration']
        assert duration==2000
        return {'file':target.name,'frames':gif.n_frames,'durationMilliseconds':duration,'size':gif.size,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'video':{'file':video.name,'bytes':video.stat().st_size,'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'fps':30,'seconds':2}}

outputs=[encode('tempo-comparison',scenarios,5,300),encode('run-comparison',[scenarios[0]],1,420)]
report={'playback':'Both sides use native 1/30-second simulation frames, encoded with repeating 30/30/40ms durations; 2 seconds shown in 2 seconds','runAnimationRate':rates,'normalRunCycleSeconds':{'before':groups['before']['run'][4]['clipDuration']/rates['before'],'after':groups['after']['run'][4]['clipDuration']/rates['after']},'sameGameplayActionEmissionSchedule':True,'actorSamples':600,'captureErrors':records['before']['errors']+records['after']['errors'],'outputs':outputs}
(OUT/'preview-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=True))
