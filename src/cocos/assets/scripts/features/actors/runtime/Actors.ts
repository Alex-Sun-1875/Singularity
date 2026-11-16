import {HeroBodyBatches} from './HeroBodyBatches';
import {fieldNpcVisible} from '../../campaign/data/FieldQuests';
import {gameResources as resources} from '../../../shared/assets/GameResources';
import {Node,Prefab,JsonAsset,assetManager,instantiate,SkeletalAnimation,Animation,AnimationClip,SkinnedMeshRenderer,MeshRenderer,Vec3,Vec4,Material,Color,Quat,Mat4,Mesh,primitives,utils} from 'cc';
import type {GameSession,EnemyState,ActionState} from '../../../core/GameSession';
import {meleeCombo} from '../../combat/common/MeleeCombo';
import {combatSegmentInterval} from '../../combat/common/CombatActionTiming';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import type {GameEvent} from '../../../core/Contracts';
import {impactStyle,impactKey,type ImpactStyle} from '../../combat/data/CombatImpact';
import {enemyProfile} from '../../combat/common/EnemyCombat';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {COMBAT_SKILLS} from '../../combat/data/PureSkills';
import {SceneBuilder} from '../../world/runtime/SceneBuilder';
import {loadBundleWithDependencies} from '../../../shared/assets/AssetBundles';
import {SurfaceMaterials} from '../../world/runtime/SurfaceMaterials';
import {NativeActorMaterials,type NativeActorMaterialManifest} from './NativeActorMaterials';
import {WeaponMaterials,EQUIPMENT_WEAPON_RESOURCES,WEAPON_VARIANT_PREFIX,selectEquipmentWeaponVariants,playerWeaponVariants,weaponAttachmentKind} from './WeaponMaterials';
import {EnvironmentAssets} from '../../world/runtime/EnvironmentAssets';
import {readHairstyle,rememberHairstyle,type HairstyleDefinition,type HairstyleOption} from './Hairstyles';
import {HairstyleGeometry} from './HairstyleGeometry';
import {actionReleaseAt,samplePlayerAction,playerHurtProgress,updateWeaponReadiness,type PlayerActionSample,type PlayerPresentation,type WeaponReadiness} from './PlayerActionPresentation';
import {PlayerCombatLocomotion} from './PlayerCombatLocomotion';
import {useBakedAnimation} from '../common/AnimationMode';
import {chapterTwoEnemyRetired} from '../../campaign/common/ChapterTwoEncounters';
import {peacefulBossRetired} from '../../campaign/common/PeacefulBosses';
import {chapterTwoSideQuestNpcVisible} from '../../campaign/data/ChapterTwoSideQuests';
type Motion={nominalSpeedMetresPerSecond?:number;holdFraction?:number;relaxFraction?:number;drawWeights?:number[];phaseSampling?:{gameplayFractions:number[];sourceFractions:number[]}};
type SwordBackPlacement={position:number[];blade:number[];normal:number[];sheathLength?:number};
type SwordBackTransform={position:Vec3;rotation:Quat;length:number};
type SwordCarryGrip={node:Node;handParent:Node;handPosition:Vec3;handRotation:Quat;backParent:Node;backPosition:Vec3;backRotation:Quat;items:Record<string,SwordBackTransform>;heldModels:Node;backModels:Node;sheath?:Node;bands:Node[];stowed:boolean;item?:string};
type ActorMetadata=NativeActorMaterialManifest&{appearanceRevision?:string;hairstyles?:HairstyleDefinition[];cocosBinding?:{bowEuler:number[];arrowEuler:number[];arrowPosition:number[];bowAimYawCorrectionDegrees?:number;bowDrawWeightByItem?:Record<string,{scale:number;offset:number}>;swordBackCarry?:{bone:string;bowBone?:string;placements:Record<string,SwordBackPlacement>;items?:Record<string,SwordBackPlacement>;hiltScale?:number;embeddedCases?:boolean;quiver?:{resource:string;placements:Record<string,SwordBackPlacement>}}};skinJointCount?:number;skeletonJointCount?:number;modelYaw?:number;libraryMotion?:{clips?:Record<string,Motion>};parts?:Record<string,{nodes:string[];defaultVisible:boolean}>;profile?:{weapon?:string}};
const MELEE_TRANSITION_SECONDS=.06;
type Actor={meleeBeat?:number;paused?:boolean;weaponStowed?:boolean;bowPose?:string;bowRenderers?:MeshRenderer[];root:Node;model:Node;animation:SkeletalAnimation|null;clips:Record<string,AnimationClip>;state:string;clock:number;id:string;actionId?:string;renderedWeaponId?:string;phase?:string;phaseDuration?:number;enemyPose?:string;weapons:Record<string,Node>;metadata:ActorMetadata;yaw?:number;speed?:number;hood?:boolean;bowHeldDraw?:number;stride:{walk:number;run:number};motion?:PlayerActionSample;swordCarry?:{socket:Node;grips:Record<string,SwordCarryGrip>;quiver?:{node:Node;items:Record<string,SwordBackTransform>}}};
type NativeContact={start:number;style:ImpactStyle;angle:number};
type NativeTint={material:Material;base:Color;flash:Color;emission?:Color|Vec4;emissionFlash:Color;flashing:boolean};
const weaponFamily=(id:string):'bow'|'staff'|'sword'=>EQUIPMENT[id]?.kind==='bow'?'bow':EQUIPMENT[id]?.kind==='staff'?'staff':'sword';
function pureActionPose(action:ActionState):string|undefined {
 const id=action.skillId??(action.kind.startsWith('pure:')?action.kind.slice(5):''),skill=COMBAT_SKILLS[id];if(!skill)return;
 if(id==='COM_01')return 'dodge';if(id==='BOW_06')return 'interact';if(!skill.offensive)return 'spell';
 return skill.style==='BOW'?'attack_bow':skill.style==='WAR'?'attack_sword':'spell';
}
export class Actors {
 reducedMotion=false;
 private enemyImpacts=new Map<string,NativeContact>();
 private enemyTints=new Map<string,NativeTint[]>();
 private enemyBaseScale=new Map<string,Vec3>();
 private contactHoldUntil=0;private nextContactHold=0;private heldClip='';private heldPose:number|undefined;
 onCombatEvents(events:readonly GameEvent[],time:number){
  if(events.some(e=>['area','travel','retry'].includes(e.type))){this.contactHoldUntil=0;this.heldPose=undefined;this.resetEnemyContacts();return;}
  const blocked=new Set(events.filter(e=>e.type==='block').map(impactKey));
  for(const e of events){if(!e.id||e.id==='player'||!this.active.has(e.id))continue;const style=impactStyle(e,blocked.has(impactKey(e)));if(!style||style.kind==='burn')continue;const previous=this.enemyImpacts.get(e.id);if(!previous||time-previous.start>.07||style.priority>previous.style.priority)this.enemyImpacts.set(e.id,{start:time,style,angle:Number(e.angle??0)});}
  if(this.reducedMotion||time<this.nextContactHold)return;
  const holds=events.map(e=>{const style=impactStyle(e,blocked.has(impactKey(e)));if(!style)return 0;const melee=typeof e.comboStage==='number'||String(e.skillId??'').startsWith('WAR_'),heavy=e.comboStage===3||['heavy','critical','kill'].includes(style.kind);return melee?Math.min(style.hold,heavy?.04:.018):style.hold;});
  const hold=Math.max(0,...holds);if(hold>0){this.contactHoldUntil=time+hold;this.nextContactHold=time+.1;this.heldPose=undefined;}
 }
 private enemyContact(actor:Actor,e:EnemyState,game:GameSession){
  const impact=this.enemyImpacts.get(e.id),age=impact?game.state.time-impact.start:Infinity;
  if(!impact&&!(this.enemyTints.get(e.id)?.some(t=>t.flashing)))return;
  if(impact&&!this.enemyTints.has(e.id)){
   // Cocos owns renderer material instances; never tint shared prefab assets.
   const tints:NativeTint[]=[];
   for(const renderer of actor.model.getComponentsInChildren(MeshRenderer))for(let i=0;i<renderer.sharedMaterials.length;i++){
    const material=renderer.getMaterialInstance(i),base=material?.getProperty('mainColor');
    if(material&&base instanceof Color){const emission=material.getProperty('emissive');tints.push({material,base:base.clone(),flash:base.clone(),emission:emission instanceof Color||emission instanceof Vec4?emission.clone():undefined,emissionFlash:new Color(),flashing:false});}
   }
   this.enemyTints.set(e.id,tints);this.enemyBaseScale.set(e.id,actor.model.scale.clone());
  }
  const heavy=impact&&['heavy','critical','kill'].includes(impact.style.kind),flash=!this.reducedMotion&&e.hp>0&&age<(heavy?.08:.06);
  for(const tint of this.enemyTints.get(e.id)??[]){
   if(flash){const color=F.color(impact!.style.role);tint.flash.set(Math.min(255,tint.base.r*.6+color.r*.6),Math.min(255,tint.base.g*.6+color.g*.6),Math.min(255,tint.base.b*.6+color.b*.6),tint.base.a);tint.emissionFlash.set(color.r*(heavy?.62:.48),color.g*(heavy?.62:.48),color.b*(heavy?.62:.48),255);}
   if(flash||tint.flashing){tint.material.setProperty('mainColor',flash?tint.flash:tint.base);if(tint.emission)tint.material.setProperty('emissive',flash?tint.emissionFlash:tint.emission);}tint.flashing=flash;
  }
  const base=this.enemyBaseScale.get(e.id),pulse=!this.reducedMotion&&e.hp>0&&age<.18?Math.sin(age/.18*Math.PI):0;
  if(base){const strength=(impact?.style.recoil??0)/.2*(game.enemyHitReaction(e.id)?.resisted?.65:1);actor.model.setScale(base.x*(1+pulse*.035*strength),base.y*(1-pulse*.04*strength),base.z);}
  if(e.hp>0)actor.model.setRotationFromEuler(0,actor.metadata.modelYaw??0,pulse*(impact?.style.kind==='armor'?1:3));
  if(age>.25)this.enemyImpacts.delete(e.id);
 }
 private resetEnemyContacts(){
  for(const [id,tints]of this.enemyTints){
   for(const t of tints){if(t.flashing&&t.material.isValid){t.material.setProperty('mainColor',t.base);if(t.emission)t.material.setProperty('emissive',t.emission);}t.flashing=false;}
   const actor=this.active.get(id),base=this.enemyBaseScale.get(id);
   if(actor?.model.isValid){if(base)actor.model.setScale(base);if(actor.state!=='death')actor.model.setRotationFromEuler(0,actor.metadata.modelYaw??0,0);}
  }
  this.enemyImpacts.clear();
 }
 private contactPose(actor:Actor,time:number){
  const clip=actor.clips[actor.state],anim=clip&&actor.animation?.getState(clip.name);
  if(this.reducedMotion||time>=this.contactHoldUntil||!anim||!(actor.state.startsWith('attack_sword')||['attack_bow','attack_staff','spell'].includes(actor.state))){this.heldPose=undefined;return;}
  if(this.heldPose===undefined||this.heldClip!==clip.name){this.heldPose=anim.time;this.heldClip=clip.name;}
  anim.speed=0;anim.time=this.heldPose;if(actor.animation?.useBakedAnimation)anim.sample();
 }

