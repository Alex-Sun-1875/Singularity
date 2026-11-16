import type {EnemyCombatProfile} from './EnemyCombat';
import {combatText} from '../locales';

/** Reuse the installed shield/hammer poses and move executor. HP, attack damage,
 * first-clear XP and loot stay on the existing boss definitions. */
export function applyEarlyChapterBosses(profiles:Record<string,EnemyCombatProfile>){
 // Complete first-chapter templates use the same authoritative tell geometry
 // as later enemies. Actors without a content template retain the legacy path.
 for(const id of ['R1-1','R1-2','R1-3']){
  profiles[id].route='profile';
  profiles[id].source.adapterTuning.push('Use the existing authored normal-enemy profile, including anticipation, direction lock and geometry. The tutorial move stays interruptible; HP, damage, XP and loot are unchanged.');
 }
 const captain=profiles.BOSS_R1,warden=profiles.BOSS_R2;
 captain.route='profile';
 captain.recoveryDamageMultiplier=1.25;captain.staggerDamageMultiplier=1.35;
 warden.recoveryDamageMultiplier=1.25;warden.staggerDamageMultiplier=1.35;
 captain.attacks.charge.interruptible=false;
 captain.attacks.short.interruptible=false;
 warden.attacks['shield-rush'].interruptible=false;
 warden.attacks['shield-rush'].recovery=1.25;
 warden.attacks['shield-sweep']={
  id:'shield-sweep',label:combatText('boss.wardenSweep'),legacyKind:'short',pose:'attack_sword',minRange:0,maxRange:2.1,
  recovery:1.5,interruptible:true,
  steps:[{id:'sweep',windup:.9,lock:.3,active:.18,baseDamage:14,element:'physical',
   geometry:[{kind:'fan',origin:'caster',radiusMetres:1.8,angleDegrees:120}],
   maxHitsPerTarget:1,requiresLineOfSight:true,requiresSameLayer:true,targetTracking:'untilFinalLock'}],
 };
 warden.halfHealth={threshold:.5,once:false,queuedAttackId:'shield-sweep',followUpAfter:{'shield-rush':'shield-sweep'}};
 warden.cycle=['shield-rush','shield-sweep'];
 captain.source.adapterTuning.push('Early-chapter counterattack: recovery takes 25% more damage and stagger takes 35% more. Sweep remains interruptible; the original visibly anticipated straight charge and half-health follow-up are committed. Collision stagger, HP, damage, XP and loot are retained.');
 warden.source.adapterTuning.push('Early-chapter counterattack: committed shield rush retains its original anticipation and leaves 1.25s recovery. The interruptible 0.9s shield sweep deals 14 base damage and leaves 1.5s recovery; it alternates normally and follows the rush below half HP. Recovery takes 25% and stagger 35% more damage.');
}
