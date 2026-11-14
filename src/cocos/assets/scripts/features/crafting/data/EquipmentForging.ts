import {EQUIPMENT,type ItemDef} from '../../equipment/data/Equipment';

export const FORGING_GOLD=[15,25,40,60,90,130,200,280,400,600,850,1200,1600,2100,2800] as const;
const IRON=[1,1,2,2,3,4,5,6,8,10,12,15,18,22,26];
const QUALITY_COST:Record<string,number>={'普通':80,'精良':90,'稀有':100,'史诗':110,'传奇':125,'神器':150};
export const MAX_FORGING_EXPERIENCE=10_000_000;
export const FORGING_TRANSACTION_LIMIT=2048;
export function forgingSlot(item:ItemDef){return item.kind==='ring'?'ring':item.slot;}
export function forgingWeight(item:ItemDef){return item.slot==='weapon'?(item.twoHanded?1:.8):item.slot==='offhand'?.2:.65;}
export function forgingCost(item:ItemDef,rank:number){const weight=Math.round(forgingWeight(item)*100),quality=QUALITY_COST[item.quality]??100,baseIron=IRON[rank-1],mainIron=Math.max(1,Math.floor((baseIron*80+50)/100)),iron=item.slot==='offhand'?baseIron-mainIron:item.slot==='weapon'&&!item.twoHanded?mainIron:Math.max(1,Math.ceil(baseIron*weight/100));return {gold:Math.max(1,Math.ceil(FORGING_GOLD[rank-1]*quality*weight/10000)),iron};}
export function forgingThreshold(item:ItemDef,rank:number){let value=0;for(let i=1;i<=rank;i++)value+=forgingCost(item,i).gold;return value;}
export function forgingRank(item:ItemDef,experience:number,cap=item.maxEnhance??3){let rank=0;while(rank<cap&&experience>=forgingThreshold(item,rank+1))rank++;return rank;}
export function forgingStep(item:ItemDef,experience:number,cap:number){const rank=forgingRank(item,experience,cap);if(rank>=cap)return null;const full=forgingCost(item,rank+1),experienceNeeded=forgingThreshold(item,rank+1)-experience;return {rank:rank+1,experience:experienceNeeded,gold:experienceNeeded,iron:Math.ceil(full.iron*experienceNeeded/full.gold)};}
export function forgingBonus(item:ItemDef,rank:number){return {maxHp:item.slot==='weapon'||item.slot==='offhand'?0:rank*(item.kind==='armor'?3:2),armor:0,power:item.slot==='weapon'||item.slot==='offhand'?Math.round(rank*2*forgingWeight(item)*10)/10:0};}
export function forgingCraftFee(item:string){const d=EQUIPMENT[item];return d?Math.ceil((d.slot==='weapon'?30:20)*(QUALITY_COST[d.quality]??100)/100):0;}

