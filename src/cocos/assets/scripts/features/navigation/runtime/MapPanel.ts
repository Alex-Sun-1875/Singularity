import {viewportMetrics} from '../../../platform/ViewportMetrics';
import {CompactMask as Mask} from '../../../shared/ui/CompactMask';
import {ButtonComponent as Button,Color,KeyCode,Label,Node,Rect,ScrollView,UITransform,Vec2,sys} from 'cc';
import {AutoSizeType,Event as FUIEvent,GComponent,GGraph,GRoot,GTextField} from 'fairygui-cc';
import {AREAS,R1_ROADS} from '../../world/data/WorldData';
import {playableArea,playableExits} from '../../journey/data/ChapterJourney';
import type {GameSession} from '../../../core/GameSession';
import {authoredWaypoint,waypointUnlocked,type Waypoint} from '../common/FastTravel';
import {navigationText as T} from '../locales';
import {CAMPAIGN_ATLAS} from '../../world/data/CampaignGeography';
import type {AreaDef,Point} from '../../../core/Contracts';
import type {Hud} from '../../../app/Hud';
import {AtlasUi as UI,AtlasViewport,ATLAS_COLORS as C} from '../../../shared/ui/AtlasUi';
import {LocalCartography as Chart} from './LocalCartography';
import {LocalMapCapture} from './LocalMapCapture';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {GoldPanelHeader} from '../../../shared/ui/GoldPanelHeader';
import {applyRpgFont,fitRpgLine} from '../../../shared/ui/RpgFont';
import {PREPARATION_SKINS} from '../../../shared/ui/PreparationTheme';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {ButtonSurface} from '../../../shared/ui/ButtonSurface';

const LAYERS=[
 {id:'surface',name:'铁誓边境',image:'stonebridge',match:(id:string)=>/^S\d\d$/.test(id)},
 {id:'highlands',name:'断岳高地',image:'highlands',match:(id:string)=>/^H\d\d$/.test(id)},
 {id:'riverbend',name:'风暴河湾',image:'riverbend',match:(id:string)=>/^B\d\d$/.test(id)},
 {id:'city',name:'黑冠城域',image:'city',match:(id:string)=>/^F\d\d$/.test(id)},
 {id:'undercity',name:'誓火深城',image:'undercity',match:(id:string)=>id.startsWith('U1-')},
 {id:'necropolis',name:'沉钟禁域',image:'necropolis',match:(id:string)=>id.startsWith('U2-')},
].filter(layer=>!['riverbend','city','necropolis'].includes(layer.id));
type XY={x:number;y:number};
type Poi={id:string;label:string;detail:string;point:Point;kind:'player'|'exit'|'npc'|'quest'|'merchant'|'checkpoint';destination?:string;locked?:boolean};
export interface MapTaskMarker {id:string;entryId:string;area:string;point?:Point;label:string}
export interface MapFocus {area:string;point?:Point;entryId?:string;markerId?:string;custom?:boolean}
export interface MapPointSelection {area:string;point:Point;label:string}
export interface MapSelection {
 label:string;detail?:string;actionLabel?:string;enabled?:boolean;onAction?:()=>void;onDetail?:()=>void;
 action?:string;detailAction?:string;
}
export interface MapMountOptions {
 host:GComponent;root:GRoot;width:number;height:number;unit:number;minTouch?:number;x?:number;y?:number;
 markers:readonly MapTaskMarker[];focus?:MapFocus;selection?:MapSelection;
 onSelectMarker(entryId:string,markerId:string):void;onSelectArea?(area:string):void;onSelectPoint?(target:MapPointSelection):void;onClearPoint?():void;
}
const CYAN=C.route,GOLD=C.gold,RED=C.red,GREEN=C.green;

