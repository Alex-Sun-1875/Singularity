"""Invalidate stale serialized mesh build caches, preserving backups.

Cocos caches release.json independently of library .bin. A restored/replaced
library can therefore leave a valid cache entry describing a different mesh.
Use the native Cocos rebuild; never rewrite geometry or morph offsets.
"""
from pathlib import Path
import argparse,json,shutil,datetime

def repair(project):
 project=Path(project).resolve();temp=(project/'temp').resolve();library=(project/'library').resolve();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S-%f');backup=temp/('morph-cache-backup-'+stamp);rows=[];checked=0;checked_morph=0
 def mesh_records(value):
  if isinstance(value,list):
   if len(value)>3 and value[1]=='.bin'and isinstance(value[2],(int,float))and isinstance(value[3],list)and value[3]and isinstance(value[3][0],dict)and 'vertexBundles'in value[3][0]:yield value
   for child in value:
    if isinstance(child,(list,dict)):yield from mesh_records(child)
  elif isinstance(value,dict):
   for child in value.values():
    if isinstance(child,(list,dict)):yield from mesh_records(child)
 for file in library.glob('*/*.json'):
  try:asset=json.loads(file.read_text(encoding='utf-8'))
  except (ValueError,UnicodeError):continue
  if not isinstance(asset,dict)or asset.get('__type__')!='cc.Mesh':continue
  uid=file.stem;native=file.with_suffix('.bin');structure=asset['_struct'];morph=structure.get('morph');end=max((v['offset']+v['length']for m in morph['subMeshMorphs']if m for t in m['targets']for v in t['displacements']),default=0)if morph else 0
  if not native.is_file()or end>native.stat().st_size:raise RuntimeError('Library itself has inconsistent mesh bytes; reimport '+str(file))
  for cached in (temp/'asset-db/assets'/uid[:2]/uid).glob('build*/release.json'):
   data=json.loads(cached.read_text(encoding='utf-8'));records=list(mesh_records(data));checked+=1;checked_morph+=int(bool(morph))
   if len(records)!=1:raise RuntimeError('Unexpected Cocos mesh-cache schema: '+str(cached))
   record=records[0];keys=['primitives','vertexBundles','morph'];stale=record[2]!=asset['_hash']or any(record[3][0].get(k)!=structure.get(k)for k in keys)
   if not stale:continue
   source=cached.parent.resolve();target=(backup/uid/source.name).resolve()
   assert source.is_relative_to(temp)and target.is_relative_to(temp)and source!=temp
   target.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(source),str(target))
   rows.append({'mesh':uid,'libraryHash':asset['_hash'],'staleCacheHash':record[2],'libraryBytes':native.stat().st_size,'morphBytesEnd':end,'backup':str(target.relative_to(project))})
 report={'project':str(project),'checkedMeshCaches':checked,'checkedMorphCaches':checked_morph,'invalidated':rows,'method':'Move stale generated build-cache directories into a project-local backup, then let Cocos rebuild them'}
 if rows:
  backup.mkdir(parents=True,exist_ok=True);(backup/'repair-record.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report));return report
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--project',default=str(Path(__file__).resolve().parents[1]));args=parser.parse_args();repair(args.project)
