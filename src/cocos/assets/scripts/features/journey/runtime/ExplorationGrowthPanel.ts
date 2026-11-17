import type {GameSession} from '../../../core/GameSession';
import type {Hud} from '../../../app/Hud';
import type {MenuRow} from '../../../shared/ui/MenuPanel';
import {campaignExperienceSources,campaignExperienceView,type CampaignExperienceSource} from '../../progression/data/CampaignExperience';
import {campaignSourceMaterials} from '../../progression/common/CampaignRewards';
import {equipmentGrowthPlan} from '../../equipment/data/CampaignEquipmentGrowth';
import {forgingLevelCap,forgingNextUnlock} from '../../crafting/data/EquipmentForging';
import {gemTierForLevel,gemSocketCapForLevel} from '../../gems/data/Gems';
import {LIFECYCLE_GROUPS} from '../../equipment/data/EquipmentLifecycle';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import {chapterTaskEquipmentSource,mainBossEquipmentView} from '../../equipment/common/BossLoot';
import {AREAS,getArea} from '../../world/data/WorldData';
import {CAMPAIGN_EVENTS} from '../../campaign/data/CampaignEvents';
import {JOURNEY_CHAPTERS,JOURNEY_TASKS} from '../data/ChapterJourney';
import {pacingText as text,pacingRewardText} from '../locales/PacingText';
import {taskPanelTabs} from './TaskPanelNavigation';

const visited=(game:GameSession,area:string)=>game.state.area===area||game.state.flags['visited:'+area]===true;
const claimed=(game:GameSession,entry:CampaignExperienceSource)=>game.state.progression.xpReceipts[entry.source]!==undefined;
const chapterSources=(chapter:number)=>campaignExperienceSources(chapter).filter(entry=>entry.category==='exploration'&&!!entry.area);
const reward=(entry:CampaignExperienceSource)=>({experience:entry.amount,...campaignSourceMaterials(entry.source)});
function sumRewards(entries:CampaignExperienceSource[]){
 const result={experience:0,gold:0,iron:0,runes:0,cores:0};
 for(const entry of entries){const value=reward(entry);for(const key of ['experience','gold','iron','runes','cores'] as const)result[key]+=value[key];}
 return result;
}
export function explorationGrowthEntry(game:GameSession,chapter:number,withChapter=false):MenuRow {
 const entries=chapterSources(chapter),done=entries.filter(entry=>claimed(game,entry)).length;
 return {label:text(withChapter?'entryChapter':'entry',{chapter}),detail:text('areaProgress',{done,total:entries.length,pending:entries.length-done}),action:`journey-growth:${chapter}`};
}
/** Read-only source browser. Unvisited areas never reveal object, enemy or
 * event names. All navigation uses the existing visited-location map route. */
