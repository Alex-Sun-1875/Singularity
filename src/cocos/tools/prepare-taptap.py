"""Prepare Cocos native bundle options; never move or remove source artwork."""
import argparse
import json
import subprocess
import sys
import uuid
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
RESOURCE_ROOT = PROJECT / 'assets/resources'


def write_json(path, data, *, creator_prefab=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, indent=2) + ('' if creator_prefab else '\n')
    if creator_prefab:
        # Creator serializes prefabs with LF and no final newline on all hosts.
        raw = content.encode('utf-8')
        if not path.exists() or path.read_bytes() != raw:
            path.write_bytes(raw)
        return
    if not path.exists() or path.read_text(encoding='utf-8') != content:
        path.write_text(content, encoding='utf-8')


def referenced_actor_images(folder):
    """Follow the same image selection as FlatActors.load, including frame sheets."""
    data = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    names = {name for action in data['actions'].values()
             for name in action.get('frameImages', [action.get('image', data.get('image', 'atlas.png'))])}
    if data.get('movementEquipment'):
        names.add(data['movementEquipment']['image'])
    result = set()
    for name in names:
        path = (folder / name.replace('\\', '/')).resolve()
        if not path.is_relative_to(folder.resolve()) or not path.is_file():
            raise SystemExit('Missing or invalid actor image: ' + str(path))
        result.add(path)
    return result


def pack_exclusions(pack):
    """Filter published assets only; retain source art and original importer UUIDs."""
    folder = RESOURCE_ROOT / pack['path']
    excluded = set(pack.get('excludeFiles', []))
    files = [p for p in folder.rglob('*') if p.is_file() and p.suffix != '.meta']
    if 'includeFiles' in pack:
        included = set(pack['includeFiles'])
        if any(not (folder / name).is_file() for name in included):
            raise SystemExit('Missing included resource in ' + pack['path'])
        excluded.update(p.relative_to(folder).as_posix() for p in files
                        if p.relative_to(folder).as_posix() not in included)
    image_types = ('.png', '.jpg', '.webp', '.jpeg')
    if pack.get('referencedImagesOnly'):
        included = referenced_actor_images(folder)
        excluded.update(p.relative_to(folder).as_posix() for p in files
                        if p.suffix.lower() in image_types and p.resolve() not in included)
    if 'includeImages' in pack:
        excluded.update(p.name for p in folder.iterdir()
                        if p.suffix.lower() in image_types and p.name not in pack['includeImages'])
    if 'referencedMaterialManifests' in pack:
        included = set()
        for name in pack['referencedMaterialManifests']:
            manifest = RESOURCE_ROOT / name
            data = json.loads(manifest.read_text(encoding='utf-8'))
            for record in data['materials']:
                for name in record['maps'].values():
                    path = (manifest.parent / name).resolve()
                    if not path.is_relative_to(RESOURCE_ROOT.resolve()) or not path.is_file():
                        raise SystemExit('Missing or invalid material texture: ' + str(path))
                    included.add(path)
        excluded.update(p.relative_to(folder).as_posix() for p in files
                        if p.suffix.lower() in image_types and p.resolve() not in included)
    return sorted(excluded)


