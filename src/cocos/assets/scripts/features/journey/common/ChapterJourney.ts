import {claimEconomyGold,economyReward} from '../../economy/common/EconomyRewards';
import {nextCampaignStage,campaignStageDone,CAMPAIGN_STAGES} from '../data/CampaignStages';
import {equipmentGrowthPlan} from '../../equipment/data/CampaignEquipmentGrowth';
import {journeyText as tr} from '../locales';
import type {GameState,EnemyState} from '../../../core/GameSession';
import {JOURNEY_CHAPTERS,PLAYABLE_CHAPTERS,JOURNEY_TASKS,journeyTaskKey,journeyBossKey,chapterForArea,type JourneyTask} from '../data/ChapterJourney';
import {campaignBattle} from '../../cinematics/data/CampaignScenes';
import {LIFECYCLE_GROUPS} from '../../equipment/data/EquipmentLifecycle';
import {mainBossEquipmentSource,chapterTaskEquipment,chapterTaskEquipmentSource} from '../../equipment/common/BossLoot';
import {chapterTwoEncounterResolved} from '../../campaign/common/ChapterTwoEncounters';
import {levelForXp} from '../../progression/common/Progression';
import {campaignExperienceQuote} from '../../progression/data/CampaignExperience';
import {campaignSourceMaterials} from '../../progression/common/CampaignRewards';

