import {ButtonComponent as Button,Color,Graphics,Label,Node,ScrollView,UITransform,Vec2,sys} from 'cc';
import {GComponent,GRoot} from 'fairygui-cc';
import type {Hud} from '../../../app/Hud';
import type {GameSession} from '../../../core/GameSession';
import type {Point} from '../../../core/Contracts';
import {viewportMetrics} from '../../../platform/ViewportMetrics';
import {AtlasUi as UI} from '../../../shared/ui/AtlasUi';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {CompactMask as Mask} from '../../../shared/ui/CompactMask';
import {bindButtonFeedback} from '../../../shared/ui/ButtonFeedback';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {applyRpgFont,fitRpgLine} from '../../../shared/ui/RpgFont';
import {RpgPanel} from '../../../shared/ui/RpgPanel';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {GoldPanelHeader} from '../../../shared/ui/GoldPanelHeader';
import {PREPARATION_DESIGN as D} from '../../../shared/ui/PreparationTheme';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {MapPanel,type MapFocus} from '../../navigation/runtime/MapPanel';
import {journalEntries,journalEntry,defaultJournalEntry,journalMarkers,type JournalEntry,type JournalTarget,type JournalAction} from '../common/AdventureJournal';
import {journalUiText as T} from '../locales/AdventureJournalUiText';

export type JournalMode='journal'|'map';
export type JournalFilter='current'|'completed'|'locations';
export interface JournalOpenOptions {mode?:JournalMode;entryId?:string;filter?:JournalFilter;area?:string}
type Layout={x:number;y:number;w:number;h:number;side:number;bodyX:number;bodyY:number;bodyW:number;bodyH:number;rightX:number;rightW:number};
type ScrollState={scroll:ScrollView;key:string};
type DocumentBlock={kind:'title'|'status'|'heading'|'text'|'update'|'button'|'space';text:string;height:number;font?:number;action?:string;disabled?:boolean;current?:boolean};

/** One session-local book: browsing never starts a route or changes quest state. */
export class AdventureJournalPanel {
 private game:GameSession|undefined;private visited:Record<string,boolean>={};private entries:JournalEntry[]=[];
 private mode:JournalMode='journal';private filter:JournalFilter='current';private selected='';private targetId='';
 private customPoint:{area:string;point:Point;label:string}|undefined;
 private expanded=new Set<number>([1]);private futureOpen=false;private offsets=new Map<string,number>();
 private hideCompleted=false;private sideExpanded=new Set<number>();private replayExpanded=new Set<number>();
 private root:GRoot|null=null;private page:GComponent|null=null;private tree:GComponent|null=null;private right:GComponent|null=null;
 private mapHost:GComponent|null=null;private header:GComponent|null=null;
 private leftScroll:ScrollState|undefined;private paperScroll:ScrollState|undefined;
 private unit=1;private pixelUnit=1;private layout:Layout|undefined;private layoutKey='';private modelKey='';private epoch=0;
 private readonly dispose=()=>this.hide();
 constructor(private readonly hud:Hud,private readonly map:MapPanel){}
 get currentMode():JournalMode{return this.mode;}

