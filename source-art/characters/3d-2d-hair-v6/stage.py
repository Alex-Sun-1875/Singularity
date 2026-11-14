from pathlib import Path
import shutil,json
BASE=Path(__file__).resolve().parent
MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109')
assert json.loads((BASE/'manifest.json').read_text())['appearanceRevision']=='reference-silver-curls-v6'
for name in ['manifest.json','raphael-polish.glb']:shutil.copy2(BASE/name,MIRROR/'assets/resources/actors/raphael'/name)
target=MIRROR/'assets/resources/actors/hair-2d-v6/textures';target.mkdir(parents=True,exist_ok=True)
shutil.copy2(BASE/'textures/hair-reference-color.png',target/'hair-reference-color.png')
meta=target/'hair-reference-color.png.meta'
if meta.exists():
 info=json.loads(meta.read_text())
 for sub in info.get('subMetas',{}).values():
  if sub.get('importer')=='texture':sub['userData'].update(mipfilter='linear',minfilter='linear',magfilter='linear',anisotropy=4)
 meta.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
# A thumbnail belongs in source review, not in the game's texture resources.
if (BASE/'textures/atlas-review.png').exists():(BASE/'textures/atlas-review.png').replace(BASE/'atlas-review.png')
for name in ['atlas-review.png','atlas-review.png.meta']:
 if (target/name).exists():(target/name).unlink()
print('Staged reference hair in temporary Cocos mirror',flush=True)