interface Host {state():GameState;experience(source:string,amount:number):void;grant(id:string,source:string):void;changed():void;emit(type:string,text:string,extra?:Record<string,unknown>):void}
export class ChapterJourney {
 constructor(private host:Host){}
 private get s(){return this.host.state();}
 taskDone(task:JourneyTask){return !!this.s.receipts[journeyTaskKey(task.id)];}
 currentTask(chapter=chapterForArea(this.s.area)){return JOURNEY_TASKS.find(t=>t.chapter===chapter&&!this.taskDone(t));}
 visible(id:string){const task=JOURNEY_TASKS.find(t=>t.id===id);return !task||this.currentTask(task.chapter)?.id===id;}
 progress(task:JourneyTask){return task.goal==='hunt'?Math.min(task.kills!,Number(this.s.receipts[`journey:hunt:${task.area}`]??0)):0;}
 ready(task:JourneyTask){if(this.currentTask(task.chapter)?.id!==task.id||this.s.area!==task.area)return false;if(task.goal==='encounter')return chapterTwoEncounterResolved(this.s,task.encounterId??task.id);if(task.goal==='hunt')return this.progress(task)>=task.kills!;if(task.goal==='clear'){const fixed=this.s.enemies.filter(e=>!e.respawnSeconds&&!e.id.startsWith('early-')),battle=campaignBattle(task.area);return fixed.length>0&&fixed.every(e=>e.hp<=0)&&(!battle||!!this.s.flags[`campaign:battle:${battle.id}:complete`]);}return true;}
 taskMaterialReward(task:JourneyTask){const reward=campaignSourceMaterials(journeyTaskKey(task.id));return reward.registered?reward:{gold:task.gold,iron:task.iron,runes:0,cores:0,registered:false};}
 rewardView(task:JourneyTask){const done=this.taskDone(task),experience=campaignExperienceQuote(journeyTaskKey(task.id),task.experience).amount;return {experience,level:this.s.progression.level,afterLevel:levelForXp(this.s.progression.totalXp+(done?0:experience)),oneTime:true,done,...this.taskMaterialReward(task)};}
 complete(id:string){const task=JOURNEY_TASKS.find(t=>t.id===id);if(!task||!this.ready(task))return false;
  const key=journeyTaskKey(id);this.s.receipts[key]=true;this.s.flags[key]=true;this.host.experience(key,task.experience);
  for(const reward of chapterTaskEquipment(task.id,this.s.combat.family??'WAR')){const source=chapterTaskEquipmentSource(task.id,reward.group);if(this.s.receipts[source]!==undefined)continue;this.s.receipts[source]=reward.item;this.s.receipts[source+':meta']=JSON.stringify([1,this.s.combat.family??'WAR']);this.host.grant(reward.item,source);}
  const reward=this.rewardView(task);
  claimEconomyGold(this.s,key);
  for(const field of ['iron','runes','cores'] as const)this.s.player[field]=Math.min(9999,this.s.player[field]+reward[field]);
  this.host.changed();this.host.emit('quest',`${task.name}完成 · 经验 +${reward.experience} · 金币 +${reward.gold} · 铁 +${reward.iron}${reward.runes?` · 符文 +${reward.runes}`:''}${reward.cores?` · 核心 +${reward.cores}`:''}`,{id});
  return true;
 }
 hunt(){const key=`journey:hunt:${this.s.area}`,merit=`journey:hunt-count:${chapterForArea(this.s.area)}`;this.s.receipts[key]=Math.min(9999,Number(this.s.receipts[key]??0)+1);this.s.receipts[merit]=Math.min(9999,Number(this.s.receipts[merit]??0)+1);this.host.changed();}
 defeated(enemy:EnemyState){const chapter=PLAYABLE_CHAPTERS.find(c=>c.boss===enemy.bossId);if(!chapter)return;this.recordBoss(chapter.id);}
 private recordBoss(id:number){const key=journeyBossKey(id);if(this.s.receipts[key])return;this.s.receipts[key]=true;this.s.flags[`journey:chapter:${id}:complete`]=true;
  const materials=equipmentGrowthPlan(id)!.sources.firstBoss;
  claimEconomyGold(this.s,key);
  for(const kind of ['iron','runes','cores'] as const)this.s.player[kind]=Math.min(9999,this.s.player[kind]+materials[kind]);this.host.changed();
  this.host.emit('chapter_clear',tr('life.chapterCleared',{chapter:id}),{chapter:id});
  if(PLAYABLE_CHAPTERS.every(c=>this.s.receipts[journeyBossKey(c.id)])){this.s.flags['journey:preview-complete']=true;this.host.emit('journey_complete','第一、第二章共同关底均已击败；第3—8章尚未开放，可以继续任务、狩猎与收集。');}
 }
 rewardAvailable(chapter:number,route:string){return false;}
 claim(chapter:number,route:string,item:string){return false;}
 lifecycleRewards(chapter:number){return LIFECYCLE_GROUPS.filter(g=>g.chapter===chapter&&g.route==='task').map(g=>{const claimed=this.s.receipts[mainBossEquipmentSource(chapter,g.id)];return {...g,claimed,awarded:typeof claimed==='string',auto:true,legacyPending:false,available:false};});}
 claimLifecycle(group:string,item:string){return false;}
 select(route:string){if(!['task','hunt','mixed'].includes(route))return false;this.s.receipts['journey:tracking']=route;this.host.changed();return true;}
 tracking(){return this.s.receipts['journey:tracking']==='task'?'task':this.s.receipts['journey:tracking']==='hunt'?'hunt':'mixed';}
 taskHint(){const stage=nextCampaignStage(this.s);if(stage&&(stage.chapter===1||this.s.progression.secondChapter))return `${stage.area} · ${stage.name}`;const task=this.currentTask();if(task)return `${task.area} · ${task.name}${task.goal==='hunt'?` ${this.progress(task)}/${task.kills}`:''}`;const c=PLAYABLE_CHAPTERS.find(c=>c.id===chapterForArea(this.s.area))!;return this.s.receipts[journeyBossKey(c.id)]?'本章任务与关底已完成':`${c.arena} · 挑战${c.bossName}`;}
 chapters(){return JOURNEY_CHAPTERS.map(c=>({...c,complete:!!this.s.receipts[journeyBossKey(c.id)]&&CAMPAIGN_STAGES.filter(stage=>stage.chapter===c.id).every(stage=>campaignStageDone(this.s,stage))}));}
}
export function validateJourneyProgress(s:GameState){
 const fail=()=>{throw new Error('无效的章节旅程记录');};
 if(s.receipts['lifecycle:v3']!==undefined&&s.receipts['lifecycle:v3']!==true)return fail();
 for(const key of Object.keys(s.receipts))if(key.startsWith('lifecycle:task:')||key.startsWith('lifecycle:mapped:')||key.startsWith('journey:legacy-eligible:')||key.startsWith('journey:reward:'))return fail();
 for(const c of PLAYABLE_CHAPTERS){
  let gap=false;for(const task of JOURNEY_TASKS.filter(t=>t.chapter===c.id)){
   const key=journeyTaskKey(task.id),earned=s.progression.xpReceipts[key],earnedValid=earned===campaignExperienceQuote(key,task.experience).amount;
   if(earned!==undefined&&s.receipts[key]!==true)return fail();
   if(s.receipts[key]!==undefined){if(s.receipts[key]!==true||gap||!earnedValid||s.flags[key]!==true||task.goal==='encounter'&&!chapterTwoEncounterResolved(s,task.encounterId??task.id))return fail();}else gap=true;
  }
  if(s.receipts[journeyBossKey(c.id)]!==undefined){const enemies=s.area===c.arena?s.enemies:s.encounters[c.arena]??[];if(s.receipts[journeyBossKey(c.id)]!==true||!enemies.some(e=>e.bossId===c.boss&&s.receipts[`kill:${c.arena}:${e.id}`]===true)||!s.flags[`journey:chapter:${c.id}:complete`])return fail();}
  const count=s.receipts[`journey:hunt-count:${c.id}`];if(count!==undefined){const total=Object.entries(s.receipts).filter(([key])=>key.startsWith('journey:hunt:')&&chapterForArea(key.slice(13))===c.id).reduce((n,[,v])=>n+Number(v),0);if(typeof count!=='number'||!Number.isInteger(count)||count<0||count>9999||count!==Math.min(9999,total))return fail();}
 }
 for(const key of Object.keys(s.progression.xpReceipts))if(key.startsWith('balance:journey-experience:'))return fail();
 for(const [key,value]of Object.entries(s.receipts))if(key.startsWith('journey:hunt:')&&(typeof value!=='number'||!Number.isInteger(value)||value<0||value>9999))return fail();
}
