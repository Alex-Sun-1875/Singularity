import {EQUIPMENT_CATALOG} from './EquipmentCatalog';
import {EQUIPMENT_EFFECTS} from '../../combat/data/PureSkills';
import {GROWING_ITEMS,GROWING_EQUIPMENT,growingStats} from './GrowingEquipment';
import {CHAPTER_WEAPONS} from './ChapterWeapons';
import {LIFECYCLE_ITEMS} from './EquipmentLifecycle';
import {FIELD_QUEST_ITEMS} from './FieldQuestEquipment';

export type EquipmentSlot = 'weapon'|'offhand'|'head'|'chest'|'hands'|'feet'|'ringLeft'|'ringRight'|'necklace';
export const ITEM_STACK_LIMIT=99;
/** Named growing equipment keeps its existing once-per-journey ownership. */
export const equipmentStackLimit=(id:string)=>GROWING_EQUIPMENT[id]?1:ITEM_STACK_LIMIT;
export interface ItemDef {
 id:string; name:string; kind:'sword'|'bow'|'staff'|'armor'|'ring'|'necklace'|'spell';
 slot:EquipmentSlot|'spell'; level:number; quality:string; description:string;
 set?:'oath'|'wind'|'seeker'|'ember'|'bell'|'seal'; twoHanded?:boolean; maxHp?:number; armor?:number;
 weaponFamily?:string; source?:string;artSource?:string;growthAttribute?:'strength'|'dexterity'|'intellect';power?:number;requiredLevel?:number;
 maxEnhance?:number;
 chapter?:number;growthMode?:'fixed'|'level';lifecycleGroup?:string;
 passive?:'steady-strike'|'recovery-strike'|'oath-guard'|'hunt-renewal';
}
/** Permanent equipment catalog plus eight unique growing items. T01–08 are migration aliases only. */
export const EQUIPMENT:Record<string,ItemDef> = Object.fromEntries([...EQUIPMENT_CATALOG,...GROWING_ITEMS,...CHAPTER_WEAPONS,...LIFECYCLE_ITEMS,...FIELD_QUEST_ITEMS].map(item=>[item.id,{...item,description:EQUIPMENT_EFFECTS[item.id]??item.description}]));
const ENHANCE_CAPS:Record<string,number>={'普通':3,'精良':5,'稀有':8,'史诗':10,'传奇':12,'神器':15};
/** Per-item exceptions live here rather than in generated catalogs or UI code. */
const ENHANCE_OVERRIDES:Record<string,number>={A10:6,J03:4};
for(const item of Object.values(EQUIPMENT))item.maxEnhance=ENHANCE_OVERRIDES[item.id]??item.maxEnhance??ENHANCE_CAPS[item.quality]??3;
export const equipmentPowerMultiplier=(id:string,level:number)=>EQUIPMENT[id]?.power?1+EQUIPMENT[id].power!/300:growingStats(id,level).multiplier;
export const FIRST_CHAPTER_IDS=['W01','W02','W07','W08','W11','A01','A02','A06','A09','A10','A13','A14','J03','J08'];
export interface RecipeDef {item:string;count:number;iron:number;runes?:number;cores?:number;refundIron?:number}
export const RECIPES:Record<string,RecipeDef>={
 C01:{item:'W04',count:1,iron:6,runes:1,cores:0,refundIron:2},
 C02:{item:'W05',count:1,iron:10,runes:3,cores:1,refundIron:4},
 C03:{item:'W09',count:1,iron:6,runes:2,cores:0,refundIron:2},
 C04:{item:'W13',count:1,iron:6,runes:2,cores:0,refundIron:2},
 C05:{item:'W16',count:1,iron:6,runes:1,cores:0,refundIron:2},
 C06:{item:'A04',count:1,iron:4,runes:1,cores:0,refundIron:1},
 C07:{item:'A08',count:1,iron:6,runes:1,cores:0,refundIron:2},
 C08:{item:'A12',count:1,iron:4,runes:1,cores:0,refundIron:1},
 C09:{item:'A16',count:1,iron:4,runes:1,cores:0,refundIron:1},
 C10:{item:'J04',count:1,iron:4,runes:2,cores:0,refundIron:1},
};
export const MERCHANTS:Record<string,{name:string;stock:Record<string,number>;prices:Record<string,number>}>= {
 mira:{name:'弥菈',stock:{J03:1},prices:{J03:28}},
 lorn:{name:'洛恩',stock:{A13:1,W15:1},prices:{A13:32,W15:64}},
 nightqi:{name:'夜祈',stock:{A10:1},prices:{A10:40}},
 severin:{name:'瑟维恩',stock:{J06:1},prices:{J06:56}},
 elise:{name:'艾莉丝',stock:{A07:1},prices:{A07:80}},
};
export function canonicalItem(id:string):string{return id.startsWith('design_eq_')?id.slice(10).toUpperCase():id.toUpperCase();}
export function canonicalMerchant(id:string):string{return ({'弥菈':'mira','洛恩':'lorn','夜祈':'nightqi','瑟维恩':'severin','艾莉丝':'elise',Mira:'mira',Lorn:'lorn',NightQi:'nightqi',reysa:'nightqi'} as Record<string,string>)[id]??id;}
