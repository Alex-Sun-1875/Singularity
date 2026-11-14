"""Stable Cocos import metadata for generated CC0 assets."""
from pathlib import Path
import json,uuid
ROOT=Path(__file__).resolve().parents[2]
base=ROOT/'assets/resources/environment'
library=json.loads((base/'library.json').read_text());cutouts={pathlib['color'].split('/')[-1] for pathlib in library['materials'].values() if pathlib['cutout']}
# Project builder presets use Cocos's native ASTC encoder plus PNG compatibility
# images. Keep normal/alpha data at 4x4; opaque albedo uses 6x6.
COMPRESS_PRESETS={'color':'45b01a21-e9db-5bc5-aaf7-622e250b4046','alpha':'a0200d77-4313-5910-94cb-f59fd43ef1e1','normal':'b856c76b-3b6a-5089-8e4e-0bed6a9df2df'}
# Keep native PNG for delivery until the real compressed rendering branch
# passes visual review. Presets remain available for a later device review.
ENVIRONMENT_COMPRESSION_ENABLED=False
def uid(path):return str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity-environment/'+str(path.relative_to(ROOT))))
for folder in [base,base/'textures']:
 meta=folder.with_name(folder.name+'.meta')
 if not meta.exists():meta.write_text(json.dumps({'ver':'1.2.0','importer':'directory','imported':True,'uuid':uid(folder),'files':[],'subMetas':{},'userData':{}},indent=2))
for file in base.rglob('*'):
 if not file.is_file() or file.suffix=='.meta':continue
 ident=uid(file);meta={'imported':True,'uuid':ident,'subMetas':{},'userData':{}}
 if file.suffix=='.png':
  name=file.stem;alpha=name in cutouts
  meta.update(ver='1.0.27',importer='image',files=['.png','.json'])
  texture={'importer':'texture','uuid':ident+'@6c48a','displayName':name,'id':'6c48a','name':'texture','userData':{'wrapModeS':'repeat','wrapModeT':'repeat','minfilter':'linear','magfilter':'linear','mipfilter':'linear','anisotropy':2,'isUuid':True,'imageUuidOrDatabaseUri':ident,'visible':False},'ver':'1.0.22','imported':True,'files':['.json'],'subMetas':{}}
  meta['subMetas']={'6c48a':texture}
  meta['userData']={'type':'texture','fixAlphaTransparencyArtifacts':alpha,'hasAlpha':alpha,'redirect':ident+'@6c48a'}
  role='normal' if name.endswith('-normal') else 'alpha' if alpha else 'color'
  meta['userData']['compressSettings']={'useCompressTexture':ENVIRONMENT_COMPRESSION_ENABLED,'presetId':COMPRESS_PRESETS[role]}
 elif file.suffix=='.bin':meta.update(ver='1.0.3',importer='buffer',files=['.bin','.json'])
 else:meta.update(ver='2.0.1',importer='json',files=['.json'])
 file.with_name(file.name+'.meta').write_text(json.dumps(meta,indent=2))
p=ROOT/'assets/scripts/features/world/runtime/EnvironmentAssets.ts'
p.with_name(p.name+'.meta').write_text(json.dumps({'ver':'4.0.24','importer':'typescript','imported':True,'uuid':uid(p),'files':[],'subMetas':{},'userData':{}},indent=2))
