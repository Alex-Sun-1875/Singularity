import {FIRE_PALETTE} from '../../../shared/assets/FirePalette';
import {Vec3} from 'cc';
import type {CombatSkillEvent,GameEvent,Point} from '../../../core/Contracts';
import type {GameSession,ProjectileState} from '../../../core/GameSession';
import {PURE_SKILLS,type SkillGeometry} from '../data/PureSkills';
import type {VfxKind,VfxLineStyle} from '../../../shared/assets/VfxAssets';
import {skillVfxGeometry} from '../data/SkillVfxGeometry';
import {drawMeleeSweep,drawMeleeContact} from './MeleeSkillEffects';
import {WARRIOR_ULTIMATE} from '../common/WarriorUltimate';
import {drawLightning,drawArrowWake,drawArrowContact,THUNDER_COLORS,ARROW_COLORS} from './SkillEnergyStrokes';
import {drawThunderCharge,drawThunderGuard,drawThunderFan,drawThunderThirdContact} from './ThunderSupportEffects';

/** Gameplay geometry and victim identities come from core events. Electrical
 * echoes may follow those same identities; they never select targets, advance
 * projectiles, or submit damage. All timers use the session clock. */
export interface SkillPreview {
 target:Point;valid:boolean;skillId?:string;rank?:number;angle?:number;
 geometry?:Partial<SkillGeometry>&{type?:string;radius?:number;length?:number;width?:number;depth?:number;angle?:number;angles?:number[]};
}
type SkillEvent=CombatSkillEvent;
export interface SkillVfxHost {
 warriorUltimate?(key:string,p:Point,angle:number,rank:number,elapsed:number):void;
 warriorSweep?(key:string,p:Point,angle:number,radius:number,span:number,stage:number,t:number,alpha:number):void;
 warriorContact?(key:string,p:Point,angle:number,strength:number,t:number):void;
 warriorCross?(key:string,p:Point,angle:number,length:number,t:number,alpha:number):void;
 warriorPulse?(key:string,p:Point,angle:number,t:number,alpha:number,iron?:boolean):void;
 groundJets?(key:string,p:Point,angle:number,length:number,width:number,age:number,alpha:number,emitting:boolean,cooling:number):void;
 meteorSeal?(key:string,p:Point,radius:number,alpha:number):void;
 thunderBeam?(key:string,points:readonly Vec3[],width:number,alpha:number,role?:'launch'|'chain'|'launchDetail'|'chainDetail'|'accent'):void;
 at(p:Point,height?:number):Vec3;
 line(points:Vec3[],color:string,width?:number,alpha?:number,taper?:boolean,style?:VfxLineStyle):void;
 detailLine?(points:Vec3[],color:string,width?:number,alpha?:number,style?:VfxLineStyle):void;
 burst(kind:VfxKind,p:Point,height:number,count:number,scale?:number,color?:string,angle?:number):void;
 loop(key:string,kind:VfxKind,p:Point,height:number,scale?:number,color?:string):unknown;
 body(p:ProjectileState):void;
 projectileAt?(p:ProjectileState,height:number):Vec3;
 playerHand?():Vec3|undefined;
 playerCastHand?():Vec3|undefined;
 visible?(from:Point,to:Point):boolean;
 blade?(key:string,p:Point,height:number,angle:number,radius:number,span:number,width:number,alpha:number,progress:number,normal?:Vec3):void;
 slash?(key:string,start:Vec3,end:Vec3,width:number,alpha:number,progress:number):void;
 fireSprite?(key:string,p:Point,height:number,width:number,tall:number,phase:number,alpha:number):void;
 fireProjectile?(key:string,p:Point,height:number,angle:number,size:number,time:number):void;
 meteor?(key:string,p:Point,rank:number,progress:number,time:number):void;
 firePlume?(key:string,p:Point,height:number,size:number,time:number,alpha:number):void;
 fireVolume?(key:string,p:Point,radius:number,rank:number,progress:number,alpha:number,angle?:number,age?:number,duration?:number):void;
 fireRibbon?(key:string,p:Point,width:number,depth:number,angle:number,time:number,alpha:number,origin?:Point,cooling?:number):void;
 thunderGround?(key:string,p:Point,radius:number,alpha:number,phase:number):void;
 thunderContact?(key:string,center:Vec3,rank:number,alpha:number,time:number):void;
 thunderField?(key:string,points:readonly Point[],rank:number,alpha:number,pulse:number):void;
}
type Cue={event:SkillEvent;start:number;duration:number;coolingAt?:number;sourceAnchor?:Vec3;kind:'cross'|'cleave'|'drop'|'bolt'|'wall'|'wave'|'afterglow'|'enchant'|'mark'|'heal'|'dash'|'metal'|'burn'|'ward'|'meleeSweep'|'blast'|'field'|'trap'|'snare'|'storm'|'stormHit'|'thunderThird'|'jetCharge'};
type Trail={castId?:string;points:Point[];time:number;visual?:Vec3[];bow?:{split:boolean;rank:number;color:string;chaining:boolean};ended?:boolean};
type ArrowLeg={points:Point[];visual:Vec3[];time:number;rank:number;color:string};
type ThunderPattern={castId:string;skillId:string;rank:number;segment:number;start:number;caster?:Point;aim?:Point;angle?:number;depths:Map<string,number>;edges:Map<string,{event:SkillEvent;sourceAnchor?:Vec3}>;nodes:Map<string,Point>;ground:Map<string,{p:Point;time:number}>};
const SILVER='#e5f2ee',GOLD='#d5b46a',ARROW='#dce5d3',FIRE=FIRE_PALETTE.body,LIGHTNING=THUNDER_COLORS.body,VIOLET=THUNDER_COLORS.halo;
const TAU=Math.PI*2;
const mix=(a:Point,b:Point,t:number):Point=>({x:a.x+(b.x-a.x)*t,z:a.z+(b.z-a.z)*t});
const distance=(a:Point,b:Point)=>Math.hypot(a.x-b.x,a.z-b.z);
const heading=(a:Point,b:Point)=>Math.atan2(b.x-a.x,b.z-a.z);
const offset=(p:Point,a:number,side:number,forward:number):Point=>({x:p.x+Math.cos(a)*side+Math.sin(a)*forward,z:p.z-Math.sin(a)*side+Math.cos(a)*forward});
const tier=(e:{rank?:number})=>Math.max(1,Math.min(5,Math.round(e.rank??1)));
const values=(rank:number,list:number[])=>list[Math.max(0,Math.min(4,rank-1))];
const noise=(seed:number)=>{const v=Math.sin(seed*127.1+91.7)*43758.5453;return v-Math.floor(v);};

