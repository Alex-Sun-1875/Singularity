import {CompactMask as Mask} from '../../../shared/ui/CompactMask';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {Color,Graphics,Node,UITransform} from 'cc';
import {qualityFeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {PREPARATION_DESIGN as D,preparationSkinAsset} from '../../../shared/ui/PreparationTheme';

export type FrameOptions={quality?:string;selected?:boolean;scale?:number;emptyStar?:boolean;appearance?:'quality'|'preparation'};
function node(parent:Node,name:string,w:number,h:number){const n=new Node(name);n.layer=parent.layer;parent.addChild(n);n.addComponent(UITransform).setContentSize(w,h);return n;}

/** One rounded silhouette for gear in inventory, worn sockets, forge and dice rewards. */
export function equipmentIconFrame(parent:Node,w:number,h:number,options:FrameOptions={}){
 const unit=options.scale??1,r=Math.min(w,h)*.12,host=node(parent,'EquipmentIconFrame:'+(options.quality??'empty'),w,h);
 const background=node(host,'RoundedBackground',w,h).addComponent(CompactGraphics);background.fillColor=C.dark;background.roundRect(-w/2,-h/2,w,h,r);background.fill();
 const content=node(host,'RoundedIconClip',w-1.8*unit,h-1.8*unit),mask=content.addComponent(Mask);mask.type=Mask.Type.GRAPHICS_STENCIL;
 const stencil=mask.subComp as Graphics;stencil.clear();stencil.roundRect(-w/2+.9*unit,-h/2+.9*unit,w-1.8*unit,h-1.8*unit,Math.max(.1,r-.9*unit));stencil.fill();
 if(options.emptyStar){
  const star=node(content,'EmptySlotMotif',w,h).addComponent(CompactGraphics);star.fillColor=new Color(C.line.r,C.line.g,C.line.b,38);
  for(let i=0;i<16;i++){const angle=Math.PI*i/8,radius=Math.min(w,h)*(i%2?.042:.17),x=Math.cos(angle)*radius,y=Math.sin(angle)*radius;if(i)star.lineTo(x,y);else star.moveTo(x,y);}star.close();star.fill();
 }
 if(options.appearance==='preparation')UiSkin.asset(host,preparationSkinAsset(options.selected?'socket-selected':'socket'),w,h,true,unit*D.canvas.width/D.canvas.sourceWidth);
 const frame=node(host,'RoundedEquipmentBorder',w,h).addComponent(CompactGraphics),role=options.quality?qualityFeedbackRole(options.quality):'text.disabled';
 frame.strokeColor=C.dark;frame.lineWidth=2.3*unit;frame.roundRect(-w/2+.7*unit,-h/2+.7*unit,w-1.4*unit,h-1.4*unit,r);frame.stroke();
 frame.strokeColor=F.color(role,options.quality?255:145);frame.lineWidth=(options.selected?1.8:1.2)*unit;frame.roundRect(-w/2+.85*unit,-h/2+.85*unit,w-1.7*unit,h-1.7*unit,r);frame.stroke();
 frame.strokeColor=F.color(role,options.quality?160:65);frame.lineWidth=.45*unit;frame.roundRect(-w/2+2.25*unit,-h/2+2.25*unit,w-4.5*unit,h-4.5*unit,Math.max(.1,r-1.4*unit));frame.stroke();
 // Selection never replaces the item's quality color. Ornament stays above icon art.
 if(options.selected){frame.strokeColor=C.gold;frame.lineWidth=.65*unit;frame.roundRect(-w/2+3.5*unit,-h/2+3.5*unit,w-7*unit,h-7*unit,Math.max(.1,r-2.5*unit));frame.stroke();}
 const artifact=options.quality==='神器';
 if(artifact)for(const [index,[sx,sy]]of [[1,-1],[-1,-1],[-1,1],[1,1]].entries()){
  const ornament=node(host,'ArtifactCorner:'+index,w,h);ornament.setPosition(-sx*(w/2-3.6*unit),-sy*(h/2-3.6*unit));
  const g=ornament.addComponent(CompactGraphics),s=Math.min(w,h)*.19,m=(x:number,y:number)=>g.moveTo(sx*x,sy*y),b=(a:number,c:number,d:number,e:number,f:number,j:number)=>g.bezierCurveTo(sx*a,sy*c,sx*d,sy*e,sx*f,sy*j);
  g.strokeColor=C.gold;g.fillColor=C.gold;g.lineWidth=Math.max(.65*unit,s*.075);
  m(0,s*.93);b(0,s*.25,s*.25,0,s*.93,0);g.stroke();
  m(s*.04,s*.6);b(s*.4,s*.67,s*.72,s*.4,s*.48,s*.26);b(s*.22,s*.12,s*.17,s*.43,s*.35,s*.47);g.stroke();
  if(artifact){m(s*.05,s*.5);b(s*.28,s*.53,s*.32,s*.78,s*.18,s*.9);b(s*.01,s*.85,-s*.01,s*.62,s*.05,s*.5);g.fill();
  m(s*.5,s*.05);b(s*.53,s*.28,s*.78,s*.32,s*.9,s*.18);b(s*.85,s*.01,s*.62,-s*.01,s*.5,s*.05);g.fill();}
  const c=s*.72,d=s*.1;m(c,c-d);g.lineTo(sx*(c+d),sy*c);g.lineTo(sx*c,sy*(c+d));g.lineTo(sx*(c-d),sy*c);g.close();g.fill();
 }
 if(artifact){
  const g=node(host,'ArtifactRunicRim',w,h).addComponent(CompactGraphics),s=Math.min(w,h),y=h/2-3.2*unit;
  g.strokeColor=C.gold;g.fillColor=C.gold;g.lineWidth=Math.max(.6*unit,s*.009);
  for(const side of [-1,1]){g.moveTo(side*s*.12,y);g.bezierCurveTo(side*s*.20,y-2*unit,side*s*.24,y+unit,side*s*.31,y);g.stroke();
   for(let i=0;i<3;i++){const x=side*(s*.17+i*s*.05);g.moveTo(x,y-1.5*unit);g.lineTo(x+side*1.4*unit,y-3.2*unit);g.lineTo(x+side*2.6*unit,y-1.5*unit);g.stroke();}}
  const c=s*.075;g.moveTo(-c,y);g.lineTo(-c,y-c*.65);g.lineTo(c,y-c*.65);g.lineTo(c,y);g.lineTo(c*.35,y-c*.3);g.lineTo(0,y+c*.25);g.lineTo(-c*.35,y-c*.3);g.close();g.fill();
 }
 if(options.appearance==='preparation'&&!options.quality)frame.node.active=false;
 return {host,content};
}
