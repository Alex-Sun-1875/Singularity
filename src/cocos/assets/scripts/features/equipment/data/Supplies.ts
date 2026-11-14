import type {FeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {ITEM_STACK_LIMIT} from './Equipment';

export type SupplyId='SUPPLY_HEALTH'|'SUPPLY_FOCUS'|'SUPPLY_STAMINA'|'SUPPLY_MANA';
export interface SupplyDef {name:string;stock:'healthPotions'|'focusPotions'|'staminaPotions'|'manaPotions';capacity:number;icon:string;groundArt:string;groundSize:number;feedback:FeedbackRole}
const GROUND_BOTTLE_SIZE=.56;
/** Physical ground props are separate from the HUD glyphs; carrying rules are shared. */
export const SUPPLIES:Record<SupplyId,SupplyDef>={
 SUPPLY_HEALTH:{name:'生命药剂',stock:'healthPotions',capacity:ITEM_STACK_LIMIT,icon:'potion-health',groundArt:'equipment/supplies-v2/health-bottle',groundSize:GROUND_BOTTLE_SIZE,feedback:'damage.heal'},
 SUPPLY_FOCUS:{name:'专注药水',stock:'focusPotions',capacity:ITEM_STACK_LIMIT,icon:'potion-focus',groundArt:'equipment/supplies-v2/focus-bottle',groundSize:GROUND_BOTTLE_SIZE,feedback:'resource.focus'},
 SUPPLY_STAMINA:{name:'体力药水',stock:'staminaPotions',capacity:ITEM_STACK_LIMIT,icon:'potion-stamina',groundArt:'equipment/supplies-v2/stamina-bottle',groundSize:GROUND_BOTTLE_SIZE,feedback:'resource.stamina'},
 SUPPLY_MANA:{name:'法力药水',stock:'manaPotions',capacity:ITEM_STACK_LIMIT,icon:'potion-mana',groundArt:'equipment/supplies-v2/mana-bottle',groundSize:GROUND_BOTTLE_SIZE,feedback:'resource.mana'},
};
export const isSupplyId=(id:string):id is SupplyId=>Object.prototype.hasOwnProperty.call(SUPPLIES,id);
export const SUPPLY_LOOT_POLICY={chance:.35,healthWeight:.55,guaranteedPackSlot:7,lifetimeSeconds:120,maxPilesPerArea:24,maxPiles:96} as const;
export const supplySource=(area:string,enemy:string,cycle:number)=>`supply:${area}:${enemy}:${cycle}`;
function random(seed:number,key:string){let n=seed;for(let i=0;i<key.length;i++)n=(n*131+key.charCodeAt(i))%2147483647;return ((n+1)*48271)%2147483647;}
export interface SupplyEnemy {id:string;kind:string;bossId?:string;templateId?:string;packId?:string}
/** Independent of equipment RNG/pity, keyed to one actual enemy life. */
export function supplyDrop(seed:number,area:string,enemy:SupplyEnemy,cycle:number):{item:SupplyId;count:number}|null;
export function supplyDrop(seed:number,area:string,enemy:SupplyEnemy,cycle:number,version:1|2|3):{item:SupplyId|'SUPPLY_OIL';count:number}|null;
export function supplyDrop(seed:number,area:string,enemy:SupplyEnemy,cycle:number,version:1|2|3=3):{item:SupplyId|'SUPPLY_OIL';count:number}|null {
 const source=supplySource(area,enemy.id,cycle),elite=!!enemy.bossId||enemy.kind==='captain'||!!enemy.templateId?.includes('ALPHA');
 const guaranteed=elite||!!enemy.packId&&enemy.id===`${enemy.packId}-${SUPPLY_LOOT_POLICY.guaranteedPackSlot}`;
 if(!guaranteed&&random(seed,source)/2147483647>=SUPPLY_LOOT_POLICY.chance)return null;
 // V1/V2 are read-only proofs for existing ground drops; current rolls only grant potions.
 const choice=random(seed,source+':item')/2147483647,item=choice<SUPPLY_LOOT_POLICY.healthWeight?'SUPPLY_HEALTH':version<3&&choice>=.8?'SUPPLY_OIL':'SUPPLY_FOCUS';
 return {item:version>=2&&item==='SUPPLY_FOCUS'?(['SUPPLY_FOCUS','SUPPLY_STAMINA','SUPPLY_MANA'] as const)[random(seed,source+':resource')%3]:item,count:elite?2:1};
}
