import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {Camera,Graphics,Node,UITransform,Vec2,Vec3,screen} from 'cc';
import type {GameEvent,Point} from '../../../core/Contracts';
import type {GameSession} from '../../../core/GameSession';
import {impactKey,impactStyle,type ImpactStyle} from '../data/CombatImpact';
import type {Hud} from '../../../app/Hud';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';

type Contact={node:Node;ink:Graphics;id:string;point:Point;start:number;style:ImpactStyle;angle:number};
/** Bounded contact cues and camera impulses. Rules, input and HUD time keep running. */
export class CombatImpactFeedback {
 reducedMotion=false;
 private root:Node;private contacts:Contact[]=[];private clock=0;private nextSound=0;private nextKick=0;
 private kick:{start:number;strength:number;direction:Vec2}|null=null;private offset=new Vec3();
 private hits=0;private sounds=0;private maximumKick=0;
 constructor(private hud:Hud,private camera:Camera,private world:SceneBuilder,private play:(id:string,volume:number)=>void,private headPoint?:(id:string)=>Vec3|undefined){
  this.root=hud.node('CombatImpactFeedback',hud.root,0,0,1,1);this.root.setSiblingIndex(0);
 }
 private bodyPoint(id:string,point:Point){const foot=new Vec3(point.x,this.world.height(point),point.z),head=this.headPoint?.(id);return head?Vec3.lerp(new Vec3(),foot,head,.53):foot.add(new Vec3(0,.95,0));}
 /** Remove last frame's visual displacement before the normal camera follows. */
 beforeCamera(){if(this.offset.lengthSqr()>0&&this.camera.node.isValid)this.camera.node.setPosition(this.camera.node.position.clone().subtract(this.offset));this.offset.set(0,0,0);}
 onEvents(events:readonly GameEvent[],game:GameSession){
  if(events.some(e=>['area','travel','retry'].includes(e.type))){this.clear();return;}
  const blocked=new Set(events.filter(e=>e.type==='block').map(impactKey)),chosen=new Map<string,{event:GameEvent;style:ImpactStyle}>();
  for(const event of events){const style=impactStyle(event,blocked.has(impactKey(event)));if(!style||!event.id)continue;const key=impactKey(event),previous=chosen.get(key);if(!previous||style.priority>=previous.style.priority)chosen.set(key,{event,style});}
  let strongest:ImpactStyle|undefined;
  for(const {event,style}of chosen.values()){
   const enemy=game.state.enemies.find(e=>e.id===event.id),point=event.at??enemy;if(!point)continue;
   // Offscreen contacts do not consume impact/sound budget or shake the camera.
   const at=this.camera.worldToScreen(this.bodyPoint(event.id!,point)),size=screen.windowSize;
   if(at.z<0||at.z>1||at.x<0||at.x>size.width||at.y<0||at.y>size.height)continue;
   let cue=this.contacts.find(c=>!c.node.active)|| (this.contacts.length<12?this.create():this.contacts.reduce((a,b)=>a.start<b.start?a:b));
   const duplicate=this.contacts.find(c=>c.node.active&&c.id===event.id&&this.clock-c.start<.045);if(duplicate){if(duplicate.style.priority>=style.priority)continue;cue=duplicate;}
   cue.id=event.id!;cue.point={x:point.x,z:point.z};cue.start=this.clock;cue.style=style;cue.angle=Number(event.angle??Math.atan2(point.x-game.state.player.x,point.z-game.state.player.z));cue.node.active=true;this.hits++;
   if(!strongest||style.priority>strongest.priority)strongest=style;
   if(!this.reducedMotion&&style.kick>0&&this.clock>=this.nextKick){
    const right=this.camera.node.right,up=this.camera.node.up,direction=new Vec2(Math.sin(cue.angle)*right.x+Math.cos(cue.angle)*right.z,Math.sin(cue.angle)*up.x+Math.cos(cue.angle)*up.z);direction.normalize();
    this.kick={start:this.clock,strength:style.kick,direction};this.nextKick=this.clock+.095;
   }else if(this.kick&&this.clock-this.kick.start<.025)this.kick.strength=Math.max(this.kick.strength,style.kick);
  }
  if(strongest?.sound&&this.clock>=this.nextSound){this.play(strongest.sound,strongest.volume);this.sounds++;this.nextSound=this.clock+.065;}
 }
 private create():Contact {const node=this.hud.node('ContactImpact',this.root,0,0,1,1),ink=node.addComponent(CompactGraphics);node.active=false;const cue={node,ink,id:'',point:{x:0,z:0},start:0,style:undefined as unknown as ImpactStyle,angle:0};this.contacts.push(cue);return cue;}
 update(dt:number,game:GameSession,paused:boolean){
  if(paused){this.clear();return;}this.clock+=Math.min(.1,Math.max(0,dt));
  const cssHeight=screen.windowSize.height/Math.max(1,screen.devicePixelRatio),scale=this.hud.height/Math.max(1,cssHeight);
  if(this.kick&&!this.reducedMotion){const age=(this.clock-this.kick.start)/.13;if(age>=1)this.kick=null;else{const amount=this.kick.strength*scale*Math.sin(age*Math.PI*3)*Math.exp(-age*4),worldPixel=2*this.camera.orthoHeight/this.hud.height;this.offset.set(this.camera.node.right).multiplyScalar(this.kick.direction.x*amount*worldPixel).add(this.camera.node.up.clone().multiplyScalar(this.kick.direction.y*amount*worldPixel));this.camera.node.setPosition(this.camera.node.position.clone().add(this.offset));this.maximumKick=Math.max(this.maximumKick,Math.abs(amount)/scale);}}
  for(const cue of this.contacts){if(!cue.node.active)continue;const progress=(this.clock-cue.start)/cue.style.duration;if(progress>=1){cue.node.active=false;continue;}
   const p=game.state.enemies.find(e=>e.id===cue.id)??cue.point,at=this.camera.worldToScreen(this.bodyPoint(cue.id,p)),pixels=screen.windowSize;
   if(at.z<0||at.z>1||at.x<0||at.x>pixels.width||at.y<0||at.y>pixels.height){cue.node.active=false;continue;}
   cue.node.setPosition(at.x/pixels.width*this.hud.width-this.hud.width/2,at.y/pixels.height*this.hud.height-this.hud.height/2);
   const g=cue.ink,radius=cue.style.radius*scale*(.55+progress*.7),fade=Math.pow(1-progress,1.4),alpha=Math.round((this.reducedMotion?110:235)*fade);g.clear();
   if(!this.reducedMotion&&progress<.28){F.ink(g,'impact.core','fill',Math.round(alpha*(1-progress/.28)*.65));g.circle(0,0,radius*.32);g.fill();}
   F.ink(g,cue.style.role,'stroke',alpha);g.lineWidth=scale*(cue.style.kind==='armor'?1.4:1.8);
   const spikes=cue.style.kind==='burn'?3:cue.style.kind==='critical'||cue.style.kind==='kill'?8:5;
   for(let i=0;i<spikes;i++){const a=i/spikes*Math.PI*2+cue.angle,len=radius*(i%2?.65:1);g.moveTo(Math.cos(a)*len*.4,Math.sin(a)*len*.4);g.lineTo(Math.cos(a)*len,Math.sin(a)*len);}g.stroke();
   if(cue.style.kind!=='burn'){F.ink(g,cue.style.kind==='critical'||cue.style.kind==='kill'?'damage.critical':cue.style.role,'stroke',Math.round(alpha*.55));g.lineWidth=scale*.8;g.arc(0,0,radius*.65,progress*.9,Math.PI*1.35+progress*.9,false);g.stroke();}
  }
 }
 clear(){this.beforeCamera();for(const cue of this.contacts)cue.node.active=false;this.kick=null;}
 inspect(){return {allocated:this.contacts.length,limit:12,active:this.contacts.filter(c=>c.node.active).map(c=>({id:c.id,kind:c.style.kind,age:this.clock-c.start,radius:c.style.radius})),hits:this.hits,sounds:this.sounds,maximumKickPixels:this.maximumKick,reducedMotion:this.reducedMotion};}
 destroy(){this.clear();this.root.destroy();this.contacts=[];}
}
