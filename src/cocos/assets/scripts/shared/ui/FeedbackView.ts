import {CompactGraphics} from './CompactGraphics';
import {builtinResMgr,Color,Graphics,Label,Node,Sprite,SpriteFrame,Texture2D,UIOpacity,UIRenderer,UITransform} from 'cc';
import {FEEDBACK_PALETTE,type FeedbackRole} from './FeedbackPalette';

/** Common presentation adapter. Callers pass meaning; only the palette owns RGB.
 * @example FeedbackView.tint(label,'state.paused');
 * @example FeedbackView.bar(sprite,hp,maxHp,'health.enemy');
 * Returned colors are shared and must not be mutated; alpha variants are copies. */
export class FeedbackView {
 private static semanticFrame:SpriteFrame|undefined;
 private static colors=new Map<FeedbackRole,Color>();
 static color(role:FeedbackRole,alpha?:number):Color {
  let color=this.colors.get(role);if(!color){const hex=FEEDBACK_PALETTE[role];color=new Color(parseInt(hex.slice(1,3),16),parseInt(hex.slice(3,5),16),parseInt(hex.slice(5,7),16));this.colors.set(role,color);}
  return alpha===undefined?color:new Color(color.r,color.g,color.b,alpha);
 }
 static tint(target:Label|Sprite,role:FeedbackRole){target.color=this.color(role);}
 /** Use before drawing a Graphics path; existing geometry keeps its own color. */
 static ink(target:Graphics,role:FeedbackRole,kind:'fill'|'stroke'='fill',alpha?:number){if(kind==='stroke')target.strokeColor=this.color(role,alpha);else target.fillColor=this.color(role,alpha);}
 static combatText(label:Label,role:FeedbackRole,critical=false){
  this.tint(label,role);label.enableOutline=true;label.outlineColor=this.color(critical?'damage.critical':'text.outline');label.outlineWidth=critical?2.5:2;label.isBold=true;
 }
 /** Player health keeps the original skin; other fills use semantic colors. */
 static bar(parent:Sprite,value:number,max:number,role:FeedbackRole){
  const fraction=Math.max(0,Math.min(1,max>0?value/max:0));
  if(parent.spriteFrame?.texture)parent.fillRange=fraction;
  let fill=parent.node.getChildByName('SemanticBarFill')?.getComponent(Graphics);
  let rectangle=parent.node.getChildByName('SemanticSpriteFill')?.getComponent(Sprite);
  if(role==='health.player'){
   if(!parent.spriteFrame?.texture){parent.enabled=false;return;}
   if(fill)fill.node.active=false;if(rectangle)rectangle.node.active=false;
   parent.color=Color.WHITE;
   if(parent.type!==Sprite.Type.FILLED){parent.fillType=Sprite.FillType.HORIZONTAL;parent.fillStart=0;parent.fillRange=fraction;parent.type=Sprite.Type.FILLED;}
   parent.enabled=true;return;
  }
  // Graphics and Sprite inherit opacity differently in Creator 3.8.8. Keep
  // the original renderer for any hierarchy that can animate its opacity.
  let opaque=true;
  for(let ancestor:Node|null=parent.node;ancestor;ancestor=ancestor.parent)if(ancestor.getComponent(UIOpacity)||((ancestor.getComponent(UIRenderer)?.color.a??255)!==255)){opaque=false;break;}
  parent.enabled=false;
  if(opaque){
   if(fill)fill.node.active=false;
   if(!rectangle){
    const node=new Node('SemanticSpriteFill');node.layer=parent.node.layer;parent.node.addChild(node);if(fill)node.setSiblingIndex(fill.node.getSiblingIndex());node.addComponent(UITransform);
    rectangle=node.addComponent(Sprite);rectangle.sizeMode=Sprite.SizeMode.CUSTOM;
    if(!this.semanticFrame){this.semanticFrame=new SpriteFrame();this.semanticFrame.packable=false;this.semanticFrame.texture=builtinResMgr.get<Texture2D>('white-texture');}
    rectangle.spriteFrame=this.semanticFrame;rectangle.fillType=Sprite.FillType.HORIZONTAL;rectangle.fillStart=0;rectangle.type=Sprite.Type.FILLED;
   }
   rectangle.node.active=true;
   const data=rectangle as Sprite&{feedbackRole?:FeedbackRole;feedbackFraction?:number};
   if(data.feedbackRole!==role||data.feedbackFraction!==fraction){
    data.feedbackRole=role;data.feedbackFraction=fraction;
    const size=parent.node.getComponent(UITransform)!;rectangle.node.getComponent(UITransform)!.setContentSize(size.width,size.height);
    rectangle.color=this.color(role);rectangle.fillRange=fraction;
   }
   return;
  }
  if(rectangle)rectangle.node.active=false;
  if(!fill){const node=new Node('SemanticBarFill');node.layer=parent.node.layer;parent.node.addChild(node);if(rectangle)node.setSiblingIndex(rectangle.node.getSiblingIndex());const size=parent.node.getComponent(UITransform)!;node.addComponent(UITransform).setContentSize(size.width,size.height);fill=node.addComponent(CompactGraphics);}
  fill.node.active=true;
  const stamp=`${role}:${fraction}`,data=fill as Graphics&{feedbackStamp?:string};
  if(data.feedbackStamp!==stamp){data.feedbackStamp=stamp;const size=parent.node.getComponent(UITransform)!;fill.clear();this.ink(fill,role);fill.rect(-size.width/2,-size.height/2,size.width*fraction,size.height);fill.fill();}
 }
}
