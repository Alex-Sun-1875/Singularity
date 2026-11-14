import {Camera,Node,Material,MeshRenderer,ParticleSystem,Burst,Vec3,Quat,GradientRange,CurveRange,director,Director} from 'cc';
import {ManagedLine as Line} from '../../../shared/assets/ManagedLine';
import {BASIC_ATTACK,type GameSession,type ProjectileState} from '../../../core/GameSession';
import {meleeCombo} from '../common/MeleeCombo';
import {drawMeleeSweep,drawMeleeContact,type MeleeVfxHost} from './MeleeSkillEffects';
import type {GameEvent,Point} from '../../../core/Contracts';
import {SceneBuilder} from '../../world/runtime/SceneBuilder';
import {VfxAssets,VfxKind,type VfxLineStyle,constant,vfxColor} from '../../../shared/assets/VfxAssets';
import {NativeSkillVfx,type SkillPreview} from './NativeSkillVfx';
import {NativeEnemyVfx} from './NativeEnemyVfx';
import {MeleeBladeSurfaces} from '../../actors/runtime/MeleeBladeSurfaces';
import {SkillFireSprites} from './SkillFireSprites';
import {SkillMeteorBody} from './SkillMeteorBody';
import {ThunderGroundAura} from './ThunderGroundAura';
import {ThunderContactLights} from './ThunderContactLights';
import {ThunderArcField} from './ThunderArcField';
import {THUNDER_COLORS,isThunderColor} from './SkillEnergyStrokes';
import {actionReleaseAt,type PlayerPresentation} from '../../actors/runtime/PlayerActionPresentation';
import {COMBAT_SKILLS} from '../data/PureSkills';
import {weaponCombatFamily} from '../../progression/common/CombatLoadouts';
import {SkillAimIndicators} from './SkillAimIndicators';

type Emitter={kind:VfxKind;node:Node;system:ParticleSystem;life:number;until:number;key?:string;touched:boolean};
type Body={kind:string;node:Node;key?:string;touched:boolean};
type Path={points:Vec3[];time:number;weapon:string;family?:string};
type RibbonItem={node:Node;line:Line;width?:number;taper?:boolean;color?:string};
type RibbonPool={items:RibbonItem[];used:number};
export interface AttackRangePreview {rangeMetres:number;angle:number;valid:boolean;angleDegrees?:number;target?:Point;}
const TAU=Math.PI*2;
const BASIC_FIRE_COMET_SIZE=.48;
const smooth=(value:number)=>{const t=Math.max(0,Math.min(1,value));return t*t*(3-2*t);};
const colors={steel:'#e1f2fa',danger:'#f39b99',locked:'#f38883',arcane:'#91dfff',seal:'#c9a1f4',prayer:'#f3d69c',valid:'#83d9e9',invalid:'#f58d96'};

/** Visuals observe authoritative state/events. Cocos ParticleSystem owns
 * simulation/fading and Line owns ribbons. Neither participates in hit tests. */
