"""Adapt licensed per-skill masks with the existing metal-relief renderer."""
from pathlib import Path
from PIL import Image, ImageDraw
import importlib.util, json, hashlib, uuid, sys

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
OUTPUT=PROJECT/'src/cocos/assets/resources/ui/combat-relief'
spec=importlib.util.spec_from_file_location('relief',ROOT.parent/'skill-relief-v18/emboss.py')
relief=importlib.util.module_from_spec(spec);spec.loader.exec_module(relief)
PALETTES={
 'WAR':relief.PALETTES['skill'], 'BOW':relief.PALETTES['bow'],
 'FIR':relief.PALETTES['spell0'], 'THU':relief.PALETTES['spell1'], 'COM':relief.PALETTES['checks'],
}
record=json.loads((ROOT/'sources.json').read_text(encoding='utf8'))
pilot='--pilot' in sys.argv
assets=[a for a in record['assets'] if not pilot or a['id'] in ['WAR_01','WAR_03','FIR_01','THU_01']]
for item in assets:
 name='skill-'+item['id'].lower().replace('_','-')
 mask=Image.open(ROOT/'masks'/(item['id'].lower()+'.png')).getchannel('A')
 result=relief.emboss(mask,PALETTES[item['id'][:3]]).resize((128,128),Image.Resampling.LANCZOS)
 target=OUTPUT/(name+'.png');result.save(target,optimize=True)
 meta=target.with_suffix('.png.meta')
 if not meta.exists():
  template=(OUTPUT/'skill.png.meta').read_text(encoding='utf8')
  old=json.loads(template)['uuid'];new=str(uuid.uuid4())
  meta.write_text(template.replace(old,new).replace('"displayName": "skill"',f'"displayName": "{name}"'),encoding='utf8',newline='\n')
 item.update(asset=target.relative_to(PROJECT).as_posix(),size=list(result.size),bytes=target.stat().st_size,pngSHA256=hashlib.sha256(target.read_bytes()).hexdigest())

frame=Image.open(PROJECT/'src/cocos/assets/resources/ui/quiet-bronze/unified-gold-skill-v18.png').convert('RGBA')
cols=min(6,len(assets));rows=(len(assets)+cols-1)//cols
sheet=Image.new('RGBA',(cols*150,rows*160),(30,27,22,255));draw=ImageDraw.Draw(sheet)
for i,item in enumerate(assets):
 icon=Image.open(PROJECT/item['asset']).convert('RGBA');cx=75+i%cols*150;top=i//cols*160
 for cy,diameter in [(top+33,48),(top+100,82)]:
  sheet.alpha_composite(frame.resize((diameter,diameter),Image.Resampling.LANCZOS),(cx-diameter//2,cy-diameter//2))
  d=round(diameter*.56);sheet.alpha_composite(icon.resize((d,d),Image.Resampling.LANCZOS),(cx-d//2,cy-d//2))
 draw.text((cx-22,top+145),item['id'],fill=(225,205,162))
sheet.convert('RGB').save(ROOT/('pilot-preview.jpg' if pilot else 'isolated-preview.jpg'),quality=94)
record['artReview']['export']='Complete: deterministic SVG rasterization and existing Pillow/NumPy metal relief; 128px runtime textures.' if not pilot else 'Representative four-glyph pilot exported; full export pending.'
(ROOT/'sources.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
if not pilot:
 credits=OUTPUT/'CREDITS.txt';text=credits.read_text(encoding='utf8')
 attribution='\nPer-skill silhouettes (skill-*.png): Lorc and Delapouite, Game-icons.net, CC-BY-3.0 (https://creativecommons.org/licenses/by/3.0/). Pinned upstream sources, authors and SHA-256: source-art/ui/skill-icons-v1/sources.json. Metal-relief adaptation by this project.\n'
 if 'Per-skill silhouettes' not in text:
  temp=credits.with_suffix('.txt.tmp');temp.write_text(text+attribution,encoding='utf8',newline='\n');temp.replace(credits)
print(f'Exported {len(assets)} distinct skill glyphs; {sum(a["bytes"] for a in assets):,} PNG bytes.')
