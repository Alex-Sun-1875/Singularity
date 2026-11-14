"""Extract the exact details marked by the user; no generative image edits."""
from pathlib import Path
import json,uuid,hashlib
from PIL import Image,ImageDraw,ImageChops,ImageFilter
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
OUT=PROJECT/'src/cocos/assets/resources/ui/quiet-bronze'
im=Image.open(ROOT/'references/approved-character.png').convert('RGBA')
records=[]
def save(asset,name,rect):
 p=OUT/(name+'.png');asset.save(p)
 meta=Path(str(p)+'.meta')
 if not meta.exists():
  template=json.loads((OUT/'rpg-material-v3.png.meta').read_text(encoding='utf8'))
  meta.write_text(json.dumps(template,ensure_ascii=False,indent=2).replace(template['uuid'],str(uuid.uuid4())).replace('rpg-material-v3',name)+'\n',encoding='utf8')
 records.append({'file':p.relative_to(PROJECT).as_posix(),'source_rect':rect,'size':list(asset.size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
def line(name,rect,bloom=False):
 a=im.crop(rect);lum=a.convert('L')
 alpha=lum.point(lambda n:max(0,min(255,(n-23)*5))) if bloom else ImageChops.subtract(lum,lum.filter(ImageFilter.GaussianBlur(3))).point(lambda n:min(255,n*9))
 a.putalpha(alpha);save(a,name,rect)
line('rpg-active-rule-v4',(453,53,677,70),True)
line('rpg-character-heading-rule-v4',(679,158,1231,169))
line('rpg-character-row-rule-v4',(679,288,1231,303))
line('rpg-combat-heading-rule-v4',(1301,150,1793,161))
line('rpg-combat-row-rule-v4',(1301,208,1793,217))
line('rpg-footer-rule-v4',(425,779,987,804))
rect=(1162,210,1218,264);plus=im.crop(rect)
m=Image.new('L',(224,216));ImageDraw.Draw(m).polygon([(4,36),(36,4),(184,4),(220,36),(220,180),(188,212),(36,212),(4,180)],fill=255)
save(plus,'rpg-attribute-plus-v4',rect)
rect=(1349,459,1459,569);frame=im.crop(rect);m=Image.new('L',(440,440));d=ImageDraw.Draw(m)
d.polygon([(4,32),(32,4),(408,4),(436,32),(436,408),(408,436),(32,436),(4,408)],fill=255)
d.polygon([(16,36),(36,16),(404,16),(424,36),(424,404),(404,424),(36,424),(16,404)],fill=0)
frame.putalpha(m.resize(frame.size,Image.Resampling.LANCZOS));save(frame,'rpg-build-icon-frame-v4',rect)
rect=(1045,107,1233,156);badge=im.crop(rect);mask=Image.new('L',badge.size);d=ImageDraw.Draw(mask);d.rectangle((0,0,187,48),outline=255,width=5);d.rectangle((0,0,22,48),fill=255);d.rectangle((166,0,187,48),fill=255);badge.putalpha(mask);empty=Image.new('RGBA',badge.size,'#251b12');empty.alpha_composite(badge);save(empty,'rpg-attribute-counter-v4',rect)
(ROOT/'runtime-assets.json').write_text(json.dumps({'source':'references/approved-character.png','method':'Pillow crop, high-pass alpha extraction for fine gold lines, antialiased polygon mask for icon frame; original button pixels kept intact. Original colors and glyph preserved. No generated pixels.','assets':records},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Exported',len(records),'original detail assets.')
