import type {EnemyCombatProfile,EnemyAttackDef} from './EnemyCombat';
import {SIDE_BOSSES,SIDE_BOSS_FORGE,SIDE_BOSS_ORDERS,SIDE_BOSS_BRIDGE} from '../../campaign/data/SideBosses';
import {sideBossCombatText as text} from '../locales/SideBossCombatText';

const copy=<T>(value:T):T=>JSON.parse(JSON.stringify(value));
/** Uses existing move geometry, lock-on, collision, stagger and cooldown executors.
 * Enemy HP and reward tuning remain owned by the encounter/balance definitions. */
export function installSideBossCombat(profiles:Record<string,EnemyCombatProfile>){
 const create=(id:string,template:string)=>{
  const profile=copy(profiles[template]),boss=SIDE_BOSSES.find(b=>b.bossId===id)!;
  profile.id=id;profile.name=boss.name;profile.route='profile';profile.attackSlotCost=2;
  profile.recoveryDamageMultiplier=1.25;profile.staggerDamageMultiplier=1.35;
  profile.policy.idleBetweenMoves=.35;
  profile.source.adapterTuning.push('Independent optional-boss tactics: 25% recovery and 35% stagger openings; HP, damage scaling, first-victory and rematch loot stay on their existing owners.');
  profiles[id]=profile;return profile;
 };
 const charge=(id:string,label:string,distance:number,windup:number,recovery:number,cooldown:number):EnemyAttackDef=>{
  const move=copy(profiles.BOSS_R1.attacks.charge);move.id=id;move.label=label;
  move.minRange=3.5;move.maxRange=12;move.cooldown=cooldown;move.recovery=recovery;move.interruptible=false;
  const step=move.steps[0];step.windup=windup;step.lock=.35;step.active=.65;
  step.selfMove={mode:'charge',distance,duration:.65,collisionStops:true,collisionStaggerSeconds:1.8};
  return move;
 };

 const forge=create(SIDE_BOSS_FORGE,'ELITE_05');
 forge.attacks['double-hammer'].interruptible=true;
 forge.attacks['double-hammer'].recovery=1.7;
 forge.attacks['pressure-ring'].interruptible=false;
 forge.attacks['pressure-ring'].recovery=1.8;
 forge.attacks['overload-hammer'].interruptible=false;
 forge.attacks['reclaim-rush']=charge('reclaim-rush',text('cargoRush'),7.5,1.15,1.6,7);
 forge.cycle=['double-hammer','pressure-ring','reclaim-rush'];
 forge.source.adapterTuning.push('Hammer: 1.4s anticipation / final 0.4s lock, interruptible. Gapped ring: 1.6s / 0.5s lock, committed. Straight 7.5m rush: 1.15s / 0.35s lock, 7s cooldown; collision leaves 1.8s stagger.');

 const orders=create(SIDE_BOSS_ORDERS,'ELITE_06');
 orders.attacks['three-blades'].interruptible=false;
 orders.attacks['three-blades'].recovery=2;
 orders.attacks['oath-cut'].interruptible=true;
 orders.attacks['oath-cut'].recovery=1.8;
 orders.source.adapterTuning.push('Committed three-cut combo retains separate 0.9/0.85/1.1s anticipation and final 0.3/0.3/0.35s direction locks, then a 2s opening. The 12m pursuit cut remains interruptible and has its existing 7s cooldown.');

 const bridge=create(SIDE_BOSS_BRIDGE,'BOSS_R1');
 bridge.attacks.charge=charge('charge',bridge.attacks.charge.label,6.5,1.05,1.6,6);
 bridge.attacks.sweep.interruptible=true;bridge.attacks.sweep.recovery=1.4;
 bridge.attacks.short.interruptible=false;bridge.attacks.short.recovery=1.5;
 bridge.source.adapterTuning.push('Front shield retains its authored arc. Shield rush: 1.05s anticipation / final 0.35s lock, 6.5m straight movement and 6s cooldown; collision exposes 1.8s stagger. Sweep remains interruptible; the separately telegraphed half-health follow-up is committed.');
}
