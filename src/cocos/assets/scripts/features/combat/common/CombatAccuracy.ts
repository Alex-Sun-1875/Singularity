import type {GameState,EnemyState} from '../../../core/GameSession';
import {effectiveAttribute,equipmentRandomWord} from '../../equipment/common/EquipmentDice';
import type {Attribute} from '../../progression/common/Progression';
import {RESOURCE_RULES,resourceMaximum} from './ClassResource';
import {combatBudgetLevel} from '../../progression/data/CampaignProgression';

/** Ratings are percentage points; contact geometry is always checked first. */
export const ACCURACY_RULES={baseAccuracy:100,perFocusCapacity:.25,baseEvasion:5,perDexterity:.2,maxEvasion:25,minHitChance:.6,maxHitChance:1} as const;
const ENEMY_EVASION={raider:3,shield:1,archer:8,captain:5} as const;
export function playerCombatAttributes(s:GameState,attributes:Record<Attribute,number>=s.progression.attributes){
 const extraDex=attributes.dexterity-s.progression.attributes.dexterity,dex=effectiveAttribute(s,'dexterity')+extraDex;
 // Use permanent capacity, never the current (spendable) resource value.
 const focusCapacity=resourceMaximum(s,'BOW')+RESOURCE_RULES.perAttribute*extraDex;
 return {
  accuracy:ACCURACY_RULES.baseAccuracy+(s.combat.family==='BOW'?Math.max(0,focusCapacity-RESOURCE_RULES.base)*ACCURACY_RULES.perFocusCapacity:0),
  evasion:Math.min(ACCURACY_RULES.maxEvasion,ACCURACY_RULES.baseEvasion+Math.max(0,dex-10)*ACCURACY_RULES.perDexterity),
 };
}
export function enemyCombatAttributes(e:Pick<EnemyState,'kind'|'level'|'bossId'>){
 const level=Math.max(0,combatBudgetLevel(e.level??1)-1);
 return {accuracy:100+level*.1+(e.bossId?2:0),evasion:ENEMY_EVASION[e.kind]+level*.05+(e.bossId?2:0)};
}
export const contactHitChance=(accuracy:number,evasion:number)=>Math.max(ACCURACY_RULES.minHitChance,Math.min(ACCURACY_RULES.maxHitChance,(accuracy-evasion)/100));
/** Stable per attack/target, independent of critical rolls and frame rate. */
export function rollContactHit(seed:number,attack:string,target:string,accuracy:number,evasion:number){
 const chance=contactHitChance(accuracy,evasion),roll=equipmentRandomWord(seed,`contact-hit:${attack}:${target}`)/4294967296;
 return {landed:roll<chance,chance,roll};
}

/** A stored multi-hit outcome must agree with its deterministic contact roll. */
export function validateContactSnapshots(s:GameState){
 const fail=()=>{throw new Error('无效的命中判定存档');};
 for(const cast of s.combat.casts){
  const seen=new Set<string>();
  for(const key of cast.procs){
   const match=/^accuracy:(hit|miss):(.+)$/.exec(key);if(!match)continue;
   const enemy=s.enemies.find(e=>e.id===match[2]);if(!enemy||seen.has(enemy.id))return fail();seen.add(enemy.id);
   const result=rollContactHit(s.seed,cast.id,enemy.id,cast.accuracy??playerCombatAttributes(s).accuracy,enemyCombatAttributes(enemy).evasion);
   if(result.landed!==(match[1]==='hit')||!result.landed&&cast.hits.some(hit=>/^\d+:/.test(hit)&&hit.slice(hit.indexOf(':')+1)===enemy.id))return fail();
  }
  if(cast.accuracy!==undefined)for(const key of cast.hits){const match=/^\d+:(.+)$/.exec(key);if(match&&!cast.procs.includes(`accuracy:hit:${match[1]}`))return fail();}
 }
}
