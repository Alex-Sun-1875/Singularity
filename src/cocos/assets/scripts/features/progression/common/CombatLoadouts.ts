import {EQUIPMENT} from '../../equipment/data/Equipment';
import {COMBAT_SKILLS,LEGACY_COMBAT_SKILLS,combatSkillCatalog} from '../../combat/data/PureSkills';
import {skillUnlocked,skillRankSpent,totalSkillPoints,type ProgressionState} from './Progression';
import type {GameState} from '../../../core/GameSession';
import type {CombatState} from '../../combat/common/PureCombat';

export type CombatFamily='WAR'|'BOW'|'FIR'|'THU';
export type CombatSlots=[string|null,string|null,string|null,string|null];
/** Intended assignments retain locked skills without making them castable. */
export interface CombatLoadout {activeSlots:CombatSlots;ultimate:string|null;}
export const COMBAT_LOADOUTS:Record<CombatFamily,{name:string;weapon:string;activeSlots:CombatSlots;ultimate:string}>={
 WAR:{name:'破军战技',weapon:'W01',activeSlots:['WAR_01','WAR_02','WAR_03','WAR_04'],ultimate:'WAR_05'},
 BOW:{name:'逐风弓术',weapon:'W07',activeSlots:['BOW_01','BOW_02','BOW_06','BOW_07'],ultimate:'BOW_05'},
 FIR:{name:'烈焰秘术',weapon:'W11',activeSlots:['FIR_01','FIR_02','FIR_03','FIR_04'],ultimate:'FIR_05'},
 THU:{name:'雷霆秘术',weapon:'W11',activeSlots:['THU_01','THU_02','THU_04','THU_06'],ultimate:'THU_05'},
};
/** Browsing a profession never changes the active loadout. Armour and jewellery are shared. */
export function professionAcceptsItem(family:CombatFamily,id:string):boolean {
 const item=EQUIPMENT[id];return !!item&&item.kind!=='spell'&&(item.slot!=='weapon'||item.kind===EQUIPMENT[COMBAT_LOADOUTS[family].weapon].kind);
}
export function weaponCombatFamily(weapon:string,combat:CombatState):CombatFamily {
 const kind=EQUIPMENT[weapon]?.kind;if(kind==='sword')return 'WAR';if(kind==='bow')return 'BOW';
 if(combat.family==='FIR'||combat.family==='THU')return combat.family;
 if(combat.staffFamily)return combat.staffFamily;
 const spell=[combat.ultimate,...combat.activeSlots].find(id=>id&&['FIR','THU'].includes(COMBAT_SKILLS[id]?.style));
 return spell&&COMBAT_SKILLS[spell].style==='THU'?'THU':'FIR';
}
export function assignedLoadout(combat:CombatState):CombatLoadout|undefined{return combat.family?combat.loadouts?.[combat.family]:undefined;}
export function rememberCombatLoadout(combat:CombatState,level:number|ProgressionState):void {
 const saved=assignedLoadout(combat);if(!saved)return;
 for(let i=0;i<4;i++)if(combat.activeSlots[i]!==null||saved.activeSlots[i]===null||skillUnlocked(saved.activeSlots[i]!,level))saved.activeSlots[i]=combat.activeSlots[i];
 if(combat.ultimate!==null||saved.ultimate===null||skillUnlocked(saved.ultimate,level))saved.ultimate=combat.ultimate;
}
export function prepareCombatLoadout(combat:CombatState,weapon:string,level:number|ProgressionState,family=weaponCombatFamily(weapon,combat)):void {
 rememberCombatLoadout(combat,level);combat.loadouts??={};
 if(!combat.loadouts[family]){
  const defaults=COMBAT_LOADOUTS[family];
  combat.loadouts[family]={activeSlots:[...defaults.activeSlots],ultimate:defaults.ultimate};
 }
 combat.family=family;if(family==='FIR'||family==='THU')combat.staffFamily=family;activateCombatLoadout(combat,level);
}
export function activateCombatLoadout(combat:CombatState,level:number|ProgressionState):void {
 const saved=assignedLoadout(combat);if(!saved)return;
 combat.activeSlots=saved.activeSlots.map(id=>id&&skillUnlocked(id,level)?id:null) as CombatSlots;
 combat.ultimate=saved.ultimate&&skillUnlocked(saved.ultimate,level)?saved.ultimate:null;
}
export function validateCombatLoadouts(combat:CombatState,legacy=combat.version===2):boolean {
 if(combat.staffFamily!==undefined&&combat.staffFamily!=='FIR'&&combat.staffFamily!=='THU')return false;
 if(!combat.family||!Object.prototype.hasOwnProperty.call(COMBAT_LOADOUTS,combat.family)||!combat.loadouts||typeof combat.loadouts!=='object'||Array.isArray(combat.loadouts)||!combat.loadouts[combat.family])return false;
 const catalog=combatSkillCatalog(combat.version);
 const valid=(id:unknown,type:string,family:string)=>id===null||typeof id==='string'&&catalog[id]?.type===type&&(legacy||catalog[id].style===family||type==='active'&&catalog[id].style==='COM');
 return Object.entries(combat.loadouts).every(([family,loadout])=>Object.prototype.hasOwnProperty.call(COMBAT_LOADOUTS,family)&&loadout&&typeof loadout==='object'&&!Array.isArray(loadout)&&Object.keys(loadout).length===2&&Array.isArray(loadout.activeSlots)&&loadout.activeSlots.length===(combat.version===3?3:4)&&loadout.activeSlots.every(id=>valid(id,'active',family))&&new Set(loadout.activeSlots.filter(Boolean)).size===loadout.activeSlots.filter(Boolean).length&&valid(loadout.ultimate,'ultimate',family));
}

