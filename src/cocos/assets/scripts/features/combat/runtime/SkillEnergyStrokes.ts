import {Vec3} from 'cc';
import type {CombatSkillEvent,Point} from '../../../core/Contracts';
import type {SkillVfxHost} from './NativeSkillVfx';
import type {VfxLineStyle} from '../../../shared/assets/VfxAssets';
import type {ThunderArcField} from './ThunderArcField';

/** User reference: white-hot filaments, saturated periwinkle-blue body and
 * blue corona. The ground palette remains the separately authored residual. */
export const THUNDER_COLORS={body:'#4d6dff',core:'#e8edff',halo:'#233de8',flare:'#f3f6ff',ground:'#292e70',residual:'#4e5dcf'} as const;
export const isThunderColor=(value:string)=>Object.values(THUNDER_COLORS).some(color=>color===value.toLowerCase());
/** Reuse the approved chain-arrow palette for every player bow projectile. */
export const ARROW_COLORS={body:'#a9d7ad',core:'#f1efdf',halo:'#89c9ac',contact:'#b8dfb7',flash:'#e8f0cc'} as const;
const BLUE=THUNDER_COLORS.body,CORE=THUNDER_COLORS.core,HALO=THUNDER_COLORS.halo;
const HEIGHT=1.05;
const clamp=(value:number,low:number,high:number)=>Math.max(low,Math.min(high,value));
const mix=(a:Point,b:Point,t:number):Point=>({x:a.x+(b.x-a.x)*t,z:a.z+(b.z-a.z)*t});
const noise=(seed:number)=>{const value=Math.sin(seed*127.1+91.7)*43758.5453;return (value-Math.floor(value))*2-1;};
const field=(seed:number,t:number)=>{const i=Math.floor(t),f=t-i;return noise(seed+i*19)*(1-f)+noise(seed+(i+1)*19)*f;};
const rankOf=(rank:number)=>clamp(Math.round(rank||1),1,5);
function hash(value:string){let seed=2166136261;for(let i=0;i<value.length;i++)seed=Math.imul(seed^value.charCodeAt(i),16777619);return seed>>>0;}
function detail(host:SkillVfxHost,points:Vec3[],color:string,width:number,alpha:number,style:VfxLineStyle='solid'){
 if(host.detailLine)host.detailLine(points,color,width,Math.round(alpha),style);
 else host.line(points,color,width,Math.round(alpha),false,style);
}

/** Draw the supplied resolved pair. Parallel filaments and short free forks are
 * decorative air discharges; none finds another enemy or submits damage. */
