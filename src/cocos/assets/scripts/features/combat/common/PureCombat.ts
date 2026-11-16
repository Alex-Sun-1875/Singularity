import {playerCombatAttributes,enemyCombatAttributes,rollContactHit} from './CombatAccuracy';
import {SkillUpgrades} from '../../progression/common/SkillUpgrades';
import {resourceProfile,skillResourceText} from './ClassResource';
import {skillWeaponCompatible,skillWeaponRequirement} from './SkillWeapons';
import type {CombatSkillEvent, Point} from '../../../core/Contracts';
import type {ActionState,EnemyState,GameState,ProjectileState} from '../../../core/GameSession';
import {COMBAT_RULES,PURE_SKILLS,LEGACY_COMBAT_SKILLS,combatSkillCatalog,type CombatSkillDef,type CombatSkillRank} from '../data/PureSkills';
import {EQUIPMENT,equipmentPowerMultiplier} from '../../equipment/data/Equipment';
import {skillPower,allocatedSkillRank,skillUnlocked,type ProgressionState} from '../../progression/common/Progression';
import {equippedGearBonus,effectiveAttribute,combatCriticalChance,combatCriticalMultiplier} from '../../equipment/common/EquipmentDice';
import type {RandomForgingBonus} from '../../crafting/data/EquipmentForging';
import {growingStats} from '../../equipment/data/GrowingEquipment';
import {GrowingEquipmentCombat,validateGrowingPulses,type GrowingPulse} from './GrowingEquipmentCombat';
import {restorePlayerHealth} from '../../pets/common/PetBenefits';
import {enemyProfile,enemyCanInterrupt,enemyHurtRadius} from './EnemyCombat';
import {validateCombatLoadouts,weaponCombatFamily,type CombatFamily,type CombatLoadout} from '../../progression/common/CombatLoadouts';
import {combatActionBeatCount,combatActionDuration,combatSegmentInterval} from './CombatActionTiming';
import {BUILD_PROFILE} from '../../../shared/BuildProfile';
import {COMBAT_TACTICS} from './CombatTactics';
import {tacticsText} from '../locales/TacticsText';
export {combatActionBeatCount,combatActionDuration,combatSegmentInterval} from './CombatActionTiming';

export interface CombatSkillView {
 id:string; name:string; family:string; type:string; rank:number; requiredLevel:number; nextRequiredLevel:number|null;
 cooldown:number; resourceCost:number; resourceEnough:boolean; ready:boolean; compatible:boolean; assignedSlot:number|null; description:string; range:number; shape:string; unlocked:boolean;
}
export interface CombatCast {
 id:string; skillId:string; rank:CombatSkillRank; from:Point; to:Point; angle:number; elapsed:number;
 released:boolean; nextSegment:number; targets:string[]; hits:string[]; breakHits:string[];
 critical:boolean; power:number; attributeMultiplier:number; damageBonus:number; chargeGranted:boolean; chargeBonus:number; procs:string[];
 accuracy?:number;upgrades?:Record<string,number>;criticalChance?:number;criticalRoll?:number;criticalMultiplier?:number;
 releaseTime?:number; volleyPoints?:Record<string,Point>; waveProgress?:number;zoneUntil?:number;retreatElapsed?:number;
 rush?:{distance:number;elapsed:number;duration:number;stopped:boolean};
 equipment:string[]; passives:Record<string,number>; weapon:string;growthLevel?:number;
}
export interface CombatStatus {hunterMarkUntil:number; hunterMarkBonus:number; burnUntil:number; burnNext:number; burnDamage:number; slowUntil:number; slowPercent:number; lightningUntil:number}
export interface CombatState {
 engagement?:{area:string;enemyIds:string[];quietSince?:number};
 family?:CombatFamily;staffFamily?:'FIR'|'THU';loadouts?:Partial<Record<CombatFamily,CombatLoadout>>;
 version:2|3|4|5; activeSlots:[string|null,string|null,string|null,string|null]; passiveSlots:[string|null,string|null]; ultimate:string|null;
 charge:number; ultimateLock:number; cooldowns:Record<string,number>; buffs:Record<string,number>;
 statuses:Record<string,CombatStatus>; casts:CombatCast[];growingPending?:GrowingPulse[];
}
export interface CombatHost {
 state():GameState; visible(a:Point,b:Point):boolean; move(p:Point,d:Point,r?:number):void;
 id(prefix:string):string; emit(type:string,text?:string,extra?:Record<string,unknown>):void;
 damage(enemy:EnemyState,value:number,cast:string,element:string,angle:number,critical?:boolean):void; changed():void;
 miss?(enemy:EnemyState,action:string,chance:number,roll:number):void;
 anchors?():readonly {id:string;x:number;z:number;hp:number;radius:number}[];
 damageAnchor?(id:string,damage:number,cast:string):boolean;
}
const distance=(a:Point,b:Point)=>Math.hypot(a.x-b.x,a.z-b.z);
const angleTo=(a:Point,b:Point)=>Math.atan2(b.x-a.x,b.z-a.z);
const dir=(a:number,d:number):Point=>({x:Math.sin(a)*d,z:Math.cos(a)*d});
const add=(a:Point,b:Point):Point=>({x:a.x+b.x,z:a.z+b.z});
const delta=(a:number,b:number)=>Math.atan2(Math.sin(a-b),Math.cos(a-b));
const clamp=(n:number,a:number,b:number)=>Math.max(a,Math.min(b,n));
const at=(p:Point):Point=>({x:p.x,z:p.z});
const copy=<T>(v:T):T=>JSON.parse(JSON.stringify(v));
function segmentDistance(a:Point,b:Point,p:Point){const x=b.x-a.x,z=b.z-a.z,l=x*x+z*z,t=l?clamp(((p.x-a.x)*x+(p.z-a.z)*z)/l,0,1):0;return Math.hypot(a.x+t*x-p.x,a.z+t*z-p.z);}
function random(seed:number,id:string){let n=seed;for(let i=0;i<id.length;i++)n=(Math.imul(n,31)+id.charCodeAt(i))>>>0;return n/4294967296;}
export function freshCombat():CombatState{return {version:5,activeSlots:['WAR_01',null,null,null],passiveSlots:[null,null],ultimate:null,charge:0,ultimateLock:0,cooldowns:{},buffs:{},statuses:{},casts:[]};}

