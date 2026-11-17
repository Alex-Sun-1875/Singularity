import {redemptionStoneBalance} from '../../redemption/common/RedemptionLedger';
import type {GameState,EnemyState} from '../../../core/GameSession';
import {GEM_STATS,GEM_POLICY,gemBankKey,type GemStat} from '../../gems/data/Gems';
import {chapterForArea,playableArea,JOURNEY_TASKS,journeyTaskKey} from '../../journey/data/ChapterJourney';
import {CAMPAIGN_STAGES,campaignStageKey,campaignStageSatisfied} from '../../journey/data/CampaignStages';
import {CAMPAIGN_EVENTS} from '../../campaign/data/CampaignEvents';
import {campaignFighter} from '../../campaign/data/CampaignBattles';
import {campaignExperienceQuote} from '../../progression/data/CampaignExperience';
import {BUILD_PROFILE} from '../../../shared/BuildProfile';
import {EQUIPMENT,canonicalItem,equipmentStackLimit} from '../../equipment/data/Equipment';
import {equipmentText as et} from '../../equipment/locales';

export const MATERIAL_TIER_NAMES=['','Ⅰ','Ⅱ','Ⅲ','Ⅳ','Ⅴ'] as const;
export const MATERIAL_TIER_LEVELS=[1,20,40,60,80] as const;
export const MATERIAL_RANK_TIERS=[1,2,2,3,3,4,4,5] as const;
export const materialTierForLevel=(level:number)=>MATERIAL_TIER_LEVELS.filter(required=>level>=required).length;
export function materialNextUnlock(level:number):{tier:number;level:number}|undefined {const index=MATERIAL_TIER_LEVELS.findIndex(required=>required>level);return index<0?undefined:{tier:index+1,level:MATERIAL_TIER_LEVELS[index]};}
export type MaterialTier=1|2|3|4|5;
type DropKind='ordinary'|'elite'|'boss';
interface Harvest {area:string;enemy:string;tier:MaterialTier;kind:DropKind;count:number;cycle:number;bonusCount?:number;earnedGems?:number}
interface TaskGift {source:string;chapter:number;gem?:false}
interface Synthesis {request:string;tier:number;gold:number;level:number}
/** One counter per real spawn slot/tier, rather than a growing record per kill. */
export interface CultivationState {version:1;harvests:Record<string,Harvest>;tasks:TaskGift[];syntheses:Synthesis[];gemBatches:{after:number;bank:Record<string,number>}[];dismantled?:Record<string,{count:number;sequence:number}>}
export const freshCultivation=():CultivationState=>({version:1,harvests:{},tasks:[],syntheses:[],gemBatches:[]});
export const materialTierForRank=(rank:number)=>(MATERIAL_RANK_TIERS[rank-1]??1) as MaterialTier;
export const materialName=(tier:number)=>`强化石${MATERIAL_TIER_NAMES[tier]??tier}阶`;
export type DismantlingMode='one'|'stack'|'all';
/** Use the equipment's own level and quality; player level and enhancement never multiply returns. */
export function dismantlingYield(id:string){const d=EQUIPMENT[id];return d&&d.kind!=='spell'&&equipmentStackLimit(id)>1?{tier:Math.max(1,materialTierForLevel(d.requiredLevel??d.level)),count:({'普通':1,'精良':2,'稀有':3,'史诗':4,'传奇':6,'神器':8} as Record<string,number>)[d.quality]??1}:null;}
const dismantlingReceipt=(id:string,count:number,sequence:number)=>JSON.stringify({version:1,item:id,count,sequence});
export const cultivationEnemyTier=(level:number,area:string)=>Math.min(chapterForArea(area),level>=61?5:level>=41?4:level>=21?3:level>=11?2:1) as MaterialTier;
const plain=(value:unknown):value is Record<string,any>=>!!value&&typeof value==='object'&&!Array.isArray(value)&&Object.getPrototypeOf(value)===Object.prototype;
const integer=(value:unknown,max=1e8,min=0):value is number=>typeof value==='number'&&Number.isSafeInteger(value)&&value>=min&&value<=max;
const exact=(value:object,keys:string[])=>Object.keys(value).sort().join()===keys.slice().sort().join();
const hash=(key:string)=>{let n=2166136261;for(const char of key)n=Math.imul(n^char.charCodeAt(0),16777619);return n>>>0;};
const enemy=(s:GameState,area:string,id:string)=>(s.area===area?s.enemies:s.encounters[area]??[]).find(e=>e.id===id);
const kindOf=(e:EnemyState):DropKind=>e.bossId?'boss':e.kind==='captain'||e.templateId?.includes('ALPHA')?'elite':'ordinary';
const stonesFor=(h:Harvest)=>{const bonus=h.bonusCount??0;return h.kind==='boss'?3*(h.count+bonus):h.kind==='elite'?h.count+bonus:Math.floor((h.count-bonus+hash('stone:'+h.area+':'+h.enemy)%3)/3)+bonus;};
const gemsFor=(h:Harvest)=>{if(h.earnedGems!==undefined)return h.earnedGems;const interval=h.kind==='boss'?1:h.kind==='elite'?3:8;return Math.floor((h.count+hash('gem:'+h.area+':'+h.enemy)%interval)/interval);};
const taskValid=(s:GameState,t:TaskGift)=>{
 if(!integer(t.chapter,2,1)||typeof t.source!=='string'||s.receipts[t.source]!==true||t.chapter===2&&!s.progression.secondChapter)return false;
 const original=JOURNEY_TASKS.find(task=>journeyTaskKey(task.id)===t.source),stage=CAMPAIGN_STAGES.find(stage=>campaignStageKey(stage.id)===t.source),event=t.source.startsWith('campaign:')?CAMPAIGN_EVENTS[t.source.slice(9)]:undefined;
 if((original?.chapter??stage?.chapter??(event?chapterForArea(event.area):0))!==t.chapter)return false;
 if(original)return s.flags[t.source]===true&&Number(s.progression.xpReceipts[t.source]??0)>0;
 if(stage){const expected=campaignExperienceQuote(t.source,stage.experience).amount;return campaignStageSatisfied(s,stage)&&(expected?s.progression.xpReceipts[t.source]===expected:s.progression.xpReceipts[t.source]===undefined);}
 if(!event||!playableArea(event.area)||(event.requires??[]).some(flag=>!s.flags[flag])||event.requiresAny?.length&&!event.requiresAny.some(flag=>s.flags[flag])||(event.sets??[]).some(flag=>!s.flags[flag]))return false;
 const selected=event.choices?.find(choice=>choice.id===s.receipts['campaign:choice:'+event.id]);return !event.choices?.length||!!selected&&(selected.sets??[]).every(flag=>s.flags[flag]);
};
const state=(s:GameState)=>s.forging.cultivation;
export function cultivationGemBank(s:GameState):Record<string,number>{
 const bank:Record<string,number>={},add=(stat:GemStat,tier:number,units:number)=>{if(units){const key=gemBankKey(stat,tier);bank[key]=(bank[key]??0)+units;}};
 for(const [key,h]of Object.entries(state(s)?.harvests??{})){const count=gemsFor(h),offset=hash(key)%GEM_STATS.length;for(let i=0;i<GEM_STATS.length;i++){const first=(i-offset+GEM_STATS.length)%GEM_STATS.length,n=count>first?Math.floor((count-1-first)/GEM_STATS.length)+1:0;add(GEM_STATS[i],h.tier,n*5);}}
 for(const t of state(s)?.tasks??[])if(t.gem!==false)add(GEM_STATS[hash(t.source)%GEM_STATS.length],t.chapter,5);
 return bank;
}
export function cultivationRevision(s:GameState){const c=state(s);return c?Object.values(c.harvests).reduce((sum,h)=>sum+h.count,0)+c.tasks.length:0;}
export function materialStock(s:GameState,tier:number){
 const c=state(s);if(!c)return redemptionStoneBalance(s,tier);let total=redemptionStoneBalance(s,tier)+Object.values(c.harvests).filter(h=>h.tier===tier).reduce((n,h)=>n+stonesFor(h),0)+c.tasks.filter(t=>t.chapter===tier).length*3;
 for(const [id,entry]of Object.entries(c.dismantled??{})){const yieldPerItem=dismantlingYield(id);if(yieldPerItem?.tier===tier)total+=entry.count*yieldPerItem.count;}
 for(const t of c.syntheses){if(t.tier===tier)total-=3;if(t.tier+1===tier)total++;}
 for(const t of s.forging.transactions)if(t.kind==='enhance'&&t.materialTier===tier)total-=t.materialCount??0;
 return total;
}
export const materialBalance=(s:GameState)=>[1,2,3,4,5].map(tier=>`${MATERIAL_TIER_NAMES[tier]} ${materialStock(s,tier)}`).join(' · ');
interface Host {state():GameState;materialBoost?():boolean;changed():void;id(prefix:string):string;availability():{available:boolean;reason:string};dismantlingAvailability?():{available:boolean;reason:string};emit(type:string,text:string,extra?:Record<string,unknown>):void}
export class CultivationRewards {
 constructor(private host:Host){}
 private get s(){return this.host.state();}
 private get c(){return this.s.forging.cultivation??=freshCultivation();}
 dismantling(item:string,mode:DismantlingMode='one'){
  const s=this.s,id=canonicalItem(item),access=this.host.dismantlingAvailability?.()??this.host.availability(),entries:{id:string;count:number;tier:number;materials:number;owned:number}[]=[],materials:Record<number,number>={};let reason=access.available?'':access.reason;
  const ids=mode==='all'?Object.keys(s.inventory).sort():[id];
  for(const key of ids){const result=dismantlingYield(key),owned=s.inventory[key]??0,count=mode==='one'?Math.min(1,owned-1):owned-1;if(!result||count<=0)continue;entries.push({id:key,count,tier:result.tier,materials:count*result.count,owned});materials[result.tier]=(materials[result.tier]??0)+count*result.count;}
  if(!['one','stack','all'].includes(mode))reason=et('dismantle.invalid');
  else if(!entries.length)reason=et(mode==='all'?'dismantle.empty':'dismantle.keepOne');
  if(entries.some(e=>(state(s)?.dismantled?.[e.id]?.count??0)+e.count>1e7)||[1,2,3,4,5].some(tier=>materialStock(s,tier)+(materials[tier]??0)>1e8))reason=et('dismantle.capacity');
  const count=entries.reduce((sum,e)=>sum+e.count,0),token=JSON.stringify([s.sequence,id,mode,entries]);
  return {id,mode,entries,materials,count,allowed:!reason,reason,token};
 }
 dismantle(item:string,mode:DismantlingMode,token:string){
  const q=this.dismantling(item,mode);if(!q.allowed||token!==q.token)return false;
  const s=this.s;this.host.id('equipment-dismantle');const sequence=s.sequence,ledger=this.c.dismantled??={};
  for(const e of q.entries){s.inventory[e.id]-=e.count;const count=(ledger[e.id]?.count??0)+e.count;ledger[e.id]={count,sequence};s.receipts['dismantled:'+e.id]=dismantlingReceipt(e.id,count,sequence);}
  this.host.changed();this.host.emit('forge',et('dismantle.done',{count:q.count,materials:Object.entries(q.materials).map(([tier,count])=>`${materialName(Number(tier))} ×${count}`).join(' · ')}));return true;
 }
 private credit(delta:Record<string,number>){const s=this.s,messages:string[]=[];let batch=this.c.gemBatches[this.c.gemBatches.length-1];for(const [key,amount]of Object.entries(delta)){if(!amount)continue;if(!batch||batch.after!==s.gems.transactions.length){batch={after:s.gems.transactions.length,bank:{}};this.c.gemBatches.push(batch);}batch.bank[key]=(batch.bank[key]??0)+amount;const take=Math.min(amount,GEM_POLICY.capacity-(s.gems.bank[key]??0));if(take)s.gems.bank[key]=(s.gems.bank[key]??0)+take;if(take<amount){const rest=amount-take;s.gems.pending.bank[key]=(s.gems.pending.bank[key]??0)+rest;s.gems.pendingSources??={};const pending=s.gems.pendingSources['cultivation:overflow:0']??={};pending[key]=(pending[key]??0)+rest;}const [stat,tier]=key.split(':');messages.push(`${({'power':'伤害','maxHp':'生命','armor':'护甲','criticalChance':'暴击率','criticalDamage':'暴击伤害'} as Record<string,string>)[stat]}宝石${MATERIAL_TIER_NAMES[Number(tier)]}阶 ×${amount/5}`);}s.gems.revision++;return messages;}
 /** Real death only. Existing supply life receipts also reject save/reload duplicates. */
 defeat(e:EnemyState){const s=this.s;if(e.hp>0||e.phase!=='dead'||e.trainingEnemy||campaignFighter(e)?.drops===false||!playableArea(s.area))return false;const cycle=(e.respawnCount??0)+1;if(Number(s.receipts[`supply-cycle:${s.area}:${e.id}`]??0)<cycle)return false;const slot=`${s.area}:${e.id}`,seen=Number(s.receipts['cultivation:life:'+slot]??0);if(cycle<=seen)return false;const tier=cultivationEnemyTier(e.level??1,s.area),kind=kindOf(e),key=`${slot}:${tier}:${kind}`,h=this.c.harvests[key]??={area:s.area,enemy:e.id,tier,kind,count:0,cycle:0},stones=stonesFor(h),gems=gemsFor(h),materialBoost=BUILD_PROFILE.name!=='dev'&&!!this.host.materialBoost?.();h.earnedGems??=gemsFor(h);h.count++;if(materialBoost){h.bonusCount=(h.bonusCount??0)+1;s.receipts['cultivation:boost:'+slot]=Number(s.receipts['cultivation:boost:'+slot]??0)+1;}h.cycle=cycle;s.receipts['cultivation:life:'+slot]=cycle;const received=stonesFor(h)-stones,newGem=gemsFor(h)>gems,gemKey=gemBankKey(GEM_STATS[(hash(key)%GEM_STATS.length+gems)%GEM_STATS.length],tier),messages=this.credit(newGem?{[gemKey]:5}:{});if(received)messages.unshift(`${materialName(tier)} ×${received}`);this.host.changed();if(messages.length)this.host.emit('reward',(materialBoost?'战利品已自动收集 · 材料加成 · ':'战利品已自动收集 · ')+messages.join(' · '),{source:`cultivation:${slot}:${cycle}`,materialTier:tier,materialCount:received,materialBoost});return true;}
 /** Call only after the real quest/event completion receipt was written. */
 reward(source:string,chapter:number,kind:'task'='task'){const gift={source,chapter,gem:false as const};if(kind!=='task'||!taskValid(this.s,gift)||this.c.tasks.some(t=>t.source===source))return false;this.c.tasks.push(gift);const messages=this.credit({});messages.unshift(`${materialName(chapter)} ×3`);this.host.changed();this.host.emit('reward','培养奖励 · '+messages.join(' · '),{source});return true;}
 synthesis(tier:number){const s=this.s,access=this.host.availability(),gold=tier*5,stock=materialStock(s,tier),token=JSON.stringify([s.sequence,tier,stock,s.player.gold,s.progression.level]);let reason=access.available?'':access.reason;if(!integer(tier,4,1))reason='请选择Ⅰ至Ⅳ阶强化石';else if(s.progression.level<MATERIAL_TIER_LEVELS[tier])reason=`角色Lv${MATERIAL_TIER_LEVELS[tier]}开放${materialName(tier+1)}合成`;else if(stock<3)reason=`需要3枚${materialName(tier)}`;else if(s.player.gold<gold)reason='金币不足';return {allowed:!reason,reason,tier,stock,gold,token};}
 synthesize(tier:number,token:string){const q=this.synthesis(tier);if(!q.allowed||q.token!==token)return false;const t={request:this.host.id('stone-synthesis'),tier,gold:q.gold,level:this.s.progression.level};this.c.syntheses.push(t);this.s.player.gold-=q.gold;this.s.receipts[t.request]=JSON.stringify(t);this.host.changed();this.host.emit('forge',`合成${materialName(tier+1)} ×1`);return true;}
}
export function validateCultivation(s:GameState){
 const c=state(s);if(!c)return;const fail=():never=>{throw new Error('无效的分级培养材料记录');};if(!plain(c)||!exact(c,['version','harvests','tasks','syntheses','gemBatches',...(c.dismantled===undefined?[]:['dismantled'])])||c.version!==1||!plain(c.harvests)||!Array.isArray(c.tasks)||!Array.isArray(c.syntheses)||!Array.isArray(c.gemBatches)||c.gemBatches.length>s.gems.transactions.length+1||c.tasks.length>4096||c.syntheses.length>2048)return fail();const counts=new Map<string,number>(),cycles=new Map<string,number>(),boosts=new Map<string,number>();
 if(c.dismantled!==undefined){if(!plain(c.dismantled))return fail();for(const [id,entry]of Object.entries(c.dismantled)){if(!dismantlingYield(id)||!s.inventory[id]||!plain(entry)||!exact(entry,['count','sequence'])||!integer(entry.count,1e7,1)||!integer(entry.sequence,s.sequence,1)||s.receipts['dismantled:'+id]!==dismantlingReceipt(id,entry.count,entry.sequence))return fail();}}
 for(const key of Object.keys(s.receipts))if(key.startsWith('dismantled:')&&!c.dismantled?.[key.slice(11)])return fail();
 for(const [key,h]of Object.entries(c.harvests)){if(!plain(h)||!exact(h,['area','enemy','tier','kind','count','cycle',...(h.bonusCount===undefined?[]:['bonusCount']),...(h.earnedGems===undefined?[]:['earnedGems'])])||!playableArea(h.area)||!integer(h.tier,5,1)||!['ordinary','elite','boss'].includes(h.kind)||!integer(h.count,1e7,1)||!integer(h.cycle,1e7,1)||h.count>h.cycle||h.earnedGems!==undefined&&!integer(h.earnedGems,gemsFor({...h,earnedGems:undefined}))||h.bonusCount!==undefined&&(!integer(h.bonusCount,h.count,1)||BUILD_PROFILE.name==='dev')||key!==`${h.area}:${h.enemy}:${h.tier}:${h.kind}`)return fail();const e=enemy(s,h.area,h.enemy),slot=`${h.area}:${h.enemy}`;if(!e||e.trainingEnemy||kindOf(e)!==h.kind||h.tier>cultivationEnemyTier(e.level??1,h.area)||Number(s.receipts[`supply-cycle:${slot}`]??0)<h.cycle||Number(s.receipts[`cultivation:life:${slot}`]??0)<h.cycle||h.cycle>(e.respawnCount??0)+1||e.hp>0&&h.cycle===(e.respawnCount??0)+1)return fail();
 if(e.respawnSeconds?Number(s.receipts[`hunt-cycle:${slot}`]??0)<h.cycle:s.receipts[`kill:${slot}`]!==true)return fail();
 if(e.bossId&&Number(s.receipts[`boss:v3:${slot}:life`]??-1)<h.cycle-1)return fail();counts.set(slot,(counts.get(slot)??0)+h.count);boosts.set(slot,(boosts.get(slot)??0)+(h.bonusCount??0));cycles.set(slot,Math.max(cycles.get(slot)??0,h.cycle));}
 for(const [slot,count]of counts)if(count>(cycles.get(slot)??0)||s.receipts[`cultivation:life:${slot}`]!==cycles.get(slot)||Number(s.receipts[`cultivation:boost:${slot}`]??0)!==boosts.get(slot))return fail();for(const key of Object.keys(s.receipts))if((key.startsWith('cultivation:life:')&&!counts.has(key.slice(17)))||(key.startsWith('cultivation:boost:')&&!boosts.get(key.slice(18))))return fail();
 const granted:Record<string,number>={};let after=-1;for(const batch of c.gemBatches){if(!plain(batch)||!exact(batch,['after','bank'])||!integer(batch.after,s.gems.transactions.length)||batch.after<=after||!plain(batch.bank)||!Object.keys(batch.bank).length)return fail();after=batch.after;for(const [key,amount]of Object.entries(batch.bank)){if(!/^(power|maxHp|armor|criticalChance|criticalDamage):[1-5]$/.test(key)||!integer(amount,1e8,1)||amount%5)return fail();granted[key]=(granted[key]??0)+amount;}}const expected=cultivationGemBank(s);if(Object.keys(granted).length!==Object.keys(expected).length||Object.entries(granted).some(([key,n])=>n!==expected[key]))return fail();
 const sources=new Set<string>();for(const t of c.tasks){if(!plain(t)||!exact(t,['source','chapter',...(t.gem===undefined?[]:['gem'])])||t.gem!==undefined&&t.gem!==false||!taskValid(s,t)||sources.has(t.source))return fail();sources.add(t.source);}
 let sequence=0;const spent=[0,0,0,0,0,0];for(const t of c.syntheses){if(!plain(t)||!exact(t,['request','tier','gold','level'])||!integer(t.tier,4,1)||!integer(t.level,s.progression.level,MATERIAL_TIER_LEVELS[t.tier])||t.gold!==t.tier*5||typeof t.request!=='string'||!/^stone-synthesis:\d+$/.test(t.request)||s.receipts[t.request]!==JSON.stringify(t))return fail();const n=Number(t.request.split(':')[1]);if(n<=sequence||n>s.sequence)return fail();sequence=n;spent[t.tier]+=3;spent[t.tier+1]--;}
 if(Object.keys(s.receipts).filter(k=>k.startsWith('stone-synthesis:')).length!==c.syntheses.length)return fail();for(let tier=1;tier<=5;tier++)if(!integer(materialStock(s,tier)))return fail();
}
