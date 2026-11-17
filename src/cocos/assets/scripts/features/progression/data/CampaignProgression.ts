/** Shared eight-chapter design budgets. Future phases are planning data only:
 * these records never unlock a map, pay XP or claim an unfinished quest exists.
 */
export const CAMPAIGN_MAX_LEVEL=80;
/** Chapters 1-2 retain the level-cost curve. Their expanded main actions share
 * cumulative stage targets. Later chapters grow
 * by a fixed amount instead of extending the early quadratic to level 80. */
export const xpToNext=(level:number)=>level>=CAMPAIGN_MAX_LEVEL?0:level<=20?100+55*(level-1)+25*(level-1)**2:10170+150*(level-20);
export function cumulativeXp(level:number){let n=0;for(let l=1;l<level;l++)n+=xpToNext(l);return n;}
export const CAMPAIGN_TOTAL_EXPERIENCE=cumulativeXp(CAMPAIGN_MAX_LEVEL);
/** A content-production target, never an elapsed-time or login requirement. */
export const CAMPAIGN_PACING={calendarDays:90,activeDays:77,minutesPerActiveDay:[60,120] as const,
 chapterEndDays:[6,15,26,38,50,63,77,90] as const,chapterActiveDays:[5,8,9,10,10,11,12,12] as const,
 mainShare:1,typicalExplorationShare:.3,freeCombatShare:0,extraExplorationShare:0,
 status:'design-target-not-ninety-day-playtest',calendarGate:false,missedDaysLoseRewards:false,
} as const;
export const CAMPAIGN_CONTENT_MINUTES=[[360,480],[600,840],[720,960],[780,1020],[840,1080],[900,1140],[960,1200],[960,1200]] as const;
const boundedLevel=(level:number)=>Math.min(CAMPAIGN_MAX_LEVEL,Math.max(1,Math.floor(level)));
export const attributePointBudget=(level:number)=>3*Math.min(19,boundedLevel(level)-1)+2*Math.max(0,boundedLevel(level)-20);
export const skillPointBudget=(level:number,secondChapter:boolean)=>Math.min(19,boundedLevel(level)-1)+Math.floor(Math.max(0,boundedLevel(level)-20)/2)+(secondChapter?2:0);
/** Player-facing levels describe the eight-chapter journey. Combat keeps the
 * established level-40 endgame scale, with gradual growth between checkpoints. */
export const COMBAT_BUDGET_ANCHORS=[[1,1],[20,20],[30,24],[40,28],[50,32],[60,35],[70,38],[80,40]] as const;
export function combatBudgetLevel(level:number):number {
 const value=Math.min(CAMPAIGN_MAX_LEVEL,Math.max(1,level));
 for(let i=1;i<COMBAT_BUDGET_ANCHORS.length;i++){
  const [end,budget]=COMBAT_BUDGET_ANCHORS[i],[start,previous]=COMBAT_BUDGET_ANCHORS[i-1];
  if(value<=end)return previous+(budget-previous)*(value-start)/(end-start);
 }
 return 40;
}

export const CAMPAIGN_PHASES=[
 {chapter:1,level:1,endLevel:10,enhance:1,recommendedBossLevel:10,bossContentLevel:10,bossDurabilityMultiplier:14,released:true},
 {chapter:2,level:11,endLevel:20,enhance:2,recommendedBossLevel:20,bossContentLevel:18,bossDurabilityMultiplier:16,released:true},
 {chapter:3,level:21,endLevel:30,enhance:3,recommendedBossLevel:30,bossContentLevel:30,bossDurabilityMultiplier:17,released:false},
 {chapter:4,level:31,endLevel:40,enhance:4,recommendedBossLevel:40,bossContentLevel:40,bossDurabilityMultiplier:18,released:false},
 {chapter:5,level:41,endLevel:50,enhance:5,recommendedBossLevel:50,bossContentLevel:50,bossDurabilityMultiplier:18.5,released:false},
 {chapter:6,level:51,endLevel:60,enhance:6,recommendedBossLevel:60,bossContentLevel:60,bossDurabilityMultiplier:19,released:false},
 {chapter:7,level:61,endLevel:70,enhance:7,recommendedBossLevel:70,bossContentLevel:70,bossDurabilityMultiplier:19.5,released:false},
 {chapter:8,level:71,endLevel:80,enhance:8,recommendedBossLevel:80,bossContentLevel:80,bossDurabilityMultiplier:20,released:false},
] as const;
export type CampaignPhase=typeof CAMPAIGN_PHASES[number];
export const campaignPhase=(level:number)=>CAMPAIGN_PHASES.find(p=>level<=p.endLevel)??CAMPAIGN_PHASES[7];

/** Existing main receipts retained as source identities, not frozen XP awards.
 * Audit tools resolve these IDs against Journey/Campaign and actual spawns.
 * Optional encounters, investigations and archives belong to exploration;
 * hunting and re-fights remain free alternatives rather than a requirement.
 */
