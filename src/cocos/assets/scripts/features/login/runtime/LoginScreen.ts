import {_decorator,BlockInputEvents,Color,Component,Label,Node,Sprite,UITransform,sys} from 'cc';
import type {Hud} from '../../../app/Hud';
import type {LoginState} from '../../../platform/TapLogin';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {UI_START_MENU} from '../../../shared/ui/UiChrome';
import {applyRpgFont} from '../../../shared/ui/RpgFont';
import {GoldMenuActions} from '../../../shared/ui/GoldMenuActions';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';

const {ccclass}=_decorator;
/** Coordinates measured from the approved 1844×853 ordinary-login concept. */
const DESIGN={width:1844,height:853,panelWidth:610,panelHeight:404,panelY:487,titleY:125.5,subtitleY:201,ruleY:251,headingY:335,statusY:424,hintY:478,actionY:560,footerY:635};

/** Provider-neutral presentation. Authentication remains in PlatformServices. */
@ccclass('LoginScreen')
export class LoginScreen extends Component {
 loaded=false;
 private hud:Hud;
 private released=false;
 private hidden=new Map<Node,boolean>();
 configure(hud:Hud,state:LoginState){
  this.hud=hud;hud.modalDisposers.add(this.release);this.node.addComponent(BlockInputEvents);
  const safe=sys.getSafeAreaRect(false),u=sys.isMobile?hud.touchTargetSize/48:1.5;
  const pad=12*u,left=-hud.width/2+Math.max(pad,safe.x),right=-hud.width/2+Math.min(hud.width-pad,safe.x+safe.width),bottom=-hud.height/2+Math.max(pad,safe.y),top=-hud.height/2+Math.min(hud.height-pad,safe.y+safe.height);
  const a=Math.min(hud.height/DESIGN.height,(right-left)/720,(top-bottom)/740),x=(left+right)/2;
  const artTop=Math.min(hud.height/2,top+20*a),y=(sourceY:number)=>artTop-sourceY*a;
  const base=this.node.addComponent(CompactGraphics);base.fillColor=C.background;base.rect(-hud.width/2,-hud.height/2,hud.width,hud.height);base.fill();
  const background=UiSkin.sprite(this.node,'ui/loading/stonebridge-valley',hud.width,hud.height);background.node.name='LoginValley';
  const backgroundReady=UiSkin.frame('ui/loading/stonebridge-valley',0,background.node).then(frame=>{
   if(this.released||!this.isValid)return;const aspect=frame.originalSize.width/frame.originalSize.height,width=Math.max(hud.width,hud.height*aspect);background.node.getComponent(UITransform)!.setContentSize(width,width/aspect);
  }).catch(()=>{});
  // The landscape has its own dark foreground. No full-screen sepia tint.
  const shadow=hud.node('LoginTitleShadow',this.node,x,y(163),460*a,210*a).addComponent(CompactGraphics);
  for(let i=0;i<10;i++){shadow.fillColor=new Color(C.background.r,C.background.g,C.background.b,6+i);shadow.ellipse(0,0,(230-i*5)*a,(105-i*3)*a);shadow.fill();}
  const title=this.text('LoginGameTitle','剑与火',x,y(DESIGN.titleY),280*a,108*a,90*a,C.gold),subtitle=this.text('LoginGameSubtitle','破晓之战',x,y(DESIGN.subtitleY),220*a,54*a,44*a,C.gold);
  UiSkin.asset(hud.node('LoginTitleArt',this.node,x,y(DESIGN.titleY),272*a,97*a),UI_START_MENU.title,272*a,97*a,false,a);
  UiSkin.asset(hud.node('LoginSubtitleArt',this.node,x,y(DESIGN.subtitleY),200*a,54*a),UI_START_MENU.subtitle,200*a,54*a,false,a);
  UiSkin.asset(hud.node('LoginTitleRule',this.node,x,y(DESIGN.ruleY),276*a,23*a),UI_START_MENU.rule,276*a,23*a,false,a);
  const panel=hud.node('LoginPanel',this.node,x,y(DESIGN.panelY),DESIGN.panelWidth*a,DESIGN.panelHeight*a);UiSkin.panel(panel,DESIGN.panelWidth*a,DESIGN.panelHeight*a,C.inset,'panel',false,a);
  this.text('LoginHeading','登录',x,y(DESIGN.headingY),500*a,64*a,48*a,C.gold);
  UiSkin.asset(hud.node('LoginHeadingRule',this.node,x,y(380),480*a,8*a),'settings-title-rule-v11',480*a,8*a,false,a);
  const status=state.error==='TIMEOUT'?'登录超时':state.error==='CANCELLED'?'登录已中断':state.error==='PLATFORM_UNAVAILABLE'?'登录暂不可用':state.error==='EMPTY_CODE'?'登录未完成':'暂时无法连接';
  const hint=state.error==='PLATFORM_UNAVAILABLE'?'请关闭游戏后重新打开':state.error==='CANCELLED'||state.error==='EMPTY_CODE'?'请点击下方按钮重试':'请检查网络后重试';
  this.text('LoginStatus',status,x,y(DESIGN.statusY),530*a,54*a,34*a,C.ink);
  this.text('LoginHint',hint,x,y(DESIGN.hintY),530*a,44*a,28*a,C.muted);
  const hit=Math.max(hud.touchTargetSize,48*u),actions=hud.node('LoginActions',this.node,x,y(DESIGN.actionY),450*a,hit).addComponent(GoldMenuActions);
  actions.configure([{label:'重试登录',action:'auth:retry',primary:true}],{width:450*a,height:hit,unit:u,visualHeight:82*a,pixelScale:a,fontSize:38*a},action=>hud.actions.click(action));
  this.text('LoginProgressSafe','本地进度已保留',x,y(DESIGN.footerY),500*a,44*a,26*a,C.muted);
  void Promise.all([backgroundReady,actions.ready,...[UI_START_MENU.title,UI_START_MENU.subtitle,UI_START_MENU.rule].map(id=>UiSkin.frame('ui/quiet-bronze/'+id,0,this.node))]).then(()=>{
   if(!this.isValid||this.released)return;title.node.active=false;subtitle.node.active=false;this.loaded=actions.loaded;
  }).catch(()=>{console.warn('Login artwork unavailable; readable labels retained.');});
  this.conceal();
 }
 private text(name:string,value:string,x:number,y:number,w:number,h:number,size:number,color:Color){
  const label=this.hud.text(this.node,value,x,y,w,size,color,h);label.node.name=name;label.horizontalAlign=Label.HorizontalAlign.CENTER;label.enableWrapText=false;applyRpgFont(label);return label;
 }
 private conceal(){for(const child of this.hud.root.children){if(child===this.hud.modal)continue;if(!this.hidden.has(child))this.hidden.set(child,child.active);child.active=false;}}
 lateUpdate(){if(!this.released)this.conceal();}
 private release=()=>{if(this.released)return;this.released=true;this.enabled=false;for(const[node,active]of this.hidden)if(node.isValid)node.active=active;this.hidden.clear();this.hud?.modalDisposers.delete(this.release);};
 onDestroy(){this.release();}
}

export function showLoginScreen(hud:Hud,state:LoginState){
 hud.clearModal();hud.modal.setSiblingIndex(hud.root.children.length-1);
 const root=hud.node('LoginScreen',hud.modal,0,0,hud.width,hud.height);root.addComponent(LoginScreen).configure(hud,state);
}
