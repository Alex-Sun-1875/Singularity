import type {EnemyState,GameState} from '../../../core/GameSession';
import {petBonuses} from './PetSystem';
import {petAvailable} from './PetAccess';
import {petEffectPercent} from './PetSkillEffects';

/** Apply after the ordinary hit calculation so a small percentage remains a
 * real benefit at low character levels instead of rounding away every hit. */
export function petOutgoingDamage(s:GameState,base:number,target?:EnemyState):number {
 return base*(1+(petBonuses(s,target).damagePercent+petEffectPercent(s,'damage',target))/100);
}
/** Separate from the equipment reduction cap: armored builds still benefit. */
export function petIncomingDamage(s:GameState,base:number):number {
 return Math.max(1,base*(1-petBonuses(s).damageReductionPercent/100)*(1-petEffectPercent(s,'reduction')/100));
}
export function petMaxHealth(s:GameState,base:number):number {
 return Math.round(base*(1+petBonuses(s).maxHpPercent/100));
}
export function petResourceRecovery(s:GameState,base:number):number {
 return base*(1+(petBonuses(s).resourceRegenPercent+petEffectPercent(s,'resource'))/100);
}
/** Shared by potions, skill recovery and equipment healing. Full restoration
 * at a checkpoint and level-up HP are not healing effects. */
export function restorePlayerHealth(s:GameState,base:number):number {
 const p=s.player;
 if(p.hp<=0||!Number.isFinite(base)||base<=0)return 0;
 const amount=Math.min(p.maxHp-p.hp,base*(1+(petBonuses(s).healingReceivedPercent+petEffectPercent(s,'healing'))/100));
 if(amount>0&&petAvailable(s)&&s.pets?.active){const b=s.combat.buffs,ratio=p.hp/p.maxHp;b['petfx:healBeforeRatio']=b['petfx:healAt']===s.time?Math.min(b['petfx:healBeforeRatio']??1,ratio):ratio;b['petfx:healAt']=s.time;}
 p.hp+=amount;return amount;
}
