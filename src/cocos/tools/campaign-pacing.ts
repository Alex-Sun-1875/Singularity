/** Read-only campaign source/pacing audit. Run from src/cocos:
 * npx tsx tools/campaign-pacing.ts --output test-results/campaign-pacing.json
 * Reference calendar/action budgets are design targets, never measured play time.
 */
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {AREAS} from '../assets/scripts/features/world/data/WorldData';
import {playableArea,chapterForArea,JOURNEY_TASKS} from '../assets/scripts/features/journey/data/ChapterJourney';
import {CAMPAIGN_EVENTS} from '../assets/scripts/features/campaign/data/CampaignEvents';
import {FIELD_QUESTS} from '../assets/scripts/features/campaign/data/FieldQuests';
import {CHAPTER_TWO_SIDE_QUESTS} from '../assets/scripts/features/campaign/data/ChapterTwoSideQuests';
import {CAMPAIGN_STAGES,campaignStageKey} from '../assets/scripts/features/journey/data/CampaignStages';
import {CAMPAIGN_PHASES,CAMPAIGN_MAX_LEVEL,CAMPAIGN_TOTAL_EXPERIENCE,CAMPAIGN_PACING,CAMPAIGN_CHAPTER_BUDGETS,cumulativeXp} from '../assets/scripts/features/progression/data/CampaignProgression';

import {campaignSourceReachability,campaignExperienceSources,campaignExperienceView,campaignExperienceQuote,campaignStageExperienceView} from '../assets/scripts/features/progression/data/CampaignExperience';
import {CAMPAIGN_EQUIPMENT_GROWTH,equipmentGrowthPlan} from '../assets/scripts/features/equipment/data/CampaignEquipmentGrowth';
import {campaignSourceMaterials} from '../assets/scripts/features/progression/common/CampaignRewards';
import {awardXp} from '../assets/scripts/features/progression/common/Progression';
import {EQUIPMENT} from '../assets/scripts/features/equipment/data/Equipment';
import {LIFECYCLE_ITEMS} from '../assets/scripts/features/equipment/data/EquipmentLifecycle';
import {itemForgingView} from '../assets/scripts/features/crafting/common/EquipmentForging';
import type {AreaDef,WorldQuery} from '../assets/scripts/core/Contracts';
import {forgingLevelCap,forgingNextUnlock} from '../assets/scripts/features/crafting/data/EquipmentForging';
import {gemTierForLevel,gemSocketCapForLevel} from '../assets/scripts/features/gems/data/Gems';
import {materialStock,materialTierForLevel} from '../assets/scripts/features/crafting/common/CultivationRewards';

