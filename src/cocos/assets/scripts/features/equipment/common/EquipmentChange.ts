import {canonicalItem,EQUIPMENT,type EquipmentSlot} from '../data/Equipment';
import type {GameState} from '../../../core/GameSession';

export type EquipmentChangeBlock='missing'|'unowned'|'level'|'slot'|'two-handed'|'equipped'|'busy'|null;
export interface EquipmentChange {
 id:string;slot:EquipmentSlot;available:boolean;block:EquipmentChangeBlock;
 reason:string;requiredLevel:number;from?:EquipmentSlot;replaced?:string;offhand?:string;
}
/** One query drives the visible action and the actual transaction. No UI or engine dependencies. */
export function equipmentChange(state:GameState,item:string,requested:string|undefined,access:{available:boolean;reason:string}):EquipmentChange{
 const id=canonicalItem(item),def=EQUIPMENT[id],eq=state.equipment;
 const from=(Object.keys(eq) as (keyof typeof eq)[]).find(k=>k!=='spells'&&eq[k]===id) as EquipmentSlot|undefined;
 let slot:EquipmentSlot=def?.slot==='spell'?'weapon':def?.slot??'weapon';
 if(def?.kind==='ring')slot=requested==='ringLeft'||requested==='ringRight'?requested:from??(!eq.ringLeft?'ringLeft':!eq.ringRight?'ringRight':'ringLeft');
 const result:EquipmentChange={id,slot,from,available:false,block:null,reason:'',requiredLevel:def?.requiredLevel??1,
  replaced:typeof eq[slot]==='string'&&eq[slot]!==id?eq[slot] as string:undefined,
  offhand:def?.twoHanded&&eq.offhand?eq.offhand:undefined};
 const blocked=(block:EquipmentChangeBlock)=>({...result,block});
 if(!def||def.kind==='spell')return blocked('missing');
 if(!state.inventory[id]||!state.provenance[id])return blocked('unowned');
 if(requested&&requested!==slot)return blocked('slot');
 if(eq[slot]===id)return blocked('equipped');
 if(state.progression.level<result.requiredLevel)return blocked('level');
 if(slot==='offhand'&&EQUIPMENT[eq.weapon]?.twoHanded)return blocked('two-handed');
 if(!access.available)return {...blocked('busy'),reason:access.reason};
 return {...result,available:true};
}
