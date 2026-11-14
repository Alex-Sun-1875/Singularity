from pathlib import Path
import shutil,json
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109')
for n in ['manifest.json','raphael-polish.glb']:shutil.copy2(BASE/n,MIRROR/'assets/resources/actors/raphael'/n)
target=MIRROR/'assets/resources/actors/hairstyles-v1/textures';target.mkdir(parents=True,exist_ok=True)
for style in ['dante','nero','vergil']:
 name='hair-'+style+'-color.png';shutil.copy2(BASE/style/'textures'/name,target/name)
 meta=target/(name+'.meta')
 if meta.exists():
  info=json.loads(meta.read_text(encoding='utf-8'))
  for sub in info.get('subMetas',{}).values():
   if sub.get('importer')=='texture':sub['userData'].update(mipfilter='linear',minfilter='linear',magfilter='linear',anisotropy=4)
  meta.write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8',newline='\n')
for script in ['Actors.ts','Hairstyles.ts','Hud.ts','CharacterPanel.ts','CharacterPreview.ts','ChapterGame.ts']:
 shutil.copy2(ROOT/'src/cocos/assets/scripts/runtime'/script,MIRROR/'assets/scripts/runtime'/script)
print('Staged four hair choices and character selector',flush=True)
