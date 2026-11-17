import type {AreaDef,EnemySpawn} from '../../../core/Contracts';
import {CAMPAIGN_CHAPTER_BUDGETS,RELEASED_CHAPTER_XP_SOURCES} from './CampaignProgression';
import {JOURNEY_TASKS,chapterForArea,playableArea} from '../../journey/data/ChapterJourney';
import {MAIN_XP_EVENTS,CAMPAIGN_ENEMY_TEMPLATES} from '../../campaign/data/Campaign';
import {CAMPAIGN_EVENTS,type CampaignEventDef} from '../../campaign/data/CampaignEvents';
import {CAMPAIGN_BATTLES,campaignFighter} from '../../campaign/data/CampaignBattles';
import {GROWING_SCENES} from '../../equipment/data/GrowingEquipment';
import {FIELD_DISCOVERIES} from '../../campaign/data/FieldQuests';
import {RIDGE_FIXED_IDS,OATH_FIXED_IDS} from '../../campaign/data/ChapterTwoEncounters';
import {peacefulBossTarget} from '../../campaign/common/PeacefulBosses';
import {CAMPAIGN_STAGES,campaignStageKey} from '../../journey/data/CampaignStages';
import {LEGACY_CAMPAIGN_EXPERIENCE} from './LegacyCampaignExperience';

export interface CampaignExperienceSource {
 source:string;amount:number;chapter:number;category:'main'|'exploration';pool:'main'|'exploration';
 area?:string;label:string;objectId?:string;eventId?:string;enemyId?:string;proofKey?:string;weight:number;stageId?:string;
}
export type CampaignExperienceQuote=CampaignExperienceSource&{registered:true}|{source:string;amount:number;category:'other';registered:false;chapter?:undefined;pool?:undefined};
export interface CampaignSourceReachability {areas:Set<string>;flags:Set<string>;events:Set<string>;rounds:number;}
export interface CampaignExperienceExtra {source:string;chapter:number;area:string;label:string;amount:number;reason:string;}
type WeightedSource=Omit<CampaignExperienceSource,'amount'|'pool'>;
const sources=new Map<string,CampaignExperienceSource>();
let unallocatedExtra:CampaignExperienceExtra[]=[],blockedFutureDependencies:{source:string;area:string;missingAll:string[];missingAny:string[]}[]=[];
let installed=false;

/** Integer shares use physical workload, rather than the old five-task XP
 * spikes. Each stage owns one finite node pool and a completion payment. */
