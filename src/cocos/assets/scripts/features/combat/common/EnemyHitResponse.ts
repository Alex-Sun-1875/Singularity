import type {Point} from '../../../core/Contracts';
import type {EnemyState,GameState} from '../../../core/GameSession';
import {enemyCanInterrupt,enemyHurtRadius,enemyProfile} from './EnemyCombat';

type Impact={enemy:EnemyState;start:number;duration:number;distance:number;applied:number;angle:number;flinch:boolean;resisted:boolean};
interface Host {state():GameState;move(enemy:EnemyState,delta:Point,radius:number):void;shift(enemy:EnemyState,delta:Point):void;height(point:Point):number;emit(type:string,text?:string,extra?:Record<string,unknown>):void}
/** Short collision-clipped impulses. Durable positions stay in the existing save;
 * in-flight motion is discarded on travel/reload, never replayed for more damage. */
export class EnemyHitResponse {
 private impacts=new Map<string,Impact>();
 private basicProtection=new Map<string,{enemy:EnemyState;until:number}>();
 constructor(private host:Host){}
 reset(){this.impacts.clear();this.basicProtection.clear();}
 hit(enemy:EnemyState,action:string,source:string,angle:number){
  if(!Number.isFinite(angle)||['burn','environment','secondary','relic','push'].includes(source))return;
  const s=this.host.state(),previous=this.impacts.get(enemy.id);if(previous?.enemy===enemy&&s.time<previous.start+.32)return;
  const cast=s.combat.casts.find(c=>c.id===action);
  const basic=!cast,committed=enemy.phase==='active'||enemy.phase==='windup'&&enemy.combat?.locked===true;
  const profile=enemyProfile(enemy),boss=!!enemy.bossId||enemy.kind==='captain',fixed=profile?.movement.stationary||profile?.solidBody||profile?.policy.hitReactionMovesEnemy===false||cast?.skillId==='BOW_06'||cast?.skillId==='FIR_04'||cast?.skillId==='FIR_05'||(s.combat.buffs[`rootUntil:${enemy.id}`]??0)>s.time;
  const armored=enemy.kind==='shield'||profile?.body==='machine'||!!profile?.defense,braced=!enemyCanInterrupt(enemy)&&['windup','active'].includes(enemy.phase);
  const projectile=s.projectiles.find(q=>q.id===action),heavy=['WAR_01','WAR_04','WAR_05','BOW_01','FIR_02','FIR_05'].includes(cast?.skillId??'')||!!projectile?.charged;
  const base=heavy?.52:source==='spell'?.24:.32,scale=fixed?0:boss?.16:armored?.48:1;
  const protection=this.basicProtection.get(enemy.id),protectedBasic=basic&&protection?.enemy===enemy&&protection.until>s.time;
  // Ordinary contact has a short, bounded recoil. It cannot delay or displace a
  // locked attack; authored skill interruption remains in PureCombat's poise rules.
  const distance=basic&&(committed||protectedBasic)?0:base*scale*(braced?.25:1),flinch=!boss&&!fixed&&!braced&&!committed&&!protectedBasic&&enemy.phase!=='stagger';
  if(basic&&flinch)this.basicProtection.set(enemy.id,{enemy,until:s.time+.65});
  const impact:Impact={enemy,start:s.time,duration:.16,distance,applied:0,angle,flinch,resisted:!!(fixed||boss||armored||braced)};
  this.impacts.set(enemy.id,impact);this.host.emit('enemy_recoil',undefined,{id:enemy.id,action,angle,distance,duration:impact.duration,resisted:impact.resisted,lethal:enemy.hp<=0,at:{x:enemy.x,z:enemy.z}});
 }
 view(id:string){const impact=this.impacts.get(id);if(!impact)return;const progress=(this.host.state().time-impact.start)/impact.duration;if(progress<0||progress>=1)return;return {progress,angle:impact.angle,flinch:impact.flinch,resisted:impact.resisted,distance:impact.distance};}
 step(enemy:EnemyState,dt:number){
  const impact=this.impacts.get(enemy.id);if(!impact)return false;
  if(impact.enemy!==enemy){this.impacts.delete(enemy.id);return false;}
  const age=this.host.state().time-impact.start;if(age>=.32){this.impacts.delete(enemy.id);return false;}
  if((this.host.state().combat.buffs[`rootUntil:${enemy.id}`]??0)>this.host.state().time)impact.applied=impact.distance;
  const t=Math.max(0,Math.min(1,age/impact.duration)),desired=impact.distance*(1-(1-t)*(1-t)),length=Math.max(0,desired-impact.applied);
  if(length>0){const before={x:enemy.x,z:enemy.z};this.host.move(enemy,{x:Math.sin(impact.angle)*length,z:Math.cos(impact.angle)*length},Math.max(.35,enemyHurtRadius(enemy)));
   if(Math.abs(this.host.height(enemy)-this.host.height(before))>.6){enemy.x=before.x;enemy.z=before.z;}
   const delta={x:enemy.x-before.x,z:enemy.z-before.z};this.host.shift(enemy,delta);impact.applied=desired;
   if(Math.hypot(delta.x,delta.z)<length*.2)impact.applied=impact.distance;
  }
  return impact.flinch&&age<.12;
 }
}
