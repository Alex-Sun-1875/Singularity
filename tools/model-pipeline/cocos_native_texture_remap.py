"""Use Cocos 3.8.8's official FBX Image Remap configuration.

After installing/importing native FBXs and native-shared PNGs:
  python tools/model-pipeline/cocos_native_texture_remap.py --actors all --apply
Without --apply this only writes a reviewable plan. Matches exact PNG SHA256,
never image names or sub-asset ordering; uses existing ImageAsset UUIDs only.
Current Blender FBXs have duplicate channel image names: the official 3.8.8
importer collapses their remaps, so --apply deliberately blocks those assets.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT/'src/cocos'
ACTORS = PROJECT/'assets/resources/actors'
REPORT = ROOT/'src/.tmp/native-production/source/props'
OFFICIAL = 'C:/ProgramData/cocos/editors/Creator/3.8.8/resources/resources/3d/engine/editor/inspector/assets/fbx/material.js'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def plan(names):
    shared = {}
    for path in sorted((ACTORS/'native-shared/textures').glob('*.png')):
        meta_path = path.with_name(path.name+'.meta')
        if not meta_path.exists():
            raise RuntimeError(f'Import shared image before remapping: {path}')
        meta = read(meta_path)
        if meta.get('importer') != 'image':
            raise RuntimeError(f'Expected Cocos ImageAsset metadata: {meta_path}')
        shared.setdefault(sha256(path), []).append({'uuid': meta['uuid'], 'image': path.relative_to(PROJECT).as_posix()})
    records = []
    for name in names:
        directory = ACTORS/name
        manifest_path = directory/'manifest.json'
        if not manifest_path.exists() or read(manifest_path).get('runtimeProfile') != 'native-kit-v1':
            continue
        meta_path = directory/(name+'.fbx.meta')
        meta = read(meta_path)
        images = meta.get('userData', {}).get('imageMetas', [])
        if not images:
            raise RuntimeError(f'Import native FBX before remapping: {meta_path}')
        entries = []
        for item in images:
            uri = item['uri']
            image = PROJECT/'library'/uri[:2]/(uri+'.png')
            if not image.exists():
                raise RuntimeError(f'Original FBX image missing; reimport FBX first: {image}')
            digest = sha256(image)
            matches = shared.get(digest, [])
            if not matches:
                raise RuntimeError(f'No exact shared PNG hash match for {name} {uri}: {digest}')
            target = matches[0]  # Equal SHA256 PNGs are interchangeable.
            entries.append({'name': item.get('name', ''), 'uri': uri, 'remap': target['uuid'], 'sharedImage': target['image'],
                            'pngSHA256': digest, 'alreadyMapped': item.get('remap') == target['uuid']})
        by_name = {}
        for entry in entries:
            by_name.setdefault(entry['name'], []).append(entry)
        # 3.8.8's FBX importer restores remaps by image NAME, even though the
        # inspector presents per-image entries. Duplicate names with different
        # files collapse to the first remap on reimport (verified on first two).
        collisions = [{'name': image_name, 'distinctPNGs': len({e['pngSHA256'] for e in group}),
                       'uris': [e['uri'] for e in group]}
                      for image_name, group in by_name.items() if len({e['pngSHA256'] for e in group}) > 1]
        records.append({'actor': name, 'url': 'db://assets/'+(meta_path.relative_to(PROJECT/'assets').as_posix().removesuffix('.meta')),
                        'entries': entries, 'blockedNameCollisions': collisions})
    if not records:
        raise RuntimeError('No installed native-kit-v1 actors selected')
    return {'status': 'blocked-duplicate-source-image-names' if any(actor['blockedNameCollisions'] for actor in records) else 'dry-run-ready',
            'officialInspector': OFFICIAL, 'officialField': 'meta.userData.imageMetas[index].remap = ImageAsset UUID',
            'match': 'Exact original FBX image PNG file SHA256 == installed native-shared PNG file SHA256',
            'actors': records}


def apply(report):
    if any(actor['blockedNameCollisions'] for actor in report['actors']):
        raise RuntimeError('Cocos 3.8.8 remaps by duplicate image name, collapsing different PNGs to the first target. '
                           'No metadata changed. See blockedNameCollisions in the plan; keep original imported maps.')
    # Read current metadata inside the editor. Preserve uri, unrelated importer
    # settings, sub-assets and all UUIDs. The official asset-db saves/reimports.
    payload = [{'url': actor['url'], 'entries': [{'uri': entry['uri'], 'remap': entry['remap']} for entry in actor['entries']]}
               for actor in report['actors']]
    code = """return await (async()=>{
const actors=PAYLOAD,output=[];
for(const actor of actors){
 let meta=await Editor.Message.request('asset-db','query-asset-meta',actor.url);
 if(typeof meta==='string')meta=JSON.parse(meta);
 if(!meta||!meta.userData||!meta.userData.imageMetas)throw Error('Native FBX metadata changed; refresh and rerun remap plan');
 let changed=0;
 for(const entry of actor.entries){
  const item=meta.userData.imageMetas.find(image=>image.uri===entry.uri);
  if(!item)throw Error('Native FBX image set changed; refresh and rerun remap plan');
  if(item.remap!==entry.remap){item.remap=entry.remap;changed++;}
 }
 if(changed){await Editor.Message.request('asset-db','save-asset-meta',actor.url,JSON.stringify(meta));
  await Editor.Message.request('asset-db','refresh-asset',actor.url);}
 output.push({url:actor.url,images:actor.entries.length,changed});
}
return output;
})();""".replace('PAYLOAD', json.dumps(payload))
    args_path = REPORT/'native-texture-remap-mcp-args.json'
    args_path.write_text(json.dumps({'context': 'editor', 'code': code}, indent=2), encoding='utf-8')
    result = subprocess.run([sys.executable, str(PROJECT/'tools/cocos-mcp.py'), '--call', 'execute_javascript', '--args', str(args_path)],
                            cwd=str(PROJECT), capture_output=True, text=True, encoding='utf-8', errors='replace')
    (REPORT/'native-texture-remap-mcp-result.json').write_text(result.stdout+result.stderr, encoding='utf-8')
    print(result.stdout)
    if result.returncode:
        raise RuntimeError(result.stderr)
    # A tool-level rejection can still return shell exit code zero.
    try:
        envelope = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError('Cocos did not return a successful structured remap result') from error
    if envelope.get('ok') is not True:
        raise RuntimeError('Cocos rejected texture remapping: '+result.stdout)
    for actor in report['actors']:
        meta_path = ACTORS/actor['actor']/(actor['actor']+'.fbx.meta')
        meta = read(meta_path)
        actual = {image['uri']: image.get('remap') for image in meta['userData']['imageMetas']}
        if any(actual.get(entry['uri']) != entry['remap'] for entry in actor['entries']):
            raise RuntimeError(f'Remap readback mismatch: {actor["actor"]}')
    report['applied'] = True
    report['status'] = 'applied'
    report['verifiedImageRemaps'] = sum(len(actor['entries']) for actor in report['actors'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--actors', default='all', help='all or comma separated installed native actor IDs')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    names = sorted(path.parent.name for path in ACTORS.glob('*/manifest.json')) if args.actors == 'all' else args.actors.split(',')
    REPORT.mkdir(parents=True, exist_ok=True)
    report = plan(names)
    report_path = REPORT/'native-texture-remap-report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    if args.apply:
        apply(report)
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'actors': len(report['actors']), 'images': sum(len(actor['entries']) for actor in report['actors']),
                      'applied': report.get('applied', False), 'report': str(REPORT/'native-texture-remap-report.json')}))


if __name__ == '__main__':
    main()
