"""Crop and encode actual runtime frames with Pillow; no generated artwork."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent/'runtime';SOURCE=BASE/'after'
record=json.loads((SOURCE/'frames.json').read_text())
text=(ROOT/'src/cocos/assets/scripts/features/equipment/data/EquipmentCatalog.ts').read_text(encoding='utf-8')
catalog=json.loads(text[text.index('= [')+2:text.rindex(']')+1]);names={x['id']:x['name'] for x in catalog}
ids=['W01','W02','L01','W07','W08','L02','W11']
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
grouped={key:[x for x in record['rows'] if x['id']==key] for key in ids}
output={};contact=Image.new('RGB',(1280,774*2),'#171717');contact_draw=ImageDraw.Draw(contact)

def encode(frames,target):
    # One shared palette prevents stationary wood textures from flickering.
    samples=frames[::max(1,len(frames)//12)]
    sheet=Image.new('RGB',(frames[0].width*len(samples),frames[0].height))
    for i,f in enumerate(samples):sheet.paste(f,(i*f.width,0))
    palette=sheet.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    indexed[0].save(target,save_all=True,append_images=indexed[1:],duration=40,loop=0,optimize=True,disposal=1)
    with Image.open(target) as im:
        duration=0
        for i in range(im.n_frames):im.seek(i);duration+=im.info['duration']
        return {'file':target.name,'frames':im.n_frames,'seconds':duration/1000,'bytes':target.stat().st_size,'size':im.size}

for key in ids:
    frames=[]
    for row in grouped[key]:
        picture=Image.open(SOURCE/row['file']).convert('RGB').crop((130,20,770,740))
        canvas=Image.new('RGB',(640,774),'#171717');canvas.paste(picture,(0,54));d=ImageDraw.Draw(canvas)
        d.text((14,5),names[key],font=font,fill='#ead7aa')
        d.text((14,31),('右上方向' if row['degrees']==45 else '左下方向')+' · 实机动作慢放',font=small,fill='#bbb8b2')
        frames.append(canvas)
    output[key]=encode(frames,BASE/f'weapon-{key}.gif')
    print(key,json.dumps(output[key]),flush=True)

# Seven synchronized weapon cells and a larger crop of the corrected bow grip.
order=['W07','W08','L02','W11','W01','W02','L01']
overview=[]
for index in range(len(grouped[ids[0]])):
    board=Image.new('RGB',(1440,896),'#171717');d=ImageDraw.Draw(board)
    for cell,key in enumerate(order):
        row=grouped[key][index];im=Image.open(SOURCE/row['file']).convert('RGB').crop((130,20,770,740)).resize((360,405),Image.Resampling.LANCZOS)
        x=cell%4*360;y=cell//4*448
        board.paste(im,(x,y+43));d.text((x+10,y+5),names[key],font=font,fill='#ead7aa')
    row=grouped['W07'][index];close=Image.open(SOURCE/row['file']).convert('RGB').crop((180,170,700,580)).resize((360,284),Image.Resampling.LANCZOS)
    board.paste(close,(1080,448+95));d.text((1090,454),'弓的握持 · 局部放大',font=font,fill='#ead7aa');d.text((1090,485),'完整手臂动作 · 实机慢放',font=small,fill='#bbb8b2')
    overview.append(board)
output['overview']=encode(overview,BASE/'all-weapons.gif')
overview[47].save(BASE/'all-weapons-poster.jpg',quality=94)
(BASE/'previews.json').write_text(json.dumps({'source':'Actual final Cocos build, unchanged combat simulation; Pillow crop/caption/GIF encode','playbackSpeed':(1/60)/.04,'outputs':output},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('OVERVIEW',json.dumps(output['overview']),flush=True)
