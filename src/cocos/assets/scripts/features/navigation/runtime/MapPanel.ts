import {CompactMask as Mask} from '../../../shared/ui/CompactMask';
import {Color,KeyCode,Label,Node,Rect,ScrollBar,ScrollView,screen,UITransform,sys} from 'cc';
import {Event as FUIEvent,GComponent,GGraph,GRoot,GTextField} from 'fairygui-cc';
import {AREAS,R1_ROADS} from '../../world/data/WorldData';
import {playableArea,playableExits} from '../../journey/data/ChapterJourney';
import {HUNTING_GROUNDS,locationEntryLevel} from '../../world/data/MonsterEcology';
import {CAMPAIGN_ENEMY_TEMPLATES} from '../../campaign/data/Campaign';
import {CAMPAIGN_ATLAS} from '../../world/data/CampaignGeography';
import type {AreaDef,Point} from '../../../core/Contracts';
import type {Hud} from '../../../app/Hud';
import {AtlasUi as UI,AtlasViewport,ATLAS_COLORS as C} from '../../../shared/ui/AtlasUi';
import {LocalCartography as Chart} from './LocalCartography';
import {LocalMapCapture} from './LocalMapCapture';
import {UiSkin} from '../../../shared/ui/UiSkin';
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
type Filter='all'|'visited'|'checkpoint';
type Poi={id:string;label:string;detail:string;point:Point;kind:'player'|'exit'|'npc'|'quest'|'merchant'|'checkpoint';destination?:string;locked?:boolean};
const CYAN=C.route,GOLD=C.gold,RED=C.red,GREEN=C.green;

