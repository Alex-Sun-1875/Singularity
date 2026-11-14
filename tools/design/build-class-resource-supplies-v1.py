"""Deterministic recolours of approved supply art; no generative model used."""
from pathlib import Path
import colorsys
import json
import uuid
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
RES=ROOT/'src/cocos/assets/resources'
ART=ROOT/'source-art/ui/class-resource-supplies-v1'
ART.mkdir(parents=True,exist_ok=True)
reference=RES/'equipment/supplies-v2/focus-bottle.png'
source=ART/'focus-bottle-original.png'
if not source.exists():
    source.write_bytes(reference.read_bytes())
base=Image.open(source).convert('RGBA')

def metadata(target,template):
    old=json.loads(template.read_text(encoding='utf-8'))
    original=old['uuid'];new=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:'+target.relative_to(ROOT).as_posix()))
    value=json.dumps(old,ensure_ascii=False,indent=2).replace(original,new).replace(template.name[:-9],target.stem)
    target.with_suffix(target.suffix+'.meta').write_text(value+'\n',encoding='utf-8')

outputs=[]
for kind,hue in [('focus',.38),('stamina',.105),('mana',.60)]:
    result=base.copy()
    data=[]
    for r,g,b,a in base.getdata():
        h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
        if a and .48<h<.81 and s>.15:
            r,g,b=(round(c*255) for c in colorsys.hsv_to_rgb(hue,s,v))
        data.append((r,g,b,a))
    result.putdata(data)
    target=RES/f'equipment/supplies-v2/{kind}-bottle.png';result.save(target)
    if kind!='focus':metadata(target,reference.with_suffix('.png.meta'))
    outputs.append(str(target.relative_to(ROOT)))
    # White silhouettes inherit public semantic colours at runtime. Each badge
    # also has a distinct shape, so the tiny HUD glyph is not colour-only.
    if kind=='focus':continue
    target=RES/f'ui/icons/potion-{kind}.png'
    result=Image.open(RES/'ui/icons/potion-focus.png').convert('RGBA')
    scale=4;result=result.resize((512,512));draw=ImageDraw.Draw(result)
    draw.ellipse((274,274,510,510),fill='white',outline=(0,0,0,0),width=12)
    if kind=='stamina':
        draw.polygon([(400,298),(329,400),(383,400),(356,488),(458,369),(402,369)],fill=(0,0,0,0))
    else:
        draw.polygon([(391,306),(339,386),(443,386)],fill=(0,0,0,0))
        draw.ellipse((339,350,443,461),fill=(0,0,0,0))
    result.resize((128,128),Image.Resampling.LANCZOS).save(target)
    metadata(target,RES/'ui/icons/potion-focus.png.meta');outputs.append(str(target.relative_to(ROOT)))

module=ROOT/'src/cocos/assets/scripts/features/combat/common/ClassResource.ts'
metadata_path=module.with_suffix('.ts.meta')
if not metadata_path.exists():
    data=json.loads((module.parent/'MeleeCombo.ts.meta').read_text(encoding='utf-8'))
    data['uuid']=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:ClassResource.ts'))
    metadata_path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
(ART/'provenance.json').write_text(json.dumps({'date':'2026-11-12','method':'Pillow HSV recolour + distinct HUD badge silhouettes','source':'src/cocos/assets/resources/equipment/supplies-v2/focus-bottle.png (preserved original alongside this file)','outputs':outputs,'generation':'deterministic local pixel processing','artReview':'pending'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared',len(outputs),'supply assets and module metadata')