export function drawLightning(host:SkillVfxHost,event:CombatSkillEvent,alpha:number,time:number,sourceAnchor?:Vec3,pulse=0):void {
 const from=event.from,to=event.to??from,rank=rankOf(event.rank),network=event.phase==='network',dx=to.x-from.x,dz=to.z-from.z,length=Math.hypot(dx,dz);
 const corridor=event.phase==='corridor',halfWidth=Math.max(.03,(event.width??.65)/2);
 const bound=(p:Point)=>{if(!corridor||length<.001)return p;const x=p.x-from.x,z=p.z-from.z,f=clamp((x*dx+z*dz)/length,0,length),side=clamp((x*dz-z*dx)/length,-halfWidth*.78,halfWidth*.78);return{x:from.x+dx/length*f+dz/length*side,z:from.z+dz/length*f-dx/length*side};};
 const brightness=clamp(Math.round(alpha),0,255);if(!brightness)return;
 const sourceOffset=sourceAnchor?.clone().subtract(host.at(from,HEIGHT));
 const seed=hash(`${event.castId}:${event.segment}:${event.sourceId??''}:${event.targetId??''}`)%100003;
 const phase=Math.floor(time*18),motion=time*18-phase,tremble=noise(seed+phase)*.045*(1-motion)+noise(seed+phase+1)*.045*motion;
 if(length<.04){
  const centre=host.at(to,HEIGHT),reach=.28+rank*.026,rays=6,points:Vec3[]=[centre];
  host.thunderContact?.(`${event.castId}:${event.targetId??'contact'}`,centre,rank,brightness,time);
  // One native path for all crooked radial sparks, leaving the Line budget
  // available for every real network edge and the enemy's danger telegraphs.
  for(let i=0;i<rays;i++){
   const a=i/rays*Math.PI*2+noise(seed+i*17)*.35,r=reach*(.65+.35*Math.abs(noise(seed+i*29)));
   for(let j=1;j<=2;j++){const t=j/2,angle=a+noise(seed+i*31+j*7)*.3;points.push(host.at({x:to.x+Math.cos(angle)*r*t,z:to.z+Math.sin(angle)*r*t},HEIGHT+noise(seed+i*47+j*3)*r*.4));}points.push(centre);
  }
  host.line(points,CORE,.023+rank*.0018,Math.round(brightness*.85),false,'core');
  detail(host,points,HALO,.13,brightness*.42,'glow');return;
 }
 if(sourceAnchor&&!network)host.thunderContact?.(`${event.castId}:entry`,sourceAnchor,rank,brightness*.95,time);
 const perpendicular={x:dz/length,z:-dx/length},forward={x:dx/length,z:dz/length};
 // Creator's public Line owns a fixed100-point buffer.
 // Each resolved edge has a cast-specific shape in a narrow corridor. Keep
 // the hand exit calm, with short irregular kinks instead of a scaled curve.
 const count=Math.round(clamp(Math.ceil(length/.11),16,88)),spread=Math.min(length*.16,.055+length*.022,network?.28:.24),points:Vec3[]=[],worldPoints:Point[]=[];
 const frequency=1.65+noise(seed+83)*.35;
 for(let i=0;i<=count;i++){
  const t=i===0?0:i===count?1:(i+noise(seed+i*61)*.25)/count,base=mix(from,to,t),envelope=i===0||i===count?0:Math.pow(Math.max(0,Math.sin(Math.PI*t)),.65)*(network?1:Math.min(1,t*8));
  const side=envelope*((field(seed,t*length*frequency)*.72+field(seed+11,t*length*frequency*2.1)*.28)*spread+field(seed+172,t*length*3.6+time*.85)*.018+noise(seed+i*43+7)*.012+tremble*.12);
  const p=bound({x:base.x+perpendicular.x*side,z:base.z+perpendicular.z*side});worldPoints.push(p);
  const point=host.at(p,HEIGHT+(i===0||i===count?0:noise(seed+i*11)*.035*envelope));
  if(sourceOffset)point.add(sourceOffset.clone().multiplyScalar(1-t));points.push(point);
 }
 if(host.thunderBeam){
  host.thunderBeam(event.castId+':'+event.segment,points,(network?.29:.50)+rank*.010,brightness,network?'chain':'launch');
 }else{
  host.line(points,'#b8ceff',(network?.126:.172)+rank*.0046,Math.round(brightness*.72),true,'glow');
  host.line(points,CORE,.078+rank*.003,Math.round(brightness*.96),true,'core');
 }
 // One short free fork can leave the main path, with a fresh position,
 // direction and reach for every cast. It never becomes a second long loop.
 const forks=length>.8?1:0;
 for(let i=0;i<forks;i++){
  const index=Math.round(count*(.28+(noise(seed+211)*.5+.5)*.42)),base=worldPoints[index],sign=noise(seed+307)>0?1:-1;
  const reach=Math.min(length*.16,(network?.30:.38)+rank*.018)*(.7+.3*Math.abs(noise(seed+419))),branch:Vec3[]=[points[index]];
  for(let j=1;j<=7;j++){
   const t=j/7,jitter=noise(seed+j*17)*reach*.14*Math.sin(Math.PI*t),q={x:base.x+forward.x*reach*t*.65+perpendicular.x*(reach*t*sign+jitter),z:base.z+forward.z*reach*t*.65+perpendicular.z*(reach*t*sign+jitter)},point=host.at(bound(q),HEIGHT+noise(seed+j*3)*.035*t);
   if(sourceOffset)point.add(sourceOffset.clone().multiplyScalar(1-index/count));branch.push(point);
  }
  if(host.thunderBeam)host.thunderBeam(event.castId+':'+event.segment,branch,network?.16:.18,brightness*.65,network?'chainDetail':'launchDetail');
  else detail(host,branch,CORE,.021+rank*.0014,brightness*(network?.55:.65),'core');
 }

}

/** A compact flying discharge follows the real basic projectile. Its entire
 * wake stays behind the head and inside the distance already travelled. */
