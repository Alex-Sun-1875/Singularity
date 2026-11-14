"""Only crop, normalize and encode actual 2D assets / Cocos renders."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
OUT=BASE/'runtime'
IDS=['W01','W02','L01']
catalog=(ROOT/'src/cocos/assets/scripts/features/equipment/data/EquipmentCatalog.ts').read_text(encoding='utf-8')
NAMES={row['id']:row['name'] for row in json.loads(catalog[catalog.index('= [')+2:catalog.rindex(']')+1])}
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
SMALL=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
FLAT=ROOT/'src/cocos/assets/resources/flat2d/characters/raphael'
manifest=json.loads((FLAT/'manifest.json').read_text(encoding='utf-8'))
capture=json.loads((OUT/'comparison/frames.json').read_text())
for row in capture['rows']:
    image=Image.frombytes('RGBA',(row['width'],row['height']),(OUT/'comparison'/row['file']).read_bytes()).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    image.save(OUT/'comparison'/row['file'].replace('.rgba','.png'))

board=Image.new('RGB',(1116,530),'#343434');draw=ImageDraw.Draw(board)
draw.text((18,12),'背负位置对照 · 右肩出柄，斜向左胯',font=FONT,fill='#e8d9bc')
for col,id in enumerate(IDS):
    action=manifest['actions']['explore_idle_'+id]
    index=action.get('directionFrameIndices',[0,4,8,12])[2]
    x,y,w,h=action['perFrameRects'][index]
    reference=Image.open(FLAT/action['image']).convert('RGBA').crop((x,y,x+w,y+h))
    native=Image.open(OUT/'comparison'/f'{id}-back.png').convert('RGBA')
    draw.text((col*372+12,48),f'{NAMES[id]} · {id}',font=FONT,fill='#e8d9bc')
    for cell,(picture,label) in enumerate([(reference,'2D 设计稿'),(native,'当前 3D 实机')]):
        picture=picture.crop(picture.getchannel('A').getbbox());picture.thumbnail((172,382),Image.Resampling.LANCZOS)
        # Equal full-body height with preserved aspect ratio; no pose painting.
        height=382;width=round(picture.width*height/picture.height);picture=picture.resize((width,height),Image.Resampling.LANCZOS)
        left=col*372+cell*186+(186-width)//2
        board.paste(picture,(left,112+382-height),picture)
        draw.text((col*372+cell*186+16,83),label,font=SMALL,fill='#c8c8c8')
    if col<2:draw.line((col*372+371,48,col*372+371,506),fill='#66605a')
draw.text((18,505),'对齐背负位置与尺寸；3D 人物的脸型、衣装仍沿用现有模型。',font=SMALL,fill='#bcb6aa')
board.save(OUT/'design-comparison.jpg',quality=95)

report=json.loads((OUT/'report.json').read_text())
grouped={id:[r for r in report['frames'] if r['id']==id] for id in IDS}
frames=[]
for index in range(len(grouped['W01'])):
    canvas=Image.new('RGB',(1080,464),'#1d1d1d');d=ImageDraw.Draw(canvas)
    phase=grouped['W01'][index]['phase']
    label={'turn':'背负 · 连续转身','run':'背负 · 跑动','idle':'背负 · 停步','attack':'持剑 · 挥击与回势','settle':'脱战后收回背部'}[phase]
    for col,id in enumerate(IDS):
        row=grouped[id][index]
        picture=Image.open(OUT/row['file']).convert('RGB').crop((100,90,700,730)).resize((360,384),Image.Resampling.LANCZOS)
        canvas.paste(picture,(col*360,76));d.text((col*360+12,7),NAMES[id],font=FONT,fill='#e8d9bc')
        d.text((col*360+12,40),label,font=SMALL,fill='#c8c8c8')
    frames.append(canvas)

samples=frames[::12];sheet=Image.new('RGB',(1080*len(samples),464))
for i,frame in enumerate(samples):sheet.paste(frame,(1080*i,0))
palette=sheet.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
indexed=[frame.quantize(palette=palette,dither=Image.Dither.NONE) for frame in frames]
target=OUT/'sword-carry.gif'
indexed[0].save(target,save_all=True,append_images=indexed[1:],duration=50,loop=0,optimize=True,disposal=1)
frames[0].save(OUT/'sword-carry-poster.jpg',quality=95)
contact=Image.new('RGB',(1080,464*4),'#1d1d1d')
for row,index in enumerate([0,42,63,141]):contact.paste(frames[index],(0,row*464))
contact.save(OUT/'review-contact.jpg',quality=94)
with Image.open(target) as gif:
    duration=0
    for i in range(gif.n_frames):gif.seek(i);duration+=gif.info['duration']
    verification={'frames':gif.n_frames,'seconds':duration/1000,'size':gif.size,'bytes':target.stat().st_size,'loop':gif.info.get('loop'),'sourceFrames':len(report['frames']),'simulatedFrameSeconds':1/30,'playbackFrameSeconds':.05,'source':'Actual final Cocos scene and inventory RenderTexture; deterministic crop/scale/caption only'}
(OUT/'previews.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(verification))
