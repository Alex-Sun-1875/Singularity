import type {ActionState,GameSession} from '../../../core/GameSession';
import type {CombatCast} from '../../combat/common/PureCombat';
import {combatActionBeatCount,combatSegmentInterval} from '../../combat/common/CombatActionTiming';
import {COMBAT_SKILLS} from '../../combat/data/PureSkills';
import type {Vec3} from 'cc';

type Clip={frames?:number;frameIndices?:number[];phaseStarts?:number[]};
export type PlayerActionPhase='prepare'|'raise'|'aim'|'rush'|'release'|'rearm'|'channel'|'recover'|'settle'|'dodge';
export type PlayerActionSample={phase:PlayerActionPhase;ordinal:number;progress:number;beat:number;beats:number;releaseAt:number;lift:number;settle:boolean;rushRun:boolean};
export type PlayerPresentation={actionId?:string;phase?:PlayerActionPhase;beat:number;facing:number;hand:Vec3;castHand?:Vec3;pose:string;ordinal:number};
const clamp=(n:number)=>Math.max(0,Math.min(1,n));

/** Reach the authored recoil promptly, then play its recovery before returning
 * to the current action clock. This is presentation, not a new rule stun. */
export function playerHurtProgress(hurtTime:number):number|undefined {
 const elapsed=.45-hurtTime;
 if(hurtTime<=0||elapsed<0||elapsed>=.22)return undefined;
 return elapsed<.04?elapsed/.04*.48:elapsed<.09?.48+(elapsed-.04)/.05*.10:.58+(elapsed-.09)/.13*.419;
}

export type WeaponReadiness={area?:string;ready:boolean;until:number};
/** Shared 2D/native presentation rule: facing alone never draws a weapon. */
export function updateWeaponReadiness(carry:WeaponReadiness,game:GameSession,world:{height:(p:{x:number;z:number})=>number;visible:(a:{x:number;z:number},b:{x:number;z:number})=>boolean}):boolean {
 const s=game.state,p=s.player;
 if(carry.area!==s.area){carry.area=s.area;carry.ready=false;carry.until=-Infinity;}
 const height=world.height(p),visibleThreat=(target:{x:number;z:number})=>Math.hypot(target.x-p.x,target.z-p.z)<=7&&Math.abs(world.height(target)-height)<1.2&&world.visible(p,target);
 const threat=p.hurtTime>0||!!s.action&&s.action.kind!=='dash'||s.enemies.some(enemy=>enemy.hp>0&&visibleThreat(enemy))||s.projectiles.some(projectile=>projectile.owner==='enemy'&&projectile.remaining>0&&visibleThreat(projectile));
 if(threat)carry.until=s.time+2;
 // An exploration dodge stays stowed; a combat dodge keeps its entry state.
 return carry.ready=threat||s.time<carry.until||s.action?.kind==='dash'&&carry.ready;
}

export function playerActionPose(action:ActionState,weapon:'sword'|'staff'|'bow'):string {
 const skill=COMBAT_SKILLS[action.skillId??''];
 if(action.kind==='dash'||skill?.id==='COM_01')return 'dodge';
 if(action.kind==='bowAim'||action.kind==='bow')return 'attack_bow';
 if(action.kind==='staff')return 'attack_staff';
 if(action.kind==='sword')return 'attack_sword';
 if(action.kind==='push')return 'interact';
 if(skill){
  if(skill.style==='WAR'&&skill.offensive)return 'attack_sword';
  if(skill.style==='BOW'&&skill.id!=='BOW_04')return 'attack_bow';
  // Use the existing raised-staff/release/recover drawings, preserving the
  // equipped staff through elemental, protection and healing gestures.
  return weapon==='staff'?'attack_staff':'spell';
 }
 if(action.kind.startsWith('spell:'))return weapon==='staff'?'attack_staff':'spell';
 return action.kind==='skill'?'attack_'+weapon:'attack_sword';
}

