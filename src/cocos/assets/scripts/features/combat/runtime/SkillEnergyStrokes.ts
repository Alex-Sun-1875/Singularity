import type {Vec3} from 'cc';
import type {CombatSkillEvent,Point} from '../../../core/Contracts';
import type {SkillVfxHost} from './NativeSkillVfx';
import type {VfxLineStyle} from '../../../shared/assets/VfxAssets';

/** User reference: white-hot filaments, saturated periwinkle-blue body and
 * blue corona. The ground palette remains the separately authored residual. */
export const THUNDER_COLORS={body:'#4d6dff',core:'#e8edff',halo:'#233de8',flare:'#f3f6ff',ground:'#292e70',residual:'#4e5dcf'} as const;
export const isThunderColor=(value:string)=>Object.values(THUNDER_COLORS).some(color=>color===value.toLowerCase());
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
 const seed=hash(`${event.castId}:${event.segment}:${event.sourceId??''}:${event.targetId??''}:${pulse}`)%100003;
 const phase=Math.floor(time*28),motion=time*28-phase,tremble=noise(seed+phase)*.055*(1-motion)+noise(seed+phase+1)*.055*motion;
 if(length<.04){
  const centre=host.at(to,HEIGHT),reach=.28+rank*.026,rays=6+Math.floor(rank/2),points:Vec3[]=[centre];
  host.thunderContact?.(`${event.castId}:${event.targetId??'contact'}`,centre,rank,brightness,time);
  // One native path for all crooked radial sparks, leaving the Line budget
  // available for every real network edge and the enemy's danger telegraphs.
  for(let i=0;i<rays;i++){
   const a=i/rays*Math.PI*2+noise(seed+i*17)*.35,r=reach*(.65+.35*Math.abs(noise(seed+i*29)));
   for(let j=1;j<=2;j++){const t=j/2,angle=a+noise(seed+i*31+j*7)*.3;points.push(host.at({x:to.x+Math.cos(angle)*r*t,z:to.z+Math.sin(angle)*r*t},HEIGHT+noise(seed+i*47+j*3)*r*.4));}points.push(centre);
  }
  host.line(points,CORE,.014+rank*.001,Math.round(brightness*.85),false,'core');
  detail(host,points,HALO,.13,brightness*.42,'glow');return;
 }
 if(sourceAnchor&&!network)host.thunderContact?.(`${event.castId}:entry`,sourceAnchor,rank,brightness*.95,time);
 const perpendicular={x:dz/length,z:-dx/length},forward={x:dx/length,z:dz/length};
 // Creator's public Line owns a fixed100-point buffer.
 const count=Math.round(clamp(Math.ceil(length/.16),12,94)),spread=clamp(.11+length*.032,.18,.48),points:Vec3[]=[],worldPoints:Point[]=[];
 for(let i=0;i<=count;i++){
  const t=i===0?0:i===count?1:(i+noise(seed+i*61)*.25)/count,base=mix(from,to,t),envelope=i===0||i===count?0:Math.pow(Math.max(0,Math.sin(Math.PI*t)),.3);
  const side=envelope*(field(seed,t*length*1.1)*spread+field(seed+172,t*length*3.6)*.095+noise(seed+i*43+7)*.038+tremble*.3);
  const p=bound({x:base.x+perpendicular.x*side,z:base.z+perpendicular.z*side});worldPoints.push(p);
  const point=host.at(p,HEIGHT+(i===0||i===count?0:noise(seed+i*11)*.095*envelope));
  if(sourceOffset)point.add(sourceOffset.clone().multiplyScalar(1-t));points.push(point);
 }
 host.line(points,BLUE,(network?.064:.082)+rank*.0034,Math.round(brightness*.94),true,'solid');
 host.line(points,CORE,.024+rank*.0018,Math.round(brightness*.96),true,'core');
 detail(host,points,HALO,.43+rank*.025,brightness*.62,'glow');
 // A long launch is a bundle of three irregular filaments; every network edge
 // also carries its own thinner parallel filament, meeting the same endpoints.
 const filaments=network?1:2;
 for(let strand=0;strand<filaments;strand++){
  const sign=strand%2?-1:1,path=points.map((p,i)=>{const t=i/count,envelope=Math.pow(Math.max(0,Math.sin(Math.PI*t)),.4),offset=envelope*sign*(network?.075:.16+strand*.06)*(.15+Math.abs(field(seed+331+strand*17,t*length*1.7))*1.85);return p.clone().add(host.at(bound({x:worldPoints[i].x+perpendicular.x*offset,z:worldPoints[i].z+perpendicular.z*offset}),HEIGHT).subtract(host.at(worldPoints[i],HEIGHT)));});
  detail(host,path,CORE,.013+rank*.001,brightness*(network?.66:.83),'core');
 }
 const forks=network?(length>3.3&&rank>=3?2:1):Math.min(4,2+Math.floor(rank/2));
 for(let i=0;i<forks;i++){
  const index=Math.round(count*(.2+(i+.35)/(forks+.7)*.61)),base=worldPoints[index],sign=noise(seed+i*23)>0?1:-1,reach=Math.min(network?.26+rank*.042:.42+rank*.07,length*.24),branch:Vec3[]=[points[index]];
  for(let j=1;j<=6;j++){
   const t=j/6,jitter=noise(seed+i*101+j*17)*.065*Math.sin(Math.PI*t),q={x:base.x+forward.x*reach*t*.53+perpendicular.x*(reach*t*sign+jitter),z:base.z+forward.z*reach*t*.53+perpendicular.z*(reach*t*sign+jitter)},point=host.at(bound(q),HEIGHT+noise(seed+i*73+j*3)*.065);
   if(sourceOffset)point.add(sourceOffset.clone().multiplyScalar(1-index/count));branch.push(point);
  }
  detail(host,branch,CORE,.012+rank*.0007,brightness*(network?.65:.82),'core');
  detail(host,branch,HALO,.12,brightness*.30,'glow');
 }
}