def selective_packs(profile):
    """Cocos prefab references collect existing UUIDs into small bundles.

    Source artwork, importer UUIDs and authored resource paths remain intact.
    These sibling bundle roots do not nest inside any existing Asset Bundle.
    """
    bundles, routes = [], {}
    for group in profile.get('selectivePacks', []):
        name = group['name']
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in name):
            raise SystemExit('Invalid selective bundle name: ' + name)
        files = set()
        for pattern in group.get('sources', []):
            matches = {p for p in RESOURCE_ROOT.glob(pattern) if p.is_file() and p.suffix != '.meta'}
            if not matches:
                raise SystemExit('Empty selective resource pattern: ' + pattern)
            files.update(matches)
        if group.get('weaponVariants'):
            manifest = RESOURCE_ROOT / 'actors/props-native/manifest.json'
            files.add(manifest)
            props = json.loads(manifest.read_text(encoding='utf-8'))['props']
            for variant in group['weaponVariants']:
                folder = RESOURCE_ROOT / 'actors/props-native' / variant
                files.update(folder.glob('*.fbx'))
                files.update(folder.glob('*.glb'))
                for record in props[variant]['materials']:
                    for relative in record['maps'].values():
                        files.add((RESOURCE_ROOT / 'actors/raphael' / relative).resolve())
        entries = set()
        for file in sorted(files):
            if not file.resolve().is_relative_to(RESOURCE_ROOT.resolve()) or not file.is_file():
                raise SystemExit('Missing selective resource: ' + str(file))
            meta = json.loads(file.with_name(file.name + '.meta').read_text(encoding='utf-8'))
            stem = file.relative_to(RESOURCE_ROOT).with_suffix('').as_posix()
            asset_routes = {}
            if meta['importer'] in ('fbx', 'gltf'):
                for sub in meta['subMetas'].values():
                    if sub['importer'] == 'gltf-scene':
                        asset_routes[stem + '/' + Path(sub['name']).stem] = sub['uuid']
            else:
                asset_routes[stem] = meta['uuid']
                for sub in meta.get('subMetas', {}).values():
                    if sub['importer'] in ('texture', 'sprite-frame'):
                        asset_routes[stem + '/' + sub['name']] = sub['uuid']
            if not asset_routes:
                raise SystemExit('No loadable selective asset: ' + str(file))
            for logical, asset_uuid in asset_routes.items():
                if logical in routes:
                    raise SystemExit('Overlapping selective resource: ' + logical)
                routes[logical] = {'bundle': name, 'uuid': asset_uuid}
                entries.add(asset_uuid)
        for logical, target in group.get('aliases', {}).items():
            matches = {key: value for key, value in routes.items()
                       if value['bundle'] == name and (key == target or key.startswith(target + '/'))}
            if not matches:
                raise SystemExit('Missing selective alias target: ' + target)
            for key, value in matches.items():
                alias = logical + key[len(target):]
                if alias in routes:
                    raise SystemExit('Overlapping selective alias: ' + alias)
                routes[alias] = dict(value)
        folder = PROJECT / 'assets/bundle-groups' / name
        for directory in [folder.parent, folder]:
            meta = directory.with_name(directory.name + '.meta')
            if not meta.exists():
                write_json(meta, {'ver': '1.2.0', 'importer': 'directory', 'imported': True,
                                 'uuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'singularity/' + directory.relative_to(PROJECT).as_posix())),
                                 'files': [], 'subMetas': {}, 'userData': {}})
        # Typed Asset references use Cocos' normal dependency collector. Bundle
        # filters can only select assets within their root, not external UUIDs.
        marker = folder / 'bundle.json'
        write_json(marker, {'name': name, 'purpose': 'selective-resource-bundle'})
        marker_meta = marker.with_name(marker.name + '.meta')
        if not marker_meta.exists():
            write_json(marker_meta, {'ver': '2.0.1', 'importer': 'json', 'imported': True,
                                    'uuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'singularity/' + marker.relative_to(PROJECT).as_posix())),
                                    'files': ['.json'], 'subMetas': {}, 'userData': {}})
        script_uuid = json.loads((PROJECT / 'assets/scripts/shared/assets/BundleAssetReferences.ts.meta').read_text(encoding='utf-8'))['uuid'].replace('-', '')
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        script_id = script_uuid[:5] + ''.join(alphabet[int(script_uuid[i:i+3], 16) >> 6] +
                                              alphabet[int(script_uuid[i:i+3], 16) & 63]
                                              for i in range(5, 32, 3))
        prefab = folder / 'assets.prefab'
        write_json(prefab, [
            # Creator normalizes both names to the prefab filename on import.
            # Emit its stable form so exporting never mutates release inputs.
            {'__type__': 'cc.Prefab', '_name': prefab.stem, '_objFlags': 0, '_native': '',
             'data': {'__id__': 1}, 'persistent': False},
            {'__type__': 'cc.Node', '_name': prefab.stem, '_objFlags': 0, '_parent': None, '_children': [],
             '_active': True, '_components': [{'__id__': 2}], '_prefab': None,
             '_lpos': {'__type__': 'cc.Vec3', 'x': 0, 'y': 0, 'z': 0},
             '_lrot': {'__type__': 'cc.Quat', 'x': 0, 'y': 0, 'z': 0, 'w': 1},
             '_lscale': {'__type__': 'cc.Vec3', 'x': 1, 'y': 1, 'z': 1}, '_layer': 1},
            {'__type__': script_id, '_name': '', '_objFlags': 0, 'node': {'__id__': 1}, '_enabled': True,
             '__prefab': None, 'assets': [{'__uuid__': asset_uuid} for asset_uuid in sorted(entries)]}],
                   creator_prefab=True)
        prefab_meta = prefab.with_name(prefab.name + '.meta')
        if not prefab_meta.exists():
            write_json(prefab_meta, {'ver': '1.1.50', 'importer': 'prefab', 'imported': True,
                                    'uuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'singularity/' + prefab.relative_to(PROJECT).as_posix())),
                                    'files': ['.json'], 'subMetas': {}, 'userData': {}})
        bundles.append({'root': 'db://' + folder.relative_to(PROJECT).as_posix(), 'name': name,
                        'priority': 11, 'output': True, 'isRemote': False})
    return bundles, routes


