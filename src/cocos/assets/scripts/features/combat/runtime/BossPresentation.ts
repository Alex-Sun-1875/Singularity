import type {BossEntry} from '../common/BossDirectory';
import {bossClock} from '../common/BossDirectory';
import type {FeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {bossText as tr} from '../locales/bosses';

const portraits:Record<string,string>={BOSS_R1:'captain',BOSS_R2:'warden',ELITE_01:'overseer',ELITE_02:'huntmaster',ELITE_05:'golem',ELITE_06:'oath',BEAST_RIDGEBREAKER:'beast',BEAST_THORN_ALPHA:'alpha',BEAST_ASH_ALPHA:'alpha'};
export const bossPortrait=(row:BossEntry)=>'ui/boss-awareness/'+(portraits[row.spawn.bossId??row.spawn.templateId??'']??'boss-entry');
export function bossStatus(row:BossEntry):{primary:string;secondary:string;role:FeedbackRole}{
 const kind=tr(row.spawn.respawnSeconds?'wild':row.kind==='elite'?'elite':row.spawn.bossId==='BEAST_RIDGEBREAKER'?'optional':'boss');
 if(row.state==='cooldown')return {primary:bossClock(row.remaining),secondary:tr(row.spawn.respawnSeconds?'wildAfter':'after'),role:'text.secondary'};
 return {primary:tr(row.state==='alive'?'alive':row.state==='ready'?'ready':row.state==='waiting'?'waiting':'explore'),secondary:kind,role:row.state==='ready'||row.state==='alive'?'state.success':'text.secondary'};
}
