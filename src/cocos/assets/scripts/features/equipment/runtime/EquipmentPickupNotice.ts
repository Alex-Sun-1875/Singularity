import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {Graphics,Label,Node,Sprite,UIOpacity,UITransform,Vec2} from 'cc';
import type {ItemDef} from '../data/Equipment';
import {qualityFeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {EquipmentArt} from './EquipmentArt';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {applyRpgFont} from '../../../shared/ui/RpgFont';
import {UiSkin} from '../../../shared/ui/UiSkin';
import type {Hud} from '../../../app/Hud';

type Pickup={item:ItemDef;count:number;elapsed:number;duration:number;priority:number};

/** A single passive HUD lane. Acquisition events survive unrelated system toasts,
 * menus and layout rebuilds; only visible time counts toward dismissal. */
export class EquipmentPickupNotice {
 private current:Pickup|null=null;
 private pending:Pickup[]=[];
 private root:Node|null=null;
 private opacity:UIOpacity|null=null;
 private sheen:Graphics|null=null;
 private glow:Sprite|null=null;
 private width=0;
 private unit=1;
 private anchor={x:0,y:0};
 private animatedNotice:Pickup|null=null;private animatedRoot:Node|null=null;
 private animatedElapsed=-1;private animatedX=Infinity;private animatedY=Infinity;private animatedReduced=false;
 constructor(private hud:Hud){}

 mount(width:number,unit:number){
  this.width=width;this.unit=unit;
  this.root=this.hud.node('EquipmentPickupNotice',this.hud.root,0,0,width,58*unit);
  this.opacity=this.root.addComponent(UIOpacity);this.root.active=false;
  this.render();
 }

 enqueue(item:ItemDef,count=1){
  const priority=item.quality==='神器'?2:item.quality==='传奇'?1:0;
  const next:Pickup={item,count,elapsed:0,duration:priority?5.4:item.quality==='史诗'?3.6:3,priority};
  if(!this.current||priority>this.current.priority){
   if(this.current){this.current.elapsed=0;this.pending.push(this.current);}
   this.current=next;this.render();
  }else this.pending.push(next);
  this.pending.sort((a,b)=>b.priority-a.priority);
 }

 clear(){this.current=null;this.pending=[];if(this.root)this.root.active=false;}
 get visible(){return !!this.root?.active;}

 layout(x:number,y:number,visible:boolean){
  this.anchor.x=x;this.anchor.y=y;
  if(this.root){this.root.active=visible&&!!this.current;this.animate();}
 }

 update(dt:number,visible:boolean){
  if(this.current&&visible){
   this.current.elapsed+=Math.max(0,dt);
   if(this.current.elapsed>=this.current.duration){this.current=this.pending.shift()??null;this.render();}
  }
  this.layout(this.anchor.x,this.anchor.y,visible);
 }

 private render(){
  const root=this.root;if(!root)return;
  this.animatedNotice=null;
  for(const child of [...root.children])child.destroy();root.removeAllChildren();this.sheen=null;this.glow=null;
  const notice=this.current;if(!notice){root.active=false;return;}
  const {item,priority}=notice,s=this.unit,w=this.width,role=qualityFeedbackRole(item.quality);
  // Reuse the approved paired metal lips and material rather than painting a
  // second notification skin. The frame is decorative and never captures input.
  const frame=this.hud.node('PickupFrame',root,0,0,w,58*s);UiSkin.panel(frame,w,58*s,F.color('text.outline',230),'capsule');
  const iconX=-w/2+27*s;
  this.glow=UiSkin.sprite(root,'ui/quiet-bronze/skill-soft-halo-v17',62*s,62*s,F.color(role,priority?255:120));this.glow.node.setPosition(iconX,0);this.glow.node.name='PickupQualityGlow';
  const icon=this.hud.node('PickupEquipment',root,iconX,0,44*s,44*s),sprite=icon.addComponent(Sprite);sprite.sizeMode=Sprite.SizeMode.CUSTOM;sprite.trim=false;
  void EquipmentArt.itemFrame(item,icon).then(frame=>{if(!icon.isValid)return;const scale=Math.min(44*s/frame.rect.width,44*s/frame.rect.height);icon.getComponent(UITransform)!.setContentSize(frame.rect.width*scale,frame.rect.height*scale);sprite.spriteFrame=frame;}).catch(error=>{if(icon.isValid)console.warn('[EquipmentPickup]',String(error));});
  const textWidth=w-64*s,textX=-w/2+58*s+textWidth/2;
  const badge=this.hud.text(root,`获得${item.quality}装备`,textX,15*s,textWidth,11.5*s,F.color(role,225),16*s);
  badge.node.name='PickupQuality';badge.enableWrapText=false;
  const name=this.hud.text(root,`${item.name}${notice.count>1?` ×${notice.count}`:''}`,textX,-4*s,textWidth,(priority?21:18.5)*s,F.color(role),29*s);
  name.node.name='PickupName';name.enableWrapText=false;
  name.enableOutline=true;name.outlineColor=F.color('text.outline',220);name.outlineWidth=.75*s;
  if(priority){name.enableShadow=true;name.shadowColor=F.color(role,140);name.shadowBlur=4*s;name.shadowOffset=new Vec2(0,0);}
  for(const label of [badge,name]){applyRpgFont(label);label.horizontalAlign=Label.HorizontalAlign.LEFT;label.lineHeight=label.fontSize*1.2;}
  const rule=UiSkin.sprite(root,'ui/quiet-bronze/rpg-equipment-title-rule-v5',textWidth,10*s,F.color(role,priority?235:140));rule.node.name='PickupEngraving';rule.node.setPosition(textX,-23*s);
  if(priority)this.sheen=this.hud.node('PickupSheen',root,0,0,w,50*s).addComponent(CompactGraphics);
  this.animate();
 }

 private animate(){
  const n=this.current,root=this.root;if(!n||!root||!this.opacity)return;
  const reduced=this.hud.reducedMotion;
  if(this.animatedNotice===n&&this.animatedRoot===root&&this.animatedElapsed===n.elapsed&&this.animatedX===this.anchor.x&&this.animatedY===this.anchor.y&&this.animatedReduced===reduced)return;
  this.animatedNotice=n;this.animatedRoot=root;this.animatedElapsed=n.elapsed;this.animatedX=this.anchor.x;this.animatedY=this.anchor.y;this.animatedReduced=reduced;
  const enter=reduced?1:Math.min(1,n.elapsed/.22),exit=reduced?1:Math.min(1,(n.duration-n.elapsed)/.25);
  this.opacity.opacity=Math.round(255*Math.max(0,Math.min(enter,exit)));
  const p=root.position;if(p.x!==this.anchor.x||p.y!==this.anchor.y)root.setPosition(this.anchor.x,this.anchor.y);
  const scale=root.scale;if(scale.x!==1||scale.y!==1||scale.z!==1)root.setScale(1,1,1);
  if(this.glow)this.glow.color=F.color(qualityFeedbackRole(n.item.quality),n.priority?(reduced?210:Math.round(210+45*Math.max(0,1-n.elapsed))):120);
  if(this.sheen){
   this.sheen.node.active=!reduced&&n.elapsed<.85;
   // A single light travels along the reused engraving, away from the text.
   if(this.sheen.node.active){
    this.sheen.clear();
    const t=n.elapsed/.85,s=this.unit,w=this.width,x=-w/2+62*s+(w-94*s)*t,y=-23*s;
    F.ink(this.sheen,'impact.core','stroke',Math.round(145*Math.sin(t*Math.PI)));this.sheen.lineWidth=.65*s;
    this.sheen.moveTo(x,y);this.sheen.lineTo(x+23*s,y);this.sheen.stroke();
   }
  }
 }
}