function distribute(entries:WeightedSource[],budget:number):void {
 const ordered=[...entries].sort((a,b)=>a.source.localeCompare(b.source)),total=ordered.reduce((n,e)=>n+e.weight,0);
 if(!ordered.length||total<=0)return;
 const amounts=ordered.map(e=>Math.floor(budget*e.weight/total));
 let remaining=budget-amounts.reduce((n,amount)=>n+amount,0);
 const remainders=ordered.map((e,i)=>({i,remainder:budget*e.weight%total})).sort((a,b)=>b.remainder-a.remainder||a.i-b.i);
 for(const {i}of remainders)if(remaining>0){amounts[i]++;remaining--;}
 ordered.forEach((entry,i)=>sources.set(entry.source,{...entry,amount:amounts[i],pool:entry.category}));
}
function installMainSources():void {
 let previousTarget=0;
 const owned=new Set<string>();
 for(const stage of CAMPAIGN_STAGES){
  const chapter=stage.chapter,budget=stage.targetTotalXp-previousTarget,entries:WeightedSource[]=[];previousTarget=stage.targetTotalXp;
  const add=(entry:Omit<WeightedSource,'chapter'|'category'|'stageId'>)=>{
   if(entries.some(value=>value.source===entry.source))return;
   if(owned.has(entry.source))throw new Error('Main XP source belongs to two stages: '+entry.source);
   owned.add(entry.source);entries.push({...entry,chapter,category:'main',stageId:stage.id});
  };
  const fixed=(source:string,weight=1)=>{const [,area,...id]=source.split(':'),enemyId=id.join(':');add({source,area,enemyId,label:enemyId,proofKey:`kill:${area}:${enemyId}`,weight});};
  for(const action of stage.actions){
   if(action.kind==='task'){
    const task=JOURNEY_TASKS.find(value=>value.id===action.taskId);if(!task)throw new Error('Missing main task: '+action.taskId);
    add({source:'journey:task:'+task.id,area:task.area,label:task.name,proofKey:'journey:task:'+task.id,weight:task.goal==='observe'?4:8});
   }
   if(action.kind==='task'||action.kind==='boss')for(const source of RELEASED_CHAPTER_XP_SOURCES[chapter].fixedFirstClear.filter(source=>source.split(':')[1]===action.area)){
    const boss=/BOSS_R/.test(source)||source==='enemy:S10:s10-captain';
    if(action.kind==='boss'&&!boss)continue;
    fixed(source,boss?6:1);
   }
   if(action.kind==='event'&&action.eventId){
    const event=CAMPAIGN_EVENTS[action.eventId];if(!event)throw new Error('Missing main event: '+action.eventId);
    const source=event.experienceEvent??'campaign:'+event.id;
    add({source,area:event.area,label:event.label,eventId:event.id,...(!event.experienceEvent?{proofKey:source}:{}),weight:4});
    for(const enemyId of event.defeatIds??[])fixed(`enemy:${event.area}:${enemyId}`);
    // A boss victory can leave its guards alive. Those kills become mandatory
    // at the following clearEncounter action, which owns their XP instead.
    if(event.clearEncounter)for(const fixedSource of RELEASED_CHAPTER_XP_SOURCES[chapter].fixedFirstClear.filter(source=>source.split(':')[1]===event.area&&!/BOSS_R/.test(source)&&source!=='enemy:S10:s10-captain'))if(!owned.has(fixedSource))fixed(fixedSource);
   }
   const id=action.flag==='read_letter'?'M1_XP_1':action.flag==='workers_departed'?'M2_XP_1':action.flag==='gate_raised'?'M2_XP_2':undefined;
   if(id){const event=MAIN_XP_EVENTS.find(event=>event.id===id)!;add({source:id,area:action.area,label:event.trigger,eventId:id,weight:4});}
  }
  const nodeBudget=budget-stage.experience;
  if(budget<=0||nodeBudget<0||!entries.length&&nodeBudget!==0)throw new Error('Invalid main stage XP budget: '+stage.id);
  distribute(entries,nodeBudget);
  const source=campaignStageKey(stage.id);sources.set(source,{source,chapter,category:'main',pool:'main',area:stage.area,label:stage.name,proofKey:source,weight:1,amount:stage.experience,stageId:stage.id});
 }
 for(const chapter of [1,2])if(Array.from(sources.values()).filter(entry=>entry.chapter===chapter&&entry.category==='main').reduce((n,entry)=>n+entry.amount,0)!==CAMPAIGN_CHAPTER_BUDGETS[chapter-1].experience.mainXp)throw new Error('Main chapter XP does not meet its entry target');
}
installMainSources();

/** Static producer closure bounds source feasibility. It neither moves a hero
 * nor completes any event. Branch outcomes are a union of possible routes;
 * geometry, victory and actual content duration still require play evidence. */
