import {AnimationClip,AnimationState,Director,Node,Quat,Vec3,director,instantiate,type SkeletalAnimation} from 'cc';
import type {ActionState} from '../../../core/GameSession';
import {PlayerStationaryFootwork} from './PlayerStationaryFootwork';

type Joint={node:Node;sample:Node};
type Gait='walk'|'run';
type SavedJoint={node:Node;position:Vec3;rotation:Quat;appliedPosition:Vec3;appliedRotation:Quat};
const angle=(value:number)=>Math.atan2(Math.sin(value),Math.cos(value));

type SamplerMask=NonNullable<Parameters<AnimationState['initialize']>[2]>;
function sampledJoints(root:Node,kept:ReadonlySet<Node>):SamplerMask {
 // The 3.8.8 legacy sampler reads the mask's joint list. Its mask asset
 // constructor is not exported in the cropped runtime, so adapt that data
 // without pulling in the animation graph. Native pose QA covers this bridge.
 const joints:{path:string;enabled:boolean}[]=[];
 const visit=(node:Node,path:string)=>{
  if(!kept.has(node))joints.push({path,enabled:false});
  for(const child of node.children)visit(child,path?path+'/'+child.name:child.name);
 };
 visit(root,'');return {joints} as SamplerMask;
}

/** Sample the existing stride on a small, renderer-free skeleton. Apply only
 * its hips/legs after Cocos has evaluated the authoritative action pose. */
export class PlayerCombatLocomotion {
 private readonly sampleRoot:Node;
 private readonly samples:Record<Gait,AnimationState>;
 private readonly joints:Joint[]=[];
 private readonly braceJoints:Joint[]=[];
 private readonly staffBrace:AnimationState|undefined;
 private readonly braceRoot:Node|undefined;
 private braceWeight=0;
 private readonly pelvis:Joint;
 private readonly spine:Node;
 private readonly upperPosition=new Vec3();
 private readonly blendedPosition=new Vec3();
 private readonly upperRotation=new Quat();
 private readonly rotation=new Quat();
 private readonly inverse=new Quat();
 private readonly turn=new Quat();
 private weight=0;
 private phase=0;
 private heading=0;
 private backward=false;
 private gait:Gait='walk';
 private paused=false;
 private readonly footwork:PlayerStationaryFootwork|undefined;
 private readonly sourcePose:SavedJoint[];
 private poseSaved=false;private poseApplied=false;
 private manualSockets=false;
 private readonly autoSockets:SkeletalAnimation['sockets'];

 static create(skeletal:SkeletalAnimation,clips:Record<string,AnimationClip>,stride:Record<Gait,number>){
  const root=skeletal.node,sockets=skeletal.sockets;
  const find=(node:Node,name:string):Node|undefined=>node.name===name?node:node.children.map(child=>find(child,name)).find(Boolean);
  const pelvis=find(root,'pelvis'),spine=find(root,'spine_01'),left=find(root,'thigh_l'),right=find(root,'thigh_r');
  if(!pelvis||!spine||!left||!right||!clips.walk||!clips.run)return;
  return new PlayerCombatLocomotion(root,clips,stride,pelvis,spine,left,right,sockets,skeletal);
 }

