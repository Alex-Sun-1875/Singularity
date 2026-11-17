import type {GameState} from '../../../core/GameSession';
import {GEM_STATS,type GemStat,type GemTier} from '../../gems/data/Gems';
import {REDEMPTION_WEAPONS,REDEMPTION_RECORD_LIMIT,redemptionCampaignById,redemptionGemChoices,type RedemptionReward} from '../data/RedemptionCampaigns';
import {redemptionText} from '../locales';

export interface RedemptionGem {stat:GemStat;tier:GemTier;units:number}
export interface RedemptionRecord {campaignId:string;rewardVersion:1;grantId:string;gemRequest:string;weapon?:string;compensation:boolean;gems:RedemptionGem[];received:Record<string,number>;pending:Record<string,number>;rewards?:RedemptionReward[]}
export interface RedemptionState {version:1;revision:number;records:RedemptionRecord[]}
export interface RedemptionRecordView extends RedemptionRecord {remaining:Record<string,number>}
export const freshRedemption=():RedemptionState=>({version:1,revision:0,records:[]});
export const freshRedemptions=freshRedemption;
export const redemptionSource=(r:RedemptionRecord)=>`redeem:${r.campaignId}:${r.grantId}`;
export const redemptionOwned=(s:GameState,id:string)=>!!s.inventory[id]||s.receipts[`growing-owned:${id}`]!==undefined||s.groundLoot.some(d=>d.item===id);
const object=(v:unknown):v is Record<string,any>=>!!v&&typeof v==='object'&&!Array.isArray(v)&&Object.getPrototypeOf(v)===Object.prototype;
const keys=(v:object,wanted:string[])=>Object.keys(v).sort().join()===wanted.slice().sort().join();
const positive=(v:unknown,max=1e8):v is number=>typeof v==='number'&&Number.isSafeInteger(v)&&v>0&&v<=max;
function validReward(v:unknown):v is RedemptionReward {
 if(!object(v)||!positive(v.amount))return false;
 if(v.kind==='stone')return keys(v,['kind','tier','amount'])&&[1,2,3,4,5].includes(v.tier);
 if(v.kind==='equipment'||v.kind==='supply')return keys(v,['kind','item','amount'])&&typeof v.item==='string';
 return ['gold','iron','runes','cores','drills'].includes(v.kind)&&keys(v,['kind','amount']);
}
export function redemptionGemBank(gems:readonly RedemptionGem[]){const bank:Record<string,number>={};for(const g of gems){const key=`${g.stat}:${g.tier}`;bank[key]=(bank[key]??0)+g.units;}return bank;}
export function validRedemptionRecord(r:unknown):r is RedemptionRecord {
 if(!object(r)||!keys(r,['campaignId','rewardVersion','grantId','gemRequest','compensation','gems','received','pending',...('weapon' in r?['weapon']:[]),...('rewards' in r?['rewards']:[])])||r.rewardVersion!==1||typeof r.campaignId!=='string'||typeof r.grantId!=='string'||!/^redemption:[1-9]\d*$/.test(r.grantId)||typeof r.gemRequest!=='string'||!/^gem-redeem:[1-9]\d*$/.test(r.gemRequest)||typeof r.compensation!=='boolean'||!Array.isArray(r.gems)||!object(r.received)||!object(r.pending))return false;
 const c=redemptionCampaignById(r.campaignId);if(!c||c.version!==r.rewardVersion||r.compensation&&!c.weapon||c.weapon&&!r.compensation&&!REDEMPTION_WEAPONS.includes(r.weapon as any)||(!c.weapon||r.compensation)&&r.weapon!==undefined)return false;
 if(JSON.stringify(r.rewards??[])!==JSON.stringify(c.rewards??[])||!Array.isArray(r.rewards??[])||(r.rewards??[]).some((v:unknown)=>!validReward(v)))return false;
 const tiers=redemptionGemChoices(c,r.compensation);if(r.gems.length!==tiers.length||r.gems.some((g:unknown,i:number)=>!object(g)||!keys(g,['stat','tier','units'])||!GEM_STATS.includes(g.stat)||g.tier!==tiers[i]||g.units!==5))return false;
 const expected=redemptionGemBank(r.gems),all=new Set([...Object.keys(r.received),...Object.keys(r.pending)]);
 return Object.keys(expected).every(k=>(r.received[k]??0)+(r.pending[k]??0)===expected[k])&&Array.from(all).every(k=>expected[k]!==undefined&&(!Object.prototype.hasOwnProperty.call(r.received,k)||positive(r.received[k]))&&(!Object.prototype.hasOwnProperty.call(r.pending,k)||positive(r.pending[k])));
}
export function redemptionRecordBySource(s:GameState,source:string){return s.redemption?.records.find(r=>redemptionSource(r)===source&&validRedemptionRecord(r));}
export function validRedemptionEquipmentSource(s:GameState,id:string,source:string):boolean {const r=redemptionRecordBySource(s,source);return !!r&&!!(r.weapon===id||r.rewards?.some(v=>v.kind==='equipment'&&v.item===id))&&s.receipts[r.grantId]===r.campaignId&&s.receipts[`grant:${source}:${id}`]===true;}
export function redemptionStoneBalance(s:GameState,tier:number):number {return (s.redemption?.records??[]).reduce((sum,r)=>sum+(r.rewards??[]).reduce((n,v)=>n+(v.kind==='stone'&&v.tier===tier?v.amount:0),0),0);}
export function redemptionEquipmentSourceLabel(s:GameState,id:string):string|undefined {const source=s.provenance[id];if(typeof source!=='string'||!validRedemptionEquipmentSource(s,id,source))return;const r=redemptionRecordBySource(s,source)!;return redemptionText('source',{name:redemptionText(redemptionCampaignById(r.campaignId)!.nameKey)});}
export function validateRedemption(s:GameState){
 const fail=():never=>{throw new Error('无效的兑换礼包记录');},r=s.redemption,receiptKeys=Object.keys(s.receipts).filter(k=>k.startsWith('redemption:'));
 if(r===undefined){if(receiptKeys.length||Object.values(s.provenance).some(v=>v.startsWith('redeem:'))||s.gems.transactions.some(t=>t.kind==='redeem'))fail();return;}
 if(!object(r)||!keys(r,['version','revision','records'])||r.version!==1||!Array.isArray(r.records)||r.records.length>REDEMPTION_RECORD_LIMIT||r.revision!==r.records.length)return fail();
 const campaigns=new Set<string>(),requests=new Set<string>();let sequence=0;
 for(const record of r.records){
  if(!validRedemptionRecord(record))return fail();const n=Number(record.grantId.split(':')[1]),m=Number(record.gemRequest.split(':')[1]);
  if(!positive(n,s.sequence)||!positive(m,s.sequence)||n<=sequence||m!==n+1||campaigns.has(record.campaignId)||requests.has(record.grantId)||s.receipts[record.grantId]!==record.campaignId)return fail();sequence=m;campaigns.add(record.campaignId);requests.add(record.grantId);
  if(record.weapon&&(s.inventory[record.weapon]!==1||s.provenance[record.weapon]!==redemptionSource(record)||!validRedemptionEquipmentSource(s,record.weapon,redemptionSource(record))))return fail();
  if(record.compensation&&!REDEMPTION_WEAPONS.every(id=>redemptionOwned(s,id)))return fail();
  for(const reward of record.rewards??[])if(reward.kind==='equipment'&&(!s.inventory[reward.item]||s.receipts[`grant:${redemptionSource(record)}:${reward.item}`]!==true))return fail();
  const events=s.gems.transactions.filter(t=>t.request===record.gemRequest);if(events.length!==1||events[0].kind!=='redeem'||events[0].source!==redemptionSource(record))return fail();
 }
 if(receiptKeys.length!==requests.size||receiptKeys.some(k=>!requests.has(k)))return fail();
}
export const validateRedemptions=validateRedemption;
