import type {Point} from '../../../core/Contracts';

/** One clock for the approved two-turn pose, crescent meshes and real contacts. */
export const WHIRLWIND={windup:.18,segmentSeconds:.48,spinSeconds:.96,finishSeconds:.36,recoverySeconds:.36,baseRadius:2.15,fractions:[.28,.28,.44] as readonly number[]};
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const ease=(x:number)=>{const q=clamp(x);return q*q*(3-2*q);};
const delta=(x:number)=>Math.atan2(Math.sin(x),Math.cos(x));
export function whirlwindPose(elapsed:number,releaseAt=WHIRLWIND.windup){
 const age=elapsed-releaseAt;
 if(age<0){const q=ease(elapsed/Math.max(.001,releaseAt));return {turn:-Math.PI*.16*q,sourcePhase:.04+.22*q,age};}
 if(age<WHIRLWIND.spinSeconds){const s=ease(age/WHIRLWIND.spinSeconds);return {turn:-Math.PI*.16+(Math.PI*4+Math.PI*.16)*s,sourcePhase:.25+.30*(.5-.5*Math.cos(Math.PI*4*s)),age};}
 return {turn:Math.PI*4,sourcePhase:.25+.75*ease((age-WHIRLWIND.spinSeconds)/.34),age};
}
export function whirlwindFinisher(age:number,radius:number){
 const p=clamp((age-WHIRLWIND.spinSeconds)/WHIRLWIND.finishSeconds),scale=radius/WHIRLWIND.baseRadius;
 return {progress:p,offset:(.30+2.15*ease(p))*scale,radius:(1.48+.28*ease(p))*scale};
}
/** Sweep the visible sectors, including a coarse frame's intermediate poses.
 * Each target is still deduplicated by the combat cast's segment hit keys. */
export function whirlwindTouches(relative:Point,angle:number,previous:number,current:number,radius:number,hurtRadius:number,segment:number):boolean {
 const start=segment*WHIRLWIND.segmentSeconds,end=start+(segment<2?WHIRLWIND.segmentSeconds:WHIRLWIND.finishSeconds),lo=Math.max(previous,start,segment<2?.03:start),hi=Math.min(current,end);
 if(hi<lo)return false;
 const metres=Math.hypot(relative.x,relative.z),bearing=Math.atan2(relative.x,relative.z),padding=Math.asin(Math.min(1,hurtRadius/Math.max(.001,metres))),steps=Math.min(64,Math.max(1,Math.ceil((hi-lo)/.008)));
 for(let i=0;i<=steps;i++){
  const age=lo+(hi-lo)*i/steps;
  if(segment<2){
   const turn=whirlwindPose(age+WHIRLWIND.windup).turn,d=Math.abs(delta(bearing-angle-turn));
   if(metres<=radius+hurtRadius&&d<=1.15+padding)return true;
   if(age>.08&&metres<=radius*1.96/2.15+hurtRadius&&Math.abs(delta(bearing-angle-turn-Math.PI))<=1.025+padding)return true;
  }else{
   const finishAge=age-WHIRLWIND.spinSeconds;
   if(finishAge>=.07&&finishAge<=.15&&metres<=radius*.75+hurtRadius&&Math.abs(delta(bearing-angle))<=1.10+padding)return true;
   const wave=whirlwindFinisher(age,radius),x=relative.x-Math.sin(angle)*wave.offset,z=relative.z-Math.cos(angle)*wave.offset,d=Math.hypot(x,z),turn=Math.abs(delta(Math.atan2(x,z)-angle));
   if(d<=wave.radius+hurtRadius&&d>=wave.radius*.77-hurtRadius&&turn<=1.10+Math.asin(Math.min(1,hurtRadius/Math.max(.001,d))))return true;
  }
 }
 return false;
}
