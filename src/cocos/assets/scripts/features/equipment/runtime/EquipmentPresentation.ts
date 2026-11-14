import type {EquipmentSlot,ItemDef} from '../data/Equipment';

export const EQUIPMENT_SLOT_NAMES:Record<EquipmentSlot,string>={weapon:'主手',offhand:'副手',head:'头部',chest:'身体',hands:'手套',feet:'靴',ringLeft:'左戒',ringRight:'右戒',necklace:'项链'};
export const EQUIPMENT_SLOT_ICONS:Record<EquipmentSlot,string>={weapon:'attack',offhand:'push',head:'gear-head',chest:'gear-chest',hands:'gear-hands',feet:'gear-feet',ringLeft:'gear-ring',ringRight:'gear-ring',necklace:'gear-necklace'};

/** A weapon family describes weapons; armour and jewellery use their actual slot. */
export function equipmentTypeName(item:ItemDef):string {
 if(item.slot==='weapon'||item.slot==='offhand')return item.weaponFamily??EQUIPMENT_SLOT_NAMES[item.slot];
 return item.kind==='ring'?'戒指':EQUIPMENT_SLOT_NAMES[item.slot as EquipmentSlot]??'装备';
}

export function equipmentIcon(item:ItemDef):string {
 if(item.kind==='bow')return 'bow';if(item.kind==='sword')return 'attack';if(item.kind==='staff')return 'skill';if(item.kind==='spell')return 'spell0';
 return EQUIPMENT_SLOT_ICONS[item.slot as EquipmentSlot]??'inventory';
}
