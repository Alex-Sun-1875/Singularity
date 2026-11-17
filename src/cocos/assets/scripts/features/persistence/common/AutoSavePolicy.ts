import type {GameEvent} from '../../../core/Contracts';

const IMMEDIATE=new Set(['item','quest','journey_complete','complete','travel','retry','death','rest','captain_defeated','check_roll','check_result','loot_roll','level_up','auto_allocate']);
const PROGRESS=new Set(['experience','reward','defeat','loot_drop']);

/** Bounded periodic saves plus a non-sliding deadline for continuous rewards.
 * Lifecycle/manual commits bypass the clock through ChapterGame.save(). */
export class AutoSavePolicy {
 private elapsed=0;
 private progressIn:number|undefined;
 private retryIn:number|undefined;
 advance(seconds:number):void {
  if(!Number.isFinite(seconds)||seconds<=0)return;
  this.elapsed+=seconds;
  if(this.progressIn!==undefined)this.progressIn-=seconds;
  if(this.retryIn!==undefined)this.retryIn-=seconds;
 }
 /** Return whether this event batch needs an immediate durable commit. */
 observe(events:readonly GameEvent[]):boolean {
  let immediate=false;
  for(const event of events){
   if(IMMEDIATE.has(event.type)||event.type==='experience'&&Number(event.levels)>0||event.type==='campaign_battle'&&event.complete===true)immediate=true;
   else if(PROGRESS.has(event.type))this.progressIn??=3;
  }
  return immediate;
 }
 due(dirty:boolean):boolean {
  if(!dirty)return false;
  if(this.retryIn!==undefined)return this.retryIn<=0;
  return this.elapsed>=15||this.progressIn!==undefined&&this.progressIn<=0;
 }
 committed(ok:boolean):void {
  if(!ok){this.retryIn=2;return;}
  this.elapsed=0;this.progressIn=undefined;this.retryIn=undefined;
 }
}
