import type {GameState} from '../../../core/GameSession';
import {effectiveAttribute} from '../../equipment/common/EquipmentDice';
import type {Attribute} from '../../progression/common/Progression';
import type {CombatFamily} from '../../progression/common/CombatLoadouts';
import type {CombatSkillDef} from '../data/PureSkills';
import {COMBAT_BALANCE} from '../data/CombatBalance';

export type ResourceKind='stamina'|'focus'|'mana';
export const RESOURCE_RULES={base:100,perAttribute:2,combatRegen:COMBAT_BALANCE.combatResourceRegen,restRegen:COMBAT_BALANCE.restResourceRegen,potionFraction:.45,potionCooldown:COMBAT_BALANCE.potionCooldown} as const;
const PROFILES={
 WAR:{kind:'stamina',name:'体力',attribute:'strength',potion:'体力药水',stock:'staminaPotions',icon:'potion-stamina',feedback:'resource.stamina'},
 BOW:{kind:'focus',name:'专注',attribute:'dexterity',potion:'专注药水',stock:'focusPotions',icon:'potion-focus',feedback:'resource.focus'},
 FIR:{kind:'mana',name:'法力',attribute:'intellect',potion:'法力药水',stock:'manaPotions',icon:'potion-mana',feedback:'resource.mana'},
 THU:{kind:'mana',name:'法力',attribute:'intellect',potion:'法力药水',stock:'manaPotions',icon:'potion-mana',feedback:'resource.mana'},
} as const;
export const resourceProfile=(s:GameState)=>PROFILES[s.combat.family??'WAR'];
export const resourceForFamily=(family:CombatFamily)=>PROFILES[family];
export const resourceCostText=(skill:CombatSkillDef)=>skill.resourceCost?`消耗${skill.resourceCost}${(PROFILES[skill.style as CombatFamily]?.name??'职业资源')} · 自动恢复`:skill.type==='passive'?'被动效果，不消耗资源':'不消耗职业资源';
export function resourceMaximum(s:GameState,family:CombatFamily=s.combat.family??'WAR'){
 const attribute:Attribute=PROFILES[family].attribute;
 return Math.round(RESOURCE_RULES.base+RESOURCE_RULES.perAttribute*Math.max(0,effectiveAttribute(s,attribute)-10));
}
/** Capacity changes preserve fullness, so swapping equipment/attributes cannot refill. */
export function synchronizeResource(s:GameState){
 const p=s.player,max=resourceMaximum(s),fraction=p.maxFocus>0?p.focus/p.maxFocus:0;
 p.focus=Math.max(0,Math.min(max,fraction*max));p.maxFocus=max;
}
/** Only called on an already validated copy of an older save. */
export function migrateClassResource(s:GameState){
 const p=s.player;if(p.resourceVersion===1)return false;
 p.resourceVersion=1;p.staminaPotions=2;p.manaPotions=2;
 // Charge has no conversion value; preserve the existing renewable resource.
 s.combat.charge=0;return true;
}
export const skillResourceText=(value:string)=>value.replace(/消耗100蓄能/g,'消耗45职业资源').replace(/不产生蓄能/g,'不触发资源回复').replace(/刷蓄能/g,'重复回复资源');
