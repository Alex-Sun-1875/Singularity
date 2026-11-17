import type {GameState} from '../../../core/GameSession';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import {GEM_STATS,GEM_POLICY,type GemStat,type GemTier} from '../../gems/data/Gems';
import {grantRedemptionGems} from '../../gems/common/GemWorkshop';
import {creditGold} from '../../economy/common/GoldWallet';
import {SUPPLIES} from '../../equipment/data/Supplies';
import {materialStock} from '../../crafting/common/CultivationRewards';
import {REDEMPTION_WEAPONS,REDEMPTION_RECORD_LIMIT,redemptionCampaign,redemptionGemChoices,type RedemptionCampaign} from '../data/RedemptionCampaigns';
import {redemptionText as t} from '../locales';
import {freshRedemption,redemptionOwned,redemptionSource,type RedemptionGem,type RedemptionRecord,type RedemptionRecordView} from './RedemptionLedger';
export * from './RedemptionLedger';
export interface RedemptionSelection {weapon?:string;gems:GemStat[]}
export interface RedemptionQuote {allowed:boolean;reason:string;token:string;campaign?:RedemptionCampaign;weaponOptions:{id:string;name:string;available:boolean;reason:string}[];gemChoices:GemTier[];compensation:boolean;resolved?:{weapon?:string;gems:RedemptionGem[]};record?:RedemptionRecord}
export interface RedemptionHost {state():GameState;availability():{available:boolean;reason:string};prepareWeapon(next:GameState,id:string,source:string,amount?:number):boolean;commit(next:GameState):boolean}
const copy=<T>(v:T):T=>JSON.parse(JSON.stringify(v));
export class Redemption {
 constructor(private host:RedemptionHost){}
 lookup(code:string){return redemptionCampaign(code);}
 records():RedemptionRecordView[]{const s=this.host.state();return (s.redemption?.records??[]).map(r=>({...copy(r),remaining:copy(s.gems.pendingSources?.[r.grantId]??{})}));}
 quote(code:string,selection:RedemptionSelection):RedemptionQuote {
  const s=this.host.state(),campaign=this.lookup(code),weaponOptions=REDEMPTION_WEAPONS.map(id=>({id,name:EQUIPMENT[id].name,available:!redemptionOwned(s,id),reason:redemptionOwned(s,id)?t('reason.owned'):''})),compensation=!!campaign?.weapon&&weaponOptions.every(v=>!v.available),gemChoices=campaign?redemptionGemChoices(campaign,compensation):[],record=s.redemption?.records.find(r=>r.campaignId===campaign?.id);
  const q:RedemptionQuote={allowed:false,reason:'',token:JSON.stringify([s.seed,s.sequence,s.revision,s.redemption?.revision??0,s.gems.version,s.gems.revision,campaign?.id??'',campaign?.version??0,weaponOptions.map(v=>v.available),[selection?.weapon??null,selection?.gems??[]]]),campaign,weaponOptions,gemChoices,compensation,...(record?{record:copy(record)}:{})};
  if(!campaign){q.reason=t('reason.invalid');return q;}if(record){q.reason=t('reason.claimed');return q;}
  const access=this.host.availability();if(!access.available){q.reason=access.reason||t('reason.busy');return q;}
  if((s.redemption?.records.length??0)>=REDEMPTION_RECORD_LIMIT||s.gems.transactions.length>=GEM_POLICY.ledgerLimit||s.sequence>=Number.MAX_SAFE_INTEGER-2){q.reason=t('reason.limit');return q;}
  if(!selection||!Array.isArray(selection.gems)||selection.gems.length!==gemChoices.length||selection.gems.some(stat=>!GEM_STATS.includes(stat))||campaign.weapon&&!compensation&&!weaponOptions.some(v=>v.id===selection.weapon&&v.available)||(!campaign.weapon||compensation)&&selection.weapon!==undefined){q.reason=t('reason.selection');return q;}
  q.resolved={...(campaign.weapon&&!compensation?{weapon:selection.weapon}:{}),gems:selection.gems.map((stat,i)=>({stat,tier:gemChoices[i],units:5}))};
  try {const next=copy(s),r=this.prepare(next,q);if(!r){q.reason=t('reason.full');return q;}q.allowed=true;}catch{q.reason=t('reason.full');}return q;
 }
 private prepare(next:GameState,q:RedemptionQuote){
  if(!q.campaign||!q.resolved)return;next.redemption??=freshRedemption();
  const grantId=`redemption:${++next.sequence}`,gemRequest=`gem-redeem:${++next.sequence}`,r:RedemptionRecord={campaignId:q.campaign.id,rewardVersion:q.campaign.version,grantId,gemRequest,...(q.resolved.weapon?{weapon:q.resolved.weapon}:{}),compensation:q.compensation,gems:copy(q.resolved.gems),received:{},pending:{}};
  if(q.campaign.rewards?.length)r.rewards=copy(Array.from(q.campaign.rewards));
  // Gem validation resolves this exact record; allocations are filled on the disposable copy.
  next.redemption.records.push(r);next.redemption.revision++;next.receipts[grantId]=r.campaignId;
  if(!grantRedemptionGems(next,r))return;
  if(r.weapon&&!this.host.prepareWeapon(next,r.weapon,redemptionSource(r)))return;
  for(const reward of r.rewards??[]){
   if(!Number.isSafeInteger(reward.amount)||reward.amount<=0||reward.amount>1e8)return;
   if(reward.kind==='gold')creditGold(next,reward.amount);
   else if(reward.kind==='equipment'){if(!this.host.prepareWeapon(next,reward.item,redemptionSource(r),reward.amount))return;}
   else if(reward.kind==='supply'){const def=SUPPLIES[reward.item];if(!def||next.player[def.stock]+reward.amount>def.capacity)return;next.player[def.stock]+=reward.amount;}
   else if(reward.kind==='stone'){if(materialStock(next,reward.tier)>1e8)return;}
   else if(reward.kind!=='drills'){if(next.player[reward.kind]+reward.amount>9999)return;next.player[reward.kind]+=reward.amount;}
  }
  return r;
 }
 claim(code:string,selection:RedemptionSelection,token:string){const q=this.quote(code,selection);if(!q.allowed||token!==q.token)return false;try{const next=copy(this.host.state());if(!this.prepare(next,q))return false;return this.host.commit(next);}catch{return false;}}
}
export {Redemption as Redemptions};
