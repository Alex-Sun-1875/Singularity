import type {AreaDef,Point} from '../../../core/Contracts';
import type {GameSession} from '../../../core/GameSession';
import {AREAS} from '../../world/data/WorldData';
import {JOURNEY_CHAPTERS,JOURNEY_TASKS,chapterForArea,journeyBossKey,journeyChapterDisplay,playableArea,type JourneyTask} from '../data/ChapterJourney';
import {FIELD_QUESTS,FIELD_QUEST_EVENTS} from '../../campaign/data/FieldQuests';
import {CHAPTER_TWO_SIDE_QUESTS,CHAPTER_TWO_SIDE_QUEST_EVENTS,chapterTwoSideQuestOutcome,chapterTwoSideQuestResponse} from '../../campaign/data/ChapterTwoSideQuests';
import {CAMPAIGN_EVENTS,type CampaignEventDef} from '../../campaign/data/CampaignEvents';
import {chapterTwoEncounterView,type ChapterTwoEncounterView} from '../../campaign/common/ChapterTwoEncounters';
import {campaignPrerequisiteTargets} from '../../campaign/common/CampaignNavigation';
import {availableRoutes} from '../../automation/common/AutomationRoute';
import {authoredWaypoint,waypointUnlocked} from '../../navigation/common/FastTravel';
import {CAMPAIGN_SCENES} from '../../cinematics/data/CampaignScenes';
import {cinematicText} from '../../cinematics/locales';
import {adventureJournalText as text} from '../locales/AdventureJournalText';

export type JournalEntryKind='chapter'|'main'|'side'|'area'|'replay';
export type JournalStatus='active'|'available'|'completed'|'locked'|'upcoming';
export interface JournalSection {id:string;title:string;text:string}
export interface JournalUpdate {id:string;title:string;text:string;status:'completed'|'current'|'locked';choice?:string;targetIds:string[]}
export interface JournalAction {id:string;label:string;action:string;disabled?:boolean;reason?:string;primary?:boolean}
export interface JournalTarget {id:string;entryId:string;area:string;point?:Point;label:string;objectId?:string;eventId?:string;kind:JournalEntryKind;status:JournalStatus;known:boolean;current?:boolean}
export interface JournalEntry {
 id:string;kind:JournalEntryKind;chapter:number;title:string;status:JournalStatus;statusText:string;summary:string;
 sections:JournalSection[];updates:JournalUpdate[];targets:JournalTarget[];actions:JournalAction[];
 parentId?:string;waypoint?:boolean;
}
type Context={game:GameSession;known:Set<string>;routes:ReturnType<typeof availableRoutes>};
const SIDE_QUESTS=[...FIELD_QUESTS,...CHAPTER_TWO_SIDE_QUESTS];
const SIDE_EVENTS=[...FIELD_QUEST_EVENTS,...CHAPTER_TWO_SIDE_QUEST_EVENTS];
const section=(id:string,key:Parameters<typeof text>[0],body:string):JournalSection=>({id,title:text(key),text:body});
const statusText=(status:JournalStatus)=>text(`status.${status}`);
const point=(value:Point):Point=>({x:value.x,z:value.z});
const liveChapter=(id:number)=>JOURNEY_CHAPTERS.some(chapter=>chapter.id===id&&chapter.available);
const chapterUnlocked=(game:GameSession,id:number)=>liveChapter(id)&&(id===1||id===2&&game.state.progression.secondChapter);
const areaKnown=(context:Context,id:string)=>context.known.has(id);
function context(game:GameSession):Context {
 const known=new Set<string>([game.state.area]);
 for(const [flag,value]of Object.entries(game.state.flags))if(value&&flag.startsWith('visited:'))known.add(flag.slice(8));
 for(const id of Array.from(known))if(/^S\d\d-/.test(id))known.add(id.slice(0,3));
 return {game,known,routes:availableRoutes(game,AREAS)};
}
function entry(id:string,kind:JournalEntryKind,chapter:number,title:string,status:JournalStatus,summary:string):JournalEntry {
 return {id,kind,chapter,title,status,statusText:statusText(status),summary,sections:[],updates:[],targets:[],actions:[],...(kind!=='chapter'?{parentId:`chapter:${chapter}`}:{})};
}
function target(context:Context,owner:JournalEntry,id:string,area:string,label:string,at?:Point,extra:Pick<JournalTarget,'objectId'|'eventId'>={}):JournalTarget|null {
 if(!AREAS[area]||!playableArea(area)||!liveChapter(chapterForArea(area)))return null;
 const known=areaKnown(context,area);
 return {id,entryId:owner.id,area,label,kind:owner.kind,status:owner.status,known,...(known&&at?{point:point(at)}:{}),...extra};
}
function eventTarget(context:Context,owner:JournalEntry,event:CampaignEventDef,suffix=event.id):JournalTarget|null {
 const area=AREAS[event.area],object=area?.objects.find(object=>object.action==='campaign_event'&&object.eventId===event.id);
 return target(context,owner,`${owner.id}:${suffix}`,event.area,event.label,object??event.at??area?.spawn,{objectId:object?.id,eventId:event.id});
}
function addTarget(owner:JournalEntry,value:JournalTarget|null):void {if(value&&!owner.targets.some(item=>item.id===value.id))owner.targets.push(value);}
function mapAction(owner:JournalEntry):void {if(owner.targets.length)owner.actions.push({id:`${owner.id}:map`,label:text('action.map'),action:'journal:mode:map'});}
function addPrerequisites(context:Context,owner:JournalEntry,eventId:string):void {
 for(const prerequisite of campaignPrerequisiteTargets(context.game,AREAS,eventId)){
  const destination=prerequisite.destination,id=`${owner.id}:prerequisite:${eventId}:${prerequisite.id}`;
  addTarget(owner,target(context,owner,id,destination.area,destination.label,destination.point,{objectId:destination.objectId}));
  if(!owner.actions.some(action=>action.id===id))owner.actions.push({id,label:text('action.prerequisite',{name:destination.label}),action:`campaign-prerequisite-go:${eventId}:${prerequisite.id}`,disabled:prerequisite.blocked,reason:prerequisite.blocked?text('gate.route'):'',primary:!prerequisite.blocked});
 }
}
function taskGoal(context:Context,task:JourneyTask):string {
 return task.goal==='hunt'?text('goal.hunt',{done:context.game.journey.progress(task),total:task.kills??0}):text(`goal.${task.goal}`);
}
/** Encounter route availability also closes unused alternatives. Only physical
 * receipts identify actions that actually happened, so closed != completed. */
