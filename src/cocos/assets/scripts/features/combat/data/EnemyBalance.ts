import type {EnemySpawn} from '../../../core/Contracts';

/** Fixed content-level durability. Player level and equipment never enter it. */
export const ENEMY_DURABILITY={boss:5,packElite:2.5,earlyPack:1.25,pack:.8,waveVeteran:1.35,waveSupport:.9,waveFiller:.85,waveMinimumBase:36,waveMinimumPerLevel:6} as const;
export function enemyHealthMultiplier(e:Pick<EnemySpawn,'bossId'|'packId'|'templateId'|'level'>):number {
 if(e.bossId)return ENEMY_DURABILITY.boss;
 if(!e.packId)return 1;
 if(e.templateId?.includes('ALPHA'))return ENEMY_DURABILITY.packElite;
 return (e.level??1)<=5?ENEMY_DURABILITY.earlyPack:ENEMY_DURABILITY.pack;
}
export function campaignWaveHealth(fullHp:number,level:number,kind:EnemySpawn['kind'],veteran:boolean,filler:boolean):number {
 const weight=veteran?ENEMY_DURABILITY.waveVeteran:kind==='archer'?ENEMY_DURABILITY.waveSupport:filler?ENEMY_DURABILITY.waveFiller:1;
 const minimum=(ENEMY_DURABILITY.waveMinimumBase+ENEMY_DURABILITY.waveMinimumPerLevel*level)*(veteran?ENEMY_DURABILITY.waveVeteran:1);
 return Math.round(Math.max(minimum,fullHp*weight));
}
