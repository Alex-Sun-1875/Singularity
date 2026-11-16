import {viewportMetrics} from '../../../platform/ViewportMetrics';
import {CompactMask as Mask} from '../../../shared/ui/CompactMask';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {BlockInputEvents,ButtonComponent as Button,Color,Graphics,isValid,Label,Node,ScrollBar,ScrollView,sys,UITransform} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import {EQUIPMENT} from '../data/Equipment';
import {EquipmentArt,type EquipmentArtDef,type EquipmentArtManifest,type EquipmentFamily} from './EquipmentArt';
import type {Hud} from '../../../app/Hud';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {GoldPanelHeader} from '../../../shared/ui/GoldPanelHeader';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';

type Selection={family:EquipmentFamily;selected:Partial<Record<EquipmentFamily,string>>};
const selections=new WeakMap<GameSession,Selection>();
const galleries=new WeakMap<Node,Gallery>();
const FAMILIES:[EquipmentFamily,string][]=[['sword','剑'],['bow','弓'],['staff','杖'],['oath','誓卫'],['wind','游猎'],['seeker','观星'],['jewelry','首饰']];
const GRADES=['普通','精良','稀有','史诗','传奇'];
const COLORS=[C.unknown,C.green,C.route,C.purple,C.gold];

/** Read-only design comparison. Selection belongs to this UI session, never the save. */
export function renderEquipmentGallery(hud:Hud,game:GameSession,host:Node,width:number,height:number):void{
 galleries.get(host)?.destroy();
 const selection=selections.get(game)??{family:'sword',selected:{}};selections.set(game,selection);
 const gallery=new Gallery(hud,game,host,width,height,selection);galleries.set(host,gallery);gallery.show();
}

