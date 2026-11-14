"""Record the current installed release only after existing audits have passed."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ACTOR = ROOT / 'src/cocos/assets/resources/flat2d/characters/raphael'
DEPLOY = ROOT / 'src/cocos/temp/character-identity-build-project/deployment-report.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


manifest = read(ACTOR / 'manifest.json')
pack = read(HERE / 'pack-report.json')
inventory = read(HERE / 'inventory.json')
contract = read(HERE / 'playback-contract-before.json')
audit = read(HERE / 'runtime-audit.json')
deployment = read(DEPLOY)
motion = read(HERE / 'test-results/flat2d-browser-motion.json')
reference = read(HERE / 'reference-lock-report.json')
manifest_sha = sha(ACTOR / 'manifest.json')

assert pack['status'] == 'installed'
assert manifest_sha == pack['installedManifestSHA256'] == deployment['sourceManifestSHA256']
assert manifest_sha == audit['manifestHashes']['source']
assert audit['manifestMatches'] and audit['coverageMatches']
assert not audit['errors'] and not audit['poses']['mismatches'] and not motion['errors']
assert len(audit['textures']) == 69 and all(r['matches'] for r in audit['textures'])
assert manifest['directions'] == contract['directions']
assert set(manifest['actions']) == set(contract['actions'])
for action, fields in contract['actions'].items():
    assert all(manifest['actions'][action].get(k) == value for k, value in fields.items()), action
assert sha(ACTOR / 'manifest.json.meta') == inventory['manifestMetaSHA256']
for row in inventory['images']:
    assert sha(ACTOR / (row['image'] + '.meta')) == row['metaSHA256']
for row in pack['images']:
    assert sha(ACTOR / row['image']) == row['afterSHA256']
assert manifest['attackIdentityPacking']['artApprovalReportSHA256'] == sha(HERE / 'art-acceptance.json')
assert reference['pinnedFrames'] == 64 and reference['physicalFrames'] == 996
maximum = max(max(row['size']) for row in pack['images'])
assert maximum <= 2048
assert deployment['status'] == 'deployed'
assert deployment['deployedTreeMatchesBuiltHashes']
assert deployment['snapshotOriginalFilesUnchangedAfterDeployment']

report = dict(
    status='passed', date='2026-11-08', revision=manifest['revision'],
    actions=len(manifest['actions']), atlases=len(pack['images']), physicalFrames=pack['physicalFrames'],
    runtimeSamples=audit['poses']['phaseSamples'], runtimeCaptures=len(audit['captures']),
    runtimeErrors=audit['errors'], runtimeMismatches=audit['poses']['mismatches'],
    manifestSHA256=manifest_sha, allRuntimeTextureBytesMatch=True,
    all70ActorMetadataFilesUnchanged=True, timingDirectionEquipmentImageContractUnchanged=True,
    maximumAtlasSide=maximum, immutableReferenceFrames=64,
    localArtAcceptanceSHA256=sha(HERE / 'art-acceptance.json'),
    referenceLockReportSHA256=sha(HERE / 'reference-lock-report.json'),
    runtimeAuditSHA256=sha(HERE / 'runtime-audit.json'),
    buildDeploymentReport=str(DEPLOY), buildDeploymentReportSHA256=sha(DEPLOY),
    buildMethod='isolated Cocos 3.8.8 project snapshot; original project configuration untouched',
    normalInputCapture='test-results/flat2d-browser-motion.json',
    normalInputChecks=[r['name'] for r in motion['reports']],
    normalInputErrors=motion['errors'],
    generationMode='built-in cloud OpenAI image_gen; two edits, reviewed partial compositing; no local model inference or downloads',
    extraOriginalAtlasBackups=False,
    retiredCompiledCache='src/cocos/build/concept-2d-character-identity-retired retained; older unreferenced compiled files may remain',
)
(HERE / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
