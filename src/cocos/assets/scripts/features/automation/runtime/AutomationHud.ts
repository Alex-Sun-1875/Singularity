import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {BlockInputEvents,ButtonComponent as Button,Label,Node,UITransform,Vec2} from 'cc';
import type {AutomationMode} from '../common/Automation';
import type {Hud} from '../../../app/Hud';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {UI_FRAME_GOLD,UI_FRAME_LAYOUT} from '../../../shared/ui/UiChrome';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import type {FeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {applyRpgFont} from '../../../shared/ui/RpgFont';
import {bindButtonFeedback} from '../../../shared/ui/ButtonFeedback';
import {automationText as tr} from '../locales';

export interface AutomationExperience {earned:number;cap:number;rate:number;capped?:boolean}
export interface AutomationHudState {mode:AutomationMode;navigating:boolean;paused:boolean;status:string;experience?:AutomationExperience}

/** A fixed-width HUD flyout. Opening it never pauses or changes automation. */
export class AutomationHud {
 readonly root:Node;
 private opened=false;
 private stamp='';
 private statusLabel:Label|null=null;
 private experienceValue:Label|null=null;
 private state:AutomationHudState={mode:'manual',navigating:false,paused:false,status:''};
 private targets:Node[]=[];
 private readonly hit:number;
 private readonly gap:number;
 private readonly width:number;
 private readonly visualHeight:number;
 private readonly trayHeight:number;
 private readonly trayY:number;
 constructor(private readonly hud:Hud,private readonly scale:number,top:number,availableWidth:number){
  this.hit=UI_FRAME_LAYOUT.hit*scale;this.gap=UI_FRAME_LAYOUT.gap*scale;
  this.width=Math.min(availableWidth,144*scale);this.visualHeight=26*scale;this.trayHeight=56*scale;
  // Visible chrome is compact; the 48px header and mode targets still have
  // an 8px gap. Frame padding never substitutes for touch clearance.
  this.trayY=-this.hit-this.gap;
  this.root=hud.node('AutomationHud',hud.root,0,top-this.hit/2,this.width,this.hit);this.root.active=false;
 }
 get expanded(){return this.opened;}
 get visible(){return this.root.activeInHierarchy;}
 get bottom(){return this.root.position.y-(this.opened?-this.trayY+this.trayHeight/2:this.hit/2);}
 get visualBottom(){return this.root.position.y-this.visualHeight/2;}
 setExpanded(expanded:boolean){if(this.opened===expanded)return;this.opened=expanded;this.render();}
 toggle(){this.setExpanded(!this.opened);}
 update(state:AutomationHudState,visible:boolean){
  const previous=this.state,a=previous.experience,b=state.experience;
  if(this.stamp&&this.root.active===visible&&(visible||!this.opened)&&previous.mode===state.mode&&previous.navigating===state.navigating&&previous.paused===state.paused&&previous.status===state.status&&!!a===!!b&&a?.earned===b?.earned&&a?.cap===b?.cap&&a?.rate===b?.rate)return;
  // Snapshot the small value object; callers may reuse and mutate their state.
  this.state={...state,experience:b?{...b}:undefined};this.root.active=visible;
  if(!visible)this.opened=false;
  this.render();
 }
 contains(point:Vec2):boolean{return this.targets.some(n=>n.isValid&&n.activeInHierarchy&&!!n.getComponent(UITransform)?.hitTest(point));}
 private label(parent:Node,text:string,x:number,y:number,w:number,h:number,size=13){
  const label=this.hud.text(parent,text,x,y,w,size*this.scale,C.ink,h);applyRpgFont(label);
  label.lineHeight=size*this.scale*1.25;label.enableWrapText=false;label.overflow=Label.Overflow.CLAMP;label.horizontalAlign=Label.HorizontalAlign.CENTER;label.cacheMode=Label.CacheMode.CHAR;return label;
 }
 private button(parent:Node,action:string,x:number,y:number,w:number,h:number,run:()=>void,faceHeight:number,visualParent?:Node):Node {
  const n=this.hud.node(action,parent,x,y,w,h),b=n.addComponent(Button);b.transition=Button.Transition.NONE;n.addComponent(BlockInputEvents);this.targets.push(n);
  const fw=w-6*this.scale,fh=faceHeight-4*this.scale,face=this.hud.node('PressedFace',visualParent??n,0,0,fw,fh),g=face.addComponent(CompactGraphics);
  // The compact header's visible capsule owns its wash. Its larger hit target
  // stays separate, with text above and the original metal lip above the wash.
  const border=visualParent?.getChildByName('SharedGoldFrame');if(border)face.setSiblingIndex(border.getSiblingIndex());
  bindButtonFeedback(n,b,state=>{if(!g.isValid)return;g.clear();if(state!=='idle'){g.fillColor=C.button;g.roundRect(-fw/2,-fh/2,fw,fh,visualParent?fh/2:Math.min(5*this.scale,fh/2));g.fill();}});
  n.on(Button.EventType.CLICK,run);return n;
 }
 private modeButton(parent:Node,choice:{label:string;action:string;icon:string;selected:boolean},x:number,width:number){
  const n=this.button(parent,choice.action,x,0,width,this.hit,()=>{this.setExpanded(false);this.hud.actions.click(choice.action);},this.hit);
  const role:FeedbackRole=this.state.paused?'state.paused':'state.running';
  // Existing gold iconography stays symmetric above the two short labels.
  const icon=UiSkin.asset(n,choice.icon,20*this.scale,20*this.scale,false);icon.node.setPosition(0,9*this.scale);F.tint(icon,'state.ready');
  const text=this.label(n,choice.label,0,-12*this.scale,width,20*this.scale,13);F.tint(text,choice.selected?role:'text.normal');
 }
 private render(){
  const s=this.state,key=[this.root.active,this.opened,s.mode,s.paused,!!s.experience].join('|');if(key===this.stamp){this.updateStatus();return;}this.stamp=key;
  if(!this.root.active)return;
  for(const n of [...this.root.children]){n.removeFromParent();n.destroy();}this.targets=[];this.statusLabel=null;this.experienceValue=null;
  const running=s.mode!=='manual',role:FeedbackRole=s.paused&&running?'state.paused':running?'state.running':'state.idle';
  const bar=this.hud.node('AutomationBar',this.root,0,0,this.width,this.visualHeight);UiSkin.panel(bar,this.width,this.visualHeight,C.inset,'capsule',false,this.scale/4);
  const main=this.button(this.root,'automation',0,0,this.width,this.hit,()=>this.hud.actions.click('automation'),this.visualHeight,bar);
  const idle=s.mode==='idle',showXp=!!s.experience;
  // Auto is centred on the entire fixed-width bar, independently of the caret.
  this.statusLabel=this.label(main,tr(idle?'mode.hunt':'mode.task'),showXp?-this.width/2+21*this.scale:0,0,showXp?30*this.scale:this.width-40*this.scale,this.visualHeight,13);
  this.statusLabel.node.name='AutomationStatus';F.tint(this.statusLabel,running?role:'text.normal');
  if(showXp){
   const dot=this.label(main,'·',-this.width/2+38.5*this.scale,0,6*this.scale,this.visualHeight,12);F.tint(dot,'text.secondary');
   const start=-this.width/2+44*this.scale,right=this.width/2-16*this.scale;
   this.experienceValue=this.label(main,'',(start+right)/2,0,right-start,this.visualHeight,12);this.experienceValue.node.name='AutomationDailyExperience';this.experienceValue.horizontalAlign=Label.HorizontalAlign.LEFT;
  }
  const arrow=this.hud.node('AutomationChevron',main,this.width/2-10*this.scale,0,8*this.scale,6*this.scale).addComponent(CompactGraphics);arrow.strokeColor=UI_FRAME_GOLD.light;arrow.lineWidth=this.scale;
  const sign=this.opened?-1:1;arrow.moveTo(-3*this.scale,1.5*this.scale*sign);arrow.lineTo(0,-1.5*this.scale*sign);arrow.lineTo(3*this.scale,1.5*this.scale*sign);arrow.stroke();
  if(this.opened){
   const tray=this.hud.node('AutomationModes',this.root,0,this.trayY,this.width,this.trayHeight);UiSkin.panel(tray,this.width,this.trayHeight,C.inset,'panel',false,this.scale/4);
   tray.addComponent(BlockInputEvents);this.targets.push(tray);
   const choices=[{label:tr('mode.task'),action:'auto:quest',icon:'automation-battle-v5',selected:s.mode==='quest'},{label:tr('mode.hunt'),action:'auto:idle',icon:'automation-hunt-v5',selected:s.mode==='idle'}];
   const width=(this.width-16*this.scale-this.gap)/2,step=width+this.gap;
   choices.forEach((choice,i)=>this.modeButton(tray,choice,(i-.5)*step,width));
  }
  this.updateStatus();
 }
 private updateStatus(){
  // Quota/status changes never replace a button during an ongoing press.
  if(!this.root.active||!this.experienceValue?.isValid)return;
  const d=this.state.experience,full=!!d&&(d.capped??(d.cap>0&&d.earned>=d.cap));
  this.experienceValue.string=d?d.cap<0?tr('daily.unlimited'):full?tr('daily.capped'):d.cap===0?tr('daily.maxLevel'):tr('daily.header',{earned:d.earned,cap:d.cap}):tr('daily.loading');F.tint(this.experienceValue,full?'state.paused':'text.secondary');
 }
}
