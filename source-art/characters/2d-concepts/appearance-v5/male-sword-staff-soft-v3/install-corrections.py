"""Byte-copy selected built-in image outputs and preserve complete stage provenance."""
from pathlib import Path
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent
records=json.loads((HERE/'generation-records.json').read_text(encoding='utf8'))
corrections=json.loads((HERE/'correction-records.json').read_text(encoding='utf8'))
history=HERE/'history';history.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for r in records:
    relevant=[c for c in corrections if c['name']==r['name']]
    if not relevant:continue
    initial=history/('initial-'+r['name'])
    if not initial.exists():shutil.copyfile(r['sourcePath'],initial)
    stages=[{k:v for k,v in r.items() if k not in ['generationStages']}]
    for c in relevant:
        archived=history/(c['kind']+'-'+r['name'])
        shutil.copyfile(c['rawOutputPath'],archived)
        target=Path(c['target'])
        target_archive=initial if target==Path(r['sourcePath']) else history/('layout-'+r['name'])
        assert sha(target)==sha(target_archive)
        stage={'kind':c['kind'],'prompt':c['prompt'],'rawOutputPath':c['rawOutputPath'],
               'actualToolEditTargetPath':c['target'],'inputs':[str(target_archive),r['inputs'][1]],
               'inputSHA256s':{str(target_archive):sha(target_archive),r['inputs'][1]:sha(r['inputs'][1])},
               'archivedRawPath':str(archived),'rawSHA256':sha(c['rawOutputPath'])}
        stages.append(stage)
    final=stages[-1]
    shutil.copyfile(final['rawOutputPath'],r['sourcePath'])
    shutil.copyfile(r['sourcePath'],r['runtimePath'])
    r.update({'generationStages':stages,'prompt':final['prompt'],'rawOutputPath':final['rawOutputPath'],
              'inputs':final['inputs'],'inputSHA256s':final['inputSHA256s'],'rawSHA256':final['rawSHA256'],
              'sourceSHA256':sha(r['sourcePath']),'runtimeSHA256':sha(r['runtimePath']),
              'builtinTool':True,'pixelEditsAfterGeneration':False})
    assert r['sourceSHA256']==r['runtimeSHA256']==r['rawSHA256']
(HERE/'generation-records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Selected3headcorrections; retained initial images and W02 layout stage in history.')
