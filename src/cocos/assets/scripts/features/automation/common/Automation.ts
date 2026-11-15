import {resourceProfile} from '../../combat/common/ClassResource';
import {allocatedSkillRank} from '../../progression/common/Progression';
import type {AreaDef,ExitDef,InputFrame,Point,WorldQuery} from '../../../core/Contracts';
import type {GameSession,EnemyState} from '../../../core/GameSession';
import {enemyHurtRadius,enemyContains,enemyProfile} from '../../combat/common/EnemyCombat';
import {COMBAT_SKILLS} from '../../combat/data/PureSkills';
import {HUNT_ENCOUNTERS} from '../../world/data/MonsterEcology';
import {JOURNEY_TASKS,chapterForArea} from '../../journey/data/ChapterJourney';
import {journeyGuidance,type JourneyGuidance} from '../../journey/common/JourneyGuide';
import {availableRoute,enemyApproachPath} from './AutomationRoute';
import {automationText as tr} from '../locales';
export {availableRoute} from './AutomationRoute';

export type AutomationMode='manual'|'quest'|'idle';
export type AutomationPause='manual'|'menu'|'story'|'dialogue'|'dice'|'background'|'auth'|'portrait'|'failure'|'blocked';
export interface NavigationTarget {area:string;point:Point;label:string;exitId?:string;objectId?:string;taskId?:string;bossKey?:string}
export interface AutomationStep {input:InputFrame;travel?:ExitDef;pickup?:string;interact?:string;notice?:string}
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
 private nextSupportAt=0;

 get paused(){return !!this.pauseReason;}
 get active(){return !this.paused&&(this.mode!=='manual'||!!this.destination);}
 private get modeLabel(){return tr(this.mode==='idle'?'mode.hunt':'mode.task');}
 stop(){this.mode='manual';this.destination=null;this.pausedDestination=null;this.pauseReason=null;this.status='';this.resetRoute();this.enemyId='';this.restPoint=null;this.restScanAt=0;this.area='';this.blocked.clear();this.blockedSweepAt=0;this.scanAt=0;this.interactAt=0;this.recoveryAt=0;this.nextSkillAt=0;this.nextUltimateAt=0;this.questTaskId=undefined;this.questChapter=undefined;this.guidance=null;this.objectiveAt=0;this.interactionStarted=-1;this.recovery=null;this.huntArea='';this.evadeGoal=null;this.evadeUntil=0;this.evadeScanAt=0;this.nextSupportAt=0;}
 pause(reason:AutomationPause='manual',message?:string){
  // An external interruption must also suspend an intent that was already
  // waiting for a menu/story; closing that overlay must not restart it.
  if(!this.active){
   if(this.paused&&['background','auth','portrait','failure'].includes(reason)&&['menu','story','dialogue','dice'].includes(this.pauseReason??'')){this.pauseReason=reason;this.status=message??tr(`pause.${reason}`);}
   return;
  }
  this.pauseReason=reason;
  if(this.destination){this.pausedDestination=this.destination;this.destination=null;}
  this.status=message??tr(this.mode==='manual'?'navigation.paused':`pause.${reason}`);
  this.resetRoute();this.enemyId='';this.evadeGoal=null;this.evadeUntil=0;
 }
 pauseNavigation(message=tr('navigation.paused')){this.pause('manual',message);}
 resume(){if(!this.paused)return;this.destination=this.pausedDestination;this.pausedDestination=null;this.pauseReason=null;this.objectiveAt=0;this.interactionStarted=-1;this.recovery=null;this.recoveryAt=0;this.resetRoute();}
 resumeAfter(reason:AutomationPause){if(this.pauseReason===reason)this.resume();}
 setMode(mode:AutomationMode,taskId?:string){this.stop();this.mode=mode;this.questTaskId=taskId;this.questChapter=JOURNEY_TASKS.find(t=>t.id===taskId)?.chapter;this.status=tr(mode==='idle'?'hunt.search':'task.select');}
 navigate(target:NavigationTarget){this.stop();this.destination={...target,point:{...target.point}};this.status=tr('navigation.travel',{target:target.label});}
 private resetRoute(){this.route=[];this.routeGoal=null;this.replanAt=0;this.lastPosition=null;this.stuck=0;this.lastWalkAt=-Infinity;}
 private visible(world:WorldQuery,a:Point,b:Point){return world.visible(a,b)&&Math.abs(world.height(a)-world.height(b))<1.2;}
 private walk(game:GameSession,world:WorldQuery,goal:Point,dt:number,enemy?:EnemyState):InputFrame|null {
  const p=game.state.player,now=game.state.time;
  if(this.lastPosition&&now-this.lastWalkAt<.25){this.stuck=distance(p,this.lastPosition)<.015?this.stuck+dt:0;if(this.stuck>4)return null;if(this.stuck>1)this.replanAt=0;}else this.stuck=0;
  this.lastPosition={x:p.x,z:p.z};this.lastWalkAt=now;
  if(!this.routeGoal||distance(goal,this.routeGoal)>1||now>=this.replanAt||!this.route.length){this.route=enemy?enemyApproachPath(game,world,enemy):world.path?.(p,goal)??[];this.routeGoal={x:goal.x,z:goal.z};this.replanAt=now+.8;if(!this.route.length)return null;}
  while(this.route.length&&distance(p,this.route[0])<.18)this.route.shift();
  const next=this.route[0];if(!next)return still();
  const d=distance(p,next),amount=Math.min(1,d/(6.5*Math.max(.01,dt)));
  return {x:(next.x-p.x)/d*amount,z:(next.z-p.z)/d*amount};
 }
 private fail(message:string,stop=false):AutomationStep {if(stop)this.stop();else this.pause('blocked',message);return {input:still(),notice:message};}
 /** Null means arrived; crossing an exit retains the objective across scene rebuild. */
 private travel(game:GameSession,world:WorldQuery,areas:Record<string,AreaDef>,target:NavigationTarget,dt:number):AutomationStep|null {
  const s=game.state,p=s.player,exit=s.area!==target.area?availableRoute(game,areas,target.area)?.[0]:target.exitId?areas[s.area]?.exits.find(e=>e.id===target.exitId):undefined;
  if(s.area!==target.area&&!exit)return this.fail(tr('route.locked'));
  const requirement=exit&&game.exitRequirement(exit);if(requirement)return this.fail(requirement);
  const goal=exit??target.point;
  const object=target.objectId&&areas[s.area]?.objects.find(o=>o.id===target.objectId);
  if(distance(p,goal)<(exit?1.1:object?Math.min(.9,object.radius??1.35):.9)&&this.visible(world,p,goal)){
   if(exit){this.resetRoute();if(this.mode==='manual'&&s.area===target.area)this.stop();return {input:still(),travel:exit};}
   return null;
  }
  const frame=this.walk(game,world,goal,dt);return frame?{input:frame}:this.fail(tr('pause.blocked'));
 }
 private refreshObjective(game:GameSession,world:WorldQuery,areas:Record<string,AreaDef>){
  const now=game.state.time,old=JOURNEY_TASKS.find(t=>t.id===this.questTaskId);
  if(old&&game.journey.taskDone(old)){this.questTaskId=game.journey.currentTask(old.chapter)?.id;this.objectiveAt=0;this.interactionStarted=-1;this.enemyId='';}
  if(now<this.objectiveAt&&this.guidance)return;
  this.objectiveAt=now+.8;this.questChapter??=chapterForArea(game.state.area);
  let guide=journeyGuidance(game,areas,world,this.questTaskId,'task',this.questChapter);
  // A level gate does not destroy the task intent. Farm a reachable ground until
  // the gate opens, then the next bounded objective scan switches back.
  if(guide?.blocked&&availableRoute(game,areas,guide.destination.area)===null)guide=journeyGuidance(game,areas,world,undefined,'hunt',this.questChapter);
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
 /** Reuse the authored attack/zone geometry. Walking and dodging still obey
  * normal collision, action cancellation and the equipped dodge skill. */
 private evade(game:GameSession,world:WorldQuery):AutomationStep|null {
  const s=game.state,p=s.player,now=s.time;
  if(s.action?.kind==='dash')return {input:still()};
  if(now>=this.evadeUntil&&now>=this.evadeScanAt){
   this.evadeGoal=null;this.evadeScanAt=now+.15;
   const enemies=s.enemies.filter(e=>{const c=e.combat,step=c&&enemyProfile(e)?.attacks[c.moveId]?.steps[c.stepIndex];return e.hp>0&&distance(p,e)<18&&(e.phase==='active'||e.phase==='windup'&&(step?step.windup-(c?.stepElapsed??0)<=.35:e.phaseTime<=.35))&&this.visible(world,p,e);});
   const geometry=enemies.flatMap(e=>{const c=e.combat,step=c&&enemyProfile(e)?.attacks[c.moveId]?.steps[c.stepIndex];return step&&(step.baseDamage>0||step.projectile||step.zone)?c?.telegraphGeometry??c?.geometry??[]:[];});
   const hazards=s.enemyHazards.filter(h=>h.remaining>0&&h.maxTicks>0&&(h.damage>0||h.status)).flatMap(h=>h.geometry);
   const legacy=enemies.filter(e=>!e.combat&&distance(p,e)<4);
   const danger=(q:Point)=>geometry.some(g=>enemyContains(g,q))||hazards.some(g=>enemyContains(g,q))||s.fireZones.some(f=>distance(f,q)<f.radius+.4)||legacy.some(e=>distance(q,e)<(e.attackKind==='charge'?4:2.4)&&Math.cos(Math.atan2(q.x-e.x,q.z-e.z)-e.targetAngle)>.1);
   if(danger(p)){
    let score=-Infinity;
    for(let i=0;i<12;i++){
     const angle=i*Math.PI/6,q={x:p.x+Math.sin(angle)*3.2,z:p.z+Math.cos(angle)*3.2};
     if(danger(q)||!this.visible(world,p,q))continue;
     const value=Math.min(10,...enemies.map(e=>distance(q,e)));
     if(value>score){score=value;this.evadeGoal=q;}
    }
    if(this.evadeGoal){this.evadeUntil=now+.42;this.evadeDashed=false;this.resetRoute();}
   }
  }
  if(!this.evadeGoal||now>=this.evadeUntil)return null;
  const d=distance(p,this.evadeGoal);if(d<.25)return {input:still()};
  const dash=!this.evadeDashed&&(!s.action||s.action.elapsed>=.3)&&!!allocatedSkillRank(s.progression,'COM_01');
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
  if(this.destination){
   if(s.enemies.some(e=>e.hp>0&&distance(p,e)<8&&this.visible(world,p,e))){this.pauseNavigation(tr('navigation.threat'));return {input:still(),notice:this.status};}
   const target=this.destination;this.status=tr('navigation.travel',{target:target.label});
   const step=this.travel(game,world,areas,target,dt);if(step)return step;
   if(s.action)return {input:still()};
   this.stop();return {input:still(),interact:target.objectId,notice:tr('navigation.arrived',{target:target.label})};
  }
  if(!s.action&&p.hp/p.maxHp<=.45&&p.healthPotions>0&&!(s.cooldowns.consumable>0))game.useConsumable('health');
  if(this.mode==='idle'){this.huntArea||=s.area;if(this.huntArea!==s.area)return this.fail(tr('hunt.empty'),true);}
  const evade=this.evade(game,world);if(evade)return evade;
  const recovery=this.recover(game,world,areas,dt);if(recovery)return recovery;
  if(this.mode==='quest')this.refreshObjective(game,world,areas);
  const guide=this.guidance,target=guide?.destination,local=this.mode==='idle'||target?.area===s.area;
  const task=JOURNEY_TASKS.find(t=>t.id===target?.taskId);
  const scope:CombatScope=this.mode==='idle'?'hunt':!local?'travel':guide?.kind==='boss'||task?.goal==='clear'?'clear':guide?.kind==='hunt'||task?.goal==='hunt'?'hunt':'travel';
  const loot=this.collect(game,world,dt);if(loot)return loot;
  const combat=this.fight(game,world,dt,scope);if(combat)return combat;
  if(this.mode==='idle')return this.waitForHunt(game,world,areas,dt);
  if(!guide||!target)return this.fail(tr('task.missing'));
  if(!local){this.status=tr('task.travel',{target:target.label});return this.travel(game,world,areas,target,dt)??{input:still()};}
  if(guide.kind==='hunt'||task?.goal==='hunt')return this.waitForHunt(game,world,areas,dt);
  if(task?.goal==='observe'){
   const object=areas[s.area]?.objects.find(o=>o.action==='journey_task'&&o.eventId===task.id);
   if(!object)return this.fail(tr('task.failed'));
   this.status=tr('task.interact');const step=this.travel(game,world,areas,{...target,point:object},dt);if(step)return step;
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
  // A bow must be released through normal input after its charge, never held forever.
  if(s.action?.kind==='bowAim'){frame.attack=visible&&d<=reach&&s.action.elapsed<.85;return {input:frame};}
  if(visible&&!s.action){
   const resource=resourceProfile(s);
   if(p.hp/p.maxHp>.45&&p.focus/p.maxFocus<.2&&p[resource.stock]>0&&!(s.cooldowns.consumable>0))game.useConsumable('resource');
   // Decisions below inspect only equipped slots. Building every learned and
   // unlearned skill's description/readiness here repeats catalogue work in
   // every ordinary attack gap during continuous hunting.
   const equipped=s.combat.activeSlots.filter((id):id is string=>!!id);
   if(s.combat.ultimate)equipped.push(s.combat.ultimate);
   const views=game.combatSkillView(equipped);
   if(now>=this.nextSupportAt)for(let slot=0;slot<4;slot++){
    const id=s.combat.activeSlots[slot],rank=id&&allocatedSkillRank(s.progression,id);
    if(!id||!rank||COMBAT_SKILLS[id]?.offensive||!views.find(v=>v.id===id)?.ready)continue;
    const heal=rank.healMaxHpPercent>0&&p.hp/p.maxHp<.65&&!(s.combat.buffs.healCount>0);
    const shield=rank.shieldMaxHpPercent>0&&d<6&&p.shield<p.maxHp*.08;
    const ward=id==='THU_06'&&d<6&&(p.hp<p.maxHp*.8||enemy.phase==='windup'||enemy.phase==='active')&&(s.combat.buffs.stormWardUntil??0)<=now;
    const enchant=id==='THU_03'&&d<=profile.rangeMetres&&((s.combat.buffs.thunderCharges??0)<=0||(s.combat.buffs.thunderUntil??0)<=now);
    if(heal||shield||ward||enchant){frame.combatSlot=slot as 0|1|2|3;this.nextSupportAt=now+1.5;return {input:frame};}
   }
   const usable=(id:string|null)=>{
    if(!id||!COMBAT_SKILLS[id]?.offensive||!s.progression.learned[id]||!views.find(v=>v.id===id)?.ready)return false;
    const rank=allocatedSkillRank(s.progression,id);if(!rank)return false;
    if(id==='BOW_07'&&d>3.5)return false;
    if(id==='BOW_06'&&(d>5||enemy.kind==='archer'||s.combat.casts.some(c=>c.skillId===id&&(c.zoneUntil??0)>now)))return false;
    if(id==='FIR_04'&&enemy.kind==='archer'&&d>4)return false;
    const g=rank.geometry,self=COMBAT_SKILLS[id].targetingMode==='self';
    const range=self?g?.radiusMetres??rank.castRangeMetres:rank.castRangeMetres;
    return range>0&&d<=range+(g?.kind.startsWith('melee')?enemyHurtRadius(enemy):0)-.1;
   };
   if(now>=this.nextUltimateAt&&usable(s.combat.ultimate)){frame.ultimate=true;this.nextUltimateAt=now+8;return {input:frame};}
   if(now>=this.nextSkillAt)for(let i=0;i<4;i++){
    const slot=(this.skillIndex+i)%4,id=s.combat.activeSlots[slot];if(!usable(id))continue;
    if(id==='FIR_04'){const reach=Math.min(d*.55,4);frame.target={x:p.x+Math.sin(aim)*reach,z:p.z+Math.cos(aim)*reach};frame.aim=aim+Math.PI/2;}
    frame.combatSlot=slot as 0|1|2|3;this.skillIndex=(slot+1)%4;this.nextSkillAt=now+1.2;return {input:frame};
   }
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
