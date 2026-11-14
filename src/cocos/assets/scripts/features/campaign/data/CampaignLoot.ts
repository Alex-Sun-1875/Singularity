import {CAMPAIGN_EQUIPMENT,CAMPAIGN_LEVEL_LIST,CAMPAIGN_BOSSES} from './Campaign';
import {ITEM_STACK_LIMIT} from '../../equipment/data/Equipment';

export interface WeightedEquipment {id:string;weight:number}
export interface RegionLootDef {ordinaryGold:number;duplicateGold:number;outpostGold:number;eliteGold:number;ordinaryIron:number;outpostIron:number;eliteIron:number;equipmentChance:number;pityMisses:number}
export const REGIONAL_LOOT_POOLS:Record<string,WeightedEquipment[]>={};
for(const region of ['R1','R2','R3','R4','U1','U2'])REGIONAL_LOOT_POOLS[region]=CAMPAIGN_EQUIPMENT.filter(item=>item.id.startsWith(`D${region}-`)).map(item=>({id:item.id,weight:item.weight??0}));
export const REGION_LOOT:Record<string,RegionLootDef>=Object.fromEntries([
 ['R1',3,8,40,80],['R2',4,12,55,100],['R3',5,16,70,120],['R4',6,20,90,160],['U1',4,12,55,110],['U2',5,16,70,130],
].map(([id,ordinaryGold,duplicateGold,outpostGold,eliteGold])=>[id,{ordinaryGold:Number(ordinaryGold),duplicateGold:Number(duplicateGold),outpostGold:Number(outpostGold),eliteGold:Number(eliteGold),ordinaryIron:1,outpostIron:3,eliteIron:5,equipmentChance:.2,pityMisses:5}]));
export const OUTPOST_AREAS=CAMPAIGN_LEVEL_LIST.filter(area=>area.reward.includes('据点包')).map(area=>area.id);
export const ELITE_LOOT:Record<string,{eventId:string;bossId:string;item:string;region:string}>=Object.fromEntries(CAMPAIGN_BOSSES.filter(boss=>boss.id.startsWith('ELITE_')).map(boss=>[boss.arena!,{eventId:`V_E${boss.id.slice(-2)}`,bossId:boss.id,item:`DE${boss.id.slice(-2)}`,region:boss.region}]));
/** Only a completed, previously unclaimed death/event advances ordinary pity.
 * Outpost/elite pools are guaranteed draws and never advance/reset that counter.
 * At stack capacity, a duplicate converts to iron 2 + local gold.
 */
export const LOOT_POLICY={ordinaryPityScope:'region',equipmentPerId:ITEM_STACK_LIMIT,duplicateIron:2,ordinaryMissesBeforeGuarantee:5,guaranteedDrawChangesPity:false,peacefulUsesSameEventReceipt:true,retreatNeverCompletesEvent:true} as const;
