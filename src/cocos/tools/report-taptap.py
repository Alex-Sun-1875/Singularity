"""Measure a real converted TapTap build, separating main payload from subpackages."""
import argparse
import hashlib
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

PROJECT = Path(__file__).resolve().parents[1]


def verify_selective_routes(game, packages):
    """Every generated logical route must resolve in its real exported bundle."""
    text = (PROJECT / 'assets/scripts/shared/assets/ResourcePacks.ts').read_text(encoding='utf-8')
    match = re.search(r'RESOURCE_ASSET_PACKS:[^=]+?=\s*(\{.*\});', text, re.S)
    routes = json.loads(match.group(1)) if match else {}
    roots = {p['name']: game / p['root'] for p in packages}
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    exported = {}
    counts = {}
    for logical, route in routes.items():
        name, asset_uuid = route['bundle'], route['uuid']
        if name not in exported:
            if name not in roots:
                raise SystemExit('Selective subpackage missing: ' + name)
            config = next(roots[name].glob('config*.json'), None)
            if not config:
                raise SystemExit('Selective bundle config missing: ' + name)
            exported[name] = set(json.loads(config.read_text(encoding='utf-8'))['uuids'])
        base, separator, sub = asset_uuid.partition('@')
        value = base.replace('-', '')
        compact = value[:2] + ''.join(alphabet[int(value[i:i+3], 16) >> 6] +
                                      alphabet[int(value[i:i+3], 16) & 63]
                                      for i in range(2, 32, 3))
        if separator:
            compact += '@' + sub
        if asset_uuid not in exported[name] and compact not in exported[name]:
            raise SystemExit('Selective asset was not exported: ' + name + '/' + logical)
        counts[name] = counts.get(name, 0) + 1
    return {'checkedRoutes': len(routes), 'bundles': counts}


def inspect_wasm(game, packages, enabled, all_files):
    """Check the Cocos transport split; never infer platform function splitting."""
    pack_names = {'__ccWasmAssetSubpkg__', '__ccWasmChunkSubpkg__'}
    transport = [p for p in packages if p['name'] in pack_names]
    modules = []
    for path in all_files:
        if not path.name.endswith(('.wasm', '.wasm.br', '.wasm.gz')):
            continue
        relative = path.relative_to(game).as_posix()
        owner = next((p['name'] for p in packages
                      if path.is_relative_to(game / p['root'])), None)
        if path.suffix == '.wasm':
            with path.open('rb') as stream:
                if stream.read(8) != b'\x00asm\x01\x00\x00\x00':
                    raise SystemExit('Invalid WASM module header: ' + relative)
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        modules.append({'path': relative, 'bytes': path.stat().st_size,
                        'sha256': digest, 'subpackage': owner})
    if enabled and modules:
        if {p['name'] for p in transport} != pack_names:
            raise SystemExit('Cocos engine WASM splitting is enabled but its two subpackages are missing')
        if any(m['subpackage'] != '__ccWasmAssetSubpkg__' for m in modules):
            raise SystemExit('Engine WASM was left outside its declared asset subpackage')
        # Check the generated engine actually references both package names;
        # declaring directories alone does not connect them to its loader.
        engines = [p.read_text(encoding='utf-8') for p in (game / 'cocos-js').glob('cc*.js')]
        if not any(all(name in source for name in pack_names) and 'loadSubpackage' in source
                   for source in engines):
            raise SystemExit('Missing Cocos WASM subpackage loader in the exported engine')
    return {'engineTransport': {
                'requested': enabled,
                'localValidationPassed': bool(enabled and modules and transport),
                'packages': transport, 'modules': modules,
                'wasmBytes': sum(m['bytes'] for m in modules),
                'wasmBytesInMainPackage': sum(m['bytes'] for m in modules if m['subpackage'] is None),
                'note': 'Whole engine modules are packaged separately. They can still be required during startup.'},
            'platformFunctionSplit': {
                'verified': False,
                'status': 'requires-compatible-sdk-export-and-console-collection',
                'note': 'The installed Cocos converter exports game.zip, not the documented game_wasm_split.zip. Cocos transport packs do not prove platform function splitting.',
                'guide': 'https://developer.taptap.cn/minigameapidoc/dev/tutorial/performance/launch/wasm-subpackage/'}}


