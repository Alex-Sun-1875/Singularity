import {Color,Label,UIOpacity} from 'cc';

type Variant={label:Label;opacity:UIOpacity;used:number};

/** Reuse a few exact native TTF layouts when a short hint alternates states.
 * Zero opacity keeps hidden variants out of the draw list without onEnable
 * invalidating their text textures. The parent owns all nodes and their fonts.
 */
export class LabelVariants {
 readonly empty:Label;
 private readonly variants:Variant[]=[];
 private selected:Variant|undefined;
 private clock=0;

 constructor(private readonly create:()=>Label,private readonly limit=6){
  this.empty=create();this.empty.node.addComponent(UIOpacity).opacity=0;
 }

 set(text:string,color:Readonly<Color>):Label {
  if(!text){
   if(this.selected)this.selected.opacity.opacity=0;
   this.selected=undefined;return this.empty;
  }
  if(this.selected?.label.string===text&&this.selected.label.color.equals(color))return this.selected.label;
  let next=this.variants.find(v=>v.label.string===text&&v.label.color.equals(color));
  if(!next){
   if(this.variants.length<this.limit){
    const label=this.create(),opacity=label.node.addComponent(UIOpacity);opacity.opacity=0;
    next={label,opacity,used:0};this.variants.push(next);
   }else next=this.variants.reduce((a,b)=>a.used<b.used?a:b);
   next.label.string=text;next.label.color=color;
  }
  if(this.selected&&this.selected!==next)this.selected.opacity.opacity=0;
  next.opacity.opacity=255;next.used=++this.clock;this.selected=next;
  return next.label;
 }
}