 private constructor(root:Node,clips:Record<string,AnimationClip>,private readonly stride:Record<Gait,number>,pelvis:Node,spine:Node,left:Node,right:Node,sockets:readonly {path:string;target:Node|null}[],private readonly skeletal:SkeletalAnimation){
  this.spine=spine;
  this.autoSockets=skeletal.sockets;
  this.footwork=PlayerStationaryFootwork.create(root,sockets);
  const lower=new Set<Node>(),leg=(node:Node)=>{lower.add(node);for(const child of node.children)leg(child);};
  leg(left);leg(right);
  const arm=new Set<Node>(),collectArm=(node:Node)=>{arm.add(node);for(const child of node.children)collectArm(child);};
  const findArm=(node:Node):Node|undefined=>node.name==='clavicle_r'?node:node.children.map(findArm).find(Boolean),clavicle=findArm(spine);if(clavicle)collectArm(clavicle);
  for(let node:Node|null=pelvis;node&&node!==root;node=node.parent)lower.add(node);
  const sampled=new Set(lower),include=(node:Node)=>{sampled.add(node);for(const child of node.children)include(child);};
  include(pelvis);
  const copy=(node:Node):Node=>{
   const sample=new Node(node.name);sample.setPosition(node.position);sample.setRotation(node.rotation);sample.setScale(node.scale);
   if(lower.has(node))this.joints.push({node,sample});
   if(arm.has(node))this.braceJoints.push({node,sample});
   for(const child of node.children)if(sampled.has(child))sample.addChild(copy(child));
   return sample;
  };
  this.sampleRoot=copy(root);
  this.pelvis=this.joints.find(joint=>joint.node===pelvis)!;
  this.sourcePose=[...this.joints.map(joint=>joint.node),spine,...this.braceJoints.map(joint=>joint.node)].map(node=>({node,position:new Vec3(),rotation:new Quat(),appliedPosition:new Vec3(),appliedRotation:new Quat()}));
  const strideMask=sampledJoints(this.sampleRoot,new Set(this.joints.map(joint=>joint.sample)));
  const sample=(gait:Gait)=>{const state=new AnimationState(clips[gait]);state.initialize(this.sampleRoot,undefined,strideMask);state.wrapMode=AnimationClip.WrapMode.Loop;return state;};
  this.samples={walk:sample('walk'),run:sample('run')};
  if(clips.idle_staff){
   // A separate sampler prevents the held-arm pose from averaging the stride
   // during the few frames that blend from a hit back into moving combat.
   this.braceRoot=instantiate(this.sampleRoot);
   for(const joint of this.braceJoints){const path:string[]=[];for(let node:Node|null=joint.sample;node&&node!==this.sampleRoot;node=node.parent)path.unshift(node.name);joint.sample=this.braceRoot.getChildByPath(path.join('/'))!;}
   const braceMask=sampledJoints(this.braceRoot,new Set(this.braceJoints.map(joint=>joint.sample)));
   this.staffBrace=new AnimationState(clips.idle_staff);this.staffBrace.initialize(this.braceRoot,undefined,braceMask);
  }
  director.on(Director.EVENT_BEFORE_UPDATE,this.restorePose,this);
  director.on(Director.EVENT_AFTER_UPDATE,this.apply,this);
 }

 get active(){return this.weight>0||!!this.footwork?.active||this.braceWeight>0;}
 get stridePhase(){return this.phase;}
 setPaused(paused:boolean){
  const changed=this.paused!==paused;this.paused=paused;
  if(!changed)return;
  if(!paused)this.restorePose();
  else if(this.active&&this.poseApplied){
   for(const pose of this.sourcePose){if(!Vec3.equals(pose.node.position,pose.appliedPosition))pose.node.setPosition(pose.appliedPosition);if(!Quat.equals(pose.node.rotation,pose.appliedRotation))pose.node.setRotation(pose.appliedRotation);}
   this.poseSaved=true;
  }
 }
 reset(){this.restorePose(true);this.weight=0;this.phase=0;this.heading=0;this.backward=false;this.footwork?.reset();this.poseApplied=false;this.braceWeight=0;}
 setStaffHit(active:boolean,dt:number){
  this.braceWeight=active&&this.staffBrace?1:Math.max(0,this.braceWeight-dt/.06);
  if(this.braceWeight>0&&this.staffBrace){this.staffBrace.time=0;this.staffBrace.sample();}
 }
 setManualSockets(manual:boolean){
  if(this.manualSockets===manual)return;
  // Automatic sockets populate Cocos's per-frame joint matrix cache before
  // late pose corrections. Sample the same registered targets after our pose
  // instead, so real-time skinning and attached props see identical bones.
  this.skeletal.sockets=manual?[]:this.autoSockets;this.manualSockets=manual;
 }

 private restorePose(force=false){
  if(!this.poseSaved||this.paused&&!force)return;
  // Imported clips may omit constant channels. Undo the previous procedural
  // correction before evaluating the next frame so it cannot accumulate.
  for(const pose of this.sourcePose)if(pose.node.isValid){if(!Vec3.equals(pose.node.position,pose.position))pose.node.setPosition(pose.position);if(!Quat.equals(pose.node.rotation,pose.rotation))pose.node.setRotation(pose.rotation);}
  this.poseSaved=false;
 }

