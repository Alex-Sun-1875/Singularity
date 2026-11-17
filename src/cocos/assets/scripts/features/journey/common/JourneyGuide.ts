import type {AreaDef,Point,WorldQuery} from '../../../core/Contracts';
import type {EnemyState,GameSession} from '../../../core/GameSession';
import type {NavigationTarget} from '../../automation/common/Automation';
import {availableRoutes,enemyApproachPath,exitBlockage,routeBlockage,pathBlockage,type NavigationBlockage} from '../../automation/common/AutomationRoute';
import {chapterForArea,PLAYABLE_CHAPTERS,JOURNEY_TASKS,type JourneyTask} from '../data/ChapterJourney';
import {HUNTING_GROUNDS,HUNT_ENCOUNTERS} from '../../world/data/MonsterEcology';
import {journeyText as tr} from '../locales';
import {chapterTwoEncounterView,chapterTwoEnemyRetired} from '../../campaign/common/ChapterTwoEncounters';
import {OATH_SEQUENCE} from '../../campaign/data/ChapterTwoEncounters';
import {CHAPTER_TWO_SIDE_QUEST_EVENTS,CHAPTER_TWO_SIDE_QUESTS} from '../../campaign/data/ChapterTwoSideQuests';
import {FIELD_QUEST_EVENTS,FIELD_QUESTS} from '../../campaign/data/FieldQuests';
import {campaignPrerequisiteTargets} from '../../campaign/common/CampaignNavigation';
import {campaignExperienceSources,type CampaignExperienceSource} from '../../progression/data/CampaignExperience';
import {CAMPAIGN_STAGES,nextCampaignStage,nextCampaignStageAction,campaignStageDone} from '../data/CampaignStages';
import {CAMPAIGN_EVENTS} from '../../campaign/data/CampaignEvents';
import {earlyEnemyActive} from '../../campaign/data/EarlyChapterContent';
import {peacefulBossRetired} from '../../campaign/common/PeacefulBosses';
import {sideBossById} from '../../campaign/data/SideBosses';
import {campaignBattle} from '../../campaign/data/CampaignBattles';
import {interactionApproachPath} from '../../navigation/common/InteractionApproach';

export interface JourneyGuidance {
 destination:NavigationTarget;point:Point;bearing:Point;distance:number;hops:number;nextArea?:string;
 instruction:string;detail:string;safe:boolean;blocked:boolean;kind:'task'|'hunt'|'boss';
 progress?:string;reminder?:string;blockage?:NavigationBlockage;
 targetId?:string;targetType:'exit'|'object'|'enemy'|'position';
}
export interface JourneyGuidanceOptions {skip?:ReadonlySet<string>;allKnown?:boolean;finite?:boolean;automatic?:boolean}
export const journeyTargetKey=(target:NavigationTarget)=>target.stageId?'stage:'+target.stageId:target.taskId?'task:'+target.taskId:target.explorationSource?'source:'+target.explorationSource:target.objectId?'object:'+target.objectId:target.enemyId?'enemy:'+target.area+':'+target.enemyId:'area:'+target.area;
const sideQuests=()=>[...FIELD_QUESTS,...CHAPTER_TWO_SIDE_QUESTS];
const sideEvents=()=>[...FIELD_QUEST_EVENTS,...CHAPTER_TWO_SIDE_QUEST_EVENTS];
const areaKnown=(game:GameSession,id:string)=>game.state.area===id||!!game.state.flags['visited:'+id]||id==='S01'&&Object.keys(game.state.flags).some(flag=>flag.startsWith('visited:S01-')&&game.state.flags[flag]);
function sideKnown(game:GameSession,quest:ReturnType<typeof sideQuests>[number]){
 if(quest.chapter===2&&!game.state.progression.secondChapter)return false;
 if('hidden'in quest)return !!game.state.flags[quest.hidden];
 // Public quest-board entries are already known, even before visiting their
 // first NPC. Their real acceptance, route and action prerequisites still apply.
 return true;
}
function explorationKnown(game:GameSession,eventId:string|undefined,area:string){
 const quest=eventId&&sideQuests().find(quest=>quest.steps.some(id=>id===eventId));
 return quest?sideKnown(game,quest):areaKnown(game,area);
}
function explorationStillPossible(game:GameSession,eventId:string|undefined){
 const event=eventId?CAMPAIGN_EVENTS[eventId]:undefined;
 const required=(event as typeof event&{requiresReceipts?:Record<string,string|number|boolean>})?.requiresReceipts;
 return Object.entries(required??{}).every(([key,value])=>game.state.receipts[key]===undefined||game.state.receipts[key]===value);
}
function explorationDormantOrResolved(game:GameSession,areas:Record<string,AreaDef>,entry:CampaignExperienceSource){
 const s=game.state,area=entry.area?areas[entry.area]:undefined,object=entry.objectId?area?.objects.find(object=>object.id===entry.objectId):undefined;
 if(object?.evidence&&s.flags[object.evidence])return true;
 if(object?.action==='campaign_event'&&game.campaignEventAvailability(object.eventId??'',true).completed)return true;
 return !!entry.enemyId&&(!earlyEnemyActive(entry.enemyId,s.flags)||chapterTwoEnemyRetired(s,entry.enemyId)||peacefulBossRetired(s,entry.enemyId));
}
/** Completion uses authored task receipts, never XP remaining. Hidden quests
 * and unexplored sites do not become known by running the controller. */
