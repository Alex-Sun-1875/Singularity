import {EQUIPMENT} from '../data/Equipment';
import {GROWING_EQUIPMENT,growingStats} from '../data/GrowingEquipment';
import {lifecycleGroup} from '../data/EquipmentLifecycle';
import {itemForgingBonus} from '../../crafting/common/EquipmentForging';
import {freshForgingBonus,type RandomForgingBonus} from '../../crafting/data/EquipmentForging';
import {equippedGemBonus} from '../../gems/common/GemWorkshop';
import type {Attribute} from '../../progression/common/Progression';
import type {GameState} from '../../../core/GameSession';
import type {DiceView} from '../../progression/common/SkillChecks';
import {CAMPAIGN_MAX_LEVEL} from '../../progression/data/CampaignProgression';
import {redemptionEquipmentSourceLabel} from '../../redemption/common/RedemptionLedger';

export interface GearBonus {maxHp:number;armor:number;power:number}
export interface EquipmentRoll {item:string;source:string;level:number;face:number|null;claimed:boolean}
export type EquipmentRollBook=Record<string,EquipmentRoll>;
export interface GearOutcome {name:string;bonus:GearBonus;upgrade:string|null;description:string}
export interface EquipmentDiceView {item:string;level:number;face:number|null;outcome:GearOutcome|null;possibleUpgrade:string|null;upgradeOwned:boolean;bonus:GearBonus;acquisitionSource?:string}
const EMPTY:GearBonus={maxHp:0,armor:0,power:0};
export const GEAR_GRADES=['普通','精良','稀有','史诗','传奇','神器'];
function word(seed:number,key:string){let h=seed>>>0;for(let i=0;i<key.length;i++)h=Math.imul(h^key.charCodeAt(i),16777619)>>>0;h^=h>>>16;h=Math.imul(h,0x7feb352d);h^=h>>>15;return(h^(h>>>16))>>>0;}
export const equipmentRandomWord=word;
export function equipmentFace(seed:number,r:EquipmentRoll){return word(seed,`gear:${r.item}:${r.source}:face`)%6+1;}
export function equipmentUpgrade(seed:number,r:EquipmentRoll):string|null {
 const base=EQUIPMENT[r.item];if(!base||GROWING_EQUIPMENT[r.item])return null;
 const grade=GEAR_GRADES.indexOf(base.quality),pool=Object.values(EQUIPMENT).filter(d=>
  (base.lifecycleGroup?!!d.lifecycleGroup&&lifecycleGroup(d.lifecycleGroup)?.route==='battle'&&d.chapter===base.chapter&&(d.requiredLevel??1)<=r.level&&d.weaponFamily===base.weaponFamily:/^D[RUE]/.test(d.id)&&d.level<=r.level)
  &&!GROWING_EQUIPMENT[d.id]&&d.kind===base.kind&&d.slot===base.slot&&GEAR_GRADES.indexOf(d.quality)>grade);
 if(!pool.length)return null;const next=Math.min(...pool.map(d=>GEAR_GRADES.indexOf(d.quality))),choices=pool.filter(d=>GEAR_GRADES.indexOf(d.quality)===next).sort((a,b)=>a.id.localeCompare(b.id));
 return choices[word(seed,`gear:${r.item}:${r.source}:upgrade`)%choices.length].id;
}
export function equipmentOutcome(seed:number,r:EquipmentRoll):GearOutcome|null {
 if(r.face===null)return null;const bonus={...EMPTY},scale=1+Math.floor((r.level-1)/10);let name='原装';
 if(r.face===2){name='坚韧';bonus.maxHp=6*scale;}
 if(r.face===3){name='护佑';bonus.armor=2;}
 if(r.face===4){name='锋芒';bonus.power=3;}
 if(r.face===5){name='精铸';bonus.maxHp=8*scale;bonus.power=3;}
 if(r.face===6){name='升格';bonus.maxHp=10*scale;bonus.power=5;}
 const upgrade=r.face===6?equipmentUpgrade(seed,r):null;
 return {name,bonus,upgrade,description:r.face===1?'保持原有品质与效果，基础装备完整保留。':upgrade?'原装备获得额外铸印，并额外发现一件更高品质的同部位装备。':'铸印永久附着在这件装备上，穿戴后生效。'};
}
export function bonusText(b:GearBonus&Partial<RandomForgingBonus>){return [b.maxHp?`最大生命 +${b.maxHp}`:'',b.armor?`护甲 +${b.armor}%`:'',b.power?`攻击 / 技能伤害 +${b.power}%`:'',b.criticalChance?`暴击率 +${b.criticalChance}%`:'',b.criticalDamage?`暴击伤害 +${b.criticalDamage}%`:'',b.strength?`力量 +${b.strength}`:'',b.dexterity?`敏捷 +${b.dexterity}`:'',b.intellect?`智力 +${b.intellect}`:'',b.vitality?`体质 +${b.vitality}`:''].filter(Boolean).join('\n');}
export function itemGearBonus(s:GameState,id:string):GearBonus {const r=s.dice?.gear?.[id];return r?.claimed&&r.face!==null?equipmentOutcome(s.seed,r)!.bonus:EMPTY;}
export function equippedGearBonus(s:GameState):RandomForgingBonus {
 const result=freshForgingBonus(),keys=Object.keys(result) as (keyof RandomForgingBonus)[],equipped=new Set(Object.values(s.equipment).filter((id):id is string=>typeof id==='string'));
 for(const id of equipped){const b=itemGearBonus(s,id),f=itemForgingBonus(s,id);result.maxHp+=b.maxHp;result.armor+=b.armor;result.power+=b.power;for(const key of keys)result[key]+=f[key];}
 // Gem crystal units and item weights are resolved once by the gem domain.
 const gems=equippedGemBonus(s);for(const key of keys)result[key]+=gems[key];
 const counts:Record<string,number>={};for(const id of equipped){const set=EQUIPMENT[id]?.set;if(set)counts[set]=(counts[set]??0)+1;}
 if((counts.wind??0)>=2)result.criticalChance+=1;if((counts.ember??0)>=2)result.power+=1.5;if((counts.bell??0)>=2)result.power+=1.5;
 for(const key of keys)result[key]=Math.round(result[key]*1e6)/1e6;
 return result;
}
export function equipmentAttributeBonus(s:GameState,attribute:Attribute,gear=equippedGearBonus(s)){let value=gear[attribute];for(const id of new Set(Object.values(s.equipment).filter((id):id is string=>typeof id==='string')))if(EQUIPMENT[id]?.growthAttribute===attribute)value+=growingStats(id,s.progression.level).attribute;return value;}
export const effectiveAttribute=(s:GameState,attribute:Attribute,gear=equippedGearBonus(s))=>s.progression.attributes[attribute]+equipmentAttributeBonus(s,attribute,gear);
export const combatCriticalChance=(s:GameState,gear=equippedGearBonus(s))=>Math.min(.3,.05+.0012*(effectiveAttribute(s,'dexterity',gear)-10)+gear.criticalChance/100);
export const combatCriticalMultiplier=(s:GameState,gear=equippedGearBonus(s))=>Math.min(2.5,1.5+gear.criticalDamage/100);
interface Host {state():GameState;grant(item:string,count:number,source:string):void;recalculate():void;changed():void;emit(type:string,text?:string,extra?:Record<string,unknown>):void}
/** First-acquisition ledger. Old dice records remain valid save evidence. */
export class EquipmentDice {
 constructor(private host:Host){}
 private get s(){return this.host.state();}
 enqueue(item:string,source:string){
  if(!EQUIPMENT[item]||EQUIPMENT[item].kind==='spell'||source.startsWith('gear-upgrade:'))return;
  this.s.dice.gear??={};if(this.s.dice.gear[item])return;
  this.s.dice.gear[item]={item,source,level:this.s.progression.level,face:null,claimed:true};
  this.s.receipts['gear-refine:'+item]=true;
 }
 /** Pending notices already own their equipment. Retire only their acknowledgement. */
 settlePending(){
  let changed=false;
  for(const r of Object.values(this.s.dice.gear??{}))if(!r.claimed){
   r.face=null;r.claimed=true;this.s.receipts['gear-refine:'+r.item]=true;changed=true;
  }
  if(this.s.dice.active?.id.startsWith('gear:')){this.s.dice.active=null;changed=true;}
  if(changed)this.host.changed();
 }
 view():DiceView|null {const a=this.s.dice.active;if(!a?.id.startsWith('gear:'))return null;const r=this.s.dice.gear![a.id.slice(5)],d=EQUIPMENT[r.item];
  return {id:a.id,title:d.name,prompt:d.description,skillLabel:'获得装备',abilityLabel:'装备',dc:0,mode:'normal',modifiers:[],help:null,roll:null,attempt:0,inspiration:this.s.dice.inspiration,canReroll:false,canCancel:false,successText:'装备已放入行囊。',failureText:'',chance:1,gear:{item:r.item,level:this.s.progression.level,face:null,outcome:null,possibleUpgrade:null,upgradeOwned:false,bonus:EMPTY,acquisitionSource:redemptionEquipmentSourceLabel(this.s,r.item)}};
 }
 finish(){const a=this.s.dice.active,r=a?.id.startsWith('gear:')?this.s.dice.gear?.[a.id.slice(5)]:null;if(!r||r.claimed)return;
  // A pending result from an older build must not activate a free random bonus.
  r.face=null;r.claimed=true;this.s.receipts['gear-refine:'+r.item]=true;
  this.s.dice.active=null;this.host.recalculate();this.host.changed();
 }
}
const object=(v:unknown):v is Record<string,any>=>!!v&&typeof v==='object'&&!Array.isArray(v)&&Object.getPrototypeOf(v)===Object.prototype;
export function validateEquipmentDice(value:unknown,seed:number,receipts:Record<string,unknown>,active:any,area?:string){
 const fail=():never=>{throw new Error('无效的装备锻印存档');};
 if(!object(value)||Object.keys(value).length>Object.keys(EQUIPMENT).length)return fail();
 for(const [id,r]of Object.entries(value)){if(!EQUIPMENT[id]||!object(r)||Object.keys(r).sort().join()!=='claimed,face,item,level,source'||r.item!==id||typeof r.source!=='string'||r.source.length>200||!Number.isInteger(r.level)||r.level<1||r.level>CAMPAIGN_MAX_LEVEL||typeof r.claimed!=='boolean'||r.face!==null&&r.face!==equipmentFace(seed,r as EquipmentRoll)||r.claimed!==(receipts['gear-refine:'+id]===true)||r.source!=='initial'&&receipts[`grant:${r.source}:${id}`]!==true)fail();}
 for(const key of Object.keys(receipts))if(key.startsWith('gear-refine:')&&(!value[key.slice(12)]?.claimed||receipts[key]!==true))fail();
 if(active?.id?.startsWith('gear:')){const r=value[active.id.slice(5)];if(!r||r.claimed||area&&active.area!==area||active.sourceId!==r.source||JSON.stringify(active.context)!==JSON.stringify({mode:'normal',modifiers:[],helpDie:false,helpLabel:null})||Object.keys(active).sort().join()!=='area,context,id,sourceId')fail();}
}
export function validateEquipmentOwnership(s:GameState){for(const [id,r]of Object.entries(s.dice?.gear??{})){const source=s.provenance[id];if(!s.inventory[id]||r.level>s.progression.level||source!==r.source&&source!==`${r.source}:owned:${id}`)throw new Error('无效的装备锻印来源');}}
export function validEquipmentUpgrade(s:GameState,id:string,source:string){const base=source.slice(13),r=s.dice?.gear?.[base];return source.startsWith('gear-upgrade:')&&!!r?.claimed&&r.face===6&&equipmentOutcome(s.seed,r)?.upgrade===id&&s.receipts['gear-refine:'+base]===true;}