export class NativeSkillVfx {
 reducedMotion=false;
 private cues:Cue[]=[];
 private trails=new Map<string,Trail>();
 private arrowLegs:ArrowLeg[]=[];
 private seen=new Set<string>();
 private clues=new Map<string,{p:Point;start:number;duration:number}>();
 private thunderPatterns=new Map<string,ThunderPattern>();
 private now=0;
 constructor(private readonly host:SkillVfxHost){}
 private point(e:SkillEvent){return e.at??e.to??e.from;}
 private thunder(e:SkillEvent,contact=false){
  let pattern=this.thunderPatterns.get(e.castId);
  if(!pattern){
   if(this.thunderPatterns.size>=12)this.thunderPatterns.delete(this.thunderPatterns.keys().next().value!);
   pattern={castId:e.castId,skillId:e.skillId,rank:tier(e),segment:e.segment,start:this.now,depths:new Map(),edges:new Map(),nodes:new Map(),ground:new Map()};this.thunderPatterns.set(e.castId,pattern);
  }
  if(e.type==='skill_release'){pattern.caster={...e.from};pattern.aim={...(e.to??e.from)};pattern.angle=e.angle;}
  if(pattern.segment!==e.segment){pattern.segment=e.segment;pattern.start=this.now;pattern.edges.clear();pattern.nodes.clear();pattern.depths.clear();}
  if(e.targetId&&e.to)pattern.nodes.set(e.targetId,{...e.to});
  if(contact&&e.targetId)pattern.ground.set(e.targetId,{p:{...this.point(e)},time:this.now});
  if(e.sourceId)pattern.nodes.set(e.sourceId,{...e.from});
  if(!contact&&e.targetId&&e.to){
   pattern.depths.set(e.targetId,e.sourceId?(pattern.depths.get(e.sourceId)??0)+1:0);
   const event={...e,from:{...e.from},to:{...e.to}};
   pattern.edges.set(`${e.sourceId??'entry'}:${e.targetId}:${e.phase}`,{event});
  }
 }
 private add(e:SkillEvent,kind:Cue['kind'],duration:number,keyed=false){
  const g=skillVfxGeometry(e),snapshot={...e,geometry:g,radius:g.radiusMetres,width:g.widthMetres,length:g.lengthMetres,depth:g.depthMetres,angleDegrees:g.angleDegrees,anglesDegrees:g.anglesDegrees,from:{...e.from},to:e.to?{...e.to}:undefined,at:e.at?{...e.at}:undefined};
  if(keyed){
   this.cues=this.cues.filter(c=>!(c.kind===kind&&(
    kind==='enchant'||kind==='burn'&&c.event.targetId===e.targetId||
    c.event.castId===e.castId&&c.event.targetId===e.targetId)));
  }
  // Continuous visuals and short contacts have separate native pools. Old visual
  // records can be dropped without affecting any authoritative gameplay object.
  if(this.cues.length>=112)this.cues.splice(this.cues.findIndex(c=>c.kind!=='wall'&&c.kind!=='enchant'&&!(c.kind==='meleeSweep'&&c.event.skillId==='WAR_05'&&c.event.segment===2)),1);
  const start=e.skillId==='WAR_05'&&e.type==='skill_segment'&&e.segment===2&&kind==='meleeSweep'&&Number.isFinite(e.startedAt)?e.startedAt!:this.now;
  this.cues.push({event:snapshot,start,duration:Math.max(.06,duration),kind});
 }
 private stroke(a:Point,b:Point,color:string,width=.025,alpha=180,height=.7){this.host.line([this.host.at(a,height),this.host.at(b,height)],color,width,alpha);}
 private detail(points:Vec3[],color:string,width:number,alpha:number,style?:VfxLineStyle){
  if(this.host.detailLine)this.host.detailLine(points,color,width,alpha,style);else this.host.line(points,color,width,alpha,false,style);
 }
 private arc(p:Point,a:number,span:number,color:string,alpha:number){
  const points:Vec3[]=[];for(let i=0;i<=20;i++){const s=i/10-1;points.push(this.host.at(offset(p,a,s*span*.5,(1-s*s)*span*.22),.72+(1-s*s)*.12));}
  this.host.line(points,color,.105,alpha,true);
 }
 private scratch(p:Point,a:number,count:number,color:string,alpha:number,height=.8){
  for(let i=0;i<count;i++){const c=offset(p,a,(i-(count-1)/2)*.055,0);this.stroke(offset(c,a,0,-.10),offset(c,a,.08,.13),color,.015,alpha,height+(i%2)*.04);}
 }
 private contact(e:SkillEvent){
  const p=this.point(e),r=tier(e),family=e.skillId.slice(0,3),a=e.angle??heading(e.from,p);
  if(e.skillId==='COM_02'){this.add(e,'heal',.65);this.host.burst('heal',p,.7,3+r,.85);return;}
  if(family==='WAR'){
   this.add(e,'metal',.18);
  }else if(family==='BOW'){
   // Contacts currently identify the cast; redirects identify the projectile.
   const path=e.projectileId?this.trails.get(e.projectileId):e.skillId==='BOW_02'?[...this.trails.values()].find(t=>t.castId===e.castId&&t.bow?.chaining):undefined;
   if(path?.bow){
    // A true contact can complete the last travelled centimetres. It never
    // draws the frozen future path before the projectile reaches this point.
    if(distance(path.points[0]??p,p)>.02){path.points.unshift({...p});path.visual?.unshift(this.host.at(p,1.05));}
    path.time=this.now;path.ended=true;
   }
   drawArrowContact(this.host,p,a,r,e.skillId==='BOW_02');
  }else if(family==='FIR'){
   this.host.burst('fireCore',p,.18,1,.65+.07*r);
   this.host.burst('ember',p,.22,3+r,.5+.04*r);
   if(e.skillId==='FIR_P2'&&e.to)this.add(e,'bolt',.18);
  }else if(family==='THU'){
   if(e.skillId==='THU_01')this.cues=this.cues.filter(c=>!(c.event.castId===e.castId&&c.kind==='bolt'&&c.event.phase==='corridor'));
   this.host.burst('flash',p,.85,1,.37+.035*r,LIGHTNING);
   if(['THU_03','THU_P1'].includes(e.skillId)){
    // The three real basic contacts refresh one aftermath at the same victim.
    this.thunder({...e,castId:'weapon-thunder:'+e.targetId},true);
    if(e.skillId==='THU_03'&&e.segment===3)this.add(e,'thunderThird',.18);
   }
   else if(['THU_01','THU_02','THU_04','THU_05'].includes(e.skillId))this.thunder(e,true);
   else this.add({...e,from:p,to:p},'bolt',.16+.008*r);
  }
 }
 /** Returns true only for one of the active four-family/common skill events. */
 event(event:GameEvent,time:number):boolean{
  if(event.type==='clue_reveal'&&event.at){
   this.clues.set(event.id??'clue',{p:{...event.at},start:time,duration:Number(event.duration)||3});
   this.host.burst('spark',event.at,.18,3,.3,'#e9ca8b');return true;
  }
  if(!event.type.startsWith('skill_')||typeof event.skillId!=='string'||!/^(WAR|BOW|FIR|THU|COM)_/.test(event.skillId))return false;
  const e=event as SkillEvent;if(!e.from)return true;this.now=time;
  const r=tier(e),p=this.point(e),id=e.skillId;
  if(e.type==='skill_end'){
 this.cues=this.cues.filter(c=>{
  if(c.event.castId!==e.castId)return true;
  if(c.kind==='blast'&&c.event.skillId.startsWith('FIR'))return true;
  if((c.kind==='wall'||c.kind==='field')&&c.event.skillId.startsWith('FIR')){
   if(c.coolingAt===undefined){c.coolingAt=this.now;c.duration=this.now-c.start+1.8;}return true;
  }return false;
 });if(e.phase==='triggered')this.add(e,'snare',.4);return true;
}
  // The core may publish multiple notifications for a contact, but a consumed
  // event batch or resumed menu must never manufacture a second visual strike.
  const recurring=['heal','defense','shieldHit'].includes(e.castId)?time.toFixed(4):'';
  const key=`${e.type}:${e.castId}:${e.segment}:${e.waveIndex??''}:${e.sourceId??''}:${e.targetId??''}:${e.phase??''}:${e.status??''}:${e.projectileId??''}:${recurring}:${e.from.x.toFixed(3)}:${e.from.z.toFixed(3)}:${e.to?.x.toFixed(3)??''}:${e.to?.z.toFixed(3)??''}`;
  if(this.seen.has(key))return true;this.seen.add(key);if(this.seen.size>768)this.seen.delete(this.seen.values().next().value!);
  if(e.type==='skill_cast'){
   if(id==='FIR_02')this.add(e,'drop',e.duration??.55);
   if(id==='FIR_04')this.add(e,'jetCharge',e.duration??.25);
   // Continuous hand charge follows the sampled player pose in Effects.
   return true;
  }
  if(e.type==='skill_hit'){this.contact(e);return true;}
  if(e.type==='skill_status'){
   if(e.status==='shieldHit')return true;
   else if(id==='COM_02'){
    // The initial three-second buff notice is not a fourth heal pulse.
    if((e.duration??0)<1){this.add(e,'heal',.7);this.host.burst('heal',e.from,.75,3+r,.9);}
   }
   else if(id==='COM_01'||id==='BOW_P2')this.add(id==='BOW_P2'?{...e,from:e.to??e.from}:e,'dash',e.duration??.32);
   else if(id==='WAR_03'||id==='FIR_03')return true;
   else if(id==='THU_03')this.add(e,'enchant',e.duration??6,true);
   else if(id==='THU_06'){if(e.status==='wardHit'){this.add(e,'stormHit',.22,true);this.host.burst('flash',e.from,.9,1,.23+.01*r,LIGHTNING);}else this.add(e,'storm',e.duration??3,true);}
   else if(id==='BOW_04'||id==='BOW_P1')this.add(e,'mark',e.duration??(id==='BOW_04'?8:.35),true);
   else if(id==='FIR_P1')this.host.burst('ember',p,.18,2+r,.3);
   else if(id==='FIR_P2'){this.add(e,'bolt',.22);this.host.burst('ember',p,.16,2+r,.4);}
   else if(e.status==='burn')this.add(e,'burn',e.duration??3,true);
   else if(e.status==='root')this.add(e,'snare',e.duration??.8,true);
   else if(id==='THU_P2')this.add(e,'ward',3,true);
   else if(id==='WAR_P1'||id==='WAR_P2'||id==='THU_P1'&&e.status!=='thunderWeapon')this.add(e,'metal',.22);
   return true;
  }
  if(e.type==='skill_zone'){
   if(id==='FIR_04')this.add(e,'wall',e.duration??4,true);else if(id==='BOW_06')this.add(e,'trap',e.duration??8,true);else if(id==='FIR_05')this.add(e,'field',e.duration??3.3,true);
   return true;
  }
  if(e.type==='skill_segment'){
   if(id==='BOW_02'&&e.phase==='redirect'&&e.projectileId){
    const path=this.trails.get(e.projectileId);
    if(path?.bow){
     const completed=path.points.map(p=>({...p})),visual=path.visual?.map(p=>p.clone())??completed.map(p=>this.host.at(p,1.05));
     // Replace a completed target-centre sample with the true redirect position.
     if(path.ended){completed.shift();visual.shift();}
     if(!completed.length||distance(completed[0],e.from)>.02){completed.unshift({...e.from});visual.unshift(this.host.at(e.from,1.05));}
     if(completed.length>1)this.arrowLegs.push({points:completed,visual,time:this.now,rank:path.bow.rank,color:path.bow.color});
     if(this.arrowLegs.length>8)this.arrowLegs.shift();
     path.points=[{...e.from}];path.visual=[this.host.at(e.from,1.05)];path.time=this.now;path.ended=false;
    }
   }
   if(id==='WAR_01'||id==='WAR_05'){this.add(e,'meleeSweep',id==='WAR_01'?.50:e.segment===2?WARRIOR_ULTIMATE.visualDuration:.52);}
   else if(id==='WAR_02')this.add(e,'cross',.50);
   else if(id==='WAR_04')return true;
   else if(id==='FIR_02')this.blast(e);
   // Projectile launch notifications must not create an explosion at the
   // frozen end point; impact is a separate authoritative contact event.
   else if(id==='FIR_01'&&e.phase==='impact')this.blast(e);
   else if(id==='FIR_04'){
    this.host.burst('fireCore',p,.1,1,.55+.05*r);
    this.host.burst('ember',p,.1,3+r,.7);
   }else if(id==='FIR_05'&&e.segment===0)this.add(e,'wave',e.duration??.30);
   else if(id==='THU_01'&&!e.targetId){
    if(this.thunderPatterns.get(e.castId)?.ground.size)return true;
    const g=skillVfxGeometry(e),far=offset(e.from,e.angle??0,0,g.lengthMetres??0);let end=far;
    if(this.host.visible?.(e.from,far)===false){let lo=0,hi=1;for(let i=0;i<9;i++){const mid=(lo+hi)/2;if(this.host.visible?.(e.from,mix(e.from,far,mid))===false)hi=mid;else lo=mid;}end=mix(e.from,far,lo);}
    this.add({...e,to:end,phase:'corridor'},'bolt',.18);
   }
   else if(id.startsWith('THU')&&e.to&&e.targetId)this.thunder(e);
   else if(id==='COM_01')this.add(e,'dash',.34);
   return true;
  }
  if(e.type==='skill_release'){
   if(['THU_01','THU_02','THU_04','THU_05'].includes(id))this.thunder(e);
   if(id==='WAR_03'||id==='FIR_03')return true;
   else if(id==='THU_03')this.add(e,'enchant',6,true);
   else if(id==='THU_06')this.add(e,'storm',3,true);
   else if(id==='BOW_07')this.add(e,'dash',.4);
   else if(id==='COM_01')this.add(e,'dash',.34);
   else if(id==='COM_02')return true;
   else if(id.startsWith('WAR'))this.add({...e,to:e.from,at:e.from},'metal',.14);
   else if(id.startsWith('BOW'))this.host.burst('dust',e.from,.8,2,.22,'#b8b9a4');
  }
  return true;
 }
 private blast(e:SkillEvent){
  const radius=skillVfxGeometry(e).radiusMetres??0;if(radius<=0)return;
  const p=this.point(e),rank=tier(e),scale=radius;
  if(e.skillId==='FIR_02'&&e.segment>0){this.host.burst('ember',p,.18,4+rank,.45);return;}
  this.add(e,'blast',e.skillId==='FIR_02'?4.55:1.85);
  this.host.burst('fireCore',p,.16,1,Math.min(1.1,scale*.28));
  this.host.burst('ember',p,.15,7+rank*2,scale*.9);
  this.host.burst('impactScorch',p,.025,1,scale*.92);
 }
 /** Draw only current authoritative projectile positions. Frozen split paths are
  * represented by the moving child arrow, never by a pre-drawn future curve. */
 projectile(p:ProjectileState,time:number):boolean{
  const meta=p as ProjectileState&{skillId?:string;rank?:number;segment?:number;child?:boolean;width?:number};
  if(!meta.skillId||!/^(WAR|BOW|FIR)_/.test(meta.skillId))return false;
  const r=tier(meta),a=p.angle,family=meta.skillId.slice(0,3),height=family==='FIR'?.85:.82;
  let trail=this.trails.get(p.id);if(!trail){trail={points:[],time,visual:[],castId:p.castId};this.trails.set(p.id,trail);}
  trail.time=time;if(!trail.points.length||distance(trail.points[0],p)>.035){trail.points.unshift({x:p.x,z:p.z});trail.visual?.unshift(this.host.projectileAt?.(p,family==='BOW'?1.05:height)??this.host.at(p,family==='BOW'?1.05:height));}
  // A redirect is a new leg of this same physical arrow, never a child fan.
  const split=false;
  const limit=family==='BOW'?(meta.skillId==='BOW_02'?2.8:1.05):family==='WAR'?1.55:1.05;
  let length=0;for(let i=1;i<trail.points.length;i++){
   const step=distance(trail.points[i-1],trail.points[i]);
   if(length+step>limit){trail.points[i]=mix(trail.points[i-1],trail.points[i],(limit-length)/Math.max(.0001,step));trail.points.length=i+1;break;}
   length+=step;
  }trail.points.length=Math.min(split?56:meta.skillId==='BOW_02'?32:14,trail.points.length);
  if(trail.visual)trail.visual.length=Math.min(trail.visual.length,trail.points.length);
  if(family==='BOW'){
   this.host.body(p);
   const color=ARROW_COLORS.body;trail.bow={split,rank:r,color,chaining:meta.skillId==='BOW_02'};trail.ended=false;
   drawArrowWake(this.host,trail.points,color,split,r,trail.visual,1,trail.bow.chaining);
  }else if(family==='WAR'){
   const span=meta.width??values(r,meta.skillId==='WAR_05'?[2.4,2.8,3.2,3.8,4.4]:[.8,1,1.15,1.35,1.6]);
   this.arc(p,a,span,SILVER,240);
   this.host.line(trail.points.map(q=>this.host.at(q,.75)),SILVER,.024,145);
   // Sparse directional gold scratches stay behind the single silver blade.
   for(let i=0;i<Math.ceil(r/2);i++){
    const side=(i-(Math.ceil(r/2)-1)/2)*span*.32;
    this.stroke(offset(p,a,side,-.15),offset(p,a,side,-.48-.04*r),GOLD,.016,165,.68);
   }
  }else{
   this.host.fireProjectile?.('flame:'+p.id,p,height,a,1.28+.09*r,time);
   // The shared moving wisps supply the complete wake; only sparse sparks
   // remain outside it, with no opaque rolling cloud or straight red beam.
   this.host.loop('skill:ember:'+p.id,'ember',p,height,.18);
  }
  return true;
 }
 private bolt(e:SkillEvent,alpha:number,source?:Vec3,pulse=0){drawLightning(this.host,e,alpha,this.now,source,pulse);}
 /** Each real damage beat owns one short discharge. A near-to-far brightness
  * front exposes the sparse path; it never delays or invents gameplay contacts.
  * The independently timed ground patches survive the air arcs and cast end. */
 private updateThunder(game:GameSession){
  const residualLife=2.6;
  for(const pattern of Array.from(this.thunderPatterns.values()).sort((a,b)=>b.start-a.start)){
   const age=this.now-pattern.start;
   let lastContact=pattern.start;for(const point of pattern.ground.values())lastContact=Math.max(lastContact,point.time);
   if(this.now-lastContact>=residualLife){this.thunderPatterns.delete(pattern.castId);continue;}
   const chain=pattern.skillId==='THU_02',network=['THU_02','THU_04','THU_05'].includes(pattern.skillId);
   const rank=PURE_SKILLS[pattern.skillId]?.ranks[pattern.rank-1],reach=rank?.connectionRadiusMetres??rank?.geometry?.radiusMetres??0;
   const nodePoint=(id:string|undefined,frozen:Point)=>{const enemy=id?game.state.enemies.find(e=>e.id===id&&e.hp>0):undefined;return enemy?{x:enemy.x,z:enemy.z}:frozen;};
   const beatStrength=pattern.skillId==='THU_05'?[.91,.76,1][Math.min(2,pattern.segment)]:1;
   const light=(depth:number,entry=false)=>{
    const duration=entry?.125:chain?.17:.18;if(age<0||age>=duration)return 0;
    const attack=Math.min(1,(age+.012)/.022),fade=Math.pow(Math.max(0,1-age/duration),.66);
    const front=Math.min(.055,depth*(chain?.012:.009)),accent=Math.exp(-Math.pow((age-front)/.038,2));
    return Math.round(250*beatStrength*attack*fade*(entry?1:.38+.62*accent));
   };
   if(age<.18){
    for(const edge of pattern.edges.values()){
     const e=edge.event,entry=!e.sourceId,depth=pattern.depths.get(e.targetId??'')??0,alpha=light(depth,entry);if(alpha<=0)continue;
     const from=nodePoint(e.sourceId,e.from),to=nodePoint(e.targetId,e.to??e.from);
     if(network&&e.sourceId&&(distance(from,to)>reach+.001||this.host.visible?.(from,to)===false))continue;
     if(entry&&pattern.caster&&distance(e.from,pattern.caster)<.01)edge.sourceAnchor=(this.host.playerCastHand?.()??this.host.playerHand?.())?.clone()??edge.sourceAnchor;
     this.bolt({...e,from,to},pattern.skillId==='THU_04'&&e.sourceId?Math.round(alpha*.68):alpha,edge.sourceAnchor,0);
    }
    if(age<.105)for(const [id,p]of pattern.nodes){
     const point=nodePoint(id,p),depth=pattern.depths.get(id)??0;
     this.bolt({type:'skill_hit',skillId:pattern.skillId,family:'THU',rank:pattern.rank,castId:pattern.castId,shape:'contact',from:point,to:point,targetId:id,segment:pattern.segment},Math.round(light(depth)*.86),undefined,0);
    }
    if(pattern.skillId==='THU_04'&&pattern.aim){
     drawThunderFan(this.host,'fan-front:'+pattern.castId+':'+pattern.segment,pattern.aim,pattern.angle??0,Array.from(pattern.nodes.values()),pattern.rank,this.reducedMotion?.065:age,pattern.segment,light(0)*.88);
    }
    // The last real ultimate beat has a brief vertical contact accent. It
    // belongs to the same hit, adds no target, ground circle or extra damage.
    if(pattern.skillId==='THU_05'&&pattern.segment===2&&age<.09){
     const root=Array.from(pattern.edges.values()).find(edge=>!edge.event.sourceId)?.event;
     if(root?.to){const p=nodePoint(root.targetId,root.to),alpha=light(0);
      const points=[this.host.at(p,3.2+pattern.rank*.06),this.host.at({x:p.x+.10,z:p.z-.07},2.25),this.host.at(p,1.05)];
      this.host.line(points,THUNDER_COLORS.core,.065,alpha,true,'core');this.detail(points,THUNDER_COLORS.body,.26,alpha*.35,'glow');
     }
    }
   }
   if(!this.host.thunderGround)continue;
   for(const [id,point]of pattern.ground){
    const elapsed=this.now-point.time;if(elapsed<0||elapsed>=residualLife)continue;
    const t=elapsed/residualLife,fade=1-Math.pow(Math.max(0,(t-.42)/.58),1.2);
    const charge=this.reducedMotion?1:.94+.06*Math.sin(elapsed*17);
    const radius=pattern.skillId==='THU_05'?.90+.08*pattern.rank:.64+.055*pattern.rank;
    this.host.thunderGround('thunder-hit:'+pattern.castId+':'+id,point.p,radius,Math.round((175+pattern.rank*5)*fade*charge),this.reducedMotion?0:t);
   }
  }
 }
 /** Buffs follow real shared charge/ward state, so echoed events cannot
  * create another set of charge marks or guard layers. */
 private updateThunderSupport(game:GameSession){
  const b=game.state.combat.buffs,p=game.state.player,hand=this.host.playerHand?.();
  const charges=Math.max(0,Math.min(3,Math.round(b.thunderCharges??0)));
  if(hand&&charges>0&&(b.thunderUntil??0)>this.now){
   const a=game.state.action,firing=!!a&&a.kind==='staff'&&a.emitted;
   drawThunderCharge(this.host,'player:thunder-charge',hand,charges,b.thunderRank??1,this.now,firing,this.reducedMotion);
  }
  const left=(b.stormWardUntil??0)-this.now,active=left>0;
  if(active){
   const hit=this.cues.find(c=>c.kind==='stormHit'&&this.now-c.start<c.duration);
   const impact=hit?Math.pow(1-(this.now-hit.start)/hit.duration,1.4):0;
   const opacity=((b.stormWardReduction??0)>0?155:68)+impact*110;
   const intro=Math.min(1,(3-left+.015)/.10),fade=Math.min(1,left/.32);
   drawThunderGuard(this.host,'player:storm-ward',p,p.angle,1,this.now,opacity*Math.max(0,intro)*fade,impact,false,this.reducedMotion);
  }

 }
 inspectThunder(){return Array.from(this.thunderPatterns.values()).map(pattern=>({castId:pattern.castId,skillId:pattern.skillId,segment:pattern.segment,age:this.now-pattern.start,edges:pattern.edges.size,nodes:pattern.nodes.size,ground:pattern.ground.size,pulseWindows:[[0,.18]],expiresAt:Math.max(pattern.start,...Array.from(pattern.ground.values()).map(point=>point.time))+2.6}));}
 private wall(c:Cue,progress:number,alpha:number){
  const e=c.event,rank=tier(e),p=this.point(e),wave=c.kind==='wave',after=c.kind==='afterglow',field=c.kind==='field';
  if(e.skillId==='FIR_04'){
   const g=skillVfxGeometry(e),cooling=c.coolingAt===undefined?0:Math.min(1,(this.now-c.coolingAt)/1.8);
   this.host.groundJets?.('jet:'+e.castId,e.from,e.angle??0,g.lengthMetres??0,g.widthMetres??0,this.now-c.start,Math.pow(1-cooling,1.12),true,cooling);return;
  }
  const a=(e.angle??heading(e.from,p))+(wave||after||field?0:Math.PI/2);
  // placedStrip's long axis is forward; the advancing fire wave's long axis
  // is transverse. Keep those different authored rectangles visible.
  const geometry=skillVfxGeometry(e),width=(wave||after||field?geometry.widthMetres:geometry.lengthMetres)??0;
  const depth=(wave||after||field?geometry.depthMetres:geometry.widthMetres)??0;if(width<=0||depth<=0)return;
  if(c.coolingAt!==undefined){
   const cooling=Math.min(1,Math.max(0,(this.now-c.coolingAt)/1.8));
   const fade=Math.pow(1-cooling,1.12);
   this.host.fireRibbon?.(`${field||after?'bed':'cooling'}:${e.castId}`,p,width,depth,a,this.now,(field?.82:.86)*fade,p,cooling);return;
  }
  const steps=Math.min(7,Math.max(3,Math.ceil(width/1.6))),front=wave?(progress*depth-depth/2):0;
  if(after||field){
   const filledDepth=field?depth*Math.min(1,(this.now-c.start)/.30):depth,center=field?offset(p,a,0,(filledDepth-depth)/2):p;
   const fade=field?1:Math.min(1,(1-progress)*6),opacity=(after?.74:.82)*fade;
   if(filledDepth>0)this.host.fireRibbon?.(`bed:${e.castId}`,center,width,filledDepth,a,this.now,opacity,p);
   return;
  }
  if(this.host.fireRibbon){
   // A persistent wall or advancing front is one continuous low rolling strip,
   // rather than a row of full explosion clouds. Its centre follows only the
   // already resolved front; the authoritative rectangle and ticks stay intact.
   const opacity=(wave?.92:.86)*(wave?Math.min(1,(1-progress)*8):1);
   const bandDepth=wave?Math.min(depth,1.1,2*Math.min(front+depth/2,depth/2-front)):depth;
   if(bandDepth>0)this.host.fireRibbon(`field:${e.castId}:${e.segment}`,offset(p,a,0,front),width,bandDepth,a,this.now,opacity,p);
   return;
  }
  for(let i=0;i<steps;i++){
   const q=offset(p,a,((i+.5)/steps-.5)*width,front),size=(wave?.75:.62)+rank*.035;
   if(this.host.fireVolume)this.host.fireVolume(`wall:${e.castId}:${e.segment}:${i}`,q,width/steps*.54,rank,.30+.12*Math.sin(this.now*4+i),.80);
   else this.host.fireSprite?.(`wall:${e.castId}:${e.segment}:${i}`,q,.03,width/steps*1.18,width/steps*1.18*432/768,(i+Math.floor(this.now*7))%3===0?2:1,.70+.08*Math.sin(this.now*11+i));
   if(i%2===0)this.host.loop(`skill:wallCore:${e.castId}:${e.segment}:${i}`,'fireCore',q,.10,.33+.03*rank);
   // A rectangular field is visibly filled at foot level, never a round disc.
   if(!wave&&depth>1.2){const back=offset(q,a,0,-depth*.27);this.host.loop(`skill:wallLow:${e.castId}:${e.segment}:${i}`,'flame',back,.08,.47);}
  }
  if(progress<.35){
   const l=offset(p,a,-width*.5,front),r=offset(p,a,width*.5,front);
   this.stroke(l,r,FIRE_PALETTE.highlight,.045,Math.min(130,alpha),.075);
  }
 }
 update(game:GameSession){
  this.now=game.state.time;const player=game.state.player;
  this.updateThunder(game);
  this.updateThunderSupport(game);
  for(const [id,clue] of this.clues){
   const elapsed=this.now-clue.start;if(elapsed>=clue.duration){this.clues.delete(id);continue;}
   const alpha=Math.round(175*Math.min(1,(clue.duration-elapsed)*2));
   for(const side of [-1,1])for(const end of [-1,1]){
    const corner={x:clue.p.x+side*.32,z:clue.p.z+end*.32};
    this.host.line([this.host.at({x:corner.x-side*.13,z:corner.z},.08),this.host.at(corner,.08),this.host.at({x:corner.x,z:corner.z-end*.13},.08)],'#e2c68b',.022,alpha);
   }
  }
  for(const c of this.cues){
   if((c.kind==='wall'||c.kind==='field')&&c.event.skillId.startsWith('FIR')&&c.coolingAt===undefined&&this.now>=c.start+c.duration){
    c.coolingAt=c.start+c.duration;c.duration+=1.8;
   }
  }
  this.cues=this.cues.filter(c=>this.now-c.start<c.duration);
  for(const c of this.cues){
   const e=c.event,rank=tier(e),age=this.now-c.start,t=Math.max(0,Math.min(1,age/c.duration)),p=this.point(e),a=e.angle??heading(e.from,p);
   const pressureWave=c.kind==='cross'||c.kind==='meleeSweep'&&(e.skillId==='WAR_01'||e.skillId==='WAR_05');
   const alpha=pressureWave?245:['meleeSweep','cross'].includes(c.kind)?Math.round(245*(t<.65?1:Math.pow((1-t)/.35,1.1))):Math.round(225*Math.pow(1-t,1.7));
   if(c.kind==='trap'){
    if(!game.state.combat.casts.some(cast=>cast.id===e.castId&&(cast.zoneUntil??0)>this.now))continue;
    const radius=skillVfxGeometry(e).radiusMetres??1.8,armed=age>=.3,opacity=armed?155:75;
    const loop:Vec3[]=[];for(let i=0;i<=24;i++){const angle=i*TAU/24;loop.push(this.host.at(offset(p,0,Math.cos(angle)*.48,Math.sin(angle)*.32),.07));}this.host.line(loop,GOLD,.024,opacity);
    for(let i=0;i<4;i++){const angle=i*TAU/4,q=offset(p,angle,0,.62);this.stroke(q,offset(q,angle,0,.16),SILVER,.034,opacity,.09);const edge=offset(p,angle,0,radius);this.stroke(offset(edge,angle,-.11,0),offset(edge,angle,.11,0),ARROW,.014,55,.035);}
    this.stroke(offset(p,0,-.45,-.25),offset(p,0,.45,.25),ARROW,.018,opacity,.06);this.stroke(offset(p,0,.45,-.25),offset(p,0,-.45,.25),ARROW,.018,opacity,.06);continue;
   }
   if(c.kind==='snare'){
    const target=e.targetId?game.state.enemies.find(enemy=>enemy.id===e.targetId&&enemy.hp>0):undefined,q=target??p;
    for(let i=0;i<3;i++){const side=(i-1)*.13;this.host.line([this.host.at(offset(q,a,-.36,side),.08),this.host.at(offset(q,a,0,side+.12),.24),this.host.at(offset(q,a,.36,side),.08)],GOLD,.024,alpha);}continue;
   }
   if(c.kind==='storm'||c.kind==='stormHit'||c.kind==='enchant'||c.kind==='ward')continue;
   if(c.kind==='thunderThird'){
    const enemy=game.state.enemies.find(n=>n.id===e.targetId&&n.hp>0);
    drawThunderThirdContact(this.host,'third-contact:'+e.castId,enemy??p,rank,t);continue;
   }
   if(c.kind==='bolt'){
    if(e.skillId.startsWith('FIR')){if(e.to)this.stroke(e.from,e.to,FIRE,.04,Math.round(alpha*.7),.16);}
    else {
     const cast=game.state.combat.casts.find(cast=>cast.id===e.castId);
     if(!c.sourceAnchor&&e.phase!=='network'&&cast&&distance(e.from,cast.from)<.01&&e.to&&distance(e.from,e.to)>.1)c.sourceAnchor=(this.host.playerCastHand?.()??this.host.playerHand?.())?.clone();
     this.bolt(e,alpha,c.sourceAnchor);
    }continue;
   }
   if(c.kind==='meleeSweep'){
    const g=skillVfxGeometry(e),radius=g.radiusMetres??0,span=(g.angleDegrees??0)*Math.PI/180;
    const count=PURE_SKILLS[e.skillId]?.ranks[rank-1]?.authoredDamageHits??1,stage=e.segment===count-1&&count>=3?3:e.segment%2+1;
    if(e.skillId==='WAR_05'&&stage===3&&this.host.warriorUltimate){this.host.warriorUltimate(`strike:${e.skillId}:${e.castId}:${e.segment}`,e.from,a,rank,age);continue;}
    drawMeleeSweep(this.host,`strike:${e.skillId}:${e.castId}:${e.segment}`,e.from,a,radius,span,stage,t,Math.round(alpha*1.12));
    if(!this.reducedMotion&&e.segment>0&&t<.32){
     const previous=this.cues.find(q=>q.kind==='meleeSweep'&&q.event.castId===e.castId&&q.event.segment===e.segment-1);
     if(previous)drawMeleeSweep(this.host,`echo:${e.castId}:${e.segment}`,previous.event.from,a,radius,span,e.segment%2?1:2,1,Math.round(40*(1-t/.32)));
    }
    continue;
   }
   if(c.kind==='blast'){
    // Keep one actual contact frame at the resolved impact point. The drop
    // ends with the cast action, so it otherwise disappears just before its
    // leading nose reaches the seal. This is presentation at the existing hit
    // time, not an early landing, a second hit, or a new animation clock.
    if(e.skillId==='FIR_02'&&e.segment===0&&age<.045)this.host.meteor?.('meteor:'+e.castId,p,rank,1-1e-6,this.now);
    if(e.skillId==='FIR_02'&&e.segment===0){
     // Keep the same anchored sigil under the impact and sustained fire. Its
     // final fade follows this existing cue's game clock, including pause.
     const hold=Math.min(3.3,c.duration*.75),tail=Math.max(.001,c.duration-hold),q=Math.max(0,Math.min(1,(age-hold)/tail));
     this.host.meteorSeal?.('meteor-seal:'+e.castId,p,skillVfxGeometry(e).radiusMetres??0,.9*(1-q*q*(3-2*q)));
    }
    const radius=skillVfxGeometry(e).radiusMetres??0,peak=e.skillId==='FIR_02'?.55:.30;
    const progress=age<peak?.68*age/peak:.68+.32*Math.min(1,(age-peak)/(c.duration-peak));
    let presented=progress;
    if(e.skillId==='FIR_02'){
     const roll=(at:number)=>.22+.13*(.5-.5*Math.cos((at-.18)*Math.PI*2/.66));
     if(age<.18)presented=.22*age/.18;
     else if(age<1.20)presented=roll(age);
     else if(age<1.65){const q=(age-1.20)/.45,s=q*q*(3-2*q);presented=roll(1.20)+(.68-roll(1.20))*s;}
     else presented=.68+.32*Math.min(1,(age-1.65)/(c.duration-1.65));
    }
    this.host.fireVolume?.(`impact:${e.castId}:${e.segment}`,p,radius,rank,presented,.96*(e.skillId==='FIR_02'&&e.segment>0?.65:1),a,age,c.duration);
    continue;
   }
   if(c.kind==='wall'||c.kind==='wave'||c.kind==='afterglow'||c.kind==='field'){this.wall(c,t,alpha);continue;}
   if(c.kind==='mark'||c.kind==='burn'){
    const enemy=game.state.enemies.find(n=>n.id===e.targetId&&n.hp>0);if(!enemy)continue;
    const status=game.state.combat?.statuses[enemy.id];
    if(c.kind==='mark'){if(e.skillId==='BOW_04'&&!(status?.hunterMarkUntil>this.now))continue;this.scratch(enemy,enemy.angle,rank,'#c4c5ac',95,.88);}
    else if(status?.burnUntil>this.now)this.host.loop('skill:burn:'+e.targetId,'flame',enemy,.23,.22+.025*rank,'#dc7a32');continue;
   }
   if(c.kind==='metal'&&e.skillId==='WAR_P1'){this.host.warriorPulse?.('passive:'+e.skillId+':'+e.castId,player,player.angle,t,alpha);continue;}
   if(c.kind==='metal'&&['WAR_01','WAR_02','WAR_04','WAR_05'].includes(e.skillId)){if(e.type==='skill_hit')drawMeleeContact(this.host,'hit:'+e.castId+':'+e.segment+':'+(e.waveIndex??'cut')+':'+e.targetId,p,a,e.skillId==='WAR_05'&&e.segment===2?2:1,t,this.reducedMotion);continue;}
   if(c.kind==='metal'){
    if(e.skillId.startsWith('THU'))this.bolt({...e,from:p,to:p},alpha);
    else {
     this.scratch(p,a,rank,SILVER,alpha,.76);
     if(e.targetId){
      drawMeleeContact(this.host,`contact:${e.castId}:${e.targetId}:${e.segment}`,p,a,1+rank*.16,t,this.reducedMotion);

     }
    }continue;
   }
   if(c.kind==='heal'){
    for(let i=0;i<2+Math.ceil(rank/2);i++){
     const side=(i%2?1:-1)*(.19+Math.floor(i/2)*.08),q=offset(player,player.angle,side,0),h=.43+t*.35+i*.07;
     this.host.line([this.host.at(q,h-.08),this.host.at(offset(q,player.angle,.035,0),h),this.host.at(q,h+.08),this.host.at(offset(q,player.angle,-.035,0),h),this.host.at(q,h-.08)],'#ecdeb0',.016,Math.round(alpha*.65));
    }continue;
   }
   if(c.kind==='dash'){
    const key='dash:'+e.castId;let path=this.trails.get(key);if(!path){path={points:[{...e.from}],time:this.now};this.trails.set(key,path);}
    path.time=this.now;path.points.push({x:player.x,z:player.z});if(path.points.length>24)path.points.splice(0,path.points.length-24);
    this.host.line(path.points.map(q=>this.host.at(q,.09)),'#d0e9e2',.035,Math.round(alpha*.55));
    if(path.points.length>2)for(let i=0;i<Math.min(rank,4);i++){const q=path.points[Math.floor(i*(path.points.length-1)/Math.max(1,Math.min(rank,4)))];this.stroke(offset(q,player.angle,-.06,0),offset(q,player.angle,.06,-.14),'#c2dad7',.018,Math.round(alpha*.45),.1);}continue;
   }
   if(c.kind==='jetCharge'){
    if(game.state.action?.id!==e.castId)continue;
    const g=skillVfxGeometry(e);this.host.groundJets?.('jet:'+e.castId,e.from,e.angle??0,g.lengthMetres??0,g.widthMetres??0,age,Math.min(1,age/.12),false,0);continue;
   }
   if(c.kind==='drop'){
    if(game.state.action?.id!==e.castId)continue;
    this.host.meteorSeal?.('meteor-seal:'+e.castId,p,skillVfxGeometry(e).radiusMetres??0,Math.min(1,age/.16)*.9);
    if(age>=.30)this.host.meteor?.('meteor:'+e.castId,p,rank,Math.max(0,(age-.30)/Math.max(.1,c.duration-.30)),this.now);
    continue;
   }
   if(c.kind==='cross'&&this.host.warriorCross){const g=skillVfxGeometry(e),contact=this.cues.find(q=>q.kind==='metal'&&q.event.castId===e.castId&&q.event.targetId);this.host.warriorCross('cross:'+e.castId,contact?this.point(contact.event):p,a,g.lengthMetres??1.6,t,alpha);continue;}
   if(c.kind==='cross'){
    const g=skillVfxGeometry(e),length=g.lengthMetres??0,cuts=g.anglesDegrees??[];
    const directions=cuts;
    for(const degrees of directions){const angle=a+degrees*Math.PI/180,start=offset(p,angle,0,-length*.5),end=offset(p,angle,0,length*.5);
     const tip=mix(start,end,Math.min(1,t*8));
     this.host.line([this.host.at(start,.72),this.host.at(tip,.72)],GOLD,.30,Math.round(alpha*.22),true,'glow');
     if(this.host.slash)this.host.slash(`cross:${e.castId}:${e.segment}:${degrees}`,this.host.at(start,.84),this.host.at(tip,.84),Math.min(g.widthMetres??.3,.28+.02*rank),alpha,t);
     this.host.line([this.host.at(start,.86),this.host.at(tip,.86)],'#fff9e9',.045,alpha,true,'core');
     this.scratch(tip,angle,Math.ceil(rank/2),GOLD,alpha,.55);
    }continue;
   }
   if(c.kind==='cleave'){
    if(e.segment===0){
     const h=2.75-t*1.25,edge=[this.host.at(offset(p,a,0,-.20),h),this.host.at(p,.15)];
     this.host.line(edge,GOLD,.34,Math.round(alpha*.23),true,'glow');
     if(this.host.slash)this.host.slash(`cleave:${e.castId}:${e.segment}`,edge[0],edge[1],.40+.025*rank,Math.round(alpha*Math.min(1,(1-t)*2)),t);
     this.host.line(edge,'#fff9e9',.06,alpha,true,'core');
    }
    const radius=skillVfxGeometry(e).radiusMetres??0;
    for(let k=0;k<4;k++){
     const angle=a+(k-1.5)*.78,points:Vec3[]=[];
     for(let i=0;i<=5;i++){const q=offset(p,angle,i===5?0:(i%2?.06:-.06),i/5*radius*Math.min(1,t*4));points.push(this.host.at(q,.065));}
     this.host.line(points,GOLD,.022,Math.round(alpha*.65));
     if(t<.48)this.detail(points,'#f5e8bd',.14,Math.round(alpha*.18),'glow');
    }
   }
  }
  for(const [id,path]of this.trails){
   const age=this.now-path.time,ttl=path.bow?.chaining ? .38 : .24;
   if(path.bow&&(path.ended||age>.0001)&&age<ttl){
    drawArrowWake(this.host,path.points,path.bow.color,path.bow.split,path.bow.rank,path.visual,Math.pow(1-age/ttl,1.5),path.bow.chaining);
   }
   if(age>(path.bow?ttl:.4))this.trails.delete(id);
  }
  this.arrowLegs=this.arrowLegs.filter(leg=>this.now-leg.time<.40);
  for(const leg of this.arrowLegs){
   const fade=.52*Math.pow(1-(this.now-leg.time)/.40,1.1);
   drawArrowWake(this.host,leg.points,leg.color,false,leg.rank,leg.visual,fade,true);
  }
 }
 clear(preserveCues=false){
  // Resume anchored shields/marks/fields from the same session clock; transient
  // contacts are discarded so a menu cannot replay their flashes or bursts.
  this.cues=preserveCues?this.cues.filter(c=>['enchant','mark','burn','ward','wall','wave','field','blast','drop','jetCharge'].includes(c.kind)||c.kind==='meleeSweep'&&c.event.skillId==='WAR_05'&&c.event.segment===2):[];
  this.trails.clear();this.arrowLegs=[];if(!preserveCues){this.seen.clear();this.clues.clear();this.thunderPatterns.clear();}
 }
}
