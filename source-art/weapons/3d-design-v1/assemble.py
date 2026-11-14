"""Compose actual design references and actual Cocos PNG/JPEG renders only."""
from pathlib import Path
import json,sys,zipfile,hashlib
from PIL import Image,ImageDraw,ImageFont
import numpy as np
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];OUT=BASE/'runtime';GAL=OUT/'gallery'
items=json.loads((BASE/'designs.json').read_text(encoding='utf-8'));ids=[x['id']for x in items];names={x['id']:x['name']for x in items}
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18);SMALL=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14);TITLE=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28)
COLOR='#ded2b8';BG='#2c3437'

def normalized_mask(im):
    a=im.getchannel('A');im=im.crop(a.getbbox());return np.array(im.getchannel('A').resize((128,384)))>90

def paste_fit(board,im,box):
    x,y,w,h=box;im=im.copy();im.thumbnail((w,h),Image.Resampling.LANCZOS);board.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2),im if im.mode=='RGBA' else None)

def encode(frames,path,duration):
    sample=frames[::max(1,len(frames)//9)];sheet=Image.new('RGB',(frames[0].width*len(sample),frames[0].height))
    for i,f in enumerate(sample):sheet.paste(f,(f.width*i,0))
    palette=sheet.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE)for f in frames]
    indexed[0].save(path,save_all=True,append_images=indexed[1:],loop=0,duration=duration,optimize=True,disposal=1)
    with Image.open(path)as gif:
        seconds=0
        for i in range(gif.n_frames):gif.seek(i);seconds+=gif.info['duration']/1000
        return {'file':path.name,'frames':gif.n_frames,'seconds':round(seconds,3),'bytes':path.stat().st_size,'size':gif.size}

fronts={}
for item in items:
    id=item['id'];reference=normalized_mask(Image.open(BASE/'prepared'/(id+'.png')).convert('RGBA'));scores=[]
    for angle in [0,180]:
        actual=normalized_mask(Image.open(GAL/f'{id}-{angle}.png').convert('RGBA'));scores.append((np.logical_and(actual,reference).sum()/max(1,np.logical_or(actual,reference).sum()),angle))
    fronts[id]=max(scores)[1]

overview=Image.new('RGB',(1440,1648),BG);d=ImageDraw.Draw(overview);d.text((20,12),'24 件武器 · 游戏中的实际3D模型',font=TITLE,fill=COLOR);d.text((21,50),'按现有2D设计重建 · 各模型独立取景，实际携带比例见动作图',font=SMALL,fill='#b3bbbd')
comparison=Image.new('RGB',(1800,1816),BG);c=ImageDraw.Draw(comparison);c.text((20,13),'2D 设计与游戏模型对照',font=TITLE,fill=COLOR)
for i,item in enumerate(items):
    id=item['id'];x=i%6*240;y=i//6*390+84;native=Image.open(GAL/f'{id}-{(fronts[id]+30)%360}.png').convert('RGBA')
    d.text((x+9,y+3),id+' '+names[id],font=FONT,fill=COLOR);paste_fit(overview,native,(x+7,y+29,226,350))
    x=i%6*300;y=i//6*435+72;c.text((x+9,y),id+' '+names[id],font=FONT,fill=COLOR);c.text((x+13,y+27),'同系2D参考'if id in ['W04','W05']else'2D 参考',font=SMALL,fill='#abb7b9');c.text((x+164,y+27),'游戏 3D',font=SMALL,fill='#abb7b9')
    ref=Image.open(BASE/'prepared'/(id+'.png')).convert('RGBA');ref=ref.crop(ref.getchannel('A').getbbox());actual=Image.open(GAL/f'{id}-{fronts[id]}.png').convert('RGBA');actual=actual.crop(actual.getchannel('A').getbbox())
    paste_fit(comparison,ref,(x+8,y+53,138,365));paste_fit(comparison,actual,(x+154,y+53,138,365))
overview.save(OUT/'models-overview.jpg',quality=96);comparison.save(OUT/'design-comparison.jpg',quality=96)

turntable=[]
for f in range(12):
    board=Image.new('RGB',(1440,1648),BG);draw=ImageDraw.Draw(board);draw.text((20,13),'24 件武器 · 实际模型转面',font=TITLE,fill=COLOR);draw.text((20,51),'同一组Cocos网格与PBR材质，12个实际渲染视角',font=SMALL,fill='#b3bbbd')
    for i,id in enumerate(ids):
        x=i%6*240;y=i//6*390+84;draw.text((x+9,y+3),id+' '+names[id],font=FONT,fill=COLOR);im=Image.open(GAL/f'{id}-{(fronts[id]+f*30)%360}.png').convert('RGBA');paste_fit(board,im,(x+7,y+29,226,350))
    turntable.append(board)