export function actionReleaseAt(action:ActionState):number {
 if(action.skillId)return action.releaseAt??COMBAT_SKILLS[action.skillId]?.windupSeconds??.25;
 if(action.kind==='sword')return action.releaseAt??.12;
 if(action.kind==='push')return .10;
 if(action.kind==='staff')return .20;
 if(action.kind==='bow')return action.charged?0:.12;
 if(action.kind==='dash')return .04;
 return .25;
}

/** The quad renderer samples its existing authored key poses on the same
 * action clock as the rules. No independent animation timer can outrun a hit. */
export function samplePlayerAction(action:ActionState,pose:string,clip:Clip,cast?:CombatCast,bowChargeSeconds=.8):PlayerActionSample {
 const count=clip.frameIndices?.length??clip.frames??1,releaseOrdinal=Math.min(pose==='spell'||pose==='interact'?1:2,count-1),raised=Math.max(0,releaseOrdinal-1),recovered=count-1;
 const releaseAt=actionReleaseAt(action),def=COMBAT_SKILLS[action.skillId??''],rank=cast?.rank??def?.ranks[Math.max(0,(action.rank??1)-1)];
 const beats=def?combatActionBeatCount(def,rank):1,interval=def?combatSegmentInterval(def.id,rank):.16;
 let phase:PlayerActionPhase='prepare',ordinal=0,beat=0,lift=0,settle=false,rushRun=false;
 if(pose==='dodge'){
  const t=clamp(action.elapsed/Math.max(.001,action.duration));phase='dodge';ordinal=Math.min(count-1,Math.floor(t*count));
 }else if(action.kind==='bowAim'){
  lift=clamp(action.elapsed/bowChargeSeconds);phase='aim';ordinal=lift<.12?0:raised;
 }else {
  const flagsRelease=!!action.skillId||['staff','bow','skill'].includes(action.kind)||action.kind.startsWith('spell:');
  const released=action.elapsed+1e-8>=releaseAt&&(!flagsRelease||action.emitted);
  if(!released){
   const t=clamp(action.elapsed/Math.max(.001,releaseAt));lift=t;
   phase=t<.18?'prepare':'raise';ordinal=t<.18?0:raised;
   if(action.kind==='bow')ordinal=raised; // continue the held draw into release
   if(cast?.rush&&action.emitted&&cast.rush.elapsed<cast.rush.duration){
    phase='rush';lift=1;ordinal=raised;rushRun=cast.rush.elapsed/cast.rush.duration<.72;
   }
  }else {
   const elapsed=Math.max(0,action.elapsed-releaseAt),scheduled=Math.min(beats-1,Math.floor((elapsed+1e-8)/interval));
   beat=cast?Math.min(scheduled,Math.max(0,cast.nextSegment-1)):scheduled;
   const within=Math.max(0,elapsed-beat*interval);
   if(beat<beats-1){
    const t=clamp(within/interval),channel=def?.style==='THU';
    phase=channel?'channel':t<.42?'release':'rearm';ordinal=channel||t<.42?releaseOrdinal:raised;lift=channel||t<.42?1:.8;
   }else {
    const recovery=Math.max(.001,action.duration-releaseAt-(beats-1)*interval),t=clamp(within/recovery);
    const contact=action.kind==='sword'?Math.min(.4,.1/recovery):.28;
    phase=t<contact?'release':t<.88?'recover':'settle';ordinal=t<contact?releaseOrdinal:recovered;lift=1-clamp((t-contact)/Math.max(.001,1-contact));settle=phase==='settle';
   }
  }
 }
 const start=clip.phaseStarts?.[ordinal]??ordinal/count,next=clip.phaseStarts?.[ordinal+1]??(ordinal+1)/count;
 return {phase,ordinal,progress:start+(next-start)*.025,beat,beats,releaseAt,lift,settle,rushRun};
}
