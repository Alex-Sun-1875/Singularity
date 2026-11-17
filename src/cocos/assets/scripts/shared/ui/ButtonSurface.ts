import {_decorator,ButtonComponent as Button,Color,Component,Node,UITransform} from 'cc';
import {CompactGraphics} from './CompactGraphics';
import {bindButtonFeedback,type ButtonFeedbackState} from './ButtonFeedback';
import {FeedbackView as F} from './FeedbackView';
import {UI_COLORS as C} from './UiTheme';

const {ccclass}=_decorator;
export interface ButtonSurfaceOptions {
 width:number;height:number;x?:number;y?:number;radius?:number;
 /** Artwork gets a translucent inlay; plain rows use the existing brown fill. */
 overlay?:boolean;idleFill?:Color;border?:Color;
 /** Keep the inlay above this background and below text, icons and selection edges. */
 after?:Node;parent?:Node;name?:string;
}

/** Shared visible feedback bounds, independent of the native Button's touch bounds. */
@ccclass('ButtonSurface')
export class ButtonSurface extends Component {
 private face:Node|null=null;
 private ink:CompactGraphics|null=null;
 private options!:ButtonSurfaceOptions;
 configure(button:Button,options:ButtonSurfaceOptions):this {
  this.options=options;
  if(!this.face){this.face=new Node(options.name??'ButtonSurface');this.face.layer=this.node.layer;this.face.addComponent(UITransform);this.ink=this.face.addComponent(CompactGraphics);}
  const face=this.face,parent=options.parent??this.node;parent.addChild(face);face.setPosition(options.x??0,options.y??0);
  face.getComponent(UITransform)!.setContentSize(Math.max(1,options.width),Math.max(1,options.height));
  face.setSiblingIndex(options.after?.parent===parent?options.after.getSiblingIndex()+1:0);
  bindButtonFeedback(this.node,button,state=>this.paint(state));return this;
 }
 private paint(state:ButtonFeedbackState):void {
  const g=this.ink;if(!g?.isValid)return;g.clear();
  const o=this.options,w=Math.max(1,o.width),h=Math.max(1,o.height),radius=Math.min(o.radius??4,w/2,h/2);
  const fill=state==='idle'?o.idleFill:o.overlay?F.color(state==='pressed'?'control.pressed':'control.hover',state==='pressed'?100:40):state==='pressed'?C.button:C.hover;
  if(fill){g.fillColor=fill;g.roundRect(-w/2,-h/2,w,h,radius);g.fill();}
  if(o.border){g.strokeColor=o.border;g.lineWidth=1;g.roundRect(-w/2,-h/2,w,h,radius);g.stroke();}
 }
 static attach(node:Node,options:ButtonSurfaceOptions):ButtonSurface|undefined {
  const button=node.getComponent(Button);if(!button)return;
  return (node.getComponent(ButtonSurface)??node.addComponent(ButtonSurface)).configure(button,options);
 }
}
