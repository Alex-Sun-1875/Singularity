import {Label,Node} from 'cc';
import type {RpgPanel} from './RpgPanel';
import {UiSkin} from './UiSkin';
import {PREPARATION_DESIGN as D,preparationSkinAsset} from './PreparationTheme';
import {UI_COLORS as C} from './UiTheme';
import {FeedbackView as F} from './FeedbackView';

/** Original approved design components, with changing text always drawn by Cocos. */
export class PreparationSkin {
 static art(ui:RpgPanel,parent:Node,id:string,x:number,y:number,w:number,h:number,sliced=false){
  const s=UiSkin.asset(parent,preparationSkinAsset(id),w*ui.scale,h*ui.scale,sliced,ui.scale*D.canvas.width/D.canvas.sourceWidth);s.node.setPosition(x,y);return s;
 }
 static rule(ui:RpgPanel,parent:Node,x:number,y:number,w:number){return this.art(ui,parent,'rule',x,y,w,D.decoration.ruleHeight);}
 static separator(ui:RpgPanel,parent:Node,x:number,y:number,h:number){const n=ui.hud.node('PreparationSeparator',parent,x,y,h*ui.scale,ui.scale);UiSkin.rule(n,h*ui.scale,ui.scale);n.setRotationFromEuler(0,0,90);return n;}
 static caption(ui:RpgPanel,parent:Node,prefix:string,value:string,x:number,y:number,w:number,size:number=D.caption.font){
  const units=(s:string)=>Array.from(s).reduce((n,c)=>n+(c.charCodeAt(0)<128?D.caption.asciiWidth:1),0),p=units(prefix),v=units(value),font=Math.min(size,w/Math.max(1,p+v)),left=x-(p+v)*font*ui.scale/2;
  for(const [s,cx,width,color] of [[prefix,left+p*font*ui.scale/2,p*font,C.muted],[value,left+(p+v/2)*font*ui.scale,v*font,F.color(D.colorRoles.selected)]] as const){const label=ui.text(parent,s,cx,y,(width+D.caption.labelInset)*ui.scale,D.caption.height*ui.scale,color,font*ui.scale);label.horizontalAlign=Label.HorizontalAlign.CENTER;label.enableWrapText=false;}
 }
 static badge(ui:RpgPanel,parent:Node,value:string,x:number,y:number,w:number=D.badge.width,tone:'gold'|'teal'='gold',h:number=D.badge.height){
  const host=ui.hud.node('PreparationBadge',parent,x,y,w*ui.scale,h*ui.scale);
  this.art(ui,host,tone==='teal'?'badge-teal':'badge-gold',0,0,w,h,true);
  const text=ui.text(host,value,0,0,(w-D.badge.textInset)*ui.scale,h*ui.scale,tone==='teal'?F.color(D.colorRoles.selected):C.gold,(h<D.badge.compactHeight?D.badge.compactFont:D.badge.font)*ui.scale);text.horizontalAlign=Label.HorizontalAlign.CENTER;text.enableWrapText=false;return host;
 }
 static step(ui:RpgPanel,value:string,x:number,y:number,action:string,enabled:boolean,run:()=>void,w:number=D.step.width){
  const n=ui.button(ui.panel,'',ui.x(x),ui.y(y),Math.max(ui.hit,w*ui.scale),action,enabled,false,ui.hit,run,'catalog');
  const skin=this.art(ui,n,'step',0,0,w,D.step.height,true);if(!enabled)skin.color=F.color(D.colorRoles.disabled,D.step.disabledAlpha);
  const label=ui.text(n,value,0,0,(w-D.step.labelInset)*ui.scale,D.step.labelHeight*ui.scale,enabled?C.gold:F.color(D.colorRoles.disabled),D.step.font*ui.scale);label.horizontalAlign=Label.HorizontalAlign.CENTER;
  return n;
 }
}