function routeRecorded(context:Context,view:ChapterTwoEncounterView,id:string):boolean {
 const r=context.game.state.receipts,prefix=`chapter2:${view.id}:`;
 if(id==='quarry-survey')return r[prefix+'survey']===true;
 if(id==='quarry-witness'||id==='quarry-ledger')return r[prefix+'choice']===id.slice(7);
 if(id==='ridge-parley')return view.method==='parley';
 if(id==='ridge-alarm')return r[prefix+'alarm']===true;
 if(id==='ridge-battle'||id==='oath-battle')return view.method==='battle';
 if(id==='oath-read')return r[prefix+'read']===true;
 const ordinal=['oath-north','oath-west','oath-east'].indexOf(id);
 return ordinal>=0&&Number(r[prefix+'progress']??0)>ordinal;
}
function mainEntry(context:Context,task:JourneyTask):JournalEntry {
 const game=context.game,done=game.journey.taskDone(task),current=game.journey.currentTask(task.chapter)?.id===task.id,unlocked=chapterUnlocked(game,task.chapter);
 const status:JournalStatus=done?'completed':!unlocked||!current?'locked':'active';
 const result=entry(`main:${task.id}`,'main',task.chapter,task.name,status,task.story),area=AREAS[task.area];
 const object=area?.objects.find(object=>object.action==='journey_task'&&object.eventId===task.id),view=chapterTwoEncounterView(game.state,task.encounterId??task.id);
 const base=target(context,result,result.id+':site',task.area,task.name,object??area?.spawn,{objectId:object?.id});
 result.sections.push(section('current','section.current',done?text('reward.received'):!unlocked?text('gate.chapter'):!current?text('gate.previous'):taskGoal(context,task)));
 result.sections.push(section('reward','section.reward',text('reward.task',{experience:task.experience,gold:task.gold,iron:task.iron})+'\n'+text(done?'reward.received':'reward.once')));
 if(current&&!done&&unlocked)result.actions.push({id:result.id+':go',label:text('action.go'),action:`journey-go:${task.id}`,disabled:!context.routes.has(task.area),reason:context.routes.has(task.area)?'':text('gate.route'),primary:true});
 if(view){
  const known=view.clues.filter(clue=>clue.known);
  result.sections.push(section('clues','section.clues',known.length?known.map(clue=>clue.label).join('\n'):text('record.cluesNone')));
  result.sections.push(section('outcome','section.outcome',view.outcome));
  // Map points do not encode the correct mechanism order or select a branch.
  for(const route of view.routes.slice().sort((a,b)=>a.label.localeCompare(b.label))){
   const recorded=routeRecorded(context,view,route.id),event=CAMPAIGN_EVENTS[route.eventId];
   if(view.resolved&&!recorded)continue;
   const routeTarget=event&&(recorded||current&&unlocked&&route.available)?eventTarget(context,result,event):null;
   if(routeTarget){routeTarget.status=recorded?'completed':'active';routeTarget.current=!recorded&&current&&unlocked;}
   addTarget(result,routeTarget);
   result.updates.push({id:route.id,title:route.label,text:recorded?view.outcome:view.resolved?text('record.unused'):route.reason,status:recorded?'completed':current&&unlocked&&route.available?'current':'locked',targetIds:routeTarget?[routeTarget.id]:[]});
   if(!current||done||!unlocked||view.resolved||!event)continue;
   if(route.available)result.actions.push({id:result.id+':route:'+route.id,label:text('action.route',{name:route.label}),action:`journey-field-go:${route.eventId}`,disabled:!context.routes.has(route.area),reason:context.routes.has(route.area)?'':text('gate.route')});
   else if(!route.completed)addPrerequisites(context,result,route.eventId);
  }
 }
 if(!result.targets.length||view?.resolved&&current&&!done)addTarget(result,base);
 if(base&&current&&unlocked&&!done&&result.targets.includes(base))base.current=true;
 result.targets.sort((a,b)=>Number(!!b.current)-Number(!!a.current));
 if(!view)result.updates.push({id:task.id,title:task.name,text:done?task.story:current?taskGoal(context,task):text('record.later'),status:done?'completed':current&&unlocked?'current':'locked',targetIds:base?[base.id]:[]});
 mapAction(result);return result;
}
function sideEntry(context:Context,quest:typeof SIDE_QUESTS[number]):JournalEntry|null {
 const game=context.game,s=game.state;if('hidden'in quest&&!s.flags[quest.hidden])return null;
 const definitions=quest.steps.map(id=>SIDE_EVENTS.find(event=>event.id===id)).filter((event):event is CampaignEventDef=>!!event),next=definitions.find(event=>s.receipts['campaign:'+event.id]!==true),started=definitions.some(event=>s.receipts['campaign:'+event.id]===true),done=!next,unlocked=chapterUnlocked(game,quest.chapter);
 const status:JournalStatus=done?'completed':!unlocked?'locked':started?'active':'available';
 const result=entry(`side:${quest.id}`,'side',quest.chapter,quest.name,status,definitions[0]?.description??'');
 result.sections.push(section('current','section.current',done?text('reward.received'):!unlocked?text('gate.chapter'):next?next.label:text('record.pending')));
 result.sections.push(section('reward','section.reward',quest.reward));
 const response=chapterTwoSideQuestResponse(s,quest.id),outcome=chapterTwoSideQuestOutcome(s,quest.id);
 if(response)result.sections.push(section('response','section.response',response));
 if(outcome)result.sections.push(section('outcome','section.outcome',outcome));
 for(const event of definitions){
  const completed=s.receipts['campaign:'+event.id]===true,current=event.id===next?.id,availability=game.campaignEventAvailability(event.id,true),choice=completed?event.choices?.find(choice=>choice.id===s.receipts['campaign:choice:'+event.id]):undefined;
  const site=(completed||current&&unlocked)?eventTarget(context,result,event):null;
  if(site){site.status=completed?'completed':'active';site.current=current&&unlocked;}
  addTarget(result,site);
  result.updates.push({id:event.id,title:event.label,text:completed?choice?.text??availability.reason:current?(!unlocked?text('gate.chapter'):availability.reason):text('record.later'),status:completed?'completed':current&&unlocked?'current':'locked',...(choice&&(event.choices?.length??0)>1?{choice:text('record.choice',{choice:choice.label})}:{}),targetIds:site?[site.id]:[]});
  if(!current||done||!unlocked)continue;
  if(availability.available)result.actions.push({id:result.id+':go',label:text('action.go'),action:`journey-field-go:${event.id}`,disabled:!context.routes.has(event.area),reason:context.routes.has(event.area)?'':text('gate.route'),primary:true});
  else addPrerequisites(context,result,event.id);
 }
 result.targets.sort((a,b)=>Number(!!b.current)-Number(!!a.current));
 mapAction(result);
 return result;
}
function chapterEntry(context:Context,chapter:typeof JOURNEY_CHAPTERS[number],children:JournalEntry[]):JournalEntry {
 const display=journeyChapterDisplay(chapter),unlocked=chapterUnlocked(context.game,chapter.id),won=!!context.game.state.receipts[journeyBossKey(chapter.id)],tasks=JOURNEY_TASKS.filter(task=>task.chapter===chapter.id),done=tasks.filter(task=>context.game.journey.taskDone(task)).length,status:JournalStatus=!chapter.available?'upcoming':won&&done===tasks.length?'completed':unlocked?'active':'locked';
 const result=entry(`chapter:${chapter.id}`,'chapter',chapter.id,display.title,status,display.story);
 if(!chapter.available)return result;
 const current=children.find(child=>child.chapter===chapter.id&&child.kind==='main'&&child.status==='active');
 result.sections.push(section('progress','section.progress',text('progress.chapter',{done,total:tasks.length,boss:text(won?'boss.complete':'boss.pending')})+'\n'+text('boss.rule')));
 result.sections.push(section('current','section.current',!unlocked?text('gate.chapter'):current?.title??(!won?text('boss.goal',{boss:chapter.bossName}):text('empty.current'))));
 result.sections.push(section('reward','section.reward',text('boss.reward')));
 for(const task of tasks){const child=children.find(child=>child.id===`main:${task.id}`)!;result.updates.push({id:child.id,title:child.title,text:child.statusText,status:child.status==='completed'?'completed':child.status==='active'?'current':'locked',targetIds:child.targets.map(target=>target.id)});}
 const bossAt=AREAS[chapter.arena]?.enemies.find(enemy=>enemy.bossId===chapter.boss),bossTarget=target(context,result,result.id+':boss',chapter.arena,chapter.bossName,bossAt??AREAS[chapter.arena]?.spawn);
 result.updates.push({id:result.id+':boss',title:text('boss.goal',{boss:chapter.bossName}),text:text(won?'boss.complete':'boss.pending'),status:won?'completed':unlocked?'current':'locked',targetIds:bossTarget?[bossTarget.id]:[]});
 const relevant=children.filter(child=>child.chapter===chapter.id&&(child.kind==='main'||child.kind==='side'));
 relevant.sort((a,b)=>Number(b.status==='active')-Number(a.status==='active'));
 for(const child of relevant)for(const site of child.targets)addTarget(result,site);
 addTarget(result,bossTarget);
 if(current)result.actions.push(...current.actions.filter(action=>action.primary));
 result.actions.push({id:result.id+':main-rewards',label:text('action.mainRewards'),action:`journey-main-boss-rewards:${chapter.id}`},{id:result.id+':loot-sources',label:text('action.lootSources'),action:`journey-loot:${chapter.id}`});
 mapAction(result);return result;
}
function areaEntry(context:Context,area:AreaDef,stories:JournalEntry[]):JournalEntry {
 const current=context.game.state.area===area.id,result=entry(`area:${area.id}`,'area',chapterForArea(area.id),area.name,current?'active':'available',area.subtitle),waypoint=authoredWaypoint(area),unlocked=waypointUnlocked(context.game.state.flags,area);
 result.waypoint=unlocked;addTarget(result,target(context,result,result.id+':site',area.id,area.name,waypoint?.point??area.spawn));
 result.sections.push(section('location','section.location',text(current?'location.current':'location.visited')));
 const related=stories.filter(story=>(story.kind==='main'||story.kind==='side')&&story.targets.some(target=>target.area===area.id));
 if(related.length)result.sections.push(section('related','section.related',related.map(story=>`${story.title} · ${story.statusText}`).join('\n')));
 if(waypoint){
  const availability=context.game.fastTravelAvailability(area);result.sections.push(section('waypoint','section.waypoint',text(unlocked?'waypoint.unlocked':'waypoint.locked')+(unlocked?'\n'+availability.reason:'')));
  if(unlocked)result.actions.push({id:result.id+':travel',label:text('action.travel',{name:area.name}),action:'map-travel:'+area.id,disabled:!availability.available,reason:availability.reason,primary:true});
 }
 mapAction(result);return result;
}
/** Read-only presentation snapshots. No selection, navigation, rewards or
 * progress writes live here; explicit action strings use existing controllers. */
