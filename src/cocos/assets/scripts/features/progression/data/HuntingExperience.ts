/** Idle XP is a sub-limit of the shared daily repeat-combat allowance. */
export const HUNT_EXPERIENCE_POLICY={
 dailyCap:1000,
 utcOffsetHours:8,
 rates:[100,75,50,25] as readonly number[],
} as const;
export function dailyCombatExperienceCap(level:number){return level>=40?0:level<=5?1000:level<=10?1500:level<=15?3000:6000;}
/** Stable kill rewards: increasing level costs must never increase kill XP. */
export function huntingKillExperience(enemyLevel:number,playerLevel:number,elite=false){
 const level=Math.max(1,Math.min(39,Math.floor(enemyLevel))),effective=Math.min(level,playerLevel+2);
 const difference=Math.max(0,playerLevel-level-3);
 const rate=Math.max(10,100-20*difference);
 return Math.max(1,Math.floor((4+Math.floor(.6*effective))*rate/100))*(elite?3:1);
}
