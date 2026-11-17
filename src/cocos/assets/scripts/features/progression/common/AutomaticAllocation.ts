import {ATTRIBUTES,SKILL_RANK_COSTS,type Attribute,type ProgressionState} from './Progression';
import {COMBAT_LOADOUTS,type CombatFamily} from './CombatLoadouts';

/** Spend only unused points. Preserve every manual investment and other family.
 * Two primary points per vitality point, then capped-stat overflow. Skills
 * prioritise the current fixed kit's main attack, area attack and ultimate. */
export function automaticAllocation(p:ProgressionState,family:CombatFamily){
 const primary:Attribute=family==='WAR'?'strength':family==='BOW'?'dexterity':'intellect',attributes={...p.attributes},learned={...p.learned};
 let attributesLeft=p.unspentPoints,skillsLeft=p.skillPoints;
 while(attributesLeft>0){
  const preferred=attributes[primary]-10<2*(attributes.vitality-10+1)?primary:'vitality';
  const key=[preferred,primary,'vitality',...ATTRIBUTES].find(key=>attributes[key as Attribute]<80) as Attribute|undefined;
  if(!key)break;attributes[key]++;attributesLeft--;
 }
 const kit=COMBAT_LOADOUTS[family],priority=[kit.activeSlots[0],kit.activeSlots[3],kit.ultimate,family+'_P1',kit.activeSlots[1],kit.activeSlots[2],family+'_P2','COM_01','COM_02'];
 for(const id of priority){
  if(!id)continue;
  while(learned[id]>0&&learned[id]<5&&skillsLeft>=SKILL_RANK_COSTS[learned[id]+1]){skillsLeft-=SKILL_RANK_COSTS[learned[id]+1];learned[id]++;}
 }
 return {attributes,learned,attributePoints:p.unspentPoints-attributesLeft,skillPoints:p.skillPoints-skillsLeft};
}
