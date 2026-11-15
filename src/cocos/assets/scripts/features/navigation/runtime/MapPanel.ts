import {viewportMetrics} from '../../../platform/ViewportMetrics';
import {CompactMask as Mask} from '../../../shared/ui/CompactMask';
import {ButtonComponent as Button,Color,KeyCode,Label,Node,Rect,ScrollView,UITransform,Vec2,sys} from 'cc';
import {Event as FUIEvent,GComponent,GGraph,GRoot,GTextField} from 'fairygui-cc';
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
import {UI_PANEL_BACK} from '../../../shared/ui/UiChrome';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';

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
const CYAN=C.route,GOLD=C.gold,RED=C.red,GREEN=C.green;

/** FairyGUI provides clipping, drag capture and buttons; map data stays real. */
export class MapPanel {
 private root:GRoot|null=null;private pendingHost:Node|null=null;private capture:LocalMapCapture|null=null;
 private game:GameSession;private regionMenuOpen=false;private legendOpen=false;private worldMode=false;private waypoint='';private unit=1;private layoutKey='';private listOffset=0;
 private current='';private visited:Record<string,boolean>={};private localMode=false;private layer=0;private selected='';private selectedPoi='player';private marked='';private localMark:Point|null=null;
 private zoom=1;private pan:XY={x:0,y:0};private needsFit=true;private field:GComponent|null=null;private viewport:GComponent|null=null;private mapW=0;private mapH=0;private fieldW=0;private fieldH=0;private mapScale=1;private zoomLabel:GTextField|null=null;private compact=false;private dragged=false;private font=18;private controlH=48;
 constructor(private readonly hud:Hud){}
 hide():void{Chart.flush();this.pendingHost=null;this.capture?.destroy();this.capture=null;this.field?.stopDrag();this.field=null;this.viewport=null;this.zoomLabel=null;if(this.root){const root=this.root;this.root=null;root.node.active=false;root.node.removeFromParent();root.dispose();}}
 refreshLayout():void{if(this.root&&!this.root.isDisposed&&this.layoutKey!==this.layoutSignature())this.build();}
 private layoutSignature():string{const s=sys.getSafeAreaRect(false),m=viewportMetrics.menuRect;return [this.hud.width,this.hud.height,s.x,s.y,s.width,s.height,m?.left,m?.top,m?.right,m?.bottom].join(':');}
 private compactMode():boolean{return viewportMetrics.windowSize.height/Math.max(1,viewportMetrics.devicePixelRatio)<600;}
 private later(run:()=>void):void{const root=this.root;void Promise.resolve().then(()=>{if(root&&this.root===root&&!root.isDisposed)run();});}
 show(game:GameSession,visited:Record<string,boolean>,selected?:string):void{
  this.game=game;const current=game.state.area;
  if(current!==this.current){this.localMode=false;this.worldMode=false;this.layer=this.layerFor(current);this.regionMenuOpen=false;this.zoom=1;this.pan={x:0,y:0};this.needsFit=true;this.selectedPoi='player';this.localMark=null;this.listOffset=0;}
  this.current=current;this.visited=visited;
  if(selected&&AREAS[selected]){this.localMode=false;this.worldMode=false;this.layer=this.layerFor(selected);this.selected=selected;if(waypointUnlocked(game.state.flags,AREAS[selected]))this.waypoint=selected;}
  if(!this.destinations().some(p=>p.id===this.waypoint))this.waypoint=this.destinations().find(p=>p.area!==current&&this.layerFor(p.area)===this.layerFor(current))?.id??this.destinations().find(p=>p.area!==current)?.id??this.destinations()[0]?.id??'';
  if(!this.areas().some(a=>a.id===this.selected)&&!this.destinations().some(p=>p.id===this.selected))this.selected=this.areas().find(a=>a.id===this.currentId())?.id??this.areas()[0]?.id??'';
  this.build();
 }
 key(code:KeyCode):boolean{if(!this.root||!this.field)return false;if(code===KeyCode.EQUAL||code===KeyCode.NUM_PLUS){this.scale(1.25);return true;}if(code===KeyCode.DASH||code===KeyCode.NUM_SUBTRACT){this.scale(.8);return true;}const directions:Record<number,XY>={[KeyCode.ARROW_LEFT]:{x:90,y:0},[KeyCode.ARROW_RIGHT]:{x:-90,y:0},[KeyCode.ARROW_UP]:{x:0,y:90},[KeyCode.ARROW_DOWN]:{x:0,y:-90}};if(directions[code]){this.pan.x+=directions[code].x;this.pan.y+=directions[code].y;this.transform();return true;}if(code===KeyCode.HOME){this.locate();return true;}return false;}
 private currentId():string{return this.current.startsWith('S')?this.current.slice(0,3):this.current;}
 private layerFor(id:string):number{const index=LAYERS.findIndex(layer=>layer.match(id.startsWith('S')?id.slice(0,3):id));return Math.max(0,index);}
 private areas():AreaDef[]{return Object.values(AREAS).filter(a=>playableArea(a.id)&&LAYERS[this.layer].match(a.id));}
 private known(id:string):boolean{return id===this.currentId()||!!this.visited[id]||Object.keys(this.visited).some(key=>this.visited[key]&&key.startsWith(id+'-'));}
 private edges():[string,string][]{if(this.layer===0)return R1_ROADS;const ids=new Set(this.areas().map(a=>a.id));return this.areas().flatMap(a=>a.exits.filter(e=>ids.has(e.to)&&a.id<e.to).map(e=>[a.id,e.to]as[string,string]));}
 private route():string[]{const start=this.currentId();if(!LAYERS[this.layer].match(start)||!this.marked)return [];const queue=[[start]],seen=new Set([start]);while(queue.length){const path=queue.shift()!,last=path[path.length-1];if(last===this.marked)return path;for(const[a,b]of this.edges()){const next=a===last?b:b===last?a:'';if(next&&!seen.has(next)){seen.add(next);queue.push(path.concat(next));}}}return [];}
 private build():void{
  this.hud.clearModal();
  if(!UI.ready){this.hud.show(T('map.title'),T('map.loading'),[{label:T('map.back'),action:'close'}]);const host=this.hud.modal.children[0];this.pendingHost=host;void UI.load().then(()=>{if(this.pendingHost===host&&host.isValid)this.build();}).catch(()=>this.hud.show(T('map.title'),T('map.failed'),[{label:T('map.back'),action:'close'}]));return;}
  const w=this.hud.width,h=this.hud.height,cssH=viewportMetrics.windowSize.height/Math.max(1,viewportMetrics.devicePixelRatio);
  this.compact=this.compactMode();this.unit=sys.isMobile?h/cssH:1.25;const u=this.unit;
  this.font=14*u;this.controlH=48*u;this.layoutKey=this.layoutSignature();
  this.hud.modal.getComponent(UITransform)!.setContentSize(w,h);const root=GRoot.create();this.root=root;this.hud.modal.addChild(root.node);root.onWinResize();root.name='JourneyMap';root.node.name='JourneyMap';
  const safe=sys.getSafeAreaRect(false),pad=Math.max(10*u,safe.x+6*u),right=Math.min(w-10*u,safe.x+safe.width-6*u),headerY=Math.max(6*u,h-safe.y-safe.height+4*u),gap=10*u,sideW=216*u;
  const menu=viewportMetrics.menuRect,menuLeft=menu?menu.left/menu.windowWidth*w:w-(sys.isMobile?118*u:0),menuBottom=menu?menu.bottom/menu.windowHeight*h:0;
  const top=Math.max(headerY+this.controlH+8*u,menuBottom+8*u),bottom=h-Math.max(8*u,safe.y+4*u),page=UI.panel(root,'MapPage',0,0,w,h,C.background,false);
  UI.image(page,'MapLeather','leather-inset-v8',0,0,w,h,Color.WHITE);
  UI.image(page,'MapOuterFrame','double-gold-frame-rpg-v4',pad-5*u,headerY-3*u,right-pad+10*u,bottom-headerY+8*u,Color.WHITE,true);
  UI.image(page,'MapHeader','prep-header-v2',pad,headerY,right-pad,this.controlH,Color.WHITE);
  const back=this.button(page,'map:close','',pad,headerY,this.controlH,this.controlH,()=>this.hud.actions.click('close'));
  back.getChild('EquipmentButton').visible=false;
  UiSkin.asset(back.node,UI_PANEL_BACK.skin,20*u,20*u,false).node.setPosition(this.controlH/2,-this.controlH/2);
  const titleX=pad+this.controlH+8*u,titleW=78*u,tabX=titleX+titleW+12*u,tabW=88*u;
  UI.text(page,T('map.title'),titleX,headerY,titleW,this.controlH,18*u,GOLD,true);
  this.tab(page,'map:regional',T('map.region'),tabX,headerY,tabW,()=>{this.worldMode=false;this.localMode=false;this.layer=this.layerFor(this.current);this.reset();this.build();},!this.worldMode);
  this.tab(page,'map:world',T('map.world'),tabX+tabW+8*u,headerY,tabW,()=>{this.worldMode=true;this.localMode=false;this.reset();this.build();},this.worldMode);
  const nameX=tabX+tabW*2+24*u,nameW=Math.min(right,menuLeft-8*u)-nameX;
  if(nameW>80*u)UI.text(page,this.worldMode?'':LAYERS[this.layer].name,nameX,headerY,nameW,this.controlH,13*u,C.muted);
  this.mapW=right-pad-gap-sideW;this.mapH=bottom-top;
  if(this.mapW<300*u||this.mapH<190*u){UI.text(page,'请横屏查看旅途地图',pad,h/2-30,right-pad,60,18*u,C.ink,true);return;}
  const frame=UI.panel(page,'MapFrame',pad,top,this.mapW,this.mapH,C.dark,false);
  const viewport=UI.place(frame,new AtlasViewport(),'MapViewport',0,0,this.mapW,this.mapH);this.viewport=viewport;this.createField(viewport);
  this.controls(frame);this.sidebar(page,pad+this.mapW+gap,top,sideW,this.mapH);this.transform();
  if(this.legendOpen)this.legend(frame,8*u,42*u,166*u,Math.min(this.mapH-this.controlH-62*u,200*u));
  if(this.regionMenuOpen)this.regionMenu(page,pad+8*u,top+44*u,160*u);
 }
 private button(parent:GComponent,name:string,title:string,x:number,y:number,w:number,h:number,run:()=>void,active=false,gold=false){
  const button=UI.button(parent,name,title,x,y,w,h,()=>{if(!this.hud.mapTravel.busy)this.later(run);},false,this.font);
  for(const key of ['QuietBronze','ActiveTeal','Selected']){const child=button.getChild(key);if(child)child.visible=false;}
  const art=UI.image(button,'EquipmentButton',gold?'prep-button-gold-v2':active?'rpg-selection-frame-v3':'prep-button-dark-v2',0,0,w,h,Color.WHITE,true);button.setChildIndex(art,0);
  button.getTextField().color=gold?C.dark:active?GOLD:C.ink;return button;
 }
 private tab(parent:GComponent,name:string,title:string,x:number,y:number,w:number,run:()=>void,active:boolean):void{
  const tab=this.button(parent,name,title,x,y,w,this.controlH,run,active);
  tab.getChild('EquipmentButton').visible=false;
  if(active)UI.image(tab,'ActiveUnderline','rpg-active-rule-v4',0,this.controlH-6*this.unit,w,6*this.unit,Color.WHITE);
 }
 private destinations():Waypoint[]{return Object.values(AREAS).filter(area=>waypointUnlocked(this.game.state.flags,area)).map(area=>authoredWaypoint(area)!).sort((a,b)=>this.layerFor(a.area)-this.layerFor(b.area)||a.id.localeCompare(b.id));}
 private selectWaypoint(id:string):void{this.waypoint=id;this.selected=id;this.localMode=false;this.worldMode=false;this.layer=this.layerFor(id);this.hud.mapTravel.error='';this.reset();this.build();this.zoom=Math.max(this.zoom,1.5);const p=this.position(id);this.pan={x:(this.fieldW/2-p.x)*this.zoom,y:(this.fieldH/2-p.y)*this.zoom};this.transform();}
 private reset():void{this.zoom=1;this.pan={x:0,y:0};this.needsFit=true;}
 private regionMenu(parent:GComponent,x:number,y:number,w:number):void{
  const dismiss=UI.place(parent,new GComponent(),'map:regions:dismiss',0,0,this.hud.width,this.hud.height);dismiss.opaque=true;dismiss.onClick(()=>this.later(()=>{this.regionMenuOpen=false;this.build();}));
  const columns=LAYERS.length*(this.controlH+6)+14>this.hud.height-y-12?2:1,itemW=columns===2?Math.max(180,w*.7):w,rows=Math.ceil(LAYERS.length/columns),pickerW=itemW*columns;
  const picker=UI.panel(parent,'MapRegionPicker',Math.min(x,this.hud.width-pickerW-12),y,pickerW,rows*(this.controlH+6)+14,C.panel);
  LAYERS.forEach((layer,index)=>UI.button(picker,'map:layer:'+layer.id,layer.name,7+index%columns*itemW,7+Math.floor(index/columns)*(this.controlH+6),itemW-14,this.controlH,()=>this.later(()=>{this.localMode=false;this.worldMode=false;this.layer=index;this.selected='';this.regionMenuOpen=false;this.reset();this.show(this.game,this.visited);}),!this.localMode&&this.layer===index,this.font));
 }
 private legend(parent:GComponent,x:number,y:number,w:number,h:number):void{
  const u=this.unit,panel=UI.panel(parent,'MapLegend',x,y,w,h,C.panel),rows:[string,Color,string][]=[['◆',CYAN,T('legend.player')],['rune',C.purple,T('legend.waypoint')],['○',CYAN,T('legend.exit')],['◇',GOLD,T('legend.quest')],['●',GREEN,T('legend.npc')],['⚑',GOLD,T('legend.mark')]];
  const line=(h-16*u)/rows.length;
  rows.forEach(([symbol,color,text],i)=>{if(symbol==='rune'){const icon=UI.place(panel,new GGraph(),'WaypointLegend',12*u,8*u+i*line+(line-18*u)/2,18*u,18*u);icon.touchable=false;this.exitRune(icon);}else UI.text(panel,symbol,8*u,8*u+i*line,28*u,line,this.font,color,true);UI.text(panel,text,38*u,8*u+i*line,w-44*u,line,12*u,C.ink);});
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
   const snapshot=UI.place(field,new GComponent(),'TerrainSnapshot',0,0,this.fieldW,this.fieldH);snapshot.touchable=false;this.capture=new LocalMapCapture(snapshot.node,area,0,0,this.fieldW,this.fieldH);
   const fog=UI.place(field,new GGraph(),'UnexploredFog',0,0,this.fieldW,this.fieldH);fog.touchable=false;Chart.drawFog(fog._content,area,this.mapScale,this.fieldW/2,-this.fieldH/2);
   for(const poi of this.pois())this.localPin(field,poi);
   if(this.localMark)this.localPin(field,{id:'custom',label:'自定标记',detail:'探索用标记',point:this.localMark,kind:'quest'},true);
   field.onClick((event:FUIEvent)=>{if(this.dragged)return;const p=field.globalToLocal(event.pos.x,event.pos.y),point={x:(p.x-this.fieldW/2)/this.mapScale,z:(this.fieldH/2-p.y)/this.mapScale};if(Math.abs(point.x)>area.width/2||Math.abs(point.z)>area.depth/2)return;this.localMark=point;this.selectedPoi='custom';this.waypoint='';this.later(()=>this.build());});
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
  else if(poi.kind==='npc'||poi.kind==='merchant')icon.drawEllipse(1,C.dark,color);else icon.drawRegularPolygon(1.5,poi.kind==='player'?C.ink:color,poi.kind==='player'?CYAN:C.dark,4,0);
  if(poi.id===this.selectedPoi){const ring=UI.place(marker,new GGraph(),'SelectedRing',size/2-12,size/2-12,24,24);ring.drawEllipse(1,color,Color.TRANSPARENT);ring.touchable=false;}
  if(custom)UI.text(marker,'⚑',size/2-12,size/2-18,24,32,this.font,GOLD,true);
  if(poi.kind==='exit'){
   const width=Math.max(140,Math.min(sys.isMobile?300:230,(poi.destination?.length??6)*this.font+24)),height=this.font+12,dx=Math.max(width/2+4,Math.min(this.fieldW-width/2-4,x))-x,below=y+24+height<this.fieldH;
   const labelX=(size-width)/2+dx,labelY=below?size/2+22:size/2-22-height;
   UI.fill(marker,'ExitNameBacking',labelX-3,labelY-2,width+6,height+4,new Color(16,11,26,242));const text=UI.text(marker,poi.destination??poi.label,labelX,labelY,width,height,this.font,poi.locked?C.purple:C.route,true);text.name='ExitDestinationName';text.node.name=text.name;text.touchable=false;
  }
  marker.onClick((event:FUIEvent)=>{event.propagationStopped=true;if(this.dragged)return;this.selectedPoi=poi.id;this.waypoint='';this.later(()=>this.build());});
 }
 private exitRune(icon:GGraph,locked=false):void{
  const g=icon._content,x=icon.width/2,y=-icon.height/2,r=Math.min(icon.width,icon.height)*.32,ink=new Color(16,11,26),purple=locked?new Color(196,165,237,165):C.purple,cyan=locked?new Color(131,205,230,155):C.route;
  g.strokeColor=ink;g.lineWidth=5;g.circle(x,y,r);g.stroke();g.strokeColor=purple;g.lineWidth=2;g.circle(x,y,r);g.stroke();
  g.strokeColor=cyan;g.fillColor=ink;g.lineWidth=1.8;g.moveTo(x,y+r*.57);g.lineTo(x+r*.48,y);g.lineTo(x,y-r*.57);g.lineTo(x-r*.48,y);g.close();g.fill();g.stroke();
  for(let index=0;index<4;index++){const angle=index*Math.PI/2;g.moveTo(x+Math.cos(angle)*(r-1.6),y+Math.sin(angle)*(r-1.6));g.lineTo(x+Math.cos(angle)*(r+2.5),y+Math.sin(angle)*(r+2.5));}g.stroke();
 }
 private position(id:string):XY{const atlasId=id.startsWith('S')?id.slice(0,3):id,point=CAMPAIGN_ATLAS[atlasId]??AREAS[id].atlas;return{x:point.x/100*this.fieldW,y:(1-point.z/100)*this.fieldH};}
 private worldPin(parent:GComponent,area:AreaDef):void{
  const waypoint=waypointUnlocked(this.game.state.flags,area),p=this.position(area.id),known=this.known(area.id),current=area.id===this.currentId(),selected=area.id===this.selected,size=this.controlH,color=current?CYAN:selected?GOLD:known?C.ink:C.muted;
  const marker=UI.place(parent,new GComponent(),'map:place:'+area.id,p.x,p.y,size,size);marker.setPivot(.5,.5,true);marker.opaque=true;const icon=UI.place(marker,new GGraph(),'MarkerIcon',size/2-9,size/2-9,18,18);icon.touchable=false;if(waypoint){icon.setPosition(size/2-13*this.unit,size/2-13*this.unit);icon.setSize(26*this.unit,26*this.unit);this.exitRune(icon);}else icon.drawRegularPolygon(1.5,color,C.dark,4,0);
  if(current)UI.text(marker,'◆',size/2+8*this.unit,size/2-17*this.unit,18*this.unit,24*this.unit,14*this.unit,CYAN,true);
  if(selected||current){const width=Math.max(90*this.unit,area.name.length*this.font+12),labelY=p.y>this.fieldH*.6?size/2-this.font-26*this.unit:size/2+16*this.unit;UI.fill(marker,'LabelBacking',(size-width)/2,labelY,width,this.font+8,new Color(C.dark.r,C.dark.g,C.dark.b,230));UI.text(marker,area.name,(size-width)/2,labelY,width,this.font+8,this.font,color,true);}
  marker.onClick((event:FUIEvent)=>{event.propagationStopped=true;if(!this.dragged){if(waypoint)this.later(()=>this.selectWaypoint(area.id));else{this.selected=area.id;this.waypoint='';this.later(()=>this.build());}}});
 }
 private createWorld(field:GComponent):void{
  UI.image(field,'WorldIllustration','atlas/world',0,0,this.fieldW,this.fieldH,Color.WHITE);
  // The overview expresses regions. Exact local markers stay on authored regional atlases.
  const positions=[{x:.22,y:.53},{x:.57,y:.27},{x:.40,y:.73}];
  const cover=UI.place(field,new GGraph(),'WorldUnknownFog',0,0,this.fieldW,this.fieldH);cover.touchable=false;
  const known=LAYERS.map((layer,i)=>({layer,i})).filter(({layer})=>Object.keys(this.visited).some(id=>this.visited[id]&&layer.match(id)));
  const g=cover._content,step=16;for(let x=0;x<this.fieldW;x+=step)for(let y=0;y<this.fieldH;y+=step){const d=Math.min(...known.map(({i})=>Math.hypot((x+step/2)/this.fieldW-positions[i].x,(y+step/2)/this.fieldH-positions[i].y)));const t=Math.max(0,Math.min(1,(d-.11)/.14));g.fillColor=new Color(C.dark.r,C.dark.g,C.dark.b,Math.round(50+198*t*t*(3-2*t)));g.rect(x,-y-step,step,step);g.fill();}
  for(const {layer,i}of known){const p=positions[i],size=this.controlH,marker=UI.place(field,new GComponent(),'map:place:region:'+layer.id,p.x*this.fieldW,p.y*this.fieldH,size,size);marker.setPivot(.5,.5,true);marker.opaque=true;const icon=UI.place(marker,new GGraph(),'RegionRune',size/2-12*this.unit,size/2-12*this.unit,24*this.unit,24*this.unit);this.exitRune(icon);
   UI.text(marker,layer.name,size/2-65*this.unit,size/2+16*this.unit,130*this.unit,24*this.unit,this.font,GOLD,true);
   marker.onClick(()=>this.later(()=>{if(this.dragged)return;this.layer=i;this.worldMode=false;this.reset();this.build();}));
  }
 }
 private controls(frame:GComponent):void{
  const u=this.unit,h=this.controlH,pad=8*u,y=this.mapH-h-8*u;
  this.button(frame,'map:regions',LAYERS[this.layer].name+' ▾',pad,6*u,132*u,h,()=>{this.regionMenuOpen=!this.regionMenuOpen;this.legendOpen=false;this.build();});
  if(!this.worldMode)this.button(frame,'map:local',this.localMode?T('map.region'):T('map.local'),this.mapW-96*u,6*u,88*u,h,()=>{this.localMode=!this.localMode;this.reset();this.build();},this.localMode);
  this.button(frame,'map:legend',T('map.legend'),pad,y,52*u,h,()=>{this.legendOpen=!this.legendOpen;this.regionMenuOpen=false;this.build();},this.legendOpen);
  this.button(frame,'map:zoom-out','−',pad+60*u,y,h,h,()=>this.scale(.8));
  this.zoomLabel=UI.text(frame,Math.round(this.zoom*100)+'%',pad+112*u,y,40*u,h,12*u,C.ink,true);
  this.button(frame,'map:zoom-in','+',pad+156*u,y,h,h,()=>this.scale(1.25));
  const locateX=this.mapW-76*u;
  if(this.mapW>=360*u)this.button(frame,'map:fit',T('map.fit'),locateX-60*u,y,52*u,h,()=>this.fit());
  this.button(frame,'map:locate',T('map.locate'),locateX,y,68*u,h,()=>this.locate());
  UI.text(frame,this.worldMode?'':T('map.unknown'),8*u,this.mapH-h-32*u,this.mapW-16*u,20*u,11*u,C.muted);
 }
 private sidebar(parent:GComponent,x:number,y:number,w:number,h:number):void{
  const u=this.unit,pad=12*u,cw=w-pad*2,side=UI.panel(parent,'MapSidebar',x,y,w,h,C.panel,false);
  UI.image(side,'WaypointLeather','leather-inset-v8',0,0,w,h,Color.WHITE);UI.image(side,'WaypointFrame','rpg-selection-frame-v3',0,0,w,h,Color.WHITE,true);
  const points=this.destinations();UI.text(side,T('map.waypoints'),pad,6*u,cw,25*u,18*u,GOLD);UI.text(side,T('map.unlocked',{count:points.length}),pad,31*u,cw,20*u,12*u,C.muted);
  const foot=h-102*u,listY=58*u,listH=Math.max(48*u,foot-listY-6*u),rowH=52*u,gap=8*u;
  const host=this.hud.node('WaypointScroll',side.node,pad+cw/2,-listY-listH/2,cw,listH),viewport=this.hud.node('WaypointViewport',host,0,0,cw,listH);viewport.addComponent(Mask).type=Mask.Type.GRAPHICS_RECT;
  const content=this.hud.node('WaypointContent',viewport,0,listH/2,cw,Math.max(listH,points.length*(rowH+gap)-gap));content.getComponent(UITransform)!.setAnchorPoint(.5,1);
  const scroll=host.addComponent(ScrollView);scroll.content=content;scroll.horizontal=false;scroll.vertical=true;scroll.cancelInnerEvents=true;scroll.inertia=true;scroll.elastic=false;
  for(const [i,point]of points.entries()){
   const selected=point.id===this.waypoint,row=this.hud.node('map:waypoint:'+point.id,content,0,-i*(rowH+gap)-rowH/2,cw,rowH);
   UiSkin.asset(row,selected?'rpg-selection-frame-v3':'prep-button-dark-v2',cw,rowH,true);
   const button=row.addComponent(Button);button.transition=Button.Transition.SCALE;button.zoomScale=.98;button.interactable=!this.hud.mapTravel.busy;
   const rune=this.hud.text(row,'◎',-cw/2+18*u,0,24*u,24*u,F.color('quality.epic'),rowH);rune.horizontalAlign=Label.HorizontalAlign.CENTER;
   this.hud.text(row,point.name,16*u,10*u,cw-58*u,15*u,selected?GOLD:C.ink,24*u);
   this.hud.text(row,LAYERS[this.layerFor(point.id)].name+(point.area===this.current?' · '+T('map.current'):''),16*u,-12*u,cw-58*u,11*u,C.muted,20*u);
   row.on(Button.EventType.CLICK,()=>{this.listOffset=scroll.getScrollOffset().y;this.selectWaypoint(point.id);});
  }
  if(!points.length)UI.text(side,T('map.empty'),pad,listY,cw,listH,13*u,C.muted,true);
  this.listOffset=Math.max(0,Math.min(this.listOffset,points.length*(rowH+gap)-gap-listH));scroll.scrollToOffset(new Vec2(0,this.listOffset),0);
  const destination=AREAS[this.waypoint],status=destination?this.game.fastTravelAvailability(destination):{available:false,reason:T('map.select')},busy=this.hud.mapTravel.busy;
  const selectedArea=AREAS[this.selected],poi=this.localMode?(this.selectedPoi==='custom'&&this.localMark?{id:'custom',label:T('legend.mark'),point:this.localMark}:this.selectedPoi!=='player'?this.pois().find(p=>p.id===this.selectedPoi):undefined):!this.worldMode&&!this.waypoint&&selectedArea&&this.known(selectedArea.id)?{id:selectedArea.id,label:selectedArea.name,point:selectedArea.spawn}:undefined,note=this.hud.mapTravel.error||(busy?T('map.busy'):poi?poi.label+' · '+T('map.discovered'):status.reason);
  UI.image(side,'TravelRule','rpg-footer-rule-v4',pad,foot,cw,5*u,Color.WHITE);
  UI.text(side,note,pad,foot+6*u,cw,34*u,12*u,this.hud.mapTravel.error?F.color('state.failure'):C.muted,true);
  const travelWidth=poi?(cw-8*u)*.58:cw,travel=this.button(side,'map:travel',poi?T('map.walk'):busy?T('map.busy'):destination?T('map.travel',{name:destination.name}):T('map.select'),pad,h-this.controlH-12*u,travelWidth,this.controlH,()=>{if(poi){const area=this.localMode?this.current:poi.id,exit=this.localMode?AREAS[area].exits.find(e=>'exit:'+e.id===poi.id):undefined;this.hud.actions.navigate({area,point:{...poi.point},label:poi.label,exitId:exit?.id});}else this.hud.actions.click('map-travel:'+this.waypoint);},false,true);
  travel.enabled=(!!poi||status.available)&&!busy;travel.alpha=travel.enabled?1:.55;
  if(poi&&this.localMode)this.button(side,'map:mark',this.localMark?T('map.unmark'):T('map.mark'),pad+travelWidth+8*u,h-this.controlH-12*u,cw-travelWidth-8*u,this.controlH,()=>{this.localMark=this.localMark?null:{...poi.point};if(!this.localMark)this.selectedPoi='player';this.build();});
  const index=points.findIndex(p=>p.id===this.waypoint),itemTop=index*(rowH+gap);if(index>=0&&(itemTop<this.listOffset||itemTop+rowH>this.listOffset+listH)){this.listOffset=Math.max(0,Math.min(itemTop,points.length*(rowH+gap)-gap-listH));scroll.scrollToOffset(new Vec2(0,this.listOffset),0);}
 }
 private minimumZoom():number{return this.fieldW>0&&this.fieldH>0?Math.min(1,this.mapW/this.fieldW,this.mapH/this.fieldH):1;}
 private fit():void{this.field?.stopDrag();this.zoom=this.minimumZoom();this.pan={x:0,y:0};this.transform();}
 private scale(factor:number):void{this.field?.stopDrag();this.zoom=Math.max(this.minimumZoom(),Math.min(3,this.zoom*factor));this.transform();}
 private clusterMarkers():void{
  if(!this.field||this.localMode||this.worldMode)return;
  const field=this.field,old=Array.from({length:field.numChildren},(_,i)=>field.getChildAt(i)).filter(n=>n.name.startsWith('map:cluster:'));for(const node of old)node.dispose();
  const pins=Array.from({length:field.numChildren},(_,i)=>field.getChildAt(i)).filter(n=>n.name.startsWith('map:place:'));
  for(const pin of pins)pin.visible=true;
  const remaining=new Set(pins),gap=(this.controlH+8*this.unit)/this.zoom;
  while(remaining.size){const group=[remaining.values().next().value!];remaining.delete(group[0]);for(let i=0;i<group.length;i++)for(const pin of remaining)if(Math.hypot(group[i].x-pin.x,group[i].y-pin.y)<gap){group.push(pin);remaining.delete(pin);}
   if(group.length<2)continue;for(const pin of group)pin.visible=false;
   const x=group.reduce((v,p)=>v+p.x,0)/group.length,y=group.reduce((v,p)=>v+p.y,0)/group.length,size=this.controlH,cluster=UI.place(field,new GComponent(),'map:cluster:'+group.map(p=>p.name).join(','),x,y,size,size);cluster.setPivot(.5,.5,true);cluster.setScale(1/this.zoom,1/this.zoom);cluster.opaque=true;
   const icon=UI.place(cluster,new GGraph(),'ClusterRune',size/2-13*this.unit,size/2-13*this.unit,26*this.unit,26*this.unit);this.exitRune(icon);
   UI.text(cluster,String(group.length),size/2+9*this.unit,size/2-21*this.unit,20*this.unit,22*this.unit,13*this.unit,GOLD,true);
   cluster.onClick((event:FUIEvent)=>{event.propagationStopped=true;if(this.dragged)return;this.later(()=>{this.zoom=Math.min(3,this.zoom*1.6);this.pan={x:(this.fieldW/2-x)*this.zoom,y:(this.fieldH/2-y)*this.zoom};this.transform();});});
  }
 }
 private transform():void{
  if(!this.field||this.field.isDisposed)return;this.zoom=Math.max(this.minimumZoom(),Math.min(3,this.zoom));const limitX=Math.max(0,(this.fieldW*this.zoom-this.mapW)/2),limitY=Math.max(0,(this.fieldH*this.zoom-this.mapH)/2);this.pan.x=Math.max(-limitX,Math.min(limitX,this.pan.x));this.pan.y=Math.max(-limitY,Math.min(limitY,this.pan.y));this.field.setScale(this.zoom,this.zoom);this.field.setPosition((this.mapW-this.fieldW*this.zoom)/2+this.pan.x,(this.mapH-this.fieldH*this.zoom)/2+this.pan.y);
  if(this.viewport&&this.root){const global=this.viewport.localToGlobal(),origin=this.root.globalToLocal(global.x,global.y),width=this.fieldW*this.zoom,height=this.fieldH*this.zoom,extraX=Math.max(0,width-this.mapW),extraY=Math.max(0,height-this.mapH);this.field.dragBounds=new Rect(origin.x+(extraX?-extraX:(this.mapW-width)/2),origin.y+(extraY?-extraY:(this.mapH-height)/2),width+extraX,height+extraY);}
  for(let i=0;i<this.field.numChildren;i++){const child=this.field.getChildAt(i);if(child.name.startsWith('map:place:'))child.setScale(1/this.zoom,1/this.zoom);}this.clusterMarkers();if(this.zoomLabel)this.zoomLabel.text=Math.round(this.zoom*100)+'%';
 }
 private locate():void{if(this.worldMode){this.worldMode=false;this.localMode=false;this.layer=this.layerFor(this.current);this.reset();this.build();}if(this.localMode){const p=Chart.current?.state.player??AREAS[this.current].spawn;this.zoom=1.2;this.pan={x:-p.x*this.mapScale*this.zoom,y:p.z*this.mapScale*this.zoom};this.transform();}else{this.layer=this.layerFor(this.current);this.selected=this.currentId();this.reset();this.build();const p=this.position(this.currentId());this.zoom=1.4;this.pan={x:(this.fieldW/2-p.x)*this.zoom,y:(this.fieldH/2-p.y)*this.zoom};this.transform();}}
 inspect(){return{open:!!this.root&&!this.root.isDisposed,mode:this.worldMode?'world':this.localMode?'local':'region',waypoints:this.destinations().map(p=>p.id),selectedWaypoint:this.waypoint,travelBusy:this.hud.mapTravel.busy,region:LAYERS[this.layer].id,regionPickerOpen:this.regionMenuOpen,regionCount:LAYERS.length,regionAreaCount:this.areas().length,selectedPoi:this.selectedPoi,revealedExits:this.localMode?this.pois().filter(p=>p.kind==='exit').map(p=>({id:p.id,name:p.destination,locked:!!p.locked,x:p.point.x,z:p.point.z})):[],worldPositions:this.localMode?[]:this.areas().map(area=>({id:area.id,...this.position(area.id)}))};}
}
