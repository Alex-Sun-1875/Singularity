import {Label,Node} from 'cc';
import type {RpgPanel} from './RpgPanel';
import {PreparationSkin as P} from './PreparationSkin';
import {PREPARATION_DESIGN as D,type PreparationSkinName} from './PreparationTheme';
import {UiSkin} from './UiSkin';
import {UI_COLORS as C} from './UiTheme';
import {FeedbackView as F} from './FeedbackView';

export interface PreparationAction {action:string;enabled?:boolean;run:()=>void}
interface Position {x:number;y:number}
function text(ui:RpgPanel,value:string,x:number,y:number,w:number,h:number,size:number,color=C.ink,align=Label.HorizontalAlign.LEFT){
 const label=ui.text(ui.panel,value,ui.x(x),ui.y(y),w*ui.scale,h*ui.scale,color,size*ui.scale);label.horizontalAlign=align;return label;
}

/** Native Cocos compositions. Pages supply live data and actions; this owns appearance. */
export class PreparationControls {
 static identity(ui:RpgPanel,options:Position&{value:string;width:number;fontSize?:number;height?:number;textWidth?:number;labelHeight?:number;skin?:PreparationSkinName}){
  const {x,y,width,value}=options,h=options.height??D.identity.height;
  const image=P.art(ui,ui.panel,options.skin??'identity',ui.x(x),ui.y(y),width,h);
  const label=text(ui,value,x,y,options.textWidth??width-D.identity.textInset,options.labelHeight??D.identity.labelHeight,options.fontSize??D.typography.identity,C.ink,Label.HorizontalAlign.CENTER);
  return {image,label};
 }
 static tab(ui:RpgPanel,options:Position&PreparationAction&{label:string;width:number;selected:boolean;fontSize?:number}){
  const u=ui.scale,s=D.tab,n=ui.button(ui.panel,'',ui.x(options.x),ui.y(options.y),options.width*u,options.action,options.enabled!==false,false,ui.referenceLayout?s.referenceHitHeight*u:ui.hit,options.run,'catalog');
  P.art(ui,n,options.selected?'side-tab-selected':'side-tab',0,0,options.width,options.selected?s.selectedHeight:s.height,true);
  const label=ui.text(n,options.label,0,0,(options.width-s.textInset)*u,s.labelHeight*u,options.selected?F.color(D.colorRoles.selected):C.ink,(options.fontSize??D.typography.sideTab)*u);label.horizontalAlign=Label.HorizontalAlign.CENTER;return n;
 }
 static cardBackground(ui:RpgPanel,parent:Node,width:number,height:number,selected=false){
  P.art(ui,parent,'card',0,0,width,height,true);if(selected)P.art(ui,parent,'card-selected',0,0,width+D.card.selectedExtraWidth,height+D.card.selectedExtraHeight,true);
 }
 static rowBackground(ui:RpgPanel,parent:Node,width:number,height:number,selected=false){
  P.art(ui,parent,'skill-row',0,0,width,height,true);if(selected)P.art(ui,parent,'skill-selected',0,0,width+D.row.selectedExtraWidth,height+D.row.selectedExtraHeight,true);
 }
 static icon(ui:RpgPanel,parent:Node,path:string|undefined,x:number,y:number,size:number,name?:string){
  if(!path)return;const image=UiSkin.sprite(parent,path,size*ui.scale,size*ui.scale);if(name)image.node.name=name;image.node.setPosition(x,y);return image;
 }
 static professionCard(ui:RpgPanel,options:Position&PreparationAction&{width:number;height:number;selected:boolean;image:string;title:string;description:string;badge?:{label:string;tone:'gold'|'teal'}}){
  const u=ui.scale,s=D.professionCard,w=options.width,h=options.height,n=ui.button(ui.panel,'',ui.x(options.x),ui.y(options.y),w*u,options.action,options.enabled!==false,false,h*u,options.run,'catalog');
  this.cardBackground(ui,n,w,h,options.selected);
  const painting=UiSkin.asset(n,options.image,(w-s.artInset)*u,h*s.artHeight*u,false);painting.node.setPosition(0,h*s.artY*u);
  const title=ui.text(n,options.title,0,h*s.titleY*u,(w-s.titleInset)*u,s.titleHeight*u,options.selected?F.color(D.colorRoles.selected):C.ink,s.titleFont*u);title.horizontalAlign=Label.HorizontalAlign.CENTER;
  P.rule(ui,n,0,h*s.ruleY*u,w-s.ruleInset);
  const detail=ui.text(n,options.description,0,h*s.descriptionY*u,(w-s.descriptionInset)*u,s.descriptionHeight*u,C.ink,s.descriptionFont*u);detail.horizontalAlign=Label.HorizontalAlign.CENTER;
  if(options.badge)P.badge(ui,n,options.badge.label,(w/2-s.badgeRight)*u,(h/2-s.badgeTop)*u,s.badgeWidth,options.badge.tone);return n;
 }
 static attributeRow(ui:RpgPanel,options:{y:number;height:number;label:string;icon:string;before:number;after:number;decrease:PreparationAction;increase:PreparationAction;centerX?:number}){
  const u=ui.scale,s=D.attributeRow,cx=options.centerX??s.centerX,y=options.y,before=options.before,after=options.after,x=(offset:number)=>cx+offset;
  const image=P.art(ui,ui.panel,'attribute-row',ui.x(cx),ui.y(y),s.width,options.height,true);
  P.art(ui,ui.panel,options.icon,ui.x(x(s.iconX)),ui.y(y),s.iconWidth,s.iconHeight);
  text(ui,options.label,x(s.nameX),y,s.nameWidth,s.nameHeight,D.typography.attributeName,C.ink,Label.HorizontalAlign.CENTER);
  P.separator(ui,ui.panel,ui.x(x(s.separatorX)),ui.y(y),s.separatorHeight);
  text(ui,String(before),x(s.beforeX),y,s.beforeWidth,s.nameHeight,D.typography.number,C.ink,Label.HorizontalAlign.RIGHT);
  text(ui,'→',x(s.arrowX),y,s.arrowWidth,s.nameHeight,s.arrowFont,C.ink,Label.HorizontalAlign.CENTER);
  text(ui,String(after),x(s.afterX),y,s.afterWidth,s.nameHeight,D.typography.number,before!==after?F.color(D.colorRoles.selected):C.ink,Label.HorizontalAlign.CENTER);
  if(after!==before)text(ui,`(${after>before?'+':''}${after-before})`,x(s.deltaX),y,s.deltaWidth,s.nameHeight,D.typography.delta,C.gold,Label.HorizontalAlign.CENTER);
  [options.decrease,options.increase].forEach((action,i)=>P.step(ui,i?'+' :'−',ui.referenceLayout?x(s.referenceButtonX)+i*s.referenceButtonStep:x(s.compactButtonX)+i*(Math.max(D.step.width,ui.hit/u)+ui.gap/u),y,action.action,action.enabled!==false,action.run,ui.referenceLayout?s.referenceButtonWidth:D.step.width));
  return image;
 }
 static skillRow(ui:RpgPanel,parent:Node,options:Position&PreparationAction&{height:number;title:string;level:string;selected:boolean;changed:boolean;iconPath?:string;iconName?:string}){
  const u=ui.scale,s=D.skillRow,n=ui.button(parent,'',options.x*u,options.y*u,s.width*u,options.action,options.enabled!==false,false,options.height*u,options.run,'catalog');
  this.rowBackground(ui,n,s.width,s.height,options.selected);
  this.icon(ui,n,options.iconPath,s.iconX*u,0,s.iconSize,options.iconName);
  const title=ui.text(n,options.title,s.nameX*u,0,s.nameWidth*u,s.labelHeight*u,C.ink,D.typography.rowTitle*u);title.enableWrapText=false;
  const level=ui.text(n,options.level,s.levelX*u,0,s.levelWidth*u,s.labelHeight*u,options.changed?F.color(D.colorRoles.selected):C.ink,s.levelFont*u);level.horizontalAlign=Label.HorizontalAlign.RIGHT;level.enableWrapText=false;level.overflow=Label.Overflow.SHRINK;return n;
 }
 static pointCounter(ui:RpgPanel,options:Position&PreparationAction&{width:number;height:number;variant:'attribute'|'skill';title:string;subtitle:string}){
  const u=ui.scale,s=D.counter,skill=options.variant==='skill',w=options.width,n=ui.button(ui.panel,'',ui.x(options.x),ui.y(options.y),(skill?s.skillWidth:w+s.extraWidth)*u,options.action,options.enabled!==false,false,options.height*u,options.run,'catalog');
  if(!skill)P.art(ui,n,'point-counter',0,0,w,options.height-s.backgroundInset,true);
  const title=ui.text(n,options.title,0,s.titleY*u,(skill?s.skillTitleWidth:w-s.titleInset)*u,s.labelHeight*u,C.ink,(skill?s.skillTitleFont:s.attributeTitleFont)*u);title.horizontalAlign=Label.HorizontalAlign.CENTER;
  const cost=ui.text(n,options.subtitle,0,s.costY*u,(w-s.costInset)*u,s.labelHeight*u,C.ink,(skill?s.skillCostFont:s.attributeCostFont)*u);cost.horizontalAlign=Label.HorizontalAlign.CENTER;return n;
 }
}
