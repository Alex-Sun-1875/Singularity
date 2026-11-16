import {_decorator,ButtonComponent as Button,Camera,Component,Graphics,Node,UITransform,Vec3,sys} from 'cc';
import {isTapMinigame} from '../../platform/RuntimePlatform';
import {retainViewportMetrics,viewportMetrics} from '../../platform/ViewportMetrics';
import {bindButtonFeedback,type ButtonFeedbackState} from './ButtonFeedback';
import {CompactGraphics} from './CompactGraphics';
import {FeedbackView as F} from './FeedbackView';
import {UI_PANEL_HEADER as H} from './UiChrome';
import {UI_COLORS as C} from './UiTheme';

const {ccclass}=_decorator;
type Bounds={left:number;right:number;bottom:number;top:number};
interface HeaderViewport {root:Node;camera:Camera;width:number;height:number}
export interface GoldPanelHeaderOptions {
 width:number;unit:number;hit?:number;centerX?:number;centerY:number;inset?:number;
 viewport:HeaderViewport;action:string;disabled?:boolean;
 dismissSide?:'auto'|'left';
}

/** One dismiss target. Pages retain routing and may request left return; otherwise host geometry chooses. */
@ccclass('GoldPanelHeader')
export class GoldPanelHeader extends Component {
 button!:Node;
 mode:'back'|'close'='close';
 capsuleSource:'native'|'reserved'|'none'='none';
 private options!:GoldPanelHeaderOptions;
 private native!:Button;
 private ink!:Graphics;
 private activate:()=>void=()=>{};
 private releaseMetrics?:()=>void;
 private revision=-1;
 private state:ButtonFeedbackState='idle';
 private matrix:number[]=[];

