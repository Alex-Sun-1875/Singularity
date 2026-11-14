import type {EnemyCombatProfile} from './EnemyCombat';
import {combatText} from '../locales';

/** Reuse the installed shield/hammer poses and move executor. HP, attack damage,
 * first-clear XP and loot stay on the existing boss definitions. */
export function applyEarlyChapterBosses(profiles:Record<string,EnemyCombatProfile>){
 const captain=profiles.BOSS_R1,warden=profiles.BOSS_R2;
 captain.recoveryDamageMultiplier=1.1;
 warden.recoveryDamageMultiplier=1.1;
 warden.attacks['shield-rush'].recovery=1.25;
 warden.attacks['shield-sweep']={
  id:'shield-sweep',label:combatText('boss.wardenSweep'),legacyKind:'short',pose:'attack_sword',minRange:0,maxRange:2.1,
  recovery:1.5,interruptible:true,
  steps:[{id:'sweep',windup:.9,lock:.3,active:.18,baseDamage:14,element:'physical',
   geometry:[{kind:'fan',origin:'caster',radiusMetres:1.8,angleDegrees:120}],
   maxHitsPerTarget:1,requiresLineOfSight:true,requiresSameLayer:true,targetTracking:'untilFinalLock'}],
 };
 warden.halfHealth={threshold:.5,once:false,queuedAttackId:'shield-sweep',followUpAfter:{'shield-rush':'shield-sweep'}};
 captain.source.adapterTuning.push('Early-chapter counterattack: recovery/stagger takes 10% more damage; original HP, damage, XP and loot are retained.');
 warden.source.adapterTuning.push('Early-chapter counterattack: 1.25s rush recovery; below half HP a separately telegraphed 0.9s shield sweep deals 14 base damage and leaves 1.5s recovery. Openings take 10% more damage.');
}
