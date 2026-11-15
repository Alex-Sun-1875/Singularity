import {CompactGraphics} from './CompactGraphics';
import {_decorator,BlockInputEvents,ButtonComponent as Button,Color,Component,Graphics,isValid,Label,Node,UITransform} from 'cc';
import {DoubleGoldFrame} from './DoubleGoldFrame';
import {FeedbackView as F} from './FeedbackView';
import {applyRpgFont} from './RpgFont';
import {UI_FRAME_LAYOUT as L,UI_GOLD_PANEL_RULES as RULES,UI_SETTINGS_REFERENCE as R,UI_PANEL_BACK as BACK} from './UiChrome';
import {UiSkin} from './UiSkin';
import {UI_COLORS as C} from './UiTheme';

const {ccclass,requireComponent}=_decorator;
export type GoldPanelVariant='standard'|'settings';
export interface GoldPanelAction {label:string;action:string;disabled?:boolean}
export interface GoldPanelTab {label:string;action:string;selected:boolean;disabled?:boolean}
export interface GoldPanelMeasure {width:number;hit:number;unit:number;mobile:boolean;variant?:GoldPanelVariant;crest?:boolean;tabCount?:number}
export interface GoldPanelMetrics {
 referenceScale:number;pixelScale:number;padding:number;gap:number;crestReserve:number;
 titleFont:number;titleY:number;closeX:number;closeY:number;tabsY:number;bodyTop:number;
}
export interface GoldPanelShellOptions extends GoldPanelMeasure {
 title:string;height:number;centeredTitle?:boolean;dismissAction?:string;tabs?:readonly GoldPanelTab[];fill?:Color;
 /** Optional compact header rule, measured from the top of the content panel. */
 titleRuleY?:number;
}

/** Shared chrome only. Page owners retain body layout, data, scrolling and routing. */
@ccclass('GoldPanelShell')
@requireComponent(UITransform)
export class GoldPanelShell extends Component {
 loaded=false;
 loadError='';
 ready:Promise<void>=Promise.resolve();
 metrics!:GoldPanelMetrics;
 private options!:GoldPanelShellOptions;
 private owned:Node[]=[];
 private version=0;
 private activate:(action:string)=>void=()=>{};

 static measure(o:GoldPanelMeasure):GoldPanelMetrics {
  const r=o.variant==='settings'?o.width/R.width:0,pad=L.padding*o.unit,gap=L.gap*o.unit,inset=L.closeInset*o.unit;
  const closeX=Math.max(inset+o.hit/2,r?R.closeOffset*r:0),closeY=r&&o.mobile?Math.max(inset,(R.closeOffset+R.closeSize/2)*r-o.hit/2):closeX;
  const tabsY=r?Math.max(R.tabsY*r,closeY+o.hit+gap):o.hit+2*inset+o.hit/2;
  return {referenceScale:r,pixelScale:r||(o.mobile?R.mobileWidth/R.width*o.unit:1),padding:pad,gap,
   crestReserve:o.crest?(r?R.crestReserve*r:R.crestReserve*(o.mobile?R.mobileWidth/R.width*o.unit:1)):0,
   titleFont:r?R.titleSize*r:o.mobile?20*o.unit:27,titleY:r?R.titleY*r:closeX,closeX,closeY,tabsY,
   bodyTop:r?Math.max(tabsY+o.hit/2,Math.min((R.rowFirstY-R.rowHeight/2)*r,R.rowFirstY*r-o.hit/2)):o.hit+2*inset+(o.tabCount?o.hit:0)+gap};
 }