class Gallery {
 private readonly root:Node;private readonly font:number;private readonly hit:number;private readonly gap:number;
 private data:EquipmentArtManifest|null=null;private revision=0;private disposed=false;private main:Node|null=null;private detail:Node|null=null;
 private readonly dispose=()=>this.destroy();
 constructor(private readonly hud:Hud,private readonly game:GameSession,host:Node,private readonly width:number,private readonly height:number,private readonly state:Selection){
  const cssHeight=viewportMetrics.windowSize.height/Math.max(1,viewportMetrics.devicePixelRatio);
  this.font=sys.isMobile?Math.max(28,Math.ceil(14*hud.height/cssHeight)):17;
  this.hit=sys.isMobile?Math.max(84,Math.ceil(48*hud.height/cssHeight)):48;
  this.gap=sys.isMobile?14:10;
  this.root=hud.node('EquipmentGallery',host,0,0,width,height);hud.modalDisposers.add(this.dispose);
 }
 private alive(node=this.root):boolean{return !this.disposed&&isValid(this.root,true)&&isValid(node,true);}
 private clear(parent:Node):void{for(const child of [...parent.children]){child.active=false;child.removeFromParent();child.destroy();}}
 private label(parent:Node,text:string,x:number,y:number,w:number,h:number,size=this.font,color=C.ink):Label{
  const label=this.hud.text(parent,text,x,y,w,size,color,h);label.lineHeight=size*1.22;label.overflow=Label.Overflow.CLAMP;label.enableWrapText=true;return label;
 }
 private center(parent:Node,text:string,y:number,w:number,h:number,size=this.font,color=C.ink):Label{
  const label=this.label(parent,text,0,y,w,h,size,color);label.horizontalAlign=Label.HorizontalAlign.CENTER;return label;
 }
 private button(parent:Node,text:string,x:number,y:number,w:number,h:number,name:string,click:()=>void,selected=false):Node{
  const node=this.hud.node(name,parent,x,y,w,h);UiSkin.button(node,w,h);this.center(node,text,0,w-18,h-8);
  if(selected){const g=node.addComponent(CompactGraphics);g.strokeColor=C.goldLight;g.lineWidth=2;g.roundRect(-w/2+2,-h/2+2,w-4,h-4,4);g.stroke();UiSkin.selected(node,w,h);}
  node.on(Button.EventType.CLICK,click);return node;
 }
 private short(text:string,characters:number):string{return text.length>characters?text.slice(0,Math.max(1,characters-1))+'…':text;}
 private currentItems():[string,EquipmentArtDef][]{return Object.entries(this.data?.items??{}).filter(([,art])=>art.family===this.state.family).sort((a,b)=>a[1].grade-b[1].grade);}
 private owned(id:string):boolean{return (this.game.state.inventory[id]??0)>0;}
 private mapped(art:EquipmentArtDef):string[]{return (art.existingIds??[]).filter(id=>!!EQUIPMENT[id]);}
 private inventory(art:EquipmentArtDef):string{
  const ids=this.mapped(art);return ids.length?ids.map(id=>EQUIPMENT[id].name+' · '+(this.owned(id)?'已获得':'尚未获得')).join('；'):'后续设计';
 }
 private status(art:EquipmentArtDef):{text:string;color:Color}{
  const ids=this.mapped(art),count=ids.filter(id=>this.owned(id)).length;
  return !ids.length?{text:'后续设计',color:C.muted}:count===ids.length?{text:'已获得',color:C.green}:count?{text:`已获得 ${count}/${ids.length}`,color:C.green}:{text:'尚未获得',color:C.unknown};
 }
 show():void{
  const request=++this.revision;this.clear(this.root);this.center(this.root,'正在载入装备图鉴…',0,this.width-40,60,this.font,C.muted);
  void EquipmentArt.manifest().then(data=>{if(!this.alive()||request!==this.revision)return;this.data=data;this.paint();}).catch(()=>{
   if(!this.alive()||request!==this.revision)return;this.clear(this.root);
   this.center(this.root,'装备图鉴载入失败',this.hit/2+12,this.width-40,48,this.font,C.red);
   this.button(this.root,'重试',0,-this.hit/2-10,Math.max(180,this.hit*2),this.hit,'gallery:retry',()=>this.show());
  });
 }
 private paint():void{
  if(!this.alive())return;this.revision++;this.clear(this.root);this.detail=null;
  const main=this.hud.node('GalleryComparison',this.root,0,0,this.width,this.height);this.main=main;
  const familyW=(this.width-this.gap*6)/7;
  FAMILIES.forEach(([family,name],i)=>this.button(main,name,-this.width/2+familyW/2+i*(familyW+this.gap),this.height/2-this.hit/2,familyW,this.hit,'gallery:family:'+family,()=>{this.state.family=family;this.paint();},this.state.family===family));
  const items=this.currentItems();
  if(items.length!==5||items.some(([,art],i)=>art.grade!==i+1)){
   this.center(main,'此分类的五阶设计资料尚未完整载入',-12,this.width-40,70,this.font,C.red);
   this.button(main,'重试资料',0,-this.hit-18,220,this.hit,'gallery:retry-family',()=>this.show());return;
  }
  let selected=items.find(([id])=>id===this.state.selected[this.state.family]);if(!selected)selected=items[0];this.state.selected[this.state.family]=selected[0];
  // CharacterPanel's return control starts just above the host's lower edge.
  // Reserve a real touch gap instead of letting the two action targets overlap.
  const footerGap=this.gap+2,summaryH=Math.max(this.hit+footerGap,this.font*2.75),cardsH=this.height-this.hit-summaryH-this.gap*2;
  const cardW=(this.width-this.gap*4)/5,cardsY=this.height/2-this.hit-this.gap-cardsH/2;
  items.forEach(([id,art],i)=>this.card(main,id,art,-this.width/2+cardW/2+i*(cardW+this.gap),cardsY,cardW,cardsH,id===selected![0]));
  const summary=this.hud.node('GallerySelectionDetails',main,0,-this.height/2+summaryH/2,this.width,summaryH),zoomW=Math.max(176,this.hit*2.1),textW=this.width-zoomW-this.gap-12;
  const name=selected[1].name,art=selected[1],line=this.font*1.25,characters=Math.max(12,Math.floor(textW/this.font)),ids=this.mapped(art);
  const title=ids.length===1&&EQUIPMENT[ids[0]].name===name?this.inventory(art):name+' · '+this.inventory(art);
  const lines=[title,'材质 · '+(art.materials?.join('、')||'资料待补充')+'   结构 · '+(art.features?.join('、')||art.description||'资料待补充')];
  lines.forEach((text,i)=>this.label(summary,this.short(text,characters),-this.width/2+textW/2+6,line*(.5-i),textW,line,this.font,i===0?C.goldLight:C.ink));
  this.button(summary,'放大查看',this.width/2-zoomW/2,footerGap/2,zoomW,this.hit,'gallery:enlarge',()=>this.enlarge(art));
 }
 private card(parent:Node,id:string,art:EquipmentArtDef,x:number,y:number,w:number,h:number,selected:boolean):void{
  const card=this.hud.node('gallery:design:'+id,parent,x,y,w,h),g=card.addComponent(CompactGraphics),color=COLORS[art.grade-1]??C.gold;
  g.fillColor=selected?C.button:C.dark;g.roundRect(-w/2,-h/2,w,h,4);g.fill();g.strokeColor=selected?C.goldLight:color;g.lineWidth=selected?3:1;g.roundRect(-w/2+2,-h/2+2,w-4,h-4,4);g.stroke();
  const button=card.addComponent(Button);button.transition=Button.Transition.COLOR;button.target=card;button.normalColor=Color.WHITE;button.hoverColor=C.goldLight;button.pressedColor=C.gold;button.duration=.1;
  card.on(Button.EventType.CLICK,()=>{this.state.selected[this.state.family]=id;this.paint();});
  const line=this.font*1.25,artH=Math.max(this.hit,h-line*3-18),image=this.hud.node('GalleryArtwork',card,0,h/2-line-6-artH/2,w-20,artH);
  this.center(card,GRADES[art.grade-1]??String(art.grade),h/2-line/2-3,w-16,line,this.font,color);
  const status=this.status(art),nameY=-h/2+line*1.5+4;
  this.center(card,this.short(art.name,Math.max(4,Math.floor((w-18)/this.font))),nameY,w-18,line,this.font,C.ink);
  this.center(card,status.text,-h/2+line/2+4,w-16,line,this.font,status.color);
  this.artwork(image,art,w-20,artH);
 }
 private artwork(host:Node,art:EquipmentArtDef,w:number,h:number):void{
  const request=this.revision;this.clear(host);this.center(host,'载入图像…',0,w,h,this.font,C.muted);
  // Preflight exposes failures to the player. mount then reuses the cached native frame.
  void EquipmentArt.frame(art,undefined,host).then(()=>{
   if(!this.alive(host)||request!==this.revision)return;this.clear(host);EquipmentArt.mount(host,art,w,h);
  }).catch(()=>{
   if(!this.alive(host)||request!==this.revision)return;this.clear(host);
   this.button(host,'图片失败\n点此重试',0,0,w,Math.max(this.hit,h),'gallery:retry-art',()=>this.artwork(host,art,w,h));
  });
 }
 private scroll(parent:Node,x:number,y:number,w:number,h:number,text:string):void{
  const font=this.font,line=font*1.35,characters=Math.max(8,Math.floor((w-24)/font)),lines=text.split('\n').reduce((count,value)=>count+Math.max(1,Math.ceil(value.length/characters)),0),contentH=Math.max(h,lines*line+20);
  const host=this.hud.node('GalleryDetailScroll',parent,x,y,w,h),viewport=this.hud.node('Viewport',host,0,0,w,h);viewport.addComponent(Mask).type=Mask.Type.GRAPHICS_RECT;
  const content=this.hud.node('Content',viewport,0,h/2,w,contentH);content.getComponent(UITransform)!.setAnchorPoint(.5,1);
  const label=this.label(content,text,-4,-contentH/2+4,w-24,contentH-8,font,C.ink);label.lineHeight=line;label.verticalAlign=Label.VerticalAlign.TOP;
  const scroll=host.addComponent(ScrollView);scroll.content=content;scroll.horizontal=false;scroll.vertical=true;scroll.cancelInnerEvents=true;
  if(contentH>h){const track=this.hud.node('GalleryScrollbar',host,w/2-3,0,4,h),bar=track.addComponent(ScrollBar),handle=UiSkin.asset(track,'bar-focus-fill',4,28,false);handle.node.setScale(1,1,1);handle.node.getComponent(UITransform)!.setContentSize(4,28);handle.color=C.gold;bar.handle=handle;bar.direction=1;bar.enableAutoHide=false;scroll.verticalScrollBar=bar;}
 }
 private enlarge(art:EquipmentArtDef):void{
  if(!this.alive()||this.detail)return;this.revision++;if(this.main)this.main.active=false;
  const detail=this.hud.panel(this.root,0,0,this.width,this.height,C.background);detail.name='EquipmentGalleryDetail';detail.addComponent(BlockInputEvents);this.detail=detail;
  const headerY=this.height/2-this.hit/2,titleW=this.width-2*(this.hit+this.gap+12*this.hud.uiUnit);
  GoldPanelHeader.attach(detail,{width:this.width,unit:this.hud.uiUnit,hit:this.hit,centerY:headerY,viewport:this.hud,action:'gallery:detail-back'},()=>this.paint());
  this.label(detail,art.name,0,headerY,titleW,this.hit,this.font+2,C.goldLight);
  const bodyH=this.height-this.hit-this.gap*2,artW=this.width*.43,bodyY=-this.hit/2;
  const image=this.hud.node('GalleryEnlargedArtwork',detail,-this.width/2+artW/2,bodyY,artW-16,bodyH);this.artwork(image,art,artW-16,bodyH);
  const infoW=this.width-artW-this.gap-12,infoX=-this.width/2+artW+this.gap+infoW/2,ids=this.mapped(art),mapped=ids.length?ids.map(id=>`${EQUIPMENT[id].name}（${id}）\n${this.owned(id)?'已获得':'尚未获得'}`).join('\n\n'):'后续设计';
  const family=FAMILIES.find(([id])=>id===art.family)?.[1]??art.family;
  const text=[family+' · '+(GRADES[art.grade-1]??''),'','材质',art.materials?.join('、')||'资料待补充','','结构',art.features?.map(value=>'· '+value).join('\n')||'资料待补充',...(art.description?['',art.description]:[]),'','首章物品',mapped].join('\n');
  this.scroll(detail,infoX,bodyY,infoW,bodyH,text);
 }
 destroy():void{if(this.disposed)return;this.disposed=true;this.revision++;this.hud.modalDisposers.delete(this.dispose);if(isValid(this.root,true)){this.root.active=false;this.root.destroy();}this.main=null;this.detail=null;}
}