export type ForgingStat='power'|'criticalChance'|'criticalDamage'|'strength'|'dexterity'|'intellect'|'vitality'|'maxHp'|'armor';
export interface ForgingRoll {rank:number;stat:ForgingStat;amount:number;added:boolean}
export interface ForgingAffix {stat:ForgingStat;value:number}
export interface RandomForgingBonus {maxHp:number;armor:number;power:number;criticalChance:number;criticalDamage:number;strength:number;dexterity:number;intellect:number;vitality:number}
export const freshForgingBonus=():RandomForgingBonus=>({maxHp:0,armor:0,power:0,criticalChance:0,criticalDamage:0,strength:0,dexterity:0,intellect:0,vitality:0});
export const FORGING_STAT_NAMES:Record<ForgingStat,string>={power:'伤害加成',criticalChance:'暴击率',criticalDamage:'暴击伤害',strength:'力量',dexterity:'敏捷',intellect:'智力',vitality:'体质',maxHp:'生命上限',armor:'护甲'};
export const forgingCapacity=(item:ItemDef)=>['传奇','神器'].includes(item.quality)?3:['稀有','史诗'].includes(item.quality)?2:1;
export const forgingAffixCount=(item:ItemDef,rank:number)=>Math.min(forgingCapacity(item),rank>=6?3:rank>=3?2:rank>=1?1:0);
const tenth=(value:number)=>Math.round(value*10)/10;
export function forgingPool(item:ItemDef):ForgingStat[]{
 if(item.slot==='offhand')return ['power','criticalChance','maxHp','armor'];
 if(item.slot==='weapon')return ['power','criticalChance','criticalDamage',item.kind==='sword'?'strength':item.kind==='bow'?'dexterity':'intellect',...(item.kind==='sword'?['vitality' as const]:[])];
 if(item.kind==='armor')return ['maxHp','armor','vitality',...(item.set==='wind'?['dexterity' as const]:item.set==='ember'||item.set==='bell'?['intellect' as const]:['strength' as const])];
 return ['maxHp','criticalChance','criticalDamage','vitality','strength','dexterity','intellect'];
}
export function forgingRange(item:ItemDef,stat:ForgingStat){
 const quality=({'普通':.85,'精良':.9,'稀有':1,'史诗':1.05,'传奇':1.1,'神器':1.2} as Record<string,number>)[item.quality]??1,weight=forgingWeight(item),scale=quality*weight;
 if(['strength','dexterity','intellect','vitality'].includes(stat))return {min:1,max:['传奇','神器'].includes(item.quality)?2:1,step:1};
 if(stat==='maxHp')return {min:Math.max(1,Math.round(4*scale)),max:Math.max(1,Math.round(6*scale)),step:1};
 const range=stat==='power'?[1.2,1.6]:stat==='criticalChance'?[.5,.8]:stat==='criticalDamage'?[3,5]:[.4,.7];
 return {min:Math.max(.1,tenth(range[0]*scale)),max:Math.max(.1,tenth(range[1]*scale)),step:.1};
}
export function forgingAffixes(rolls:readonly ForgingRoll[],rank:number):ForgingAffix[]{const values=new Map<ForgingStat,number>();for(const roll of rolls){if(roll.rank>rank)break;values.set(roll.stat,tenth((values.get(roll.stat)??0)+roll.amount));}return Array.from(values,([stat,value])=>({stat,value}));}
export function forgingCandidates(item:ItemDef,rank:number,rolls:readonly ForgingRoll[]){
 const current=forgingAffixes(rolls,rank-1),added=current.length<forgingAffixCount(item,rank),stats=added?forgingPool(item).filter(stat=>!current.some(a=>a.stat===stat)):current.map(a=>a.stat);
 return {added,candidates:stats.map(stat=>({stat,...forgingRange(item,stat),probability:1/stats.length}))};
}
/** Stable item/rank draws reuse a result after reload, respec or round-trip inheritance. */
function forgingWord(seed:number,key:string){let n=seed>>>0;for(let i=0;i<key.length;i++)n=Math.imul(n^key.charCodeAt(i),16777619)>>>0;n^=n>>>16;n=Math.imul(n,0x7feb352d);n^=n>>>15;return (n^(n>>>16))>>>0;}
export function forgingNextRoll(seed:number,item:ItemDef,rank:number,rolls:readonly ForgingRoll[]):ForgingRoll{
 const q=forgingCandidates(item,rank,rolls),candidate=q.candidates[forgingWord(seed,`forge-v2:${item.id}:${rank}:stat`)%q.candidates.length],count=Math.round((candidate.max-candidate.min)/candidate.step)+1,amount=tenth(candidate.min+(forgingWord(seed,`forge-v2:${item.id}:${rank}:amount`)%count)*candidate.step);
 return {rank,stat:candidate.stat,amount,added:q.added};
}
export function forgingRolls(seed:number,item:ItemDef,rank:number):ForgingRoll[]{const rolls:ForgingRoll[]=[];for(let i=1;i<=rank;i++)rolls.push(forgingNextRoll(seed,item,i,rolls));return rolls;}
export function randomForgingBonus(rolls:readonly ForgingRoll[],rank:number):RandomForgingBonus{const result=freshForgingBonus();for(const a of forgingAffixes(rolls,rank))result[a.stat]=a.value;result.maxHp+=4*result.vitality;return result;}
export function forgingValue(stat:ForgingStat,value:number){return `+${Number(value.toFixed(1))}${['power','criticalChance','criticalDamage','armor'].includes(stat)?'%':''}`;}
export function forgingAffixText(a:ForgingAffix){return `${FORGING_STAT_NAMES[a.stat]} ${forgingValue(a.stat,a.value)}`;}