/** FairyGUI provides clipping, drag capture and buttons; map data stays real. */
export class MapPanel {
 private root:GRoot|null=null;private pendingHost:Node|null=null;private capture:LocalMapCapture|null=null;
 private regionMenuOpen=false;
 private current='';private visited:Record<string,boolean>={};private localMode=true;private layer=0;private selected='';private selectedPoi='player';private filter:Filter='all';private marked='';private localMark:Point|null=null;
 private zoom=1;private pan:XY={x:0,y:0};private needsFit=true;private field:GComponent|null=null;private viewport:GComponent|null=null;private mapW=0;private mapH=0;private fieldW=0;private fieldH=0;private mapScale=1;private zoomLabel:GTextField|null=null;private compact=false;private dragged=false;private font=18;private controlH=48;
 constructor(private readonly hud:Hud){}
 hide():void{Chart.flush();this.pendingHost=null;this.capture?.destroy();this.capture=null;this.field?.stopDrag();this.field=null;this.viewport=null;this.zoomLabel=null;if(this.root){const root=this.root;this.root=null;root.node.active=false;root.node.removeFromParent();root.dispose();}}
 refreshLayout():void{if(this.root&&!this.root.isDisposed&&this.compact!==this.compactMode())this.build();}
 private compactMode():boolean{return screen.windowSize.height/Math.max(1,screen.devicePixelRatio)<600;}
 private later(run:()=>void):void{const root=this.root;void Promise.resolve().then(()=>{if(root&&this.root===root&&!root.isDisposed)run();});}
 show(current:string,visited:Record<string,boolean>,selected?:string):void{
  if(current!==this.current){this.localMode=true;this.layer=this.layerFor(current);this.regionMenuOpen=false;this.zoom=1;this.pan={x:0,y:0};this.needsFit=true;this.selectedPoi='player';this.localMark=null;}
  this.current=current;this.visited=visited;
  if(selected&&AREAS[selected]){this.localMode=false;this.layer=this.layerFor(selected);this.selected=selected;}
  if(!this.areas().some(a=>a.id===this.selected))this.selected=this.areas().find(a=>a.id===this.currentId())?.id??this.areas()[0]?.id??'';
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
  if(!UI.ready){this.hud.show('旅途地图','正在展开地图…',[{label:'返回旅途',action:'close'}]);const host=this.hud.modal.children[0];this.pendingHost=host;void UI.load().then(()=>{if(this.pendingHost===host&&host.isValid)this.build();}).catch(()=>this.hud.show('地图载入失败','请返回旅途后重试。',[{label:'返回旅途',action:'close'}]));return;}
  const w=this.hud.width,h=this.hud.height;this.compact=this.compactMode();const cssH=screen.windowSize.height/Math.max(1,screen.devicePixelRatio);this.font=sys.isMobile?Math.max(26,Math.ceil(14.5*h/cssH)):18;this.controlH=sys.isMobile?Math.max(84,Math.ceil(46*h/cssH)):48;
  this.hud.modal.getComponent(UITransform)!.setContentSize(w,h);const root=GRoot.create();this.root=root;this.hud.modal.addChild(root.node);root.onWinResize();root.name='JourneyMap';root.node.name='JourneyMap';
  const page=UI.panel(root,'MapPage',0,0,w,h,C.background,false),pad=22,gap=16,legendW=sys.isMobile?210:182,sideW=sys.isMobile?324:268,top=this.controlH+40;
  this.mapW=w-pad*2-gap*2-legendW-sideW;this.mapH=h-top-26;
  if(this.mapW<300){UI.text(page,'请横屏查看旅途地图',24,h/2-60,w-48,70,this.font+6,C.ink,true);UI.button(page,'map:close','返回旅途',w/2-120,h/2+35,240,this.controlH,()=>this.hud.actions.click('close'),false,this.font);return;}
  UI.text(page,'旅 途 地 图',pad,10,legendW,this.controlH,this.font+8,GOLD,true);
  const tabW=sys.isMobile?176:145,tabX=pad+legendW+gap;
  UI.button(page,'map:local','区域地图',tabX,16,tabW,this.controlH,()=>this.later(()=>{this.localMode=true;this.regionMenuOpen=false;this.reset();this.build();}),this.localMode,this.font);
  const regionX=tabX+tabW+8,regionW=sys.isMobile?300:250;
  UI.button(page,'map:regions','世界地图 · '+LAYERS[this.layer].name+' ▾',regionX,16,regionW,this.controlH,()=>this.later(()=>{this.regionMenuOpen=!this.regionMenuOpen;this.build();}),!this.localMode,this.font);
  UI.button(page,'map:close',sys.isMobile?'返回旅途':'返回  Esc',w-pad-(sys.isMobile?180:146),16,sys.isMobile?180:146,this.controlH,()=>this.hud.actions.click('close'),false,this.font);
  this.legend(page,pad,top,legendW,this.mapH);
  const mapX=pad+legendW+gap,frame=UI.panel(page,'MapFrame',mapX,top,this.mapW,this.mapH,C.dark);
  const viewport=UI.place(frame,new AtlasViewport(),'MapViewport',4,4,this.mapW-8,this.mapH-8);this.viewport=viewport;this.mapW-=8;this.mapH-=8;this.createField(viewport);
  this.controls(frame);this.sidebar(page,mapX+this.mapW+8+gap,top,sideW,this.mapH+8);this.transform();
  if(this.regionMenuOpen)this.regionMenu(page,regionX,24+this.controlH,regionW);
 }
 private reset():void{this.zoom=1;this.pan={x:0,y:0};this.needsFit=true;}
 private regionMenu(parent:GComponent,x:number,y:number,w:number):void{
  const dismiss=UI.place(parent,new GComponent(),'map:regions:dismiss',0,0,this.hud.width,this.hud.height);dismiss.opaque=true;dismiss.onClick(()=>this.later(()=>{this.regionMenuOpen=false;this.build();}));
  const columns=LAYERS.length*(this.controlH+6)+14>this.hud.height-y-12?2:1,itemW=columns===2?Math.max(180,w*.7):w,rows=Math.ceil(LAYERS.length/columns),pickerW=itemW*columns;
  const picker=UI.panel(parent,'MapRegionPicker',Math.min(x,this.hud.width-pickerW-12),y,pickerW,rows*(this.controlH+6)+14,C.panel);
  LAYERS.forEach((layer,index)=>UI.button(picker,'map:layer:'+layer.id,layer.name,7+index%columns*itemW,7+Math.floor(index/columns)*(this.controlH+6),itemW-14,this.controlH,()=>this.later(()=>{this.localMode=false;this.layer=index;this.selected='';this.filter='all';this.regionMenuOpen=false;this.reset();this.show(this.current,this.visited);}),!this.localMode&&this.layer===index,this.font));
 }
 private legend(parent:GComponent,x:number,y:number,w:number,h:number):void{
  const panel=UI.panel(parent,'MapLegend',x,y,w,h,C.panel),area=AREAS[this.current];
  UI.text(panel,this.localMode?area.name:LAYERS[this.layer].name,14,16,w-28,60,this.font+4,GOLD,true);UI.image(panel,'LegendRule','divider',16,85,w-32,6,GOLD);
  const rows:[string,Color,string][]=[['◆',CYAN,'队伍位置'],['rune',C.purple,'区域入口'],['◇',GOLD,'任务地点'],['●',GREEN,'人物 / 盟友'],['●',RED,'附近敌人'],['⌂',GOLD,'休整点'],['⚑',GOLD,'自定标记']];
  const line=Math.min(54,(h-238)/rows.length);rows.forEach(([symbol,color,text],i)=>{if(symbol==='rune'){const icon=UI.place(panel,new GGraph(),'ExitRuneLegend',21,112+i*line+(line-24)/2,24,24);icon.touchable=false;this.exitRune(icon);}else UI.text(panel,symbol,14,112+i*line,36,line,this.font+2,color,true);UI.text(panel,text,54,112+i*line,w-68,line,this.font,C.ink);});
  UI.text(panel,'黑暗处尚未探索',14,h-110,w-28,50,this.font,C.muted,true);UI.text(panel,this.localMode?'点地图放置标记':'点地点查看详情',14,h-62,w-28,40,this.font,C.muted,true);
 }
 private createField(viewport:GComponent):void{
  const area=AREAS[this.current];
  if(this.localMode){this.mapScale=Math.max(this.mapW/area.width,this.mapH/area.depth)*1.06;this.fieldW=area.width*this.mapScale;this.fieldH=area.depth*this.mapScale;}
  else{const cover=Math.max(this.mapW/1536,this.mapH/1024);this.fieldW=1536*cover;this.fieldH=1024*cover;}
  if(this.localMode&&this.needsFit){this.zoom=this.minimumZoom();this.needsFit=false;}
  const field=UI.place(viewport,new GComponent(),'MapField',0,0,this.fieldW,this.fieldH);this.field=field;field.opaque=true;field.draggable=true;
  if(this.localMode){
   const floor=UI.place(field,new GGraph(),'CoordinateTerrain',0,0,this.fieldW,this.fieldH);floor.touchable=false;Chart.drawTerrain(floor._content,area,this.mapScale,this.fieldW/2,-this.fieldH/2);
   const snapshot=UI.place(field,new GComponent(),'TerrainSnapshot',0,0,this.fieldW,this.fieldH);snapshot.touchable=false;this.capture=new LocalMapCapture(snapshot.node,area,0,0,this.fieldW,this.fieldH);
   const fog=UI.place(field,new GGraph(),'UnexploredFog',0,0,this.fieldW,this.fieldH);fog.touchable=false;Chart.drawFog(fog._content,area,this.mapScale,this.fieldW/2,-this.fieldH/2);
   for(const poi of this.pois())this.localPin(field,poi);
   if(this.localMark)this.localPin(field,{id:'custom',label:'自定标记',detail:'探索用标记',point:this.localMark,kind:'quest'},true);
   field.onClick((event:FUIEvent)=>{if(this.dragged)return;const p=field.globalToLocal(event.pos.x,event.pos.y),point={x:(p.x-this.fieldW/2)/this.mapScale,z:(this.fieldH/2-p.y)/this.mapScale};if(Math.abs(point.x)>area.width/2||Math.abs(point.z)>area.depth/2)return;this.localMark=point;this.selectedPoi='custom';this.later(()=>this.build());});
  }else{
   UI.image(field,'TerrainIllustration','atlas/'+LAYERS[this.layer].image,0,0,this.fieldW,this.fieldH,Color.WHITE);
   const fog=UI.place(field,new GGraph(),'WorldExplorationFog',0,0,this.fieldW,this.fieldH);fog.touchable=false;const g=fog._content,known=this.areas().filter(a=>this.known(a.id)).map(a=>this.position(a.id)),step=32;
   for(let x=0;x<this.fieldW;x+=step)for(let y=0;y<this.fieldH;y+=step){const d=Math.min(...known.map(p=>Math.hypot(x+step/2-p.x,y+step/2-p.y)));g.fillColor=new Color(C.dark.r,C.dark.g,C.dark.b,d<135?0:d<190?160:245);g.rect(x,-y-step,step,step);g.fill();}
   const roads=UI.place(field,new GGraph(),'RoadOverlay',0,0,this.fieldW,this.fieldH);roads.touchable=false;const rg=roads._content;rg.lineWidth=1.7;rg.strokeColor=new Color(C.line.r,C.line.g,C.line.b,160);
   for(const[a,b]of this.edges())if(this.known(a)&&this.known(b)){const p=this.position(a),q=this.position(b);rg.moveTo(p.x,-p.y);rg.lineTo(q.x,-q.y);rg.stroke();}
   const route=this.route();rg.lineWidth=3;rg.strokeColor=C.route;for(let i=1;i<route.length;i++)if(this.known(route[i-1])&&this.known(route[i])){const p=this.position(route[i-1]),q=this.position(route[i]);rg.moveTo(p.x,-p.y);rg.lineTo(q.x,-q.y);rg.stroke();}
   for(const a of this.areas())if(this.filter==='all'||this.filter==='visited'&&this.known(a.id)||this.filter==='checkpoint'&&this.known(a.id)&&(a.checkpoint||a.objects.some(o=>o.action==='checkpoint')))this.worldPin(field,a);
  }
  field.on(FUIEvent.TOUCH_BEGIN,()=>{this.dragged=false;});field.on(FUIEvent.DRAG_START,()=>{this.dragged=true;});field.on(FUIEvent.DRAG_MOVE,()=>{this.pan={x:field.x-(this.mapW-this.fieldW*this.zoom)/2,y:field.y-(this.mapH-this.fieldH*this.zoom)/2};});viewport.on(FUIEvent.MOUSE_WHEEL,(event:FUIEvent)=>{event.propagationStopped=true;if(event.mouseWheelDelta)this.scale(event.mouseWheelDelta>0?1.15:1/1.15);});
 }
 private pois():Poi[]{
  const area=AREAS[this.current],game=Chart.current,p=game?.state.area===area.id?game.state.player:area.spawn;const result:Poi[]=[{id:'player',label:'拉斐尔',detail:'队伍当前位置',point:p,kind:'player'}];
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
  marker.onClick((event:FUIEvent)=>{event.propagationStopped=true;if(this.dragged)return;this.selectedPoi=poi.id;this.later(()=>this.build());});
 }
 private exitRune(icon:GGraph,locked=false):void{
  const g=icon._content,x=icon.width/2,y=-icon.height/2,r=Math.min(icon.width,icon.height)*.32,ink=new Color(16,11,26),purple=locked?new Color(196,165,237,165):C.purple,cyan=locked?new Color(131,205,230,155):C.route;
  g.strokeColor=ink;g.lineWidth=5;g.circle(x,y,r);g.stroke();g.strokeColor=purple;g.lineWidth=2;g.circle(x,y,r);g.stroke();
  g.strokeColor=cyan;g.fillColor=ink;g.lineWidth=1.8;g.moveTo(x,y+r*.57);g.lineTo(x+r*.48,y);g.lineTo(x,y-r*.57);g.lineTo(x-r*.48,y);g.close();g.fill();g.stroke();
  for(let index=0;index<4;index++){const angle=index*Math.PI/2;g.moveTo(x+Math.cos(angle)*(r-1.6),y+Math.sin(angle)*(r-1.6));g.lineTo(x+Math.cos(angle)*(r+2.5),y+Math.sin(angle)*(r+2.5));}g.stroke();
 }
 private position(id:string):XY{const point=CAMPAIGN_ATLAS[id]??AREAS[id].atlas;return{x:point.x/100*this.fieldW,y:(1-point.z/100)*this.fieldH};}
 private worldPin(parent:GComponent,area:AreaDef):void{
  const p=this.position(area.id),known=this.known(area.id),current=area.id===this.currentId(),selected=area.id===this.selected,size=sys.isMobile?Math.max(84,this.controlH):52,color=current?CYAN:selected?GOLD:known?C.ink:C.muted;
  const marker=UI.place(parent,new GComponent(),'map:place:'+area.id,p.x,p.y,size,size);marker.setPivot(.5,.5,true);marker.opaque=true;const icon=UI.place(marker,new GGraph(),'MarkerIcon',size/2-9,size/2-9,18,18);icon.touchable=false;icon.drawRegularPolygon(1.5,color,C.dark,4,0);
  UI.text(marker,current?'◆':known?'·':'?',size/2-10,size/2-15,20,30,22,color,true);
  if(selected||current||known){const width=Math.max(140,area.name.length*this.font+12);UI.fill(marker,'LabelBacking',(size-width)/2,size/2+14,width,this.font+10,new Color(C.dark.r,C.dark.g,C.dark.b,230));UI.text(marker,area.name,(size-width)/2,size/2+14,width,this.font+10,this.font,color,true);}
  marker.onClick(()=>{if(!this.dragged){this.selected=area.id;this.later(()=>this.build());}});
 }
 private controls(frame:GComponent):void{
  const h=this.controlH,pad=12,y=this.mapH-h-12,w=sys.isMobile?92:50;
  UI.button(frame,'map:zoom-out','−',pad,y,w,h,()=>this.scale(.8),false,this.font+8);UI.button(frame,'map:zoom-in','+',pad+w+8,y,w,h,()=>this.scale(1.25),false,this.font+8);
  const fitW=sys.isMobile?144:90,locateW=sys.isMobile?172:126;UI.button(frame,'map:fit','全览',this.mapW-fitW-locateW-28,y,fitW,h,()=>this.fit(),false,this.font);UI.button(frame,'map:locate','定位队伍',this.mapW-locateW-12,y,locateW,h,()=>this.locate(),false,this.font);
  if(this.mapW>650)this.zoomLabel=UI.text(frame,Math.round(this.zoom*100)+'%',pad+w*2+24,y,90,h,this.font,C.muted,true);UI.text(frame,'N',16,14,30,30,this.font,C.ink,true);
 }
 private sidebar(parent:GComponent,x:number,y:number,w:number,h:number):void{
  const side=UI.panel(parent,'MapSidebar',x,y,w,h,C.panel),pad=18,cw=w-pad*2;
  UI.text(side,this.localMode?'探索手记':'已发现的地点',pad,14,cw,50,this.font+4,GOLD,true);UI.image(side,'SidebarRule','divider',pad,72,cw,6,GOLD);
  if(this.localMode){
   const area=AREAS[this.current],poi=this.selectedPoi==='custom'&&this.localMark?{label:'自定标记',detail:'指路标记不改变入口条件。',point:this.localMark}:this.pois().find(p=>p.id===this.selectedPoi)??this.pois()[0];
   const taskY=h-this.controlH-190;UI.text(side,poi.label,pad,99,cw,60,this.font+4,C.ink);UI.text(side,`X ${Math.round(poi.point.x)}  ·  Z ${Math.round(poi.point.z)}`,pad,158,cw,42,this.font,C.muted);this.bodyScroll(side,pad,211,cw,Math.max(38,taskY-222),poi.detail);
   const objective=Chart.current?.explorationGuide()??area.subtitle;UI.text(side,'狩猎与可选委托',pad,taskY,cw,40,this.font,GOLD);this.bodyScroll(side,pad,taskY+42,cw,124,objective);
   const buttonW=(cw-10)/2,exit=area.exits.find(e=>e.id===this.selectedPoi||'exit:'+e.id===this.selectedPoi);
   UI.button(side,'map:navigate','前往此处',pad,h-this.controlH-12,buttonW,this.controlH,()=>this.later(()=>this.hud.actions.navigate({area:this.current,point:{...poi.point},label:poi.label,exitId:exit?.id})),false,this.font);
   UI.button(side,'map:mark',this.localMark?'清除标记':'标记此处',pad+buttonW+10,h-this.controlH-12,buttonW,this.controlH,()=>this.later(()=>{this.localMark=this.localMark?null:{...poi.point};this.build();}),!!this.localMark,this.font);
  }else{
   const filters:[Filter,string][]=[['all','全部地点'],['visited','已抵达'],['checkpoint','休整点']],index=filters.findIndex(([id])=>id===this.filter);UI.button(side,'map:filter:cycle','筛选 · '+filters[index][1],pad,93,cw,this.controlH,()=>this.later(()=>{this.filter=filters[(index+1)%3][0];this.build();}),false,this.font);
   const area=AREAS[this.selected];if(!area)return;const infoTop=104+this.controlH;UI.text(side,area.name,pad,infoTop,cw,55,this.font+6,C.ink);UI.text(side,area.id===this.currentId()?'队伍所在区域':this.known(area.id)?'已抵达':'尚未抵达',pad,infoTop+57,cw,42,this.font,this.known(area.id)?CYAN:C.muted);this.bodyScroll(side,pad,infoTop+112,cw,Math.max(38,Math.min(140,h-infoTop-this.controlH-180)),`通行等级 Lv${locationEntryLevel(area.id)}。${HUNTING_GROUNDS[area.id]?`\n狩猎 Lv${HUNTING_GROUNDS[area.id].level}：${[...new Set(HUNTING_GROUNDS[area.id].packs.flat())].map(id=>CAMPAIGN_ENEMY_TEMPLATES[id]?.name??id).join('、')}。\n怪群可反复狩猎；刷怪经验每日递减并设上限，掉落仍可获取。`:''}\n${this.known(area.id)?'可选调查：'+area.subtitle:'前往探索后记录地形、入口与人物。'}`);
   UI.text(side,'自动步行 · 遵守道路与等级限制',pad,h-this.controlH-64,cw,42,this.font,C.muted);const buttonW=(cw-10)/2;
   UI.button(side,'map:navigate','前往此处',pad,h-this.controlH-12,buttonW,this.controlH,()=>this.later(()=>this.hud.actions.navigate({area:area.id,point:{...area.spawn},label:area.name})),false,this.font);
   UI.button(side,'map:mark',this.marked===area.id?'取消标记':'标记此处',pad+buttonW+10,h-this.controlH-12,buttonW,this.controlH,()=>this.later(()=>{this.marked=this.marked===area.id?'':area.id;this.build();}),this.marked===area.id,this.font);
  }
 }
 private bodyScroll(parent:GComponent,x:number,y:number,w:number,h:number,value:string):void{
  const host=this.hud.node('MapDetailScroll',parent.node,x+w/2,-y-h/2,w,h),viewport=this.hud.node('Viewport',host,0,0,w,h);viewport.addComponent(Mask).type=Mask.Type.GRAPHICS_RECT;
  const content=this.hud.node('Content',viewport,0,h/2,w,h);content.getComponent(UITransform)!.setAnchorPoint(.5,1);
  const label=this.hud.text(content,value,-5,-6,w-12,this.font,C.ink,h);label.node.getComponent(UITransform)!.setAnchorPoint(.5,1);label.overflow=Label.Overflow.RESIZE_HEIGHT;label.verticalAlign=Label.VerticalAlign.TOP;label.enableWrapText=true;label.updateRenderData(true);content.getComponent(UITransform)!.setContentSize(w,Math.max(h,label.node.getComponent(UITransform)!.height+12));
  const scroll=host.addComponent(ScrollView);scroll.content=content;scroll.horizontal=false;scroll.vertical=true;scroll.cancelInnerEvents=true;
  const track=this.hud.node('DetailScrollbar',host,w/2-2,0,3,h),bar=track.addComponent(ScrollBar),handle=UiSkin.asset(track,'bar-focus-fill',3,24,false);handle.node.setScale(1,1,1);handle.node.getComponent(UITransform)!.setContentSize(3,24);handle.color=C.route;bar.handle=handle;bar.direction=1;bar.enableAutoHide=false;scroll.verticalScrollBar=bar;
 }
 private minimumZoom():number{return this.fieldW>0&&this.fieldH>0?Math.min(1,this.mapW/this.fieldW,this.mapH/this.fieldH):1;}
 private fit():void{this.field?.stopDrag();this.zoom=this.minimumZoom();this.pan={x:0,y:0};this.transform();}
 private scale(factor:number):void{this.field?.stopDrag();this.zoom=Math.max(this.minimumZoom(),Math.min(3,this.zoom*factor));this.transform();}
 private transform():void{
  if(!this.field||this.field.isDisposed)return;this.zoom=Math.max(this.minimumZoom(),Math.min(3,this.zoom));const limitX=Math.max(0,(this.fieldW*this.zoom-this.mapW)/2),limitY=Math.max(0,(this.fieldH*this.zoom-this.mapH)/2);this.pan.x=Math.max(-limitX,Math.min(limitX,this.pan.x));this.pan.y=Math.max(-limitY,Math.min(limitY,this.pan.y));this.field.setScale(this.zoom,this.zoom);this.field.setPosition((this.mapW-this.fieldW*this.zoom)/2+this.pan.x,(this.mapH-this.fieldH*this.zoom)/2+this.pan.y);
  if(this.viewport&&this.root){const global=this.viewport.localToGlobal(),origin=this.root.globalToLocal(global.x,global.y),width=this.fieldW*this.zoom,height=this.fieldH*this.zoom,extraX=Math.max(0,width-this.mapW),extraY=Math.max(0,height-this.mapH);this.field.dragBounds=new Rect(origin.x+(extraX?-extraX:(this.mapW-width)/2),origin.y+(extraY?-extraY:(this.mapH-height)/2),width+extraX,height+extraY);}
  for(let i=0;i<this.field.numChildren;i++){const child=this.field.getChildAt(i);if(child.name.startsWith('map:place:'))child.setScale(1/this.zoom,1/this.zoom);}if(this.zoomLabel)this.zoomLabel.text=Math.round(this.zoom*100)+'%';
 }
 private locate():void{if(this.localMode){const p=Chart.current?.state.player??AREAS[this.current].spawn;this.zoom=1.2;this.pan={x:-p.x*this.mapScale*this.zoom,y:p.z*this.mapScale*this.zoom};this.transform();}else{this.layer=this.layerFor(this.current);this.selected=this.currentId();this.reset();this.build();const p=this.position(this.currentId());this.zoom=1.4;this.pan={x:(this.fieldW/2-p.x)*this.zoom,y:(this.fieldH/2-p.y)*this.zoom};this.transform();}}
 inspect(){return{open:!!this.root&&!this.root.isDisposed,mode:this.localMode?'local':'region',region:LAYERS[this.layer].id,regionPickerOpen:this.regionMenuOpen,regionCount:LAYERS.length,regionAreaCount:this.areas().length,selectedPoi:this.selectedPoi,revealedExits:this.localMode?this.pois().filter(p=>p.kind==='exit').map(p=>({id:p.id,name:p.destination,locked:!!p.locked,x:p.point.x,z:p.point.z})):[],worldPositions:this.localMode?[]:this.areas().map(area=>({id:area.id,...this.position(area.id)}))};}
}
