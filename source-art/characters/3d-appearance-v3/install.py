from pathlib import Path
import json,shutil,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];DEST=ROOT/'src/cocos/assets/resources/actors';manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'));preservation=json.loads((BASE/'preservation.json').read_text(encoding='utf-8'))
assert preservation['faceHeadEyesBrowsGeometryUVWeightsUnchanged']and preservation['allBodyClothingGeometryUVWeightsUnchanged']and preservation['all14MotionCurvesUnchanged']
folder=DEST/'appearance-v3/textures';folder.mkdir(parents=True,exist_ok=True)
names={Path(p).name for r in manifest['materials']for p in r['maps'].values()if'appearance-v3/'in p}
for name in names:shutil.copyfile(BASE/'textures'/name,folder/name)
shutil.copyfile(BASE/'raphael-polish.glb',DEST/'raphael/raphael-polish.glb');(DEST/'raphael/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
record={'runtimeGLBSHA256':hashlib.sha256((DEST/'raphael/raphael-polish.glb').read_bytes()).hexdigest(),'manifestSHA256':hashlib.sha256((DEST/'raphael/manifest.json').read_bytes()).hexdigest(),'textures':[{ 'path':(folder/n).relative_to(ROOT).as_posix(),'sha256':hashlib.sha256((folder/n).read_bytes()).hexdigest()}for n in sorted(names)],'preservation':preservation}
(BASE/'install-record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print('Installed refined original actor;',len(names),'maps')
