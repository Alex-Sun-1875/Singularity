import type {EnemySpawn} from '../../../core/Contracts';
import {CAMPAIGN_PHASES,CAMPAIGN_MAX_LEVEL,combatBudgetLevel} from '../../progression/data/CampaignProgression';

/** Fixed authored-content budgets. Never depend on player level or equipment. */
export const ENEMY_DURABILITY={base:80,perLevel:30,quadratic:1.25,light:.85,heavy:1.25,elite:3,firstBoss:CAMPAIGN_PHASES[0].bossDurabilityMultiplier,mainBoss:CAMPAIGN_PHASES[1].bossDurabilityMultiplier,beastBoss:12,waveVeteran:1.2} as const;
type EnemyBudget=Pick<EnemySpawn,'kind'|'bossId'|'templateId'|'level'>;
const contentLevel=(level=1)=>Math.max(1,Math.min(CAMPAIGN_MAX_LEVEL,level));
export function ordinaryEnemyHealth(level=1):number {const n=combatBudgetLevel(contentLevel(level))-1;return ENEMY_DURABILITY.base+ENEMY_DURABILITY.perLevel*n+ENEMY_DURABILITY.quadratic*n*n;}
export function enemyHealthMultiplier(e:EnemyBudget):number {
 const id=e.bossId??e.templateId??'';
 if(id.startsWith('SIDE_C2_'))return Math.max(ENEMY_DURABILITY.beastBoss,(11000+300*Math.max(0,combatBudgetLevel(contentLevel(e.level))-12))/ordinaryEnemyHealth(e.level));
 if(/^BOSS_R[1-8]$/.test(id))return CAMPAIGN_PHASES[Number(id.slice(6))-1].bossDurabilityMultiplier;
 if(id.startsWith('ELITE_')||id.includes('ALPHA'))return ENEMY_DURABILITY.elite;
 if(e.bossId)return id==='BEAST_RIDGEBREAKER'?ENEMY_DURABILITY.beastBoss:ENEMY_DURABILITY.mainBoss;
 if(e.kind==='archer'||/SPITTER|SPIDER|SCARAB/.test(id))return ENEMY_DURABILITY.light;
 if(e.kind==='shield'||/IRON_HIDE|QUARRY_MAW|CINDER_CRAWLER/.test(id))return ENEMY_DURABILITY.heavy;
 return 1;
}
export const enemyContentHealth=(e:EnemyBudget)=>Math.round(ordinaryEnemyHealth(e.level)*enemyHealthMultiplier(e));
/** A veteran is a stronger member, not a second source of level growth. Other
 * reinforcements keep their ordinary archetype budget and attack damage. */
export function campaignWaveHealth(fullHp:number,_level:number,_kind:EnemySpawn['kind'],veteran:boolean,_filler:boolean):number {
 return Math.round(fullHp*(veteran?ENEMY_DURABILITY.waveVeteran:1));
}
/** Baseline damage rises with content level; the authored move's relative
 * strength, anticipation, hit count and element remain meaningful. */
export function enemyDamageMultiplier(e:Pick<EnemySpawn,'bossId'|'level'>):number {
 const n=combatBudgetLevel(contentLevel(e.level))-1,boss=e.bossId&&!e.bossId.startsWith('ELITE_');
 return (14+.75*n)/12*(boss?1.15:1);
}
/** Idempotent content refresh: preserve wounds and deaths, never grant a life. */
export function synchronizeEnemyHealth(e:{hp:number;maxHp:number},maxHp:number):boolean {
 if(e.maxHp===maxHp)return false;
 const fraction=e.maxHp>0?Math.max(0,Math.min(1,e.hp/e.maxHp)):0;
 e.hp=e.hp>0?Math.max(1,Math.min(maxHp,Math.round(fraction*maxHp))):0;e.maxHp=maxHp;return true;
}
