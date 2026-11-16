import type {EnemyState,GameState} from '../../../core/GameSession';
import {petAvailable} from './PetAccess';

export const PET_EFFECT_PREFIX='petfx:';
export type PetEffectKind='damage'|'reduction'|'resource'|'healing';
export function petEffectActive(s:GameState):boolean {
 return petAvailable(s)&&!!s.pets?.active&&s.receipts['petfx:owner']===s.pets.active&&s.player.hp>0&&s.status!=='dead';
}
export function petEffectPercent(s:GameState,kind:PetEffectKind,target?:EnemyState):number {
 if(!petEffectActive(s)||(s.combat.buffs[`petfx:${kind}Until`]??0)<=s.time)return 0;
 if(kind==='damage'&&s.receipts['petfx:target']&&(!target||s.receipts['petfx:target']!==`${s.area}/${target.id}`))return 0;
 return Math.max(0,Math.min(40,s.combat.buffs[`petfx:${kind}Percent`]??0));
}
export function clearPetSkillEffects(s:GameState):void {
 for(const key of Object.keys(s.combat.buffs))if(key.startsWith(PET_EFFECT_PREFIX))delete s.combat.buffs[key];
 delete s.receipts['petfx:owner'];delete s.receipts['petfx:target'];
}
