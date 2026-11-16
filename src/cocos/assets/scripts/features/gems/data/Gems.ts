import type {ItemDef} from '../../equipment/data/Equipment';

export const GEM_STATS=['power','maxHp','armor','criticalChance','criticalDamage'] as const;
export type GemStat=typeof GEM_STATS[number];
export type GemTier=1|2|3|4|5;
export const GEM_STAT_NAMES:Record<GemStat,string>={power:'伤害加成',maxHp:'生命上限',armor:'护甲',criticalChance:'暴击率',criticalDamage:'暴击伤害'};
export const GEM_TIER_NAMES=['','Ⅰ','Ⅱ','Ⅲ','Ⅳ','Ⅴ'] as const;
export const GEM_POLICY={sockets:5,capacity:999999,ledgerLimit:4096,huntInterval:10,exchangeUnits:5,synthesisUnits:5} as const;
/** Standard-size costs; multiples of five make the 4/1/5 cuts exactly integral. */
export const GEM_OPEN_COST=[0,5,10,20,40] as const;
const BASE:Record<GemStat,number>={power:.2,maxHp:2,armor:.1,criticalChance:.05,criticalDamage:.5};
const SCALE=[0,1,1.5,2.25,3.375,5.0625] as const;
export const gemUnits=(item:ItemDef)=>item.slot==='offhand'?1:item.slot==='weapon'&&!item.twoHanded?4:5;
export const gemBankKey=(stat:GemStat,tier:number)=>`${stat}:${tier}`;
export const GEM_QUALITY_CAPACITY:Readonly<Record<string,number>>={'普通':0,'精良':0,'稀有':2,'史诗':3,'传奇':4,'神器':5};
export const gemCapacity=(item:Pick<ItemDef,'quality'>|undefined)=>item?GEM_QUALITY_CAPACITY[item.quality]??0:0;
export const gemEligible=(item:Pick<ItemDef,'quality'>|undefined)=>gemCapacity(item)>0;
export const GEM_TIER_LEVELS=[0,1,10,20,30,40] as const;
export const gemTierCap=(s:{progression:{level:number;secondChapter:boolean}})=>Math.max(s.progression.secondChapter?2:1,s.progression.level>=40?5:s.progression.level>=30?4:s.progression.level>=20?3:s.progression.level>=10?2:1);
export const gemAmount=(stat:GemStat,tier:number,units=5)=>Math.round(BASE[stat]*(SCALE[tier]??0)*units/5*1e6)/1e6;
export const gemValueText=(stat:GemStat,tier:number,units=5)=>`${GEM_STAT_NAMES[stat]} +${gemAmount(stat,tier,units)}${stat==='maxHp'?'':'%'}`;
export const gemOpenCost=(hole:number,units:number)=>(GEM_OPEN_COST[hole]??0)*units/5;
export const gemOpeningInvestment=(opened:number,units:number)=>GEM_OPEN_COST.slice(1,opened).reduce<number>((n,c)=>n+c*units/5,0);
