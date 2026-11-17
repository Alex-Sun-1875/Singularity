import {Vec3} from 'cc';
import type {Point} from '../../../core/Contracts';
import type {SkillVfxHost} from './NativeSkillVfx';
import {THUNDER_COLORS} from './SkillEnergyStrokes';

const TAU=Math.PI*2;
const clamp=(value:number,min=0,max=1)=>Math.max(min,Math.min(max,value));
const local=(p:Point,a:number,side:number,forward:number):Point=>({x:p.x+Math.cos(a)*side+Math.sin(a)*forward,z:p.z-Math.sin(a)*side+Math.cos(a)*forward});

/** Reuse the approved white-core strip without treating decorative curves as
 * target-to-target connections. No targeting or gameplay events live here. */
function energy(host:SkillVfxHost,key:string,points:Vec3[],width:number,alpha:number){
 if(points.length<2||alpha<=0)return;
 if(host.thunderBeam)host.thunderBeam(key,points,width,Math.round(alpha),'accent');
 else host.line(points,THUNDER_COLORS.core,width*.22,Math.round(alpha),true,'core');
}

/** The three live charges cling to the actual animated palm / weapon grip.
 * They are small electrical strokes, never three floating attack beams. */
export function drawThunderCharge(host:SkillVfxHost,key:string,hand:Vec3,charges:number,rank:number,time:number,firing:boolean,reduced:boolean){
 const phase=reduced?0:time*.85,radius=.105+.006*rank,alpha=82+charges*13+(firing?45:0);
 for(let strand=0;strand<2;strand++){
  const points:Vec3[]=[];
  for(let i=0;i<=14;i++){
   const t=i/14,a=phase+strand*Math.PI+t*Math.PI*1.3;
   const r=radius*(.78+.22*Math.sin(Math.PI*t));
   points.push(hand.clone().add(new Vec3(Math.cos(a)*r,-.035+t*.28,Math.sin(a)*r)));
  }
  energy(host,key,points,.09+rank*.003,alpha*(strand?.67:1));
 }
 for(let i=0;i<charges;i++){
  const a=phase+i*TAU/3,at=hand.clone().add(new Vec3(Math.cos(a)*radius*1.3,.18+Math.sin(a)*.045,Math.sin(a)*radius*1.3));
  energy(host,key,[at.clone().add(new Vec3(-.035,-.045,0)),at,at.clone().add(new Vec3(.035,.045,0))],.070,alpha*1.18);
 }
}

/** Open, tilted ribs give the protection depth without a ground range circle
 * or an opaque bubble. The one real guarded hit briefly compresses the ribs. */
export function drawThunderGuard(host:SkillVfxHost,key:string,p:Point,facing:number,rank:number,time:number,opacity:number,impact:number,passive=false,reduced=false,crownOnly=false){
 const count=crownOnly?0:passive?2:3,phase=reduced?0:time*.32;
 for(let rib=0;rib<count;rib++){
  const points:Vec3[]=[],a=facing+rib*TAU/count+phase;
  for(let i=0;i<=18;i++){
   const t=i/18,envelope=Math.sin(Math.PI*t);
   const radius=(.18+(passive?.21:.31)*envelope)*(1-impact*.13);
   const twist=.055*Math.sin(t*TAU+rib*1.8)*(reduced?.4:1);
   const q=local(p,a,twist,radius),height=(passive?.68:.32)+t*(passive?.76:1.24);
   points.push(host.at(q,height));
  }
  energy(host,key,points,(passive?.10:.14)+impact*.025,opacity*(rib===0?1:.75));
 }
 // Three restrained shoulder marks distinguish the earned passive shield.
 if(passive)for(let i=0;i<3;i++){
  const q=local(p,facing,(i-1)*.115,-.11);
  energy(host,key,[host.at(local(q,facing,-.035,0),1.26),host.at(q,1.36+(i===1?.06:0)),host.at(local(q,facing,.035,0),1.28)],.075,opacity*.88);
 }
}

/** Each real fan beat shows a short, broken transverse front inside its actual
 * occupied sector. The front reverses on beat two; it is not an outline of the
 * targeting area and cannot pass through occluded terrain. */
export function drawThunderFan(host:SkillVfxHost,key:string,origin:Point,facing:number,contacts:readonly Point[],rank:number,age:number,segment:number,opacity:number){
 if(contacts.length<2||age<0||age>.16)return;
 let lo=Infinity,hi=-Infinity,reach=0;
 for(const p of contacts){
  const dx=p.x-origin.x,dz=p.z-origin.z;
  const side=dx*Math.cos(facing)-dz*Math.sin(facing),forward=dx*Math.sin(facing)+dz*Math.cos(facing);
  const angle=clamp(Math.atan2(side,forward),-Math.PI*.30,Math.PI*.30);
  lo=Math.min(lo,angle);hi=Math.max(hi,angle);reach=Math.max(reach,Math.hypot(dx,dz));
 }
 if(hi-lo<.15||reach<.5)return;
 for(let band=0;band<2;band++){
  const progress=clamp((age-band*.018)/.115),head=segment%2?1-progress:progress;
  const start=clamp(head-(segment%2?0:.40)),end=clamp(head+(segment%2?.40:0));
  if(end-start<.015)continue;
  const radius=reach*(band?.84:.52),height=.92+band*.18;
  let path:Vec3[]=[],previous:Point|undefined;
  const flush=()=>{energy(host,key,path,(band?.16:.20)+rank*.003,opacity*(band?.65:1)*(1-progress*.65));path=[];previous=undefined;};
  for(let i=0;i<=20;i++){
   const t=i/20,u=start+(end-start)*t,a=facing+lo+(hi-lo)*u;
   const wobble=Math.sin(i*2.3+segment*1.7+band)*.055*Math.sin(Math.PI*t);
   const q={x:origin.x+Math.sin(a)*(radius+wobble),z:origin.z+Math.cos(a)*(radius+wobble)};
   if(host.visible?.(origin,q)===false||previous&&host.visible?.(previous,q)===false){flush();continue;}
   path.push(host.at(q,height+Math.sin(Math.PI*t)*.11));previous=q;
  }
  flush();
 }
}

export function drawThunderThirdContact(host:SkillVfxHost,key:string,p:Point,rank:number,progress:number){
 const alpha=235*Math.pow(1-clamp(progress),1.4);
 for(const side of [-1,1]){
  const q={x:p.x+side*.26,z:p.z+side*.12};
  energy(host,key,[host.at(q,1.48+rank*.025),host.at({x:p.x+side*.10,z:p.z-side*.05},1.14),host.at(p,.84)],.15,alpha);
 }
}
