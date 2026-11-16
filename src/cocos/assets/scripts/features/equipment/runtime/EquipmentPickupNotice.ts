import {Label,Node,Sprite,UIOpacity,UITransform} from 'cc';
import type {ItemDef} from '../data/Equipment';
import {qualityFeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {EquipmentArt} from './EquipmentArt';
import {equipmentBasePresentation,equipmentTypeName} from './EquipmentPresentation';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {applyRpgFont,fitRpgLine} from '../../../shared/ui/RpgFont';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {UiChrome} from '../../../shared/ui/UiChrome';
import type {Hud} from '../../../app/Hud';
import type {GameSession} from '../../../core/GameSession';
import {EQUIPMENT} from '../data/Equipment';
import {EQUIPMENT_DROP_NOTICE_SECONDS,equipmentDropPriority,highlightedEquipment} from '../common/LootFeedback';
import {equipmentText} from '../locales';

type Pickup={item:ItemDef;count:number;elapsed:number;duration:number;priority:number;dropId?:string;available?:boolean};
const NOTICE_HEIGHT=72;

/** A single passive HUD lane. Acquisition events survive unrelated system toasts,
 * menus and layout rebuilds; only visible time counts toward dismissal. */
export class EquipmentPickupNotice {
 private current:Pickup|null=null;
 private pending:Pickup[]=[];
 private announcedDrops=new Set<string>();
 private root:Node|null=null;
 private opacity:UIOpacity|null=null;
 private glow:Sprite|null=null;
 private width=0;
 private unit=1;
 private level=1;
 private anchor={x:0,y:0};
 private animatedNotice:Pickup|null=null;private animatedRoot:Node|null=null;
 private animatedElapsed=-1;private animatedX=Infinity;private animatedY=Infinity;private animatedReduced=false;
 constructor(private hud:Hud){}

 mount(width:number,unit:number){
  this.width=width;this.unit=unit;
  this.root=this.hud.node('EquipmentPickupNotice',this.hud.root,0,0,width,NOTICE_HEIGHT*unit);
  this.opacity=this.root.addComponent(UIOpacity);this.root.active=false;
  this.render();
 }

 enqueue(item:ItemDef,count=1,level=this.level){
  if(this.level!==level){this.level=level;if(this.current)this.render();}
  const priority=equipmentDropPriority(item.quality);
  this.queue({item,count,elapsed:0,duration:priority>=2?5.4:priority===1?3.6:3,priority});
 }

 /** Reconcile against the authoritative pile IDs, including reloads and travel.
  * A collected/removed pile cannot survive in the current slot or its queue. */
 syncGroundLoot(game:GameSession){
  if(this.level!==game.state.progression.level){this.level=game.state.progression.level;if(this.current)this.render();}
  const drops=new Map(game.state.groundLoot.filter(d=>d.area===game.state.area).map(d=>[d.id,d]));
  this.pending=this.pending.filter(n=>!n.dropId||drops.has(n.dropId));
  if(this.current?.dropId&&!drops.has(this.current.dropId)){this.current=this.pending.shift()??null;this.render();}
  for(const drop of drops.values()){
   const item=EQUIPMENT[drop.item];if(!item||!highlightedEquipment(item.quality))continue;
   const available=game.canPickupLoot(drop);
   if(this.current?.dropId===drop.id&&this.current.available!==available){this.current.available=available;this.render();}
   const waiting=this.pending.find(n=>n.dropId===drop.id);if(waiting)waiting.available=available;
   if(this.announcedDrops.has(drop.id)||Math.hypot(drop.x-game.state.player.x,drop.z-game.state.player.z)>=30)continue;
   this.announcedDrops.add(drop.id);
   this.queue({item,count:1,elapsed:0,duration:EQUIPMENT_DROP_NOTICE_SECONDS,priority:equipmentDropPriority(item.quality),dropId:drop.id,available});
  }
 }

 dismissDrop(id:string){
  this.pending=this.pending.filter(n=>n.dropId!==id);
  if(this.current?.dropId===id){this.current=this.pending.shift()??null;this.render();}
 }

 private queue(next:Pickup){
  const priority=next.priority;
  if(!this.current||priority>this.current.priority){
   if(this.current)this.pending.push(this.current);
   this.current=next;this.render();
  }else this.pending.push(next);
  this.pending.sort((a,b)=>b.priority-a.priority);
 }

 clear(){this.current=null;this.pending=[];this.announcedDrops.clear();if(this.root)this.root.active=false;}
 get visible(){return !!this.root?.active;}
 get hasNotice(){return !!this.current;}
 get dropVisible(){return !!this.current?.dropId;}
 get height(){return NOTICE_HEIGHT*this.unit;}
 inspect(){return {visible:this.visible,current:this.current?{id:this.current.dropId,item:this.current.item.id,elapsed:this.current.elapsed,duration:this.current.duration,available:this.current.available}:null,pending:this.pending.map(n=>({id:n.dropId,item:n.item.id,elapsed:n.elapsed}))};}

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
  for(const child of [...root.children])child.destroy();root.removeAllChildren();this.glow=null;
  const notice=this.current;if(!notice){root.active=false;return;}
  const {item}=notice,s=this.unit,w=this.width,role=qualityFeedbackRole(item.quality);
  // Both states share the accepted v2 cut-metal border and its brown material.
  // Only the truthful status text differs; this lane never captures input.
  root.getComponent(UITransform)!.setContentSize(w,NOTICE_HEIGHT*s);
  const frame=this.hud.node('EquipmentNoticeFrame',root,0,0,w,NOTICE_HEIGHT*s);
  UiSkin.panel(frame,w,NOTICE_HEIGHT*s,F.color('text.outline',230),'panel',false,s/2,'loot-drop-panel-v1',true);
  const iconX=-w/2+50*s,iconSize=56*s;
  this.glow=UiSkin.sprite(root,'ui/quiet-bronze/skill-soft-halo-v17',78*s,66*s,F.color(role,150));this.glow.node.setPosition(iconX,0);this.glow.node.name='NoticeQualityGlow';
  if(item.quality==='传奇'||item.quality==='神器'){
   // Keep the existing four-corner engraving behind the item silhouette.
   const ornaments=this.hud.node('NoticeEquipmentOrnaments',root,iconX,0,72,68);
   ornaments.setScale(s,s,1);UiChrome.cornerOrnaments(ornaments,72,68);
  }
  const icon=this.hud.node('NoticeEquipment',root,iconX,0,iconSize,iconSize),sprite=icon.addComponent(Sprite);sprite.sizeMode=Sprite.SizeMode.CUSTOM;sprite.trim=false;
  void EquipmentArt.itemFrame(item,icon).then(frame=>{if(!icon.isValid)return;const scale=Math.min(iconSize/frame.rect.width,iconSize/frame.rect.height);icon.getComponent(UITransform)!.setContentSize(frame.rect.width*scale,frame.rect.height*scale);sprite.spriteFrame=frame;}).catch(error=>{if(icon.isValid)console.warn('[EquipmentNotice]',String(error));});
  // The reference's three text rows share one left edge next to the artwork.
  const textLeft=98*s,showStats=w/s>=290,statsLeft=w-88*s,width=showStats?statsLeft-textLeft-12*s:w-textLeft-18*s,x=-w/2+textLeft+width/2;
  const titleText=equipmentText(notice.dropId?'loot.dropTitle':'loot.acquiredTitle',{quality:item.quality});
  const countText=notice.count>1?` ×${notice.count}`:'';
  const nameText=fitRpgLine(item.name,width-(countText?(.56*countText.length+.44)*20*s:0),20*s)+countText;
  const hintText=equipmentText(notice.dropId?notice.available?'loot.autoPickup':'loot.noticeFull':'loot.acquired');
  const title=this.hud.text(root,fitRpgLine(titleText,width,11.5*s),x,22*s,width,11.5*s,F.color(role),16*s);
  const name=this.hud.text(root,nameText,x-4*s,0,width,20*s,F.color(role),27*s);
  const hint=this.hud.text(root,fitRpgLine(hintText,width,11*s),x,-22*s,width,11*s,F.color('text.normal'),16*s);
  title.node.name='NoticeQuality';name.node.name='NoticeName';hint.node.name='NoticeHint';
  for(const label of [title,name,hint]){applyRpgFont(label);label.horizontalAlign=Label.HorizontalAlign.LEFT;label.enableWrapText=false;label.overflow=Label.Overflow.CLAMP;label.enableOutline=true;label.outlineColor=F.color('text.outline',220);label.outlineWidth=.6*s;}
  if(showStats){
   const base=equipmentBasePresentation(item,this.level),bonuses=base.stats.filter(stat=>stat.label!=='等级要求'),stats=(bonuses.length?bonuses:base.stats).slice(0,2),statWidth=70*s,statX=-w/2+statsLeft;
   const heading=this.hud.text(root,bonuses.length?equipmentText('loot.noticeAttributes'):equipmentTypeName(item),statX+statWidth/2,22*s,statWidth,9.5*s,F.color('text.secondary'),14*s);
   heading.node.name='NoticeStatsHeading';heading.horizontalAlign=Label.HorizontalAlign.LEFT;heading.enableWrapText=false;heading.overflow=Label.Overflow.CLAMP;applyRpgFont(heading);
   const compact:Record<string,string>={'基础攻击／技能威力':equipmentText('loot.noticePower'),'最大生命':equipmentText('loot.noticeHealth'),'等级要求':equipmentText('loot.noticeLevel')};
   stats.forEach((stat,index)=>{
    const y=(stats.length===1?0:4-index*22)*s,labelWidth=24*s,valueWidth=statWidth-labelWidth;
    const caption=this.hud.text(root,compact[stat.label]??stat.label,statX+labelWidth/2,y,labelWidth,11*s,F.color('text.secondary'),16*s);
    const value=this.hud.text(root,fitRpgLine(stat.value,valueWidth,11.5*s),statX+labelWidth+valueWidth/2,y,valueWidth,11.5*s,F.color('text.normal'),16*s);
    caption.node.name='NoticeStatLabel'+index;value.node.name='NoticeStatValue'+index;
    caption.horizontalAlign=Label.HorizontalAlign.LEFT;value.horizontalAlign=Label.HorizontalAlign.RIGHT;
    for(const label of [caption,value]){applyRpgFont(label);label.enableWrapText=false;label.overflow=Label.Overflow.CLAMP;}
   });
  }
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
 }
}
