import type {EquipmentSlot,ItemDef} from '../data/Equipment';
import {GROWING_EQUIPMENT,growingStats} from '../data/GrowingEquipment';
import {equipmentStory} from '../common/EquipmentStories';

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

/** Catalog and level growth only; enhancement, gems and old imprints stay separate. */
export function equipmentBasePresentation(item:ItemDef,level:number):{description:string;stats:{label:string;value:string}[];lore:string;source:string} {
 const growth=GROWING_EQUIPMENT[item.id]?growingStats(item.id,level):null,power=growth?.power??item.power??0,maxHp=growth?.maxHp??item.maxHp??0,armor=item.armor??0;
 const format=(value:number)=>String(Number(value.toFixed(1))),stats:{label:string;value:string}[]=[{label:'等级要求',value:`Lv${item.requiredLevel??1}`}];
 if(power)stats.push({label:'基础攻击／技能威力',value:`+${format(power/3)}%`});
 if(maxHp)stats.push({label:'最大生命',value:`+${format(maxHp)}`});
 if(armor)stats.push({label:'护甲',value:`+${format(armor)}%`});
 if(growth?.attribute&&item.growthAttribute){const names={strength:'力量',dexterity:'敏捷',intellect:'智力'};stats.push({label:names[item.growthAttribute],value:`+${format(growth.attribute)}`});}
 // Stage catalogs carry repeated headings/numbers as well as real passives.
 // Keep passives and set effects; ordinary damage-reduction prose is untouched.
 const description=item.lifecycleGroup||/^CJ\d+_/.test(item.id)?item.description.split('\n').filter(line=>line!==item.source&&!/^(第\d+章\s*·|Lv\d+起可装备|武器强度|最大生命|来源[：:])/.test(line)&&!/(阶段装备|阶段属性固定|基础数值不随人物等级成长)/.test(line)).join('\n'):item.description;
 return {description,stats,...equipmentStory(item)};
}
