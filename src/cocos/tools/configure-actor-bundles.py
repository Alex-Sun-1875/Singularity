"""Keep model UUIDs and paths stable while isolating lazy actor resource packs."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]/'assets/resources/actors'
for folder in sorted(root.iterdir()):
    if not folder.is_dir():
        continue
    manifest=folder/'manifest.json'
    prefab=json.loads(manifest.read_text(encoding='utf-8')).get('prefabRoot') if manifest.exists() else None
    if not (folder/(folder.name+'.fbx')).exists() and not (prefab and (folder/(prefab+'.glb')).exists()):
        continue
    meta=folder.with_suffix('.meta')
    data=json.loads(meta.read_text(encoding='utf-8'))
    data.setdefault('userData',{}).update(isBundle=True,bundleName='actor-'+folder.name,priority=9,bundleConfigID='default')
    meta.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print('actor-'+folder.name)
builder=root.parents[2]/'settings/v2/packages/builder.json'
data=json.loads(builder.read_text(encoding='utf-8'))
data.setdefault('bundleConfig',{}).setdefault('custom',{})['default']={
    'displayName':'i18n:builder.asset_bundle.defaultConfig',
    'configs':{
        'native':{'preferredOptions':{'isRemote':False,'compressionType':'merge_dep'}},
        'web':{'preferredOptions':{'isRemote':False,'compressionType':'merge_dep'},'fallbackOptions':{'compressionType':'merge_dep'}},
        'miniGame':{'fallbackOptions':{'isRemote':False,'compressionType':'merge_dep'},'configMode':'overwrite','overwriteSettings':{'wechatgame':{'isRemote':False,'compressionType':'subpackage'}}}
    }
}
builder.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
