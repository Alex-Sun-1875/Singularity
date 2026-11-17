"""Refresh the existing WAR_04 art in the HUD's real static atlas."""
from pathlib import Path
import hashlib, importlib.util, json, re
from PIL import Image

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
PROJECT=ROOT/'src/cocos'
UI=PROJECT/'assets/resources/ui'
CIRCULAR=UI/'combat-relief/hud-circular'
SOURCE=UI/'combat-relief/rpg-war-04.png'
TILE=CIRCULAR/'rpg-war-04.png'
ATLAS=CIRCULAR/'atlases/war.png'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

spec=importlib.util.spec_from_file_location('hud_recipe',PROJECT/'tools/build-hud-render-assets.py')
recipe=importlib.util.module_from_spec(spec);spec.loader.exec_module(recipe)
catalog=(PROJECT/'assets/scripts/shared/ui/HudSkillAtlas.ts').read_text(encoding='utf8')
names=json.loads(re.search(r'"WAR":\s*(\[[^\]]+\])',catalog).group(1))
index=names.index('rpg-war-04');x,y=index%4*256,index//4*256
rect=(x,y,x+256,y+256)
metadata={str(p.relative_to(ROOT)):digest(p) for p in [Path(str(TILE)+'.meta'),Path(str(ATLAS)+'.meta')]}
atlas=Image.open(ATLAS).convert('RGBA');before=atlas.copy()
if not (BASE/'hud-icon-before.png').exists():before.crop(rect).save(BASE/'hud-icon-before.png')
image=Image.open(SOURCE).convert('RGBA')
tile=recipe.circle_alpha(image,min(image.size)*.047)
assert tile.convert('RGB').tobytes()==image.convert('RGB').tobytes()
tile.save(TILE,optimize=True)
atlas.paste(tile,(x,y));atlas.save(ATLAS,optimize=True)
for i,name in enumerate(names):
 r=(i%4*256,i//4*256,i%4*256+256,i//4*256+256)
 assert atlas.crop(r).tobytes()==(tile.tobytes() if i==index else before.crop(r).tobytes()),name
assert atlas.crop((768,256,1024,512)).tobytes()==before.crop((768,256,1024,512)).tobytes()
for p,h in metadata.items():assert digest(ROOT/p)==h,p

p=CIRCULAR/'provenance.json';data=json.loads(p.read_text(encoding='utf8'))
entry=next(e for e in data['entries'] if e.get('output')=='combat-relief/hud-circular/rpg-war-04.png')
entry.update(sourceSha256=digest(SOURCE),outputSha256=digest(TILE))
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
p=CIRCULAR/'atlases/provenance.json';data=json.loads(p.read_text(encoding='utf8'))
entry=next(e for e in data['entries'] if e['group']=='WAR')
entry['outputSha256']=digest(ATLAS)
next(s for s in entry['sources'] if s['name']=='rpg-war-04')['sha256']=digest(TILE)
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
tile.save(BASE/'hud-icon-circular.png')
record={'reason':'Original art was replaced, but HUD loads a separate static atlas whose WAR_04 tile still contained the old ground-impact icon.','recipe':'Existing build-hud-render-assets.py circle_alpha and lossless 1:1 atlas packing','slot':index,'rect':list(rect),'sourceSha256':digest(SOURCE),'circularSha256':digest(TILE),'atlasSha256':digest(ATLAS),'otherAtlasTilesUnchanged':True,'shieldTileUnchanged':True,'metadataUnchanged':True,'runtimeVisualReview':'pending'}
(BASE/'hud-icon-fix.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record))
