import {FireFieldEffects} from './FireFieldEffects';
import {FireImpactEffects} from './FireImpactEffects';
import {gameResources as resources} from '../../../shared/assets/GameResources';
import {Camera,EffectAsset,Material,Mesh,MeshRenderer,Node,Quat,Texture2D,Vec3,Vec4,primitives,utils} from 'cc';

type Point={x:number;z:number};
type FireBody={key:string;root:Node;card:Node;material:Material;touched:boolean;phase:number;blend:number;width:number;height:number;mode:string;textureId:number};
const LIMIT=64,FRAMES=32,ROOT=.416666667;
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const smooth=(n:number)=>{n=clamp(n);return n*n*(3-2*n);};

/** The approved lance has its own silhouette; charge/comet wisps retain their
 * narrow flow. Ground field and radial impact use connected native surfaces,
 * rather than repeated upright cards. Presentation reads resolved combat only. */
export class SkillFireSprites {
 private static textures:Texture2D[]=[];
 private static effect:EffectAsset|undefined;
 private static pending:Promise<void>|null=null;
 private static revision=0;
 private readonly root:Node;
 private readonly mesh:Mesh;
 private readonly items:FireBody[]=[];
 private readonly rotation=new Quat();
 private readonly roll=new Quat();
 private readonly direction=new Vec3();
 private readonly color=new Vec4(1,1,1,1);
 private readonly frameState=new Vec4();
 private readonly field:FireFieldEffects;
 private readonly impact:FireImpactEffects;
 private disposed=false;
 reducedMotion=false;
 static preload():Promise<void>{
  if(this.pending)return this.pending;const revision=this.revision;
  const textures=['fire-ground-jets-v27','fire-lance-v30','fire-meteor-reference-tail-v33'].map(name=>new Promise<Texture2D>((resolve,reject)=>resources.load('vfx/production/'+name+'/texture',Texture2D,(error,asset)=>{if(error){reject(error);return;}asset.addRef();resolve(asset);})));
  const effect=new Promise<EffectAsset>((resolve,reject)=>resources.load('vfx/production/fire-sprites-v30',EffectAsset,(error,asset)=>{if(error){reject(error);return;}asset.addRef();resolve(asset);}));
  this.pending=(async()=>{
   const [a,b,c,e]=await Promise.allSettled([...textures,effect]);
   if(a.status==='rejected'||b.status==='rejected'||c.status==='rejected'||e.status==='rejected'||revision!==this.revision){
    for(const result of [a,b,c,e])if(result.status==='fulfilled')result.value.decRef();
    throw a.status==='rejected'?a.reason:b.status==='rejected'?b.reason:c.status==='rejected'?c.reason:e.status==='rejected'?e.reason:new Error('Fire sprites load cancelled');
   }
   this.textures=[a.value as Texture2D,b.value as Texture2D,c.value as Texture2D];this.effect=e.value as EffectAsset;
   for(const texture of this.textures){texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);}
   await Promise.all([FireFieldEffects.preload(),FireImpactEffects.preload()]);
  })().catch(error=>{if(revision===this.revision)this.dispose();throw error;});return this.pending;
 }
 static dispose(){this.revision++;for(const texture of this.textures)texture.decRef();this.effect?.decRef();this.textures=[];this.effect=undefined;this.pending=null;FireFieldEffects.dispose();FireImpactEffects.dispose();}
 constructor(parent:Node,private readonly camera?:Camera,groundHeight?:(p:Point)=>number,visible?:(a:Point,b:Point)=>boolean){
  this.field=new FireFieldEffects(parent,camera,groundHeight??(()=>0),visible);this.impact=new FireImpactEffects(parent,camera,groundHeight??(()=>0),visible);
  this.root=new Node('FireDistinctSprites');this.root.layer=parent.layer;parent.addChild(this.root);
  const geometry=primitives.quad();for(let i=1;i<geometry.uvs!.length;i+=2)geometry.uvs![i]=1-geometry.uvs![i];this.mesh=utils.createMesh(geometry);this.mesh.name='FireSharedWispQuad';
 }
 begin(){this.field.reducedMotion=this.impact.reducedMotion=this.reducedMotion;this.field.begin();this.impact.begin();for(const item of this.items)item.touched=false;}
 private sprite(key:string,p:Vec3,width:number,height:number,clock:number,alpha:number,direction?:Vec3,lance=false,comet=false){
  if(this.disposed||!(width>0&&height>0&&alpha>1))return;
  let item=this.items.find(i=>i.key===key)??this.items.find(i=>!i.touched&&!i.root.active);
  if(!item){
   if(this.items.length>=LIMIT)return;
   if(!SkillFireSprites.effect||!SkillFireSprites.textures[0])throw new Error('SkillFireSprites.preload must finish before rendering');
   const root=new Node('FireAnchor'),card=new Node('ReferenceWisp');root.layer=card.layer=this.root.layer;root.active=false;this.root.addChild(root);root.addChild(card);
   const material=new Material();material.name='FireDistinctSpritesV30';material.initialize({effectAsset:SkillFireSprites.effect});
   const renderer=card.addComponent(MeshRenderer);renderer.mesh=this.mesh;renderer.setSharedMaterial(material,0);renderer.shadowCastingMode=0;renderer.receiveShadow=0;
   item={key,root,card,material,touched:false,phase:-1,blend:0,width:0,height:0,mode:'',textureId:-1};this.items.push(item);
  }
  item.key=key;item.touched=true;item.root.active=true;item.root.setWorldPosition(p);
  if(direction&&this.camera?.node.isValid){
   Quat.copy(this.rotation,this.camera.node.worldRotation);
   // Authored root is at the head; the long axis and fine tips trail backwards.
   const right=this.camera.node.right,up=this.camera.node.up;
   const angle=(lance||comet?Math.atan2(Vec3.dot(direction,up),Vec3.dot(direction,right)):Math.atan2(-Vec3.dot(direction,up),-Vec3.dot(direction,right))-Math.PI/2)-(comet?9.391739408467398*Math.PI/180:0);
   Quat.fromEuler(this.roll,0,0,angle*180/Math.PI);Quat.multiply(this.rotation,this.rotation,this.roll);
  }else if(this.camera?.node.isValid){const f=this.camera.node.forward;Quat.fromEuler(this.rotation,0,Math.atan2(-f.x,-f.z)*180/Math.PI,0);}
  else Quat.fromEuler(this.rotation,0,40,0);
  item.root.setWorldRotation(this.rotation);item.card.setPosition(comet?-.451972710655*width:lance?-.466796875*width:0,comet?-.222424849118*height:lance?.08754639*height:ROOT*height,comet?height*.55:0);item.card.setScale(width,height,1);
  const textureId=comet?2:lance?1:0;if(item.textureId!==textureId){item.material.setProperty('mainTexture',SkillFireSprites.textures[textureId]);item.material.setProperty('atlasState',lance||comet?new Vec4(4,4,16,1):new Vec4(8,4,32,0));item.textureId=textureId;}
  const frames=lance||comet?16:FRAMES,frame=((clock%frames)+frames)%frames,whole=Math.floor(frame),blend=frame-whole;
  this.frameState.set(whole,(whole+1)%frames,blend,0);item.material.setProperty('frameState',this.frameState);
  this.color.w=clamp(alpha/255);item.material.setProperty('mainColor',this.color);
  item.phase=whole;item.blend=blend;item.width=width;item.height=height;item.mode=comet?'reference-comet':lance?'lance':direction?'wake':'upright';
 }
 private clock(time:number,offset=0){return time*(this.reducedMotion?12:24)+offset;}
 private wakeLength(head:Vec3,direction:Vec3,travel:number,hand?:Vec3){
  const normal=this.camera?.node.forward,dot=normal?Vec3.dot(direction,normal):0,length=Math.sqrt(Math.max(0,direction.lengthSqr()-dot*dot));
  if(length<.0001)return 0;let distance=travel*length;
  if(hand){const x=direction.x-(normal?.x??0)*dot,y=direction.y-(normal?.y??0)*dot,z=direction.z-(normal?.z??0)*dot;distance=Math.min(distance,((head.x-hand.x)*x+(head.y-hand.y)*y+(head.z-hand.z)*z)/length);}
  return Math.max(0,distance-.20)/(.5+ROOT);
 }
 drawProjectile(key:string,head:Vec3,direction:Vec3,size:number,time:number,alpha=255,travel=Infinity,hand?:Vec3){
  const available=this.wakeLength(head,direction,travel,hand)*(.5+ROOT),length=Math.min(size*2.8,available/.966796875);if(length<.06)return;
  const height=size*.48*Math.min(1,length/(size*.7));
  this.sprite(key,head,length,height,this.clock(time),alpha,direction,true);
 }
 drawComet(key:string,head:Vec3,direction:Vec3,size:number,time:number,alpha=255,tailStage=-1){
  const length=size*4.818*(tailStage<0?1:Math.max(.10,tailStage/4));
  // This dedicated original-reference sheath includes its wrapped head and
  // flowing long tail. Its measured leading nose, not its image centre, is
  // the same world point as the rock's physical leading support and impact.
  this.sprite(key,head,length,length*(192/512),this.clock(time,7),alpha,direction,false,true);
 }
 drawBasicComet(key:string,head:Vec3,direction:Vec3,size:number,time:number,travel:number,hand?:Vec3){
  this.drawProjectile(key,head,direction,size*.72,time,255,travel,hand);
 }
 draw(key:string,foot:Vec3,width:number,height:number,phase:number,alpha:number){this.sprite(key,foot,width,height,phase*24,alpha);}
 drawPlume(key:string,foot:Vec3,size:number,time:number,alpha:number){this.sprite(key,foot,size*.72,size*1.7,this.clock(time),alpha);}
 drawCharge(key:string,hand:Vec3,facing:number,progress:number,release:number,strength:number,alpha:number){
  const p=clamp(progress),turn=release>=0?smooth(release):0,width=(.24+.12*p)*strength;
  this.direction.set(-Math.sin(facing)*turn,-(1-turn),-Math.cos(facing)*turn).normalize();
  this.sprite(key+':flame',hand,width,width*1.55,(p*18+Math.max(0,release)*10),alpha,this.direction);
 }
 followCharge(key:string,hand:Vec3){for(const item of this.items)if(item.root.active&&item.key===key+':flame')item.root.setWorldPosition(hand);}
 drawVolume(key:string,foot:Vec3,radius:number,rank:number,progress:number,alpha:number,time=progress,angle?:number,age?:number,duration?:number){this.impact.draw(key,foot,radius,rank,progress,alpha,time,angle,age,duration);}
 drawRibbon(key:string,foot:Vec3,width:number,depth:number,angle:number,time:number,alpha:number,origin:Point=foot,cooling=-1){this.field.draw(key,foot,width,depth,angle,time,alpha,origin,cooling);}
 end(){this.field.end();this.impact.end();for(const item of this.items)if(!item.touched)item.root.active=false;}
 clear(){this.field.clear();this.impact.clear();for(const item of this.items){item.root.active=false;item.touched=false;item.key='';}}
 inspect(){const field=this.field.inspect(),impact=this.impact.inspect();return{model:'distinct-fire-shapes-v30',capacity:LIMIT+field.capacity+impact.capacity,allocated:this.items.length+field.allocated+impact.allocated,sharedTextures:SkillFireSprites.textures.length,field,impact,active:[...this.items.filter(i=>i.root.active).map(i=>({key:i.key,kind:i.mode,phase:i.phase,frameBlend:i.blend,textureId:i.textureId,region:0,width:i.width,height:i.height,viewBias:i.mode==='reference-comet'?i.height*.55:0,position:{x:i.root.worldPosition.x,y:i.root.worldPosition.y,z:i.root.worldPosition.z}})),...field.active,...impact.active]};}
 destroy(){if(this.disposed)return;this.disposed=true;this.field.destroy();this.impact.destroy();for(const item of this.items)item.material.destroy();this.root.destroy();this.items.length=0;this.mesh.destroy();}
}