export function campaignSourceReachability(areas:readonly AreaDef[],probabilistic=false):CampaignSourceReachability {
 const released=areas.filter(area=>playableArea(area.id)),byId=new Map(released.map(area=>[area.id,area]));
 const reached=new Set<string>(byId.has('S01-T1')?['S01-T1']:byId.has('S01')?['S01']:[]),flags=new Set<string>(),events=new Set<string>();
 let rounds=0,changed=true;
 const add=(values:readonly (string|undefined)[])=>{for(const value of values)if(value&&!flags.has(value)){flags.add(value);changed=true;}};
 const has=(...values:string[])=>values.every(value=>flags.has(value));
 while(changed&&rounds++<100){
  changed=false;
  for(const id of Array.from(reached)){
   const area=byId.get(id)!;add(['visited:'+id]);
   for(const exit of area.exits){
    if(!byId.has(exit.to)||exit.requiredLevel===undefined&&exit.requires&&!flags.has(exit.requires))continue;
    if(!reached.has(exit.to)){reached.add(exit.to);changed=true;}add([exit.unlock]);
    if(id==='U1-05'&&has('workers_released'))add(['workers_returned','workers_departed']);
   }
   for(const enemy of area.enemies){
    if(enemy.bossId)add(['boss_defeated:'+enemy.bossId]);
    if(enemy.bossId==='BOSS_R1'||!enemy.bossId&&enemy.kind==='captain')add(['captain_defeated']);
   }
   for(const object of area.objects){
    const action=object.action;
    if(action==='inspect')add([object.evidence]);
    if(action==='secret_pass')add(['evidence:'+object.id]);
    if(action==='independent_clue')add(['independent_clue']);
    if(action==='offer')add(['offer_seen','accepted','rejected','saw_copy']);
    if(action==='recover'||action==='rescue_cart')add(['recovered','cart_rescued','nightqi_available']);
    if(action==='letter'&&has('recovered'))add(['read_letter']);
    if(action==='meeting')add(['meeting','cooperation_chosen','star_copy_chosen','choice_made','truth_asked']);
    if(action==='disable_trap'&&has('meeting'))add(['trap_disabled','trap_handled']);
    if(action==='release_workers'&&has('meeting'))add(['workers_released','trap_handled']);
    if((action==='captain_gate'||action==='gate')&&has('captain_defeated'))add(['gate_raised']);
    if(action==='finish'&&has('captain_defeated','gate_raised','recovered','read_letter','meeting','workers_released','trap_handled','choice_made'))add(['chapter1_complete']);
    if(action==='checkpoint')add(['checkpoint:'+id]);
    if(action==='journey_task'&&object.eventId)add(['journey:task:'+object.eventId]);
    if(probabilistic&&action==='dice_check'&&object.check){add(['check:'+object.check+':passed','check:'+object.check+':failed']);if(object.check==='undercity-disarm')add(['trap_disabled','trap_handled']);}
    if(action!=='campaign_event')continue;
    const event=CAMPAIGN_EVENTS[object.eventId??''];
    if(!event||(event.requires??[]).some(flag=>!flags.has(flag))||event.requiresAny?.length&&!event.requiresAny.some(flag=>flags.has(flag)))continue;
    if(!events.has(event.id)){events.add(event.id);changed=true;}
    add([...(event.sets??[]),...(event.choices??[]).flatMap(choice=>choice.sets)]);
   }
   for(const battle of CAMPAIGN_BATTLES.filter(battle=>battle.area===id))add(['campaign:battle:'+battle.id+':complete']);
   if(id==='U1-06')add(['u106_array_stopped']);
   if(probabilistic){
    for(const scene of GROWING_SCENES.filter(scene=>scene.area===id))add([scene.flag]);
    for(const discovery of FIELD_DISCOVERIES.filter(discovery=>discovery.chapter===chapterForArea(id)))add([discovery.flag]);
   }
  }
  if(has('m7_prepared','west_tower_down','east_tower_down'))add(['final_ready']);
 }
 if(rounds>=100)throw new Error('Campaign prerequisite closure did not converge');
 return {areas:reached,flags,events,rounds};
}
export const sourceReachability=campaignSourceReachability;
const meaningfulEvent=(event:CampaignEventDef)=>!event.experienceEvent&&!event.chapterTwoAction&&!!(event.experience||event.gold||event.iron||event.runes||event.cores||event.items?.length||event.choiceItems?.length||event.clearEncounter||event.sets?.some(flag=>!flag.startsWith('cosmetic_')));
const enemyBaseExperience=(enemy:EnemySpawn)=>{
 const template=CAMPAIGN_ENEMY_TEMPLATES[enemy.bossId??enemy.templateId??''];
 return template?.firstClearExperience??(20+8*((enemy.level??1)-1))*(enemy.bossId?(template?.mandatory?8:3):1);
};

/** Called once after all production scene installers. No WorldData import: the
 * registry sees real objects/spawns without creating a module dependency loop. */
