import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {BlockInputEvents,Color,EventTouch,Graphics,Label,Node,Sprite,Tween,UITransform,sys,tween} from 'cc';
import type {Hud} from '../../../app/Hud';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';

const INK=C.ink,GOLD=C.gold,MUTED=C.muted;
const TIPS=[
 '沿道路和石阶探索。地图上的标记可帮助你找到实际可走的入口。',
 '弓按住蓄力、松手放箭。技能可按住预瞄、拖动选点，再松手释放。',
 '脱战后可随时更换装备，无需返回检查点。已领取的遗物和商人的余货会随旅途保存。',
 '检定失败仍可继续探索。留意信件、侧门，以及人物愿意说出的另一条线索。',
];

/** Original artwork; the caller supplies real asset/actor loading progress. */
export class LoadingScreen {
 private pageRoot:Node|null=null;private pageVisible=false;private pageMessage=false;
 private root:Node|null=null;private background:Sprite|null=null;private percentage:Label|null=null;private message:Label|null=null;private tip:Label|null=null;
 private fill:Graphics|null=null;private spinner:Node|null=null;private visible=false;private progress=0;private status='正在准备旅途';private width=0;private height=0;private generation=0;private artworkPending=false;
 constructor(private readonly hud:Hud){}
 show(progress:number,message='正在准备旅途'):void {
  const resume=!!this.root?.isValid&&!this.root.active;
  this.visible=true;this.progress=progress<0?-1:Math.max(0,Math.min(1,progress));this.status=message;
  if(!this.root?.isValid||this.root.parent!==this.hud.root||this.width!==this.hud.width||this.height!==this.hud.height)this.build();
  if(this.root){this.root.active=true;this.root.setSiblingIndex(this.hud.root.children.length-1);}if(resume&&this.spinner)tween(this.spinner).by(2.8,{angle:-360}).repeatForever().start();this.loadArtwork();this.refresh();
 }
 /** Call after Hud.resize(); rebuilds safely if Hud replaced its root children. */
 update(_dt=0):void {if(this.visible){if(!this.root?.isValid||this.root.parent!==this.hud.root||this.width!==this.hud.width||this.height!==this.hud.height)this.build();this.root?.setSiblingIndex(this.hud.root.children.length-1);}if(this.pageVisible)this.coverPage();}
 /** Keep the complete previous page visible while blocking its stale controls. */
 coverPage(message=false):void {
  this.pageVisible=true;this.pageMessage=this.pageMessage||message;
  const size=this.pageRoot?.getComponent(UITransform);
  if(!this.pageRoot?.isValid||this.pageRoot.parent!==this.hud.root||size?.width!==this.hud.width||size?.height!==this.hud.height){
   this.pageRoot?.destroy();this.pageRoot=this.hud.node('PreparingPage',this.hud.root,0,0,this.hud.width,this.hud.height);this.pageRoot.addComponent(BlockInputEvents);
  }
  this.pageRoot.setSiblingIndex(this.hud.root.children.length-1);
  if(this.pageMessage&&!this.pageRoot.getChildByName('PageLoadingStatus')){
   const u=this.hud.touchTargetSize/48,status=this.hud.node('PageLoadingStatus',this.pageRoot,0,0,250*u,64*u);UiSkin.panel(status,250*u,64*u);
   this.hud.text(status,'正在准备页面…',0,0,224*u,16*u,INK,48*u).horizontalAlign=Label.HorizontalAlign.CENTER;
  }
 }
 uncoverPage():void {this.pageVisible=false;this.pageMessage=false;this.pageRoot?.destroy();this.pageRoot=null;}
 hide():void {this.visible=false;this.generation++;this.artworkPending=false;if(this.background)this.background.spriteFrame=null;if(this.root)UiSkin.releaseOwner(this.root);if(this.root?.isValid)this.root.active=false;if(this.spinner)Tween.stopAllByTarget(this.spinner);}
 destroy():void {this.uncoverPage();this.visible=false;this.generation++;if(this.spinner)Tween.stopAllByTarget(this.spinner);if(this.root?.isValid)this.root.destroy();this.root=null;}
 private build():void {
  if(this.spinner)Tween.stopAllByTarget(this.spinner);if(this.root?.isValid)this.root.destroy();
  const hud=this.hud,w=hud.width,h=hud.height,mobile=sys.isMobile,portrait=w<h;this.width=w;this.height=h;
  const root=hud.node('JourneyLoading',hud.root,0,0,w,h);this.root=root;
  const black=root.addComponent(CompactGraphics);black.fillColor=C.background;black.rect(-w/2,-h/2,w,h);black.fill();
  for(const type of [Node.EventType.TOUCH_START,Node.EventType.TOUCH_MOVE,Node.EventType.TOUCH_END,Node.EventType.TOUCH_CANCEL])root.on(type,(event:EventTouch)=>{event.propagationStopped=true;});
  const picture=hud.node('ValleyArtwork',root,0,0,w,h);this.background=picture.addComponent(Sprite);this.background.sizeMode=Sprite.SizeMode.CUSTOM;this.background.trim=false;
  this.generation++;this.artworkPending=false;this.loadArtwork();
  const shade=hud.node('ReadingShade',root,0,0,w,h),g=shade.addComponent(CompactGraphics);
  // The artwork already has a dark foreground; a narrow native overlay protects text on wider phones.
  for(let i=0;i<48;i++){g.fillColor=new Color(0,0,0,Math.round(225*(1-i/47)));g.rect(-w/2,-h/2+i*h/192,w,h/192);g.fill();}
  const bottom=-h/2,tipY=bottom+(portrait?180:mobile?114:94),progressY=bottom+(portrait?112:mobile?57:48),pad=Math.max(38,w*.035),contentW=portrait?w-56:Math.min(980,w-pad*2-140);
  this.tip=hud.text(root,TIPS[0],portrait?0:-35,tipY,contentW,portrait?22:mobile?27:19,INK,portrait?90:mobile?82:58);this.tip.horizontalAlign=Label.HorizontalAlign.CENTER;this.tip.node.name='LoadingTip';
  this.message=hud.text(root,'',0,bottom+(mobile?27:23),Math.min(w-90,800),mobile?21:14,MUTED,30);this.message.horizontalAlign=Label.HorizontalAlign.CENTER;this.message.node.name='LoadingStage';
  const trackW=portrait?w-76:Math.min(480,w*.37),track=hud.node('RealProgress',root,0,progressY,trackW,2),tg=track.addComponent(CompactGraphics);tg.strokeColor=new Color(C.line.r,C.line.g,C.line.b,150);tg.lineWidth=1;tg.moveTo(-trackW/2,0);tg.lineTo(trackW/2,0);tg.stroke();this.fill=hud.node('ProgressFill',track,0,0,trackW,2).addComponent(CompactGraphics);
  const statusY=portrait?bottom+78:tipY-1,spinner=hud.node('LoadingCompass',root,portrait?45:w/2-pad-22,statusY,54,54);this.spinner=spinner;const sg=spinner.addComponent(CompactGraphics);sg.strokeColor=GOLD;sg.lineWidth=1.6;sg.circle(0,0,16);sg.stroke();sg.strokeColor=C.ink;sg.lineWidth=2.4;sg.arc(0,0,11,Math.PI*.08,Math.PI*1.43,false);sg.stroke();for(let i=0;i<4;i++){const a=i*Math.PI/2;sg.moveTo(Math.cos(a)*19,Math.sin(a)*19);sg.lineTo(Math.cos(a)*25,Math.sin(a)*25);sg.stroke();}
  this.percentage=hud.text(root,'',portrait?-30:w/2-pad-95,statusY,84,mobile?28:19,GOLD,45);this.percentage.horizontalAlign=Label.HorizontalAlign.RIGHT;this.percentage.node.name='LoadingPercentage';
  tween(spinner).by(2.8,{angle:-360}).repeatForever().start();this.refresh();
 }
 private loadArtwork():void {
  const sprite=this.background,root=this.root,token=this.generation;if(!sprite||!root?.isValid||sprite.spriteFrame||this.artworkPending)return;this.artworkPending=true;
  void UiSkin.frame('ui/loading/stonebridge-valley',0,root).then(frame=>{if(this.root!==root||!root.isValid||token!==this.generation)return;sprite.spriteFrame=frame;const aspect=frame.originalSize.width/frame.originalSize.height,coverW=Math.max(this.width,this.height*aspect);sprite.node.getComponent(UITransform)!.setContentSize(coverW,coverW/aspect);}).catch(()=>{}).finally(()=>{if(token===this.generation)this.artworkPending=false;});
 }
 private refresh():void {
  if(!this.root?.isValid)return;const known=this.progress>=0;
  if(this.percentage)this.percentage.string=known?`${Math.round(this.progress*100)}%`:'';
  if(this.message)this.message.string=this.status;
  if(this.tip)this.tip.string=this.width<this.height?'横屏游玩，地图与背包会更清晰。':TIPS[Math.min(TIPS.length-1,Math.floor(Math.max(0,this.progress)*TIPS.length))];
  if(this.fill){const width=this.fill.node.getComponent(UITransform)!.width;this.fill.clear();if(known){this.fill.strokeColor=GOLD;this.fill.lineWidth=2;this.fill.moveTo(-width/2,0);this.fill.lineTo(-width/2+width*this.progress,0);this.fill.stroke();}}
 }
}
