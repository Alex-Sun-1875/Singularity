import {resourceProfile} from '../../combat/common/ClassResource';
import {allocatedSkillRank,skillPower} from '../../progression/common/Progression';
import type {AreaDef,ExitDef,GameEvent,InputFrame,InteractionDef,Point,WorldQuery} from '../../../core/Contracts';
import {interactionApproachPath,interactionInRange} from '../../navigation/common/InteractionApproach';
import type {GameSession,EnemyState} from '../../../core/GameSession';
import {EQUIPMENT,type EquipmentSlot} from '../../equipment/data/Equipment';
import {recommendedEquipmentChange} from '../../equipment/common/EquipmentRecommendation';
import {enemyHurtRadius,enemyContains,enemyProfile} from '../../combat/common/EnemyCombat';
import {COMBAT_SKILLS} from '../../combat/data/PureSkills';
import {WARRIOR_ULTIMATE_CONTACT,warriorUltimateTouches} from '../../combat/common/WarriorUltimate';
import {HUNT_ENCOUNTERS} from '../../world/data/MonsterEcology';
import {JOURNEY_TASKS,chapterForArea} from '../../journey/data/ChapterJourney';
import {journeyGuidance,journeyQueueStatus,journeyTargetKey,type JourneyGuidance} from '../../journey/common/JourneyGuide';
import {BUILD_PROFILE} from '../../../shared/BuildProfile';
import {availableRoute,enemyApproachPath,routeBlockage,exitBlockage,pathBlockage,navigationBlockageText} from './AutomationRoute';
import {CAMPAIGN_EVENTS} from '../../campaign/data/CampaignEvents';
import {automationText as tr} from '../locales';
export {availableRoute} from './AutomationRoute';

export type AutomationMode='manual'|'quest'|'idle';
export type AutomationPause='manual'|'menu'|'story'|'dialogue'|'dice'|'choice'|'background'|'auth'|'portrait'|'failure'|'blocked';
export interface NavigationTarget {area:string;point:Point;label:string;exitId?:string;objectId?:string;taskId?:string;stageId?:string;bossKey?:string;enemyId?:string;journey?:boolean;sideQuest?:boolean;explorationSource?:string}
export interface AutomationStep {input:InputFrame;travel?:ExitDef;pickup?:string;equip?:{item:string;slot:EquipmentSlot};prepare?:boolean;interact?:string;notice?:string}
const distance=(a:Point,b:Point)=>Math.hypot(a.x-b.x,a.z-b.z);
const still=():InputFrame=>({x:0,z:0});
type CombatScope='travel'|'clear'|'hunt';

/** Durable gameplay stays in GameSession. This transient controller only requests
 * ordinary movement, attacks, interaction, pickups and travel. */
export class Automation {
 mode:AutomationMode='manual';
 destination:NavigationTarget|null=null;
 pausedDestination:NavigationTarget|null=null;
 status='';
 pauseReason:AutomationPause|null=null;
 private area='';
 private enemyId='';
 private route:Point[]=[];
 private routeGoal:Point|null=null;
 private replanAt=0;
 private blocked=new Map<string,number>();
 private blockedSweepAt=0;
 private scanAt=0;
 private lastPosition:Point|null=null;
 private stuck=0;
 private lastWalkAt=-Infinity;
 private nextSkillAt=0;
 private nextUltimateAt=0;
 private skillIndex=0;
 private basicActions=0;
 private lastBasicAction='';
 private restPoint:Point|null=null;
 private restScanAt=0;
 private questTaskId:string|undefined;
 private questChapter:number|undefined;
 private guidance:JourneyGuidance|null=null;
 private objectiveAt=0;
 private interactAt=0;
 private interactionStarted=-1;
 private recovery:NavigationTarget|null=null;
 private recoveryAt=0;
 private huntArea='';
 private evadeGoal:Point|null=null;
 private evadeUntil=0;
 private evadeScanAt=0;
 private evadeDashed=false;
 private evadeDashSafe=false;
 private nextSupportAt=0;
 private equipmentTarget:{item:string;slot:EquipmentSlot}|null=null;
 private equipmentScanAt=0;
 private nextEquipmentAt=0;
 private preparation:NavigationTarget|null=null;
 private preparationRetryAt=0;
 private preparationUntil=0;
 private deferred=new Set<string>();
 taskState:'running'|'awaiting-choice'|'blocked'|'completed'='running';