export const RELEASED_CHAPTER_XP_SOURCES:Record<number,{story:string[];fixedFirstClear:string[]}>= {
 1:{story:['journey:task:border-traces','journey:task:border-mill','journey:task:border-hunt','journey:task:border-camp','journey:task:border-watch','M1_XP_1','M2_XP_1','M2_XP_2'],fixedFirstClear:[
  'enemy:S07:s07-lane-raider','enemy:S07:s07-lane-shield','enemy:S07:s07-mill-archer',
  'enemy:S07:campaign-mill-hound-a','enemy:S07:campaign-mill-hound-b',
  'enemy:S09:s09-tax-shield','enemy:S09:s09-back-archer','enemy:S09:s09-tax-raider','enemy:S09:s09-back-raider',
  'enemy:U1-03:campaign-U1-03-U1-4-1','enemy:U1-03:u103-prospector-raider','enemy:U1-03:campaign-U1-03-U1-2-3',
  'enemy:S10:s10-captain',
 ]},
 2:{story:['journey:task:highland-front','journey:task:highland-workers','journey:task:highland-hunt','journey:task:highland-ridge','journey:task:highland-oath','M3_XP_1','M4_XP_1','M4_XP_2'],fixedFirstClear:[
  'enemy:H03:campaign-H03-U1-1-1','enemy:H03:campaign-H03-R2-1-2',
  'enemy:H03:campaign-workshop-crawler','enemy:H03:campaign-workshop-spitter','enemy:H03:campaign-workshop-hound-a','enemy:H03:campaign-workshop-hound-b',
  'enemy:H08:campaign-H08-BOSS_R2-1','enemy:H08:campaign-H08-R2-2-2','enemy:H08:campaign-H08-R2-2-3',
 ]},
};

/** Exit includes the next chapter's entry level. The complete main route alone
 * covers that target. Unique exploration adds an optional 30%; neither a full
 * exploration clear nor repeat combat is required for chapter progression.
 * Future source allocations stay unassigned until real content is authored.
 */
export const CAMPAIGN_CHAPTER_BUDGETS=CAMPAIGN_PHASES.map((phase,index)=>{
 const entryTotalXp=cumulativeXp(phase.level),exitLevel=CAMPAIGN_PHASES[index+1]?.level??CAMPAIGN_MAX_LEVEL;
 const exitTotalXp=cumulativeXp(exitLevel),sources=RELEASED_CHAPTER_XP_SOURCES[phase.chapter],requiredXp=exitTotalXp-entryTotalXp;
 const mainXp=requiredXp,typicalExplorationXp=Math.round(requiredXp*CAMPAIGN_PACING.typicalExplorationShare),freeCombatXp=0;
 const activeDays=CAMPAIGN_PACING.chapterActiveDays[index];
 return {...phase,experience:{entryTotalXp,beforeBossTotalXp:cumulativeXp(phase.recommendedBossLevel),exitLevel,exitTotalXp,
  requiredXp,requiredStoryAndFixedXp:mainXp,mainXp,typicalExplorationXp,freeCombatXp,extraExplorationXp:freeCombatXp,uniqueExplorationXp:typicalExplorationXp+freeCombatXp,
  mandatoryStory:{status:phase.released?'resolve-existing-source-receipts':'unallocated-planning',sourceIds:sources?.story??[]},
  fixedFirstClear:{status:phase.released?'resolve-existing-source-receipts':'unallocated-planning',sourceIds:sources?.fixedFirstClear??[]},
  optional:{requiredXp:0,availableXp:typicalExplorationXp,policy:'optional exploration adds growth; no mandatory full clear'},
  repeatCombat:{requiredXp:0,targetXp:freeCombatXp,policy:'optional hunting and re-fights; no calendar gate or mandatory daily login'},
 },pacing:{chapterEndDay:CAMPAIGN_PACING.chapterEndDays[index],activeDays,averageXpPerActiveDay:requiredXp/activeDays,
  requiredContentMinutes:CAMPAIGN_CONTENT_MINUTES[index],
  requiredContentCount:Math.ceil(CAMPAIGN_CONTENT_MINUTES[index][0]/25),contentUnitMinutes:25,
  status:phase.released?'authored-content-duration-needs-measurement':'future-content-production-target-only',
 },ttk:{reference:'same-chapter normal equipment, legal skill points, active combat',normalSeconds:[3,6] as const,eliteSeconds:[10,18] as const,
  bossSeconds:phase.chapter===1?[45,70] as const:[60,90] as const,
  bareTimeRatio:[1.5,2.5] as const,developedTimeRatio:[.65,.85] as const,
  status:phase.released?'requires-real-encounter-evidence':'future-content-target-only',
 }};
});

/** Separate source coverage from a planned target without inventing rewards. */
export function chapterExperienceCoverage(chapter:number,storyXp:number,fixedFirstClearXp:number){
 const budget=CAMPAIGN_CHAPTER_BUDGETS.find(p=>p.chapter===chapter);if(!budget)return null;
 const authoredXp=storyXp+fixedFirstClearXp,required=budget.experience.mainXp;
 return {chapter,storyXp,fixedFirstClearXp,authoredXp,requiredXp:required,shortfallXp:Math.max(0,required-authoredXp),
  optionalXpRequired:0,optionalXpAvailable:budget.experience.typicalExplorationXp,extraExplorationXp:budget.experience.extraExplorationXp,repeatCombatXpRequired:0,covered:authoredXp>=required};
}
