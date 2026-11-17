import type {GameSession} from '../../../core/GameSession';
import type {Hud} from '../../../app/Hud';
import {JOURNEY_CHAPTERS,PLAYABLE_CHAPTERS,JOURNEY_TASKS,journeyBossKey,journeyChapterDisplay} from '../data/ChapterJourney';
import {campaignText} from '../../campaign/locales';
import {campaignPrerequisiteTargets} from '../../campaign/common/CampaignNavigation';
import {fieldQuestText as fieldText} from '../../campaign/locales/FieldQuestText';
import {getArea,AREAS} from '../../world/data/WorldData';
import {journeyText as tr} from '../locales';
import {Label} from 'cc';
import {chapterTwoEncounterView} from '../../campaign/common/ChapterTwoEncounters';
import {encounterText} from '../../campaign/locales/ChapterTwoEncounterText';
import {renderEncounterJourney} from './EncounterJourneyPanel';
import {renderTaskOverview} from './TaskOverviewPanel';
import {renderJourneyBossRewards,journeyBossState} from './JourneyBossRewards';
import {mainBossEquipmentView} from '../../equipment/common/BossLoot';
import {SIDE_QUESTS,SIDE_QUEST_EVENTS,sideEventStatus,sideStepBoss,sideBattleHint,sideQuestRewardText,sideEventRewardText} from './SideQuestPanel';
import {randomBossRewardText} from '../../combat/runtime/BossRewardPresentation';
import {taskPanelTabs} from './TaskPanelNavigation';
import {taskPanelText as panelText} from '../locales/TaskPanelText';
import {pacingRewardText} from '../locales/PacingText';
import {renderExplorationGrowth,explorationGrowthEntry} from './ExplorationGrowthPanel';

const styleName=(style:string)=>tr(style==='WAR'?'life.styleWar':style==='BOW'?'life.styleBow':style==='FIR'?'life.styleFire':'life.styleThunder');
let timerSecond=-1;
export function updateJourneyCooldowns(hud:Hud,game:GameSession,force=false){
 const second=Math.floor(Date.now()/1000);if(!force&&second===timerSecond)return;timerSecond=second;
 for(const label of hud.root.getComponentsInChildren(Label))if(label.node.activeInHierarchy&&label.node.name.startsWith('BossCooldown:'))label.string=journeyBossState(game,label.node.name.slice(13));
}

