import type {GameEvent} from '../../../core/Contracts';

export type AudioFamily='WAR'|'BOW'|'FIR'|'THU';
/** Individual contact cues, never the multi-action audition demonstrations. */
export const COMBAT_AUDIO_CUES={
 war_swing:{family:'WAR',duration:.26},war_slash:{family:'WAR',duration:.40},
 war_armor:{family:'WAR',duration:.48},war_finish:{family:'WAR',duration:.56},
 bow_draw:{family:'BOW',duration:.62},bow_release:{family:'BOW',duration:.30},
 bow_pierce:{family:'BOW',duration:.30},bow_heavy:{family:'BOW',duration:.42},bow_armor:{family:'BOW',duration:.30},
 fir_charge:{family:'FIR',duration:.72},fir_burst:{family:'FIR',duration:1.05},fir_wall:{family:'FIR',duration:3.00},
 thu_charge:{family:'THU',duration:.60},thu_crack:{family:'THU',duration:.80},thu_network:{family:'THU',duration:1.45},
} as const;
export type CombatAudioCue=keyof typeof COMBAT_AUDIO_CUES;
export interface CombatAudioRequest {cue:CombatAudioCue;volume:number;priority:number;limit?:number}
export const AUDIO_FAMILIES:readonly AudioFamily[]=['WAR','BOW','FIR','THU'];
export const combatAudioPath=(cue:CombatAudioCue,variation:number)=>`audio/combat-v9/${COMBAT_AUDIO_CUES[cue].family.toLowerCase()}/${cue}_v${variation}`;

export function audioFamily(value:unknown):AudioFamily|undefined {
 if(typeof value!=='string')return;
 const key=value.toUpperCase();
 if(key==='FIRE')return 'FIR';if(key==='LIGHTNING')return 'THU';
 return AUDIO_FAMILIES.find(f=>key===f||key.startsWith(f+'_'));
}
/** Snapshot fields win over the current loadout when an old projectile lands. */
export function eventAudioFamily(event:GameEvent,fallback:AudioFamily):AudioFamily {
 return audioFamily(event.family)??audioFamily(event.skillId)??audioFamily(event.element)??audioFamily(event.source)??fallback;
}
export function preparationCue(family:AudioFamily):CombatAudioCue|undefined {
 return family==='BOW'?'bow_draw':family==='FIR'?'fir_charge':family==='THU'?'thu_charge':undefined;
}
const HEAVY_SKILLS=new Set(['WAR_01','WAR_04','WAR_05','BOW_01','BOW_05']);
export function contactAudioRequest(event:GameEvent,family:AudioFamily,blocked=false):CombatAudioRequest|undefined {
 if(event.type!=='block'&&(event.type!=='hit'||!(Number(event.hpLost)>0)))return;
 if(event.owner!==undefined&&event.owner!=='player')return;
 // The placed wall gets one successful skill_zone flame bed. Its periodic
 // contacts never add burst explosions, including the first slow/contact tick.
 if(['burn','environment','pet','secondary','relic','relicPhysical'].includes(String(event.source))||event.action==='burn'||event.skillId==='FIR_04')return;
 const material=String(event.material??'').toLowerCase(),armor=blocked||event.type==='block'||['armor','metal','machine'].includes(material);
 const heavy=event.charged===true||event.comboStage===3||HEAVY_SKILLS.has(String(event.skillId));
 const result=event.lethal===true?1.12:event.critical===true?1.07:1;
 const priority=event.lethal===true?5:event.critical===true?4:3;
 if(family==='WAR')return {cue:armor?'war_armor':heavy||event.lethal===true?'war_finish':'war_slash',volume:(armor ? .64 : .68)*result,priority};
 if(family==='BOW')return {cue:armor?'bow_armor':heavy||event.lethal===true?'bow_heavy':'bow_pierce',volume:(armor ? .68 : .72)*result,priority};
 if(family==='FIR')return {cue:'fir_burst',volume:.58*result,priority};
 const network=['THU_02','THU_04','THU_05'].includes(String(event.skillId));
 return {cue:network?'thu_network':'thu_crack',volume:(network ? .49 : .60)*result,priority};
}
