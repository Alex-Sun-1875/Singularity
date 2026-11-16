import {viewportMetrics} from '../../../platform/ViewportMetrics';
import {ButtonComponent as Button,Color,Graphics,Label,Node,sys,UIOpacity,Vec2} from 'cc';
import type {Hud} from '../../../app/Hud';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {applyRpgFont} from '../../../shared/ui/RpgFont';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {currentLocale} from '../../../shared/i18n/Localization';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {cinematicText} from '../locales';
import {cinematicLayout,CINEMATIC_STYLE as S} from '../common/CinematicLayout';

/** Subtitle-only overlay; independent from the game's framed menus and HUD. */
export class CinematicSubtitles {
 readonly root:Node;readonly layout:ReturnType<typeof cinematicLayout>;
 private opacity:UIOpacity;private speaker:Label;private caption:Label;private controls:Label[]=[];
 private continueLabel?:Label;private continueArrow?:Graphics;
 private continueGeometry?:{labelX:number;arrowX:number;arrowY:number;width:number;height:number;gap:number};
 constructor(private hud:Hud){
  const w=hud.width,h=hud.height,cssHeight=viewportMetrics.windowSize.height/Math.max(1,viewportMetrics.devicePixelRatio),scale=h/Math.max(1,cssHeight),safe=sys.getSafeAreaRect(false);
  this.layout=cinematicLayout(w,h,{left:safe.x,right:Math.max(0,w-safe.x-safe.width),top:Math.max(0,h-safe.y-safe.height),bottom:safe.y});
  // Phone targets use real logical-screen units. Desktop follows the same design scale.
  this.layout.hit=Math.max(this.layout.hit,48*scale);
  const l=this.layout,u=l.unit;
  this.root=hud.node('CinematicSubtitles',hud.root,0,0,w,h);this.opacity=this.root.addComponent(UIOpacity);
  const gradient=hud.node('SubtitleGradient',this.root,0,-h/2+S.gradientHeight*u/2,w,S.gradientHeight*u);
  UiSkin.sprite(gradient,'ui/cinematics/subtitle-gradient',w,S.gradientHeight*u);
  this.speaker=this.label('Speaker','',l.captionX,l.speakerY,l.captionWidth,S.speaker*u,26*u,C.gold);
  this.caption=this.label('Subtitle','',l.captionX,l.captionY,l.captionWidth,S.caption*u,S.lineHeight*2*u,F.color('text.normal'));
  this.caption.lineHeight=S.lineHeight*u;this.caption.enableWrapText=false;
  this.control('SkipStory',cinematicText('ui.skip'),l.skipX,l.skipY,'campaign:skip');
  this.control('ContinueStory',cinematicText('ui.continue'),l.continueX,l.continueY,'campaign:next',true);
 }
 private label(name:string,value:string,x:number,y:number,width:number,size:number,height:number,color:Color){
  const n=this.hud.node(name,this.root,x-this.hud.width/2,this.hud.height/2-y,width,height),l=n.addComponent(Label);
  l.string=value;l.fontSize=size;l.lineHeight=size*1.5;l.color=color;l.horizontalAlign=Label.HorizontalAlign.CENTER;
  l.verticalAlign=Label.VerticalAlign.CENTER;l.overflow=Label.Overflow.CLAMP;l.enableWrapText=false;
  l.enableShadow=true;l.shadowColor=new Color(0,0,0,230);l.shadowBlur=3*this.layout.unit;l.shadowOffset=new Vec2(0,-this.layout.unit);
  applyRpgFont(l);return l;
 }
 private control(name:string,value:string,x:number,y:number,action:string,chevron=false){
  const l=this.layout,u=l.unit,n=this.hud.node(name,this.root,x-this.hud.width/2,this.hud.height/2-y,l.controlWidth,l.hit);
  const button=n.addComponent(Button);button.transition=Button.Transition.NONE;
  const text=this.label(name+'Label',value,x,y,l.controlWidth,S.controlSize*u,26*u,chevron?C.gold:F.color('text.normal'));
  // Visual text nodes never receive the button's events or enlarge its footprint.
  text.node.parent=n;text.node.setPosition(0,0);
  if(chevron){
   this.continueLabel=text;
   this.continueArrow=this.hud.node('ContinueChevron',n,0,0,10*u,16*u).addComponent(CompactGraphics);
   this.layoutContinue();
  }
  const tint=(pressed:boolean)=>{text.color=pressed?F.color('state.ready'):chevron?C.gold:F.color('text.normal');if(chevron)this.drawContinueArrow(text.color);};
  n.on(Node.EventType.TOUCH_START,()=>tint(true));n.on(Node.EventType.TOUCH_CANCEL,()=>tint(false));n.on(Node.EventType.TOUCH_END,()=>tint(false));
  n.on(Node.EventType.MOUSE_ENTER,()=>tint(true));n.on(Node.EventType.MOUSE_LEAVE,()=>tint(false));
  n.on(Button.EventType.CLICK,()=>this.hud.actions.click(action));this.controls.push(text);
 }
 private layoutContinue(){
  if(!this.continueLabel||!this.continueArrow)return;
  const u=this.layout.unit,size=S.controlSize*u;
  // Ink bounds of the bundled rpg-serif-v2.ttf, in em. Cocos 3.8.8 centers
  // alphabetic TTF labels with baseline 0.37em below the node center. The
  // asymmetric shadow padding also shifts the rendered ink in its quad.
  // Keep the arrow on that ink center, independent of glyph › metrics.
  const ink=currentLocale()==='en'?{advance:4.56,left:.054,right:4.518,bottom:-.017,top:.777}:{advance:2,left:.029,right:1.967,bottom:-.084,top:.839};
  const width=6*u,gap=8*u,textWidth=(ink.right-ink.left)*size;
  this.continueGeometry={labelX:-(width+gap)/2-((ink.left+ink.right-ink.advance)/2)*size,
   arrowX:(textWidth+gap)/2,arrowY:((ink.top+ink.bottom)/2-.37)*size-(this.continueLabel.enableShadow?this.continueLabel.shadowOffset.y:0),
   width,height:(ink.top-ink.bottom)*size*.78,gap};
  this.continueLabel.node.setPosition(this.continueGeometry.labelX,0);
  this.continueArrow.node.setPosition(this.continueGeometry.arrowX,this.continueGeometry.arrowY);
  this.drawContinueArrow(this.continueLabel.color);
 }
 private drawContinueArrow(color:Color){
  const g=this.continueArrow,geometry=this.continueGeometry;if(!g||!geometry)return;
  const {width,height}=geometry;g.clear();g.strokeColor=color;g.lineWidth=1.25*this.layout.unit;
  g.lineCap=Graphics.LineCap.ROUND;g.lineJoin=Graphics.LineJoin.ROUND;
  g.moveTo(-width/2,height/2);g.lineTo(width/2,0);g.lineTo(-width/2,-height/2);g.stroke();
 }
 show(speaker:string,text:string){this.speaker.string=speaker;this.caption.string=text;}
 refreshControls(){this.controls[0].string=cinematicText('ui.skip');this.controls[1].string=cinematicText('ui.continue');this.layoutContinue();}
 fade(amount:number,captionAmount=1){this.opacity.opacity=Math.round(255*Math.max(0,Math.min(1,amount)));this.caption.color=F.color('text.normal',Math.round(255*captionAmount));}
 inspect(){const l=this.layout,u=l.unit;return {speaker:this.speaker.string,text:this.caption.string,fontSize:this.caption.fontSize/u,lineHeight:this.caption.lineHeight/u,
  subtitle:{x:l.captionX/u,y:l.captionY/u,width:l.captionWidth/u},controls:this.controls.map(c=>c.string),continueGeometry:this.continueGeometry,hit:l.hit/u,layout:l};}
 destroy(){this.root.destroy();}
}
