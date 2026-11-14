"""Deterministic crops from the approved cloud UI proposal; labels remain native Cocos text."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import hashlib, json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'src/cocos/assets/resources/ui/quiet-bronze'
source=HERE/'03-profession-preview-generated.png'
image=Image.open(source).convert('RGBA')
boxes={'war':(490,164,828,278),'bow':(870,164,1211,277),'fir':(490,422,828,558),'thu':(870,420,1211,558)}
exports=[]
for family,box in boxes.items():
    crop=image.crop(box)
    mask=Image.new('L',crop.size,0)
    ImageDraw.Draw(mask).rounded_rectangle((6,6,crop.width-7,crop.height-7),radius=15,fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(5))
    crop.putalpha(ImageChops.multiply(crop.getchannel('A'),mask))
    filename=f'rpg-profession-{family}-v1.png'
    crop.save(OUT/filename)
    exports.append({'file':filename,'source':source.name,'box':box,'method':'crop with edge alpha feather; no generated editing','sha256':hashlib.sha256((OUT/filename).read_bytes()).hexdigest()})
(HERE/'profession-art-exports.json').write_text(json.dumps(exports,ensure_ascii=False,indent=2),encoding='utf-8')
review=Image.new('RGB',(720,310),'#19130e')
for i,row in enumerate(exports):
    art=Image.open(OUT/row['file']);art.thumbnail((340,140))
    review.paste(art,(10+(i%2)*360,10+(i//2)*155),art)
review.save(HERE/'profession-art-review.jpg',quality=95)
print('Exported four profession illustrations from the approved concept.')
