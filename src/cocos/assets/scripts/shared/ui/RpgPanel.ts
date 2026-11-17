import {viewportMetrics} from '../../platform/ViewportMetrics';
import {CompactMask as Mask} from './CompactMask';
import {CompactGraphics} from './CompactGraphics';
import {BlockInputEvents,ButtonComponent as Button,Color,Graphics,Label,Node,ScrollView,ScrollBar,Sprite,SpriteFrame,Texture2D,builtinResMgr,sys,UITransform} from 'cc';
import type {GameSession} from '../../core/GameSession';
import type {Hud} from '../../app/Hud';
import {UiSkin} from './UiSkin';
import {UI_COLORS as C} from './UiTheme';
import {FeedbackView as F} from './FeedbackView';
import {applyRpgFont} from './RpgFont';
import {UiChrome,UI_PANEL_HEADER as H} from './UiChrome';
import {GoldPanelHeader} from './GoldPanelHeader';
import {PreparationSkin as P} from './PreparationSkin';
import {DoubleGoldFrame} from './DoubleGoldFrame';
import {PREPARATION_DESIGN as D} from './PreparationTheme';
import {ButtonSurface} from './ButtonSurface';
export type RpgTab='character'|'equipment'|'profession'|'allocation'|'skills'|'forge';
export interface RpgFooterAction {label:string;action:string;enabled?:boolean;primary?:boolean;run?:()=>void;back?:boolean}
let scrollbarFrame:SpriteFrame|undefined;
export class RpgPanel {
 private readonly header:GoldPanelHeader;
 readonly panel:Node;readonly width:number;readonly height:number;readonly hit:number;readonly gap:number;readonly font:number;readonly minFont:number;readonly margin:number;readonly bodyTop:number;readonly bodyBottom:number;readonly footerY:number;readonly scale:number;readonly mobile=sys.isMobile;
 constructor(readonly hud:Hud,readonly game:GameSession,active:RpgTab,name:string,readonly expanded=false){
  hud.clearModal();const backdrop=hud.node('RpgBackdrop',hud.modal,0,0,hud.width,hud.height);backdrop.addComponent(BlockInputEvents);const dark=backdrop.addComponent(CompactGraphics);dark.fillColor=new Color(C.background.r,C.background.g,C.background.b,D.shell.backdropAlpha);dark.rect(-hud.width/2,-hud.height/2,hud.width,hud.height);dark.fill();
  const dismiss=backdrop.addComponent(Button);dismiss.transition=Button.Transition.NONE;backdrop.on(Button.EventType.CLICK,()=>hud.actions.click('close'));
  const safe=sys.getSafeAreaRect(false),left=-hud.width/2+safe.x,right=left+safe.width,bottom=-hud.height/2+safe.y,top=bottom+safe.height;
  const ratio=hud.height/Math.max(1,viewportMetrics.windowSize.height/Math.max(1,viewportMetrics.devicePixelRatio));
  // Floating on every device. A narrower safe area may make the dialog taller,
  // while the outside world and the rounded metal lip remain visible.
  const availableH=top-bottom-D.shell.phoneVerticalGutterLogical*ratio,preferredH=Math.min(D.shell.phoneHeightLogical*ratio,availableH);
  this.width=this.mobile?Math.min(right-left-D.shell.phoneHorizontalGutterLogical*ratio,preferredH*D.canvas.width/D.canvas.height):Math.min(D.shell.desktopWidthLogical*ratio,right-left-D.shell.desktopHorizontalGutterLogical*ratio,(top-bottom-D.shell.desktopVerticalGutterLogical*ratio)*D.canvas.width/D.canvas.height);
  this.height=this.mobile?preferredH:this.width*D.canvas.height/D.canvas.width;this.scale=this.width/D.canvas.width;
  this.hit=D.interaction.hitLogical*ratio;this.gap=D.interaction.gapLogical*ratio;this.minFont=D.typography.minimumLogical*ratio;this.font=Math.max(D.typography.body*this.scale,this.minFont);this.margin=D.shell.margin*this.scale;
  const shell=hud.node('RpgDialog',hud.modal,(left+right)/2,(top+bottom)/2,this.width,this.height);shell.addComponent(BlockInputEvents);
  // The quest tracker and this dialog share the same rounded, two-lip metal component.
  const skinScale=D.frame.pixelScaleLogical*ratio;UiSkin.panel(shell,this.width,this.height,C.background,'panel',false,skinScale,D.frame.asset);
  this.panel=hud.node(name,shell,0,0,this.width,this.height);this.panel.addComponent(BlockInputEvents);
  const mask=this.panel.addComponent(Mask);mask.type=Mask.Type.GRAPHICS_STENCIL;const clip=mask.subComp as Graphics,inset=D.frame.clipInsetSource*skinScale;
  clip.clear();clip.roundRect(-this.width/2+inset,-this.height/2+inset,this.width-2*inset,this.height-2*inset,D.frame.clipRadiusSource*skinScale);clip.fill();
  shell.getComponent(DoubleGoldFrame)!.bringBorderToFront();
  if(this.expanded){const material=hud.node('PreparationMaterial',this.panel,0,0,this.width,this.height),g=material.addComponent(CompactGraphics);g.fillColor=C.background;g.rect(-this.width/2,-this.height/2,this.width,this.height);g.fill();P.art(this,material,'surface',0,0,D.canvas.width,this.height/this.scale);}
  // Small native scrolls stay inside the metal band and clear the existing controls.
  if(!this.expanded){const engraving=hud.node('RpgDialogInnerEngraving',shell,0,0,this.width-4*ratio,this.height-4*ratio),unit=.4*ratio;engraving.setScale(unit,unit,1);UiChrome.frame(engraving,(this.width-4*ratio)/unit,(this.height-4*ratio)/unit);}
  const reference=this.referenceLayout,headerUnit=ratio,headerY=this.height/2-H.height/2*ratio,visualY=0,headerBottom=this.height/2-H.height*ratio;
  // Slim visible chrome; independent 48px targets still clear the first body row.
  if(this.expanded)P.art(this,this.panel,'header',0,this.height/2-H.height/2*headerUnit,D.canvas.width,H.height*headerUnit/this.scale);
  const brand=this.expanded?P.art(this,this.panel,'logo',this.x(D.header.logoX),headerY+visualY,D.header.logoWidth,D.header.logoHeight):UiSkin.asset(this.panel,'rpg-logo-v2',66*this.scale,22*this.scale,false);if(!this.expanded)brand.node.setPosition(this.x(104),headerY+visualY);
  if(this.expanded){P.separator(this,this.panel,this.x(D.header.leftSeparatorX),headerY+visualY,D.header.separatorHeight);P.separator(this,this.panel,this.x(D.header.rightSeparatorX),headerY+visualY,D.header.separatorHeight);}
  const tabs:[RpgTab,string,string][]=[['character','人物','attributes'],['equipment','装备','inventory'],['profession','职业','profession'],['allocation','加点','allocation:attributes'],['skills','技能','checks'],['forge','培养','forge']];
  tabs.forEach(([id,title,action],i)=>{const x=this.x((this.expanded?D.header.tabStart:184)+i*((this.expanded?D.header.tabWidth:68)+Math.max(D.header.tabMinimumGap,this.gap/this.scale))),w=(this.expanded?D.header.tabWidth:68)*this.scale,n=this.tab(this.panel,title,x,headerY,w,action,false,visualY);n.children.filter(c=>c.getComponent(Label)).forEach(c=>{const label=c.getComponent(Label)!;label.fontSize=(this.expanded?D.typography.navigation:16)*this.scale*this.textScale;label.lineHeight=label.fontSize*1.3;label.color=id===active?F.color(this.expanded?D.colorRoles.selected:'state.running'):this.expanded?F.color(D.colorRoles.ink):C.ink;});if(id===active){const rule=this.expanded?P.art(this,n,'active',0,visualY-(reference?D.header.underlineOffset*this.scale:12*ratio),D.header.underlineWidth,D.header.underlineHeight):UiSkin.asset(n,'rpg-active-rule-v4',68*this.scale,7.8*this.scale,false);if(!this.expanded)rule.node.setPosition(0,visualY-(reference?D.header.underlineOffset*this.scale:12*ratio));}});
  if(reference)for(const n of this.panel.children.filter(n=>tabs.some(t=>t[2]===n.name)))n.getComponent(UITransform)!.height=D.header.referenceHitHeight*this.scale;
  this.header=GoldPanelHeader.attach(this.panel,{width:this.width,unit:ratio,hit:this.hit,centerY:headerY,viewport:hud,action:'close'},()=>hud.actions.click('close'));
  const coinX=Math.min(this.x(D.header.coinX),this.width/2-this.hit-20*ratio-(D.header.goldX-D.header.coinX+D.header.goldWidth/2)*this.scale);
  const coin=UiSkin.asset(this.panel,D.artwork.coin,D.header.coinSize*this.scale,D.header.coinSize*this.scale,false);coin.node.setPosition(coinX,headerY+visualY);const gold=this.text(this.panel,String(game.state.player.gold),coinX+(D.header.goldX-D.header.coinX)*this.scale,headerY+visualY,D.header.goldWidth*this.scale,26*this.scale,C.ink,D.header.goldFont*this.scale);gold.enableWrapText=false;gold.overflow=Label.Overflow.SHRINK;
  this.footerY=-this.height/2+this.gap+this.hit/2;this.bodyTop=headerBottom-this.gap;this.bodyBottom=this.footerY+this.hit/2+this.gap;
  this.divider(this.panel,this.height/2-H.height*headerUnit);this.divider(this.panel,this.bodyBottom-this.gap/2);
 }
 get textScale(){return this.expanded?1:.92;}
 x(value:number){return -this.width/2+value*this.scale;}
 y(value:number){return this.height/2-value*this.scale;}
 get bodyHeight(){return this.bodyTop-this.bodyBottom;}
 get bodyY(){return (this.bodyTop+this.bodyBottom)/2;}
 get contentTop(){return (this.height/2-this.bodyTop)/this.scale;}
 get contentBottom(){return (this.height/2-this.bodyBottom)/this.scale;}
 /** Keep approved body coordinates below the current shared Header and above the footer. */
 referenceY(value:number){return this.contentTop+(value-D.shell.contentTop)*(this.contentBottom-this.contentTop)/(D.shell.contentBottom-D.shell.contentTop);}
 get referenceLayout(){return !this.mobile&&this.width/this.hit>=D.shell.referenceMinWidthLogical/D.interaction.hitLogical;}
 column(left:number,w:number,name:string){const n=this.surface(this.panel,this.x(left+w/2),this.bodyY,w*this.scale,this.bodyHeight,C.background);n.name=name;return n;}
 text(parent:Node,value:string,x:number,y:number,w:number,h=38,color=C.ink,size=this.font){const actual=Math.max(size*this.textScale,this.minFont),tone=this.expanded&&color===C.ink?F.color(D.colorRoles.ink):this.expanded&&color===C.gold?F.color(D.colorRoles.accent):color,label=this.hud.text(parent,value,x,y,w,actual,tone,Math.max(h,actual*D.typography.lineHeight));applyRpgFont(label);label.lineHeight=actual*D.typography.lineHeight;label.enableWrapText=true;label.overflow=Label.Overflow.CLAMP;return label;}
 surface(parent:Node,x:number,y:number,w:number,h:number,fill=C.panel){const n=this.hud.node('RpgSurface',parent,x,y,w,h),g=n.addComponent(CompactGraphics);g.fillColor=this.expanded?C.background:fill;g.rect(-w/2,-h/2,w,h);g.fill();if(this.expanded){P.art(this,n,'surface',0,0,w/this.scale,h/this.scale);g.strokeColor=C.line;g.lineWidth=.45*this.scale;g.moveTo(-w/2,-h/2);g.lineTo(-w/2,h/2);g.stroke();}else{UiSkin.asset(n,'rpg-material-v3',w,h,false).color=new Color(255,255,255,235);UiSkin.asset(n,'rpg-inner-frame-v3',w,h,false);}return n;}
 divider(parent:Node,y:number){if(this.expanded){P.art(this,parent,'shell-rule',0,y,D.canvas.width,D.decoration.ruleHeight);return;}const s=UiSkin.asset(parent,'rpg-section-divider-v3',this.width,8*this.scale,false);s.node.setPosition(0,y);}
 drape(parent:Node,w:number,h:number){if(this.expanded){P.art(this,parent,'smoke',w/2-D.decoration.smokeWidth/2*this.scale,h/2-D.decoration.smokeHeight/2*this.scale,D.decoration.smokeWidth,D.decoration.smokeHeight);return;}const s=UiSkin.asset(parent,'rpg-drape-v3',44*this.scale,h,false);s.node.setPosition(w/2-22*this.scale,0);}
 tab(parent:Node,title:string,x:number,y:number,w:number,action:string,selected=false,offset=0,run?:()=>void,plate=false,tone:'gold'|'quiet'='gold'){const n=this.hud.node(action,parent,x,y,w,this.hit),b=n.addComponent(Button);b.transition=Button.Transition.NONE;let artwork:Node|undefined;if(plate){const s=UiSkin.asset(n,selected?tone==='quiet'?'rpg-tab-selected-v3':'rpg-button-gold-v3':'rpg-button-dark-v3',w,26*this.scale,true);s.node.setPosition(0,offset);artwork=s.node;}this.feedback(n,w-4*this.scale,22*this.scale,offset,artwork);const l=this.text(n,title,0,offset,w-12,28*this.scale,plate&&selected&&tone!=='quiet'?C.dark:C.ink,15*this.scale);l.horizontalAlign=Label.HorizontalAlign.CENTER;n.on(Button.EventType.CLICK,()=>run?run():this.hud.actions.click(action));return n;}
 feedback(node:Node,width:number,height:number,y=0,after?:Node){return ButtonSurface.attach(node,{width:Math.max(1,width-4*this.scale),height:Math.max(1,height-4*this.scale),y,radius:3*this.scale,overlay:true,after});}
 button(parent:Node,title:string,x:number,y:number,w:number,action:string,enabled=true,selected=false,h=this.hit,run?:()=>void,style?:'primary'|'footer'|'catalog'|'step'|'attribute'){
  const n=this.hud.node(action,parent,x,y,w,h),b=n.addComponent(Button);b.transition=Button.Transition.NONE;b.interactable=enabled;const vh=style==='step'?24*this.scale:style==='primary'||style==='footer'?Math.min(h,D.footer.buttonHeight*this.scale):h,vw=style==='step'?26*this.scale:w;
  if(style==='attribute'){const skin=UiSkin.asset(n,'rpg-attribute-plus-v4',25.6*this.scale,24.7*this.scale,false);if(!enabled)skin.color=F.color('text.disabled',220);}else if(style!=='catalog'){const skin=this.expanded?P.art(this,n,style==='primary'&&enabled?'button-gold':'button-dark',0,0,vw/this.scale,vh/this.scale,true):UiSkin.asset(n,style==='primary'&&enabled?'rpg-button-gold-v3':'rpg-button-dark-v3',vw,vh,true);if(!enabled)skin.color=new Color(255,255,255,185);}
  if(selected&&style!=='primary'){const sw=Math.max(1,vw-4*this.scale),sh=Math.max(1,vh-4*this.scale);if(this.expanded)P.art(this,n,'card-selected',0,0,sw/this.scale,sh/this.scale,true);else UiSkin.asset(n,'rpg-selection-frame-v3',sw,sh,true);}
  if(style==='attribute')this.feedback(n,25.6*this.scale,24.7*this.scale,0,n.children[0]);
  else if(style!=='catalog')this.feedback(n,vw,vh,0,n.children[0]);
  else this.feedback(n,vw,Math.min(h,32*this.scale));
  const l=this.text(n,style==='attribute'?'':title,0,0,vw-8,vh-4,enabled?(style==='primary'?C.dark:C.ink):F.color('text.disabled'),style==='step'?21*this.scale:(this.expanded&&(style==='primary'||style==='footer')?D.typography.footer:15)*this.scale);l.horizontalAlign=Label.HorizontalAlign.CENTER;
  if(style==='footer'||style==='primary'){l.enableWrapText=false;l.overflow=Label.Overflow.SHRINK;}
  n.on(Button.EventType.CLICK,()=>{if(enabled){if(run)run();else this.hud.actions.click(action);}});return n;
 }
 rule(parent:Node,y:number,w:number){const g=this.hud.node('RpgRule',parent,0,y,w,2).addComponent(CompactGraphics);g.strokeColor=C.line;g.lineWidth=.65*this.scale;g.moveTo(-w/2,0);g.lineTo(-3*this.scale,0);g.moveTo(3*this.scale,0);g.lineTo(w/2,0);g.stroke();g.strokeColor=C.gold;const r=1.6*this.scale;g.moveTo(0,r);g.lineTo(r,0);g.lineTo(0,-r);g.lineTo(-r,0);g.close();g.stroke();}
 scroll(parent:Node,x:number,y:number,w:number,h:number,contentHeight:number){return RpgPanel.scroll(this.hud,parent,x,y,w,h,contentHeight,this.scale);}
 static scroll(hud:Hud,parent:Node,x:number,y:number,w:number,h:number,contentHeight:number,scale:number){
  const host=hud.node('RpgScroll',parent,x,y,w,h),viewport=hud.node('Viewport',host,0,0,w,h);viewport.addComponent(Mask).type=Mask.Type.GRAPHICS_RECT;
  const content=hud.node('Content',viewport,0,h/2,w,Math.max(h,contentHeight));content.getComponent(UITransform)!.setAnchorPoint(.5,1);
  const overflow=contentHeight>h+scale,scroll=host.addComponent(ScrollView);scroll.content=content;scroll.horizontal=false;scroll.vertical=overflow;scroll.cancelInnerEvents=true;
  if(overflow){
   // Outside the clipped content: the last inventory column keeps its full hit area.
   const track=hud.node('RpgScrollbar',host,w/2+3.5*scale,0,2*scale,h),g=track.addComponent(CompactGraphics);g.fillColor=new Color(C.line.r,C.line.g,C.line.b,100);g.roundRect(-scale,-h/2,2*scale,h,scale);g.fill();
   if(!scrollbarFrame){scrollbarFrame=new SpriteFrame();scrollbarFrame.packable=false;scrollbarFrame.texture=builtinResMgr.get<Texture2D>('white-texture');}
   const handle=hud.node('ScrollHandle',track,0,0,2*scale,24*scale).addComponent(Sprite);handle.spriteFrame=scrollbarFrame;handle.sizeMode=Sprite.SizeMode.CUSTOM;handle.color=C.gold;
   const bar=track.addComponent(ScrollBar);bar.handle=handle;bar.direction=1;bar.enableAutoHide=false;scroll.verticalScrollBar=bar;
  }
  return content;
 }
 progress(parent:Node,x:number,y:number,w:number,h:number,value:number,max:number,health=false){const host=this.hud.node('RpgProgress',parent,x,y,w,h),g=host.addComponent(CompactGraphics);g.fillColor=C.dark;g.strokeColor=C.gold;g.lineWidth=.6*this.scale;g.roundRect(-w/2,-h/2,w,h,2*this.scale);g.fill();g.stroke();if(health){const s=UiSkin.asset(host,'bar-health-fill',w-2*this.scale,h-2*this.scale,false);F.bar(s,value,max,'health.player');}else{g.fillColor=C.gold;g.roundRect(-w/2+this.scale,-h/2+this.scale,Math.max(.1,(w-2*this.scale)*Math.min(1,value/Math.max(1,max))),h-2*this.scale,this.scale);g.fill();}return host;}
 footer(status:string,buttons:RpgFooterAction[],statusAction?:string){
  const back=buttons.find(b=>b.back)??buttons.find(b=>b.action==='close');
  if(back)this.header.setAction(back.action,back.run??(()=>this.hud.actions.click(back.action)),back.enabled!==false);
  buttons=buttons.filter(b=>!b.back&&b.action!=='close');
  const long=buttons.some(b=>b.primary&&b.label.length>=8),widths=buttons.map((b,i)=>buttons.length===3?(this.expanded?D.footer.widths[i]:long?[108,164,126][i]:[102,114,124][i])*this.scale:Math.min(140*this.scale,(this.width*.76-(buttons.length-1)*this.gap)/buttons.length)),gaps=buttons.length===3?(this.expanded?D.footer.gaps:long?[12,12]:[10,22]).map(n=>n*this.scale):buttons.slice(1).map(()=>this.gap),total=widths.reduce((a,b)=>a+b,0)+gaps.reduce((a,b)=>a+b,0);let x=this.width/2-(this.expanded?D.footer.rightInset:14)*this.scale-total;
  const visualOffset=0,fire=UiSkin.asset(this.panel,D.artwork.campfire,(this.expanded?D.footer.fire.width:38)*this.scale,(this.expanded?D.footer.fire.height:34)*this.scale,false);fire.node.setPosition(this.x(this.expanded?D.footer.fire.x:40),this.footerY+visualOffset);
  const statusX=this.expanded?D.footer.statusX:62,sw=Math.max(90*this.scale,x-this.x(statusX)-10*this.scale),statusHost=this.hud.node(statusAction??'FooterStatus',this.panel,this.x(statusX)+sw/2,this.footerY,sw,this.hit);
  const units=Array.from(status).reduce((n,c)=>n+(/\s/.test(c)?.3:c==='·'||c==='，'?.35:c.charCodeAt(0)<128?.54:1),0),statusFont=Math.max(D.footer.statusMinFont,Math.min(D.footer.statusMaxFont,sw/this.scale/Math.max(1,units))),textWidth=units*statusFont*this.scale;
  this.text(statusHost,status,0,visualOffset,sw,(textWidth>sw?statusFont*2.6:28)*this.scale,C.ink,statusFont*this.scale);
  if(statusAction){const b=statusHost.addComponent(Button);b.transition=Button.Transition.NONE;statusHost.on(Button.EventType.CLICK,()=>this.hud.actions.click(statusAction));}
  const flourishLeft=Math.max(this.x(194.5),this.x(statusX)+textWidth+8*this.scale),flourishRight=x-10*this.scale;
  if(flourishRight-flourishLeft>70*this.scale){const line=UiSkin.asset(this.panel,D.artwork.footerRule,flourishRight-flourishLeft,11.4*this.scale,false);line.node.name='FooterFlourish';line.node.setPosition((flourishLeft+flourishRight)/2,this.footerY+visualOffset);}
  buttons.forEach((b,i)=>{const node=this.button(this.panel,b.label,x+widths[i]/2,this.footerY,widths[i],b.action,b.enabled!==false,!!b.primary,this.hit,b.run,b.primary?'primary':'footer');
   node.children.forEach(c=>c.setPosition(c.position.x,c.position.y+visualOffset,c.position.z));x+=widths[i]+(gaps[i]??0);
  });
 }
}