export function renderJourney(hud:Hud,game:GameSession,menu:string){
 const s=game.state,j=game.journey,parts=menu.split(':');
 if(renderExplorationGrowth(hud,game,menu))return;
 if(renderTaskOverview(hud,game,menu))return;
 if(renderEncounterJourney(hud,game,menu))return;
 if(renderJourneyBossRewards(hud,game,menu))return;
 if(parts[0]==='journey-field'){
  const chapter=Number(parts[1]),quests=SIDE_QUESTS.filter(q=>q.chapter===chapter);
  hud.showList(fieldText('ui.side'),fieldText('ui.chapterHint',false,{chapter}),quests.map(q=>{
   const hidden='hidden'in q?q.hidden:undefined,discovered=!hidden||s.flags[hidden],next=q.steps.find(id=>!s.receipts[`campaign:${id}`]),event=SIDE_QUEST_EVENTS.find(e=>e.id===next);
   return {label:!discovered?fieldText('ui.undiscovered'):`${fieldText(next?'ui.progress':'ui.complete')} · ${q.name}`,detail:!discovered?fieldText('ui.explore'):`${sideQuestRewardText(q)}${event?'\n'+fieldText('ui.next')+'：'+getArea(event.area).name+' · '+event.label+'\n'+sideEventStatus(game,event).reason:''}`,disabled:!discovered,action:`journey-field-task:${next??q.steps[q.steps.length-1]}`};
  }),[{back:true,label:fieldText('ui.backChapter'),action:`journey-chapter:${chapter}`}],hud.touchTargetSize,{placement:'center',tabs:taskPanelTabs('side')});return;
 }
 if(parts[0]==='journey-field-task'){
  const q=SIDE_QUESTS.find(q=>q.steps.some(id=>id===parts[1])),event=SIDE_QUEST_EVENTS.find(e=>e.id===parts[1]);if(!q||!event||'hidden'in q&&!s.flags[q.hidden])return;
  const choice=event.choices?.find(c=>c.id===s.receipts['campaign:choice:'+event.id]);
  const status=sideEventStatus(game,event),ready=status.available;
  const prerequisites=!ready&&!status.completed?campaignPrerequisiteTargets(game,AREAS,event.id):[];
  const boss=sideStepBoss(event.id),battle=sideBattleHint(game,event.id),onlyBoss=prerequisites.length===1&&prerequisites[0].id===boss?.enemyId;
  const navigation=prerequisites.length?{label:encounterText(onlyBoss?'boss.autoFight':'ui.autoPrerequisite'),action:prerequisites.length===1&&!prerequisites[0].blocked?`campaign-prerequisite-go:${event.id}:${prerequisites[0].id}`:`campaign-prerequisites:${event.id}`}:undefined,overview=parts[2]==='tasks';
  hud.show(event.label,`${getArea(event.area).name}\n\n${status.completed?campaignText('event.completed')+'\n'+status.reason:status.reason}${battle?'\n\n'+battle:''}\n\n${event.description}${choice?'\n\n'+encounterText('ui.recordedChoice',{choice:choice.label})+'\n'+choice.text:''}\n\n${encounterText('boss.taskMaterials',{reward:sideEventRewardText(event)})}${boss?'\n\n'+randomBossRewardText():''}`,[...(ready?[{label:encounterText('ui.autoGo'),action:`journey-field-go:${event.id}`}]:navigation?[navigation]:[]),{label:fieldText('ui.map'),action:`journey-map:${event.area}`},{back:true,label:overview?encounterText('ui.backSide'):fieldText('ui.backField'),action:overview?`journey-side-task:${q.id}`:`journey-field:${q.chapter}`}]);return;
 }
 if(parts[0]==='journey-loot-style'){
  const chapter=Number(parts[1]),current=game.bossLoot.view().style;
  hud.showList(tr('life.preference',{style:styleName(current)}),tr('life.preferenceHint'),['WAR','BOW','FIR','THU'].map(style=>({label:styleName(style),detail:current===style?tr('life.selected'):'',action:`journey-loot-set:${style}:${chapter}`})),[{back:true,label:'返回奖池',action:`journey-loot:${chapter}`}]);return;
 }
 const navigation=(id?:string)=>{
  const a=hud.automationView,same=!!id&&a.taskId===id;
  return {label:same&&a.navigating?'停止寻路':same&&a.paused?'继续寻路':encounterText('ui.autoGo'),action:same&&a.navigating?'journey-stop':`journey-go${id?':'+id:''}`};
 };
 if(parts[0]==='journey-task'){
  const task=JOURNEY_TASKS.find(t=>t.id===parts[1]);if(!task)return;
  const done=j.taskDone(task),goal=task.goal==='hunt'?`游荡怪 ${j.progress(task)} / ${task.kills}`:task.goal==='clear'?'击败本地固定敌阵（含固定首领），游荡怪无需清空':'在现场观察战况';
  const unlocked=task.chapter===1||s.progression.secondChapter,reward=j.rewardView(task);
  hud.show(task.name,`${task.story}\n\n地点：${getArea(task.area).name} · ${task.area}\n目标：${goal}\n奖励：${pacingRewardText(reward)}\n状态：${done?'已完成':!unlocked?encounterText('ui.chapterLevelGate'):j.currentTask(task.chapter)?.id===task.id?'进行中 · 可自动前往':'先完成前一阶段'}\n\n抵达调查目标后自动打开交互；清场与狩猎自动结算。此处寻路遇敌暂停；左栏和顶部的自动任务会连续赶路、战斗并执行调查，现场行动和剧情分支选择首个正常推进选项，剧情结束后继续。`,[...(unlocked&&j.currentTask(task.chapter)?.id===task.id?[navigation(task.id)]:[]),{label:'在地图查看地点',action:`journey-map:${task.area}`},{back:true,label:parts[2]==='tasks'?encounterText('ui.backTaskPanel'):'返回本章',action:parts[2]==='tasks'?'journey-tasks:main':`journey-chapter:${task.chapter}`}]);return;
 }
 if(parts[0]==='journey-chapter'){
  const chapter=JOURNEY_CHAPTERS.find(c=>c.id===Number(parts[1]));if(!chapter){renderTaskOverview(hud,game,'journey-tasks:chapters');return;}
  const display=journeyChapterDisplay(chapter);
  if(!chapter.available){
   hud.show(display.title,display.story,[{back:true,label:panelText('backChapters'),action:'journey-tasks:chapters'}],false,{placement:'center',dismissOnBackdrop:false,tabs:taskPanelTabs('chapters')});return;
  }
  const tasks=JOURNEY_TASKS.filter(t=>t.chapter===chapter.id),done=tasks.filter(t=>j.taskDone(t)).length,won=!!s.receipts[journeyBossKey(chapter.id)];
  const rows=tasks.map((t,i)=>{const encounter=chapterTwoEncounterView(s,t.id),known=encounter?.clues.filter(c=>c.known).length??0;return {label:`${j.taskDone(t)?'已完成':chapter.id===2&&!s.progression.secondChapter?panelText('status.locked'):hud.automationView.navigating&&hud.automationView.taskId===t.id?'寻路中':j.currentTask(chapter.id)?.id===t.id?'进行中':'待进行'} · ${i+1} ${t.name}`,detail:`${getArea(t.area).name} · ${pacingRewardText(j.rewardView(t))}${encounter?'\n'+encounterText('ui.routeCount',{count:encounter.routes.length,known,total:encounter.clues.length}):t.goal==='hunt'?` · ${j.progress(t)}/${t.kills}`:''}${(chapter.id===1||s.progression.secondChapter)&&j.currentTask(chapter.id)?.id===t.id?' · 可自动寻路':''}`,action:`journey-task:${t.id}`};});
  rows.push(explorationGrowthEntry(game,chapter.id));
  rows.push({label:won?'关底已通关':`共同关底 · ${chapter.bossName}`,detail:`${chapter.arena} · ${tr('growth.bossRoute',{level:chapter.endLevel})}\n${encounterText('boss.mainCompletion')}`,action:`journey-map:${chapter.arena}`});
  const fixed=mainBossEquipmentView(s,chapter.id);rows.push({label:encounterText('boss.fixedTitle'),detail:encounterText(fixed.awarded?'boss.awarded':'boss.awaitFirstWin'),action:`journey-main-boss-rewards:${chapter.id}`});
  rows.push({label:fieldText('ui.side'),detail:fieldText('ui.entryDetail'),action:`journey-field:${chapter.id}`});
  rows.push({label:tr('life.sources'),detail:encounterText('boss.randomShort'),action:`journey-loot:${chapter.id}`});
  const current=j.currentTask(chapter.id),unlocked=chapter.id===1||s.progression.secondChapter,progress=panelText('progress',{done,total:tasks.length,boss:panelText(won?'boss.done':'boss.pending')}),goal=!unlocked?panelText('levelGate',{level:chapter.level}):current?panelText('current',{name:current.name}):won?panelText('chapterFinished'):panelText('current',{name:panelText('bossGoal',{boss:chapter.bossName})});
  hud.showList(display.title,display.story+'\n'+progress+'\n'+goal,rows,[...(unlocked&&current?[navigation(current.id)]:[]),{label:j.tracking()==='hunt'?'切换任务':'切换狩猎',action:j.tracking()==='hunt'?'journey-track:task':'journey-track:hunt'},{back:true,label:panelText('backChapters'),action:'journey-tasks:chapters'}],hud.touchTargetSize,{placement:'center',tabs:taskPanelTabs('chapters')});return;
 }
 renderTaskOverview(hud,game,'journey-tasks:chapters');
}
