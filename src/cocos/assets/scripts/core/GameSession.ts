import {equipmentText as gearText} from '../features/equipment/locales';
import type { AreaDef, EnemySpawn, ExitDef, GameEvent, InputFrame, InteractionDef, Point, WorldQuery, SkillProjectileMetadata,AttackFeedbackMetadata } from './Contracts';
import { EQUIPMENT, MERCHANTS, RECIPES, canonicalItem, canonicalMerchant,equipmentPowerMultiplier,equipmentStackLimit, type EquipmentSlot,type ItemDef } from '../features/equipment/data/Equipment';
import {SKILLS,freshDiceState,skillModifiers,rollMode,drawCheckRoll,checkChance,type DiceState,type DiceView,type CheckContext} from '../features/progression/common/SkillChecks';
import {SKILL_CHECKS} from '../features/progression/data/SkillChecks';
import {EquipmentDice,itemGearBonus,equippedGearBonus,bonusText,effectiveAttribute,combatCriticalChance,combatCriticalMultiplier} from '../features/equipment/common/EquipmentDice';
import {equipmentChange} from '../features/equipment/common/EquipmentChange';
import {EquipmentForging,freshForging,itemForgingView,syncRandomForging,type ForgingState} from '../features/crafting/common/EquipmentForging';
import {forgingAffixText} from '../features/crafting/data/EquipmentForging';
import {ACTION_NAMES} from '../features/progression/common/SkillChecks';
import {PureCombat,freshCombat,type CombatState} from '../features/combat/common/PureCombat';
import {MeleeCombo,meleeCombo,MELEE_INPUT_BUFFER} from '../features/combat/common/MeleeCombo';
import {freshProgression,allocatedSkillRank,skillPlanRemaining,unlockSkills,awardXp,baseMaxHp,cumulativeXp,progressionView,validateProgression,updateExperienceCurve,type ProgressionState,type Attribute,ATTRIBUTES} from '../features/progression/common/Progression';
import {PURE_SKILLS,COMBAT_RULES,RETIRED_SPELL_TO_SKILL} from '../features/combat/data/PureSkills';
import {CAMPAIGN_ENEMY_TEMPLATES,CAMPAIGN_LEVELS,MAIN_XP_EVENTS} from '../features/campaign/data/Campaign';
import {CAMPAIGN_EVENTS,type CampaignEventDef} from '../features/campaign/data/CampaignEvents';
import {campaignFighter,combatGroup,CAMPAIGN_FORMATION} from '../features/campaign/data/CampaignBattles';
import {validateCurrentSnapshot,migrateRemovedOil} from '../features/persistence/common/CombatPersistence';
import {CampaignLoot} from '../features/campaign/common/CampaignLoot';
import {EnemyCombat,enemyProfile,enemyHurtRadius,enemyHealthMultiplier,enemyDamageMultiplier,enemyGuardMultiplier,type EnemyMoveState,type EnemyHazardState,type EnemyProjectileMetadata} from '../features/combat/common/EnemyCombat';
import {HUNT_ENCOUNTERS,HUNTING_GROUNDS,HUNT_LAYOUT_VERSION,locationEntryLevel,huntingBaseHp} from '../features/world/data/MonsterEcology';
import {playerCombatAttributes,enemyCombatAttributes,rollContactHit} from '../features/combat/common/CombatAccuracy';
import {RESOURCE_RULES,resourceProfile,synchronizeResource,migrateClassResource,type ResourceKind} from '../features/combat/common/ClassResource';
import {SUPPLIES,SUPPLY_LOOT_POLICY,isSupplyId,type SupplyId} from '../features/equipment/data/Supplies';
import {GROWING_EQUIPMENT,GROWING_BOSS_DROPS,growingStats,growingDescription,growingQuestVisible,growingJournal} from '../features/equipment/data/GrowingEquipment';
import {GrowingEquipmentLoot,growingOwned} from '../features/equipment/common/GrowingEquipmentLoot';
import type {EnemyDamageElement} from '../features/combat/data/EnemyCombat';
import {ChapterJourney,initializeLifecycleJourney} from '../features/journey/common/ChapterJourney';
import {CampaignDirector} from '../features/cinematics/common/CampaignDirector';
import {EnemyHitResponse} from '../features/combat/common/EnemyHitResponse';
import {playableArea,chapterForArea,PLAYABLE_CHAPTERS} from '../features/journey/data/ChapterJourney';
import {COMBAT_LOADOUTS,prepareCombatLoadout,rememberCombatLoadout,activateCombatLoadout,assignedLoadout,migrateFourSkillKit,type CombatFamily} from '../features/progression/common/CombatLoadouts';
import {huntingExperienceView,takeCombatExperience,ensureDailyExperience} from '../features/progression/common/HuntingExperience';
import {huntingKillExperience} from '../features/progression/data/HuntingExperience';
import {BossLoot} from '../features/equipment/common/BossLoot';
import {releasedEquipmentChapter} from '../features/equipment/data/EquipmentLifecycle';

export const ENEMY_ARCHER_START_RANGE=14;
export const ENEMY_ARCHER_SHOT_RANGE=18;
export const DISENGAGEMENT_SECONDS={cleared:1,retreat:5} as const;
// Shared by basic hit detection, projectile travel and the targeting display.
export const BASIC_ATTACK={sword:{rangeMetres:1.85,angleDegrees:110},bow:{rangeMetres:9,angleDegrees:0},staff:{rangeMetres:7,angleDegrees:0}} as const;
export interface PlayerState extends Point { hp:number; maxHp:number; focus:number; maxFocus:number; resourceVersion:1; staminaPotions:number; manaPotions:number; healthPotions:number; focusPotions:number; gold:number; iron:number; runes:number; cores:number; angle:number; hurtTime:number; shield:number; movingTime:number }
export interface EnemyState extends EnemySpawn { hp:number; maxHp:number; angle:number; phase:'idle'|'approach'|'windup'|'active'|'recovery'|'stagger'|'dead'; phaseTime:number; attackCount:number; targetAngle:number; attackKind:'swing'|'charge'|'shot'|'short'; struck:boolean; markedUntil:number; lightningUntil:number; pushImmuneUntil:number; staggerProtectedUntil:number; halfAnnounced:boolean;combat?:EnemyMoveState;respawnAt?:number;respawnCount?:number;diedAt?:number }
export interface GroundLoot extends Point {id:string;area:string;item:string;source:string;createdAt:number;count?:number;supplyVersion?:2|3}
export const LOOT_PICKUP_RADIUS=1.35;
export const CORPSE_SECONDS=30;
/** The retired oil kind is accepted only while validating legacy saves. */
export interface ProjectileState extends Point, SkillProjectileMetadata, EnemyProjectileMetadata { id:string; kind:'arrow'|'staff'|'spell'|'crossbow'|'oil'|'blade'|'flame'; accuracy?:number; angle:number; speed:number; remaining:number; damage:number; owner:'player'|'enemy'; weapon:string; hits:string[]; leg:'out'|'back'; returning:boolean; charged:boolean; pierce:number; age:number; target?:Point; origin?:Point; releasedAt?:number }
export interface DialogueState { id:string; speaker:string; text:string; options:{id:string;label:string}[] }
export interface ActionState extends AttackFeedbackMetadata { accuracy?:number; id:string; kind:string; elapsed:number; duration:number; angle:number; hits:string[]; emitted:boolean; damage:number; target?:Point; charged?:boolean; skillId?:string; rank?:number; releaseAt?:number;comboStage?:number }
export interface FireZone extends Point { id:string; remaining:number; tick:number; radius:number }
export interface BarrelState extends Point { id:string; fuse:number; exploded:boolean }
export interface EquipmentState { weapon:string; offhand:string|null; head:string|null; chest:string|null; hands:string|null; feet:string|null; ringLeft:string|null; ringRight:string|null; necklace:string|null; spells:[string|null,string|null] }
export interface GameState {
 forging:ForgingState;
 dice:DiceState;
 version:3; progression:ProgressionState; combat:CombatState; seed:number; area:string; time:number; sequence:number; revision:number; status:'playing'|'dead'|'complete';
 player:PlayerState; enemies:EnemyState[]; encounters:Record<string,EnemyState[]>; projectiles:ProjectileState[]; fireZones:FireZone[]; barrels:BarrelState[];
 enemyHazards:EnemyHazardState[];
 groundLoot:GroundLoot[];
 flags:Record<string,boolean>; inventory:Record<string,number>; provenance:Record<string,string>; pending:Record<string,number>;
 equipment:EquipmentState; dialogue:DialogueState|null; action:ActionState|null; cooldowns:Record<string,number>;
 receipts:Record<string,string|number|boolean>; recipes:string[]; merchantStock:Record<string,Record<string,number>>; discoveredMerchants:string[];
 checkpoint:{area:string;x:number;z:number}; dropRolls:Record<string,{roll:number;result:string}>; movedDistance:number; effectCounters:Record<string,number>;
}
const dist=(a:Point,b:Point)=>Math.hypot(a.x-b.x,a.z-b.z);
const clamp=(n:number,a:number,b:number)=>Math.max(a,Math.min(b,n));
const deltaAngle=(a:number,b:number)=>Math.atan2(Math.sin(a-b),Math.cos(a-b));
const clone=<T>(x:T):T=>JSON.parse(JSON.stringify(x));
const direction=(angle:number,length:number):Point=>({x:Math.sin(angle)*length,z:Math.cos(angle)*length});
const aim=(a:Point,b:Point)=>Math.atan2(b.x-a.x,b.z-a.z);
const finite=(n:unknown,min:number,max:number)=>typeof n==='number'&&Number.isFinite(n)&&n>=min&&n<=max;
const record=(x:unknown):x is Record<string,any>=>!!x&&typeof x==='object'&&!Array.isArray(x)&&Object.getPrototypeOf(x)===Object.prototype;
const point=(x:unknown):x is Point & Record<string,any>=>record(x)&&finite(x.x,-5000,5000)&&finite(x.z,-5000,5000);
const sourceRandom=(seed:number,source:string)=>{let n=seed;for(let i=0;i<source.length;i++)n=(n*131+source.charCodeAt(i))%2147483647;return ((n+1)*48271)%2147483647;};

/** Simulation uses the saved world clock; daily XP uses an injectable calendar.
 * Rules are independent of the renderer and storage platform. */
