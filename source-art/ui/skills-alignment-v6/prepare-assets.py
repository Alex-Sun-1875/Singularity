"""Extract approved skill-page details with Pillow; no generated edits."""
from pathlib import Path
import json,hashlib,uuid
from PIL import Image,ImageDraw,ImageFilter,ImageChops,ImageEnhance
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
OUT=PROJECT/'src/cocos/assets/resources/ui/quiet-bronze'
source=Image.open(HERE/'references/approved-skills.png').convert('RGBA')
records=[]

def save(image,name,rect):
    path=OUT/(name+'.png');image.save(path);meta=Path(str(path)+'.meta')
    if not meta.exists():
        template=json.loads((OUT/'rpg-material-v3.png.meta').read_text(encoding='utf-8'))
        meta.write_text(json.dumps(template,ensure_ascii=False,indent=2).replace(template['uuid'],str(uuid.uuid4())).replace('rpg-material-v3',name)+'\n',encoding='utf-8')
    records.append({'file':path.relative_to(PROJECT).as_posix(),'source_rect':rect,'size':list(image.size),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})

def blank(rect,edge=8):
    image=source.crop(rect);w,h=image.size;field=image.copy();d=ImageDraw.Draw(field)
    for y in range(edge,h-edge):
        row=[image.getpixel((x,y)) for x in range(14,w-14)]
        color=tuple(sorted(p[k] for p in row)[len(row)//4] for k in range(3))+(255,)
        d.line((12,y,w-13,y),fill=color)
    field=field.filter(ImageFilter.GaussianBlur(1))
    image.paste(field.crop((14,edge,w-14,h-edge)),(14,edge))
    return image

def line(name,rect):
    image=source.crop(rect);lum=image.convert('L')
    image.putalpha(ImageChops.subtract(lum,lum.filter(ImageFilter.GaussianBlur(3))).point(lambda n:min(255,n*9)))
    save(image,name,rect)

rect=(39,90,995,151);image=blank(rect)
# Remove the baked selected segment from the continuous base; it is mounted separately.
image.paste(image.crop((240,8,400,53)).resize((184,45)),(14,8))
image.paste(ImageEnhance.Brightness(image.crop((0,0,201,61))).enhance(.45),(0,0))
save(image,'rpg-skill-family-bar-v6',rect)
rect=(40,90,240,151);save(blank(rect),'rpg-skill-family-selected-v6',rect)
rect=(1057,98,1268,147);image=source.crop(rect);mask=Image.new('L',image.size);d=ImageDraw.Draw(mask);d.rectangle((0,0,image.width-1,image.height-1),outline=255,width=5);d.rectangle((0,0,23,image.height),fill=255);d.rectangle((image.width-24,0,image.width,image.height),fill=255);image.putalpha(mask);field=Image.new('RGBA',image.size,'#251b12');field.alpha_composite(image);save(field,'rpg-skill-points-v6',rect)
rect=(210,193,296,226);image=blank(rect,5)
mask=Image.new('L',(image.width*4,image.height*4));d=ImageDraw.Draw(mask)
d.polygon([(0,64),(24,48),(36,16),(72,0),(272,0),(304,16),(320,44),(344,64),(320,84),(304,116),(272,132),(72,132),(36,116),(24,84)],fill=255)
image.putalpha(mask.resize(image.size,Image.Resampling.LANCZOS));save(image,'rpg-skill-type-v6',rect)
rect=(39,180,367,344);image=source.crop(rect);mask=Image.new('L',image.size);ImageDraw.Draw(mask).rectangle((0,0,image.width-1,image.height-1),outline=255,width=12)
image.putalpha(ImageChops.multiply(mask,image.convert('L').point(lambda n:min(255,max(0,(n-27)*5)))));save(image,'rpg-skill-selected-v6',rect)
rect=(384,194,514,324);image=source.crop(rect);mask=Image.new('L',(520,520));d=ImageDraw.Draw(mask)
d.polygon([(4,32),(32,4),(488,4),(516,32),(516,488),(488,516),(32,516),(4,488)],fill=255)
d.polygon([(16,36),(36,16),(484,16),(504,36),(504,484),(484,504),(36,504),(16,484)],fill=0)
image.putalpha(mask.resize(image.size,Image.Resampling.LANCZOS));save(image,'rpg-skill-icon-frame-v6',rect)
rect=(340,598,380,637);image=source.crop(rect);field=Image.new('RGBA',image.size,'#21190f');mask=Image.new('L',image.size);ImageDraw.Draw(mask).rectangle((0,0,image.width-1,image.height-1),outline=255,width=6);image.putalpha(mask);field.alpha_composite(image);save(field,'rpg-skill-slot-number-v6',rect)
for name,rect in {'rpg-skill-minus-v6':(1381,475,1436,525),'rpg-skill-plus-v6':(1726,475,1780,525)}.items():save(source.crop(rect),name,rect)
rect=(1463,472,1699,528);save(blank(rect),'rpg-skill-preview-v6',rect)
for name,rect in {'rpg-skill-header-rule-v6':(34,159,1283,173),'rpg-skill-row-rule-v6':(35,345,1279,357),'rpg-skill-loadout-divider-v6':(0,543,1844,558),'rpg-skill-detail-rule-v6':(1350,290,1808,303),'rpg-skill-equipped-rule-v6':(42,666,245,685),'rpg-skill-group-rule-v6':(335,574,581,587),'rpg-skill-group-divider-v6':(281,552,288,717)}.items():line(name,rect)
for name,rect in {'rpg-skill-rank-on-v6':(245,304,265,325),'rpg-skill-rank-off-v6':(294,304,314,325),'rpg-skill-upgrade-arrow-v6':(1558,384,1605,408)}.items():
    image=source.crop(rect);image.putalpha(image.convert('L').point(lambda n:max(0,min(255,(n-36)*4))));save(image,name,rect)
(HERE/'runtime-assets.json').write_text(json.dumps({'source':'references/approved-skills.png','method':'Approved image crops, letter-field removal, edge and alpha masks. No new generated pixels.','assets':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared',len(records),'skill detail assets.')
