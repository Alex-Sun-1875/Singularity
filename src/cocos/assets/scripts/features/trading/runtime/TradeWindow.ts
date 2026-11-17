import {BlockInputEvents,ButtonComponent as Button,Color,Label,Node,ScrollView,UITransform,sys} from 'cc';
import type {Hud} from '../../../app/Hud';
import {viewportMetrics} from '../../../platform/ViewportMetrics';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {GoldPanelHeader} from '../../../shared/ui/GoldPanelHeader';
import {RpgPanel} from '../../../shared/ui/RpgPanel';
import {applyRpgFont} from '../../../shared/ui/RpgFont';
import {ButtonSurface} from '../../../shared/ui/ButtonSurface';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {PREPARATION_DESIGN as D,preparationSkinAsset} from '../../../shared/ui/PreparationTheme';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';

/** A dedicated trade window. Shared artwork/input primitives do not own its layout. */
export class TradeWindow {
 readonly panel:Node;readonly scale:number;readonly width:number;readonly height:number;
 readonly hit=D.interaction.hitLogical;readonly gap=D.interaction.gapLogical;
 constructor(readonly hud:Hud){
  hud.clearModal();this.scale=hud.height/Math.max(1,viewportMetrics.windowSize.height/viewportMetrics.devicePixelRatio);
  const u=this.scale,safe=sys.getSafeAreaRect(false);
  this.width=Math.min(sys.isMobile?740:880,safe.width/u-24);this.height=Math.min(sys.isMobile?354:470,safe.height/u-16);
  const shade=hud.node('TradeBackdrop',hud.modal,0,0,hud.width,hud.height);shade.addComponent(BlockInputEvents);
  const ink=shade.addComponent(CompactGraphics);ink.fillColor=new Color(C.background.r,C.background.g,C.background.b,110);ink.rect(-hud.width/2,-hud.height/2,hud.width,hud.height);ink.fill();
  const dismiss=shade.addComponent(Button);dismiss.transition=Button.Transition.NONE;shade.on(Button.EventType.CLICK,()=>hud.actions.click('close'));
  this.panel=hud.node('MerchantInventoryPanel',hud.modal,-hud.width/2+safe.x+safe.width/2,-hud.height/2+safe.y+safe.height/2,this.width*u,this.height*u);this.panel.addComponent(BlockInputEvents);
  UiSkin.panel(this.panel,this.width*u,this.height*u,C.background,'panel',false,D.frame.pixelScaleLogical*u,D.frame.asset);
  GoldPanelHeader.attach(this.panel,{width:this.width*u,unit:u,hit:this.hit*u,centerY:this.y(32),viewport:hud,action:'close'},()=>hud.actions.click('close'));
  this.rule(64);this.rule(this.height-56);
 }
 x(value:number){return (-this.width/2+value)*this.scale;}
 y(value:number){return (this.height/2-value)*this.scale;}
 text(parent:Node,value:string,x:number,y:number,w:number,h=24,size:number=D.typography.body,color=C.ink){
  const u=this.scale,label=this.hud.text(parent,value,x*u,y*u,w*u,Math.max(D.typography.minimumLogical,size)*u,color,h*u);
  applyRpgFont(label);label.lineHeight=label.fontSize*D.typography.lineHeight;label.enableWrapText=true;label.overflow=Label.Overflow.CLAMP;return label;
 }
 label(value:string,x:number,y:number,w:number,h=24,size:number=D.typography.body,color=C.ink){return this.text(this.panel,value,x-this.width/2,this.height/2-y,w,h,size,color);}
 button(parent:Node,label:string,x:number,y:number,w:number,action:string,enabled=true,selected=false,primary=false){
  const u=this.scale,n=this.hud.node(action,parent,x*u,y*u,w*u,this.hit*u),button=n.addComponent(Button);button.transition=Button.Transition.NONE;button.interactable=enabled;
  let face:Node;
  if(primary){const image=UiSkin.asset(n,preparationSkinAsset(enabled?'button-gold':'button-dark'),w*u,32*u,true);face=image.node;}
  else {face=this.hud.node('QuantityFace',n,0,0,w*u,30*u);const g=face.addComponent(CompactGraphics);g.fillColor=selected?F.color('selection.surface'):C.inset;g.strokeColor=selected?F.color('selection.edge'):F.color('text.secondary',65);g.lineWidth=.8*u;g.roundRect(-w*u/2,-15*u,w*u,30*u,2*u);g.fill();g.stroke();}
  ButtonSurface.attach(n,{width:(w-4)*u,height:28*u,radius:2*u,overlay:true,after:face});
  const text=this.text(n,label,0,0,w-8,28,primary?15:14,enabled?primary?C.dark:selected?F.color('selection.highlight'):C.ink:F.color('text.disabled'));text.horizontalAlign=Label.HorizontalAlign.CENTER;text.enableWrapText=false;
  n.on(Button.EventType.CLICK,()=>{if(enabled)this.hud.actions.click(action);});return n;
 }
 action(label:string,x:number,y:number,w:number,action:string,enabled=true,selected=false,primary=false){return this.button(this.panel,label,x-this.width/2,this.height/2-y,w,action,enabled,selected,primary);}
 tab(label:string,x:number,y:number,w:number,action:string,selected=false){
  const u=this.scale,n=this.hud.node(action,this.panel,this.x(x),this.y(y),w*u,this.hit*u),b=n.addComponent(Button);b.transition=Button.Transition.NONE;
  ButtonSurface.attach(n,{width:(w-8)*u,height:28*u,radius:2*u,overlay:true});
  const text=this.text(n,label,0,1,w-8,26,14,selected?C.gold:C.muted);text.horizontalAlign=Label.HorizontalAlign.CENTER;text.enableWrapText=false;
  if(selected)UiSkin.asset(n,preparationSkinAsset('active'),Math.min(46,w-12)*u,5*u,false).node.setPosition(0,-16*u);
  n.on(Button.EventType.CLICK,()=>this.hud.actions.click(action));return n;
 }
 link(label:string,x:number,y:number,w:number,action:string){const n=this.tab(label,x,y,w,action);n.getComponentInChildren(Label)!.color=C.gold;return n;}
 divider(x:number,top:number,height:number){const line=UiSkin.asset(this.panel,preparationSkinAsset('rule'),height*this.scale,5*this.scale,false);line.node.setPosition(this.x(x),this.y(top+height/2));line.node.setRotationFromEuler(0,0,90);}
 scroll(x:number,top:number,w:number,h:number,contentHeight:number,name:string){
  const u=this.scale,content=RpgPanel.scroll(this.hud,this.panel,this.x(x+w/2),this.y(top+h/2),w*u,h*u,contentHeight*u,u);content.name=name;
  return {content,view:content.parent!.parent!.getComponent(ScrollView)!};
 }
 private rule(top:number){UiSkin.asset(this.panel,preparationSkinAsset('rule'),(this.width-32)*this.scale,7*this.scale,false).node.setPosition(0,this.y(top));}
}
