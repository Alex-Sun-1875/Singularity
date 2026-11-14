import type {AreaDef} from '../../../core/Contracts';
import {CHAPTER_1_SCENES} from './chapter-1';
import {CHAPTER_2_SCENES} from './chapter-2';
import {FIELD_QUEST_SCENES} from './FieldQuestScenes';
export type {CampaignBeat,CampaignCue,CampaignScene} from '../common/CinematicTypes';
export {CAMPAIGN_BATTLES,campaignBattle} from '../../campaign/data/CampaignBattles';
export const CAMPAIGN_SCENES=[...CHAPTER_1_SCENES,...CHAPTER_2_SCENES,...FIELD_QUEST_SCENES];
export const campaignScene=(id:string)=>CAMPAIGN_SCENES.find(s=>s.id===id);
export function installCampaignScenes(areas:Record<string,AreaDef>){
 for(const id of ['S01-T1','S01','H01']){const area=areas[id];area.objects.push({id:'campaign-hunt:'+id,action:'hunting_guide',label:'出发狩猎 · 怪物与战役',description:'镇内安全，怪物在野外；打开猎区路线。',x:area.spawn.x+3,z:area.spawn.z,radius:1.35});}
}