export class Effects {
 private emitters:Emitter[]=[];private loops=new Map<string,Emitter>();private lines:RibbonItem[]=[];private lineIndex=0;
 private readonly linePools=new Map<Material,RibbonPool>();
 private bodies:Body[]=[];private paths=new Map<string,Path>();private actionCues=new Set<string>();private fireCues=new Set<string>();private phases=new Map<string,string>();
 private now=0;private lastTime=-1;private area='';private root:Node;private skills:NativeSkillVfx;private enemies:NativeEnemyVfx;private blades:MeleeBladeSurfaces;private fireSprites:SkillFireSprites;private meteor:SkillMeteorBody;private groundThunder:ThunderGroundAura;private thunderContacts:ThunderContactLights;private thunderField:ThunderArcField;
 private details:{points:Vec3[];color:string;width:number;alpha:number;style?:VfxLineStyle}[]=[];
 private playerSource?:()=>PlayerPresentation|undefined;
 private aimIndicators?:SkillAimIndicators;
 private meleeHost:MeleeVfxHost;private lowMotion=false;
 private basicTrails:{id:string;p:Point;angle:number;stage:number;start:number}[]=[];
 private fireContacts:{id:string;p:Point;start:number}[]=[];
 private fireFamily=false;
 private readonly fireDirection=new Vec3();
 private readonly lineCentre=new Vec3();
 private meleeContacts:{id:string;p:Point;angle:number;stage:number;start:number}[]=[];
 set reducedMotion(value:boolean){this.lowMotion=value;this.skills.reducedMotion=value;this.fireSprites.reducedMotion=value;}
 get reducedMotion(){return this.lowMotion;}
 private projectileOffsets=new Map<string,Vec3>();private projectileRanges=new Map<string,number>();private renderingProjectile:ProjectileState|undefined;
 private volleyWarmup:Promise<void>|null=null;private disposed=false;
 setPlayerPresentationSource(source:()=>PlayerPresentation|undefined){this.playerSource=source;}
 constructor(readonly world:SceneBuilder,private readonly flatCamera?:Camera,private readonly nativePlayer=false){this.root=new Node('CombatVFX');world.root.addChild(this.root);this.area=world.area.id;this.blades=new MeleeBladeSurfaces(this.root,flatCamera);this.groundThunder=new ThunderGroundAura(this.root,p=>world.height(p));this.thunderContacts=new ThunderContactLights(this.root,flatCamera);this.thunderField=new ThunderArcField(this.root,(p,h)=>this.at(p,h));this.fireSprites=new SkillFireSprites(this.root,flatCamera,p=>world.height(p),(a,b)=>world.visible(a,b)&&Math.abs(world.height(a)-world.height(b))<1.2);this.meteor=new SkillMeteorBody(p=>world.height(p),this.fireSprites);const host={meteor:(key:string,p:Point,rank:number,progress:number,time:number)=>this.meteor.draw(key,p,rank,progress,time),thunderField:(key:string,points:readonly Point[],rank:number,alpha:number,pulse:number)=>this.thunderField.draw(key,points,rank,alpha,pulse),thunderContact:(key:string,center:Vec3,rank:number,alpha:number,time:number)=>this.thunderContacts.draw(key,center,rank,alpha,time),visible:(a:Point,b:Point)=>world.visible(a,b)&&Math.abs(world.height(a)-world.height(b))<1.2,thunderGround:(key:string,p:Point,radius:number,alpha:number,phase:number)=>this.groundThunder.draw(key,p,radius,alpha,phase),at:(p:Point,h?:number)=>this.at(p,h),line:(p:Vec3[],c:string,w?:number,a?:number,t?:boolean,style?:VfxLineStyle)=>this.line(p,c,w,a,t,style),detailLine:(points:Vec3[],color:string,width=.02,alpha=140,style?:VfxLineStyle)=>{if(this.details.length<160)this.details.push({points,color,width,alpha,style});},burst:(k:VfxKind,p:Point,h:number,n:number,s?:number,c?:string,a?:number)=>this.burst(k,p,h,n,s,c,a),loop:(key:string,k:VfxKind,p:Point,h:number,s?:number,c?:string)=>this.loop(key,k,p,h,s,c),body:(p:ProjectileState)=>this.body(p),projectileAt:(p:ProjectileState,h:number)=>this.projectileAt(p,h),playerHand:()=>this.playerSource?.()?.hand,blade:(key:string,p:Point,height:number,angle:number,radius:number,span:number,width:number,alpha:number,progress:number,normal?:Vec3)=>this.blades.draw(key,this.playerAt(p,height),angle,radius,span,width,alpha,progress,normal),slash:(key:string,start:Vec3,end:Vec3,width:number,alpha:number,progress:number)=>this.blades.drawSlash(key,start,end,width,alpha,progress),fireProjectile:(key:string,p:Point,height:number,angle:number,size:number,time:number)=>{const q=this.renderingProjectile===p?this.projectileAt(this.renderingProjectile,height):this.at(p,height);this.fireDirection.set(Math.sin(angle),0,Math.cos(angle));this.fireSprites.drawProjectile(key,q,this.fireDirection,size,time);},firePlume:(key:string,p:Point,height:number,size:number,time:number,alpha:number)=>this.fireSprites.drawPlume(key,this.at(p,height),size,time,alpha),fireSprite:(key:string,p:Point,height:number,width:number,tall:number,phase:number,alpha:number)=>this.fireSprites.draw(key,this.renderingProjectile===p?this.projectileAt(this.renderingProjectile,height):this.at(p,height),width,tall,phase,Math.round(alpha*255)),fireRibbon:(key:string,p:Point,width:number,depth:number,angle:number,time:number,alpha:number,origin?:Point)=>this.fireSprites.drawRibbon(key,this.at(p,.03),width,depth,angle,time,Math.round(alpha*255),origin),fireVolume:(key:string,p:Point,radius:number,rank:number,progress:number,alpha:number)=>this.fireSprites.drawVolume(key,this.at(p,.03),radius,rank,progress,Math.round(alpha*255))};this.meleeHost=host;this.skills=new NativeSkillVfx(host);this.enemies=new NativeEnemyVfx(host,world,this.root,flatCamera);}
 static preload(){return Promise.all([VfxAssets.preload(),MeleeBladeSurfaces.preload()]);}
 private preparedFamily='';
 async prepareShaders(point:Point,game?:GameSession){await VfxAssets.prepareShaders(this.world.root,this.at(point,.9),this.world.mesh('cylinder'));if(game)await this.prepareEquipment(game);}
 /** Create bounded native pools while the loading/equipment UI is still up.
  * Reusing them removes first-volley component/material allocation spikes.
  * Counts, particle profiles, paths and gameplay are identical at emission.
  */
 async prepareEquipment(game:GameSession):Promise<void>{
  if(this.disposed)return;
  const s=game.state,count=s.enemies.filter(e=>e.hp>0).length,family=weaponCombatFamily(s.equipment.weapon,s.combat);
  if(this.preparedFamily!==family){
   this.clear();this.blades.destroy();this.fireSprites.destroy();this.meteor.destroy();this.groundThunder.destroy();
   this.blades=new MeleeBladeSurfaces(this.root,this.flatCamera);this.fireSprites=new SkillFireSprites(this.root,this.flatCamera,p=>this.world.height(p),(a,b)=>this.world.visible(a,b)&&Math.abs(this.world.height(a)-this.world.height(b))<1.2);this.meteor=new SkillMeteorBody(p=>this.world.height(p),this.fireSprites);this.groundThunder=new ThunderGroundAura(this.root,p=>this.world.height(p));
   this.fireSprites.reducedMotion=this.lowMotion;this.preparedFamily=family;this.volleyWarmup=undefined;
   // Native enemy fire uses the shared particle masks, not these player-only
   // sequences. Release only after their old renderers/materials are detached.
   if(family!=='FIR')SkillFireSprites.dispose();if(family!=='THU')ThunderGroundAura.dispose();
  }
  if(family==='FIR')await SkillFireSprites.preload();else if(family==='THU')await ThunderGroundAura.preload();else if(family==='WAR')await MeleeBladeSurfaces.preload();
  if(this.disposed||family!=='BOW'||count<4)return;
  await (this.volleyWarmup??(this.volleyWarmup=this.warmVolleyPools(s.player,Math.min(24,Math.max(12,count+4)))));
 }
 private async warmVolleyPools(point:Point,count:number){
  let jobs=0;
  const yieldBatch=async()=>{if(++jobs%4===0)await new Promise<void>(resolve=>director.once(Director.EVENT_AFTER_DRAW,resolve));};
  for(const kind of ['spark','flash','dust'] as const){
   if(this.disposed)return;
   let existing=this.emitters.filter(e=>e.kind===kind).length;
   while(existing++<count&&this.emitters.length<96&&!this.disposed){
    const native=VfxAssets.emitter(kind,this.root);native.system.stop();native.node.active=false;
    this.emitters.push({kind,...native,until:0,touched:false});await yieldBatch();
   }
  }
  while(this.bodies.length<Math.min(32,count*3)&&!this.disposed){const body=this.createArrowBody();body.node.active=false;await yieldBatch();}
  if(this.disposed)return;
  const anchor=this.at(point,1.05);
  for(const style of ['solid','core'] as const){
   if(this.disposed)return;
   const material=VfxAssets.lineMaterial(style,false);let pool=this.linePools.get(material);
   if(!pool){pool={items:[],used:0};this.linePools.set(material,pool);}
   while(pool.items.length<Math.min(32,count*2)&&this.lines.length<160&&!this.disposed){
    const item=this.createRibbon(material);pool.items.push(item);
    Reflect.set(item.line,'texture',VfxAssets.lineTexture(style));constant(item.line.width,.001);
    item.line.color.mode=GradientRange.Mode.Color;item.line.color.color=vfxColor('#ffffff',0);
    item.line.positions=[anchor,anchor.clone().add(new Vec3(.001,0,0))];item.node.active=true;item.node.active=false;
    await yieldBatch();
   }
  }
 }
 /** Release shared masks only after all Effects instances are destroyed. */
 static dispose(){VfxAssets.dispose();SkillFireSprites.dispose();MeleeBladeSurfaces.disposeAssets();ThunderGroundAura.dispose();}
 private at(p:Point,height=0){
  const base=new Vec3(p.x,this.world.height(p),p.z);
  // 2D人物的身高沿相机up展开，手部特效采用相同坐标，避免被世界Y投影压低。
  if(this.flatCamera){base.add(Vec3.multiplyScalar(new Vec3(),this.flatCamera.node.up,height));if(height>.25)base.add(Vec3.multiplyScalar(new Vec3(),this.flatCamera.node.forward,-.055));return base;}
  base.y+=height;return base;
 }
 private playerAt(p:Point,height:number):Vec3{return this.nativePlayer?new Vec3(p.x,this.world.height(p)+height,p.z):this.at(p,height);}
 private projectileAt(p:ProjectileState,height:number):Vec3 {
  const base=p.owner==='player'?this.playerAt(p,height):this.at(p,height),straightShot=!!this.flatCamera&&p.kind==='arrow'||p.owner==='player'&&p.kind==='staff'&&!p.skillId&&this.fireFamily;
  if(p.owner!=='player'||p.child||p.returning||!straightShot&&p.age>=.14)return base;
  let offset=this.projectileOffsets.get(p.id);
  if(!offset&&p.age<=.08){
   const source=this.playerSource?.();
   if(source&&(!p.castId||source.actionId===p.castId)){
    const origin=p.from??{x:p.x-Math.sin(p.angle)*p.speed*p.age,z:p.z-Math.cos(p.angle)*p.speed*p.age};
    offset=source.hand.clone();
    // All airborne effects use their visible head as the hand anchor.

    offset.subtract(this.playerAt(origin,height));this.projectileOffsets.set(p.id,offset);
    if(straightShot)this.projectileRanges.set(p.id,Math.max(.01,p.remaining+p.speed*p.age));
   }
  }
  if(offset){
   // Arrows and basic fire bolts fly freely from the fixed release socket to
   // the authoritative ray endpoint, without the old .14s hand easing.
   const t=Math.max(0,Math.min(1,straightShot?p.age*p.speed/(this.projectileRanges.get(p.id)??1):p.age/.14));
   base.add(Vec3.multiplyScalar(new Vec3(),offset,straightShot?1-t:1-t*t*(3-2*t)));
  }
  return base;
 }
 private acquire(kind:VfxKind):Emitter|undefined{
  let e=this.emitters.find(e=>e.kind===kind&&!e.key&&e.until<=this.now);
  if(!e){if(this.emitters.length>=96){const idle=this.emitters.findIndex(e=>!e.key&&e.until<=this.now);if(idle<0)return;this.emitters[idle].node.destroy();this.emitters.splice(idle,1);}const native=VfxAssets.emitter(kind,this.root);e={kind,...native,until:0,touched:false};this.emitters.push(e);}
  e.node.active=true;e.node.setScale(1,1,1);e.node.setRotationFromEuler(0,0,0);e.system.stop();VfxAssets.reset(e.system,kind);return e;
 }
 private burst(kind:VfxKind,p:Point,height:number,count:number,scale=1,color?:string,angle=0){
  const e=this.acquire(kind);if(!e)return;e.node.setPosition(this.at(p,height));e.node.setScale(scale,scale,scale);constant(e.system.startRotationZ,angle);
  if(color)e.system.startColor.color=vfxColor(color,kind==='slash'?170:220);const burst=new Burst();burst.time=0;burst.repeatCount=1;constant(burst.count,count);e.system.bursts=[burst];constant(e.system.rateOverTime,0);e.system.duration=Math.max(1,e.life+.1);e.system.loop=false;e.system.play();e.until=this.now+e.life+.08;return e;
 }
 private loop(key:string,kind:VfxKind,p:Point,height:number,scale=1,color?:string){
  let e=this.loops.get(key);if(!e){e=this.acquire(kind);if(!e)return;e.key=key;this.loops.set(key,e);e.node.setPosition(this.renderingProjectile===p?this.projectileAt(this.renderingProjectile,height):this.at(p,height));e.node.setScale(scale,scale,scale);if(color)e.system.startColor.color=vfxColor(color,190);e.system.play();}
  e.touched=true;e.node.setPosition(this.renderingProjectile===p?this.projectileAt(this.renderingProjectile,height):this.at(p,height));e.node.setScale(scale,scale,scale);if(color)e.system.startColor.color=vfxColor(color,190);return e;
 }
 private line(points:Vec3[],color:string,width=.035,alpha=200,taper=false,style?:VfxLineStyle){
  if(points.length<2||this.lineIndex>=160)return;this.lineIndex++;
  // Native Line evaluates its width curve ONLY at supplied path vertices.
  // A two-point tapered slash otherwise samples two zero-width ends and its
  // entire hot blade vanishes. Supply interior samples for the actual profile.
  if(taper&&points.length===2){const[a,b]=points;points=Array.from({length:9},(_,i)=>Vec3.lerp(new Vec3(),a,b,i/8));}
  // The same pooled Line can be a warning, a soft halo, or a bright core on
  // successive frames. Always restore its material AND sorting priority.
  const hex=color.toLowerCase(),electric=isThunderColor(hex)||['#2679ff','#72afff','#316dff','#367cff','#e8f7ff','#718dff'].includes(hex);
  const resolved=style??(electric&&width>=.19?'glow':[THUNDER_COLORS.core,THUNDER_COLORS.flare,'#72afff','#e8f7ff'].includes(hex)?'core':'solid');
  const material=VfxAssets.lineMaterial(resolved,electric);
  let pool=this.linePools.get(material);if(!pool){pool={items:[],used:0};this.linePools.set(material,pool);}
  let item=pool.items[pool.used];
  if(!item){
   // Preserve native material instances between frames. Rebinding Line's
   // shared material clones passes and allocates uniform buffers again.
   // At the existing160-node bound, lend an unused slot from another group.
   if(this.lines.length>=160)for(const donor of this.linePools.values())if(donor!==pool&&donor.items.length>donor.used){item=donor.items.pop()!;break;}
   if(!item&&this.lines.length<160){item=this.createRibbon(material);item.node.active=true;}
   if(!item)return;
   pool.items.push(item);
  }
  pool.used++;
  // Configure before onLoad, avoiding a default-trail material/PSO that the
  // actual ribbon immediately replaces. Native geometry and styling stay equal.
  if(item.line.lineMaterial!==material)item.line.lineMaterial=material;
  const warning=['#f39b99','#f38883','#f58d96','#d57963','#ffb365','#ffd09a'].includes(hex);
  item.line.priority=warning?3:resolved==='glow'?0:resolved==='core'?2:1;
  item.node.active=true;
  // Line.onEnable rebinds Line.texture, which otherwise resets a pooled
  // material to null. The 3.8.8 getter incorrectly declares this setter null.
  const texture=VfxAssets.lineTexture(resolved);if(item.line.texture!==texture)Reflect.set(item.line,'texture',texture);
  // World-space geometry bypasses the node matrix; native sorting still uses
  // its transform, so keep that transform at the actual ribbon centre.
  const centre=this.lineCentre.set(0,0,0);for(const p of points)centre.add(p);centre.multiplyScalar(1/points.length);item.node.setWorldPosition(centre);
  if(item.taper!==taper||item.width!==width){
   if(taper){item.line.width.mode=CurveRange.Mode.Curve;item.line.width.spline.assignSorted([[0,{value:.001}],[.18,{value:width*.5}],[.5,{value:width}],[.82,{value:width*.5}],[1,{value:.001}]]);}
   else constant(item.line.width,width);item.taper=taper;item.width=width;
  }
  item.line.color.mode=GradientRange.Mode.Color;if(item.color!==color){item.line.color.color.fromHEX(color);item.color=color;}item.line.color.color.a=alpha;item.line.positions=points;
 }
 private createRibbon(material:Material):RibbonItem {
  const node=new Node('VFX:Ribbon');node.active=false;this.root.addChild(node);const line=node.addComponent(Line);line.lineMaterial=material;line.worldSpace=true;
  const item={node,line};this.lines.push(item);return item;
 }
 private circle(p:Point,radius:number,color:string,width=.035,alpha=200,start=0,length=TAU,height=.055){
  const points:Vec3[]=[];const n=Math.max(8,Math.ceil(32*length/TAU));for(let i=0;i<=n;i++){const a=start+length*i/n,q={x:p.x+Math.sin(a)*radius,z:p.z+Math.cos(a)*radius};points.push(this.at(q,height));}this.line(points,color,width,alpha);
 }
 private local(p:Point,angle:number,side:number,forward:number,height=.055){const q={x:p.x+Math.cos(angle)*side+Math.sin(angle)*forward,z:p.z-Math.sin(angle)*side+Math.cos(angle)*forward};return this.at(q,height);}
 private createArrowBody():Body {
   const node=new Node('Projectile:arrow');this.root.addChild(node);const body:Body={kind:'arrow',node,touched:false};this.bodies.push(body);
   // The same opaque shaft/head/feather meshes share native instanced passes.
   // Creator 3.8.8's world-transform shader retains inverse-scale normals.
   const part=(name:string,mesh:string,x:number,y:number,z:number,sx:number,sy:number,sz:number,color:string,rx=0)=>{const n=new Node(name);node.addChild(n);n.setPosition(x,y,z);n.setScale(sx,sy,sz);n.setRotationFromEuler(rx,0,0);const r=n.addComponent(MeshRenderer);r.mesh=this.world.mesh(mesh);r.setSharedMaterial(VfxAssets.solid(color,true),0);};
   part('Steel shaft','cylinder',0,0,0,.035,.62,.035,'#bcc5cd',90);part('Steel broadhead','cone',0,0,.36,.11,.18,.035,'#dbe3e9',90);part('Fletching','cone',0,0,-.25,.10,.18,.035,'#dcd0af',90);
   return body;
 }
 private body(p:ProjectileState){
  let body=this.bodies.find(b=>b.key===p.id);
  if(!body){body=this.bodies.find(b=>b.kind==='arrow'&&!b.key);if(!body&&this.bodies.length<64)body=this.createArrowBody();if(!body)return;body.key=p.id;}
  body.touched=true;body.node.active=true;const height=1.05;
  // Thicken only player skill arrows for phone readability; shaft length,
  // current position, frozen flight path and gameplay collider stay unchanged.
  const arrowWidth=p.owner==='player'&&p.skillId?.startsWith('BOW_')?1.35:1;body.node.setScale(arrowWidth,arrowWidth,1);
  const position=this.projectileAt(p,height);body.node.setPosition(position);
  if(this.flatCamera){
   // Point the existing +Z arrow mesh along its rendered flight, including
   // the calibrated hand outlet, rather than leaving its nose at a skew.
   const step=.05,next={...p,x:p.x+Math.sin(p.angle)*step,z:p.z+Math.cos(p.angle)*step,age:p.age+step/Math.max(.01,p.speed),remaining:p.remaining-step};
   const axis=this.projectileAt(next,height).subtract(position);
   if(axis.lengthSqr()>.000001)body.node.setRotation(Quat.rotationTo(new Quat(),new Vec3(0,0,1),axis.normalize()));
  }else body.node.setRotationFromEuler(0,p.angle*180/Math.PI,0);
 }
 private projectile(p:ProjectileState){
  if(this.enemies.projectile(p,this.now))return;
  if(this.skills.projectile(p,this.now))return;
  const height=1.05;
  if(p.kind==='arrow'||p.kind==='crossbow')this.body(p);
  if(p.owner==='player'&&p.kind==='staff'&&this.fireFamily){
   const center=this.projectileAt(p,1.05);this.fireDirection.set(Math.sin(p.angle),0,Math.cos(p.angle));
   const offset=this.projectileOffsets.get(p.id),range=this.projectileRanges.get(p.id);
   if(offset&&range){this.fireDirection.x-=offset.x/range;this.fireDirection.y-=offset.y/range;this.fireDirection.z-=offset.z/range;}
   // Keep the incandescent head size; shorten only the wake. Its birth reads
   // actual travel distance so it cannot stretch backwards through the hand.
   this.fireSprites.drawBasicComet('basic:'+p.id,center,this.fireDirection,BASIC_FIRE_COMET_SIZE,this.now,p.age*p.speed,this.playerSource?.()?.hand);
   return;
  }
  const spell=p.kind==='spell',staff=p.kind==='staff',kind:VfxKind=spell?(p.weapon==='T02'?'seal':p.weapon==='T03'?'prayer':'arcane'):staff?'charge':'arrowWake';
  const color=p.owner==='enemy'?colors.danger:spell?(p.weapon==='T02'?colors.seal:p.weapon==='T03'?colors.prayer:colors.arcane):staff?'#c8d4cd':p.charged?'#e8ddb2':colors.steel;
  this.loop('projectile:'+p.id,kind,p,height,staff?.55:p.charged?1.2:1,color);
  let path=this.paths.get(p.id);if(!path){path={points:[],time:this.now,weapon:p.weapon};this.paths.set(p.id,path);}path.time=this.now;path.points.unshift(this.projectileAt(p,height));path.points.length=Math.min(path.points.length,spell?9:p.charged?8:5);
  this.line(path.points,color,spell?.065:staff?.022:p.charged?.035:.017,p.owner==='enemy'?190:staff?120:160);
  if(spell)this.loop('projectileCore:'+p.id,'charge',p,height,.65,color);
 }
 private playerAction(game:GameSession){
  const s=game.state,a=s.action,p=s.player;if(!a)return;
  const def=COMBAT_SKILLS[a.skillId??''],release=actionReleaseAt(a),binding=this.playerSource?.(),motion=binding?.actionId===a.id?binding:undefined;
  const family=def?.style??(a.kind==='staff'&&this.fireFamily?'FIR':undefined),color=family==='WAR'?colors.steel:family==='FIR'?'#ffb85b':family==='THU'?THUNDER_COLORS.body:family==='BOW'||a.kind==='bow'||a.kind==='bowAim'?'#dce9c2':family==='COM'?'#ecdfb3':a.kind==='staff'?'#c8d4cd':colors.arcane;
  const inWindup=motion?['prepare','raise','aim','rearm','channel'].includes(motion.phase??''):a.kind==='bowAim'||!a.emitted&&a.elapsed<release;
  if(inWindup&&(!!def||a.kind==='staff'||a.kind==='bowAim'||a.kind==='bow'||a.kind.startsWith('spell:'))){
   const kind:VfxKind=family==='FIR'?'fireCore':'charge',charged=a.kind==='bowAim'&&a.elapsed>=.8;
   const loop=this.loop('player:charge:'+a.id,kind,p,1.10,family==='WAR'?.30:family==='FIR'?.24:charged?.85:.47,color);
   if(loop&&motion)loop.node.setWorldPosition(motion.hand);
  }
  const released=motion?motion.phase==='release'||motion.phase==='channel':a.elapsed>=release&&(a.kind==='sword'||a.emitted),beat=motion?.beat??0;
  const handCue=`hand:${a.id}:${beat}`;
  if(released&&!this.actionCues.has(handCue)){
   this.actionCues.add(handCue);
   if(a.kind!=='sword'&&a.kind!=='dash'&&a.kind!=='push'){
    const flash=this.burst(family==='FIR'?'ember':'flash',p,1.10,family==='FIR'?3:1,family==='WAR'?.25:.32,color);
    if(flash&&motion)flash.node.setWorldPosition(motion.hand);
   }
  }
  if(a.kind==='push'&&a.elapsed>=.1&&!this.actionCues.has(a.id)){
   this.actionCues.add(a.id);this.burst('dust',{x:p.x+Math.sin(a.angle)*.7,z:p.z+Math.cos(a.angle)*.7},.3,10,.8);
  }else if(a.kind==='dash'&&a.elapsed>=.04&&!this.actionCues.has(a.id)){
   this.actionCues.add(a.id);this.burst('dust',p,.08,8,.8);
  }
  if(this.actionCues.size>192)this.actionCues.delete(this.actionCues.values().next().value!);
  if(a.kind==='sword'&&a.elapsed>=release&&a.elapsed<release+.20){
   const key='basic-trail:'+a.id;let trail=this.basicTrails.find(q=>q.id===a.id);
   if(!trail&&!this.actionCues.has(key)){trail={id:a.id,p:{x:p.x,z:p.z},angle:a.angle,stage:a.comboStage??1,start:s.time-(a.elapsed-release)};this.basicTrails.push(trail);this.actionCues.add(key);}
   if(trail)trail.p={x:p.x,z:p.z};
  }
 }

