import type {GameSession} from '../../../core/GameSession';
import type {Hud} from '../../../app/Hud';
import {PLAYABLE_CHAPTERS,JOURNEY_TASKS,journeyBossKey,chapterForArea,playableArea} from '../data/ChapterJourney';
import {chapterWeaponIds} from '../../equipment/data/ChapterWeapons';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import {FIELD_QUESTS,FIELD_QUEST_EVENTS} from '../../campaign/data/FieldQuests';
import {fieldQuestText as fieldText} from '../../campaign/locales/FieldQuestText';
import {getArea,AREAS} from '../../world/data/WorldData';
import {journeyText as tr} from '../locales';
import {LIFECYCLE_GROUPS,lifecycleGroup} from '../../equipment/data/EquipmentLifecycle';
import {Label} from 'cc';
import {artifactWeaponForStyle} from '../../equipment/data/GrowingEquipment';
import {CAMPAIGN_ENEMY_TEMPLATES} from '../../campaign/data/Campaign';

const styleName=(style:string)=>tr(style==='WAR'?'life.styleWar':style==='BOW'?'life.styleBow':style==='FIR'?'life.styleFire':'life.styleThunder');
const timeText=(seconds:number)=>`${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;
function bossStatus(game:GameSession,boss:string){
 const enemy=[...game.state.enemies,...Object.values(game.state.encounters).flat()].find(e=>e.bossId===boss);
 if(enemy&&enemy.hp>0)return tr('life.bossFighting');
 if(!game.state.flags[`boss_defeated:${boss}`]&&!enemy?.respawnCount&&enemy?.hp!==0)return tr('life.bossAlive');
 const v=game.bossLoot.view(boss);return v.remaining?tr('life.cooldown',{time:timeText(v.remaining)}):tr('life.bossReady');
}
let timerSecond=-1;
export function updateJourneyCooldowns(hud:Hud,game:GameSession,force=false){
 const second=Math.floor(Date.now()/1000);if(!force&&second===timerSecond)return;timerSecond=second;
 for(const label of hud.root.getComponentsInChildren(Label))if(label.node.activeInHierarchy&&label.node.name.startsWith('BossCooldown:'))label.string=bossStatus(game,label.node.name.slice(13));
}

export function renderJourney(hud:Hud,game:GameSession,menu:string){
 const s=game.state,j=game.journey,parts=menu.split(':');
 if(parts[0]==='journey-field'){
  const chapter=Number(parts[1]),quests=FIELD_QUESTS.filter(q=>q.chapter===chapter);
  hud.showList(fieldText('ui.side'),fieldText('ui.chapterHint',false,{chapter}),quests.map(q=>{
   const hidden='hidden'in q?q.hidden:undefined,discovered=!hidden||s.flags[hidden],next=q.steps.find(id=>!s.receipts[`campaign:${id}`]),event=FIELD_QUEST_EVENTS.find(e=>e.id===next);
   return {label:!discovered?fieldText('ui.undiscovered'):`${fieldText(next?'ui.progress':'ui.complete')} · ${q.name}`,detail:!discovered?fieldText('ui.explore'):`${q.reward}${event?'\n'+fieldText('ui.next')+'：'+getArea(event.area).name+' · '+event.label:''}`,action:discovered&&next?`journey-field-task:${next}`:'journey-unavailable'};
  }),[{label:fieldText('ui.backChapter'),action:`journey-chapter:${chapter}`},{label:fieldText('ui.return'),action:'close'}]);return;
 }
 if(parts[0]==='journey-field-task'){
  const q=FIELD_QUESTS.find(q=>q.steps.some(id=>id===parts[1])),event=FIELD_QUEST_EVENTS.find(e=>e.id===parts[1]);if(!q||!event||'hidden'in q&&!s.flags[q.hidden])return;
  const done=!!s.receipts[`campaign:${event.id}`],ready=!done&&event.requires?.every(f=>s.flags[f]);
  hud.show(event.label,`${getArea(event.area).name}\n\n${event.description}\n\n${fieldText('ui.reward')}：${q.reward}`,[...(ready?[{label:fieldText('ui.go'),action:`journey-field-go:${event.id}`}]:[]),{label:fieldText('ui.map'),action:`journey-map:${event.area}`},{label:fieldText('ui.backField'),action:`journey-field:${q.chapter}`}]);return;
 }
 if(parts[0]==='journey-life-reward'){
  const group=lifecycleGroup(parts[1]);if(!group||group.route!=='task'||group.chapter>2)return;
  hud.showList(tr('life.choose',{name:group.name}),tr('life.choice'),group.items.map(id=>{const item=EQUIPMENT[id];return {label:item.name,detail:group.slot==='weapon'?tr('life.weaponChoice',{level:item.requiredLevel??1,family:item.weaponFamily??'',power:item.power??0}):game.itemView(id).description,action:`journey-life-claim:${group.id}:${id}`};}),[{label:'返回本章',action:`journey-chapter:${group.chapter}`}]);return;
 }
 if(parts[0]==='journey-loot-style'){
  const chapter=Number(parts[1]),current=game.bossLoot.view().style;
  hud.showList(tr('life.preference',{style:styleName(current)}),tr('life.preferenceHint'),['WAR','BOW','FIR','THU'].map(style=>({label:styleName(style),detail:current===style?tr('life.selected'):'',action:`journey-loot-set:${style}:${chapter}`})),[{label:'返回奖池',action:`journey-loot:${chapter}`}]);return;
 }
 if(parts[0]==='journey-loot'){
  const chapter=Number(parts[1]),v=game.bossLoot.view(),daily=game.huntingExperience();
  const rows=LIFECYCLE_GROUPS.filter(g=>g.chapter===chapter&&g.route==='battle').map(g=>({label:tr('life.random',{quality:g.quality,name:g.name}),detail:tr('life.randomDetail',{level:g.requiredLevel}),action:`journey-loot-item:${g.items.find(id=>id.endsWith('_'+v.style))??g.items[0]}:${chapter}`}));
  for(const id of [artifactWeaponForStyle[v.style],'DG_A02'])rows.push({label:tr('life.artifact',{name:EQUIPMENT[id].name}),detail:tr('life.artifactDetail'),action:`journey-loot-item:${id}:${chapter}`});
  rows.push({label:tr('life.preference',{style:styleName(v.style)}),detail:tr('life.preferenceHint'),action:`journey-loot-style:${chapter}`});
  const bosses=Object.values(AREAS).filter(a=>playableArea(a.id)&&chapterForArea(a.id)===chapter).flatMap(a=>a.enemies.filter(e=>!!e.bossId).map(e=>({area:a.id,enemy:e})));
  for(const b of bosses)rows.push({label:`${b.area} · ${PLAYABLE_CHAPTERS.find(c=>c.boss===b.enemy.bossId)?.bossName??CAMPAIGN_ENEMY_TEMPLATES[b.enemy.bossId!]?.name??getArea(b.area).name}`,detail:bossStatus(game,b.enemy.bossId!),action:`journey-map:${b.area}`});
  hud.showList(tr('life.title',{chapter}),`${tr('life.rules')}\n${tr('life.daily',{earned:daily.earned,cap:daily.cap,idle:daily.idleEarned,idleCap:daily.idleCap,level:daily.startingLevel})}`,rows,[{label:'返回本章',action:`journey-chapter:${chapter}`}]);
  for(const b of bosses){const label=hud.root.getComponentsInChildren(Label).find(l=>l.node.name==='MenuRowDetail'&&l.node.parent?.name===`journey-map:${b.area}`);if(label)label.node.name='BossCooldown:'+b.enemy.bossId;}
  updateJourneyCooldowns(hud,game,true);return;
 }
 if(parts[0]==='journey-loot-item'){
  const item=EQUIPMENT[parts[1]];if(!item)return;hud.show(item.name,game.itemView(item.id).description,[{label:'返回奖池',action:`journey-loot:${Number(parts[2])||item.chapter||chapterForArea(s.area)}`}]);return;
 }
 const navigation=(id?:string)=>{
  const a=hud.automationView,same=!!id&&a.taskId===id;
  return {label:same&&a.navigating?'停止寻路':same&&a.paused?'继续寻路':'开启自动寻路',action:same&&a.navigating?'journey-stop':`journey-go${id?':'+id:''}`};
 };
 if(parts[0]==='journey-reward'){
  const chapter=Number(parts[1]),route=parts[2];
  hud.showList(`第${chapter}章 · ${route==='task'?'任务':route==='hunt'?'狩猎':'关底'}史诗武器`,'四流派任选一件；来源独立，选择后永久保存。',chapterWeaponIds(chapter,route).map(id=>({label:EQUIPMENT[id].name,detail:`Lv${EQUIPMENT[id].requiredLevel} · ${EQUIPMENT[id].weaponFamily}\n攻击/技能威力 +${EQUIPMENT[id].power!/3}%`,action:`journey-claim:${chapter}:${route}:${id}`})),[{label:'返回本章',action:`journey-chapter:${chapter}`}]);return;
 }
 if(parts[0]==='journey-task'){
  const task=JOURNEY_TASKS.find(t=>t.id===parts[1]);if(!task)return;
  const done=j.taskDone(task),goal=task.goal==='hunt'?`游荡怪 ${j.progress(task)} / ${task.kills}`:task.goal==='clear'?'击败本地固定敌阵（含固定首领），游荡怪无需清空':'在现场观察战况';
  hud.show(task.name,`${task.story}\n\n地点：${getArea(task.area).name} · ${task.area}\n目标：${goal}\n奖励：经验 ${task.experience} · 金币 ${task.gold} · 铁 ${task.iron}\n状态：${done?'已完成':j.currentTask(task.chapter)?.id===task.id?'进行中 · 可开启自动寻路':'先完成前一阶段'}\n\n抵达调查目标后自动打开交互；清场与狩猎自动结算。此处寻路遇敌暂停；顶部“自动任务”会连续赶路、战斗，等待确认调查后推进下一阶段。`,[...(j.currentTask(task.chapter)?.id===task.id?[navigation(task.id)]:[]),{label:'在地图查看地点',action:`journey-map:${task.area}`},{label:'返回本章',action:`journey-chapter:${task.chapter}`}]);return;
 }
 if(parts[0]==='journey-chapter'){
  const chapter=PLAYABLE_CHAPTERS.find(c=>c.id===Number(parts[1]));if(!chapter)return;
  const tasks=JOURNEY_TASKS.filter(t=>t.chapter===chapter.id),done=tasks.filter(t=>j.taskDone(t)).length,won=!!s.receipts[journeyBossKey(chapter.id)];
  const rows=tasks.map((t,i)=>({label:`${j.taskDone(t)?'已完成':hud.automationView.navigating&&hud.automationView.taskId===t.id?'寻路中':j.currentTask(chapter.id)?.id===t.id?'进行中':'待进行'} · ${i+1} ${t.name}`,detail:`${getArea(t.area).name} · 经验 ${t.experience}${t.goal==='hunt'?` · ${j.progress(t)}/${t.kills}`:''}${j.currentTask(chapter.id)?.id===t.id?' · 可自动寻路':''}`,action:`journey-task:${t.id}`}));
  rows.push({label:won?'关底已通关':`共同关底 · ${chapter.bossName}`,detail:`${chapter.arena} · ${tr('growth.bossRoute',{level:chapter.endLevel})}`,action:`journey-map:${chapter.arena}`});
  for(const reward of j.lifecycleRewards(chapter.id))rows.push({label:tr('life.task',{quality:reward.quality,name:reward.name}),detail:reward.claimed?tr('life.claimed',{name:EQUIPMENT[String(reward.claimed)]?.name??''}):reward.legacyPending?tr('life.legacyHint'):reward.available?tr('life.ready'):tr('life.locked',{task:JOURNEY_TASKS.find(t=>t.id===reward.task)?.name??''}),action:reward.available?`journey-life-reward:${reward.id}`:'journey-unavailable'});
  rows.push({label:fieldText('ui.side'),detail:fieldText('ui.entryDetail'),action:`journey-field:${chapter.id}`});
  rows.push({label:tr('life.sources'),detail:tr('life.rules'),action:`journey-loot:${chapter.id}`});
  for(const route of ['task','hunt','boss'])if(j.rewardAvailable(chapter.id,route))rows.push({label:tr('life.legacy',{route}),detail:tr('life.legacyHint'),action:`journey-reward:${chapter.id}:${route}`});
  hud.showList(`第${chapter.id}章 ${chapter.name}`,`任务 ${done}/5 · 关底 ${won?'已通关':'未通关'} · Lv${chapter.level}—${chapter.endLevel}\n${chapter.story}\n${tr('growth.hunt')}`,rows,[navigation(j.currentTask(chapter.id)?.id),{label:j.tracking()==='hunt'?'切换任务':'切换狩猎',action:j.tracking()==='hunt'?'journey-track:task':'journey-track:hunt'},{label:'八章旅程',action:'journey'}]);return;
 }
 hud.showList('破晓之战 · 八章旅程',tr('growth.summary',{earned:game.huntingExperience().earned,cap:game.huntingExperience().cap}),j.chapters().map(c=>({label:`第${c.id}章 ${c.name}`,detail:c.available?(c.complete?'已通关 · 可继续任务与狩猎':'已开放 · 任务和刷怪均可推进'):'尚未开放',disabled:!c.available,action:c.available?`journey-chapter:${c.id}`:'journey-locked'})),[{label:'出发狩猎',action:'hunting'},{label:'战役见闻',action:'campaign-log'},{label:'返回旅途',action:'close'}]);
}
