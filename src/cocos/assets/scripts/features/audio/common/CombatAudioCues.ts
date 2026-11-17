import type {GameEvent} from '../../../core/Contracts';

export type AudioFamily='WAR'|'BOW'|'FIR'|'THU';
/** Release-only air cues. Combat contacts deliberately have no audio route. */
export const COMBAT_AUDIO_CUES={
 war_swing:{family:'WAR',duration:.26},bow_release:{family:'BOW',duration:.22},
 fir_release:{family:'FIR',duration:.36},thu_release:{family:'THU',duration:.30},
} as const;
export type CombatAudioCue=keyof typeof COMBAT_AUDIO_CUES;
export interface CombatAudioRequest {cue:CombatAudioCue;volume:number;priority:number;limit?:number}
export const AUDIO_FAMILIES:readonly AudioFamily[]=['WAR','BOW','FIR','THU'];
export const combatAudioPath=(cue:CombatAudioCue,variation:number)=>`audio/combat-v12/${COMBAT_AUDIO_CUES[cue].family.toLowerCase()}/${cue}_v${variation}`;
export const RELEASE_AUDIO:Readonly<Record<AudioFamily,{cue:CombatAudioCue;volume:number}>>={
 WAR:{cue:'war_swing',volume:.62},BOW:{cue:'bow_release',volume:.64},
 FIR:{cue:'fir_release',volume:.40},THU:{cue:'thu_release',volume:.40},
};

export function audioFamily(value:unknown):AudioFamily|undefined {
 if(typeof value!=='string')return;
 const key=value.toUpperCase();
 if(key==='FIRE')return 'FIR';if(key==='LIGHTNING')return 'THU';
 return AUDIO_FAMILIES.find(f=>key===f||key.startsWith(f+'_'));
}
/** Released projectiles and skills retain their own weapon/element identity. */
export function eventAudioFamily(event:GameEvent,fallback:AudioFamily):AudioFamily {
 return audioFamily(event.family)??audioFamily(event.skillId)??audioFamily(event.element)??audioFamily(event.source)??fallback;
}
