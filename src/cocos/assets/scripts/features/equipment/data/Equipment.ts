import {EQUIPMENT_CATALOG} from './EquipmentCatalog';
import {EQUIPMENT_EFFECTS} from '../../combat/data/PureSkills';
import {GROWING_ITEMS,GROWING_EQUIPMENT,growingStats} from './GrowingEquipment';
import {CHAPTER_WEAPONS} from './ChapterWeapons';
import {LIFECYCLE_ITEMS} from './EquipmentLifecycle';
import {FIELD_QUEST_ITEMS} from './FieldQuestEquipment';
import {weaponPowerMultiplier,weaponPowerBonusPercent,nativeWeaponStrength} from './WeaponPower';

export type EquipmentSlot = 'weapon'|'offhand'|'head'|'chest'|'hands'|'feet'|'ringLeft'|'ringRight'|'necklace';
export const ITEM_STACK_LIMIT=99;
/** Named growing equipment keeps its existing once-per-journey ownership. */
export const equipmentStackLimit=(id:string)=>GROWING_EQUIPMENT[id]?1:ITEM_STACK_LIMIT;
export interface ItemDef {
 id:string; name:string; kind:'sword'|'bow'|'staff'|'armor'|'ring'|'necklace'|'spell';
 slot:EquipmentSlot|'spell'; level:number; quality:string; description:string;
 set?:'oath'|'wind'|'seeker'|'ember'|'bell'|'seal'; twoHanded?:boolean; maxHp?:number; armor?:number;
 weaponFamily?:string; source?:string;acquisitionSource?:string;artSource?:string;growthAttribute?:'strength'|'dexterity'|'intellect';power?:number;requiredLevel?:number;
 maxEnhance?:number;
 chapter?:number;growthMode?:'fixed'|'level';lifecycleGroup?:string;
 passive?:'steady-strike'|'recovery-strike'|'oath-guard'|'hunt-renewal';
}
/** Permanent equipment catalog plus eight unique growing items. T01–08 are migration aliases only. */
export const EQUIPMENT:Record<string,ItemDef> = Object.fromEntries([...EQUIPMENT_CATALOG,...GROWING_ITEMS,...CHAPTER_WEAPONS,...LIFECYCLE_ITEMS,...FIELD_QUEST_ITEMS].map(item=>[item.id,{...item,description:EQUIPMENT_EFFECTS[item.id]??item.description}]));
export const ENHANCE_CAPS:Record<string,number>={'普通':1,'精良':2,'稀有':3,'史诗':4,'传奇':6,'神器':8};
/** Per-item exceptions live here rather than in generated catalogs or UI code. */
const ENHANCE_OVERRIDES:Record<string,number>={A10:2,J03:1};
for(const item of Object.values(EQUIPMENT)){
 item.maxEnhance=Math.min(8,ENHANCE_CAPS[item.quality]??1,ENHANCE_OVERRIDES[item.id]??item.maxEnhance??8);
 if(item.slot==='weapon'&&!GROWING_EQUIPMENT[item.id]&&item.power===undefined){
  item.power=nativeWeaponStrength(item);
  if(item.power>0)item.description=`武器强度 ${item.power} · 基础攻击/技能威力 +${Number(weaponPowerBonusPercent(item.power).toFixed(1))}%\n${item.description}`;
 }
}
export const equipmentPowerMultiplier=(id:string,level:number)=>EQUIPMENT[id]?.power?weaponPowerMultiplier(EQUIPMENT[id].power!):growingStats(id,level).multiplier;
/** Existing H03 workshop inventory; offered once by its trial and collected through R2 loot. */
export const H03_EQUIPMENT_OPTIONS=['W04','W09','W13','W16','A04','A08','A12'] as const;
export const FIRST_CHAPTER_IDS=['W01','W02','W07','W08','W11','A01','A02','A06','A09','A10','A13','A14','J03','J08'];
export const MERCHANTS:Record<string,{name:string;stock:Record<string,number>;prices:Record<string,number>}>= {
 supplies:{name:'布兰',stock:{A01:1,A12:1},prices:{A01:120,A12:160}},
 jeweler:{name:'琳娜',stock:{},prices:{}},
 mira:{name:'弥菈',stock:{J03:1},prices:{J03:180}},
 lorn:{name:'洛恩',stock:{A13:1,W15:1,A09:1},prices:{A13:200,W15:420,A09:320}},
 nightqi:{name:'夜祈',stock:{A10:1},prices:{A10:420}},
 severin:{name:'瑟维恩',stock:{J06:1,A04:1,A08:1},prices:{J06:560,A04:480,A08:560}},
 elise:{name:'艾莉丝',stock:{A07:1},prices:{A07:840}},
};
export function canonicalItem(id:string):string{return id.startsWith('design_eq_')?id.slice(10).toUpperCase():id.toUpperCase();}
export function canonicalMerchant(id:string):string{return ({'弥菈':'mira','洛恩':'lorn','夜祈':'nightqi','瑟维恩':'severin','艾莉丝':'elise',Mira:'mira',Lorn:'lorn',NightQi:'nightqi',reysa:'nightqi'} as Record<string,string>)[id]??id;}

/** Existing receipts keep their paid price; these values are never offered by a new shop. */
export const MERCHANT_RECORDED_PRICES:Record<string,Record<string,number>>={mira:{J03:28},lorn:{A13:32,W15:64},nightqi:{A10:40},severin:{J06:56},elise:{A07:80}};
export const merchantTradeProof=(receipts:Record<string,string|number|boolean>,merchant:string,item:string)=>[MERCHANTS[merchant]?.prices[item],MERCHANT_RECORDED_PRICES[merchant]?.[item]].filter(price=>price!==undefined).some(price=>Object.values(receipts).includes(`${merchant}:${item}:${price}`));