def prepare_resource_routes(profile):
    packs = list(profile['packs'])
    for collection in profile['collections']:
        for folder in sorted((RESOURCE_ROOT / collection['path']).iterdir()):
            if folder.is_dir() and folder.name not in collection.get('exclude', []):
                packs.append({'path': folder.relative_to(RESOURCE_ROOT).as_posix(),
                              'name': collection['namePrefix'] + folder.name,
                              'referencedImagesOnly': collection.get('referencedImagesOnly', False)})
    groups, asset_routes = selective_packs(profile)
    names = [pack['name'] for pack in packs] + [group['name'] for group in groups]
    if len(names) != len(set(names)):
        raise SystemExit('Duplicate resource pack names')
    for pack in packs:
        if not (RESOURCE_ROOT / pack['path']).is_dir():
            raise SystemExit('Missing resource directory: ' + pack['path'])

    # Ordinary Web/editor previews still resolve the old resources paths. Release
    # builds use the same paths through GameResources and these explicit bundles.
    routes = sorted(({'prefix': p['path'] + '/', 'bundle': p['name']} for p in packs),
                    key=lambda p: (-len(p['prefix']), p['prefix']))
    generated = ('/** Generated by tools/prepare-taptap.py from release/taptap.json. */\n'
                 'export const RESOURCE_PACKS:readonly {prefix:string;bundle:string}[] = '
                 + json.dumps(routes, ensure_ascii=False, indent=2) + ';\n'
                 + '/** Exact UUID routes for source-preserving selective bundles. */\n'
                 + 'export const RESOURCE_ASSET_PACKS:Readonly<Record<string,{bundle:string;uuid:string}>> = '
                 + json.dumps(asset_routes, ensure_ascii=False, indent=2) + ';\n')
    runtime_file = PROJECT / 'assets/scripts/shared/assets/ResourcePacks.ts'
    if not runtime_file.exists() or runtime_file.read_text(encoding='utf-8') != generated:
        runtime_file.write_text(generated, encoding='utf-8')

    return packs


