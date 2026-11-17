"""Reuse the project's deterministic flow field, with independent WAR ownership."""
from pathlib import Path
import hashlib,json,uuid,shutil
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
OUT=ROOT/'src/cocos/assets/resources/vfx/production'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=OUT/'fire-flow-noise-v24.png'
target=OUT/'warrior-flow-v1.png'
shutil.copyfile(source,target)
def metadata(source,target):
 data=json.loads(source.read_text(encoding='utf8'));old=data['uuid'];new=str(uuid.uuid4())
 if target.exists():new=json.loads(target.read_text(encoding='utf8'))['uuid']
 text=json.dumps(data).replace(old,new).replace('fire-flow-noise-v24','warrior-flow-v1')
 data=json.loads(text)
 if target.name.endswith('.png.meta'):
  for child in data.get('subMetas',{}).values():
   if child.get('importer')=='texture':child['userData'].update(wrapModeS='repeat',wrapModeT='repeat')
 target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
metadata(OUT/'fire-flow-noise-v24.png.meta',OUT/'warrior-flow-v1.png.meta')
shutil.copyfile(BASE/'warrior-pressure-wave-v2.effect',OUT/'warrior-pressure-wave-v2.effect')
metadata(OUT/'fire-ground-v24.effect.meta',OUT/'warrior-pressure-wave-v2.effect.meta')
record={'method':'Reuse existing deterministic 128x128 RGB flow field, no new image generation; independent warrior asset references. Original source bytes retained.','source':str(source.relative_to(ROOT)),'sourceSha256':sha(source),'output':str(target.relative_to(ROOT)),'outputSha256':sha(target),'effectSha256':sha(OUT/'warrior-pressure-wave-v2.effect'),'generation':'not used','artReview':'pending actual game inspection'}
(BASE/'asset-provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record))
