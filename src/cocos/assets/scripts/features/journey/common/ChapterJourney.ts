import {journeyText as tr} from '../locales';
import type {GameState,EnemyState} from '../../../core/GameSession';
import {JOURNEY_CHAPTERS,PLAYABLE_CHAPTERS,JOURNEY_TASKS,journeyTaskKey,journeyBossKey,chapterForArea,type JourneyTask} from '../data/ChapterJourney';
import {chapterWeaponIds} from '../../equipment/data/ChapterWeapons';
import {campaignBattle} from '../../cinematics/data/CampaignScenes';
import {LIFECYCLE_GROUPS,lifecycleGroup,lifecycleTaskSource} from '../../equipment/data/EquipmentLifecycle';

interface Host {state():GameState;experience(source:string,amount:number):void;grant(id:string,source:string):void;changed():void;emit(type:string,text:string,extra?:Record<string,unknown>):void}
export class ChapterJourney {
 constructor(private host:Host){}
 private get s(){return this.host.state();}
 taskDone(task:JourneyTask){return !!this.s.receipts[journeyTaskKey(task.id)];}
 currentTask(chapter=chapterForArea(this.s.area)){return JOURNEY_TASKS.find(t=>t.chapter===chapter&&!this.taskDone(t));}
 visible(id:string){const task=JOURNEY_TASKS.find(t=>t.id===id);return !task||this.currentTask(task.chapter)?.id===id;}
 progress(task:JourneyTask){return task.goal==='hunt'?Math.min(task.kills!,Number(this.s.receipts[`journey:hunt:${task.area}`]??0)):0;}
 ready(task:JourneyTask){if(this.currentTask(task.chapter)?.id!==task.id||this.s.area!==task.area)return false;if(task.goal==='hunt')return this.progress(task)>=task.kills!;if(task.goal==='clear'){const fixed=this.s.enemies.filter(e=>!e.respawnSeconds),battle=campaignBattle(task.area);return fixed.length>0&&fixed.every(e=>e.hp<=0)&&(!battle||!!this.s.flags[`campaign:battle:${battle.id}:complete`]);}return true;}
 complete(id:string){const task=JOURNEY_TASKS.find(t=>t.id===id);if(!task||!this.ready(task))return false;
  const key=journeyTaskKey(id);this.s.receipts[key]=true;this.s.flags[key]=true;this.host.experience(key,task.experience);
  this.s.player.gold=Math.min(9999,this.s.player.gold+task.gold);this.s.player.iron=Math.min(9999,this.s.player.iron+task.iron);
  this.host.changed();this.host.emit('quest',`${task.name}完成 · 经验 +${task.experience} · 金币 +${task.gold} · 铁 +${task.iron}`,{id});
  if(this.lifecycleRewards(task.chapter).some(r=>r.available))this.host.emit('notice',tr('life.rewardUnlocked'));return true;
 }
 hunt(){const key=`journey:hunt:${this.s.area}`,merit=`journey:hunt-count:${chapterForArea(this.s.area)}`;this.s.receipts[key]=Math.min(9999,Number(this.s.receipts[key]??0)+1);this.s.receipts[merit]=Math.min(9999,Number(this.s.receipts[merit]??0)+1);this.host.changed();}
 defeated(enemy:EnemyState){const chapter=PLAYABLE_CHAPTERS.find(c=>c.boss===enemy.bossId);if(!chapter)return;this.recordBoss(chapter.id);}
 private recordBoss(id:number){const key=journeyBossKey(id);if(this.s.receipts[key])return;this.s.receipts[key]=true;this.s.flags[`journey:chapter:${id}:complete`]=true;
  const chapter=PLAYABLE_CHAPTERS.find(c=>c.id===id)!,enemy=this.s.enemies.find(e=>e.bossId===chapter.boss),basePaid=enemy&&this.s.receipts[`boss:v3:${chapter.arena}:${enemy.id}:life`]!==undefined;
  this.s.player.gold=Math.min(9999,this.s.player.gold+(id===1?225:450)-(basePaid?(id===1?12:16):0));this.s.player.iron=Math.min(9999,this.s.player.iron+(id===1?8:12));this.host.changed();
  this.host.emit('chapter_clear',tr('life.chapterCleared',{chapter:id}),{chapter:id});
  if(PLAYABLE_CHAPTERS.every(c=>this.s.receipts[journeyBossKey(c.id)])){this.s.flags['journey:preview-complete']=true;this.host.emit('journey_complete','第一、第二章共同关底均已击败；第3—8章尚未开放，可以继续任务、狩猎与收集。');}
 }
 rewardAvailable(chapter:number,route:string){return !!PLAYABLE_CHAPTERS.find(c=>c.id===chapter)&&(!this.s.receipts['lifecycle:v3']||!!this.s.receipts[`journey:legacy-eligible:${chapter}:${route}`])&&(route==='boss'?!!this.s.receipts[journeyBossKey(chapter)]:route==='hunt'?Number(this.s.receipts[`journey:hunt-count:${chapter}`]??0)>=40:route==='task'&&!this.currentTask(chapter))&&!this.s.receipts[`journey:reward:${chapter}:${route}`];}
 claim(chapter:number,route:string,item:string){if(!this.rewardAvailable(chapter,route)||!chapterWeaponIds(chapter,route).includes(item)||this.s.inventory[item])return false;const key=`journey:reward:${chapter}:${route}`;this.s.receipts[key]=item;this.host.grant(item,key);if(chapter===1&&route==='task'&&!this.s.receipts[lifecycleTaskSource('LC1_T_E')])this.s.receipts['lifecycle:mapped:LC1_T_E']=item;this.host.changed();return true;}
 lifecycleRewards(chapter:number){return LIFECYCLE_GROUPS.filter(g=>g.chapter===chapter&&g.route==='task').map(g=>{const claimed=this.s.receipts[lifecycleTaskSource(g.id)],mapped=this.s.receipts[`lifecycle:mapped:${g.id}`],legacyPending=g.id==='LC1_T_E'&&!!this.s.receipts['journey:legacy-eligible:1:task']&&!this.s.receipts['journey:reward:1:task'];return {...g,claimed:claimed??mapped,legacyPending,available:chapter<=2&&!!g.task&&!!this.s.receipts[journeyTaskKey(g.task)]&&!claimed&&!mapped&&!legacyPending};});}
 claimLifecycle(group:string,item:string){const reward=this.lifecycleRewards(lifecycleGroup(group)?.chapter??0).find(g=>g.id===group);if(!reward?.available||!reward.items.includes(item)||this.s.inventory[item])return false;const source=lifecycleTaskSource(group);this.s.receipts[source]=item;this.host.grant(item,source);this.host.changed();return true;}
 select(route:string){if(!['task','hunt','mixed'].includes(route))return false;this.s.receipts['journey:tracking']=route;this.host.changed();return true;}
 tracking(){return this.s.receipts['journey:tracking']==='task'?'task':this.s.receipts['journey:tracking']==='hunt'?'hunt':'mixed';}
 taskHint(){const task=this.currentTask();if(task)return `${task.area} · ${task.name}${task.goal==='hunt'?` ${this.progress(task)}/${task.kills}`:''}`;const c=PLAYABLE_CHAPTERS.find(c=>c.id===chapterForArea(this.s.area))!;return this.s.receipts[journeyBossKey(c.id)]?'本章任务与关底已完成':`${c.arena} · 挑战${c.bossName}`;}
 chapters(){return JOURNEY_CHAPTERS.map(c=>({...c,complete:!!this.s.receipts[journeyBossKey(c.id)]}));}
}
/** Preserve already earned legacy claims; new hunting/boss kills unlock no fixed gear. */
export function initializeLifecycleJourney(s:GameState){
 if(s.receipts['lifecycle:v3'])return false;
 for(const c of PLAYABLE_CHAPTERS)for(const route of ['task','hunt','boss']){
  const eligible=route==='task'?JOURNEY_TASKS.filter(t=>t.chapter===c.id).every(t=>s.receipts[journeyTaskKey(t.id)]):route==='hunt'?Number(s.receipts[`journey:hunt-count:${c.id}`]??0)>=40:!!s.receipts[journeyBossKey(c.id)];
  if(eligible&&!s.receipts[`journey:reward:${c.id}:${route}`])s.receipts[`journey:legacy-eligible:${c.id}:${route}`]=true;
 }
 const old=s.receipts['journey:reward:1:task'];if(typeof old==='string')s.receipts['lifecycle:mapped:LC1_T_E']=old;
 s.receipts['lifecycle:v3']=true;return true;
}
export function validLifecycleTaskItem(s:GameState,id:string,source:string){
 const g=lifecycleGroup(source.slice('lifecycle:task:'.length));return source.startsWith('lifecycle:task:')&&!!g&&g.chapter<=2&&g.route==='task'&&g.items.includes(id)&&s.receipts[source]===id&&!!g.task&&s.receipts[journeyTaskKey(g.task)]===true;
}
export function validJourneyItem(s:GameState,id:string,source:string){const m=/^journey:reward:([12]):(task|boss|hunt)$/.exec(source);if(!m||s.receipts[source]!==id||!chapterWeaponIds(Number(m[1]),m[2]).includes(id))return false;return m[2]==='boss'?s.receipts[journeyBossKey(Number(m[1]))]===true:m[2]==='hunt'?Number(s.receipts[`journey:hunt-count:${m[1]}`]??0)>=40:JOURNEY_TASKS.filter(t=>t.chapter===Number(m[1])).every(t=>s.receipts[journeyTaskKey(t.id)]===true);}
export function validateJourneyProgress(s:GameState){
 const fail=()=>{throw new Error('无效的章节旅程记录');};
 if(s.receipts['lifecycle:v3']!==undefined&&s.receipts['lifecycle:v3']!==true)return fail();
 for(const [key,value]of Object.entries(s.receipts))if(key.startsWith('lifecycle:task:')&&(typeof value!=='string'||!validLifecycleTaskItem(s,value,key)||!s.inventory[value]||s.provenance[value]!==key))return fail();
 const mapped=s.receipts['lifecycle:mapped:LC1_T_E'];if(mapped!==undefined&&(typeof mapped!=='string'||s.receipts['journey:reward:1:task']!==mapped||!validJourneyItem(s,mapped,'journey:reward:1:task')))return fail();
 for(const c of PLAYABLE_CHAPTERS){
  let gap=false;for(const task of JOURNEY_TASKS.filter(t=>t.chapter===c.id)){const key=journeyTaskKey(task.id);if(s.receipts[key]!==undefined){if(s.receipts[key]!==true||gap||s.progression.xpReceipts[key]!==task.experience||s.flags[key]!==true)return fail();}else gap=true;}
  if(s.receipts[journeyBossKey(c.id)]!==undefined){const enemies=s.area===c.arena?s.enemies:s.encounters[c.arena]??[];if(s.receipts[journeyBossKey(c.id)]!==true||!enemies.some(e=>e.bossId===c.boss&&s.receipts[`kill:${c.arena}:${e.id}`]===true)||!s.flags[`journey:chapter:${c.id}:complete`])return fail();}
  const count=s.receipts[`journey:hunt-count:${c.id}`];if(count!==undefined){const total=Object.entries(s.receipts).filter(([key])=>key.startsWith('journey:hunt:')&&chapterForArea(key.slice(13))===c.id).reduce((n,[,v])=>n+Number(v),0);if(typeof count!=='number'||!Number.isInteger(count)||count<0||count>9999||count!==Math.min(9999,total))return fail();}
  for(const route of ['task','hunt','boss']){const key=`journey:reward:${c.id}:${route}`,item=s.receipts[key];if(item!==undefined&&(typeof item!=='string'||!s.inventory[item]||s.provenance[item]!==key||!validJourneyItem(s,item,key)))return fail();}
 }
 for(const [key,value]of Object.entries(s.receipts))if(key.startsWith('journey:hunt:')&&(typeof value!=='number'||!Number.isInteger(value)||value<0||value>9999))return fail();
}
