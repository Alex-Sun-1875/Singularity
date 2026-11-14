import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {Camera,Color,Graphics,Label,Node,Quat,UITransform,Vec3,screen,sys} from 'cc';
import type {ExitDef} from '../../../core/Contracts';
import type {GameSession} from '../../../core/GameSession';
import {AREAS} from '../../world/data/WorldData';
import type {Hud} from '../../../app/Hud';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';
import {LocalCartography as Chart} from '../../navigation/runtime/LocalCartography';
import {SIGIL_FRAME,type PortalMount} from './PortalPlacement';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';

type Sign={exit:ExitDef;node:Node;plate:Graphics;title:Label;detail:Label;mark:Graphics;near:boolean;edge:boolean;locked:boolean;distance:number;skin:string};
const INK=new Color(C.ink.r,C.ink.g,C.ink.b,220),MUTED=new Color(C.muted.r,C.muted.g,C.muted.b,205);

/** Decorative exit captions; the single scene interaction owns actual input. */
export class PortalHud {
 private root:Node|null=null;
 private signs:Sign[]=[];
 private width=0;private height=0;private plateW=168;private plateH=30;private touchH=44;
 private disposed=false;
 constructor(private readonly hud:Hud,private readonly camera:Camera,private readonly world:SceneBuilder){}

 private build():void{
  this.clear();this.width=this.hud.width;this.height=this.hud.height;
  const mobile=sys.isMobile,scale=this.height/Math.max(1,screen.windowSize.height/screen.devicePixelRatio);
  this.plateH=mobile?Math.max(38,22*scale):30;this.plateW=mobile?Math.max(190,118*scale):168;this.touchH=mobile?Math.max(this.plateH,44*scale):this.plateH;
  this.root=this.hud.node('PortalHud',this.hud.root);
  for(const exit of this.world.area.exits){
   const node=this.hud.node('PortalName:'+exit.id,this.root,0,0,this.plateW,this.plateH),plate=node.addComponent(CompactGraphics);
   const title=this.hud.text(node,'',8,0,this.plateW-34,mobile?Math.max(18,Math.ceil(10*scale)):13,INK,this.plateH*.55);title.horizontalAlign=Label.HorizontalAlign.CENTER;title.lineHeight=title.fontSize*1.1;
   const detail=this.hud.text(node,'',8,-this.plateH*.24,this.plateW-34,mobile?Math.max(16,Math.ceil(9*scale)):10,MUTED,this.plateH*.44);detail.horizontalAlign=Label.HorizontalAlign.CENTER;detail.lineHeight=detail.fontSize*1.1;
   const mark=this.hud.node('PortalRuneIcon',node,-this.plateW/2+14,0,18,18).addComponent(CompactGraphics);
   const sign:Sign={exit,node,plate,title,detail,mark,near:false,edge:false,locked:false,distance:0,skin:''};this.signs.push(sign);
  }
 }

 private skin(sign:Sign):void{
  const key=sign.locked+':'+sign.edge+':'+sign.near;if(key===sign.skin)return;sign.skin=key;
  const g=sign.plate;g.clear();g.fillColor=new Color(C.dark.r,C.dark.g,C.dark.b,sign.near?190:135);g.strokeColor=new Color(C.line.r,C.line.g,C.line.b,130);g.lineWidth=1;
  g.roundRect(-this.plateW/2,-this.plateH/2,this.plateW,this.plateH,4);g.fill();if(sign.near)g.stroke();
  sign.node.getComponent(UITransform)!.setContentSize(this.plateW,sign.near?this.touchH:this.plateH);
  const m=sign.mark;m.clear();m.strokeColor=MUTED;m.lineWidth=1;m.circle(0,0,6);m.stroke();m.circle(0,0,3);m.stroke();
 }

