"""Archive rejected PNG bytes and select recorded ImageGen run redraws."""
from pathlib import Path
import hashlib, json, shutil, sys

SOURCE = Path(__file__).parent
generation_path = SOURCE/'run-v3-generation.json'
generation = json.loads(generation_path.read_text(encoding='utf8'))
correction_path = SOURCE/(sys.argv[1] if len(sys.argv)>1 else 'run-v3-b-corrections.json')
corrections = json.loads(correction_path.read_text(encoding='utf8'))
records = json.loads((SOURCE/'install-records.json').read_text(encoding='utf8'))
history_path = SOURCE/'run-v3-rejected-install-records.json'
history = json.loads(history_path.read_text(encoding='utf8')) if history_path.exists() else {}
for new in corrections['selected']:
    old = next(item for item in generation['selected'] if item['name'] == new['name'])
    if old['generated'] == new['generated']:
        continue
    source = SOURCE/(old['name']+'.png')
    archive = SOURCE/(old['name']+corrections.get('rejectedSuffix','-rejected-same-leg')+'.png')
    assert not archive.exists() or archive.read_bytes() == source.read_bytes()
    shutil.copyfile(source, archive)
    rejected = {**old, 'reason': corrections['reason'], 'archivedSourcePNG': archive.name,
        'archivedSourcePNGSHA256': hashlib.sha256(archive.read_bytes()).hexdigest()}
    generation['rejected'].append(rejected)
    history[archive.stem] = {'reason': corrections['reason'], 'archivedSourcePNG': archive.name,
        'previousInstallRecord': records[old['name']]}
    old.clear()
    old.update(new)
    old['correctionRecord'] = correction_path.name
generation_path.write_text(json.dumps(generation, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print('Selected corrected run sources; rejected PNGs and installation metadata archived.')
