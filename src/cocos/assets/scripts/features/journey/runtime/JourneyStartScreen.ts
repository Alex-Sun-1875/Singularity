import {trainingText} from '../../debug/locales';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {_decorator,BlockInputEvents,Color,Component,Graphics,Label,Node,sys} from 'cc';
import type {Hud} from '../../../app/Hud';
import {BUILD_INFO} from '../../../app/BuildInfo';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {UI_START_MENU as R} from '../../../shared/ui/UiChrome';
import {applyRpgFont} from '../../../shared/ui/RpgFont';
import {GoldMenuActions} from '../../../shared/ui/GoldMenuActions';

const {ccclass}=_decorator;

/** Approved narrow menu. World/HUD ownership is restored when any action opens. */
@ccclass('JourneyStartScreen')
export class JourneyStartScreen extends Component {
 loaded=false;
 private hud:Hud;
 private hidden=new Map<Node,boolean>();
 private released=false;
 configure(hud:Hud,loading:boolean,failure:string,guestTest:boolean){
  this.hud=hud;hud.modalDisposers.add(this.release);
  const u=sys.isMobile?hud.touchTargetSize/R.hit:1.5,safe=sys.getSafeAreaRect(false),pad=12*u;
  const left=-hud.width/2+Math.max(pad,safe.x),right=-hud.width/2+Math.min(hud.width-pad,safe.x+safe.width),bottom=-hud.height/2+Math.max(pad,safe.y),x=(left+right)/2;
  const vertical=hud.height/R.height,art=Math.min(vertical,hud.width/R.width,R.maxWidth*u/R.buttonWidth),width=R.buttonWidth*art,visualH=R.buttonHeight*art,hit=Math.max(hud.touchTargetSize,R.hit*u),step=Math.max(R.buttonStep*vertical,hit+R.gap*u);
  this.node.addComponent(BlockInputEvents);
  const shade=this.node.addComponent(CompactGraphics);shade.fillColor=new Color(C.background.r,C.background.g,C.background.b,108);shade.rect(-hud.width/2,-hud.height/2,hud.width,hud.height);shade.fill();
  const titleY=hud.height/2-R.titleY*vertical,subtitleY=hud.height/2-R.subtitleY*vertical;
  const title=this.text('StartTitle','剑与火',x,titleY,R.titleWidth*art,R.titleHeight*art,90*art,C.gold),subtitle=this.text('StartSubtitle','破晓之战',x,subtitleY,R.subtitleWidth*art,R.subtitleHeight*art,44*art,C.gold);
  UiSkin.asset(hud.node('StartWordmark',this.node,x,titleY,R.titleWidth*art,R.titleHeight*art),R.title,R.titleWidth*art,R.titleHeight*art,false,art);
  UiSkin.asset(hud.node('StartSubtitleArt',this.node,x,subtitleY,R.subtitleWidth*art,R.subtitleHeight*art),R.subtitle,R.subtitleWidth*art,R.subtitleHeight*art,false,art);
  UiSkin.asset(hud.node('StartTitleRule',this.node,x,hud.height/2-R.ruleY*vertical,R.ruleWidth*art,R.ruleHeight*art),R.rule,R.ruleWidth*art,R.ruleHeight*art,false,art);
  const footerY=Math.max(bottom+12*u,hud.height/2-R.footerY*vertical),lastMinimum=footerY+R.footerClearance*u+hit/2,first=Math.min(R.buttonFirstY*vertical,hud.height/2-lastMinimum-3*step);
  const entries=[{action:'begin',label:loading?'正在准备…':failure?'重新载入':'继续旅途'},{action:'new',label:'新建旅程'},{action:'settings',label:'设置'},{action:'training:enter',label:trainingText('title')}];
  const actions=hud.node('MenuActions',this.node,x,hud.height/2-first-1.5*step,width,4*hit+3*(step-hit)).addComponent(GoldMenuActions);
  actions.configure(entries.map((entry,i)=>({...entry,primary:i===0,disabled:loading})),{width,height:hit,gap:step-hit,unit:u,visualHeight:visualH,pixelScale:art,fontSize:Math.max(14*u,R.labelSize*art)},action=>hud.actions.click(action));
  this.text('StartVersion',`v${BUILD_INFO.version}${guestTest?' · 游客测试 · 仅本机存档':''}`,x,footerY,Math.max(width,hud.width-48*u),24*u,guestTest?11*u:12*u,C.muted);
  void Promise.all([actions.ready,...[R.title,R.subtitle,R.rule].map(id=>UiSkin.frame('ui/quiet-bronze/'+id,0,this.node))]).then(()=>{if(this.isValid&&!this.released){title.node.active=false;subtitle.node.active=false;this.loaded=actions.loaded;}}).catch(()=>{console.warn('Title menu chrome unavailable; wordmark text retained.');});
  this.conceal();
 }
 private text(name:string,value:string,x:number,y:number,w:number,h:number,size:number,color:Color,parent=this.node){
  const label=this.hud.text(parent,value,x,y,w,size,color,h);label.node.name=name;label.horizontalAlign=Label.HorizontalAlign.CENTER;applyRpgFont(label);return label;
 }
 private conceal(){
  for(const child of this.hud.root.children){
   if(child===this.hud.modal||child.name==='JourneyLoading'||child.name==='CampaignScene')continue;
   if(!this.hidden.has(child))this.hidden.set(child,child.active);
   child.active=false;
  }
 }
 lateUpdate(){if(!this.released)this.conceal();}
 private release=()=>{if(this.released)return;this.released=true;this.enabled=false;for(const [node,active]of this.hidden)if(node.isValid)node.active=active;this.hidden.clear();this.hud?.modalDisposers.delete(this.release);};
 onDestroy(){this.release();}
}

export function showJourneyStart(hud:Hud,loading:boolean,failure:string,guestTest:boolean){
 hud.clearModal();hud.modal.setSiblingIndex(hud.root.children.length-1);
 const root=hud.node('JourneyStartScreen',hud.modal,0,0,hud.width,hud.height);
 root.addComponent(JourneyStartScreen).configure(hud,loading,failure,guestTest);
}
