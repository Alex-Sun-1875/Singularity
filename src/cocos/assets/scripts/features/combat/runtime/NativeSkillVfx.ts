import {Vec3} from 'cc';
import type {CombatSkillEvent,GameEvent,Point} from '../../../core/Contracts';
import type {GameSession,ProjectileState} from '../../../core/GameSession';
import {PURE_SKILLS,type SkillGeometry} from '../data/PureSkills';
import type {VfxKind,VfxLineStyle} from '../../../shared/assets/VfxAssets';
import {skillVfxGeometry} from '../data/SkillVfxGeometry';
import {drawMeleeSweep,drawMeleeContact} from './MeleeSkillEffects';
import {drawLightning,drawArrowWake,drawArrowContact,THUNDER_COLORS} from './SkillEnergyStrokes';

/** Gameplay geometry and victim identities come from core events. Electrical
 * echoes may follow those same identities; they never select targets, advance
 * projectiles, or submit damage. All timers use the session clock. */
export interface SkillPreview {
 target:Point;valid:boolean;skillId?:string;rank?:number;angle?:number;
 geometry?:Partial<SkillGeometry>&{type?:string;radius?:number;length?:number;width?:number;depth?:number;angle?:number;angles?:number[]};
}
type SkillEvent=CombatSkillEvent;
export interface SkillVfxHost {
 at(p:Point,height?:number):Vec3;
 line(points:Vec3[],color:string,width?:number,alpha?:number,taper?:boolean,style?:VfxLineStyle):void;
 detailLine?(points:Vec3[],color:string,width?:number,alpha?:number,style?:VfxLineStyle):void;
 burst(kind:VfxKind,p:Point,height:number,count:number,scale?:number,color?:string,angle?:number):void;
 loop(key:string,kind:VfxKind,p:Point,height:number,scale?:number,color?:string):unknown;
 body(p:ProjectileState):void;
 projectileAt?(p:ProjectileState,height:number):Vec3;
 playerHand?():Vec3|undefined;
 visible?(from:Point,to:Point):boolean;
 blade?(key:string,p:Point,height:number,angle:number,radius:number,span:number,width:number,alpha:number,progress:number,normal?:Vec3):void;
 slash?(key:string,start:Vec3,end:Vec3,width:number,alpha:number,progress:number):void;
 fireSprite?(key:string,p:Point,height:number,width:number,tall:number,phase:number,alpha:number):void;
 fireProjectile?(key:string,p:Point,height:number,angle:number,size:number,time:number):void;
 meteor?(key:string,p:Point,rank:number,progress:number,time:number):void;
 firePlume?(key:string,p:Point,height:number,size:number,time:number,alpha:number):void;
 fireVolume?(key:string,p:Point,radius:number,rank:number,progress:number,alpha:number):void;
 fireRibbon?(key:string,p:Point,width:number,depth:number,angle:number,time:number,alpha:number,origin?:Point):void;
 thunderGround?(key:string,p:Point,radius:number,alpha:number,phase:number):void;
 thunderContact?(key:string,center:Vec3,rank:number,alpha:number,time:number):void;
 thunderField?(key:string,points:readonly Point[],rank:number,alpha:number,pulse:number):void;
}
type Cue={event:SkillEvent;start:number;duration:number;sourceAnchor?:Vec3;kind:'cross'|'cleave'|'drop'|'bolt'|'wall'|'wave'|'afterglow'|'shield'|'guardHit'|'enchant'|'mark'|'heal'|'dash'|'metal'|'burn'|'ward'|'meleeSweep'|'blast'|'field'|'trap'|'snare'|'storm'};
type Trail={points:Point[];time:number;visual?:Vec3[];bow?:{split:boolean;rank:number;color:string};ended?:boolean};
type ThunderPattern={castId:string;skillId:string;rank:number;segment:number;start:number;edges:Map<string,{event:SkillEvent;sourceAnchor?:Vec3}>;nodes:Map<string,Point>;ground:Map<string,{p:Point;time:number}>};
const SILVER='#e5f2ee',GOLD='#d5b46a',ARROW='#dce5d3',FIRE='#fa913d',LIGHTNING=THUNDER_COLORS.body,VIOLET=THUNDER_COLORS.halo;
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
   pattern={castId:e.castId,skillId:e.skillId,rank:tier(e),segment:e.segment,start:this.now,edges:new Map(),nodes:new Map(),ground:new Map()};this.thunderPatterns.set(e.castId,pattern);
  }
  if(pattern.segment!==e.segment){pattern.segment=e.segment;pattern.start=this.now;pattern.edges.clear();pattern.nodes.clear();}
  if(e.targetId&&e.to)pattern.nodes.set(e.targetId,{...e.to});
  if(contact&&e.targetId)pattern.ground.set(e.targetId,{p:{...this.point(e)},time:this.now});
  if(e.sourceId)pattern.nodes.set(e.sourceId,{...e.from});
  if(!contact&&e.to){
   const event={...e,from:{...e.from},to:{...e.to}};
   pattern.edges.set(`${e.sourceId??'entry'}:${e.targetId}:${e.phase}`,{event});
  }
 }
 private add(e:SkillEvent,kind:Cue['kind'],duration:number,keyed=false){
  const g=skillVfxGeometry(e),snapshot={...e,geometry:g,radius:g.radiusMetres,width:g.widthMetres,length:g.lengthMetres,depth:g.depthMetres,angleDegrees:g.angleDegrees,anglesDegrees:g.anglesDegrees,from:{...e.from},to:e.to?{...e.to}:undefined,at:e.at?{...e.at}:undefined};
  if(keyed){
   this.cues=this.cues.filter(c=>!(c.kind===kind&&(
    kind==='shield'||kind==='enchant'||kind==='burn'&&c.event.targetId===e.targetId||
    c.event.castId===e.castId&&c.event.targetId===e.targetId)));
  }
  // Continuous visuals and short contacts have separate native pools. Old visual
  // records can be dropped without affecting any authoritative gameplay object.
  if(this.cues.length>=112)this.cues.splice(this.cues.findIndex(c=>c.kind!=='shield'&&c.kind!=='wall'&&c.kind!=='enchant'),1);
  this.cues.push({event:snapshot,start:this.now,duration:Math.max(.06,duration),kind});
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
   const final=e.skillId==='WAR_05'&&e.segment===2||e.skillId==='WAR_01'&&e.segment===2;
   this.host.burst('spark',p,.7,4+r*2+(final?3:0),.65+.06*r,GOLD);this.host.burst('flash',p,.75,1,(.43+.04*r)*(final?1.16:1),SILVER);
   this.add(e,'metal',.16+.008*r);if(r>=3)this.host.burst('dust',p,.08,3+r,.7);
  }else if(family==='BOW'){
   const path=e.projectileId?this.trails.get(e.projectileId):undefined;
   if(path?.bow){
    // A true contact can complete the last travelled centimetres. It never
    // draws the frozen future path before the projectile reaches this point.
    if(distance(path.points[0]??p,p)>.02){path.points.unshift({...p});path.visual?.unshift(this.host.at(p,1.05));}
    path.time=this.now;path.ended=true;
   }
   drawArrowContact(this.host,p,a,r);
  }else if(family==='FIR'){
   this.host.burst('fireCore',p,.18,1,.65+.07*r);
   this.host.burst('ember',p,.22,3+r,.5+.04*r);
   if(e.skillId==='FIR_P2'&&e.to)this.add(e,'bolt',.18);
  }else if(family==='THU'){
   this.host.burst('flash',p,.85,1,.37+.035*r,LIGHTNING);
   if(['THU_01','THU_02','THU_04','THU_05'].includes(e.skillId))this.thunder(e,true);
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
  if(e.type==='skill_end'){this.cues=this.cues.filter(c=>c.event.castId!==e.castId);if(e.phase==='triggered')this.add(e,'snare',.4);return true;}
  // The core may publish multiple notifications for a contact, but a consumed
  // event batch or resumed menu must never manufacture a second visual strike.
  const recurring=['heal','defense','shieldHit'].includes(e.castId)?time.toFixed(4):'';
  const key=`${e.type}:${e.castId}:${e.segment}:${e.sourceId??''}:${e.targetId??''}:${e.phase??''}:${e.status??''}:${e.projectileId??''}:${recurring}:${e.from.x.toFixed(3)}:${e.from.z.toFixed(3)}:${e.to?.x.toFixed(3)??''}:${e.to?.z.toFixed(3)??''}`;
  if(this.seen.has(key))return true;this.seen.add(key);if(this.seen.size>768)this.seen.delete(this.seen.values().next().value!);
  if(e.type==='skill_cast'){
   if(id==='FIR_02')this.add(e,'drop',e.duration??.55);
   // Continuous hand charge follows the sampled player pose in Effects.
   return true;
  }
  if(e.type==='skill_hit'){this.contact(e);return true;}
  if(e.type==='skill_status'){
   if(e.status==='shieldHit'){
    this.add(e,'guardHit',e.duration??.15);
    this.host.burst(id==='FIR_03'?'ember':'spark',e.from,.85,2+r,.35,id==='FIR_03'?FIRE:GOLD);
   }else if(id==='COM_02'){
    // The initial three-second buff notice is not a fourth heal pulse.
    if((e.duration??0)<1){this.add(e,'heal',.7);this.host.burst('heal',e.from,.75,3+r,.9);}
   }
   else if(id==='COM_01'||id==='BOW_P2')this.add(id==='BOW_P2'?{...e,from:e.to??e.from}:e,'dash',e.duration??.32);
   else if(id==='WAR_03'||id==='FIR_03')this.add(e,'shield',e.duration??4,true);
   else if(e.status==='root')this.add(e,'snare',e.duration??.8,true);
   else if(id==='THU_03')this.add(e,'enchant',e.duration??6,true);
   else if(id==='THU_06'){if(e.status==='wardHit')this.host.burst('flash',e.from,.8,1,.45,LIGHTNING);else this.add(e,'storm',e.duration??3,true);}
   else if(id==='BOW_04'||id==='BOW_P1')this.add(e,'mark',e.duration??(id==='BOW_04'?8:.35),true);
   else if(id==='FIR_P1')this.host.burst('ember',p,.18,2+r,.3);
   else if(id==='FIR_P2'){this.add(e,'bolt',.22);this.host.burst('ember',p,.16,2+r,.4);}
   else if(e.status==='burn')this.add(e,'burn',e.duration??3,true);
   else if(id==='THU_P2')this.add(e,'ward',3,true);
   else if(id==='WAR_P1'||id==='WAR_P2'||id==='THU_P1')this.add(e,'metal',.22);
   return true;
  }
  if(e.type==='skill_zone'){
   if(id==='FIR_04')this.add(e,'wall',e.duration??4,true);else if(id==='BOW_06')this.add(e,'trap',e.duration??8,true);else if(id==='FIR_05')this.add(e,'field',e.duration??3.3,true);
   return true;
  }
  if(e.type==='skill_segment'){
   if(id==='WAR_01'||id==='WAR_05'){this.add(e,'meleeSweep',id==='WAR_05'&&e.segment===2?.28:.22);if(id==='WAR_05'&&e.segment===2)this.host.burst('dust',e.from,.06,7,.9,GOLD);}
   else if(id==='WAR_02')this.add(e,'cross',.22);
   else if(id==='WAR_04'){
    this.add(e,'cleave',.28);this.host.burst('dust',p,.1,6+r*2,.8+.14*r);
    this.host.burst('spark',p,.2,6+r*2,.85,GOLD);
   }else if(id==='FIR_02')this.blast(e);
   // Projectile launch notifications must not create an explosion at the
   // frozen end point; impact is a separate authoritative contact event.
   else if(id==='FIR_01'&&e.phase==='impact')this.blast(e);
   else if(id==='FIR_04'){
    this.host.burst('fireCore',p,.1,1,.55+.05*r);
    this.host.burst('ember',p,.1,3+r,.7);
   }else if(id==='FIR_05')this.add(e,e.segment===0?'wave':'afterglow',e.duration??.36);
   else if(id==='THU_01'&&!e.targetId){
    const g=skillVfxGeometry(e),far=offset(e.from,e.angle??0,0,g.lengthMetres??0);let end=far;
    if(this.host.visible?.(e.from,far)===false){let lo=0,hi=1;for(let i=0;i<9;i++){const mid=(lo+hi)/2;if(this.host.visible?.(e.from,mix(e.from,far,mid))===false)hi=mid;else lo=mid;}end=mix(e.from,far,lo);}
    this.add({...e,to:end,phase:'corridor'},'bolt',.18);
   }
   else if(id.startsWith('THU')&&e.to&&e.targetId)this.thunder(e);
   else if(id==='COM_01')this.add(e,'dash',.34);
   return true;
  }
  if(e.type==='skill_release'){
   if(id==='WAR_03'||id==='FIR_03')this.add(e,'shield',e.duration??4,true);
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
  this.add(e,'blast',e.skillId==='FIR_02'?.64:.34);
  this.host.burst('fireCore',p,.16,1,Math.min(1.1,scale*.28));
  this.host.burst('ember',p,.15,7+rank*2,scale*.9);
  this.host.burst('impactScorch',p,.025,1,scale*.92);
 }
 /** Draw only current authoritative projectile positions. Frozen split paths are
  * represented by the moving child arrow, never by a pre-drawn future curve. */
 projectile(p:ProjectileState,time:number):boolean{
  const meta=p as ProjectileState&{skillId?:string;rank?:number;segment?:number;child?:boolean;width?:number};
  if(!meta.skillId||!/^(WAR|BOW|FIR)_/.test(meta.skillId))return false;
  const r=tier(meta),a=p.angle,family=meta.skillId.slice(0,3),height=family==='FIR'?.62:.82;
  let trail=this.trails.get(p.id);if(!trail){trail={points:[],time,visual:[]};this.trails.set(p.id,trail);}
  trail.time=time;if(!trail.points.length||distance(trail.points[0],p)>.035){trail.points.unshift({x:p.x,z:p.z});trail.visual?.unshift(this.host.projectileAt?.(p,family==='BOW'?1.05:height)??this.host.at(p,family==='BOW'?1.05:height));}
  // A redirect is a new leg of this same physical arrow, never a child fan.
  const split=false;
  const limit=family==='BOW'?(meta.skillId==='BOW_02'?1.15:.72):family==='WAR'?1.55:1.05;
  let length=0;for(let i=1;i<trail.points.length;i++){
   const step=distance(trail.points[i-1],trail.points[i]);
   if(length+step>limit){trail.points[i]=mix(trail.points[i-1],trail.points[i],(limit-length)/Math.max(.0001,step));trail.points.length=i+1;break;}
   length+=step;
  }trail.points.length=Math.min(split?56:14,trail.points.length);
  if(trail.visual)trail.visual.length=Math.min(trail.visual.length,trail.points.length);
  if(family==='BOW'){
   this.host.body(p);
   const color=ARROW;trail.bow={split,rank:r,color};trail.ended=false;
   drawArrowWake(this.host,trail.points,color,split,r,trail.visual);
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
   this.host.loop('skill:fire-tail:'+p.id,'fireRoll',p,height,.48+.025*r);
   this.host.line(trail.visual??trail.points.map(q=>this.host.at(q,height)),'#ff762b',.12,90,true,'glow');
   this.host.loop('skill:ember:'+p.id,'ember',p,height,.18);
  }
  return true;
 }
 private bolt(e:SkillEvent,alpha:number,source?:Vec3,pulse=0){drawLightning(this.host,e,alpha,this.now,source,pulse);}
 /** Three separated discharges reuse the same authoritative graph. New real
  * beats replace that graph, so visual echoes never multiply damage or stack
  * several full graphs into the native Line budget. Ground light outlives it. */
 private updateThunder(game:GameSession){
  const starts=[0,.18,.40],lengths=[.105,.095,.14],strength=[1,.76,.92];
  for(const pattern of Array.from(this.thunderPatterns.values()).sort((a,b)=>b.start-a.start)){
   const age=this.now-pattern.start;if(age>=2){this.thunderPatterns.delete(pattern.castId);continue;}
   let pulse=-1,alpha=0;
   for(let i=0;i<starts.length;i++){
    const local=age-starts[i];if(local<0||local>=lengths[i])continue;
    const t=local/lengths[i],attack=Math.min(1,(local+.012)/.018);
    pulse=i;alpha=Math.round(245*strength[i]*attack*Math.pow(1-t,1.05));break;
   }
   if(pulse>=0&&alpha>0){
    if(pattern.skillId!=='THU_01'&&pattern.ground.size)this.host.thunderField?.(`${pattern.castId}:${pattern.segment}`,Array.from(pattern.ground.values()).map(hit=>hit.p),pattern.rank,alpha,pulse);
    const network=['THU_02','THU_04','THU_05'].includes(pattern.skillId),rank=PURE_SKILLS[pattern.skillId]?.ranks[pattern.rank-1],reach=rank?.connectionRadiusMetres??rank?.geometry?.radiusMetres??0;
    const nodePoint=(id:string|undefined,frozen:Point)=>{const enemy=id?game.state.enemies.find(e=>e.id===id&&e.hp>0):undefined;return network&&pulse>0&&enemy?{x:enemy.x,z:enemy.z}:frozen;};
    for(const edge of pattern.edges.values()){
     const e=edge.event;if(network&&pulse>0&&e.phase!=='network')continue;
     if(!edge.sourceAnchor&&e.phase!=='network'){
      const cast=game.state.combat.casts.find(c=>c.id===pattern.castId);
      if(cast&&distance(e.from,cast.from)<.01)edge.sourceAnchor=this.host.playerHand?.()?.clone();
     }
     // Follow only the already resolved pair. A fast beast must not run away
     // from its visual contact while the graph keeps flashing at empty air.
     const visual=network&&pulse>0?{...e,from:nodePoint(e.sourceId,e.from),to:nodePoint(e.targetId,e.to??e.from)}:e;
     if(network&&pulse>0&&(distance(visual.from,visual.to??visual.from)>reach+.001||this.host.visible?.(visual.from,visual.to??visual.from)===false))continue;
     this.bolt(visual,alpha,edge.sourceAnchor,pulse);
    }
    for(const [id,p]of pattern.nodes){const point=nodePoint(id,p);this.bolt({type:'skill_hit',skillId:pattern.skillId,family:'THU',rank:pattern.rank,castId:pattern.castId,shape:'contact',from:point,to:point,targetId:id,segment:pattern.segment},alpha,undefined,pulse);}
   }
   if(!this.host.thunderGround||!pattern.ground.size)continue;
   const points=Array.from(pattern.ground.values()),center={x:0,z:0};
   for(const point of points){center.x+=point.p.x;center.z+=point.p.z;}center.x/=points.length;center.z/=points.length;
   // The first real contact already owns the charged ground cloud. Do not
   // delay its opacity until after the opening discharge has almost ended.
   const fade=Math.min(1,(2-age)/.65),grow=1;
   for(const [id,point]of pattern.ground){
    const elapsed=this.now-point.time;if(elapsed>=2)continue;
    const localFade=Math.min(1,(2-elapsed)/.65),charge=1+.13*Math.sin(elapsed*23);
    this.host.thunderGround(`thunder-hit:${pattern.castId}:${id}`,point.p,.28+.025*pattern.rank,Math.round(150*localFade*grow*charge),elapsed/2);
   }
  }
 }
 inspectThunder(){return Array.from(this.thunderPatterns.values()).map(pattern=>({castId:pattern.castId,skillId:pattern.skillId,segment:pattern.segment,age:this.now-pattern.start,edges:pattern.edges.size,nodes:pattern.nodes.size,ground:pattern.ground.size,pulseWindows:[[0,.105],[.18,.275],[.40,.54]],expiresAt:pattern.start+2}));}
 private shield(e:SkillEvent,p:Point,a:number,alpha:number){
  const rank=tier(e),fire=e.skillId==='FIR_03',count=fire?Math.min(4,1+Math.ceil(rank/2)):Math.min(5,rank+1);
  for(let i=0;i<count;i++){
   const side=(i-(count-1)/2)*.16,q=offset(p,a,side,.30),h=.68+(i%2)*.17;
   const left=offset(q,a,-.085,0),right=offset(q,a,.085,0);
   if(fire){
    // Narrow bent feather and quill, attached to shoulder/arm. The metal guard
    // below has a different plate silhouette, rather than a recoloured shell.
    const lean=side<0?-.08:.08,tip=offset(q,a,lean,0);
    this.host.line([this.host.at(q,h-.15),this.host.at(left,h),this.host.at(tip,h+.27),this.host.at(right,h+.08),this.host.at(q,h-.15)],FIRE,.018,alpha);
    this.host.line([this.host.at(q,h-.12),this.host.at(tip,h+.23)],'#ffdb94',.012,Math.round(alpha*.75));
    this.host.line([this.host.at(left,h+.01),this.host.at(q,h+.06),this.host.at(right,h+.12)],FIRE,.011,Math.round(alpha*.65));
    this.host.firePlume?.(`guard:${e.castId}:${i}`,q,h-.18,.38+.025*rank,this.now+i*.13,alpha*.85);
   }else{
    // Open armour plates, anchored to chest and forearm, not a halo.
    this.host.line([this.host.at(left,h-.16),this.host.at(left,h+.13),this.host.at(q,h+.23),this.host.at(right,h+.13),this.host.at(right,h-.16)],SILVER,.022,alpha);
    this.stroke(q,offset(q,a,.055,.02),GOLD,.012,Math.round(alpha*.7),h+.09);
   }
  }
 }
 private wall(c:Cue,progress:number,alpha:number){
  const e=c.event,rank=tier(e),p=this.point(e),wave=c.kind==='wave',after=c.kind==='afterglow',field=c.kind==='field';
  const a=(e.angle??heading(e.from,p))+(wave||after||field?0:Math.PI/2);
  // placedStrip's long axis is forward; the advancing fire wave's long axis
  // is transverse. Keep those different authored rectangles visible.
  const geometry=skillVfxGeometry(e),width=(wave||after||field?geometry.widthMetres:geometry.lengthMetres)??0;
  const depth=(wave||after||field?geometry.depthMetres:geometry.widthMetres)??0;if(width<=0||depth<=0)return;
  const steps=Math.min(7,Math.max(3,Math.ceil(width/1.6))),front=wave?(progress*depth-depth/2):0;
  if(after||field){
   const filledDepth=field?depth*Math.min(1,(this.now-c.start)/.30):depth,center=field?offset(p,a,0,(filledDepth-depth)/2):p;
   const fade=Math.min(1,(1-progress)*6),opacity=(after?.74:.60)*fade;
   if(filledDepth>0)this.host.fireRibbon?.(`bed:${e.castId}`,center,width,filledDepth,a,this.now,opacity,p);
   return;
  }
  if(this.host.fireRibbon){
   // A persistent wall or advancing front is one continuous low rolling strip,
   // rather than a row of full explosion clouds. Its centre follows only the
   // already resolved front; the authoritative rectangle and ticks stay intact.
   const opacity=(wave?.92:.86)*Math.min(1,(1-progress)*8);
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
   this.stroke(l,r,'#ffc473',.045,Math.min(130,alpha),.075);
  }
 }
 update(game:GameSession){
  this.now=game.state.time;const player=game.state.player;
  this.updateThunder(game);
  for(const [id,clue] of this.clues){
   const elapsed=this.now-clue.start;if(elapsed>=clue.duration){this.clues.delete(id);continue;}
   const alpha=Math.round(175*Math.min(1,(clue.duration-elapsed)*2));
   for(const side of [-1,1])for(const end of [-1,1]){
    const corner={x:clue.p.x+side*.32,z:clue.p.z+end*.32};
    this.host.line([this.host.at({x:corner.x-side*.13,z:corner.z},.08),this.host.at(corner,.08),this.host.at({x:corner.x,z:corner.z-end*.13},.08)],'#e2c68b',.022,alpha);
   }
  }
  this.cues=this.cues.filter(c=>this.now-c.start<c.duration);
  for(const c of this.cues){
   const e=c.event,rank=tier(e),age=this.now-c.start,t=Math.max(0,Math.min(1,age/c.duration)),p=this.point(e),a=e.angle??heading(e.from,p);
   const alpha=Math.round(225*Math.pow(1-t,1.7));
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
   if(c.kind==='storm'){
    if((game.state.combat.buffs.stormWardUntil??0)<=this.now)continue;
    for(const side of [-1,1]){const q=offset(player,player.angle,side*.30,-.1);this.host.line([this.host.at(offset(q,player.angle,0,-.18),.36),this.host.at(q,.62),this.host.at(offset(q,player.angle,side*.08,.08),.77)],LIGHTNING,.023,game.state.combat.buffs.stormWardReduction>0?145:70);}continue;
   }
   if(c.kind==='bolt'){
    if(e.skillId.startsWith('FIR')){if(e.to)this.stroke(e.from,e.to,FIRE,.04,Math.round(alpha*.7),.16);}
    else {
     const cast=game.state.combat.casts.find(cast=>cast.id===e.castId);
     if(!c.sourceAnchor&&e.phase!=='network'&&cast&&distance(e.from,cast.from)<.01&&e.to&&distance(e.from,e.to)>.1)c.sourceAnchor=this.host.playerHand?.()?.clone();
     this.bolt(e,alpha,c.sourceAnchor);
    }continue;
   }
   if(c.kind==='meleeSweep'){
    const g=skillVfxGeometry(e),radius=g.radiusMetres??0,span=(g.angleDegrees??0)*Math.PI/180;
    const count=PURE_SKILLS[e.skillId]?.ranks[rank-1]?.authoredDamageHits??1,stage=e.segment===count-1&&count>=3?3:e.segment%2+1;
    drawMeleeSweep(this.host,`strike:${e.castId}:${e.segment}`,e.from,a,radius,span,stage,t,Math.round(alpha*1.12));
    if(!this.reducedMotion&&e.segment>0&&t<.32){
     const previous=this.cues.find(q=>q.kind==='meleeSweep'&&q.event.castId===e.castId&&q.event.segment===e.segment-1);
     if(previous)drawMeleeSweep(this.host,`echo:${e.castId}:${e.segment}`,previous.event.from,a,radius,span,e.segment%2?1:2,1,Math.round(40*(1-t/.32)));
    }
    continue;
   }
   if(c.kind==='blast'){
    const radius=skillVfxGeometry(e).radiusMetres??0,phase=t<.12?0:t<.46?1:t<.75?2:3;
    const grow=t<.12?.68+t*2.2:1,fade=t<.55?1:Math.pow((1-t)/.45,.85);
    if(this.host.fireVolume)this.host.fireVolume(`impact:${e.castId}:${e.segment}`,p,radius,rank,t,.96*(e.skillId==='FIR_02'&&e.segment>0?.65:1));
    else this.host.fireSprite?.(`impact:${e.castId}:${e.segment}`,p,.03,radius*2.1*grow,radius*2.1*432/768*grow,phase,Math.min(.94,fade*.94));
    continue;
   }
   if(c.kind==='wall'||c.kind==='wave'||c.kind==='afterglow'||c.kind==='field'){this.wall(c,t,alpha);continue;}
   if(c.kind==='shield'){
    if(player.shield<=0&&age>.1)continue;
    this.shield(e,player,player.angle,Math.round(100*Math.min(1,(1-t)*5)));continue;
   }
   if(c.kind==='guardHit'){this.shield(e,p,player.angle,alpha);continue;}
   if(c.kind==='enchant'){
    const q=offset(player,player.angle,.25,.40),remaining=Math.max(0,Math.min(3,Number(game.state.combat?.buffs.thunderCharges??0)));
    for(let i=0;i<remaining;i++)this.bolt({...e,from:offset(q,player.angle,(i-1)*.09,0),to:offset(q,player.angle,(i-1)*.09,.25)},85);continue;
   }
   if(c.kind==='ward'){if(player.shield>0)for(let i=0;i<rank;i++)this.stroke(offset(player,player.angle,(i-(rank-1)/2)*.08,.15),offset(player,player.angle,(i-(rank-1)/2)*.08+.04,.24),VIOLET,.016,95,.95);continue;}
   if(c.kind==='mark'||c.kind==='burn'){
    const enemy=game.state.enemies.find(n=>n.id===e.targetId&&n.hp>0);if(!enemy)continue;
    const status=game.state.combat?.statuses[enemy.id];
    if(c.kind==='mark'){if(e.skillId==='BOW_04'&&!(status?.hunterMarkUntil>this.now))continue;this.scratch(enemy,enemy.angle,rank,'#c4c5ac',95,.88);}
    else if(status?.burnUntil>this.now)this.host.loop('skill:burn:'+e.targetId,'flame',enemy,.23,.22+.025*rank,'#dc7a32');continue;
   }
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
   if(c.kind==='drop'){
    if(game.state.action?.id!==e.castId)continue;
    this.host.meteor?.('meteor:'+e.castId,p,rank,t,this.now);
    continue;
   }
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
   const age=this.now-path.time;
   if(path.bow&&(path.ended||age>.0001)&&age<.24){
    drawArrowWake(this.host,path.points,path.bow.color,path.bow.split,path.bow.rank,path.visual,Math.pow(1-age/.24,1.5));
   }
   if(age>(path.bow?.24:.4))this.trails.delete(id);
  }
 }
 clear(preserveCues=false){
  // Resume anchored shields/marks/fields from the same session clock; transient
  // contacts are discarded so a menu cannot replay their flashes or bursts.
  this.cues=preserveCues?this.cues.filter(c=>['shield','enchant','mark','burn','ward','wall','wave'].includes(c.kind)):[];
  this.trails.clear();if(!preserveCues){this.seen.clear();this.clues.clear();this.thunderPatterns.clear();}
 }
}