 update(dt:number,speed:number,relativeHeading:number,gait:Gait,enabled:boolean,blocked:boolean,basePhase?:number,action?:ActionState){
  this.paused=false;
  if(blocked){this.reset();return;}
  const stepping=enabled&&speed>.08;
  this.footwork?.update(dt,action,enabled&&!stepping&&!!action);
  if(stepping&&this.weight===0&&basePhase!==undefined)this.phase=basePhase%1;
  this.weight=Math.max(0,Math.min(1,this.weight+(stepping?1:-1)*dt/.10));
  if(this.weight===0)return;
  if(stepping){
   this.gait=gait;
   const direction=angle(relativeHeading),rear=Math.abs(direction);
   // Hysteresis prevents repeated forward/back switches during a strafe.
   this.backward=rear>(this.backward?Math.PI*.44:Math.PI*.56);
   const heading=angle(direction-(this.backward?Math.PI:0));
   this.heading=angle(this.heading+angle(heading-this.heading)*(1-Math.exp(-dt*18)));
   const cycle=this.samples[gait].clip.duration*this.stride[gait];
   this.phase=((this.phase+(this.backward?-1:1)*speed*dt/Math.max(.001,cycle))%1+1)%1;
  }
  const sample=this.samples[this.gait];sample.time=this.phase*sample.clip.duration;sample.sample();
 }

 private apply(){
  if(this.paused){if(this.manualSockets)this.footwork?.syncSockets();return;}
  if(!this.active||!this.spine.isValid)return;
  for(const pose of this.sourcePose){pose.position.set(pose.node.position);pose.rotation.set(pose.node.rotation);}
  this.poseSaved=true;
  this.footwork?.prepare();
  // Keep the action's upper body and its real hand/weapon sockets in place.
  // Only the lower-body joints receive the distance-driven stride.
  if(this.weight>0){
  this.upperPosition.set(this.spine.worldPosition);this.upperRotation.set(this.spine.worldRotation);
  for(const joint of this.joints){
   Vec3.lerp(this.blendedPosition,joint.node.position,joint.sample.position,this.weight);
   Quat.slerp(this.rotation,joint.node.rotation,joint.sample.rotation,this.weight);
   if(joint===this.pelvis){
    Quat.fromAxisAngle(this.turn,Vec3.UP,this.heading*this.weight);
    const parent=joint.node.parent!.worldRotation;
    Quat.invert(this.inverse,parent);Quat.multiply(this.turn,this.inverse,this.turn);Quat.multiply(this.turn,this.turn,parent);
    Quat.multiply(this.rotation,this.turn,this.rotation);
   }
   if(!Vec3.equals(joint.node.position,this.blendedPosition))joint.node.setPosition(this.blendedPosition);if(!Quat.equals(joint.node.rotation,this.rotation))joint.node.setRotation(this.rotation);
  }
  this.spine.setWorldPosition(this.upperPosition);this.spine.setWorldRotation(this.upperRotation);
  }
  this.footwork?.apply();
  if(this.braceWeight>0){
   for(const joint of this.braceJoints){Vec3.lerp(this.blendedPosition,joint.node.position,joint.sample.position,this.braceWeight);Quat.slerp(this.rotation,joint.node.rotation,joint.sample.rotation,this.braceWeight);joint.node.setPosition(this.blendedPosition);joint.node.setRotation(this.rotation);}
  }
  if(this.manualSockets)this.footwork?.syncSockets();
  for(const pose of this.sourcePose){pose.appliedPosition.set(pose.node.position);pose.appliedRotation.set(pose.node.rotation);}
  this.poseApplied=true;
 }
 inspect(){return {weight:this.weight,gait:this.gait,phase:this.phase,heading:this.heading,backward:this.backward,stationary:this.footwork?.inspect(),staffBrace:this.braceWeight};}
 destroy(){director.off(Director.EVENT_BEFORE_UPDATE,this.restorePose,this);director.off(Director.EVENT_AFTER_UPDATE,this.apply,this);for(const state of Object.values(this.samples))state.destroy();this.staffBrace?.destroy();this.braceRoot?.destroy();this.sampleRoot.destroy();}
}