 onEvents(events:readonly GameEvent[],game:GameSession):void{
  this.now=game.state.time;
  const skillContacts=new Set(events.filter(e=>e.type==='skill_hit').map(e=>`${e.castId}:${e.targetId}`));
  for(const event of events){
   if(event.type==='campaign_battle'&&Array.isArray(event.enemies)){for(const id of event.enemies){const enemy=game.state.enemies.find(e=>e.id===id);if(enemy){this.burst('dust',enemy,.1,12,1.2);this.burst('flash',enemy,.2,1,.55,'#efb16d');}}continue;}
   if(this.skills.event(event,this.now))continue;
   if(this.enemies.event(event,game))continue;
   const enemy=event.id?game.state.enemies.find(e=>e.id===event.id):undefined,p=event.at??enemy??game.state.player;
   if(event.type==='growing_proc'){
    const kind=String(event.kind),color=kind.includes('thunder')?'#a5d8ff':kind==='fire'?'#f5a46a':'#f1ce87';
    if(kind==='shadow')this.burst('slash',p,.8,1,1.35,color,-Number(event.angle??0));
    else if(kind==='fire'){this.burst('ember',p,.3,12,.7,color);this.burst('flash',p,.4,1,.6,color);}
    else if(kind==='thunder'){this.burst('spark',p,.8,12,.8,color);this.burst('flash',p,.8,1,.6,color);}
    else this.burst('rune',p,.15,1,kind==='dawn'?1.3:.65,color);
    continue;
   }
   if(event.type==='area'){this.clear();this.area=game.state.area;continue;}
   if(event.type==='hit'&&Number(event.hpLost)>0){
    if(Number(event.comboStage)>0){this.meleeContacts.push({id:String(event.action)+':'+event.id,p:{...p},angle:Number(event.angle)||0,stage:Number(event.comboStage),start:this.now});if(this.meleeContacts.length>12)this.meleeContacts.shift();}
    // Generic damage still drives HUD/audio; the skill event owns its contact.
    if(skillContacts.has(`${event.action}:${event.id}`))continue;
    if(event.action==='burn'){this.burst('ember',p,.18,2,.28);continue;}
    if(event.element==='FIR'||this.paths.get(String(event.action))?.family==='FIR'){
     this.fireContacts.push({id:String(event.action)+':'+event.id,p:{...p},start:this.now});if(this.fireContacts.length>12)this.fireContacts.shift();
     this.burst('ember',p,.65,5,.30);this.burst('fireCore',p,.65,1,.50);continue;
    }
    const spell=event.source==='spell',environment=event.source==='environment',weapon=this.paths.get(String(event.action))?.weapon??game.state.action?.kind.slice(6),identity:VfxKind=weapon==='T02'?'seal':weapon==='T03'?'prayer':'arcane',color=weapon==='T02'?colors.seal:weapon==='T03'?colors.prayer:colors.arcane;
    this.burst(environment?'ember':spell?identity:'spark',p,.9,environment?4:spell?5:4,event.critical===true?1.15:.7,spell?color:undefined);
    // The shared contact cue owns the short bright impact; avoid double flashes.
   }else if(event.type==='block'){this.burst('spark',p,1,6,.7);}
   else if(event.type==='hurt'){this.burst('dust',game.state.player,.8,7,.6,'#b68a79');this.burst('spark',game.state.player,.85,4,.7,'#daac87');}
   else if(event.type==='explosion'){
    const scale=Number(event.radius??1.1)/1.1;this.burst('flame',p,.3,18,scale*1.15);this.burst('ember',p,.3,20,scale);this.burst('smoke',p,.4,9,scale);this.burst('dust',p,.1,10,scale);this.burst('flash',p,.5,1,scale*1.4);
   }else if(event.type==='stagger'||event.type==='defeat'){this.burst('dust',p,.08,event.type==='defeat'?9:12,.85);}
   else if(event.type==='mark'){this.burst('rune',p,.075,1,.8,colors.seal);}
   else if(event.type==='evade'){this.burst('dust',p,.1,5,.65);}
   else if(event.type==='counter_ready'){this.burst('rune',p,.07,1,.9,colors.prayer);}
  }
 }
 /** Alias for callers that consume the authoritative event batch. */
 consume(events:readonly GameEvent[],game:GameSession){this.onEvents(events,game);}
 update(game:GameSession,preview?:SkillPreview,range?:AttackRangePreview){
  const s=game.state;this.now=s.time;this.fireFamily=weaponCombatFamily(s.equipment.weapon,s.combat)==='FIR';
  if(this.area!==s.area||s.time<this.lastTime){this.clear();this.area=s.area;}
  this.lastTime=s.time;if(s.status==='dead'||s.dialogue||s.dice.active){this.clear(true);return;}
  this.lineIndex=0;for(const pool of this.linePools.values())pool.used=0;this.details=[];this.blades.begin();this.fireSprites.begin();this.meteor.begin();this.groundThunder.begin();this.thunderContacts.begin();this.thunderField.begin();for(const e of this.emitters)e.touched=false;for(const b of this.bodies)b.touched=false;
  // Enemy combat effects retain their bodies/impacts without attack outlines.
  this.enemies.update(game);
  for(const enemy of s.enemies){
   if(enemy.hp<=0)continue;const nativeEnemy=this.enemies.handles(enemy);
   const previous=this.phases.get(enemy.id);if(!nativeEnemy&&enemy.phase==='active'&&previous==='windup'&&enemy.attackKind!=='shot'){
    if(enemy.attackKind==='charge')this.burst('dust',enemy,.1,9,1.1);
    else this.burst('slash',{x:enemy.x+Math.sin(enemy.targetAngle)*.55,z:enemy.z+Math.cos(enemy.targetAngle)*.55},.9,1,enemy.kind==='captain'?1.3:.8,'#cdbca4',-enemy.targetAngle);
   }this.phases.set(enemy.id,enemy.phase);
   if(enemy.markedUntil>s.time&&!(s.combat?.statuses[enemy.id]?.hunterMarkUntil>s.time))this.circle(enemy,.37,colors.seal,.025,155);
   if(enemy.lightningUntil>s.time)this.loop('marked:'+enemy.id,'charge',enemy,1.25,.45,colors.arcane);
  }
  if(preview){this.aimIndicators??=new SkillAimIndicators(this.root,p=>this.world.height(p),this.flatCamera);this.aimIndicators.update(s.player,preview,range);}
  else this.aimIndicators?.clear();
  for(const projectile of s.projectiles){this.renderingProjectile=projectile;this.projectile(projectile);}this.renderingProjectile=undefined;
  for(const id of this.projectileOffsets.keys())if(!s.projectiles.some(p=>p.id===id)){this.projectileOffsets.delete(id);this.projectileRanges.delete(id);}
  for(const fire of s.fireZones){
   this.loop('fire:'+fire.id,'flame',fire,.15,fire.radius);this.loop('embers:'+fire.id,'ember',fire,.2,fire.radius);this.loop('smoke:'+fire.id,'smoke',fire,.45,fire.radius);
   // Pausing clears native loops. Keep the one-shot cue independent of that pool.
   if(!this.fireCues.has(fire.id)){this.fireCues.add(fire.id);this.burst('scorch',fire,.025,1,fire.radius);}
   this.circle(fire,fire.radius,'#d7a16c',.022,90);
  }
  for(const id of this.fireCues)if(!s.fireZones.some(fire=>fire.id===id))this.fireCues.delete(id);
  for(const barrel of s.barrels)if(!barrel.exploded&&barrel.fuse>=0)this.loop('fuse:'+barrel.id,'ember',barrel,.86,.22);
  this.playerAction(game);this.skills.update(game);
  this.fireContacts=this.fireContacts.filter(q=>this.now-q.start<.32);
  for(const q of this.fireContacts)this.fireSprites.drawVolume('basic-hit:'+q.id,this.at(q.p,.32),.48,1,(this.now-q.start)/.32,235);
  this.basicTrails=this.basicTrails.filter(q=>this.now-q.start<.42);
  for(const q of this.basicTrails){const age=this.now-q.start,alpha=age<.20?Math.round(255*(1-.58*smooth(age/.20))):this.lowMotion?0:Math.round(255*.42*(1-smooth((age-.20)/.22)));
   drawMeleeSweep(this.meleeHost,'basic:'+q.id,q.p,q.angle,BASIC_ATTACK.sword.rangeMetres,BASIC_ATTACK.sword.angleDegrees*Math.PI/180,q.stage,Math.min(1,age/.18),alpha);
  }
  this.meleeContacts=this.meleeContacts.filter(q=>this.now-q.start<.18);
  for(const q of this.meleeContacts)drawMeleeContact(this.meleeHost,q.id,q.p,q.angle,meleeCombo(q.stage).strength,(this.now-q.start)/.18,this.lowMotion);
  this.blades.end();this.fireSprites.end();this.meteor.end();this.groundThunder.end();this.thunderContacts.end();this.thunderField.end();for(const d of this.details)this.line(d.points,d.color,d.width,d.alpha,false,d.style);this.details=[];
  for(const e of this.emitters){if(e.key&&!e.touched){this.loops.delete(e.key);e.key=undefined;e.system.stopEmitting();e.until=this.now+e.life+.08;}if(!e.key&&e.until<=this.now&&e.node.active){e.system.stop();e.node.active=false;}}
  for(const b of this.bodies)if(!b.touched){b.key=undefined;b.node.active=false;}
  for(const [id,path]of this.paths)if(this.now-path.time>.35)this.paths.delete(id);
  for(const pool of this.linePools.values())for(let i=pool.used;i<pool.items.length;i++)pool.items[i].node.active=false;
 }
 clearAim(){this.aimIndicators?.clear();}
 /** Menus stop native simulation; retain cue history so resuming an action cannot replay its burst. */
 clear(preserveCues=false){this.aimIndicators?.clear();this.fireContacts=[];this.basicTrails=[];this.meleeContacts=[];this.blades.clear();this.fireSprites.clear();this.meteor.clear();this.groundThunder.clear();this.thunderContacts.clear();this.thunderField.clear();this.skills.clear(preserveCues);this.enemies.clear();this.details=[];for(const e of this.emitters){e.system.stop();e.node.active=false;e.key=undefined;e.until=0;}for(const l of this.lines)l.node.active=false;for(const pool of this.linePools.values())pool.used=0;for(const b of this.bodies){b.node.active=false;b.key=undefined;}this.loops.clear();this.paths.clear();this.projectileOffsets.clear();this.projectileRanges.clear();this.renderingProjectile=undefined;if(!preserveCues){this.phases.clear();this.actionCues.clear();this.fireCues.clear();}this.lineIndex=0;}
 destroy(){this.disposed=true;this.clear();this.aimIndicators?.destroy();this.enemies.destroy();this.blades.destroy();this.fireSprites.destroy();this.meteor.destroy();this.groundThunder.destroy();this.thunderContacts.destroy();this.thunderField.destroy();this.root.destroy();this.emitters=[];this.lines=[];this.linePools.clear();this.bodies=[];}
}
