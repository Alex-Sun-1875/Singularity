import {campaignBattle} from './CampaignBattles';

export type ChapterTwoEncounterId='quarry-rescue'|'ridge-post'|'oath-array';
export type ChapterTwoActionId='quarry-survey'|'quarry-witness'|'quarry-ledger'|'ridge-parley'|'ridge-alarm'|'ridge-battle'|'oath-read'|'oath-north'|'oath-west'|'oath-east'|'oath-battle';
export interface ChapterTwoAction {id:ChapterTwoActionId;encounter:ChapterTwoEncounterId;area:string;point:{x:number;z:number};method:'investigate'|'rescue'|'negotiate'|'sabotage'|'battle'|'mechanism'}
export const CHAPTER_TWO_ENCOUNTERS=[
 {id:'quarry-rescue',area:'H04',taskId:'highland-hunt',text:'quarry'},
 {id:'ridge-post',area:'H07',taskId:'highland-ridge',text:'ridge'},
 {id:'oath-array',area:'U1-06',taskId:'highland-oath',text:'oath'},
] as const;
export const CHAPTER_TWO_ACTIONS:readonly ChapterTwoAction[]=[
 {id:'quarry-survey',encounter:'quarry-rescue',area:'H04',point:{x:-18,z:-24},method:'investigate'},
 {id:'quarry-witness',encounter:'quarry-rescue',area:'H04',point:{x:-22,z:-20},method:'rescue'},
 {id:'quarry-ledger',encounter:'quarry-rescue',area:'H04',point:{x:-12,z:-26},method:'rescue'},
 {id:'ridge-parley',encounter:'ridge-post',area:'H07',point:{x:-24,z:-20},method:'negotiate'},
 {id:'ridge-alarm',encounter:'ridge-post',area:'H07',point:{x:-38,z:-18},method:'sabotage'},
 {id:'ridge-battle',encounter:'ridge-post',area:'H07',point:{x:-12,z:-24},method:'battle'},
 {id:'oath-read',encounter:'oath-array',area:'U1-06',point:{x:-14,z:-30},method:'investigate'},
 {id:'oath-north',encounter:'oath-array',area:'U1-06',point:{x:0,z:-20},method:'mechanism'},
 {id:'oath-west',encounter:'oath-array',area:'U1-06',point:{x:-20,z:-28},method:'mechanism'},
 {id:'oath-east',encounter:'oath-array',area:'U1-06',point:{x:20,z:-28},method:'mechanism'},
 {id:'oath-battle',encounter:'oath-array',area:'U1-06',point:{x:12,z:-24},method:'battle'},
];
export const chapterTwoAction=(id:string)=>CHAPTER_TWO_ACTIONS.find(action=>action.id===id);
export const chapterTwoEventId=(id:ChapterTwoActionId)=>'c2-'+id;
/** Content IDs identify this encounter's guards; wildlife is never withdrawn. */
export const RIDGE_FIXED_IDS=['campaign-H07-R2-2-1','campaign-H07-R2-1-2','campaign-H07-R2-4-3'] as const;
export const RIDGE_ALARM_IDS=['campaign-H07-R2-2-1','campaign-H07-R2-4-3'] as const;
export const OATH_INITIAL_IDS=['campaign-U1-06-ELITE_06-1'] as const;
export const OATH_FIXED_IDS:readonly string[]=[...OATH_INITIAL_IDS,...(campaignBattle('U1-06')?.waves.flatMap(wave=>wave.enemies.map(enemy=>enemy.id))??[])];
export const OATH_SEQUENCE:readonly ChapterTwoActionId[]=['oath-north','oath-west','oath-east'];
