import type {Point} from '../../../core/Contracts';
import type {CinematicMessageKey} from '../locales/zh-CN';
export type CampaignCue='dusk'|'beacon'|'alarm'|'crown'|'furnace'|'command'|'bells'|'quiet';
export interface CampaignBeat {speaker:CinematicMessageKey;text:CinematicMessageKey;seconds:number;focus?:Point;cue?:CampaignCue;turnArmy?:boolean}
export interface CampaignScene {id:string;chapter:1|2;area:string;title:CinematicMessageKey;focusActor?:string;at?:Point;radius?:number;trigger:'approach'|'victory'|'task';task?:string;boss?:string;beats:CampaignBeat[]}
export const beat=(speaker:CinematicMessageKey,text:CinematicMessageKey,seconds=5,extra:Partial<CampaignBeat>={}):CampaignBeat=>({speaker,text,seconds,...extra});