export function journalEntries(game:GameSession):JournalEntry[] {
 const c=context(game),stories:JournalEntry[]=JOURNEY_TASKS.filter(task=>liveChapter(task.chapter)).map(task=>mainEntry(c,task));
 for(const quest of SIDE_QUESTS){if(!liveChapter(quest.chapter))continue;const item=sideEntry(c,quest);if(item)stories.push(item);}
 for(const scene of CAMPAIGN_SCENES){
  if(!liveChapter(scene.chapter)||game.state.receipts[`campaign:seen:${scene.id}`]!==true)continue;
  const item=entry(`replay:${scene.id}`,'replay',scene.chapter,cinematicText(scene.title,{},'zh-CN'),'completed',AREAS[scene.area]?.name??'');
  const lines=scene.beats.map(beat=>`${cinematicText(beat.speaker,{},'zh-CN')}：${cinematicText(beat.text,{},'zh-CN')}`);
  item.sections.push(section('replay','section.replay',lines.join('\n\n')));
  addTarget(item,target(c,item,item.id+':site',scene.area,AREAS[scene.area]?.name??item.title,scene.at??AREAS[scene.area]?.spawn));stories.push(item);
 }
 const chapters=JOURNEY_CHAPTERS.map(chapter=>chapterEntry(c,chapter,stories));
 const areas=Object.values(AREAS).filter(area=>playableArea(area.id)&&liveChapter(chapterForArea(area.id))&&areaKnown(c,area.id)&&!/^T[1-6]$/.test(area.id)).map(area=>areaEntry(c,area,stories));
 return [...chapters,...stories,...areas];
}
function areaPreview(game:GameSession,id:string,entries:JournalEntry[]):JournalEntry|null {
 const area=AREAS[id];if(!area||!playableArea(id)||!liveChapter(chapterForArea(id)))return null;
 const known=entries.find(entry=>entry.id===`area:${id}`);if(known)return known;
 // Compatibility focus for a deliberately requested destination, not a new
 // discovery: no subtitle, POIs, exact coordinate or travel capability leaks.
 const preview=entry(`area:${id}`,'area',chapterForArea(id),area.name,'available',text('location.unexplored'));
 preview.waypoint=false;preview.sections.push(section('location','section.location',text('location.unexplored')));
 preview.targets.push({id:preview.id+':site',entryId:preview.id,area:id,label:area.name,kind:'area',status:'available',known:false});
 return preview;
}
/** Explicit legacy map focus may name an unexplored but released area. These
 * previews never join the ordinary directory and never unlock a waypoint. */