def measure(root, output, browser_report=None):
    root = root.resolve()
    game = root / 'game'
    config = json.loads((game / 'game.json').read_text(encoding='utf-8'))
    identity = json.loads((root / 'identity.json').read_text(encoding='utf-8'))
    plan = json.loads((PROJECT / 'temp/taptap-resource-plan.json').read_text(encoding='utf-8'))
    release = plan['release']
    for required in ('game.js', 'game.json', 'project.config.json', 'release-info.json', 'BUILD_README.txt'):
        if not (game / required).is_file():
            raise SystemExit('Missing game entry/configuration: ' + required)
    project_config = json.loads((game / 'project.config.json').read_text(encoding='utf-8'))
    build_info = json.loads((game / 'release-info.json').read_text(encoding='utf-8'))
    profile = release['buildProfile']
    if build_info.get('buildProfile') != profile or identity.get('buildProfile') != profile:
        raise SystemExit('Compiled gameplay profile and build manifest differ')
    profile_name = profile['name']
    if profile_name not in ('dev', 'test', 'release'):
        raise SystemExit('Unknown gameplay profile')
    markers = set()
    for script in game.rglob('*.js'):
        markers.update(re.findall(r'singularity-build-profile-v\d+-(?:dev|test|release)(?:-[a-f0-9]{12})?', script.read_text(encoding='utf-8')))
    if markers != {profile['marker']}:
        raise SystemExit('Package contains missing or mixed compiled gameplay profiles')
    release_notes = build_info.get('releaseNotes')
    if identity.get('releaseNotes') != release_notes:
        raise SystemExit('Release notes identity drift')
    if profile_name == 'release':
        if not release_notes or identity['buildMode'] != 'release':
            raise SystemExit('Release package must include its release update log')
        for filename, digest_key in (('RELEASE_NOTES.md', 'notesSha256'), ('source-manifest.json', 'sourceManifestSha256'), ('release-changes.json', 'changesSha256')):
            file = game / filename
            if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != release_notes[digest_key]:
                raise SystemExit('Release metadata is missing or corrupt: ' + filename)
        source_manifest = json.loads((game / 'source-manifest.json').read_text(encoding='utf-8'))
        if source_manifest.get('version') != release['version'] or source_manifest.get('profile') != 'release':
            raise SystemExit('Release source manifest does not match this package')
    elif release_notes or any((game / name).exists() for name in ('RELEASE_NOTES.md', 'source-manifest.json', 'release-changes.json')):
        raise SystemExit('Non-release package contains stale release metadata')
    guest_test = identity['buildMode'] == 'guest-test'
    login_mode = 'guest' if guest_test else 'platform'
    if build_info.get('loginMode') != login_mode or identity.get('login', {}).get('mode') != login_mode:
        raise SystemExit('Package login mode does not match its build identity')
    if (build_info.get('loginProvider') != 'taptap-minigame'
            or build_info.get('customAuthService') is not False
            or identity.get('login', {}).get('customAuthService') is not False):
        raise SystemExit('Package must use TapTap platform login without a custom auth service')
    if guest_test and release.get('buildMode') != 'test':
        raise SystemExit('Guest access is allowed only for an explicit test build')
    entry_flags = re.findall(r'globalThis\.__SINGULARITY_GUEST_TEST__\s*=\s*(true|false)\s*;', (game / 'game.js').read_text(encoding='utf-8'))
    if entry_flags != ['true' if guest_test else 'false']:
        raise SystemExit('Native game entry does not match the declared login mode')
    if config.get('productVersion') != release['version'] or build_info['version'] != release['version']:
        raise SystemExit('Package version does not match the build manifest')
    stamp = datetime.fromisoformat(build_info['builtAt'].replace('Z', '+00:00')).strftime('%Y%m%dT%H%M%SZ')
    package_name = f"{release['projectName']}_{release['version']}.zip"
    legacy_name = f"{release['projectName']}_{release['version']}_TapTap_{identity['buildMode']}_{stamp}.zip"
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*_(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\.zip', package_name) or build_info.get('packageFilename') not in (package_name, legacy_name):
        raise SystemExit('Package filename does not match its version/build identity')
    # Legacy ZIP bytes stay immutable when organizing an existing version.
    output = output.resolve() / release['version']
    if build_info.get('projectName') != release['projectName'] or build_info.get('buildMode') != identity['buildMode']:
        raise SystemExit('Package English name/build mode drift')
    if config.get('productName') != release['title'] or config.get('deviceOrientation') != release['orientation'] or config.get('networkTimeout') != release['networkTimeout']:
        raise SystemExit('Game title, orientation or network timeout drift')
    expected_id = None if identity['identity'] == 'unbound-local-audit' else release['miniAppId']
    if project_config.get('appid') != expected_id or build_info.get('miniAppId') != expected_id:
        raise SystemExit('Package MiniApp ID mismatch')
    if 'subpackages' in config:
        raise SystemExit('TapTap requires camelCase subPackages')
    packages = config.get('subPackages', [])
    if not packages or len({p['name'] for p in packages}) != len(packages):
        raise SystemExit('Missing or duplicate subpackage names')
    all_files = sorted(p for p in game.rglob('*') if p.is_file())
    main_files = list(all_files)
    output.mkdir(parents=True, exist_ok=True)
    report_packs = []
    package_directories = []
    for pack in packages:
        relative = PurePosixPath(pack['root'])
        if relative.is_absolute() or '..' in relative.parts:
            raise SystemExit('Invalid subpackage root: ' + str(relative))
        directory = game.joinpath(*relative.parts).resolve()
        if not directory.is_relative_to(game.resolve()) or not directory.is_dir():
            raise SystemExit('Missing subpackage ' + pack['name'])
        if not (directory / 'game.js').is_file():
            raise SystemExit('Missing Cocos subpackage game.js: ' + pack['name'])
        if any(directory.is_relative_to(other) or other.is_relative_to(directory) for other in package_directories):
            raise SystemExit('Duplicate or nested subpackage root: ' + pack['name'])
        package_directories.append(directory)
        files = [p for p in all_files if p.is_relative_to(directory)]
        if not files:
            raise SystemExit('Empty subpackage: ' + pack['name'])
        members = set(files)
        main_files = [p for p in main_files if p not in members]
        report_packs.append({'name': pack['name'], 'root': str(relative), 'files': len(files),
                             'rawBytes': sum(p.stat().st_size for p in files)})
    selective_validation = verify_selective_routes(game, packages)
    first_zip = output / 'checks/initial.zip'
    first_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(first_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for p in main_files:
            archive.write(p, p.relative_to(game).as_posix())
    with zipfile.ZipFile(first_zip) as archive:
        if archive.testzip():
            raise SystemExit('Initial payload ZIP failed CRC')
    upload_zip = root / 'game.zip'
    with zipfile.ZipFile(upload_zip) as archive:
        if archive.testzip():
            raise SystemExit('Official converter ZIP failed CRC')
        expected = {p.relative_to(game).as_posix() for p in all_files}
        names = [info.filename for info in archive.infolist() if not info.is_dir()]
        if len(names) != len(set(names)) or set(names) != expected:
            raise SystemExit('Official converter ZIP does not match its game directory')
        compressed_files = {info.filename: info.compress_size for info in archive.infolist() if not info.is_dir()}
    for pack in report_packs:
        prefix = pack['root'].rstrip('/') + '/'
        pack['deflatedContentBytes'] = sum(size for name, size in compressed_files.items() if name.startswith(prefix))
    with upload_zip.open('rb') as stream:
        upload_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    expected_packs = {p['name'] for p in plan['packs']} | {p['name'] for p in plan['profile'].get('selectivePacks', [])}
    actual_packs = {p['name'] for p in report_packs}
    # Cocos also emits built-in resources, WASM packs and tiny wrappers for
    # disabled comparison bundles. Keep them visible in the accounting.
    allowed_extra = {'resources', '__ccWasmAssetSubpkg__', '__ccWasmChunkSubpkg__'}
    allowed_extra |= {p['name'] for p in plan['bundles'] if not p.get('output', True)}
    if expected_packs - actual_packs or actual_packs - expected_packs - allowed_extra:
        raise SystemExit('Resource split not applied: missing=' + str(expected_packs-actual_packs)
                         + ', unexpected=' + str(actual_packs-expected_packs-allowed_extra))
    # Validate Cocos' generated dependency graph, rather than hand-coding cross-package require paths.
    manifests = {}
    for filename in list((game / 'assets').glob('*/config*.json')) + list((game / 'subpackages').glob('*/config*.json')):
        manifest = json.loads(filename.read_text(encoding='utf-8'))
        if 'name' in manifest:
            manifests[manifest['name']] = manifest.get('deps', [])
    for name, deps in manifests.items():
        if any(dep not in manifests for dep in deps):
            raise SystemExit('Missing Cocos bundle dependency for ' + name)
    def visit(name, chain=()):
        if name in chain:
            raise SystemExit('Cyclic Cocos bundle dependencies: ' + ' -> '.join(chain + (name,)))
        for dep in manifests[name]:
            visit(dep, chain + (name,))
    for name in manifests:
        visit(name)
    settings_files = list((game / 'src').glob('settings*.json'))
    if len(settings_files) != 1:
        raise SystemExit('Expected one Cocos settings manifest')
    settings = json.loads(settings_files[0].read_text(encoding='utf-8'))
    if set(settings['assets'].get('subpackages', [])) - actual_packs:
        raise SystemExit('Cocos subpackage registration is missing from game.json')
    for pack in report_packs:
        pack['dependencies'] = manifests.get(pack['name'], [])
    wasm = inspect_wasm(game, report_packs, plan['profile']['engineWasmSubpackage'], all_files)
    budget = plan['profile']['initialPackageBudgetMiB'] * 1048576
    report = {'measuredAt': datetime.now(timezone.utc).isoformat(),
              'version': release['version'], 'cocosVersion': '3.8.8', 'resourceProfile': 'release/taptap.json',
              'resourceProfileSha256': hashlib.sha256((PROJECT / 'release/taptap.json').read_bytes()).hexdigest(),
              'identity': identity, 'buildDirectory': str(root),
              'initialPayload': {'files': len(main_files),
                  'rawBytes': sum(p.stat().st_size for p in main_files),
                  'zipBytes': first_zip.stat().st_size, 'zipMiB': round(first_zip.stat().st_size/1048576, 2),
                  'budgetMiB': budget/1048576, 'withinLocalBudget': first_zip.stat().st_size <= budget and sum(p.stat().st_size for p in main_files) <= budget,
                  'sha256': hashlib.sha256(first_zip.read_bytes()).hexdigest(),
                  'note': 'Offline ZIP of files outside declared subPackages; platform-delivered first package is not measured.'},
              'total': {'files': len(all_files), 'rawBytes': sum(p.stat().st_size for p in all_files),
                        'uploadZipBytes': upload_zip.stat().st_size,
                        'uploadZipSha256': upload_hash,
                        'uploadZipMiB': round(upload_zip.stat().st_size/1048576, 2),
                        'uploadZipMB': round(upload_zip.stat().st_size/1000000, 2),
                        'consoleObservedLimitBytes': release['uploadZipLimitBytes'],
                        'withinConsoleObservedLimit': upload_zip.stat().st_size < release['uploadZipLimitBytes']},
              'subpackages': sorted(report_packs, key=lambda p: -p['rawBytes']),
              'sourceAssetFilters': {
                  'excludedTrees': plan['profile']['excludedResourceTrees'],
                  'excludedAssets': plan.get('excludedAssets', []),
                  'note': 'Source files are preserved. These build filters are not measured ZIP savings; Cocos still includes required dependencies.'},
              'wasm': wasm,
              'selectiveAssetValidation': selective_validation,
              'limitations': ['No upload or TapTap real-device validation.',
                             'Platform acceptance of the full upload ZIP size is unverified.',
                             'Initial payload excludes on-demand packs required before gameplay.',
                             'Official converter ZIP includes all subpackage directories.']}
    if browser_report:
        browser = json.loads(browser_report.read_text(encoding='utf-8'))
        names = set().union(*(r['startupPacks']['bundles'] for r in browser['reports']))
        names |= {'__ccWasmAssetSubpkg__', '__ccWasmChunkSubpkg__'}
        startup = [p for p in report_packs if p['name'] in names]
        report['openingDependencies'] = {
            'observedIn': 'Web release preview using the same resource profile',
            'bundles': sorted(p['name'] for p in startup),
            'rawBytesIncludingInitialPayload': report['initialPayload']['rawBytes'] + sum(p['rawBytes'] for p in startup),
            'deflatedContentBytesIncludingInitialZip': report['initialPayload']['zipBytes'] + sum(p['deflatedContentBytes'] for p in startup),
            'webColdStartTransferBytes': [r['startupBytes'] for r in browser['reports']],
            'note': 'Whole declared packs plus both generated WASM packs; not a measurement of TapTap network traffic or loading time.'}
    checks_passed = report['initialPayload']['withinLocalBudget'] and report['total']['withinConsoleObservedLimit']
    build_mode = identity.get('buildMode', release.get('buildMode', 'audit' if expected_id is None else 'release'))
    delivery = output.resolve()
    delivered_zip = delivery / package_name
    upload_settings = {'version': release['version'], 'title': release['title'], 'miniAppId': release['miniAppId'],
        'buildMode': build_mode, 'buildProfile': profile, 'releaseNotes': release_notes,
        'purpose': 'upload-guest-test' if guest_test else 'upload-test' if build_mode == 'test' else build_mode,
        'loginMode': login_mode, 'localSaveOnly': True,
        'projectName': release['projectName'], 'builtAt': build_info['builtAt'],
        'packageIdentity': identity['identity'], 'packageFilename': str(delivered_zip),
        'converterPackageFilename': str(upload_zip),
        'sourcePackageFilename': build_info['packageFilename'],
        'packageSha256': upload_hash, 'uploadZipBytes': upload_zip.stat().st_size,
        'minimumBaseLibraryVersion': release['minimumBaseLibraryVersion'],
        'minimumBaseLibraryAction': 'Confirm the platform-parsed minimum library version after uploading; not the WeChat libVersion field.',
        'orientation': release['orientation'], 'subpackageCount': len(packages), 'contentPackCount': len(expected_packs),
        'storeArtwork': release.get('branding'),
        'cocosWasmTransportPacks': sorted(actual_packs & {'__ccWasmAssetSubpkg__', '__ccWasmChunkSubpkg__'}),
        'platformWasmFunctionSplitVerified': False,
        'wasm': wasm,
        'loginProvider': 'taptap-minigame', 'customAuthService': False,
        'identityExchange': False, 'accountScopedLocalSave': False,
        'localBlockers': release['localBlockers'],
        'consoleChecks': release['consoleChecks'], 'packageAuditPassed': checks_passed,
        'localConfigurationReady': checks_passed and expected_id is not None and not release['localBlockers'],
        'releasePreflightPassed': build_mode == 'release' and checks_passed and expected_id is not None and not release['localBlockers'],
        'platformVerified': False, 'uploaded': False}
    report['releaseInfo'] = build_info
    report['deliveryDirectory'] = str(delivery)
    (output / 'upload-settings.json').write_text(json.dumps(upload_settings, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('initialPayload', 'total')}, ensure_ascii=False, indent=2))
    if not checks_passed:
        raise SystemExit('Package exceeds the internal initial-payload budget or the console-observed upload ZIP limit; see report.json')
    delivery.mkdir(parents=True, exist_ok=True)
    if delivered_zip.exists():
        with delivered_zip.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != upload_hash:
                raise SystemExit('Refusing to overwrite a different package with the same name: ' + str(delivered_zip))
    else:
        shutil.copyfile(upload_zip, delivered_zip)
    with delivered_zip.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != upload_hash:
            raise SystemExit('Exported ZIP checksum mismatch')
    (delivery / (package_name + '.sha256')).write_text(upload_hash + '  ' + package_name + '\n', encoding='ascii')
    if profile_name == 'release':
        for name in ('RELEASE_NOTES.md', 'source-manifest.json', 'release-changes.json'):
            shutil.copyfile(game / name, delivery / name)
        archive = PROJECT.parents[1] / 'docs/releases' / (release['version'] + '.md')
        archive.parent.mkdir(parents=True, exist_ok=True)
        text = (game / 'RELEASE_NOTES.md').read_bytes()
        if archive.exists() and archive.read_bytes() != text:
            raise SystemExit('Refusing to overwrite a different archived release log: ' + str(archive))
        archive.write_bytes(text)
    notes = (game / 'BUILD_README.txt').read_text(encoding='utf-8') + '\n' + '\n'.join([
        f"完整 ZIP：{upload_zip.stat().st_size:,} 字节 / {report['total']['uploadZipMB']} MB",
        f"主包文件：{report['initialPayload']['rawBytes']:,} 字节；本地压缩测量：{report['initialPayload']['zipMiB']} MiB。",
        f"分包数量：{len(packages)}；完整 ZIP 已包含所有分包。",
        '可玩前资源量尚未在本次 TapTap 真机启动中测量；主包大小不代表全部启动下载量。',
        '仅上传本目录的游戏 ZIP；.sha256、report.json 和 upload-settings.json 供核对留档。',
        'SHA-256：' + upload_hash, '',
    ])
    (delivery / 'BUILD_README.txt').write_text(notes, encoding='utf-8')
    print('Named upload package: ' + str(delivered_zip))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('--output', type=Path, default=PROJECT.parent / 'out', help='Output root; files are grouped under <version>/')
    parser.add_argument('--browser-report', type=Path)
    args = parser.parse_args()
    measure(args.build, args.output, args.browser_report)