/** Newest first. Reclip the supplied travelled path by arc length, so a split
 * arrow can show its bend without drawing an untravelled route to the target. */
export function drawArrowWake(host:SkillVfxHost,points:readonly Point[],color:string,split:boolean,rank:number,visualPoints?:readonly Vec3[],opacity=1):void {
 if(points.length<2||opacity<=0)return;
 // A child's whole already-flown curve establishes the split fan. Its head
 // still has a short bright wake; the faint path survives contact for .24s.
 if(split){
  const flown=points.map((p,i)=>visualPoints?.[i]?.clone()??host.at(p,1.05));
  host.line(flown,'#c6ddb0',.026,Math.round(115*opacity),true,'solid');
  detail(host,flown,'#d3eab0',.14,48*opacity,'glow');
 }
 const limit=split?1.25:.70,path:Point[]=[{...points[0]}];let travelled=0;
 for(let i=1;i<points.length;i++){
  const previous=points[i-1],next=points[i],length=Math.hypot(next.x-previous.x,next.z-previous.z);
  if(length<.00001)continue;
  if(travelled+length>=limit){path.push(mix(previous,next,(limit-travelled)/length));break;}
  path.push({...next});travelled+=length;
 }
 if(path.length<2)return;
 const native=path.map((p,i)=>visualPoints?.[i]?.clone()??host.at(p,1.05)),alpha=(split?225:190)*opacity;
 host.line(native,split?'#d8efb4':color,split?.044:.032,Math.round(alpha),true,'solid');
 host.line(native,split?'#f5f8de':'#f1efdf',split?.018:.012,Math.round(alpha*.82),true,'core');
}

/** One small physical puncture, called once by the authoritative contact event. */
export function drawArrowContact(host:SkillVfxHost,point:Point,angle:number,rank:number):void {
 const tier=rankOf(rank);
 host.burst('spark',point,.78,3+Math.floor(tier/2),.34+tier*.018,'#e5d8ab',-angle);
 host.burst('flash',point,.78,1,.34+tier*.017,'#e8f0cc');
 host.burst('dust',point,.61,2+Math.floor(tier/3),.25+tier*.008,'#b9ae8e');
}
