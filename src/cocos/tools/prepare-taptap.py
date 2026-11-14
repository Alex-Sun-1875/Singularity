"""Prepare Cocos native bundle options; never move or remove source artwork."""
import argparse
import json
import subprocess
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
RESOURCE_ROOT = PROJECT / 'assets/resources'


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


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


def prepare(platform, output_name, mode='audit'):
    spec = spec_from_file_location('native_texture_reuse', PROJECT / 'tools/prepare-native-texture-reuse.py')
    reuse = module_from_spec(spec)
    spec.loader.exec_module(reuse)
    reuse.prepare()
    release = json.loads(subprocess.check_output(['node', str(PROJECT / 'tools/taptap-config.cjs'),
                         '--prepare', '--json', '--mode', mode], encoding='utf-8'))
    profile = json.loads((PROJECT / 'release/taptap.json').read_text(encoding='utf-8'))
    if 'surfaces' in profile['excludedResourceTrees']:
        hero = json.loads((RESOURCE_ROOT / 'actors/raphael/manifest.json').read_text(encoding='utf-8'))
        if hero.get('runtimeProfile') != 'native-kit-v1' or not hero.get('cocosBinding', {}).get('swordBackCarry', {}).get('embeddedCases'):
            raise SystemExit('This hero requires the surface-materials bundle; restore it before packaging.')
    packs = list(profile['packs'])
    for collection in profile['collections']:
        for folder in sorted((RESOURCE_ROOT / collection['path']).iterdir()):
            if folder.is_dir() and folder.name not in collection.get('exclude', []):
                packs.append({'path': folder.relative_to(RESOURCE_ROOT).as_posix(),
                              'name': collection['namePrefix'] + folder.name,
                              'referencedImagesOnly': collection.get('referencedImagesOnly', False)})
    names = [pack['name'] for pack in packs]
    if len(names) != len(set(names)):
        raise SystemExit('Duplicate resource pack names')
    excluded_assets = []
    for pack in packs:
        if not (RESOURCE_ROOT / pack['path']).is_dir():
            raise SystemExit('Missing resource directory: ' + pack['path'])

    # Ordinary Web/editor previews still resolve the old resources paths. Release
    # builds use the same paths through GameResources and these explicit bundles.
    routes = sorted(({'prefix': p['path'] + '/', 'bundle': p['name']} for p in packs),
                    key=lambda p: (-len(p['prefix']), p['prefix']))
    generated = ('/** Generated by tools/prepare-taptap.py from release/taptap.json. */\n'
                 'export const RESOURCE_PACKS:readonly {prefix:string;bundle:string}[] = '
                 + json.dumps(routes, ensure_ascii=False, indent=2) + ';\n')
    runtime_file = PROJECT / 'assets/scripts/shared/assets/ResourcePacks.ts'
    if not runtime_file.exists() or runtime_file.read_text(encoding='utf-8') != generated:
        runtime_file.write_text(generated, encoding='utf-8')

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
               'identity': 'provided-app-id' if mode in ('test', 'release') else 'unbound', 'platform': platform, 'release': release})
    print(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', choices=['wechatgame', 'web-mobile'], default='wechatgame')
    parser.add_argument('--output-name', default='taptap-audit')
    parser.add_argument('--mode', choices=['audit', 'preview', 'test', 'release'], default='audit')
    args = parser.parse_args()
    if not args.output_name.replace('-', '').replace('_', '').isalnum():
        parser.error('output-name must be a simple directory name')
    prepare(args.platform, args.output_name, args.mode)
