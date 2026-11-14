import {Button,Camera,EventTouch,Label,Node,UITransform,Vec2,Vec3,screen,sys} from 'cc';
import type {Point,InteractionDef} from '../../../core/Contracts';
import type {Hud} from '../../../app/Hud';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {qualityFeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {journeyText} from '../../journey/locales';

export interface SceneInteractionTarget {id:string;name:string;verb:string;point:Point;height:number;blocked?:string;quality?:string;anchorHeight?:number;avoid?:{point:Point;height:number};objective?:boolean}

/** One text action attached to the nearby scene target, never a permanent HUD slot. */
export class SceneInteraction {
 private root:Node|null=null;private button:Node|null=null;private label:Label|null=null;
 private target:SceneInteractionTarget|null=null;private pressedId:string|null=null;
 private width=0;private height=0;private faceWidth=0;private faceHeight=0;
 private approached=new Set<string>();private approachScan=0;
 constructor(private hud:Hud,private camera:Camera,private perform:(id:string)=>void){}
 rememberApproach(objects:InteractionDef[],player:Point){
  for(const o of objects)if(Math.hypot(o.x-player.x,o.z-player.z)<=Math.min(1.35,o.radius??1.35)+.35)this.approached.add(o.id);
 }
 approach(objects:InteractionDef[],player:Point,dt:number,available:(o:InteractionDef)=>boolean,preferredId?:string){
  this.approachScan-=dt;if(this.approachScan>0)return;this.approachScan=.1;
  let nearest:InteractionDef|undefined,best=Infinity;
  for(const o of objects){
   const d=Math.hypot(o.x-player.x,o.z-player.z),radius=Math.min(1.35,o.radius??1.35);
   // A wider exit radius prevents close/reopen loops and boundary jitter.
   if(d>radius+.75){this.approached.delete(o.id);continue;}
   if(d>radius||this.approached.has(o.id)||!available(o))continue;
   if(o.id===preferredId){nearest=o;break;}
   if(d<best){nearest=o;best=d;}
  }
  if(nearest)this.rememberApproach(objects,player);
  return nearest;
 }
 private build(){
  this.root?.destroy();this.width=this.hud.width;this.height=this.hud.height;
  this.faceHeight=Math.max(sys.isMobile?this.hud.touchTargetSize:48,48);
  this.faceWidth=Math.max(sys.isMobile?284:208,this.faceHeight*3);
  this.root=this.hud.node('SceneInteraction',this.hud.root);
  this.hud.modal.setSiblingIndex(this.hud.root.children.length-1);
  this.button=this.hud.button(this.root,'',0,0,this.faceWidth,this.faceHeight,'scene-interaction');
  this.label=this.button.getComponentInChildren(Label)!;this.label.fontSize=sys.isMobile?22:16;this.label.lineHeight=this.label.fontSize*1.25;
  this.button.off(Button.EventType.CLICK);
  this.button.on(Node.EventType.TOUCH_START,(e:EventTouch)=>{e.propagationStopped=true;this.pressedId=this.target?.id??null;});
  this.button.on(Node.EventType.TOUCH_END,(e:EventTouch)=>{e.propagationStopped=true;});
  this.button.on(Node.EventType.TOUCH_CANCEL,()=>{this.pressedId=null;});
  this.button.on(Button.EventType.CLICK,()=>{const id=this.pressedId;this.pressedId=null;if(id&&id===this.target?.id&&!this.target.blocked){this.root!.active=false;this.perform(id);}});
 }
 update(target:SceneInteractionTarget|null,hidden=false){
  if(!this.root?.isValid||this.width!==this.hud.width||this.height!==this.hud.height)this.build();
  if(this.target?.id!==target?.id)this.pressedId=null;
  this.target=target;this.root!.active=!!target&&!hidden;if(!target||hidden)return;
  const at=this.camera.worldToScreen(new Vec3(target.point.x,target.height+(target.anchorHeight??2.4),target.point.z)),pixels=screen.windowSize;
  const x=at.x/Math.max(1,pixels.width)*this.width-this.width/2,y=at.y/Math.max(1,pixels.height)*this.height-this.height/2;
  const halfW=this.faceWidth/2,halfH=this.faceHeight/2;
  const avoid=target.avoid&&this.camera.worldToScreen(new Vec3(target.avoid.point.x,target.avoid.height,target.avoid.point.z));
  const player=avoid?{x:avoid.x/Math.max(1,pixels.width)*this.width-this.width/2,y:avoid.y/Math.max(1,pixels.height)*this.height-this.height/2}:undefined;
  // If the target is offscreen or hidden by existing edge controls, do not pin
  // a detached action somewhere else on the screen.
  const candidates=target.quality||target.objective?[
   {x:Math.max(x+halfW+24,(player?.x??x)+halfW+this.faceHeight*.65+16),y},
   {x:Math.min(x-halfW-24,(player?.x??x)-halfW-this.faceHeight*.65-16),y},
   {x,y:Math.max(y+halfH+24,(player?.y??y)+halfH+this.faceHeight*1.2+16)},
   {x,y:Math.min(y-halfH-24,(player?.y??y)-halfH-this.faceHeight*1.2-16)},
  ]:[{x,y:y+halfH+8},{x:x+halfW+16,y},{x:x-halfW-16,y}];
  const place=candidates.find(q=>(!player||Math.abs(q.x-player.x)>halfW+this.faceHeight*.65||Math.abs(q.y-player.y)>halfH+this.faceHeight*1.2)&&Math.abs(q.x)+halfW<this.width/2-12&&Math.abs(q.y)+halfH<this.height/2-12&&[
   [0,0],[-halfW,-halfH],[halfW,-halfH],[-halfW,halfH],[halfW,halfH],
  ].every(([dx,dy])=>!this.hud.isOverUI(new Vec2((q.x+dx+this.width/2)/this.width*pixels.width,(q.y+dy+this.height/2)/this.height*pixels.height))));
  this.root!.active=!!place;if(!place)return;
  this.root!.setPosition(place.x,place.y);
  const name=target.name.length>10?target.name.slice(0,9)+'…':target.name;
  this.label!.string=`${name}\n${target.blocked??`${sys.isMobile?'点击':'F ·'}${target.verb}${target.objective?' · '+journeyText('marker.task'):''}`}`;
  F.tint(this.label!,target.blocked?'state.blocked':target.objective?'map.task':target.quality?qualityFeedbackRole(target.quality):'state.ready');
  this.button!.getComponent(Button)!.interactable=!target.blocked;
 }
 isOverUI(point:Vec2){return !!this.root?.activeInHierarchy&&!!this.button?.getComponent(UITransform)?.hitTest(point);}
 get visibleTargetId(){return this.root?.activeInHierarchy?this.target?.id:undefined;}
 inspect(){return {visible:!!this.root?.activeInHierarchy,target:this.target?.id??null,name:this.target?.name??'',verb:this.target?.verb??'',blocked:this.target?.blocked??null,text:this.label?.string??'',position:this.root?{x:this.root.position.x,y:this.root.position.y}:null,width:this.faceWidth,height:this.faceHeight};}
 destroy(){this.root?.destroy();this.root=null;this.target=null;this.pressedId=null;}
}