export function installCampaignExperience(areas:Record<string,AreaDef>):void {
 for(const [key,entry]of Array.from(sources.entries()))if(entry.category==='exploration')sources.delete(key);
 unallocatedExtra=[];blockedFutureDependencies=[];
 const list=Object.values(areas),guaranteed=campaignSourceReachability(list),possible=campaignSourceReachability(list,true),entries:WeightedSource[]=[];
 const seen=new Set<string>(),add=(entry:WeightedSource)=>{if(!seen.has(entry.source)&&!sources.has(entry.source)){seen.add(entry.source);entries.push(entry);}};
 for(const area of list){
  if(!playableArea(area.id)||!possible.areas.has(area.id))continue;
  const chapter=chapterForArea(area.id);
  for(const object of area.objects){
   if(['inspect','secret_pass','cache'].includes(object.action)){
    if(!guaranteed.areas.has(area.id))continue;
    add({source:`explore:${area.id}:${object.id}`,chapter,category:'exploration',area:area.id,label:object.label,objectId:object.id,proofKey:`interaction:${area.id}:${object.id}`,weight:object.action==='inspect'?40:80});
   }else if(object.action==='campaign_event'){
    const event=CAMPAIGN_EVENTS[object.eventId??''];if(!event)continue;
    const source=event.experienceEvent??'campaign:'+event.id;
    if(!possible.events.has(event.id)){
     blockedFutureDependencies.push({source,area:area.id,missingAll:(event.requires??[]).filter(flag=>!possible.flags.has(flag)),missingAny:event.requiresAny?.length&&!event.requiresAny.some(flag=>possible.flags.has(flag))?[...event.requiresAny]:[]});continue;
    }
    if(event.experienceEvent||event.chapterTwoAction||/^c[12]-/.test(event.id))continue;
    if(!guaranteed.events.has(event.id)){
     if(event.experience)unallocatedExtra.push({source,chapter,area:area.id,label:event.label,amount:event.experience,reason:'probabilistic-discovery-prerequisite'});continue;
    }
    if(meaningfulEvent(event))add({source,chapter,category:'exploration',area:area.id,label:event.label,objectId:object.id,eventId:event.id,proofKey:source,weight:Math.max(80,event.experience??(event.clearEncounter?180:100))});
   }
  }
  for(const enemy of area.enemies){
   if(enemy.respawnSeconds||enemy.trainingDummy||enemy.trainingEnemy||campaignFighter(enemy)?.deferExperience)continue;
   const source=`enemy:${area.id}:${enemy.id}`;if(sources.has(source))continue;
   const base=enemyBaseExperience(enemy),routeExclusive=(RIDGE_FIXED_IDS as readonly string[]).includes(enemy.id)||(OATH_FIXED_IDS as readonly string[]).includes(enemy.id)||Object.values(CAMPAIGN_EVENTS).some(event=>event.peacefulResolution&&peacefulBossTarget(event.id,area.id,enemy));
   if(routeExclusive){unallocatedExtra.push({source,chapter,area:area.id,label:CAMPAIGN_ENEMY_TEMPLATES[enemy.bossId??enemy.templateId??'']?.name??enemy.id,amount:base,reason:'combat-route-exclusive'});continue;}
   if(guaranteed.areas.has(area.id))add({source,chapter,category:'exploration',area:area.id,label:CAMPAIGN_ENEMY_TEMPLATES[enemy.bossId??enemy.templateId??'']?.name??enemy.id,enemyId:enemy.id,proofKey:`kill:${area.id}:${enemy.id}`,weight:base});
  }
 }
 for(const battle of CAMPAIGN_BATTLES){
  if(!guaranteed.areas.has(battle.area))continue;
  for(const wave of battle.waves)for(const reward of wave.experience){
   const source=`enemy:${battle.area}:${reward.id}`;
   if(sources.has(source))continue;
   if((OATH_FIXED_IDS as readonly string[]).includes(reward.id)){unallocatedExtra.push({source,chapter:chapterForArea(battle.area),area:battle.area,label:battle.title,amount:reward.amount,reason:'combat-route-exclusive'});continue;}
   add({source,chapter:chapterForArea(battle.area),category:'exploration',area:battle.area,label:battle.title,enemyId:reward.id,proofKey:`kill:${battle.area}:${reward.id}`,weight:reward.amount});
  }
 }
 for(const chapter of [1,2])distribute(entries.filter(entry=>entry.chapter===chapter),CAMPAIGN_CHAPTER_BUDGETS[chapter-1].experience.uniqueExplorationXp);
 installed=true;
}

/** Unknown sources retain their explicitly supplied base reward. An unregistered
 * zero-XP/future event therefore never acquires a new award from this policy. */
