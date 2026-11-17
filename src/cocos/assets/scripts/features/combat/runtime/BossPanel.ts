import {BlockInputEvents,ButtonComponent as Button,Label,Node,ScrollView,UITransform,sys} from 'cc';
import {CompactMask as Mask} from '../../../shared/ui/CompactMask';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import type {Hud} from '../../../app/Hud';
import type {GameSession} from '../../../core/GameSession';
import {BossDirectory,type BossEntry,bossClock,BOSS_LEVEL_WINDOW} from '../common/BossDirectory';
import {availableRoutes} from '../../automation/common/AutomationRoute';
import {AREAS} from '../../world/data/WorldData';
import {GoldPanelShell} from '../../../shared/ui/GoldPanelShell';
import {GoldMenuButton} from '../../../shared/ui/GoldMenuButton';
import {UI_FRAME_LAYOUT,UI_GOLD_PANEL_CONTENT} from '../../../shared/ui/UiChrome';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {applyRpgFont} from '../../../shared/ui/RpgFont';
import {bossPortrait,bossStatus} from './BossPresentation';
import {bossText as tr} from '../locales/bosses';
import {bossRewardSummary} from './BossRewardPresentation';
import {ButtonSurface} from '../../../shared/ui/ButtonSurface';

type RowView={node:Node;entry:BossEntry;selection:Node;primary:Label;secondary:Label};
/** Compact authored shell and native scrolling; the footer never scrolls away. */
export class BossPanel {
 private root!:Node;private range!:Label;private count!:Label;private detail!:Label;
 private follow!:GoldMenuButton;private go!:GoldMenuButton;private rows=new Map<string,RowView>();
 private selected='';private shape='';private readonly width:number;private readonly height:number;
 constructor(private readonly hud:Hud,private readonly game:GameSession,private readonly directory:BossDirectory,selected=''){
  this.width=hud.width;this.height=hud.height;this.selected=selected;this.update();
 }
 get valid(){return this.root?.isValid&&this.root.parent&&this.width===this.hud.width&&this.height===this.hud.height;}
 get selectedKey(){return this.selected;}
 update(){
  const entries=this.directory.list(this.game),shape=entries.map(e=>e.key).sort().join('|');
  if(!entries.some(e=>e.key===this.selected))this.selected=entries[0]?.key??'';
  if(!this.root?.isValid||shape!==this.shape){this.shape=shape;this.build(entries);}
  const level=this.game.state.progression.level;
  this.range.string=tr('range',{min:Math.max(1,level-BOSS_LEVEL_WINDOW),max:level+BOSS_LEVEL_WINDOW});this.count.string=tr('count',{count:entries.length});
  entries.forEach((entry,i)=>{const row=this.rows.get(entry.key)!,status=bossStatus(entry),y=-(i*60+26)*this.hud.uiUnit;if(row.node.position.y!==y)row.node.setPosition(0,y);row.entry=entry;row.primary.string=status.primary;row.secondary.string=status.secondary;F.tint(row.primary,status.role);F.tint(row.secondary,status.role);row.selection.active=entry.key===this.selected;});
  const row=entries.find(e=>e.key===this.selected),reachable=row&&availableRoutes(this.game,AREAS,row.area).has(row.area);
  this.follow.setLabel(tr(row?.followed?'followed':'follow'));this.follow.setInteractable(!!row);
  this.go.setLabel(tr(row?.state==='cooldown'?'early':'go'));this.go.setInteractable(!!reachable);
  this.detail.string=!row?'':(!reachable?tr('blocked'):tr(row.spawn.respawnSeconds&&['waiting','cooldown'].includes(row.state)?'waitDetail':row.state==='cooldown'?'cooldown':row.state==='ready'?'entrance':'approach',{place:row.place,time:bossClock(row.remaining)}))+(bossRewardSummary(row.spawn)?'\n'+bossRewardSummary(row.spawn):'');
 }
 private text(parent:Node,name:string,value:string,x:number,y:number,w:number,size:number,role:'text.normal'|'text.secondary'|'text.preparation'|'text.preparationAccent',h=18):Label {
  const u=this.hud.uiUnit,l=this.hud.text(parent,value,x*u,y*u,w*u,size*u,F.color(role),h*u);l.node.name=name;applyRpgFont(l);l.enableWrapText=false;l.lineHeight=size*u*1.3;l.overflow=Label.Overflow.CLAMP;return l;
 }
 private build(entries:BossEntry[]){
  this.hud.clearModal();this.rows.clear();const u=this.hud.uiUnit,w=306*u,listHeight=(entries.length?Math.min(entries.length,2)*52+(Math.min(entries.length,2)-1)*8:56)*u,h=(entries.length===1?238:entries.length?298:242)*u;
  const textWidth=w/u-2*(UI_FRAME_LAYOUT.padding+UI_GOLD_PANEL_CONTENT.textInset),ruleWidth=w-2*UI_GOLD_PANEL_CONTENT.ruleInset*u,metadataWidth=96,metadataX=(textWidth-metadataWidth)/2;
  // Keep the original row skin and touch band; only its visual content follows the shared text inset.
  const rowLeft=-textWidth/2+UI_FRAME_LAYOUT.gap,rowRight=textWidth/2-UI_FRAME_LAYOUT.gap,labelLeft=rowLeft+41,statusWidth=56,statusX=rowRight-statusWidth/2;
  const veil=this.hud.node('BossListVeil',this.hud.modal,0,0,this.hud.width,this.hud.height),shade=veil.addComponent(CompactGraphics);F.ink(shade,'text.outline','fill',42);shade.rect(-this.hud.width/2,-this.hud.height/2,this.hud.width,this.hud.height);shade.fill();veil.addComponent(BlockInputEvents);veil.addComponent(Button).transition=Button.Transition.NONE;veil.on(Button.EventType.CLICK,()=>this.hud.actions.click('close'));
  const safe=sys.getSafeAreaRect(false),right=Math.min(this.hud.width/2-29*u,-this.hud.width/2+safe.x+safe.width-8*u),top=this.hud.height/2-56*u;
  this.root=this.hud.node('BossTargetPanel',this.hud.modal,right-w/2,top-h/2,w,h);
  const shell=this.root.addComponent(GoldPanelShell);shell.configure({title:tr('title'),width:w,height:h,hit:48*u,unit:u,mobile:true,crest:true,dismissAction:'close',titleRuleY:55*u,viewport:this.hud},a=>this.hud.actions.click(a));
  const title=this.root.getChildByName('MenuTitle')?.getComponent(Label);if(title)F.tint(title,'text.preparationAccent');
  this.range=this.text(this.root,'BossLevelRange','',-metadataX,h/u/2-70,metadataWidth,9.5,'text.secondary');
  this.count=this.text(this.root,'BossTargetCount','',metadataX,h/u/2-70,metadataWidth,9,'text.secondary');this.count.horizontalAlign=Label.HorizontalAlign.RIGHT;
  const host=this.hud.node('BossListScroll',this.root,0,h/2-82*u-listHeight/2,266*u,listHeight),viewport=this.hud.node('Viewport',host,0,0,266*u,listHeight);viewport.addComponent(Mask).type=Mask.Type.GRAPHICS_RECT;
  const contentHeight=Math.max(listHeight,entries.length*60*u-8*u),content=this.hud.node('BossRows',viewport,0,listHeight/2,266*u,contentHeight);content.getComponent(UITransform)!.setAnchorPoint(.5,1);
  const scroll=host.addComponent(ScrollView);scroll.content=content;scroll.horizontal=false;scroll.vertical=contentHeight>listHeight;scroll.elastic=!this.hud.reducedMotion;scroll.inertia=!this.hud.reducedMotion;scroll.cancelInnerEvents=true;
  if(!entries.length){const l=this.text(content,'BossEmpty',tr('empty',{min:Math.max(1,this.game.state.progression.level-5),max:this.game.state.progression.level+5}),0,-28,textWidth,10,'text.secondary');l.horizontalAlign=Label.HorizontalAlign.CENTER;}
  entries.forEach((entry,i)=>{
   const row=this.hud.node('BossRow:'+entry.key,content,0,-(i*60+26)*u,264*u,52*u),button=row.addComponent(Button);button.transition=Button.Transition.NONE;row.addComponent(BlockInputEvents);
   const background=UiSkin.sprite(row,'ui/boss-awareness/row',264*u,52*u);
   ButtonSurface.attach(row,{width:256*u,height:44*u,radius:4*u,overlay:true,after:background.node});
   const selection=UiSkin.sprite(row,'ui/boss-awareness/row-selected',260*u,48*u).node;selection.name='BossRowSelection';selection.active=entry.key===this.selected;
   UiSkin.sprite(row,bossPortrait(entry),32*u,32*u).node.setPosition((rowLeft+16)*u,0);
   this.text(row,'BossName',entry.name,labelLeft+51,8,102,12,'text.preparation');this.text(row,'BossPlace',`${entry.place} · Lv${entry.level}`,labelLeft+61,-11,122,9,'text.secondary');
   const primary=this.text(row,'BossAvailability','',statusX,8,statusWidth,10,'text.secondary'),secondary=this.text(row,'BossKind','',statusX,-10,statusWidth,8,'text.secondary');primary.horizontalAlign=secondary.horizontalAlign=Label.HorizontalAlign.RIGHT;
   this.rows.set(entry.key,{node:row,entry,selection,primary,secondary});row.on(Button.EventType.CLICK,()=>{this.selected=entry.key;this.update();});
  });
  if(contentHeight>listHeight){
   const thumbHeight=Math.max(16*u,listHeight*listHeight/contentHeight),track=this.hud.node('BossScrollTrack',this.root,137*u,host.position.y,2*u,listHeight),g=track.addComponent(CompactGraphics);F.ink(g,'text.secondary','fill',55);g.rect(-u,-listHeight/2,2*u,listHeight);g.fill();
   const thumb=this.hud.node('BossScrollThumb',track,0,listHeight/2-thumbHeight/2,2*u,thumbHeight),ink=thumb.addComponent(CompactGraphics);F.ink(ink,'text.preparationAccent','fill',190);ink.rect(-u,-thumbHeight/2,2*u,thumbHeight);ink.fill();
   host.on(ScrollView.EventType.SCROLLING,()=>{const n=Math.max(0,Math.min(1,scroll.getScrollOffset().y/(contentHeight-listHeight)));thumb.setPosition(0,listHeight/2-thumbHeight/2-n*(listHeight-thumbHeight));});
  }
  const footerTop=82*u+listHeight;shell.divider(this.root,'row',h/2-footerTop-6*u,ruleWidth);
  this.detail=this.text(this.root,'BossSelectionDetail','',0,h/u/2-footerTop/u-22,textWidth,9,'text.secondary',30);this.detail.horizontalAlign=Label.HorizontalAlign.CENTER;this.detail.enableWrapText=true;
  const actionY=h/2-footerTop-72*u;
  const action=(name:string,x:number,primary:boolean)=>{const n=this.hud.node(name,this.root,x*u,actionY,127*u,48*u),b=n.addComponent(GoldMenuButton);b.configure({label:'',width:127*u,height:48*u,unit:u,visualHeight:30*u,fontSize:12*u,primary},()=>this.hud.actions.click(name+':'+this.selected));return b;};
  this.follow=action('boss-follow',-67.5,false);this.go=action('boss-go',67.5,true);
 }
}
