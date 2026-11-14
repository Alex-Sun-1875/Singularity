"""Install verified native actor and the existing pipeline's fifteen PBR maps."""
from pathlib import Path
import json,shutil,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];DEST=ROOT/'src/cocos/assets/resources/actors';actor=DEST/'raphael'
review=json.loads((BASE/'export-verification.json').read_text(encoding='utf-8'));assert review['roundtrip']['passed']and review['all14ActionCurvesUnchanged']and all(r['maxLeft']==r['maxRight']==0 for r in review['meshContact'])
manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'));manifest['profile'].update(hair='short silver waves/curls',haircolor=[.35,.38,.42],coat=[.07,.02,.032],cloth=[.018,.021,.030],armor='none')
backup=BASE/'before';backup.mkdir(exist_ok=True)
for name in ['raphael.fbx','manifest.json']:
    if not (backup/name).exists():shutil.copyfile(actor/name,backup/name)
folder=DEST/'appearance-v1/textures';folder.mkdir(parents=True,exist_ok=True)
for path in (BASE/'stage/native-shared/textures').glob('*.png'):shutil.copyfile(path,folder/path.name)
shutil.copyfile(backup/'raphael.fbx',actor/'raphael.fbx')
if (backup/'raphael.fbx.meta').exists():shutil.copyfile(backup/'raphael.fbx.meta',actor/'raphael.fbx.meta')
shutil.copyfile(BASE/'raphael-designed.glb',actor/'raphael-designed.glb');manifest['prefabRoot']='raphael-designed'
(actor/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
record={'runtimeGLBSHA256':hashlib.sha256((actor/'raphael-designed.glb').read_bytes()).hexdigest(),'legacyFBXSHA256':hashlib.sha256((actor/'raphael.fbx').read_bytes()).hexdigest(),'manifestSHA256':hashlib.sha256((actor/'manifest.json').read_bytes()).hexdigest(),'textures':[{'file':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in folder.glob('*.png')],'rigAnd14ActionCurvesPreserved':True,'renderers':13,'triangles':manifest['triangles'],'runtimeFormat':'Native glTF; the editors bundled FBX converter crashed on the new FBX, while Blender roundtrip passed'}
(BASE/'install-record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print('Installed appearance',record['triangles'],'triangles;',len(record['textures']),'maps')