 private sigilLabelPoint(mount:PortalMount):Vec3{
  const frame=SIGIL_FRAME,center=new Vec3(mount.position.x,mount.position.y+frame.centerHeight,mount.position.z);
  const rotation=Quat.multiply(new Quat(),Quat.fromEuler(new Quat(),0,frame.yaw,0),Quat.fromEuler(new Quat(),frame.pitch,0,0));
  const projectedCenter=this.camera.worldToScreen(center),pixels=screen.windowSize;
  let top=-Infinity;
  for(const x of [-.5,.5])for(const y of [-.5,.5]){
   const corner=Vec3.transformQuat(new Vec3(),new Vec3(x*frame.size,y*frame.size,0),rotation).add(center);
   top=Math.max(top,this.camera.worldToScreen(corner).y);
  }
  return new Vec3(projectedCenter.x/Math.max(1,pixels.width)*this.width-this.width/2,top/Math.max(1,pixels.height)*this.height-this.height/2+this.plateH/2+12,0);
 }

 update(game:GameSession,hidden=false,interactionId?:string):void{
  if(this.disposed)return;
  if(!this.root?.isValid||this.width!==this.hud.width||this.height!==this.hud.height)this.build();
  this.root!.active=!hidden;if(hidden)return;
  const p=game.state.player,pixels=screen.windowSize,halfW=this.width/2,halfH=this.height/2;
  for(const sign of this.signs){
   const e=sign.exit,distance=Math.hypot(e.x-p.x,e.z-p.z),near=distance<=1.35;
   sign.distance=distance;sign.near=near;sign.locked=!!game.exitRequirement(e);
   // Captions only appear within four metres. Distant exits need neither
   // screen projection (five for sigils) nor text/skin/layout submissions.
   if(distance>4||e.id===interactionId){sign.node.active=false;sign.edge=true;continue;}
   const seen=Chart.revealed(this.world.area.id,e,game);
   const mount=this.world.portalMounts.find(m=>m.id===e.id),standing=mount?.kind==='side-waystone'||mount?.kind==='exit-sigil';
   const top=standing?new Vec3(mount.position.x,mount.position.y+mount.height+.15,mount.position.z).add(Vec3.multiplyScalar(new Vec3(),this.camera.node.up,.3)):new Vec3(e.x,this.world.height(e),e.z).add(Vec3.multiplyScalar(new Vec3(),this.camera.node.up,3));
   const projected=this.camera.worldToScreen(top),label=mount?.kind==='exit-sigil'?this.sigilLabelPoint(mount):new Vec3(projected.x/Math.max(1,pixels.width)*this.width-halfW,projected.y/Math.max(1,pixels.height)*this.height-halfH,0),x=label.x,y=label.y;
   const onScreen=x>-halfW+this.plateW/2+12&&x<halfW-this.plateW/2-12&&y>-halfH+this.plateH/2+125&&y<halfH-this.plateH/2-24;
   const maxY=x<-halfW+350?halfH-235:x>halfW-300?halfH-265:halfH-60;
   // The minimap already gives off-screen bearings. Keep world captions at the
   // entrance itself instead of moving a duplicate card into a HUD corner.
   sign.edge=!onScreen;sign.node.active=e.id!==interactionId&&onScreen&&y<=maxY&&distance<=4&&(seen||this.world.visible(p,e));
   if(onScreen){
    sign.node.setPosition(x,y,0);sign.mark.node.angle=0;
   }
   this.skin(sign);
   const destination=AREAS[e.to]?.name??e.label,name=destination.length>12?destination.slice(0,11)+'…':destination,expanded=sign.locked;
   sign.title.string=name+(expanded?'':` · ${Math.ceil(distance)}m`);sign.title.node.setPosition(8,expanded?this.plateH*.19:0);sign.detail.node.active=expanded;
   sign.detail.string=sign.locked?`Lv${e.requiredLevel??1} · ${Math.ceil(distance)}m`:'';
  }
 }

 inspect(){return{ready:!!this.root?.isValid&&!this.disposed,enabled:!!this.root?.active,entries:this.signs.map(s=>({id:s.exit.id,to:s.exit.to,destination:AREAS[s.exit.to]?.name??s.exit.label,visible:s.node.activeInHierarchy,edge:s.edge,locked:s.locked,near:s.near,distance:s.distance,label:s.detail.string,bounds:{x:s.node.position.x-this.plateW/2,y:s.node.position.y-this.plateH/2,width:this.plateW,height:this.plateH}}))};}
 private clear():void{this.signs=[];if(this.root?.isValid)this.root.destroy();this.root=null;}
 destroy():void{if(this.disposed)return;this.disposed=true;this.clear();}
}
