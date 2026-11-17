import {Camera,Color,Director,EffectAsset,Material,Mesh,MeshRenderer,Node,Quat,Texture2D,Vec3,Vec4,director,primitives,utils} from 'cc';
import {gameResources as resources} from '../../../shared/assets/GameResources';
import type {GameSession} from '../../../core/GameSession';
import type {GameEvent,Point} from '../../../core/Contracts';
import {weaponCombatFamily} from '../../progression/common/CombatLoadouts';

type Family='WAR'|'BOW'|'FIR'|'THU';
const PATH='vfx/production/';
const SKINS:Record<Family,{tint:string;channel:readonly number[]}>= {
 WAR:{tint:'#e2c792',channel:[1,0,0,0]},BOW:{tint:'#72d8b8',channel:[0,1,0,0]},
 FIR:{tint:'#ff9746',channel:[0,0,1,0]},THU:{tint:'#9698ff',channel:[0,0,0,1]},
};
const clamp=(v:number)=>Math.max(0,Math.min(1,v));
const smooth=(v:number)=>{const t=clamp(v);return t*t*(3-2*t);};

/** One real 3D ellipsoid observes the player's actual shield state, including
 * equipment/passive grants. It never grants protection or changes combat rules.
 * All skins share geometry, material, uniforms and timing; only tint and motif
 * channel vary. Front/rear passes preserve native depth and do not write depth. */
