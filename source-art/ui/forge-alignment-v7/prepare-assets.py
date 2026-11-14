"""Approved workshop details, cropped and masked with Pillow; no new generation."""
from pathlib import Path
import json,hashlib,uuid
import numpy as np
from scipy.interpolate import RBFInterpolator
from PIL import Image,ImageDraw,ImageFilter,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
OUT=PROJECT/'src/cocos/assets/resources/ui/quiet-bronze'
source=Image.open(HERE/'references/approved-forge.png').convert('RGBA')
records=[]

def save(image,name,rect,method='crop'):
    path=OUT/(name+'.png');image.save(path);meta=Path(str(path)+'.meta')
    if not meta.exists():
        template=json.loads((OUT/'rpg-material-v3.png.meta').read_text(encoding='utf-8'))
        meta.write_text(json.dumps(template,ensure_ascii=False,indent=2).replace(template['uuid'],str(uuid.uuid4())).replace('rpg-material-v3',name)+'\n',encoding='utf-8')
    records.append({'file':path.relative_to(PROJECT).as_posix(),'source_rect':rect,'method':method,'size':list(image.size),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})

def blank(rect,bright=False):
    image=source.crop(rect);w,h=image.size;field=image.copy();d=ImageDraw.Draw(field)
    for y in range(7,h-7):
        row=[image.getpixel((x,y)) for x in range(14,w-14)]
        color=tuple(sorted(p[k] for p in row)[len(row)*(3 if bright else 1)//4] for k in range(3))+(255,)
        d.line((12,y,w-13,y),fill=color)
    field=field.filter(ImageFilter.GaussianBlur(1));image.paste(field.crop((14,8,w-14,h-8)),(14,8));return image

for name,rect in {'rpg-forge-tab-dark-v7':(676,90,841,143),'rpg-forge-tab-gold-v7':(838,86,1011,147)}.items():save(blank(rect,'gold' in name),name,rect,'original bevel, native label field blanked')
rect=(1157,757,1515,828);save(blank(rect,True),'rpg-forge-confirm-v7',rect,'original gold footer bevel; native cost label field blanked')
for name,rect,width in [('rpg-forge-row-v7',(62,355,512,465),5),('rpg-forge-row-selected-v7',(58,235,515,350),12)]:
    image=source.crop(rect);mask=Image.new('L',image.size);ImageDraw.Draw(mask).rectangle((0,0,image.width-1,image.height-1),outline=255,width=width)
    image.putalpha(ImageChops.multiply(mask,image.convert('L').point(lambda n:min(255,max(0,(n-23)*5)))))
    save(image,name,rect,'original edge and glow mask; icon and text omitted')
rect=(656,645,1005,704);stamp=source.crop(rect);d=ImageDraw.Draw(stamp)
# Keep the campfire and metal edge; the inscription is a live native label.
d.rectangle((87,10,333,48),fill=(26,20,13,255))
save(stamp,'rpg-forge-stamp-v7',rect,'original frame and campfire; native inscription field blanked')
rect=(590,573,1085,718);anvil=source.crop(rect)
anvil.paste(source.crop((840,573,875,598)),(212,0))
anvil.paste(stamp,(656-590,645-573))
mask=Image.new('L',(495*4,145*4));d=ImageDraw.Draw(mask)
points=[(16,54),(62,49),(77,14),(100,7),(130,7),(137,16),(327,16),(335,8),(363,8),(383,21),(396,48),(437,48),(461,61),(463,80),(453,83),(468,131),(482,144),(0,144),(18,134),(29,83),(17,82)]
d.polygon([(x*4,y*4) for x,y in points],fill=255);anvil.putalpha(mask.resize(anvil.size,Image.Resampling.LANCZOS))
save(anvil,'rpg-forge-anvil-v7',rect,'anvil silhouette; old sword tip covered with adjacent stone; blanked native stamp')
# Preserve the approved room proportions and pixels outside two live-content patches.
rect=(532,161,1228,717);room=source.crop(rect)
def replace_region(bounds,sample):
    x,y,right,bottom=bounds;w,h=right-x,bottom-y
    original=np.asarray(source.crop(bounds).convert('RGB'),dtype=float)
    sy,sx=np.mgrid[0:h:4,0:w:4];edge=(sx<7)|(sx>w-8)|(sy<7)|(sy>h-8)
    known=np.column_stack((sx[edge],sy[edge]))
    interpolator=RBFInterpolator(known/50,original[sy[edge],sx[edge]],smoothing=2)
    yy,xx=np.mgrid[0:h,0:w];values=interpolator(np.column_stack((xx.ravel(),yy.ravel()))/50).reshape(h,w,3)
    neutral=source.crop(sample).convert('RGB').resize((w,h),Image.Resampling.LANCZOS)
    grain=np.asarray(neutral,dtype=float)-np.asarray(neutral.filter(ImageFilter.GaussianBlur(5)),dtype=float)
    patch=Image.fromarray(np.uint8(np.clip(values+grain*.25,0,255))).convert('RGBA')
    mask=Image.new('L',(w,h));ImageDraw.Draw(mask).rectangle((4,4,w-5,h-5),fill=255);mask=mask.filter(ImageFilter.GaussianBlur(3));patch.putalpha(mask);room.alpha_composite(patch,(x-rect[0],y-rect[1]))
replace_region((782,164,954,603),(705,460,780,572))
replace_region((958,224,1205,355),(1010,357,1200,451))
room.alpha_composite(stamp,(656-rect[0],645-rect[1]))
save(room,'rpg-forge-approved-room-v7',rect,'approved room pixels; old weapon and lettering removed with deterministic interpolation from their clean boundaries plus faint adjacent-wall grain; native stamp blanked')
for name,rect in {'rpg-forge-coin-v7':(1299,500,1380,577),'rpg-forge-iron-v7':(1551,499,1635,576)}.items():save(source.crop(rect),name,rect)
for name,rect in {'rpg-forge-heading-rule-v7':(1266,198,1785,211),'rpg-forge-rule-v7':(1266,271,1785,286),'rpg-forge-list-rule-v7':(211,194,498,209),'rpg-forge-list-underline-v7':(78,213,222,224),'rpg-forge-name-rule-v7':(971,330,1180,347),'rpg-forge-header-rule-v7':(1191,109,1538,124)}.items():
    image=source.crop(rect);lum=image.convert('L');image.putalpha(ImageChops.subtract(lum,lum.filter(ImageFilter.GaussianBlur(3))).point(lambda n:min(255,n*9)));save(image,name,rect,'high-pass line alpha')
for name,rect in {'rpg-forge-arrow-v7':(1509,223,1563,257),'rpg-forge-stage-v7':(1288,348,1325,384),'rpg-forge-limit-v7':(1286,389,1327,424)}.items():
    image=source.crop(rect);image.putalpha(image.convert('L').point(lambda n:min(255,max(0,(n-35)*4))));save(image,name,rect,'background brightness alpha')
(HERE/'runtime-assets.json').write_text(json.dumps({'source':'references/approved-forge.png','method':'Pillow crops, letter-field blanking, original line/edge masks and deterministic anvil compositing. No generative image output; deterministic local pixel interpolation only.','assets':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared',len(records),'workshop details.')
