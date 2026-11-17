import type {Point} from '../../../core/Contracts';
import type {GameSession} from '../../../core/GameSession';
import {enemyDisplayName} from '../../combat/common/BossAwareness';
import {AREAS} from '../../world/data/WorldData';
import {JOURNEY_TASKS} from '../data/ChapterJourney';
import type {JourneyGuidance} from './JourneyGuide';
import {journeyText as text} from '../locales';

export interface ObjectiveTarget {id:string;point:Point;name:string;action:string;distance:number;type:JourneyGuidance['targetType'];blocked:boolean;blockage?:JourneyGuidance['blockage'];kind:JourneyGuidance['kind'];level?:number}
/** Resolve the selected, still-current objective without navigation queries or rule changes. */
export function objectiveTarget(game:GameSession,guide:JourneyGuidance|null):ObjectiveTarget|null {
 const s=game.state;if(!guide||s.status==='dead'||s.player.hp<=0)return null;
 if(guide.destination.area!==s.area&&!guide.hops)return null;
 const taskId=guide.destination.taskId,task=taskId?JOURNEY_TASKS.find(t=>t.id===taskId):undefined;
 if(task&&game.journey.currentTask(task.chapter)?.id!==task.id)return null;
 if(task&&task.goal!=='observe'&&guide.targetType==='object')return null;
 let point=guide.point,name=guide.instruction,action=guide.targetType==='position'?text('action.rest'):guide.kind==='hunt'?text('action.hunt'):text('action.travel'),level:number|undefined;
 if(guide.targetType==='enemy'){
  const enemy=s.enemies.find(e=>e.id===guide.targetId&&e.hp>0);if(!enemy)return null;
  point=enemy;name=enemyDisplayName(enemy);action=task?.goal==='hunt'||guide.kind==='hunt'?text('action.hunt'):text('action.defeat');level=enemy.level;
 }else if(guide.targetType==='exit'){
  const exit=AREAS[s.area]?.exits.find(e=>e.id===guide.targetId);if(!exit)return null;point=exit;name=AREAS[exit.to]?.name??exit.label;action=text('action.travel');
 }else if(guide.targetType==='object'){
  const object=AREAS[s.area]?.objects.find(o=>o.id===guide.targetId);if(!object||!game.interactionVisible(object))return null;point=object;name=object.label;action=object.action==='journey_task'?text('action.investigate'):text('action.interact');
 }
 const metres=guide.targetType==='enemy'||guide.blocked?Math.hypot(point.x-s.player.x,point.z-s.player.z):guide.distance;
 return {id:guide.targetId??`objective:${s.area}:${guide.kind}`,point,name,action,distance:metres,type:guide.targetType,blocked:guide.blocked,blockage:guide.blockage,kind:guide.kind,level};
}
