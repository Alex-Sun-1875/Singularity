import type {GameEvent} from '../../../core/Contracts';
import {damageFeedbackRole,type FeedbackRole} from '../../../shared/ui/FeedbackPalette';

export type ImpactKind='light'|'heavy'|'critical'|'armor'|'fire'|'lightning'|'kill'|'burn';
export interface ImpactStyle {kind:ImpactKind;priority:number;hold:number;duration:number;radius:number;kick:number;recoil:number;sound:string;volume:number;role:FeedbackRole}
/** Logical pixels, seconds and presentation strength; never damage or stun rules. */
export const COMBAT_IMPACTS:Readonly<Record<ImpactKind,ImpactStyle>>={
 light:{kind:'light',priority:1,hold:.032,duration:.13,radius:10,kick:.65,recoil:.13,sound:'impact-flesh',volume:.52,role:'damage.physical'},
 heavy:{kind:'heavy',priority:5,hold:.048,duration:.18,radius:15,kick:1.3,recoil:.2,sound:'impact-heavy',volume:.58,role:'damage.physical'},
 critical:{kind:'critical',priority:6,hold:.06,duration:.2,radius:17,kick:1.8,recoil:.22,sound:'impact-critical',volume:.6,role:'damage.critical'},
 armor:{kind:'armor',priority:3,hold:.022,duration:.14,radius:11,kick:.35,recoil:.045,sound:'impact-armor',volume:.45,role:'impact.metal'},
 fire:{kind:'fire',priority:4,hold:.018,duration:.17,radius:13,kick:.45,recoil:.08,sound:'impact-fire',volume:.43,role:'damage.fire'},
 lightning:{kind:'lightning',priority:4,hold:.025,duration:.15,radius:14,kick:.65,recoil:.09,sound:'impact-lightning',volume:.42,role:'damage.lightning'},
 kill:{kind:'kill',priority:7,hold:.065,duration:.23,radius:19,kick:2,recoil:.24,sound:'impact-kill',volume:.6,role:'damage.critical'},
 burn:{kind:'burn',priority:0,hold:0,duration:.09,radius:4,kick:0,recoil:0,sound:'',volume:0,role:'damage.fire'},
};
const HEAVY=new Set(['WAR_01','WAR_04','WAR_05','BOW_01','FIR_02','FIR_05']);
export const impactKey=(event:GameEvent)=>`${event.id??''}:${event.action??''}`;
export function impactStyle(event:GameEvent,blocked=false):ImpactStyle|undefined {
 if(event.type==='block')return COMBAT_IMPACTS.armor;
 if(event.type!=='hit'||!(Number(event.hpLost)>0))return;
 const kind:ImpactKind=event.lethal===true?'kill':blocked?'armor':event.critical===true?'critical':event.source==='burn'||event.action==='burn'?'burn':event.comboStage===3||event.charged===true||HEAVY.has(String(event.skillId))?'heavy':event.element==='FIR'||event.element==='fire'?'fire':event.element==='THU'||event.element==='lightning'?'lightning':'light';
 const style=COMBAT_IMPACTS[kind];return kind==='critical'||kind==='kill'?{...style,role:damageFeedbackRole(String(event.element))}:style;
}
