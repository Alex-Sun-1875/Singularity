import {CAMPAIGN_PHASES,CAMPAIGN_PACING} from '../../progression/data/CampaignProgression';

export interface CampaignMaterialBudget {gold:number;iron:number;runes:number;cores:number}
export type EquipmentRewardKind='story'|'exploration'|'firstBoss'|'optionalRepeat';
const materials=(gold=0,iron=0,runes=0,cores=0):CampaignMaterialBudget=>({gold,iron,runes,cores});
const MAIN_RANKS=[1,2,3,4,4,5,5,6] as const;
const OTHER_RANKS=[0,1,1,1,2,2,3,4] as const;
const BUDGETS=[
 materials(450,45),materials(900,55,6,1),materials(1000,30,2),materials(1400,35,2),
 materials(1800,45,3),materials(2300,55,10,1),materials(3000,65,10,1),materials(8500,160,16,2),
] as const;
const STORY_RUNES=[0,2,0,0,1,2,2,4],EXPLORATION_RUNES=[0,2,1,1,1,4,4,6];
/** Optional repeat activity targets are audit allowances, not automatic grants.
 * A real, chapter-qualified reward source must be authored before using them. */
const REPEAT_ALLOWANCES=[
 materials(90,8),materials(180,10),materials(200,12,1),materials(280,15,1),
 materials(360,18,1),materials(460,22,2),materials(600,25,2,1),materials(1700,40,4,3),
] as const;

/** Normal cultivation keeps existing investment through inheritance and does
 * not assume an artifact drop. +7/+8 are optional artifact cultivation targets.
 * Future chapters describe production budgets; no source IDs are invented. */
export const CAMPAIGN_EQUIPMENT_GROWTH=CAMPAIGN_PHASES.map((phase,index)=>{
 const budget=BUDGETS[index],story=materials(Math.floor(budget.gold*.4),Math.floor(budget.iron*.4),STORY_RUNES[index]);
 const exploration=materials(Math.floor(budget.gold*.4),Math.floor(budget.iron*.4),EXPLORATION_RUNES[index]);
 const firstBoss=materials(budget.gold-story.gold-exploration.gold,budget.iron-story.iron-exploration.iron,budget.runes-story.runes-exploration.runes,budget.cores);
 return {chapter:phase.chapter,activeDays:CAMPAIGN_PACING.chapterActiveDays[index],released:phase.released,
  status:phase.released?'requires-verified-source-receipts':'unallocated-planning',
  target:{mainWeaponRank:MAIN_RANKS[index],otherSlotRank:OTHER_RANKS[index],cap:phase.enhance},
  budget,sources:{story,exploration,firstBoss,optionalRepeat:REPEAT_ALLOWANCES[index]},
  policy:{inheritance:true,calendarGate:false,ordinaryCombatLootIsExtra:true,optionalRepeatIsGuaranteed:false},
 };
});
export const equipmentGrowthPlan=(chapter:number)=>CAMPAIGN_EQUIPMENT_GROWTH.find(phase=>phase.chapter===chapter);

/** Divide a finite pool over verified sources in stable source-ID order.
 * Prefix differences preserve even a one-core budget across many small sources.
 * The caller owns source/receipt verification and must award each source once;
 * this pure allocator cannot make an unreleased chapter or repeat source real. */
export function equipmentSourceAllocation(chapter:number,kind:EquipmentRewardKind,weightBefore:number,sourceWeight:number,totalWeight:number):CampaignMaterialBudget {
 const plan=equipmentGrowthPlan(chapter);
 if(!plan||![weightBefore,sourceWeight,totalWeight].every(Number.isSafeInteger)||weightBefore<0||sourceWeight<=0||totalWeight<=0||weightBefore+sourceWeight>totalWeight)return materials();
 const budget=plan.sources[kind],portion=(value:number)=>Math.floor(value*(weightBefore+sourceWeight)/totalWeight)-Math.floor(value*weightBefore/totalWeight);
 return materials(portion(budget.gold),portion(budget.iron),portion(budget.runes),portion(budget.cores));
}