/** FairyGUI provides clipping, drag capture and buttons; map data stays real. */
export class MapPanel {
 private root:GRoot|null=null;private pendingHost:Node|null=null;private capture:LocalMapCapture|null=null;
 private game:GameSession;private regionMenuOpen=false;private legendOpen=false;private worldMode=false;private waypoint='';private unit=1;private layoutKey='';private listOffset=0;
 private current='';private visited:Record<string,boolean>={};private localMode=false;private layer=0;private selected='';private selectedPoi='player';private marked='';private localMark:Point|null=null;
 private zoom=1;private pan:XY={x:0,y:0};private needsFit=true;private field:GComponent|null=null;private viewport:GComponent|null=null;private mapW=0;private mapH=0;private fieldW=0;private fieldH=0;private mapScale=1;private zoomLabel:GTextField|null=null;private compact=false;private dragged=false;private font=18;private controlH=48;
 private embedded:MapMountOptions|null=null;private surface:GComponent|null=null;private ownsRoot=false;
 private mapFrame:GComponent|null=null;private waypointRail:GComponent|null=null;private selectionView:GComponent|null=null;private modeMenuOpen=false;
 private taskPins=new Map<GComponent,MapTaskMarker[]>();private markerPicker:GComponent|null=null;private markerDismiss:GComponent|null=null;
 private focused:MapFocus|undefined;private focusRequest='';private focusPending=false;private focusZoomNeeded=false;private captureCount=0;private tasksSignature='';
 constructor(private readonly hud:Hud){}
 private closeMarkerPicker():void{if(this.markerPicker&&!this.markerPicker.isDisposed)this.markerPicker.dispose();if(this.markerDismiss&&!this.markerDismiss.isDisposed)this.markerDismiss.dispose();this.markerPicker=null;this.markerDismiss=null;}
 private disposeSurface():void{this.pendingHost=null;this.closeMarkerPicker();this.capture?.destroy();this.capture=null;if(this.field&&!this.field.isDisposed)this.field.stopDrag();this.field=null;this.viewport=null;this.zoomLabel=null;this.mapFrame=null;this.waypointRail=null;this.selectionView=null;this.taskPins.clear();this.tasksSignature='';if(this.surface&&!this.surface.isDisposed)this.surface.dispose();this.surface=null;}
 unmount():void{Chart.flush();this.disposeSurface();const root=this.root,owned=this.ownsRoot;this.root=null;this.ownsRoot=false;this.embedded=null;this.modeMenuOpen=false;this.regionMenuOpen=false;if(root&&owned&&!root.isDisposed){root.node.active=false;root.node.removeFromParent();root.dispose();}}
 hide():void{this.unmount();}
 refreshLayout():void{if(!this.embedded&&this.root&&!this.root.isDisposed&&this.layoutKey!==this.layoutSignature())this.build();}
 private layoutSignature():string{const s=sys.getSafeAreaRect(false),m=viewportMetrics.menuRect;return [this.hud.width,this.hud.height,s.x,s.y,s.width,s.height,m?.left,m?.top,m?.right,m?.bottom].join(':');}
 private compactMode():boolean{return viewportMetrics.windowSize.height/Math.max(1,viewportMetrics.devicePixelRatio)<600;}
 private later(run:()=>void):void{const root=this.root,surface=this.surface;void Promise.resolve().then(()=>{if(root&&this.root===root&&!root.isDisposed&&(!surface||this.surface===surface&&!surface.isDisposed))run();});}
 private prepare(game:GameSession,visited:Record<string,boolean>):void{
  const replaced=this.game!==game;if(replaced){this.current='';this.selected='';this.waypoint='';this.marked='';this.focused=undefined;this.focusRequest='';this.focusPending=false;this.focusZoomNeeded=false;}
  this.game=game;const current=game.state.area;
  if(current!==this.current){this.localMode=false;this.worldMode=false;this.layer=this.layerFor(current);this.regionMenuOpen=false;this.legendOpen=false;this.zoom=1;this.pan={x:0,y:0};this.needsFit=true;this.selectedPoi='player';this.localMark=null;this.listOffset=0;this.focusRequest='';}
  this.current=current;this.visited=visited;
 }
 show(game:GameSession,visited:Record<string,boolean>,selected?:string):void{
  if(this.embedded)this.unmount();this.prepare(game,visited);const current=game.state.area;
  if(selected&&AREAS[selected]){this.localMode=false;this.worldMode=false;this.layer=this.layerFor(selected);this.selected=selected;if(waypointUnlocked(game.state.flags,AREAS[selected]))this.waypoint=selected;}
  if(!this.destinations().some(p=>p.id===this.waypoint))this.waypoint=this.destinations().find(p=>p.area!==current&&this.layerFor(p.area)===this.layerFor(current))?.id??this.destinations().find(p=>p.area!==current)?.id??this.destinations()[0]?.id??'';
  if(!this.areas().some(a=>a.id===this.selected)&&!this.destinations().some(p=>p.id===this.selected))this.selected=this.areas().find(a=>a.id===this.currentId())?.id??this.areas()[0]?.id??'';
  this.build();
 }
 /** An owned surface inside a caller-owned book/root. No modal is cleared. */
 mount(game:GameSession,visited:Record<string,boolean>,options:MapMountOptions):void{
  if(options.host.isDisposed||options.root.isDisposed)return;
  const previous=this.embedded,oldGame=this.game,oldCurrent=this.current;
  const changedHost=!!this.root&&(!previous||previous.host!==options.host||previous.root!==options.root);
  if(changedHost)this.unmount();this.prepare(game,visited);this.embedded=options;this.root=options.root;this.ownsRoot=false;
  const resized=!previous||previous.width!==options.width||previous.height!==options.height||previous.unit!==options.unit||previous.minTouch!==options.minTouch||previous.x!==options.x||previous.y!==options.y;
  const request=options.focus?this.focusKey(options.focus):'',newFocus=!!options.focus&&request!==this.focusRequest;let changedMode=false;
  if(newFocus){this.focusRequest=request;changedMode=this.applyFocus(options.focus!);}
  if(changedHost||resized||oldGame!==game||oldCurrent!==this.current||changedMode||!this.surface||this.surface.isDisposed||!UI.ready){this.build();return;}
  this.updateTaskMarkers();this.updateLocalMark();this.renderSelection();this.renderWaypointRail();if(this.focusPending)this.centerFocus();this.transform();
 }
 updateSelection(selection?:MapSelection):void{if(!this.embedded)return;this.embedded.selection=selection;this.renderSelection();}
 focus(target:MapFocus):void{if(!this.embedded||!this.root||this.root.isDisposed)return;this.focusRequest=this.focusKey(target);const changed=this.applyFocus(target);if(changed)this.build();else{this.updateTaskMarkers();this.updateLocalMark();this.centerFocus();this.transform();}}
 private focusKey(target:MapFocus):string{return [target.area,target.point?.x,target.point?.z,target.entryId??'',target.markerId??'',target.custom===true].join(':');}
 private applyFocus(target:MapFocus):boolean{
  const area=AREAS[target.area];if(!area||!playableArea(area.id))return false;
  if(target.custom!==true)this.localMark=null;
  const layer=this.layerFor(area.id),local=area.id===this.current&&!!target.point&&(target.custom===true||Chart.revealed(area.id,target.point,this.game)),changed=this.worldMode||layer!==this.layer||local!==this.localMode;
  this.focusZoomNeeded=changed||this.focused?.area!==target.area;
  this.focused={area:target.area,point:target.point?{...target.point}:undefined,entryId:target.entryId,markerId:target.markerId,custom:target.custom};this.focusPending=true;this.selected=area.id;this.worldMode=false;this.localMode=local;this.layer=layer;if(changed)this.reset();return changed;
 }
 private centerFocus():void{
  if(!this.focused||!this.field)return;this.focusPending=false;const target=this.focused;
  if(this.focusZoomNeeded)this.zoom=Math.max(this.zoom,this.localMode?1.2:1.25);this.focusZoomNeeded=false;
  if(this.localMode&&target.area===this.current&&target.point&&(target.custom===true||Chart.revealed(target.area,target.point,this.game)))this.pan={x:-target.point.x*this.mapScale*this.zoom,y:target.point.z*this.mapScale*this.zoom};
  else if(!this.worldMode&&AREAS[target.area]&&playableArea(target.area)){const p=this.position(target.area);this.pan={x:(this.fieldW/2-p.x)*this.zoom,y:(this.fieldH/2-p.y)*this.zoom};}
 }
 key(code:KeyCode):boolean{if(!this.root||!this.field)return false;if(code===KeyCode.EQUAL||code===KeyCode.NUM_PLUS){this.scale(1.25);return true;}if(code===KeyCode.DASH||code===KeyCode.NUM_SUBTRACT){this.scale(.8);return true;}const directions:Record<number,XY>={[KeyCode.ARROW_LEFT]:{x:90,y:0},[KeyCode.ARROW_RIGHT]:{x:-90,y:0},[KeyCode.ARROW_UP]:{x:0,y:90},[KeyCode.ARROW_DOWN]:{x:0,y:-90}};if(directions[code]){this.pan.x+=directions[code].x;this.pan.y+=directions[code].y;this.transform();return true;}if(code===KeyCode.HOME){this.locate();return true;}return false;}
 private currentId():string{return this.current.startsWith('S')?this.current.slice(0,3):this.current;}
 private layerFor(id:string):number{const index=LAYERS.findIndex(layer=>layer.match(id.startsWith('S')?id.slice(0,3):id));return Math.max(0,index);}
 private areas():AreaDef[]{return Object.values(AREAS).filter(a=>playableArea(a.id)&&LAYERS[this.layer].match(a.id));}
 private known(id:string):boolean{return id===this.currentId()||!!this.visited[id]||Object.keys(this.visited).some(key=>this.visited[key]&&key.startsWith(id+'-'));}
 private edges():[string,string][]{if(this.layer===0)return R1_ROADS;const ids=new Set(this.areas().map(a=>a.id));return this.areas().flatMap(a=>a.exits.filter(e=>ids.has(e.to)&&a.id<e.to).map(e=>[a.id,e.to]as[string,string]));}
 private route():string[]{const start=this.currentId();if(!LAYERS[this.layer].match(start)||!this.marked)return [];const queue=[[start]],seen=new Set([start]);while(queue.length){const path=queue.shift()!,last=path[path.length-1];if(last===this.marked)return path;for(const[a,b]of this.edges()){const next=a===last?b:b===last?a:'';if(next&&!seen.has(next)){seen.add(next);queue.push(path.concat(next));}}}return [];}
 private build():void{
  if(this.embedded){this.buildEmbedded();return;}
  this.hud.clearModal();
  if(!UI.ready){this.hud.show(T('map.title'),T('map.loading'),[{label:T('map.back'),action:'close'}]);const host=this.hud.modal.children[0];this.pendingHost=host;void UI.load().then(()=>{if(this.pendingHost===host&&host.isValid)this.build();}).catch(()=>this.hud.show(T('map.title'),T('map.failed'),[{label:T('map.back'),action:'close'}]));return;}
  const w=this.hud.width,h=this.hud.height,cssH=viewportMetrics.windowSize.height/Math.max(1,viewportMetrics.devicePixelRatio);
  this.compact=this.compactMode();this.unit=sys.isMobile?h/cssH:1.25;const u=this.unit;
  this.font=14*u;this.controlH=48*u;this.layoutKey=this.layoutSignature();
  this.hud.modal.getComponent(UITransform)!.setContentSize(w,h);const root=GRoot.create();this.root=root;this.ownsRoot=true;this.hud.modal.addChild(root.node);root.onWinResize();root.name='JourneyMap';root.node.name='JourneyMap';
  const safe=sys.getSafeAreaRect(false),pad=Math.max(10*u,safe.x+6*u),right=Math.min(w-10*u,safe.x+safe.width-6*u),headerY=Math.max(6*u,h-safe.y-safe.height+4*u),gap=10*u,sideW=216*u;
  const menu=viewportMetrics.menuRect,menuLeft=menu?menu.left/menu.windowWidth*w:w-(sys.isMobile?118*u:0),menuBottom=menu?menu.bottom/menu.windowHeight*h:0;
  const top=Math.max(headerY+this.controlH+8*u,menuBottom+8*u),bottom=h-Math.max(8*u,safe.y+4*u),page=UI.panel(root,'MapPage',0,0,w,h,C.background,false);
  this.surface=page;
  UI.image(page,'MapLeather','leather-inset-v8',0,0,w,h,Color.WHITE);
  UI.image(page,'MapOuterFrame','double-gold-frame-rpg-v4',pad-5*u,headerY-3*u,right-pad+10*u,bottom-headerY+8*u,Color.WHITE,true);
  UI.image(page,'MapHeader','prep-header-v2',pad,headerY,right-pad,this.controlH,Color.WHITE);
  GoldPanelHeader.attach(page.node,{width:right-pad,centerX:(pad+right)/2,centerY:-headerY-this.controlH/2,unit:u,hit:this.controlH,inset:0,viewport:this.hud,action:'map:close'},()=>this.hud.actions.click('close'));
  const titleX=pad+this.controlH+8*u,titleW=78*u,tabX=titleX+titleW+12*u,tabW=88*u;
  this.text(page,T('map.title'),titleX,headerY,titleW,this.controlH,18*u,GOLD,true);
  this.tab(page,'map:regional',T('map.region'),tabX,headerY,tabW,()=>{this.worldMode=false;this.localMode=false;this.layer=this.layerFor(this.current);this.reset();this.build();},!this.worldMode);
  this.tab(page,'map:world',T('map.world'),tabX+tabW+8*u,headerY,tabW,()=>{this.worldMode=true;this.localMode=false;this.reset();this.build();},this.worldMode);
  const nameX=tabX+tabW*2+24*u,nameW=Math.min(right-this.controlH-8*u,menuLeft-8*u)-nameX;
  if(nameW>80*u)this.text(page,this.worldMode?'':LAYERS[this.layer].name,nameX,headerY,nameW,this.controlH,13*u,C.muted);
  this.mapW=right-pad-gap-sideW;this.mapH=bottom-top;
  if(this.mapW<300*u||this.mapH<190*u){this.text(page,'请横屏查看旅途地图',pad,h/2-30,right-pad,60,18*u,C.ink,true);return;}
  const frame=UI.panel(page,'MapFrame',pad,top,this.mapW,this.mapH,C.dark,false);
  const viewport=UI.place(frame,new AtlasViewport(),'MapViewport',0,0,this.mapW,this.mapH);this.viewport=viewport;this.createField(viewport);
  this.controls(frame);this.sidebar(page,pad+this.mapW+gap,top,sideW,this.mapH);this.transform();
  if(this.legendOpen)this.legend(frame,8*u,42*u,166*u,Math.min(this.mapH-this.controlH-62*u,200*u));
  if(this.regionMenuOpen)this.regionMenu(page,pad+8*u,top+44*u,160*u);
 }
 private buildEmbedded():void{
  const options=this.embedded;if(!options||options.host.isDisposed||options.root.isDisposed)return;
  this.disposeSurface();this.root=options.root;this.ownsRoot=false;this.compact=this.compactMode();this.unit=Math.max(.1,options.unit);this.font=14*this.unit;this.controlH=Math.max(48*this.unit,options.minTouch??0);
  this.mapW=Math.max(1,options.width);this.mapH=Math.max(1,options.height);this.layoutKey=[this.mapW,this.mapH,this.unit].join(':');
  const bodyW=this.mapW,bodyH=this.mapH,u=this.unit,legendW=96*u,railW=100*u,gap=8*u;
  const surface=UI.place(options.host,new AtlasViewport(),'EmbeddedMapSurface',options.x??0,options.y??0,bodyW,bodyH);this.surface=surface;
  this.mapW=Math.max(1,bodyW-legendW-railW-gap*2);
  if(!UI.ready){
   this.text(surface,T('map.loading'),8*u,0,bodyW-16*u,bodyH,this.font,C.muted,true);
   void UI.load().then(()=>{if(this.embedded===options&&!options.host.isDisposed&&!options.root.isDisposed)this.build();}).catch(()=>{if(this.surface===surface&&!surface.isDisposed)this.text(surface,T('map.failed'),8*this.unit,0,this.mapW-16*this.unit,this.mapH,this.font,RED,true);});return;
  }
  const frame=UI.place(surface,new AtlasViewport(),'MapFrame',legendW+gap,0,this.mapW,this.mapH);this.mapFrame=frame;
  UI.fill(frame,'MapBacking',0,0,this.mapW,this.mapH,C.dark);
  const viewport=UI.place(frame,new AtlasViewport(),'MapViewport',0,0,this.mapW,this.mapH);this.viewport=viewport;this.createField(viewport);this.updateTaskMarkers();this.embeddedLegend(surface,legendW);this.embeddedControls(frame);this.renderWaypointRail();this.updateLocalMark();this.renderSelection();
  if(this.focusPending)this.centerFocus();this.transform();
  if(this.modeMenuOpen)this.modeMenu(surface,legendW+gap+8*u,8*u);
  if(this.regionMenuOpen)this.regionMenu(frame,8*u,8*u,160*u);
 }
 private text(parent:GComponent,value:string,x:number,y:number,w:number,h:number,size:number,color:Color,center=false):GTextField{
  const label=UI.text(parent,value,x,y,w,h,size,color,center);label.autoSize=AutoSizeType.None;label.singleLine=!value.includes('\n');if(label.singleLine)label.text=fitRpgLine(value,w,size);label.touchable=false;
  const native=label.node.getComponent(Label);if(native)applyRpgFont(native);return label;
 }
 private embeddedLegend(parent:GComponent,w:number):void{
  const u=this.unit,ink=F.color('text.preparation'),accent=F.color('text.preparationAccent');
  this.text(parent,LAYERS[this.layer].name,0,0,w-4*u,21*u,15*u,accent);
  UI.image(parent,'MapLegendRule',PREPARATION_SKINS.rule.asset,0,20*u,w-6*u,5*u,Color.WHITE);
  const rows:[string,Color,string][]=[['player',CYAN,T('legend.player')],['quest',GOLD,T('legend.quest')],['person',GREEN,T('legend.people')],['merchant',accent,T('legend.merchant')],['rest',accent,T('legend.rest')],['exit',CYAN,T('legend.exit')],['rune',C.purple,T('map.compactWaypoints')],['mark',GOLD,T('legend.mark')]];
  rows.forEach(([kind,color,label],i)=>{const y=(28+i*23)*u;this.legendGlyph(parent,kind,u,y+4*u,14*u,color);this.text(parent,label,20*u,y,w-24*u,23*u,12*u,ink);});
  const mode=this.compactAction(parent,'map:mode',T('map.controls')+' ▾',0,this.mapH-this.controlH,w,()=>{this.modeMenuOpen=!this.modeMenuOpen;this.regionMenuOpen=false;this.refreshEmbeddedMenus();});mode.getTextField().fontSize=12*u;
 }
 private legendGlyph(parent:GComponent,kind:string,x:number,y:number,size:number,color:Color):void{
  const icon=UI.place(parent,new GGraph(),'MapLegend:'+kind,x,y,size,size);icon.touchable=false;if(kind==='rune'){this.exitRune(icon);return;}
  const g=icon._content,k=size/24,m=(a:number,b:number)=>g.moveTo(a*k,-b*k),l=(a:number,b:number)=>g.lineTo(a*k,-b*k),c=(a:number,b:number,d:number,e:number,f:number,h:number)=>g.bezierCurveTo(a*k,-b*k,d*k,-e*k,f*k,-h*k);g.strokeColor=color;g.fillColor=color;g.lineWidth=1.4*k;
  if(kind==='player'||kind==='quest'){m(12,2);l(22,12);l(12,22);l(2,12);g.close();if(kind==='player')g.fill();else{g.stroke();m(12,6);l(18,12);l(12,18);l(6,12);g.close();g.stroke();}return;}
  if(kind==='person'){g.circle(12*k,-6*k,3.2*k);m(5,22);l(5,17);c(5,9,19,9,19,17);l(19,22);}
  else if(kind==='merchant'){m(9,3);l(12,5);l(16,3);l(14,9);c(24,17,20,22,12,22);c(3,22,1,17,10,9);l(9,3);m(8,9);l(16,9);m(12,13);l(12,19);m(9,16);l(15,16);}
  else if(kind==='rest'){m(14,2);c(17,8,9,9,12,14);c(15,12,17,9,17,8);c(25,19,14,24,8,19);c(3,16,5,12,8,8);c(6,17,12,16,10,12);c(9,8,14,6,14,2);m(3,23);l(21,20);m(3,20);l(21,23);}
  else if(kind==='exit'){m(4,23);l(4,10);c(4,0,20,0,20,10);l(20,23);m(8,23);l(8,10);c(8,5,16,5,16,10);l(16,23);m(2,23);l(22,23);}
  else if(kind==='mark'){m(5,23);l(5,3);c(9,-1,13,8,21,3);l(21,14);c(13,19,9,10,5,14);}
  g.stroke();
 }
 private compactAction(parent:GComponent,name:string,title:string,x:number,y:number,w:number,run:()=>void,skinHeight=32*this.unit){
  const button=this.button(parent,name,title,x,y,w,this.controlH,run),inset=w<=52*this.unit?6*this.unit:0;button.getChild('EquipmentButton')?.dispose();
  // AtlasUi.image owns a native Sprite whose geometry is fixed at creation.
  const art=UI.image(button,'EquipmentButton',PREPARATION_SKINS['button-dark'].asset,inset,(this.controlH-skinHeight)/2,w-inset*2,skinHeight,Color.WHITE,true);button.setChildIndex(art,0);return button;
 }
 private embeddedControls(frame:GComponent):void{
  const u=this.unit,h=this.controlH,y=this.mapH-h,x=this.mapW-h*3-16*u;
  const minus=this.compactAction(frame,'map:zoom-out','−',x,y,h,()=>this.scale(.8));minus.getTextField().fontSize=22*u;
  const plus=this.compactAction(frame,'map:zoom-in','+',x+h+8*u,y,h,()=>this.scale(1.25));plus.getTextField().fontSize=22*u;
  const locate=this.compactAction(frame,'map:locate','',x+h*2+16*u,y,h,()=>this.locate()),glyph=UI.place(locate,new GGraph(),'MapLocateGlyph',h/2-8*u,h/2-8*u,16*u,16*u);glyph.touchable=false;
  const g=glyph._content;g.strokeColor=GOLD;g.lineWidth=u;g.circle(8*u,-8*u,5*u);g.moveTo(8*u,0);g.lineTo(8*u,-5*u);g.moveTo(8*u,-11*u);g.lineTo(8*u,-16*u);g.moveTo(0,-8*u);g.lineTo(5*u,-8*u);g.moveTo(11*u,-8*u);g.lineTo(16*u,-8*u);g.stroke();
  const north=this.text(frame,'N',this.mapW-26*u,7*u,18*u,16*u,11*u,GOLD,true);north.name='MapNorth';
 }
 private refreshEmbeddedMenus():void{
  const surface=this.surface;if(!this.embedded||!surface)return;
  for(const name of ['MapModePicker','map:mode:dismiss'])surface.getChild(name)?.dispose();
  for(const name of ['MapRegionPicker','map:regions:dismiss'])this.mapFrame?.getChild(name)?.dispose();
  if(this.modeMenuOpen)this.modeMenu(surface,112*this.unit,8*this.unit);
  if(this.regionMenuOpen&&this.mapFrame)this.regionMenu(this.mapFrame,8*this.unit,8*this.unit,160*this.unit);
 }
 private modeMenu(parent:GComponent,x:number,y:number):void{
  const u=this.unit,h=this.controlH,width=Math.max(172*u,h+16*u),gap=8*u,height=3*h+gap*2+16*u,dismiss=UI.place(parent,new GComponent(),'map:mode:dismiss',0,0,parent.width,parent.height);dismiss.opaque=true;dismiss.onClick(()=>this.later(()=>{this.modeMenuOpen=false;this.refreshEmbeddedMenus();}));
  const picker=UI.panel(parent,'MapModePicker',Math.max(0,Math.min(x,parent.width-width)),Math.max(0,Math.min(y,parent.height-height)),width,height,C.panel,false);
  this.button(picker,'map:world-toggle',this.worldMode?T('map.region'):T('map.world'),8*u,8*u,width-16*u,h,()=>{this.modeMenuOpen=false;this.worldMode=!this.worldMode;this.localMode=false;this.reset();this.build();},this.worldMode);
  this.button(picker,'map:regions',T('map.regions'),8*u,8*u+h+gap,width-16*u,h,()=>{this.modeMenuOpen=false;this.regionMenuOpen=true;this.refreshEmbeddedMenus();});
  this.button(picker,'map:local',this.localMode?T('map.region'):T('map.local'),8*u,8*u+(h+gap)*2,width-16*u,h,()=>{this.modeMenuOpen=false;this.localMode=!this.localMode;this.worldMode=false;if(this.localMode)this.layer=this.layerFor(this.current);this.reset();this.build();},this.localMode);
 }
 private renderSelection():void{
  this.selectionView?.dispose();this.selectionView=null;const frame=this.mapFrame,selection=this.embedded?.selection;if(!frame||!selection)return;
  const u=this.unit,width=Math.max(1,this.mapW-this.controlH*3-32*u),height=this.controlH,view=UI.place(frame,new GComponent(),'MapSelection',4*u,this.mapH-height,width,height);this.selectionView=view;
  UI.fill(view,'SelectionBacking',0,0,width,height,new Color(C.dark.r,C.dark.g,C.dark.b,210));
  const busy=this.hud.mapTravel.busy,action=selection.onAction&&selection.actionLabel,details=!!selection.onDetail,actionW=action?Math.max(this.controlH,Math.min(88*u,width*.34)):0,detailW=details?this.controlH:0,actionsW=actionW+detailW+(action&&details?8*u:0),textW=Math.max(1,width-actionsW-8*u);
  this.text(view,selection.label,4*u,selection.detail?1*u:12*u,textW,23*u,13*u,GOLD);
  if(selection.detail)this.text(view,selection.detail,4*u,23*u,textW,22*u,11*u,C.muted);
  if(details){const detail=this.compactAction(view,selection.detailAction??'map:selection-detail',T('map.details'),width-actionsW,0,detailW,()=>selection.onDetail?.());detail.getTextField().fontSize=12*u;}
  if(action){const button=this.compactAction(view,selection.action??'map:selection-action',selection.actionLabel!,width-actionW,0,actionW,()=>{if(selection.enabled!==false&&!this.hud.mapTravel.busy)selection.onAction?.();},28*u);button.enabled=selection.enabled!==false&&!busy;button.alpha=button.enabled?1:.55;button.getTextField().fontSize=12*u;}
 }
 private renderWaypointRail():void{
  const options=this.embedded,surface=this.surface;if(!options||!surface)return;this.waypointRail?.dispose();
  const u=this.unit,w=100*u,h=this.mapH,side=UI.place(surface,new GComponent(),'MapWaypointRail',options.width-w,0,w,h);this.waypointRail=side;
  UI.fill(side,'WaypointDivider',-4*u,0,u,h,new Color(C.line.r,C.line.g,C.line.b,100));
  const rune=UI.place(side,new GGraph(),'WaypointHeadingRune',0,3*u,16*u,16*u);rune.touchable=false;this.exitRune(rune);this.text(side,T('map.compactWaypoints'),22*u,0,w-22*u,23*u,15*u,GOLD);UI.image(side,'WaypointHeadingRule',PREPARATION_SKINS.rule.asset,0,21*u,w,5*u,Color.WHITE);
  const points=this.destinations().filter(point=>this.worldMode||this.layerFor(point.area)===this.layer);
  if(!points.some(point=>point.id===this.waypoint))this.waypoint=points.find(point=>point.area===this.current)?.id??points[0]?.id??'';
  const destination=AREAS[this.waypoint],status=destination?this.game.fastTravelAvailability(destination):{available:false,reason:T('map.select')},busy=this.hud.mapTravel.busy,note=this.hud.mapTravel.error||(busy?T('map.busy'):!status.available&&destination?status.reason:'');
  const listY=26*u,listH=Math.max(0,h-34*u-this.controlH-(note?32*u:0)),rowH=28*u,host=this.hud.node('MapWaypointScroll',side.node,w/2,-listY-listH/2,w,listH),viewport=this.hud.node('MapWaypointViewport',host,0,0,w,listH);viewport.addComponent(Mask).type=Mask.Type.GRAPHICS_RECT;
  const contentH=Math.max(listH,points.length*rowH),content=this.hud.node('MapWaypointContent',viewport,0,listH/2,w,contentH);content.getComponent(UITransform)!.setAnchorPoint(.5,1);
  const scroll=host.addComponent(ScrollView);scroll.content=content;scroll.horizontal=false;scroll.vertical=true;scroll.cancelInnerEvents=true;scroll.inertia=true;scroll.elastic=false;
  points.forEach((point,i)=>{const selected=point.id===this.waypoint,row=this.hud.node('map:waypoint:'+point.id,content,0,-i*rowH-rowH/2,w,rowH);
   if(selected)UiSkin.asset(row,PREPARATION_SKINS['skill-selected'].asset,w,22*u,true);
   const button=row.addComponent(Button);button.transition=Button.Transition.NONE;button.interactable=!this.hud.mapTravel.busy;
   ButtonSurface.attach(row,{width:w-6*u,height:22*u,radius:3*u,overlay:true,after:row.children[0]});
   const label=this.hud.text(row,fitRpgLine(point.name,w-20*u,13*u),0,0,w-20*u,13*u,selected?GOLD:C.muted,rowH);label.fontFamily='SimSun';applyRpgFont(label);
   row.on(Button.EventType.CLICK,()=>{if(scroll.isScrolling()||scroll.isAutoScrolling()||this.hud.mapTravel.busy)return;this.listOffset=scroll.getScrollOffset().y;this.selectWaypoint(point.id);});
  });
  if(!points.length)this.text(side,T('map.compactEmpty'),4*u,listY+8*u,w-8*u,48*u,12*u,C.muted,true);
  this.listOffset=Math.max(0,Math.min(this.listOffset,contentH-listH));scroll.scrollToOffset(new Vec2(0,this.listOffset),0);
  host.on(ScrollView.EventType.SCROLL_ENDED,()=>{this.listOffset=scroll.getScrollOffset().y;});
  if(note){const message=this.text(side,note,4*u,listY+listH,w-8*u,32*u,11*u,this.hud.mapTravel.error?F.color('state.failure'):C.muted,true);message.name='MapTravelStatus';message.singleLine=false;message.text=note;}
  const travel=this.compactAction(side,'map:travel',busy?T('map.busy'):T('map.compactTravel'),0,h-this.controlH,w,()=>{const current=AREAS[this.waypoint];if(current&&!this.hud.mapTravel.busy&&this.game.fastTravelAvailability(current).available)this.hud.actions.click('map-travel:'+this.waypoint);},28*u);travel.enabled=!!destination&&status.available&&!busy;travel.alpha=travel.enabled?1:.55;travel.getTextField().fontSize=15*u;
 }
 private button(parent:GComponent,name:string,title:string,x:number,y:number,w:number,h:number,run:()=>void,active=false,gold=false){
  const button=UI.button(parent,name,title,x,y,w,h,()=>{if(!this.hud.mapTravel.busy)this.later(run);},false,this.font);
  for(const key of ['QuietBronze','ActiveTeal','Selected']){const child=button.getChild(key);if(child)child.visible=false;}
  const art=UI.image(button,'EquipmentButton',gold?'prep-button-gold-v2':active?'rpg-selection-frame-v3':'prep-button-dark-v2',0,0,w,h,Color.WHITE,true);button.setChildIndex(art,0);
  const label=button.getTextField();label.color=gold?C.dark:active?GOLD:F.color('text.preparation');label.setPosition(0,0);label.setSize(w,h);label.autoSize=AutoSizeType.None;label.text=fitRpgLine(title,w-4*this.unit,this.font);const native=label.node.getComponent(Label);if(native)applyRpgFont(native);return button;
 }
 private tab(parent:GComponent,name:string,title:string,x:number,y:number,w:number,run:()=>void,active:boolean):void{
  const tab=this.button(parent,name,title,x,y,w,this.controlH,run,active);
  tab.getChild('EquipmentButton').visible=false;
  if(active)UI.image(tab,'ActiveUnderline','rpg-active-rule-v4',0,this.controlH-6*this.unit,w,6*this.unit,Color.WHITE);
 }
 private destinations():Waypoint[]{return this.game?Object.values(AREAS).filter(area=>waypointUnlocked(this.game.state.flags,area)).map(area=>authoredWaypoint(area)!).sort((a,b)=>this.layerFor(a.area)-this.layerFor(b.area)||a.id.localeCompare(b.id)):[];}
 private selectWaypoint(id:string):void{this.waypoint=id;this.selected=id;this.localMode=false;this.worldMode=false;this.layer=this.layerFor(id);this.hud.mapTravel.error='';this.reset();this.build();this.zoom=Math.max(this.zoom,1.5);const p=this.position(id);this.pan={x:(this.fieldW/2-p.x)*this.zoom,y:(this.fieldH/2-p.y)*this.zoom};this.transform();}
 private reset():void{this.zoom=1;this.pan={x:0,y:0};this.needsFit=true;}
 private regionMenu(parent:GComponent,x:number,y:number,w:number):void{
  const width=this.embedded?this.mapW:this.hud.width,height=this.embedded?this.mapH:this.hud.height,u=this.unit,gap=8*u,pad=8*u;
  const dismiss=UI.place(parent,new GComponent(),'map:regions:dismiss',0,0,width,height);dismiss.opaque=true;dismiss.onClick(()=>this.later(()=>{this.regionMenuOpen=false;if(this.embedded)this.refreshEmbeddedMenus();else this.build();}));
  const columns=LAYERS.length*(this.controlH+gap)+pad*2>height-y-pad?2:1,itemW=columns===2?Math.max(120*u,w*.7):w,rows=Math.ceil(LAYERS.length/columns),pickerW=Math.min(width-pad*2,itemW*columns),columnW=pickerW/columns,pickerH=rows*this.controlH+(rows-1)*gap+pad*2;
  const picker=UI.panel(parent,'MapRegionPicker',Math.max(pad,Math.min(x,width-pickerW-pad)),Math.max(4*u,Math.min(y,height-pickerH-pad)),pickerW,pickerH,C.panel);
  LAYERS.forEach((layer,index)=>this.button(picker,'map:layer:'+layer.id,layer.name,pad+index%columns*columnW,pad+Math.floor(index/columns)*(this.controlH+gap),columnW-pad*2,this.controlH,()=>{this.localMode=false;this.worldMode=false;this.layer=index;this.selected='';this.regionMenuOpen=false;this.reset();if(this.embedded)this.build();else this.show(this.game,this.visited);},!this.localMode&&this.layer===index));
 }
 private legend(parent:GComponent,x:number,y:number,w:number,h:number):void{
  const u=this.unit,panel=UI.panel(parent,'MapLegend',x,y,w,h,C.panel),rows:[string,Color,string][]=[['◆',CYAN,T('legend.player')],['rune',C.purple,T('legend.waypoint')],['○',CYAN,T('legend.exit')],['◇',GOLD,T('legend.quest')],['●',GREEN,T('legend.npc')],['⚑',GOLD,T('legend.mark')]];
  const line=(h-16*u)/rows.length;
  rows.forEach(([symbol,color,text],i)=>{if(symbol==='rune'){const icon=UI.place(panel,new GGraph(),'WaypointLegend',12*u,8*u+i*line+(line-18*u)/2,18*u,18*u);icon.touchable=false;this.exitRune(icon);}else this.text(panel,symbol,8*u,8*u+i*line,28*u,line,this.font,color,true);this.text(panel,text,38*u,8*u+i*line,w-44*u,line,12*u,C.ink);});
 }
 private createField(viewport:GComponent):void{
  const area=AREAS[this.current];
  if(this.localMode){this.mapScale=Math.max(this.mapW/area.width,this.mapH/area.depth)*1.06;this.fieldW=area.width*this.mapScale;this.fieldH=area.depth*this.mapScale;}
  else{const cover=Math.max(this.mapW/1536,this.mapH/1024);this.fieldW=1536*cover;this.fieldH=1024*cover;}
  if(this.needsFit){this.zoom=this.minimumZoom();this.needsFit=false;}
  const field=UI.place(viewport,new GComponent(),'MapField',0,0,this.fieldW,this.fieldH);this.field=field;field.opaque=true;field.draggable=true;
  if(this.worldMode){this.createWorld(field);}
  else if(this.localMode){
   const floor=UI.place(field,new GGraph(),'CoordinateTerrain',0,0,this.fieldW,this.fieldH);floor.touchable=false;Chart.drawTerrain(floor._content,area,this.mapScale,this.fieldW/2,-this.fieldH/2);
   if(this.current===this.game.state.area){const snapshot=UI.place(field,new GComponent(),'TerrainSnapshot',0,0,this.fieldW,this.fieldH);snapshot.touchable=false;this.capture=new LocalMapCapture(snapshot.node,area,0,0,this.fieldW,this.fieldH);this.captureCount++;}
   const fog=UI.place(field,new GGraph(),'UnexploredFog',0,0,this.fieldW,this.fieldH);fog.touchable=false;Chart.drawFog(fog._content,area,this.mapScale,this.fieldW/2,-this.fieldH/2);
   for(const poi of this.pois())this.localPin(field,poi);
   if(this.localMark)this.localPin(field,{id:'custom',label:'自定标记',detail:'探索用标记',point:this.localMark,kind:'quest'},true);
   field.onClick((event:FUIEvent)=>{if(this.dragged)return;const p=field.globalToLocal(event.pos.x,event.pos.y),point={x:(p.x-this.fieldW/2)/this.mapScale,z:(this.fieldH/2-p.y)/this.mapScale};if(Math.abs(point.x)>area.width/2||Math.abs(point.z)>area.depth/2)return;this.localMark=point;this.selectedPoi='custom';this.waypoint='';if(this.embedded){this.closeMarkerPicker();this.updateLocalMark();this.transform();this.embedded.onSelectPoint?.({area:this.current,point:{...point},label:'自定标记'});return;}this.later(()=>this.build());});
  }else{
   UI.image(field,'TerrainIllustration','atlas/'+LAYERS[this.layer].image,0,0,this.fieldW,this.fieldH,Color.WHITE);
   const fog=UI.place(field,new GGraph(),'WorldExplorationFog',0,0,this.fieldW,this.fieldH);fog.touchable=false;const g=fog._content,known=this.areas().filter(a=>this.known(a.id)).map(a=>this.position(a.id)),step=16;
   for(let x=0;x<this.fieldW;x+=step)for(let y=0;y<this.fieldH;y+=step){const d=Math.min(...known.map(p=>Math.hypot(x+step/2-p.x,y+step/2-p.y)));const t=Math.max(0,Math.min(1,(d-88*this.unit)/(82*this.unit)));g.fillColor=new Color(C.dark.r,C.dark.g,C.dark.b,Math.round(248*t*t*(3-2*t)));g.rect(x,-y-step,step,step);g.fill();}
   const roads=UI.place(field,new GGraph(),'RoadOverlay',0,0,this.fieldW,this.fieldH);roads.touchable=false;const rg=roads._content;rg.lineWidth=1.7;rg.strokeColor=new Color(C.line.r,C.line.g,C.line.b,160);
   for(const[a,b]of this.edges())if(this.known(a)&&this.known(b)){const p=this.position(a),q=this.position(b);rg.moveTo(p.x,-p.y);rg.lineTo(q.x,-q.y);rg.stroke();}
   const route=this.route();rg.lineWidth=3;rg.strokeColor=C.route;for(let i=1;i<route.length;i++)if(this.known(route[i-1])&&this.known(route[i])){const p=this.position(route[i-1]),q=this.position(route[i]);rg.moveTo(p.x,-p.y);rg.lineTo(q.x,-q.y);rg.stroke();}
   for(const a of this.areas())if(this.known(a.id))this.worldPin(field,a);
   for(const point of this.destinations())if(/^S\d\d-/.test(point.area)&&this.layer===0)this.worldPin(field,AREAS[point.area]);
  }
  field.on(FUIEvent.TOUCH_BEGIN,()=>{this.dragged=false;});field.on(FUIEvent.DRAG_START,()=>{this.dragged=true;});field.on(FUIEvent.DRAG_MOVE,()=>{this.pan={x:field.x-(this.mapW-this.fieldW*this.zoom)/2,y:field.y-(this.mapH-this.fieldH*this.zoom)/2};});viewport.on(FUIEvent.MOUSE_WHEEL,(event:FUIEvent)=>{event.propagationStopped=true;if(event.mouseWheelDelta)this.scale(event.mouseWheelDelta>0?1.15:1/1.15);});
 }
 private pois():Poi[]{
  const area=AREAS[this.current],game=this.game,p=game?.state.area===area.id?game.state.player:area.spawn;const result:Poi[]=[{id:'player',label:'拉斐尔',detail:'队伍当前位置',point:p,kind:'player'}];
  for(const e of playableExits(area))if(Chart.revealed(area.id,e)){const destination=AREAS[e.to]?.name??e.to,locked=!!game?.exitRequirement(e);result.push({id:'exit:'+e.id,label:destination,detail:`${locked?`需要 Lv${e.requiredLevel??1}；`:'等级已满足，可自由通行；'}请前往现场${locked?'查看通行条件':sys.isMobile?'点交互进入目的地':'按 F 进入目的地'}。`,point:e,kind:'exit',destination,locked});}
  for(const o of area.objects){if(game&&!game.interactionVisible(o)||!Chart.revealed(area.id,o))continue;const kind=Chart.kind(o);if(kind==='place')continue;
   const merchantKnown=!!o.merchant&&!!game?.state.discoveredMerchants.includes(o.merchant);
   const detail=kind==='checkpoint'?'已发现的休整点；请前往现场休整。':merchantKnown?'已发现的商人；请前往现场交谈，查看本趟余货。':kind==='quest'?'已发现的任务地点；请前往现场交谈或调查。':'已发现的人物；请前往现场交谈。';
   result.push({id:o.id,label:o.label,detail,point:o,kind});
  }return result;
 }
 private localPin(parent:GComponent,poi:Poi,custom=false):void{
  const x=this.fieldW/2+poi.point.x*this.mapScale,y=this.fieldH/2-poi.point.z*this.mapScale,size=sys.isMobile?Math.max(84,this.controlH):48,color=F.color(poi.kind==='exit'?'map.exit':poi.kind==='player'?'map.player':poi.kind==='npc'||poi.kind==='checkpoint'?'map.ally':'map.task');
  const marker=UI.place(parent,new GComponent(),'map:place:'+poi.id,x,y,size,size);marker.setPivot(.5,.5,true);marker.opaque=true;const icon=UI.place(marker,new GGraph(),'MarkerIcon',size/2-7,size/2-7,14,14);icon.touchable=false;
  if(poi.kind==='exit'){icon.name='ExitRuneIcon';icon.node.name=icon.name;icon.setPosition(size/2-15,size/2-15);icon.setSize(30,30);this.exitRune(icon,poi.locked);}
  else if(poi.kind==='merchant'){icon.visible=false;this.legendGlyph(marker,'merchant',size/2-12,size/2-12,24,color);}
  else if(poi.kind==='npc')icon.drawEllipse(1,C.dark,color);else icon.drawRegularPolygon(1.5,poi.kind==='player'?C.ink:color,poi.kind==='player'?CYAN:C.dark,4,0);
  if(poi.id===this.selectedPoi){const ring=UI.place(marker,new GGraph(),'SelectedRing',size/2-12,size/2-12,24,24);ring.drawEllipse(1,color,Color.TRANSPARENT);ring.touchable=false;}
  if(custom)this.text(marker,'⚑',size/2-12,size/2-18,24,32,this.font,GOLD,true);
  if(poi.kind==='exit'){
   const width=Math.max(140,Math.min(sys.isMobile?300:230,(poi.destination?.length??6)*this.font+24)),height=this.font+12,dx=Math.max(width/2+4,Math.min(this.fieldW-width/2-4,x))-x,below=y+24+height<this.fieldH;
   const labelX=(size-width)/2+dx,labelY=below?size/2+22:size/2-22-height;
   UI.fill(marker,'ExitNameBacking',labelX-3,labelY-2,width+6,height+4,new Color(16,11,26,242));const text=this.text(marker,poi.destination??poi.label,labelX,labelY,width,height,this.font,poi.locked?C.purple:C.route,true);text.name='ExitDestinationName';text.node.name=text.name;text.touchable=false;
  }
  marker.onClick((event:FUIEvent)=>{event.propagationStopped=true;if(this.dragged)return;this.selectedPoi=poi.id;this.waypoint='';if(this.embedded){if(poi.id==='custom')this.embedded.onSelectPoint?.({area:this.current,point:{...poi.point},label:'自定标记'});else this.embedded.onSelectArea?.(this.current);return;}this.later(()=>this.build());});
 }
 private exitRune(icon:GGraph,locked=false):void{
  const g=icon._content,x=icon.width/2,y=-icon.height/2,r=Math.min(icon.width,icon.height)*.32,ink=new Color(16,11,26),purple=locked?new Color(196,165,237,165):C.purple,cyan=locked?new Color(131,205,230,155):C.route;
  g.strokeColor=ink;g.lineWidth=5;g.circle(x,y,r);g.stroke();g.strokeColor=purple;g.lineWidth=2;g.circle(x,y,r);g.stroke();
  g.strokeColor=cyan;g.fillColor=ink;g.lineWidth=1.8;g.moveTo(x,y+r*.57);g.lineTo(x+r*.48,y);g.lineTo(x,y-r*.57);g.lineTo(x-r*.48,y);g.close();g.fill();g.stroke();
  for(let index=0;index<4;index++){const angle=index*Math.PI/2;g.moveTo(x+Math.cos(angle)*(r-1.6),y+Math.sin(angle)*(r-1.6));g.lineTo(x+Math.cos(angle)*(r+2.5),y+Math.sin(angle)*(r+2.5));}g.stroke();
 }
 private updateTaskMarkers():void{
  const options=this.embedded,field=this.field;if(!options||!field||field.isDisposed)return;
  const signature=JSON.stringify([this.localMode,this.worldMode,this.layer,this.focused?.area,this.focused?.entryId,this.focused?.markerId,this.focused&&this.known(this.focused.area),options.markers.map(marker=>[marker.id,marker.entryId,marker.area,marker.point?.x,marker.point?.z,marker.label,this.known(marker.area)])]);if(signature===this.tasksSignature)return;this.tasksSignature=signature;this.closeMarkerPicker();
  for(const pin of this.taskPins.keys())if(!pin.isDisposed)pin.dispose();this.taskPins.clear();field.getChild('map:focus-region')?.dispose();if(this.worldMode)return;
  this.unknownFocusHint(field);
  const buckets=new Map<string,MapTaskMarker[]>();
  for(const marker of options.markers){
   const area=AREAS[marker.area];if(!area||!playableArea(area.id)||!this.known(area.id))continue;
   if(this.localMode&&(area.id!==this.current||!marker.point||!Number.isFinite(marker.point.x)||!Number.isFinite(marker.point.z)||!Chart.revealed(area.id,marker.point,this.game)))continue;
   if(!this.localMode&&this.layerFor(area.id)!==this.layer)continue;
   const key=this.localMode?`${marker.point!.x.toFixed(2)},${marker.point!.z.toFixed(2)}`:area.id,group=buckets.get(key)??[];if(!group.some(item=>item.id===marker.id))group.push(marker);buckets.set(key,group);
  }
  for(const group of buckets.values()){
   const marker=group[0],p=this.localMode?{x:this.fieldW/2+marker.point!.x*this.mapScale,y:this.fieldH/2-marker.point!.z*this.mapScale}:this.position(marker.area),size=this.controlH,selected=group.some(item=>this.focused?.markerId?item.id===this.focused.markerId:item.entryId===this.focused?.entryId);
   const pin=UI.place(field,new GComponent(),'map:task:'+group.map(item=>item.id).join(','),p.x,p.y,size,size);pin.setPivot(.5,.5,true);pin.opaque=true;
   const icon=UI.place(pin,new GGraph(),'TaskMarker',size/2-10*this.unit,size/2-10*this.unit,20*this.unit,20*this.unit);icon.touchable=false;icon.drawRegularPolygon(2,selected?CYAN:GOLD,C.dark,4,0);
   if(selected){const ring=UI.place(pin,new GGraph(),'SelectedTask',size/2-16*this.unit,size/2-16*this.unit,32*this.unit,32*this.unit);ring.touchable=false;ring.drawEllipse(1.5,CYAN,Color.TRANSPARENT);}
   if(group.length>1){const count=this.text(pin,String(group.length),size/2+7*this.unit,size/2-21*this.unit,22*this.unit,22*this.unit,13*this.unit,GOLD,true);count.touchable=false;}
   pin.onClick((event:FUIEvent)=>{event.propagationStopped=true;if(!this.dragged)this.later(()=>this.chooseTaskMarkers(group));});this.taskPins.set(pin,group);
  }
 }
 private unknownFocusHint(field:GComponent):void{
  const target=this.focused;if(!target||this.localMode||this.known(target.area))return;
  const area=AREAS[target.area];if(!area||!playableArea(area.id)||this.layerFor(area.id)!==this.layer)return;
  // A journal reference supplies only an approximate region, never a discovered POI.
  const region=AREAS[area.id.startsWith('S')?area.id.slice(0,3):area.id]??area,p=this.position(region.id),u=this.unit;
  const hint=UI.place(field,new GComponent(),'map:focus-region',p.x,p.y,1,1);hint.touchable=false;
  const ring=UI.place(hint,new GGraph(),'UnexploredRegionRing',-30*u,-30*u,60*u,60*u);ring.touchable=false;ring.drawEllipse(2*u,GOLD,new Color(C.dark.r,C.dark.g,C.dark.b,80));
  const question=this.text(hint,'?',-15*u,-22*u,30*u,42*u,24*u,GOLD,true);question.touchable=false;
  const label=this.text(hint,region.name+' · 尚未探索',-100*u,36*u,200*u,30*u,13*u,GOLD,true);label.touchable=false;
 }
 private updateLocalMark():void{
  if(!this.embedded||!this.surface||!this.field)return;
  const frame=this.mapFrame??this.surface;this.field.getChild('map:place:custom')?.dispose();frame.getChild('map:clear-mark')?.dispose();
  if(!this.localMode||!this.localMark)return;
  this.localPin(this.field,{id:'custom',label:'自定标记',detail:'探索用标记',point:this.localMark,kind:'quest'},true);
  this.compactAction(frame,'map:clear-mark',T('map.unmark'),8*this.unit,0,88*this.unit,()=>{this.localMark=null;this.selectedPoi='player';this.updateLocalMark();this.transform();this.embedded?.onClearPoint?.();},28*this.unit);
 }
 private chooseTaskMarkers(markers:readonly MapTaskMarker[],page=0):void{
  const options=this.embedded,parent=this.mapFrame??this.surface;if(!options||!parent||parent.isDisposed)return;const entries=Array.from(new Map(markers.map(marker=>[marker.id,marker])).values());if(!entries.length)return;
  this.closeMarkerPicker();if(entries.length===1){options.onSelectMarker(entries[0].entryId,entries[0].id);return;}
  const u=this.unit,h=this.controlH,gap=8*u,width=Math.min(this.mapW-16*u,300*u),header=30*u,rows=Math.max(1,Math.floor((this.mapH-24*u-header-h-gap)/(h+gap))),pages=Math.ceil(entries.length/rows),index=Math.max(0,Math.min(page,pages-1)),visible=entries.slice(index*rows,(index+1)*rows),height=header+16*u+visible.length*(h+gap)+(pages>1?h+gap:0);
  const dismiss=UI.place(parent,new GComponent(),'TaskMarkerDismiss',0,0,this.mapW,this.mapH);dismiss.opaque=true;dismiss.onClick(()=>this.closeMarkerPicker());this.markerDismiss=dismiss;
  const panel=UI.panel(parent,'TaskMarkerPicker',(this.mapW-width)/2,Math.max(4*u,(this.mapH-height)/2),width,height,C.panel,false);this.markerPicker=panel;
  this.text(panel,`此处目标 · ${entries.length}`,8*u,4*u,width-16*u,header,14*u,GOLD);
  visible.forEach((entry,row)=>this.button(panel,'map:task-select:'+entry.id,entry.label,8*u,header+8*u+row*(h+gap),width-16*u,h,()=>{this.closeMarkerPicker();this.embedded?.onSelectMarker(entry.entryId,entry.id);}));
  if(pages>1){const y=height-h-8*u,w=(width-24*u)/2;const previous=this.button(panel,'map:task-previous','上一页',8*u,y,w,h,()=>this.chooseTaskMarkers(entries,index-1));previous.enabled=index>0;const next=this.button(panel,'map:task-next','下一页',16*u+w,y,w,h,()=>this.chooseTaskMarkers(entries,index+1));next.enabled=index<pages-1;}
 }
 private position(id:string):XY{const atlasId=id.startsWith('S')?id.slice(0,3):id,point=CAMPAIGN_ATLAS[atlasId]??AREAS[id].atlas;return{x:point.x/100*this.fieldW,y:(1-point.z/100)*this.fieldH};}
 private worldPin(parent:GComponent,area:AreaDef):void{
  const waypoint=waypointUnlocked(this.game.state.flags,area),p=this.position(area.id),known=this.known(area.id),current=area.id===this.currentId(),selected=area.id===this.selected,size=this.controlH,color=current?CYAN:selected?GOLD:known?C.ink:C.muted;
  const marker=UI.place(parent,new GComponent(),'map:place:'+area.id,p.x,p.y,size,size);marker.setPivot(.5,.5,true);marker.opaque=true;const icon=UI.place(marker,new GGraph(),'MarkerIcon',size/2-9,size/2-9,18,18);icon.touchable=false;if(waypoint){icon.setPosition(size/2-13*this.unit,size/2-13*this.unit);icon.setSize(26*this.unit,26*this.unit);this.exitRune(icon);}else icon.drawRegularPolygon(1.5,color,C.dark,4,0);
  if(current)this.text(marker,'◆',size/2+8*this.unit,size/2-17*this.unit,18*this.unit,24*this.unit,14*this.unit,CYAN,true);
  if(selected||current){const width=Math.max(90*this.unit,area.name.length*this.font+12),labelY=p.y>this.fieldH*.6?size/2-this.font-26*this.unit:size/2+16*this.unit;UI.fill(marker,'LabelBacking',(size-width)/2,labelY,width,this.font+8,new Color(C.dark.r,C.dark.g,C.dark.b,230));this.text(marker,area.name,(size-width)/2,labelY,width,this.font+8,this.font,color,true);}
  marker.onClick((event:FUIEvent)=>{event.propagationStopped=true;if(!this.dragged){if(this.embedded){this.selected=area.id;this.embedded.onSelectArea?.(area.id);return;}if(waypoint)this.later(()=>this.selectWaypoint(area.id));else{this.selected=area.id;this.waypoint='';this.later(()=>this.build());}}});
 }
 private createWorld(field:GComponent):void{
  UI.image(field,'WorldIllustration','atlas/world',0,0,this.fieldW,this.fieldH,Color.WHITE);
  // The overview expresses regions. Exact local markers stay on authored regional atlases.
  const positions=[{x:.22,y:.53},{x:.57,y:.27},{x:.40,y:.73}];
  const cover=UI.place(field,new GGraph(),'WorldUnknownFog',0,0,this.fieldW,this.fieldH);cover.touchable=false;
  const known=LAYERS.map((layer,i)=>({layer,i})).filter(({layer})=>Object.values(AREAS).some(area=>playableArea(area.id)&&layer.match(area.id)&&this.known(area.id)));
  const g=cover._content,step=16;for(let x=0;x<this.fieldW;x+=step)for(let y=0;y<this.fieldH;y+=step){const d=Math.min(...known.map(({i})=>Math.hypot((x+step/2)/this.fieldW-positions[i].x,(y+step/2)/this.fieldH-positions[i].y)));const t=Math.max(0,Math.min(1,(d-.11)/.14));g.fillColor=new Color(C.dark.r,C.dark.g,C.dark.b,Math.round(50+198*t*t*(3-2*t)));g.rect(x,-y-step,step,step);g.fill();}
  for(const {layer,i}of known){const p=positions[i],size=this.controlH,marker=UI.place(field,new GComponent(),'map:place:region:'+layer.id,p.x*this.fieldW,p.y*this.fieldH,size,size);marker.setPivot(.5,.5,true);marker.opaque=true;const icon=UI.place(marker,new GGraph(),'RegionRune',size/2-12*this.unit,size/2-12*this.unit,24*this.unit,24*this.unit);this.exitRune(icon);
   this.text(marker,layer.name,size/2-65*this.unit,size/2+16*this.unit,130*this.unit,24*this.unit,this.font,GOLD,true);
   marker.onClick(()=>this.later(()=>{if(this.dragged)return;this.layer=i;this.worldMode=false;this.reset();this.build();}));
  }
 }
 private controls(frame:GComponent):void{
  const u=this.unit,h=this.controlH,pad=8*u,y=this.mapH-h-8*u;
  this.button(frame,'map:regions',LAYERS[this.layer].name+' ▾',pad,6*u,132*u,h,()=>{this.regionMenuOpen=!this.regionMenuOpen;this.legendOpen=false;this.build();});
  if(this.embedded)this.button(frame,'map:world-toggle',this.worldMode?T('map.region'):T('map.world'),pad+140*u,6*u,74*u,h,()=>{this.worldMode=!this.worldMode;this.localMode=false;this.reset();this.build();},this.worldMode);
  if(!this.worldMode)this.button(frame,'map:local',this.localMode?T('map.region'):T('map.local'),this.mapW-96*u,6*u,88*u,h,()=>{this.localMode=!this.localMode;if(this.localMode)this.layer=this.layerFor(this.current);this.reset();this.build();},this.localMode);
  this.button(frame,'map:legend',T('map.legend'),pad,y,52*u,h,()=>{this.legendOpen=!this.legendOpen;this.regionMenuOpen=false;this.build();},this.legendOpen);
  this.button(frame,'map:zoom-out','−',pad+60*u,y,h,h,()=>this.scale(.8));
  this.zoomLabel=this.text(frame,Math.round(this.zoom*100)+'%',pad+112*u,y,40*u,h,12*u,C.ink,true);
  this.button(frame,'map:zoom-in','+',pad+156*u,y,h,h,()=>this.scale(1.25));
  const locateX=this.mapW-76*u;
  if(this.mapW>=360*u)this.button(frame,'map:fit',T('map.fit'),locateX-60*u,y,52*u,h,()=>this.fit());
  this.button(frame,'map:locate',T('map.locate'),locateX,y,68*u,h,()=>this.locate());
  this.text(frame,this.worldMode?'':T('map.unknown'),8*u,this.mapH-h-32*u,this.mapW-16*u,20*u,11*u,C.muted);
 }
 private sidebar(parent:GComponent,x:number,y:number,w:number,h:number):void{
  const u=this.unit,pad=12*u,cw=w-pad*2,side=UI.panel(parent,'MapSidebar',x,y,w,h,C.panel,false);
  UI.image(side,'WaypointLeather','leather-inset-v8',0,0,w,h,Color.WHITE);UI.image(side,'WaypointFrame','rpg-selection-frame-v3',0,0,w,h,Color.WHITE,true);
  const points=this.destinations();this.text(side,T('map.waypoints'),pad,6*u,cw,25*u,18*u,GOLD);this.text(side,T('map.unlocked',{count:points.length}),pad,31*u,cw,20*u,12*u,C.muted);
  const foot=h-102*u,listY=58*u,listH=Math.max(48*u,foot-listY-6*u),rowH=52*u,gap=8*u;
  const host=this.hud.node('WaypointScroll',side.node,pad+cw/2,-listY-listH/2,cw,listH),viewport=this.hud.node('WaypointViewport',host,0,0,cw,listH);viewport.addComponent(Mask).type=Mask.Type.GRAPHICS_RECT;
  const content=this.hud.node('WaypointContent',viewport,0,listH/2,cw,Math.max(listH,points.length*(rowH+gap)-gap));content.getComponent(UITransform)!.setAnchorPoint(.5,1);
  const scroll=host.addComponent(ScrollView);scroll.content=content;scroll.horizontal=false;scroll.vertical=true;scroll.cancelInnerEvents=true;scroll.inertia=true;scroll.elastic=false;
  for(const [i,point]of points.entries()){
   const selected=point.id===this.waypoint,row=this.hud.node('map:waypoint:'+point.id,content,0,-i*(rowH+gap)-rowH/2,cw,rowH);
   const skin=UiSkin.asset(row,selected?'rpg-selection-frame-v3':'prep-button-dark-v2',cw,rowH,true);
   const button=row.addComponent(Button);button.transition=Button.Transition.NONE;button.interactable=!this.hud.mapTravel.busy;
   ButtonSurface.attach(row,{width:cw-8*u,height:rowH-8*u,radius:3*u,overlay:true,after:skin.node});
   const rune=this.hud.text(row,'◎',-cw/2+18*u,0,24*u,24*u,F.color('quality.epic'),rowH);rune.horizontalAlign=Label.HorizontalAlign.CENTER;
   this.hud.text(row,point.name,16*u,10*u,cw-58*u,15*u,selected?GOLD:C.ink,24*u);
   this.hud.text(row,LAYERS[this.layerFor(point.id)].name+(point.area===this.current?' · '+T('map.current'):''),16*u,-12*u,cw-58*u,11*u,C.muted,20*u);
   row.on(Button.EventType.CLICK,()=>{this.listOffset=scroll.getScrollOffset().y;this.selectWaypoint(point.id);});
  }
  if(!points.length)this.text(side,T('map.empty'),pad,listY,cw,listH,13*u,C.muted,true);
  this.listOffset=Math.max(0,Math.min(this.listOffset,points.length*(rowH+gap)-gap-listH));scroll.scrollToOffset(new Vec2(0,this.listOffset),0);
  const destination=AREAS[this.waypoint],status=destination?this.game.fastTravelAvailability(destination):{available:false,reason:T('map.select')},busy=this.hud.mapTravel.busy;
  const selectedArea=AREAS[this.selected],poi=this.localMode?(this.selectedPoi==='custom'&&this.localMark?{id:'custom',label:T('legend.mark'),point:this.localMark}:this.selectedPoi!=='player'?this.pois().find(p=>p.id===this.selectedPoi):undefined):!this.worldMode&&!this.waypoint&&selectedArea&&this.known(selectedArea.id)?{id:selectedArea.id,label:selectedArea.name,point:selectedArea.spawn}:undefined,note=this.hud.mapTravel.error||(busy?T('map.busy'):poi?poi.label+' · '+T('map.discovered'):status.reason);
  UI.image(side,'TravelRule','rpg-footer-rule-v4',pad,foot,cw,5*u,Color.WHITE);
  this.text(side,note,pad,foot+6*u,cw,34*u,12*u,this.hud.mapTravel.error?F.color('state.failure'):C.muted,true);
  const travelWidth=poi?(cw-8*u)*.58:cw,travel=this.button(side,'map:travel',poi?T('map.walk'):busy?T('map.busy'):destination?T('map.travel',{name:destination.name}):T('map.select'),pad,h-this.controlH-12*u,travelWidth,this.controlH,()=>{if(poi){const area=this.localMode?this.current:poi.id,exit=this.localMode?AREAS[area].exits.find(e=>'exit:'+e.id===poi.id):undefined;this.hud.actions.navigate({area,point:{...poi.point},label:poi.label,exitId:exit?.id});}else this.hud.actions.click('map-travel:'+this.waypoint);},false,true);
  travel.enabled=(!!poi||status.available)&&!busy;travel.alpha=travel.enabled?1:.55;
  if(poi&&this.localMode)this.button(side,'map:mark',this.localMark?T('map.unmark'):T('map.mark'),pad+travelWidth+8*u,h-this.controlH-12*u,cw-travelWidth-8*u,this.controlH,()=>{this.localMark=this.localMark?null:{...poi.point};if(!this.localMark)this.selectedPoi='player';this.build();});
  const index=points.findIndex(p=>p.id===this.waypoint),itemTop=index*(rowH+gap);if(index>=0&&(itemTop<this.listOffset||itemTop+rowH>this.listOffset+listH)){this.listOffset=Math.max(0,Math.min(itemTop,points.length*(rowH+gap)-gap-listH));scroll.scrollToOffset(new Vec2(0,this.listOffset),0);}
 }
 private minimumZoom():number{return this.fieldW>0&&this.fieldH>0?Math.min(1,this.mapW/this.fieldW,this.mapH/this.fieldH):1;}
 private fit():void{this.field?.stopDrag();this.zoom=this.minimumZoom();this.pan={x:0,y:0};this.transform();}
 private scale(factor:number):void{this.field?.stopDrag();this.zoom=Math.max(this.minimumZoom(),Math.min(3,this.zoom*factor));this.transform();}
 private clusterMarkers():void{
  if(!this.field||this.localMode&&!this.embedded||this.worldMode)return;
  const field=this.field,old=Array.from({length:field.numChildren},(_,i)=>field.getChildAt(i)).filter(n=>n.name.startsWith('map:cluster:'));for(const node of old)node.dispose();
  const player=this.localMode?field.getChild('map:place:player'):null;
  if(player){player.visible=true;player.touchable=false;}
  const pins=Array.from({length:field.numChildren},(_,i)=>field.getChildAt(i)).filter(n=>n!==player&&(n.name.startsWith('map:place:')||n.name.startsWith('map:task:'))) as GComponent[];
  for(const pin of pins){pin.visible=true;pin.touchable=true;}
  const remaining=new Set(pins),gap=(this.controlH+8*this.unit)/this.zoom;
  while(remaining.size){const group=[remaining.values().next().value!];remaining.delete(group[0]);for(let i=0;i<group.length;i++)for(const pin of remaining)if(Math.hypot(group[i].x-pin.x,group[i].y-pin.y)<gap){group.push(pin);remaining.delete(pin);}
   if(group.length<2)continue;for(const pin of group){pin.visible=false;pin.touchable=false;}
   const tasks=Array.from(new Map(group.flatMap(pin=>this.taskPins.get(pin)??[]).map(marker=>[marker.id,marker])).values());
   const x=group.reduce((v,p)=>v+p.x,0)/group.length,y=group.reduce((v,p)=>v+p.y,0)/group.length,size=this.controlH,cluster=UI.place(field,new GComponent(),'map:cluster:'+group.map(p=>p.name).join(','),x,y,size,size);cluster.setPivot(.5,.5,true);cluster.setScale(1/this.zoom,1/this.zoom);cluster.opaque=true;
   const icon=UI.place(cluster,new GGraph(),'ClusterRune',size/2-13*this.unit,size/2-13*this.unit,26*this.unit,26*this.unit);this.exitRune(icon);
   const count=this.text(cluster,String(tasks.length||group.length),size/2+9*this.unit,size/2-21*this.unit,20*this.unit,22*this.unit,13*this.unit,tasks.length?GOLD:C.ink,true);count.touchable=false;
   cluster.onClick((event:FUIEvent)=>{event.propagationStopped=true;if(this.dragged)return;this.later(()=>{if(tasks.length){this.chooseTaskMarkers(tasks);return;}this.zoom=Math.min(3,this.zoom*1.6);this.pan={x:(this.fieldW/2-x)*this.zoom,y:(this.fieldH/2-y)*this.zoom};this.transform();});});
  }
  if(player)field.setChildIndex(player,field.numChildren-1);
 }
 private transform():void{
  if(!this.field||this.field.isDisposed)return;this.zoom=Math.max(this.minimumZoom(),Math.min(3,this.zoom));const limitX=Math.max(0,(this.fieldW*this.zoom-this.mapW)/2),limitY=Math.max(0,(this.fieldH*this.zoom-this.mapH)/2);this.pan.x=Math.max(-limitX,Math.min(limitX,this.pan.x));this.pan.y=Math.max(-limitY,Math.min(limitY,this.pan.y));this.field.setScale(this.zoom,this.zoom);this.field.setPosition((this.mapW-this.fieldW*this.zoom)/2+this.pan.x,(this.mapH-this.fieldH*this.zoom)/2+this.pan.y);
  if(this.viewport&&this.root){const global=this.viewport.localToGlobal(),origin=this.root.globalToLocal(global.x,global.y),width=this.fieldW*this.zoom,height=this.fieldH*this.zoom,extraX=Math.max(0,width-this.mapW),extraY=Math.max(0,height-this.mapH);this.field.dragBounds=new Rect(origin.x+(extraX?-extraX:(this.mapW-width)/2),origin.y+(extraY?-extraY:(this.mapH-height)/2),width+extraX,height+extraY);}
  for(let i=0;i<this.field.numChildren;i++){const child=this.field.getChildAt(i);if(child.name.startsWith('map:place:')||child.name.startsWith('map:task:'))child.setScale(1/this.zoom,1/this.zoom);}this.clusterMarkers();if(this.zoomLabel)this.zoomLabel.text=Math.round(this.zoom*100)+'%';
 }
 private locate():void{if(this.worldMode){this.worldMode=false;this.localMode=false;this.layer=this.layerFor(this.current);this.reset();this.build();}if(this.localMode){const p=Chart.current?.state.player??AREAS[this.current].spawn;this.zoom=1.2;this.pan={x:-p.x*this.mapScale*this.zoom,y:p.z*this.mapScale*this.zoom};this.transform();}else{this.layer=this.layerFor(this.current);this.selected=this.currentId();this.reset();this.build();const p=this.position(this.currentId());this.zoom=1.4;this.pan={x:(this.fieldW/2-p.x)*this.zoom,y:(this.fieldH/2-p.y)*this.zoom};this.transform();}}
 inspect(){return{open:!!this.root&&!this.root.isDisposed,embedded:!!this.embedded,ownsRoot:this.ownsRoot,mode:this.worldMode?'world':this.localMode?'local':'region',zoom:this.zoom,pan:{...this.pan},captures:this.captureCount,taskMarkers:Array.from(this.taskPins.values()).flat().map(marker=>({id:marker.id,entryId:marker.entryId,area:marker.area})),selectedEntry:this.focused?.entryId??'',selectedMarker:this.focused?.markerId??'',waypoints:this.destinations().map(p=>p.id),selectedWaypoint:this.waypoint,travelBusy:this.hud.mapTravel.busy,region:LAYERS[this.layer].id,regionPickerOpen:this.regionMenuOpen,regionCount:LAYERS.length,regionAreaCount:this.areas().length,selectedPoi:this.selectedPoi,revealedExits:this.localMode?this.pois().filter(p=>p.kind==='exit').map(p=>({id:p.id,name:p.destination,locked:!!p.locked,x:p.point.x,z:p.point.z})):[],worldPositions:this.localMode?[]:this.areas().map(area=>({id:area.id,...this.position(area.id)}))};}
}