def prepare(platform, output_name, mode='test', gameplay_profile='test'):
    subprocess.check_call([sys.executable, str(PROJECT / 'tools/prepare-startup-preview.py')])
    spec = spec_from_file_location('native_texture_reuse', PROJECT / 'tools/prepare-native-texture-reuse.py')
    reuse = module_from_spec(spec)
    spec.loader.exec_module(reuse)
    reuse.prepare()
    release = json.loads(subprocess.check_output(['node', str(PROJECT / 'tools/taptap-config.cjs'),
                         '--prepare', '--json', '--mode', mode, '--profile', gameplay_profile], encoding='utf-8'))
    profile = json.loads((PROJECT / 'release/taptap.json').read_text(encoding='utf-8'))
    if 'surfaces' in profile['excludedResourceTrees']:
        hero = json.loads((RESOURCE_ROOT / 'actors/raphael/manifest.json').read_text(encoding='utf-8'))
        if hero.get('runtimeProfile') != 'native-kit-v1' or not hero.get('cocosBinding', {}).get('swordBackCarry', {}).get('embeddedCases'):
            raise SystemExit('This hero requires the surface-materials bundle; restore it before packaging.')
    packs = prepare_resource_routes(profile)
    names = [pack['name'] for pack in packs]
    excluded_assets = []

    def exclusion(path, glob=True):
        return {'range': 'exclude', 'type': 'url',
                'patchOption': {'patchType': 'glob' if glob else 'beginWith',
                                'value': 'db://assets/resources/' + path}}

    resource_filters = [exclusion(path + '/**') for path in profile['excludedResourceTrees']]
    resource_filters += [exclusion(p['path'] + '/**') for p in packs]
    resource_filters += [exclusion(path, False) for path in profile.get('excludedResourceFiles', [])]
    bundles = [{'root': 'db://assets/resources', 'name': 'resources', 'priority': 8,
                'output': True, 'isRemote': False, 'compressionType': 'merge_dep',
                'bundleFilterConfig': resource_filters}]
    for pack in packs:
        bundle = {'root': 'db://assets/resources/' + pack['path'], 'name': pack['name'],
                  'output': True, 'priority': 9, 'isRemote': False,
                  'compressionType': 'subpackage' if platform == 'wechatgame' else 'merge_dep'}
        excluded = pack_exclusions(pack)
        for name in excluded:
            path = RESOURCE_ROOT / pack['path'] / name
            if path.is_file():
                excluded_assets.append({'path': path.relative_to(RESOURCE_ROOT).as_posix(),
                                        'sourceBytes': path.stat().st_size, 'bundle': pack['name']})
        if excluded:
            bundle['bundleFilterConfig'] = [exclusion(pack['path'] + '/' + name, False)
                                            for name in excluded]
        bundles.append(bundle)
    groups, _ = selective_packs(profile)
    for group in groups:
        group['compressionType'] = 'subpackage' if platform == 'wechatgame' else 'merge_dep'
        bundles.append(group)
    # Existing 3D comparison NPC bundles are deliberately omitted from this
    # release. Their files and original .meta UUIDs remain untouched.
    for meta in sorted((RESOURCE_ROOT / 'actors').glob('*.meta')):
        data = json.loads(meta.read_text(encoding='utf-8'))
        name = data.get('userData', {}).get('bundleName')
        if data.get('userData', {}).get('isBundle') and name not in names:
            bundles.append({'root': 'db://assets/resources/actors/' + meta.stem,
                            'name': name, 'output': False})
    scene = 'e0158e35-9bac-42ca-a8e1-16cdd7e71953'
    config = {'platform': platform, 'name': release['projectName'], 'outputName': output_name,
              'buildPath': 'project://build', 'debug': False, 'sourceMaps': False,
              'useSplashScreen': False,
              'startScene': scene, 'scenes': [{'url': 'db://assets/FirstChapter.scene', 'uuid': scene}],
              'md5Cache': True, 'mainBundleCompressionType': 'merge_dep',
              'bundleConfigs': bundles, 'packages': {'taptap-minigame-tools': {'enableTapConvert': False}}}
    if platform == 'wechatgame':
        # Creator's WeChat defaults force WebGL 2 off independently of the
        # project's module selection. This project excludes WebGL 1, so retain
        # its WebGL 2 backend in both the engine and generated first-screen boot.
        config['overwriteProjectSettings'] = {
            'includeModules': {'gfx-webgl2': 'on'}}
        # Cocos may insert its own WeChat sample ID during intermediate export.
        # convert-taptap.cjs removes it; it is never a TapTap identity.
        config['packages']['wechatgame'] = {'orientation': profile['orientation'],
                                            'separateEngine': False,
                                            'wasmSubpackage': profile['engineWasmSubpackage']}
    path = PROJECT / 'temp' / ('build-' + output_name + '.json')
    write_json(path, config)
    write_json(PROJECT / 'temp/taptap-resource-plan.json', {'profile': profile, 'packs': packs,
               'bundles': bundles, 'excludedAssets': excluded_assets,
               'identity': 'provided-app-id' if mode in ('dev', 'test', 'release') else 'unbound', 'platform': platform, 'release': release})
    print(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', choices=['wechatgame', 'web-mobile'], default='wechatgame')
    parser.add_argument('--output-name', default='taptap-audit')
    parser.add_argument('--mode', choices=['audit', 'preview', 'dev', 'test', 'release'], default='test')
    parser.add_argument('--profile', choices=['dev', 'test', 'release'], default='test')
    parser.add_argument('--routes-only', action='store_true', help='Regenerate only ResourcePacks from the release profile; no build or identity configuration changes.')
    args = parser.parse_args()
    if args.routes_only:
        profile = json.loads((PROJECT / 'release/taptap.json').read_text(encoding='utf-8'))
        packs = prepare_resource_routes(profile)
        print('Prepared resource routes for ' + str(len(packs)) + ' packs')
        raise SystemExit(0)
    if not args.output_name.replace('-', '').replace('_', '').isalnum():
        parser.error('output-name must be a simple directory name')
    prepare(args.platform, args.output_name, args.mode, args.profile)
