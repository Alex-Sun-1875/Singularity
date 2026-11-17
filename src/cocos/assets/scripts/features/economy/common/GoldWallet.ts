import type {GameState} from '../../../core/GameSession';
import {GOLD_CAPACITY,GOLD_PENDING_LIMIT} from '../data/Economy';

const PENDING='wallet:pending-gold';
export const pendingGold=(s:GameState)=>Number(s.receipts[PENDING]??0);
/** Callers own the real reward receipt. A full wallet never destroys a reward. */
export function creditGold(s:GameState,amount:number):number {
 if(!Number.isSafeInteger(amount)||amount<0||amount>GOLD_PENDING_LIMIT-pendingGold(s))throw new Error('无效的金币奖励');
 const received=Math.min(amount,GOLD_CAPACITY-s.player.gold),left=amount-received;
 s.player.gold+=received;if(left)s.receipts[PENDING]=pendingGold(s)+left;return received;
}
export function collectGold(s:GameState):number {
 const take=Math.min(pendingGold(s),GOLD_CAPACITY-s.player.gold);if(take<=0)return 0;
 s.player.gold+=take;s.receipts[PENDING]=pendingGold(s)-take;return take;
}
export function validateGoldWallet(s:GameState):void {
 const n=pendingGold(s);if(!Number.isSafeInteger(n)||n<0||n>GOLD_PENDING_LIMIT)throw new Error('无效的待领金币');
}
