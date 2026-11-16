import type {ItemDef} from '../data/Equipment';
import {equipmentText as text} from '../locales';
import type {EquipmentMessageKey} from '../locales/zh-CN';

/** Narrative identity is separate from effect text and from acquisition rules. */
const NAMED_STORIES:Record<string,EquipmentMessageKey>={
 W06:'story.uncrownedOath',W14:'story.skyRift',L01:'story.stormTestament',L02:'story.astraLetter',
 DG_L01:'story.lastWatch',DG_L02:'story.moonString',DG_L03:'story.longCandle',DG_L04:'story.beforeRain',DG_L05:'story.lateReturn',DG_L06:'story.reverseClock',
 DG_A01:'story.royalDusk',DG_A02:'story.secondDawn',DG_A03:'story.royalStars',DG_A04:'story.royalEmbers',DG_A05:'story.royalThunder',
 SQ_DAWN_NECKLACE:'story.watcherMemory',
};
const STAGE_STORIES:Record<string,EquipmentMessageKey>={
 '1T':'story.borderOath','1B':'story.duskHunt','2T':'story.mountainOath','2B':'story.bridgeBreak',
 '3T':'story.sunkenBell','3B':'story.riverBreak','4T':'story.sleeplessOath','4B':'story.throneJudgment',
 '5T':'story.cityPact','5B':'story.brokenBanner','6T':'story.wallEmbers','6B':'story.blackCrownOrder',
 '7T':'story.longWatch','7B':'story.winglessDawn','8T':'story.dawnOath','8B':'story.nightEnd',
};
const SHARED_LEGEND_SOURCE:Record<string,EquipmentMessageKey>={
 DG_L01:'source.borderLegend',DG_L02:'source.moonString',DG_L04:'source.beforeRain',
 DG_L03:'source.longCandle',DG_L05:'source.lateReturn',DG_L06:'source.reverseClock',
};

/** Display current routes without changing catalogs, drop pools or save proofs. */
export function equipmentStory(item:ItemDef):{lore:string;source:string}{
 const stage=/^LC([1-8])_([TB])_/.exec(item.lifecycleGroup??''),story=NAMED_STORIES[item.id]??(stage?STAGE_STORIES[stage[1]+stage[2]]:undefined);
 const lore=story?text(story):'';
 if(item.id==='DG_A01')return {lore,source:text('source.royalDusk')};
 if(item.id.startsWith('DG_A'))return {lore,source:text('source.artifactPool')};
 const legend=SHARED_LEGEND_SOURCE[item.id];if(legend)return {lore,source:text(legend)};
 if(item.id==='SQ_DAWN_NECKLACE')return {lore,source:text('source.chapterRandom',{chapter:1})};
 if(stage)return {lore,source:text(stage[2]==='T'?'source.chapterMainBoss':'source.chapterRandom',{chapter:Number(stage[1])})};
 if(item.id==='W06')return {lore,source:text('source.uncrownedOath')};
 if(item.id==='W14')return {lore,source:text('source.skyRift')};
 if(item.id==='L01'||item.id==='L02')return {lore,source:text('source.oldLegend')};
 return {lore,source:item.source??''};
}
