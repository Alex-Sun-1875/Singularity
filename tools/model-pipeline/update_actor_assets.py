from pathlib import Path
import json
root=Path(__file__).resolve().parents[2]
path=root/'src/scripts/Game/ActorAssets.lua'
header=path.read_text(encoding='utf-8').split('local actors=')[0]
lines=['local actors={']
for key,folder in [('hero','raphael'),('mira','mira'),('raider','raider')]:
    manifest=root/'src/assets/model'/folder/'manifest.json'
    if not manifest.exists():
        lines.append('    '+key+'={status="awaiting_local_model"},')
        continue
    data=json.loads(manifest.read_text(encoding='utf-8'))
    for relative in [data['model'],*data['materials'],*data['clips'].values()]:
        if not (root/'src/assets'/relative).is_file(): raise RuntimeError('Missing exported resource: '+relative)
    lines.append('    '+key+'={status="local_authored",model='+json.dumps(data['model'])+',')
    lines.append('        materials={'+','.join(json.dumps(p) for p in data['materials'])+'},')
    lines.append('        clips={'+','.join(k+'='+json.dumps(p) for k,p in data['clips'].items())+'},')
    lines.append('        sockets={'+','.join(k+'={rotation={'+','.join(str(n) for n in v['rotation'])+'},position={'+','.join(str(n) for n in v['position'])+'}}' for k,v in data.get('sockets',{}).items())+'}},')
lines.extend(['}','return actors',''])
path.write_text(header+'\n'.join(lines),encoding='utf-8',newline='\n')
print('Updated local actor resources from inspected native export manifests.')
