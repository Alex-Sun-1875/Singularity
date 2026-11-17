import {CompactMask as Mask} from '../../../shared/ui/CompactMask';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {Color,Graphics,Node,UITransform} from 'cc';
import {qualityFeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {UiChrome} from '../../../shared/ui/UiChrome';
import {PREPARATION_DESIGN as D,preparationSkinAsset} from '../../../shared/ui/PreparationTheme';
import {ButtonSurface} from '../../../shared/ui/ButtonSurface';

export type FrameOptions={quality?:string;selected?:boolean;scale?:number;emptyStar?:boolean;appearance?:'quality'|'preparation';ornamentScale?:number};
function node(parent:Node,name:string,w:number,h:number){const n=new Node(name);n.layer=parent.layer;parent.addChild(n);n.addComponent(UITransform).setContentSize(w,h);return n;}

/** One rounded silhouette for gear in inventory, worn sockets, forge and dice rewards. */
export function equipmentIconFrame(parent:Node,w:number,h:number,options:FrameOptions={}){
 const unit=options.scale??1,r=Math.min(w,h)*.12,host=node(parent,'EquipmentIconFrame:'+(options.quality??'empty'),w,h);
 const background=node(host,'RoundedBackground',w,h).addComponent(CompactGraphics);background.fillColor=C.dark;background.roundRect(-w/2,-h/2,w,h,r);background.fill();
 const content=node(host,'RoundedIconClip',w-1.8*unit,h-1.8*unit),mask=content.addComponent(Mask);mask.type=Mask.Type.GRAPHICS_STENCIL;
 const stencil=mask.subComp as Graphics;stencil.clear();stencil.roundRect(-w/2+.9*unit,-h/2+.9*unit,w-1.8*unit,h-1.8*unit,Math.max(.1,r-.9*unit));stencil.fill();
 if(options.selected){const inlay=UiSkin.asset(content,preparationSkinAsset('selection-inlay'),w,h,false);inlay.node.name='EquipmentSelectionInlay';}
 if(options.emptyStar){
  const star=node(content,'EmptySlotMotif',w,h).addComponent(CompactGraphics);star.fillColor=new Color(C.line.r,C.line.g,C.line.b,38);
  for(let i=0;i<16;i++){const angle=Math.PI*i/8,radius=Math.min(w,h)*(i%2?.042:.17),x=Math.cos(angle)*radius,y=Math.sin(angle)*radius;if(i)star.lineTo(x,y);else star.moveTo(x,y);}star.close();star.fill();
 }
 if(options.appearance==='preparation')UiSkin.asset(host,preparationSkinAsset('socket'),w,h,true,unit*D.canvas.width/D.canvas.sourceWidth);
 const frame=node(host,'RoundedEquipmentBorder',w,h).addComponent(CompactGraphics),role=options.quality?qualityFeedbackRole(options.quality):'text.disabled';
 frame.strokeColor=C.dark;frame.lineWidth=2.3*unit;frame.roundRect(-w/2+.7*unit,-h/2+.7*unit,w-1.4*unit,h-1.4*unit,r);frame.stroke();
 frame.strokeColor=F.color(role,options.quality?255:145);frame.lineWidth=1.2*unit;frame.roundRect(-w/2+.85*unit,-h/2+.85*unit,w-1.7*unit,h-1.7*unit,r);frame.stroke();
 frame.strokeColor=F.color(role,options.quality?160:65);frame.lineWidth=.45*unit;frame.roundRect(-w/2+2.25*unit,-h/2+2.25*unit,w-4.5*unit,h-4.5*unit,Math.max(.1,r-1.4*unit));frame.stroke();
 // Selection never replaces the item's quality color. Ornament stays above icon art.
 if(options.selected){frame.strokeColor=F.color('selection.edge');frame.lineWidth=.65*unit;frame.roundRect(-w/2+3.5*unit,-h/2+3.5*unit,w-7*unit,h-7*unit,Math.max(.1,r-2.5*unit));frame.stroke();}
 if(options.quality==='神器'||options.quality==='传奇'){
  // Reuse the approved panel curls verbatim; only their display scale changes.
  const requested=options.ornamentScale??1,ornamentScale=Math.min(w,h)>=72*unit&&Number.isFinite(requested)?Math.max(1,Math.min(2,requested)):1;
  const scale=.5*unit,inset=Math.max(2*unit,r*.32-7*scale),innerW=w-2*inset,innerH=h-2*inset,ornament=node(host,'SharedEquipmentCornerwork',innerW/scale,innerH/scale);
  ornament.setScale(scale,scale,1);UiChrome.cornerOrnaments(ornament,innerW/scale,innerH/scale,ornamentScale);
 }
 if(options.appearance==='preparation'&&!options.quality&&!options.selected)frame.node.active=false;
 ButtonSurface.attach(parent,{parent:host,after:content,width:Math.max(1,w-6*unit),height:Math.max(1,h-6*unit),radius:Math.max(.1,r-2*unit),overlay:true});
 return {host,content};
}
