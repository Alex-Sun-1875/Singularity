import {viewportMetrics,retainViewportMetrics} from '../platform/ViewportMetrics';
import {skillWeaponRequirement} from '../features/combat/common/SkillWeapons';
import {updateJourneyCooldowns} from '../features/journey/runtime/JourneyPanel';
import {journeyText as lifecycleText} from '../features/journey/locales';
import {BUILD_INFO} from './BuildInfo';
import {worldText} from '../features/world/locales';
import {CAMPAIGN_EVENTS} from '../features/campaign/data/CampaignEvents';
import {campaignPrerequisiteTargets} from '../features/campaign/common/CampaignNavigation';
import {PreparationResources} from './PreparationResources';
import {currentLocale,LOCALE_PREFERENCE,setLocale} from '../shared/i18n/Localization';
import {_decorator,Component,Node,Camera,Vec3,Vec4,Quat,Color,DirectionalLight,PhysicsSystem,CapsuleCharacterController,input,Input,EventKeyboard,KeyCode,EventMouse,EventTouch,UITransform,Layers,view,AudioSource,AudioClip,director,Director,Material,tween,Tween,sys,SpriteFrame,Texture2D,Rect,Size,JsonAsset,dynamicAtlasManager} from 'cc';
import {DEV} from 'cc/env';
import {gameResources as resources,isTapRelease} from '../shared/assets/GameResources';
import type {GameEvent,InputFrame,InteractionDef,ExitDef,Point,WorldQuery} from '../core/Contracts';
import {GameSession,type GroundLoot} from '../core/GameSession';
import {Automation,type AutomationPause,type NavigationTarget} from '../features/automation/common/Automation';
import {automationText as autoText} from '../features/automation/locales';
import {journeyGuidance,resetJourneyGuidance,navigationGuidance} from '../features/journey/common/JourneyGuide';
import {TaskPresence} from '../features/journey/runtime/TaskPresence';
import {JOURNEY_TASKS,chapterForArea} from '../features/journey/data/ChapterJourney';
import {SceneInteraction,type SceneInteractionTarget} from '../features/world/runtime/SceneInteraction';
import {EquipmentArt} from '../features/equipment/runtime/EquipmentArt';
import {GroundLootPresentation} from '../features/equipment/runtime/GroundLootPresentation';
import {SUPPLIES,isSupplyId} from '../features/equipment/data/Supplies';
import {CombatImpactFeedback} from '../features/combat/runtime/CombatImpactFeedback';
import {eventFeedbackRole,qualityFeedbackRole,type FeedbackRole} from '../shared/ui/FeedbackPalette';
import {SaveStore} from '../features/persistence/common/SaveStore';
import {AutoSavePolicy} from '../features/persistence/common/AutoSavePolicy';
import {discardCombatSkillPreview} from '../features/progression/runtime/CombatPanel';
import {SkillEffectDebug} from '../features/debug/runtime/SkillEffectDebug';
import {TrainingRange,TRAINING_MONSTER_COUNTS,type TargetFormation} from '../features/debug/common/TrainingRange';
import {buildTrainingFloor,renderTrainingRange} from '../features/debug/runtime/TrainingRangeView';
import {trainingText} from '../features/debug/locales';
import {TouchOwnership} from '../shared/input/TouchOwnership';
import {getArea,AREAS} from '../features/world/data/WorldData';
import {EQUIPMENT,equipmentStackLimit} from '../features/equipment/data/Equipment';
import {highlightedEquipment} from '../features/equipment/common/LootFeedback';
import {recordEquipmentChange,recordEquipmentPreparing,beginEquipmentVisit,selectEquipmentCategory,selectEquipmentSocket} from '../features/equipment/runtime/EquipmentPanels';
import {browseCombatFamily} from '../features/progression/runtime/SkillBook';
import {hasPreparationPreview,discardPreparationPreview,beginAllocation,browseAllocationFamily,resetAllocationPreview,chooseProfession,professionPreview,professionBusy} from '../features/progression/runtime/PreparationPanels';
import {preparationText as pt} from '../features/progression/locales';
import {prepareCombatLoadout,type CombatFamily} from '../features/progression/common/CombatLoadouts';
import {equipmentText,equipmentChangeReason} from '../features/equipment/locales';
import {SceneBuilder} from '../features/world/runtime/SceneBuilder';
import {MapResources} from '../features/world/runtime/MapResources';
import {Actors} from '../features/actors/runtime/Actors';
import {FlatActors} from '../features/actors/runtime/FlatActors';
import {Player3DActors} from '../features/actors/runtime/Player3DActors';
import {FlatWorldPresentation} from '../features/world/runtime/FlatWorldPresentation';
import {PortalHud} from '../features/portals/runtime/PortalHud';
import {PortalPresentation} from '../features/portals/runtime/PortalPresentation';
import {Effects,type AttackRangePreview} from '../features/combat/runtime/Effects';
import {PlatformServices} from '../platform/PlatformServices';
import {BackgroundMusic} from '../features/audio/runtime/BackgroundMusic';
import {Hud} from './Hud';
import {UiSkin} from '../shared/ui/UiSkin';
import {HAIRSTYLE_PORTRAITS} from '../features/actors/runtime/Hairstyles';
import {renderMenu} from './Menus';
import {CheckpointCompass} from '../features/navigation/runtime/CheckpointCompass';
import {loadBundleWithDependencies} from '../shared/assets/AssetBundles';
import {DicePanel} from '../features/dice/runtime/DicePanel';
import {SurfaceMaterials} from '../features/world/runtime/SurfaceMaterials';
import {navigationText as mapText} from '../features/navigation/locales';
import {LoadingScreen} from '../features/loading/runtime/LoadingScreen';
import {showLoginScreen} from '../features/login/runtime/LoginScreen';
import {LocalCartography} from '../features/navigation/runtime/LocalCartography';
import {prepareNavigationWasm,setComputationWasmEnabled,navigationWasmState} from '../features/navigation/runtime/NavigationWasm';
import {Navigation} from '../features/navigation/runtime/Navigation';
import {COMBAT_RULES,COMBAT_SKILLS} from '../features/combat/data/PureSkills';
import {resourceProfile} from '../features/combat/common/ClassResource';
import {ATTRIBUTES,baseMaxHp,cumulativeXp,allocatedSkillRank,unlockSkills,skillRankSpent,type Attribute} from '../features/progression/common/Progression';
import {skillFramingPoints,rangedCameraFrame} from '../features/navigation/runtime/RangedCamera';
import {nearestBoss,bossKind,bossName} from '../features/combat/common/BossAwareness';
import {BossDirectory} from '../features/combat/common/BossDirectory';
import {BossPanel} from '../features/combat/runtime/BossPanel';
import {bossText} from '../features/combat/locales/bosses';
import {EnemyCombatFeedback} from '../features/combat/runtime/EnemyCombatFeedback';
import {CampaignPresentation} from '../features/cinematics/runtime/CampaignPresentation';
import type {CampaignBeat} from '../features/cinematics/data/CampaignScenes';
const {ccclass}=_decorator;
const distance=(a:Point,b:Point)=>Math.hypot(a.x-b.x,a.z-b.z);
// Keep ordinary exploration comfortable; slow walking retains its own pace.
// Both manual input and automation pass through the session's movement speed.
const MODEL_RUN_SPEED=5.0,MODEL_WALK_SPEED=2.0;
@ccclass('ChapterGame')
export class ChapterGame extends Component {
 session:GameSession;store:SaveStore;platform:PlatformServices;world:SceneBuilder;actors:Actors|FlatActors|Player3DActors;effects:Effects;hud:Hud;dicePanel:DicePanel;camera:Camera;capsule:CapsuleCharacterController;
 private readonly flatMode=isTapRelease||(typeof location!=='undefined'&&new URLSearchParams(location.search).get('view')==='2d');
 // The painted world uses the native 3D hero by default; sprite comparison is explicit.
 private readonly modelPlayer=this.flatMode&&(isTapRelease||new URLSearchParams(location.search).get('player')!=='2d');
 // The local-only profile lives in memory. Its expanded attribute budget must
 // never enter SaveStore or relax the normal progression validator.
 private readonly temporaryMax=DEV&&!isTapRelease&&typeof location!=='undefined'&&['127.0.0.1','localhost','[::1]'].includes(location.hostname)&&new URLSearchParams(location.search).get('test')==='max';
 private readonly skillEffectDebug=new SkillEffectDebug();
 private trainingRange:TrainingRange|undefined;
 private rangeReturn:{session:GameSession;menu:string;saved:string;taskId:string|undefined}|undefined;
 private get skillDebugAvailable(){return this.temporaryMax||!!this.trainingRange;}
 private portalHud:PortalHud|undefined;private flatWorld:FlatWorldPresentation|undefined;private nativePortals:PortalPresentation|undefined;private flatPortrait:SpriteFrame|undefined;private flatHead:SpriteFrame|undefined;
 private hairstyleHeads=new Map<string,SpriteFrame>();
 private hairstyleHeadOwner:Node|undefined;private hairstyleHeadRevision=0;
 private loadingScreen:LoadingScreen;private diceKeys=new Set<number>();private keyLight:DirectionalLight;
 private music:BackgroundMusic|undefined;
 private campaignView:CampaignPresentation|undefined;
 // Long-lived presenters share callbacks created outside rebuild's async scope.
 // Otherwise their closures can keep previous presenters and whole maps alive.
 private readonly campaignFinished=(id:string)=>{this.session.campaign.finish(id);this.clearInput(false);this.automation.resumeAfter('story');this.save();if(id==='highland-victory'&&this.session.state.flags['journey:preview-complete'])this.open('journey-finish');};
 private readonly campaignSound=(cue:string)=>this.play(cue==='bells'?'bells':cue==='alarm'?'complete':cue==='command'?'spell':'interact');
 private readonly campaignArmy=(beat:CampaignBeat|undefined,time:number)=>{if(this.actors instanceof FlatActors||this.actors instanceof Player3DActors)this.actors.presentCampaign(beat,time,this.session);};
 private readonly presentationSource=()=>this.actors.playerPresentation();
 private readonly enemyHead=(id:string)=>(this.actors as {enemyHeadPoint?:(id:string)=>Vec3|undefined})?.enemyHeadPoint?.(id);
 private readonly sceneInteract=(id:string)=>this.click('interact:'+id);
 private readonly impactSound=(id:string,volume:number)=>{const clip=this.sounds.get(id);if(clip)this.audio.playOneShot(clip,volume);};
 private keys=new Set<number>();private touches=new TouchOwnership();private heldAttack=false;private mouseAim:number|undefined;private pulse:Partial<InputFrame>={};
 private automation=new Automation();
 private readonly bosses=new BossDirectory(AREAS);
 private bossPanel:BossPanel|undefined;
 private bossPanelClock=0;
 private bossTravel:NavigationTarget|null=null;
 private bossTravelArea='';
 private automationDismissedTouch=false;
 private aiming:string|null=null;private aimTarget:Point|undefined;private compass=new CheckpointCompass(AREAS);private compassText='';private compassTime=0;private encounterTime=.2;private encounterText='';private menu='title';private modalKey='';private loading=false;private failure='';private saved='';private readonly autosave=new AutoSavePolicy();private toastRole:FeedbackRole='text.normal';private toast='';private toastTime=0;private page=0;private merchant='';private visited:Record<string,boolean>={};private cleanup:()=>void;private audio:AudioSource;private sounds=new Map<string,AudioClip>();private lastAimTime=-999;
 private manualSkillAim=false;
 private manualBasicAim=false;
 private aimGesture:{id:number;start:Point;anchor:Point;right:Point;up:Point;scale:number;manual:boolean}|null=null;
 private skillPress:{id:number;control:string;start:Point;elapsed:number;dragged:boolean;inspecting:boolean;usable:boolean}|null=null;
 private combatFocus:{target:Point;skillId:string;rank:number;until:number}|null=null;
 private manualCameraHeight=4.4;private lastCombatSound=-1;
 private readonly followCameraRotation=new Quat();private readonly followCameraPosition=new Vec3();
 private enemyFeedback:EnemyCombatFeedback|undefined;
 private impact:CombatImpactFeedback|undefined;
 private guideTime=0;private guideArea='';private trackedTaskId:string|undefined;private sceneInteraction:SceneInteraction|undefined;
 private groundLootView:GroundLootPresentation|undefined;
 private readonly mapResources=new MapResources();
 private preparationResources:PreparationResources;private preparingPage=false;private pagePreparationRevision=0;
 private taskPresence:TaskPresence|undefined;
 private authPromptVisible=false;
 private bootPrepared=false;private startupFailure=false;private destroyed=false;private bootPromise:Promise<void>|undefined;private accessPromise:Promise<void>|undefined;
 private background=false;private resetFrameTime=false;private resumeSavedJourney=false;private returnToMainMenu=false;
 private pendingPreparationAction:string|undefined;
 private query:WorldQuery={move:(p,d,r)=>this.moveCharacter(p,d,r),visible:(a,b)=>this.world?this.world.visible(a,b):true,height:p=>this.world?.height(p)??0,path:(a,b)=>this.world?.path(a,b)??[],recoverPosition:(p,r)=>this.world?.recoverPosition(p,r),inView:p=>this.reinforcementInView(p)};
 private reinforcementInView(point:Point){
  if(!this.camera||!this.world)return false;
  const size=viewportMetrics.windowSize,y=this.world.height(point);
  // Check feet and head with a margin for names, the minimap and touch controls.
  for(const height of [.1,2.2]){const p=this.camera.worldToScreen(new Vec3(point.x,y+height,point.z));if(p.z<0||p.z>1||p.x<size.width*.06||p.x>size.width*.94||p.y<size.height*.14||p.y>size.height*.86)return false;}
  return true;
 }
 private moveCharacter(p:Point,d:Point,r:number):Point {
  if(!this.world||d.x===0&&d.z===0)return p;const target=this.world.move(p,d,r),controller=this.capsule;
  if(p!==this.session?.state.player||!controller?.isValid)return target;
  // Rules substep the footprint first; Bullet then resolves the actual capsule
  // against the scene's solid geometry and terrain before rules accept position.
  PhysicsSystem.instance.syncSceneToPhysics();controller.centerWorldPosition=new Vec3(p.x,this.world.height(p)+.93,p.z);
  controller.move(new Vec3(target.x-p.x,this.world.height(target)-this.world.height(p)-.02,target.z-p.z));
  const actual=controller.node.position;return {x:actual.x,z:actual.z};
 }
 private previousPhysicsAutoSimulation:boolean|undefined;
 private equipmentPreparing=false;
 private viewportCleanup:(()=>void)|undefined;
 async start(){
  this.viewportCleanup=retainViewportMetrics();
  void prepareNavigationWasm();
  // Pack original pixels at 1:1; this changes empty atlas capacity, not art size.
  if(dynamicAtlasManager.atlasCount===0)dynamicAtlasManager.textureSize=1280;
  const scene=director.getScene()!;
  this.hud=new Hud(scene,{click:a=>this.click(a),touch:(a,p,e)=>this.touch(a,p,e),navigate:target=>this.startNavigation(target)});
  this.preparationResources=new PreparationResources(this.node);
  this.loadingScreen=new LoadingScreen(this.hud);this.dicePanel=new DicePanel(this.hud);
  this.platform=new PlatformServices(()=>{if(!this.platform?.auth.ready||this.updatePromptVisible){this.clearInput(true,'auth');this.campaignView?.suspend();}this.modalKey='';this.renderModal();if(this.platform?.updates.status==='failed')this.say(this.platform.updates.message,8);});
  try{setLocale(this.platform.getItem(LOCALE_PREFERENCE));}catch{/* Story language defaults to Chinese if storage is unavailable. */}
  try{this.hud.reducedMotion=this.platform.getItem('sword-fire-ui-reduced-motion')==='1';}catch{/* Cosmetic preferences cannot prevent boot. */}
  try{this.hud.skillAimMode=this.platform.getItem('sword-fire-skill-aim-mode')==='manual'?'manual':'auto';}catch{/* Use automatic aiming if the preference cannot be read. */}
  this.music=new BackgroundMusic(this.node,this.platform,()=>{this.modalKey='';this.renderModal();});
  this.cleanup=this.platform.lifecycle(()=>this.enterBackground(),()=>this.returnToForeground());
  this.memoryCleanup=this.platform.memoryPressure(warning=>{
   if(this.destroyed)return;
   const device=director.root?.device,record={version:BUILD_INFO.version,area:this.session?.state.area??null,time:Date.now(),level:warning?.level??null,gfxBytes:device?{...device.memoryStatus}:null};
   console.warn('[MemoryPressure]',JSON.stringify(record));
   this.mapResources.trimNeighbors();
   Navigation.resetSearchBackend();
   try{this.platform.setItem('sword-fire-last-memory-warning',JSON.stringify(record));}catch{/* Diagnostics cannot interrupt the journey. */}
   this.save();
  });
  this.renderModal();await this.ensureAccess();
 }
 private enterBackground(){
  if(this.background)return;this.background=true;
  this.music?.setSuspended(true);this.campaignView?.suspend();this.diceKeys.clear();this.clearInput(true,'background');this.hud?.collapseAutomation();this.sceneInteraction?.update(null,true);this.save();
 }
 private returnToForeground(){
  if(!this.background)return;this.background=false;this.resetFrameTime=true;
  this.music?.setSuspended(false);this.diceKeys.clear();this.clearInput();void this.ensureAccess(true);
 }
 private ensureAccess(resume=false):Promise<void>{
  if(this.accessPromise)return this.accessPromise;
  this.accessPromise=(async()=>{
   if(!await this.platform.auth.ensure(resume)||this.destroyed)return;
   if(!this.bootPromise)this.bootPromise=this.bootWorld();
   try{await this.bootPromise;}catch(error){if(!this.destroyed){this.loadingScreen?.hide();this.loading=false;this.failure='旅途资源载入失败，请检查网络后重试。';this.startupFailure=true;this.bootPromise=undefined;console.warn('[Chapter] Startup resource load failed');}}
   if(!this.destroyed){this.modalKey='';this.renderModal();}
  })().finally(()=>{this.accessPromise=undefined;});return this.accessPromise;
 }
 private memoryCleanup:()=>void=()=>{};
 private async bootWorld(){
  this.startupFailure=false;this.failure='';
  if(!this.bootPrepared){
   const scene=director.getScene()!;PhysicsSystem.instance.gravity=new Vec3(0,-9.81,0);PhysicsSystem.instance.fixedTimeStep=1/60;
   // Flat scenes use static scenery queries and explicit capsule moves, without dynamic rigid bodies.
   if(this.flatMode){this.previousPhysicsAutoSimulation??=PhysicsSystem.instance.autoSimulation;PhysicsSystem.instance.autoSimulation=false;}
   this.store=new SaveStore(this.platform);const loaded=this.store.load(this.query);
   // A verified journey continues even if the host recreated the game while
   // it was in the background. Recovery warnings retain their explicit UI.
   if(loaded.session&&!loaded.warning){this.menu='';this.resumeSavedJourney=true;}
   this.session=loaded.session??new GameSession(Date.now()%2147483646,this.query);if(!loaded.session)this.session.enter(getArea('S01-T1'));if(loaded.warning){this.toast=loaded.warning;this.toastTime=20;this.saved='尚未保存';}
   this.applyPlaytestLevel(this.session);this.applyTemporaryMax();
   const cam=new Node('WorldCamera');scene.addChild(cam);this.camera=cam.addComponent(Camera);this.camera.projection=Camera.ProjectionType.ORTHO;this.camera.orthoHeight=4.1;this.camera.near=.1;this.camera.far=160;this.camera.clearColor=new Color(24,23,21);this.camera.visibility=Layers.Enum.DEFAULT|(1<<18);
   cam.lookAt(new Vec3(-15,-19.35,-18));this.followCameraRotation.set(cam.rotation);
   const sun=new Node('Daylight');scene.addChild(sun);sun.setRotationFromEuler(-55,-35,0);const light=sun.addComponent(DirectionalLight);this.keyLight=light;light.color=new Color(255,240,215);light.illuminance=50000;light.shadowEnabled=true;light.shadowDistance=sys.isMobile?28:45;light.shadowNormalBias=.015;light.shadowPcf=sys.isMobile?1:2;if(sys.isMobile)light.csmLevel=1;
   const globals=scene.globals;globals.ambient.skyColor=new Vec4(.75,.79,.84,1);globals.ambient.skyIllum=25000;globals.ambient.groundAlbedo=new Vec4(.43,.43,.42,1);globals.shadows.enabled=false;globals.shadows.type=1;globals.shadows.shadowMapSize=sys.isMobile?1024:2048;globals.skybox.enabled=false;globals.fog.enabled=false;
   if(this.flatMode&&!this.modelPlayer)this.hud.setFlatPortrait(null);this.loadingScreen.show(.04,'正在准备旅途');this.audio=this.node.addComponent(AudioSource);
   for(const id of ['step','sword','hit','arrow','spell','interact','complete','dice','bells','impact-flesh','impact-heavy','impact-critical','impact-armor','impact-fire','impact-lightning','impact-kill'])resources.load(`audio/${id}`,AudioClip,(err,clip)=>{if(!err)this.sounds.set(id,clip);});
   input.on(Input.EventType.KEY_DOWN,this.keyDown,this);input.on(Input.EventType.KEY_UP,this.keyUp,this);input.on(Input.EventType.MOUSE_MOVE,this.mouseMove,this);input.on(Input.EventType.MOUSE_DOWN,this.mouseDown,this);input.on(Input.EventType.MOUSE_UP,this.mouseUp,this);input.on(Input.EventType.MOUSE_WHEEL,this.mouseWheel,this);
   for(const type of [Input.EventType.TOUCH_START,Input.EventType.TOUCH_MOVE,Input.EventType.TOUCH_END,Input.EventType.TOUCH_CANCEL] as const)input.on(type,this.movementTouch,this);
   if(DEV)(globalThis as any).__chapter={app:this,areas:AREAS,get state(){return (this as any).app.session.state;},wasm:{setEnabled:setComputationWasmEnabled,inspect:navigationWasmState},inspect:()=>({area:this.session.state.area,actors:this.actors?.inspect(),ready:!!this.actors&&!this.loading&&!this.failure,menu:this.menu,objective:this.session.objective(),errors:this.failure})};
   this.bootPrepared=true;
  }
  this.loading=true;this.loadingScreen.show(.04,'正在准备旅途');
  await loadBundleWithDependencies('resources');if(this.destroyed)return;this.loadingScreen.show(.16,'正在展开石桥边地');
  const startup=[
   new Promise<Material>((resolve,reject)=>resources.load('materials/Field',Material,(err,asset)=>err?reject(err):resolve(asset))),
   this.flatMode?Promise.resolve():SurfaceMaterials.load(),SceneBuilder.preload(this.flatMode),Effects.preload(),this.modelPlayer?Actors.preload('raphael',this.session.state.equipment.weapon):Promise.resolve(),
  ];
  let ready=0;await Promise.all(startup.map(task=>task.then(()=>{if(!this.startupFailure&&!this.destroyed)this.loadingScreen.show(.16+(++ready)*.44/startup.length,'正在布置场景与特效');})));
  if(this.destroyed)return;await this.rebuild();if(this.resumeSavedJourney){this.music?.start();this.resumeSavedJourney=false;}this.renderModal();console.log('[Chapter] Cocos first chapter initialized',this.session.state.area);
 }
 private async rebuild(fastTravel=false){
  this.pagePreparationRevision++;this.preparingPage=false;
  this.session.setMovementSpeed(!this.flatMode||this.modelPlayer?MODEL_RUN_SPEED:3.6);
  this.combatFocus=null;
  const retainedPlayer=this.modelPlayer&&this.actors instanceof Player3DActors?this.actors.takePlayer():undefined;
  this.loading=true;this.clearInput(false);this.campaignView?.destroy();this.campaignView=undefined;this.impact?.destroy();this.impact=undefined;this.sceneInteraction?.destroy();this.sceneInteraction=undefined;this.groundLootView?.destroy();this.groundLootView=undefined;this.taskPresence?.destroy();this.taskPresence=undefined;this.portalHud?.destroy();this.portalHud=undefined;this.enemyFeedback?.destroy();this.enemyFeedback=undefined;this.actors?.destroy();this.effects?.destroy();this.flatWorld?.destroy();this.flatWorld=undefined;this.nativePortals?.destroy();this.nativePortals=undefined;this.flatPortrait?.destroy();this.flatPortrait=undefined;this.world?.destroy();const area=this.trainingRange?.area??getArea(this.session.state.area),entry={x:this.session.state.player.x,z:this.session.state.player.z};
  this.loadingScreen?.show(.64,'正在进入'+area.name);this.mapResources.select(area,id=>AREAS[id]);this.world=new SceneBuilder(director.getScene()!,area,this.flatMode,this.mapResources);LocalCartography.setLayout(area.id,this.world.layoutObstacles);this.session.enter(this.world.area,entry,fastTravel);resetJourneyGuidance(this.session);this.guideArea='';this.encounterTime=.2;this.encounterText='';this.compassText='';
  if(this.trainingRange){this.trainingRange.reset();buildTrainingFloor(this.world);}
  this.portalHud=new PortalHud(this.hud,this.camera,this.world);
  this.sceneInteraction=new SceneInteraction(this.hud,this.camera,this.sceneInteract);
  this.groundLootView=new GroundLootPresentation(this.world,this.camera,this.hud);
  this.taskPresence=new TaskPresence(this.hud,this.camera,this.world);
  this.impact=new CombatImpactFeedback(this.hud,this.camera,this.world,this.impactSound,this.enemyHead);this.impact.reducedMotion=this.hud.reducedMotion;
  let presentationFailure='';
  // Capture environment renderers before starting actors, then overlap their
  // independent resource loads instead of waiting for the entire map first.
  let presentationReady:Promise<void>;
  if(this.flatMode&&!this.trainingRange){this.flatWorld=new FlatWorldPresentation(this.world,this.camera);presentationReady=this.flatWorld.build().catch(error=>{presentationFailure=String(error);console.error('[Chapter] Map presentation load failed',error);});}
  else{this.nativePortals=new PortalPresentation(this.world,this.camera);presentationReady=this.nativePortals.build().catch(error=>{presentationFailure=String(error);console.error('[Chapter] Waystone presentation load failed',error);});}
  this.effects=new Effects(this.world,this.flatMode?this.camera:undefined,this.modelPlayer);this.actors=this.modelPlayer?new Player3DActors(director.getScene()!,this.world,this.camera,retainedPlayer):this.flatMode?new FlatActors(director.getScene()!,this.world,this.camera):new Actors(director.getScene()!,this.world);this.actors.reducedMotion=this.hud.reducedMotion;this.effects.reducedMotion=this.hud.reducedMotion;this.effects.setPlayerPresentationSource(this.presentationSource);this.enemyFeedback=new EnemyCombatFeedback(this.hud,this.camera,this.world,this.enemyHead);this.configureLighting(area.kind);
  const proxy=new Node('PlayerController');this.world.root.addChild(proxy);proxy.setPosition(entry.x,this.world.height(entry),entry.z);this.capsule=proxy.addComponent(CapsuleCharacterController);this.capsule.radius=.32;this.capsule.height=1.18;this.capsule.center=new Vec3(0,.91,0);this.capsule.stepOffset=.35;this.capsule.slopeLimit=45;this.capsule.setGroup(8);this.capsule.setMask(6);
  this.visited={};for(const [id,v]of Object.entries(this.session.state.flags))if(id.startsWith('visited:'))this.visited[id.slice(8)]=v;
  try{await this.actors.build(this.session,(done,total)=>this.loadingScreen?.show(.68+.30*done/total,'正在准备人物 '+done+' / '+total));if(this.actors instanceof FlatActors)await this.prepareFlatPortrait();else void this.prepareHairstylePortrait();this.failure=presentationFailure;}catch(error){this.failure=String(error);console.error('[Chapter] Character presentation load failed',error);}
  await presentationReady;if(this.destroyed)return;this.failure=this.failure||presentationFailure;
  // Enable only once real casters exist, before the loading cover is removed.
  // Cocos 3.8.8 otherwise allocates a clear-only map then replaces its color
  // texture on the first size-dirty frame without destroying the old color.
  director.getScene()!.globals.shadows.enabled=true;
  this.campaignView=new CampaignPresentation(this.hud,this.camera,this.world,this.session,this.campaignFinished,this.campaignSound,this.campaignArmy);this.hud.previewSource=this.actors.playerModel();this.loadingScreen?.show(1,'旅途已就绪');this.positionCamera(1);await this.effects.prepareShaders(this.session.state.player,this.session);await this.enemyFeedback?.prepareTextGlyphs();await this.preparationResources.prepare(this.session).catch(error=>console.warn('[Chapter] Initial page prewarm failed',error));await new Promise<void>(resolve=>director.once(Director.EVENT_AFTER_DRAW,resolve));if(this.destroyed)return;this.world.syncPhysics();this.loadingScreen?.hide();this.loading=false;this.modalKey='';this.positionCamera(1);this.renderModal();if(this.flatMode&&!this.trainingRange)this.mapResources.prefetch(id=>AREAS[id]);
 }
 private async travelFromMap(id:string):Promise<void>{
  const game=this.session,destination=AREAS[id],travel=this.hud.mapTravel;
  if(this.menu!=='map'||travel.busy||this.loading||this.failure||this.trainingRange||!destination)return;
  if(this.equipmentPreparing||this.preparingPage||this.campaignView?.active){travel.error=mapText('map.submitting');this.modalKey='';this.renderModal();return;}
  const status=game.fastTravelAvailability(destination);
  if(!status.available){travel.error=status.reason;this.modalKey='';this.renderModal();return;}
  // Pause input and automatic movement before taking the transactional snapshot.
  this.automation.stop();this.clearInput(false);this.effects?.clear();this.impact?.clear();
  if(!game.fastTravel(destination))return;
  travel.busy=true;travel.error='';this.modalKey='';this.renderModal();
  try{
   await new Promise<void>(resolve=>director.once(Director.EVENT_AFTER_DRAW,resolve));
   await this.rebuild(true);
   if(this.destroyed)return;
   if(this.failure)throw new Error('Destination presentation unavailable');
   game.completeFastTravel(true);travel.busy=false;this.menu='';this.hud.clearModal();this.say(mapText('map.arrived',{name:destination.name}),5);this.save();
  }catch(error){
   game.completeFastTravel(false);
   if(this.destroyed)return;
   console.warn('[Map] Fast travel failed; restoring origin',error);
   this.failure='';
   try{await this.rebuild(true);}catch(recoveryError){console.error('[Map] Origin presentation unavailable',recoveryError);this.loading=false;this.failure='旅途资源载入失败，请返回后重试。';}
   travel.busy=false;travel.error=mapText('map.failure');this.menu='map';this.modalKey='';this.renderModal();
  }finally{
   game.completeFastTravel(false);travel.busy=false;
  }
 }
 private async prepareHairstylePortrait(){
  const actors=this.actors instanceof Player3DActors?this.actors.player:this.actors instanceof Actors?this.actors:null;
  const id=actors?.playerHairstyles().find(style=>style.selected)?.id??'curly',path=HAIRSTYLE_PORTRAITS[id];if(!path)return;
  const revision=++this.hairstyleHeadRevision,owner=new Node('SelectedHairstylePortrait');this.node.addChild(owner);
  try{
   const frame=await UiSkin.frame(path,0,owner);if(this.destroyed||revision!==this.hairstyleHeadRevision){owner.destroy();return;}
   const previous=this.hairstyleHeadOwner;this.hairstyleHeadOwner=owner;this.hairstyleHeads.clear();this.hairstyleHeads.set(id,frame);this.refreshHairstylePortrait();
   if(['inventory','attributes','checks','equipment-catalog'].includes(this.menu)){this.modalKey='';this.renderModal();}previous?.destroy();
  }catch(error){owner.destroy();console.warn('[HUD] Hairstyle portrait unavailable; keeping the current portrait.',error);}
 }
 private refreshHairstylePortrait(){
  const actors=this.actors instanceof Player3DActors?this.actors.player:this.actors instanceof Actors?this.actors:null;
  const id=actors?.playerHairstyles().find(style=>style.selected)?.id??'curly',frame=this.hairstyleHeads.get(id);
  if(frame)this.hud.setHeadPortrait(frame);else void this.prepareHairstylePortrait();
 }
 private async prepareFlatPortrait(){
  const portrait=(this.actors as FlatActors).playerPortrait();if(!portrait)return;
  this.hud.flatPortraitViewsForWeapon=weapon=>this.actors instanceof FlatActors?this.actors.playerPortraitViews(weapon):[];
  const bounds=portrait.bounds,r=portrait.rect;
  const rect=bounds?new Rect(r.x+bounds[0],r.y+bounds[1],bounds[2]-bounds[0],bounds[3]-bounds[1]):r;
  this.flatPortrait=new SpriteFrame();this.flatPortrait.reset({texture:portrait.texture,rect,originalSize:new Size(rect.width,rect.height)});this.flatPortrait.packable=false;
  this.hud.setFlatPortrait(this.flatPortrait,await this.playerHeadReference());
 }
 private async playerHeadReference():Promise<SpriteFrame>{
  if(!this.flatHead){const texture=await new Promise<Texture2D>((resolve,reject)=>resources.load('flat2d/hero-head-design-reference/texture',Texture2D,(e,a)=>e?reject(e):resolve(a)));this.flatHead=new SpriteFrame();this.flatHead.reset({texture,rect:new Rect(1250,0,502,502),originalSize:new Size(502,502)});this.flatHead.packable=false;}
  return this.flatHead;
 }
 private clearInput(stopAutomation=true,reason:AutomationPause='manual'){this.impact?.clear();this.effects?.clearAim();if(stopAutomation)this.automation.pause(reason);this.keys.clear();this.touches.clear();this.heldAttack=false;this.aiming=null;this.aimGesture=null;this.skillPress=null;this.hud?.hideSkillDescription();this.manualSkillAim=false;this.manualBasicAim=false;this.mouseAim=undefined;this.lastAimTime=-999;this.pulse={};this.session?.cancelInput();this.hud?.joystick?.setPosition(0,0,0);this.hud?.setAimCancelVisible(false);}
 private takeControl(){this.hud?.collapseAutomation();if(this.automation.active){this.automation.pause('manual');this.session.cancelInput();}}
 private currentGuidance(){
  if(this.trainingRange)return null;
  const task=JOURNEY_TASKS.find(t=>t.id===this.trackedTaskId);
  if(task&&this.session.journey.taskDone(task)){this.trackedTaskId=this.session.journey.currentTask(task.chapter)?.id;if(this.automation.destination?.taskId===task.id||this.automation.pausedDestination?.taskId===task.id)this.automation.stop();}
  const target=this.automation.destination??this.automation.pausedDestination;
  if(target)return navigationGuidance(this.session,AREAS,this.query,target);
  if(this.bossTravel&&this.automation.mode==='manual'&&!this.automation.active&&this.bossTravel.area===this.session.state.area&&distance(this.bossTravel.point,this.session.state.player)<=1.35)return navigationGuidance(this.session,AREAS,this.query,this.bossTravel);
  return journeyGuidance(this.session,AREAS,this.query,this.trackedTaskId);
 }
 private startJourneyNavigation(id?:string){
  this.bossTravel=null;
  if(id){const task=JOURNEY_TASKS.find(t=>t.id===id);if(!task||this.session.journey.currentTask(task.chapter)?.id!==id){this.say('请先完成当前阶段，已完成的任务无需再次寻路。');return;}this.trackedTaskId=id;this.session.journey.select('task');}
  const guide=this.currentGuidance();if(!guide)return;
  if(guide.blocked){this.say('目标路线尚未开放或道路受阻，请查看任务地点与等级条件。');return;}
  if(guide.destination.taskId)this.trackedTaskId=guide.destination.taskId;
  this.hud.setGuidance(guide);this.guideTime=0;this.startNavigation(guide.destination);
 }
 private startNavigation(target:NavigationTarget){
  if(this.trainingRange)return;
  if(this.loading||this.failure||this.session.state.status==='dead'||this.session.state.dialogue||this.session.state.dice.active||this.campaignView?.active)return;
  if(target.bossKey){const fresh=this.bosses.navigation(this.session,target.bossKey,this.session.state.area===target.area?this.query:undefined);if(!fresh){this.say(bossText('blocked'));return;}target=fresh;}
  this.bossTravel=target.bossKey?target:null;this.bossTravelArea=this.session.state.area;
  this.clearInput();this.menu='';this.modalKey='';this.hud.clearModal();this.automation.navigate(target);this.guideTime=1;this.hud.setGuidance(this.currentGuidance());this.say('正在前往'+target.label+'；移动可接管。');
 }
 private say(text:string,time=4,role:FeedbackRole='text.normal'){this.toast=text;this.toastTime=time;this.toastRole=role;}
 private play(id:string){const clip=this.sounds.get(id);if(clip)this.audio.playOneShot(clip,.35);}
 private async enterTrainingRange(){
  if(this.trainingRange){this.open('training-range');return;}
  if(this.failure||this.hud.portrait||this.session.state.status==='dead'||this.session.state.dialogue||this.session.state.dice.active||this.campaignView?.active)return;
  this.clearInput();this.automation.stop();this.bossTravel=null;discardCombatSkillPreview(this.session);
  if(!this.save())return;
  this.rangeReturn={session:this.session,menu:this.menu==='title'?'title':'',saved:this.saved,taskId:this.trackedTaskId};
  this.trainingRange=new TrainingRange(this.query);this.session=this.trainingRange.session;this.trackedTaskId=undefined;this.hud.trainingRange=this.trainingRange;
  this.hud.clearEquipmentPickups();this.toast='';this.hud.setGuidance(null);this.menu='training-range';this.returnToMainMenu=false;this.music?.start();this.save();
  await this.rebuild();
 }
 private async leaveTrainingRange(){
  const previous=this.rangeReturn;if(!previous)return;
  this.clearInput();this.automation.stop();this.trainingRange=undefined;this.rangeReturn=undefined;
  this.session=previous.session;this.trackedTaskId=previous.taskId;this.saved=previous.saved;this.menu=previous.menu;this.hud.trainingRange=undefined;this.toast='';this.guideArea='';this.hud.setGuidance(null);
  await this.rebuild();
 }
 private resetTrainingRange(){
  if(!this.trainingRange)return;this.clearInput();this.trainingRange.reset();this.combatFocus=null;this.effects?.clear();this.impact?.clear();this.actors?.update(this.session,0,false,true);this.positionCamera(1);this.say(trainingText('resetNotice'));this.save();
 }
 private applyPlaytestLevel(session:GameSession){
  if(DEV&&!isTapRelease&&COMBAT_RULES.localPlaytestMaxLevel&&typeof location!=='undefined'&&new URLSearchParams(location.search).get('progression')!=='natural'&&['127.0.0.1','localhost','[::1]'].includes(location.hostname))session.raiseToMaxLevel();
 }
 private applyTemporaryMax(){
  if(!this.temporaryMax)return;
  const s=this.session.state,p=s.progression,xp=cumulativeXp(40);
  if(p.totalXp<xp){p.xpReceipts['local-max-test']=xp-p.totalXp;p.totalXp=xp;}
  p.level=40;p.unspentPoints=0;p.ultimateGiftClaimed=true;
  for(const key of ATTRIBUTES)p.attributes[key]=80;
  unlockSkills(p,true);p.skillPoints=41-Object.values(p.learned).reduce((n,rank)=>n+skillRankSpent(rank),0);
  for(const id of Object.keys(EQUIPMENT)){s.inventory[id]=1;s.provenance[id]??='local-max-test';}
  s.equipment.weapon='W10';s.equipment.offhand=null;
  prepareCombatLoadout(s.combat,s.equipment.weapon,s.progression,'BOW');
  let bonus=0;for(const [key,id]of Object.entries(s.equipment))if(key!=='spells'&&typeof id==='string')bonus+=EQUIPMENT[id]?.maxHp??0;
  if((this.session.setCounts().oath??0)>=2)bonus+=8;
  s.player.maxHp=baseMaxHp(p)+bonus;s.player.hp=s.player.maxHp;s.player.focus=s.player.maxFocus;
  s.combat.charge=0;s.player.focus=s.player.maxFocus;s.combat.ultimateLock=0;s.combat.cooldowns={};s.cooldowns={};
  s.combat.ultimate??=Object.values(COMBAT_SKILLS).find(d=>d.type==='ultimate'&&d.style==='THU')?.id??null;
  this.saved='临时满级测试 · 返回普通链接恢复原进度';this.say('临时测试：设置 → 技能效果调试可切换1—5级；F8快速打开。',12);
 }
 private save():boolean{if(this.hud?.mapTravel.busy)return false;if(!this.store||!this.session)return true;if(this.trainingRange){this.saved=trainingText('saved');this.session.dirty=false;this.autosave.committed(true);return true;}if(this.temporaryMax){this.saved='临时满级测试 · 返回普通链接恢复原进度';this.session.dirty=false;this.autosave.committed(true);return true;}const r=this.store.write(this.session);this.saved=r.ok?'已保存 ✓':'尚未保存';if(!r.ok)this.say(r.error??'本地保存失败',8);this.autosave.committed(r.ok);return r.ok;}
 private process(events:GameEvent[]){
  let saveRequested=this.autosave.observe(events);
  this.trainingRange?.observe(events);
  this.impact?.onEvents(events,this.session);
  this.effects?.onEvents(events,this.session);
  this.enemyFeedback?.onEvents(events,this.session);
  this.actors?.onCombatEvents(events,this.session.state.time);
  for(const e of events){
   const item=EQUIPMENT[String(e.type==='loot_drop'?e.item:e.id)];
   if(e.type==='item'&&item){if(e.lootId&&highlightedEquipment(item.quality))this.hud.dismissEquipmentDrop(String(e.lootId));else this.hud.showEquipmentPickup(item,Math.max(1,Number(e.value)||1));}
   else if(e.type==='loot_drop'&&item&&highlightedEquipment(item.quality)){/* The authoritative pile owns its 24-second HUD notice. */}
   else if(e.text&&!['miss','loot_roll'].includes(e.type))this.say(e.text,e.type==='inspect'?7:e.type==='level_up'?8:4,item&&['loot_drop','equip'].includes(e.type)?qualityFeedbackRole(item.quality):eventFeedbackRole(e));
   if(e.type==='travel'||e.type==='retry'){void this.rebuild();saveRequested=true;}
   if(e.type==='journey_open')this.open('journey');
   if(e.type==='hunting_open')this.open('hunting');
   if(e.type==='journey_complete')saveRequested=true;
   if(e.type==='shop'){this.merchant=String(e.id);this.open('shop');}
   if(e.type==='complete'){this.open('complete');this.play('complete');saveRequested=true;}
   if(['reward','item','quest','rest','dialogue'].includes(e.type))this.play('interact');
   if(e.type==='campaign_battle')this.play(e.complete?'complete':'interact');
   if(e.type==='check_roll')this.play('dice');
   if(e.type==='check_result')this.play(e.success?'complete':'hit');

   if(e.type==='attack'||e.type==='action'&&e.kind==='sword')this.play('sword');
   if(e.type==='projectile'&&!e.skillId)this.play(e.kind==='arrow'?'arrow':'spell');
   if(e.type==='skill_release'){
    const id=String(e.skillId),def=COMBAT_SKILLS[id],rank=Number(e.rank)||1,target=e.to as Point|undefined;
    if(def?.offensive&&target)this.combatFocus={skillId:id,rank,target:{...target},until:this.session.state.time+4};
    this.play(def?.style==='BOW'?'arrow':def?.style==='WAR'?'sword':'spell');
   }
  }
  // One commit per event batch, even when a kill levels up and grants items.
  if(saveRequested)this.save();
 }
 private interaction():{object?:InteractionDef;exit?:ExitDef;loot?:string;prompt?:SceneInteractionTarget}{
  const p=this.session.state.player,a=this.world.area,task=this.trackedTaskId??this.session.journey.currentTask()?.id;
  const lootTarget=(drop:GroundLoot)=>{
   const supply=isSupplyId(drop.item)?SUPPLIES[drop.item]:undefined,item=EQUIPMENT[drop.item];
   return {loot:drop.id,prompt:{id:drop.id,name:supply?`${supply.name} ×${drop.count??1}`:`${item.quality} · ${item.name}`,verb:equipmentText('loot.pickup'),point:drop,height:this.world.height(drop),quality:supply?'普通':item.quality,anchorHeight:supply ? .4 : .8,blocked:!this.session.canPickupLoot(drop)?equipmentText('loot.supplyFull',{count:supply?p[supply.stock]:this.session.state.inventory[drop.item],capacity:supply?supply.capacity:equipmentStackLimit(drop.item)}):undefined,avoid:{point:p,height:this.world.height(p)+1}}};
  };
  const loot=this.session.nearbyLoot()[0];
  if(loot)return lootTarget(loot);
  const visible=(q:Point)=>this.world.visible(p,q)&&Math.abs(this.world.height(p)-this.world.height(q))<1.2;
  const priority=(o:InteractionDef)=>o.action==='journey_task'&&o.eventId===task?0:o.actor?1:['journey_board','hunting_guide'].includes(o.action)?3:2;
  const objects=a.objects.filter(o=>this.session.interactionVisible(o)&&distance(p,o)<=Math.min(1.35,o.radius??1.35)&&visible(o)&&(o.action!=='journey_task'||JOURNEY_TASKS.find(t=>t.id===o.eventId)?.goal==='observe')).sort((u,v)=>{
   if(priority(u)===0||priority(v)===0)return priority(u)-priority(v);
   const delta=distance(u,p)-distance(v,p);if(Math.abs(delta)>.2)return delta;
   const current=this.sceneInteraction?.visibleTargetId;return Number(v.id===current)-Number(u.id===current)||priority(u)-priority(v)||delta;
  });
  const object=objects[0];
  if(object){const status=this.session.interactionAvailability(object);const verbs:Record<string,string>={offer:'交谈',merchant:'交易',meeting:'交谈',inspect:'查看',dice_check:'调查',cache:'开启',locked_cache:'开启',recover:'取回',letter:'读信',checkpoint:'休整',journey_task:'调查',journey_board:'查看旅程',hunting_guide:'查看猎区',release_workers:'解救',disable_trap:'拆除',captain_gate:'开启',finish:'确认',growing_scene:'调查',growing_rematch:'挑战',skill_archive:'阅读'};return {object,prompt:{id:object.id,name:object.label,verb:status.completed?worldText('interaction.viewResult'):!status.available?worldText('interaction.viewRequirements'):object.action==='campaign_event'?status.confirmLabel:verbs[object.action]??'操作',point:object,height:this.world.height(object),objective:object.id===this.hud.activeGuidance?.targetId,avoid:object.id===this.hud.activeGuidance?.targetId?{point:p,height:this.world.height(p)+1}:undefined}};}
  const exit=a.exits.filter(e=>distance(p,e)<=1.35&&visible(e)).sort((u,v)=>distance(u,p)-distance(v,p))[0];
  if(exit)return {exit,prompt:{id:exit.id,name:getArea(exit.to).name,verb:'进入',point:exit,height:this.world.height(exit),blocked:this.session.exitRequirement(exit)??undefined,objective:exit.id===this.hud.activeGuidance?.targetId,avoid:exit.id===this.hud.activeGuidance?.targetId?{point:p,height:this.world.height(p)+1}:undefined}};
  // Full supplies explain their limit without taking priority over usable targets.
  const full=this.session.nearbyLoot(true)[0];return full?lootTarget(full):{};
 }
 private interact(expectedId?:string){const c=this.interaction();if(expectedId&&expectedId!==(c.loot??c.object?.id??c.exit?.id))return;if(c.loot&&c.prompt?.blocked){this.say(c.prompt.blocked);return;}this.sceneInteraction?.update(null,true);this.takeControl();if(c.loot){this.process(this.session.pickupLoot(c.loot));this.save();}else if(c.object){if(!this.session.interactionAvailability(c.object).available||c.object.actor||['merchant','offer','meeting','letter','journey_task','campaign_event'].includes(c.object.action)){this.arrivalInteraction(c.object.id);return;}this.process(this.session.interact(c.object));this.save();}else if(c.exit)this.process(this.session.travel(c.exit));else this.say('靠近人物或场景物件后，会显示对应的操作。');this.modalKey='';this.renderModal();}
 private arrivalInteraction(id:string,confirmed=false){
  const s=this.session.state,p=s.player,object=this.world.area.objects.find(o=>o.id===id);
  // Resolve the selected destination itself; nearby loot or another NPC must
  // never replace the target when an automatic route finishes.
  if(!object||!this.session.interactionVisible(object)&&!this.session.interactionAvailability(object).completed||s.status==='dead'||s.dialogue||s.dice.active||s.action
   ||distance(p,object)>Math.min(1.35,object.radius??1.35)||!this.world.visible(p,object)||Math.abs(this.world.height(p)-this.world.height(object))>=1.2){
   this.automation.pause('blocked',autoText('task.failed'));this.say(autoText('task.failed'));return;
  }
  this.sceneInteraction?.rememberApproach(this.world.area.objects,p);this.sceneInteraction?.update(null,true);this.clearInput(false);
  const access=this.session.interactionAvailability(object);
  if(!access.available||access.readOnly){
   if(access.available){this.process(this.session.interact(object));this.save();}
   this.open('interaction:'+id);return;
  }
  // Authored choices are already a confirmation; do not put a second one before them.
  const event=object.action==='campaign_event'?CAMPAIGN_EVENTS[object.eventId??'']:undefined;
  const hasChoices=!!(event?.choices?.length||event?.choiceItems?.length);
  if(!confirmed&&!hasChoices&&!['offer','meeting','letter','dice_check','journey_board','hunting_guide'].includes(object.action)){
   this.open('interaction:'+id);return;
  }
  this.process(this.session.interact(object));this.save();
  if(!s.dialogue&&!s.dice.active&&(object.action==='campaign_event'||this.session.interactionAvailability(object).completed)){this.menu='interaction:'+id;this.automation.pause('menu');}
  this.modalKey='';this.renderModal();
 }
 private get updatePromptVisible():boolean{const u=this.platform?.updates;return !!u&&(u.status==='applying'||u.ready&&u.promptPending)&&!this.hud?.portrait&&!this.loading&&(!this.session||(this.menu==='title'||this.menu==='pause')&&!this.session.state.dialogue&&!this.session.state.dice.active);}
 private click(action:string){
  if(this.background)return;
  this.music?.gesture();
  if(action==='update:apply'){this.platform.updates.apply(()=>this.save());return;}
  if(action==='update:later'){this.platform.updates.defer();return;}
  if(action==='update:show'){this.platform.updates.requestPrompt();return;}
  if(this.updatePromptVisible)return;
  if(action==='resources:retry'){void this.ensureAccess();return;}
  if(action==='auth:retry'){void this.ensureAccess();return;}
  if(this.updatePromptVisible||!this.platform?.auth.ready||!this.session||!this.world||this.loading)return;
  if(action==='dev-tools'){if(this.session.developmentTools.enabled&&!this.trainingRange)this.open('dev-tools');return;}
  if(action.startsWith('dev:')){
   if(this.menu!=='dev-tools'||this.trainingRange||!this.session.developmentTools.enabled)return;
   const result=this.session.developmentTools.run(action.slice(4));this.say(result.message);
   if(result.ok)this.save();this.modalKey='';this.renderModal();return;
  }
  if(action==='training:enter'){void this.enterTrainingRange();return;}
  if(this.trainingRange){
   if(action==='training:exit'){void this.leaveTrainingRange();return;}
   if(['pause','title','settings','map','journey','journey-toggle-navigation','training:settings'].includes(action)){this.open('training-range');return;}
   if(action==='checks'){this.open('skill-effect-debug');return;}
   if(action==='new'||action==='confirm-new'||action.startsWith('auto:')||action==='automation')return;
   if(action.startsWith('training:')){
    const range=this.trainingRange;
    if(action==='training:injure'){this.clearInput();this.session.state.player.hp=Math.ceil(this.session.state.player.maxHp/2);this.session.state.revision++;this.menu='';this.hud.clearModal();return;}
    if(action==='training:report'){this.hud.show(trainingText('report'),(range.groupMode?trainingText('groupStats',{remaining:range.remainingMonsters,total:range.targetCount,defeated:range.defeatedMonsters})+'\n':'')+trainingText('stats',{damage:range.damage,hits:range.hits,misses:range.misses,criticals:range.criticalHits,dps:Math.round(range.dps),seconds:range.elapsed.toFixed(1)})+'\n\n'+trainingText('reportDescription'),[{label:trainingText('toolbar'),action:'training:settings'},{label:trainingText('resume'),action:'close'}]);return;}
    if(action.startsWith('training:formation:')){const id=action.slice('training:formation:'.length) as TargetFormation;if(!['single','cluster','line','horde'].includes(id))return;const rebuild=(id==='horde')!==range.groupMode;range.formation=id;if(rebuild){this.menu='training-range';void this.rebuild();return;}}
    else if(action==='training:monster-count'&&range.groupMode){const counts=TRAINING_MONSTER_COUNTS;range.monsterCount=counts[(counts.findIndex(n=>n===range.monsterCount)+1)%counts.length];this.menu='training-range';void this.rebuild();return;}
    else if(action==='training:distance'){const distances=[1.5,4,8,12];range.distance=distances[(distances.indexOf(range.distance)+1)%distances.length];}
    else if(action==='training:resource')range.unlimitedResource=!range.unlimitedResource;
    else if(action==='training:retaliate')range.retaliate=!range.retaliate;
    else if(action!=='training:reset')return;
    this.resetTrainingRange();if(action==='training:reset'){this.menu='';this.hud.clearModal();}this.modalKey='';this.renderModal();return;
   }
  }
  if(action==='preparation:keep'){this.pendingPreparationAction=undefined;this.modalKey='';this.renderModal();return;}
  if(action==='preparation:discard'){const next=this.pendingPreparationAction;this.pendingPreparationAction=undefined;discardPreparationPreview(this.session);if(next)this.click(next);return;}
  const leavesAllocation=action==='close'||action.startsWith('allocation:')&&action!==this.menu||['attributes','inventory','equipment','profession','checks','appearance','map','pause','title','journey'].includes(action)||action.startsWith('forge');
  if(this.menu.startsWith('allocation:')&&hasPreparationPreview(this.session)&&leavesAllocation){this.pendingPreparationAction=action;this.hud.show(pt('allocation.dirtyTitle'),pt('allocation.dirtyHint'),[{label:pt('allocation.keep'),action:'preparation:keep'},{label:pt('allocation.discard'),action:'preparation:discard'}]);return;}
  if(action==='allocation-saved'){this.save();this.say(pt('allocation.saved'));this.modalKey='';this.renderModal();return;}
  if(action.startsWith('inventory-slot:')){selectEquipmentSocket(this.session,action.slice(15));this.menu='inventory';this.modalKey='';this.renderModal();return;}
  if(action.startsWith('inventory-category:')){selectEquipmentCategory(this.session,action.slice(19));this.menu='inventory';this.modalKey='';this.renderModal();return;}
  if(action.startsWith('combat-family:')){const family=action.slice(14);this.menu='checks';this.preparePage(()=>this.preparationResources.family(this.session,family),()=>browseCombatFamily(this.session,family));return;}
  if(action.startsWith('allocation-browse:')){const family=action.slice(18) as 'WAR'|'BOW'|'FIR'|'THU'|'COM';this.preparePage(()=>this.preparationResources.family(this.session,family),()=>browseAllocationFamily(this.session,family));return;}
  if(action.startsWith('allocation-reset:')){if(this.session.preparationAvailability().available)resetAllocationPreview(this.session,action.slice(17));this.modalKey='';this.renderModal();return;}
  if(action.startsWith('allocation-skill:')){const id=action.slice(17);this.open('allocation:skills');this.preparePage(()=>this.preparationResources.family(this.session,COMBAT_SKILLS[id]?.style??this.session.state.combat.family),()=>beginAllocation(this.session,id));return;}
  if(action==='profession-apply'){void this.applyProfessionPrepared();return;}
  if(action==='profession'||action.startsWith('profession-for:')){
   const id=action.startsWith('profession-for:')?action.slice(15):undefined,item=id?EQUIPMENT[id]:undefined;
   const family:CombatFamily=item?.kind==='sword'?'WAR':item?.kind==='bow'?'BOW':item?.kind==='staff'?(this.session.state.combat.family==='THU'?'THU':'FIR'):this.session.state.combat.family;
   chooseProfession(this.session,family,id);this.open('profession');return;
  }
  if(action==='skill-effect-debug'||action.startsWith('debug:')){
   if(!this.skillDebugAvailable||this.failure||this.hud.portrait||this.session.state.status==='dead'||this.session.state.dialogue||this.session.state.dice.active)return;
   if(action==='skill-effect-debug'){this.open(action);return;}
   if(this.menu!=='skill-effect-debug')return;
   this.clearInput();discardCombatSkillPreview(this.session);
   if(this.skillEffectDebug.handle(action,this.session)){if(this.trainingRange)this.resetTrainingRange();this.combatFocus=null;this.effects?.clear();this.impact?.clear();this.actors?.update(this.session,0,false,true);this.modalKey='';this.renderModal();}return;
  }
  if(this.campaignView?.active&&!this.menu){this.campaignView.handle(action);return;}
  if(action==='automation'){
   if(this.failure||this.hud.portrait||this.session.state.status==='dead'||this.session.state.dialogue||this.session.state.dice.active||this.menu)return;
   this.clearInput(false);this.hud.toggleAutomation();return;
  }
  if(action.startsWith('auto:')){
   if(this.failure||this.hud.portrait||this.session.state.status==='dead'||this.session.state.dialogue||this.session.state.dice.active||this.menu&&this.menu!=='navigation'&&this.menu!=='automation')return;
   const command=action.slice(5);
   const dismiss=()=>{this.hud.collapseAutomation();if(this.menu==='automation'){this.menu='';this.modalKey='';this.hud.clearModal();}};
   if(command==='stop'){this.automation.stop();this.clearInput(false);dismiss();this.say('自动操作已停止。');return;}
   if(command==='navigate'){dismiss();if(this.automation.destination){this.automation.stop();this.clearInput(false);this.say('自动寻路已停止。');}else this.open('navigation');return;}
   if(command==='resume'){this.clearInput(false);this.automation.resume();dismiss();return;}
   if(command==='quest'||command==='battle'||command==='idle'){
    const requested=command==='idle'?'idle':'quest';
    if(this.automation.mode===requested&&this.automation.paused){this.automation.resume();dismiss();return;}
    const mode=this.automation.mode===requested?'manual':requested;this.clearInput(false);this.automation.setMode(mode,this.trackedTaskId);dismiss();
    this.say(autoText(mode==='manual'?'stopped':mode==='idle'?'started.hunt':'started.task'),3);return;
   }
   if(command.startsWith('object:')){const object=this.world.area.objects.find(o=>o.id===command.slice(7)&&this.session.interactionVisible(o));if(object)this.startNavigation({area:this.session.state.area,point:object,label:object.label,objectId:object.id});return;}
   if(command.startsWith('exit:')){const exit=this.world.area.exits.find(e=>e.id===command.slice(5));if(exit){const requirement=this.session.exitRequirement(exit);if(requirement)this.say(requirement);else this.startNavigation({area:this.session.state.area,point:exit,label:exit.label,exitId:exit.id});}return;}
   return;
  }
  if(action==='hunting'||action==='campaign-log'||action.startsWith('campaign-log:')){this.open(action);return;}
  if(action.startsWith('hairstyle:')){
   if(this.loading||this.failure||this.session.state.dice.active||this.session.state.dialogue)return;
   const actors=this.actors instanceof Player3DActors?this.actors.player:this.actors instanceof Actors?this.actors:null;
   void actors?.setPlayerHairstyle(action.slice(10)).then(changed=>{if(!changed||this.destroyed)return;this.refreshHairstylePortrait();this.say('发型已更换');this.modalKey='';this.renderModal();}).catch(error=>{if(!this.destroyed){console.warn('[Hair] Style load failed',error);this.say('发型载入失败，请重试。');}});return;
  }
  if(action==='combat-plan-saved'){if(this.save())this.say('技能加点已保存。');this.modalKey='';this.renderModal();return;}
  if(action.startsWith('combat-active:')||action.startsWith('combat-passive:')||action.startsWith('combat-ultimate:')||action.startsWith('combat-loadout:')||action.startsWith('attribute:')||action==='attribute-respec'){
   if(this.loading||this.session.state.dice.active||this.session.state.dialogue)return;
   if(this.temporaryMax&&(action.startsWith('attribute:')||action==='attribute-respec')){this.say('临时测试中四项属性已固定为80');return;}
   const parts=action.split(':');let ok=false;
   if(parts[0]==='combat-active')ok=this.session.assignActiveSkill(Number(parts[1]),parts[2]);
   if(parts[0]==='combat-passive')ok=this.session.assignPassive(Number(parts[1]),parts[2]);
   if(parts[0]==='combat-ultimate')ok=this.session.assignUltimate(parts[1]);
   if(parts[0]==='combat-loadout'){chooseProfession(this.session,parts[1] as CombatFamily);this.open('profession');return;}
   if(parts[0]==='attribute')ok=this.session.allocateAttribute(parts[1] as Attribute);
   if(action==='attribute-respec')ok=this.session.respecAttributes();
   this.say(ok?'整备已保存。':'需要安全检查点、已解锁技能及可用槽位。');this.save();this.modalKey='';this.renderModal();return;
  }
  if(action.startsWith('dice:')){const v=this.session.diceView();if(!v||this.loading||this.failure||this.dicePanel.busy)return;const command=action.slice(5);let events:GameEvent[]=[];if(command==='roll')events=this.session.rollCheck(false,v.attempt);if(command==='reroll')events=this.session.rollCheck(true,v.attempt);if(command==='continue')events=this.session.finishCheck();if(command==='cancel')events=this.session.cancelCheck();if(command==='help')events=this.session.toggleCheckHelp();this.process(events);this.clearInput(false);if(!this.session.state.dice.active)this.automation.resumeAfter('dice');this.save();this.modalKey='';this.renderModal();return;}
  if(this.session?.state.dice.active)return;
  if(action==='toggle-impact-motion'){if(this.menu!=='settings'&&this.menu!=='pause')return;this.hud.reducedMotion=!this.hud.reducedMotion;if(this.effects)this.effects.reducedMotion=this.hud.reducedMotion;if(this.impact){this.impact.clear();this.impact.reducedMotion=this.hud.reducedMotion;}if(this.actors)this.actors.reducedMotion=this.hud.reducedMotion;try{this.platform.setItem('sword-fire-ui-reduced-motion',this.hud.reducedMotion?'1':'0');}catch{this.say('显示设置已应用，本机偏好暂未保存。');}this.modalKey='';this.renderModal();return;}
  if(action==='toggle-music'){if(this.menu==='pause'||this.menu==='settings'){this.music?.toggle();}return;}
  if(action==='toggle-story-locale'){
   if(this.menu!=='settings')return;setLocale(currentLocale()==='en'?'zh-CN':'en');
   try{this.platform.setItem(LOCALE_PREFERENCE,currentLocale());}catch{/* The current story language still applies for this session. */}
   this.modalKey='';this.renderModal();return;
  }
  if(action.startsWith('settings-tab:')){const tab=action.slice(13);if(this.menu!=='settings'||!['audio','controls','journey'].includes(tab))return;this.hud.settingsTab=tab as 'audio'|'controls'|'journey';this.modalKey='';this.renderModal();return;}
  if(action==='toggle-skill-names'){if(this.menu!=='pause'&&this.menu!=='settings'||this.loading||this.hud.portrait)return;this.hud.setSkillNamesVisible(!this.hud.skillNamesVisible);this.modalKey='';this.renderModal();return;}
  if(action==='toggle-skill-aim'){if(this.menu!=='settings'||this.loading||this.hud.portrait)return;this.clearInput();this.hud.skillAimMode=this.hud.skillAimMode==='auto'?'manual':'auto';try{this.platform.setItem('sword-fire-skill-aim-mode',this.hud.skillAimMode);}catch{this.say('瞄准设置已应用，本机偏好暂未保存。');}this.modalKey='';this.renderModal();return;}
  if(action==='bosses'){
   if(this.loading||this.failure||this.trainingRange||this.session.state.status==='dead'||this.session.state.dialogue||this.hud.portrait)return;
   this.automation.pauseNavigation();this.open('bosses');return;
  }
  if(action.startsWith('boss-follow:')){
   if(this.menu!=='bosses')return;this.bosses.follow(this.session,action.slice(12));this.save();this.bossPanel?.update();return;
  }
  if(action.startsWith('boss-go:')){
   if(this.loading||this.failure||this.trainingRange||this.session.state.status==='dead'||this.session.state.dialogue||this.menu&&this.menu!=='bosses')return;
   const key=action.slice(8),row=this.bosses.find(this.session,key);if(!row){this.say(bossText('outOfRange'));return;}
   const target=this.bosses.navigation(this.session,key,this.session.state.area===row.area?this.query:undefined);if(!target){this.say(bossText('blocked'));return;}
   this.bosses.dismiss();this.hud.setBossAwareness(null,this.bosses.count);this.startNavigation(target);return;
  }
  if(action==='supplies'){if(this.failure||this.menu||this.session.state.dialogue||this.hud.portrait||this.aiming||this.heldAttack||this.campaignView?.active)return;this.hud.toggleSupplyBelt();return;}
  if(action==='potion-health'||action==='potion-focus'||action==='potion-resource'){if(this.loading||this.failure||this.menu||this.session.state.dialogue||this.hud.portrait||this.aiming||this.heldAttack)return;const ok=this.session.useConsumable(action==='potion-health'?'health':'resource');if(ok){this.play('interact');this.save();}return;}
  if(action.startsWith('campaign-prerequisite-go:')){
   if(this.failure||this.hud.portrait||this.session.state.status==='dead'||this.session.state.dialogue||this.session.state.dice.active)return;
   const selected=action.slice('campaign-prerequisite-go:'.length),split=selected.indexOf(':'),id=selected.slice(0,split),key=selected.slice(split+1);
   const target=campaignPrerequisiteTargets(this.session,AREAS,id).find(target=>target.id===key);
   if(!target||target.blocked){this.say(target?autoText('route.locked'):autoText('task.failed'));this.modalKey='';this.renderModal();return;}
   const guide=navigationGuidance(this.session,AREAS,this.query,target.destination);
   if(!guide||guide.blocked){this.say(autoText('route.locked'));return;}
   this.startNavigation(target.destination);return;
  }
  if(action==='journey'||action.startsWith('journey-')){
   if(this.loading||this.failure||this.session.state.dialogue)return;
   const parts=action.split(':');
   if(action==='journey-current'){this.open(`journey-chapter:${JOURNEY_TASKS.find(t=>t.id===this.trackedTaskId)?.chapter??chapterForArea(this.session.state.area)}`);return;}
   if(action==='journey-stop'){this.automation.stop();this.clearInput(false);this.say('自动寻路已关闭。');this.modalKey='';this.renderModal();return;}
   if(action==='journey-toggle-navigation'){
    if(this.automation.destination){if(this.automation.destination.bossKey){this.automation.pauseNavigation();this.clearInput(false);this.say('首领寻路已暂停，点击继续可恢复。');}else{this.automation.stop();this.clearInput(false);this.say('自动寻路已关闭。');}return;}
    const paused=this.automation.pausedDestination;if(paused&&!paused.taskId){this.startNavigation(paused);return;}
    const task=JOURNEY_TASKS.find(t=>t.id===paused?.taskId);this.startJourneyNavigation(task&&!this.session.journey.taskDone(task)?task.id:undefined);return;
   }
   if(parts[0]==='journey-go'){this.startJourneyNavigation(parts[1]||undefined);return;}
   if(parts[0]==='journey-field-go'){
    const object=Object.values(AREAS).flatMap(area=>area.objects.map(object=>({area:area.id,object}))).find(v=>v.object.action==='campaign_event'&&v.object.eventId===parts[1]&&this.session.interactionVisible(v.object));
    if(object)this.startNavigation({area:object.area,point:object.object,label:object.object.label,objectId:object.object.id});return;
   }
   if(action==='journey-locked'){this.say('第3—8章尚未开放，当前可游玩第一、第二章。');return;}
   if(action==='journey-unavailable'){this.say('查看本章任务与关底进度，达成后即可自选。');return;}
   if(parts[0]==='journey-track'){this.automation.stop();this.trackedTaskId=undefined;this.session.journey.select(parts[1]);this.open('');this.guideTime=1;this.say(parts[1]==='task'?'正在跟随任务；点击自动寻路即可出发。':parts[1]==='hunt'?'正在跟随狩猎；点击自动寻路前往猎区。':'任务与狩猎并列指引');return;}
   if(parts[0]==='journey-life-claim'){const ok=this.session.claimLifecycleReward(parts[1],parts[2]);this.say(lifecycleText(ok?'life.claimOk':'life.claimFailed'));this.save();this.open(`journey-chapter:${parts[1].startsWith('LC1_')?1:2}`);return;}
   if(parts[0]==='journey-loot-set'){this.session.bossLoot.selectStyle(parts[1]);this.save();this.open(`journey-loot:${parts[2]}`);return;}
   if(parts[0]==='journey-claim'){const ok=this.session.claimJourneyWeapon(Number(parts[1]),parts[2],parts[3]);this.say(ok?'史诗武器已领取，可在背包装备。':'需要脱战、奖励尚未领取，并选择尚未拥有的武器。');this.save();this.open(`journey-chapter:${parts[1]}`);return;}
   if(parts[0]==='journey-map'){this.open('map');this.hud.atlas(this.session,this.visited,parts[1]);return;}
   this.open(action);return;
  }
  if(action==='begin'||action==='close'&&this.menu==='title'){if(this.loading)return;if(this.failure){this.say('角色资源仍在载入，请稍后重试。');void this.rebuild();return;}this.returnToMainMenu=false;this.menu='';this.clearInput();this.hud.clearModal();this.music?.start();this.save();return;}
  if(action.startsWith('interaction-confirm:')){const id=action.slice(20);if(this.menu!=='interaction:'+id)return;this.menu='';this.hud.clearModal();this.automation.resumeAfter('menu');this.arrivalInteraction(id,true);return;}
  if(action==='interact'||action.startsWith('interact:')){if(!this.menu)this.interact(action.startsWith('interact:')?action.slice(9):undefined);return;}
  if(action==='close'){if(this.session.state.dialogue)return;if(this.returnToMainMenu){this.open('title');return;}discardCombatSkillPreview(this.session);const preserveAutomation=this.menu==='automation',completedInteraction=this.menu.startsWith('interaction:')&&this.world.area.objects.some(o=>o.id===this.menu.slice(12)&&this.session.interactionAvailability(o).completed),cancelInteraction=this.menu.startsWith('interaction:')&&!completedInteraction||this.menu.startsWith('campaign-prerequisites:');this.pagePreparationRevision++;this.preparingPage=false;this.menu='';this.clearInput(false);if(!preserveAutomation)this.automation.resumeAfter('menu');if(cancelInteraction)this.automation.pause('manual');this.modalKey='';this.hud.clearModal();return;}
  if(action.startsWith('choice:')){const dialogue=this.session.state.dialogue?.id;this.process(this.session.choose(action.slice(7)));this.save();if(dialogue?.startsWith('campaign:')&&!this.session.state.dialogue){this.automation.resumeAfter('dialogue');const object=this.world.area.objects.find(o=>o.action==='campaign_event'&&o.eventId===dialogue.slice(9));if(object&&this.session.interactionAvailability(object).completed){this.menu='interaction:'+object.id;this.automation.pause('menu');}else if(action==='choice:cancel:campaign'){this.menu='';this.automation.pause('manual');}}this.modalKey='';this.renderModal();return;}
  if(action==='cancel-new'){this.open(this.returnToMainMenu?'title':'pause');return;}
  if(action==='new'){this.open('confirm-new');return;}
  if(action==='confirm-new'){const fresh=new GameSession(Date.now()%2147483646,this.query);fresh.enter(getArea('S01-T1'));this.applyPlaytestLevel(fresh);const r=this.temporaryMax?{ok:true,error:undefined,warning:undefined}:this.store.startFresh(fresh);if(!r.ok){this.say(r.error||'新旅程未创建');return;}if(r.warning)this.say(r.warning,8);this.returnToMainMenu=false;this.automation.stop();this.bossTravel=null;this.trackedTaskId=undefined;this.hud.clearEquipmentPickups();this.session=fresh;this.applyTemporaryMax();this.menu='';this.music?.start();void this.rebuild();return;}
  if(action==='retry'){this.menu='';this.process(this.session.retry());this.modalKey='';return;}
  if(action==='rest'){const ok=this.session.rest();this.say(ok?'已在检查点休整，生命、职业资源、各类药水已补满。':'在安全检查点旁才能休整。');this.save();this.modalKey='';this.renderModal();return;}
  if(action==='next'||action==='previous'){const pages=Math.max(1,Math.ceil(Object.keys(this.session.state.inventory).filter(id=>this.session.state.inventory[id]>0).length/6));this.page=Math.min(pages-1,Math.max(0,this.page+(action==='next'?1:-1)));this.modalKey='';this.renderModal();return;}
  if(action.startsWith('equipment-dice:')){const ok=this.session.openEquipmentDice(action.slice(15));if(ok)this.menu='';else this.say('这件装备已完成锻印，或当前无法处理装备。');this.save();this.modalKey='';this.renderModal();return;}
  if(action.startsWith('equip:')){const [,id,slot]=action.split(':');void this.equipPrepared(id,slot);return;}
  if(action.startsWith('buy:')){const ok=this.session.buy(this.merchant,action.slice(4));this.say(ok?'交易完成。':'金币、容量或库存不足。');this.save();this.modalKey='';this.renderModal();return;}
  if(action.startsWith('forge-submit:')){const [,id,token]=action.split(':'),q=this.session.forging.enhancement(id),ok=this.session.forging.enhance(id,token);this.say(ok?`${EQUIPMENT[id].name}已强化至＋${q.step!.rank}`:q.reason||'状态已变化，请重新确认强化费用。');this.open((ok?'forge-result:':'forge-item:')+id);return;}
  if(action.startsWith('forge-inherit:')){const [,from,to,token]=action.split(':'),q=this.session.forging.transfer(from,to),ok=this.session.forging.inherit(from,to,token);this.say(ok?'强化经验已传承，原装备与骰印保留。':q.reason||'状态已变化，请重新确认传承费用。');this.open(ok?'forge-item:'+to:`forge-transfer:${from}:${to}`);return;}
  if(action.startsWith('craft-submit:')){const [,recipe,token]=action.split(':'),q=this.session.forging.craft(recipe),ok=this.session.craft(recipe,token);this.say(ok?'装备锻造完成。':q.reason||'资源已变化，请重新确认费用。');this.open(ok?'forge-item:'+q.item:'craft-preview:'+recipe);return;}
  if(action==='forge-info')return;
  if(action.startsWith('craft:')){const ok=this.session.craft(action.slice(6));this.say(ok?'装备锻造完成。':'需要安全检查点、已学图纸与足够材料。');this.save();this.modalKey='';this.renderModal();return;}
  if(action.startsWith('map-travel:')){void this.travelFromMap(action.slice(11));return;}
  if(action.startsWith('atlas:')){this.hud.atlas(this.session,this.visited,action.slice(6));return;}
  this.page=0;this.open(action);
 }
 private async equipPrepared(id:string,slot?:string){
  const d=EQUIPMENT[id];if(!d||d.kind==='spell'||this.equipmentPreparing)return;
  const actors=this.actors,session=this.session;this.equipmentPreparing=true;recordEquipmentPreparing(session,id);this.modalKey='';this.renderModal();
  try{
   if(session.equipmentChange(id,slot).available&&['sword','bow','staff'].includes(d.kind)&&(actors instanceof Actors||actors instanceof Player3DActors))await actors.preparePlayerWeapon(id);
   if(this.destroyed||this.actors!==actors||this.session!==session)return;
   const change=session.equipmentChange(id,slot),ok=session.equip(id,slot);if(ok){actors?.update(session,0,false,true);await this.effects?.prepareEquipment(session);}
   if(this.destroyed||this.actors!==actors||this.session!==session)return;
   const message=ok?equipmentText('notice.equipped',{name:d.name}):equipmentChangeReason(change);
   recordEquipmentChange(session,id,message);this.say(message,4,ok?qualityFeedbackRole(d.quality):'text.normal');this.save();this.modalKey='';this.renderModal();
  }catch(error){if(!this.destroyed&&this.session===session){const message=equipmentText('notice.loadFailed');recordEquipmentChange(session,id,message);this.say(message,6);}}
  finally{this.equipmentPreparing=false;recordEquipmentPreparing(session);if(!this.destroyed&&this.session===session){this.modalKey='';this.renderModal();}}
 }
 private async applyProfessionPrepared(){
  if(this.menu!=='profession'||this.equipmentPreparing)return;const session=this.session,v=professionPreview(session);if(v.busy)return;
  const change=session.combatLoadoutChange(v.family,v.weapon);if(!change.available||!change.weapon||change.token!==v.token){professionBusy(session,false,change.reason);this.modalKey='';this.renderModal();return;}
  const actors=this.actors;professionBusy(session,true);this.equipmentPreparing=true;this.modalKey='';this.renderModal();
  try{
   if(session.state.equipment.weapon!==change.weapon&&(actors instanceof Actors||actors instanceof Player3DActors))await actors.preparePlayerWeapon(change.weapon);
   if(this.destroyed||this.session!==session||this.actors!==actors||this.menu!=='profession')return;
   const ok=session.applyCombatLoadout(change.family,change.weapon,change.token);
   if(ok){actors?.update(session,0,false,true);await this.effects?.prepareEquipment(session);if(this.destroyed||this.actors!==actors||this.session!==session)return;this.save();this.say(pt('profession.saved'));}
   professionBusy(session,false,pt(ok?'profession.saved':'profession.stale'));
  }catch{professionBusy(session,false,pt('profession.failed'));}
  finally{this.equipmentPreparing=false;professionBusy(session,false,professionPreview(session).notice);if(!this.destroyed&&this.session===session){this.modalKey='';this.renderModal();}}
 }
 private preparePage(load:()=>Promise<void>,commit?:()=>void){
  const revision=++this.pagePreparationRevision,session=this.session;this.preparingPage=true;
  void load().then(()=>{if(this.destroyed||revision!==this.pagePreparationRevision||session!==this.session)return;commit?.();this.preparingPage=false;this.modalKey='';this.renderModal();},error=>{if(this.destroyed||revision!==this.pagePreparationRevision)return;this.preparingPage=false;console.warn('[Chapter] Page prewarm failed',error);this.modalKey='';this.renderModal();});
 }
 private open(menu:string){
  this.pagePreparationRevision++;this.preparingPage=false;
  if(menu==='title')this.returnToMainMenu=false;else if(this.menu==='title')this.returnToMainMenu=true;
  if((menu==='inventory'||menu==='equipment')&&this.menu!=='inventory'&&this.menu!=='equipment')beginEquipmentVisit(this.session);
  if(menu.startsWith('allocation:')&&!this.menu.startsWith('allocation:'))beginAllocation(this.session);
  if(menu&&this.automation.destination?.bossKey)this.automation.pauseNavigation();
  this.hud.collapseAutomation();this.clearInput(true,'menu');if(!menu)this.automation.resumeAfter('menu');
  if(menu==='inventory'||menu==='equipment'||menu==='appearance'||menu==='profession'||menu.startsWith('allocation:'))this.session?.prepareEquipmentChange();
  if(menu)this.sceneInteraction?.update(null,true);this.menu=menu;this.modalKey='';this.save();
  if(this.session&&this.preparationResources?.needs(menu))this.preparePage(()=>this.preparationResources.page(this.session,menu));else this.renderModal();
 }
 private renderModal(){
  if(!this.hud||this.destroyed)return;
  if(this.authPromptVisible&&this.platform?.auth.state.status!=='failed'){this.authPromptVisible=false;this.hud.clearModal();this.modalKey='';}
  if(this.updatePromptVisible){const u=this.platform.updates,key='update:'+u.status+u.message;this.loadingScreen?.hide();this.dicePanel?.clear();if(this.modalKey!==key){this.modalKey=key;this.hud.show('游戏更新',u.message,u.ready?[{label:'保存并更新',action:'update:apply'},{label:'稍后',action:'update:later'}]:[]);}return;}
  if(this.startupFailure&&this.platform?.auth.ready){const key='startup:'+this.failure;if(this.modalKey!==key){this.modalKey=key;this.hud.show('暂时无法启程',this.failure+'\n本地进度已保留。',[{label:'重试载入',action:'resources:retry'}]);}return;}
  if(this.platform&&!this.platform.auth.ready){
   const state=this.platform.auth.state;
   if(state.status!=='failed'){
    // Keep the existing game/menu visible during foreground checks. Access
    // remains gated until the official host callback confirms the session.
    if(!this.session&&this.modalKey!=='auth:pending'){this.modalKey='auth:pending';this.loadingScreen?.show(-1,'正在准备旅途');}
    this.loadingScreen?.update();
    return;
   }
   this.loadingScreen?.hide();this.dicePanel?.clear();this.authPromptVisible=true;const key='auth:'+state.status+state.message;
   if(this.modalKey!==key){this.modalKey=key;showLoginScreen(this.hud,state);}
   return;
  }
  if(this.preparingPage)return;
  if(!this.session)return;
  if(!this.menu&&!this.loading&&!this.failure&&!this.campaignView?.active&&!this.automation.active)this.session.prepareEquipmentDice();
  if(this.hud.portrait){if(this.modalKey!=='portrait'){this.hud.clearModal();this.modalKey='portrait';}return;}
  const s=this.session.state,d=s.dialogue;
  // Simulation revision changes every frame. Empty gameplay has no menu data
  // to refresh; still check pending equipment dice before taking this path.
  if(!this.menu&&!d&&s.status!=='dead'&&!s.dice.active&&!this.loading&&!this.failure){
   if(this.modalKey!=='gameplay'){
    this.modalKey='gameplay';this.dicePanel?.clear();
    renderMenu(this.hud,this.session,'',false,'',this.page,this.merchant,this.visited,this.saved);
   }
   return;
  }
  if(this.menu==='bosses'&&!d&&s.status!=='dead'&&!s.dice.active&&!this.loading&&!this.failure){
   if(this.modalKey!=='bosses'||!this.bossPanel?.valid){this.bossPanel=new BossPanel(this.hud,this.session,this.bosses,this.bossPanel?.selectedKey);this.modalKey='bosses';}
   return;
  }
  const timedInteraction=this.menu.startsWith('interaction:')&&this.world.area.objects.some(o=>o.id===this.menu.slice(12)&&o.action==='growing_rematch');
  const key=[this.menu,d?.id,d?.text,s.status,this.loading,this.failure,this.page,s.revision,timedInteraction?Math.floor(Date.now()/1000):''].join('|');if(this.modalKey===key)return;this.modalKey=key;this.hud.hairstyles=this.actors instanceof Player3DActors?this.actors.player.playerHairstyles():this.actors instanceof Actors?this.actors.playerHairstyles():[];const check=this.session.diceView();if(check&&!this.loading&&!this.failure){this.clearInput(true,'dice');this.dicePanel.show(check);return;}this.dicePanel?.clear();if(d)this.clearInput(true,'dialogue');if(this.trainingRange&&(this.menu==='training-range'||s.status==='dead')){renderTrainingRange(this.hud,this.trainingRange);return;}if(this.skillDebugAvailable&&this.menu==='skill-effect-debug'&&!d&&s.status!=='dead'){this.skillEffectDebug.render(this.hud,this.session,!!this.trainingRange);return;}renderMenu(this.hud,this.session,this.menu,this.loading,this.failure,this.page,this.merchant,this.visited,this.saved,this.platform.updates.ready,this.platform.auth.state.status==='guest',this.music?.label,this.skillDebugAvailable);}
 private controlForKey(code:number):string|undefined {
  const slots:Record<number,string>={[KeyCode.KEY_Q]:'combat0',[KeyCode.KEY_E]:'combat1',[KeyCode.KEY_R]:'combat2',[KeyCode.KEY_T]:'combat3',[KeyCode.DIGIT_1]:'combat0',[KeyCode.DIGIT_2]:'combat1',[KeyCode.DIGIT_3]:'combat2',[KeyCode.DIGIT_4]:'combat3',[KeyCode.KEY_G]:'ultimate'};
  return slots[code];
 }
 private skillForControl(control:string|null){
  const combat=this.session?.state.combat;if(!combat||!control)return null;
  const id=control==='ultimate'?combat.ultimate:control.startsWith('combat')?combat.activeSlots[Number(control.slice(6))]:null;
  const def=id?COMBAT_SKILLS[id]:null,rank=id?allocatedSkillRank(this.session.state.progression,id):null;
  return def&&rank?{id:id!,def,rank}:null;
 }
 private beginAim(control:string){
  this.takeControl();
  const info=this.skillForControl(control),view=this.session.combatSkillView().find(v=>v.id===info?.id);
  if(!info||!view?.ready){this.say(!view?.unlocked?'尚未达到技能解锁等级':!view.compatible?skillWeaponRequirement(info.def):!view.resourceEnough?`${resourceProfile(this.session.state).name}不足，需要${view.resourceCost}点；可普攻或使用药水`:'技能冷却或释放间隔中');return false;}
  this.aiming=control;this.aimGesture=null;this.manualSkillAim=this.hud.skillAimMode==='manual';
  const p=this.session.state.player,self=!info.def.offensive||info.def.targetingMode==='self'||info.rank.geometry?.kind.startsWith('self');
  if(self)this.aimTarget={x:p.x,z:p.z};
  else if(!this.manualSkillAim)this.aimTarget=this.session.skillAutoAimTarget(info.id);
  else if(this.session.state.time-this.lastAimTime>=5||!this.aimTarget){
   this.aimTarget={x:p.x+Math.sin(p.angle)*info.rank.castRangeMetres*.72,z:p.z+Math.cos(p.angle)*info.rank.castRangeMetres*.72};
  }
  return true;
 }
 private finishAim(control:string){
  if(this.aiming!==control)return;const info=this.skillForControl(control),target=this.previewTarget();
  this.aiming=null;this.aimGesture=null;this.manualSkillAim=false;this.hud.setAimCancelVisible(false);
  if(!info)return;
  const p=this.session.state.player,angle=distance(p,target)>.001?Math.atan2(target.x-p.x,target.z-p.z):p.angle;
  this.mouseAim=angle;this.lastAimTime=this.session.state.time;
  this.combatFocus={target:{...target},skillId:info.id,rank:info.rank.rank,until:this.session.state.time+1.5};
  this.process(this.session.castSkill(info.id,target,angle));
 }
 private cancelAim(){this.takeControl();this.aiming=null;this.aimGesture=null;if(this.skillPress)this.touches.end(this.skillPress.id,true);this.skillPress=null;this.hud.hideSkillDescription();this.manualSkillAim=false;this.heldAttack=false;this.session.cancelInput();this.hud.setAimCancelVisible(false);}
 /** Creator exposes touch phases for both mouse/trackpad and fingers, but no native long-press event. */
 private updateSkillPress(dt:number,paused:boolean):void{
  const press=this.skillPress;if(!press)return;
  if(paused||this.session.state.status==='dead'){this.clearInput(false);return;}
  if(press.dragged||press.inspecting)return;
  press.elapsed+=Math.max(0,dt);if(press.elapsed<3.6)return;
  press.inspecting=true;
  if(this.aimGesture?.id===press.id){this.aiming=null;this.aimGesture=null;this.manualSkillAim=false;this.effects?.clearAim();this.hud.setAimCancelVisible(false);}
  this.hud.setAttackRangeHint('');this.hud.showSkillDescription(this.session,press.control);
 }
 private updateAimCancel(paused=false){
  // Only the pointer that has actually dragged an aim gets a drop target.
  // Automatic bow charging and keyboard/mouse world attacks own no such drag.
  this.hud.setAimCancelVisible(!paused&&this.session.state.status!=='dead'&&!!this.aimGesture?.manual&&(!!this.aiming||this.heldAttack&&this.session.state.action?.kind==='bowAim'));
 }
 private keyDown(e:EventKeyboard){
  if(this.background)return;
  this.music?.gesture();
  if(this.updatePromptVisible||!this.platform?.auth.ready||!this.session){if(e.keyCode===KeyCode.ENTER&&this.platform?.auth.state.status==='failed')void this.ensureAccess();return;}
  if(this.loading||this.hud?.portrait)return;
  if(this.session?.state.dice.active){
   if(this.diceKeys.has(e.keyCode))return;this.diceKeys.add(e.keyCode);const v=this.session.diceView()!;
   if(e.keyCode===KeyCode.ENTER||e.keyCode===KeyCode.SPACE)this.click(v.roll?'dice:continue':'dice:roll');
   if(e.keyCode===KeyCode.KEY_R&&v.canReroll)this.click('dice:reroll');
   if(e.keyCode===KeyCode.KEY_G&&!v.roll)this.click('dice:help');
   if(e.keyCode===KeyCode.ESCAPE&&v.canCancel)this.click('dice:cancel');return;
  }
  if(this.campaignView?.active&&!this.menu){if(e.keyCode===KeyCode.ESCAPE)this.click('campaign:skip');else if(e.keyCode===KeyCode.ENTER||e.keyCode===KeyCode.SPACE)this.click('campaign:next');return;}
  if(e.keyCode===KeyCode.F8&&this.skillDebugAvailable){this.click(this.menu==='skill-effect-debug'?'close':'skill-effect-debug');return;}
  if(e.keyCode===KeyCode.ESCAPE&&this.aiming){this.cancelAim();return;}
  if(e.keyCode===KeyCode.KEY_C){this.click(this.menu==='checks'?'close':'checks');return;}
  if(e.keyCode===KeyCode.KEY_V){this.click(this.menu==='attributes'?'close':'attributes');return;}
  if(e.keyCode===KeyCode.ESCAPE){if(!this.menu&&this.hud.automationExpanded){this.hud.collapseAutomation();return;}this.clearInput(false);this.click(this.menu?'close':'pause');return;}
  if(e.keyCode===KeyCode.KEY_M){this.click(this.menu==='map'?'close':'map');return;}
  if(this.menu==='map'&&this.hud.atlasKey(e.keyCode))return;
  if(e.keyCode===KeyCode.KEY_N){this.click(this.menu.startsWith('journey')?'close':'journey');return;}
  if(e.keyCode===KeyCode.KEY_B){this.click(this.menu==='inventory'?'close':'inventory');return;}
  if(this.menu||this.session?.state.dialogue){if(e.keyCode===KeyCode.ENTER&&this.menu==='title')this.click('begin');return;}
  if(this.keys.has(e.keyCode))return;this.keys.add(e.keyCode);
  if(e.keyCode===KeyCode.KEY_J)this.manualBasicAim=false;
  const automatic:{[key:number]:string}={[KeyCode.KEY_P]:'navigate',[KeyCode.KEY_Y]:'quest',[KeyCode.KEY_H]:'idle'};
  if(automatic[e.keyCode]){this.click('auto:'+automatic[e.keyCode]);this.keys.add(e.keyCode);return;}
  if([KeyCode.KEY_W,KeyCode.KEY_A,KeyCode.KEY_S,KeyCode.KEY_D,KeyCode.KEY_J,KeyCode.KEY_F,KeyCode.SPACE].includes(e.keyCode))this.takeControl();
  if(e.keyCode===KeyCode.DIGIT_5){this.click('potion-health');return;}
  if(e.keyCode===KeyCode.DIGIT_6){this.click('potion-resource');return;}
  if(e.keyCode===KeyCode.KEY_F)this.interact();
  if(e.keyCode===KeyCode.SPACE)this.pulse.dash=true;
  const control=this.controlForKey(e.keyCode);if(control)this.beginAim(control);
 }
 private keyUp(e:EventKeyboard){
  this.diceKeys.delete(e.keyCode);this.keys.delete(e.keyCode);
  if(this.background||this.updatePromptVisible||!this.platform?.auth.ready||!this.session)return;
  if(this.menu||this.session?.state.dialogue||this.session?.state.dice.active)return;
  const control=this.controlForKey(e.keyCode);if(control)this.finishAim(control);
 }
 private isUI(e:EventMouse){return this.hud.isOverUI(e.getLocation())||!!this.sceneInteraction?.isOverUI(e.getLocation());}
 private mouseDown(e:EventMouse){
  if(this.background)return;this.music?.gesture();if(this.updatePromptVisible||!this.platform?.auth.ready||!this.session)return;
  // Creator dispatches a simulated touch before the corresponding mouse down.
  // An outside click that dismissed the flyout must not also begin an attack.
  if(e.getButton()===EventMouse.BUTTON_LEFT&&this.automationDismissedTouch){this.automationDismissedTouch=false;return;}
  if(e.getButton()===EventMouse.BUTTON_LEFT&&this.hud.automationExpanded&&!this.hud.isOverAutomation(e.getLocation())){const overUI=this.isUI(e);this.hud.collapseAutomation();if(!overUI)return;}
  if(!this.campaignView?.active&&!this.loading&&!this.failure&&!this.menu&&!this.session.state.dialogue&&!this.session.state.dice.active&&e.getButton()===EventMouse.BUTTON_LEFT&&!this.isUI(e)){this.takeControl();this.heldAttack=true;this.manualBasicAim=true;this.mouseMove(e);}if(e.getButton()===EventMouse.BUTTON_RIGHT)this.cancelAim();
 }
 private mouseUp(e:EventMouse){if(e.getButton()===EventMouse.BUTTON_LEFT)this.heldAttack=false;}
 private mouseMove(e:EventMouse){
  if(this.background||!this.platform?.auth.ready||!this.camera||!this.session||this.menu||this.loading||this.aimGesture||this.isUI(e))return;
  const p=e.getLocation(),ray=this.camera.screenPointToRay(p.x,p.y),physics=PhysicsSystem.instance;this.world?.syncPhysics();
  // Group 4 is the real walk surface, including bridges and elevated ramps.
  // Intersecting y=0 moves the cursor several metres off target on high ground.
  if(!physics.raycastClosest(ray,4,this.camera.far,false))return;
  const {x,z}=physics.raycastClosestResult.hitPoint,v=this.session.state.player;
  this.aimTarget={x,z};this.mouseAim=Math.atan2(x-v.x,z-v.z);this.lastAimTime=this.session.state.time;
  if(this.aiming)this.manualSkillAim=true;
  else if(this.heldAttack||this.keys.has(KeyCode.KEY_J)||this.session.state.action?.kind==='bowAim')this.manualBasicAim=true;
 }
 /** Keep the joystick finger on Cocos' global input stream, even outside its starting node. */
 private movementTouch(event:EventTouch){
  const code=event.getEventCode(),phase=code===Input.EventType.TOUCH_START?'start':code===Input.EventType.TOUCH_MOVE?'move':code===Input.EventType.TOUCH_END?'end':'cancel';
  if(phase!=='move')this.automationDismissedTouch=false;
  for(const touch of event.getTouches()){
   if(phase==='start'&&this.hud?.automationExpanded&&!this.hud.isOverAutomation(touch.getLocation())){this.automationDismissedTouch=!this.hud.isOverUI(touch.getLocation());this.hud.collapseAutomation();}
   if(phase==='start'?!this.hud?.isJoystickTouch(touch.getLocation()):this.touches.owner(touch.getID())!=='move')continue;
   const owned=new EventTouch([touch],false,code);owned.touch=touch;this.touch('move',phase,owned);
  }
 }
 private touch(control:string,phase:string,e:EventTouch){
  if(this.background)return;
  if(phase==='start')this.music?.gesture();
  if(this.updatePromptVisible||!this.platform?.auth.ready||!this.session)return;
    if(this.campaignView?.active||this.menu||this.session.state.dialogue||this.session.state.dice.active||this.loading||this.hud.portrait)return;
  const id=e.getID();
  // Cocos changes node event.type to TOUCH_CANCEL for a real release outside
  // the starting button. Its original input code still distinguishes that
  // release from an OS cancellation; owned aiming drags must finish there.
  if(phase==='cancel'&&e.getEventCode()===Input.EventType.TOUCH_END&&(control==='move'||this.aimGesture?.id===id))phase='end';
  if(phase==='start'){
   if(!this.touches.begin(id,control))return;
   this.takeControl();
   if(this.hud.isDescribableSkill(control)){const p=e.getUILocation();this.skillPress={id,control,start:{x:p.x,z:p.y},elapsed:0,dragged:false,inspecting:false,usable:this.hud.isControlReady(control)};}
   if(control==='attack'){this.heldAttack=true;this.manualBasicAim=false;}if(control==='move')this.lastAimTime=-999;
   const skill=control.startsWith('combat')||control==='ultimate';
   if(skill&&this.skillPress?.usable&&this.beginAim(control)||control==='attack'){
    const pos=e.getUILocation(),info=this.skillForControl(control),p=this.session.state.player,right=this.camera.node.right,up=this.camera.node.up;
    const anchor=info?p:skill?this.previewTarget():{x:p.x+Math.sin(p.angle)*6,z:p.z+Math.cos(p.angle)*6};
    this.aimGesture={id,start:{x:pos.x,z:pos.y},anchor:{x:anchor.x,z:anchor.z},right:{x:right.x,z:right.z},up:{x:up.x,z:up.z},scale:(info?.rank.castRangeMetres??8)/220,manual:false};
   }
  }
  if(this.touches.owner(id)!==control)return;
  const press=this.skillPress?.id===id?this.skillPress:null;
  if(press){
   if(press.inspecting){if(phase==='end'||phase==='cancel'){this.touches.end(id,true);this.skillPress=null;this.hud.hideSkillDescription();}return;}
   if(phase==='move'||phase==='end'){const p=e.getUILocation();if(Math.hypot(p.x-press.start.x,p.y-press.start.z)>this.hud.touchTargetSize/6)press.dragged=true;}
   if(phase==='end'||phase==='cancel'){this.skillPress=null;if(!press.usable){this.touches.end(id,true);return;}}
  }
  if(control==='move'&&(phase==='move'||phase==='start')){
   const p=this.hud.touchPosition(this.hud.joystick.parent!,e),radius=this.hud.joystickRadius;this.touches.move(id,p.x/radius,p.y/radius);
   const v=this.touches.vector();this.hud.joystick.setPosition(v.x*radius,v.z*radius,0);
  }
  if((phase==='move'||phase==='end')&&this.aimGesture?.id===id){
   const p=e.getUILocation(),g=this.aimGesture,dx=p.x-g.start.x,dy=p.y-g.start.z;
   if(g.manual||Math.hypot(dx,dy)>this.hud.touchTargetSize/6){
    g.manual=true;if(this.aiming)this.manualSkillAim=true;else if(control==='attack')this.manualBasicAim=true;
    this.aimTarget={x:g.anchor.x+(g.right.x*dx+g.up.x*dy)*g.scale,z:g.anchor.z+(g.right.z*dx+g.up.z*dy)*g.scale};
    const actor=this.session.state.player,info=this.skillForControl(this.aiming),d=distance(actor,this.aimTarget);
    if(info&&d>info.rank.castRangeMetres){const scale=info.rank.castRangeMetres/d;this.aimTarget={x:actor.x+(this.aimTarget.x-actor.x)*scale,z:actor.z+(this.aimTarget.z-actor.z)*scale};}
    this.mouseAim=Math.atan2(this.aimTarget.x-actor.x,this.aimTarget.z-actor.z);this.lastAimTime=this.session.state.time;
   }
  }
  this.updateAimCancel();
  const pos=e.getUILocation(),cancel=this.hud.cancel,bounds=cancel.getComponent(UITransform)!;
  const overCancel=this.aimGesture?.id===id&&cancel.active&&Math.abs(pos.x-this.hud.width/2-cancel.position.x)<bounds.width/2&&Math.abs(pos.y-this.hud.height/2-cancel.position.y)<bounds.height/2;
  if(phase==='cancel'||phase==='end'&&overCancel){this.touches.end(id,true);if(control==='move')this.hud.joystick.setPosition(0,0,0);else this.cancelAim();return;}
  if(phase==='end'){
   const action=this.touches.end(id,false);
   if(control==='move')this.hud.joystick.setPosition(0,0,0);
   if(control==='attack'){this.heldAttack=false;this.aimGesture=null;this.hud.setAimCancelVisible(false);}
   if(action==='dash')this.pulse.dash=true;
   if(action?.startsWith('combat')||action==='ultimate')this.finishAim(action);
   if(action==='potion-health'||action==='potion-focus'||action==='potion-resource')this.click(action);
  }
 }
 private previewTarget():Point {
  const p=this.session.state.player,info=this.skillForControl(this.aiming);
  if(info&&(!info.def.offensive||info.def.targetingMode==='self'||info.rank.geometry?.kind.startsWith('self')))return {x:p.x,z:p.z};
  if(info&&!this.manualSkillAim){this.aimTarget=this.session.skillAutoAimTarget(info.id);if(this.aimTarget)return {...this.aimTarget};}
  const range=info?.rank.castRangeMetres??8;
  if(info?.rank.geometry?.kind.startsWith('melee')){
   const raw=this.aimTarget??{x:p.x+Math.sin(p.angle)*range,z:p.z+Math.cos(p.angle)*range},d=distance(p,raw);
   return d>range&&d>.001?{x:p.x+(raw.x-p.x)*range/d,z:p.z+(raw.z-p.z)*range/d}:{...raw};
  }
  return this.aimTarget?{...this.aimTarget}:{x:p.x+Math.sin(p.angle)*range*.72,z:p.z+Math.cos(p.angle)*range*.72};
 }
 private mouseWheel(e:EventMouse){if(this.campaignView?.active)return;if(this.updatePromptVisible||!this.platform?.auth.ready||!this.session)return;if(this.menu||this.session?.state.dialogue||this.session?.state.dice.active||this.isUI(e))return;this.manualCameraHeight=Math.max(3.6,Math.min(13.5,this.manualCameraHeight*(e.getScrollY()>0?.9:1/.9)));}
 private configureLighting(kind:string){
  const ambient=director.getScene()!.globals.ambient,indoor=kind==='interior',underground=kind==='underground';Tween.stopAllByTarget(this.camera);
  this.manualCameraHeight=indoor||underground?4.3:4.6;this.camera.orthoHeight=this.manualCameraHeight;
  this.keyLight.illuminance=indoor?38000:underground?22000:50000;this.keyLight.color=indoor?new Color(255,234,203):underground?new Color(250,233,209):new Color(255,240,215);
  // Warm daylight supplies golden lit faces; a restrained, near-neutral
  // hemisphere retains cooler shadows without baking yellow into the albedo.
  // Vertical faces receive the sky/ground midpoint in Cocos' hemisphere model;
  // lift the lower hemisphere as well as the sky so faces read above dark floors.
  ambient.skyColor=indoor?new Vec4(.78,.79,.81,1):underground?new Vec4(.63,.64,.67,1):new Vec4(.75,.79,.84,1);
  ambient.skyIllum=indoor?27000:underground?17000:25000;
  ambient.groundAlbedo=indoor?new Vec4(.44,.43,.41,1):underground?new Vec4(.36,.35,.34,1):new Vec4(.43,.43,.42,1);
 }
 private encounterDirection(){
  if(this.encounterTime+1e-6<.2)return this.encounterText;
  this.encounterTime=0;this.encounterText=this.calculateEncounterDirection();return this.encounterText;
 }
 private calculateEncounterDirection(){
  const s=this.session.state,p=s.player,battle=this.session.campaign.battleHint(),boss=nearestBoss(this.session);let enemy=boss;
  if(!enemy){let best=Infinity;for(const candidate of s.enemies)if(candidate.hp>0){const metres=distance(candidate,p);if(metres<best){enemy=candidate;best=metres;}}}
  if(!enemy)return ['S01','S01-T1'].includes(s.area)?'':battle;
  const d=distance(enemy,p);if(d<6)return battle;
  const dx=enemy.x-p.x,dz=enemy.z-p.z,r=this.camera.node.right,u=this.camera.node.up,angle=Math.atan2(dx*r.x+dz*r.z,dx*u.x+dz*u.z),arrows=['↑','↗','→','↘','↓','↙','←','↖'];
  if(boss&&d<=35&&(boss.phase!=='idle'||boss.hp<boss.maxHp||(s.combat.buffs[`aggro:${boss.id}`]??0)>s.time))return battle;
  return `${battle?battle+'\n':''}${arrows[(Math.round(angle/(Math.PI/4))+8)%8]} ${boss?`${bossKind(boss)==='elite'?'精英':'首领'} · ${bossName(boss)}`:enemy.respawnSeconds?'野外怪群':'敌方阵地'} · ${Math.ceil(d)}米`;
 }
 private updateCampaign(dt:number){
  if(this.trainingRange)return false;
  const allowed=!this.menu&&!this.loading&&!this.failure&&!this.hud.portrait&&!this.session.state.dialogue&&!this.session.state.dice.active&&this.session.state.status!=='dead';
  if(allowed&&!this.campaignView?.active){const scene=this.session.campaign.pending()[0];if(scene){this.clearInput(true,'story');this.effects?.clear(true);this.save();this.campaignView?.start(scene);}}
  if(this.campaignView?.active)this.clearInput(true,'story');
  if(!this.campaignView?.update(dt,allowed))return false;
  this.actors?.update(this.session,0,false,true);this.enemyFeedback?.update(this.session,true);this.flatWorld?.update(this.camera,this.session);this.nativePortals?.update(this.camera,this.session);this.portalHud?.update(this.session,true);this.taskPresence?.update(this.session,this.hud.activeGuidance,true);this.hud.refreshMiniMap(this.session,this.camera,true);this.sceneInteraction?.update(null,true);return true;
 }
 private positionCamera(dt:number){
  if(!this.camera||!this.session)return;
  if(dt<1&&(this.menu||this.loading||this.failure||this.session.state.dialogue||this.session.state.dice.active))return;
  const s=this.session.state,p=s.player,height=(point:Point)=>this.world?.height(point)??0,y=height(p);
  const position=this.camera.node.position;
  // Ordinary follow uses a fixed bearing. Restore it after cinematics, without
  // dirtying the camera and every camera-facing sprite twice on every frame.
  if(!Quat.equals(this.camera.node.rotation,this.followCameraRotation))this.camera.node.setRotation(this.followCameraRotation);
  // Painted-world follow frames only the player, except the S02 discovery.
  // Target/cover searches below affect native 3D framing; running their physics
  // rays for the fixed painted-world frame was discarded work during combat.
  const discovery=this.flatMode&&s.area==='S02'&&!s.receipts['journey:hunt:S02'],targetFraming=!this.flatMode||discovery;
  const info=targetFraming?this.skillForControl(this.aiming):undefined,focus=targetFraming&&this.combatFocus&&this.combatFocus.until>s.time?this.combatFocus:null;
  let rank=info?.rank??(focus?COMBAT_SKILLS[focus.skillId]?.ranks[focus.rank-1]:undefined),target=info?this.previewTarget():focus?.target;
  const closeWeapon=EQUIPMENT[s.equipment.weapon]?.kind==='sword',melee=rank?!!rank.geometry?.kind.startsWith('melee')||!!rank.geometry?.kind.startsWith('self')&&closeWeapon:closeWeapon;
  // Keep quiet exit approaches clear of the bottom HUD; active combat still frames its targets.
  const quiet=!info&&!focus&&!s.action&&p.hurtTime<=0&&!this.heldAttack&&!this.keys.has(KeyCode.KEY_J);
  const closeThreat=targetFraming&&(s.enemies.some(e=>e.hp>0&&distance(e,p)<7&&this.world.visible(p,e))
   ||s.projectiles.some(q=>q.owner==='enemy'&&distance(q,p)<7));
  const exitApproach=quiet&&!closeThreat&&this.world.area.exits.some(e=>distance(e,p)<=3.2);
  let enemy:typeof s.enemies[number]|undefined,best=discovery?18:melee?7:23;
  if(targetFraming&&!exitApproach)for(const candidate of s.enemies){if(candidate.hp<=0)continue;const metres=distance(candidate,p);if(metres>=best||!this.world.visible(p,candidate))continue;best=metres;enemy=candidate;}
  if(!target&&enemy)target=enemy;
  if(target&&rank&&distance(p,target)>rank.castRangeMetres&&rank.castRangeMetres>0){const d=distance(p,target);target={x:p.x+(target.x-p.x)/d*rank.castRangeMetres,z:p.z+(target.z-p.z)/d*rank.castRangeMetres};}
  const angle=target&&distance(p,target)>.001?Math.atan2(target.x-p.x,target.z-p.z):p.angle;
  // Flat characters and cursor aiming share one stable camera plane. Framing
  // each draw/release range moves that plane under the cursor and pumps zoom.
  // Keep manual wheel zoom; follow the player without cast-driven reframing.
  const points=skillFramingPoints(p,this.flatMode?p:target??p,angle,this.flatMode?undefined:rank,height);
  if(this.trainingRange?.groupMode)for(const point of this.trainingRange.framingPoints)points.push(new Vec3(point.x,height(point),point.z),new Vec3(point.x,height(point)+2.2,point.z));
  if((!this.flatMode&&!rank||discovery)&&enemy)points.push(new Vec3(enemy.x,height(enemy)+1.1,enemy.z));
  const combat=!!enemy||!!info||!!focus,baseHeight=discovery&&enemy?Math.max(7.2,this.manualCameraHeight):!this.flatMode&&combat?Math.max(melee?4.8:6.8,this.manualCameraHeight):this.manualCameraHeight;
  // A stable view for the whole wave battle fits reinforcements before they
  // spawn. This does not reframe on each skill or change the saved manual zoom.
  const minHeight=this.session.campaign.battleReady()?baseHeight:Math.max(6.2,baseHeight);
  const frame=rangedCameraFrame(this.camera,points,p,y,this.hud.width/this.hud.height,minHeight);
  const desired=new Vec3(frame.focus.x+15,y+20,frame.focus.z+18),weight=dt>=1?1:1-Math.exp(-dt*7);
  Vec3.lerp(this.followCameraPosition,position,desired,weight);
  if(!Vec3.strictEquals(position,this.followCameraPosition))this.camera.node.setPosition(this.followCameraPosition);
  const heightDelta=(frame.height-this.camera.orthoHeight)*weight;if(heightDelta!==0)this.camera.orthoHeight+=heightDelta;
 }
 update(dt:number){if(this.background)return;if(this.resetFrameTime){dt=0;this.resetFrameTime=false;}this.impact?.beforeCamera();this.music?.update(dt,!!this.platform?.auth.ready&&!!this.session&&this.menu!=='title'&&!this.updatePromptVisible&&!this.failure,!!this.menu||this.loading||!!this.session?.state.dialogue||!!this.session?.state.dice.active||!!this.campaignView?.active||this.session?.state.status==='dead');if(this.hud?.resize()){this.clearInput(false);this.modalKey='';this.renderModal();}this.hud?.updateEquipmentPickups(Math.min(dt,.1),!!this.session&&!!this.world&&!!this.platform?.auth.ready&&!this.updatePromptVisible&&!this.loading&&!this.failure&&!this.menu&&!this.session.state.dialogue&&!this.session.state.dice.active&&!this.campaignView?.active&&this.session.state.status!=='dead',this.session);if(this.updatePromptVisible){this.clearInput();this.renderModal();return;}if(this.platform&&!this.platform.auth.ready){this.sceneInteraction?.update(null,true);this.campaignView?.suspend();this.clearInput(true,'auth');this.renderModal();return;}this.loadingScreen?.update(dt);if(!this.session||!this.world||!this.hud)return;if(this.updateCampaign(dt)){this.impact?.clear();return;}this.positionCamera(Math.min(dt,.1));this.flatWorld?.update(this.camera,this.session);this.nativePortals?.update(this.camera,this.session);this.world.presentation?.update(this.session);this.toastTime-=dt;if(this.toastTime<=0)this.toast='';this.autosave.advance(dt);
  const v=this.touches.vector(),sx=(this.keys.has(KeyCode.KEY_D)?1:0)-(this.keys.has(KeyCode.KEY_A)?1:0)+v.x,sz=(this.keys.has(KeyCode.KEY_W)?1:0)-(this.keys.has(KeyCode.KEY_S)?1:0)+v.z,right=this.camera.node.right,up=this.camera.node.up;let x=right.x*sx+up.x*sz,z=right.z*sx+up.z*sz;const length=Math.hypot(x,z),walk=this.keys.has(KeyCode.SHIFT_LEFT)||this.keys.has(KeyCode.SHIFT_RIGHT);let moveAmount=Math.min(1,Math.hypot(sx,sz))*(walk?(!this.flatMode||this.modelPlayer?MODEL_WALK_SPEED/MODEL_RUN_SPEED:.48):1);if(length>0){x=x/length*moveAmount;z=z/length*moveAmount;}
  let paused=this.hud.portrait||this.menu||this.loading||this.failure||this.session.state.dialogue||this.session.state.dice.active;
  this.updateSkillPress(dt,!!paused);
  if(this.session.state.status==='dead')this.automation.stop();
  const hold:AutomationPause|null=this.hud.portrait?'portrait':this.failure?'failure':this.menu&&this.menu!=='automation'?'menu':this.session.state.dialogue?'dialogue':this.session.state.dice.active?'dice':null;
  if(hold)this.automation.pause(hold);else if(['menu','dialogue','dice'].includes(this.automation.pauseReason??''))this.automation.resume();
  if(!paused){const attack=this.heldAttack||this.keys.has(KeyCode.KEY_J),p=this.session.state.player,basic=(!this.automation.active||length>.05)&&(attack||this.session.state.action?.kind==='bowAim');
   // Movement and stale skill/cursor directions must not override an automatic
   // basic attack. Keep resolving through the bow's release frame as well.
   const target=basic?(this.manualBasicAim?this.aimTarget:this.session.basicAutoAimTarget()):undefined;
   const aim=basic?target?Math.atan2(target.x-p.x,target.z-p.z):undefined:this.session.state.time-this.lastAimTime<5?this.mouseAim:undefined;
   let frame:InputFrame={x,z,aim,attack,...this.pulse};
   if(this.automation.active&&length>.05)this.takeControl();
   if(this.automation.active){
    const destination=this.automation.destination;
    if(destination?.bossKey&&this.bossTravelArea!==this.session.state.area){
     this.bossTravelArea=this.session.state.area;const fresh=this.bosses.navigation(this.session,destination.bossKey,this.query);
     if(fresh){this.automation.destination=fresh;this.bossTravel=fresh;this.guideTime=1;}else this.automation.pauseNavigation(bossText('blocked'));
    }
    const step=this.automation.update(this.session,this.query,AREAS,Math.min(dt,.1));frame=step.input;if(step.notice)this.say(step.notice,6);
    if(step.pickup)this.process(this.session.pickupLoot(step.pickup));
    if(step.interact)this.arrivalInteraction(step.interact);
    if(step.travel){const events=this.session.travel(step.travel),travelled=events.some(e=>e.type==='travel');if(!travelled){this.automation.pause('blocked',autoText('pause.blocked'));this.session.cancelInput();}this.process(events);this.pulse={};if(travelled)return;}
   }
   paused=this.hud.portrait||this.menu||this.loading||this.failure||this.session.state.dialogue||this.session.state.dice.active;
   x=paused?0:frame.x;z=paused?0:frame.z;moveAmount=Math.hypot(x,z);
   if(!paused){this.trainingRange?.prepareFrame();this.process(this.session.advance(Math.min(dt,.1),frame,this.automation.active&&this.automation.mode==='idle'));}this.pulse={};
  }
  if(!paused&&!this.trainingRange&&!this.automation.active&&!this.heldAttack&&!this.aiming&&!this.keys.has(KeyCode.KEY_J)){
   const s=this.session.state,p=s.player,target=this.sceneInteraction?.approach(this.world.area.objects,p,Math.min(dt,.1),o=>this.session.approachInteractionVisible(o)&&this.session.canApproachInteraction()&&this.world.visible(p,o)&&Math.abs(this.world.height(p)-this.world.height(o))<1.2,this.hud.activeGuidance?.targetId);
   if(target){this.arrivalInteraction(target.id);paused=this.menu||s.dialogue||s.dice.active;x=0;z=0;moveAmount=0;}
  }
  if(this.autosave.due(this.session.dirty))this.save();
  this.actors?.update(this.session,Math.min(dt,.1),!paused&&moveAmount>.1,!!paused,moveAmount);
  this.groundLootView?.update(this.session,!paused&&this.session.state.status!=='dead');
  this.impact?.update(dt,this.session,!!paused);
  const daily=this.session.huntingExperience();
  this.hud.setAutomation(this.automation.mode,!!this.automation.destination,this.automation.status,!paused&&this.session.state.status!=='dead',this.automation.paused,(this.automation.destination??this.automation.pausedDestination)?.taskId,daily);
  this.enemyFeedback?.update(this.session,!!paused);
  const target=this.aiming?this.previewTarget():null,info=this.skillForControl(this.aiming);
  const s=this.session.state,p=s.player,a=s.action,basic=!this.aiming&&(a?!a.skillId&&['sword','bowAim','bow','staff'].includes(a.kind):this.heldAttack||this.keys.has(KeyCode.KEY_J));
  let range:AttackRangePreview|undefined,rangeHint='';
  if(!paused&&s.status!=='dead'&&(basic||target&&info)){
   const profile=this.session.basicAttackProfile(),radius=info?.rank.castRangeMetres??profile.rangeMetres,melee=basic&&profile.angleDegrees>0;
   const point=target,angle=basic?(a?.angle??p.angle):point?Math.atan2(point.x-p.x,point.z-p.z):p.angle;
   const endpoint=point??{x:p.x+Math.sin(angle)*radius,z:p.z+Math.cos(angle)*radius},outside=distance(p,endpoint)>radius+.001;
   const reachable=this.world.visible(p,endpoint)&&Math.abs(this.world.height(p)-this.world.height(endpoint))<1.2,valid=!outside&&reachable;
   if(radius>0){range={rangeMetres:radius,angle,valid,angleDegrees:melee?profile.angleDegrees:0,target:basic?endpoint:undefined};rangeHint=`${info?this.manualSkillAim?'手动瞄准':'自动瞄准':'攻击距离'} ${radius}米${outside?' · 超出射程':!reachable?' · 路线受阻':melee?' · 前方扇形':''}`;}
  }
  this.hud.setAttackRangeHint(rangeHint,range?.valid);
  this.guideTime+=dt;if(this.world.area.id===s.area&&(this.guideTime>=.4||this.guideArea!==s.area)){this.guideTime=0;this.guideArea=s.area;this.hud.setGuidance(this.currentGuidance());}
  this.updateAimCancel(!!paused);
  if(paused)this.effects?.clear(true);
  else this.effects?.update(this.session,target&&info?{target,skillId:info.id,rank:info.rank.rank,angle:Math.atan2(target.x-this.session.state.player.x,target.z-this.session.state.player.z),geometry:info.rank.geometry,valid:distance(this.session.state.player,target)<=info.rank.castRangeMetres+.001&&this.world.visible(this.session.state.player,target)&&Math.abs(this.world.height(this.session.state.player)-this.world.height(target))<1.2}:undefined,range);
  const context=this.interaction().prompt??null;this.sceneInteraction?.update(context,!!paused||s.status==='dead'||!!this.automation.destination||this.heldAttack||!!this.aiming||!!s.action||s.enemies.some(e=>e.hp>0&&distance(e,p)<3&&this.world.visible(p,e)));
  const bossVisible=!paused&&!this.trainingRange&&!this.hud.automationExpanded&&!this.campaignView?.active&&s.status!=='dead';
  const bossNotice=this.trainingRange?null:this.bosses.update(this.session,Math.max(0,dt),!!bossVisible);
  this.hud.setBossAwareness(bossNotice,this.trainingRange?0:this.bosses.count);
  this.bossPanelClock+=dt;if(this.bossPanelClock>=.5){this.bossPanelClock=0;if(this.menu==='bosses'&&this.bossPanel?.valid)this.bossPanel.update();}
  this.encounterTime+=dt;this.compassTime+=dt;if(this.compassTime>=.5){this.compassTime=0;const st=this.session.state,home=st.equipment.necklace==='J08'&&!st.enemies.some(e=>e.hp>0&&distance(e,st.player)<7)?this.compass.find(st.area,st.player,st.flags,st.progression.level):null;if(home){const dx=home.target.x-st.player.x,dz=home.target.z-st.player.z,r=this.camera.node.right,u=this.camera.node.up,angle=Math.atan2(dx*r.x+dz*r.z,dx*u.x+dz*u.z),arrows=['↑','↗','→','↘','↓','↙','←','↖'];this.compassText='归乡信物 '+arrows[(Math.round(angle/(Math.PI/4))+8)%8]+' '+getArea(home.area).name;}else this.compassText='';}this.hud.trainingRange=this.trainingRange;this.hud.update(this.session,this.camera,this.loading?'正在准备场景与人物…':this.toast||this.encounterDirection(),this.saved,this.compassText,this.toast?this.toastRole:'text.normal');this.taskPresence?.update(this.session,this.hud.activeGuidance,!!paused||this.hud.automationExpanded,this.sceneInteraction?.visibleTargetId);this.portalHud?.update(this.session,!!this.menu||this.loading||!!this.failure||!!this.session.state.dialogue||!!this.session.state.dice.active||this.hud.portrait,this.sceneInteraction?.visibleTargetId??this.taskPresence?.captionTargetId);this.renderModal();if(this.menu.startsWith('journey'))updateJourneyCooldowns(this.hud,this.session);this.dicePanel?.update(Math.min(dt,.1));
 }
 onDestroy(){this.viewportCleanup?.();if(this.previousPhysicsAutoSimulation!==undefined){PhysicsSystem.instance.autoSimulation=this.previousPhysicsAutoSimulation;this.previousPhysicsAutoSimulation=undefined;}this.memoryCleanup();for(const type of [Input.EventType.TOUCH_START,Input.EventType.TOUCH_MOVE,Input.EventType.TOUCH_END,Input.EventType.TOUCH_CANCEL] as const)input.off(type,this.movementTouch,this);this.destroyed=true;this.music?.dispose();this.platform?.auth.dispose();this.platform?.updates.dispose();input.off(Input.EventType.KEY_DOWN,this.keyDown,this);input.off(Input.EventType.KEY_UP,this.keyUp,this);input.off(Input.EventType.MOUSE_MOVE,this.mouseMove,this);input.off(Input.EventType.MOUSE_DOWN,this.mouseDown,this);input.off(Input.EventType.MOUSE_UP,this.mouseUp,this);input.off(Input.EventType.MOUSE_WHEEL,this.mouseWheel,this);if(this.camera)Tween.stopAllByTarget(this.camera);this.cleanup?.();this.save();this.dicePanel?.clear();this.loadingScreen?.destroy();this.impact?.destroy();this.sceneInteraction?.destroy();this.groundLootView?.destroy();this.taskPresence?.destroy();this.portalHud?.destroy();this.enemyFeedback?.destroy();this.campaignView?.destroy();this.hud?.destroy();this.actors?.destroy();this.effects?.destroy();this.flatWorld?.destroy();this.nativePortals?.destroy();this.flatPortrait?.destroy();this.flatHead?.destroy();this.world?.destroy();this.mapResources.destroy();this.preparationResources?.destroy();UiSkin.dispose();EquipmentArt.dispose();SceneBuilder.releaseAssets();Effects.dispose();if(DEV)delete(globalThis as any).__chapter;}
}

