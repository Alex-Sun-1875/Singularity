import {economyReward} from '../../economy/common/EconomyRewards';
import {campaignExperienceQuote,campaignExperienceSources} from '../data/CampaignExperience';
import {equipmentSourceAllocation} from '../../equipment/data/CampaignEquipmentGrowth';

export interface CampaignMaterials {gold:number;iron:number;runes:number;cores:number;registered:boolean}

/** A single source owns one material share. Prefix allocation retains small
 * rune/core shares instead of rounding every individual reward down to zero. */
export function campaignSourceMaterials(source:string):CampaignMaterials {
 const entry=campaignExperienceQuote(source);
 if(!entry.registered)return {gold:0,iron:0,runes:0,cores:0,registered:false};
 const pool=campaignExperienceSources(entry.chapter).filter(value=>value.category===entry.category).sort((a,b)=>a.source.localeCompare(b.source));
 let before=0,total=0;
 for(const value of pool)total+=value.weight;
 // Use the same order as the reward catalog, including locale ordering.
 before=0;for(const value of pool){if(value.source===source)break;before+=value.weight;}
 return {...equipmentSourceAllocation(entry.chapter,entry.category==='main'?'story':'exploration',before,entry.weight,total),gold:economyReward(source)?.gold??0,registered:true};
}
