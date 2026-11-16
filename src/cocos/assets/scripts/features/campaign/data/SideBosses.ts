import type {AreaDef,Point} from '../../../core/Contracts';
import {CAMPAIGN_ENEMY_TEMPLATES} from './Campaign';
import {sideBossText} from '../locales/SideBossText';

export const SIDE_BOSS_FORGE='SIDE_C2_FORGE';
export const SIDE_BOSS_ORDERS='SIDE_C2_ORDERS';
export const SIDE_BOSS_BRIDGE='SIDE_C2_BRIDGE';
export interface SideBossDefinition {
 bossId:string;enemyId:string;area:string;level:number;chapter:2;questId:string;
 evidenceEventId:string;evidencePoint:Point;point:Point;rematchPoint?:Point;templateId:string;
 portrait:'golem'|'oath'|'captain';name:string;firstClearExperience:number;
}
/** Encounter identity is independent of the existing profile and art it reuses. */
export const SIDE_BOSSES:readonly SideBossDefinition[]=[
 {bossId:SIDE_BOSS_FORGE,enemyId:'side-boss-forge',area:'H05',level:12,chapter:2,questId:'side-forge',evidenceEventId:'side-forge-boss',evidencePoint:{x:20,z:-16},point:{x:8,z:14},templateId:'ELITE_05',portrait:'golem',name:sideBossText('forge.name'),firstClearExperience:500},
 {bossId:SIDE_BOSS_ORDERS,enemyId:'side-boss-orders',area:'U1-09',level:15,chapter:2,questId:'side-orders',evidenceEventId:'side-orders-boss',evidencePoint:{x:18,z:-18},point:{x:0,z:-2},templateId:'ELITE_06',portrait:'oath',name:sideBossText('orders.name'),firstClearExperience:650},
 {bossId:SIDE_BOSS_BRIDGE,enemyId:'side-boss-bridge',area:'H07',level:17,chapter:2,questId:'side-bridge',evidenceEventId:'side-bridge-boss',evidencePoint:{x:20,z:-24},point:{x:20,z:10},rematchPoint:{x:-3,z:-40},templateId:'BOSS_R1',portrait:'captain',name:sideBossText('bridge.name'),firstClearExperience:800},
];
export const sideBossForQuest=(id:string)=>SIDE_BOSSES.find(b=>b.questId===id);
export const sideBossById=(id:string)=>SIDE_BOSSES.find(b=>b.bossId===id||b.enemyId===id);
export const sideBossForEvent=(id:string)=>SIDE_BOSSES.find(b=>b.evidenceEventId===id);

/** Always installed with the world, never gated on accepting or finishing a quest. */
export function installSideBosses(areas:Record<string,AreaDef>){
 for(const boss of SIDE_BOSSES){
  const area=areas[boss.area],base=CAMPAIGN_ENEMY_TEMPLATES[boss.templateId];
  if(!area||!base)throw new Error('Missing side boss content: '+boss.bossId);
  const {fixedLoot:_fixed,rewardEvent:_event,...profile}=base;
  CAMPAIGN_ENEMY_TEMPLATES[boss.bossId]={...profile,id:boss.bossId,name:boss.name,arena:boss.area,region:boss.area.startsWith('H')?'R2':'U1',level:boss.level,mandatory:false,firstClearExperience:boss.firstClearExperience,runtimeStatus:'implemented-reusing-existing-combat-and-art'};
  area.enemies.push({id:boss.enemyId,bossId:boss.bossId,templateId:boss.templateId,contentId:boss.bossId,kind:boss.templateId==='BOSS_R1'?'captain':'shield',level:boss.level,...boss.point});
 }
}
/** The outpost's +3m default entrance sits in its gorge, so use the dry bank. */
export function placeSideBossRematches(areas:Record<string,AreaDef>){
 for(const boss of SIDE_BOSSES){
  if(!boss.rematchPoint)continue;
  const entry=areas[boss.area].objects.find(o=>o.action==='growing_rematch'&&o.eventId===boss.enemyId);
  if(entry)Object.assign(entry,boss.rematchPoint);
 }
}