 show(game:GameSession,visited:Record<string,boolean>,options:JournalOpenOptions={}):void {
  const changedGame=this.game!==game;
  if(changedGame){this.hide();this.game=game;this.mode='journal';this.filter='current';this.selected='';this.targetId='';this.customPoint=undefined;this.expanded=new Set([1]);this.sideExpanded.clear();this.replayExpanded.clear();this.hideCompleted=false;this.futureOpen=false;this.offsets.clear();}
  const requested=options.entryId??(options.area?'area:'+options.area:undefined);
  this.visited=visited;const entries=journalEntries(game),preview=(requested??this.selected).startsWith('area:')?journalEntry(game,requested??this.selected):null;
  if(preview&&!entries.some(entry=>entry.id===preview.id))entries.push(preview);
  const key=JSON.stringify([entries,this.hud.mapTravel]),changedModel=key!==this.modelKey;this.entries=entries;this.modelKey=key;
  if(options.mode)this.mode=options.mode;if(options.filter)this.filter=options.filter;
  if(requested&&entries.some(entry=>entry.id===requested)){this.selected=requested;this.revealSelection(true);this.targetId='';this.customPoint=undefined;}
  if(!entries.some(entry=>entry.id===this.selected)){this.selected=defaultJournalEntry(game);this.revealSelection(true);}
  if(!this.root||this.root.isDisposed){this.hud.clearModal();this.build();return;}
  if(this.layoutKey!==this.signature()){this.rebuild();return;}
  if(changedModel||requested||options.mode||options.filter){this.saveScrolls();this.renderHeader();this.renderTree(!!requested);this.renderRight();}
 }
 handle(action:string):boolean {
  if(!action.startsWith('journal:'))return false;
  if(!this.game||!this.root||this.root.isDisposed)return true;
  this.saveScrolls();
  if(action==='journal:walk-mark'){if(!this.hud.mapTravel.busy&&this.customPoint?.area===this.game.state.area)this.hud.actions.navigate({...this.customPoint,point:{...this.customPoint.point}});return true;}
  if(action.startsWith('journal:mode:')){const mode=action.slice(13);if(mode==='journal'||mode==='map')this.mode=mode;this.renderHeader();this.renderTree(true);this.renderRight();return true;}
  if(action.startsWith('journal:filter:')){const filter=action.slice(15);if(filter==='current'||filter==='completed'||filter==='locations')this.filter=filter;this.renderTree();return true;}
  if(action==='journal:hide-completed'){this.hideCompleted=!this.hideCompleted;this.filter='current';this.renderTree();return true;}
  if(action.startsWith('journal:group:')){const [,kind,chapterId]=action.slice(8).split(':'),chapter=Number(chapterId),set=kind==='side'?this.sideExpanded:this.replayExpanded;if(Number.isInteger(chapter)){if(set.has(chapter))set.delete(chapter);else set.add(chapter);this.renderTree();}return true;}
  if(action==='journal:future'){this.futureOpen=!this.futureOpen;this.renderTree();return true;}
  if(action.startsWith('journal:marker:')){try{const [entryId,markerId]=action.slice(15).split(':').map(value=>decodeURIComponent(value));this.select(entryId,true,markerId);}catch{}return true;}
  if(action.startsWith('journal:chapter:')){
   const chapter=Number(action.slice(16));if(!Number.isInteger(chapter))return true;
   if(this.selected==='chapter:'+chapter&&this.expanded.has(chapter))this.expanded.delete(chapter);else this.expanded.add(chapter);
   this.select('chapter:'+chapter,false);return true;
  }
  if(action.startsWith('journal:entry:')){try{this.select(decodeURIComponent(action.slice(14)));}catch{}return true;}
  if(action.startsWith('journal:target:')){try{const id=decodeURIComponent(action.slice(15));if(this.entry()?.targets.some(target=>target.id===id)){this.targetId=id;this.mode='map';this.renderHeader();this.renderRight();}}catch{}return true;}
  return true;
 }
 hide():void {
  this.saveScrolls();this.epoch++;this.hud.modalDisposers.delete(this.dispose);this.map.unmount();
  if(this.root&&!this.root.isDisposed){this.root.node.active=false;this.root.node.removeFromParent();this.root.dispose();}
  this.root=null;this.page=null;this.tree=null;this.right=null;this.header=null;this.mapHost=null;this.leftScroll=undefined;this.paperScroll=undefined;
 }
 refreshLayout():void {if(this.root&&!this.root.isDisposed&&this.layoutKey!==this.signature())this.rebuild();}
 /** Read-only view information used by runtime inspection. */
 inspect(){return {mode:this.mode,filter:this.filter,hideCompleted:this.hideCompleted,entryId:this.selected,targetId:this.targetId,upcoming:this.entry()?.status==='upcoming',visible:!!this.root&&!this.root.isDisposed,layout:this.layout,unit:this.unit};}
 private signature():string {const s=sys.getSafeAreaRect(false),m=viewportMetrics.menuRect;return [this.hud.width,this.hud.height,s.x,s.y,s.width,s.height,m?.left,m?.top,m?.right,m?.bottom].join(':');}
 private entry():JournalEntry|undefined {return this.entries.find(entry=>entry.id===this.selected);}
 private revealSelection(adjustFilter=false):void {
  const entry=this.entry();if(!entry)return;
  this.expanded.add(entry.chapter);if(entry.chapter>3)this.futureOpen=true;
  if(entry.kind==='side')this.sideExpanded.add(entry.chapter);if(entry.kind==='replay')this.replayExpanded.add(entry.chapter);
  if(entry.status==='completed')this.hideCompleted=false;
  if(adjustFilter)this.filter=entry.kind==='area'?'locations':entry.status==='completed'||entry.kind==='replay'?'completed':'current';
 }
 private select(id:string,expand=true,targetId=''):void {
  if(!this.entries.some(entry=>entry.id===id))return;
  this.selected=id;this.targetId=targetId;this.customPoint=undefined;if(expand)this.revealSelection(true);
  this.renderHeader();this.renderTree(true);this.renderRight();
 }
 private later(action:string):void {
  const epoch=this.epoch;void Promise.resolve().then(()=>{if(epoch===this.epoch&&this.root&&!this.root.isDisposed){if(!this.handle(action))this.hud.actions.click(action);}});
 }
 private saveScrolls():void {for(const state of [this.leftScroll,this.paperScroll])if(state?.scroll.isValid)this.offsets.set(state.key,Math.max(0,state.scroll.getScrollOffset().y));}
 private rebuild():void {this.hide();this.build();}
 private get hit():number {return Math.max(48*this.unit,48*this.pixelUnit);}
 private build():void {
  if(!this.game)return;this.epoch++;const w=this.hud.width,h=this.hud.height,cssH=viewportMetrics.windowSize.height/Math.max(1,viewportMetrics.devicePixelRatio);this.pixelUnit=h/Math.max(1,cssH);
  const safe=sys.getSafeAreaRect(false),base=Math.min(w/844,h/390),availableW=Math.max(1,safe.width-16*this.pixelUnit),availableH=Math.max(1,safe.height-16*this.pixelUnit);
  this.unit=Math.min(base,availableW/766,availableH/354);const u=this.unit,pw=766*u,ph=354*u;
  const x=safe.x+(safe.width-pw)/2,y=h-safe.y-safe.height+(safe.height-ph)/2,bodyX=x+14*u,bodyY=y+72*u,bodyW=pw-28*u,bodyH=ph-80*u,side=228*u;
  this.layout={x,y,w:pw,h:ph,side,bodyX,bodyY,bodyW,bodyH,rightX:bodyX+side+16*u,rightW:bodyW-side-16*u};this.layoutKey=this.signature();
  this.hud.modal.getComponent(UITransform)!.setContentSize(w,h);
  const root=this.root=GRoot.create();this.hud.modal.addChild(root.node);root.onWinResize();root.name='AdventureJournal';root.node.name='AdventureJournal';
  const page=this.page=UI.place(root,new GComponent(),'AdventureJournalPage',0,0,w,h);page.opaque=true;
  UI.fill(page,'JournalBackdrop',0,0,w,h,new Color(C.background.r,C.background.g,C.background.b,D.shell.backdropAlpha));
  const book=UI.place(page,new GComponent(),'JournalWindow',x,y,pw,ph);book.opaque=true;
  const mask=book.node.addComponent(Mask);mask.type=Mask.Type.GRAPHICS_STENCIL;const clip=mask.subComp as Graphics;clip.clear();clip.roundRect(0,-ph,pw,ph,13*u);clip.fill();
  UI.fill(book,'BookBase',0,0,pw,ph,C.background);UI.image(book,'BookSurface','prep-surface-v2',0,0,pw,ph,Color.WHITE);
  this.header=UI.place(book,new GComponent(),'JournalHeader',0,0,pw,64*u);
  this.tree=UI.place(book,new GComponent(),'JournalDirectory',14*u,72*u,side,bodyH);
  this.right=UI.place(book,new GComponent(),'JournalReadingPane',14*u+side+16*u,72*u,this.layout.rightW,bodyH);
  const border=UI.place(book,new GComponent(),'BookMetalFrame',0,0,pw,ph);border.touchable=false;
  UiSkin.asset(border.node,D.frame.asset,pw,ph,true,D.frame.pixelScaleLogical*u).node.setPosition(pw/2,-ph/2);
  this.hud.modalDisposers.add(this.dispose);this.renderHeader();this.renderTree(true);this.renderRight();
 }
 private renderHeader():void {
  const header=this.header,l=this.layout;if(!header||!l)return;header.removeChildren(0,-1,true);this.clearNative(header);const u=this.unit;
  UI.image(header,'HeaderMaterial','prep-header-v2',0,0,l.w,64*u,Color.WHITE);UI.image(header,'HeaderRule','prep-shell-rule-v5',10*u,61*u,l.w-20*u,6*u,Color.WHITE);
  UI.image(header,'HeaderBrand','prep-logo-v5',62*u,22.5*u,70*u,19*u,Color.WHITE);
  const separator=this.hud.node('JournalBrandSeparator',header.node,145*u,-32*u,u,14*u),g=separator.addComponent(CompactGraphics);g.strokeColor=C.line;g.lineWidth=.6*u;g.moveTo(0,-7*u);g.lineTo(0,7*u);g.stroke();
  this.label(header.node,T('title'),160*u,0,138*u,64*u,14*u,F.color('text.secondary')).verticalAlign=Label.VerticalAlign.CENTER;
  GoldPanelHeader.attach(header.node,{width:l.w,centerX:l.w/2,centerY:-32*u,unit:Math.max(u,this.pixelUnit),hit:this.hit,inset:12*u,viewport:this.hud,action:'close',dismissSide:'left'},()=>this.later('close'));
  for(const [index,mode,label]of [[0,'map',T('map')],[1,'journal',T('tasks')]] as const){const button=this.button(header.node,label,(307+index*80)*u,8*u,72*u,'journal:mode:'+mode,false,true,true,17*u),text=button.getComponentInChildren(Label)!;text.color=this.mode===mode?F.color(D.colorRoles.selected):F.color(D.colorRoles.ink);text.lineHeight=17*u*1.3;if(this.mode===mode)UiSkin.asset(button,'prep-active-v5',82*u,7*u,false).node.setPosition(0,-this.hit/2+8.5*u);}
  const chapter=this.entries.find(entry=>entry.id==='chapter:'+this.entry()?.chapter),caption=this.label(header.node,chapter?.title??'',l.w-278*u,0,200*u,64*u,11*u,F.color('text.secondary'));caption.horizontalAlign=Label.HorizontalAlign.RIGHT;caption.verticalAlign=Label.VerticalAlign.CENTER;caption.enableWrapText=false;
 }
 private clearNative(component:GComponent):void {for(const node of [...component.node.children])if(node!==component.displayListContainer){node.active=false;node.removeFromParent();node.destroy();}}
 private renderTree(reveal=false):void {
  const tree=this.tree,l=this.layout;if(!tree||!l)return;tree.visible=this.mode==='journal';if(!tree.visible)return;
  this.leftScroll=undefined;tree.removeChildren(0,-1,true);this.clearNative(tree);const u=this.unit,w=l.side,innerW=w-14*u,rowH=this.hit;
  const rule=this.hud.node('JournalTreeDivider',tree.node,w-u,-l.bodyH/2,u,l.bodyH),g=rule.addComponent(CompactGraphics);g.strokeColor=F.color('text.preparationAccent',90);g.lineWidth=.5*u;g.moveTo(0,-l.bodyH/2);g.lineTo(0,l.bodyH/2);g.stroke();
  this.label(tree.node,T(this.filter==='locations'?'locations':'taskLog'),0,5*u,96*u,30*u,18*u,F.color(D.colorRoles.accent));
  if(this.filter==='locations')this.button(tree.node,T('tasks'),innerW-112*u,0,112*u,'journal:filter:current',false,true,true,11*u);
  else {const toggle=this.button(tree.node,'',innerW-112*u,0,112*u,'journal:hide-completed',false,true,true,11*u),mark=this.hud.node('JournalCompletedCheck',toggle,-48*u,0,11*u,11*u),ink=mark.addComponent(CompactGraphics);ink.strokeColor=C.line;ink.lineWidth=u;ink.rect(-5.5*u,-5.5*u,11*u,11*u);ink.stroke();if(this.hideCompleted){ink.fillColor=F.color(D.colorRoles.selected);ink.rect(-3*u,-3*u,6*u,6*u);ink.fill();}const text=this.label(toggle,T('hideCompleted'),-39*u,-this.hit/2,90*u,this.hit,11*u,F.color('text.secondary'));text.verticalAlign=Label.VerticalAlign.CENTER;}
  type Row={entry?:JournalEntry;text:string;secondary?:string;action?:string;indent:number;h:number;disclosure?:boolean;open?:boolean};const rows:Row[]=[];
  const leaf=(entry:JournalEntry)=>rows.push({entry,text:entry.title,secondary:entry.statusText,indent:19*u,h:rowH,action:'journal:entry:'+encodeURIComponent(entry.id)});
  if(this.filter==='locations'){
   for(const entry of this.entries.filter(entry=>entry.kind==='area'&&entry.targets.some(target=>target.known)))rows.push({entry,text:entry.title,secondary:entry.statusText,indent:0,h:rowH,action:'journal:entry:'+encodeURIComponent(entry.id)});
   if(!rows.length)rows.push({text:T('emptyLocations'),indent:0,h:rowH});
  }else{
   for(const chapter of this.entries.filter(entry=>entry.kind==='chapter'&&(entry.chapter<=3||this.futureOpen))){
    rows.push({entry:chapter,text:chapter.title,secondary:chapter.status==='upcoming'?T('readOnly'):'',indent:0,h:rowH,action:'journal:chapter:'+chapter.chapter,disclosure:true,open:this.expanded.has(chapter.chapter)});
    if(!this.expanded.has(chapter.chapter)||chapter.status==='upcoming')continue;
    const children=this.entries.filter(entry=>entry.parentId===chapter.id&&entry.kind!=='area'&&(!this.hideCompleted||entry.status!=='completed'));children.filter(entry=>entry.kind==='main').forEach(leaf);
    for(const kind of ['side','replay'] as const){const group=children.filter(entry=>entry.kind===kind);if(!group.length)continue;const set=kind==='side'?this.sideExpanded:this.replayExpanded,open=set.has(chapter.chapter)||this.filter==='completed'&&kind==='replay';rows.push({text:T(kind),secondary:String(group.length),indent:0,h:rowH,action:'journal:group:'+kind+':'+chapter.chapter,disclosure:true,open});if(open)group.forEach(leaf);}
   }
   rows.push({text:T('later'),indent:0,h:rowH,action:'journal:future',disclosure:true,open:this.futureOpen});
  }
  const top=this.hit+8*u,viewH=Math.max(this.hit,l.bodyH-top),contentH=rows.reduce((sum,row)=>sum+row.h,0)+8*u,width=innerW-6*u;
  const content=RpgPanel.scroll(this.hud,tree.node,width/2,-top-viewH/2,width,viewH,contentH,u),scroll=content.parent!.parent!.getComponent(ScrollView)!;content.parent!.parent!.name='JournalDirectoryScroll';const key='tree:'+this.filter;this.leftScroll={scroll,key};let y=0,selectionY:number|undefined;
  for(const row of rows){const selected=row.entry?.id===this.selected;if(selected)selectionY=y;const x=-width/2+row.indent,rw=width-row.indent;
   if(row.action){const n=this.button(content,'',x,y,rw,row.action,false,true,true,14*u,row.h);if(selected)UiSkin.asset(n,'prep-skill-selected-v5',rw,28*u,true);
    const reserve=row.secondary?Math.min(55*u,rw*.32):0,tx=-rw/2+(row.disclosure?17:4)*u,title=this.label(n,fitRpgLine(row.text,rw-(row.disclosure?21:8)*u-reserve,14*u),tx,-row.h/2,rw-(row.disclosure?21:8)*u-reserve,row.h,14*u,selected?F.color(D.colorRoles.accent):row.entry?.status==='completed'?F.color('text.secondary'):F.color(D.colorRoles.ink));title.verticalAlign=Label.VerticalAlign.CENTER;
    if(row.disclosure){const mark=this.hud.node('JournalDisclosure',n,-rw/2+7*u,0,8*u,8*u),glyph=mark.addComponent(CompactGraphics);glyph.fillColor=C.muted;if(row.open){glyph.moveTo(-3.5*u,2*u);glyph.lineTo(3.5*u,2*u);glyph.lineTo(0,-2*u);}else{glyph.moveTo(-2*u,3.5*u);glyph.lineTo(2*u,0);glyph.lineTo(-2*u,-3.5*u);}glyph.close();glyph.fill();}
    if(row.secondary){const status=this.label(n,row.secondary,rw/2-reserve-4*u,-row.h/2,reserve,row.h,11*u,F.color('text.secondary'));status.horizontalAlign=Label.HorizontalAlign.RIGHT;status.verticalAlign=Label.VerticalAlign.CENTER;status.enableWrapText=false;}
   }else this.label(content,row.text,x+4*u,y+4*u,rw-8*u,row.h-8*u,13*u,F.color('text.secondary'));y+=row.h;
  }
  let offset=this.offsets.get(key)??0;if(reveal&&selectionY!==undefined&&(selectionY<offset||selectionY+rowH>offset+viewH))offset=Math.max(0,selectionY-4*u);scroll.scrollToOffset(new Vec2(0,Math.min(Math.max(0,contentH-viewH),offset)),0);
 }
 private selectedTarget(entry:JournalEntry):JournalTarget|undefined {return entry.targets.find(target=>target.id===this.targetId)??entry.targets.find(target=>target.current)??entry.targets[0];}
 private renderRight():void {
  const right=this.right,l=this.layout,game=this.game,root=this.root;if(!right||!l||!game||!root)return;
  const wide=this.mode==='map',width=wide?l.bodyW:l.rightW;this.tree!.visible=!wide;right.setPosition((wide?l.bodyX:l.rightX)-l.x,l.bodyY-l.y);right.setSize(width,l.bodyH);
  const entry=this.entry();
  if(wide&&entry&&entry.status!=='upcoming'){
   this.paperScroll=undefined;
   if(this.mapHost&&(this.mapHost.width!==width||this.mapHost.height!==l.bodyH)){this.map.unmount();this.mapHost.dispose();this.mapHost=null;}
   if(!this.mapHost){right.removeChildren(0,-1,true);this.clearNative(right);this.mapHost=UI.place(right,new GComponent(),'JournalMapPane',0,0,width,l.bodyH);}
   const target=this.selectedTarget(entry),custom=this.customPoint?.area===game.state.area?this.customPoint:undefined;
   const focus:MapFocus|undefined=custom?{area:custom.area,point:custom.point,entryId:entry.id,custom:true}:target?{area:target.area,point:target.point,entryId:entry.id,markerId:target.id}:undefined;
   this.map.mount(game,this.visited,{host:this.mapHost,root,width,height:l.bodyH,unit:this.unit,minTouch:this.hit,markers:journalMarkers(game,entry.id),...(focus?{focus}:{}),selection:this.mapSelection(entry,target),onSelectMarker:(id,markerId)=>this.later('journal:marker:'+encodeURIComponent(id)+':'+encodeURIComponent(markerId??'')),onSelectArea:area=>this.later('journal:entry:'+encodeURIComponent('area:'+area)),onSelectPoint:point=>{this.customPoint={...point,point:{...point.point}};this.map.updateSelection(this.mapSelection(entry,target));},onClearPoint:()=>{this.customPoint=undefined;this.map.updateSelection(this.mapSelection(entry,target));}});
   return;
  }
  if(this.mapHost){this.map.unmount();this.mapHost=null;}right.removeChildren(0,-1,true);this.clearNative(right);this.paperScroll=undefined;this.renderPaper(entry);
 }
 private mapSelection(entry:JournalEntry,target?:JournalTarget){
  const custom=this.customPoint?.area===this.game?.state.area?this.customPoint:undefined,primary=this.targetAction(entry,target),notice=this.hud.mapTravel.error||(this.hud.mapTravel.busy?T('travelBusy'):'');
  const action=custom?'journal:walk-mark':primary?.action;
  return {label:custom?.label??target?.label??entry.title,detail:notice||(target&&!target.known?T('unknownPlace',{name:target.label}):entry.statusText),action,detailAction:'journal:mode:journal',actionLabel:custom?T('walkMark'):primary?T(primary.action.startsWith('map-travel:')?'travel':'go'):undefined,enabled:!!action&&!this.hud.mapTravel.busy,onAction:action?()=>this.later(action):undefined,onDetail:()=>this.later('journal:mode:journal')};
 }
 private targetAction(entry:JournalEntry,target?:JournalTarget):JournalAction|undefined {
  if(!target||target.status==='completed'||entry.status==='upcoming')return;
  const owner=this.entries.find(value=>value.id===target.entryId)??entry;
  const allowed=owner.actions.filter(action=>!action.disabled);
  const direct=allowed.find(action=>action.id===target.id);if(direct)return direct;
  if(target.eventId)return allowed.find(action=>action.action==='journey-field-go:'+target.eventId);
  if(owner.kind==='area')return allowed.find(action=>action.action==='map-travel:'+target.area);
  if(target.current&&owner.kind==='main')return allowed.find(action=>action.action==='journey-go:'+owner.id.slice(5));
  return;
 }
 private renderPaper(entry?:JournalEntry):void {
  const right=this.right!,l=this.layout!,u=this.unit,w=right.width-6*u,sheet=UI.place(right,new GComponent(),'JournalDarkReader',0,0,right.width,l.bodyH);
  const mapAction=(action:string)=>action==='journal:mode:map'||action.startsWith('journey-map:'),primary=entry?.actions.find(action=>action.primary&&!mapAction(action.action));
  const canMap=!!entry?.targets.length&&entry.status!=='upcoming',title=entry?.title??T('title'),titleH=Math.max(26*u,Math.ceil(this.textWidth(title,20*u)/w)*26*u);
  this.label(sheet.node,title,0,2*u,w,titleH,20*u,F.color(D.colorRoles.accent)).lineHeight=26*u;UI.image(sheet,'ReaderTitleRule','prep-rule-v5',0,titleH+5*u,w,5*u,Color.WHITE);
  const top=titleH+16*u,viewH=Math.max(this.hit,l.bodyH-top-this.hit-8*u),blocks:DocumentBlock[]=[];
  const addText=(kind:DocumentBlock['kind'],value:string,size:number,gap=8)=>{if(value)blocks.push({kind,text:value,font:size,height:this.textHeight(value,w,size*u)+gap*u});};
  const addAction=(action:JournalAction)=>{blocks.push({kind:'button',text:action.label,height:this.hit+8*u,action:action.action,disabled:action.disabled});if(action.reason)addText('text',action.reason,11,8);};
  if(entry){addText('text',entry.summary,14,8);let placedPrimary=false;
   for(const section of entry.sections){addText('heading',section.title,14,3);addText('text',section.text,14,8);if(section.id==='current'&&primary){addAction(primary);placedPrimary=true;}}
   if(primary&&!placedPrimary)addAction(primary);
   if(entry.updates.length){addText('heading',T('timeline'),14,7);for(const update of entry.updates){const status=T(update.status==='completed'?'doneStep':update.status==='current'?'currentStep':'lockedStep');blocks.push({kind:'update',text:status+' · '+update.title,height:this.textHeight(status+' · '+update.title,w-16*u,13*u)+5*u,current:update.status==='current'});addText('text',update.text,13,6);if(update.choice)addText('text',T('choice')+'：'+update.choice,13,6);const target=entry.targets.find(target=>update.targetIds.includes(target.id));if(target)blocks.push({kind:'button',text:T('viewSite'),height:this.hit+8*u,action:'journal:target:'+encodeURIComponent(target.id)});}}
   const other=entry.actions.filter(action=>action!==primary&&!mapAction(action.action));if(other.length){addText('heading',T('actions'),14,7);other.forEach(addAction);}
  }else addText('text',T('emptyEntry'),14);
  const contentH=blocks.reduce((sum,block)=>sum+block.height,0)+8*u,content=RpgPanel.scroll(this.hud,sheet.node,w/2,-top-viewH/2,w,viewH,contentH,u),scroll=content.parent!.parent!.getComponent(ScrollView)!;
  content.parent!.parent!.name='JournalDocumentScroll';const key='paper:'+this.selected;this.paperScroll={scroll,key};let y=0;
  for(const block of blocks){const x=-w/2;
   if(block.kind==='button')this.button(content,block.text,x,y,Math.min(w,Math.max(122*u,this.textWidth(block.text,14*u)+24*u)),block.action!,false,!block.disabled,false,14*u);
   else if(block.kind==='update'){const mark=this.hud.node('TimelineSeal',content,x+4*u,-y-9*u,6*u,6*u),g=mark.addComponent(CompactGraphics);g.fillColor=block.current?F.color(D.colorRoles.accent):C.line;g.moveTo(0,2*u);g.lineTo(2*u,0);g.lineTo(0,-2*u);g.lineTo(-2*u,0);g.close();g.fill();this.label(content,block.text,x+16*u,y,w-16*u,block.height-3*u,13*u,block.current?F.color(D.colorRoles.accent):F.color('text.secondary'));}
   else if(block.kind!=='space')this.label(content,block.text,x,y,w,block.height-2*u,(block.font??14)*u,block.kind==='heading'?F.color(D.colorRoles.accent):F.color(D.colorRoles.ink));y+=block.height;
  }
  scroll.scrollToOffset(new Vec2(0,Math.min(Math.max(0,contentH-viewH),this.offsets.get(key)??0)),0);
  const footerY=l.bodyH-this.hit;UI.image(sheet,'ReaderFooterRule','prep-shell-rule-v5',0,footerY-3*u,w,5*u,Color.WHITE);
  const notice=entry?.actions.some(action=>action.action.startsWith('map-travel:'))?(this.hud.mapTravel.error||(this.hud.mapTravel.busy?T('travelBusy'):'')):'';
  const status=this.label(sheet.node,notice||entry?.statusText||'',0,footerY,Math.max(1,w-(canMap?138*u:0)),this.hit,11*u,notice?F.color(this.hud.mapTravel.error?'state.failure':'state.paused'):F.color('text.secondary'));status.verticalAlign=Label.VerticalAlign.CENTER;
  if(canMap)this.button(sheet.node,T('viewMap'),w-122*u,footerY,122*u,'journal:mode:map',false,true,false,14*u);
 }
 private textWidth(value:string,size:number):number {return Array.from(value).reduce((sum,char)=>sum+(char.charCodeAt(0)<128?.58:1),0)*size;}
 private textHeight(value:string,width:number,size:number):number {
  size=Math.max(size,11*this.pixelUnit);
  const lines=value.split('\n').reduce((sum,line)=>sum+Math.max(1,Math.ceil(this.textWidth(line,size)/Math.max(size,width))),0);
  return (lines+0.12)*size*1.43;
 }
 private label(parent:Node,value:string,x:number,y:number,w:number,h:number,size:number,color:Color,bold=false):Label {
  const label=this.hud.text(parent,value,x+w/2,-y-h/2,w,size,color,h);label.node.name='JournalText';label.fontFamily='SimSun';applyRpgFont(label);
  label.fontSize=Math.max(size,11*this.pixelUnit);label.lineHeight=label.fontSize*1.43;label.enableWrapText=true;label.overflow=Label.Overflow.CLAMP;label.verticalAlign=Label.VerticalAlign.TOP;label.isBold=bold;return label;
 }
 private button(parent:Node,title:string,x:number,y:number,w:number,action:string,selected=false,enabled=true,quiet=false,font=14*this.unit,h=this.hit):Node {
  enabled=enabled&&(!this.hud.mapTravel.busy||action==='close'||action.startsWith('journal:')&&action!=='journal:walk-mark');
  const node=this.hud.node(action,parent,x+w/2,-y-h/2,w,h),button=node.addComponent(Button);button.transition=Button.Transition.NONE;button.interactable=enabled;
  if(!quiet){const art=UiSkin.asset(node,'prep-button-dark-v2',w,28*this.unit,true);if(!enabled)art.color=new Color(255,255,255,145);}
  const fw=Math.max(1,w-8*this.unit),fh=quiet?28*this.unit:20*this.unit,face=this.hud.node('JournalButtonFeedback',node,0,0,fw,fh),g=face.addComponent(CompactGraphics);
  bindButtonFeedback(node,button,state=>{if(!g.isValid)return;g.clear();if(state==='idle'||!enabled)return;g.fillColor=new Color(C.hover.r,C.hover.g,C.hover.b,state==='pressed'?200:135);g.roundRect(-fw/2,-fh/2,fw,fh,4*this.unit);g.fill();});
  const text=this.label(node,title,-w/2+8*this.unit,-h/2,w-16*this.unit,h,font,!enabled?F.color('text.disabled'):selected?F.color(D.colorRoles.accent):F.color(D.colorRoles.ink));text.horizontalAlign=Label.HorizontalAlign.CENTER;text.verticalAlign=Label.VerticalAlign.CENTER;text.enableWrapText=false;text.overflow=Label.Overflow.CLAMP;
  node.on(Button.EventType.CLICK,()=>{if(enabled)this.later(action);});return node;
 }
}
