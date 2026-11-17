import type {GameSession,GameState} from '../../../core/GameSession';
import {EQUIPMENT,equipmentPowerMultiplier,type EquipmentSlot} from '../data/Equipment';
import {GROWING_EQUIPMENT,growingStats} from '../data/GrowingEquipment';
import {GEAR_GRADES,equippedGearBonus,effectiveAttribute,combatCriticalChance,combatCriticalMultiplier} from './EquipmentDice';
import type {EquipmentChange} from './EquipmentChange';
import {professionAcceptsItem,weaponCombatFamily} from '../../progression/common/CombatLoadouts';
import {baseMaxHp} from '../../progression/common/Progression';
import {incomingDamageReduction} from '../../combat/data/CombatBalance';

/** General-purpose auto gear: real attack/critical scaling and effective health,
 * with a small quality preference for effects that depend on combat conditions.
 * Evaluate a copied loadout; never equip, spend materials or change profession. */
function loadoutScore(s:GameState):number {
 const gear=equippedGearBonus(s),family=weaponCombatFamily(s.equipment.weapon,s.combat),attribute=family==='WAR'?'strength':family==='BOW'?'dexterity':'intellect';
 let hp=baseMaxHp(s.progression)+gear.maxHp,armor=gear.armor,quality=0;
 const counts:Record<string,number>={};
 for(const id of new Set(Object.values(s.equipment).filter((id):id is string=>typeof id==='string'))){
  const item=EQUIPMENT[id];if(!item)continue;
  hp+=GROWING_EQUIPMENT[id]?growingStats(id,s.progression.level).maxHp:item.maxHp??0;
  armor+=item.armor??0;quality+=Math.max(0,GEAR_GRADES.indexOf(item.quality));
  if(item.set)counts[item.set]=(counts[item.set]??0)+1;
 }
 if((counts.oath??0)>=2)hp+=8;
 const attack=equipmentPowerMultiplier(s.equipment.weapon,s.progression.level)*(1+gear.power/100)*(1+.008*(effectiveAttribute(s,attribute,gear)-10))*(1+combatCriticalChance(s,gear)*(combatCriticalMultiplier(s,gear)-1));
 const effectiveHp=hp/(1-incomingDamageReduction(armor,0,0,true));
 return Math.log(Math.max(.01,attack))+.5*Math.log(Math.max(1,effectiveHp))+.01*quality;
}

/** Best strictly improving legal single change, including both ring slots and
 * the offhand removed by a two-handed weapon. Busy changes can be queued until
 * ordinary disengagement completes; level/ownership restrictions never relax. */
export function recommendedEquipmentChange(game:GameSession):EquipmentChange|null {
 const s=game.state,family=weaponCombatFamily(s.equipment.weapon,s.combat);
 let best:EquipmentChange|null=null,bestScore=loadoutScore(s);
 for(const id of Object.keys(s.inventory).sort()){
  const item=EQUIPMENT[id];
  if(!item||!s.inventory[id]||!s.provenance[id]||!professionAcceptsItem(family,id))continue;
  if(item.weaponFamily==='双手火杖'&&family!=='FIR'||item.weaponFamily==='双手雷杖'&&family!=='THU')continue;
  // One owned ring cannot fill two slots; automatic upgrades keep the other
  // equipped ring in place instead of swapping the same two rings forever.
  if(Object.values(s.equipment).includes(id))continue;
  const slots:EquipmentSlot[]=item.kind==='ring'?['ringLeft','ringRight']:[item.slot as EquipmentSlot];
  for(const slot of slots){
   const change=game.equipmentChange(id,slot);
   if(!change.available&&change.block!=='busy')continue;
   const equipment={...s.equipment,[slot]:id};if(item.twoHanded)equipment.offhand=null;
   const score=loadoutScore({...s,equipment});
   if(score>bestScore+1e-6){best=change;bestScore=score;}
  }
 }
 return best;
}
