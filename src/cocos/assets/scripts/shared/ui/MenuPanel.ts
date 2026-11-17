import {CompactMask as Mask} from './CompactMask';
import {CompactGraphics} from './CompactGraphics';
import {BlockInputEvents,ButtonComponent as Button,Color,Graphics,Label,Node,ScrollView,sys,UITransform} from 'cc';
import type {Hud} from '../../app/Hud';
import {UI_COLORS as C} from './UiTheme';
import {UiSkin} from './UiSkin';
import {FeedbackView as F} from './FeedbackView';
import {EQUIPMENT} from '../../features/equipment/data/Equipment';
import {qualityFeedbackRole,type FeedbackRole} from './FeedbackPalette';
import {equipmentIcon} from '../../features/equipment/runtime/EquipmentPresentation';
import {UI_FRAME_GOLD,UI_FRAME_LAYOUT,UI_GOLD_PANEL_CONTENT as CONTENT,UI_SETTINGS_REFERENCE as R} from './UiChrome';
import {applyRpgFont} from './RpgFont';
import {GoldMenuButton} from './GoldMenuButton';
import {GoldMenuActions} from './GoldMenuActions';
import {GoldPanelShell,type GoldPanelVariant} from './GoldPanelShell';
import {GoldPanelToggle} from './GoldPanelToggle';
import {ButtonSurface} from './ButtonSurface';

export interface MenuChoice {label:string;action:string;primary?:boolean;disabled?:boolean;/** Parent navigation, rendered by the shared adaptive header. */back?:boolean}
export interface MenuRow extends MenuChoice {detail:string;icon?:string;skin?:string;/** Full local resource path; retain the illustrated item's original colors. */image?:string;selected?:boolean;disabled?:boolean;value?:string;toggle?:boolean;/** Optional semantic tone for non-equipment content. */tone?:FeedbackRole}
export interface MenuPresentation {
 placement?:'left'|'right'|'center';
 /** Width in the established 720-high Cocos design space. */
 width?:number;
 quiet?:boolean;
 /** Mandatory confirmation screens keep an explicit header cancel action. */
 dismissOnBackdrop?:boolean;
 dismissAction?:string;
 dismissDisabled?:boolean;
 tabs?:{label:string;action:string;selected:boolean}[];
 centeredTitle?:boolean;
 rightInset?:number;
 keepCenterClear?:boolean;
 crest?:boolean;
 variant?:GoldPanelVariant;
 /** Compatibility with older callers; use variant:'settings' for new pages. */
 referenceSettings?:boolean;
}

