"""Encode deterministic true-3D review frames with existing Pillow. No game changes."""
from pathlib import Path
import argparse,json,math,gc
from PIL import Image,ImageDraw,ImageFont,ImageOps

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
TEMP=ROOT/'src/.tmp/dynamic-design-3d'
MEDIA=HERE/'media';MEDIA.mkdir(exist_ok=True)
FONT=r'C:\Windows\Fonts\msyh.ttc'
BOLD=r'C:\Windows\Fonts\msyhbd.ttc'
NAMES={'WAR':'战士','BOW':'弓系','FIR':'火系','THU':'雷系','COM':'通用'}
PEAKS={'BASIC_WAR':.43,'WAR_01':.42,'WAR_02':.47,'WAR_04':.50,'WAR_05':.55,'WAR_P1':.43,
       'BASIC_BOW':.40,'BOW_01':.40,'BOW_02':.55,'BOW_03':.50,'BOW_04':.58,'BOW_05':.49,'BOW_06':.55,'BOW_07':.40,'BOW_P1':.57,'BOW_P2':.56,
       'BASIC_FIR':.43,'FIR_01':.42,'FIR_02':.55,'FIR_03':.50,'FIR_04':.55,'FIR_P1':.60,'FIR_P2':.67,
       'BASIC_THU':.35,'THU_01':.35,'THU_02':.43,'THU_03':.50,'THU_04':.44,'THU_05':.48,'THU_P1':.50,'COM_01':.34}

def framepath(family,i):return TEMP/f'render-{family}'/f'frame-{i:05d}.png'
def manifest(family):return json.loads((TEMP/f'render-{family}/capture.json').read_text(encoding='utf-8'))
def save_webp(family,reuse=False):
    data=manifest(family)
    if not data.get('native3D',False) or not data.get('modelMetadata'):raise RuntimeError('Capture lacks true-3D model evidence')
    fps=data['fps'];durations=[round((i+1)*1000/fps)-round(i*1000/fps)for i in range(data['frameCount'])]
    target=MEDIA/f'{family.lower()}-all-skills.webp'
    if not reuse:
        frames=[]
        for i in range(data['frameCount']):
            with Image.open(framepath(family,i)) as im:frames.append(im.convert('RGB'))
        frames[0].save(target,save_all=True,append_images=frames[1:],duration=durations,loop=0,quality=84,method=3,kmin=12,kmax=24,allow_mixed=True)
        del frames;gc.collect()
    with Image.open(target) as im:
        actual=im.n_frames;size=list(im.size);encoded_duration=0
        for i in range(actual):
            im.seek(i);im.load();encoded_duration+=im.info['duration']
        # WebP correctly merges identical hold frames; verify timing, not a one-to-one frame count.
        if actual<2 or abs(encoded_duration-sum(durations))>1:raise RuntimeError(f'{family}: invalid animation timing {encoded_duration}/{sum(durations)} ms')
    record={'family':family,'name':NAMES[family],'file':target.name,'size':size,'sourceFrames':data['frameCount'],'encodedFrames':actual,'fps':fps,'durationSeconds':encoded_duration/1000,'skills':[{'id':x['id'],'name':x['name'],'start':x['start'],'duration':x['duration']}for x in data['timeline']],'bytes':target.stat().st_size,'native3D':True,'runtimeIntegrated':False}
    (MEDIA/f'{family.lower()}-animation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{family}: {actual} frames, {record["durationSeconds"]:.2f}s, {record["bytes"]/1024/1024:.2f} MiB -> {target}',flush=True)

def selected_frame(family,skill,progress):
    d=manifest(family);s=next(x for x in d['timeline']if x['id']==skill)
    i=min(d['frameCount']-1,round((s['start']+min(.995,progress)*s['duration'])*d['fps']))
    with Image.open(framepath(family,i))as im:return im.convert('RGB')