 private pbrMaterials=new Map<Material,Material>();
 private nativeMaterials=new NativeActorMaterials();
 private hairMaterials:NativeActorMaterials|undefined;
 private hairLoads=new Set<NativeActorMaterials>();private hairRevision=0;private loadedHair='';
 private hairGeometry=new Map<NativeActorMaterials,HairstyleGeometry>();
 private hairSources=new Map<MeshRenderer,(Material|null)[]>();
 private weaponMaterials=new WeaponMaterials();
 private strideSpeeds=new Map<string,{walk:number;run:number}>();
 private carryReadiness:WeaponReadiness={ready:false,until:-Infinity};
 private readonly animationMode={realtime:false};
 private carryMaterials:Material[]=[];
 private carryMeshes:Mesh[]=[];
 private metadata=new Map<string,ActorMetadata>();
 private hairstyleId=readHairstyle();
 private prefabs=new Map<string,Prefab>();private active=new Map<string,Actor>();private bodyBatches:HeroBodyBatches|undefined;private pending=new Map<string,Promise<Prefab>>();
 private arriving=new Set<string>();private arrivalFailure=new Set<string>();
 private initialWeapon='W01';private disposed=false;private loadedWeapons=new Set<string>();private weaponLoads=new Map<string,Promise<void>>();
 private combatLocomotion:PlayerCombatLocomotion|undefined;
 setStartingWeapon(id:string){this.initialWeapon=id;}
 constructor(readonly scene:Node,public world:SceneBuilder,private readonly silverPlayer=false){}
 /** Transfer the one native hero before disposing the old area's root. */
 detachPlayer(){const actor=this.active.get('player');if(!actor?.root.isValid)return;this.combatLocomotion?.reset();actor.root.active=false;actor.root.setParent(this.scene);}
 adoptWorld(world:SceneBuilder){
  this.world=world;this.contactHoldUntil=0;this.nextContactHold=0;this.heldClip='';this.heldPose=undefined;this.carryReadiness={ready:false,until:-Infinity};this.animationMode.realtime=false;
  const actor=this.active.get('player');if(!actor?.root.isValid)throw new Error('Cannot transfer an unavailable player');
  actor.root.setParent(world.root);actor.state='';actor.actionId=undefined;actor.motion=undefined;actor.yaw=undefined;actor.speed=0;actor.bowHeldDraw=0;actor.renderedWeaponId=undefined;actor.weaponStowed=undefined;
 }
 async preparePlayer(game:GameSession){
  const actor=this.active.get('player');if(!actor?.root.isValid)throw new Error('Cannot prepare an unavailable player');
  const p=game.state.player;actor.root.setPosition(p.x,this.world.height(p),p.z);
  await this.preparePlayerWeapon(game.state.equipment.weapon);this.update(game,0,false);actor.root.active=true;
 }
 private static async definition(id:string,prepare?:(metadata:ActorMetadata)=>Promise<unknown>){
  const bundle=await loadBundleWithDependencies(`actor-${id}`),cachedMetadata=bundle.get('manifest',JsonAsset),metadata=cachedMetadata?.isValid?cachedMetadata:await new Promise<JsonAsset>((resolve,reject)=>bundle.load('manifest',JsonAsset,(err,json)=>err?reject(err):resolve(json)));
  const root=metadata?.json?.prefabRoot as string|undefined,path=root?bundle.getDirWithPath(root,Prefab)[0]?.path:`${id}/${id}`;if(!path)throw new Error('No actor prefab under '+root);
  const cached=bundle.get(path,Prefab),[asset]=await Promise.all([cached?.isValid?Promise.resolve(cached):new Promise<Prefab>((resolve,reject)=>bundle.load(path,Prefab,(err,prefab)=>err?reject(err):resolve(prefab))),prepare?.(metadata.json as ActorMetadata)]);return {asset,metadata:metadata.json as ActorMetadata};
 }
 /** Warm the same Cocos-managed prefab while initial world/VFX resources load. */
 static async preload(id:string,weapon='W01'){await this.definition(id,metadata=>id==='raphael'&&metadata.runtimeProfile==='native-kit-v1'?Promise.all([this.meleeClips(),metadata.appearanceRevision?NativeActorMaterials.preload(metadata):Promise.resolve(),WeaponMaterials.preloadPlayer(weapon,metadata.cocosBinding?.swordBackCarry?.quiver?.resource)]):Promise.resolve());}
 async load(id:string){if(this.prefabs.has(id))return this.prefabs.get(id)!;if(this.pending.has(id))return this.pending.get(id)!;const promise=Actors.definition(id).then(({asset,metadata})=>{this.metadata.set(id,metadata??{});const clips=metadata?.libraryMotion?.clips;this.strideSpeeds.set(id,{walk:clips?.walk?.nominalSpeedMetresPerSecond??1.05,run:clips?.run?.nominalSpeedMetresPerSecond??5.75});this.prefabs.set(id,asset);return asset;}).catch(error=>{this.pending.delete(id);throw error;});this.pending.set(id,promise);return promise;}
 async create(id:string,modelId:string,x:number,z:number){const prefab=await this.load(modelId);if(!this.world.root.isValid)return;const holder=new Node(id);this.world.root.addChild(holder);holder.setPosition(x,this.world.height({x,z}),z);const model=instantiate(prefab);holder.addChild(model);const animations=model.getComponentsInChildren(SkeletalAnimation);const animation=animations[0]??null;const clips:Record<string,AnimationClip>={};if(animation){for(const clip of animation.clips)if(clip)clips[clip.name.split('|').pop()!.replace(/\.\d+$/,'')]=clip;animation.useBakedAnimation=true;}
  // Current FBX exports already bake the Y-up axis conversion. Their visible
  // front is +Z, matching the holder's rule angle zero without another flip.
  const metadata=this.metadata.get(modelId)??{};model.setRotationFromEuler(0,metadata.modelYaw??0,0);
  const actor:Actor={root:holder,model,animation,clips,state:'',clock:0,id,weapons:{},metadata,stride:this.strideSpeeds.get(modelId)??{walk:1.05,run:5.75}};this.active.set(id,actor);this.setAnimationMode(actor,id!=='player'||weaponFamily(this.initialWeapon)!=='sword');this.play(actor,'idle');
  this.applyParts(actor);
  // These independent resource branches share the existing Cocos loader/cache.
  // Material traversal captures the imported renderers before weapons arrive.
  await Promise.all([
   metadata.runtimeProfile==='native-kit-v1'?this.nativeMaterials.apply(model,metadata,id==='player'&&this.silverPlayer&&!metadata.appearanceRevision?{hair:'../player-aim-v1/hair-silver.png',body:'../player-aim-v1/cloth-burgundy.png',arms:'../player-aim-v1/cloth-charcoal.png',legs:'../player-aim-v1/cloth-charcoal.png',hood:'../player-aim-v1/cloth-charcoal.png'}:undefined,{excludeHair:id==='player'&&!!metadata.hairstyles?.length}):Promise.resolve(),
   id==='player'&&metadata.hairstyles?.length?this.loadPlayerHairstyle(this.hairstyleId,false):Promise.resolve(),
   animation&&(id==='player'||metadata.runtimeProfile==='native-kit-v1')?this.attachWeapons(actor):Promise.resolve(),
   id==='player'&&animation?this.attachMeleeClips(actor):Promise.resolve(),
  ]);
  for(const renderer of model.getComponentsInChildren(MeshRenderer)){renderer.shadowCastingMode=1;renderer.receiveShadow=1;if(metadata.runtimeProfile==='native-kit-v1')continue;renderer.sharedMaterials.forEach((source,index)=>{if(!source)return;let material=this.pbrMaterials.get(source);if(!material){material=SurfaceMaterials.actor(source);this.pbrMaterials.set(source,material);}renderer.setSharedMaterial(material,index);});}
  const layer=(node:Node)=>{node.layer=1<<18;for(const child of node.children)layer(child);};layer(model);
  if(id==='player'&&animation&&metadata.runtimeProfile==='native-kit-v1'){this.bodyBatches=new HeroBodyBatches();this.bodyBatches.prepare(model);}
  if(id==='player'&&animation&&metadata.runtimeProfile==='native-kit-v1')this.combatLocomotion=PlayerCombatLocomotion.create(animation,clips,actor.stride);
  return actor;
 }
 async build(game:GameSession,onProgress?:(completed:number,total:number)=>void){this.setStartingWeapon(game.state.equipment.weapon);const s=game.state,requests=[this.create('player','raphael',s.player.x,s.player.z)];for(const object of this.world.area.objects){if(!object.actor)continue;const id=object.actor.toLowerCase();if((['mira','lorn','nightqi','kael','evelyn'].includes(id)||id.startsWith('field-npc-'))&&!this.active.has(id))requests.push(this.create(id,object.actorModel?(object.actorModel==='raider-shield'?'raider-shield':'raider'):id,object.x+(object.action==='meeting'?2.3:0),object.z));}
  if(this.world.area.id==='U1-04')for(const [id,x,z] of [['mira',-3,3],['kael',3,3]] as const)if(!this.world.area.objects.some(o=>o.actor===id))requests.push(this.create(id,id,x,z));
  for(const e of s.enemies)requests.push(this.create(e.id,e.kind==='captain'?'captain':e.kind==='archer'?'raider-archer':e.kind==='shield'?'raider-shield':'raider',e.x,e.z));
  let completed=0;await Promise.all(requests.map(request=>request.then(result=>{onProgress?.(++completed,requests.length);return result;})));
 }
 private static comboAsset:Promise<Prefab>|undefined;
 private static meleeClips(){return this.comboAsset??=new Promise<Prefab>((resolve,reject)=>resources.load('actors/player-melee-combo/combos-native/combos-native',Prefab,(error,prefab)=>error?reject(error):resolve(prefab))).catch(error=>{this.comboAsset=undefined;throw error;});}
 private async attachMeleeClips(actor:Actor){
  const prefab=await Actors.meleeClips(),carrier=instantiate(prefab);
  try{const clips=carrier.getComponentsInChildren(Animation).flatMap(animation=>animation.clips).filter(Boolean);
   for(const clip of clips){const key=clip!.name.split('|').pop()!.replace(/\.\d+$/,'');if(!['attack_sword_2','attack_sword_3'].includes(key))continue;actor.clips[key]=clip!;actor.animation!.createState(clip!,clip!.name);}
   for(const key of ['attack_sword_2','attack_sword_3'])if(!actor.clips[key])throw new Error('Missing melee combo motion '+key);
  }finally{carrier.destroy();}
 }
 private bonePath(root:Node,name:string):string|null{for(const child of root.children){if(child.name===name)return child.name;const path=this.bonePath(child,name);if(path)return child.name+'/'+path;}return null;}
 private applyParts(actor:Actor,hood?:boolean,force=false){
  if(!force&&hood!==undefined&&actor.hood===hood)return;if(hood!==undefined)actor.hood=hood;
  const styles=actor.id==='player'?actor.metadata.hairstyles:undefined,style=styles?.find(s=>s.id===this.hairstyleId)??styles?.[0];
  if(style)this.hairstyleId=style.id;
  for(const [part,definition]of Object.entries(actor.metadata.parts??{}))for(const name of definition.nodes){const path=this.bonePath(actor.model,name),node=path&&actor.model.getChildByPath(path);if(node)node.active=part==='hood'&&hood!==undefined?hood:part==='hair'?definition.defaultVisible&&!actor.hood&&(!style||style.nodes.includes(name)):definition.defaultVisible;}
 }
 playerHairstyles():HairstyleOption[]{return (this.active.get('player')?.metadata.hairstyles??[]).map(s=>({id:s.id,label:s.label,description:s.description,selected:s.id===this.hairstyleId}));}
 setPlayerHairstyle(id:string):Promise<boolean>{return this.loadPlayerHairstyle(id,true);}
 private releaseHair(owner:NativeActorMaterials|undefined){if(!owner)return;this.hairGeometry.get(owner)?.destroy();this.hairGeometry.delete(owner);owner.destroy();}
 private async loadPlayerHairstyle(id:string,persist:boolean):Promise<boolean>{
  const actor=this.active.get('player'),style=actor?.metadata.hairstyles?.find(s=>s.id===id)??(!persist?actor?.metadata.hairstyles?.[0]:undefined);
  if(this.disposed||!actor||!style)return false;
  if(this.loadedHair===style.id&&this.hairMaterials){this.hairRevision++;return true;}
  const revision=++this.hairRevision,owner=new NativeActorMaterials();this.hairLoads.add(owner);
  const current=()=>!this.disposed&&revision===this.hairRevision&&this.active.get('player')===actor&&actor.model.isValid;
  const roots=style.nodes.map(name=>this.bonePath(actor.model,name)).filter(Boolean).map(path=>actor.model.getChildByPath(path!)!);
  try{
   if(!roots.length)throw new Error('Missing hairstyle nodes: '+style.id);
   let geometry:HairstyleGeometry|undefined;
   if(style.geometryRoot){
    if(roots.length!==1||!actor.animation)throw new Error('Invalid hairstyle geometry binding: '+style.id);
    geometry=new HairstyleGeometry();this.hairGeometry.set(owner,geometry);await geometry.mount(style.geometryRoot,roots[0],actor.animation,current);
   }else for(const root of roots)for(const renderer of root.getComponentsInChildren(MeshRenderer)){
    if(!this.hairSources.has(renderer))this.hairSources.set(renderer,renderer.sharedMaterials.slice());
    renderer.sharedMaterials=this.hairSources.get(renderer)!;
   }
   await Promise.all(roots.map(root=>owner.apply(root,actor.metadata,undefined,{current})));
   if(!current()){this.releaseHair(owner);return false;}
   const previous=this.hairMaterials;this.hairMaterials=owner;this.loadedHair=style.id;this.hairstyleId=style.id;this.applyParts(actor,actor.hood,true);
   geometry?.show();
   for(const [renderer,sources]of this.hairSources)if(renderer.isValid&&!style.nodes.includes(renderer.node.name))renderer.sharedMaterials=sources;
   this.releaseHair(previous);if(persist)rememberHairstyle(style.id);return true;
  }catch(error){this.releaseHair(owner);if(current())throw error;return false;}
  finally{this.hairLoads.delete(owner);}
 }
 private async attachWeapons(actor:Actor){
  const animation=actor.animation!,native=actor.metadata.runtimeProfile==='native-kit-v1';
  if(native&&actor.clips.attack_bow&&(!this.bonePath(animation.node,'attach_bow_l')||!this.bonePath(animation.node,'attach_arrow_r')))throw new Error('Native bow clip is missing its authored animated attachment helpers: '+actor.id);
  const hide=(n:Node)=>{if(n.name.toLowerCase().startsWith('equipped'))n.active=false;else for(const child of n.children)hide(child);};hide(actor.model);
  const profile=actor.metadata.profile?.weapon;const kinds=actor.id==='player'?(native?['sword','greatsword','bow','staff']:['sword','bow','staff']):native?profile==='bow'?['bow']:profile==='shield'?['sword','shield']:profile==='daggers'?['dagger','dagger_off']:profile==='hammer'?['hammer','shield']:profile==='staff'?['staff']:profile==='sword'?['sword']:profile==='lantern'?['lantern']:profile==='maps'?['map-kit']:[]:[];
  await Promise.all(kinds.map(async kind=>{
   const left=['bow','shield','dagger_off','lantern','map-kit'].includes(kind),meshKind=kind==='dagger_off'?'dagger':kind,helper=native&&kind==='bow'?this.bonePath(animation.node,'attach_bow_l'):null,path=helper??this.bonePath(animation.node,left?'hand_l':'hand_r');if(!path)throw new Error('Missing actual hand bone for '+kind);
   const socket=animation.createSocket(path);if(!socket)throw new Error('Cannot create animated hand socket');
   const grip=new Node('Held_'+kind);socket.addChild(grip);
   if(helper){const r=actor.metadata.cocosBinding?.bowEuler??[90,0,180];grip.setRotationFromEuler(r[0],r[1],r[2]);}else{
    const hand=animation.node.getChildByPath(path),side=left?'l':'r',index=hand?.getChildByName('index_01_'+side),pinky=hand?.getChildByName('pinky_01_'+side);
    if(!index||!pinky)throw new Error('Missing actual knuckle bones for '+kind);
    const axis=Vec3.subtract(new Vec3(),index.position,pinky.position).normalize(),center=Vec3.add(new Vec3(),index.position,pinky.position).multiplyScalar(.5);
    grip.setPosition(center);grip.setRotation(Quat.rotationTo(new Quat(),new Vec3(0,1,0),axis));
   }
   let propParent=grip;
   if(native&&(kind==='shield'||kind==='lantern'||kind==='map-kit')){
    // Measured native idle palm frame: Held +Z points up and +Y forward.
    // Broad shields, a hanging lamp and the map tube's measuring plumb use
    // that frame. This local adapter follows the animated hand unchanged.
    propParent=new Node('GripOrientation_'+kind);grip.addChild(propParent);
    propParent.setRotation(Quat.fromAxes(new Quat(),new Vec3(-1,0,0),new Vec3(0,0,1),new Vec3(0,1,0)));
   }
   if(native&&kind==='lantern'){
    await EnvironmentAssets.load();
    // The library origin is at the sole. Move its actual top carrying handle
    // into the palm; reuse shared environment meshes/materials and no lights.
    EnvironmentAssets.place('lantern',propParent,new Vec3(0,-.445,0),{height:.48});
   }else{
    const variants=native?(actor.id==='player'?this.startingVariants(kind):kind==='shield'?[profile==='hammer'?'captain-shield':actor.id==='lorn'?'lorn-shield':'shield']:kind==='bow'&&actor.id==='nightqi'?['wind-bow']:[meshKind]):[meshKind];
    await Promise.all(variants.map(async variant=>{
     const resource=native?`actors/props-native/${variant}/${variant}/${variant}`:`actors/props/${variant}/${variant}`;
     const prefab=await new Promise<Prefab>((resolve,reject)=>resources.load(resource,Prefab,(err,p)=>err?reject(err):resolve(p))),model=instantiate(prefab);model.name=WEAPON_VARIANT_PREFIX+variant;propParent.addChild(model);
     if(native)await this.weaponMaterials.apply(model,variant);
     model.active=actor.id!=='player'||variant===meshKind;
    }));
   }
   grip.active=actor.id!=='player'||kind==='sword';actor.weapons[kind]=grip;
  }));
  const arrowPath=native&&this.bonePath(animation.node,'attach_arrow_r');if(arrowPath&&actor.weapons.bow){const socket=animation.createSocket(arrowPath);if(socket){const prefab=await new Promise<Prefab>((resolve,reject)=>resources.load('actors/props-native/arrow/arrow/arrow',Prefab,(err,p)=>err?reject(err):resolve(p)));const arrow=instantiate(prefab);socket.addChild(arrow);await this.weaponMaterials.apply(arrow,'arrow');const r=actor.metadata.cocosBinding?.arrowEuler??[0,0,0],p=actor.metadata.cocosBinding?.arrowPosition??[0,.35595446825027466,0];arrow.setRotationFromEuler(r[0],r[1],r[2]);arrow.setPosition(p[0],p[1],p[2]);arrow.active=false;actor.weapons.arrow=arrow;}}
  if(native&&actor.id==='player')await this.attachSwordCarry(actor);
 }
 private async attachSwordCarry(actor:Actor){
  const definition=actor.metadata.cocosBinding?.swordBackCarry;if(!definition)return;
  // Real-time sample() writes into Cocos' deferred blend buffer. Build the
  // shared back reference with baked sampling, which updates sockets now,
  // even when the starting sword selected the real-time animation path.
  const restoreRealtime=!actor.animation!.useBakedAnimation;
  if(restoreRealtime){this.setAnimationMode(actor,true);this.play(actor,'idle',true);}
  const animation=actor.animation!,path=this.bonePath(animation.node,definition.bone),bone=path&&animation.node.getChildByPath(path);
  if(!path||!bone)throw new Error('Missing native sword back bone: '+definition.bone);
  const socket=animation.createSocket(path);if(!socket)throw new Error('Cannot create native sword back socket');
  const bowPath=definition.bowBone?this.bonePath(animation.node,definition.bowBone):path;
  if(!bowPath)throw new Error('Missing native bow back bone: '+definition.bowBone);
  const bowSocket=bowPath===path?socket:animation.createSocket(bowPath);
  if(!bowSocket)throw new Error('Cannot create native bow back socket');
  // Design positions describe the resting back, not the FBX import pose.
  // Sample two distinct frames so a newly created baked socket is synchronized
  // even when the current idle animation is already on frame zero.
  const idleClip=actor.clips.idle,idle=idleClip&&animation.getState(idleClip.name);
  if(idle){idle.time=1/idleClip.sample;idle.sample();idle.time=0;idle.sample();}
  const references=new Map([socket,bowSocket].map(node=>[node,{inverse:Mat4.invert(new Mat4(),node.worldMatrix),inverseRotation:Quat.invert(new Quat(),node.worldRotation)}])),grips:Record<string,SwordCarryGrip>={};
  if(restoreRealtime){this.setAnimationMode(actor,false);this.play(actor,'idle',true);}
  let leather:Material|undefined,metal:Material|undefined,caseMesh:Mesh|undefined,bandMesh:Mesh|undefined;
  // The current hero's scabbards are already authored in the weapon prefabs.
  // Only older comparison models need the procedural leather/metal fallback.
  if(!definition.embeddedCases){
   await SurfaceMaterials.load();
   leather=SurfaceMaterials.create('SwordScabbardLeather','leather',new Color(122,78,47));metal=SurfaceMaterials.create('SwordScabbardBands','metal',new Color(126,102,64));
   this.carryMaterials.push(leather,metal);
   caseMesh=utils.createMesh(primitives.cylinder(.22,.5,1,{radialSegments:8,heightSegments:1}));bandMesh=utils.createMesh(primitives.cylinder(.5,.5,1,{radialSegments:8,heightSegments:1}));
   this.carryMeshes.push(caseMesh,bandMesh);
  }
  const piece=(parent:Node,name:string,mesh:Mesh,material:Material)=>{const n=new Node(name);parent.addChild(n);const r=n.addComponent(MeshRenderer);r.mesh=mesh;r.setSharedMaterial(material,0);return n;};
  const transform=(placement:SwordBackPlacement,parent=socket):SwordBackTransform=>{
   const {inverse,inverseRotation}=references.get(parent)!;
   const p=placement.position,d=placement.blade,n=placement.normal,y=new Vec3(d[0],d[1],d[2]).normalize(),z=new Vec3(n[0],n[1],n[2]).normalize(),x=Vec3.cross(new Vec3(),y,z).normalize();
   const q=Quat.fromAxes(new Quat(),x,y,z),world=Vec3.transformMat4(new Vec3(),new Vec3(p[0],p[1],p[2]),actor.model.worldMatrix);
   return {position:Vec3.transformMat4(new Vec3(),world,inverse),rotation:Quat.multiply(new Quat(),inverseRotation,Quat.multiply(new Quat(),actor.model.worldRotation,q)),length:placement.sheathLength??.8};
  };
  for(const[kind,placement]of Object.entries(definition.placements)){
   const node=actor.weapons[kind];if(!node?.parent)continue;
   const backParent=kind==='bow'?bowSocket:socket;
   const handParent=node.parent,handPosition=node.position.clone(),handRotation=node.rotation.clone(),heldModels=new Node('UnsheathedSwordModels'),backModels=new Node('SheathedSwordModels');
   for(const child of [...node.children])child.setParent(heldModels);
   node.addChild(heldModels);node.addChild(backModels);
   const variants=this.startingVariants(kind);
   await Promise.all(variants.map(async variant=>{
    const resource=await this.weaponMaterials.stowedResource(variant),prefab=await new Promise<Prefab>((resolve,reject)=>resources.load(`actors/props-native/${resource}/${resource}/${resource}`,Prefab,(error,p)=>error?reject(error):resolve(p))),hilt=instantiate(prefab);
    hilt.name=WEAPON_VARIANT_PREFIX+variant;backModels.addChild(hilt);hilt.setScale(definition.hiltScale??.55,definition.hiltScale??.55,definition.hiltScale??.55);await this.weaponMaterials.apply(hilt,resource);
   }));
   const sheath=definition.embeddedCases?undefined:piece(backModels,'LeatherScabbard',caseMesh!,leather!),bands=definition.embeddedCases?[]:[0,1,2].map(i=>piece(backModels,'ScabbardBand'+i,bandMesh!,metal!)),base=transform(placement,backParent),items:Record<string,SwordBackTransform>={};
   for(const[id,override]of Object.entries(definition.items??{}))items[id]=transform(override,backParent);
   grips[kind]={node,handParent,handPosition,handRotation,backParent,backPosition:base.position,backRotation:base.rotation,items,heldModels,backModels,sheath,bands,stowed:false};backModels.active=false;
  }
  actor.swordCarry={socket,grips};
  this.loadedWeapons.add(EQUIPMENT_WEAPON_RESOURCES[EQUIPMENT[this.initialWeapon]?.artSource??this.initialWeapon]??EQUIPMENT_WEAPON_RESOURCES.W01);
  if(definition.quiver){
   const resource=definition.quiver.resource,prefab=await new Promise<Prefab>((resolve,reject)=>resources.load(`actors/props-native/${resource}/${resource}/${resource}`,Prefab,(error,p)=>error?reject(error):resolve(p))),node=instantiate(prefab),items:Record<string,SwordBackTransform>={};
   node.name='CarriedQuiver';bowSocket.addChild(node);await this.weaponMaterials.apply(node,resource);
   for(const[id,placement]of Object.entries(definition.quiver.placements))items[id]=transform(placement,bowSocket);
   node.active=false;actor.swordCarry.quiver={node,items};
  }
 }
 private startingVariants(kind:string):string[]{
  const selected=EQUIPMENT_WEAPON_RESOURCES[EQUIPMENT[this.initialWeapon]?.artSource??this.initialWeapon]??EQUIPMENT_WEAPON_RESOURCES.W01;
  return playerWeaponVariants(kind).filter(variant=>variant===selected);
 }
 /** Await before committing equipment; unused weapon variants stay unloaded. */
 preparePlayerWeapon(id:string):Promise<void>{
  const actor=this.active.get('player');if(!actor||actor.metadata.runtimeProfile!=='native-kit-v1')return Promise.resolve();
  const variant=EQUIPMENT_WEAPON_RESOURCES[EQUIPMENT[id]?.artSource??id]??EQUIPMENT_WEAPON_RESOURCES.W01;
  if(this.loadedWeapons.has(variant))return Promise.resolve();
  const cached=this.weaponLoads.get(variant);if(cached)return cached;
  const task=(async()=>{
   const kind=weaponAttachmentKind(id),grip=actor.swordCarry?.grips[kind],parent=grip?.heldModels??actor.weapons[kind];
   if(!parent)throw new Error('Missing player weapon grip: '+kind);
   const stowed=await this.weaponMaterials.stowedResource(variant),load=(name:string)=>new Promise<Prefab>((resolve,reject)=>resources.load(`actors/props-native/${name}/${name}/${name}`,Prefab,(error,p)=>error?reject(error):resolve(p)));
   const [heldPrefab,backPrefab]=await Promise.all([load(variant),grip?load(stowed):Promise.resolve(undefined)]);
   if(this.disposed||!actor.model.isValid)throw new Error('Player left before equipment finished loading');
   const held=instantiate(heldPrefab),back=backPrefab?instantiate(backPrefab):undefined;
   try{
    const mount=(node:Node,host:Node)=>{node.name=WEAPON_VARIANT_PREFIX+variant;node.active=false;host.addChild(node);const layer=(n:Node)=>{n.layer=1<<18;for(const child of n.children)layer(child);};layer(node);};
    mount(held,parent);if(back){mount(back,grip!.backModels);const scale=actor.metadata.cocosBinding?.swordBackCarry?.hiltScale??.55;back.setScale(scale,scale,scale);}
    await Promise.all([this.weaponMaterials.apply(held,variant),back?this.weaponMaterials.apply(back,stowed):Promise.resolve()]);
    if(this.disposed)throw new Error('Player left during equipment preparation');
    this.loadedWeapons.add(variant);actor.bowRenderers=undefined;actor.bowPose=undefined;
   }catch(error){held.destroy();back?.destroy();throw error;}
  })();this.weaponLoads.set(variant,task);void task.finally(()=>this.weaponLoads.delete(variant)).catch(()=>{});return task;
 }
 private setSwordCarry(actor:Actor,kind:string,stowed:boolean,id:string){
  const carry=actor.swordCarry,b=carry?.grips[kind];if(!carry||!b||b.stowed===stowed&&b.item===id)return;
  const back=b.items[EQUIPMENT[id]?.artSource??id]??{position:b.backPosition,rotation:b.backRotation,length:.8};
  b.node.setParent(stowed?b.backParent:b.handParent);b.node.setPosition(stowed?back.position:b.handPosition);b.node.setRotation(stowed?back.rotation:b.handRotation);
  b.heldModels.active=!stowed;b.backModels.active=stowed;
  if(b.sheath){b.sheath.setPosition(0,.04+back.length/2,0);b.sheath.setScale(.046,back.length,.023);}
  for(let i=0;i<b.bands.length;i++){const t=[0,.48,.96][i],width=1-.56*t;b.bands[i].setPosition(0,.04+back.length*t,0);b.bands[i].setScale(.050*width,.014,.027*width);}
  b.stowed=stowed;b.item=id;
 }
 private sampleFraction(actor:Actor,state:string,progress:number):number{
  const phase=actor.metadata.libraryMotion?.clips?.[state]?.phaseSampling;if(!phase)return progress;
  const t=phase.gameplayFractions,v=phase.sourceFractions;for(let i=1;i<t.length;i++)if(progress<=t[i])return v[i-1]+(v[i]-v[i-1])*(progress-t[i-1])/Math.max(.0001,t[i]-t[i-1]);return v[v.length-1]??progress;
 }
 private samplePlayerFraction(actor:Actor,state:string,action:ActionState):number{
  const progress=Math.min(1,action.elapsed/action.duration);
  if(state.startsWith('attack_sword')){
   if(action.kind==='sword'){
    const stage=action.comboStage??1,profile=meleeCombo(stage),contact=stage===1?.12/.44:profile.release/profile.duration;
    // Keep the follow-through between cuts and skip the repeated entry hold in
    // the assembled return/finisher clips. The original contact time is fixed.
    const mid=stage===3?.36:stage===2?.26:.24;
    const times=[0,action.releaseAt??profile.release,mid,action.duration],poses=[stage===1?0:.035/profile.duration,contact,stage===1?.72:mid/profile.duration,stage===3?1:.93];
    for(let i=1;i<times.length;i++)if(action.elapsed<=times[i])return poses[i-1]+(poses[i]-poses[i-1])*(action.elapsed-times[i-1])/Math.max(.001,times[i]-times[i-1]);return 1;
   }
   const motion=actor.motion;if(motion){const beat=actor.meleeBeat??motion.beat,release=motion.releaseAt,profile=meleeCombo(state.endsWith('_3')?3:state.endsWith('_2')?2:1),contact=state==='attack_sword'?.12/.44:profile.release/profile.duration;
    const interval=combatSegmentInterval(action.skillId??''),contactAt=release+beat*interval;
    if(action.elapsed<contactAt){const begin=beat?contactAt-MELEE_TRANSITION_SECONDS:0;return contact*Math.max(0,Math.min(1,(action.elapsed-begin)/Math.max(.001,contactAt-begin)));}
    const within=Math.max(0,action.elapsed-contactAt),continuing=beat<motion.beats-1,window=continuing?Math.max(.001,interval-MELEE_TRANSITION_SECONDS):Math.max(.001,action.duration-contactAt);
    return contact+((continuing?.78:1)-contact)*Math.min(1,within/window);
   }
  }
  if(state==='attack_staff'&&action.kind==='staff'){
   const release=actionReleaseAt(action);if(action.elapsed<=release)return this.sampleFraction(actor,state,progress);
   const cue=this.sampleFraction(actor,state,release/action.duration);
   return cue+(1-cue)*Math.min(1,(action.elapsed-release)/Math.min(.30,Math.max(.001,action.duration-release)));
  }
  return this.sampleFraction(actor,state,progress);
 }
 private bowWeight(actor:Actor):number{
  const clip=actor.clips.attack_bow,anim=clip&&actor.animation?.getState(clip.name);if(actor.state!=='attack_bow'||!clip||!anim)return 0;
  const motion=actor.metadata.libraryMotion?.clips?.attack_bow,hold=motion?.holdFraction??.65,relax=motion?.relaxFraction??(hold+(1-hold)/3),fraction=Math.max(0,Math.min(1,anim.time/clip.duration));
  if(motion?.drawWeights?.length){const samples=motion.drawWeights,index=fraction*(samples.length-1),lo=Math.floor(index),hi=Math.min(samples.length-1,lo+1);return samples[lo]+(samples[hi]-samples[lo])*(index-lo);}
  return fraction<=hold?fraction/hold:Math.max(0,1-(fraction-hold)/Math.max(.001,relax-hold));
 }
 private drawBow(actor:Actor,weight:number,arrowVisible:boolean){
  const pose=actor.renderedWeaponId+':'+weight.toFixed(5)+':'+arrowVisible;if(actor.bowPose===pose)return;actor.bowPose=pose;
  const calibration=actor.metadata.cocosBinding?.bowDrawWeightByItem?.[actor.renderedWeaponId??''],mapped=calibration&&actor.state==='attack_bow'?weight*calibration.scale+calibration.offset*(arrowVisible?1:Math.min(1,Math.max(0,weight))):weight,minWeight=calibration?Math.min(0,calibration.offset):0,bow=actor.weapons.bow,maxWeight=Math.max(1,...(actor.metadata.libraryMotion?.clips?.attack_bow?.drawWeights??[]).map(w=>calibration?w*calibration.scale+calibration.offset:w));if(bow)for(const renderer of actor.bowRenderers??=bow.getComponentsInChildren(MeshRenderer)){if(!renderer.node.activeInHierarchy)continue;const morph=renderer.mesh?.struct.morph,shape=morph?.targetNames?.indexOf('Draw')??-1;if(shape<0||!morph)continue;for(let sub=0;sub<morph.subMeshMorphs.length;sub++)if(morph.subMeshMorphs[sub])renderer.setWeight(Math.max(minWeight,Math.min(maxWeight,mapped)),sub,shape);}
  if(actor.weapons.arrow)actor.weapons.arrow.active=arrowVisible;
 }
 private setAnimationMode(actor:Actor,baked:boolean){
  const animation=actor.animation;if(!animation||animation.useBakedAnimation===baked)return;
  animation.stop();animation.useBakedAnimation=baked;
  // Imported states were initialized for baked sampling. Recreate them through
  // the public API so the new real-time states own proper curve evaluators.
  for(const clip of Object.values(actor.clips))animation.createState(clip,clip.name);
  actor.state='';actor.actionId=undefined;
 }
 private play(actor:Actor,state:string,restart=false){if(actor.state===state&&!restart)return;actor.model.setRotationFromEuler(0,(actor.metadata.modelYaw??0)+(state==='attack_bow'?actor.metadata.cocosBinding?.bowAimYawCorrectionDegrees??0:0),0);const clip=actor.clips[state];if(!clip||!actor.animation){console.error('[Actor] missing animated clip',actor.id,state,Object.keys(actor.clips));return;}const sword=state.startsWith('attack_sword'),fromSword=actor.state.startsWith('attack_sword');const fade=actor.id==='player'?(sword?(fromSword?MELEE_TRANSITION_SECONDS:.055):state.startsWith('idle')&&fromSword?.10:state.startsWith('attack')||state==='dodge'||state==='spell'||state==='hit'?.035:state.startsWith('run')||state.startsWith('walk')?.06:.08):.10;actor.animation.crossFade(clip.name,fade);const anim=actor.animation.getState(clip.name);if(anim){anim.wrapMode=state.startsWith('idle')||state.startsWith('run')||state.startsWith('walk')?AnimationClip.WrapMode.Loop:AnimationClip.WrapMode.Normal;if(restart)anim.time=0;}actor.state=state;actor.clock=0;actor.paused=false;}
 private syncPlayerWeapon(actor:Actor,id:string,stowed=false):string {
  const family=weaponFamily(id),kind=weaponAttachmentKind(id)==='greatsword'&&actor.weapons.greatsword?'greatsword':family;
  if(actor.renderedWeaponId===id&&actor.weaponStowed===stowed)return kind;
  for(const [name,node]of Object.entries(actor.weapons)){node.active=name===kind;if(name===kind)selectEquipmentWeaponVariants(node,id);}
  this.setSwordCarry(actor,kind,stowed,id);
  const quiver=actor.swordCarry?.quiver;if(quiver){const placement=quiver.items[EQUIPMENT[id]?.artSource??id];quiver.node.active=kind==='bow'&&!!placement;if(placement){quiver.node.setPosition(placement.position);quiver.node.setRotation(placement.rotation);}}
  actor.renderedWeaponId=id;actor.weaponStowed=stowed;return kind;
 }
 update(game:GameSession,dt:number,moving:boolean,paused=false,moveAmount=1){if(paused)this.resetEnemyContacts();for(const actor of this.active.values()){if(chapterTwoEnemyRetired(game.state,actor.id)||peacefulBossRetired(game.state,actor.id))actor.root.active=false;else if(actor.id.startsWith('field-npc-'))actor.root.active=fieldNpcVisible(actor.id,game.state.flags);else if(actor.id.startsWith('side-npc-'))actor.root.active=chapterTwoSideQuestNpcVisible(actor.id,game.state);}this.combatLocomotion?.setPaused(paused);if(!paused)updateWeaponReadiness(this.carryReadiness,game,this.world);if(paused){this.contactHoldUntil=0;this.heldPose=undefined;const player=this.active.get('player'),id=game.state.equipment.weapon;if(player&&player.renderedWeaponId!==id){this.syncPlayerWeapon(player,id,!this.carryReadiness.ready&&game.state.player.hp>0);this.applyParts(player,game.state.equipment.head==='A02');const idle=weaponFamily(id)==='staff'&&this.carryReadiness.ready&&player.clips.idle_staff?'idle_staff':'idle';this.play(player,idle,true);const clip=player.clips[idle],animation=clip&&player.animation?.getState(clip.name);if(animation){animation.time=0;animation.sample();}player.actionId=undefined;this.drawBow(player,0,false);}for(const actor of this.active.values())if(!actor.paused){actor.animation?.pause();actor.paused=true;}return;}const p=game.state.player,a=game.state.action;const player=this.active.get('player');if(player){const dx=p.x-player.root.position.x,dz=p.z-player.root.position.z,speed=Math.min(8,Math.hypot(dx,dz)/Math.max(.001,dt)),travelling=speed>.08,heading=a?a.angle:travelling?Math.atan2(dx,dz):p.angle;player.speed=speed;const y=this.world.height(p);if(player.root.position.x!==p.x||player.root.position.y!==y||player.root.position.z!==p.z)player.root.setPosition(p.x,y,p.z);const angleDelta=Math.atan2(Math.sin(heading-(player.yaw??heading)),Math.cos(heading-(player.yaw??heading)));player.yaw=travelling&&!a?(player.yaw??heading)+angleDelta*(1-Math.exp(-dt*16)):heading;if(player.root.eulerAngles.y!==player.yaw*180/Math.PI)player.root.setRotationFromEuler(0,player.yaw*180/Math.PI,0);const hurtProgress=playerHurtProgress(p.hurtTime);let state=p.hp<=0?'death':hurtProgress!==undefined?'hit':a?.kind==='dash'?'dodge':a?.kind==='bowAim'?'attack_bow':a?(pureActionPose(a)??(a.kind.includes('spell')?'spell':a.kind.includes('bow')?'attack_bow':a.kind.includes('staff')?'attack_staff':a.kind==='push'?'interact':a.kind==='skill'?'attack_'+weaponFamily(game.state.equipment.weapon):'attack_sword')):travelling?(speed>(player.state.startsWith('run')?2:2.3)?'run':'walk'):'idle';if(weaponFamily(game.state.equipment.weapon)==='staff'&&player.clips.idle_staff){if(['idle','walk','run'].includes(state)&&this.carryReadiness.ready)state+='_staff';else if(state==='spell')state='attack_staff';}// Reuse the authored stride while an action moves the hero. The layer
   // survives action/beat changes, so consecutive attacks never reset the feet.
   const locomotion=this.combatLocomotion,previousState=player.state,previousClip=player.clips[previousState],previousAnim=previousClip&&player.animation?.getState(previousClip.name);
   const basePhase=(previousState.startsWith('walk')||previousState.startsWith('run'))&&previousAnim?previousAnim.time/previousClip.duration:undefined;
   const gait=moving?(moveAmount>.7?'run':'walk'):(speed>2.3?'run':'walk');
   // Melee clips already author the hips, torso and planted feet together.
   // Keep that full-body motion instead of replacing its legs with a stride/IK.
   const authoredMelee=weaponFamily(game.state.equipment.weapon)==='sword'||!!a?.skillId&&COMBAT_SKILLS[a.skillId]?.style==='WAR';
   const actionStride=!authoredMelee&&!!a&&(state.startsWith('attack')||state==='spell'||state==='interact');
   locomotion?.update(dt,speed,Math.atan2(dx,dz)-player.yaw-((player.metadata.modelYaw??0)+(state==='attack_bow'?player.metadata.cocosBinding?.bowAimYawCorrectionDegrees??0:0))*Math.PI/180,gait,actionStride,authoredMelee||['death','hit','dodge'].includes(state),basePhase,a??undefined);
   locomotion?.setStaffHit(state==='hit'&&weaponFamily(game.state.equipment.weapon)==='staff',dt);
   // Action footwork and its short exit blend use real-time joints; ranged
   // exploration retains baked skinning. Other actors keep their old path.
   // Recreating every clip evaluator during each small gap between moving
   // ranged attacks allocated repeatedly and caused avoidable long frames.
   const baked=useBakedAnimation(this.animationMode,weaponFamily(game.state.equipment.weapon)==='sword'||!!locomotion?.active,this.carryReadiness.ready);
   // Restore registered sockets before baking so Cocos keeps their target
   // transforms enabled while it suspends the skeleton's node transforms.
   if(baked)locomotion?.setManualSockets(false);this.setAnimationMode(player,baked);
   locomotion?.setManualSockets(!baked&&!!locomotion.active);
   player.meleeBeat=undefined;if(a&&state==='attack_sword'){const motion=samplePlayerAction(a,state,{frames:4},game.state.combat.casts.find(c=>c.id===a.id));let beat=a.kind==='sword'?(a.comboStage??1)-1:motion.beat;
    // Anticipate the next performed cut during the preceding follow-through;
    // native crossFade reaches its contact pose on the authoritative beat.
    if(a.kind!=='sword'&&beat<motion.beats-1&&a.elapsed>=motion.releaseAt+(beat+1)*combatSegmentInterval(a.skillId??'')-MELEE_TRANSITION_SECONDS)beat++;
    player.meleeBeat=beat;state=meleeCombo(a.skillId==='WAR_04'?3:beat%3+1).clip;}this.play(player,state,!!a&&player.actionId!==a.id);player.actionId=a?.id;player.motion=a?samplePlayerAction(a,state,{frames:4},game.state.combat.casts.find(c=>c.id===a.id),game.state.equipment.hands==='A10'?.72:.8):undefined;
   const chargeTime=game.state.equipment.hands==='A10'?.72:.8,drawTime=chargeTime*.525;
   // The pose reaches aim promptly; the rules still determine full-charge damage.
   if(a?.kind==='bowAim')player.bowHeldDraw=Math.min(1,a.elapsed/drawTime);
   const clip=player.clips[state],anim=clip&&player.animation?.getState(clip.name);
   if(anim){
    if(state==='hit'&&hurtProgress!==undefined){anim.speed=0;anim.time=hurtProgress*clip.duration;anim.sample();}
    else if(a&&(a.skillId||a.kind.startsWith('pure:'))&&state==='attack_bow'){
     const hold=player.metadata.libraryMotion?.clips?.attack_bow?.holdFraction??.65,release=Math.max(.0001,a.releaseAt??a.duration*.5),fraction=!a.emitted||a.elapsed<release?hold*Math.min(1,a.elapsed/release):hold+(1-hold)*Math.max(0,Math.min(1,(a.elapsed-release)/Math.max(.001,a.duration-release)));
     anim.speed=0;anim.time=fraction*clip.duration;anim.sample();
    }else if(a?.kind==='bow'&&state==='attack_bow'){
     const hold=player.metadata.libraryMotion?.clips?.attack_bow?.holdFraction??.65;anim.speed=0;
     const delay=a.charged?0:.12,draw=player.bowHeldDraw??0,fraction=delay>0&&a.elapsed<delay?hold*(draw+(1-draw)*a.elapsed/delay):hold+(1-hold)*Math.min(1,(a.elapsed-delay)/Math.min(.16,Math.max(.001,a.duration-delay)));
     anim.time=fraction*clip.duration;anim.sample();
    }else if(a?.kind==='skill'&&state==='attack_bow'){
     const hold=player.metadata.libraryMotion?.clips?.attack_bow?.holdFraction??.65;anim.speed=0;anim.time=(a.elapsed<.25?hold*a.elapsed/.25:hold+(1-hold)*Math.min(1,(a.elapsed-.25)/Math.max(.001,a.duration-.25)))*clip.duration;anim.sample();
    }else if(a&&a.kind!=='bowAim'&&state!=='hit'&&state!=='death'){
     const sampling=player.metadata.libraryMotion?.clips?.[state]?.phaseSampling;
     if(sampling||state.startsWith('attack_sword')){anim.speed=0;anim.time=this.samplePlayerFraction(player,state,a)*clip.duration;if(player.animation?.useBakedAnimation)anim.sample();}
     else anim.speed=clip.duration/a.duration;
    }else if(a?.kind==='bowAim'&&state==='attack_bow'){
     anim.speed=0;anim.time=Math.min(1,a.elapsed/drawTime)*(player.metadata.libraryMotion?.clips?.attack_bow?.holdFraction??.65)*clip.duration;anim.sample();
    }else anim.speed=state.startsWith('walk')?Math.max(.1,Math.min(2.5,speed/player.stride.walk)):state.startsWith('run')?Math.max(.1,Math.min(1.8,speed/player.stride.run)):state==='hit'?1.25:1;
   }
   if(anim&&!a&&locomotion?.active&&state!==previousState&&(state.startsWith('walk')||state.startsWith('run')))anim.time=locomotion.stridePhase*clip.duration;
   this.contactPose(player,game.state.time);
   const id=game.state.equipment.weapon,kind=this.syncPlayerWeapon(player,id,!this.carryReadiness.ready&&game.state.player.hp>0);this.applyParts(player,game.state.equipment.head==='A02');this.drawBow(player,this.bowWeight(player),kind==='bow'&&(a?.kind==='bowAim'||!!a&&state==='attack_bow'&&!a.emitted));
  }
  for(const e of game.state.enemies){
   const actor=this.active.get(e.id);if(!actor){if(!this.silverPlayer&&!this.arriving.has(e.id)&&!this.arrivalFailure.has(e.id)){this.arriving.add(e.id);void this.create(e.id,e.kind==='captain'?'captain':e.kind==='archer'?'raider-archer':e.kind==='shield'?'raider-shield':'raider',e.x,e.z).catch(error=>{this.arrivalFailure.add(e.id);console.error('[Campaign] Reinforcement could not load',error);}).finally(()=>this.arriving.delete(e.id));}continue;}const speed=Math.min(6,Math.hypot(e.x-actor.root.position.x,e.z-actor.root.position.z)/Math.max(.001,dt));actor.speed=speed;actor.root.setPosition(e.x,this.world.height(e),e.z);const locked=['windup','active','recovery'].includes(e.phase),turn=Math.atan2(Math.sin(e.angle-(actor.yaw??e.angle)),Math.cos(e.angle-(actor.yaw??e.angle)));actor.yaw=locked?e.angle:(actor.yaw??e.angle)+turn*(1-Math.exp(-dt*12));actor.root.setRotationFromEuler(0,actor.yaw*180/Math.PI,0);
   const attacking=['windup','active','recovery'].includes(e.phase),pose=enemyProfile(e)?.attacks[e.combat?.moveId??'']?.pose;
   if(pose)actor.enemyPose=pose;else if(!attacking)actor.enemyPose=undefined;
   const requested=e.hp<=0?'death':e.phase==='stagger'||game.enemyHitReaction(e.id)?.flinch&&!attacking?'hit':attacking?(pose??actor.enemyPose??(e.kind==='archer'?'attack_bow':'attack_sword')):e.phase==='approach'&&speed>.08?(actor.clips.walk?'walk':'run'):'idle';
   // Missing cast/command clips use this actor's own idle, never a bow/sword substitution.
   const state=actor.clips[requested]?requested:'idle';
   if(actor.phase!==e.phase){actor.phase=e.phase;actor.phaseDuration=Math.max(.001,e.phaseTime);}
   this.play(actor,state);const clip=actor.clips[state],anim=clip&&actor.animation?.getState(clip.name);
   actor.root.active=game.corpseOpacity(e)>0;
   if(e.hp<=0){this.drawBow(actor,0,false);if(anim){anim.speed=0;anim.time=state==='death'?Math.min(Math.max(0,game.state.time-(e.diedAt??game.state.time)),Math.max(0,clip.duration-.001)):0;anim.sample();}if(state!=='death')actor.model.setRotationFromEuler(0,actor.metadata.modelYaw??0,78);}
   else if(anim&&attacking&&state!=='idle'){const progress=Math.max(0,Math.min(1,1-e.phaseTime/(actor.phaseDuration??1))),bow=state==='attack_bow';const hold=actor.metadata.libraryMotion?.clips?.attack_bow?.holdFraction??.65,active=bow?Math.min(1,hold+.12):.5;const fraction=e.phase==='windup'?progress*(bow?hold:.27):e.phase==='active'?(bow?hold:.27)+progress*(bow?active-hold:.23):(bow?active:.5)+progress*(bow?1-active:.5);anim.speed=0;anim.time=fraction*clip.duration;anim.sample();this.drawBow(actor,bow?this.bowWeight(actor):0,bow&&e.phase==='windup');}
   else {this.drawBow(actor,0,false);if(anim)anim.speed=state==='walk'?Math.max(.1,Math.min(2.5,speed/actor.stride.walk)):state==='run'?Math.max(.1,Math.min(1.8,speed/actor.stride.run)):1;}
   this.enemyContact(actor,e,game);
  }
  for(const actor of this.active.values()){actor.clock+=dt;if(actor.paused){actor.animation?.resume();actor.paused=false;}}
 }
 destroy(){this.resetEnemyContacts();this.enemyTints.clear();this.enemyBaseScale.clear();this.bodyBatches?.destroy();this.bodyBatches=undefined;this.disposed=true;this.hairRevision++;this.releaseHair(this.hairMaterials);this.hairMaterials=undefined;for(const owner of this.hairLoads)this.releaseHair(owner);this.hairLoads.clear();this.hairSources.clear();this.combatLocomotion?.destroy();this.combatLocomotion=undefined;for(const actor of this.active.values())if(actor.root.isValid)actor.root.destroy();for(const material of this.pbrMaterials.values())material.destroy();this.pbrMaterials.clear();for(const material of this.carryMaterials)material.destroy();for(const mesh of this.carryMeshes)mesh.destroy();this.carryMaterials=[];this.carryMeshes=[];this.nativeMaterials.destroy();this.weaponMaterials.destroy();this.active.clear();}
 playerPresentation():PlayerPresentation|undefined {
  const actor=this.active.get('player');if(!actor)return;
  const family=weaponFamily(actor.renderedWeaponId??'W01'),kind=weaponAttachmentKind(actor.renderedWeaponId??'W01')==='greatsword'&&actor.weapons.greatsword?'greatsword':family,emptyHandCast=actor.state==='spell'&&!actor.weapons.staff?.active;
  const socket=emptyHandCast?actor.weapons.sword:actor.state==='spell'?actor.weapons.staff:family==='bow'?(actor.weapons.arrow??actor.weapons.bow):actor.weapons[kind];
  const binding=family==='bow'&&!emptyHandCast?undefined:actor.swordCarry?.grips[emptyHandCast?'sword':kind];
  // Spell/melee emitters stay at the real palm even while the visible sword
  // is on the back, including the first frame of an attack or weapon change.
  const hand=binding?Vec3.transformMat4(new Vec3(),binding.handPosition,binding.handParent.worldMatrix):socket?.worldPosition.clone()??actor.root.worldPosition.clone().add(new Vec3(0,1.2,0));
  return {actionId:actor.actionId,phase:actor.motion?.phase,beat:actor.motion?.beat??0,facing:(actor.yaw??0),hand,pose:actor.state,ordinal:actor.motion?.ordinal??0};
 }
 playerModel():Node|null{return this.active.get('player')?.model??null;}
 inspect(){return Array.from(this.active.values()).map(a=>({id:a.id,profile:a.metadata.runtimeProfile??'legacy',expectedSkinJoints:a.metadata.skinJointCount??53,expectedSkeletonSizes:[a.metadata.skinJointCount??53,a.metadata.skeletonJointCount??a.metadata.skinJointCount??53],clips:Object.keys(a.clips),state:a.state,speed:a.speed??0,position:{x:a.root.position.x,y:a.root.position.y,z:a.root.position.z},weaponCarry:a.id==='player'?(a.swordCarry?.grips[weaponAttachmentKind(a.renderedWeaponId??'W01')]?.stowed?'stowed':'ready'):undefined,combatReady:a.id==='player'?this.carryReadiness.ready:undefined,combatLocomotion:a.id==='player'?this.combatLocomotion?.inspect():undefined,skeletons:a.model.getComponentsInChildren(SkinnedMeshRenderer).map(s=>s.skeleton?.joints.length||0)}));}
}
