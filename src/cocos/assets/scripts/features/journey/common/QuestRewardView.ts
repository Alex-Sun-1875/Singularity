import type {CampaignEventDef} from '../../campaign/data/CampaignEvents';
import {MAIN_XP_EVENTS} from '../../campaign/data/Campaign';
import {campaignExperienceQuote} from '../../progression/data/CampaignExperience';
import {campaignSourceMaterials} from '../../progression/common/CampaignRewards';
import {chapterForArea} from '../data/ChapterJourney';
import type {GameState} from '../../../core/GameSession';

export interface QuestRewardAmounts {experience:number;gold:number;iron:number;runes:number;cores:number;}
export interface QuestRewardView {registered:QuestRewardAmounts;extra:QuestRewardAmounts;hasRegistered:boolean;hasExtra:boolean;hasBoss:boolean;cultivation:Record<number,{stones:number;gems:number}>;}
const empty=():QuestRewardAmounts=>({experience:0,gold:0,iron:0,runes:0,cores:0});
/** Presentation resolves the same source and fallback amounts as the award
 * entry point. Probability/route extras remain outside the finite source pool. */
export function questRewardView(events:readonly CampaignEventDef[],state?:Pick<GameState,'progression'>):QuestRewardView {
 const registered=empty(),extra=empty(),seen=new Set<string>(),cultivation:QuestRewardView['cultivation']={};let hasBoss=false;
 for(const event of events){
  hasBoss ||= !!event.requires?.some(flag=>flag.startsWith('boss_defeated:'));
  const source=event.experienceEvent??'campaign:'+event.id;if(seen.has(source))continue;seen.add(source);
  const raw=event.experienceEvent?MAIN_XP_EVENTS.find(entry=>entry.id===event.experienceEvent)?.experience??0:event.experience??0;
  const quote=campaignExperienceQuote(source,raw),materials=campaignSourceMaterials(source),destination=quote.registered?registered:extra;
  destination.experience+=state?.progression.xpReceipts[source]??quote.amount;
  const chapter=chapterForArea(event.area),gift=cultivation[chapter]??={stones:0,gems:0};gift.stones+=3;
  for(const field of ['gold','iron','runes','cores'] as const)destination[field]+=materials.registered?materials[field]:event[field]??0;
 }
 const positive=(value:QuestRewardAmounts)=>Object.values(value).some(amount=>amount>0);
 return {registered,extra,hasRegistered:positive(registered),hasExtra:positive(extra),hasBoss,cultivation};
}