export class UnifiedShieldEffects {
 // Lower the centre and extend only the lower hemisphere. The top stays at
 // 2.34m while the shell has useful width around the soles, rather than ending
 // at a narrow pole through the boots.
 static readonly centerHeight=1.0;
 private static effect:EffectAsset|undefined;
 private static texture:Texture2D|undefined;
 private static pending:Promise<void>|undefined;
 private static revision=0;
 static preload():Promise<void>{
  if(this.pending)return this.pending;
  const revision=this.revision;
  const load=<T extends EffectAsset|Texture2D>(path:string,type:new(...args:any[])=>T)=>new Promise<T>((resolve,reject)=>{
   resources.load(PATH+path,type,(error,asset)=>{
    if(error){reject(new Error('Unified shield '+path+': '+error.message));return;}
    if(revision!==this.revision){reject(new Error('Unified shield load cancelled after disposal'));return;}
    asset.addRef();resolve(asset);
   });
  });
  this.pending=Promise.all([
   load('shield-unified-v1',EffectAsset).then(asset=>{this.effect=asset;}),
   load('shield-unified-motifs-v1/texture',Texture2D).then(texture=>{
    texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);
    texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);this.texture=texture;
   }),
  ]).then(()=>undefined).catch(error=>{if(revision===this.revision)this.dispose();throw error;});
  return this.pending;
 }
 /** Only after every owning Effects instance has been destroyed. */
 static dispose(){this.revision++;this.effect?.decRef();this.texture?.decRef();this.effect=undefined;this.texture=undefined;this.pending=undefined;}

 readonly root:Node;
 private readonly mesh:Mesh;
 private readonly material:Material;
 private readonly renderer:MeshRenderer;
 private readonly state=new Vec4();private readonly hit=new Vec4(0,0,1,-1);private readonly motion=new Vec4(1,0,0,0);
 private readonly rotation=new Quat();private readonly inverse=new Quat();private readonly direction=new Vec3();
 private family:Family|undefined;
 private start=-Infinity;private until=-Infinity;private end=-Infinity;private lastTime=-Infinity;
 private amount=0;private active=false;private hitAt=-Infinity;private hitKey='';private disposed=false;
 private opacity=0;private patternOpacity=0;private broken=false;
 reducedMotion=false;

 constructor(parent:Node,private readonly anchor:(p:Point)=>Vec3,private readonly flatCamera?:Camera){
  if(!UnifiedShieldEffects.effect||!UnifiedShieldEffects.texture)throw new Error('UnifiedShieldEffects.preload must finish before creating shields');
  this.root=new Node('UnifiedPlayerShield');this.root.layer=parent.layer;this.root.active=false;parent.addChild(this.root);
  this.root.setScale(1.88,2.68,1.88);
  this.mesh=utils.createMesh(primitives.sphere(.5,{segments:24}));this.mesh.name='UnifiedShieldEllipsoid';
  this.material=new Material();this.material.name='ProjectProcedural:UnifiedShield';
  this.material.initialize({effectAsset:UnifiedShieldEffects.effect});this.material.setProperty('mainTexture',UnifiedShieldEffects.texture);
  this.renderer=this.root.addComponent(MeshRenderer);this.renderer.mesh=this.mesh;this.renderer.setSharedMaterial(this.material,0);
  this.renderer.priority=0;this.renderer.shadowCastingMode=0;this.renderer.receiveShadow=0;
 }
 /** Compile both transparent passes while the real loading screen is up. */
 async prepare(position:Vec3){
  if(this.disposed)return;
  this.root.setWorldPosition(position);this.state.set(1,0,0,0);this.material.setProperty('shieldState',this.state);this.root.active=true;
  await new Promise<void>(resolve=>director.once(Director.EVENT_AFTER_DRAW,resolve));
  if(!this.disposed)this.root.active=false;
 }
 private skin(family:Family){
  if(this.family===family)return;this.family=family;const skin=SKINS[family];
  this.material.setProperty('shieldTint',new Color().fromHEX(skin.tint));
  this.material.setProperty('motifChannel',new Vec4(...skin.channel as [number,number,number,number]));
 }
 onEvents(events:readonly GameEvent[],game:GameSession){
  if(this.disposed)return;const s=game.state,p=s.player;
  for(const event of events){
   if(event.type!=='hurt'||!(Number(event.absorbed)>0))continue;
   const key=`${s.time}:${event.action??event.source??''}:${event.absorbed}`;
   if(key===this.hitKey)continue;this.hitKey=key;this.hitAt=s.time;
   const source=s.enemies.find(e=>e.id===event.source);
   // Hurt does not always have a directional source (e.g. environmental fire).
   // Use the player's forward contact only when that direction is unavailable.
   this.direction.set(source?source.x-p.x:Math.sin(p.angle),-.14,source?source.z-p.z:Math.cos(p.angle));
   if(this.direction.lengthSqr()<.01)this.direction.set(Math.sin(p.angle),-.14,Math.cos(p.angle));
   Quat.invert(this.inverse,this.root.worldRotation);Vec3.transformQuat(this.direction,this.direction,this.inverse);this.direction.normalize();
   this.hit.set(this.direction.x,this.direction.y,this.direction.z,0);
  }
 }
 update(game:GameSession){
  if(this.disposed)return;const s=game.state,p=s.player,now=s.time;
  if(now<this.lastTime)this.clear();this.lastTime=now;
  const hasShield=p.shield>0;
  if(hasShield){
   const family=weaponCombatFamily(s.equipment.weapon,s.combat) as Family;this.skin(family);
   if(!this.active){this.start=now;this.end=-Infinity;this.broken=false;}
   this.until=Number(s.combat.buffs.shieldUntil)||now;this.active=true;
  }else if(this.active){
   this.broken=now+1/120<this.until;this.end=this.broken?now:-Infinity;this.active=false;
  }
  this.amount=Math.max(0,p.shield);
  const ending=this.broken&&now-this.end<.28;
  if(!hasShield&&!ending){this.root.active=false;this.opacity=0;return;}
  const left=Math.max(0,this.until-now);
  this.opacity=hasShield?smooth(left/.48):.50*(1-smooth((now-this.end)/.28));
  this.patternOpacity=hasShield?smooth((left-.12)/.36):1-smooth((now-this.end)/.17);
  this.root.setWorldPosition(this.anchor(p));
  // Keep a stable world-space shell; rotation does not depend on class/rank.
  // The same paired motif repeats around both hemispheres of the 3D surface.
  if(this.flatCamera)Quat.copy(this.rotation,this.flatCamera.node.worldRotation);else Quat.fromEuler(this.rotation,0,p.angle*180/Math.PI,0);
  this.root.setWorldRotation(this.rotation);
  this.root.active=this.opacity>.001;
  this.state.set(Math.max(0,now-this.start),this.opacity,this.patternOpacity,ending?clamp((now-this.end)/.28):0);
  this.hit.w=now-this.hitAt;
  this.motion.x=this.reducedMotion?0:1;
  this.material.setProperty('shieldState',this.state);this.material.setProperty('hitState',this.hit);this.material.setProperty('motionState',this.motion);
 }
 /** Keep original timestamps through pause/resume; reset them on world changes. */
 clear(preserve=false){
  this.root.active=false;this.opacity=0;
  if(preserve)return;
  this.active=false;this.broken=false;this.amount=0;this.start=this.until=this.end=this.lastTime=this.hitAt=-Infinity;this.hitKey='';
 }
 inspect(){return{visible:this.root.active,family:this.family,amount:this.amount,start:this.start,until:this.until,opacity:this.opacity,patternOpacity:this.patternOpacity,broken:this.broken,hitAt:this.hitAt,position:{x:this.root.worldPosition.x,y:this.root.worldPosition.y,z:this.root.worldPosition.z},scale:{x:this.root.scale.x,y:this.root.scale.y,z:this.root.scale.z},vertices:625,triangles:1152,passes:2};}
 destroy(){if(this.disposed)return;this.disposed=true;this.root.destroy();this.material.destroy();this.mesh.destroy();}
}
