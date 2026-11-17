import type {ItemDef} from '../../equipment/data/Equipment';
import {CAMPAIGN_MAX_LEVEL} from '../../progression/data/CampaignProgression';

export const FORGING_RANK_LEVELS=[10,20,30,40,50,60,70,CAMPAIGN_MAX_LEVEL] as const;
/** Eight paid ranks preserve the accepted full fifteen-increment budget. */
export const FORGING_EQUIVALENT_RANKS=[3,6,8,10,11,12,13,15] as const;
export const FORGING_AFFIX_RANKS=[1,2,4] as const;
export const forgingLevelCap=(level:number)=>FORGING_RANK_LEVELS.filter(required=>level>=required).length;
export function forgingNextUnlock(level:number):{rank:number;level:number}|undefined {const index=FORGING_RANK_LEVELS.findIndex(required=>required>level);return index<0?undefined:{rank:index+1,level:FORGING_RANK_LEVELS[index]};}
const INCREMENT_GOLD=[15,25,40,60,90,130,200,280,400,600,850,1200,1600,2100,2800] as const;
export const FORGING_GOLD=FORGING_EQUIVALENT_RANKS.map((end,index)=>INCREMENT_GOLD.slice(index?FORGING_EQUIVALENT_RANKS[index-1]:0,end).reduce<number>((sum,cost)=>sum+cost,0));
const IRON=[1,1,2,2,3,4,5,6,8,10,12,15,18,22,26];
const QUALITY_COST:Record<string,number>={'普通':80,'精良':90,'稀有':100,'史诗':110,'传奇':125,'神器':150};
export const MAX_FORGING_EXPERIENCE=10_000_000;
export const FORGING_TRANSACTION_LIMIT=2048;
export function forgingSlot(item:ItemDef){return item.kind==='ring'?'ring':item.slot;}
export function forgingWeight(item:ItemDef){return item.slot==='weapon'?(item.twoHanded?1:.8):item.slot==='offhand'?.2:.65;}
const incrementRange=(rank:number)=>{if(!Number.isInteger(rank)||rank<1||rank>FORGING_RANK_LEVELS.length)throw new Error('无效的强化等级');return {start:rank>1?FORGING_EQUIVALENT_RANKS[rank-2]:0,end:FORGING_EQUIVALENT_RANKS[rank-1]};};
export function forgingRankWeight(rank:number){const {start,end}=incrementRange(rank);return end-start;}
/** Aggregate each covered increment, including its original rounding. */
export function forgingTierMaterials(rank:number){const {start,end}=incrementRange(rank);let runes=0,cores=0;for(let i=start+1;i<=end;i++){if(i>=7&&i<=10)runes++;if(i>=11)cores+=i<=12?1:i<=14?2:3;}return {runes,cores};}
export function forgingCost(item:ItemDef,rank:number){const {start,end}=incrementRange(rank),weight=Math.round(forgingWeight(item)*100),quality=QUALITY_COST[item.quality]??100;let gold=0,iron=0;for(let i=start;i<end;i++){const baseIron=IRON[i],mainIron=Math.max(1,Math.floor((baseIron*80+50)/100));iron+=item.slot==='offhand'?baseIron-mainIron:item.slot==='weapon'&&!item.twoHanded?mainIron:Math.max(1,Math.ceil(baseIron*weight/100));gold+=Math.max(1,Math.ceil(INCREMENT_GOLD[i]*quality*weight/10000));}return {gold,iron,...forgingTierMaterials(rank)};}
export function forgingThreshold(item:ItemDef,rank:number){let value=0;for(let i=1;i<=rank;i++)value+=forgingCost(item,i).gold;return value;}
export function forgingRank(item:ItemDef,experience:number,cap=item.maxEnhance??1){const maximum=Math.min(cap,item.maxEnhance??1,FORGING_RANK_LEVELS.length);let rank=0;while(rank<maximum&&experience>=forgingThreshold(item,rank+1))rank++;return rank;}
export function forgingStep(item:ItemDef,experience:number,cap:number){const rank=forgingRank(item,experience,cap);if(rank>=cap)return null;const full=forgingCost(item,rank+1),experienceNeeded=forgingThreshold(item,rank+1)-experience;return {rank:rank+1,experience:experienceNeeded,gold:experienceNeeded,iron:Math.ceil(full.iron*experienceNeeded/full.gold),runes:full.runes,cores:full.cores};}
export function forgingBonus(item:ItemDef,rank:number){const equivalent=rank>0?FORGING_EQUIVALENT_RANKS[Math.min(rank,8)-1]:0;return {maxHp:item.slot==='weapon'||item.slot==='offhand'?0:equivalent*(item.kind==='armor'?3:2),armor:0,power:item.slot==='weapon'||item.slot==='offhand'?Math.round(equivalent*2*forgingWeight(item)*10)/10:0};}

