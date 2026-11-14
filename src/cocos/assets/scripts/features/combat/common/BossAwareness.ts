import type {EnemyState,GameSession} from '../../../core/GameSession';
import {CAMPAIGN_ENEMY_TEMPLATES} from '../../campaign/data/Campaign';
import {enemyProfile} from './EnemyCombat';
import {trainingText} from '../../debug/locales';

export const BOSS_NOTICE_RANGE=48;
export type BossKind='boss'|'elite';
export function bossKind(enemy:Pick<EnemyState,'bossId'|'templateId'|'kind'>):BossKind|null {
 const id=enemy.bossId??enemy.templateId??'';
 if(id.startsWith('ELITE_'))return 'elite';
 return enemy.bossId||enemy.kind==='captain'?'boss':null;
}
// All world labels resolve the same authored identity, including training targets.
export const enemyDisplayName=(enemy:EnemyState)=>enemy.trainingDummy?trainingText('target'):enemy.trainingEnemy?trainingText('monster.'+enemy.kind):CAMPAIGN_ENEMY_TEMPLATES[enemy.bossId??enemy.templateId??enemy.contentId??'']?.name??enemyProfile(enemy)?.name??(bossKind(enemy)==='elite'?'精英守卫':enemy.kind==='captain'?'灰披队长':'游荡敌人');
export const bossName=enemyDisplayName;
/** A presentation-only radar contact. Never wakes enemies or reveals terrain. */
export function nearestBoss(game:GameSession,range=BOSS_NOTICE_RANGE):EnemyState|undefined {
 const s=game.state;if(s.status==='dead'||s.player.hp<=0)return;
 let nearest:EnemyState|undefined,best=Infinity;
 for(const enemy of s.enemies){const kind=bossKind(enemy);if(enemy.hp<=0||!kind)continue;const distance=Math.hypot(enemy.x-s.player.x,enemy.z-s.player.z);if(distance>range)continue;
  const score=distance+(kind==='elite'?range+1:0);if(score<best){nearest=enemy;best=score;}
 }
 return nearest;
}
