import type {GameSession} from '../../../core/GameSession';
import type {Hud} from '../../../app/Hud';
import {FIELD_QUESTS,FIELD_QUEST_EVENTS} from '../../campaign/data/FieldQuests';
import {CHAPTER_TWO_SIDE_QUESTS,CHAPTER_TWO_SIDE_QUEST_EVENTS,chapterTwoSideQuestResponse,chapterTwoSideQuestOutcome,chapterTwoSideQuestRequiredBoss} from '../../campaign/data/ChapterTwoSideQuests';
import {sideBossById,sideBossForQuest} from '../../campaign/data/SideBosses';
import type {CampaignEventDef} from '../../campaign/data/CampaignEvents';
import {fieldQuestText as fieldText} from '../../campaign/locales/FieldQuestText';
import {getArea,AREAS} from '../../world/data/WorldData';
import {availableRoutes} from '../../automation/common/AutomationRoute';
import {encounterText as text} from '../../campaign/locales/ChapterTwoEncounterText';
import {taskPanelTabs} from './TaskPanelNavigation';
import {taskPanelText} from '../locales/TaskPanelText';

export const SIDE_QUESTS=[...FIELD_QUESTS,...CHAPTER_TWO_SIDE_QUESTS];
export const SIDE_QUEST_EVENTS=[...FIELD_QUEST_EVENTS,...CHAPTER_TWO_SIDE_QUEST_EVENTS];
export const sideStepBoss=(id:string)=>sideBossById(chapterTwoSideQuestRequiredBoss(id)??'');
export function sideBattleHint(game:GameSession,id:string){
 const boss=sideStepBoss(id);if(!boss)return '';
 return game.state.flags['boss_defeated:'+boss.bossId]?text('boss.stepAlreadyKilled'):text('boss.stepFight',{name:boss.name,level:boss.level,area:getArea(boss.area).name});
}
export function sideEventStatus(game:GameSession,event:CampaignEventDef){
 const base=game.campaignEventAvailability(event.id,true),quest=SIDE_QUESTS.find(q=>q.steps.some(id=>id===event.id));
 if(base.completed)return base;
 if(quest?.chapter===2&&!game.state.progression.secondChapter)return {...base,available:false,reason:text('ui.chapterLevelGate')};
 if(base.available&&!availableRoutes(game,AREAS).has(event.area))return {...base,available:false,reason:text('ui.routeUnavailable')};
 return base;
}
/** All optional field stories share the same steps, route gates and saved choices. */
export function renderSideQuestPanel(hud:Hud,game:GameSession,menu:string):boolean {
 const parts=menu.split(':'),s=game.state;
 if(menu==='journey-tasks:side'){
  hud.showList(text('ui.taskPanel'),text('ui.sideHelp'),SIDE_QUESTS.map(q=>{
   const hidden='hidden'in q?q.hidden:undefined,known=!hidden||s.flags[hidden],count=q.steps.filter(id=>!!s.receipts['campaign:'+id]).length,next=q.steps.find(id=>!s.receipts['campaign:'+id]),event=SIDE_QUEST_EVENTS.find(e=>e.id===next),status=event?sideEventStatus(game,event):undefined;
   return {label:known?text('ui.sideName',{chapter:q.chapter,name:q.name}):fieldText('ui.undiscovered'),detail:!known?fieldText('ui.explore'):text('ui.stepProgress',{count,total:q.steps.length})+' · '+text(next?'ui.taskInProgress':'ui.finished')+'\n'+(event?getArea(event.area).name+' · '+event.label+'\n'+status!.reason+'\n':'')+text('boss.taskMaterials',{reward:q.reward}),disabled:!known,action:'journey-side-task:'+q.id};
  }),[{back:true,label:text('ui.returnJourney'),action:'close'},{label:taskPanelText('hunt'),action:'hunting'},{label:taskPanelText('campaignLog'),action:'campaign-log'}],hud.touchTargetSize,{placement:'center',tabs:taskPanelTabs('side')});return true;
 }
 if(parts[0]!=='journey-side-task')return false;
 const quest=SIDE_QUESTS.find(q=>q.id===parts[1]);if(!quest||'hidden'in quest&&!s.flags[quest.hidden])return true;
 const rows=quest.steps.map((id,index)=>{const event=SIDE_QUEST_EVENTS.find(e=>e.id===id)!,status=sideEventStatus(game,event),choice=event.choices?.find(c=>c.id===s.receipts['campaign:choice:'+id]),battle=sideBattleHint(game,id);return {label:`${index+1} · ${event.label}`,detail:getArea(event.area).name+' · '+(status.completed?text('ui.actionCompleted'):status.reason)+(battle?'\n'+battle:'')+(choice?'\n'+text('ui.recordedChoice',{choice:choice.label}):''),action:'journey-field-task:'+id+':tasks'};});
 const context=chapterTwoSideQuestResponse(s,quest.id),outcome=chapterTwoSideQuestOutcome(s,quest.id),locked=quest.chapter===2&&!s.progression.secondChapter;
 const boss=sideBossForQuest(quest.id);
 hud.showList(quest.name,text(locked?'ui.chapterLevelGate':'ui.sideSteps')+'\n'+text('boss.taskMaterials',{reward:quest.reward})+(boss?'\n'+text('boss.rewardSplit'):'')+(context?'\n'+context:'')+(outcome?'\n'+text('ui.outcome')+'：'+outcome:''),rows,[{back:true,label:text('ui.backSide'),action:'journey-tasks:side'}],0,{placement:'center'});return true;
}
