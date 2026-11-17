import {viewportMetrics} from '../../../platform/ViewportMetrics';
import {Camera,Graphics,Label,Node,Vec2,Vec3,sys} from 'cc';
import type {Hud} from '../../../app/Hud';
import type {GameSession} from '../../../core/GameSession';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';
import type {JourneyGuidance} from '../common/JourneyGuide';
import {objectiveTarget} from '../common/ObjectiveTarget';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {fitRpgLine} from '../../../shared/ui/RpgFont';
import {journeyText as text} from '../locales';

/** One passive, camera-anchored objective. The existing scene button owns input. */
export class TaskPresence {
 private root:Node|null=null;private title:Label|null=null;private detail:Label|null=null;private mark:Graphics|null=null;
 private width=0;private height=0;private target='';private visible=false;private skin='';private compact=false;
 private anchor=new Vec3();private projected=new Vec3();private sample=new Vec2();
 constructor(private hud:Hud,private camera:Camera,private world:SceneBuilder){}
 private build(){
  this.root?.destroy();this.width=this.hud.width;this.height=this.hud.height;this.skin='';
  this.root=this.hud.node('TaskPresence',this.hud.root,0,0,300,62);
  this.mark=this.hud.node('TaskPresenceFlag',this.root,-137,12,22,26).addComponent(CompactGraphics);
  this.title=this.hud.text(this.root,'',12,12,274,sys.isMobile?24:20,F.color('map.task'),30);this.title.node.name='TaskPresenceName';this.title.horizontalAlign=Label.HorizontalAlign.CENTER;
  this.detail=this.hud.text(this.root,'',0,-16,284,sys.isMobile?21:16,F.color('text.normal'),26);this.detail.node.name='TaskPresenceDistance';this.detail.horizontalAlign=Label.HorizontalAlign.CENTER;
  for(const label of [this.title,this.detail]){label.enableWrapText=false;label.enableOutline=true;label.outlineWidth=2;label.outlineColor=F.color('text.outline');}
 }
 private hide(){this.visible=false;if(this.root?.active)this.root.active=false;}
 update(game:GameSession,guide:JourneyGuidance|null,hidden=false,interactionId?:string){
  const target=objectiveTarget(game,guide);this.target=target?.id??'';
  // Enemy names and HP belong to EnemyCombatFeedback, not a second quest caption.
  if(hidden||!target||target.type==='enemy'||target.id===interactionId){this.hide();return;}
  if(!this.root?.isValid||this.width!==this.hud.width||this.height!==this.hud.height)this.build();
  const p=game.state.player;if(!this.world.visible(p,target.point)||Math.abs(this.world.height(p)-this.world.height(target.point))>6){this.hide();return;}
  this.anchor.set(target.point.x,this.world.height(target.point),target.point.z);this.anchor.add(Vec3.multiplyScalar(this.projected,this.camera.node.up,target.type==='exit'?3.1:2));
  this.camera.worldToScreen(this.anchor,this.projected);if(this.projected.z<0||this.projected.z>1){this.hide();return;}
  const pixels=viewportMetrics.windowSize,x=this.projected.x/Math.max(1,pixels.width)*this.width-this.width/2,y=this.projected.y/Math.max(1,pixels.height)*this.height-this.height/2,halfW=150,halfH=31;
  const fits=(w:number,h:number)=>{
   if(Math.abs(x)+w>this.width/2-16||Math.abs(y)+h>this.height/2-16)return false;
   for(const [dx,dy]of [[0,0],[-w,-h],[w,-h],[-w,h],[w,h]]){this.sample.set((x+dx+this.width/2)/this.width*pixels.width,(y+dy+this.height/2)/this.height*pixels.height);if(this.hud.isOverUI(this.sample))return false;}return true;
  };
  this.compact=!fits(halfW,halfH);if(this.compact&&!fits(15,16)){this.hide();return;}
  this.title!.node.active=!this.compact;this.detail!.node.active=!this.compact;this.mark!.node.setPosition(this.compact?0:-137,this.compact?0:12);
  const role=target.blocked?'state.blocked':'map.task';
  if(this.skin!==role){this.skin=role;const g=this.mark!;g.clear();F.ink(g,role,'fill');F.ink(g,'text.outline','stroke');g.lineWidth=2;
   g.moveTo(-8,-10);g.lineTo(-8,10);g.lineTo(9,10);g.lineTo(4,3);g.lineTo(-8,3);g.close();g.fill();g.stroke();F.tint(this.title!,role);
  }
  const prefix=target.kind==='hunt'?text('marker.hunt'):target.type==='exit'?text('marker.travel'):text('marker.task'),title=fitRpgLine(`${prefix} · ${target.name}`,274,this.title!.fontSize),detail=`${target.blocked?target.blockage?.summary??text('detail.blocked'):target.action}${target.level?` · Lv${target.level}`:''} · ${text('detail.distance',{distance:Math.ceil(target.distance)})}`;
  if(this.title!.string!==title)this.title!.string=title;if(this.detail!.string!==detail)this.detail!.string=detail;
  this.root!.setPosition(x,y);this.root!.active=true;this.visible=true;
 }
 get visibleTargetId(){return this.visible?this.target:undefined;}
 get captionTargetId(){return this.visible&&!this.compact?this.target:undefined;}
 inspect(){return {id:this.target,visible:this.visible,compact:this.compact,name:this.title?.string??'',detail:this.detail?.string??'',x:this.root?.position.x??0,y:this.root?.position.y??0};}
 destroy(){this.root?.destroy();this.root=null;this.visible=false;}
}