 configure(options:GoldPanelShellOptions,activate:(action:string)=>void):void {
  this.options={...options,tabs:options.tabs?.map(t=>({...t}))};this.activate=activate;
  const version=++this.version;this.loaded=false;this.loadError='';
  for(const n of this.owned){n.removeFromParent();n.destroy();}this.owned=[];
  const o=this.options,m=this.metrics=GoldPanelShell.measure({...o,tabCount:o.tabs?.length}),r=m.referenceScale;
  this.node.getComponent(UITransform)!.setContentSize(o.width,o.height);
  if(!this.node.getComponent(BlockInputEvents))this.node.addComponent(BlockInputEvents);
  UiSkin.panel(this.node,o.width,o.height,o.fill??C.inset,'panel',!!o.crest,m.pixelScale);
  const centered=o.centeredTitle!==false,titleWidth=o.width-2*m.padding-(o.dismissAction?(m.closeX+o.hit/2+m.gap)*(centered?2:1):0);
  const title=this.caption(this.node,'MenuTitle',o.title,centered?(r?R.titleX*r:0):-o.width/2+m.padding+(o.dismissAction?m.closeX+o.hit/2+m.gap:0)+titleWidth/2,o.height/2-m.titleY,titleWidth,o.hit,m.titleFont);
  title.horizontalAlign=centered?Label.HorizontalAlign.CENTER:Label.HorizontalAlign.LEFT;title.fontFamily='SimSun';
  if(!r)title.overflow=Label.Overflow.SHRINK;
  if(o.dismissAction){const back=this.action(this.node,'',o.dismissAction,-o.width/2+m.closeX,o.height/2-m.closeY,o.hit,o.hit,L.closeGlyph*o.unit);
   UiSkin.asset(back,BACK.skin,BACK.glyphLogical*o.unit,BACK.glyphLogical*o.unit,false);
  }
  if(r){this.referenceDivider(this.node,'title',o.height/2-R.rules.title.y*r);this.referenceDivider(this.node,'tabs',o.height/2-R.rules.tabs.y*r);}
  else this.divider(this.node,'title',o.height/2-(o.titleRuleY??m.bodyTop-m.gap/2),Math.min(o.width-2*m.padding,o.width*RULES.title.width/R.width));
  if(o.tabs?.length){const tabs=o.tabs,w=(o.width-2*m.padding-(tabs.length-1)*m.gap)/tabs.length;
   tabs.forEach((tab,i)=>{
    const x=(i-(tabs.length-1)/2)*(w+m.gap),n=this.action(this.node,tab.label,tab.action,x,o.height/2-m.tabsY,w,o.hit,r?R.tabsSize*r:o.mobile?27:18,!!tab.disabled),label=n.getComponentInChildren(Label)!,visualX=r?-o.width/2+(R.tabsFirstX+i*R.tabsStep)*r:x;
    if(r)label.node.setPosition(visualX-x,m.tabsY-R.tabsTextY*r);
    if(tab.selected){F.tint(label,'state.ready');UiSkin.asset(n,r?'double-gold-tab-rule-v6':'rpg-active-rule-v4',r?120*r:w*.7,r?18*r:5*o.unit,false).node.setPosition(visualX-x+R.tabActiveXOffset*r,r?m.tabsY-(R.tabsY+R.tabRuleOffset)*r:-o.hit/2+3*o.unit);}
   });
  }
  const frame=this.node.getComponent(DoubleGoldFrame)!;
  const skins=[...Object.values(RULES).map(s=>s.skin),...(o.tabs?.length?[r?'double-gold-tab-rule-v6':'rpg-active-rule-v4']:[])];
  this.ready=Promise.all([frame.ready,...skins.map(id=>UiSkin.frame('ui/quiet-bronze/'+id,0,this.node))]).then(()=>{
   if(isValid(this,true)&&version===this.version){this.loadError=frame.loadError;this.loaded=frame.loaded&&!this.loadError;}
  }).catch(error=>{if(isValid(this,true)&&version===this.version){this.loadError=String(error);console.warn('Gold panel shell unavailable:',error);}});
 }

