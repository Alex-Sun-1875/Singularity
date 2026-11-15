import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {BlockInputEvents,ButtonComponent as Button,Graphics,Label,Node,UITransform} from 'cc';
import type {Hud} from '../../../app/Hud';
import {DoubleGoldFrame} from '../../../shared/ui/DoubleGoldFrame';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import type {FeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {applyRpgFont,fitRpgLine} from '../../../shared/ui/RpgFont';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {UI_FRAME_GOLD} from '../../../shared/ui/UiChrome';

export type QuestTrackerLine='area'|'objective'|'quest-route'|'quest-distance';
interface QuestTrackerLayout {left:number;top:number;width:number;scale:number;hit:number;expanded:boolean}

/** Display-only disclosure: it never opens a menu or changes navigation. */
export class QuestTracker {
 readonly root:Node;
 readonly textButton:Node;
 readonly navigationButton:Node;
 readonly actionLabel:Label;
 private opened:boolean;
 private readonly lines:Record<QuestTrackerLine,Label>;
 private readonly values:Record<QuestTrackerLine,string>={area:'',objective:'','quest-route':'','quest-distance':''};
 private readonly divider:Graphics;
 private role:FeedbackRole|null=null;

 constructor(private readonly hud:Hud,private readonly layout:QuestTrackerLayout){
  this.opened=layout.expanded;
  const {left,top,width}=layout,height=this.height;
  this.root=hud.node('QuestSummary',hud.root,left+width/2,top-height/2,width,height);
  UiSkin.panel(this.root,width,height,C.inset,'panel',false,.75);
  this.root.addComponent(BlockInputEvents);
  this.textButton=this.flatAction('QuestToggle',()=>this.setExpanded(!this.opened));
  this.navigationButton=this.flatAction('journey-toggle-navigation',()=>hud.actions.click('journey-toggle-navigation'));
  const line=(key:QuestTrackerLine)=>{
   const label=hud.text(this.textButton,'',0,0,1,1,C.ink,1);label.node.name='Quest:'+key;
   applyRpgFont(label);label.enableWrapText=false;label.overflow=Label.Overflow.CLAMP;
   hud.labels.set(key,label);return label;
  };
  this.lines={area:line('area'),objective:line('objective'),'quest-route':line('quest-route'),'quest-distance':line('quest-distance')};
  this.divider=hud.node('QuestActionDivider',this.root,0,0,1,24*layout.scale).addComponent(CompactGraphics);
  this.actionLabel=hud.text(this.navigationButton,'出发',0,0,1,12*layout.scale,C.ink,22*layout.scale);
  applyRpgFont(this.actionLabel);this.actionLabel.horizontalAlign=Label.HorizontalAlign.CENTER;
  this.actionLabel.enableWrapText=false;this.actionLabel.overflow=Label.Overflow.CLAMP;
  this.positionContent();this.setFeedback('state.idle');
 }

 get expanded(){return this.opened;}
 get expandedBottom(){return this.layout.top-56*this.layout.scale;}
 private get height(){return (this.opened?56:35)*this.layout.scale;}

 setExpanded(expanded:boolean):void {
  if(this.opened===expanded)return;
  this.opened=expanded;
  const {left,top,width}=this.layout,height=this.height;
  this.root.setPosition(left+width/2,top-height/2);
  this.root.getComponent(DoubleGoldFrame)!.resize(width,height);
  this.positionContent();
 }

 setLine(key:QuestTrackerLine,value:string):void {
  value=value.replace(/\n/g,' · ');
  if(this.values[key]===value)return;
  this.values[key]=value;
  // Only the distance can change the collapsed title's available width.
  if(key==='quest-distance')this.positionContent();else this.fitLine(key);
 }

 setFeedback(role:FeedbackRole):void {
  if(this.role===role)return;this.role=role;
  const idle=role==='state.idle';
  F.tint(this.lines.area,idle?'map.task':role);
  F.tint(this.lines.objective,idle?'text.normal':role);
  for(const key of ['quest-route','quest-distance']as const)F.tint(this.lines[key],idle?'text.secondary':role);
  F.tint(this.actionLabel,role);
 }

 private positionContent():void {
  const {width,scale,hit}=this.layout,height=this.height,pad=10*scale,gap=8*scale;
  const column=Math.max(52*scale,hit+4*scale),navX=width/2-column/2;
  const textLeft=-width/2+pad,textRight=navX-hit/2-gap,textWidth=textRight-textLeft;
  this.textButton.setPosition((textLeft+textRight)/2,0);
  this.textButton.getComponent(UITransform)!.setContentSize(textWidth,Math.max(hit,height-12*scale));
  this.navigationButton.setPosition(navX,0);this.navigationButton.getComponent(UITransform)!.setContentSize(hit,hit);
  // Grow collapsed touch targets downward so the gap above stays clear.
  for(const node of [this.textButton,this.navigationButton]){
   const transform=node.getComponent(UITransform)!;
   transform.setAnchorPoint(.5,Math.max(.5,1-height/(2*transform.height)));
  }
  this.actionLabel.node.getComponent(UITransform)!.setContentSize(column-12*scale,22*scale);
  const distanceWidth=this.values['quest-distance']?Math.max(22*scale,Math.min(32*scale,this.values['quest-distance'].length*9.5*.56*scale)):0;
  const titleWidth=this.opened||!distanceWidth?textWidth:textWidth-distanceWidth-4*scale;
  const place=(key:QuestTrackerLine,x:number,y:number,w:number,size:number,h:number,active=true)=>{
   const label=this.lines[key];label.fontSize=size*scale;label.lineHeight=label.fontSize*1.2;
   label.node.setPosition(x,y*scale);label.node.getComponent(UITransform)!.setContentSize(w,h*scale);label.node.active=active;
   this.fitLine(key);
  };
  place('area',0,15.33,textWidth,9.5,13,this.opened);
  place('objective',-(textWidth-titleWidth)/2,0,titleWidth,this.opened?12.5:11,18);
  place('quest-route',0,-15.33,textWidth,9.5,13,this.opened);
  place('quest-distance',textWidth/2-distanceWidth/2,0,distanceWidth,9.5,14,!this.opened&&!!distanceWidth);
  const g=this.divider,dividerHeight=24*scale;
  g.node.setPosition(width/2-column,0);g.clear();g.strokeColor=UI_FRAME_GOLD.metal;g.lineWidth=.6*scale;
  g.moveTo(0,-dividerHeight/2);g.lineTo(0,dividerHeight/2);g.stroke();
 }

 private fitLine(key:QuestTrackerLine):void {
  const label=this.lines[key];
  label.string=fitRpgLine(this.values[key],label.node.getComponent(UITransform)!.width,label.fontSize);
 }

 private flatAction(name:string,click:()=>void):Node {
  const {scale}=this.layout,n=this.hud.node(name,this.root),button=n.addComponent(Button);
  button.transition=Button.Transition.NONE;n.addComponent(BlockInputEvents);n.on(Button.EventType.CLICK,click);
  const face=this.hud.node('QuestPressedFace',n,0,0,0,0).addComponent(CompactGraphics);
  const paint=(pressed:boolean)=>{
   face.clear();if(!pressed||!button.interactable)return;
   const {width,height}=n.getComponent(UITransform)!,h=Math.min(height,this.height-12*scale);
   face.fillColor=C.button;face.roundRect(-width/2,-h/2,width,h,4*scale);face.fill();
  };
  n.on(Node.EventType.TOUCH_START,()=>paint(true));n.on(Node.EventType.TOUCH_END,()=>paint(false));n.on(Node.EventType.TOUCH_CANCEL,()=>paint(false));
  n.on(Node.EventType.MOUSE_ENTER,()=>paint(true));n.on(Node.EventType.MOUSE_LEAVE,()=>paint(false));return n;
 }
}