/** Validate the original snapshot first, then migrate its copy without replaying
 * refunds, resource recovery or rewards. Restored skills start at the free rank. */
export function migrateRestoredSkills(s:GameState):boolean {
 const c=s.combat,p=s.progression,version=c.version;if(version===4)return false;
 const old=p.learned,next:Record<string,number>={};
 for(const id of Object.keys(COMBAT_SKILLS)){
  const prior=version===3?(id==='THU_06'?old.THU_03:id==='THU_03'?0:old[id]):old[id];
  next[id]=skillUnlocked(id,p)?Math.max(1,prior??0):0;
 }
 p.learned=next;p.skillPoints=totalSkillPoints(p)-Object.values(next).reduce((sum,rank)=>sum+skillRankSpent(rank),0);
 const family=c.family!,previous=c.loadouts??{},mapped=(id:string|null)=>version===3&&id==='THU_03'?'THU_06':id;
 c.loadouts={};
 for(const key of Object.keys(COMBAT_LOADOUTS) as CombatFamily[]){
  const defaults=COMBAT_LOADOUTS[key],saved=previous[key],slots:CombatSlots=[null,null,null,null],overflow:string[]=[];
  (saved?.activeSlots??[]).forEach((raw,index)=>{const id=mapped(raw);if(!id||COMBAT_SKILLS[id]?.type!=='active'||![key,'COM'].includes(COMBAT_SKILLS[id].style)||slots.includes(id))return;if(index<4)slots[index]=id;else overflow.push(id);});
  const formerUltimate=mapped(saved?.ultimate??null);if(formerUltimate&&COMBAT_SKILLS[formerUltimate]?.type==='active')overflow.push(formerUltimate);
  for(const id of [...overflow,...defaults.activeSlots]){if(!id||slots.includes(id))continue;const empty=slots.indexOf(null);if(empty<0)break;slots[empty]=id;}
  const oldUltimate=saved?.ultimate;const ultimate=oldUltimate&&COMBAT_SKILLS[oldUltimate]?.type==='ultimate'?oldUltimate:defaults.ultimate;
  c.loadouts[key]={activeSlots:slots,ultimate};
 }
 if(version===3&&c.cooldowns.THU_03!==undefined){c.cooldowns.THU_06=c.cooldowns.THU_03;delete c.cooldowns.THU_03;}
 c.version=4;c.family=family;c.casts=[];c.buffs={};c.statuses={};c.growingPending=[];c.ultimateLock=0;c.charge=0;
 s.player.shield=0;s.action=null;s.projectiles=[];s.fireZones=[];
 activateCombatLoadout(c,p);s.receipts['skills:restored:v1']=true;return true;
}
/** Compatibility export for callers from the compact-skill revision. */
export const migrateFourSkillKit=migrateRestoredSkills;
