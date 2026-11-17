"""Copy a finished Cocos output bit-for-bit; never builds or edits its source."""
from pathlib import Path
import argparse, datetime, hashlib, json, re, shutil, stat, time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
LOCK=ROOT/'src/cocos/temp/taptap-build.lock'

def unlocked():
 if LOCK.exists():raise RuntimeError('Cocos build lock is active; wait for the actual build to finish before freezing its live output')

def digest(path,check_lock=False):
 if check_lock:unlocked()
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
 if check_lock:unlocked()
 return h.hexdigest()

def files_in(folder):
 paths=[]
 for path in sorted(folder.rglob('*')):
  if path.is_symlink():raise RuntimeError(f'Symlink in build output requires an explicit stable-source review: {path}')
  if path.is_file():paths.append(path)
 return paths

def source_map(folder):
 return {str(path.relative_to(folder)).replace('\\','/'):{'sha256':digest(path,True),'bytes':path.stat().st_size} for path in files_in(folder)}

def atomic_json(path,value):
 temporary=Path(str(path)+'.tmp');temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8');temporary.replace(path)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--source-dir',default='src/cocos/build/concept-2d');parser.add_argument('--destination');parser.add_argument('--expected-main-sha');args=parser.parse_args()
 source=(ROOT/args.source_dir).resolve();unlocked()
 if not (source/'index.html').is_file():raise RuntimeError('Source is not a complete Cocos Web output: index.html is missing')
 mains=[path for path in (source/'assets/main').glob('index*.js') if re.fullmatch(r'index(?:\..+)?\.js',path.name)]
 if len(mains)!=1:raise RuntimeError('Expected one unambiguous main index; do not freeze mixed or stale main bundles')
 main=mains[0];main_sha=digest(main,True)
 if args.expected_main_sha and args.expected_main_sha.lower()!=main_sha:raise RuntimeError('The live main SHA differs from the expected completed build')
 destination=(ROOT/args.destination).resolve() if args.destination else (ROOT/f'src/.tmp/meteor-v36-frozen-build-{main_sha[:12]}-{time.time_ns()}').resolve()
 temp_root=(ROOT/'src/.tmp').resolve()
 if not destination.is_relative_to(temp_root):raise RuntimeError('Frozen output must stay within the intended ignored src/.tmp directory')
 if destination.exists():raise RuntimeError('Destination already exists; every frozen build must have its own new directory')
 original=source_map(source);unlocked();started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 def checked_copy(src,dst):
  unlocked();result=shutil.copy2(src,dst);unlocked();return result
 try:
  shutil.copytree(source,destination,copy_function=checked_copy)
  unchanged=source_map(source)
  if original!=unchanged:raise RuntimeError('Live source files changed during the copy; this output cannot be published as a frozen snapshot')
  served={str(path.relative_to(destination)).replace('\\','/'):{'sha256':digest(path),'bytes':path.stat().st_size} for path in files_in(destination)}
  if original!=served:raise RuntimeError('Copied file set or payload SHA differs from the completed source output')
  unlocked()
  for file in files_in(destination):file.chmod(file.stat().st_mode & ~(stat.S_IWUSR|stat.S_IWGRP|stat.S_IWOTH))
  copy_manifest=Path(str(destination)+'.json')
  proof={'sourceBuild':str(source),'servedSnapshot':str(destination),'compiledSha256':main_sha,'mainFile':str(main.relative_to(source)).replace('\\','/'),
         'runtimeFileCount':len(original),'copyStartedAtUtc':started,'copyCompletedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'sourceFileSetAndPayloadsUnchanged':True,'servedFileSetAndPayloadsEqual':True,'readOnlyFileAttributesApplied':True,
         'files':[{'path':name,**value} for name,value in original.items()]}
  atomic_json(copy_manifest,proof)
  index={'sourceBuild':str(source),'servedSnapshot':str(destination),'compiledSha256':main_sha,'mainFile':proof['mainFile'],
         'runtimeFileCount':len(original),'copyManifest':str(copy_manifest),'copyManifestSha256':digest(copy_manifest)}
  atomic_json(HERE/'snapshot.json',index)
  print(json.dumps({'snapshotIndex':str(HERE/'snapshot.json'),**index},ensure_ascii=False))
 except Exception as error:
  # Keep any incomplete copy as evidence. Never delete, move, or rewrite the live output.
  atomic_json(Path(str(destination)+'.freeze-failed.json'),{'sourceBuild':str(source),'unpublishedSnapshot':str(destination),'error':str(error)})
  raise

if __name__=='__main__':main()