export type ForgingStat='power'|'criticalChance'|'criticalDamage'|'strength'|'dexterity'|'intellect'|'vitality'|'maxHp'|'armor';
export interface ForgingRoll {rank:number;stat:ForgingStat;amount:number;added:boolean}
export interface ForgingAffix {stat:ForgingStat;value:number}
export interface RandomForgingBonus {maxHp:number;armor:number;power:number;criticalChance:number;criticalDamage:number;strength:number;dexterity:number;intellect:number;vitality:number}
export const freshForgingBonus=():RandomForgingBonus=>({maxHp:0,armor:0,power:0,criticalChance:0,criticalDamage:0,strength:0,dexterity:0,intellect:0,vitality:0});
export const FORGING_STAT_NAMES:Record<ForgingStat,string>={power:'伤害加成',criticalChance:'暴击率',criticalDamage:'暴击伤害',strength:'力量',dexterity:'敏捷',intellect:'智力',vitality:'体质',maxHp:'生命上限',armor:'护甲'};
export const forgingCapacity=(item:ItemDef)=>['传奇','神器'].includes(item.quality)?3:['稀有','史诗'].includes(item.quality)?2:1;
export const forgingAffixCount=(item:ItemDef,rank:number)=>Math.min(forgingCapacity(item),FORGING_AFFIX_RANKS.filter(required=>rank>=required).length);
const tenth=(value:number)=>Math.round(value*10)/10;
export function forgingPool(item:ItemDef):ForgingStat[]{
 if(item.slot==='offhand')return ['power','criticalChance','maxHp','armor'];
 if(item.slot==='weapon')return ['power','criticalChance','criticalDamage',item.kind==='sword'?'strength':item.kind==='bow'?'dexterity':'intellect',...(item.kind==='sword'?['vitality' as const]:[])];
 if(item.kind==='armor')return ['maxHp','armor','vitality',...(item.set==='wind'?['dexterity' as const]:item.set==='ember'||item.set==='bell'?['intellect' as const]:['strength' as const])];
 return ['maxHp','criticalChance','criticalDamage','vitality','strength','dexterity','intellect'];
}
export function forgingRange(item:ItemDef,stat:ForgingStat,rank=1){
 const quality=({'普通':.85,'精良':.9,'稀有':1,'史诗':1.05,'传奇':1.1,'神器':1.2} as Record<string,number>)[item.quality]??1,weight=forgingWeight(item),scale=quality*weight,count=forgingRankWeight(rank);
 if(['strength','dexterity','intellect','vitality'].includes(stat))return {min:count,max:(['传奇','神器'].includes(item.quality)?2:1)*count,step:1};
 if(stat==='maxHp')return {min:Math.max(1,Math.round(4*scale))*count,max:Math.max(1,Math.round(6*scale))*count,step:1};
 const range=stat==='power'?[1.2,1.6]:stat==='criticalChance'?[.5,.8]:stat==='criticalDamage'?[3,5]:[.4,.7];
 return {min:tenth(Math.max(.1,tenth(range[0]*scale))*count),max:tenth(Math.max(.1,tenth(range[1]*scale))*count),step:.1};
}
export function forgingAffixes(rolls:readonly ForgingRoll[],rank:number):ForgingAffix[]{const values=new Map<ForgingStat,number>();for(const roll of rolls){if(roll.rank>rank)break;values.set(roll.stat,tenth((values.get(roll.stat)??0)+roll.amount));}return Array.from(values,([stat,value])=>({stat,value}));}
export function forgingCandidates(item:ItemDef,rank:number,rolls:readonly ForgingRoll[]){
 const current=forgingAffixes(rolls,rank-1),added=current.length<forgingAffixCount(item,rank),stats=added?forgingPool(item).filter(stat=>!current.some(a=>a.stat===stat)):current.map(a=>a.stat);
 return {added,candidates:stats.map(stat=>({stat,...forgingRange(item,stat,rank),probability:1/stats.length}))};
}
/** Stable item/rank draws reuse a result after reload, respec or round-trip inheritance. */
function forgingWord(seed:number,key:string){let n=seed>>>0;for(let i=0;i<key.length;i++)n=Math.imul(n^key.charCodeAt(i),16777619)>>>0;n^=n>>>16;n=Math.imul(n,0x7feb352d);n^=n>>>15;return (n^(n>>>16))>>>0;}
export function forgingNextRoll(seed:number,item:ItemDef,rank:number,rolls:readonly ForgingRoll[]):ForgingRoll{
 const q=forgingCandidates(item,rank,rolls),candidate=q.candidates[forgingWord(seed,`forge-v2:${item.id}:${rank}:stat`)%q.candidates.length],count=Math.round((candidate.max-candidate.min)/candidate.step)+1,amount=tenth(candidate.min+(forgingWord(seed,`forge-v2:${item.id}:${rank}:amount`)%count)*candidate.step);
 return {rank,stat:candidate.stat,amount,added:q.added};
}
export function forgingRolls(seed:number,item:ItemDef,rank:number):ForgingRoll[]{if(!Number.isInteger(rank)||rank<0||rank>Math.min(item.maxEnhance??1,FORGING_RANK_LEVELS.length))throw new Error('无效的强化等级');const rolls:ForgingRoll[]=[];for(let i=1;i<=rank;i++)rolls.push(forgingNextRoll(seed,item,i,rolls));return rolls;}
export function randomForgingBonus(rolls:readonly ForgingRoll[],rank:number):RandomForgingBonus{const result=freshForgingBonus();for(const a of forgingAffixes(rolls,rank))result[a.stat]=a.value;result.maxHp+=4*result.vitality;return result;}
export function forgingValue(stat:ForgingStat,value:number){return `+${Number(value.toFixed(1))}${['power','criticalChance','criticalDamage','armor'].includes(stat)?'%':''}`;}
export function forgingAffixText(a:ForgingAffix){return `${FORGING_STAT_NAMES[a.stat]} ${forgingValue(a.stat,a.value)}`;}