/** Geometry, damage and projectile contacts are authoritative here; the renderer only consumes their events. */
export class PureCombat {
 private upgrades=new SkillUpgrades({state:()=>this.s,status:e=>this.status(e),poise:(e,value,id)=>this.poise(e,value,id)});
 private readonly meleeFeedback=new Map<string,{id:string;at:Point;reported:boolean}>();
 private growing=new GrowingEquipmentCombat({state:()=>this.s,visible:(a,b)=>this.host.visible(a,b),damage:(e,n,c,element,a)=>this.host.damage(e,n,c,element,a),shield:(n,t)=>this.shield(n,t),status:e=>this.status(e),emit:(t,m,x)=>this.host.emit(t,m,x),changed:()=>this.host.changed()});
 constructor(private host:CombatHost){}
 growingMove(distance:number,dt:number){this.growing.move(distance,dt);}
 growingEvade(){this.growing.evade();this.upgrades.evade();}
 growingKill(action:string,source:string,e:EnemyState){this.growing.kill(action,source,e);}
 preventGrowingDeath(damage:number){return this.growing.preventDeath(damage);}
 private get s(){return this.host.state();}
 private get c(){return this.s.combat;}
 private equipped(id:string,c?:CombatCast){return c?c.equipment.includes(id):Object.values(this.s.equipment).includes(id);}
 private passive(id:string,c?:CombatCast){return c?c.passives[id]??0:this.c.passiveSlots.includes(id)?allocatedSkillRank(this.s.progression,id)?.primaryValue??0:0;}
 private ready(key:string){return !(this.c.cooldowns[key]>0);}
 private proc(c:CombatCast,id:string,cd=0){if(c.procs.includes(id)||!this.ready(id))return false;c.procs.push(id);if(cd)this.c.cooldowns[id]=cd;return true;}
 private secondary(c:CombatCast,id:string,e:EnemyState,damage:number,cd=0){if(c.procs.filter(k=>k.startsWith('secondary:')).length>=2||!this.proc(c,`secondary:${id}`,cd))return false;this.host.damage(e,damage,c.id,'secondary',c.angle);return true;}
 private addCharge(c:CombatCast,bonus=false){if(!bonus||PURE_SKILLS[c.skillId]?.type==='ultimate'||c.chargeBonus>=2)return;this.s.player.focus=Math.min(this.s.player.maxFocus,this.s.player.focus+2-c.chargeBonus);c.chargeBonus=2;}
 private shield(amount:number,duration:number){const b=this.c.buffs;b.shieldAmount=Math.min(this.s.player.maxHp*.35,Math.max(b.shieldAmount??0,amount));b.shieldUntil=this.s.time+duration;this.s.player.shield=b.shieldAmount;}
 private thunderWeapon(c:CombatCast,source:1|3,enhancement=c.rank){
  const b=this.c.buffs,damage=c.power*(source===3?enhancement.maxDamagePerTargetS:this.upgrades.passive(c,'THU_P1').extraBasicS??.75)/3;
  if((b.thunderUntil??0)>this.s.time&&(b.thunderCharges??0)>0&&(b.thunderDamage??0)>damage)return;
  b.thunderUntil=this.s.time+(source===3?enhancement.upgradeEffects?.buffSeconds??6:6);b.thunderCharges=3;b.thunderDamage=damage;b.thunderSource=source;
  b.thunderRank=source===3?enhancement.rank:PURE_SKILLS.THU_P1.ranks.find(r=>r.primaryValue===c.passives.THU_P1)?.rank??1;
 }
 private event(type:CombatSkillEvent['type'],c:CombatCast,extra:Record<string,unknown>={}) {
 const d=PURE_SKILLS[c.skillId],g=c.rank.geometry;this.host.emit(type,undefined,{skillId:c.skillId,family:d.style,rank:c.rank.rank,castId:c.id,shape:g?.kind??'self',geometry:g?{...g,anglesDegrees:g.anglesDegrees?[...g.anglesDegrees]:undefined}:undefined,from:at(c.from),to:at(c.to),segment:c.nextSegment,angle:c.angle,angleDegrees:g?.angleDegrees??0,anglesDegrees:g?.anglesDegrees?[...g.anglesDegrees]:undefined,radius:g?.radiusMetres??0,width:g?.widthMetres??0,length:g?.lengthMetres??0,depth:g?.depthMetres??0,...extra});
 }
 private passiveEvent(id:string,c:CombatCast,to?:EnemyState,status='passive',from?:Point){const d=PURE_SKILLS[id],rank=d.ranks.find(r=>r.primaryValue===c.passives[id])?.rank??1;this.event('skill_status',c,{skillId:id,family:d.style,rank,from:at(from??c.from),to:at(to??this.s.player),targetId:to?.id,status,duration:.25});}
 compatible(id:string){const d=PURE_SKILLS[id];return !!d&&skillWeaponCompatible(d,this.s.equipment.weapon);}
 view(ids?:readonly string[]):CombatSkillView[]{const skills=ids?ids.map(id=>PURE_SKILLS[id]).filter((d):d is CombatSkillDef=>!!d):Object.values(PURE_SKILLS);return skills.map(d=>{const r=allocatedSkillRank(this.s.progression,d.id),rank=r?.rank??0,cd=BUILD_PROFILE.noSkillCooldown?0:this.c.cooldowns[d.id]??0;return {id:d.id,name:d.name,family:d.style,type:d.type,rank,requiredLevel:d.unlockLevel,nextRequiredLevel:null,cooldown:cd,resourceCost:d.resourceCost,resourceEnough:this.s.player.focus+1e-8>=d.resourceCost,ready:!!r&&cd<=0&&this.compatible(d.id)&&this.s.player.focus+1e-8>=d.resourceCost&& (BUILD_PROFILE.noSkillCooldown||d.type!=='ultimate'||this.c.ultimateLock<=0),compatible:this.compatible(d.id),assignedSlot:d.type==='passive'?this.c.passiveSlots.indexOf(d.id)<0?null:this.c.passiveSlots.indexOf(d.id):d.type==='ultimate'?this.c.ultimate===d.id?0:null:this.c.activeSlots.indexOf(d.id)<0?null:this.c.activeSlots.indexOf(d.id),description:skillResourceText(r?.evolution??r?.effect??d.mechanic??'')+(d.id==='COM_01'?'\n'+tacticsText('dodgeHelp'):''),range:r?.castRangeMetres??d.ranks[0].castRangeMetres,shape:r?.geometry?.kind??'self',unlocked:!!r};});}
 cooldownFor(d:CombatSkillDef,r:CombatSkillRank){if(BUILD_PROFILE.noSkillCooldown)return 0;const reduction=(this.equipped('J04')?.05:0)+(this.equipped('W16')&&['FIR','THU'].includes(d.style)&&d.type!=='ultimate'?.04:0)+(d.id==='COM_01'&&this.equipped('DR2-01')?.06:0);return r.cooldownSeconds*(1-Math.min(.2,reduction));}
 /** Resolve again during preview and on release so dead, occluded or distant
  * enemies cannot leave an automatic cast aimed at a stale ground point. */
 autoAimTarget(id:string):Point|undefined {
  const d=PURE_SKILLS[id],r=allocatedSkillRank(this.s.progression,id),p=this.s.player;
  if(!d||!r)return undefined;
  if(!d.offensive||d.targetingMode==='self'||r.geometry?.kind.startsWith('self'))return at(p);
  let nearest:EnemyState|undefined,best=Infinity;
  for(const enemy of this.s.enemies){
   const metres=distance(p,enemy);
   if(enemy.hp<=0||metres>r.castRangeMetres+.001||metres>best||!this.host.visible(p,enemy))continue;
   if(metres===best&&nearest&&enemy.id.localeCompare(nearest.id)>=0)continue;
   nearest=enemy;best=metres;
  }
  return nearest?at(nearest):add(p,dir(p.angle,r.castRangeMetres*.72));
 }
 clearSkillCooldowns(){
  for(const key of Object.keys(this.c.cooldowns))if(key==='skillRetry'||PURE_SKILLS[key]&&PURE_SKILLS[key].type!=='passive'&&(BUILD_PROFILE.noSkillCooldown||PURE_SKILLS[key].ranks[0].cooldownSeconds===0))this.c.cooldowns[key]=0;
  if(BUILD_PROFILE.noSkillCooldown)this.c.ultimateLock=0;
  if('COM_01' in this.c.cooldowns||'dash' in this.s.cooldowns)this.s.cooldowns.dash=this.c.cooldowns.COM_01??0;
 }
 cast(id:string,target?:Point,angle?:number):boolean {
 const s=this.s,d=PURE_SKILLS[id],r=allocatedSkillRank(s.progression,id),p=s.player;
 const reject=(message:string)=>{this.host.emit('notice',message);return false;};
 if(!d||d.type==='passive'||!r||!s.progression.learned[id])return reject('技能尚未开放');
 if(d.activation==='automatic')return reject('该技能为自动强化，无需装配或手动施放');
 if(s.status==='dead'||s.dialogue||s.dice.active||s.action)return false;
 if(!this.compatible(id))return reject(skillWeaponRequirement(d));
 if(!BUILD_PROFILE.noSkillCooldown&&(this.c.cooldowns[id]??0)>0)return reject('技能冷却中');
 if(!BUILD_PROFILE.noSkillCooldown&&d.type==='ultimate'&&this.c.ultimateLock>0)return reject('终极释放间隔中');
 if(p.focus+1e-8<d.resourceCost)return reject(`${resourceProfile(s).name}不足，需要${d.resourceCost}点；可普攻、闪避或使用对应药水`);
 if(target&&(!Number.isFinite(target.x)||!Number.isFinite(target.z)))return false;
 if(id==='COM_02'&&p.hp>=p.maxHp)return reject('生命已满');
 if(id==='COM_02'&&(this.c.buffs.healCount??0)>0)return reject('恢复效果持续中');
 const requestedAngle=Number.isFinite(angle)?angle!:target&&distance(p,target)>.001?angleTo(p,target):p.angle;const a=Math.atan2(Math.sin(requestedAngle),Math.cos(requestedAngle));
 const self=!d.offensive||d.targetingMode==='self',meleeDirection=r.geometry?.kind==='meleeFan'||r.geometry?.kind==='meleeRushCross';
 // Directional melee accepts a facing, not a remote victim. The rush alone
 // moves the caster; its collision path decides the actual landing point.
 const to=self?at(p):meleeDirection?add(p,dir(a,target?Math.min(distance(p,target),r.castRangeMetres):r.castRangeMetres)):target?at(target):add(p,dir(a,Math.min(r.castRangeMetres,8)));
 if(!self&&!meleeDirection&&distance(p,to)>r.castRangeMetres+.001)return reject(`目标超出${r.castRangeMetres}米射程`);
 if(!self&&!meleeDirection&&!this.host.visible(p,to))return reject('墙体或高差阻挡施法位置');
 const attr=d.style==='WAR'?'strength':d.style==='BOW'?'dexterity':'intellect';
 const cast:CombatCast={id:this.host.id('cast'),skillId:id,rank:copy(r),from:at(p),to,angle:a,elapsed:0,released:false,nextSegment:0,targets:[],hits:[],breakHits:[],accuracy:playerCombatAttributes(s).accuracy,criticalMultiplier:combatCriticalMultiplier(s),criticalRoll:random(s.seed,`${s.sequence}:crit`),criticalChance:combatCriticalChance(s),critical:random(s.seed,`${s.sequence}:crit`)<combatCriticalChance(s),power:skillPower(s.progression)*equipmentPowerMultiplier(s.equipment.weapon,s.progression.level)*(1+equippedGearBonus(s).power/100),growthLevel:s.progression.level,attributeMultiplier:1+.008*(effectiveAttribute(s,attr)-10),damageBonus:0,chargeGranted:false,chargeBonus:0,procs:[],equipment:Object.values(s.equipment).filter((id):id is string=>typeof id==='string'),passives:Object.fromEntries(this.c.passiveSlots.filter((id):id is string=>!!id).map(id=>[id,this.passive(id)])),weapon:s.equipment.weapon};
 if(d.style==='THU'&&d.offensive&&p.movingTime>=(this.upgrades.passive(undefined,'THU_P1').movingSeconds??1.5)&&this.passive('THU_P1')&&this.ready('THU_P1')){cast.damageBonus+=this.passive('THU_P1')/100;this.c.cooldowns.THU_P1=6;cast.procs.push('passive-ready:THU_P1');}
 if(d.style==='THU'&&d.offensive&&p.movingTime>=(this.upgrades.passive(undefined,'THU_P1').movingSeconds??1.5)&&allocatedSkillRank(s.progression,'THU_03')&&this.ready('THU_03'))cast.procs.push('enhancement-ready:THU_03');
 for(const [key,value]of [['nextDamage',.06],['breakNextDamage',.08],['interruptNextDamage',.10],['crossNextDamage',.08],['dashBowDamage',.08]] as [string,number][]){if((this.c.buffs[key]??0)>s.time&&(key!=='crossNextDamage'||id==='WAR_01')&&(key!=='dashBowDamage'||id==='BOW_01')){cast.damageBonus+=value;delete this.c.buffs[key];}}
 let windup=d.windupSeconds;if(d.style==='BOW'&&this.equipped('A10'))windup*=.92;if((d.style==='FIR'||d.style==='THU')&&this.equipped('DU2-02'))windup*=.96;
 if(id==='WAR_02')cast.rush={distance:distance(p,to),elapsed:0,duration:.18,stopped:false};
 const duration=combatActionDuration(d,r,windup,cast.rush?.duration??0);
 s.action={id:cast.id,kind:id==='COM_01'?'dash':`pure:${id}`,elapsed:0,duration,angle:a,hits:[],emitted:false,damage:0,target:to,skillId:id,rank:r.rank,releaseAt:windup};
 this.c.casts.push(cast);p.angle=a;this.event('skill_cast',cast,{duration:windup});
 if(['WAR_01','WAR_02','WAR_04','WAR_05'].includes(id)){
  const intended=this.targets(cast).find(e=>this.host.visible(cast.from,e));
  if(intended){if(this.meleeFeedback.size>=64)this.meleeFeedback.delete(this.meleeFeedback.keys().next().value!);this.meleeFeedback.set(cast.id,{id:intended.id,at:at(intended),reported:false});}
 }
 if(id==='COM_01'){this.c.cooldowns[id]=this.cooldownFor(d,r);s.cooldowns.dash=this.c.cooldowns[id];s.cooldowns.dodgeDefense=2;cast.released=true;this.event('skill_release',cast,{duration:.34});if(this.equipped('DR2-04')&&this.ready('DR2-04')){this.c.buffs.dashBowDamage=s.time+3;this.c.cooldowns['DR2-04']=8;}if(this.equipped('DE04')&&this.ready('DE04')){this.c.buffs.dashBreak=s.time+3;this.c.cooldowns.DE04=8;}}
 this.host.changed();return true;
 }
 action(a:ActionState,dt:number){const c=this.c.casts.find(c=>c.id===a.id);if(!c)return;const old=a.elapsed;a.elapsed+=dt;c.elapsed=a.elapsed;
 if(c.skillId==='COM_01'&&a.elapsed>.04&&old<.26){const active=Math.max(0,Math.min(a.elapsed,.26)-Math.max(old,.04)),length=c.rank.castRangeMetres*(this.equipped('A16')?1.08:1);this.host.move(this.s.player,dir(c.angle,length*active/.22));}
 if(!c.released&&a.elapsed+1e-8>=(a.releaseAt??0)){c.released=true;c.from=at(this.s.player);a.emitted=true;this.release(c);}
 if(this.s.action?.id!==a.id)return;
 if(c.skillId==='BOW_07'&&c.released){const duration=c.rank.moveSeconds??.2,release=a.releaseAt??0,active=Math.max(0,Math.min(a.elapsed-release,duration)-Math.max(0,old-release));if(active>0)this.host.move(this.s.player,dir(c.angle,-(c.rank.moveMetres??2.5)*active/duration));c.retreatElapsed=Math.min(duration,Math.max(0,a.elapsed-release));}
 if(c.released&&c.rush&&c.rush.elapsed<c.rush.duration){
  const rush=c.rush,release=(a.releaseAt??rush.duration)-rush.duration,active=Math.max(0,Math.min(a.elapsed-release,rush.duration)-Math.max(0,old-release));
  if(active>0&&!rush.stopped){const before=at(this.s.player),length=rush.distance*active/rush.duration;this.host.move(this.s.player,dir(c.angle,length));if(distance(before,this.s.player)+.001<length)rush.stopped=true;}
  rush.elapsed=Math.min(rush.duration,Math.max(0,a.elapsed-release));
  if(rush.elapsed+1e-8>=rush.duration){
   rush.elapsed=rush.duration;c.from=at(this.s.player);c.to=at(this.s.player);a.target=at(c.to);c.releaseTime=this.s.time;
   this.segment(c,0);c.nextSegment=1;
  }
 }
 if(a.elapsed+1e-8>=a.duration)this.s.action=null;
 }
 private release(c:CombatCast){const d=PURE_SKILLS[c.skillId],r=allocatedSkillRank(this.s.progression,c.skillId),meleeDirection=r?.geometry?.kind==='meleeFan'||r?.geometry?.kind==='meleeRushCross';c.from=at(this.s.player);if(!this.compatible(c.skillId)){this.s.action=null;c.nextSegment=c.rank.authoredDamageHits;this.host.emit('notice',skillWeaponRequirement(d));return;}if(!r||r.rank<c.rank.rank||d.offensive&&!meleeDirection&&(distance(c.from,c.to)>r.castRangeMetres+.001||!this.host.visible(c.from,c.to))){this.s.action=null;c.nextSegment=c.rank.authoredDamageHits;this.host.emit('notice','出手时目标位置已超出射程或被阻挡');return;}if(c.skillId==='COM_02'&&this.s.player.hp>=this.s.player.maxHp){this.s.action=null;return;}
 if(this.s.player.focus+1e-8<d.resourceCost){this.s.action=null;c.nextSegment=r.authoredDamageHits;this.host.emit('notice',`${resourceProfile(this.s).name}不足，技能未释放`);return;}
 // The accepted rank is a windup preview. Only this successful release commits
 // the payload; its existing critical result stays shared by every later segment.
 const attr=d.style==='WAR'?'strength':d.style==='BOW'?'dexterity':'intellect',oldThunderBonus=c.passives.THU_P1??0;
 c.accuracy=playerCombatAttributes(this.s).accuracy;c.rank=copy(r);c.growthLevel=this.s.progression.level;c.power=skillPower(this.s.progression)*equipmentPowerMultiplier(this.s.equipment.weapon,c.growthLevel)*(1+equippedGearBonus(this.s).power/100);c.attributeMultiplier=1+.008*(effectiveAttribute(this.s,attr)-10);
 c.equipment=Object.values(this.s.equipment).filter((id):id is string=>typeof id==='string');c.weapon=this.s.equipment.weapon;
 c.passives=Object.fromEntries(this.c.passiveSlots.filter((id):id is string=>!!id).map(id=>[id,this.passive(id)]));
 if(c.procs.includes('passive-ready:THU_P1'))c.damageBonus+=((c.passives.THU_P1??0)-oldThunderBonus)/100;
 this.upgrades.prepare(c);
 const straight=['projectileCorridor','sweptCorridor','projectileWithImpactDisk','impactSplitProjectiles','impactChainProjectile','instantCorridor'].includes(r.geometry?.kind??'');
 if(straight&&distance(c.from,c.to)>.001)c.angle=angleTo(c.from,c.to);
 if(!d.offensive||d.targetingMode==='self')c.to=at(c.from);
 const action=this.s.action;if(action?.id===c.id){action.rank=r.rank;action.angle=c.angle;action.target=at(c.to);}this.s.player.angle=c.angle;
 this.s.player.focus=Math.max(0,this.s.player.focus-d.resourceCost);
 c.releaseTime=this.s.time;this.c.cooldowns[c.skillId]=this.cooldownFor(d,r);if(d.type==='ultimate')this.c.ultimateLock=BUILD_PROFILE.noSkillCooldown?0:d.sharedUltimateLockSeconds;this.event('skill_release',c,c.rush?{phase:'rush',duration:c.rush.duration}:{});
 if(c.rush){if(action?.id===c.id)action.releaseAt=(action.releaseAt??d.windupSeconds)+c.rush.duration;return;}
 if(r.shieldMaxHpPercent){this.shield(this.s.player.maxHp*r.shieldMaxHpPercent/100*(c.skillId==='WAR_03'&&this.equipped('W15',c)?1.12:1)*(1+(c.upgrades?.shieldPercent??0)/100),4);this.c.buffs.shieldSkill=c.skillId==='WAR_03'?1:2;this.c.buffs.shieldRank=r.rank;if(c.skillId==='WAR_03'){this.c.buffs.ironShield=this.s.time+4;this.c.buffs.ironAbsorbed=0;if(this.equipped('A13',c))this.c.buffs.ironDefense=this.s.time+3;}this.event('skill_status',c,{duration:4,status:'shield',value:this.s.player.shield});return;}
 if(c.skillId==='THU_03'){this.thunderWeapon(c,3);c.nextSegment=r.authoredDamageHits;this.event('skill_status',c,{duration:r.upgradeEffects?.buffSeconds??6,status:'thunderWeapon'});return;}
 if(c.skillId==='THU_06'){this.c.buffs.stormWardUntil=this.s.time+(r.zoneDurationSeconds??3);this.c.buffs.stormWardSpeed=r.speedPercent??.2;this.c.buffs.stormWardReduction=r.reductionPercent??.35;this.event('skill_status',c,{duration:r.zoneDurationSeconds??3,status:'stormWard'});return;}
 if(c.skillId==='FIR_04'||c.skillId==='BOW_06'){
  for(const old of this.c.casts)if(old!==c&&old.skillId===c.skillId&&old.zoneUntil){old.zoneUntil=0;old.nextSegment=old.rank.authoredDamageHits;this.event('skill_end',old);}
  c.zoneUntil=this.s.time+(r.zoneDurationSeconds??4);this.event('skill_zone',c,{duration:r.zoneDurationSeconds??4});
  if(c.skillId==='BOW_06')return;
 }
 if(c.skillId==='COM_02'){this.c.buffs.healNext=this.s.time;this.c.buffs.healCount=3;this.c.buffs.healRank=r.rank;this.c.buffs.healFirstFraction=r.upgradeEffects?.firstHealFraction??1/3;this.c.buffs.healEmergency=r.upgradeEffects?.emergencyHealPercent??0;this.c.buffs.healAmount=this.s.player.maxHp*r.healMaxHpPercent/100*(this.equipped('DE03',c)?1.08:1);this.event('skill_status',c,{duration:3,status:'heal'});return;}
 if(c.skillId==='BOW_04'||c.skillId==='THU_02'){
  const target=this.s.enemies.filter(e=>e.hp>0&&distance(e,c.to)<=1.25&&distance(e,c.from)<=r.castRangeMetres&&this.host.visible(c.from,e)).sort((a,b)=>distance(a,c.to)-distance(b,c.to)||a.id.localeCompare(b.id))[0];
  if(target){
   if(c.skillId==='BOW_04'){
    this.hit(c,target,1,0);if(!c.hits.includes(`0:${target.id}`))return;const st=this.status(target);st.hunterMarkUntil=this.s.time+(r.upgradeEffects?.markSeconds??8);st.hunterMarkBonus=r.markedDirectSkillBonusPercent??8;target.markedUntil=st.hunterMarkUntil;this.upgrades.mark(c,target);
    this.event('skill_status',c,{to:at(target),targetId:target.id,status:'hunterMark',duration:r.upgradeEffects?.markSeconds??8});
   }else{
    c.to=at(target);
    const nodes=[target,...this.s.enemies.filter(e=>e.hp>0&&e.id!==target.id&&distance(e,c.to)<=(r.geometry?.radiusMetres??0)&&this.host.visible(c.to,e)).sort((a,b)=>distance(a,c.to)-distance(b,c.to)||a.id.localeCompare(b.id)).slice(0,(r.targetLimit??1)-1)];
    c.targets=nodes.map(e=>e.id);this.lightningNetwork(c,nodes,0,1,target.id,.7);if(r.interruptSeconds&&c.hits.includes(`0:${target.id}`))this.interrupt(c,target,r.interruptSeconds);
   }
  }c.nextSegment=1;return;
 }
 if(c.skillId==='THU_04'||c.skillId==='THU_05')c.targets=this.targets(c).slice(0,r.targetLimit??999).map(e=>e.id);
 if(c.skillId==='BOW_05'){c.targets=this.targets(c).map(e=>e.id);c.volleyPoints=Object.fromEntries(c.targets.map(id=>[id,at(this.s.enemies.find(e=>e.id===id)!)]));}
 if(c.skillId==='FIR_05')this.event('skill_zone',c,{duration:3.3});
 this.segment(c,0);c.nextSegment=1;
 }
 private status(e:EnemyState){return this.c.statuses[e.id]??={hunterMarkUntil:0,hunterMarkBonus:0,burnUntil:0,burnNext:0,burnDamage:0,slowUntil:0,slowPercent:0,lightningUntil:0};}
 private slow(c:CombatCast,e:EnemyState,seconds:number){
  const st=this.status(e),percent=e.bossId||e.kind==='captain'?.1:Math.min(.45,c.rank.slowPercent??.35);
  if(st.slowUntil<=this.s.time||percent>=st.slowPercent){st.slowPercent=percent;st.slowUntil=Math.max(st.slowUntil,this.s.time+seconds);}
 }
 private interrupt(c:CombatCast,e:EnemyState,seconds:number){
  const key=`controlProtected:${e.id}`;if(e.hp<=0||e.bossId||e.kind==='captain'||(this.c.buffs[key]??0)>this.s.time||!enemyCanInterrupt(e))return;
  e.phase='stagger';e.phaseTime=seconds;this.c.buffs[key]=this.s.time+seconds+3;
  this.event('skill_status',c,{targetId:e.id,to:at(e),duration:seconds,status:'interrupt'});
 }
 private zones(){
  for(const c of this.c.casts){
   if(!c.released||c.zoneUntil===undefined)continue;
   if(c.zoneUntil<=this.s.time){if(!c.procs.includes('zone-ended')){c.procs.push('zone-ended');this.event('skill_end',c);}continue;}
   if(c.skillId==='FIR_04'){for(const e of this.targets(c))this.slow(c,e,c.rank.slowLingerSeconds??.4);continue;}
   if(c.skillId!=='BOW_06'||this.s.time<(c.releaseTime??this.s.time)+(c.rank.armSeconds??.3))continue;
   const targets=this.targets(c);if(!targets.length)continue;
   this.segment(c,0);c.nextSegment=c.rank.authoredDamageHits;c.zoneUntil=this.s.time;
   for(const e of targets){if(e.hp<=0||!c.hits.includes(`0:${e.id}`))continue;this.slow(c,e,c.rank.slowLingerSeconds??2);
    const key=`rootProtected:${e.id}`;if(!e.bossId&&e.kind!=='captain'&&(this.c.buffs[key]??0)<=this.s.time){this.c.buffs[`rootUntil:${e.id}`]=this.s.time+(c.rank.rootSeconds??.8);this.c.buffs[key]=this.s.time+(c.rank.rootSeconds??.8)+3;this.event('skill_status',c,{targetId:e.id,to:at(e),duration:c.rank.rootSeconds??.8,status:'root'});}
   }
   this.event('skill_end',c,{phase:'triggered'});
  }
 }
 private inside(c:CombatCast,e:Point,segment=0){const g=c.rank.geometry;if(!g)return false;const a=g.origin==='caster'?c.from:c.to;const x=e.x-a.x,z=e.z-a.z,forward=x*Math.sin(c.angle)+z*Math.cos(c.angle),side=x*Math.cos(c.angle)-z*Math.sin(c.angle),radius=enemyHurtRadius(e);
 switch(g.kind){case 'meleeRushCross':case 'crossStrips':return (g.anglesDegrees??[-35,35]).some(deg=>{const ang=c.angle+deg*Math.PI/180,d=dir(ang,(g.lengthMetres??0)/2);return segmentDistance({x:a.x-d.x,z:a.z-d.z},add(a,d),e)<=(g.widthMetres??0)/2+radius;});
 case 'impactAndStrip':return segment===0?distance(a,e)<=(g.radiusMetres??0)+radius:forward>=-radius&&forward<=(g.lengthMetres??0)+radius&&Math.abs(side)<=(g.widthMetres??0)/2+radius;
 case 'placedStrip':return Math.abs(forward)<=(g.lengthMetres??0)/2+radius&&Math.abs(side)<=(g.widthMetres??0)/2+radius;
 case 'targetVolley':case 'filledWaveRectangle':return Math.abs(forward)<=(g.depthMetres??0)/2+radius&&Math.abs(side)<=(g.widthMetres??0)/2+radius;
 case 'instantCorridor':return forward>=-Math.max(.1,radius-.2)&&forward<=(g.lengthMetres??0)+radius&&Math.abs(side)<=(g.widthMetres??0)/2+radius;
 case 'meleeFan':case 'boundedArcFan':return distance(a,e)<=(g.radiusMetres??0)+radius&&Math.abs(delta(angleTo(a,e),c.angle))<=(g.angleDegrees??0)*Math.PI/360+Math.asin(Math.min(1,Math.max(0,radius-.3)/Math.max(.001,distance(a,e))));
 default:return distance(a,e)<=(g.radiusMetres??c.rank.radiusMetres??0)+radius;}
 }
 private targets(c:CombatCast,segment=0){const from=c.rank.geometry?.origin==='caster'?c.from:c.to;return this.s.enemies.filter(e=>e.hp>0&&this.inside(c,e,segment)&&this.host.visible(from,e)).sort((a,b)=>distance(a,from)-distance(b,from)||a.id.localeCompare(b.id));}
 private finishMeleeFeedback(c:CombatCast,segment:number){
  const intent=this.meleeFeedback.get(c.id);if(!intent||intent.reported)return;intent.reported=true;
  if(c.hits.includes(`${segment}:${intent.id}`)||!this.s.enemies.some(e=>e.id===intent.id&&e.hp>0))return;
  this.host.emit('miss','MISS',{id:intent.id,at:{...intent.at},action:c.id,castId:c.id,skillId:c.skillId,segment,reason:'avoided'});
 }
 /** Reuse the resolved victim set and LOS query. A nearest-edge forest carries
  * each victim's one real hit; local three-neighbour links close the visible mesh
  * without another hit, proc, or target. Bounded sets need no graph dependency. */
 private lightningNetwork(c:CombatCast,enemies:EnemyState[],segment:number,fraction:number,primaryId?:string,followFraction=fraction){
  const nodes=enemies.filter(e=>e.hp>0).map(enemy=>({enemy,id:enemy.id,p:at(enemy)}));if(!nodes.length)return;
  const remaining=new Set(nodes.map(e=>e.id)),connected:typeof nodes=[],pairs=new Set<string>();
  const hop=c.rank.connectionRadiusMetres??c.rank.geometry?.radiusMetres??0;
  const entry=c.skillId==='THU_02'||c.rank.geometry?.origin==='caster'?c.from:c.to;
  const pair=(a:string,b:string)=>[a,b].sort().join('|');
  const connect=(node:typeof nodes[number],from:Point,sourceId?:string)=>{
   this.hit(c,node.enemy,node.id===primaryId?fraction:followFraction,segment,from,sourceId?'network':'connection',sourceId);
   remaining.delete(node.id);connected.push(node);if(sourceId)pairs.add(pair(sourceId,node.id));
  };
  while(remaining.size){
   let best:{from:typeof nodes[number];to:typeof nodes[number];length:number}|undefined;
   for(const from of connected)for(const to of nodes){
    if(!remaining.has(to.id))continue;const length=distance(from.p,to.p);if(length>hop+.001||!this.host.visible(from.p,to.p))continue;
    if(!best||length<best.length-1e-8||Math.abs(length-best.length)<1e-8&&(from.id+'|'+to.id)<(best.from.id+'|'+best.to.id))best={from,to,length};
   }
   if(best){connect(best.to,best.from.p,best.from.id);continue;}
   // Disconnected LOS components each receive one legal entry, never an arc
   // through a wall or a silently enlarged connection radius.
   const roots=nodes.filter(node=>remaining.has(node.id)&&this.host.visible(entry,node.p)).sort((a,b)=>(connected.length?0:Number(b.id===primaryId)-Number(a.id===primaryId))||distance(entry,a.p)-distance(entry,b.p)||a.id.localeCompare(b.id));
   if(!roots.length)break;connect(roots[0],entry);
  }
  const links=new Map<string,{from:typeof nodes[number];to:typeof nodes[number];length:number}>();
  for(const from of connected){
   const neighbours=connected.filter(to=>to.id!==from.id&&distance(from.p,to.p)<=hop+.001&&this.host.visible(from.p,to.p)).sort((a,b)=>distance(from.p,a.p)-distance(from.p,b.p)||a.id.localeCompare(b.id)).slice(0,3);
   for(const to of neighbours){const key=pair(from.id,to.id);if(!pairs.has(key))links.set(key,{from,to,length:distance(from.p,to.p)});}
  }
  // Creator's loose spread transform treats [...Map] as a one-item array.
  // Materialise entries explicitly so the packed game matches native TS.
  for(const [key,edge]of Array.from(links.entries()).sort((a,b)=>a[1].length-b[1].length||a[0].localeCompare(b[0]))){
   if(pairs.size>=nodes.length*2-1)break;pairs.add(key);
   this.event('skill_segment',c,{from:edge.from.p,to:edge.to.p,sourceId:edge.from.id,targetId:edge.to.id,segment,phase:'network'});
  }
 }
 private anchorsHit(c:CombatCast,fraction:number,segment:number){const from=c.rank.geometry?.origin==='caster'?c.from:c.to;for(const anchor of this.host.anchors?.()??[]){const key=`anchor:${segment}:${anchor.id}`;if(c.procs.includes(key)||!this.inside(c,anchor,segment)||!this.host.visible(from,anchor))continue;if(PURE_SKILLS[c.skillId].damageRole==='single'){const victim='anchor:'+anchor.id;if(c.targets.length&&c.targets[0]!==victim)continue;if(!c.targets.length)c.targets.push(victim);}c.procs.push(key);this.host.damageAnchor?.(anchor.id,c.power*c.rank.maxDamagePerTargetS*fraction*c.attributeMultiplier*(1+Math.min(.4,c.damageBonus))*(c.critical?(c.criticalMultiplier??1.5):1),c.id);}}
 private segment(c:CombatCast,n:number){const id=c.skillId,r=c.rank,count=Math.max(1,r.authoredDamageHits);c.nextSegment=n;
 // Every close cut follows the caster's current ground anchor. A later return
 // swing cannot continue damaging the place the player has already left.
 if(r.geometry?.kind==='meleeFan'){c.from=at(this.s.player);c.to=at(c.from);}
 this.event('skill_segment',c,{duration:id==='FIR_05'&&n===0?.3:undefined,phase:r.geometry?.kind.startsWith('melee')?'strike':undefined});
 if(id==='BOW_01'||id==='BOW_02'||id==='BOW_03'||id==='BOW_07'||id==='FIR_01') {const q=this.projectile(c,n,id==='BOW_03'?at(this.s.player):c.from,c.angle,1/count);if(id==='BOW_03'&&c.procs.includes('automatic'))q.targetId=c.targets[0];return;}
 if(id==='BOW_05'){const fraction=[.2,.3,.5][n];for(const target of c.targets){const fixed=c.volleyPoints?.[target];if(fixed){const q=this.projectile(c,n,at(this.s.player),angleTo(c.from,fixed),fraction);q.remaining=distance(c.from,fixed)+.4;q.targetId=target;q.feedbackTargetId=target;q.feedbackTarget=at(fixed);q.feedbackReported=false;q.feedbackActionId=c.id;}}return;}
 if(id==='FIR_05'&&n===0){c.waveProgress=0;return;}
 const fraction=id==='WAR_05'?[.2,.2,.6][n]:id==='FIR_02'&&count===2?(n===0?.75:.25):id==='WAR_04'&&count===2?(n===0?.7:.3):id==='FIR_05'?(n===0?.4:.15):1/count;
 let targets=this.targets(c,n);if(id==='THU_04'||id==='THU_05')targets=targets.filter(e=>c.targets.includes(e.id));if(id==='THU_01')targets=targets.slice(0,r.targetLimit??999);
 if(id==='THU_04'||id==='THU_05')this.lightningNetwork(c,targets,n,fraction);else for(const e of targets)this.hit(c,e,fraction,n,c.rank.geometry?.origin==='caster'?c.from:c.to);
 this.anchorsHit(c,fraction,n);
 if(['WAR_01','WAR_02','WAR_04','WAR_05'].includes(id))this.finishMeleeFeedback(c,n);
 }
 private projectile(c:CombatCast,n:number,from:Point,angle:number,fraction:number,targetId?:string){const d=PURE_SKILLS[c.skillId],r=c.rank,child=!!targetId,range=child?distance(from,c.to):r.castRangeMetres;
 // The volley rectangle selects targets; it is not the width of each arrow.
 const q:ProjectileState={id:this.host.id('skillProjectile'),kind:d.style==='BOW'?'arrow':d.style==='WAR'?'blade':'flame',x:from.x,z:from.z,angle,speed:d.style==='BOW'?COMBAT_RULES.playerProjectileSpeeds.skillArrow:COMBAT_RULES.playerProjectileSpeeds.skillFire,remaining:range,damage:c.power*r.maxDamagePerTargetS*fraction,owner:'player',weapon:c.weapon,hits:[],leg:'out',returning:false,charged:false,pierce:c.skillId==='BOW_01'||c.skillId==='BOW_02'?r.targetLimit??1:d.style==='WAR'?100:1,age:0,skillId:c.skillId,rank:r.rank,castId:c.id,segment:n,from:at(from),previousPosition:at(from),width:c.skillId==='BOW_05'?.3:r.geometry?.widthMetres??.3,targetId,child};
 const forward=(e:Point)=>(e.x-from.x)*Math.sin(angle)+(e.z-from.z)*Math.cos(angle),end=add(from,dir(angle,range));
 const intended=this.s.enemies.filter(e=>e.hp>0&&forward(e)>=0&&forward(e)<=range&&segmentDistance(from,end,e)<=(q.width??.3)/2+enemyHurtRadius(e)&&this.host.visible(from,e)).sort((a,b)=>forward(a)-forward(b)||a.id.localeCompare(b.id))[0];
 if(intended){q.feedbackTargetId=intended.id;q.feedbackTarget=at(intended);q.feedbackReported=false;q.feedbackActionId=c.id;}
 this.s.projectiles.push(q);this.event('skill_segment',c,{projectileId:q.id,segment:n,from:at(from),to:add(from,dir(angle,range)),child});return q;}
 private burn(e:EnemyState,c:CombatCast,fraction=.15){const st=this.status(e),duration=Math.min(4,3+Math.max(this.passive('FIR_P1',c),this.equipped('J01',c)?1:0)+(c.upgrades?.burnSeconds??0));st.burnUntil=this.s.time+duration;st.burnNext=this.s.time+.5;st.burnDamage=c.power*fraction*.5;this.growing.burnApplied(c,e);this.event('skill_status',c,{targetId:e.id,to:at(e),duration,status:'burn'});if(this.passive('FIR_P1',c)&&this.proc(c,'passive:FIR_P1'))this.passiveEvent('FIR_P1',c,e,'burn');}
 private break(c:CombatCast,e:EnemyState,segment=0){if(c.skillId==='WAR_05'&&segment!==c.rank.authoredDamageHits-1)return;const final=this.upgrades.finalBreak(c,segment);if(c.breakHits.includes(e.id)){if(final)this.poise(e,c.rank.breakPower*final/100,c.skillId,c);return;}if(!c.rank.breakPower)return;let value=c.rank.breakPower*(1+(this.upgrades.breakPercent(c,e,segment)+final)/100);c.breakHits.push(e.id);const boss=!!e.bossId||e.kind==='captain';if(this.equipped('W03',c)&&(boss||e.kind==='shield')&&['WAR_01','WAR_04','BOW_01','FIR_02','THU_01'].includes(c.skillId)&&this.proc(c,'W03',3))value+=boss?2:4;if(this.equipped('W07',c)&&c.skillId==='BOW_01'&&e.kind==='shield'&&this.proc(c,'W07'))value+=4;if(this.equipped('W13',c)&&c.breakHits.length===1&&c.skillId==='THU_01'&&this.status(e).hunterMarkUntil>this.s.time&&this.proc(c,'W13',4))value+=boss?2:4;if(this.equipped('DR2-03',c)&&c.breakHits.length===1&&(boss||e.kind==='shield')&&c.skillId==='FIR_01'&&this.proc(c,'DR2-03',6))value+=boss?2:4;if(this.equipped('DE05',c)&&c.skillId==='WAR_04'&&this.mechanical(e)&&this.proc(c,'DE05',6))value+=boss?3:6;if((this.c.buffs.dashBreak??0)>this.s.time){value+=boss?1.5:3;delete this.c.buffs.dashBreak;}if(this.s.flags.counter_ready&&PURE_SKILLS[c.skillId].style==='WAR'){value+=4;this.s.flags.counter_ready=false;}
 if(this.equipped('DU1-03',c)&&PURE_SKILLS[c.skillId].style==='WAR'&&this.mechanical(e)&&this.proc(c,'DU1-03',3))value+=boss?1:2;if(c.skillId==='WAR_02'&&(this.c.buffs.crossBreak??0)>this.s.time){value+=boss?2:4;delete this.c.buffs.crossBreak;}
 this.poise(e,value,c.skillId,c);
 }
 private poise(e:EnemyState,value:number,skillId:string,c?:CombatCast){
 const boss=!!e.bossId||e.kind==='captain';
 const key=`poise:${e.id}`,protectedUntil=this.c.buffs[`poiseProtected:${e.id}`]??0;if(protectedUntil>this.s.time)return;this.c.buffs[key]=(this.c.buffs[key]??0)+value;this.host.emit('poise',undefined,{id:e.id,value,skillId:skillId});
 if(!boss){const breaks=['WAR_01','WAR_04','BOW_01','FIR_02','THU_01','BASIC_FINISH'].includes(skillId);if(breaks&&this.ready(`open:${e.id}`)){const canInterrupt=enemyCanInterrupt(e),interrupted=['windup','active'].includes(e.phase)&&canInterrupt,moveId=e.combat?.moveId,profile=enemyProfile(e),guardSeconds=profile?.defense?.breakOpenSeconds??(e.kind==='shield'?2:0),openSeconds=skillId==='BASIC_FINISH'?Math.min(guardSeconds,COMBAT_TACTICS.finisherOpenSeconds):guardSeconds;
 if(canInterrupt){if(e.combat&&openSeconds>0){e.combat.guardOpenUntil=this.s.time+openSeconds;this.host.emit('guard_break',tacticsText('guardBreak'),{id:e.id,at:at(e),skillId,duration:openSeconds,until:e.combat.guardOpenUntil});}e.phase='stagger';e.phaseTime=Math.max(openSeconds,.5);if(interrupted)this.host.emit('interrupt',tacticsText('interrupt'),{id:e.id,at:at(e),skillId,moveId,duration:e.phaseTime});this.c.cooldowns[`open:${e.id}`]=5;}
 if(interrupted&&c&&this.equipped('DE01',c)&&this.proc(c,'DE01',8))this.c.buffs.interruptNextDamage=this.s.time+3;if(skillId==='WAR_01'&&e.kind==='shield'&&c&&this.equipped('DR4-03',c))this.c.buffs.crossBreak=this.s.time+3;}}
 else if(this.c.buffs[key]>=100&&(!['windup','active'].includes(e.phase)||enemyProfile(e)?.route==='profile'&&enemyCanInterrupt(e))){const moveId=e.combat?.moveId,interrupted=['windup','active'].includes(e.phase);this.c.buffs[key]=0;e.phase='stagger';e.phaseTime=.8;this.c.buffs[`poiseProtected:${e.id}`]=this.s.time+8.8;if(interrupted)this.host.emit('interrupt',tacticsText('interrupt'),{id:e.id,at:at(e),skillId,moveId,duration:.8,boss:true});this.host.emit('stagger',tacticsText('stagger'),{id:e.id,at:at(e),value:.8,duration:.8,boss:true});}
 }
 private mechanical(e:EnemyState){const profile=enemyProfile(e);return profile?profile.body==='machine':/R2|U2|钟|machine|mechan/i.test(e.templateId??e.contentId??'');}
 private contact(action:string,e:EnemyState,accuracy:number,c?:CombatCast){
  const hit=`accuracy:hit:${e.id}`,miss=`accuracy:miss:${e.id}`;if(c?.procs.includes(miss))return false;if(c?.procs.includes(hit))return true;
  const result=rollContactHit(this.s.seed,action,e.id,accuracy,enemyCombatAttributes(e).evasion);c?.procs.push(result.landed?hit:miss);
  if(!result.landed){if(this.host.miss)this.host.miss(e,action,result.chance,result.roll);else this.host.emit('miss','MISS',{id:e.id,action,reason:'accuracy',chance:result.chance,roll:result.roll,at:at(e)});return false;}return true;
 }
 private hit(c:CombatCast,e:EnemyState,fraction:number,segment:number,from=c.from,phase='connection',sourceId?:string){const key=`${segment}:${e.id}`;if(e.hp<=0||c.hits.includes(key))return;
 const d=PURE_SKILLS[c.skillId];
 // A single-target cast retains its first real contact across every beat. A
 // killed or evading victim never lets the remaining beats spill to a neighbour.
 if(d.damageRole==='single'){if(!c.targets.length)c.targets.push(e.id);if(c.targets[0]!==e.id)return;}
 const intent=this.meleeFeedback.get(c.id);if(intent?.id===e.id)intent.reported=true;if(!this.contact(c.id,e,c.accuracy??playerCombatAttributes(this.s).accuracy,c))return;c.hits.push(key);const st=this.status(e),marked=st.hunterMarkUntil>this.s.time,burning=st.burnUntil>this.s.time;let bonus=c.damageBonus+this.growing.bonus(c)+this.upgrades.damage(c,e,segment);
 if(d.style==='WAR')bonus+=this.passive('WAR_P1',c)/100;if(d.style==='BOW'&&distance(c.from,e)>5)bonus+=this.passive('BOW_P1',c)/100;if(marked)bonus+=st.hunterMarkBonus/100;if(this.equipped('A02',c)&&distance(c.from,e)>5)bonus+=.06;if(marked&&this.equipped('J02',c))bonus+=.06;if(this.equipped('W16',c)&&(d.style==='FIR'||d.style==='THU'))bonus+=.05;if(this.equipped('W05',c)&&c.skillId==='WAR_04'&&segment===c.rank.authoredDamageHits-1)bonus+=.1;if(this.equipped('L02',c)&&c.skillId==='BOW_01')bonus+=.1;
 if(d.style==='WAR'&&this.passive('WAR_P1',c)&&this.proc(c,'passive:WAR_P1'))this.passiveEvent('WAR_P1',c,e);if(d.style==='BOW'&&distance(c.from,e)>5&&this.passive('BOW_P1',c)&&this.proc(c,'passive:BOW_P1'))this.passiveEvent('BOW_P1',c,e);if(c.procs.includes('passive-ready:THU_P1')&&this.proc(c,'passive:THU_P1'))this.passiveEvent('THU_P1',c,e);
 if(marked&&d.type!=='ultimate'&&(d.style==='FIR'||d.style==='THU')&&this.equipped('DE08',c)&&this.proc(c,'DE08',10))bonus+=.08;
 const critical=c.critical||!!(c.upgrades?.stationary&&marked&&segment===0&&c.criticalRoll!==undefined&&c.criticalRoll<Math.min(.3,(c.criticalChance??.05)+(c.upgrades.markedCritical??0)/100));let damage=c.power*c.rank.maxDamagePerTargetS*fraction*c.attributeMultiplier*(1+Math.min(.4,bonus))*(critical?(c.criticalMultiplier??1.5):1);this.break(c,e,segment);const before=e.hp;this.host.damage(e,damage,c.id,d.style,distance(from,e)>.01?angleTo(from,e):c.angle,critical);if(d.style==='THU')this.event('skill_segment',c,{targetId:e.id,to:at(e),from:at(from),segment,phase,sourceId});this.event('skill_hit',c,{targetId:e.id,to:at(e),from:at(from),segment,value:Math.min(before,Math.round(damage)),critical});this.addCharge(c);this.upgrades.hit(c,e,segment);
 this.growing.hit(c,e);
 this.automaticEnhancements(c,e);
 if((c.skillId==='FIR_01'||c.skillId==='FIR_02'&&this.equipped('W12',c)&&segment===0)&&e.hp>0)this.burn(e,c);
 if(d.style==='BOW'){if(this.passive('BOW_P2',c)&&this.ready('BOW_P2')){this.c.buffs.bowSpeed=this.passive('BOW_P2',c)/100;this.c.buffs.bowSpeedUntil=this.s.time+(this.upgrades.passive(c,'BOW_P2').speedSeconds??2);this.c.buffs.bowMovingBasic=this.upgrades.passive(c,'BOW_P2').movingBasicPercent??0;this.c.cooldowns.BOW_P2=5;this.passiveEvent('BOW_P2',c,undefined,'speed');}if((this.equipped('W08',c)||this.equipped('DE02',c))&&this.ready('bowEquipSpeed')){this.c.buffs.bowEquipSpeedUntil=this.s.time+2;this.c.cooldowns.bowEquipSpeed=this.equipped('W08',c)?4:5;}}
 if(d.style==='THU'&&this.passive('THU_P2',c)&&(new Set(c.hits.map(k=>k.slice(k.indexOf(':')+1))).size>=(this.upgrades.passive(c,'THU_P2').enemyThreshold??3)||this.upgrades.passive(c,'THU_P2').eliteSatisfies&&(!!e.bossId||e.kind==='captain'))&&this.proc(c,'THU_P2',10)){this.shield(this.s.player.maxHp*this.passive('THU_P2',c)/100,3);this.passiveEvent('THU_P2',c,undefined,'shield');}
 if(d.style==='FIR'&&d.damageRole!=='single'&&e.hp<=0&&this.passive('FIR_P2',c)&&this.proc(c,'FIR_P2',6))for(const next of this.s.enemies.filter(n=>n.hp>0&&distance(n,e)<=(this.upgrades.passive(c,'FIR_P2').spreadRadius??3)&&this.host.visible(e,n)).sort((a,b)=>distance(a,e)-distance(b,e)||a.id.localeCompare(b.id)).slice(0,this.upgrades.passive(c,'FIR_P2').spreadTargets??2)){this.burn(next,c,this.passive('FIR_P2',c));this.passiveEvent('FIR_P2',c,next,'burn',e);}
 if(this.equipped('W02',c)&&d.style==='WAR'&&this.proc(c,'count:W02')){this.s.effectCounters.oath=(this.s.effectCounters.oath??0)+1;if(this.s.effectCounters.oath%3===0)this.secondary(c,'W02',e,4,2);}
 if(this.equipped('W04',c)&&c.skillId==='WAR_02'&&new Set(c.hits.map(k=>k.slice(k.indexOf(':')+1))).size>=2&&this.proc(c,'W04',8))this.c.buffs.crossNextDamage=this.s.time+4;
 if(this.equipped('W06',c)&&d.type==='active'&&marked&&this.proc(c,'W06',10))this.shield(8,3);
 if(this.equipped('W09',c)&&c.skillId==='BOW_01'&&this.proc(c,'W09',8)){const percent=e.bossId||e.kind==='captain'?.1:.25;if(st.slowUntil<=this.s.time||percent>=st.slowPercent){st.slowPercent=percent;st.slowUntil=Math.max(st.slowUntil,this.s.time+3);}}
 if(this.equipped('W10',c)&&c.skillId==='BOW_03'&&this.ready('secondary:W10')&&!c.procs.includes('secondary:W10')){this.secondary(c,'W10',e,c.power*.5,8);}
 if(this.equipped('W14',c)&&c.skillId==='THU_01')this.secondary(c,'W14',e,c.power*.35,8);
 if(this.equipped('A08',c)&&d.style==='THU'&&marked&&this.proc(c,'A08',8)){const longest=Object.keys(this.c.cooldowns).filter(id=>PURE_SKILLS[id]&&PURE_SKILLS[id].type!=='ultimate').sort((a,b)=>this.c.cooldowns[b]-this.c.cooldowns[a])[0];if(longest)this.c.cooldowns[longest]=Math.max(0,this.c.cooldowns[longest]-.5);}
 if(this.equipped('A11',c)&&(d.style==='FIR'||d.style==='THU')&&this.proc(c,'count:A11')){const old=this.c.buffs.lastSpellId;const code=Object.keys(PURE_SKILLS).indexOf(c.skillId)+1;if(old&&old!==code&&this.ready('A11')){this.c.buffs.nextDamage=this.s.time+4;this.c.cooldowns.A11=6;}this.c.buffs.lastSpellId=code;}
 if(d.type==='active'&&marked&&(this.equipped('J03',c)&&this.proc(c,'J03',3)||this.equipped('DU2-03',c)&&this.proc(c,'DU2-03',4)))this.addCharge(c,true);
 if(this.equipped('DR1-04',c)&&distance(c.from,e)>5&&this.proc(c,'DR1-04',4))this.addCharge(c,true);if(this.equipped('DR3-03',c)&&d.style==='WAR'&&burning&&this.proc(c,'DR3-03',3))this.addCharge(c,true);
 if(this.equipped('J05',c)&&d.style==='THU'&&burning&&this.ready('secondary:J05')){if(this.secondary(c,'J05',e,c.power*.35,8))st.burnUntil=0;}
 if(this.equipped('J07',c)&&this.ready('J07')){const token=`lastSkill:${e.id}`,code=Object.keys(PURE_SKILLS).indexOf(c.skillId)+1;if(this.c.buffs[token]&&this.c.buffs[token]!==code&&(this.c.buffs[`${token}:until`]??0)>this.s.time){this.shield(6,3);this.c.cooldowns.J07=10;}this.c.buffs[token]=code;this.c.buffs[`${token}:until`]=this.s.time+6;}
 if(this.equipped('DR3-04',c)&&d.style==='THU'&&this.proc(c,'DR3-04',8))this.c.buffs.nextBasicUntil=this.s.time+4;
 if(this.equipped('DU2-04',c)&&c.skillId==='BOW_01'&&marked)this.secondary(c,'DU2-04',e,4,4);
 if(this.equipped('DU1-04',c)&&(d.style==='FIR'||d.style==='THU')&&this.proc(c,'count:DU1-04')){this.s.effectCounters.spell=(this.s.effectCounters.spell??0)+1;if(this.s.effectCounters.spell%3===0)this.secondary(c,'DU1-04',e,4,3);}
 if(this.equipped('DE06',c)&&d.style==='WAR'&&this.proc(c,'count:DE06')){this.s.effectCounters.war=(this.s.effectCounters.war??0)+1;if(this.s.effectCounters.war%3===0&&this.proc(c,'DE06',8))this.shield(4,3);}
 if(this.equipped('DR1-03',c)&&['WAR_01','WAR_04','BOW_01','FIR_02','THU_01'].includes(c.skillId)&&this.proc(c,'DR1-03',6))this.c.buffs.breakNextDamage=this.s.time+3;
 if(this.equipped('L01',c)&&c.skillId==='WAR_01'&&st.lightningUntil>this.s.time&&c.procs.filter(k=>k.startsWith('legend:')).length<2){st.lightningUntil=0;c.procs.push(`legend:${e.id}`);this.secondary(c,`L01:${e.id}`,e,c.power*.3);}
 this.host.changed();
 }
 /** Enhancements have one shared source and trigger only after real contact. */
 private automaticEnhancements(c:CombatCast,e:EnemyState){
  const d=PURE_SKILLS[c.skillId],p=this.s.progression,time=this.s.time;
  if(d.style==='BOW'&&c.skillId==='BOW_01'){
   const r=allocatedSkillRank(p,'BOW_03');
   if(r&&this.ready('BOW_03')&&this.proc(c,'enhancement:BOW_03')){
    this.c.buffs.bowVolleyReadyUntil=time+5;this.c.buffs.bowVolleyRank=r.rank;
    this.c.cooldowns.BOW_03=this.cooldownFor(PURE_SKILLS.BOW_03,r);
    this.event('skill_status',c,{skillId:'BOW_03',rank:r.rank,status:'ready',duration:5});
   }
  }
  if(d.style==='BOW'&&d.activation!=='automatic'&&c.skillId!=='BOW_06'&&c.upgrades?.stationary&&e.hp>0){
   const r=allocatedSkillRank(p,'BOW_04'),key=r?'BOW_04':'autoMark';
   if((r||this.passive('BOW_P1',c))&&this.ready(key)&&this.proc(c,'enhancement:BOW_04')){
    const st=this.status(e),seconds=r?(r.upgradeEffects?.markSeconds??8):6;
    st.hunterMarkUntil=time+seconds;st.hunterMarkBonus=r?.markedDirectSkillBonusPercent??this.upgrades.passive(c,'BOW_P1').hunterMarkPercent??8;e.markedUntil=st.hunterMarkUntil;
    this.c.cooldowns[key]=r?this.cooldownFor(PURE_SKILLS.BOW_04,r):6;
    this.upgrades.mark(r?{...c,skillId:'BOW_04',rank:r}:c,e);
    this.event('skill_status',c,{skillId:r?'BOW_04':'BOW_P1',rank:r?.rank??1,status:'hunterMark',targetId:e.id,to:at(e),duration:seconds});
   }
  }
  if(d.style==='THU'&&(c.procs.includes('enhancement-ready:THU_03')||c.procs.includes('passive-ready:THU_P1'))&&this.proc(c,'enhancement:thunderWeapon')){
   const r=allocatedSkillRank(p,'THU_03');
   if(r&&this.ready('THU_03')){
    this.thunderWeapon(c,3,r);this.c.cooldowns.THU_03=this.cooldownFor(PURE_SKILLS.THU_03,r);
    this.event('skill_status',c,{skillId:'THU_03',rank:r.rank,status:'thunderWeapon',duration:r.upgradeEffects?.buffSeconds??6});
   }else if(!r){this.thunderWeapon(c,1);this.passiveEvent('THU_P1',c,undefined,'thunderWeapon');}
  }
 }
 /** The follow-up uses the existing real projectile path and one damage budget. */
 private automaticVolley(e:EnemyState,angle:number){
  const s=this.s,b=this.c.buffs;if((b.bowVolleyReadyUntil??0)<=s.time)return;
  b.bowVolleyReadyUntil=0;
  const r=allocatedSkillRank(s.progression,'BOW_03');if(!r||e.hp<=0)return;
  const equipment=Object.values(s.equipment).filter((id):id is string=>typeof id==='string'),id=this.host.id('autoVolley'),chance=combatCriticalChance(s),roll=random(s.seed,`${id}:crit`);
  const c:CombatCast={id,skillId:'BOW_03',rank:copy(r),from:at(s.player),to:at(e),angle,elapsed:0,released:true,nextSegment:0,targets:[e.id],hits:[],breakHits:[],critical:roll<chance,criticalChance:chance,criticalRoll:roll,criticalMultiplier:combatCriticalMultiplier(s),accuracy:playerCombatAttributes(s).accuracy,power:skillPower(s.progression)*equipmentPowerMultiplier(s.equipment.weapon,s.progression.level)*(1+equippedGearBonus(s).power/100),attributeMultiplier:1+.008*(effectiveAttribute(s,'dexterity')-10),damageBonus:0,chargeGranted:false,chargeBonus:0,procs:['automatic'],equipment,passives:Object.fromEntries(this.c.passiveSlots.filter((v):v is string=>!!v).map(v=>[v,this.passive(v)])),weapon:s.equipment.weapon,growthLevel:s.progression.level,releaseTime:s.time};
  this.upgrades.prepare(c);this.c.casts.push(c);this.event('skill_release',c,{phase:'automatic'});this.segment(c,0);c.nextSegment=1;
 }
 basicHit(e:EnemyState,base:number,action:string,angle:number,accuracy=playerCombatAttributes(this.s).accuracy):boolean{if(!this.contact(action,e,accuracy))return false;const key=`basic:${action}`,kind=EQUIPMENT[this.s.equipment.weapon]?.kind,attr=kind==='sword'?'strength':kind==='bow'?'dexterity':'intellect';let bonus=this.upgrades.basic(action);if((this.c.buffs.basicBonusUntil??0)>this.s.time){bonus+=.12;delete this.c.buffs.basicBonusUntil;}if((this.c.buffs.nextBasicUntil??0)>this.s.time){bonus+=.06;delete this.c.buffs.nextBasicUntil;}const critical=random(this.s.seed,`${action}:crit`)<combatCriticalChance(this.s);if(kind==='sword'&&this.s.action?.id===action&&this.s.action.comboStage===3)this.poise(e,COMBAT_TACTICS.finisherPoise,'BASIC_FINISH');this.host.damage(e,base*(1+.008*(effectiveAttribute(this.s,attr)-10))*(1+Math.min(.4,bonus))*(critical?combatCriticalMultiplier(this.s):1),action,kind==='staff'?weaponCombatFamily(this.s.equipment.weapon,this.c):'basic',angle,critical);
 if(!this.s.receipts[key]){this.s.receipts[key]=true;if(kind==='bow')this.automaticVolley(e,angle);if((this.c.buffs.thunderUntil??0)>this.s.time&&(this.c.buffs.thunderCharges??0)>0){this.c.buffs.thunderCharges--;if(this.c.buffs.thunderCharges===0&&this.c.buffs.thunderSource===3)this.upgrades.thunderThird(e);this.host.damage(e,this.c.buffs.thunderDamage,action,'secondary',angle);this.host.emit('skill_hit',undefined,{skillId:this.c.buffs.thunderSource===3?'THU_03':'THU_P1',family:'THU',rank:this.c.buffs.thunderRank,castId:action,shape:'selfBuff',from:at(e),to:at(e),targetId:e.id,segment:3-this.c.buffs.thunderCharges});}if(this.equipped('L01')&&kind==='sword'&&random(this.s.seed,`${action}:legend`)<.22)this.status(e).lightningUntil=this.s.time+7;}return true;
 }
 /** Freeze only the next leg on an actual contact. The original arrow ID,
  * hit ledger and total victim cap survive each turn; nothing is spawned. */
 private redirectArrow(c:CombatCast,q:ProjectileState,firstContact:Point):boolean {
  q.chainOrigin??=at(firstContact);if(q.hits.length>=(c.rank.targetLimit??1))return false;
  const radius=c.rank.geometry?.radiusMetres??c.rank.connectionRadiusMetres??0;
  const target=this.s.enemies.filter(e=>e.hp>0&&!q.hits.includes(e.id)&&distance(e,q.chainOrigin!)<=radius+.001&&distance(q,e)>.02&&this.host.visible(q,e)).sort((a,b)=>distance(q,a)-distance(q,b)||a.id.localeCompare(b.id))[0];
  if(!target)return false;
  const from=at(q),to=at(target),angle=angleTo(from,to),length=distance(from,to),middle={x:(from.x+to.x)/2,z:(from.z+to.z)/2};
  const bend=dir(angle+Math.PI/2,(q.hits.length%2?1:-1)*Math.min(.28,length*.07));
  q.from=from;q.target=to;q.targetId=target.id;q.child=false;q.segment=q.hits.length;q.angle=angle;
  q.feedbackTargetId=target.id;q.feedbackTarget=at(to);q.feedbackActionId=c.id;q.feedbackReported=false;delete q.feedbackFailure;
  q.frozenPath=[from,add(middle,bend),to];q.pathLength=length*1.02;q.pathProgress=0;q.remaining=q.pathLength;
  this.event('skill_segment',c,{projectileId:q.id,segment:q.segment,from,to,targetId:target.id,child:false,phase:'redirect'});return true;
 }
 projectileStep(q:ProjectileState,dt:number){if(!q.skillId)return false;const c=this.c.casts.find(c=>c.id===q.castId);if(!c){q.remaining=0;return true;}q.age+=dt;const before=at(q);q.previousPosition=before;let next=add(q,dir(q.angle,Math.min(q.remaining,q.speed*dt)));
 if(q.frozenPath){q.pathProgress=Math.min(1,(q.pathProgress??0)+dt*q.speed/(q.pathLength??1));const t=q.pathProgress,from=q.frozenPath[0],control=q.frozenPath[1],end=q.frozenPath[2];next={x:(1-t)**2*from.x+2*(1-t)*t*control.x+t*t*end.x,z:(1-t)**2*from.z+2*(1-t)*t*control.z+t*t*end.z};q.angle=angleTo(before,next);q.remaining=q.pathProgress>=1?0:Math.max(.001,(q.pathLength??1)*(1-t));}else q.remaining=Math.max(0,q.remaining-q.speed*dt);
 if(!this.host.visible(before,next)){q.remaining=0;q.feedbackFailure='blocked';if(q.skillId==='FIR_01')this.impactFire(c,before,q.segment??0);return true;}q.x=next.x;q.z=next.z;
 const targets=this.s.enemies.filter(e=>e.hp>0&&!q.hits.includes(e.id)&&(q.skillId==='BOW_02'?(!q.chainOrigin||distance(e,q.chainOrigin)<=(c.rank.geometry?.radiusMetres??0)+.001):(!q.targetId||q.targetId===e.id))&&segmentDistance(before,q,e)<=(q.width??.3)/2+enemyHurtRadius(e)&&this.host.visible(before,e)).sort((a,b)=>distance(a,before)-distance(b,before)||a.id.localeCompare(b.id));
 const anchor=(this.host.anchors?.()??[]).filter(h=>!q.hits.includes(h.id)&&segmentDistance(before,q,h)<=(q.width??.3)/2+h.radius&&this.host.visible(before,h)).sort((a,b)=>distance(a,before)-distance(b,before)||a.id.localeCompare(b.id))[0];
 if(anchor&&(!targets.length||distance(before,anchor)<distance(before,targets[0]))){q.hits.push(anchor.id);this.host.damageAnchor?.(anchor.id,q.damage*c.attributeMultiplier*(1+Math.min(.4,c.damageBonus))*(c.critical?(c.criticalMultiplier??1.5):1),c.id);if(q.skillId==='FIR_01')this.impactFire(c,anchor,q.segment??0);q.remaining=0;return true;}
 for(const e of targets){q.hits.push(e.id);if(q.skillId==='FIR_01'){this.impactFire(c,e,q.segment??0,e);q.remaining=0;break;}const fraction=q.damage/(c.power*c.rank.maxDamagePerTargetS);let attenuation=1;if(q.skillId==='BOW_01')attenuation=Math.max(this.equipped('L02',c)?.7:.6,1-.2*(q.hits.length-1));if(q.skillId==='BOW_02'&&q.hits.length>1)attenuation=c.rank.followUpDamageFraction??.75;this.hit(c,e,fraction*attenuation,q.segment??0,before);
 if(q.skillId==='BOW_02'){q.feedbackReported=true;if(!c.hits.includes(`${q.segment??0}:${e.id}`)||!this.redirectArrow(c,q,e))q.remaining=0;break;}
 if(q.hits.length>=q.pierce){q.remaining=0;break;}}
 if(q.remaining<=0&&q.skillId==='FIR_01'&&!q.hits.length)this.impactFire(c,q,q.segment??0);return true;
 }
 private impactFire(c:CombatCast,center:Point,segment:number,direct?:EnemyState){
  const targets=PURE_SKILLS[c.skillId].damageRole==='single'?(direct&&direct.hp>0?[direct]:[]):this.s.enemies.filter(e=>e.hp>0&&distance(center,e)<=(c.rank.geometry?.radiusMetres??.45)+enemyHurtRadius(e)&&this.host.visible(center,e)).sort((a,b)=>distance(a,center)-distance(b,center)||a.id.localeCompare(b.id));
  for(const e of targets)this.hit(c,e,1,segment,center);this.event('skill_segment',c,{from:at(center),to:at(center),phase:'impact'});
 }
 step(dt:number){const s=this.s,c=this.c,b=c.buffs;this.growing.step();this.upgrades.step(dt);this.c.ultimateLock=Math.max(0,this.c.ultimateLock-dt);this.zones();for(const key of Object.keys(c.cooldowns))c.cooldowns[key]=Math.max(0,c.cooldowns[key]-dt);
 if(s.flags.counter_ready&&(b.counterReadyUntil??0)<s.time)s.flags.counter_ready=false;
 if((b.shieldUntil??0)<=s.time){if((b.ironShield??0)>0&&this.equipped('DE07')&&(b.ironAbsorbed??0)>0)b.basicBonusUntil=s.time+4;delete b.ironShield;b.shieldAmount=0;s.player.shield=0;}else b.shieldAmount=s.player.shield;
 if((b.healCount??0)>0&&s.time+1e-8>=(b.healNext??0)){const first=b.healFirstFraction??1/3,fraction=b.healCount===3?first:(1-first)/2,emergency=b.healCount===1&&s.player.hp<s.player.maxHp*.5?s.player.maxHp*(b.healEmergency??0)/100:0,amount=restorePlayerHealth(s,b.healAmount*fraction+emergency);b.healCount--;b.healNext+=1;this.host.emit('heal',undefined,{value:amount});this.host.emit('skill_status',undefined,{skillId:'COM_02',family:'COM',rank:b.healRank,castId:'heal',shape:'selfHeal',from:at(s.player),to:at(s.player),segment:3-b.healCount,duration:.35,status:'heal'});}
 for(const e of s.enemies){const st=c.statuses[e.id];if(!st||e.hp<=0)continue;if(st.burnUntil>s.time&&s.time+1e-8>=st.burnNext){this.host.damage(e,st.burnDamage,'burn','burn',0);st.burnNext+=.5;}e.markedUntil=st.hunterMarkUntil;}
 for(const cast of c.casts){if(!cast.procs.includes('automatic')&&(cast.rank.geometry?.kind==='meleeFan'||cast.rank.geometry?.kind==='meleeRushCross'||combatActionBeatCount(cast)>1)&&s.action?.id!==cast.id){cast.nextSegment=cast.rank.authoredDamageHits;continue;}if(!cast.released||cast.rush&&cast.rush.elapsed<cast.rush.duration||cast.skillId==='COM_01'||cast.skillId==='BOW_06'||cast.rank.authoredDamageHits===0||cast.skillId==='BOW_04'||cast.skillId==='THU_02')continue;const elapsed=s.time-(cast.releaseTime??s.time);if(cast.skillId==='FIR_05'&&(cast.waveProgress??1)<1){const progress=Math.min(1,elapsed/.3),depth=cast.rank.geometry?.depthMetres??1;for(const e of this.targets(cast)){const forward=(e.x-cast.to.x)*Math.sin(cast.angle)+(e.z-cast.to.z)*Math.cos(cast.angle);if((forward+depth/2)/depth<=progress)this.hit(cast,e,.4,0,cast.to);}cast.waveProgress=progress;}const count=cast.rank.authoredDamageHits,interval=combatSegmentInterval(cast.skillId,cast.rank);if(cast.nextSegment<count&&elapsed+1e-8>=cast.nextSegment*interval){this.segment(cast,cast.nextSegment);cast.nextSegment++;}}
 c.casts=c.casts.filter(cast=>s.action?.id===cast.id||s.projectiles.some(q=>q.castId===cast.id)||(cast.zoneUntil??0)>s.time||cast.released&&cast.nextSegment<cast.rank.authoredDamageHits&&cast.skillId!=='BOW_04'&&cast.skillId!=='THU_02');
 for(const id of this.meleeFeedback.keys())if(!c.casts.some(cast=>cast.id===id))this.meleeFeedback.delete(id);
 }
 speedMultiplier(){let bonus=this.upgrades.speed();if((this.c.buffs.stormWardUntil??0)>this.s.time)bonus+=this.c.buffs.stormWardSpeed??0;if((this.c.buffs.bowSpeedUntil??0)>this.s.time)bonus+=this.c.buffs.bowSpeed??0;if((this.c.buffs.bowEquipSpeedUntil??0)>this.s.time)bonus+=.08;return 1+Math.min(.3,bonus);}
 enemySpeed(e:EnemyState){if((this.c.buffs[`rootUntil:${e.id}`]??0)>this.s.time)return 0;const st=this.c.statuses[e.id];return st&&st.slowUntil>this.s.time?1-st.slowPercent:1;}
 consumeDirectWard(ground:boolean){const b=this.c.buffs;if(ground||(b.stormWardUntil??0)<=this.s.time||!(b.stormWardReduction>0))return 0;const value=b.stormWardReduction;b.stormWardReduction=0;this.host.emit('skill_status',undefined,{skillId:'THU_06',family:'THU',rank:allocatedSkillRank(this.s.progression,'THU_06')?.rank??1,castId:'stormWardHit',shape:'selfBuff',from:at(this.s.player),segment:0,duration:.2,status:'wardHit'});return value;}
 reduction(fire=false){let n=fire?0:this.upgrades.reduction();if(!fire&&(this.s.player.shield>0||(this.c.buffs.passiveBrokenUntil??0)>this.s.time)){n+=this.passive('WAR_P2')/100;if(this.passive('WAR_P2'))this.host.emit('skill_status',undefined,{skillId:'WAR_P2',family:'WAR',rank:allocatedSkillRank(this.s.progression,'WAR_P2')?.rank,castId:'defense',shape:'selfShield',from:at(this.s.player),to:at(this.s.player),segment:0,duration:.25,status:'shield'});}if(!fire&&(this.c.buffs.ironDefense??0)>this.s.time)n+=.06;if(fire){if(this.equipped('A03'))n+=.1;if(this.equipped('DR3-01'))n+=.06;if(this.equipped('DU1-01'))n+=.06;}else {if(this.equipped('DR1-02'))n+=.04;if(this.equipped('DR4-02'))n+=.05;}return n;}
 absorbed(amount:number){this.upgrades.shieldAbsorbed(amount);if((this.c.buffs.ironShield??0)>this.s.time)this.c.buffs.ironAbsorbed=(this.c.buffs.ironAbsorbed??0)+amount;if(amount>0&&this.c.buffs.shieldSkill){const id=this.c.buffs.shieldSkill===1?'WAR_03':'FIR_03';this.host.emit('skill_status',undefined,{skillId:id,family:id.slice(0,3),rank:this.c.buffs.shieldRank,castId:'shieldHit',shape:'selfShield',from:at(this.s.player),to:at(this.s.player),segment:0,duration:.15,status:'shieldHit'});}}
 afterHurt(fire:boolean){if(fire&&this.equipped('A07')&&this.ready('A07')){this.c.cooldowns.A07=8;this.shield(5,3);}if(this.equipped('DR4-04')&&this.s.player.hp>0&&this.s.player.hp/this.s.player.maxHp<.35&&this.ready('DR4-04')){this.c.cooldowns['DR4-04']=20;this.shield(8,4);}}
 resetTransient(){this.upgrades.reset();this.meleeFeedback.clear();this.c.casts=[];this.c.statuses={};this.c.buffs={};this.c.growingPending=[];this.s.player.shield=0;}
}

