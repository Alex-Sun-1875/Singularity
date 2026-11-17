import {CAMPAIGN_MAX_LEVEL,combatBudgetLevel} from './CampaignProgression';
/** Online idle has a sub-budget within the shared daily combat allowance. */
export const HUNT_EXPERIENCE_POLICY={
 dailyCap:1000,
 utcOffsetHours:8,
 rates:[100,75,50,25] as readonly number[],
} as const;
export function dailyCombatExperienceCap(level:number){return historicalDailyCombatCap(level);}
/** Original tier table, shared by the live allowance and historical validation. */
export function historicalDailyCombatCap(level:number){return level>=CAMPAIGN_MAX_LEVEL?0:level<=5?1000:level<=10?1500:level<=15?3000:level<=20?6000:6000+Math.floor((level-20)/10)*1500;}
/** Stable kill rewards: increasing level costs must never increase kill XP. */
export function huntingKillExperience(enemyLevel:number,playerLevel:number,elite=false){
 const level=Math.max(1,Math.min(CAMPAIGN_MAX_LEVEL-1,Math.floor(enemyLevel))),effective=Math.min(level,playerLevel+2);
 const difference=Math.max(0,playerLevel-level-3);
 const rate=Math.max(10,100-20*difference);
 return Math.max(1,Math.floor((4+Math.floor(.6*combatBudgetLevel(effective)))*rate/100))*(elite?3:1);
}
