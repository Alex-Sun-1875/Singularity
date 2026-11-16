import type {GameEvent} from '../../../core/Contracts';
import {damageFeedbackRole,type FeedbackRole} from '../../../shared/ui/FeedbackPalette';

export type ImpactKind='light'|'heavy'|'critical'|'armor'|'fire'|'lightning'|'kill'|'burn'|'evade'|'break'|'interrupt'|'stagger'|'counter'|'hurt'|'absorbed';
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
 evade:{kind:'evade',priority:8,hold:0,duration:.28,radius:14,kick:0,recoil:0,sound:'',volume:0,role:'state.success'},
 break:{kind:'break',priority:9,hold:0,duration:.3,radius:18,kick:.65,recoil:0,sound:'impact-heavy',volume:.55,role:'state.ready'},
 interrupt:{kind:'interrupt',priority:8,hold:0,duration:.25,radius:15,kick:.35,recoil:0,sound:'impact-armor',volume:.48,role:'status.control'},
 stagger:{kind:'stagger',priority:10,hold:0,duration:.34,radius:20,kick:.7,recoil:0,sound:'impact-heavy',volume:.6,role:'status.control'},
 counter:{kind:'counter',priority:8,hold:0,duration:.24,radius:17,kick:.8,recoil:0,sound:'impact-critical',volume:.55,role:'state.ready'},
 hurt:{kind:'hurt',priority:6,hold:0,duration:.16,radius:10,kick:0,recoil:0,sound:'hit',volume:.38,role:'damage.taken'},
 absorbed:{kind:'absorbed',priority:4,hold:0,duration:.18,radius:12,kick:0,recoil:0,sound:'impact-armor',volume:.36,role:'damage.absorbed'},
};
const HEAVY=new Set(['WAR_01','WAR_04','WAR_05','BOW_01','FIR_02','FIR_05']);
export const impactKey=(event:GameEvent)=>`${event.id??''}:${event.action??''}`;
/** Outcome cues never manufacture a stun, flinch or actor contact hold. */
export function combatOutcomeStyle(event:GameEvent):ImpactStyle|undefined {
 if(event.type==='evade'&&event.timing===true)return COMBAT_IMPACTS.evade;
 if(event.type==='guard_break')return COMBAT_IMPACTS.break;
 if(event.type==='interrupt')return COMBAT_IMPACTS.interrupt;
 if(event.type==='stagger')return COMBAT_IMPACTS.stagger;
 if(event.type==='counter_hit')return COMBAT_IMPACTS.counter;
 if(event.type==='hurt')return Number(event.hpLost)>0?COMBAT_IMPACTS.hurt:Number(event.absorbed)>0?COMBAT_IMPACTS.absorbed:undefined;
}
export function impactStyle(event:GameEvent,blocked=false):ImpactStyle|undefined {
 if(event.type==='block')return COMBAT_IMPACTS.armor;
 if(event.type!=='hit'||!(Number(event.hpLost)>0))return;
 const kind:ImpactKind=event.lethal===true?'kill':blocked?'armor':event.critical===true?'critical':event.source==='burn'||event.action==='burn'?'burn':event.comboStage===3||event.charged===true||HEAVY.has(String(event.skillId))?'heavy':event.element==='FIR'||event.element==='fire'?'fire':event.element==='THU'||event.element==='lightning'?'lightning':'light';
 const style=COMBAT_IMPACTS[kind];return kind==='critical'||kind==='kill'?{...style,role:damageFeedbackRole(String(event.element))}:style;
}