def overview():
    panels=[('WAR','WAR_01','WAR_05'),('BOW','BOW_01','BOW_05'),('FIR','FIR_01','FIR_02'),('THU','THU_02','THU_05')]
    width,height=1280,672;pw,ph=626,289;frames=[];fps=20;seconds=6.6
    heading=ImageFont.truetype(BOLD,25);caption=ImageFont.truetype(FONT,16)
    for i in range(round(seconds*fps)):
        t=i/fps;second=t>=seconds/2;progress=(t%(seconds/2))/(seconds/2)
        out=Image.new('RGB',(width,height),'#211a15');d=ImageDraw.Draw(out)
        d.text((16,11),'四职业 3D 技能动态设计 · 当前模型与真实骨骼动作',font=heading,fill='#e4d3b0')
        for j,(family,one,two)in enumerate(panels):
            im=selected_frame(family,two if second else one,progress).resize((pw,ph),Image.Resampling.LANCZOS)
            x=10+(j%2)*634;y=54+(j//2)*298
            out.paste(im,(x,y));d.rectangle((x,y,x+pw,y+ph),outline='#9d804e',width=1)
        d.text((16,648),'概念动画，尚未接入游戏｜战士扩大近身覆盖提案｜陨石为火系终极｜完整版含37项',font=caption,fill='#d3c1a2')
        frames.append(out)
    webp=MEDIA/'00-four-class-overview.webp'
    frames[0].save(webp,save_all=True,append_images=frames[1:],duration=50,loop=0,quality=87,method=3)
    # A shared palette prevents the ground and lettering flickering across GIF frames.
    montage=Image.new('RGB',(640,336*8))
    for j,idx in enumerate([0,15,29,40,65,80,99,115]):montage.paste(frames[idx].resize((640,336)),(0,j*336))
    palette=montage.quantize(colors=224,method=Image.Quantize.MEDIANCUT)
    gifframes=[f.quantize(palette=palette,dither=Image.Dither.FLOYDSTEINBERG)for f in frames]
    gif=MEDIA/'00-four-class-overview.gif'
    gifframes[0].save(gif,save_all=True,append_images=gifframes[1:],duration=50,loop=0,optimize=True,disposal=1)
    frames[101].save(MEDIA/'00-four-class-poster.jpg',quality=94)
    for p in [webp,gif]:
        with Image.open(p) as im:print(p.name,im.size,im.n_frames,p.stat().st_size,flush=True)
    del frames,gifframes;gc.collect()

def contacts():
    for family in NAMES:
        data=manifest(family);items=data['timeline'];cols=3;rows=math.ceil(len(items)/cols)
        board=Image.new('RGB',(1350,76+rows*235),'#211a15');draw=ImageDraw.Draw(board)
        draw.text((22,15),NAMES[family]+' · 全技能3D动态稿代表帧',font=ImageFont.truetype(BOLD,28),fill='#e4d3b0')
        for j,s in enumerate(items):
            im=selected_frame(family,s['id'],PEAKS.get(s['id'],.53)).resize((430,199),Image.Resampling.LANCZOS)
            x=15+j%cols*445;y=67+j//cols*235;board.paste(im,(x,y))
            draw.text((x+4,y+203),s['name']+'  '+s['id'],font=ImageFont.truetype(FONT,18),fill='#ddc8a6')
        board.save(MEDIA/(family.lower()+'-contact-sheet.jpg'),quality=92)
    records=[json.loads((MEDIA/(f.lower()+'-animation.json')).read_text(encoding='utf-8'))for f in NAMES]
    index={'type':'true-3D animated design proposal','entries':sum(len(r['skills'])for r in records),'loop':True,'native3D':True,'runtimeIntegrated':False,'overview':['00-four-class-overview.gif','00-four-class-overview.webp'],'reels':records}
    (MEDIA/'animation-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--family',choices=list(NAMES));parser.add_argument('--verify-existing',action='store_true');parser.add_argument('--overview',action='store_true');parser.add_argument('--contacts',action='store_true');args=parser.parse_args()
    if args.family:save_webp(args.family,reuse=args.verify_existing)
    if args.overview:overview()
    if args.contacts:contacts()