outputs={'turntable':encode(turntable,OUT/'all-models-turntable.gif',150)}
del turntable

report=json.loads((OUT/'report.json').read_text(encoding='utf-8'));groups={id:sorted((x for x in report['frames']if x['id']==id),key=lambda x:x['index'])for id in ids}
def action_board(order,columns,cell_w,frame):
    rows=(len(order)+columns-1)//columns;cell_h=cell_w*620//600+53;board=Image.new('RGB',(columns*cell_w,rows*cell_h),'#202729');draw=ImageDraw.Draw(board)
    for i,id in enumerate(order):
        row=groups[id][frame];im=Image.open(OUT/row['file']).convert('RGB').crop((140,40,740,660)).resize((cell_w,cell_h-53),Image.Resampling.LANCZOS);x=i%columns*cell_w;y=i//columns*cell_h
        board.paste(im,(x,y+53));draw.text((x+8,y+3),id+' '+names[id],font=FONT,fill=COLOR)
        label='背负'if row['stowed'] else '拉弓'if row.get('action')=='bowAim'else'放箭 / 回势'if row['kind']=='bow'else'持握 / 回势'if not row.get('action')else'施放'if row['kind']=='staff'else'挥击'
        draw.text((x+8,y+29),label+' · 实机慢放',font=SMALL,fill='#b5bfc1')
    return board

for label,order,columns,cell_w in [('all-weapons-actions',ids,6,256),('core-weapons-actions',['W01','W02','L01','W07','W08','L02','W11'],4,320)]:
    frames=[action_board(order,columns,cell_w,index)for index in range(58)]
    outputs[label]=encode(frames,OUT/(label+'.gif'),50);frames[29].save(OUT/(label+'-poster.jpg'),quality=95)
    del frames

back=Image.new('RGB',(1440,4*370+70),'#202729');draw=ImageDraw.Draw(back);draw.text((20,14),'24 件武器 · 实际背负位置',font=TITLE,fill=COLOR)
for i,id in enumerate(ids):
    row=next(r for r in report['stills']if r['id']==id and r['index']==0);picture=Image.open(OUT/row['file']).convert('RGB').crop((150,80,750,700)).resize((240,248),Image.Resampling.LANCZOS);x=i%6*240;y=i//6*370+70;draw.text((x+8,y+3),id+' '+names[id],font=FONT,fill=COLOR);back.paste(picture,(x,y+34))
back.save(OUT/'back-carry.jpg',quality=95)

export=BASE/'exports';export.mkdir(exist_ok=True);zip_path=export/'weapon-models-24.zip'
model_index=[{'id':item['id'],'name':item['name'],'file':item['id']+'.glb','sha256':hashlib.sha256((BASE/'glb'/(item['id']+'.glb')).read_bytes()).hexdigest(),'metres':next(r['length']for r in json.loads((BASE/'prepared/models.json').read_text(encoding='utf-8'))if r['id']==item['id'])}for item in items]
package_note='24件武器GLB，内含材质与Draw形变。坐标Y向上，单位米，原点为握持中心。\n弓在Cocos中与现有人物对齐时使用附带的逐武器Draw校准；不包含角色动画。\n源Blender、FBX、Cocos接入及验证记录位于项目 source-art/weapons/3d-design-v1。\n新增网格和纹饰沿用项目既有2D设计；W04/W05使用同系列现有款式。\n原生弓弦与Draw数据源为KayKit Adventurers CC0，附原许可证。\n本包没有对项目全部美术另行指定开源许可。\n'
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as archive:
    for row in model_index:archive.write(BASE/'glb'/row['file'],'models/'+row['file'])
    archive.writestr('README.txt',package_note);archive.writestr('models.json',json.dumps(model_index,ensure_ascii=False,indent=2));archive.writestr('bow-draw-calibrations.json',json.dumps({item['id']:json.loads((BASE/'models'/(item['id']+'-draw-calibration.json')).read_text(encoding='utf-8'))for item in items if item['kind']=='bow'},indent=2))
    license=ROOT/'src/.tools/research-animation-kaykit/adventurers-free-2.0/KayKit_Adventurers_2.0_FREE/License.txt'
    archive.write(license,'licenses/KayKit-CC0.txt')
(OUT/'previews.json').write_text(json.dumps({'outputs':outputs,'frontViews':fronts,'package':str(zip_path.relative_to(ROOT)).replace('\\','/'),'models':len(model_index),'source':'Actual Cocos renders; Pillow crop, scale, alpha composition, captions and fixed-palette GIF encoding only'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(outputs),flush=True)