export function journalAreaPreview(game:GameSession,id:string):JournalEntry|null {return areaPreview(game,id,journalEntries(game));}
export function journalEntry(game:GameSession,id:string):JournalEntry|null {
 const entries=journalEntries(game);return entries.find(entry=>entry.id===id)??(id.startsWith('area:')?areaPreview(game,id.slice(5),entries):null);
}
export function defaultJournalEntry(game:GameSession):string {
 const chapter=chapterForArea(game.state.area),current=chapterUnlocked(game,chapter)?game.journey.currentTask(chapter):undefined;
 return current?`main:${current.id}`:`chapter:${chapter}`;
}
/** Selected chapter markers retain the child entry ID for map -> log linking.
 * Global markers show current stories, never hidden discoveries or future maps. */
export function journalMarkers(game:GameSession,entryId?:string,area?:string):JournalTarget[] {
 const entries=journalEntries(game),selected=entryId?(entries.find(entry=>entry.id===entryId)??(entryId.startsWith('area:')?areaPreview(game,entryId.slice(5),entries):null)):undefined;
 if(entryId&&!selected)return [];
 const sites=selected?selected.targets:entries.filter(entry=>(entry.kind==='main'||entry.kind==='side')&&(entry.status==='active'||entry.status==='available')).flatMap(entry=>entry.targets);
 return Array.from(new Map(sites.filter(target=>!area||target.area===area).map(target=>[target.id,target])).values());
}
