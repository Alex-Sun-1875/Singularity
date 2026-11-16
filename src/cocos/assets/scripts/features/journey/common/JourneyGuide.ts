import type {AreaDef,Point,WorldQuery} from '../../../core/Contracts';
import type {EnemyState,GameSession} from '../../../core/GameSession';
import type {NavigationTarget} from '../../automation/common/Automation';
import {availableRoutes,enemyApproachPath} from '../../automation/common/AutomationRoute';
import {chapterForArea,PLAYABLE_CHAPTERS,JOURNEY_TASKS,type JourneyTask} from '../data/ChapterJourney';
import {HUNTING_GROUNDS,HUNT_ENCOUNTERS} from '../../world/data/MonsterEcology';
import {journeyText as tr} from '../locales';
import {chapterTwoEncounterView} from '../../campaign/common/ChapterTwoEncounters';
import {CHAPTER_TWO_SIDE_QUEST_EVENTS,CHAPTER_TWO_SIDE_QUESTS} from '../../campaign/data/ChapterTwoSideQuests';

export interface JourneyGuidance {
 destination:NavigationTarget;point:Point;bearing:Point;distance:number;hops:number;nextArea?:string;
 instruction:string;detail:string;safe:boolean;blocked:boolean;kind:'task'|'hunt'|'boss';
 targetId?:string;targetType:'exit'|'object'|'enemy'|'position';
}
/** Guidance for a deliberately selected destination, sharing normal route gates. */
export function navigationGuidance(game:GameSession,areas:Record<string,AreaDef>,world:WorldQuery,target:NavigationTarget):JourneyGuidance|null {
 const local=areas[game.state.area];if(!local||!areas[target.area])return null;
 const route=availableRoutes(game,areas,target.area).get(target.area),point=route?.[0]??target.point;
 const path=route===undefined?[]:guidancePath(game,local,world,point),blocked=!path.length;
 return {destination:target,point,bearing:path.find(q=>distance(q,game.state.player)>1.5)??point,
  distance:path.slice(1).reduce((n,q,i)=>n+distance(q,path[i]),0),hops:route?.length??0,nextArea:route?.[0]?.to,
  instruction:target.label,detail:route?.length?`下一站 ${areas[route[0].to].name} · ${route.length}次过图`:target.objectId?'抵达后自动打开交互':'抵达后手动接近或从入口发起再战',
  safe:!game.state.enemies.some(e=>e.hp>0),blocked,kind:target.bossKey?'boss':'task',targetType:route?.length||target.exitId?'exit':target.objectId?'object':'position',targetId:route?.[0]?.id??target.exitId??target.objectId};
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
 const enemy=game.state.enemies.find(e=>e===target&&e.hp>0);
 const key=`${enemy?`${enemy.id}:${game.state.equipment.weapon}`:'walk'}:${p.x},${p.z}>${target.x},${target.z}`,cached=cache.routes.get(key);
 if(cached!==undefined)return cached;
 const path=(enemy?enemyApproachPath(game,world,enemy):world.path(p,target)).map(q=>({x:q.x,z:q.z}));
 if(cache.routes.size>=64)cache.routes.delete(cache.routes.keys().next().value!);
 cache.routes.set(key,path);return path;
}
/** One actionable destination. No saved tutorial mode, input capture, or quest locks. */
export function journeyGuidance(game:GameSession,areas:Record<string,AreaDef>,world?:WorldQuery,taskId?:string,preference=game.journey.tracking(),chapterId=chapterForArea(game.state.area)):JourneyGuidance|null {
 const s=game.state,p=s.player,local=areas[s.area];if(!local)return null;
 // Share one fresh regional search across all candidate hunting grounds.
 let routes:ReturnType<typeof availableRoutes>|undefined;
 const routeTo=(id:string)=>{if(id===s.area)return [];routes??=availableRoutes(game,areas);return routes.get(id)??null;};
 const chapter=PLAYABLE_CHAPTERS.find(c=>c.id===chapterId)!;
 const selected=JOURNEY_TASKS.find(t=>t.id===taskId&&game.journey.currentTask(t.chapter)?.id===t.id);
 let task=selected??game.journey.currentTask(chapter.id),kind:JourneyGuidance['kind']='task';
 let target:NavigationTarget|undefined,instruction='',detail='';
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
  // Pick a nearby interaction, never an answer inferred from the mechanism sequence.
  // Explicit route selections continue through navigationGuidance unchanged.
  const origin=s.area===current.area?p:areas[current.area].spawn;
  const ranked=choices.slice().sort((a,b)=>distance(origin,a.point)-distance(origin,b.point));
  const route=ranked.find(candidate=>candidate.area!==s.area||guidancePath(game,local,world,candidate.point).length)??ranked[0];
  if(!route)return {target:{area:current.area,point:generic??areas[current.area].spawn,label:current.name} as NavigationTarget,detail:tr('growth.encounterUnavailable')};
  const object=areas[route.area]?.objects.find(o=>o.eventId===route.eventId&&o.action==='campaign_event');
  return {target:{area:route.area,point:object??route.point,label:route.label,objectId:object?.id} as NavigationTarget,detail:tr(current.encounterId==='oath-array'?'growth.mechanismRoute':'growth.encounter')};
 };
 const sideQuestTarget=()=>{
  if(!s.progression.secondChapter)return;
  for(const quest of CHAPTER_TWO_SIDE_QUESTS){
   const id=quest.steps.find(step=>s.receipts['campaign:'+step]!==true),event=CHAPTER_TWO_SIDE_QUEST_EVENTS.find(def=>def.id===id);
   if(!event||!game.campaignEventAvailability(event.id,true).available)continue;
   const object=areas[event.area]?.objects.find(o=>o.action==='campaign_event'&&o.eventId===event.id);
   if(!object)continue;
   target={area:event.area,point:object,label:event.label,objectId:object.id,sideQuest:true};instruction=quest.name;detail=tr('growth.sideQuest',{quest:quest.name});return;
  }
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
 if(!selected&&preference==='hunt')hunting();
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
  if(chapter.id===1&&s.progression.level<chapter.endLevel&&s.area!==chapter.arena){hunting();detail=tr('growth.boss',{level:chapter.endLevel,current:s.progression.level});}
  else {kind='boss';const boss=s.area===chapter.arena?s.enemies.find(e=>e.hp>0&&e.bossId===chapter.boss):undefined;
   target={area:chapter.arena,point:boss??areas[chapter.arena].enemies.find(e=>e.bossId===chapter.boss)??areas[chapter.arena].spawn,label:chapter.bossName};instruction='挑战'+chapter.bossName;detail=s.progression.level<chapter.endLevel?tr('growth.boss',{level:chapter.endLevel,current:s.progression.level}):'共同关底 · 胜利即可通关';}
 }else if(chapter.id===1&&s.progression.level>=11&&(!s.receipts['journey:boss:2']||game.journey.currentTask(2))){
  task=game.journey.currentTask(2);const c=PLAYABLE_CHAPTERS[1],object=task&&areas[task.area].objects.find(o=>o.eventId===task!.id);target={area:task?.area??c.arena,point:object??areas[task?.area??c.arena].spawn,label:task?.name??c.bossName,objectId:task?.goal==='observe'?object?.id:undefined};instruction='第二章 · '+(task?.name??c.bossName);detail='前往高地继续旅程';if(task?.goal==='encounter'){const encounter=encounterTarget(task);target=encounter.target;detail=encounter.detail;}
 }else if(chapter.id===1)hunting();
 else sideQuestTarget();
 if(!target)return null;
 target.journey=true;
 if(task&&(selected||preference!=='hunt'))target.taskId=task.id;
 const route=routeTo(target.area),point=route?.[0]??target.point;
 const path=route===null?[]:guidancePath(game,local,world,point),blocked=route===null||!path.length;
 const bearing=path.find(q=>distance(q,p)>1.5)??point;
 if(route?.length)detail=`下一站 ${areas[route[0].to].name} · ${route.length}次过图`;
 if(task&&kind==='task'&&(selected||preference!=='hunt')){const reward=game.journey.rewardView(task);detail+=' · '+tr('growth.taskReward',{experience:reward.experience,level:reward.afterLevel});}
 const targetId=(point as Point&{id?:string}).id,targetType:JourneyGuidance['targetType']=route?.length?'exit':targetId&&s.enemies.some(e=>e.id===targetId)?'enemy':targetId&&local.objects.some(o=>o.id===targetId)?'object':'position';
 const metres=path.slice(1).reduce((n,q,i)=>n+distance(q,path[i]),0)+(targetType==='enemy'&&path.length?distance(path[path.length-1],point):0);
 return {destination:target,point,bearing,distance:metres,hops:route?.length??0,nextArea:route?.[0]?.to,instruction,detail,safe:!local.enemies.length,blocked,kind,targetId,targetType};
}