export function drawThunderDart(thunder:ThunderArcField,key:string,head:Vec3,direction:Vec3,travelled:number,time:number,reduced=false):void {
 const length=Math.min(.78,Math.max(0,travelled));if(length<.002)return;
 const forward=direction.clone().normalize(),side=new Vec3(forward.z,0,-forward.x).normalize(),seed=hash(key)%100003;
 const points:Vec3[]=[],steps=12;
 for(let i=0;i<=steps;i++){
  const t=i/steps,envelope=Math.sin(Math.PI*t),sway=(field(seed,t*5)*.036+(reduced?0:field(seed+71,t*8+time*5)*.009))*envelope;
  points.push(head.clone().add(forward.clone().multiplyScalar(-length*(1-t))).add(side.clone().multiplyScalar(sway)).add(new Vec3(0,noise(seed+i*13)*.015*envelope,0)));
 }
 // Share one native batch with the other basic darts and their short contacts.
 thunder.addBeam('basic-thunder',points,.18,245,'accent');
 if(length<.12||reduced)return;
 const start=points[4],sign=noise(seed+157)>0?1:-1,reach=Math.min(.19,length*.28),fork:Vec3[]=[start];
 for(let i=1;i<=5;i++){
  const t=i/5;fork.push(start.clone().add(forward.clone().multiplyScalar(-reach*t*.65)).add(side.clone().multiplyScalar(sign*reach*t+noise(seed+i*29)*reach*.16*Math.sin(Math.PI*t))));
 }
 thunder.addBeam('basic-thunder',fork,.065,150,'accent');
 // Two fine filaments converge at the visible tip; no spherical light body.
 const filament:Vec3[]=[];
 for(let i=0;i<=6;i++){
  const t=i/6;filament.push(head.clone().add(forward.clone().multiplyScalar(-Math.min(length,.30)*(1-t))).add(side.clone().multiplyScalar(-sign*.075*Math.sin(Math.PI*t))));
 }
 thunder.addBeam('basic-thunder',filament,.075,190,'accent');
}

/** A real basic hit cracks into a few local sparks and fades within .14s. */
export function drawThunderDartContact(thunder:ThunderArcField,key:string,center:Vec3,age:number,reduced=false):void {
 const progress=clamp(age/.14,0,1),alpha=Math.round(240*Math.pow(1-progress,1.7));if(age<0||alpha<=0)return;
 const seed=hash(key)%100003,count=reduced?3:5;
 for(let i=0;i<count;i++){
  const angle=i/count*Math.PI*2+noise(seed+i*31)*.3,reach=(.15+.12*progress)*(.8+.2*Math.abs(noise(seed+i*47))),path:Vec3[]=[center];
  for(let j=1;j<=4;j++){
   const t=j/4,a=angle+noise(seed+i*71+j*11)*.28;
   path.push(center.clone().add(new Vec3(Math.cos(a)*reach*t,noise(seed+i*37+j*7)*reach*.45*t,Math.sin(a)*reach*t)));
  }
  thunder.addBeam('basic-thunder',path,.10*(1-progress*.55),alpha,'accent');
 }
}

/** Newest first. Clip the actual rendered path, including the interpolated
 * final sample, so curved wakes never extend into an untravelled route. */
export function drawArrowWake(host:SkillVfxHost,points:readonly Point[],color:string,split:boolean,rank:number,visualPoints?:readonly Vec3[],opacity=1,chaining=false):void {
 if(points.length<2||opacity<=0)return;
 const flown=points.map((p,i)=>visualPoints?.[i]?.clone()??host.at(p,1.05));
 if(split){
  host.line(flown,color,.026,Math.round(115*opacity),true,'solid');
  detail(host,flown,ARROW_COLORS.halo,.14,48*opacity,'glow');
 }
 const limit=chaining?2.35:split?1.25:.88,native:Vec3[]=[flown[0]];let travelled=0;
 for(let i=1;i<flown.length;i++){
  const previous=flown[i-1],next=flown[i],length=Vec3.distance(previous,next);
  if(length<.00001)continue;
  if(travelled+length>=limit){native.push(Vec3.lerp(new Vec3(),previous,next,(limit-travelled)/length));break;}
  native.push(next);travelled+=length;
 }
 if(native.length<2)return;
 const alpha=(chaining?215:split?225:190)*opacity;
 host.line(native,ARROW_COLORS.halo,chaining?.13:.10,Math.round((chaining?42:32)*opacity),true,'glow');
 host.line(native,color,chaining?.052:split?.044:.037,Math.round(alpha),true,'core');
 host.line(native,ARROW_COLORS.core,chaining?.017:split?.018:.014,Math.round(alpha*.82),true,'core');
}

/** One small physical puncture, called once by the authoritative contact event. */
export function drawArrowContact(host:SkillVfxHost,point:Point,angle:number,rank:number,chaining=false):void {
 const tier=rankOf(rank);
 host.burst('spark',point,.78,3+Math.floor(tier/2)+(chaining?1:0),(.34+tier*.018)*(chaining?1.12:1),ARROW_COLORS.contact,-angle);
 host.burst('flash',point,.78,1,(.34+tier*.017)*(chaining?1.25:1),ARROW_COLORS.flash);
 host.burst('dust',point,.61,2+Math.floor(tier/3),.25+tier*.008,'#b9ae8e');
}