 /** Fading lines share source art; page owners supply only width and position. */
 divider(parent:Node,kind:keyof typeof RULES,y:number,width:number,x=0):Node {
  const spec=RULES[kind],h=spec.height*this.metrics.pixelScale,n=this.part('GoldPanelRule:'+kind,parent,x,y,width,h);
  UiSkin.asset(n,spec.skin,width,h,false);return n;
 }
 /** Exact approved placements, usable inside the page's scrolling body as well. */
 referenceDivider(parent:Node,kind:keyof typeof R.rules,y:number):Node {
  const r=this.metrics.referenceScale,spec=R.rules[kind],w=spec.width*r,h=spec.height*r,n=this.part('SettingsRule:'+kind,parent,(spec.x-R.width/2)*r,y,w,h);
  UiSkin.asset(n,spec.skin,w,h,false);return n;
 }
 /** Quiet footer actions from the approved panel, independent of page callbacks. */
 footer(actions:readonly GoldPanelAction[]):void {
  actions=actions.filter(a=>a.action!==this.options.dismissAction);
  const o=this.options,m=this.metrics,r=m.referenceScale,y=Math.min(r?R.footerY*r:o.height-m.padding-o.hit/2,o.height-m.padding-o.hit/2);
  const available=o.width-2*m.padding,width=Math.min((available-(actions.length-1)*m.gap)/Math.max(1,actions.length),r&&actions.length===2?R.footerStep*r-m.gap:o.width);
  actions.forEach((a,i)=>this.action(this.node,a.label,a.action,r&&actions.length===2?-o.width/2+(R.footerFirstX+i*R.footerStep)*r:(i-(actions.length-1)/2)*(width+m.gap),o.height/2-y,width,o.hit,r?Math.max(o.mobile?14*o.unit:0,R.footerSize*r):o.mobile?27:18,!!a.disabled));
  if(actions.length===2){if(r)this.referenceDivider(this.node,'footer',o.height/2-R.rules.footer.y*r);else this.divider(this.node,'vertical',o.height/2-y,RULES.vertical.width*m.pixelScale);}
 }
 private part(name:string,parent:Node,x:number,y:number,w:number,h:number):Node {
  const n=new Node(name);n.layer=this.node.layer;parent.addChild(n);n.setPosition(x,y);n.addComponent(UITransform).setContentSize(w,h);this.owned.push(n);return n;
 }
 private caption(parent:Node,name:string,value:string,x:number,y:number,w:number,h:number,size:number):Label {
  const label=this.part(name,parent,x,y,w,h).addComponent(Label);label.string=value;label.fontSize=size;label.lineHeight=size*1.4;label.enableWrapText=true;label.overflow=Label.Overflow.CLAMP;label.color=C.ink;label.verticalAlign=Label.VerticalAlign.CENTER;applyRpgFont(label);return label;
 }
 private action(parent:Node,label:string,action:string,x:number,y:number,w:number,h:number,size:number,disabled=false):Node {
  const n=this.part(action,parent,x,y,w,h),face=this.part('GoldPanelActionFace',n,0,0,w,h),g=face.addComponent(CompactGraphics),b=n.addComponent(Button);b.transition=Button.Transition.NONE;b.interactable=!disabled;
  const draw=(pressed=false)=>{g.clear();if(pressed){g.fillColor=C.hover;g.roundRect(-w/2,-h/2,w,h,3);g.fill();}};
  if(!disabled){for(const event of [Node.EventType.TOUCH_START,Node.EventType.MOUSE_ENTER])n.on(event,()=>draw(true));for(const event of [Node.EventType.TOUCH_END,Node.EventType.TOUCH_CANCEL,Node.EventType.MOUSE_LEAVE])n.on(event,()=>draw());}
  const text=this.caption(n,'Text',label,0,0,w-16,h,size);text.horizontalAlign=Label.HorizontalAlign.CENTER;if(disabled)F.tint(text,'text.disabled');
  n.on(Button.EventType.CLICK,()=>{if(b.interactable)this.activate(action);});return n;
 }
 onDestroy(){this.version++;}
}