const args=process.argv.slice(2),option=(key:string,fallback:string)=>{const index=args.indexOf('--'+key);return index<0?fallback:args[index+1];};
const economyProfile=option('economy-profile','full');
if(!['full','typical'].includes(economyProfile))throw new Error('Economy profile must be full or typical');
const hash=(value:string|Buffer)=>createHash('sha256').update(value).digest('hex');
const allAreas=[...new Map(Object.values(AREAS).map(area=>[area.id,area])).values()];
const possible=campaignSourceReachability(allAreas,true),nonrandom=campaignSourceReachability(allAreas,false);
const eventObjects=allAreas.flatMap(area=>area.objects.filter(object=>object.action==='campaign_event').map(object=>({area:area.id,object,event:CAMPAIGN_EVENTS[object.eventId??'']}))).filter(row=>!!row.event);
const blockedEvents=eventObjects.filter(row=>playableArea(row.area)&&!possible.events.has(row.event.id)).map(({area,object,event})=>({area,objectId:object.id,eventId:event.id,experienceSource:event.experienceEvent??'campaign:'+event.id,missingAll:(event.requires??[]).filter(flag=>!possible.flags.has(flag)),missingAny:event.requiresAny?.length&&!event.requiresAny.some(flag=>possible.flags.has(flag))?event.requiresAny:[],dependencyProducers:[...(event.requires??[]),...(event.requiresAny??[])].filter(flag=>!possible.flags.has(flag)).map(flag=>({flag,events:Object.values(CAMPAIGN_EVENTS).filter(event=>event.sets?.includes(flag)||event.choices?.some(choice=>choice.sets.includes(flag))).map(event=>({id:event.id,area:event.area,released:playableArea(event.area)})),evidence:allAreas.flatMap(area=>area.objects.filter(object=>object.evidence===flag).map(object=>({area:area.id,id:object.id,released:playableArea(area.id)})))}))}));
const probabilisticEvents=eventObjects.filter(row=>possible.events.has(row.event.id)&&!nonrandom.events.has(row.event.id)).map(({event})=>({id:event.id,area:event.area,requires:event.requires}));
const content=[1,2].map(chapter=>{
 const areas=allAreas.filter(area=>playableArea(area.id)&&chapterForArea(area.id)===chapter),objects=areas.flatMap(area=>area.objects),events=eventObjects.filter(row=>areas.some(area=>area.id===row.area));
 return{chapter,areas:areas.length,areaIds:areas.map(area=>area.id),checkpoints:areas.filter(area=>area.checkpoint).length,interactionObjects:objects.length,actions:objects.reduce<Record<string,number>>((counts,object)=>(counts[object.action]=(counts[object.action]??0)+1,counts),{}),fixedEnemySpawns:areas.flatMap(area=>area.enemies).filter(enemy=>!enemy.respawnSeconds).length,repeatHuntingSpawns:areas.flatMap(area=>area.enemies).filter(enemy=>enemy.respawnSeconds&&!enemy.bossId).length,journeyTasks:JOURNEY_TASKS.filter(task=>task.chapter===chapter).map(task=>task.id),fieldQuests:FIELD_QUESTS.filter(quest=>quest.chapter===chapter).map(quest=>({id:quest.id,steps:quest.steps.length})),chapterTwoSideQuests:CHAPTER_TWO_SIDE_QUESTS.filter(quest=>quest.chapter===chapter).map(quest=>({id:quest.id,steps:quest.steps.length})),campaignEvents:events.length,possibleCampaignEvents:events.filter(row=>possible.events.has(row.event.id)).length,nonrandomCampaignEvents:events.filter(row=>nonrandom.events.has(row.event.id)).length};
});
const calendarEnds=CAMPAIGN_PACING.chapterEndDays,activeEnds=CAMPAIGN_PACING.chapterActiveDays.map((_,index)=>CAMPAIGN_PACING.chapterActiveDays.slice(0,index+1).reduce((n,days)=>n+days,0));
const reference=CAMPAIGN_PHASES.map((phase,index)=>{
 const previousCalendar=index?calendarEnds[index-1]:0,previousActive=index?activeEnds[index-1]:0;
 const entryXp=cumulativeXp(phase.level),exitLevel=CAMPAIGN_PHASES[index+1]?.level??CAMPAIGN_MAX_LEVEL,totalXp=cumulativeXp(exitLevel)-entryXp,activeDays=activeEnds[index]-previousActive;
 return{chapter:phase.chapter,released:phase.released,calendarEnd:calendarEnds[index],calendarDays:calendarEnds[index]-previousCalendar,activeEnd:activeEnds[index],activeDays,activeWindowMinutes:[activeDays*CAMPAIGN_PACING.minutesPerActiveDay[0],activeDays*CAMPAIGN_PACING.minutesPerActiveDay[1]],contentTargetMinutes:CAMPAIGN_CHAPTER_BUDGETS[index].pacing.requiredContentMinutes,entryLevel:phase.level,exitLevel,totalXp,referenceOnly:true,notMeasuredTime:true};
});
const stageDefinitions=CAMPAIGN_STAGES.map(stage=>({id:stage.id,chapter:stage.chapter,name:stage.name,source:campaignStageKey(stage.id),targetTotalXp:stage.targetTotalXp,completionXp:stage.experience,actualSourceBudget:campaignStageExperienceView(stage.id),authoredActions:stage.actions.map(action=>({...action}))}));
const naturalPath=option('natural','test-results/campaign-pacing-natural-first-chapter.json');
const natural=existsSync(naturalPath)?JSON.parse(readFileSync(naturalPath,'utf8')):undefined;
const materialKeys=['gold','iron','runes','cores'] as const;
const zeroMaterials=()=>({gold:0,iron:0,runes:0,cores:0});
const materialCoverage=CAMPAIGN_EQUIPMENT_GROWTH.map(plan=>{
 const entries=campaignExperienceSources(plan.chapter),story=zeroMaterials(),exploration=zeroMaterials();
 for(const entry of entries){const reward=campaignSourceMaterials(entry.source),pool=entry.category==='main'?story:exploration;for(const key of materialKeys)pool[key]+=reward[key];}
 return{chapter:plan.chapter,released:plan.released,plan,registered:{story,exploration,firstBoss:plan.released?plan.sources.firstBoss:zeroMaterials()},poolSumsMatch:plan.released?materialKeys.every(key=>story[key]===plan.sources.story[key]&&exploration[key]===plan.sources.exploration[key]):null,firstBossProof:plan.released?'native journey:boss:<chapter> once receipt':'no authored future boss/source',optionalRepeat:'Allowance only; not registered as an automatic grant.'};
});

