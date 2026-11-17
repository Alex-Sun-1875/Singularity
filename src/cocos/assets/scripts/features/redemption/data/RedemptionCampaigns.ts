import type {GemTier} from '../../gems/data/Gems';
import type {SupplyId} from '../../equipment/data/Supplies';

/** Codes are explicit content bundles, independent of ordinary loot/shop policy. */
export type RedemptionReward=
 |{kind:'gold'|'iron'|'runes'|'cores'|'drills';amount:number}
 |{kind:'supply';item:SupplyId;amount:number}
 |{kind:'stone';tier:1|2|3|4|5;amount:number}
 |{kind:'equipment';item:string;amount:number};

/** Published IDs and reward versions remain stable across ordinary game updates. */
export const REDEMPTION_WEAPONS=['DG_L01','DG_L02','DG_L03','DG_L04'] as const;
export interface RedemptionCampaign {id:string;version:1;code:string;aliases:readonly string[];name:string;nameKey:'campaign.legend'|'campaign.gems3'|'campaign.gems4'|'campaign.gems5';weapon:boolean;gems:readonly {tier:GemTier;count:number}[];rewards?:readonly RedemptionReward[]}
export const REDEMPTION_CAMPAIGNS:readonly RedemptionCampaign[]=[
 {id:'sf-legend',version:1,code:'SFLEGEND',aliases:[],name:'传奇启程',nameKey:'campaign.legend',weapon:true,gems:[{tier:3,count:1}]},
 {id:'sf-gems3',version:1,code:'SFGEMS3',aliases:[],name:'晶辉珍藏',nameKey:'campaign.gems3',weapon:false,gems:[{tier:3,count:3}]},
 {id:'sf-gems4',version:1,code:'SFGEMS4',aliases:[],name:'星耀典藏',nameKey:'campaign.gems4',weapon:false,gems:[{tier:4,count:2}]},
 {id:'sf-gems5',version:1,code:'SFGEMS5',aliases:[],name:'巅峰珍礼',nameKey:'campaign.gems5',weapon:false,gems:[{tier:5,count:1}]},
];
export const REDEMPTION_RECORD_LIMIT=256;
export const normalizeRedemptionCode=(code:string)=>typeof code==='string'?code.trim().toUpperCase():'';
export function redemptionCampaign(code:string){const value=normalizeRedemptionCode(code);return /^[A-Z0-9]{1,13}$/.test(value)?REDEMPTION_CAMPAIGNS.find(c=>c.code===value||c.aliases.includes(value)):undefined;}
export const redemptionCampaignById=(id:string)=>REDEMPTION_CAMPAIGNS.find(c=>c.id===id);
export function redemptionGemChoices(c:RedemptionCampaign,compensation=false):GemTier[]{return [...(compensation?[4,4] as GemTier[]:[]),...c.gems.flatMap(g=>Array.from({length:g.count},()=>g.tier))];}
