import {Mat4,Node,Quat,Vec3} from 'cc';
import type {ActionState} from '../../../core/GameSession';
import {actionReleaseAt} from './PlayerActionPresentation';
import {TwoBoneLegIK} from './TwoBoneLegIK';

type Leg={ik:TwoBoneLegIK;anchor:Vec3;rotation:Quat;target:Vec3;groundY:number};
type Socket={path:string;target:Node|null};
const clamp=(value:number)=>Math.max(0,Math.min(1,value));
const smooth=(value:number)=>{const t=clamp(value);return t*t*(3-2*t);};

/** One short, grounded advance-and-return step per action, on its rule clock. */
export class PlayerStationaryFootwork {
 private readonly legs:Leg[];
 private readonly inverse=new Mat4();private readonly rotation=new Quat();private readonly footRotation=new Quat();
 private readonly offset=new Vec3();private readonly localOffset=new Vec3();private readonly position=new Vec3();
 private readonly upperPosition=new Vec3();private readonly upperRotation=new Quat();
 private readonly socketMatrix=new Mat4();
 private readonly bindings:{bone:Node;target:Node}[];
 private actionId:string|undefined;private capture=false;private nextLead=0;private lead=0;private enabled=false;
 private entryElapsed=0;private lastKind='';
 private weight=0;private advance=0;private lift=0;private load=0;private breath=0;
 private readonly stepLength=.15;
 static create(root:Node,sockets:readonly Socket[]){
  const find=(node:Node,name:string):Node|undefined=>node.name===name?node:node.children.map(child=>find(child,name)).find(Boolean);
  const pelvis=find(root,'pelvis'),spine=find(root,'spine_01');
  const chains=['l','r'].map(side=>[find(root,'thigh_'+side),find(root,'calf_'+side),find(root,'foot_'+side)]);
  if(!pelvis||!spine||chains.some(chain=>chain.some(node=>!node)))return;
  return new PlayerStationaryFootwork(root,pelvis,spine,sockets,chains.map(([thigh,calf,foot])=>new TwoBoneLegIK(thigh!,calf!,foot!)));
 }
 private constructor(private readonly root:Node,private readonly pelvis:Node,private readonly spine:Node,private readonly sockets:readonly Socket[],chains:TwoBoneLegIK[]){
  Mat4.invert(this.inverse,root.worldMatrix);Quat.invert(this.rotation,root.worldRotation);
  this.legs=chains.map(ik=>{const anchor=Vec3.transformMat4(new Vec3(),ik.foot.worldPosition,this.inverse),rotation=Quat.multiply(new Quat(),this.rotation,ik.foot.worldRotation);return {ik,anchor,rotation,target:new Vec3(),groundY:anchor.y};});
  this.bindings=sockets.map(socket=>({bone:root.getChildByPath(socket.path),target:socket.target})).filter((binding):binding is {bone:Node;target:Node}=>!!binding.bone&&!!binding.target);
 }
 get active(){return this.weight>0;}
 reset(){this.weight=0;this.actionId=undefined;this.capture=false;this.advance=0;this.lift=0;this.load=0;this.breath=0;this.enabled=false;this.offset.set(0,0,0);}
 update(dt:number,action:ActionState|undefined,enabled:boolean){
  if(enabled&&action){
   if(this.actionId!==action.id||!this.enabled){this.actionId=action.id;this.lead=this.nextLead;this.nextLead=1-this.nextLead;this.capture=true;this.entryElapsed=0;}
   if(!this.enabled)this.entryElapsed=action.elapsed;
   if(action.kind==='bow'&&this.lastKind==='bowAim')this.entryElapsed=0;
   const elapsed=Math.max(0,action.elapsed-this.entryElapsed),duration=Math.max(.08,action.duration-this.entryElapsed);
   const held=action.kind==='bowAim',releasedBow=action.kind==='bow';
   const plantEnd=held?.30:releasedBow?0:Math.min(Math.max(.10,actionReleaseAt(action)-this.entryElapsed),duration*.55);
   const recoverStart=Math.max(plantEnd+.04,duration-.25);
   let out=0,back=0;
   if(held)out=clamp(elapsed/plantEnd);
   else if(releasedBow){out=1;back=clamp((elapsed-.035)/Math.max(.08,duration-.035));}
   else {out=clamp(elapsed/Math.max(.001,plantEnd));back=clamp((elapsed-recoverStart)/Math.max(.08,duration-recoverStart));}
   this.advance=this.stepLength*smooth(out)*(1-smooth(back));
   this.lift=.055*(Math.sin(Math.PI*out)**2+Math.sin(Math.PI*back)**2);
   this.load=smooth(out)*(1-smooth(back));
   this.breath=this.load*(held?.003:.005)*Math.sin(action.elapsed*(held?3.5:11));
   this.lastKind=action.kind;
  }
  this.enabled=enabled;
  this.weight=clamp(this.weight+(enabled?1:-1)*dt/.10);
 }
 prepare(){
  if(!this.active||!this.spine.isValid)return;
  if(this.capture){
   Mat4.invert(this.inverse,this.root.worldMatrix);
   for(const leg of this.legs){Vec3.transformMat4(leg.anchor,leg.ik.foot.worldPosition,this.inverse);leg.anchor.y=leg.groundY;}
   this.capture=false;
  }
 }
 apply(){
  if(!this.active||!this.spine.isValid)return;
  const supportSide=this.lead===0?-1:1;
  this.localOffset.set(supportSide*(.024*this.lift/.055+.006*this.load),-.014*this.load-.009*this.lift/.055+this.breath,.045*this.load);
  Vec3.transformQuat(this.offset,this.localOffset,this.root.worldRotation).multiplyScalar(this.weight);
  let sink=0;
  for(let i=0;i<this.legs.length;i++){
   const leg=this.legs[i];this.localOffset.set(0,i===this.lead?this.lift:0,i===this.lead?this.advance:0);
   Vec3.transformQuat(this.position,this.localOffset,this.root.worldRotation);
   Vec3.transformMat4(leg.target,leg.anchor,this.root.worldMatrix).add(this.position);
   // Authored combo poses can raise the hips and change their root scale.
   // Lower the centre of mass enough to reach both feet without stretching.
   const hip=leg.ik.thigh.worldPosition,knee=leg.ik.calf.worldPosition,foot=leg.ik.foot.worldPosition,reach=Vec3.distance(hip,knee)+Vec3.distance(knee,foot)-.006;
   const dx=hip.x+this.offset.x-leg.target.x,dz=hip.z+this.offset.z-leg.target.z;
   sink=Math.min(sink,leg.target.y+Math.sqrt(Math.max(.0001,reach*reach-dx*dx-dz*dz))-hip.y-this.offset.y);
  }
  this.offset.y+=Math.max(-.18,sink)*this.weight;
  this.upperPosition.set(this.spine.worldPosition).add(this.offset);this.upperRotation.set(this.spine.worldRotation);
  Vec3.add(this.position,this.pelvis.worldPosition,this.offset);this.pelvis.setWorldPosition(this.position);
  for(const leg of this.legs){
   Quat.multiply(this.footRotation,this.root.worldRotation,leg.rotation);leg.ik.solve(leg.target,this.footRotation,this.weight);
  }
  this.spine.setWorldPosition(this.upperPosition);this.spine.setWorldRotation(this.upperRotation);
  // Rebind from the final bones, including frames that switch baked/real-time
  // modes. Translating a cached socket alone can preserve an old clip's pose.
 }
 syncSockets(){for(const {bone,target} of this.bindings)if(target.isValid&&target.parent){Mat4.invert(this.inverse,target.parent.worldMatrix);Mat4.multiply(this.socketMatrix,this.inverse,bone.worldMatrix);target.matrix=this.socketMatrix;}}
 inspect(){return {weight:this.weight,lead:this.lead===0?'left':'right',advance:this.advance,lift:this.lift,load:this.load,offset:{x:this.offset.x,y:this.offset.y,z:this.offset.z}};}
}