 static attach(parent:Node,options:GoldPanelHeaderOptions,activate:()=>void):GoldPanelHeader {
  const node=new Node('GoldPanelHeader');node.layer=parent.layer;parent.addChild(node);
  node.addComponent(UITransform);const header=node.addComponent(GoldPanelHeader);
  header.configure(options,activate);return header;
 }
 private configure(options:GoldPanelHeaderOptions,activate:()=>void):void {
  this.options=options;this.activate=activate;
  this.node.setPosition(options.centerX??0,options.centerY);
  const hit=Math.max(options.hit??0,H.hit*options.unit);
  this.node.getComponent(UITransform)!.setContentSize(options.width,hit);
  this.button=new Node(options.action);this.button.layer=this.node.layer;this.node.addChild(this.button);
  this.button.addComponent(UITransform).setContentSize(hit,hit);
  this.native=this.button.addComponent(Button);this.native.transition=Button.Transition.NONE;this.native.interactable=!options.disabled;
  const face=new Node('HeaderDismissGlyph');face.layer=this.node.layer;this.button.addChild(face);
  face.addComponent(UITransform).setContentSize(H.feedback*options.unit,H.feedback*options.unit);this.ink=face.addComponent(CompactGraphics);
  bindButtonFeedback(this.button,this.native,state=>{this.state=state;this.paint();});
  this.button.on(Button.EventType.CLICK,()=>{if(this.native.interactable)this.activate();});
  this.refresh();
 }
 setAction(action:string,activate:()=>void,enabled=true):void {
  this.button.name=action;this.activate=activate;this.native.interactable=enabled;this.state='idle';this.paint();
 }
 onEnable():void {this.releaseMetrics=retainViewportMetrics();this.revision=-1;}
 onDisable():void {this.releaseMetrics?.();this.releaseMetrics=undefined;this.state='idle';if(this.ink)this.paint();}
 onDestroy():void {this.releaseMetrics?.();this.releaseMetrics=undefined;}
 lateUpdate():void {
  if(!this.options)return;
  // Host getters remain cached. Observe transforms as FairyGUI and Canvas finish layout.
  const m=this.node.worldMatrix,values=[m.m00,m.m01,m.m04,m.m05,m.m12,m.m13];
  if(this.revision!==viewportMetrics.revision||values.some((v,i)=>v!==this.matrix[i])){this.matrix=values;this.refresh();}
 }
 private bounds(x:number):Bounds {
  const {camera}=this.options.viewport,transform=this.node.getComponent(UITransform)!,hit=this.button.getComponent(UITransform)!.width;
  const points=[[-1,-1],[1,-1],[-1,1],[1,1]].map(([sx,sy])=>camera.worldToScreen(transform.convertToWorldSpaceAR(new Vec3(x+sx*hit/2,sy*hit/2))));
  return {left:Math.min(...points.map(p=>p.x)),right:Math.max(...points.map(p=>p.x)),bottom:Math.min(...points.map(p=>p.y)),top:Math.max(...points.map(p=>p.y))};
 }
 private safeBounds():Bounds {
  const {root,camera,width,height}=this.options.viewport,s=sys.getSafeAreaRect(false),t=root.getComponent(UITransform)!;
  const a=camera.worldToScreen(t.convertToWorldSpaceAR(new Vec3(s.x-width/2,s.y-height/2))),b=camera.worldToScreen(t.convertToWorldSpaceAR(new Vec3(s.x+s.width-width/2,s.y+s.height-height/2)));
  return {left:a.x,right:b.x,bottom:a.y,top:b.y};
 }
 private capsule():Bounds|null {
  const rect=viewportMetrics.menuRect,size=viewportMetrics.windowSize;
  if(rect){this.capsuleSource='native';return {left:rect.left/rect.windowWidth*size.width,right:rect.right/rect.windowWidth*size.width,bottom:size.height-rect.bottom/rect.windowHeight*size.height,top:size.height-rect.top/rect.windowHeight*size.height};}
  if(!isTapMinigame){this.capsuleSource='none';return null;}
  // Older TapTap hosts: reserve the existing conservative header corner, never invent a measured rectangle.
  this.capsuleSource='reserved';const density=viewportMetrics.devicePixelRatio;
  return {left:size.width-H.fallbackCapsuleWidth*density,right:size.width,bottom:size.height-H.fallbackCapsuleHeight*density,top:size.height};
 }
 refresh():void {
  if(!this.options||!this.native)return;
  const o=this.options,hit=this.button.getComponent(UITransform)!.width,inset=o.inset??H.inset*o.unit,x=o.width/2-inset-hit/2;
  const right=this.bounds(x),safe=this.safeBounds(),capsule=this.capsule(),gap=H.gap*viewportMetrics.devicePixelRatio;
  const inside=(b:Bounds)=>b.left>=safe.left-.5&&b.right<=safe.right+.5&&b.bottom>=safe.bottom-.5&&b.top<=safe.top+.5;
  const overlaps=(b:Bounds)=>!!capsule&&b.left<capsule.right+gap&&b.right>capsule.left-gap&&b.bottom<capsule.top+gap&&b.top>capsule.bottom-gap;
  this.mode=o.dismissSide==='left'?'back':inside(right)&&!overlaps(right)?'close':'back';
  let targetX=this.mode==='close'?x:-x;
  // Keep the whole chosen target inside a changed hardware safe area.
  const chosen=this.bounds(targetX),scale=(chosen.right-chosen.left)/hit;
  if(scale>0){targetX+=Math.max(0,safe.left-chosen.left)/scale-Math.max(0,chosen.right-safe.right)/scale;}
  const scaleY=(chosen.top-chosen.bottom)/hit,targetY=scaleY>0?(Math.max(0,safe.bottom-chosen.bottom)-Math.max(0,chosen.top-safe.top))/scaleY:0;
  this.button.setPosition(targetX,targetY);this.revision=viewportMetrics.revision;this.paint();
 }
 private paint():void {
  if(!this.ink||!this.options)return;
  const g=this.ink,u=this.options.unit,disabled=!this.native.interactable;g.clear();
  if(!disabled&&this.state!=='idle'){const size=H.feedback*u;g.fillColor=this.state==='pressed'?C.button:C.hover;g.roundRect(-size/2,-size/2,size,size,5*u);g.fill();}
  g.strokeColor=disabled?F.color('text.disabled',125):this.state==='idle'?C.gold:C.goldLight;g.lineWidth=H.stroke*u;
  g.lineCap=Graphics.LineCap.ROUND;g.lineJoin=Graphics.LineJoin.ROUND;
  const k=H.glyph*u/24,point=(x:number,y:number)=>({x:(x-12)*k,y:(12-y)*k});
  const paths=this.mode==='back'?[[[14,5],[7,12],[14,19]],[[7,12],[20,12]]]:[[[6,6],[18,18]],[[18,6],[6,18]]];
  for(const path of paths){path.forEach(([x,y],i)=>{const p=point(x,y);if(i)g.lineTo(p.x,p.y);else g.moveTo(p.x,p.y);});g.stroke();}
 }
}