 get paused(){return !!this.pauseReason;}
 get active(){return !this.paused&&(this.mode!=='manual'||!!this.destination);}
 /** Follow the authored option order. Retry, postponement and shopping are
  * not progress defaults; manual input and external pauses keep ownership. */
 dialogueChoice(game:GameSession):string|undefined {
  const s=game.state,d=s.dialogue;
  if(this.mode!=='quest'||this.paused&&this.pauseReason!=='dialogue'||s.status==='dead'||s.dice.active||!d)return;
  const event=d.id.startsWith('campaign:')?CAMPAIGN_EVENTS[d.id.slice(9)]:undefined;
  return d.options.find(option=>option.id!=='later'&&option.id!=='shop'&&!option.id.startsWith('cancel:')&&!event?.choices?.some(choice=>choice.id===option.id&&choice.retry))?.id;
 }
 private get modeLabel(){return tr(this.mode==='idle'?'mode.hunt':'mode.task');}
 stop(){this.mode='manual';this.destination=null;this.pausedDestination=null;this.pauseReason=null;this.status='';this.resetRoute();this.enemyId='';this.restPoint=null;this.restScanAt=0;this.area='';this.blocked.clear();this.blockedSweepAt=0;this.scanAt=0;this.interactAt=0;this.recoveryAt=0;this.nextSkillAt=0;this.nextUltimateAt=0;this.basicActions=0;this.lastBasicAction='';this.questTaskId=undefined;this.questChapter=undefined;this.guidance=null;this.objectiveAt=0;this.interactionStarted=-1;this.recovery=null;this.huntArea='';this.evadeGoal=null;this.evadeUntil=0;this.evadeScanAt=0;this.nextSupportAt=0;this.equipmentTarget=null;this.equipmentScanAt=0;this.nextEquipmentAt=0;this.preparation=null;this.preparationRetryAt=0;this.preparationUntil=0;this.deferred.clear();this.taskState='running';}
 /** Scene rebuilding invalidates geometry, including same-map fast travel,
  * but retains the selected task, deferred queue, mode and pause ownership. */
 refreshArea(){this.area='';this.resetRoute();this.enemyId='';this.guidance=null;this.objectiveAt=0;this.interactionStarted=-1;this.evadeGoal=null;this.evadeUntil=0;this.equipmentTarget=null;this.equipmentScanAt=0;}
 /** "Later" postpones this objective for this run, without losing the queue or
  * writing a completion receipt. Enabling a new run makes it eligible again. */
 deferInteraction(objectId?:string){
  if(this.mode!=='quest')return false;
  const target=this.guidance?.destination;
  if(target)this.deferred.add(journeyTargetKey(target));
  if(objectId)this.deferred.add('object:'+objectId);
  this.guidance=null;this.objectiveAt=0;this.interactionStarted=-1;this.enemyId='';this.resetRoute();
  this.resumeAfter('dialogue');this.resumeAfter('menu');return true;
 }
 /** Observe successful physical pickups, including proximity-collected rare loot. */
 observeLoot(events:readonly GameEvent[]){
  if(this.mode==='manual')return;
  if(events.some(event=>event.type==='item'&&typeof event.id==='string'&&EQUIPMENT[event.id])){this.equipmentTarget=null;this.equipmentScanAt=0;}
 }
 /** Re-query after asynchronous model loading; the player may have taken over. */
 autoEquipmentChange(game:GameSession,id:string,slot?:EquipmentSlot){
  if(!this.active||this.mode==='manual')return null;
  const change=recommendedEquipmentChange(game);
  return change?.id===id&&(!slot||change.slot===slot)?change:null;
 }
 private equipLoot(game:GameSession):AutomationStep|null {
  if(this.mode==='manual')return null;
  const s=game.state,access=game.equipmentAvailability();
  // Do not scan the bag or stop defending while there is an active threat.
  if(!access.available&&!access.settling)return null;
  if(s.time>=this.equipmentScanAt){
   const best=recommendedEquipmentChange(game);this.equipmentTarget=best?{item:best.id,slot:best.slot}:null;this.equipmentScanAt=s.time+1;
  }
  if(!this.equipmentTarget)return null;
  const target=this.equipmentTarget,change=game.equipmentChange(target.item,target.slot);
  if(change.available){
   if(s.time<this.nextEquipmentAt)return {input:still()};
   this.nextEquipmentAt=s.time+2;return {input:still(),equip:target};
  }
  // Wait for the real disengagement clock before walking into another pack.
  if(change.block==='busy'){this.status=change.reason;return {input:still()};}
  this.equipmentTarget=null;this.equipmentScanAt=0;this.nextEquipmentAt=0;
  return null;
 }
 pause(reason:AutomationPause='manual',message?:string){
  // An external interruption must also suspend an intent that was already
  // waiting for a menu/story; closing that overlay must not restart it.
  if(!this.active){
   if(this.paused&&['background','auth','portrait','failure'].includes(reason)&&['menu','story','dialogue','dice'].includes(this.pauseReason??'')){this.pauseReason=reason;this.status=message??tr(`pause.${reason}`);}
   return;
  }
  this.pauseReason=reason;
  this.taskState=['dialogue','dice','story','menu','choice'].includes(reason)?'awaiting-choice':'blocked';
  if(this.destination){this.pausedDestination=this.destination;this.destination=null;}
  this.status=message??tr(this.mode==='manual'?'navigation.paused':`pause.${reason}`);
  this.resetRoute();this.enemyId='';this.evadeGoal=null;this.evadeUntil=0;
 }
 pauseNavigation(message=tr('navigation.paused')){this.pause('manual',message);}
 resume(){if(!this.paused)return;this.destination=this.pausedDestination;this.pausedDestination=null;this.pauseReason=null;this.objectiveAt=0;this.interactionStarted=-1;this.recovery=null;this.recoveryAt=0;this.preparation=null;this.preparationRetryAt=0;this.taskState='running';this.resetRoute();}
 resumeAfter(reason:AutomationPause){if(this.pauseReason===reason)this.resume();}
 setMode(mode:AutomationMode,taskId?:string){this.stop();this.mode=mode;this.questTaskId=taskId;this.questChapter=JOURNEY_TASKS.find(t=>t.id===taskId)?.chapter;this.status=tr(mode==='idle'?'hunt.search':'task.select');}
 navigate(target:NavigationTarget,preserveQuest=false){
  if(preserveQuest&&this.mode==='quest'){
   this.destination={...target,journey:false,point:{...target.point}};this.pausedDestination=null;this.pauseReason=null;this.guidance=null;this.objectiveAt=0;this.interactionStarted=-1;this.taskState='running';this.resetRoute();this.enemyId='';
  }else {this.stop();this.destination={...target,point:{...target.point}};}
  this.status=tr('navigation.travel',{target:target.label});
 }
 private resetRoute(){this.route=[];this.routeGoal=null;this.replanAt=0;this.lastPosition=null;this.stuck=0;this.lastWalkAt=-Infinity;}
 private visible(world:WorldQuery,a:Point,b:Point){return world.visible(a,b)&&Math.abs(world.height(a)-world.height(b))<1.2;}
 private walk(game:GameSession,world:WorldQuery,goal:Point,dt:number,enemy?:EnemyState,object?:InteractionDef):InputFrame|null {
  const p=game.state.player,now=game.state.time;
  if(this.lastPosition&&now-this.lastWalkAt<.25){this.stuck=distance(p,this.lastPosition)<.015?this.stuck+dt:0;if(this.stuck>4)return null;if(this.stuck>1)this.replanAt=0;}else this.stuck=0;
  this.lastPosition={x:p.x,z:p.z};this.lastWalkAt=now;
  if(!this.routeGoal||distance(goal,this.routeGoal)>1||now>=this.replanAt||!this.route.length){this.route=enemy?enemyApproachPath(game,world,enemy):object?interactionApproachPath(world,p,object):world.path?.(p,goal)??[];this.routeGoal={x:goal.x,z:goal.z};this.replanAt=now+.8;if(!this.route.length)return null;}
  while(this.route.length&&distance(p,this.route[0])<(object&&this.route.length===1?.025:.18))this.route.shift();
  const next=this.route[0];if(!next)return still();
  const d=distance(p,next),amount=Math.min(1,d/(6.5*Math.max(.01,dt)));
  return {x:(next.x-p.x)/d*amount,z:(next.z-p.z)/d*amount};
 }
 private fail(message:string,stop=false):AutomationStep {if(stop)this.stop();else this.pause('blocked',message);return {input:still(),notice:message};}
 /** Null means arrived; crossing an exit retains the objective across scene rebuild. */
 private travel(game:GameSession,world:WorldQuery,areas:Record<string,AreaDef>,target:NavigationTarget,dt:number):AutomationStep|null {
  const s=game.state,p=s.player,exit=s.area!==target.area?availableRoute(game,areas,target.area)?.[0]:target.exitId?areas[s.area]?.exits.find(e=>e.id===target.exitId):undefined;
  if(s.area!==target.area&&!exit){const blockage=routeBlockage(game,areas,target.area);return this.fail(blockage?navigationBlockageText(blockage):tr('route.locked'));}
  const requirement=exit&&exitBlockage(game,areas,s.area,exit);if(requirement)return this.fail(navigationBlockageText(requirement));
  const goal=exit??target.point;
  const object=!exit&&target.objectId?areas[s.area]?.objects.find(o=>o.id===target.objectId):undefined;
  if(object?interactionInRange(world,p,object,.05):distance(p,goal)<(exit?1.1:.9)&&this.visible(world,p,goal)){
   if(exit){this.resetRoute();if(this.mode==='manual'&&s.area===target.area)this.stop();return {input:still(),travel:exit};}
   return null;
  }
  const frame=this.walk(game,world,goal,dt,undefined,object);return frame?{input:frame}:this.fail(navigationBlockageText(pathBlockage(target.label,false,this.stuck>4)));
 }
 private refreshObjective(game:GameSession,world:WorldQuery,areas:Record<string,AreaDef>){
  const now=game.state.time,old=JOURNEY_TASKS.find(t=>t.id===this.questTaskId);
  if(old&&game.journey.taskDone(old)){this.questTaskId=game.journey.currentTask(old.chapter)?.id;this.objectiveAt=0;this.interactionStarted=-1;this.enemyId='';}
  if(now<this.objectiveAt&&this.guidance)return;
  this.objectiveAt=now+.8;this.questChapter??=chapterForArea(game.state.area);
  const guide=journeyGuidance(game,areas,world,this.questTaskId,'task',this.questChapter,{skip:this.deferred,allKnown:BUILD_PROFILE.developmentTools,finite:true,automatic:true});
  const previous=this.guidance?.destination,next=guide?.destination;
  if(previous?.area!==next?.area||previous?.taskId!==next?.taskId||previous?.objectId!==next?.objectId||previous?.enemyId!==next?.enemyId||previous?.stageId!==next?.stageId||previous?.explorationSource!==next?.explorationSource||this.guidance?.kind!==guide?.kind){this.enemyId='';this.scanAt=0;this.resetRoute();this.interactionStarted=-1;}
  if(guide?.destination.taskId){this.questTaskId=guide.destination.taskId;this.questChapter=JOURNEY_TASKS.find(t=>t.id===this.questTaskId)?.chapter;}
  this.guidance=guide;
 }
 private collect(game:GameSession,world:WorldQuery,dt:number):AutomationStep|null {
  const s=game.state,p=s.player,now=s.time;
  if(s.action||s.enemies.some(e=>e.hp>0&&distance(p,e)<10&&this.visible(world,p,e)))return null;
  const nearby=game.nearbyLoot()[0];if(nearby){this.status=tr('loot.collect',{mode:this.modeLabel});return {input:still(),pickup:nearby.id};}
  const drops=s.groundLoot.filter(d=>d.area===s.area&&game.canPickupLoot(d)&&(this.blocked.get(d.id)??0)<=now&&(this.mode==='idle'||distance(p,d)<=12)).sort((a,b)=>distance(p,a)-distance(p,b));
  for(const drop of drops.slice(0,3)){const frame=this.walk(game,world,drop,dt);if(frame){this.status=tr('loot.approach',{mode:this.modeLabel});return {input:frame};}this.blocked.set(drop.id,now+8);this.resetRoute();}
  return null;
 }
 private recover(game:GameSession,world:WorldQuery,areas:Record<string,AreaDef>,dt:number):AutomationStep|null {
  const s=game.state,p=s.player;
  if(!this.recovery&&(p.hp/p.maxHp>.2||p.healthPotions>0))return null;
  if(!this.recovery){
   const local=areas[s.area],targets:NavigationTarget[]=[];
   if(local?.checkpoint)targets.push({area:s.area,point:local.spawn,label:local.name});
   for(const object of local?.objects??[])if(object.action==='checkpoint')targets.push({area:s.area,point:object,label:object.label});
   if(this.mode==='quest'||s.checkpoint.area===s.area)targets.push({area:s.checkpoint.area,point:s.checkpoint,label:areas[s.checkpoint.area]?.name??s.checkpoint.area});
   this.recovery=targets.find(t=>availableRoute(game,areas,t.area)!==null&&(t.area!==s.area||world.path?.(p,t.point).length))??null;
   if(!this.recovery)return this.fail(tr('health.low'));
   this.resetRoute();this.enemyId='';this.recoveryAt=s.time+90;
  }
  if(s.time>this.recoveryAt)return this.fail(tr('health.failed'));
  this.status=tr('health.return');
  // Never let automatic hunting leave the area selected when it was enabled.
  if(this.mode==='idle'&&this.recovery.area!==this.huntArea)return this.fail(tr('health.low'));
  const step=this.travel(game,world,areas,this.recovery,dt);if(step)return step;
  if(game.rest()){this.recovery=null;this.resetRoute();this.objectiveAt=0;this.status=tr('health.rest');return {input:still()};}
  return this.fail(tr('health.failed'));
 }
 /** Spend unused growth points through the same checkpoint transactions as
  * manual preparation. A short detour retains the task and never moves idle
  * hunting to another map. A blocked detour must not stop the task queue. */
 private prepareProgression(game:GameSession,world:WorldQuery,areas:Record<string,AreaDef>,dt:number):AutomationStep|null {
  if(this.mode==='manual')return null;
  const s=game.state,p=s.player;
  if(!s.progression.unspentPoints&&!s.progression.skillPoints){this.preparation=null;return null;}
  if(!this.preparation&&s.time<this.preparationRetryAt)return null;
  const plan=game.automaticProgressionPlan();
  if(!plan.attributePoints&&!plan.skillPoints){this.preparation=null;this.preparationRetryAt=s.time+1;return null;}
  if(game.preparationAvailability().available){this.preparation=null;this.preparationRetryAt=s.time+1;this.resetRoute();this.objectiveAt=0;this.status=tr('growth.allocate');return {input:still(),prepare:true};}
  const access=game.equipmentAvailability();
  if(!this.preparation){
   if(!access.available){if(access.settling){this.status=access.reason;return {input:still()};}return null;}
   const loot=this.collect(game,world,dt);if(loot)return loot;
   const local=areas[s.area],targets:NavigationTarget[]=[];
   if(local?.checkpoint)targets.push({area:s.area,point:local.spawn,label:local.name});
   for(const object of local?.objects??[])if(object.action==='checkpoint')targets.push({area:s.area,point:object,label:object.label});
   if(this.mode==='quest'||s.checkpoint.area===s.area)targets.push({area:s.checkpoint.area,point:s.checkpoint,label:areas[s.checkpoint.area]?.name??s.checkpoint.area});
   this.preparation=targets.filter(target=>availableRoute(game,areas,target.area)!==null&&(target.area!==s.area||!!world.path?.(p,target.point).length)).sort((a,b)=>Number(a.area!==s.area)-Number(b.area!==s.area)||distance(p,a.point)-distance(p,b.point))[0]??null;
   if(!this.preparation){this.preparationRetryAt=s.time+10;return null;}
   this.preparationUntil=s.time+90;this.resetRoute();this.enemyId='';
  }
  const skip=()=>{this.preparation=null;this.preparationRetryAt=s.time+30;this.resetRoute();return null;};
  if(s.time>this.preparationUntil)return skip();
  const evade=this.evade(game,world);if(evade)return evade;
  const combat=this.fight(game,world,dt,'travel');if(combat)return combat;
  if(!access.available){this.status=access.reason;return {input:still()};}
  const target=this.preparation,exit=s.area!==target.area?availableRoute(game,areas,target.area)?.[0]:undefined;
  if(s.area!==target.area&&!exit||exit&&game.exitRequirement(exit))return skip();
  const goal=exit??target.point;this.status=tr('growth.travel');
  if(distance(p,goal)<.9&&this.visible(world,p,goal)){
   if(exit){this.resetRoute();return {input:still(),travel:exit};}
   return skip();
  }
  const frame=this.walk(game,world,goal,dt);return frame?{input:frame}:skip();
 }
 /** Reuse the authored attack/zone geometry. Walking and dodging still obey
  * normal collision, action cancellation and the equipped dodge skill. */
 private evade(game:GameSession,world:WorldQuery):AutomationStep|null {
  const s=game.state,p=s.player,now=s.time;
  if(s.action?.kind==='dash')return {input:still()};
  if(now>=this.evadeUntil&&now>=this.evadeScanAt){
   this.evadeGoal=null;this.evadeDashSafe=false;this.evadeScanAt=now+.15;
   const enemies=s.enemies.filter(e=>{const c=e.combat,step=c&&enemyProfile(e)?.attacks[c.moveId]?.steps[c.stepIndex];return e.hp>0&&distance(p,e)<18&&(e.phase==='active'||e.phase==='windup'&&(step?step.windup-(c?.stepElapsed??0)<=.35:e.phaseTime<=.35))&&this.visible(world,p,e);});
   const geometry=enemies.flatMap(e=>{const c=e.combat,step=c&&enemyProfile(e)?.attacks[c.moveId]?.steps[c.stepIndex];return step&&(step.baseDamage>0||step.projectile||step.zone)?c?.telegraphGeometry??c?.geometry??[]:[];});
   const hazards=s.enemyHazards.filter(h=>h.remaining>0&&h.maxTicks>0&&(h.damage>0||h.status)).flatMap(h=>h.geometry);
   const legacy=enemies.filter(e=>!e.combat&&distance(p,e)<4);
   const danger=(q:Point)=>geometry.some(g=>enemyContains(g,q))||hazards.some(g=>enemyContains(g,q))||s.fireZones.some(f=>distance(f,q)<f.radius+.4)||legacy.some(e=>distance(q,e)<(e.attackKind==='charge'?4:2.4)&&Math.cos(Math.atan2(q.x-e.x,q.z-e.z)-e.targetAngle)>.1);
   if(danger(p)){
    const profile=game.basicAttackProfile(),melee=profile.angleDegrees>0;
    const target=s.enemies.find(e=>e.id===this.enemyId&&e.hp>0)??s.enemies.filter(e=>e.hp>0&&this.visible(world,p,e)).sort((a,b)=>distance(p,a)-distance(p,b))[0];
    const preferred=melee?1.55:profile.rangeMetres*.65;
    for(const radius of [1.6,3.2]){
     let score=-Infinity;
     for(let i=0;i<12;i++){
      const angle=i*Math.PI/6,q={x:p.x+Math.sin(angle)*radius,z:p.z+Math.cos(angle)*radius};
      if(danger(q)||!this.visible(world,p,q))continue;
      const metres=target?distance(q,target):radius;
      const value=-Math.abs(metres-preferred)-Math.max(0,metres-profile.rangeMetres)*2;
      if(value>score){score=value;this.evadeGoal=q;}
     }
     // A small safe step keeps melee contacts and placed fields useful. Only
     // search the larger ring when every nearby candidate is actually unsafe.
     if(this.evadeGoal){
      const dodge=allocatedSkillRank(s.progression,'COM_01');
      if(radius>2&&dodge){
       const length=dodge.castRangeMetres*(s.equipment.feet==='A16'?1.08:1),scale=length/radius;
       const landing={x:p.x+(this.evadeGoal.x-p.x)*scale,z:p.z+(this.evadeGoal.z-p.z)*scale};
       this.evadeDashSafe=!danger(landing)&&this.visible(world,p,landing);
      }
      break;
     }
    }
    if(this.evadeGoal){this.evadeUntil=now+.42;this.evadeDashed=false;this.resetRoute();}
   }
  }
  if(!this.evadeGoal||now>=this.evadeUntil)return null;
  const d=distance(p,this.evadeGoal);if(d<.25){this.evadeGoal=null;this.evadeUntil=now;return null;}
  const dash=this.evadeDashSafe&&!this.evadeDashed&&(!s.action||s.action.elapsed>=.3)&&(s.combat.cooldowns.COM_01??0)<=.05&&!!allocatedSkillRank(s.progression,'COM_01');
  if(dash)this.evadeDashed=true;
  this.status=tr('health.retreat');return {input:{x:(this.evadeGoal.x-p.x)/d,z:(this.evadeGoal.z-p.z)/d,dash}};
 }
 update(game:GameSession,world:WorldQuery,areas:Record<string,AreaDef>,dt:number):AutomationStep {
  const s=game.state,p=s.player;
  if(!this.active)return {input:still()};
  if(s.time>=this.blockedSweepAt){this.blockedSweepAt=s.time+8;for(const [id,until]of this.blocked)if(until<=s.time)this.blocked.delete(id);}
  if(s.status==='dead')return this.fail(tr('dead'),true);
  if(s.dialogue||s.dice.active){this.pause(s.dialogue?'dialogue':'dice');return {input:still()};}
  if(this.area!==s.area){this.area=s.area;this.resetRoute();this.enemyId='';this.blocked.clear();this.scanAt=0;this.restPoint=null;this.restScanAt=0;this.objectiveAt=0;}
  const equipment=this.equipLoot(game);if(equipment)return equipment;
  if(!s.action&&p.hp/p.maxHp<=.45&&p.healthPotions>0&&!(s.cooldowns.consumable>0))game.useConsumable('health');
  const preparation=this.prepareProgression(game,world,areas,dt);if(preparation)return preparation;
  const destinationTask=JOURNEY_TASKS.find(task=>task.id===this.destination?.taskId);
  if(this.mode==='quest'&&destinationTask&&game.journey.taskDone(destinationTask)){this.destination=null;this.resetRoute();this.objectiveAt=0;}
  if(this.destination){
   // Journey navigation follows the current objective, including after combat
   // or a scene change. Explicit map/object/boss destinations stay fixed.
   if(this.destination.journey&&s.time>=this.objectiveAt){
    this.objectiveAt=s.time+.8;
    const guide=journeyGuidance(game,areas,world,this.destination.taskId);
    if(!guide)return this.fail(tr('task.missing'));
    if(guide.blocked)return this.fail(guide.blockage?navigationBlockageText(guide.blockage):tr('pause.blocked'));
    this.destination={...guide.destination,point:{...guide.destination.point}};
   }
   if(this.mode==='quest'){
    if(!s.action&&p.hp/p.maxHp<=.45&&p.healthPotions>0&&!(s.cooldowns.consumable>0))game.useConsumable('health');
    const combat=this.fight(game,world,dt,this.destination.enemyId&&s.area===this.destination.area?'clear':'travel');if(combat)return combat;
   }else if(s.enemies.some(e=>e.hp>0&&distance(p,e)<8&&this.visible(world,p,e))){this.pauseNavigation(tr('navigation.threat'));return {input:still(),notice:this.status};}
   const target=this.destination;this.status=tr('navigation.travel',{target:target.label});
   const step=this.travel(game,world,areas,target,dt);if(step)return step;
   if(s.action)return {input:still()};
   if(this.mode==='quest'){this.destination=null;this.resetRoute();this.objectiveAt=0;}else this.stop();
   return {input:still(),interact:target.objectId,notice:tr('navigation.arrived',{target:target.label})};
  }
  if(!s.action&&p.hp/p.maxHp<=.45&&p.healthPotions>0&&!(s.cooldowns.consumable>0))game.useConsumable('health');
  if(this.mode==='idle'){this.huntArea||=s.area;if(this.huntArea!==s.area)return this.fail(tr('hunt.empty'),true);}
  const evade=this.evade(game,world);if(evade){this.interactionStarted=-1;return evade;}
  const recovery=this.recover(game,world,areas,dt);if(recovery){this.interactionStarted=-1;return recovery;}
  if(this.mode==='quest')this.refreshObjective(game,world,areas);
  const guide=this.guidance,target=guide?.destination,local=this.mode==='idle'||target?.area===s.area;
  if(this.mode==='quest'&&(!guide||!target)){
   const pending=journeyQueueStatus(game,areas);
   if(pending.remaining)return this.fail(tr('task.remaining',{count:pending.remaining}));
   this.stop();this.taskState='completed';this.status=tr('task.completed');return {input:still(),notice:this.status};
  }
  const task=JOURNEY_TASKS.find(t=>t.id===target?.taskId);
  const scope:CombatScope=this.mode==='idle'?'hunt':!local?'travel':guide?.kind==='boss'||target?.enemyId||target?.explorationSource&&guide?.targetType==='enemy'||task?.goal==='clear'||task?.goal==='encounter'&&guide?.targetType==='enemy'?'clear':guide?.kind==='hunt'||task?.goal==='hunt'?'hunt':'travel';
  // Reach the actual authored action. The app confirms its default through
  // ordinary dialogue; travel itself never commits a puzzle or branch receipt.
  if((task?.goal==='encounter'||target?.sideQuest)&&local&&target?.objectId){
   const object=areas[s.area]?.objects.find(o=>o.id===target.objectId);
   if(!object)return this.fail(tr('task.failed'));
   this.status=tr('task.travel',{target:object.label});
   const step=this.travel(game,world,areas,{...target,point:object},dt);if(step)return step;
   if(s.action)return {input:still()};
   this.objectiveAt=0;this.interactionStarted=-1;return {input:still(),interact:object.id,notice:tr('task.interact')};
  }
  const loot=this.collect(game,world,dt);if(loot)return loot;
  const combat=this.fight(game,world,dt,scope);if(combat){this.interactionStarted=-1;return combat;}
  if(this.mode==='idle')return this.waitForHunt(game,world,areas,dt);
  if(!guide||!target)return this.fail(tr('task.missing'));
  if(!local){this.status=tr('task.travel',{target:target.label});return this.travel(game,world,areas,target,dt)??{input:still()};}
  if(target.exitId){this.status=tr('task.travel',{target:target.label});return this.travel(game,world,areas,target,dt)??{input:still()};}
  if(guide.kind==='hunt'||task?.goal==='hunt')return this.waitForHunt(game,world,areas,dt);
  if(task?.goal==='observe'||target.explorationSource&&target.objectId){
   const object=areas[s.area]?.objects.find(o=>target.explorationSource?o.id===target.objectId:o.action==='journey_task'&&o.eventId===task?.id);
   if(!object)return this.fail(tr('task.failed'));
   this.status=tr('task.interact');const step=this.travel(game,world,areas,{...target,point:object},dt);if(step)return step;
   const access=game.interactionAvailability(object);
   if(!access.available){
    this.interactionStarted=-1;
    if(access.completed){this.objectiveAt=0;return {input:still()};}
    if(task&&!game.journey.ready(task)||target.explorationSource&&game.canApproachInteraction())return this.fail(access.reason);
    // Combat/projectiles/telegraphs can make a reached observation temporarily
    // unsafe. Keep the controller running instead of opening a blocking modal.
    this.status=access.reason;return {input:still()};
   }
   if(this.interactionStarted<0)this.interactionStarted=s.time;
   if(s.time-this.interactionStarted>8)return this.fail(tr('task.failed'));
   if(!s.action&&s.time>=this.interactAt){this.interactAt=s.time+.5;return {input:still(),interact:object.id};}
  }
  this.status=tr('task.settle');return {input:still()};
 }
 private waitForHunt(game:GameSession,world:WorldQuery,areas:Record<string,AreaDef>,dt:number):AutomationStep {
  const s=game.state,p=s.player,now=s.time;
  const slots=(HUNT_ENCOUNTERS[s.area]??[]).filter(slot=>s.enemies.some(e=>e.id===slot.id&&e.hp<=0));
  if(!slots.length){this.status=tr(s.enemies.some(e=>e.respawnSeconds)?'hunt.unreachable':'hunt.empty');return {input:still()};}
  if(!this.restPoint&&now>=this.restScanAt){
   this.restScanAt=now+3;
   const area=areas[s.area],points:Point[]=[];
   if(area)for(let x=-2;x<=2;x++)for(let z=-2;z<=2;z++)points.push({x:x*(area.width/2-2)/2,z:z*(area.depth/2-2)/2});
   const clearance=(q:Point)=>slots.filter(slot=>distance(q,slot)>22).length;
   const candidates=points.filter(q=>clearance(q)>0).sort((a,b)=>clearance(b)-clearance(a)||distance(a,p)-distance(b,p));
   for(const q of candidates.slice(0,4))if(world.path?.(p,q).length){this.restPoint=q;this.resetRoute();break;}
  }
  this.status=tr('hunt.wait');
  if(this.restPoint&&distance(p,this.restPoint)>.8){const frame=this.walk(game,world,this.restPoint,dt);if(frame)return {input:frame};this.restPoint=null;}
  return {input:still()};
 }
 private fight(game:GameSession,world:WorldQuery,dt:number,scope:CombatScope):AutomationStep|null {
  const s=game.state,p=s.player,now=s.time;
  const eligible=(e:EnemyState)=>e.hp>0&&((scope==='clear'&&!e.respawnSeconds)||(scope==='hunt'&&!!e.respawnSeconds)||distance(p,e)<10&&this.visible(world,p,e));
  let enemy=s.enemies.find(e=>e.id===this.enemyId&&e.hp>0&&(eligible(e)||scope==='travel'&&distance(p,e)<=18));
  if(!enemy&&now>=this.scanAt){
   this.scanAt=now+.75;
   const candidates=s.enemies.filter(e=>eligible(e)&&(this.blocked.get(e.id)??0)<=now);
   const priority=(e:EnemyState)=>distance(e,p)-(distance(e,p)<6&&this.visible(world,p,e)?20:0);
   candidates.sort((a,b)=>priority(a)-priority(b));
   // At most three candidates per bounded scan; retain the selected approach.
   let approach:Point[]=[];
   for(const candidate of candidates.slice(0,3)){
    approach=enemyApproachPath(game,world,candidate);if(approach.length){enemy=candidate;break;}
    this.blocked.set(candidate.id,now+8);
   }
   if(enemy){this.enemyId=enemy.id;this.resetRoute();this.route=approach;this.routeGoal={x:enemy.x,z:enemy.z};this.replanAt=now+.8;this.restPoint=null;}
  }
  if(!enemy){this.enemyId='';return null;}
  this.status=tr(this.mode==='idle'?'hunt.fight':'task.fight');
  const d=distance(p,enemy),visible=this.visible(world,p,enemy),profile=game.basicAttackProfile();
  const reach=profile.rangeMetres+(profile.angleDegrees?enemyHurtRadius(enemy):0)-.2;
  const aim=Math.atan2(enemy.x-p.x,enemy.z-p.z),frame:InputFrame={x:0,z:0,aim,target:{x:enemy.x,z:enemy.z}};
  // Ordinary automatic fire uses taps. Charging every shot leaves long empty
  // attack gaps; manual input still controls the normal charged shot.
  if(s.action?.kind==='bowAim'){frame.attack=false;return {input:frame};}
  const basic=s.action;
  if(basic?.emitted&&(basic.kind==='bow'||basic.kind==='staff')&&basic.id!==this.lastBasicAction){this.lastBasicAction=basic.id;this.basicActions=Math.min(2,this.basicActions+1);}
  if(visible&&!s.action){
   const resource=resourceProfile(s);
   if(p.hp/p.maxHp>.45&&p.focus/p.maxFocus<.2&&p[resource.stock]>0&&!(s.cooldowns.consumable>0))game.useConsumable('resource');
   // Decisions below inspect only equipped slots. Building every learned and
   // unlearned skill's description/readiness here repeats catalogue work in
   // every ordinary attack gap during continuous hunting.
   const equipped=s.combat.activeSlots.filter((id):id is string=>!!id);
   if(s.combat.ultimate)equipped.push(s.combat.ultimate);
   if(s.progression.learned.COM_02)equipped.push('COM_02');
   const views=game.combatSkillView(equipped);
   const nearby=s.enemies.filter(e=>e.hp>0&&distance(p,e)<=18&&this.visible(world,p,e));
   // Read the current attack only. A ready dodge is preferred to spending a
   // fresh shield at full health before every harmless approach.
   const imminent=nearby.some(e=>{
    if(e.phase!=='active'&&e.phase!=='windup')return false;
    const c=e.combat,step=c&&enemyProfile(e)?.attacks[c.moveId]?.steps[c.stepIndex];
    if(e.phase==='windup'&&(step?step.windup-(c?.stepElapsed??0):e.phaseTime)>.55)return false;
    const geometry=c?.telegraphGeometry??c?.geometry;
    return geometry?.length?geometry.some(g=>enemyContains(g,p)):distance(p,e)<4&&Math.cos(Math.atan2(p.x-e.x,p.z-e.z)-e.targetAngle)>.1;
   });
   const dodgeReady=!!allocatedSkillRank(s.progression,'COM_01')&&(s.combat.cooldowns.COM_01??0)<=.05;
   const needsProtection=p.hp/p.maxHp<.8||imminent&&!dodgeReady;
   // Weave a single-target ranged skill between actual basic releases. Strong
   // targets, danger and enemies beyond basic range can justify casting first.
   const preferBasics=profile.angleDegrees===0&&d<=reach&&!enemy.bossId&&enemy.kind!=='captain'&&!imminent&&p.hp/p.maxHp>=.45;
   if(now>=this.nextSupportAt&&p.hp/p.maxHp<.65&&!(s.combat.buffs.healCount>0)&&views.find(v=>v.id==='COM_02')?.ready){frame.healSkill=true;this.nextSupportAt=now+1.5;return {input:frame};}
   if(now>=this.nextSupportAt)for(let slot=0;slot<4;slot++){
    const id=s.combat.activeSlots[slot],rank=id&&allocatedSkillRank(s.progression,id);
    if(!id||!rank||COMBAT_SKILLS[id]?.offensive||!views.find(v=>v.id===id)?.ready)continue;
    const heal=rank.healMaxHpPercent>0&&p.hp/p.maxHp<.65&&!(s.combat.buffs.healCount>0);
    const shield=rank.shieldMaxHpPercent>0&&d<6&&needsProtection&&p.shield<p.maxHp*.08;
    const ward=id==='THU_06'&&d<6&&needsProtection&&(s.combat.buffs.stormWardUntil??0)<=now;
    const enchant=id==='THU_03'&&d<=profile.rangeMetres&&((s.combat.buffs.thunderCharges??0)<=0||(s.combat.buffs.thunderUntil??0)<=now);
    if(heal||shield||ward||enchant){frame.combatSlot=slot as 0|1|2|3;this.nextSupportAt=now+1.5;return {input:frame};}
   }
   const usable=(id:string|null)=>{
    if(!id||!COMBAT_SKILLS[id]?.offensive||!s.progression.learned[id]||!views.find(v=>v.id===id)?.ready)return false;
    const rank=allocatedSkillRank(s.progression,id);if(!rank)return false;
    if(preferBasics&&COMBAT_SKILLS[id].damageRole==='single'&&this.basicActions<2)return false;
    if(id==='BOW_07'&&(d>3.5||!(p.hp/p.maxHp<.6||imminent&&!dodgeReady)))return false;
    if(id==='BOW_06'&&(d>5||!!enemy.bossId||enemy.kind==='captain'||enemy.kind==='archer'||s.combat.casts.some(c=>c.skillId===id&&(c.zoneUntil??0)>now)))return false;
    const g=rank.geometry,self=COMBAT_SKILLS[id].targetingMode==='self';
    const range=self?g?.radiusMetres??rank.castRangeMetres:rank.castRangeMetres;
    return range>0&&d<=range+(g?.kind.startsWith('melee')?enemyHurtRadius(enemy):0)-.1;
   };
   // Estimate only current, visible coverage. The executor still performs all
   // real contacts, collision, target caps and subsequent segment checks.
   const coverageCache=new Map<string,{count:number;point:Point;angle:number}>();
   const coverage=(id:string)=>{
    const cached=coverageCache.get(id);if(cached)return cached;
    const def=COMBAT_SKILLS[id],rank=allocatedSkillRank(s.progression,id)!,g=rank.geometry;
    let best={count:1,point:{x:enemy.x,z:enemy.z},angle:aim};
    if(def.damageRole==='single'||id==='WAR_02'){coverageCache.set(id,best);return best;}
    const points:Point[]=[best.point];
    if(g?.origin==='aimPoint')points.push(...nearby.filter(e=>distance(p,e)<=rank.castRangeMetres).slice(0,8));
    for(const point of points){
     const angle=Math.atan2(point.x-p.x,point.z-p.z),origin=g?.origin==='caster'?p:point;
     let count=nearby.filter(e=>{
      if(!this.visible(world,origin,e))return false;
      const x=e.x-origin.x,z=e.z-origin.z,r=enemyHurtRadius(e),forward=x*Math.sin(angle)+z*Math.cos(angle),side=x*Math.cos(angle)-z*Math.sin(angle);
      if(id==='WAR_05'&&warriorUltimateTouches({forward,side},WARRIOR_ULTIMATE_CONTACT.startAge,WARRIOR_ULTIMATE_CONTACT.endAge,r))return true;
      if(g?.kind==='instantCorridor'||g?.kind==='projectileCorridor')return forward>=-r&&forward<=(g.lengthMetres??rank.castRangeMetres)+r&&Math.abs(side)<=(g.widthMetres??0)/2+r;
      if(g?.kind==='targetVolley'||g?.kind==='filledWaveRectangle')return Math.abs(forward)<=(g.depthMetres??0)/2+r&&Math.abs(side)<=(g.widthMetres??0)/2+r;
      if(g?.kind==='meleeFan'||g?.kind==='boundedArcFan')return distance(origin,e)<=(g.radiusMetres??rank.radiusMetres)+r&&Math.abs(Math.atan2(Math.sin(Math.atan2(x,z)-angle),Math.cos(Math.atan2(x,z)-angle)))<=(g.angleDegrees??0)*Math.PI/360;
      return distance(origin,e)<=(g?.radiusMetres??rank.radiusMetres)+r;
     }).length;
     count=Math.min(count,rank.targetLimit??def.maxTargets??Infinity);
     if(count>best.count)best={count,point:{x:point.x,z:point.z},angle};
    }
    coverageCache.set(id,best);return best;
   };
   const request=(id:string)=>{
    const target=coverage(id);frame.target=target.point;frame.aim=target.angle;
    if(COMBAT_SKILLS[id].damageRole==='single')this.basicActions=0;
    if(id===s.combat.ultimate){frame.ultimate=true;this.nextUltimateAt=now+8;}
    else {const slot=s.combat.activeSlots.indexOf(id);frame.combatSlot=slot as 0|1|2|3;this.skillIndex=(slot+1)%4;this.nextSkillAt=now+1.2;}
    return {input:frame};
   };
   const primary=s.combat.family+'_01',primaryRank=allocatedSkillRank(s.progression,primary),primaryBudget=(primaryRank?.maxDamagePerTargetS??0)*skillPower(s.progression);
   const finishable=!enemy.bossId&&enemy.kind!=='captain'&&enemy.hp<=primaryBudget;
   const ordinary=s.combat.activeSlots.filter((id):id is string=>!!id&&id!==primary&&usable(id));
   const area=ordinary.filter(id=>coverage(id).count>=2).sort((a,b)=>{
    const value=(id:string)=>allocatedSkillRank(s.progression,id)!.maxDamagePerTargetS*coverage(id).count/(1+COMBAT_SKILLS[id].resourceCost*.02);
    return value(b)-value(a);
   });
   const strongArea=area.find(id=>allocatedSkillRank(s.progression,id)!.maxDamagePerTargetS*coverage(id).count>(primaryRank?.maxDamagePerTargetS??0)*1.1);
   if(ordinary.includes('BOW_07')&&now>=this.nextSupportAt){this.nextSupportAt=now+1.5;return request('BOW_07');}
   const ultimate=s.combat.ultimate;
   const groupUltimate=!!ultimate&&usable(ultimate)&&coverage(ultimate).count>=2;
   const singleBoss=(!!enemy.bossId||enemy.kind==='captain')&&nearby.length===1;
   if(now>=this.nextSkillAt&&usable(primary)&&((!strongArea&&!groupUltimate)||finishable||singleBoss))return request(primary);
   if(now>=this.nextUltimateAt&&ultimate&&usable(ultimate)&&!finishable)return request(ultimate);
   if(now>=this.nextSkillAt){
    if(strongArea&&!finishable)return request(strongArea);
    if(usable(primary))return request(primary);
    // Keep enough for the imminent main attack instead of spending the last
    // resource on a low-damage control against a single survivor.
    for(let i=0;i<4;i++){
     const slot=(this.skillIndex+i)%4,id=s.combat.activeSlots[slot];if(!id||!ordinary.includes(id))continue;
     if(finishable||((s.combat.cooldowns[primary]??0)<=1.2&&p.focus<COMBAT_SKILLS[id].resourceCost+(COMBAT_SKILLS[primary]?.resourceCost??0)))continue;
     return request(id);
    }
   }
  }
  if(s.action?.kind==='sword'&&s.action.elapsed+dt+1e-8>=s.action.duration){
   // Holding attack would start another cut inside GameSession before this
   // controller ever sees an idle frame. Release only at the completed cut
   // when a real equipped skill needs that gap; never cancel its active beat.
   const ids=s.combat.activeSlots.filter((id):id is string=>!!id);if(s.combat.ultimate)ids.push(s.combat.ultimate);
   if(s.progression.learned.COM_02)ids.push('COM_02');
   const pending=game.combatSkillView(ids).some(view=>{
    if(!view.ready)return false;const def=COMBAT_SKILLS[view.id],rank=allocatedSkillRank(s.progression,view.id)!;
    if(def.offensive)return now>=(def.type==='ultimate'?this.nextUltimateAt:this.nextSkillAt)&&visible&&d<=rank.castRangeMetres+enemyHurtRadius(enemy);
    return now>=this.nextSupportAt&&(view.id==='COM_02'?p.hp/p.maxHp<.65&&!(s.combat.buffs.healCount>0):p.hp/p.maxHp<.8&&rank.shieldMaxHpPercent>0&&p.shield<p.maxHp*.08);
   });
   if(pending){frame.attack=false;return {input:frame};}
  }
  if(visible&&d<=reach){frame.attack=true;this.stuck=0;return {input:frame};}
  // Freeze facing through the current action, then repath toward a moving target.
  if(s.action)return {input:frame};
  const movement=this.walk(game,world,enemy,dt,enemy);
  if(movement)return {input:{...frame,...movement}};
  this.blocked.set(enemy.id,now+8);this.enemyId='';this.resetRoute();this.status=tr('target.blocked',{mode:this.modeLabel});
  return {input:still()};
 }
}
