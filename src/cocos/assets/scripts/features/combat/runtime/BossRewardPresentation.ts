import type {EnemyState} from '../../../core/GameSession';
import {BOSS_LOOT_POLICY,bossRewardKind} from '../../equipment/common/BossLoot';
import {encounterText as text} from '../../campaign/locales/ChapterTwoEncounterText';

const percent=(value:number)=>Number((value*100).toFixed(3));
export function randomBossRewardText(){
 return text('boss.randomRules')+'\n'+text('boss.randomRates',{epic:percent(BOSS_LOOT_POLICY.epic),legendary:percent(BOSS_LOOT_POLICY.legendary),artifact:percent(BOSS_LOOT_POLICY.artifact)})+'\n'+text('boss.randomPity',{epic:BOSS_LOOT_POLICY.epicPity,legendary:BOSS_LOOT_POLICY.legendaryPity});
}
export function bossRewardSummary(enemy:string|Pick<EnemyState,'bossId'>){
 const kind=bossRewardKind(enemy);
 return kind==='fixed'?text('boss.fixedShort'):kind==='random'?text('boss.randomShort'):'';
}