export function journeyQueueStatus(game:GameSession,areas:Record<string,AreaDef>){
 const s=game.state,quests=sideQuests().filter(quest=>sideKnown(game,quest));
 const main=CAMPAIGN_STAGES.filter(stage=>(stage.chapter===1||s.progression.secondChapter)&&!campaignStageDone(s,stage)).length;
 const bosses=PLAYABLE_CHAPTERS.filter(chapter=>(chapter.id===1||s.progression.secondChapter)&&!s.receipts['journey:boss:'+chapter.id]).length;
 const side=quests.filter(quest=>quest.steps.some(id=>s.receipts['campaign:'+id]!==true)).length;
 const exploration=campaignExperienceSources().filter(entry=>entry.category==='exploration'&&entry.area&&areas[entry.area]&&s.progression.xpReceipts[entry.source]===undefined&&(!entry.proofKey||!s.receipts[entry.proofKey])&&explorationKnown(game,entry.eventId,entry.area)&&explorationStillPossible(game,entry.eventId)&&!explorationDormantOrResolved(game,areas,entry)&&!entry.eventId?.startsWith('chapter2-action:')&&!sideQuests().some(quest=>quest.steps.some(id=>id===entry.eventId))).length;
 return {remaining:main+side+exploration,main,bosses,side,exploration};
}
/** Completion conditions share the real task receipts and selected destination.
 * Keep this separate from route/reward prose so compact HUDs cannot hide it. */
