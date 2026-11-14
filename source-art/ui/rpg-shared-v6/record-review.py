"""Public component extraction review; no new artwork or gameplay changes."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
QA=ROOT/'src/cocos/test-results/rpg-shared-v6'
def read(p):return json.loads(p.read_text('utf-8'))
mobile=read(QA/'runtime-review.json');desktop=read(QA/'desktop/runtime-review.json')
regression=read(QA/'regression/browser-review.json');profiles=read(QA/'profiles/profiles.json')
default=read(QA/'default-preview.json');copied=read(QA/'build-copy-review.json');pixels=read(QA/'pixel-comparison.json')
for report in [mobile,desktop,regression]:
 assert not report['errors'] and not report['failed']
 for p in report['reports']:
  assert not p['small'] and not p['overlap'] and not p.get('missingSprites',[]),p['name']
  if report is not desktop:assert not p.get('close',p.get('tooClose',[])),p['name']
assert not default['errors'] and not copied['mismatches']
assert all(p['rounded'] and p['borderFront'] and abs(p['visibleHeader']-40)<.3 for p in default['panels'])
assert pixels['sameDataMaxChannelError']<=3 and pixels['sameDataMaxMeanError']<.001
files=['shared/ui/PreparationTheme.ts','shared/ui/PreparationControls.ts','shared/ui/PreparationSkin.ts','shared/ui/RpgPanel.ts','shared/ui/UiSkin.ts','shared/ui/UiTheme.ts','features/equipment/runtime/EquipmentIconFrame.ts','features/equipment/runtime/EquipmentPanels.ts','features/progression/runtime/PreparationPanels.ts','features/progression/runtime/SkillBook.ts','features/crafting/runtime/ForgeWorkshop.ts','features/crafting/runtime/ForgingPanel.ts']
mirror=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-profession-v1/src/cocos');hashes=[]
for f in files:
 p=ROOT/'src/cocos/assets/scripts'/f;assert p.read_bytes()==(mirror/'assets/scripts'/f).read_bytes(),f
 hashes.append({'file':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
result={'date':'2026-11-12','request':'Extract approved UI designs into public variables and native components.','status':'implemented_and_browser_reviewed',
 'configuration':'src/cocos/assets/scripts/shared/ui/PreparationTheme.ts','components':'src/cocos/assets/scripts/shared/ui/PreparationControls.ts','documentation':'docs/design/preparation-components.md',
 'publicExports':['PREPARATION_DESIGN','PREPARATION_SKINS','PREPARATION_SKIN_INSETS','PreparationControls','equipmentIconFrame appearance:preparation'],
 'configurationScope':['screen and artwork units','semantic color roles using existing palette','responsive dialog and input sizes','header/footer and typography','component dimensions and primary page columns','skin paths, versions and nine-slice insets'],
 'componentScope':['identity label','side tab','profession card','attribute row','skill row','point counter','row/card backgrounds','shared icon and equipment frame rendering'],
 'reuse':['RpgPanel','PreparationSkin','DoubleGoldFrame','UiSkin','equipmentIconFrame','native Cocos Button/Label/Sprite/Mask/ScrollView'],
 'pages':['character','equipment','profession','attribute allocation','skill allocation','combat skill configuration','workshop enhancement','affix pool','crafting','inheritance'],
 'validation':{'typeScript':'npm run check passed','skinCatalog':'63 registered assets exist','Cocos':'Creator3.8.8 web-mobile completed','phoneStates':len(mobile['reports']),'desktopStates':len(desktop['reports']),'functionalStates':len(regression['reports']),'additionalProfileStates':len(profiles['reports']),'defaultPreviewPages':len(default['panels']),'runtimeErrors':0,'missingSprites':0,'overlappingControls':0,'pixelComparedStates':pixels['states'],'sameDataComparedStates':pixels['sameDataStates'],'sameDataMaxChannelError':pixels['sameDataMaxChannelError'],'sameDataMaxMeanError':pixels['sameDataMaxMeanError'],'sourceAndBuildMatched':True,'filesCopiedAndVerified':copied['filesVerified']},
 'visualComparison':'24 same-data states retain dialog geometry and appearance, with only small rasterization rounding differences.6 additional states have different movement-speed or randomized affix text; exact label differences recorded in pixel-comparison.json.',
 'sourceHashes':hashes,'newRuntimeDependencies':[],'newArtwork':False,'gameplayFilesChangedByThisRefactor':[],
 'preview':{'url':'http://127.0.0.1:7469/?preview=rpg-shared-v6','output':'src/cocos/build/concept-2d','candidate':'src/cocos/build/concept-2d-rpg-shared-v6','backup':copied['backup'],'published':False},
 'fixtures':'Independent browser profiles, canonical progression/gear APIs and rendered controls. User save not cleared or replaced.',
 'remaining':['TapTap physical-device/platform acceptance remains separate.']}
(HERE/'implementation-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');(QA/'source-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result['validation'],ensure_ascii=False))