/** Declared financial projection, not a natural playthrough: finite chapter
 * income, legal owned-item fixtures, and actual production forge/inherit APIs.
 * Native level gates remain authoritative. This does not inject stones/gems
 * or mark future chapters released; missing cultivation stock stays visible.
 */
async function projectEconomy(){
 const {GameSession}=await import('../assets/scripts/core/GameSession');
  const world:WorldQuery={move:(from,delta)=>({x:from.x+delta.x,z:from.z+delta.z}),visible:()=>true,height:()=>0};
  const arena:AreaDef={id:'PACING_ECONOMY_FIXTURE',name:'Financial fixture',subtitle:'',kind:'town',palette:'meadow',width:100,depth:100,spawn:{x:0,z:0},atlas:{x:0,z:0},exits:[],objects:[],buildings:[],obstacles:[],enemies:[],checkpoint:true};
  return(['WAR','BOW','FIR','THU'] as const).map(family=>{
   const game=new GameSession(73014,world),state=game.state,rows:{failures:unknown[];[key:string]:unknown}[]=[];game.enter(arena);
   for(const key of materialKeys)state.player[key]=0;
   for(const phase of CAMPAIGN_PHASES){
    const plan=equipmentGrowthPlan(phase.chapter)!,level=phase.endLevel;
    awardXp(state.progression,'pacing-planned-level-'+phase.chapter,cumulativeXp(level)-state.progression.totalXp);
    let income={...plan.budget},incomeEvidence:{kind:string;sourceIds?:string[];explorationXp?:number}={kind:'full finite chapter source budget'};
    if(economyProfile==='typical'){
     let exploration=zeroMaterials();const eligible=campaignExperienceSources(phase.chapter).filter(source=>source.category==='exploration').sort((a,b)=>a.source.localeCompare(b.source)),selected:string[]=[];
     let xp=0;
     if(eligible.length){
      const target=CAMPAIGN_CHAPTER_BUDGETS[phase.chapter-1].experience.typicalExplorationXp;
      for(const source of eligible){if(xp>=target)break;xp+=source.amount;selected.push(source.source);const reward=campaignSourceMaterials(source.source);for(const key of materialKeys)exploration[key]+=reward[key];}
      incomeEvidence={kind:'real registered subset reaching typical exploration XP; source feasibility fixture, not natural route',sourceIds:selected,explorationXp:xp};
     }else{
      const share=CAMPAIGN_PACING.typicalExplorationShare/(CAMPAIGN_PACING.typicalExplorationShare+CAMPAIGN_PACING.extraExplorationShare);
      exploration=Object.fromEntries(materialKeys.map(key=>[key,Math.floor(plan.sources.exploration[key]*share)])) as ReturnType<typeof zeroMaterials>;
      incomeEvidence={kind:'unreleased future design projection: typical fraction of exploration material budget; no source IDs authored'};
     }
     income=Object.fromEntries(materialKeys.map(key=>[key,plan.sources.story[key]+plan.sources.firstBoss[key]+exploration[key]])) as ReturnType<typeof zeroMaterials>;
    }
    const opening=Object.fromEntries(materialKeys.map(key=>[key,state.player[key]])),lostToWalletCap=zeroMaterials();
    for(const key of materialKeys){lostToWalletCap[key]=Math.max(0,state.player[key]+income[key]-9999);state.player[key]=Math.min(9999,state.player[key]+income[key]);}
    const beforeSpend=Object.fromEntries(materialKeys.map(key=>[key,state.player[key]]));
    const pool=LIFECYCLE_ITEMS.filter(item=>(item.chapter??99)<=phase.chapter&&(item.requiredLevel??99)<=level);
    const weapon=pool.filter(item=>item.slot==='weapon'&&item.id.endsWith('_'+family)).sort((a,b)=>(b.requiredLevel??0)-(a.requiredLevel??0)||(b.quality==='传奇'?1:0)-(a.quality==='传奇'?1:0))[0];
    if(!weapon)throw new Error('No legal phase weapon fixture');
    const chosen:{id:string;slot:Exclude<keyof typeof state.equipment,'spells'>}[]=[{id:weapon.id,slot:'weapon'}],fallback=['A01','A06','A09','A13','J03','J08'];
    for(const slot of ['head','chest','hands','feet','ringLeft','ringRight','necklace','offhand'] as const){
     if(slot==='offhand'&&(family!=='WAR'||weapon.twoHanded))continue;
     const baseSlot=slot==='ringRight'?'ringLeft':slot;
     const item=pool.filter(item=>item.slot===baseSlot&&!chosen.some(choice=>choice.id===item.id)).sort((a,b)=>(b.requiredLevel??0)-(a.requiredLevel??0)||(b.quality==='传奇'?1:0)-(a.quality==='传奇'?1:0))[0]??fallback.map(id=>EQUIPMENT[id]).find(item=>item.slot===baseSlot&&!chosen.some(choice=>choice.id===item.id))??(slot==='offhand'?EQUIPMENT.W15:undefined);
     if(item&&(item.requiredLevel??1)<=level)chosen.push({id:item.id,slot});
    }
    const transfers:unknown[]=[],failures:unknown[]=[],payments:unknown[]=[];
    for(const {id,slot} of chosen){
     const item=EQUIPMENT[id];
     const previous=state.equipment[slot];state.inventory[id]=1;state.provenance[id]='pacing-ownership-fixture';
     if(typeof previous==='string'&&previous!==id&&(itemForgingView(state,previous)?.rank??0)>0){
      const quote=game.forging.transfer(previous,id);
      if(!quote.allowed||!game.forging.inherit(previous,id,quote.token))failures.push({kind:'inherit',from:previous,to:id,reason:quote.reason});
      else transfers.push({from:previous,to:id,gold:quote.gold,after:quote.after});
     }
     if(!game.equip(id,slot==='ringRight'?'ringRight':undefined))throw new Error('Legal phase gear rejected: '+id);
     const target=item.slot==='weapon'?plan.target.mainWeaponRank:plan.target.otherSlotRank;
     while((itemForgingView(state,id)?.rank??0)<target){
      const quote=game.forging.enhancement(id);
      if(!quote.allowed||!quote.step){failures.push({kind:'unformed-cultivation',id,target,actual:itemForgingView(state,id)?.rank,reason:quote.reason,level:state.progression.level,legalRankCap:forgingLevelCap(state.progression.level),materialTier:quote.materialTier,materialRequired:quote.materialCount,materialOwned:quote.materialOwned,currencyWouldCoverQuotedStep:quote.step?materialKeys.every(key=>state.player[key]>=quote.step![key]):null});break;}
      const before=Object.fromEntries(materialKeys.map(key=>[key,state.player[key]]));
      if(!game.forging.enhance(id,quote.token))throw new Error('Quoted enhancement rejected');
      const paid=Object.fromEntries(materialKeys.map(key=>[key,Number(before[key])-state.player[key]]));
      if(materialKeys.some(key=>paid[key]!==quote.step![key]))throw new Error('Production payment differs from its quote: '+id);
      payments.push({id,rank:quote.step.rank,paid});
     }
    }
    const equipment=Object.fromEntries(Object.entries(state.equipment).filter(([slot,id])=>slot!=='spells'&&typeof id==='string').map(([slot,id])=>[slot,{id,rank:itemForgingView(state,id as string)?.rank,cap:itemForgingView(state,id as string)?.cap}]));
    const closing=Object.fromEntries(materialKeys.map(key=>[key,state.player[key]]));
    rows.push({chapter:phase.chapter,level,unlocks:{forgingRank:forgingLevelCap(level),nextRank:forgingNextUnlock(level),gemTier:gemTierForLevel(level),socketCount:gemSocketCapForLevel(level),materialTier:materialTierForLevel(level)},opening,plannedIncome:income,incomeEvidence,lostToWalletCap,beforeSpend,closing,spent:Object.fromEntries(materialKeys.map(key=>[key,Number(beforeSpend[key])-state.player[key]])),stones:Object.fromEntries([1,2,3,4,5].map(tier=>[tier,materialStock(state,tier)])),equipment,transfers,payments,failures,status:failures.length?'unformed: finite currency preparation does not supply earned cultivation materials':'declared targets formed through native gates'});
   }
   return{family,rows};
  });
}
async function main(){
const economyProjection=args.includes('--project-economy')?await projectEconomy():undefined;
const naturalQuoteMismatches=natural?Object.entries(natural.xpReceipts??{}).flatMap(([source,amount])=>{const quote=campaignExperienceQuote(source);return quote.registered&&quote.amount!==amount?[{source,artifactAmount:amount,currentAmount:quote.amount}]:[];}):[];
const measuredMilestone=natural?.milestones?.at(-1),measuredRouteSeconds=natural&&!naturalQuoteMismatches.length&&measuredMilestone?Number(measuredMilestone.time??measuredMilestone.seconds??0):0;
const workloadCoverage={scope:'Only a current matching-source natural route artifact counts as recorded action time. The rest is unverified design workload, not an estimate of how long unplayed content actually takes.',requiredContentTargetTotalMinutes:[0,1].map(index=>CAMPAIGN_CHAPTER_BUDGETS.reduce((n,phase)=>n+phase.pacing.requiredContentMinutes[index],0)),requiredTotalActiveWindowMinutes:CAMPAIGN_PACING.minutesPerActiveDay.map(minutes=>minutes*CAMPAIGN_PACING.activeDays),recordedCurrentRouteMinutes:measuredRouteSeconds/60,futureUnreleasedContentTargetMinutes:[0,1].map(index=>CAMPAIGN_CHAPTER_BUDGETS.filter(phase=>!phase.released).reduce((n,phase)=>n+phase.pacing.requiredContentMinutes[index],0)),futureUnreleasedActiveWindowMinutes:CAMPAIGN_PACING.minutesPerActiveDay.map(minutes=>minutes*CAMPAIGN_PHASES.filter(phase=>!phase.released).reduce((n,phase)=>n+CAMPAIGN_PACING.chapterActiveDays[phase.chapter-1],0)),chapters:CAMPAIGN_CHAPTER_BUDGETS.map(phase=>({chapter:phase.chapter,released:phase.released,requiredContentMinutes:phase.pacing.requiredContentMinutes,requiredContentUnits:phase.pacing.requiredContentCount,referenceUnitMinutes:phase.pacing.contentUnitMinutes,recordedNaturalRouteMinutes:phase.chapter===1?measuredRouteSeconds/60:0,status:!phase.released?'future content not released; complete workload unproven':phase.chapter===1&&measuredRouteSeconds?'one real route recorded; not full chapter content census duration':'no current natural-route timing artifact'}))};
const coverageChecks=CAMPAIGN_PHASES.filter(phase=>phase.released).map(phase=>{const view=campaignExperienceView(phase.chapter)!,stages=CAMPAIGN_STAGES.filter(stage=>stage.chapter===phase.chapter);return{chapter:phase.chapter,mainCovered:view.main.availableXp===view.main.targetXp,optionalCovered:view.exploration.availableXp===view.exploration.targetXp,stageTargetsIncrease:stages.every((stage,index)=>!index||stage.targetTotalXp>stages[index-1].targetTotalXp),lastStageTarget:stages[stages.length-1]?.targetTotalXp,chapterExitTarget:CAMPAIGN_CHAPTER_BUDGETS[phase.chapter-1].experience.exitTotalXp};});
const report={schemaVersion:2,createdUtc:new Date().toISOString(),scope:'Prerequisite/source census and workload reference. Source-only mode changes no character. Explicit --project-economy prepares isolated character levels and item ownership using finite currency; it does not supply earned stones/gems or change chapter release flags. Calendar dates are content workload targets, never calendar locks or measured action durations. Possible closure assumes successful combat/legal future level gates and unions branch outcomes, so it is a source feasibility bound rather than natural route proof.',design:{calendarDays:CAMPAIGN_PACING.calendarDays,activeDays:CAMPAIGN_PACING.activeDays,dailyActiveMinutes:CAMPAIGN_PACING.minutesPerActiveDay,totalActiveHours:CAMPAIGN_PACING.minutesPerActiveDay.map(minutes=>minutes*CAMPAIGN_PACING.activeDays/60),maximumLevel:CAMPAIGN_MAX_LEVEL,totalExperience:CAMPAIGN_TOTAL_EXPERIENCE,shares:{main:CAMPAIGN_PACING.mainShare,typicalUniqueExploration:CAMPAIGN_PACING.typicalExplorationShare,optionalRepeat:CAMPAIGN_PACING.freeCombatShare,availableUniqueExploration:CAMPAIGN_PACING.typicalExplorationShare+CAMPAIGN_PACING.extraExplorationShare},reference},workloadCoverage,stages:{definitions:stageDefinitions,observed:natural?.stageMilestones??[],observationResolutionSeconds:natural?.stageObservationResolutionSeconds,policy:'Observed times come only from real receipt snapshots. A missing stage timestamp is not interpolated from total XP or a design duration.'},naturalCultivation:natural?.cultivation??{status:'not recorded by this natural artifact'},coverageChecks,actualContent:{totalAuthoredAreas:allAreas.length,releasedAreas:allAreas.filter(area=>playableArea(area.id)).length,chapters:content},reachability:{possibleAreas:[...possible.areas].sort(),possibleFlags:[...possible.flags].sort(),nonrandomFlags:[...nonrandom.flags].sort(),blockedEvents,probabilisticEvents,limitations:'Static semantic closure does not prove physical navigation, branch compatibility, combat victory, reward affordability or action time. Nonrandom means no random discovery prerequisite, not guaranteed player completion.'},naturalRoute:natural?{status:naturalQuoteMismatches.length?'historical artifact differs from current source rules; not current pacing evidence':'source amounts match current registry; actual route scope remains limited',currentSourceAmountMismatches:naturalQuoteMismatches,artifact:naturalPath,sha256:hash(readFileSync(naturalPath)),scope:natural.scope,milestones:natural.milestones,equipmentRewards:natural.equipmentRewards}:null,rewardCoverage:{status:'actual registered sources only; future source gaps remain explicit',chapters:CAMPAIGN_PHASES.map(phase=>campaignExperienceView(phase.chapter)),sources:campaignExperienceSources()},economy:{status:economyProjection?'production-api planned financial projection; not natural acquisition proof':'material source coverage only; pass --project-economy for finite currency and native-gate preparation audit',materialCoverage,economyProfile,projection:economyProjection,projectionScope:'Owned legal same-phase items are fixtures. Only finite declared phase budgets fund cultivation; no ordinary loot, optional repeat, injected bonus stocks, gems or equipment acquisition expenses are counted. Native character-level rank gates apply; no chapter released flags or secondChapter override is used. Missing earned stones remain a declared unformed-build result. Native wallet cap losses are reported. This tests the stated forging target, not full equipment acquisition, gem economy, exploration time or future playability.'},validation:{rewardReplay:{status:'run separately; this audit does not claim a historical test log is current',test:'tests/campaign-pacing.rules.test.ts',artifact:'test-results/campaign-pacing-rules.log',scope:'Real town inspect/cache interaction, durable proof, snapshot restore, calendar advance/rollback, registered amount/unknown-source tamper rejection. These are receipt fixtures, not natural route time.'},naturalPacing:{status:measuredRouteSeconds?'current source-matching first-chapter route artifact':'pending current source-matching natural route',artifact:naturalPath,ninetyDayRouteProven:false},futureChapters:'Planning only: no full routes or measured action minutes for chapters3–8.'}};
const output=option('output','test-results/campaign-pacing.json');writeFileSync(resolve(output),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({output,coverageChecks,content,blockedEvents,probabilisticEvents,projection:economyProjection?.map(family=>({family:family.family,unformedPhases:family.rows.filter(row=>row.failures.length).length})),referenceScope:'Shared design workload only; recorded route minutes are reported separately'}));
if(coverageChecks.some(check=>!check.mainCovered||!check.optionalCovered||!check.stageTargetsIncrease||check.lastStageTarget!==check.chapterExitTarget))throw new Error('Current released source/stage coverage failed; inspect output');

}
main().catch(error=>{console.error(error);process.exitCode=1;});
