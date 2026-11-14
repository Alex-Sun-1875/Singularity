"""Rebuild approved equipment UI crops with Pillow; no generation or downloads."""
from pathlib import Path
import hashlib,json,uuid
from PIL import Image,ImageDraw,ImageFilter,ImageChops,ImageOps

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
OUT=PROJECT/'src/cocos/assets/resources/ui/quiet-bronze'
manifest=json.loads((HERE/'runtime-assets.json').read_text(encoding='utf-8'))
reference=Image.open(HERE/'references/approved-equipment.png').convert('RGBA')

def blank(a):
    w,h=a.size;field=a.copy();d=ImageDraw.Draw(field)
    for y in range(5,h-5):
        row=[a.getpixel((x,y)) for x in range(12,w-12)]
        color=tuple(sorted(p[k] for p in row)[len(row)//2] for k in range(3))+(255,)
        d.line((10,y,w-11,y),fill=color)
    field=field.filter(ImageFilter.GaussianBlur(1))
    a.paste(field.crop((13,7,w-13,h-7)),(13,7))
    return a

for record in manifest['assets']:
    path=PROJECT/record['file'];name=path.stem
    source=Image.open(PROJECT/record['source_asset']).convert('RGBA') if 'source_asset' in record else reference
    image=source.crop(record['source_rect']);w,h=image.size
    if name in ['rpg-equipment-category-bar-v5','rpg-equipment-category-selected-v5']:
        image=blank(image)
    elif name=='rpg-equipment-quality-frame-v5':
        mask=Image.new('L',(w*4,h*4));d=ImageDraw.Draw(mask)
        d.polygon([(0,28),(28,0),(w*4-28,0),(w*4-1,28),(w*4-1,h*4-28),(w*4-28,h*4-1),(28,h*4-1),(0,h*4-28)],fill=255)
        d.polygon([(24,36),(36,24),(w*4-36,24),(w*4-25,36),(w*4-25,h*4-36),(w*4-36,h*4-25),(36,h*4-25),(24,h*4-36)],fill=0)
        image=ImageOps.grayscale(image).convert('RGBA')
        alpha=ImageChops.multiply(mask.resize((w,h),Image.Resampling.LANCZOS),image.convert('L').point(lambda n:min(255,max(0,(n-22)*4))))
        image.putalpha(alpha)
    elif name=='rpg-equipment-selected-frame-v5':
        mask=Image.new('L',image.size);ImageDraw.Draw(mask).rectangle((0,0,w-1,h-1),outline=255,width=9)
        image.putalpha(ImageChops.multiply(mask,image.convert('L').point(lambda n:min(255,max(0,(n-35)*4)))))
    elif name.endswith('rule-v5'):
        lum=image.convert('L')
        image.putalpha(ImageChops.subtract(lum,lum.filter(ImageFilter.GaussianBlur(3))).point(lambda n:min(255,n*9)))
    elif name=='rpg-equipment-source-v5':
        image.putalpha(image.convert('L').point(lambda n:max(0,min(255,(n-35)*4))))
    image.save(path)
    meta=Path(str(path)+'.meta')
    if not meta.exists():
        template=json.loads((OUT/'rpg-material-v3.png.meta').read_text(encoding='utf-8'))
        meta.write_text(json.dumps(template,ensure_ascii=False,indent=2).replace(template['uuid'],str(uuid.uuid4())).replace('rpg-material-v3',name)+'\n',encoding='utf-8')
    record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    record['size']=list(image.size)

(HERE/'runtime-assets.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared',len(manifest['assets']),'equipment crops.')
