from pathlib import Path
import shutil,json
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109')
for n in ['manifest.json','raphael-polish.glb']:shutil.copy2(BASE/n,MIRROR/'assets/resources/actors/raphael'/n)
target=MIRROR/'assets/resources/actors/hairstyles-v2/textures';target.mkdir(parents=True,exist_ok=True)
manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
used={Path(v).name for m in manifest['materials'] for v in m.get('maps',{}).values() if '../hairstyles-v2/textures/' in v}
# This is the task-owned staging folder; rejected pilot maps stay in source art.
assert target.resolve()==Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109/assets/resources/actors/hairstyles-v2/textures').resolve()
for p in target.glob('*.png'):
 if p.name not in used:
  p.unlink();meta=p.with_name(p.name+'.meta')
  if meta.exists():meta.unlink()
for p in [BASE/'textures'/name for name in sorted(used)]:
 shutil.copy2(p,target/p.name);meta=target/(p.name+'.meta')
 if meta.exists():
  info=json.loads(meta.read_text(encoding='utf-8'))
  for sub in info.get('subMetas',{}).values():
   if sub.get('importer')=='texture':sub['userData'].update(mipfilter='linear',minfilter='linear',magfilter='linear',anisotropy=4)
  meta.write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Staged manifest-referenced hairstyle maps',sorted(used),flush=True)
