import type {AreaDef} from '../../../core/Contracts';
import type {GameSession} from '../../../core/GameSession';
import type {NavigationTarget} from '../../automation/common/Automation';
import {availableRoutes} from '../../automation/common/AutomationRoute';
import {CAMPAIGN_EVENTS,type CampaignEventDef} from '../data/CampaignEvents';
import {CAMPAIGN_ENEMY_TEMPLATES} from '../data/Campaign';
import {campaignText} from '../locales';

export interface CampaignPrerequisiteTarget {id:string;destination:NavigationTarget;blocked:boolean}

/** Resolve saved prerequisite flags to authored interactions, without changing quest progress. */
export function campaignPrerequisiteTargets(game:GameSession,areas:Record<string,AreaDef>,id:string):CampaignPrerequisiteTarget[] {
 const status=game.campaignEventAvailability(id,true),event=CAMPAIGN_EVENTS[id];
 if(!event||status.available||status.completed)return [];
 const flags=game.state.flags,targets=new Map<string,NavigationTarget>();
 const objects=Object.values(areas).flatMap(area=>area.objects.map(object=>({area,object})));
 const missing=(d:CampaignEventDef)=>[...(d.requires??[]).filter(flag=>!flags[flag]),...(d.requiresAny?.some(flag=>flags[flag])?[]:d.requiresAny??[])];
 const add=(key:string,target:NavigationTarget)=>{targets.set(key,target);};
 const resolve=(flag:string,seen:Set<string>)=>{
  if(flags[flag]||seen.has(flag))return;
  const next=new Set(seen);next.add(flag);
  // These outcomes are committed by the existing exit and tower rules.
  if(flag==='final_ready'){for(const key of ['m7_prepared','west_tower_down','east_tower_down'])resolve(key,next);return;}
  if(flag==='workers_returned'){
   if(!flags.workers_released){resolve('workers_released',next);return;}
   const area=areas['U1-05'],exit=area?.exits.find(e=>!game.exitRequirement(e));
   if(exit)add(exit.id,{area:area.id,point:exit,label:exit.label,exitId:exit.id});
   return;
  }
  if(flag==='gate_raised'&&!flags.captain_defeated){resolve('captain_defeated',next);return;}
  if(flag==='workers_released'&&!flags.meeting){resolve('meeting',next);return;}
  const legacy:Record<string,string>={workers_released:'release_workers',gate_raised:'captain_gate',meeting:'meeting'};
  for(const {area,object} of objects){
   const source=object.action==='campaign_event'?CAMPAIGN_EVENTS[object.eventId??'']:undefined;
   const produces=source?.sets?.includes(flag)||source?.choices?.some(choice=>choice.sets.includes(flag));
   if(object.evidence!==flag&&!(legacy[flag]&&object.action===legacy[flag])&&!produces)continue;
   if(game.interactionAvailability(object).completed)continue;
   const dependencies=source?missing(source):[];
   if(dependencies.length){for(const dependency of dependencies)resolve(dependency,next);continue;}
   if(!game.interactionVisible(object))continue;
   add(object.id,{area:area.id,point:object,label:object.label,objectId:object.id});
  }
  const boss=flag.startsWith('boss_defeated:')?flag.slice(14):undefined;
  if(boss||flag==='captain_defeated')for(const area of Object.values(areas)){
   if(flag==='captain_defeated'&&area.id!=='S10')continue;
   const enemy=area.enemies.find(e=>boss?e.bossId===boss:e.kind==='captain');
   if(enemy)add(enemy.id,{area:area.id,point:enemy,label:campaignText('event.defeatPrerequisite',{name:boss?CAMPAIGN_ENEMY_TEMPLATES[boss]?.name??area.name:campaignText('event.captain')})});
  }
 };
 for(const flag of missing(event))resolve(flag,new Set());
 const routes=availableRoutes(game,areas);
 return Array.from(targets,([key,destination])=>({id:key,destination,blocked:!routes.has(destination.area)})).sort((a,b)=>Number(a.blocked)-Number(b.blocked));
}
