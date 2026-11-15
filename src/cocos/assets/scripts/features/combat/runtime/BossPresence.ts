import {viewportMetrics} from '../../../platform/ViewportMetrics';
import {journeyText} from '../../journey/locales';
import {Camera,Label,Node,Vec2,Vec3} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import type {Hud} from '../../../app/Hud';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';
import {bossKind,bossName,nearestBoss} from '../common/BossAwareness';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {fitRpgLine} from '../../../shared/ui/RpgFont';
import {BossHealthStrip,bossHudScale,BOSS_HEAD_HEIGHT,BOSS_HEAD_GAP} from './BossHud';

/** Three centered rows: name, health bar, then numeric HP / level nearest the head. */
export class BossPresence {
 private root:Node|null=null;private title:Label|null=null;private detail:Label|null=null;private health:BossHealthStrip|null=null;
 private width=0;private height=0;private unit=1;private target='';private visible=false;
 private anchor=new Vec3();private projected=new Vec3();private bodyProjected=new Vec3();private sample=new Vec2();
 constructor(private hud:Hud,private camera:Camera,private world:SceneBuilder,private headPoint:(id:string)=>Vec3|undefined){}
 private build(){
  this.root?.destroy();this.width=this.hud.width;this.height=this.hud.height;this.unit=bossHudScale(this.hud);const u=this.unit;
  this.root=this.hud.node('BossPresence',this.hud.root,0,0,184*u,BOSS_HEAD_HEIGHT*u);
  this.health=new BossHealthStrip(this.hud,this.root,184*u,u);
  this.title=this.hud.text(this.root,'',0,12*u,this.health.barWidth,10*u,F.color('identity.boss'),14*u);this.title.node.name='BossPresenceName';this.title.horizontalAlign=Label.HorizontalAlign.CENTER;
  this.detail=this.hud.text(this.root,'',0,-12*u,184*u,9.5*u,F.color('text.normal'),14*u);this.detail.node.name='BossPresenceDistance';this.detail.horizontalAlign=Label.HorizontalAlign.CENTER;
  for(const label of [this.title,this.detail]){label.enableWrapText=false;label.isBold=true;label.overflow=Label.Overflow.CLAMP;label.lineHeight=label.fontSize*1.2;label.enableOutline=true;label.outlineWidth=u;label.outlineColor=F.color('text.outline');}
  // Keep both bottom-row fields visible even with unusually large HP.
  this.detail.overflow=Label.Overflow.SHRINK;
 }
 private hide(){this.visible=false;if(this.root?.active)this.root.active=false;}
 update(game:GameSession,hidden=false,objectiveId?:string){
  if(!this.root?.isValid||this.width!==this.hud.width||this.height!==this.hud.height)this.build();
  if(hidden){this.hide();return;}
  const enemy=nearestBoss(game);this.target=enemy?.id??'';if(!enemy){this.hide();return;}
  const p=game.state.player;if(!this.world.visible(p,enemy)||Math.abs(this.world.height(p)-this.world.height(enemy))>6){this.hide();return;}
  const head=this.headPoint(enemy.id);this.anchor.set(head?.x??enemy.x,head?.y??this.world.height(enemy)+3,head?.z??enemy.z);
  this.camera.worldToScreen(this.anchor,this.projected);if(this.projected.z<0||this.projected.z>1){this.hide();return;}
  // Use the body axis for horizontal alignment; head height still comes from
  // the authored sprite/model, so animation and level text cannot shift the bar.
  this.anchor.set(enemy.x,this.world.height(enemy),enemy.z);this.camera.worldToScreen(this.anchor,this.bodyProjected);
  const u=this.unit,pixels=viewportMetrics.windowSize,x=this.bodyProjected.x/Math.max(1,pixels.width)*this.width-this.width/2,y=this.projected.y/Math.max(1,pixels.height)*this.height-this.height/2+(BOSS_HEAD_GAP+BOSS_HEAD_HEIGHT/2)*u;
  const halfW=92*u,halfH=BOSS_HEAD_HEIGHT/2*u;if(!Number.isFinite(x+y)||Math.abs(x)+halfW>this.width/2-16||Math.abs(y)+halfH>this.height/2-16){this.hide();return;}
  // Never shift a world nameplate onto the player or an existing control.
  // The ordinary enemy HP bar remains available when this larger marker culls.
  for(const [dx,dy]of [[0,0],[-halfW,-halfH],[halfW,-halfH],[-halfW,halfH],[halfW,halfH]]){
   this.sample.set((x+dx+this.width/2)/this.width*pixels.width,(y+dy+this.height/2)/this.height*pixels.height);if(this.hud.isOverUI(this.sample)){this.hide();return;}
  }
  const kind=bossKind(enemy),role=kind==='elite'?'identity.elite':'identity.boss';F.tint(this.title!,role);
  const objective=enemy.id===objectiveId;
  this.health!.update(enemy);
  const name=fitRpgLine(`${objective?journeyText('marker.boss'):kind==='elite'?'精英':'首领'} · ${bossName(enemy)}`,this.health!.barWidth,this.title!.fontSize),detail=this.health!.readout;
  if(this.title!.string!==name)this.title!.string=name;if(this.detail!.string!==detail)this.detail!.string=detail;
  this.root!.setPosition(x,y);this.root!.active=true;this.visible=true;
 }
 inspect(){return {id:this.target,visible:this.visible,name:this.title?.string??'',distance:this.detail?.string??'',health:this.health?.inspect(),x:this.root?.position.x??0,y:this.root?.position.y??0};}
 get visibleTargetId(){return this.visible?this.target:undefined;}
 destroy(){this.root?.destroy();this.root=null;this.health=null;this.visible=false;}
}
