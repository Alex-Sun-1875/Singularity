import {Camera,Quat,Vec3} from 'cc';
import type {Point} from '../../../core/Contracts';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';

/** Stable isometric medium shot, retaining the actor renderer's camera plane. */
export class CinematicCamera {
 private position=new Vec3();private rotation=new Quat();private height=0;private focus?:Point;
 private target=new Vec3();private shotHeight=0;
 constructor(private camera:Camera,private world:SceneBuilder){}
 begin(player:Point,focus?:Point){
  this.position.set(this.camera.node.position);this.rotation.set(this.camera.node.rotation);this.height=this.camera.orthoHeight;this.focus=undefined;
  this.shotHeight=Math.max(3.8,Math.min(5.5,this.height*.82));this.frame(player,focus);
 }
 frame(player:Point,focus?:Point){
  const point=focus??player;if(this.focus&&Math.hypot(point.x-this.focus.x,point.z-this.focus.z)<.05)return;
  this.focus={...point};const x=player.x+(point.x-player.x)*.45,z=player.z+(point.z-player.z)*.45;
  // Lower the optical centre a little so feet, objects and action clear the subtitles.
  this.target.set(x+15,this.world.height(player)+19.15,z+18);
 }
 update(dt:number,reducedMotion:boolean){
  const weight=reducedMotion?1:1-Math.exp(-Math.min(.1,dt)*8);
  const at=this.camera.node;at.setPosition(Vec3.lerp(new Vec3(),at.position,this.target,weight));
  at.lookAt(new Vec3(at.position.x-15,at.position.y-19.35,at.position.z-18));
  this.camera.orthoHeight+=(this.shotHeight-this.camera.orthoHeight)*weight;
 }
 restore(amount=1){
  const at=this.camera.node;at.setPosition(Vec3.lerp(new Vec3(),at.position,this.position,amount));
  at.setRotation(Quat.slerp(new Quat(),at.rotation,this.rotation,amount));this.camera.orthoHeight+=(this.height-this.camera.orthoHeight)*amount;
 }
}
