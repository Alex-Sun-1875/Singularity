import type {GameState} from '../../../core/GameSession';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import {equippedGearBonus,combatCriticalChance,combatCriticalMultiplier} from '../../equipment/common/EquipmentDice';
import {COMBAT_BALANCE} from '../../combat/data/CombatBalance';
import {itemGemView} from './GemWorkshop';
import {gemAmount,type GemStat} from '../data/Gems';
import {gemText} from '../locales';

function effective(s:GameState,gear=equippedGearBonus(s)){
 const armor=Array.from(new Set(Object.values(s.equipment).filter((id):id is string=>typeof id==='string'))).reduce((n,id)=>n+(EQUIPMENT[id]?.armor??0),0)+gear.armor;
 return {power:1+gear.power/100,maxHp:gear.maxHp,armor:Math.min(COMBAT_BALANCE.equipmentReductionCap*100,armor),criticalChance:combatCriticalChance(s,gear)*100,criticalDamage:combatCriticalMultiplier(s,gear)*100};
}
function difference(before:ReturnType<typeof effective>,after:ReturnType<typeof effective>,stat:GemStat){return stat==='power'?(after.power/before.power-1)*100:after[stat]-before[stat];}
const display=(value:number)=>`${value>=0?'+':''}${Number(value.toFixed(3))}`;
/** An empty standard socket is an explicit reference, rather than a DPS promise. */
export function gemPurchasePreview(s:GameState,stat:GemStat,tier:number):string {
 const before=effective(s),gear=equippedGearBonus(s);gear[stat]+=gemAmount(stat,tier);
 const delta=difference(before,effective(s,gear),stat);
 return gemText('preview.reference',{effect:gemText(('preview.effective.'+stat) as Parameters<typeof gemText>[0],{value:display(delta)})});
}
export function gemSocketPreview(s:GameState,item:string,hole:number,stat:GemStat,tier:number):string {
 if(!Object.values(s.equipment).includes(item))return gemText('preview.notEquipped');
 const view=itemGemView(s,item),sockets=view.sockets.map(g=>g?{...g}:null);sockets[hole]={stat,tier:tier as 1|2|3|4|5,units:view.units};
 const next:GameState={...s,gems:{...s.gems,items:{...s.gems.items,[item]:{opened:view.opened,sockets}}}},before=effective(s),after=effective(next);
 const changes=(['power','maxHp','armor','criticalChance','criticalDamage'] as GemStat[]).filter(key=>Math.abs(difference(before,after,key))>1e-7).map(key=>gemText(('preview.effective.'+key) as Parameters<typeof gemText>[0],{value:display(difference(before,after,key))}));
 return gemText('preview.actual',{effect:changes.join(' · ')||gemText('preview.noEffectiveChange')});
}
