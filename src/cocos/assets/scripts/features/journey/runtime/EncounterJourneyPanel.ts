import type {GameSession} from '../../../core/GameSession';
import type {Hud} from '../../../app/Hud';
import type {MenuRow,MenuChoice} from '../../../shared/ui/MenuPanel';
import {JOURNEY_TASKS,type JourneyTask} from '../data/ChapterJourney';
import {AREAS,getArea} from '../../world/data/WorldData';
import {CAMPAIGN_EVENTS} from '../../campaign/data/CampaignEvents';
import {campaignPrerequisiteTargets} from '../../campaign/common/CampaignNavigation';
import {chapterTwoEncounterView,chapterTwoChoiceHint} from '../../campaign/common/ChapterTwoEncounters';
import {encounterText as text} from '../../campaign/locales/ChapterTwoEncounterText';

type EncounterView=NonNullable<ReturnType<typeof chapterTwoEncounterView>>;
function rewardSummary(game:GameSession,task:JourneyTask){
 const reward=game.journey.rewardView(task),base=text('ui.reward',{experience:reward.experience,gold:task.gold,iron:task.iron});
 return base+'\n'+(reward.done?text('ui.rewardClaimed'):text('ui.rewardLevel',{level:reward.afterLevel,current:reward.level}));
}
function clueRows(view:EncounterView,action:string):MenuRow[]{
 return view.clues.map(clue=>({label:clue.known?text('ui.clueKnown',{name:clue.label}):text('ui.clueUnknown'),detail:'',action,disabled:true}));
}
function routeHint(route:EncounterView['routes'][number]):string {
 return chapterTwoChoiceHint('chapter2:'+route.id,'confirm')??'';
}
const routeStatus=(view:EncounterView,route:EncounterView['routes'][number])=>text(view.resolved?'ui.routeComplete':route.completed?'ui.actionCompleted':view.combatStarted&&route.method==='battle'?'ui.routeFighting':route.available?'ui.routeReady':'ui.routeBlocked');
/** Narrative preparation stays in a deliberate management page, away from combat HUD. */
export function renderEncounterJourney(hud:Hud,game:GameSession,menu:string):boolean {
 const parts=menu.split(':');if(parts[0]!=='journey-task'&&parts[0]!=='journey-encounter-route'&&parts[0]!=='journey-encounter-clues')return false;
 const view=chapterTwoEncounterView(game.state,parts[1]);if(!view)return false;
 const task=JOURNEY_TASKS.find(t=>t.id===view.taskId);if(!task)return false;
 const overview=(parts[0]==='journey-encounter-route'?parts[3]:parts[2])==='tasks',suffix=overview?':tasks':'';
 const back:MenuChoice={back:true,label:text('ui.backTask'),action:'journey-task:'+task.id+suffix},known=view.clues.filter(c=>c.known).length;
 if(parts[0]==='journey-encounter-clues'){
  hud.showList(text('ui.clues',{known,total:view.clues.length}),view.outcome,clueRows(view,menu),[back],0,{placement:'center'});return true;
 }
 if(parts[0]==='journey-encounter-route'){
  const route=view.routes.find(r=>r.id===parts[2]);if(!route)return false;
  const event=CAMPAIGN_EVENTS[route.eventId],hint=routeHint(route),prerequisites=!route.available&&!route.completed&&!view.resolved?campaignPrerequisiteTargets(game,AREAS,route.eventId):[];
  const buttons:MenuChoice[]=[back];
  if(!view.resolved&&!route.completed&&route.available)buttons.push({label:text('ui.autoGo'),action:'journey-field-go:'+route.eventId,primary:true});
  else if(!view.resolved&&view.combatStarted&&route.method==='battle'&&game.journey.currentTask(task.chapter)?.id===task.id)buttons.push({label:text('ui.returnBattle'),action:'journey-go:'+task.id,primary:true});
  else if(prerequisites.length)buttons.push({label:text('ui.autoPrerequisite'),action:prerequisites.length===1&&!prerequisites[0].blocked?`campaign-prerequisite-go:${route.eventId}:${prerequisites[0].id}`:'campaign-prerequisites:'+route.eventId});
  buttons.push({label:text('ui.map'),action:'journey-map:'+route.area});
  const rows:MenuRow[]=[{label:routeStatus(view,route),detail:route.completed&&!view.resolved?text('ui.actionRecorded'):route.reason,action:menu,disabled:true}];
  if(hint)rows.push({label:text('ui.choiceHint',{hint}),detail:text('ui.confirmOnSite'),action:menu,disabled:true});
  rows.push(...clueRows(view,menu));
  rows.push({label:text('ui.outcome'),detail:view.outcome,action:menu,disabled:true});
  hud.showList(route.label,`${getArea(route.area).name} · ${route.methodLabel}\n${event?.description??view.summary}`,rows,buttons,0,{placement:'center'});return true;
 }
 const current=game.journey.currentTask(task.chapter)?.id===task.id,done=game.journey.taskDone(task);
 const rows:MenuRow[]=view.routes.map(route=>({label:route.label,detail:route.methodLabel+' · '+routeStatus(view,route)+'\n'+(route.completed&&!view.resolved?text('ui.actionRecorded'):route.reason),action:`journey-encounter-route:${task.id}:${route.id}${suffix}`}));
 rows.push({label:text('ui.clues',{known,total:view.clues.length}),detail:known?view.clues.filter(c=>c.known).map(c=>c.label).join('；'):text('ui.noClues'),action:'journey-encounter-clues:'+task.id+suffix});
 rows.push({label:text('ui.outcome'),detail:view.combatStarted&&!view.resolved?text('ui.combatInProgress')+'\n'+view.outcome:view.outcome,action:'journey-encounter-clues:'+task.id+suffix});
 const status=done?text('ui.finished'):current?text('ui.taskAvailable'):view.resolved?text('ui.awaitingReward'):text('ui.taskLocked');
 hud.showList(view.title,`${getArea(view.area).name} · ${status}\n${view.summary}\n${rewardSummary(game,task)}`,rows,[{back:true,label:text(overview?'ui.backTaskPanel':'ui.backChapter'),action:overview?'journey-tasks:main':'journey-chapter:'+task.chapter},{label:text('ui.map'),action:'journey-map:'+view.area}],0,{placement:'center'});return true;
}
