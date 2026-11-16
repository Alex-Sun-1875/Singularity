import type {GameSession} from '../../../core/GameSession';
import type {Hud} from '../../../app/Hud';
import type {MenuRow} from '../../../shared/ui/MenuPanel';
import {JOURNEY_CHAPTERS,JOURNEY_TASKS,journeyBossKey,journeyChapterDisplay,type JourneyTask,type JourneyChapter} from '../data/ChapterJourney';
import {getArea} from '../../world/data/WorldData';
import {chapterTwoEncounterView} from '../../campaign/common/ChapterTwoEncounters';
import {encounterText as text} from '../../campaign/locales/ChapterTwoEncounterText';
import {taskPanelText as panelText} from '../locales/TaskPanelText';
import {taskPanelTabs} from './TaskPanelNavigation';
import {renderSideQuestPanel} from './SideQuestPanel';

export function taskGoal(game:GameSession,task:JourneyTask):string {
 if(task.goal==='encounter')return text('ui.goal.encounter');
 if(task.goal==='hunt')return text('ui.goal.hunt',{count:game.journey.progress(task),total:task.kills??0});
 return text(task.goal==='clear'?'ui.goal.clear':'ui.goal.observe');
}
const chapterRow=(game:GameSession,chapter:JourneyChapter):MenuRow=>{
 const display=journeyChapterDisplay(chapter),action='journey-chapter:'+chapter.id;
 if(!chapter.available)return {label:display.title,detail:display.story,action};
 const tasks=JOURNEY_TASKS.filter(task=>task.chapter===chapter.id),done=tasks.filter(task=>game.journey.taskDone(task)).length,current=game.journey.currentTask(chapter.id),won=!!game.state.receipts[journeyBossKey(chapter.id)],locked=chapter.id===2&&!game.state.progression.secondChapter;
 const progress=panelText('progress',{done,total:tasks.length,boss:panelText(won?'boss.done':'boss.pending')}),goal=locked?panelText('levelGate',{level:chapter.level}):current?panelText('current',{name:current.name}):won?panelText('chapterFinished'):panelText('current',{name:panelText('bossGoal',{boss:chapter.bossName})});
 return {label:display.title,detail:display.story+'\n'+progress+'\n'+goal,action};
};
/** One task workspace: chapter stories, main objectives and optional stories. */
export function renderTaskOverview(hud:Hud,game:GameSession,menu:string):boolean {
 if(renderSideQuestPanel(hud,game,menu))return true;
 const chapterIndex=menu==='journey'||menu==='journey-chapters'||menu==='journey-tasks'||menu==='journey-tasks:chapters';
 if(chapterIndex||menu==='journey-future'){
  const future=menu==='journey-future',chapters=JOURNEY_CHAPTERS.filter(chapter=>future?chapter.id>3:chapter.id<=3),rows:MenuRow[]=chapters.map(chapter=>chapterRow(game,chapter));
  if(!future)rows.push({label:panelText('future.title'),detail:panelText('future.summary'),action:'journey-future'});
  hud.showList(panelText(future?'future.title':'title'),panelText(future?'future.description':'overview'),rows,[{back:true,label:panelText(future?'backChapters':'return'),action:future?'journey-tasks:chapters':'close'},...future?[]:[{label:panelText('hunt'),action:'hunting'},{label:panelText('campaignLog'),action:'campaign-log'}]],hud.touchTargetSize,{placement:'center',tabs:taskPanelTabs('chapters')});return true;
 }
 if(menu==='journey-tasks:main'){
  const rows:MenuRow[]=JOURNEY_TASKS.map(task=>{
   const done=game.journey.taskDone(task),current=game.journey.currentTask(task.chapter)?.id===task.id,locked=task.chapter===2&&!game.state.progression.secondChapter,reward=game.journey.rewardView(task),view=chapterTwoEncounterView(game.state,task.id),status=panelText(done?'status.done':locked?'status.locked':current?'status.current':'status.pending');
   return {label:panelText('taskTitle',{chapter:task.chapter,name:task.name}),detail:status+' · '+getArea(task.area).name+' · '+taskGoal(game,task)+'\n'+text('ui.reward',{experience:reward.experience,gold:task.gold,iron:task.iron})+(view?'\n'+text('ui.routeCount',{count:view.routes.length,known:view.clues.filter(clue=>clue.known).length,total:view.clues.length}):''),action:'journey-task:'+task.id+':tasks'};
  });
  hud.showList(panelText('title'),panelText('mainHelp'),rows,[{back:true,label:panelText('return'),action:'close'},{label:panelText('hunt'),action:'hunting'},{label:panelText('campaignLog'),action:'campaign-log'}],hud.touchTargetSize,{placement:'center',tabs:taskPanelTabs('main')});return true;
 }
 return false;
}