// Exact prior fan reaches are accepted only for already-saved transient casts.
// Restore clears these casts; damage, angles, timing and every other field must
// still match the current authored rank, so this cannot authorize forged damage.
const PRIOR_MELEE_REACH:Record<string,readonly number[]>={WAR_01:[2.4,2.4,2.54,2.64,2.76],WAR_05:[3.5,3.5,3.71,3.85,4.02]};
function acceptedRankSnapshot(id:string,rank:CombatSkillRank,version=5){
 const current=combatSkillCatalog(version)[id]?.ranks[rank.rank-1];if(!current)return false;
 if(JSON.stringify(rank)===JSON.stringify(current))return true;
 const old=PRIOR_MELEE_REACH[id]?.[rank.rank-1];if(old===undefined||rank.rangeMetres!==old||rank.castRangeMetres!==old||rank.geometry?.kind!=='meleeFan'||rank.geometry.radiusMetres!==old)return false;
 const normalized={...rank,rangeMetres:current.rangeMetres,castRangeMetres:current.castRangeMetres,geometry:{...rank.geometry,radiusMetres:current.geometry?.radiusMetres}};
 return JSON.stringify(normalized)===JSON.stringify(current);
}
export function validateCombat(value:unknown,progression:number|ProgressionState,gearPower:Record<string,number>={},gearStats:Record<string,Partial<RandomForgingBonus>>={}){const level=typeof progression==='number'?progression:progression.level;const c=value as CombatState,legacy=c?.version===2,catalog=combatSkillCatalog(c?.version),fail=()=>{throw new Error('无效的纯技能存档');};if(!c||![2,3,4,5].includes(c.version)||!Array.isArray(c.activeSlots)||c.activeSlots.length!==(c.version===3?3:4)||!Array.isArray(c.passiveSlots)||c.passiveSlots.length!==2||!Number.isFinite(c.charge)||c.charge<0||c.charge>100||!Number.isFinite(c.ultimateLock)||c.ultimateLock<0||c.ultimateLock>45)return fail();
 if(!validateCombatLoadouts(c,legacy,progression))return fail();
 if(c.engagement!==undefined){const e=c.engagement;if(!e||typeof e!=='object'||Array.isArray(e)||Object.keys(e).some(k=>!['area','enemyIds','quietSince'].includes(k))||typeof e.area!=='string'||e.area.length>100||!Array.isArray(e.enemyIds)||e.enemyIds.length>2000||e.enemyIds.some(id=>typeof id!=='string'||id.length>180)||new Set(e.enemyIds).size!==e.enemyIds.length||e.quietSince!==undefined&&(!Number.isFinite(e.quietSince)||e.quietSince<0||e.quietSince>1e10))return fail();}
 const check=(id:string|null,type:string)=>id===null||!!catalog[id]&&catalog[id].type===type&&(legacy||type==='passive'||catalog[id].style===c.family||type==='active'&&catalog[id].style==='COM')&&(typeof progression==='number'?level>=catalog[id].unlockLevel:!!progression.learned[id]&&(progression.secondChapter||level>=catalog[id].unlockLevel));if(c.activeSlots.some(id=>!check(id,'active'))||new Set(c.activeSlots.filter(Boolean)).size!==c.activeSlots.filter(Boolean).length||c.passiveSlots.some((id,i)=>!check(id,'passive')||id!==null&&(i===0?level<6:level<11)&&!(typeof progression!=='number'&&progression.secondChapter))||new Set(c.passiveSlots.filter(Boolean)).size!==c.passiveSlots.filter(Boolean).length||!check(c.ultimate,'ultimate'))return fail();
 for(const record of [c.cooldowns,c.buffs])if(!record||Object.entries(record).some(([k,v])=>k.length>180||!Number.isFinite(v)||v<0||v>1e10))return fail();if(!c.statuses||!Array.isArray(c.casts)||c.casts.length>200)return fail();
 validateGrowingPulses(c.growingPending);
 const point=(v:Point)=>!!v&&Number.isFinite(v.x)&&Number.isFinite(v.z)&&Math.abs(v.x)<=5000&&Math.abs(v.z)<=5000;
 for(const st of Object.values(c.statuses))if(!st||Object.values(st).some(v=>!Number.isFinite(v)||v<0||v>1e10)||Object.keys(st).length!==8)return fail();
 for(const cast of c.casts){const capturedDex=(typeof progression==='number'?80:progression.attributes.dexterity)+(Array.isArray(cast.equipment)?Array.from(new Set(cast.equipment)).reduce((n,id)=>n+(gearStats[id]?.dexterity??0)+(EQUIPMENT[id]?.growthAttribute==='dexterity'?growingStats(id,cast.growthLevel??level).attribute:0),0):0),accuracyLimit=100+(EQUIPMENT[cast.weapon]?.kind==='bow'?Math.max(0,capturedDex-10)*.5:0);if(cast.accuracy!==undefined&&(!Number.isFinite(cast.accuracy)||cast.accuracy<100||cast.accuracy>accuracyLimit+.0000001))return fail();if(cast.criticalMultiplier!==undefined&&(!Number.isFinite(cast.criticalMultiplier)||cast.criticalMultiplier<1.5||cast.criticalMultiplier>Math.min(2.5,1.5+(Array.isArray(cast.equipment)?cast.equipment.reduce((n,id)=>n+(gearStats[id]?.criticalDamage??0),0):0)/100)+.0000001))return fail();if(cast.upgrades&&Object.entries(cast.upgrades).some(([k,v])=>!['breakPercent','shieldPercent','shieldFinisher','burnSeconds','stationary','stationaryBreak','markedCritical'].includes(k)||!Number.isFinite(v)||v<0||v>100)||cast.criticalChance!==undefined&&(!Number.isFinite(cast.criticalChance)||cast.criticalChance<0||cast.criticalChance>.3)||cast.criticalRoll!==undefined&&(!Number.isFinite(cast.criticalRoll)||cast.criticalRoll<0||cast.criticalRoll>1))return fail();const d=catalog[cast.skillId];if(cast.rush&&(cast.skillId!=='WAR_02'||!Number.isFinite(cast.rush.distance)||cast.rush.distance<0||cast.rush.distance>4.02+.001||!Number.isFinite(cast.rush.elapsed)||cast.rush.elapsed<0||cast.rush.elapsed>.18||cast.rush.duration!==.18||typeof cast.rush.stopped!=='boolean'))return fail();if(cast.zoneUntil!==undefined&&(legacy||!['FIR_04','BOW_06'].includes(cast.skillId)||!Number.isFinite(cast.zoneUntil)||!Number.isFinite(cast.releaseTime)||Math.abs(cast.zoneUntil-(cast.releaseTime!+(cast.rank.zoneDurationSeconds??0)))>.001)||cast.retreatElapsed!==undefined&&(legacy||cast.skillId!=='BOW_07'||!Number.isFinite(cast.retreatElapsed)||cast.retreatElapsed<0||cast.retreatElapsed>.201))return fail();if(!d||typeof cast.id!=='string'||!cast.rank||!Number.isInteger(cast.rank.rank)||cast.rank.rank<1||cast.rank.rank>5||typeof progression!=='number'&&cast.rank.rank>(progression.learned[cast.skillId]??0)||!acceptedRankSnapshot(cast.skillId,cast.rank,c.version)||!point(cast.from)||!point(cast.to)||!Number.isFinite(cast.angle)||!Number.isFinite(cast.power)||cast.power<24||cast.power>(24+1.5*(level-1))*equipmentPowerMultiplier(cast.weapon,cast.growthLevel??level)*(1+(Array.isArray(cast.equipment)?cast.equipment.reduce((n,id)=>n+(gearPower[id]??0),0):0)/100)+.0000001||cast.growthLevel!==undefined&&(!Number.isInteger(cast.growthLevel)||cast.growthLevel<1||cast.growthLevel>level)||!Number.isFinite(cast.attributeMultiplier)||cast.attributeMultiplier<1||cast.attributeMultiplier>1.61+.008*(Array.isArray(cast.equipment)?cast.equipment.reduce((n,id)=>n+Math.max(gearStats[id]?.strength??0,gearStats[id]?.dexterity??0,gearStats[id]?.intellect??0),0):0)+.0000001||!Number.isFinite(cast.damageBonus)||cast.damageBonus<0||cast.damageBonus>2||typeof cast.critical!=='boolean'||typeof cast.released!=='boolean'||!Number.isInteger(cast.nextSegment)||cast.nextSegment<0||cast.nextSegment>5||!Array.isArray(cast.equipment)||cast.equipment.some(id=>!EQUIPMENT[id])||!cast.passives||Object.entries(cast.passives).some(([id,v])=>!catalog[id]||catalog[id].type!=='passive'||!Number.isFinite(v)||v<0||v>100))return fail();for(const list of [cast.targets,cast.hits,cast.breakHits,cast.procs])if(!Array.isArray(list)||list.length>1000||list.some(id=>typeof id!=='string'||id.length>200))return fail();}
}
