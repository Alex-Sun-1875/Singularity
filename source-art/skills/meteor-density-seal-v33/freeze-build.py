"""Copy a completed real Web export for stable, unmodified native recording.

Other chats share the live output. Every runtime file is hashed before/after
copying; no compiled script, scene, texture or shader is patched here.
"""
from pathlib import Path
import hashlib,json,shutil,time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
SOURCE=ROOT/'src/cocos/build/concept-2d'
LOCK=ROOT/'src/cocos/temp/taptap-build.lock'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(p):
 return {x.relative_to(p).as_posix():sha(x) for x in sorted(p.rglob('*')) if x.is_file() and x.name!='local-preview.json'}
if LOCK.exists():raise SystemExit('A Cocos export is active. Wait; no lock or process was changed.')
before=files(SOURCE)
main=next(x for x in before if x.startswith('assets/main/index.') and x.endswith('.js'))
target=ROOT/'src/.tmp'/('meteor-v33-frozen-build-'+before[main][:12]+'-'+str(time.time_ns()))
shutil.copytree(SOURCE,target)
after=files(SOURCE);copied=files(target)
if before!=after or before!=copied:
 raise SystemExit('Source export changed while copying. Snapshot retained as incomplete; do not record it.')
record={'sourceBuild':str(SOURCE),'servedSnapshot':str(target),'compiledMain':main,'compiledSha256':before[main],
        'runtimeFileCount':len(before),'runtimeFiles':before,'method':'Bitwise copy of a completed real Cocos export. All runtime files equal before/after/source/copy; local-preview.json launcher metadata excluded from hash inventory. No runtime media/code modifications.'}
report=target.with_name(target.name+'.json');report.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
small={'servedSnapshot':str(target),'compiledSha256':before[main],'runtimeFileCount':len(before),'copyManifest':str(report)}
(HERE/'snapshot.json').write_text(json.dumps(small,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(small,ensure_ascii=False))