export function renderExplorationGrowth(hud:Hud,game:GameSession,menu:string):boolean {
 const parts=menu.split(':'),kind=parts[0];if(!['journey-growth','journey-growth-area','journey-growth-source','journey-growth-gear'].includes(kind))return false;
 const chapter=Number(parts[1]),definition=JOURNEY_CHAPTERS.find(entry=>entry.id===chapter),back={back:true,label:text('backChapter'),action:`journey-chapter:${chapter}`};
 if(!definition?.available){hud.show(text('entry'),text('unopened'),[back]);return true;}
 const entries=chapterSources(chapter),home=`journey-growth:${chapter}`,homeBack={back:true,label:text('backGrowth'),action:home},presentation={placement:'center' as const,tabs:taskPanelTabs('chapters')};
 if(kind==='journey-growth-gear'){
  const plan=equipmentGrowthPlan(chapter)!,rows:MenuRow[]=[],style=game.bossLoot.view().style;
  const level=game.state.progression.level,next=forgingNextUnlock(level);
  rows.push({label:text('cultivationLevel',{level}),detail:text('cultivationCaps',{rank:forgingLevelCap(level),tier:gemTierForLevel(level),holes:gemSocketCapForLevel(level)})+'\n'+(next?text('cultivationNext',next):text('cultivationMax')),action:menu,disabled:true});
  for(const group of LIFECYCLE_GROUPS.filter(group=>group.chapter===chapter&&group.rewardStage==='midChapter')){
   const source=chapterTaskEquipmentSource(group.rewardTask!,group.id),item=game.state.receipts[source],preview=typeof item==='string'?item:group.items.find(id=>id.endsWith('_'+style))??group.items[0],task=JOURNEY_TASKS.find(task=>task.id===group.rewardTask)!;
   rows.push({label:text('gearMid')+' · '+EQUIPMENT[preview].name,detail:(typeof item==='string'?text('gearOwned',{item:EQUIPMENT[item]?.name??item}):text('gearAwaitTask'))+'\n'+text('gearTask',{task:task.name}),action:`journey-task:${task.id}`});
  }
  const fixed=mainBossEquipmentView(game.state,chapter);
  rows.push({label:text('gearBoss'),detail:fixed.rewards.map(entry=>EQUIPMENT[entry.item].name).join(' · ')+'\n'+text(fixed.awarded?'claimed':'gearAwaitBoss'),action:`journey-main-boss-rewards:${chapter}`});
  hud.showList(text('gear'),text('gearTarget',{weapon:plan.target.mainWeaponRank,other:plan.target.otherSlotRank,cap:plan.target.cap})+'\n'+text('gearHint'),rows,[homeBack],hud.touchTargetSize,presentation);return true;
 }
 if(kind==='journey-growth-source'){
  let source='';try{source=decodeURIComponent(parts[2]??'');}catch{/* Invalid links show the ordinary chapter list. */}
  const entry=entries.find(entry=>entry.source===source);
  if(!entry?.area||!visited(game,entry.area)){hud.show(text('entry'),text('empty'),[homeBack]);return true;}
  const object=entry.objectId?AREAS[entry.area]?.objects.find(object=>object.id===entry.objectId):undefined,event=entry.eventId?CAMPAIGN_EVENTS[entry.eventId]:undefined;
  const body=[text('location',{area:getArea(entry.area).name}),text(claimed(game,entry)?'claimed':'pending'),event?.description??object?.description??'',text('sourceReward',{reward:pacingRewardText(reward(entry))}),text('sourceHint'),text('permanent')].filter(Boolean).join('\n\n');
  hud.show(entry.label,body,[{label:text('map'),action:`journey-map:${entry.area}`},{back:true,label:text('backArea'),action:`journey-growth-area:${chapter}:${entry.area}`}],false,presentation);return true;
 }
 if(kind==='journey-growth-area'){
  const area=parts[2];if(!area||!visited(game,area)||!entries.some(entry=>entry.area===area)){hud.show(text('entry'),text('empty'),[homeBack]);return true;}
  const local=entries.filter(entry=>entry.area===area),done=local.filter(entry=>claimed(game,entry)).length;
  const rows=local.slice().sort((a,b)=>Number(claimed(game,a))-Number(claimed(game,b))||a.label.localeCompare(b.label)).map(entry=>({label:text(claimed(game,entry)?'claimed':'pending')+' · '+entry.label,detail:pacingRewardText(reward(entry)),action:`journey-growth-source:${chapter}:${encodeURIComponent(entry.source)}`}));
  hud.showList(getArea(area).name,text('areaProgress',{done,total:local.length,pending:local.length-done})+'\n'+text('permanent'),rows,[{label:text('map'),action:`journey-map:${area}`},homeBack],hud.touchTargetSize,presentation);return true;
 }
 const view=campaignExperienceView(chapter,game.state.progression.xpReceipts)!,done=entries.filter(entry=>claimed(game,entry)).length,rows:MenuRow[]=[{label:text('gear'),detail:text('entryHint'),action:`journey-growth-gear:${chapter}`}];
 const areas=Array.from(new Set(entries.map(entry=>entry.area!))),known=areas.filter(area=>visited(game,area));
 for(const area of known){const local=entries.filter(entry=>entry.area===area),pending=local.filter(entry=>!claimed(game,entry));rows.push({label:getArea(area).name,detail:text('areaProgress',{done:local.length-pending.length,total:local.length,pending:pending.length})+'\n'+text('remaining',{reward:pacingRewardText(sumRewards(pending))}),action:`journey-growth-area:${chapter}:${area}`});}
 if(areas.length>known.length)rows.push({label:text('unknown'),detail:text('unknownDetail',{count:areas.length-known.length}),action:home,disabled:true});
 const summary=text('progress',{done,total:entries.length,earned:view.exploration.earnedXp,available:view.exploration.availableXp})+'\n'+text('permanent')+'\n'+text('pace');
 hud.showList(text('title',{chapter}),summary,rows,[back],hud.touchTargetSize,presentation);return true;
}
