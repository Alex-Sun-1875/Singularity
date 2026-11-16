import type {GameState,EnemyState} from '../../../core/GameSession';

/** Only these original scene opponents respond to the old peaceful actions. */
const TARGETS:Record<string,{area:string;boss:string}>={
 's13-dismiss-overseer':{area:'S13',boss:'ELITE_01'},'h14-cancel-hunt':{area:'H14',boss:'ELITE_02'},
 'b14-return-contract':{area:'B14',boss:'ELITE_03'},'f17-release':{area:'F17',boss:'ELITE_04'},
 'u107-pressure':{area:'U1-07',boss:'ELITE_05'},'u203-pressure':{area:'U2-03',boss:'ELITE_07'},
 'u207-stop-mirrors':{area:'U2-07',boss:'ELITE_08'},
};
export const peacefulBossReceipt=(eventId:string,enemyId:string)=>`campaign:peaceful:${eventId}:${enemyId}`;
export function peacefulBossTarget(eventId:string,area:string,enemy:Pick<EnemyState,'bossId'>){const target=TARGETS[eventId];return !!target&&target.area===area&&target.boss===enemy.bossId;}
export function peacefulBossRetired(s:Pick<GameState,'area'|'enemies'|'encounters'|'receipts'>,enemyId:string):boolean {
 return Object.entries(TARGETS).some(([event,target])=>{if(s.receipts[peacefulBossReceipt(event,enemyId)]!==true||s.receipts['campaign:'+event]!==true)return false;return (s.area===target.area?s.enemies:s.encounters[target.area]??[]).some(e=>e.id===enemyId&&e.bossId===target.boss&&e.hp===0&&e.phase==='dead'&&e.diedAt===undefined&&s.receipts[`kill:${target.area}:${enemyId}`]!==true&&s.receipts[`boss:v3:${target.area}:${enemyId}:life`]===undefined);});
}
export function validatePeacefulBosses(s:GameState){for(const [key,value]of Object.entries(s.receipts))if(key.startsWith('campaign:peaceful:')){const rest=key.slice(18),event=Object.keys(TARGETS).find(id=>rest.startsWith(id+':')),id=event?rest.slice(event.length+1):'';if(!event||value!==true||!peacefulBossRetired(s,id))throw new Error('无效的首领和平处置记录');}}