export class GameSession {
 state:GameState;
 dirty=false;
 private areaDef:AreaDef|null=null;
 // Presentation profiles configure travel speed without changing saved state.
 private movementSpeed=3.6;
 setMovementSpeed(metresPerSecond:number){if(Number.isFinite(metresPerSecond)&&metresPerSecond>0)this.movementSpeed=metresPerSecond;}
 basicAttackProfile(){return BASIC_ATTACK[EQUIPMENT[this.state.equipment.weapon]?.kind as keyof typeof BASIC_ATTACK]??BASIC_ATTACK.sword;}
 basicAutoAimTarget():Point|undefined {
  const s=this.state,p=s.player,profile=this.basicAttackProfile();let nearest:EnemyState|undefined,best=Infinity;
  for(const enemy of s.enemies){
   const metres=dist(p,enemy),reach=profile.rangeMetres+(profile.angleDegrees>0?Math.max(.25,enemyHurtRadius(enemy)-.05):0);
   if(enemy.hp<=0||metres>reach+.001||metres>best||!this.visible(p,enemy))continue;
   if(metres===best&&nearest&&enemy.id.localeCompare(nearest.id)>=0)continue;
   nearest=enemy;best=metres;
  }
  return nearest?{x:nearest.x,z:nearest.z}:undefined;
 }
 private previous:InputFrame={x:0,z:0};
 private events:GameEvent[]=[];
 private merchant:string|null=null;
 private merchantAnchor:Point|null=null;
 private navigation=new Map<string,{points:Point[];until:number}>();
 private secondaryCounts=new Map<string,number>();
 private explosionDamage=new Map<string,number>();
 private nextSupplySweep=0;
 private readonly meleeChain=new MeleeCombo();
 private combatRules:PureCombat=new PureCombat({state:()=>this.state,visible:(a,b)=>this.visible(a,b),move:(p,d,r)=>this.move(p,d,r),id:p=>this.id(p),emit:(type,text,extra)=>this.emit(type,text,extra),damage:(e,value,cast,element,angle,critical)=>this.damageEnemy(e,value,cast,element==='relic'||element==='relicPhysical'||element==='secondary'||element==='burn'?element:['FIR','THU'].includes(element)?'spell':'pure',angle,{element,critical}),miss:(e,action,chance,roll)=>this.missEnemy(e,action,chance,roll),anchors:()=>this.enemyRules.anchors(),damageAnchor:(id,damage,cast)=>this.enemyRules.damageAnchor(id,damage,cast),changed:()=>this.changed()});
 private lootRules=new CampaignLoot({state:()=>this.state,grant:(item,count,source,at)=>at?this.dropEquipment(item,source,at):this.grant(item,count,source),supply:(item,count,source,at)=>this.dropSupply(item,count,source,at),changed:()=>this.changed(),emit:(type,text,extra)=>this.emit(type,text,extra)});
 readonly bossLoot=new BossLoot({state:()=>this.state,now:()=>this.calendarNow(),grant:(item,source,at)=>this.dropEquipment(item,source,at),changed:()=>this.changed(),emit:(t,m,x)=>this.emit(t,m,x)});
 private growingLoot=new GrowingEquipmentLoot({state:()=>this.state,grant:(item,count,source,at)=>at?this.dropEquipment(item,source,at):this.grant(item,count,source),changed:()=>this.changed(),emit:(t,m,x)=>this.emit(t,m,x)});
 private equipmentDice=new EquipmentDice({state:()=>this.state,grant:(item,count,source)=>this.grant(item,count,source),recalculate:()=>this.recalculate(),changed:()=>this.changed(),emit:(t,m,x)=>this.emit(t,m,x)});
 readonly forging=new EquipmentForging({state:()=>this.state,availability:()=>this.forgingAvailability(),id:p=>this.id(p),changed:()=>this.changed(),recalculate:()=>this.recalculate(),emit:(t,m)=>this.emit(t,m)});
 readonly journey=new ChapterJourney({state:()=>this.state,grant:(id,source)=>this.grant(id,1,source),experience:(source,amount)=>{this.gainExperience(source,amount);},changed:()=>this.changed(),emit:(type,text,extra)=>this.emit(type,text,extra)});
 readonly campaign=new CampaignDirector({state:()=>this.state,spawnWave:enemies=>this.spawnCampaignWave(enemies),experience:(source,amount)=>{this.gainExperience(source,amount);},changed:()=>this.changed(),emit:(type,text,extra)=>this.emit(type,text,extra)});
 private enemyRules:EnemyCombat=new EnemyCombat({speed:e=>this.combatRules.enemySpeed(e),state:()=>this.state,id:prefix=>this.id(prefix),visible:(a,b)=>this.visible(a,b),move:(p,d,r)=>this.move(p,d,r),path:(a,b)=>this.world.path?.(a,b)??[],emit:(type,text,extra)=>this.emit(type,text,extra),hurt:(damage,source,heavy,element,ground,hitId)=>this.hurt(damage,source,heavy,element,ground,hitId),changed:()=>this.changed()});
 private hitResponse=new EnemyHitResponse({state:()=>this.state,move:(e,d,r)=>this.move(e,d,r),height:p=>this.world.height(p),shift:(e,d)=>this.enemyRules.shiftCaster(e,d),emit:(t,m,x)=>this.emit(t,m,x)});
 enemyHitReaction(id:string){return this.hitResponse.view(id);}
  constructor(seed:number, private world:WorldQuery,private calendarNow:()=>number=Date.now) {
  const n=Number.isFinite(seed)?Math.floor(Math.abs(seed))%2147483646+1:73014;
  this.state={forging:freshForging(),dice:freshDiceState(),version:3,progression:freshProgression(),combat:freshCombat(),seed:n,area:'S01',time:0,sequence:0,revision:0,status:'playing',player:{x:0,z:0,hp:120,maxHp:120,focus:100,maxFocus:100,resourceVersion:1,staminaPotions:2,manaPotions:2,healthPotions:3,focusPotions:2,gold:0,iron:0,runes:0,cores:0,angle:0,hurtTime:0,shield:0,movingTime:0},enemies:[],encounters:{},projectiles:[],fireZones:[],barrels:[],flags:{},inventory:{W01:1,W07:1,W11:1},provenance:{W01:'initial',W07:'initial',W11:'initial'},pending:{},equipment:{weapon:'W01',offhand:null,head:null,chest:null,hands:null,feet:null,ringLeft:null,ringRight:null,necklace:null,spells:[null,null]},dialogue:null,action:null,cooldowns:{},receipts:{initial:true,'lifecycle:v3':true},recipes:[],merchantStock:Object.fromEntries(Object.entries(MERCHANTS).map(([id,m])=>[id,{...m.stock}])),discoveredMerchants:[],checkpoint:{area:'S01',x:0,z:0},dropRolls:{},movedDistance:0,effectCounters:{},enemyHazards:[],groundLoot:[]};
  prepareCombatLoadout(this.state.combat,this.state.equipment.weapon,this.state.progression);
 }
 private changed(){this.state.revision++;this.dirty=true;}
 private emit(type:string,text?:string,extra:Record<string,unknown>={}){this.events.push({type,text,...extra});}
 private drain(){const events=this.events;this.events=[];return events;}
 private id(prefix:string){return `${prefix}:${++this.state.sequence}`;}
 private once(id:string,work:()=>void){if(this.state.receipts[id])return false;work();this.state.receipts[id]=true;this.changed();return true;}
 private gold(id:string,n:number){this.once(id,()=>{this.state.player.gold=Math.min(9999,this.state.player.gold+n);this.emit('reward',`金币 +${n}`,{id,value:n});});}
 private dropEquipment(item:string,source:string,at:Point){
  const s=this.state,id=canonicalItem(item),def=EQUIPMENT[id];if(!def||(s.inventory[id]??0)>=equipmentStackLimit(id)||s.groundLoot.some(d=>d.item===id))return;
  // A pile owns its roll until pickup; inventory and forging begin only then.
  const siblings=s.groundLoot.filter(d=>d.area===s.area&&dist(d,at)<1.1).length;
  const candidate=siblings?this.world.move(at,direction(siblings*2.4,.65),.16):at;
  const place=point(candidate)&&this.visible(at,candidate)?candidate:at;
  const drop:GroundLoot={id:this.id('loot'),area:s.area,item:id,source,x:place.x,z:place.z,createdAt:s.time};
  s.groundLoot.push(drop);this.changed();this.emit('loot_drop',`${def.name}掉落在地，靠近后拾取`,{id:drop.id,item:id,at:{x:drop.x,z:drop.z}});
 }
 private pruneSupplies(force=false){
  const s=this.state;if(!force&&s.time<this.nextSupplySweep)return;this.nextSupplySweep=s.time+.5;
  const length=s.groundLoot.length;
  s.groundLoot=s.groundLoot.filter(d=>!isSupplyId(d.item)||d.createdAt+SUPPLY_LOOT_POLICY.lifetimeSeconds>s.time);
  if(s.groundLoot.length!==length)this.changed();
 }
 private dropSupply(item:SupplyId,count:number,source:string,at:Point){
  const s=this.state;if(s.groundLoot.some(d=>d.source===source))return;this.pruneSupplies(true);
  const supplies=s.groundLoot.filter(d=>isSupplyId(d.item)),local=supplies.filter(d=>d.area===s.area);
  const oldest=(drops:GroundLoot[])=>drops.reduce((a,b)=>a.createdAt<=b.createdAt?a:b);
  const discard=local.length>=SUPPLY_LOOT_POLICY.maxPilesPerArea?oldest(local):supplies.length>=SUPPLY_LOOT_POLICY.maxPiles?oldest(supplies):undefined;
  if(discard)s.groundLoot=s.groundLoot.filter(d=>d.id!==discard.id);
  const siblings=s.groundLoot.filter(d=>d.area===s.area&&dist(d,at)<1.1).length,candidate=siblings?this.world.move(at,direction(siblings*2.4,.65),.16):at;
  const place=point(candidate)&&this.visible(at,candidate)?candidate:at;
  const drop:GroundLoot={id:this.id('loot'),area:s.area,item,count,source,supplyVersion:3,x:place.x,z:place.z,createdAt:s.time};
  s.groundLoot.push(drop);this.changed();this.emit('loot_drop',`${SUPPLIES[item].name} ×${count}`,{id:drop.id,item,count,at:{x:drop.x,z:drop.z}});
 }
 canPickupLoot(drop:GroundLoot){const def=isSupplyId(drop.item)?SUPPLIES[drop.item]:undefined;return def?this.state.player[def.stock]<def.capacity:(this.state.inventory[drop.item]??0)<equipmentStackLimit(drop.item);}
 nearbyLoot(includeUnavailable=false){return this.state.groundLoot.filter(d=>d.area===this.state.area&&(includeUnavailable||this.canPickupLoot(d))&&dist(d,this.state.player)<=LOOT_PICKUP_RADIUS&&this.visible(this.state.player,d)).sort((a,b)=>Number(!this.canPickupLoot(a))-Number(!this.canPickupLoot(b))||Number(isSupplyId(a.item))-Number(isSupplyId(b.item))||dist(a,this.state.player)-dist(b,this.state.player)||a.id.localeCompare(b.id));}
 private collectSupply(drop:GroundLoot){
  if(!isSupplyId(drop.item))return;
  const def=SUPPLIES[drop.item],p=this.state.player,count=drop.count??1,taken=Math.min(count,def.capacity-p[def.stock]);
  if(taken<=0)return;
  p[def.stock]+=taken;if(taken===count)this.state.groundLoot=this.state.groundLoot.filter(d=>d.id!==drop.id);else drop.count=count-taken;
  this.changed();this.emit('supply_pickup',`${def.name} +${taken}`,{id:drop.id,item:drop.item,value:taken,remaining:count-taken});
 }
 private collectNearbySupplies(){
  if(this.state.player.hp<=0)return;
  for(const drop of this.state.groundLoot)if(drop.area===this.state.area&&isSupplyId(drop.item)&&this.canPickupLoot(drop)&&dist(drop,this.state.player)<=LOOT_PICKUP_RADIUS&&this.visible(this.state.player,drop))this.collectSupply(drop);
 }
 pickupLoot(id:string):GameEvent[]{
  const s=this.state,drop=s.groundLoot.find(d=>d.id===id&&d.area===s.area);
  if(!drop||s.status==='dead'||s.player.hp<=0||s.dialogue||s.dice.active||s.action)return [];
  if(dist(s.player,drop)>LOOT_PICKUP_RADIUS||!this.visible(s.player,drop)){this.emit('notice','靠近并绕过阻挡后拾取');return this.drain();}
  if(isSupplyId(drop.item)){if(!this.canPickupLoot(drop))this.emit('notice',`${SUPPLIES[drop.item].name}已满`);else this.collectSupply(drop);return this.drain();}
  if(!this.canPickupLoot(drop)){this.emit('notice',`${EQUIPMENT[drop.item].name}已满 · ${equipmentStackLimit(drop.item)}/${equipmentStackLimit(drop.item)}`);return this.drain();}
  s.groundLoot=s.groundLoot.filter(d=>d.id!==id);this.grant(drop.item,1,drop.source);this.changed();return this.drain();
 }
 corpseOpacity(enemy:EnemyState){return enemy.hp>0?1:enemy.diedAt===undefined?0:clamp((enemy.diedAt+CORPSE_SECONDS-this.state.time)/3,0,1);}
 private grant(item:string,count:number,source:string){
  const id=canonicalItem(item),def=EQUIPMENT[id];if(RETIRED_SPELL_TO_SKILL[id]){this.state.receipts[`legacy-skill:${source}:${id}`]=true;this.emit('skill_learned','传承已记录；技能按章节开放，强化请分配技能点',{id:RETIRED_SPELL_TO_SKILL[id]});this.changed();return;}if(!def)return;
  if(GROWING_EQUIPMENT[id]){if(growingOwned(this.state,id)){this.emit('notice',`${def.name}本旅程已经获得过，不会重复领取。`);return;}this.state.receipts[`growing-owned:${id}`]=source;count=1;}
  const owned=this.state.inventory[id]??0,accepted=Math.max(0,Math.min(count,equipmentStackLimit(id)-owned));
  if(!accepted){this.emit('notice',`${def.name}已达叠加上限 ${equipmentStackLimit(id)}`);return;}
  this.state.inventory[id]=owned+accepted;
  this.state.provenance[id]??=source;this.state.receipts[`grant:${source}:${id}`]=true;
  if(!owned)this.equipmentDice.enqueue(id,source);
  this.emit('item',`获得${def.name}${accepted>1?` ×${accepted}`:''}`,{id,value:accepted});this.changed();
 }
 enter(area:AreaDef,entry?:Point):GameEvent[]{
  this.hitResponse.reset();this.meleeChain.reset();
  this.enemyRules.reset();
  const same=this.state.area===area.id;if(!same)this.state.dice.active=null;
  if(!same)this.combatRules.resetTransient();
  if(this.areaDef)this.state.encounters[this.areaDef.id]=clone(this.state.enemies);
  this.areaDef=area;this.state.area=area.id;
  const p=entry??(same&&this.state.encounters[area.id]?this.state.player:area.spawn);
  this.state.player.x=clamp(p.x,-area.width/2+.35,area.width/2-.35);this.state.player.z=clamp(p.z,-area.depth/2+.35,area.depth/2-.35);
  this.state.enemies=this.state.flags[`visited:${area.id}`]&&this.state.encounters[area.id]?clone(this.state.encounters[area.id]):area.enemies.map(e=>this.spawn(e));
  this.syncHuntingPacks();
  this.pruneSupplies(true);
  this.respawnHunts();
  this.state.encounters[area.id]=clone(this.state.enemies);
  this.state.projectiles=[];this.state.fireZones=[];this.state.action=null;this.state.dialogue=null;this.previous={x:0,z:0};this.merchant=null;this.merchantAnchor=null;this.navigation.clear();
  this.state.barrels=area.obstacles.filter(o=>o.kind==='barrel').map((o,i)=>({id:`${area.id}:barrel:${i}`,x:o.x,z:o.z,fuse:-1,exploded:!!this.state.flags[`${area.id}:barrel:${i}:exploded`]}));
  this.state.flags[`visited:${area.id}`]=true;
  if(chapterForArea(area.id)>=2&&unlockSkills(this.state.progression,true)){activateCombatLoadout(this.state.combat,this.state.progression);this.state.progression.ultimateGiftClaimed=true;this.state.combat.charge=0;this.emit('notice','全部技能已开放为1级，获得2技能点；请在安全检查点自由加点。');}
  if(area.checkpoint&&this.safe())this.setCheckpoint();
  this.recalculate();this.changed();this.emit('area',area.name,{id:area.id});return this.drain();
 }
 private spawn(e:EnemySpawn):EnemyState {const def=CAMPAIGN_ENEMY_TEMPLATES[e.templateId??e.bossId??''],level=e.level??def?.level??1,base=huntingBaseHp(e)??def?.baseHp??def?.hp??e.hp??({raider:72,shield:105,archer:60,captain:360}[e.kind]),maxHp=campaignFighter(e)?.maxHp??Math.round(base*enemyHealthMultiplier(e)*(1+.14*(level-1))),movement=enemyProfile(e)?.movement,angle=movement?.stationary&&movement.facingPoint?aim(e,movement.facingPoint):0;return {...e,level,hp:maxHp,maxHp,angle,phase:'idle',phaseTime:.35,attackCount:0,targetAngle:angle,attackKind:'swing',struck:false,markedUntil:0,lightningUntil:0,pushImmuneUntil:0,staggerProtectedUntil:0,halfAnnounced:false};}
 private enemyDamage(e:EnemyState,base:number){const def=CAMPAIGN_ENEMY_TEMPLATES[e.templateId??e.bossId??''],reference=e.kind==='captain'?22:e.kind==='shield'?16:e.kind==='archer'?14:12;return (def?.baseDamage??def?.damage??reference)*(base/reference)*(1+.045*((e.level??1)-1))*enemyDamageMultiplier(e);}
 private checkHelp(id:string):string|null {
  const s=this.state;if(['mira-motive','mira-terms'].includes(id)&&s.flags.saw_copy)return '已核对的求援抄件';
  if(['inn-lockbox','quarry-runes'].includes(id)&&s.discoveredMerchants.includes('lorn'))return '洛恩的工具指引';
  if(id==='grave-record'&&s.flags.independent_clue)return '信使副本的日期';
  if(id==='undercity-disarm'&&s.flags.read_letter)return '原信中的退路提示';return null;
 }
 private checkContext(id:string):CheckContext {const f=this.state.flags,def=SKILL_CHECKS[id];const advantage=id==='mira-motive'&&(f.saw_copy||f['check:grave-record:passed'])||id==='mira-terms'&&(f['check:mira-motive:passed']||f['check:grave-record:passed'])||id==='undercity-disarm'&&f['check:quarry-runes:passed'];const disadvantage=id==='mira-terms'&&f['check:mira-motive:failed'];return {mode:rollMode(!!advantage,!!disadvantage),modifiers:skillModifiers(def.skill),helpDie:false,helpLabel:this.checkHelp(id)};}
 private beginCheck(id:string,sourceId:string):void {
  const s=this.state,def=SKILL_CHECKS[id],source=this.areaDef?.objects.find(o=>o.id===sourceId);if(!def||def.area!==s.area||def.sourceId!==sourceId||!source||s.dice.active||s.status==='dead'||dist(s.player,source)>1.35||!this.visible(s.player,source)||!this.safe())return;
  if(id==='undercity-disarm'&&!s.flags.meeting){this.emit('notice','先到长桌确认诱片的用途');return;}
  if(id==='undercity-disarm'&&s.flags.trap_disabled){this.emit('notice','诱片已经安全拆除，无需再次冒险');return;}
  const record=s.dice.records[id];if(record?.committed){this.emit('notice',record.rolls[record.rolls.length-1].success?'这次行动已经达成，结果已记录。':'你已经接受这次失败；寻找其他线索或路线。');return;}
  s.dice.active={id,area:s.area,sourceId,context:record?.context??this.checkContext(id)};this.cancelInput();this.changed();this.emit('check_open',def.title,{id});
 }
 diceView():DiceView|null {const s=this.state,a=s.dice.active;if(!a)return null;if(a.id.startsWith('gear:'))return this.equipmentDice.view();const d=SKILL_CHECKS[a.id],r=s.dice.records[a.id],roll=r?.rolls[r.rolls.length-1]??null;return {id:d.id,title:d.title,prompt:d.prompt,skillLabel:ACTION_NAMES[d.skill],abilityLabel:'行动',dc:d.dc,mode:a.context.mode,modifiers:a.context.modifiers.map((m,i)=>({...m,label:i?'经验准备':'行动准备'})),help:a.context.helpLabel?{label:a.context.helpLabel,enabled:a.context.helpDie}:null,roll,attempt:r?.rolls.length??0,inspiration:s.dice.inspiration,canReroll:!!roll&&!roll.success&&s.dice.inspiration>0&&(r?.rolls.length??0)<5,canCancel:!roll,successText:d.successText,failureText:d.failureText,chance:checkChance(d.dc,a.context)};}
 prepareEquipmentDice():boolean {return !this.state.dice.active&&!this.state.dialogue&&this.equipmentAvailability().available&&this.equipmentDice.open();}
 openEquipmentDice(item:string):boolean {if(!this.state.inventory[item]||this.state.dice.active||this.state.dialogue||!this.equipmentAvailability().available)return false;this.equipmentDice.enqueue(item,this.state.provenance[item],true);return this.equipmentDice.open(item);}
 toggleCheckHelp():GameEvent[]{const a=this.state.dice.active;if(a&&a.context.helpLabel&&!this.state.dice.records[a.id]?.rolls.length){a.context.helpDie=!a.context.helpDie;this.changed();}return this.drain();}
 rollCheck(reroll=false,expectedAttempt=0):GameEvent[]{const s=this.state,a=s.dice.active;if(!a||s.status==='dead')return [];const def=SKILL_CHECKS[a.id],old=s.dice.records[a.id],count=old?.rolls.length??0;
  if(a.id.startsWith('gear:')){if(!reroll)this.equipmentDice.roll(expectedAttempt);return this.drain();}
  if(count!==expectedAttempt||old?.committed||(reroll?(!count||old!.rolls[count-1].success||s.dice.inspiration<1||count>=5):count>0))return [];
  if(reroll)s.dice.inspiration--;const record=old??{area:a.area,sourceId:a.sourceId,context:clone(a.context),rolls:[],committed:false};record.rolls.push(drawCheckRoll(s.seed,a.id,count+1,def.dc,record.context));s.dice.records[a.id]=record;this.changed();this.emit('check_roll',undefined,{id:a.id,attempt:count+1});return this.drain();
 }
 cancelCheck():GameEvent[]{const s=this.state,a=s.dice.active;if(a?.id.startsWith('gear:')){this.equipmentDice.finish(true);return this.drain();}if(a&&!s.dice.records[a.id]?.rolls.length){s.dice.active=null;this.changed();}return this.drain();}
 finishCheck():GameEvent[]{const s=this.state,a=s.dice.active;if(!a)return [];if(a.id.startsWith('gear:')){this.equipmentDice.finish();return this.drain();}const r=s.dice.records[a.id],roll=r?.rolls[r.rolls.length-1];if(!r||r.committed||!roll)return [];r.committed=true;s.flags[`check:${a.id}:${roll.success?'passed':'failed'}`]=true;
  if(roll.success){
   if(a.id==='mira-motive')s.flags.saw_copy=true;
   if(['mira-terms','grave-record'].includes(a.id))s.flags.independent_clue=true;
   if(a.id==='inn-lockbox'){this.gold('dice:inn-lockbox',12);s.player.iron=Math.min(9999,s.player.iron+2);}
   if(a.id==='quarry-runes')s.player.iron=Math.min(9999,s.player.iron+2);
   if(a.id==='undercity-disarm'){s.flags.trap_disabled=true;s.flags.trap_handled=true;s.player.focus=Math.min(s.player.maxFocus,s.player.focus+20);}
   if(['mira-terms','grave-record','quarry-runes','undercity-disarm'].includes(a.id))this.awardInspiration('check:'+a.id);
  }else if(a.id==='undercity-disarm')s.player.focus=Math.max(0,s.player.focus-20);
  s.dice.active=null;this.changed();this.emit('check_result',roll.success?SKILL_CHECKS[a.id].successText:SKILL_CHECKS[a.id].failureText,{id:a.id,success:roll.success});
  if(a.sourceId==='t1-mira'&&s.area==='S01-T1')this.offer();return this.drain();
 }
 private awardInspiration(source:string){const s=this.state;if(s.dice.earned.includes(source))return;s.dice.earned.push(source);s.receipts['inspiration:'+source]=true;const old=s.dice.inspiration;s.dice.inspiration=Math.min(4,old+1);this.changed();if(s.dice.inspiration>old)this.emit('inspiration','余烬 +1',{id:source});}
 private visible(a:Point,b:Point){return this.world.visible(a,b)&&Math.abs(this.world.height(a)-this.world.height(b))<1.2;}
 private move(p:Point,d:Point,r=.32){
  // Reuse SceneBuilder's substepped axis sliding for the giant's solid body.
  // This clips player travel; it never pushes or relocates the monster.
  if(p===this.state.player){const bodies=this.state.enemies.filter(e=>e.hp>0&&enemyProfile(e)?.solidBody);
   if(bodies.length){const q={...p},steps=Math.max(1,Math.ceil(Math.hypot(d.x,d.z)/.15));
    const blocked=(x:number,z:number)=>bodies.some(e=>{const next=Math.hypot(x-e.x,z-e.z),previous=Math.hypot(q.x-e.x,q.z-e.z);return next<r+enemyHurtRadius(e)&&next<previous-1e-8;});
    for(let i=0;i<steps;i++){const x=q.x+d.x/steps,z=q.z+d.z/steps;if(!blocked(x,q.z))q.x=x;if(!blocked(q.x,z))q.z=z;}d={x:q.x-p.x,z:q.z-p.z};
   }
  }
  const moved=this.world.move(p,d,r);if(!point(moved))return;const a=this.areaDef;p.x=a?clamp(moved.x,-a.width/2+r,a.width/2-r):moved.x;p.z=a?clamp(moved.z,-a.depth/2+r,a.depth/2-r):moved.z;
 }
 private safe(){return !this.state.enemies.some(e=>(!e.trainingDummy||e.trainingAttacks)&&e.hp>0&&dist(e,this.state.player)<3)&&!this.state.projectiles.some(p=>p.owner==='enemy'&&dist(p,this.state.player)<3)&&!this.state.fireZones.some(f=>dist(f,this.state.player)<f.radius+1)&&!this.enemyRules.dangerAt(this.state.player);}
 private checkpointNear(){const p=this.state.player,a=this.areaDef;return !!a&&((a.checkpoint&&dist(p,a.spawn)<3)||(this.state.checkpoint.area===a.id&&dist(p,this.state.checkpoint)<2)||a.objects.some(o=>o.action==='checkpoint'&&dist(p,o)<=1.35&&this.visible(p,o)));}
 private setCheckpoint(){this.state.checkpoint={area:this.state.area,x:this.state.player.x,z:this.state.player.z};this.state.flags[`checkpoint:${this.state.area}`]=true;}
 private threateningEnemy(e:EnemyState){
  const s=this.state;
  if(e.hp<=0||e.trainingDummy&&!e.trainingAttacks)return false;
  const profile=enemyProfile(e),aggro=(s.combat.buffs[`aggro:${e.id}`]??0)>s.time;
  let range=profile?.route==='profile'?(aggro?profile.movement.damagedAwarenessRange:profile.movement.awarenessRange):aggro?Math.max(24,profile?.movement.damagedAwarenessRange??24):e.kind==='archer'?ENEMY_ARCHER_START_RANGE:12;
  if(e.phase==='windup'||e.phase==='active')range=Math.max(range,profile?.route==='profile'?Math.max(0,...Object.values(profile.attacks).map(a=>a.maxRange)):e.kind==='archer'?ENEMY_ARCHER_SHOT_RANGE:range);
  // A distant stale phase or a passive enemy behind a wall does not lock the bag.
  return dist(e,s.player)<=range&&(this.visible(e,s.player)||e.phase==='approach');
 }
 private inCombat(){
  return !!this.state.combat.engagement||this.combatEffectsPending()||this.state.enemies.some(e=>this.threateningEnemy(e));
 }
 private combatEffectsPending(){
  const s=this.state,alive=s.enemies.some(e=>e.hp>0);
  return s.player.hurtTime>0||(s.combat.buffs.enemyBurnUntil??0)>s.time
   ||s.fireZones.some(f=>f.remaining>0&&dist(f,s.player)<f.radius+1&&this.visible(f,s.player))||this.enemyRules.dangerAt(s.player)
   ||s.projectiles.some(q=>q.remaining>0&&(q.owner==='player'?alive:dist(q,s.player)<3||this.visible(q,s.player)&&this.segmentHits(q,{x:q.x+Math.sin(q.angle)*q.remaining,z:q.z+Math.cos(q.angle)*q.remaining},s.player,.7)))
   ||alive&&s.combat.casts.some(c=>c.rank.authoredDamageHits>0)
   ||s.enemies.some(e=>e.hp>0&&(s.combat.statuses[e.id]?.burnUntil??0)>s.time);
 }
 private recordCombat(enemy?:EnemyState){
  const s=this.state;
  if(!s.combat.engagement||s.combat.engagement.area!==s.area)s.combat.engagement={area:s.area,enemyIds:[]};
  const engagement=s.combat.engagement;delete engagement.quietSince;
  if(enemy&&!engagement.enemyIds.includes(enemy.id))engagement.enemyIds.push(enemy.id);
 }
 private disengagementDelay(){
  const s=this.state,e=s.combat.engagement;
  return e&&e.area===s.area&&e.enemyIds.length>0&&e.enemyIds.every(id=>s.enemies.some(enemy=>enemy.id===id&&enemy.hp<=0))?DISENGAGEMENT_SECONDS.cleared:DISENGAGEMENT_SECONDS.retreat;
 }
 private updateCombatEngagement(){
  const s=this.state;let danger=this.combatEffectsPending();
  for(const enemy of s.enemies)if(this.threateningEnemy(enemy)){this.recordCombat(enemy);danger=true;}
  if(danger){this.recordCombat();return;}
  const e=s.combat.engagement;if(!e)return;
  if(e.quietSince===undefined){e.quietSince=s.time;this.emit('notice',gearText('combat.settling',{seconds:this.disengagementDelay()}));}
  if(s.time-e.quietSince+1e-8>=this.disengagementDelay()){delete s.combat.engagement;this.emit('notice',gearText('combat.ready'));}
 }
 equipmentAvailability():{available:boolean;reason:string}{
  if(this.state.status==='dead')return {available:false,reason:'倒下后无法更换装备'};
  if(this.state.dice.active)return {available:false,reason:'请先完成当前骰盘'};
  if(this.combatEffectsPending()||this.state.enemies.some(e=>this.threateningEnemy(e)))return {available:false,reason:gearText('combat.blocked')};
  const engagement=this.state.combat.engagement;
  if(engagement)return {available:false,reason:gearText('combat.wait',{seconds:Math.max(.1,Math.ceil((this.disengagementDelay()-(engagement.quietSince===undefined?0:this.state.time-engagement.quietSince))*10)/10).toFixed(1)})};
  if(this.state.action)return {available:false,reason:'当前动作结束后再更换'};
  return {available:true,reason:gearText('combat.ready')};
 }
 /** A paused bag must not wait forever for a harmless action's recovery timer. */
 prepareEquipmentChange():boolean {
  const s=this.state,noEnemies=!s.enemies.some(e=>e.hp>0);
  if(s.status==='dead'||s.dialogue||s.dice.active||this.inCombat())return false;
  const pending=!!s.action||noEnemies&&s.projectiles.some(q=>q.owner==='player');
  if(!pending)return false;
  this.cancelInput();s.action=null;this.meleeChain.reset();
  // In an empty safe scene, discard only the player's unfinished shots. Keep buffs, shields and hazards.
  if(noEnemies)s.projectiles=s.projectiles.filter(q=>q.owner!=='player');
  this.changed();return true;
 }
 equipmentChange(item:string,slot?:string){return equipmentChange(this.state,item,slot,this.equipmentAvailability());}
 preparationAvailability():{available:boolean;reason:string}{
  if(this.state.status==='dead')return {available:false,reason:'倒下后无法整备'};
  if(this.state.dice.active)return {available:false,reason:'请先完成当前骰盘'};
  if(!this.safe())return {available:false,reason:'附近仍有敌人或火焰'};
  if(this.inCombat())return {available:false,reason:'战斗尚未结束，请先脱战再整备'};
  if(!this.checkpointNear())return {available:false,reason:'请到安全检查点整备'};
  if(this.state.action)return {available:false,reason:'当前动作结束后再整备'};
  return {available:true,reason:'安全检查点 · 可以整备'};
 }
 forgingAvailability():{available:boolean;reason:string}{
  const s=this.state,access=this.equipmentAvailability();if(!access.available)return access;
  if(s.dialogue||s.action||s.combat.casts.length||s.projectiles.length)return {available:false,reason:'请先完成当前交谈或攻击动作'};
  const anchors:Point[]=[];if(this.merchant==='lorn'&&this.merchantAnchor)anchors.push(this.merchantAnchor);if(s.discoveredMerchants.includes('lorn'))anchors.push(...this.areaDef?.objects.filter(o=>o.action==='merchant'&&canonicalMerchant(o.merchant??o.actor??'')==='lorn')??[]);
  const atLorn=anchors.some(anchor=>dist(s.player,anchor)<=1.35&&this.visible(s.player,anchor));
  return this.checkpointNear()||atLorn?{available:true,reason:atLorn?'洛恩工坊 · 可以锻造与强化':'安全检查点 · 可以锻造与强化'}:{available:false,reason:'请前往安全检查点，或到洛恩工坊现场整备'};
 }
 equip(item:string,slot?:string):boolean{
  const id=canonicalItem(item),def=EQUIPMENT[id];if(!def||!this.state.provenance[id]||!this.equipmentAvailability().available||this.state.progression.level<(def.requiredLevel??1))return false;
  if(def.kind==='spell'){
   const i=slot==='spell1'?1:0;if(this.state.equipment.spells[1-i]===id)return false;this.state.equipment.spells[i]=id;
  }else{
   const change=this.equipmentChange(id,slot);if(!change.available&&change.block!=='equipped')return false;
   if((change.from==='ringLeft'||change.from==='ringRight')&&change.from!==change.slot)this.state.equipment[change.from]=change.replaced??null;
   this.state.equipment[change.slot]=id;if(def.twoHanded)this.state.equipment.offhand=null;
  }
  if(def.slot==='weapon')prepareCombatLoadout(this.state.combat,this.state.equipment.weapon,this.state.progression);
  this.recalculate();this.changed();this.emit('equip',`已装备${def.name}`,{id});return true;
 }
 private equipped(id:string){return Object.values(this.state.equipment).includes(id);}
 claimLifecycleReward(group:string,item:string){return this.state.status!=='dead'&&!this.state.dialogue&&!this.state.dice.active&&this.equipmentAvailability().available&&this.journey.claimLifecycle(group,item);}
 claimJourneyWeapon(chapter:number,route:string,item:string){return this.state.status!=='dead'&&!this.state.dialogue&&!this.state.dice.active&&this.equipmentAvailability().available&&this.journey.claim(chapter,route,item);}
 setCounts():Record<string,number>{const counts:Record<string,number>={};for(const [key,id] of Object.entries(this.state.equipment)){if(key==='spells'||typeof id!=='string')continue;const set=EQUIPMENT[id]?.set;if(set)counts[set]=(counts[set]??0)+1;}return counts;}
 itemView(id:string):ItemDef {
  const d=EQUIPMENT[id];if(!d)return d;const base=GROWING_EQUIPMENT[id]?{...d,maxHp:growingStats(id,this.state.progression.level).maxHp,description:growingDescription(d,this.state.progression.level)}:d,b=itemGearBonus(this.state,id),f=itemForgingView(this.state,id)!,extra=bonusText(b),improvement=f.affixes.map(forgingAffixText).join('；'),description=[base.description,`强化＋${f.rank} · 当前上限＋${f.cap} · 装备极限＋${f.maximum}`,`强化属性 ${f.affixes.length}／${f.capacity}${improvement?'：'+improvement:''}`,extra?'免费锻印：'+extra.replace(/\n/g,'；'):''].filter(Boolean).join('\n');
  return {...base,name:base.name+(f.rank?` ＋${f.rank}`:''),maxHp:(base.maxHp??0)+b.maxHp+f.bonus.maxHp,armor:(base.armor??0)+b.armor+f.bonus.armor,description};
 }
 interactionVisible(o:InteractionDef){
  if(o.action==='journey_task')return this.journey.visible(o.eventId??'');
  return !o.eventId||growingQuestVisible(o.eventId,this.state.flags);
 }
 canApproachInteraction(){const s=this.state;return s.status!=='dead'&&!s.dialogue&&!s.dice.active&&!s.action&&this.safe()&&!this.inCombat();}
 approachInteractionVisible(o:InteractionDef){
  if(!this.interactionVisible(o))return false;
  const s=this.state,a=o.action;
  if(a==='journey_task'){const task=this.journey.currentTask();return !!task&&task.id===o.eventId&&task.goal==='observe';}
  if(a==='campaign_event'){
   const d=CAMPAIGN_EVENTS[o.eventId??''];
   return !!d&&d.area===s.area&&!s.receipts[`campaign:${d.id}`]&&!d.requires?.some(f=>!s.flags[f])
    &&(!d.requiresAny?.length||d.requiresAny.some(f=>s.flags[f]))&&(!d.clearEncounter||this.campaign.battleReady()&&!s.enemies.some(e=>e.hp>0&&!e.respawnSeconds));
  }
  const completed:Record<string,string>={independent_clue:'independent_clue',letter:'read_letter',recover:'recovered',rescue_cart:'cart_rescued',release_workers:'workers_released',disable_trap:'trap_disabled',captain_gate:'gate_raised',gate:'gate_raised',finish:'chapter1_complete'};
  if(completed[a]&&s.flags[completed[a]])return false;
  if(a==='letter'&&!s.flags.recovered||['release_workers','disable_trap'].includes(a)&&!s.flags.meeting||['captain_gate','gate'].includes(a)&&!s.flags.captain_defeated||a==='finish'&&!this.canComplete())return false;
  if(['recover','rescue_cart'].includes(a)&&s.enemies.some(e=>e.hp>0&&!e.respawnSeconds))return false;
  return !!o.actor||['offer','merchant','meeting',...Object.keys(completed)].includes(a);
 }
 private recalculate(){syncRandomForging(this.state);if(!this.areaDef){this.enemyRules.reset();for(const enemy of [...this.state.enemies,...Object.values(this.state.encounters).flat()])EnemyCombat.restore(enemy);}let bonus=0;for(const [key,id]of Object.entries(this.state.equipment))if(key!=='spells'&&typeof id==='string')bonus+=this.itemView(id)?.maxHp??0;if((this.setCounts().oath??0)>=2)bonus+=8;this.state.player.maxHp=baseMaxHp(this.state.progression)+bonus;this.state.player.hp=Math.min(this.state.player.hp,this.state.player.maxHp);this.state.player.shield=Math.min(this.state.player.shield,this.state.player.maxHp*.35);synchronizeResource(this.state);}
 combatSkillView(ids?:readonly string[]){return this.combatRules.view(ids);}
 skillAutoAimTarget(id:string){return this.combatRules.autoAimTarget(id);}
 progressionView(){const p=progressionView(this.state.progression),gear=equippedGearBonus(this.state),attributes={...p.attributes};for(const key of ATTRIBUTES)attributes[key]=effectiveAttribute(this.state,key,gear);p.baseSkillPower*=equipmentPowerMultiplier(this.state.equipment.weapon,p.level)*(1+gear.power/100);return {...p,movementSpeed:this.movementSpeed,attributes,baseAttributes:p.attributes,equipmentAttributes:Object.fromEntries(ATTRIBUTES.map(key=>[key,attributes[key]-p.attributes[key]])) as Record<Attribute,number>,...playerCombatAttributes(this.state),criticalChance:combatCriticalChance(this.state,gear)*100,criticalDamage:combatCriticalMultiplier(this.state,gear)*100};}
 attributePlanToken(){const p=this.state.progression;return JSON.stringify([p.level,p.attributes,p.unspentPoints]);}
 applyAttributePlan(attributes:Record<Attribute,number>,token:string){const p=this.state.progression;if(token!==this.attributePlanToken()||!this.preparationAvailability().available||!attributes||Object.keys(attributes).length!==4||ATTRIBUTES.some(k=>!Number.isInteger(attributes[k])||attributes[k]<10||attributes[k]>80))return false;const spent=ATTRIBUTES.reduce((n,k)=>n+attributes[k]-10,0),remaining=3*(p.level-1)-spent;if(remaining<0)return false;p.attributes={...attributes};p.unspentPoints=remaining;this.recalculate();this.changed();return true;}
 skillPlanToken():string{return JSON.stringify([this.state.progression.learned,this.state.progression.skillPoints,this.state.progression.level,this.state.progression.secondChapter]);}
 applySkillPlan(learned:Record<string,number>,expectedToken?:string):boolean {
  const p=this.state.progression;if(p.version!==3||!this.preparationAvailability().available||expectedToken!==undefined&&expectedToken!==this.skillPlanToken())return false;
  const remaining=skillPlanRemaining(p,learned);if(remaining===null)return false;
  // Durable allocation changes cannot upgrade an already flying payload or keep
  // old high-rank buffs alive after a free refund. HP is never restored here.
  p.learned={...learned};p.skillPoints=remaining;this.resetCombatTransient();activateCombatLoadout(this.state.combat,p);this.changed();return true;
 }
 /** Clear a previous skill configuration before respec or local effect comparison. */
 resetCombatTransient():void{this.cancelInput();this.state.action=null;this.combatRules.resetTransient();this.state.projectiles=this.state.projectiles.filter(q=>q.owner!=='player');}
 learnSkill(id:string):boolean{const p=this.state.progression,rank=p.learned[id];if(!rank||rank>=5)return false;return this.applySkillPlan({...p.learned,[id]:rank+1});}
 assignActiveSkill(slot:number,id:string|null):boolean{
  if(!Number.isInteger(slot)||slot<0||slot>3||!this.preparationAvailability().available||id!==null&&(!PURE_SKILLS[id]||PURE_SKILLS[id].type!=='active'||!['COM',this.state.combat.family].includes(PURE_SKILLS[id].style)||!allocatedSkillRank(this.state.progression,id)))return false;
  const c=this.state.combat;prepareCombatLoadout(c,this.state.equipment.weapon,this.state.progression);const saved=assignedLoadout(c)!,other=id===null?-1:saved.activeSlots.indexOf(id),previous=saved.activeSlots[slot];
  if(other>=0&&other!==slot)saved.activeSlots[other]=previous;saved.activeSlots[slot]=id;activateCombatLoadout(c,this.state.progression);this.changed();return true;
 }
 combatLoadoutChange(family:CombatFamily,preferredWeapon?:string){
  const s=this.state,access=this.equipmentAvailability(),preset=Object.prototype.hasOwnProperty.call(COMBAT_LOADOUTS,family)?COMBAT_LOADOUTS[family]:undefined;
  const valid=(id:string)=>!!preset&&s.inventory[id]>0&&!!s.provenance[id]&&EQUIPMENT[id]?.kind===EQUIPMENT[preset.weapon].kind&&s.progression.level>=(EQUIPMENT[id].requiredLevel??1);
  const owned=Object.keys(s.inventory).filter(valid).sort((a,b)=>equipmentPowerMultiplier(b,s.progression.level)-equipmentPowerMultiplier(a,s.progression.level)||a.localeCompare(b));
  const weapon=preferredWeapon?(valid(preferredWeapon)?preferredWeapon:undefined):valid(s.equipment.weapon)?s.equipment.weapon:owned[0];
  const token=JSON.stringify([family,weapon,s.equipment,s.progression.level,s.combat.family,s.combat.loadouts]);
  return {family,weapon,token,available:!!preset&&!!weapon&&access.available,reason:!preset?'职业不可用':!weapon?'尚未持有该职业可用等级的武器':access.reason,
   offhand:weapon&&EQUIPMENT[weapon].twoHanded?s.equipment.offhand:undefined,
   activeSlots:s.combat.loadouts?.[family]?.activeSlots??preset?.activeSlots,ultimate:s.combat.loadouts?.[family]?.ultimate??preset?.ultimate};
 }
 applyCombatLoadout(family:CombatFamily,preferredWeapon?:string,expectedToken?:string):boolean{
  const change=this.combatLoadoutChange(family,preferredWeapon);if(!change.available||!change.weapon||expectedToken!==undefined&&expectedToken!==change.token)return false;
  if(this.state.equipment.weapon!==change.weapon&&!this.equip(change.weapon))return false;
  this.resetCombatTransient();prepareCombatLoadout(this.state.combat,this.state.equipment.weapon,this.state.progression,family);synchronizeResource(this.state);this.changed();return true;
 }
 assignPassive(slot:number,id:string|null):boolean{if(!Number.isInteger(slot)||slot<0||slot>1||(slot===0?this.state.progression.level<6&&!this.state.progression.secondChapter:!this.state.progression.secondChapter)||!this.preparationAvailability().available||id!==null&&(!PURE_SKILLS[id]||PURE_SKILLS[id].type!=='passive'||!allocatedSkillRank(this.state.progression,id))||id!==null&&this.state.combat.passiveSlots.some((n,i)=>n===id&&i!==slot))return false;this.state.combat.passiveSlots[slot]=id;this.changed();return true;}
 assignUltimate(id:string|null):boolean{if(!this.preparationAvailability().available||id!==null&&(!PURE_SKILLS[id]||PURE_SKILLS[id].type!=='ultimate'||!['COM',this.state.combat.family].includes(PURE_SKILLS[id].style)||!allocatedSkillRank(this.state.progression,id)))return false;prepareCombatLoadout(this.state.combat,this.state.equipment.weapon,this.state.progression);assignedLoadout(this.state.combat)!.ultimate=id;activateCombatLoadout(this.state.combat,this.state.progression);this.changed();return true;}
 castSkill(id:string,target?:Point,angle?:number):GameEvent[]{if(id!=='COM_01'&&!this.state.combat.activeSlots.includes(id)&&this.state.combat.ultimate!==id)return [];this.meleeChain.reset();this.combatRules.cast(id,target,angle);return this.drain();}
 allocateAttribute(key:Attribute,count=1):boolean{const p=this.state.progression;if(!ATTRIBUTES.includes(key)||!Number.isInteger(count)||count<1||count>p.unspentPoints||p.attributes[key]+count>80||!this.preparationAvailability().available)return false;p.attributes[key]+=count;p.unspentPoints-=count;this.recalculate();this.changed();return true;}
 respecAttributes():boolean{if(!this.preparationAvailability().available)return false;const p=this.state.progression;for(const key of ATTRIBUTES)p.attributes[key]=10;p.unspentPoints=3*(p.level-1);this.recalculate();this.changed();return true;}
 raiseToMaxLevel():boolean{const remaining=cumulativeXp(40)-this.state.progression.totalXp;return remaining>0&&this.gainExperience('local-playtest-level40',remaining);}
 awardExperience(source:string):boolean{const event=MAIN_XP_EVENTS.find(e=>e.id===source);if(!event)return false;return this.gainExperience(source,event.experience);}
 huntingExperience(){return huntingExperienceView(this.state.receipts,this.calendarNow(),this.state.progression.level);}
 private gainExperience(source:string,amount:number,repeat=false,idleHunting=false){const p=this.state.progression;if(ensureDailyExperience(this.state.receipts,this.calendarNow(),p.level))this.changed();if(!repeat&&p.xpReceipts[source]!==undefined)return false;if(repeat){const remaining=cumulativeXp(40)-p.totalXp;if(remaining<=0)return false;amount=takeCombatExperience(this.state.receipts,this.calendarNow(),p.level,amount,remaining,idleHunting);}if(amount<=0)return false;rememberCombatLoadout(this.state.combat,p);const levels=awardXp(p,source,amount,repeat);activateCombatLoadout(this.state.combat,p);this.state.player.hp+=5*levels;this.recalculate();if(p.secondChapter&&!p.ultimateGiftClaimed){p.ultimateGiftClaimed=true;this.state.combat.charge=0;this.emit('notice',COMBAT_RULES.ultimateRequiresCharge?'终极技能已开放':'终极技能已开放，使用当前职业资源');}this.changed();this.emit('experience',`经验 +${amount}`,{id:source,value:amount,level:p.level,levels});return true;}
 private syncProgression(){const f=this.state.flags;if(f.recovered&&f.read_letter)this.awardExperience('M1_XP_1');if(f.workers_departed||f.workers_returned)this.awardExperience('M2_XP_1');if(f.captain_defeated&&f.gate_raised)this.awardExperience('M2_XP_2');if(f.m7_prepared&&(f.west_tower_down||f.east_tower_down))this.awardExperience('M7_XP_2');if(f.m7_prepared&&f.west_tower_down&&f.east_tower_down){this.awardExperience('M7_XP_3');f.final_ready=true;}}
 /** Pointer cancellation/menu/background is distinct from a legal bow release. */
 cancelInput():void{this.meleeChain.reset();const a=this.state.action;if(a&&(a.kind==='bowAim'||a.kind==='bow'&&!a.emitted||a.kind.startsWith('spell:')&&!a.emitted||a.kind.startsWith('pure:')&&!a.emitted))this.state.action=null;this.previous={x:0,z:0};}
 /** All repeat combat shares the frozen daily allowance; idle has a sub-limit. */
 advance(dt:number,input:InputFrame,idleHunting=false):GameEvent[]{
  if(ensureDailyExperience(this.state.receipts,this.calendarNow(),this.state.progression.level))this.changed();
  if(!Number.isFinite(dt)||dt<=0||dt>5)return [];
  if(this.state.status==='dead'||this.state.dialogue||this.state.dice.active){this.previous={x:0,z:0};return [];}
  const clean:InputFrame={...input,x:Number.isFinite(input.x)?clamp(input.x,-1,1):0,z:Number.isFinite(input.z)?clamp(input.z,-1,1):0};
  let remaining=dt;let first=true;
  while(remaining>1e-8){const step=Math.min(.02,remaining);this.step(step,clean,first,idleHunting);remaining-=step;first=false;if(this.state.player.hp<=0)break;}
  this.updateCombatEngagement();
  const task=this.journey.currentTask();
  if(task&&task.goal!=='observe'&&this.state.player.hp>0&&this.safe()&&this.journey.complete(task.id))this.campaign.task(task.id);
  // The active encounter already is authoritative. Detach it at snapshot/travel, not every rendered frame.
  this.previous={...clean};this.state.encounters[this.state.area]=this.state.enemies;this.changed();return this.drain();
 }
 private step(dt:number,input:InputFrame,first:boolean,idleHunting:boolean){
  const s=this.state,p=s.player;s.time+=dt;p.hurtTime=Math.max(0,p.hurtTime-dt);p.focus=Math.min(p.maxFocus,p.focus+(s.combat.engagement?RESOURCE_RULES.combatRegen:RESOURCE_RULES.restRegen)*dt);
  for(const k of Object.keys(s.cooldowns))s.cooldowns[k]=Math.max(0,s.cooldowns[k]-dt);
  this.pruneSupplies();this.respawnHunts();this.combatRules.step(dt);this.enemyRules.tick(dt);
  const facingAction=s.action;
  if(facingAction&&facingAction.kind!=='bowAim')p.angle=facingAction.angle;
  else if(Number.isFinite(input.aim))p.angle=input.aim!;else if(Math.hypot(input.x,input.z)>.01)p.angle=Math.atan2(input.x,input.z);
  if(first)this.input(input);
  const a=s.action;
  const norm=Math.max(1,Math.hypot(input.x,input.z));let speed=this.movementSpeed;
  const sets=this.setCounts();let speedBonus=(sets.wind??0)>=2?.08:0;
  if(this.equipped('A14')&&p.movingTime>=1.5)s.combat.buffs.walkSpeedUntil=s.time+1;
  if(this.equipped('A14')&&(s.combat.buffs.walkSpeedUntil??0)>s.time)speedBonus+=.05;
  if((s.cooldowns.wind_speed??0)>0)speedBonus+=.08;
  speed*=(1+Math.min((s.combat.buffs.stormWardUntil??0)>s.time?.3:.2,speedBonus+this.combatRules.speedMultiplier()-1))*this.enemyRules.playerMoveMultiplier();
  const moving=Math.hypot(input.x,input.z)>.01;p.movingTime=moving?p.movingTime+dt:0;
  if(a)speed*=a.skillId==='BOW_07'&&a.emitted&&a.elapsed<(a.releaseAt??0)+.2?0:a.skillId==='WAR_02'&&a.emitted&&a.elapsed<(a.releaseAt??0)?0:a.skillId==='COM_02'&&this.equipped('DE03')?1:a.kind==='dash'?0:a.kind==='bowAim'?.6:a.kind==='sword'&&a.elapsed>=(a.releaseAt??.12)&&a.elapsed<(a.releaseAt??.12)+.10?.35:.65;
  const before={x:p.x,z:p.z};this.move(p,{x:input.x/norm*speed*dt,z:input.z/norm*speed*dt});s.movedDistance+=dist(before,p);this.combatRules.growingMove(dist(before,p),dt);
  if(a)this.actionStep(a,dt,input.attack===true,input.aim);
  this.collectNearbySupplies();
  for(const e of s.enemies){const reeling=this.hitResponse.step(e,dt);if(e.hp>0&&!reeling)this.enemyStep(e,dt);}
  this.projectilesStep(dt);this.environmentStep(dt);this.deaths(idleHunting);
 }
 private input(input:InputFrame){
  const s=this.state,a=s.action;
  if(input.dash&&!this.previous.dash){this.meleeChain.reset();if(a&&a.elapsed>=.3)s.action=null;if(!s.action){const angle=Math.hypot(input.x,input.z)>.01?Math.atan2(input.x,input.z):s.player.angle+Math.PI;this.combatRules.cast('COM_01',undefined,angle);}return;}
  if(a?.kind==='bowAim'){a.angle=s.player.angle;if(!input.attack){const held=a.elapsed;s.action={...a,kind:'bow',elapsed:0,duration:.3,charged:held>=.8,damage:held>=.8?30:18};this.captureRayFeedback(s.action,s.player,s.action.angle,BASIC_ATTACK.bow.rangeMetres,.45);}return;}
  if(a){if(a.kind==='sword'&&input.attack&&!this.previous.attack&&a.elapsed>=a.duration-MELEE_INPUT_BUFFER)this.meleeChain.buffer(s.time);else if(a.kind!=='sword')this.meleeChain.reset();return;}
  if(input.ultimate&&!this.previous.ultimate){this.meleeChain.reset();const id=s.combat.ultimate;if(id)this.combatRules.cast(id,input.target,input.aim);return;}
  const slot=input.combatSlot??(input.skill&&!this.previous.skill?0:input.spell!==undefined&&input.spell!==this.previous.spell?input.spell+1:undefined);
  if(slot!==undefined&&slot<4&&(input.combatSlot===undefined||input.combatSlot!==this.previous.combatSlot)){this.meleeChain.reset();const id=s.combat.activeSlots[slot];if(id)this.combatRules.cast(id,input.target,input.aim);return;}
  if(input.attack||EQUIPMENT[s.equipment.weapon].kind==='sword'&&this.meleeChain.queued(s.time)){const kind=EQUIPMENT[s.equipment.weapon].kind;this.start(kind==='bow'?'bowAim':kind==='staff'?'staff':'sword',kind==='bow'?9999:kind==='staff'?.7:.44,kind==='staff'?16:24);}
 } private start(kind:string,duration:number,damage:number){
  const s=this.state,combo=kind==='sword'?this.meleeChain.begin(s.time,s.equipment.weapon,s.area):undefined,a:ActionState={id:this.id('action'),accuracy:playerCombatAttributes(s).accuracy,kind,elapsed:0,duration:combo?.duration??duration,angle:s.player.angle,hits:[],emitted:false,damage,comboStage:combo?.stage,releaseAt:combo?.release};s.action=a;if(!combo)this.meleeChain.reset();
  if(kind==='sword'){
   const target=s.enemies.filter(e=>e.hp>0&&dist(s.player,e)<=BASIC_ATTACK.sword.rangeMetres+Math.max(.25,enemyHurtRadius(e)-.05)&&Math.abs(deltaAngle(aim(s.player,e),a.angle))<=BASIC_ATTACK.sword.angleDegrees*Math.PI/360&&this.visible(s.player,e)).sort((x,y)=>dist(s.player,x)-dist(s.player,y)||x.id.localeCompare(y.id))[0];
   this.rememberFeedback(a,target);
  }else if(kind==='staff')this.captureRayFeedback(a,s.player,a.angle,BASIC_ATTACK.staff.rangeMetres,.45);
  this.emit('action',undefined,{kind,id:a.id,comboStage:a.comboStage});
 }
 private rememberFeedback(intent:AttackFeedbackMetadata,target:EnemyState|undefined){
  if(!target)return;intent.feedbackTargetId=target.id;intent.feedbackTarget={x:target.x,z:target.z};intent.feedbackReported=false;
 }
 private captureRayFeedback(intent:AttackFeedbackMetadata,from:Point,angle:number,range:number,radius:number){
  const forward=(e:Point)=>(e.x-from.x)*Math.sin(angle)+(e.z-from.z)*Math.cos(angle);
  const end={x:from.x+Math.sin(angle)*range,z:from.z+Math.cos(angle)*range};
  const target=this.state.enemies.filter(e=>e.hp>0&&forward(e)>=0&&forward(e)<=range&&this.segmentHits(from,end,e,radius)&&this.visible(from,e)).sort((a,b)=>forward(a)-forward(b)||a.id.localeCompare(b.id))[0];
  this.rememberFeedback(intent,target);
 }
 private finishFeedback(intent:AttackFeedbackMetadata,hits:readonly string[],extra:Record<string,unknown>){
  if(intent.feedbackReported)return;intent.feedbackReported=true;
  const id=intent.feedbackTargetId;if(!id||!intent.feedbackTarget||hits.includes(id))return;
  const target=this.state.enemies.find(e=>e.id===id&&e.hp>0);if(!target)return;
  this.emit('miss','MISS',{id,at:{...intent.feedbackTarget},reason:intent.feedbackFailure??'avoided',...extra});
 }
 private startDash(input:InputFrame){if(this.state.cooldowns.dash>0)return;this.start('dash',.34,0);const angle=Math.hypot(input.x,input.z)>.01?Math.atan2(input.x,input.z):this.state.player.angle+Math.PI;this.state.action!.angle=angle;this.state.cooldowns.dash=1.1;this.state.cooldowns.dodgeDefense=2;}
 private actionStep(a:ActionState,dt:number,heldAttack=false,nextAim?:number){
  if(a.skillId){this.combatRules.action(a,dt);return;}const old=a.elapsed;a.elapsed+=dt;const s=this.state;
  if(a.kind==='dash'&&a.elapsed>.04&&old<.22){const active=Math.max(0,Math.min(a.elapsed,.22)-Math.max(old,.04));this.move(s.player,direction(a.angle,active/ .18*1.55));}
  if(a.kind==='sword'){if(a.elapsed>=(a.releaseAt??.12)&&old<(a.releaseAt??.12))a.accuracy=playerCombatAttributes(s).accuracy;const release=a.releaseAt??.12,end=release+meleeCombo(a.comboStage).active;if(a.elapsed>=release&&old<end)this.arc(a,24,BASIC_ATTACK.sword.rangeMetres,BASIC_ATTACK.sword.angleDegrees,false);if(old<end&&a.elapsed+1e-8>=end)this.finishFeedback(a,a.hits,{action:a.id});}
  if(a.kind==='push'&&a.elapsed>=.10&&old<.16)this.arc(a,8,1.35,90,true);
  const release=a.kind==='staff'?.20:a.kind==='bow'?Math.max(0,.12-(a.charged?.12:0)):.25;
  if(!a.emitted&&a.kind!=='bowAim'&&a.kind!=='sword'&&a.kind!=='push'&&a.kind!=='dash'&&a.elapsed+1e-8>=release){
   a.emitted=true;a.accuracy=playerCombatAttributes(s).accuracy;
   if(a.kind==='staff')this.projectile(a,'staff',16,BASIC_ATTACK.staff.rangeMetres,COMBAT_RULES.playerProjectileSpeeds.basicMagic);
   else if(a.kind==='bow')this.projectile(a,'arrow',a.damage,BASIC_ATTACK.bow.rangeMetres,COMBAT_RULES.playerProjectileSpeeds.basicArrow);
   else if(a.kind==='skill'){
    if(s.player.focus>=20){s.player.focus-=20;const kind=EQUIPMENT[s.equipment.weapon].kind;s.cooldowns.skill=kind==='sword'?6:kind==='bow'?8:7;
     if(kind==='sword'){this.move(s.player,direction(a.angle,.8));this.arc(a,24*1.2,BASIC_ATTACK.sword.rangeMetres,BASIC_ATTACK.sword.angleDegrees,false,true);}else this.projectile(a,kind==='bow'?'arrow':'staff',kind==='bow'?18:19.2,kind==='bow'?9:7,kind==='bow'?COMBAT_RULES.playerProjectileSpeeds.basicArrow:COMBAT_RULES.playerProjectileSpeeds.basicMagic,2);this.changed();}
   }else if(a.kind.startsWith('spell:')){
    const id=a.kind.slice(6);if((s.inventory[id]??0)>0){s.inventory[id]--;s.cooldowns[id]=id==='T01'?6:8;s.receipts[`use:${a.id}`]=id;this.projectile(a,'spell',a.damage,7,COMBAT_RULES.playerProjectileSpeeds.basicMagic,1,id);this.changed();}
   }
  }
  if(a.elapsed>=a.duration&&a.kind!=='bowAim'){if(a.kind==='sword')this.meleeChain.complete(a.comboStage??1,s.time);s.action=null;if(a.kind==='sword'&&(heldAttack||this.meleeChain.queued(s.time))){if(Number.isFinite(nextAim))s.player.angle=nextAim!;this.start('sword',.44,24);}}
 }
 private arc(a:ActionState,base:number,range:number,degrees:number,push:boolean,skill=false){
  const p=this.state.player;
  for(const e of this.state.enemies){if(e.hp<=0||a.hits.includes(e.id)||dist(p,e)>range+Math.max(.25,enemyHurtRadius(e)-.05)||Math.abs(deltaAngle(aim(p,e),a.angle))>degrees*Math.PI/360||!this.visible(p,e))continue;a.hits.push(e.id);
   this.damageEnemy(e,push?8:this.weaponDamage(base,e),a.id,push?'push':skill?'skill':'main',a.angle,{element:push?'push':skill?'skill':'basic',accuracy:a.accuracy});
   if(push){const boss=e.kind==='captain';let length=enemyProfile(e)?.movement.stationary?0:boss?(e.phase==='windup'?.12:e.phase==='stagger'?.65:.25):e.kind==='shield'?.5:1.35;this.move(e,direction(a.angle,length),.35);
    if(!boss&&this.state.time>=e.pushImmuneUntil){e.phase='stagger';e.phaseTime=e.kind==='shield'?.25:.45;e.pushImmuneUntil=this.state.time+1.2;}
    this.emit('push',boss?'稳住':undefined,{id:e.id,value:length});
   }
  }
  if(!push)for(const anchor of this.enemyRules.anchors())if(!a.hits.includes(anchor.id)&&dist(p,anchor)<=range+anchor.radius&&Math.abs(deltaAngle(aim(p,anchor),a.angle))<=degrees*Math.PI/360&&this.visible(p,anchor)){a.hits.push(anchor.id);this.enemyRules.damageAnchor(anchor.id,this.weaponDamage(base),a.id);}
 }
 private weaponDamage(base:number,_e?:EnemyState){const id=this.state.equipment.weapon;return base*(1+equippedGearBonus(this.state).power/100)*(GROWING_EQUIPMENT[id]||EQUIPMENT[id].power?equipmentPowerMultiplier(id,this.state.progression.level):1+(EQUIPMENT[id].level-1)*.08);}
 private projectile(a:ActionState,kind:ProjectileState['kind'],base:number,range:number,speed:number,pierce=1,weapon=this.state.equipment.weapon){
  const p=this.state.player,q:ProjectileState={id:this.id('projectile'),kind,x:p.x,z:p.z,accuracy:a.accuracy??playerCombatAttributes(this.state).accuracy,angle:a.angle,speed,remaining:range,damage:kind==='spell'?base:Math.round(this.weaponDamage(base)),owner:'player',weapon,hits:[],leg:'out',returning:false,charged:!!a.charged,pierce,age:0,feedbackActionId:a.id};
  if(a.feedbackTargetId&&a.feedbackTarget){q.feedbackTargetId=a.feedbackTargetId;q.feedbackTarget={...a.feedbackTarget};q.feedbackReported=false;}else this.captureRayFeedback(q,p,a.angle,range,.45);
  this.state.projectiles.push(q);this.emit('projectile',undefined,{id:q.id,kind});
 }
 private damageEnemy(e:EnemyState,damage:number,action:string,source:string,angle:number,feedback?:{element:string;critical?:boolean;accuracy?:number}):boolean{
  if(e.hp<=0)return false;
  if(source==='main')return this.combatRules.basicHit(e,damage,action,angle,feedback?.accuracy);if(source==='secondary'){const used=this.secondaryCounts.get(action)??0;if(used>=2)return false;this.secondaryCounts.set(action,used+1);if(this.secondaryCounts.size>1000)this.secondaryCounts.delete(this.secondaryCounts.keys().next().value!);}
  const s=this.state;let value=damage;const passive=EQUIPMENT[s.equipment.weapon]?.passive;if(['main','pure','spell','skill','basic'].includes(source)){if(passive==='steady-strike')value*=1.04;if(passive==='recovery-strike'&&(e.phase==='recovery'||e.phase==='stagger'))value*=1.08;}if(['pure','spell','relic','relicPhysical','burn'].includes(source)){s.combat.buffs[`aggro:${e.id}`]=s.time+20;}
  if(source==='main'){let bonus=0;if(this.equipped('A02')&&dist(s.player,e)>5)bonus+=.06;if((this.setCounts().wind??0)>=4&&e.markedUntil>s.time)bonus+=.10;value*=1+Math.min(.4,bonus);}
  const guard=enemyGuardMultiplier(e,angle,s.time);if(guard!==undefined){if(!['spell','environment','relic','burn'].includes(source)&&guard<1){value*=guard;this.emit('block','盾挡',{id:e.id,action,at:{x:e.x,z:e.z},angle});}}else if((e.kind==='shield'||e.kind==='captain')&&e.phase!=='stagger'&&e.phase!=='recovery'&&!['spell','environment','relic','burn'].includes(source)&&Math.abs(deltaAngle(angle+Math.PI,e.angle))<Math.PI/3){value*=.4;this.emit('block','盾挡',{id:e.id,action,at:{x:e.x,z:e.z},angle});}
  const opening=enemyProfile(e)?.recoveryDamageMultiplier??1;
  if(e.phase==='recovery'||e.phase==='stagger')value*=opening;
  const oldHp=e.hp;e.hp=Math.max(e.trainingDummy?1:0,e.hp-Math.round(value));if(oldHp>0&&e.hp<=0){this.combatRules.growingKill(action,source,e);if(['main','pure','spell','skill','basic'].includes(source)&&Object.values(s.equipment).some(id=>typeof id==='string'&&EQUIPMENT[id]?.passive==='hunt-renewal')&&!(s.cooldowns.lifecycleHeal>0)&&s.player.hp>0){const healed=(s.player.maxHp-s.player.hp)*.03;s.player.hp+=healed;s.cooldowns.lifecycleHeal=5;if(healed>0)this.emit('heal',gearText('loot.huntHeal',{amount:Math.round(healed)}),{value:healed});}}this.emit('hit',undefined,{id:e.id,value:Math.round(value),hpLost:oldHp-e.hp,element:feedback?.element??source,critical:feedback?.critical??false,lethal:e.hp<=0,skillId:s.combat.casts.find(c=>c.id===action)?.skillId,charged:s.projectiles.find(q=>q.id===action||q.feedbackActionId===action)?.charged??false,angle,source,action,comboStage:s.action?.id===action?s.action.comboStage:undefined,at:{x:e.x,z:e.z},opening:opening>1&&(e.phase==='recovery'||e.phase==='stagger')});
  if(e.hp<oldHp){this.recordCombat(e);s.combat.buffs[`aggro:${e.id}`]=s.time+20;this.enemyRules.alertPack(e);this.hitResponse.hit(e,action,source,angle);}
  if(source==='main'||source==='skill'){
   const weapon=s.equipment.weapon;
   if(this.equipped('A09')&&s.flags.counter_ready&&EQUIPMENT[weapon].kind==='sword'){s.flags.counter_ready=false;this.poise(e,4);}
   if(weapon==='W02'&&s.receipts[`count:${action}`]!==true){s.receipts[`count:${action}`]=true;s.effectCounters.oath=(s.effectCounters.oath??0)+1;if(s.effectCounters.oath%3===0&&!(s.cooldowns.oathFire>0)){s.cooldowns.oathFire=2;this.damageEnemy(e,4,action,'secondary',angle);}}
   if(weapon==='L01'){
    if(source==='skill'&&e.lightningUntil>s.time){e.lightningUntil=0;this.damageEnemy(e,18,action,'secondary',angle);const next=s.enemies.filter(n=>n.id!==e.id&&n.hp>0&&dist(n,e)<=3&&this.visible(e,n)).sort((a,b)=>dist(a,e)-dist(b,e)||a.id.localeCompare(b.id))[0];if(next)this.damageEnemy(next,9,action,'secondary',aim(e,next));}
    else if(source==='main')e.lightningUntil=s.time+6;
   }
   if(this.equipped('J03')&&e.markedUntil>s.time&&!(s.cooldowns.ringFocus>0)){s.player.focus=Math.min(s.player.maxFocus,s.player.focus+2);s.cooldowns.ringFocus=3;}
   if(source==='main'&&(this.setCounts().wind??0)>=4&&s.movedDistance>=2&&!(s.cooldowns.windMark>0)){e.markedUntil=Math.max(e.markedUntil,s.time+4);s.cooldowns.windMark=8;s.movedDistance=0;this.emit('mark',undefined,{id:e.id});}
   if(source==='main'&&(this.setCounts().oath??0)>=4&&(s.cooldowns.oathReady??0)>0&&!(s.cooldowns.oathProc>0)){s.cooldowns.oathReady=0;s.cooldowns.oathProc=10;s.player.shield=Math.min(30,s.player.shield+8);this.damageEnemy(e,8,action,'secondary',angle);}
  }
  this.changed();return true;
 }
 private missEnemy(e:EnemyState,action:string,chance:number,roll:number){this.recordCombat(e);this.state.combat.buffs[`aggro:${e.id}`]=this.state.time+20;this.enemyRules.alertPack(e);this.emit('miss','MISS',{id:e.id,action,reason:'accuracy',chance,roll,at:{x:e.x,z:e.z}});this.changed();}
 private poise(e:EnemyState,amount:number){const s=this.state,key=`poise:${s.area}:${e.id}`;if(e.hp<=0||s.time<e.staggerProtectedUntil||(s.cooldowns[key]??0)>0)return;s.effectCounters[key]=(s.effectCounters[key]??0)+amount;this.emit('poise','回敬：削韧 +4',{id:e.id,value:amount});if(s.effectCounters[key]>=100&&(e.kind!=='captain'||!['windup','active'].includes(e.phase))){s.effectCounters[key]=0;e.phase='stagger';e.phaseTime=.6;s.cooldowns[key]=8.6;this.emit('stagger','失衡',{id:e.id,value:.6});}}
 private hurt(damage:number,source:string,heavy=false,element:EnemyDamageElement=source==='fire'?'fire':'physical',ground=false,hitId?:string,accuracy?:number):boolean{
  const s=this.state,p=s.player;if(p.hp<=0||p.hurtTime>0)return false;
  this.recordCombat(s.enemies.find(e=>e.id===source));
  const a=s.action;
  if(source!=='fire'&&!ground&&a?.kind==='dash'&&a.elapsed>=.06&&a.elapsed<=.20){this.emit('evade','闪避');this.combatRules.growingEvade();if((this.setCounts().oath??0)>=4&&!(s.cooldowns.oathProc>0))s.cooldowns.oathReady=4;if(this.equipped('A09')&&!(s.cooldowns.counter>0)){s.flags.counter_ready=true;s.combat.buffs.counterReadyUntil=s.time+4;s.cooldowns.counter=6;this.emit('counter_ready','老兵的回敬：下一次近战削韧 +4');}return false;}
  const attacker=s.enemies.find(e=>e.id===source);
  if(!ground&&(attacker||accuracy!==undefined)){const key=hitId??`enemy:${s.area}:${source}:${attacker?.respawnCount??0}:${attacker?.attackCount??0}`,result=rollContactHit(s.seed,key,'player',accuracy??enemyCombatAttributes(attacker!).accuracy,playerCombatAttributes(s).evasion);if(!result.landed){this.emit('miss','闪避',{id:'player',action:key,source,reason:'evasion',chance:result.chance,roll:result.roll,at:{x:p.x,z:p.z}});this.changed();return false;}}
  let reduction=element==='physical'?this.combatRules.reduction(false):element==='fire'?this.combatRules.reduction(true):element==='lightning'&&this.equipped('J06')?-.05:0;if(!ground&&Object.values(s.equipment).some(id=>typeof id==='string'&&EQUIPMENT[id]?.passive==='oath-guard'))reduction+=.02;if(element==='physical'){for(const [slot,id]of Object.entries(s.equipment))if(slot!=='spells'&&typeof id==='string')reduction+=(this.itemView(id)?.armor??0)/100;if(this.equipped('A06')&&(s.cooldowns.dodgeDefense??0)>0&&!(s.cooldowns.leatherDefense>0)){reduction+=.1;s.cooldowns.leatherDefense=8;}}
  reduction+=this.combatRules.consumeDirectWard(ground);let amount=Math.max(1,Math.round(damage*(1-Math.min(.4,reduction))));const absorbed=Math.min(p.shield,amount);p.shield-=absorbed;this.combatRules.absorbed(absorbed);amount-=absorbed;const oldHp=p.hp;if(source==='fire'||!this.combatRules.preventGrowingDeath(amount))p.hp=Math.max(0,p.hp-amount);else amount=Math.max(0,oldHp-1);p.hurtTime=.45;this.meleeChain.reset();
  if(heavy&&a&&a.elapsed<(a.skillId?(a.releaseAt??0):a.kind.startsWith('spell:')?.25:a.kind==='sword'?(a.releaseAt??.12):.12)){if(a.kind.startsWith('spell:'))s.cooldowns.spellRetry=.4;s.action=null;}
  this.combatRules.afterHurt(element==='fire'&&amount>0);this.emit('hurt',undefined,{value:amount,hpLost:oldHp-p.hp,absorbed,source,element});this.changed();return true;
 }
 private enemyStep(e:EnemyState,dt:number){
  if(e.trainingDummy&&!e.trainingAttacks){e.phaseTime=Math.max(0,e.phaseTime-dt);if(e.phaseTime===0&&(e.phase==='stagger'||e.phase==='recovery'))e.phase='idle';return;}
  if(this.enemyRules.step(e,dt))return;
  const s=this.state,p=s.player,d=dist(e,p);e.phaseTime=Math.max(0,e.phaseTime-dt);
  if(e.kind==='captain'&&!e.halfAnnounced&&e.hp<=e.maxHp/2){e.halfAnnounced=true;this.emit('warning','锤柄收紧：横扫后将追加短击',{id:e.id});}
  if(e.phase==='stagger'){if(e.phaseTime<=0){e.phase='recovery';e.phaseTime=.5;e.staggerProtectedUntil=s.time+2;}return;}
  if(e.phase==='windup'){
   const lock=e.kind==='archer'?.3:e.attackKind==='charge'?.35:.25;if(e.phaseTime>lock)e.targetAngle=aim(e,p);e.angle=e.targetAngle;
   if(e.phaseTime<=0){e.phase='active';e.phaseTime=e.kind==='archer'?.02:e.attackKind==='charge'?(e.kind==='captain'?.55:.28):.16;e.struck=false;
    if(e.kind==='archer'&&d<=ENEMY_ARCHER_SHOT_RANGE&&this.visible(e,p))s.projectiles.push({id:this.id('crossbow'),kind:'crossbow',x:e.x,z:e.z,angle:e.targetAngle,speed:8,remaining:ENEMY_ARCHER_SHOT_RANGE,damage:this.enemyDamage(e,14),owner:'enemy',accuracy:enemyCombatAttributes(e).accuracy,weapon:'crossbow',hits:[],leg:'out',returning:false,charged:false,pierce:1,age:0});}
   return;
  }
  if(e.phase==='active'){
   if(e.attackKind==='charge'){
    const before={x:e.x,z:e.z};const move=direction(e.targetAngle,dt*(e.kind==='captain'?3.8/.55:1.2/.28));this.move(e,move,.4);
    if(e.kind==='captain'&&dist(before,e)<Math.hypot(move.x,move.z)*.5){e.phase='stagger';e.phaseTime=s.time>=e.staggerProtectedUntil?1.5:.35;this.emit('stagger','撞击石墩',{id:e.id});return;}
   }
   const range=e.attackKind==='charge'?1:e.kind==='captain'?(e.attackKind==='short'?1.5:2.1):1.15;
   const width=e.kind==='captain'?150:80;
   if(!e.struck&&d<=range+.25&&Math.abs(deltaAngle(aim(e,p),e.targetAngle))<width*Math.PI/360&&this.visible(e,p)){e.struck=true;const landed=this.hurt(this.enemyDamage(e,e.kind==='captain'?(e.attackKind==='charge'?24:e.attackKind==='short'?14:22):e.kind==='shield'?16:12),e.id,e.kind!=='raider');}
   if(e.phaseTime<=0){if(e.kind==='captain'&&e.halfAnnounced&&e.attackKind==='swing'){e.attackKind='short';e.phase='windup';e.phaseTime=.6;e.targetAngle=aim(e,p);this.emit('telegraph','短击',{id:e.id,duration:.6});}else{e.phase='recovery';e.phaseTime=e.kind==='archer'?1.8:e.kind==='captain'?(e.attackKind==='charge'&&enemyProfile(e)?.route==='legacy'?Math.max(1.5,Object.values(enemyProfile(e)!.attacks).find(a=>a.legacyKind==='charge')?.recovery??1.5):1.1):e.kind==='shield'?1.85:1.25;}}
   return;
  }
  if(e.phase==='recovery'){if(e.phaseTime<=0){e.phase='idle';e.phaseTime=.5;}return;}
  if(d>((s.combat.buffs[`aggro:${e.id}`]??0)>s.time?Math.max(24,enemyProfile(e)?.movement.damagedAwarenessRange??24):e.kind==='archer'?ENEMY_ARCHER_START_RANGE:12)){if(e.phase!=='idle'){e.phase='idle';e.phaseTime=.35;}return;}
  if(!this.visible(e,p)){
   const pathWorld=this.world as WorldQuery & {path?:(from:Point,to:Point)=>Point[]};
   if(pathWorld.path){let route=this.navigation.get(e.id);if(!route||route.until<s.time){route={points:pathWorld.path(e,p),until:s.time+.6};this.navigation.set(e.id,route);}while(route.points.length&&dist(e,route.points[0])<.4)route.points.shift();if(route.points.length){const target=route.points[0];e.angle=aim(e,target);e.phase='approach';this.move(e,direction(e.angle,Math.min(dist(e,target),dt*1.7*this.combatRules.enemySpeed(e))),.35);return;}}
   e.phase='idle';e.phaseTime=.35;return;
  }
  e.angle=aim(e,p);
  const range=e.kind==='archer'?ENEMY_ARCHER_START_RANGE:e.kind==='captain'?2.8:e.kind==='shield'?1.8:1.2;
  if(d>range){e.phase='approach';this.move(e,direction(e.angle,dt*(e.kind==='captain'?1.5:1.7)*this.combatRules.enemySpeed(e)),.35);return;}
  if(e.kind==='archer'&&d<2){this.move(e,direction(e.angle,-dt*1.5*this.combatRules.enemySpeed(e)),.35);}
  let slots=0,groupAttacks=0;const group=combatGroup(e);for(const other of s.enemies)if(other.hp>0&&(other.phase==='windup'||other.phase==='active')){slots+=enemyProfile(other)?.attackSlotCost??(other.kind==='captain'?2:1);if(group&&combatGroup(other)===group)groupAttacks++;}
  if(e.phaseTime<=0&&slots+(e.kind==='captain'?2:1)<=3&&(!group||groupAttacks<2)){e.attackKind=e.kind==='archer'?'shot':e.kind==='shield'?'charge':e.kind==='captain'&&e.attackCount%2===1?'charge':'swing';e.attackCount++;e.phase='windup';e.phaseTime=e.kind==='archer'?1.1:e.kind==='captain'?(e.attackKind==='charge'?1:.8):e.kind==='shield'?.75:.65;e.targetAngle=e.angle;this.emit('telegraph',e.attackKind==='charge'?'盾冲':e.attackKind==='shot'?'弩箭':'横扫',{id:e.id,duration:e.phaseTime,angle:e.targetAngle});}
 }
 private segmentHits(a:Point,b:Point,target:Point,radius:number){const dx=b.x-a.x,dz=b.z-a.z,length=dx*dx+dz*dz;const t=length?clamp(((target.x-a.x)*dx+(target.z-a.z)*dz)/length,0,1):0;return Math.hypot(a.x+dx*t-target.x,a.z+dz*t-target.z)<=radius+Math.max(0,enemyHurtRadius(target)-.3);}
 private projectilesStep(dt:number){
  const s=this.state;
  for(const q of [...s.projectiles]){
   if(this.combatRules.projectileStep(q,dt))continue;
   q.age+=dt;
   if(q.leg==='back')q.angle=aim(q,s.player);
   const before={x:q.x,z:q.z},move=direction(q.angle,q.speed*dt),next={x:q.x+move.x,z:q.z+move.z};q.remaining-=q.speed*dt;
   if(!this.visible(before,next)){q.remaining=0;q.returning=false;q.feedbackFailure='blocked';continue;}
   q.x=next.x;q.z=next.z;
   if(q.owner==='player'){
    const targets=s.enemies.filter(e=>e.hp>0&&!q.hits.includes(e.id)&&this.segmentHits(before,q,e,.45)&&this.visible(before,e)).sort((a,b)=>dist(before,a)-dist(before,b)||a.id.localeCompare(b.id));
    const anchor=this.enemyRules.anchors().filter(h=>this.segmentHits(before,q,h,h.radius+.1)&&this.visible(before,h)).sort((a,b)=>dist(before,a)-dist(before,b)||a.id.localeCompare(b.id))[0];if(anchor&&(!targets.length||dist(before,anchor)<dist(before,targets[0]))){this.enemyRules.damageAnchor(anchor.id,q.damage,q.id);q.remaining=0;continue;}
    for(const e of targets){q.hits.push(e.id);const spell=q.kind==='spell',landed=this.damageEnemy(e,q.damage,q.id,spell?'spell':q.pierce>1?'skill':'main',q.angle,{element:spell?'spell':'basic',accuracy:q.accuracy});
     if(landed&&q.weapon==='T02')e.markedUntil=s.time+8;
     if(landed&&q.weapon==='T03'&&e.markedUntil>s.time){this.damageEnemy(e,8,q.id,'secondary',q.angle);s.player.hp=Math.min(s.player.maxHp,s.player.hp+4);}
     if(landed&&q.weapon==='W08'&&q.charged&&!(s.cooldowns.windSpeedLock>0)){s.cooldowns.wind_speed=2;s.cooldowns.windSpeedLock=4;}
     if(q.hits.length>=q.pierce){if(q.returning&&q.leg==='out'){q.leg='back';q.hits=[];q.remaining=12;}else q.remaining=0;break;}q.damage=Math.round(q.damage*.5);
    }
   }else if(!q.hits.includes('player')&&this.segmentHits(before,q,s.player,q.enemyRadius??.4)&&this.visible(before,s.player)){q.hits.push('player');if(q.enemyId)this.enemyRules.projectileHit(q);else this.hurt(q.damage,q.id,false,'physical',false,q.id,q.accuracy??100);q.remaining=0;}
   if(q.returning&&q.leg==='out'&&q.remaining<=0){q.leg='back';q.hits=[];q.remaining=12;}
   if(q.leg==='back'&&dist(q,s.player)<.4)q.remaining=0;
  }
  for(const q of s.projectiles)if(q.owner==='player'&&(q.remaining<=0||q.age>=10)){
   const cast=q.castId?s.combat.casts.find(c=>c.id===q.castId):undefined;
   const targetWasHit=q.feedbackTargetId&&cast?.hits.includes(`${q.segment??0}:${q.feedbackTargetId}`);
   const hits=targetWasHit?[...q.hits,q.feedbackTargetId!]:q.hits;
   if(!q.feedbackFailure)q.feedbackFailure='expired';
   this.finishFeedback(q,hits,{action:q.feedbackActionId??q.castId??q.id,castId:q.castId,projectileId:q.id,skillId:q.skillId,segment:q.segment});
  }
  s.projectiles=s.projectiles.filter(q=>q.remaining>0&&q.age<10);
 }
 private ignite(b:BarrelState,fuse:number){if(b.exploded||b.fuse>=0)return;b.fuse=fuse;this.emit('fuse','油桶引信',{id:b.id,duration:fuse});}
 private fire(at:Point){this.state.fireZones.push({id:this.id('fire'),x:at.x,z:at.z,radius:1.1,remaining:4,tick:.25});}
 private explosion(at:Point,radius:number,enemy:number,player:number,id:string){for(const e of this.state.enemies)if(e.hp>0&&dist(at,e)<=radius&&this.visible(at,e)){let value=enemy;if(player>0){const group=`${Math.floor(this.state.time*10)}:${e.id}`,used=this.explosionDamage.get(group)??0;value=Math.min(enemy,96-used);this.explosionDamage.set(group,used+value);}if(value>0)this.damageEnemy(e,value,id,'environment',aim(at,e));}if(this.explosionDamage.size>1000)this.explosionDamage.clear();if(player>0&&dist(at,this.state.player)<=radius&&this.visible(at,this.state.player))this.hurt(player,'fire');for(const b of this.state.barrels)if(!b.exploded&&dist(at,b)<=radius&&this.visible(at,b))this.ignite(b,.35);this.emit('explosion',undefined,{at,id,radius});}
 private environmentStep(dt:number){
  const s=this.state;for(const b of s.barrels)if(!b.exploded&&b.fuse>=0){b.fuse-=dt;if(b.fuse<=0){b.exploded=true;s.flags[`${b.id}:exploded`]=true;this.explosion(b,1.7,48,18,b.id);this.fire(b);this.changed();}}
  for(const f of s.fireZones){f.remaining-=dt;f.tick=Math.max(0,f.tick-dt);}
  const contact=(target:Point,id:string,damage:()=>void)=>{const key=`fireContact:${s.area}:${id}`;if(!s.fireZones.some(f=>f.remaining>0&&dist(f,target)<=f.radius&&this.visible(f,target))){delete s.effectCounters[key];return;}const next=s.effectCounters[key];if(next===undefined)s.effectCounters[key]=s.time+.25;else if(s.time+1e-8>=next){damage();s.effectCounters[key]=s.time+.5;}};
  for(const e of s.enemies)if(e.hp>0)contact(e,e.id,()=>this.damageEnemy(e,6,this.id('fireTick'),'environment',0));
  contact(s.player,'player',()=>this.hurt(3,'fire',false,'fire',true));
  s.fireZones=s.fireZones.filter(f=>f.remaining>0);
 }
 private syncHuntingPacks(){
  const s=this.state,existing=new Map(s.enemies.map(e=>[e.id,e])),layoutKey=`hunting-layout:${HUNT_LAYOUT_VERSION}:${s.area}`,layoutChanged=!s.receipts[layoutKey];
  for(const slot of HUNT_ENCOUNTERS[s.area]??[]){
   const enemy=existing.get(slot.id);
   if(!enemy){
    const added=this.spawn(slot);
    // A save resumed inside the new formation must never materialize enemies
    // beside the player. The ordinary distance-gated respawn activates them later.
    if(dist(s.player,slot)<20){added.hp=0;added.phase='dead';added.respawnAt=s.time;}
    s.enemies.push(added);continue;
   }
   // Move only unseen, idle pre-layout enemies. Never heal or reset deaths,
   // timers, life counters or any fixed story enemy/reward from the old save.
   if(layoutChanged&&enemy.hp>0&&enemy.phase==='idle'&&dist(s.player,enemy)>=20&&dist(s.player,slot)>=20){
    enemy.x=slot.x;enemy.z=slot.z;enemy.combat=undefined;
   }
   const compositionChanged=enemy.templateId!==slot.templateId||enemy.kind!==slot.kind;
   if(!enemy.packId||compositionChanged){
    enemy.maxHp=this.spawn(slot).maxHp;enemy.hp=Math.min(enemy.hp,enemy.maxHp);
    if(compositionChanged){enemy.kind=slot.kind;enemy.templateId=slot.templateId;enemy.contentId=slot.contentId;enemy.combat=undefined;if(enemy.hp>0){enemy.phase='recovery';enemy.phaseTime=.5;}}
   }
   enemy.packId=slot.packId;enemy.respawnSeconds=slot.respawnSeconds;
  }
  if(HUNT_ENCOUNTERS[s.area])s.receipts[layoutKey]=true;
 }
 private respawnHunts(){
  if(!this.areaDef||this.state.status==='dead')return;
  const s=this.state,slots=HUNT_ENCOUNTERS[s.area]??[];
  for(let i=0;i<s.enemies.length;i++){
   const enemy=s.enemies[i];if(enemy.hp>0||!enemy.respawnSeconds||enemy.respawnAt===undefined||s.time<enemy.respawnAt)continue;
   const slot=slots.find(e=>e.id===enemy.id);if(!slot||dist(s.player,slot)<20||s.fireZones.some(f=>dist(f,slot)<f.radius+2)||s.enemies.some(e=>e.hp>0&&dist(e,slot)<1.3))continue;
   s.enemies[i]={...this.spawn(slot),respawnCount:(enemy.respawnCount??0)+1};
   this.navigation.delete(enemy.id);s.enemyHazards=s.enemyHazards?.filter(h=>h.ownerId!==enemy.id);
   this.changed();this.emit('enemy_respawn',undefined,{id:enemy.id,at:{x:slot.x,z:slot.z}});
  }
 }
 private spawnCampaignWave(enemies:EnemySpawn[]):EnemyState[]{
  const area=this.areaDef,p=this.state.player;if(!area||!enemies.length)return [];
  // Fit a whole squad before committing. Blocked sites retry without spawning
  // inside the player, changing layers or scattering a pack across the map.
  const ordered=[...enemies].sort((a,b)=>Number(a.kind==='archer')-Number(b.kind==='archer'));
  for(const radius of [8.5,10,12])for(let i=0;i<24;i++){
   const angle=p.angle+i*Math.PI/12,forward=direction(angle,1),center={x:p.x+forward.x*radius,z:p.z+forward.z*radius};
   const points=ordered.map((_,j)=>{const f=CAMPAIGN_FORMATION[j];return {x:center.x+forward.z*f.x+forward.x*f.z,z:center.z-forward.x*f.x+forward.z*f.z};});
   const valid=points.every(q=>(!this.world.inView||this.world.inView(q))&&dist(p,q)>=7&&Math.abs(q.x)<area.width/2-3&&Math.abs(q.z)<area.depth/2-3&&Math.abs(this.world.height(p)-this.world.height(q))<.6&&!area.obstacles.some(o=>Math.abs(q.x-o.x)<o.width/2+1&&Math.abs(q.z-o.z)<o.depth/2+1)&&!area.buildings.some(o=>Math.abs(q.x-o.x)<o.width/2+1&&Math.abs(q.z-o.z)<o.depth/2+1)&&!area.exits.some(e=>dist(e,q)<8)&&!area.objects.some(o=>(o.actor||o.action==='checkpoint')&&dist(o,q)<6)&&!this.state.enemies.some(e=>e.hp>0&&dist(e,q)<1.5)&&!this.state.fireZones.some(f=>dist(f,q)<f.radius+1)&&this.visible(p,q)&&(!this.world.path||this.world.path(p,q).length>0));
   if(valid)return ordered.map((e,j)=>this.spawn({...e,...points[j]}));
  }
  return [];
 }
 private deaths(idleHunting:boolean){
  const s=this.state;
  for(const e of s.enemies)if(e.hp<=0&&e.phase!=='dead'){e.phase='dead';e.hp=0;e.diedAt=s.time;
   if(e.trainingEnemy){this.changed();this.emit('defeat',undefined,{id:e.id});continue;}
   if(e.respawnSeconds){
    e.respawnAt=s.time+e.respawnSeconds;
    if(this.lootRules.hunt(e)){this.lootRules.supplies(e);this.gainExperience(`hunt:${s.area}:${e.id}`,huntingKillExperience(e.level??1,s.progression.level,e.templateId?.includes('ALPHA')),true,idleHunting);this.journey.hunt();this.growingLoot.hunt();}
    this.changed();this.emit('defeat',undefined,{id:e.id});continue;
   }
   const growingLife=this.bossLoot.defeat(e);
   if(e.bossId&&(e.respawnCount??0)>0){if(growingLife){this.lootRules.supplies(e);this.gainExperience(`growing-rematch:${e.bossId}`,3*huntingKillExperience(e.level??1,s.progression.level),true,idleHunting);}this.emit('defeat',undefined,{id:e.id});continue;}
   this.once(`kill:${s.area}:${e.id}`,()=>{this.lootRules.enemy(e);this.lootRules.supplies(e);const level=e.level??1,template=CAMPAIGN_ENEMY_TEMPLATES[e.bossId??e.templateId??''];if(!campaignFighter(e)?.deferExperience)this.gainExperience(`enemy:${s.area}:${e.id}`,template?.firstClearExperience??(20+8*(level-1))*(e.bossId?(template?.mandatory?8:3):1));if(e.bossId)s.flags[`boss_defeated:${e.bossId}`]=true;if(e.bossId==='BOSS_R1'||!e.bossId&&e.kind==='captain'){s.flags.captain_defeated=true;this.awardInspiration('captain');this.emit('captain_defeated','灰披队长卸下盾牌；横杆已可抬起',{id:e.id});}else if(e.id.includes('warden'))this.rollLegend(`pass:${s.area}:${e.id}`,.25,e);this.emit('defeat',undefined,{id:e.id});});}
  for(const e of s.enemies)if(e.bossId&&e.hp<=0&&s.receipts[`kill:${s.area}:${e.id}`])this.journey.defeated(e);
  if(s.player.hp>0)this.campaign.tick();
  this.lootRules.encounter(s.enemies.slice().reverse().find(e=>e.diedAt===s.time));if(s.player.hp<=0&&s.status!=='dead'){s.status='dead';s.dialogue=null;s.action=null;this.changed();this.emit('death','返回最近检查点；已击败敌人与已消耗物品保留');}
 }
 interact(object:InteractionDef):GameEvent[]{
  const s=this.state,p=s.player;if(s.status==='dead'||s.dialogue||s.dice.active)return [];
  if(!point(object)||dist(p,object)>Math.min(1.35,object.radius??1.35)||!this.visible(p,object)){this.emit('notice','靠近并绕过阻挡后交互');return this.drain();}
  const def=this.areaDef?.objects.find(o=>o.id===object.id);if(this.areaDef?.objects.length&&(!def||def.action!==object.action))return [];
  if(!this.interactionVisible(object))return [];
  const a=object.action;
  if(['offer','merchant','meeting','finish','checkpoint','recover','release_workers','disable_trap','cache'].includes(a)&&!this.safe()){this.emit('notice','附近仍有敌人或火焰');return this.drain();}
  if(a==='journey_board'){this.emit('journey_open');}
  else if(a==='hunting_guide'){this.emit('hunting_open');}
  else if(a==='journey_task'){const task=this.journey.currentTask();if(!this.safe())this.emit('notice','先离开敌人的攻击范围');else if(this.journey.complete(object.eventId??''))this.campaign.task(object.eventId??'');else this.emit('notice',task?.goal==='hunt'?`本地游荡怪 ${this.journey.progress(task)} / ${task.kills}，达成后自动结算`:'先完成前一任务；本地固定守军与增援结束后自动结算');}
  else if(a==='growing_scene'){if(!this.safe()){this.emit('notice','先离开敌人的攻击范围再调查');return this.drain();}this.growingLoot.scene(object.eventId??'');}
  else if(a==='growing_rematch'){this.growingRematch(object.eventId??'');}
  else if(a==='campaign_event'&&object.eventId){this.beginCampaignEvent(object.eventId);}
  else if(a==='skill_archive'){this.gainExperience(`archive:${s.area}:${object.id}`,s.area.startsWith('U2')?900:s.area.startsWith('H')?450:220);this.emit('inspect','永久技能档案已记录，按角色等级开放技能');}
  else if(a==='dice_check'&&object.check){this.beginCheck(object.check,object.id);}
  else if(a==='offer'){s.flags.offer_seen=true;this.offer();}
  else if(a==='independent_clue'){s.flags.independent_clue=true;this.emit('notice',object.description||'信使的记录指向地下。无需接约也可追查。');this.changed();}
  else if(a==='recover'||a==='rescue_cart'){
   if(s.enemies.some(e=>e.hp>0&&!e.respawnSeconds)){this.emit('notice','先解除圣匣车旁的全部守军');return this.drain();}
   if(a==='rescue_cart'){s.flags.cart_rescued=true;this.gold('design_reward_coin_ch01_obj02',20);}
   else{this.once('relic_recovered',()=>{s.flags.recovered=true;s.flags.cart_rescued=true;this.gold('design_reward_coin_ch01_obj02',20);this.emit('quest','遗物匣中有完整星片与原信。请亲自读信。');});}
   if(!s.discoveredMerchants.includes('nightqi'))s.flags.nightqi_available=true;
  }else if(a==='letter'){
   if(s.flags.recovered)this.dialogue('letter','拉斐尔',s.flags.saw_copy?'求援段和日期与抄件一致。她隐去的是落款：伊芙琳·灰。':s.flags.offer_seen?'原信日期就在近日。弥菈接约前就知道有人求援。落款：伊芙琳·灰。':'原信写于近日，落款：伊芙琳·灰。碑上宣告的死亡与纸上的求援日期相互矛盾。',[['read_letter','读完原信并记录落款']]);else this.emit('notice','先找回装有原信的遗物匣');
  }else if(a==='captain_gate'||a==='gate'){
   if(!s.flags.captain_defeated)this.emit('notice','队长仍在守着横杆');
   else this.once('obj_ch01_04',()=>{s.flags.gate_raised=true;this.grant('W02',1,'reward_ch01_gate_sword');this.grant('T03',3,'gate_spell_pack');this.gold('design_reward_coin_ch01_obj04',20);this.emit('quest','横杆已抬起，获得未熄之誓。');});
  }else if(a==='meeting'){
   this.dialogue('meeting','伊芙琳',s.flags.saw_copy?'“你这次带了几个回来的人？” 你知道有人求援；弥菈隐去的是她的姓名。十八年的等待留在桌边。':s.flags.offer_seen?'“你这次带了几个回来的人？” 弥菈把这趟叫作寻宝。现在她承认：接约前已读过求援信。':'阵亡者正在吃晚饭。伊芙琳看向身旁的弥菈：“你这次带了几个回来的人？” 你从独立线索而来，先听他们说明十八年前的约定。',[['cooperate','我会帮开门。之后重新谈约定；共同署名。'],['star_copy','我继续找遗库；保留星片副本与独立行动。'],['ask_truth','弥菈，把你还没告诉我的说完。']]);
  }else if(a==='release_workers'){
   if(!s.flags.meeting)this.emit('notice','先到长桌与伊芙琳见面');else if(!s.flags.trap_disabled&&s.enemies.some(e=>e.hp>0))this.emit('notice','先处理监区守卫，或从检修侧廊拆除诱片');else this.once('workers_released',()=>{s.flags.workers_released=true;s.flags.trap_handled=true;this.awardInspiration('release-workers');this.emit('quest','工匠已从扣押间获释。救援不要求和解。');});
  }else if(a==='disable_trap'){
   if(!s.flags.meeting)this.emit('notice','先到长桌确认门上的诱片');else this.once('trap_disabled',()=>{s.flags.trap_disabled=true;s.flags.trap_handled=true;this.emit('quest','诱片拆除，安全出口已确认。');});
  }else if(a==='finish'){
   if(this.canComplete())this.once('chapter_complete',()=>{s.flags.chapter1_complete=true;this.gold('design_reward_coin_ch01_obj05',20);this.emit('quest','被截获的星片 · 首章完成。高地、河湾与黑冠城域已可继续探索。');});else this.emit('objective',this.questObjective());
  }else if(a==='checkpoint'){this.setCheckpoint();this.rest();}
  else if(a==='cache')this.cache(object);
  else if(a==='merchant'){
   const id=canonicalMerchant(object.merchant??object.actor??'');if(MERCHANTS[id]){if(id==='mira'&&!s.flags.accepted){this.emit('notice','弥菈的补给只向接约者开放');}else{if(!s.discoveredMerchants.includes(id))s.discoveredMerchants.push(id);this.merchant=id;this.merchantAnchor={x:object.x,z:object.z};this.emit('shop',MERCHANTS[id].name,{id});this.changed();}}
  }else if(a==='secret_pass'){s.flags[`evidence:${object.id}`]=true;this.emit('inspect',object.description,{id:object.id});this.changed();}
  else if(a==='barrel'){this.emit('inspect','封存的军需桶，不参与战斗爆炸');}
  else {if(object.evidence)s.flags[object.evidence]=true;this.emit('inspect',object.description,{id:object.id});this.changed();}
  this.syncProgression();return this.drain();
 }
 private growingRematch(id:string){
  const s=this.state,index=s.enemies.findIndex(e=>e.id===id),enemy=s.enemies[index];
  if(!enemy?.bossId||enemy.hp>0||!s.flags[`boss_defeated:${enemy.bossId}`]&&!s.receipts[`kill:${s.area}:${enemy.id}`]){this.emit('notice',gearText('loot.rematchFirst'));return;}
  if(!this.safe()){this.emit('notice',gearText('loot.rematchSafe'));return;}
  if(!this.bossLoot.beginRematch(enemy.bossId)){const seconds=this.bossLoot.view(enemy.bossId).remaining;this.emit('notice',gearText('loot.rematchWait',{time:`${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`}));return;}
  const authored=this.areaDef?.enemies.find(e=>e.id===id);if(!authored)return;
  this.combatRules.resetTransient();this.enemyRules.reset();s.projectiles=[];s.fireZones=[];
  s.enemies[index]={...this.spawn({...authored,level:this.bossLoot.rematchLevel(authored),lootChapter:releasedEquipmentChapter(s.progression.level)}),respawnCount:(enemy.respawnCount??0)+1};
  this.changed();this.emit('notice',gearText('loot.rematchStarted'));
 }
 private beginCampaignEvent(id:string){const d=CAMPAIGN_EVENTS[id],s=this.state;if(!d||d.area!==s.area)return;if(d.requires?.some(flag=>!s.flags[flag])||d.requiresAny?.length&&!d.requiresAny.some(flag=>s.flags[flag])){this.emit('notice','先完成现场前置行动，再执行这项操作');return;}if(s.receipts[`campaign:${id}`]){this.emit('inspect','这项现场行动已经完成，结果已保存');return;}if(d.clearEncounter&&(!this.campaign.battleReady()||s.enemies.some(e=>e.hp>0&&!e.respawnSeconds))){this.emit('notice','先处理本地固定守军及其增援');return;}if(!d.peacefulResolution&&!this.safe()){this.emit('notice','先离开敌人的攻击范围');return;}
  const itemOptions=(d.choiceItems??[]).filter(item=>!s.inventory[item]&&(!GROWING_EQUIPMENT[item]||!growingOwned(s,item)));if(d.choices?.length){this.dialogue(`campaign:${id}`,d.optional?d.label:'现场行动',d.description,d.choices.map(c=>[c.id,c.label]));}else if(itemOptions.length){this.dialogue(`campaign:${id}`,'武备自选',d.description,itemOptions.map(item=>[`equipment:${item}`,EQUIPMENT[item]?.name??item]));}else this.finishCampaignEvent(d);
 }
 private finishCampaignEvent(d:CampaignEventDef,choice?:string){const s=this.state,key=`campaign:${d.id}`;if(s.receipts[key])return;const choiceDef=d.choices?.find(c=>c.id===choice),chosenItem=choice?.startsWith('equipment:')?choice.slice(10):null;if(d.choices?.length&&!choiceDef||chosenItem&&!d.choiceItems?.includes(chosenItem))return;
  const shared=d.experienceEvent&&s.progression.xpReceipts[d.experienceEvent]!==undefined;for(const flag of [...d.sets??[],...choiceDef?.sets??[]])s.flags[flag]=true;
  if(d.peacefulResolution)for(const e of s.enemies)if(e.hp>0&&!e.respawnSeconds){e.hp=0;e.phase='dead';this.once(`kill:${s.area}:${e.id}`,()=>{const level=e.level??1,template=CAMPAIGN_ENEMY_TEMPLATES[e.bossId??e.templateId??''];if(!campaignFighter(e)?.deferExperience)this.gainExperience(`enemy:${s.area}:${e.id}`,template?.firstClearExperience??(20+8*(level-1))*(e.bossId?3:1));this.lootRules.enemy(e);if(e.bossId)s.flags[`boss_defeated:${e.bossId}`]=true;});}s.encounters[s.area]=clone(s.enemies);this.lootRules.encounter();
  if(!shared){if(d.gold)this.gold(key,d.gold);s.player.iron=Math.min(9999,s.player.iron+(d.iron??0));s.player.runes=Math.min(9999,s.player.runes+(d.runes??0));s.player.cores=Math.min(9999,s.player.cores+(d.cores??0));for(const item of d.items??[])this.grant(item,1,key);if(chosenItem)this.grant(chosenItem,1,key);else if(d.choiceItems?.length&&!d.choiceItems.some(item=>!s.inventory[item])){s.player.iron=Math.min(9999,s.player.iron+2);s.player.gold=Math.min(9999,s.player.gold+12);}if(d.experienceEvent)this.awardExperience(d.experienceEvent);if(d.experience)this.gainExperience(key,d.experience);}
  for(const recipe of d.recipes??[])if(RECIPES[recipe]&&!s.recipes.includes(recipe))s.recipes.push(recipe);s.receipts[key]=true;s.dialogue=null;this.syncProgression();if(d.id.startsWith('investigate-'))this.growingLoot.opportunity();this.campaign.task(d.id);if(s.flags.m8_complete){s.flags.complete=true;s.status='complete';this.emit('complete','终局行动已完成，世界进度已保存');}this.changed();this.emit('quest',choiceDef?.text??d.description,{id:d.id});
 }
 private cache(o:InteractionDef){
  const s=this.state,item=canonicalItem(o.item??'');
  const source=item==='W08'?'design_reward_ch01_oath_sword':EQUIPMENT[item]?`design_find_${item.toLowerCase()}`:`cache:${o.id}`;
  this.once(source,()=>{const item=o.item??'iron',n=Math.floor(clamp(o.amount??1,1,9999));if(item==='gold')this.gold(o.id.includes('sign')?'design_container_coin_ch01_sign':`coin:${o.id}`,n);else if(item==='iron'){s.player.iron=Math.min(9999,s.player.iron+n);this.emit('reward',`废铁 +${n}`,{id:o.id,value:n});}else if((EQUIPMENT[canonicalItem(item)]||RETIRED_SPELL_TO_SKILL[canonicalItem(item)])&&canonicalItem(item)!=='W02'&&canonicalItem(item)!=='T03'&&!['J03','A13','A10','L01','L02'].includes(canonicalItem(item))){this.grant(item,n,source);}if(o.evidence==='legendary'||o.item==='W08'||o.id.includes('hidden'))this.rollLegend(`cache:${o.id}:legend`,.18);});
  for(const [key,left]of Object.entries(s.pending)){if(!key.startsWith(`${source}|`))continue;delete s.pending[key];this.grant(key.split('|')[1],left,source);}
  if(this.equipped('A12'))for(const object of this.areaDef?.objects??[])if(object.id!==o.id&&dist(s.player,object)<=4&&this.visible(s.player,object))this.emit('clue_reveal',object.label,{id:object.id,at:{x:object.x,z:object.z},duration:3});
 }
 private dialogue(id:string,speaker:string,text:string,options:[string,string][]){
  if(id==='offer'&&this.state.area==='S01-T1'&&!this.state.flags.recovered){options=[...options];for(const [key,label]of [['mira-motive','察迹 · 留意她收信时的停顿'],['mira-terms','对证 · 将抄件与附约摆在一起']])if(!this.state.dice.records[key]?.committed)options.push(['check:'+key,label]);}
  this.state.dialogue={id,speaker,text,options:options.map(([id,label])=>({id,label}))};this.previous={x:0,z:0};this.state.action=null;this.emit('dialogue',text,{id});}
 private offer(){const s=this.state;
  if(s.flags.recovered){this.dialogue('debrief','弥菈',s.flags.saw_copy?'你看过求援段。她隐瞒的是伊芙琳的身份。下面还有人等着开门。':'她认出了落款。“接约前我读过信。先把门打开，再解释。” 预支已经错过，独立追查仍可继续。',s.flags.accepted?[['shop','看看契约补给与探险印戒'],['leave','前往地下寻找伊芙琳']]:[['leave','前往地下寻找伊芙琳']]);}
  else if(s.flags.accepted)this.dialogue('accepted','弥菈','共同署名与分成写在契约上。样片只投出零散星点；完整星片仍在截获的匣中。',[['shop','看看契约补给与探险印戒'],['leave','沿线索出发']]);
  else this.dialogue('offer','弥菈',s.flags.saw_copy?'她展示了日期和求援段，仍遮住姓名。“入口是否塌了，是你的价钱。”':'她倒扣第三只杯子。“替我拿回遗物匣，共同署名。” 贴身纸袋被她收回：雇主隐瞒了失踪者身份。',[['accept','先说分成。我接受委托，预支60金币。'],['ask_letter','先把藏着的信抄件给我看。'],['reject','我不接约。从信使与军营独立追查。']]);
 }
 choose(id:string):GameEvent[]{
  const s=this.state,d=s.dialogue;if(!d||s.dice.active||!d.options.some(o=>o.id===id))return [];
  if(d.id.startsWith('campaign:')){const event=CAMPAIGN_EVENTS[d.id.slice(9)];if(event)this.finishCampaignEvent(event,id);return this.drain();}
  if(d.id==='offer'&&id.startsWith('check:')){this.beginCheck(id.slice(6),'t1-mira');return this.drain();}
  if(id==='shop'&&s.flags.accepted){const anchor=this.areaDef?.objects.find(o=>o.action==='offer'&&o.merchant==='mira');if(anchor&&dist(s.player,anchor)<=1.35&&this.visible(s.player,anchor)&&this.safe()){this.merchant='mira';this.merchantAnchor={x:anchor.x,z:anchor.z};if(!s.discoveredMerchants.includes('mira'))s.discoveredMerchants.push('mira');s.dialogue=null;this.emit('shop',MERCHANTS.mira.name,{id:'mira'});this.changed();return this.drain();}}
  if(d.id==='offer'&&id==='ask_letter'){s.flags.saw_copy=true;this.dialogue('offer','弥菈','她展示抄件日期和求援段，遮住姓名。“近日确实有人求援；那个人，我会亲自去找。”',[['accept','带着这些已公开的信息接约，预支60金币。'],['reject','保留立场，独立追查。']]);this.changed();return this.drain();}
  if(d.id==='offer'&&id==='accept'&&!s.flags.recovered){s.flags.accepted=true;s.flags.rejected=false;this.gold('design_reward_coin_ch01_obj01',60);}
  if(d.id==='offer'&&id==='reject'){s.flags.rejected=true;this.emit('quest','可从信使与军营线索独立追查，未领取预支。');}
  if(d.id==='letter'&&id==='read_letter'){s.flags.read_letter=true;this.awardInspiration('read-letter');this.emit('quest','原信已读：去地下长桌找伊芙琳。');}
  if(d.id==='meeting'){
   if(id==='ask_truth'){s.flags.truth_asked=true;this.awardInspiration('ask-truth');this.dialogue('meeting','弥菈',s.flags.saw_copy?'“你知道有人求援。我没说她是谁。十八年前我答应上去找船，她在下面等。”':'“接约前我读过信。知道她还在。我想先把门打开，再解释我怎么让她等到现在。”',[['cooperate','先帮开门，重新谈约定并共同署名。'],['star_copy','继续独立寻宝，保留星片副本。']]);this.changed();return this.drain();}
   s.flags.meeting=true;s.flags.cooperation_chosen=id==='cooperate';s.flags.star_copy_chosen=id==='star_copy';s.flags.choice_made=true;
  }
  s.dialogue=null;this.previous={x:0,z:0};this.syncProgression();this.changed();return this.drain();
 }
 exitRequirement(exit:ExitDef):string|null {
  if(!playableArea(exit.to))return '第3—8章尚未开放；当前可游玩第一、第二章';
  // A previously cleared arena stays accessible after rebalancing a current save.
  if(exit.to==='S10'&&this.state.flags['boss_defeated:BOSS_R1']||exit.to==='H08'&&this.state.flags['boss_defeated:BOSS_R2'])return null;
  const level=exit.requiredLevel;
  if(level!==undefined)return this.state.progression.level<level?`需要 Lv${level}，当前 Lv${this.state.progression.level}；任务与狩猎均可升级`:null;
  return exit.requires&&!this.state.flags[exit.requires]?'从另一侧解除门闩或放下梯子':null;
 }
 objective():string {
  const chapter=PLAYABLE_CHAPTERS.find(c=>c.id===chapterForArea(this.state.area))!,route=this.journey.tracking();
  if(route!=='hunt')return this.journey.taskHint();
  return `第${chapter.id}章 ${chapter.name} · ${this.state.receipts[`journey:boss:${chapter.id}`]?'已通关':`挑战${chapter.bossName}`}`;
 }
 explorationGuide():string {
  const s=this.state,p=this.progressionView(),ground=HUNTING_GROUNDS[s.area];
  const suggested=ground?s.area:Object.keys(HUNTING_GROUNDS).filter(id=>locationEntryLevel(id)<=p.level).sort((a,b)=>Math.abs(HUNTING_GROUNDS[a].level-p.level)-Math.abs(HUNTING_GROUNDS[b].level-p.level))[0];
  const hunt=HUNTING_GROUNDS[suggested],names=[...new Set(hunt.packs.flat())].map(id=>CAMPAIGN_ENEMY_TEMPLATES[id]?.name??id).join('、');
  const alive=s.enemies.filter(e=>e.respawnSeconds&&e.hp>0).length;
  return `${this.objective()}\n${p.level<40?`升级经验 ${p.xp} / ${p.xpToNext}`:'已达最高等级，继续狩猎可获得掉落'}\n${ground?`本地游荡怪 ${alive} / ${HUNT_ENCOUNTERS[s.area].length}`:`推荐 Lv${hunt.level} ${CAMPAIGN_LEVELS[suggested]?.name??suggested}`}：${names}。怪群击败后28秒起补充，远离出生点20米后刷新。\n${growingJournal(s.area,s.flags,s.receipts,s.inventory)}\n任务路线：${this.journey.taskHint()}\n狩猎路线：自由选择猎区成长，再挑战本章关底。\nN 打开旅程 · 八章规划，当前开放前两章`;
 }
 private canComplete(){const f=this.state.flags;return f.captain_defeated&&f.gate_raised&&f.recovered&&f.read_letter&&f.meeting&&f.workers_released&&(f.trap_handled||f.trap_disabled)&&f.choice_made;}
 questObjective():string{if(this.areaDef?.objects.some(o=>o.action==='journey_board'))return this.journey.taskHint();const f=this.state.flags;if(f.m8_complete)return '终局已完成 · 可继续探索已开放道路';if(!f.accepted&&!f.independent_clue&&!f.recovered)return f.rejected?'向信使或军营取得独立线索':'与弥菈谈委托，或向信使独立追查';if(!f.recovered)return '找回圣匣车中被截获的原信与完整星片';if(!f.read_letter)return '亲自阅读遗物匣中的原信';if(!f.meeting)return '前往 U1-04 长桌，与伊芙琳见面并表明立场';if(!f.workers_released)return '前往 U1-05 释放被扣押的工匠';if(!f.workers_departed)return '从 U1-05 核验过的出口带工匠实际离场';if(!f.captain_defeated)return '回地表击败 S10 灰披队长';if(!f.gate_raised)return '亲手抬起 S10 横杆，领取未熄之誓';if(!f.choice_made)return '回 U1-04 长桌确认救援与星片的约定';if(!f.m3_heat_test)return '前往 H03 疏散工位，实际完成散热回退试验';if(!f.m4_bridge_open)return '在 H08 接回手柄，放下通往军械岸的矿桥';if(!f.m4_bridge_reward)return '在 H09 打开桥后武备台';if(!f.m4_contact)return '前往 U1-08，建立第一次可中止接触';if(!f.m5_pressure)return '从 U2-03 内侧分区泄压，打开深闸';if(!f.m5_archive)return '在 U2-06 核验两个角度的原刻与现代拓本';if(!f.m6_verified)return '在 B10 战后完成校光、复秤、封签并开匣';if(!f.m7_prepared)return '在 F04 或 F07 实际核验一条安全出口';if(!f.west_tower_down||!f.east_tower_down)return `亲手卸下${!f.west_tower_down?' F09 西':''}${!f.east_tower_down?' F10 东':''}弩台固定销`;if(!f['boss_defeated:BOSS_R4'])return '进入 F13 决战庭，击败阿德里安';if(!f.m7_vault)return '在 F14 转动同侧绞盘，开启黑冠主箱';if(!f.core_plans_known)return '在 U2-07 解除镜阵，取得迁行与静眠原图';if(!f.core_exit_verified)return '在 U1-08 实走迁行口，核验两端安全线';return '回 U1-08 选择并亲手执行终局方案';}
 travel(exit:ExitDef):GameEvent[]{
  const s=this.state,def=this.areaDef?.exits.find(e=>e.id===exit.id&&e.to===exit.to);if(!def||s.status==='dead'||s.dialogue||s.dice.active)return [];
  if(dist(s.player,def)>1.35||!this.visible(s.player,def)){this.emit('notice','走到出口再离开');return this.drain();}
  const requirement=this.exitRequirement(def);if(requirement){this.emit('notice',requirement);return this.drain();}
  if(s.enemies.some(e=>e.hp>0&&dist(e,s.player)<3)||s.projectiles.some(q=>q.owner==='enemy'&&dist(q,s.player)<3)){this.emit('notice','先离开敌人的攻击范围');return this.drain();}
  this.enemyRules.reset();
  if(s.area==='U1-05'&&s.flags.workers_released&&!s.flags.workers_departed){s.flags.workers_departed=true;s.flags.workers_returned=true;this.emit('workers_exit','工匠已沿核验过的出口实际离场');this.syncProgression();}if(def.unlock)s.flags[def.unlock]=true;s.encounters[s.area]=clone(s.enemies);this.combatRules.resetTransient();s.area=def.to;s.player.x=def.entry.x;s.player.z=def.entry.z;s.enemies=clone(s.encounters[def.to]??[]);s.projectiles=[];s.fireZones=[];s.action=null;this.areaDef=null;this.previous={x:0,z:0};this.merchant=null;this.merchantAnchor=null;this.changed();this.emit('travel',def.label,{id:def.id,to:def.to,entry:def.entry});return this.drain();
 }
 buy(merchant:string,item:string):boolean{
  const m=canonicalMerchant(merchant),id=canonicalItem(item),def=MERCHANTS[m],s=this.state;
  if(!def||this.merchant!==m||!this.merchantAnchor||dist(s.player,this.merchantAnchor)>1.35||!this.visible(s.player,this.merchantAnchor)||!s.discoveredMerchants.includes(m)||!this.safe()||s.status==='dead'||!!s.dice.active)return false;
  const count=s.merchantStock[m][id]??0,price=def.prices[id];if(count<=0||price===undefined||s.player.gold<price)return false;
  if((s.inventory[id]??0)>=equipmentStackLimit(id))return false;
  const request=this.id('trade');s.player.gold-=price;s.merchantStock[m][id]--;this.grant(id,1,`trade:${m}`);s.receipts[request]=`${m}:${id}:${price}`;this.changed();return true;
 }
 craft(recipe:string,expectedToken?:string):boolean{const q=this.forging.craft(recipe),r=RECIPES[recipe],s=this.state;if(!q.allowed||expectedToken!==undefined&&expectedToken!==q.token){this.emit('notice',q.reason||'资源已变化，请重新确认费用');return false;}s.player.gold-=q.gold;s.player.iron-=q.iron;s.player.runes-=q.runes;s.player.cores-=q.cores;this.grant(r.item,1,`craft:${recipe}`);const request=this.id('craft');s.receipts[request]=recipe;s.receipts[`craft-fee:${request}`]=q.gold;this.changed();this.emit('forge',`${EQUIPMENT[r.item].name}锻造完成${q.teaching?' · 首次教学免工费':''}`);return true;}
 useConsumable(kind:'health'|'resource'|ResourceKind):boolean{
  const s=this.state,p=s.player,profile=resourceProfile(s);if(!['health','resource','stamina','focus','mana'].includes(kind))return false;
  if(kind!=='health'&&kind!=='resource'&&kind!==profile.kind){this.emit('notice',`当前职业需要${profile.potion}`);return false;}
  if(s.status==='dead'||p.hp<=0||s.action||s.dialogue||s.dice.active){this.emit('notice','当前动作结束后再使用药剂');return false;}
  if((s.cooldowns.consumable??0)>1e-6){this.emit('notice','药剂尚在冷却中');return false;}
  const health=kind==='health',stock=health?'healthPotions':profile.stock,value=health?'hp':'focus',max=health?p.maxHp:p.maxFocus;
  if(p[stock]<=0){this.emit('notice','药剂已用尽，返回安全检查点补充');return false;}
  if(p[value]>=max){this.emit('notice',`${health?'生命':profile.name}已满，无需使用药水`);return false;}
  const restored=Math.min(health?Math.max(40,max*.4):max*RESOURCE_RULES.potionFraction,max-p[value]);p[value]+=restored;p[stock]--;s.cooldowns.consumable=RESOURCE_RULES.potionCooldown;
  s.receipts[this.id('consumable')]=health?'health':profile.kind;this.changed();this.emit('consumable',`${health?'生命':profile.name} +${Math.ceil(restored)}`);return true;
 }
 rest():boolean{if(this.state.status==='dead'||!!this.state.dice.active||!this.safe()||!this.checkpointNear())return false;const p=this.state.player;p.hp=p.maxHp;p.focus=p.maxFocus;for(const def of Object.values(SUPPLIES))p[def.stock]=def.capacity;this.state.cooldowns.consumable=0;this.setCheckpoint();this.changed();this.emit('rest','检查点休整：生命、职业资源、药水补满；技能消耗职业资源并自动恢复');return true;}
 retry():GameEvent[]{const s=this.state;if(s.status!=='dead')return [];this.meleeChain.reset();this.hitResponse.reset();s.encounters[s.area]=s.enemies.map(e=>e.hp<=0?clone(e):this.spawn({...e,hp:e.maxHp}));this.combatRules.resetTransient();delete s.combat.engagement;this.enemyRules.reset();s.status=s.flags.m8_complete?'complete':'playing';s.area=s.checkpoint.area;s.player.x=s.checkpoint.x;s.player.z=s.checkpoint.z;s.player.hp=s.player.maxHp;s.player.focus=s.player.maxFocus;for(const def of Object.values(SUPPLIES))s.player[def.stock]=def.capacity;s.cooldowns.consumable=0;s.player.hurtTime=0;s.player.shield=0;s.action=null;s.dialogue=null;s.projectiles=[];s.fireZones=[];s.enemies=clone(s.encounters[s.area]??[]);this.areaDef=null;this.previous={x:0,z:0};this.changed();this.emit('retry','已返回检查点；固定守军进度保留，野外怪群按狩猎周期补充',{to:s.area,entry:{x:s.player.x,z:s.player.z}});return this.drain();}
 private rollLegend(source:string,chance:number,at?:Point){const s=this.state;if(s.dropRolls[source])return;const n=sourceRandom(s.seed,source);let result='none';if(n/2147483647<chance){const pool=['L01','L02'].filter(id=>!s.inventory[id]&&!s.groundLoot.some(d=>d.item===id));if(pool.length){result=pool[(n*48271%2147483647)%pool.length];if(at)this.dropEquipment(result,`legend:${source}`,at);else this.grant(result,1,`legend:${source}`);}else{s.player.iron=Math.min(9999,s.player.iron+3);result='duplicate_iron';}}s.dropRolls[source]={roll:n,result};s.receipts[`roll:${source}`]=result;this.changed();this.emit('loot_roll',result,{id:source});}
 snapshot():GameState{this.state.encounters[this.state.area]=clone(this.state.enemies);rememberCombatLoadout(this.state.combat,this.state.progression);return clone(this.state);}
 static restore(snapshot:unknown,world:WorldQuery,calendarNow:()=>number=Date.now):GameSession {
  validateSnapshot(snapshot);
  const game=new GameSession(snapshot.seed-1,world,calendarNow);game.state=clone(snapshot);const s=game.state,oilMigrated=migrateRemovedOil(s),skillsMigrated=migrateFourSkillKit(s),journeyMigrated=initializeLifecycleJourney(s),curveMigrated=updateExperienceCurve(s.progression),resourcesMigrated=migrateClassResource(s),migrated=oilMigrated||resourcesMigrated||skillsMigrated||journeyMigrated||curveMigrated||!s.forging||s.forging.version===1||!s.groundLoot;s.groundLoot??=[];if(!s.forging)s.forging=freshForging();syncRandomForging(s);
  // Resume current-format durable state; in-flight input and effects never resume.
  s.dialogue=null;s.action=null;s.projectiles=[];s.fireZones=[];s.combat.casts=[];
  game.combatRules.clearSkillCooldowns();s.player.hurtTime=0;
  activateCombatLoadout(s.combat,s.progression);game.recalculate();game.dirty=migrated;return game;
 }
}

/** Reject malformed/unknown snapshots before any state is installed or written. */
export function validateSnapshot(value:unknown):asserts value is GameState {
 const fail=()=>{throw new Error('无效或不支持的首章存档');};
 const jsonSafe=(v:unknown,depth=0):boolean=>depth<20&&(v===null||typeof v==='boolean'||typeof v==='string'&&v.length<10000||typeof v==='number'&&Number.isFinite(v)||Array.isArray(v)&&v.length<=20000&&v.every(x=>jsonSafe(x,depth+1))||record(v)&&Object.keys(v).length<=20000&&Object.entries(v).every(([k,x])=>k.length<300&&k!=='__proto__'&&k!=='constructor'&&k!=='prototype'&&jsonSafe(x,depth+1)));
 if(!jsonSafe(value))return fail();
 validateCurrentSnapshot(value);
}