function objectiveReminder(game:GameSession,areas:Record<string,AreaDef>,target:NavigationTarget,kind:JourneyGuidance['kind']){
 const s=game.state,local=target.area===s.area,task=JOURNEY_TASKS.find(task=>task.id===target.taskId);
 const hint=(progress:string,reminder:string)=>({progress,reminder});
 if(task?.goal==='hunt'){
  const count=game.journey.progress(task),total=task.kills??0;
  const waiting=local&&!s.enemies.some(enemy=>enemy.hp>0&&enemy.respawnSeconds);
  return hint(tr('tracker.kills',{count,total}),tr(count>=total?'tracker.settle':waiting?'tracker.waitHunt':'tracker.hunt',{count,total,area:areas[task.area].name}));
 }
 const view=task?.goal==='encounter'?chapterTwoEncounterView(s,task.encounterId??task.id):undefined;
 if(view?.resolved)return hint(tr('tracker.settling'),tr('tracker.settle'));
 if(view?.id==='oath-array'&&!view.combatStarted&&s.receipts['chapter2:oath-array:read']){
  const count=Number(s.receipts['chapter2:oath-array:progress']??0),total=OATH_SEQUENCE.length;
  return hint(tr('tracker.mechanismCount',{count,total}),tr('tracker.mechanism',{count,total,target:target.label}));
 }
 const object=target.objectId?areas[target.area]?.objects.find(object=>object.id===target.objectId):undefined;
 const stage=CAMPAIGN_STAGES.find(stage=>stage.id===target.stageId),action=stage&&nextCampaignStageAction(s,stage);
 const eventId=object?.action==='campaign_event'?object.eventId:action?.kind==='event'&&action.area===target.area?action.eventId:undefined,event=CAMPAIGN_EVENTS[eventId??''];
 if(target.enemyId&&event?.defeatIds?.includes(target.enemyId)){
  const count=event.defeatIds.filter(id=>s.receipts[`kill:${event.area}:${id}`]===true).length;
  return hint(tr('tracker.kills',{count,total:event.defeatIds.length}),tr('tracker.prerequisite'));
 }
 if(task?.goal==='clear'||view?.combatStarted||event?.clearEncounter){
  if(!local)return hint(tr('tracker.clear'),tr('tracker.clearArea',{area:areas[target.area].name}));
  const fixed=s.enemies.filter(enemy=>!enemy.respawnSeconds&&!enemy.trainingEnemy&&(task?.goal!=='clear'||!enemy.id.startsWith('early-'))),alive=fixed.filter(enemy=>enemy.hp>0).length;
  const battle=campaignBattle(s.area),pending=battle&&!s.flags[`campaign:battle:${battle.id}:complete`]?battle.waves.filter((_,i)=>!s.receipts[`campaign:wave:${battle.id}:${i}`]).flatMap(wave=>wave.enemies).filter(enemy=>!s.enemies.some(existing=>existing.id===enemy.id)).length:0;
  const count=alive+pending;
  if(!count)return hint(tr('tracker.settling'),tr('tracker.settle'));
  return hint(tr('tracker.remaining',{count}),tr(alive?'tracker.defenders':'tracker.reinforcements',{count}));
 }
 const defeat=target.label.startsWith(tr('action.defeat'))?target.label:tr('tracker.defeat',{target:target.label});
 if(kind==='boss')return hint(tr('tracker.boss'),defeat);
 if(kind==='hunt')return hint(tr('tracker.free'),tr('tracker.freeHunt'));
 if(target.enemyId)return hint(tr('action.defeat'),defeat);
 if(target.exitId)return hint(tr('tracker.travel'),tr('tracker.exit',{target:target.label}));
 if(task?.goal==='observe')return hint(tr('tracker.investigate'),tr('tracker.observe',{target:target.label}));
 if(object)return hint(tr('tracker.interact'),event?.objectiveHint??tr('tracker.object',{target:object.label}));
 return {};
}
/** Guidance for a deliberately selected destination, sharing normal route gates. */
export function navigationGuidance(game:GameSession,areas:Record<string,AreaDef>,world:WorldQuery,target:NavigationTarget):JourneyGuidance|null {
 const local=areas[game.state.area];if(!local||!areas[target.area])return null;
 const route=availableRoutes(game,areas,target.area).get(target.area),point=route?.[0]??target.point;
 const object=!route?.length&&target.objectId?local.objects.find(object=>object.id===target.objectId):undefined;
 const path=route===undefined?[]:guidancePath(game,local,world,object??point),exit=!route?.length&&target.exitId?local.exits.find(exit=>exit.id===target.exitId):undefined;
 const gate=exit?exitBlockage(game,areas,local.id,exit):undefined,blocked=!path.length||!!gate;
 const blockage=route===undefined?routeBlockage(game,areas,target.area):gate??(!path.length?pathBlockage(target.label,!!target.enemyId):undefined);
 return {destination:target,point,bearing:path.find(q=>distance(q,game.state.player)>1.5)??point,
  distance:path.slice(1).reduce((n,q,i)=>n+distance(q,path[i]),0),hops:route?.length??0,nextArea:route?.[0]?.to,
  instruction:target.label,detail:route?.length?`下一站 ${areas[route[0].to].name} · ${route.length}次过图`:target.objectId?'抵达后自动打开交互':'抵达后手动接近或从入口发起再战',
  safe:!game.state.enemies.some(e=>e.hp>0),blocked,blockage,kind:target.bossKey?'boss':'task',...objectiveReminder(game,areas,target,target.bossKey?'boss':'task'),targetType:route?.length||target.exitId?'exit':target.objectId?'object':'position',targetId:route?.[0]?.id??target.exitId??target.objectId};
}
const distance=(a:Point,b:Point)=>Math.hypot(a.x-b.x,a.z-b.z);
// A scene's walk geometry is immutable. Unchanged endpoints can reuse the full
// route, including reachability, without repeating connector and collision work.
const guidancePaths=new WeakMap<GameSession,{world:WorldQuery;area:AreaDef;routes:Map<string,Point[]>}>();
export function resetJourneyGuidance(game:GameSession){guidancePaths.delete(game);}
function guidancePath(game:GameSession,area:AreaDef,world:WorldQuery|undefined,target:Point):Point[]{
 const p=game.state.player;if(!world?.path)return [p,target];
 let cache=guidancePaths.get(game);
 if(!cache||cache.world!==world||cache.area!==area){cache={world,area,routes:new Map()};guidancePaths.set(game,cache);}
 const id=(target as Point&{id?:string}).id;
 const enemy=game.state.enemies.find(e=>(e===target||!!id&&e.id===id)&&e.hp>0),object=id?area.objects.find(object=>object.id===id):undefined;
 const key=`${enemy?`${enemy.id}:${game.state.equipment.weapon}`:object?`object:${object.id}:${object.radius}`:'walk'}:${p.x},${p.z}>${target.x},${target.z}`,cached=cache.routes.get(key);
 if(cached!==undefined)return cached;
 const path=(enemy?enemyApproachPath(game,world,enemy):object?interactionApproachPath(world,p,object):world.path(p,target)).map(q=>({x:q.x,z:q.z}));
 if(cache.routes.size>=64)cache.routes.delete(cache.routes.keys().next().value!);
 cache.routes.set(key,path);return path;
}
/** One actionable destination. No saved tutorial mode, input capture, or quest locks. */
export function journeyGuidance(game:GameSession,areas:Record<string,AreaDef>,world?:WorldQuery,taskId?:string,preference=game.journey.tracking(),chapterId=chapterForArea(game.state.area),options:JourneyGuidanceOptions={}):JourneyGuidance|null {
 const s=game.state,p=s.player,local=areas[s.area];if(!local)return null;
 // Share one fresh regional search across all candidate hunting grounds.
 let routes:ReturnType<typeof availableRoutes>|undefined;
 const routeTo=(id:string)=>{if(id===s.area)return [];routes??=availableRoutes(game,areas);return routes.get(id)??null;};
 const chapter=PLAYABLE_CHAPTERS.find(c=>c.id===chapterId);if(!chapter)return null;
 const selected=JOURNEY_TASKS.find(t=>t.id===taskId&&game.journey.currentTask(t.chapter)?.id===t.id);
 let task=selected??game.journey.currentTask(chapter.id),kind:JourneyGuidance['kind']='task';
 let target:NavigationTarget|undefined,instruction='',detail='';
 let missingPrerequisite:{target:NavigationTarget;blockage:NavigationBlockage}|undefined;
 const nextStage=preference!=='hunt'?nextCampaignStage(s):undefined,stage=nextStage&&(nextStage.chapter===1||s.progression.secondChapter)?nextStage:undefined;
 const stageAction=stage&&nextCampaignStageAction(s,stage);
 if(stageAction?.kind==='task')task=JOURNEY_TASKS.find(candidate=>candidate.id===stageAction.taskId);
 else if(stage)task=undefined;
 const skipped=(candidate:NavigationTarget)=>!!options.skip&&(options.skip.has(journeyTargetKey(candidate))||!!candidate.objectId&&options.skip.has('object:'+candidate.objectId));
 // A blocked nearest enemy must not hide the rest of a reachable encounter.
 // Preserve the true blocked result when none of the living targets can be met.
 const reachableEnemy=(enemies:EnemyState[])=>enemies.find(e=>guidancePath(game,local,world,e).length)??enemies[0];
 const encounterTarget=(current:JourneyTask)=>{
  const view=chapterTwoEncounterView(s,current.encounterId??current.id),generic=areas[current.area]?.objects.find(o=>o.action==='journey_task'&&o.eventId===current.id);
  if(view?.resolved)return {target:{area:current.area,point:generic??areas[current.area].spawn,label:current.name,objectId:generic?.id} as NavigationTarget,detail:tr('growth.encounterResolved')};
  if(view&&'combatStarted'in view&&view.combatStarted===true){
   const enemies=s.area===current.area?s.enemies.filter(e=>e.hp>0&&!e.respawnSeconds&&!e.trainingEnemy).sort((a,b)=>distance(a,p)-distance(b,p)):[],enemy=reachableEnemy(enemies);
   return {target:{area:current.area,point:enemy??areas[current.area].spawn,label:current.name} as NavigationTarget,detail:tr(enemy?'growth.encounterBattle':'growth.encounterWave')};
  }
  const available=view?.routes.filter(route=>route.available)??[],interactions=available.filter(route=>route.method!=='battle'),choices=interactions.length?interactions:available;
  // Automatic tasks follow the first authored route and the inspected control
  // sequence. Explicit navigation retains the selected physical destination.
  const origin=s.area===current.area?p:areas[current.area].spawn;
  const defaultId=view?.id==='oath-array'?(s.receipts['chapter2:oath-array:read']?OATH_SEQUENCE[Number(s.receipts['chapter2:oath-array:progress']??0)]:'oath-read'):undefined;
  const defaultRoute=options.automatic?(defaultId?choices.find(route=>route.id===defaultId):choices[0]):undefined;
  const ranked=defaultRoute?[defaultRoute]:choices.slice().sort((a,b)=>distance(origin,a.point)-distance(origin,b.point));
  const route=ranked.find(candidate=>candidate.area!==s.area||guidancePath(game,local,world,candidate.point).length)??ranked[0];
  if(!route)return {target:{area:current.area,point:generic??areas[current.area].spawn,label:current.name} as NavigationTarget,detail:tr('growth.encounterUnavailable')};
  const object=areas[route.area]?.objects.find(o=>o.eventId===route.eventId&&o.action==='campaign_event');
  return {target:{area:route.area,point:object??route.point,label:route.label,objectId:object?.id} as NavigationTarget,detail:tr(current.encounterId==='oath-array'?'growth.mechanismRoute':'growth.encounter')};
 };
 const sideQuestTarget=()=>{
  const candidates=sideQuests().filter(quest=>sideKnown(game,quest)).flatMap(quest=>{
   const id=quest.steps.find(step=>s.receipts['campaign:'+step]!==true),event=sideEvents().find(def=>def.id===id);
   if(!event)return [];
   const object=areas[event.area]?.objects.find(o=>o.action==='campaign_event'&&o.eventId===event.id);
   if(!object||options.skip?.has('object:'+object.id))return [];
   let destination:NavigationTarget|undefined;
   if(game.campaignEventAvailability(event.id,true).available){
    const fixed=event.clearEncounter&&s.area===event.area?s.enemies.filter(enemy=>enemy.hp>0&&!enemy.respawnSeconds&&!enemy.trainingEnemy).sort((a,b)=>distance(p,a)-distance(p,b)):[];
    const enemy=reachableEnemy(fixed);
    destination=enemy?{area:event.area,point:enemy,label:event.label,enemyId:enemy.id,sideQuest:true}:{area:event.area,point:object,label:event.label,objectId:object.id,sideQuest:true};
   }else destination=campaignPrerequisiteTargets(game,areas,event.id).find(prerequisite=>!prerequisite.blocked)?.destination;
   if(!destination||skipped(destination))return [];
   const route=routeTo(destination.area);if(route===null)return [];
   const started=quest.steps.some(step=>s.receipts['campaign:'+step]===true);
   return [{quest,destination:{...destination,sideQuest:true},score:(started?0:10000)+route.length*1000+distance(destination.area===s.area?p:areas[destination.area].spawn,destination.point)}];
  }).sort((a,b)=>a.score-b.score||a.quest.id.localeCompare(b.quest.id));
  const next=candidates.find(candidate=>candidate.destination.area!==s.area||guidancePath(game,local,world,candidate.destination.point).length);
  if(!next)return false;
  task=undefined;target=next.destination;kind='task';instruction=next.quest.name;detail=tr('growth.sideQuest',{quest:next.quest.name});return true;
 };
 // Repeat combat is optional preparation. The authored one-time sources remain
 // available after the daily cap and must be used before seeking more prey.
 const exploration=()=>{
  const candidates=campaignExperienceSources(options.allKnown?undefined:chapterId).filter(entry=>entry.category==='exploration'&&entry.area&&areas[entry.area]&&s.progression.xpReceipts[entry.source]===undefined&&(!entry.proofKey||!s.receipts[entry.proofKey])&&explorationKnown(game,entry.eventId,entry.area)&&explorationStillPossible(game,entry.eventId)&&!explorationDormantOrResolved(game,areas,entry)&&!options.skip?.has('source:'+entry.source)).flatMap(entry=>{
   const area=areas[entry.area!],route=routeTo(area.id);if(route===null)return [];
   const object=entry.objectId?area.objects.find(o=>o.id===entry.objectId):undefined;
   if(object){
    if(!['inspect','secret_pass','cache','campaign_event'].includes(object.action)||options.skip?.has('object:'+object.id))return [];
    if(object.action==='campaign_event'&&!game.campaignEventAvailability(object.eventId??'',true).available)return [];
    if(object.evidence&&s.flags[object.evidence])return [];
    if(area.id===s.area&&(!game.interactionVisible(object)||game.interactionAvailability(object).completed))return [];
   }
   const enemy=entry.enemyId?(area.id===s.area?s.enemies:s.encounters[area.id]??area.enemies).find(e=>e.id===entry.enemyId):undefined;
   if(!object&&(!enemy||enemy.hp<=0||enemy.respawnSeconds))return [];
   const point=object??enemy!,origin=area.id===s.area?p:area.spawn;
   return [{entry,object,point,score:route.length*1000+distance(origin,point)}];
  }).sort((a,b)=>a.score-b.score||a.entry.source.localeCompare(b.entry.source));
  const candidate=candidates.find(({entry,point})=>entry.area!==s.area||guidancePath(game,local,world,point).length);
  if(!candidate)return false;
  const {entry,object,point}=candidate;kind='task';task=undefined;
  const event=object?.action==='campaign_event'?CAMPAIGN_EVENTS[object.eventId??'']:undefined;
  const fixed=event?.clearEncounter&&entry.area===s.area?s.enemies.filter(enemy=>enemy.hp>0&&!enemy.respawnSeconds&&!enemy.trainingEnemy&&!sideBossById(enemy.id)).sort((a,b)=>distance(p,a)-distance(p,b)):[];
  const enemy=reachableEnemy(fixed);
  target=enemy?{area:entry.area!,point:enemy,label:entry.label,enemyId:enemy.id,explorationSource:entry.source}:{area:entry.area!,point,label:entry.label,objectId:object?.id,enemyId:!object?'id'in point?String(point.id):undefined:undefined,explorationSource:entry.source,sideQuest:object?.action==='campaign_event'};
  instruction=tr('growth.exploration',{target:entry.label});detail=tr('growth.explorationReward',{experience:entry.amount});return true;
 };
 const preparation=(requiredLevel?:number)=>{
  if(!exploration()&&game.huntingExperience().remaining>0&&(!options.finite||requiredLevel!==undefined&&s.progression.level<requiredLevel))hunting();
 };
 const hunting=(preferredArea?:string)=>{
  kind='hunt';
  const grounds=Object.entries(HUNTING_GROUNDS).filter(([,def])=>def.level<=s.progression.level+1).map(([id,def])=>({id,def,route:routeTo(id)})).filter(v=>v.route!==null);
  grounds.sort((a,b)=>Math.abs(a.def.level-s.progression.level)-Math.abs(b.def.level-s.progression.level)||a.route!.length-b.route!.length);
  const ground=grounds.find(g=>g.id===preferredArea)??grounds[0];if(!ground)return;
  const alive=ground.id===s.area?s.enemies.filter(e=>e.hp>0&&e.respawnSeconds).sort((a,b)=>distance(a,p)-distance(b,p)):[];
  const slots=HUNT_ENCOUNTERS[ground.id],point=reachableEnemy(alive)??slots?.[0]??areas[ground.id].spawn;
  target={area:ground.id,point,label:'Lv'+ground.def.level+' '+areas[ground.id].name+'狩猎'};
  instruction='狩猎 · '+areas[ground.id].name;
  detail=ground.id===s.area?`游荡怪 ${alive.length}只 · 击败后自动计数`:`Lv${ground.def.level}猎区 · 任务外也可成长`;
  if(ground.id===s.area&&!alive.length){
   const wait=Math.max(0,Math.ceil(Math.min(...s.enemies.filter(e=>e.respawnSeconds).map(e=>(e.respawnAt??s.time)-s.time))));
   const rest=[local.spawn,...local.exits].find(q=>slots.every(e=>distance(e,q)>21)&&(!world?.path||guidancePath(game,local,world,q).length));
   target.point=rest??local.spawn;instruction='猎区休整 · 等待补充';detail=wait>0?`${wait}秒后补充 · 离出生点20米`:'离出生点20米，让怪群重新出没';
  }
 };
 if(stage&&stageAction&&stageAction.kind!=='task'){
  const area=areas[stageAction.area];
  if(area){
   if(stageAction.kind==='event'){
    const event=CAMPAIGN_EVENTS[stageAction.eventId??''],object=area.objects.find(object=>object.action==='campaign_event'&&object.eventId===stageAction.eventId);
    const availability=game.campaignEventAvailability(stageAction.eventId??'',true);
    if(object&&!availability.available&&!availability.completed)missingPrerequisite={target:{area:area.id,point:object,label:stage.name,objectId:object.id,stageId:stage.id,sideQuest:true},blockage:{code:'prerequisite',summary:tr('block.actionPrerequisite'),reason:availability.reason,hint:tr('block.prerequisiteHint')}};
    if(event&&availability.available&&object){
     const fixed=event.clearEncounter&&s.area===area.id?s.enemies.filter(enemy=>enemy.hp>0&&!enemy.respawnSeconds&&!enemy.trainingEnemy).sort((a,b)=>distance(p,a)-distance(p,b)):[];
     const enemy=reachableEnemy(fixed);
     target=enemy?{area:area.id,point:enemy,label:stage.name,enemyId:enemy.id}:{area:area.id,point:object,label:object.label,objectId:object.id,sideQuest:true};
    }else {
     target=campaignPrerequisiteTargets(game,areas,stageAction.eventId??'').find(prerequisite=>!prerequisite.blocked)?.destination;
     detail=availability.reason;
    }
   }else if(stageAction.kind==='action'){
    const object=area.objects.find(object=>object.action===stageAction.action||stageAction.action==='recover'&&object.action==='rescue_cart');
    if(object){
     const enemies=s.area===area.id&&!game.interactionAvailability(object).available?s.enemies.filter(enemy=>enemy.hp>0&&!enemy.respawnSeconds&&!enemy.trainingEnemy).sort((a,b)=>distance(p,a)-distance(p,b)):[];
     const enemy=reachableEnemy(enemies);
     target=enemy?{area:area.id,point:enemy,label:stage.name,enemyId:enemy.id}:{area:area.id,point:object,label:object.label,objectId:object.id,sideQuest:true};
    }
   }else if(stageAction.kind==='exit'){
    const exit=area.exits.find(exit=>!game.exitRequirement(exit));
    if(exit)target={area:area.id,point:exit,label:exit.label,exitId:exit.id};
   }else if(stageAction.kind==='boss'){
    const enemy=(s.area===area.id?s.enemies:area.enemies).find(enemy=>enemy.bossId===stageAction.bossId);
    if(enemy){kind='boss';target={area:area.id,point:enemy,label:stage.name,enemyId:enemy.id};}
   }
   if(target){target.stageId=stage.id;instruction=target.label;detail||=stage.story;}
  }
 }
 if(target){/* The current v2 stage already supplied its real action. */}
 else if(stage&&stageAction?.kind!=='task'){
  // A missing stage prerequisite is not permission to run later story stages.
  sideQuestTarget()||exploration();
 }
 else if(!selected&&preference==='hunt')hunting();
 else if(task){
  const object=areas[task.area]?.objects.find(o=>o.action==='journey_task'&&o.eventId===task!.id);
  target={area:task.area,point:object??areas[task.area].spawn,label:task.name,objectId:task.goal==='observe'?object?.id:undefined};instruction=task.name;
  if(task.goal==='encounter'){const encounter=encounterTarget(task);target=encounter.target;detail=encounter.detail;}
  else if(s.area===task.area){
   if(task.goal==='observe')detail='靠近金色标记 · 交互观察';
   else if(game.journey.ready(task))detail='目标达成 · 奖励自动结算';
   else {
    const enemies=s.enemies.filter(e=>e.hp>0&&(task!.goal==='hunt'?!!e.respawnSeconds:!e.respawnSeconds)).sort((a,b)=>distance(a,p)-distance(b,p));
    if(enemies.length)target.point=reachableEnemy(enemies);
    detail=task.goal==='hunt'?`游荡怪 ${game.journey.progress(task)}/${task.kills} · 击败后自动计数`:`固定守军 ${enemies.length} · 清完自动结算`;
    if(task.goal==='hunt'&&!enemies.length){hunting(task.area);instruction=task.name;detail=`狩猎 ${game.journey.progress(task)}/${task.kills} · 离出生点20米等待补充`;}
   }
  }else detail='前往'+areas[task.area].name;
 }else if(!s.receipts[`journey:boss:${chapter.id}`]){
  if(chapter.id===1&&s.progression.level<chapter.endLevel&&s.area!==chapter.arena)preparation(chapter.endLevel);
  else {kind='boss';const boss=s.area===chapter.arena?s.enemies.find(e=>e.hp>0&&e.bossId===chapter.boss):undefined;
   target={area:chapter.arena,point:boss??areas[chapter.arena].enemies.find(e=>e.bossId===chapter.boss)??areas[chapter.arena].spawn,label:chapter.bossName};instruction='挑战'+chapter.bossName;detail=s.progression.level<chapter.endLevel?tr('growth.boss',{level:chapter.endLevel,current:s.progression.level}):'共同关底 · 胜利即可通关';}
 }else if(chapter.id===1&&s.progression.level>=11&&(!s.receipts['journey:boss:2']||game.journey.currentTask(2))){
  task=game.journey.currentTask(2);const c=PLAYABLE_CHAPTERS[1],object=task&&areas[task.area].objects.find(o=>o.eventId===task!.id);target={area:task?.area??c.arena,point:object??areas[task?.area??c.arena].spawn,label:task?.name??c.bossName,objectId:task?.goal==='observe'?object?.id:undefined};instruction='第二章 · '+(task?.name??c.bossName);detail='前往高地继续旅程';if(task?.goal==='encounter'){const encounter=encounterTarget(task);target=encounter.target;detail=encounter.detail;}
 }else if(chapter.id===1){if(s.progression.level<11)preparation(11);else sideQuestTarget();}
 else sideQuestTarget();
 if(target&&stage&&stageAction?.kind==='task'&&task?.id===stageAction.taskId&&!target.sideQuest&&!target.explorationSource){target.stageId=stage.id;instruction=stage.name;}
 if(target&&skipped(target)){target=undefined;task=undefined;}
 if(preference!=='hunt'&&target&&routeTo(target.area)===null){const blockedTarget=target;target=undefined;preparation();target??=blockedTarget;}
 if(preference!=='hunt'&&!target)sideQuestTarget()||exploration();
 if(!target&&missingPrerequisite&&!skipped(missingPrerequisite.target)){target=missingPrerequisite.target;instruction=target.label;detail=missingPrerequisite.blockage.reason;}
 if(!target)return null;
 target.journey=true;
 if(stage&&stageAction?.kind==='task'&&task?.id===stageAction.taskId&&!target.sideQuest&&!target.explorationSource){target.stageId=stage.id;instruction=stage.name;}
 if(task&&!target.explorationSource&&(selected||preference!=='hunt')&&(kind==='task'||task.goal==='hunt'&&target.area===task.area))target.taskId=task.id;
 const route=routeTo(target.area),point=route?.[0]??target.point;
 const targetExitId=target.exitId;
 const path=route===null?[]:guidancePath(game,local,world,point),exit=!route?.length&&targetExitId?local.exits.find(exit=>exit.id===targetExitId):undefined;
 const gate=exit?exitBlockage(game,areas,local.id,exit):undefined,prerequisite=target===missingPrerequisite?.target?missingPrerequisite.blockage:undefined,blocked=route===null||!path.length||!!gate||!!prerequisite;
 const bearing=path.find(q=>distance(q,p)>1.5)??point;
 if(route?.length)detail=`下一站 ${areas[route[0].to].name} · ${route.length}次过图`;
 if(task&&target.taskId){const reward=game.journey.rewardView(task);detail+=' · '+tr('growth.taskReward',{experience:reward.experience,level:reward.afterLevel});}
 const targetId=(point as Point&{id?:string}).id,targetType:JourneyGuidance['targetType']=route?.length?'exit':targetId&&s.enemies.some(e=>e.id===targetId)?'enemy':targetId&&local.objects.some(o=>o.id===targetId)?'object':'position';
 const blockage=route===null?routeBlockage(game,areas,target.area):gate??prerequisite??(!path.length?pathBlockage(target.label,targetType==='enemy'):undefined);
 const metres=path.slice(1).reduce((n,q,i)=>n+distance(q,path[i]),0)+(targetType==='enemy'&&path.length?distance(path[path.length-1],point):0);
 return {destination:target,point,bearing,distance:metres,hops:route?.length??0,nextArea:route?.[0]?.to,instruction,detail,...objectiveReminder(game,areas,target,kind),safe:!local.enemies.length,blocked,blockage,kind,targetId,targetType};
}
