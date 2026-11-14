"""Arrange actual Cocos screenshots; no repainting or generated edits."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
RUNTIME=PROJECT/'src/cocos/test-results/ui-polish-v9'
OUT=ROOT/'review';OUT.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/NotoSerifSC-VF.ttf',20)
inputs=[]
def sheet(name,panels):
 canvas=Image.new('RGB',(1688,856),(20,15,11));draw=ImageDraw.Draw(canvas)
 for i,(file,label) in enumerate(panels):
  path=RUNTIME/file;image=Image.open(path).convert('RGB');image.thumbnail((844,390),Image.Resampling.LANCZOS)
  x=(i%2)*844;y=(i//2)*428
  draw.text((x+16,y+7),label,font=font,fill=(230,207,163))
  canvas.paste(image,(x+(844-image.width)//2,y+38))
  inputs.append({'file':path.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 canvas.save(OUT/name,quality=94)
sheet('overview.jpg',[('mobile-character.png','人物'),('mobile-equipment.png','装备'),('mobile-skills.png','技能'),('mobile-forge.png','强化工坊')])
sheet('secondary.jpg',[('mobile-appearance.png','外观与锻印入口'),('mobile-dice.png','免费锻印'),('mobile-dice-result.png','锻印结果'),('mobile-transfer.png','强化传承')])
(ROOT/'runtime-images.json').write_text(json.dumps({'method':'Actual native Cocos captures, scaled and arranged with Pillow; isolated review profiles; no UI painted over runtime','inputs':inputs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared overview and secondary sheets from runtime captures.')