export function campaignExperienceQuote(source:string,baseAmount=0):CampaignExperienceQuote {
 const entry=sources.get(source);return entry?{...entry,registered:true}:{source,amount:baseAmount,category:'other',registered:false};
}
export function campaignExperienceSources(chapter?:number):CampaignExperienceSource[]{return Array.from(sources.values()).filter(entry=>chapter===undefined||entry.chapter===chapter).map(entry=>({...entry}));}
export function campaignStageExperienceView(stageId:string){
 const stage=CAMPAIGN_STAGES.find(stage=>stage.id===stageId);if(!stage)return null;
 const entries=campaignExperienceSources(stage.chapter).filter(entry=>entry.stageId===stageId),completion=entries.find(entry=>entry.source===campaignStageKey(stageId));
 return {stageId,chapter:stage.chapter,targetTotalXp:stage.targetTotalXp,budgetXp:entries.reduce((n,entry)=>n+entry.amount,0),completionXp:completion?.amount??0,nodeXp:entries.filter(entry=>entry!==completion).reduce((n,entry)=>n+entry.amount,0),sources:entries};
}
export function campaignExperienceView(chapter:number,xpReceipts:Record<string,number>={}){
 const budget=CAMPAIGN_CHAPTER_BUDGETS.find(entry=>entry.chapter===chapter);if(!budget)return null;
 const entries=campaignExperienceSources(chapter),main=entries.filter(entry=>entry.category==='main'),exploration=entries.filter(entry=>entry.category==='exploration');
 const amount=(rows:CampaignExperienceSource[])=>rows.reduce((n,entry)=>n+entry.amount,0),earned=(rows:CampaignExperienceSource[])=>rows.reduce((n,entry)=>n+(xpReceipts[entry.source]??0),0),extras=unallocatedExtra.filter(entry=>entry.chapter===chapter);
 return {chapter,released:budget.released,installed,status:budget.released?'source-budget-not-duration-proof':'unallocated-future-content',pacing:budget.pacing,
  requiredXp:budget.experience.requiredXp,main:{targetXp:budget.experience.mainXp,availableXp:amount(main),earnedXp:earned(main),sourceCount:main.length},
  exploration:{typicalTargetXp:budget.experience.typicalExplorationXp,targetXp:budget.experience.uniqueExplorationXp,availableXp:amount(exploration),earnedXp:earned(exploration),sourceCount:exploration.length},
  freeCombat:{targetXp:budget.experience.freeCombatXp,requiredXp:0},unallocatedExtra:extras.map(entry=>({...entry})),unallocatedExtraMaximumXp:extras.reduce((n,entry)=>n+entry.amount,0),
  blockedFutureDependencies:blockedFutureDependencies.filter(entry=>chapterForArea(entry.area)===chapter).map(entry=>({...entry})),
  contentMinutesMeasured:false};
}
export function validateCampaignExperienceReceipts(xpReceipts:Record<string,number>,completionReceipts:Record<string,string|number|boolean>,proof?:(entry:CampaignExperienceSource)=>boolean,monsterMultiplier=1):void {
 for(const entry of Array.from(sources.values())){
  const earned=xpReceipts[entry.source];if(earned===undefined)continue;
  const expected=(completionReceipts['campaign:xp:v2:'+entry.source]===true?entry.amount:LEGACY_CAMPAIGN_EXPERIENCE[entry.source]??entry.amount)*(entry.source.startsWith('enemy:')?monsterMultiplier:1);
  if(earned!==expected||entry.proofKey&&completionReceipts[entry.proofKey]!==true||proof&&!proof(entry))throw new Error('无效的章节经验奖励凭证');
 }
 for(const entry of unallocatedExtra){
  const earned=xpReceipts[entry.source];if(earned===undefined)continue;
  const enemy=entry.source.startsWith('enemy:'),proofKey=enemy?'kill:'+entry.source.slice(6):entry.source;
  if(earned!==entry.amount*(enemy?monsterMultiplier:1)||completionReceipts[proofKey]!==true)throw new Error('无效的可选经验奖励凭证');
 }
 for(const source of Object.keys(xpReceipts))if(source.startsWith('explore:')&&!sources.has(source))throw new Error('无效的探索经验来源');
}