/** Content-sized menus, separate from the full equipment/map workspaces. */
export class MenuPanel {
 private readonly mobile=sys.isMobile;
 private readonly hit:number;
 private readonly gap:number;
 private readonly pad:number;
 private readonly font:number;
 private readonly width:number;
 private readonly maxHeight:number;
 private readonly bounds:{left:number;right:number;bottom:number;top:number};
 private readonly header:number;
 private readonly scale:number;
 private readonly crestReserve:number;
 private readonly referenceScale:number;
 private readonly referenceHeight:number;
 private readonly variant:GoldPanelVariant;
 private shell!:GoldPanelShell;
 constructor(private readonly hud:Hud,private readonly options:MenuPresentation={},minimumHit=0){
  this.hit=Math.max(hud.touchTargetSize,minimumHit);this.scale=this.mobile?this.hit/UI_FRAME_LAYOUT.hit:1;
  this.gap=UI_FRAME_LAYOUT.gap*this.scale;this.pad=UI_FRAME_LAYOUT.padding*this.scale;
  this.variant=options.variant??(options.referenceSettings?'settings':'standard');
  this.font=this.mobile?26:17;
  const safe=sys.getSafeAreaRect(false),edge=this.mobile?12:16;
  this.bounds={left:-hud.width/2+Math.max(edge,safe.x),right:-hud.width/2+Math.min(hud.width-edge,safe.x+safe.width),bottom:-hud.height/2+Math.max(edge,safe.y),top:-hud.height/2+Math.min(hud.height-edge,safe.y+safe.height)};
  const availableHeight=this.bounds.top-this.bounds.bottom,settingsWidth=this.variant==='settings'&&this.mobile?Math.min(options.width??R.mobileWidth*this.scale,availableHeight*R.width/(R.height+(options.crest?R.crestReserve:0))):options.width;
  this.width=Math.min(settingsWidth??(this.mobile?620:560),this.bounds.right-this.bounds.left);
  const chrome=GoldPanelShell.measure({width:this.width,hit:this.hit,unit:this.scale,mobile:this.mobile,variant:this.variant,crest:options.crest,tabCount:options.tabs?.length});
  this.referenceScale=chrome.referenceScale;this.crestReserve=chrome.crestReserve;this.header=chrome.bodyTop;
  this.maxHeight=availableHeight-this.crestReserve;this.referenceHeight=this.referenceScale?Math.min(this.maxHeight,R.height*this.referenceScale):0;
 }
 private textHeight(value:string,width:number,size=this.font):number {
  if(!value)return 0;
  const lines=value.split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil(Array.from(line).reduce((w,c)=>w+(c.charCodeAt(0)<128?.57:1.02),0)*size/Math.max(1,width))),0);
  return Math.ceil(lines*size*1.4+4);
 }
 private text(parent:Node,value:string,x:number,y:number,width:number,height:number,size=this.font,color=C.ink):Label {
  const label=this.hud.text(parent,value,x,y,width,size,color,height);applyRpgFont(label);label.lineHeight=size*1.4;label.enableWrapText=true;label.overflow=Label.Overflow.CLAMP;return label;
 }
 private rule(parent:Node,y:number,width:number){
  this.shell.divider(parent,'row',y,Math.min(width,this.width-2*CONTENT.ruleInset*this.scale));
 }
 private settingsRule(parent:Node,kind:keyof typeof R.rules,y:number){
  this.shell.referenceDivider(parent,kind,y);
 }
 private surface(title:string,desiredHeight:number,dismiss?:string,disabled=false):{panel:Node;height:number}{
  this.hud.clearModal();const {hud}=this,height=Math.min(this.maxHeight,desiredHeight),shade=hud.node('MenuBackdrop',hud.modal,0,0,hud.width,hud.height),ink=shade.addComponent(CompactGraphics);
  ink.fillColor=new Color(C.background.r,C.background.g,C.background.b,this.options.quiet?0:96);ink.rect(-hud.width/2,-hud.height/2,hud.width,hud.height);ink.fill();
  shade.addComponent(BlockInputEvents);
  // Only dismiss screens which explicitly offer a way back. Dialogue, login,
  // new-game confirmation and mandatory recovery retain their own choices.
  if(dismiss&&!disabled&&this.options.dismissOnBackdrop!==false){const b=shade.addComponent(Button);b.transition=Button.Transition.NONE;shade.on(Button.EventType.CLICK,()=>hud.actions.click(dismiss));}
  const {left,right,bottom,top}=this.bounds,placement=this.options.placement??'center',inset=Math.min(this.options.rightInset??0,Math.max(0,this.options.keepCenterClear?right-this.width-this.pad:right-left-this.width)),x=placement==='left'?left+this.width/2:placement==='right'?right-this.width/2-inset:(left+right)/2;
  const panel=hud.node('MenuSheet',hud.modal,x,(top+bottom-this.crestReserve)/2,this.width,height);this.shell=panel.addComponent(GoldPanelShell);
  this.shell.configure({title,width:this.width,height,hit:this.hit,unit:this.scale,mobile:this.mobile,variant:this.variant,crest:this.options.crest,centeredTitle:this.options.centeredTitle,dismissAction:dismiss,dismissDisabled:disabled,tabs:this.options.tabs,viewport:hud},action=>hud.actions.click(action));
  return {panel,height};
 }
 private scroll(panel:Node,y:number,height:number,contentHeight:number):Node {
  const width=this.width-2*this.pad,host=this.hud.node('MenuScroll',panel,0,y,width,height),viewport=this.hud.node('Viewport',host,0,0,width,height);
  viewport.addComponent(Mask).type=Mask.Type.GRAPHICS_RECT;
  const content=this.hud.node('Content',viewport,0,height/2,width,Math.max(height,contentHeight));content.getComponent(UITransform)!.setAnchorPoint(.5,1);
  const scroll=host.addComponent(ScrollView);scroll.content=content;scroll.horizontal=false;scroll.vertical=contentHeight>height;scroll.inertia=!this.hud.reducedMotion;scroll.elastic=!this.hud.reducedMotion;scroll.cancelInnerEvents=true;
  if(contentHeight>height){
   // A small live thumb gives long menus a visible scroll affordance.
   const trackHeight=height,thumbHeight=Math.max(24,height*height/contentHeight),track=this.hud.node('MenuScrollTrack',panel,this.width/2-7,y,3,trackHeight),g=track.addComponent(CompactGraphics);
   g.fillColor=C.button;g.rect(-1.5,-trackHeight/2,3,trackHeight);g.fill();
   const thumb=this.hud.node('MenuScrollThumb',track,0,trackHeight/2-thumbHeight/2,3,thumbHeight),t=thumb.addComponent(CompactGraphics);t.fillColor=C.gold;t.rect(-1.5,-thumbHeight/2,3,thumbHeight);t.fill();
   host.on(ScrollView.EventType.SCROLLING,()=>{const offset=Math.max(0,Math.min(1,scroll.getScrollOffset().y/(contentHeight-height)));thumb.setPosition(0,trackHeight/2-thumbHeight/2-offset*(trackHeight-thumbHeight));});
  }
  return content;
 }
 private face(node:Node,width:number,height:number,selected=false,disabled=false,quiet=false,visualOffset=0):Button {
  const inset=4*this.scale,w=Math.max(1,width-2*inset),h=Math.max(1,height-2*inset),b=node.addComponent(Button);b.transition=Button.Transition.NONE;b.interactable=!disabled;
  ButtonSurface.attach(node,{width:w,height:h,y:visualOffset,radius:6*this.scale,idleFill:quiet?undefined:C.button,border:selected&&!quiet?UI_FRAME_GOLD.metal:undefined,name:'MenuRowFace'});
  return b;
 }
 private choice(parent:Node,choice:MenuChoice,x:number,y:number,width:number,height=this.hit,primary=false,quiet=true,chrome=false){
  const n=this.hud.node(choice.action,parent,x,y,width,height);
  if(chrome&&!this.referenceScale){n.addComponent(GoldMenuButton).configure({label:choice.label,width,height,unit:this.scale,fontSize:this.mobile?27:18,primary:choice.primary??primary,disabled:choice.disabled,wrap:true},()=>this.hud.actions.click(choice.action));return n;}
  this.face(n,width,height,primary,!!choice.disabled,quiet);
  const label=this.text(n,choice.label,0,0,width-16,height,this.referenceScale?Math.max(this.mobile?14*this.scale:0,R.footerSize*this.referenceScale):this.mobile?27:18,primary?F.color('state.ready'):C.ink);label.horizontalAlign=Label.HorizontalAlign.CENTER;
  n.on(Button.EventType.CLICK,()=>this.hud.actions.click(choice.action));return n;
 }
 private rowHeight(row:MenuRow):number {
  const textWidth=this.rowTextWidth(row),labelH=this.textHeight(row.label,textWidth,this.referenceScale?Math.max(this.mobile?14*this.scale:0,R.rowSize*this.referenceScale):this.mobile?28:19),detailH=this.textHeight(row.detail,textWidth,this.referenceScale?Math.max(this.mobile?14*this.scale:0,20*this.referenceScale):this.mobile?26:16);
  return Math.max(this.hit,labelH+(detailH?detailH+4:0)+20);
 }
 private rowTextWidth(row:MenuRow):number {
  if(this.referenceScale){const r=this.referenceScale,end=row.toggle?this.width-(R.toggleRight+R.toggleWidth+14)*r:row.value?this.width-86*r:this.width-36*r;return Math.max(40,end-R.labelX*r);}
  const m=this.rowMetrics(row);
  return Math.max(40,this.width-2*this.pad-2*CONTENT.textInset*this.scale-m.iconSpace-m.accessoryWidth-CONTENT.accessoryGap*this.scale);
 }
 private rowMetrics(row:MenuRow){
  const id=row.action.split(':')[1],item=row.image?undefined:EQUIPMENT[id],icon=row.image??row.skin??row.icon??(item?equipmentIcon(item):undefined),iconSize=row.image?40*this.scale:row.skin?21*this.scale:this.mobile?38:28;
  return {item,icon,iconSize,iconSpace:icon?iconSize+CONTENT.iconGap*this.scale:0,accessoryWidth:row.toggle?52*this.scale:row.value?(this.mobile?70:48):row.selected?(this.mobile?102:74):20};
 }
 private row(parent:Node,row:MenuRow,y:number,height:number,visualOffset=0,referenceSwitch=false){
  const r=this.referenceScale,width=this.width-2*this.pad,n=this.hud.node(row.action,parent,0,y,width,height),{item,icon,iconSize,iconSpace,accessoryWidth}=this.rowMetrics(row),labelSize=r?Math.max(this.mobile?14*this.scale:0,R.rowSize*r):this.mobile?28:19,detailSize=r?Math.max(this.mobile?14*this.scale:0,20*r):this.mobile?26:16;
  // Reference switches keep their smaller artwork inside contiguous touch bands.
  // Text rows instead cover the complete measured title/detail block.
  this.face(n,width,referenceSwitch?Math.min(height,R.rowHeight*r):height,false,!!row.disabled,true,visualOffset);
  const textWidth=this.rowTextWidth(row),textX=r?-this.width/2+R.labelX*r+textWidth/2:-width/2+CONTENT.textInset*this.scale+iconSpace+textWidth/2,labelH=this.textHeight(row.label,textWidth,labelSize),detailH=this.textHeight(row.detail,textWidth,detailSize),total=labelH+(detailH?detailH+4:0);
  const label=this.text(n,row.label,textX,total/2-labelH/2,textWidth,labelH,labelSize,row.disabled?F.color('text.disabled'):row.tone?F.color(row.tone):item?F.color(qualityFeedbackRole(item.quality)):C.ink);
  label.node.name='MenuRowTitle';
  if(row.detail)this.text(n,row.detail,textX,-total/2+detailH/2,textWidth,detailH,detailSize,F.color('text.disabled')).node.name='MenuRowDetail';
  if(icon){const size=r?R.iconSize*r:iconSize,sprite=row.image?UiSkin.sprite(n,row.image,size,size):row.skin?UiSkin.asset(n,row.skin,size,size,false):UiSkin.sprite(n,'ui/icons/'+icon,size,size,row.disabled?F.color('text.disabled'):item?F.color(qualityFeedbackRole(item.quality)):C.gold);sprite.node.setPosition(r?-this.width/2+R.iconX*r:-width/2+CONTENT.textInset*this.scale+size/2,0);}
  if(row.toggle){const sw=r?R.toggleWidth*r:accessoryWidth,sh=r?R.toggleHeight*r:25*this.scale,x=r?this.width/2-R.toggleRight*r-sw/2:width/2-CONTENT.textInset*this.scale-sw/2,track=this.hud.node('MenuToggle',n,x,0,sw,sh);track.addComponent(GoldPanelToggle).configure({width:sw,height:sh,on:!!row.selected,label:row.value,unit:this.scale,variant:this.variant});}
  else{const value=row.value??(row.selected?'已开启':'›'),valueWidth=accessoryWidth;const state=this.text(n,value,width/2-(r?12:CONTENT.textInset*this.scale)-valueWidth/2,0,valueWidth,height,row.value||row.selected?this.mobile?24:16:this.mobile?32:24,row.disabled?F.color('text.disabled'):row.selected?F.color('state.running'):C.muted);state.horizontalAlign=Label.HorizontalAlign.RIGHT;state.node.name='MenuRowValue';}
  if(visualOffset)for(const child of n.children)if(child.name!=='MenuRowFace')child.setPosition(child.position.x,child.position.y+visualOffset);
  n.on(Button.EventType.CLICK,()=>{if(!row.disabled)this.hud.actions.click(row.action);});
 }
 private navigation(buttons:readonly MenuChoice[]){
  const back=buttons.find(b=>b.back)??buttons.find(b=>b.action==='close');
  const dismiss=this.options.dismissAction??back?.action,disabled=this.options.dismissDisabled??buttons.find(b=>b.action===dismiss)?.disabled??false;
  return {dismiss,disabled,actions:buttons.filter(b=>!b.back&&b.action!=='close'&&b.action!==this.options.dismissAction)};
 }
 show(title:string,body:string,buttons:MenuChoice[]){
  const {dismiss,disabled,actions:choices}=this.navigation(buttons);
  const width=this.width-2*this.pad,textWidth=width-2*CONTENT.textInset*this.scale,textHeight=this.textHeight(body,textWidth),introTop=CONTENT.introTop*this.scale,bodyHeight=body?introTop+textHeight+CONTENT.bodyBottom*this.scale:0,choiceGap=body&&choices.length?this.gap*1.5:0,heights=choices.map(b=>Math.max(this.hit,this.textHeight(b.label,width-16*this.scale,this.mobile?27:18)+16*this.scale));
  const choicesHeight=heights.reduce((s,h)=>s+h,0)+Math.max(0,choices.length-1)*this.gap,choiceViewHeight=Math.min(choicesHeight,this.maxHeight*.5),bodyViewHeight=Math.min(bodyHeight,this.maxHeight-this.header-this.pad-choiceGap-choiceViewHeight);
  const {panel,height}=this.surface(title,this.header+bodyViewHeight+choiceGap+choiceViewHeight+this.pad,dismiss,disabled);
  // Keep the first action visible even when help or introduction text is long.
  if(body){const content=this.scroll(panel,height/2-this.header-bodyViewHeight/2,bodyViewHeight,bodyHeight);this.text(content,body,0,-introTop-textHeight/2,textWidth,textHeight).verticalAlign=Label.VerticalAlign.TOP;}
  if(choices.length){const content=this.scroll(panel,-height/2+this.pad+choiceViewHeight/2,choiceViewHeight,choicesHeight),actions=this.hud.node('MenuActions',content,0,-choicesHeight/2,width,choicesHeight).addComponent(GoldMenuActions);
   actions.configure(choices.map((b,i)=>({...b,primary:b.primary??i===0,height:heights[i]})),{width,height:this.hit,gap:this.gap,unit:this.scale,visualGap:CONTENT.actionVisualGap*this.scale,fontSize:this.mobile?27:18,wrap:true},action=>this.hud.actions.click(action));}

 }
 showList(title:string,subtitle:string,rows:MenuRow[],footer:MenuChoice[]){
  if(this.referenceScale){this.showReferenceList(title,rows,footer);return;}
  const {dismiss,disabled,actions}=this.navigation(footer),width=this.width-2*this.pad;
  const subtitleWidth=width-2*CONTENT.textInset*this.scale,subtitleTextHeight=this.textHeight(subtitle,subtitleWidth),introTop=CONTENT.introTop*this.scale,subtitleHeight=subtitle?introTop+subtitleTextHeight:0,heights=rows.map(r=>this.rowHeight(r)),empty=rows.length?0:this.textHeight('暂无可选内容',subtitleWidth)+this.gap;
  const contentHeight=subtitleHeight+(subtitle?this.gap:0)+heights.reduce((s,h)=>s+h,0)+Math.max(0,rows.length-1)*this.gap+empty;
  // A footer with more than two actions becomes a vertical group so targets
  // never become narrow strips on phone screens.
  const stack=actions.length>2,footerRows=stack?actions.length:actions.length?1:0,footerHeight=footerRows?(this.hit+this.gap)*footerRows:0;
  const {panel,height}=this.surface(title,this.header+contentHeight+footerHeight+this.pad,dismiss,disabled),viewHeight=height-this.header-footerHeight-this.pad,content=this.scroll(panel,-height/2+this.pad+footerHeight+viewHeight/2,viewHeight,contentHeight);
  if(subtitle)this.text(content,subtitle,0,-introTop-subtitleTextHeight/2,subtitleWidth,subtitleTextHeight,this.font,F.color('text.disabled')).verticalAlign=Label.VerticalAlign.TOP;
  let y=subtitleHeight+(subtitle?this.gap:0);rows.forEach((r,i)=>{this.row(content,r,-y-heights[i]/2,heights[i]);y+=heights[i]+this.gap;if(i<rows.length-1)this.rule(content,-y+this.gap/2,width);});
  if(!rows.length)this.text(content,'暂无可选内容',0,-y-empty/2,subtitleWidth,empty,this.font,F.color('text.disabled'));
  if(actions.length){this.rule(panel,-height/2+this.pad+footerHeight-this.gap,width);const actionWidth=stack?width:(width-(actions.length-1)*this.gap)/actions.length;
   actions.forEach((b,i)=>this.choice(panel,b,stack?0:(i-(actions.length-1)/2)*(actionWidth+this.gap),-height/2+this.pad+this.hit/2+(stack?(actions.length-1-i)*(this.hit+this.gap):0),actionWidth,this.hit,b.action==='close'&&b.label.startsWith('继续'),true,true));}
 }
 private showReferenceList(title:string,rows:MenuRow[],footer:MenuChoice[]){
  const r=this.referenceScale,{dismiss,disabled,actions}=this.navigation(footer),referenceRows=rows.length===3&&rows.every(row=>row.toggle&&!row.detail),heights=rows.map(row=>Math.max(R.rowHeight*r,this.rowHeight(row))),centers:number[]=[];
  // Grouped switches use contiguous phone hit bands; visible rows retain the approved slots.
  rows.forEach((_,i)=>centers.push(Math.max((R.rowFirstY+i*R.rowStep)*r,i?centers[i-1]+heights[i-1]/2+(referenceRows?0:this.gap)+heights[i]/2:this.header+heights[i]/2)));
  const last=rows.length?centers[centers.length-1]+heights[heights.length-1]/2:this.header,{panel,height}=this.surface(title,this.referenceHeight,dismiss,disabled);
  const footerCenter=Math.min(R.footerY*r,height-this.pad-this.hit/2),bodyHeight=Math.max(this.hit,footerCenter-this.hit/2-this.gap-this.header),contentHeight=Math.max(bodyHeight,last-this.header),content=this.scroll(panel,height/2-this.header-bodyHeight/2,bodyHeight,contentHeight);
  rows.forEach((row,i)=>{this.row(content,row,-centers[i]+this.header,heights[i],referenceRows?centers[i]-(R.rowFirstY+i*R.rowStep)*r:0,referenceRows);if(i<rows.length-1)this.settingsRule(content,'row',referenceRows?this.header-(R.rowRuleFirstY+i*R.rowStep)*r:-((centers[i]+heights[i]/2+centers[i+1]-heights[i+1]/2)/2-this.header));});
  this.settingsRule(panel,'row',height/2-(referenceRows?(R.rowRuleFirstY+(rows.length-1)*R.rowStep)*r:Math.min(last+this.gap/2,footerCenter-this.hit/2-this.gap/2)));
  this.shell.footer(actions);
 }
}
