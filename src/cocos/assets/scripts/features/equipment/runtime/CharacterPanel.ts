import {viewportMetrics} from '../../../platform/ViewportMetrics';
import {resourceProfile} from '../../combat/common/ClassResource';
import {CompactMask as Mask} from '../../../shared/ui/CompactMask';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {qualityFeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {equipmentIconFrame} from './EquipmentIconFrame';
import {BlockInputEvents,ButtonComponent as Button,Color,EventTouch,Graphics,Label,Node,ScrollView,ScrollBar,sys,UITransform} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import {SKILLS,ACTION_NAMES,type SkillId} from '../../progression/common/SkillChecks';
import {EQUIPMENT,type EquipmentSlot,type ItemDef} from '../data/Equipment';
import {getArea} from '../../world/data/WorldData';
import {Hud} from '../../../app/Hud';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {GoldPanelHeader} from '../../../shared/ui/GoldPanelHeader';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {EQUIPMENT_SLOT_NAMES,EQUIPMENT_SLOT_ICONS} from './EquipmentPresentation';
import {CharacterPreview} from '../../actors/runtime/CharacterPreview';
import {FlatCharacterPreview} from '../../actors/runtime/FlatCharacterPreview';
import {EquipmentArt} from './EquipmentArt';
import {COMBAT_RULES} from '../../combat/data/PureSkills';
import {applyRpgFont} from '../../../shared/ui/RpgFont';
import {renderEquipmentGallery} from './EquipmentGallery';

export type CharacterTab='inventory'|'attributes'|'skills'|'catalog';
type Filter='all'|'weapon'|'armor'|'jewelry'|'hairstyle';
type ViewState={selected:string;filter:Filter;skill:SkillId};
const states=new WeakMap<GameSession,ViewState>();
const SKILL_TEXT:Record<SkillId,string>={insight:'读懂人物的言外之意，判断其动机与隐瞒。',persuasion:'比对抄件、证词与记录，找出可以被现场验证的矛盾。',investigation:'仔细寻找文字、机关与遗物留下的线索。',sleight:'用灵巧的双手处理锁具、诱片和精密装置。',athletics:'凭借力量与身体控制，应对攀爬、推移和障碍。'};

/** Paper doll, inspectable inventory and actual game statistics. UI state never grants an item. */
export function renderCharacterPanel(hud:Hud,game:GameSession,tab:CharacterTab='inventory'){
 const state=states.get(game)??{selected:game.state.equipment.weapon,filter:'all' as Filter,skill:'insight' as SkillId};states.set(game,state);
 new CharacterPanel(hud,game,tab,state).show();
}

class CharacterPanel {
 private readonly mobile=sys.isMobile;private readonly font:number;private readonly hit:number;
 private hover:Node|null=null;private panel:Node;private right:Node;private summaryHost:Node;private skillButtons=new Map<SkillId,Node>();private detail:Node|null=null;private preview:CharacterPreview|FlatCharacterPreview|null=null;
 private width=0;private height=0;private bodyH=0;private leftW=0;private middleW=0;private rightW=0;
 constructor(private readonly hud:Hud,private readonly game:GameSession,private readonly tab:CharacterTab,private readonly state:ViewState){const cssHeight=viewportMetrics.windowSize.height/Math.max(1,viewportMetrics.devicePixelRatio);this.font=this.mobile?Math.max(28,Math.ceil(14*hud.height/cssHeight)):17;this.hit=this.mobile?Math.max(88,Math.ceil(48*hud.height/cssHeight)):48;}
 private label(parent:Node,value:string,x:number,y:number,w:number,size=this.font,color=C.ink,h=40){const actual=Math.max(size,12*this.hud.height/390),l=this.hud.text(parent,value,x,y,w,actual,color,Math.max(h,actual*1.34));applyRpgFont(l);l.lineHeight=actual*1.34;l.overflow=Label.Overflow.CLAMP;l.enableWrapText=true;return l;}
 private button(parent:Node,title:string,x:number,y:number,w:number,h:number,name:string,click:()=>void,selected=false){
  const n=this.hud.node(name,parent,x,y,w,h);UiSkin.button(n,w,h);const label=this.label(n,title,0,0,w-16,this.font,C.ink,h-4);label.horizontalAlign=Label.HorizontalAlign.CENTER;
  if(selected){const line=n.addComponent(CompactGraphics);line.strokeColor=C.route;line.lineWidth=2;line.roundRect(-w/2+2,-h/2+2,w-4,h-4,4);line.stroke();}
  n.on(Button.EventType.CLICK,click);return n;
 }
 private rule(parent:Node,y:number,w:number){const n=this.hud.node('CharacterRule',parent,0,y,w,2),g=n.addComponent(CompactGraphics);g.strokeColor=new Color(C.line.r,C.line.g,C.line.b,145);g.lineWidth=1;g.moveTo(-w/2,0);g.lineTo(w/2,0);g.stroke();g.moveTo(-7,-3);g.lineTo(0,1);g.lineTo(7,-3);g.stroke();}
 private scroll(parent:Node,x:number,y:number,w:number,h:number,contentH:number){const host=this.hud.node('CharacterScroll',parent,x,y,w,h),viewport=this.hud.node('Viewport',host,0,0,w,h);viewport.addComponent(Mask).type=Mask.Type.GRAPHICS_RECT;const content=this.hud.node('Content',viewport,0,h/2,w,Math.max(h,contentH));content.getComponent(UITransform)!.setAnchorPoint(.5,1);const scroll=host.addComponent(ScrollView);scroll.content=content;scroll.horizontal=false;scroll.vertical=true;scroll.cancelInnerEvents=true;if(contentH>h+1){const track=this.hud.node('CharacterScrollbar',host,w/2-2,0,3,h),bar=track.addComponent(ScrollBar),handle=UiSkin.asset(track,'bar-focus-fill',3,24,false);handle.node.setScale(1,1,1);handle.node.getComponent(UITransform)!.setContentSize(3,24);handle.color=C.route;bar.handle=handle;bar.direction=1;bar.enableAutoHide=false;scroll.verticalScrollBar=bar;}return content;}
 show(){
  this.hud.clearModal();const shade=this.hud.node('CharacterBackdrop',this.hud.modal,0,0,this.hud.width,this.hud.height);shade.addComponent(BlockInputEvents);const g=shade.addComponent(CompactGraphics);g.fillColor=new Color(0,0,0,176);g.rect(-this.hud.width/2,-this.hud.height/2,this.hud.width,this.hud.height);g.fill();
  const safe=sys.getSafeAreaRect(false),left=-this.hud.width/2+Math.max(20,safe.x),right=-this.hud.width/2+Math.min(this.hud.width-20,safe.x+safe.width),bottom=-this.hud.height/2+Math.max(18,safe.y),top=-this.hud.height/2+Math.min(this.hud.height-18,safe.y+safe.height);
  this.width=Math.min(right-left,1460);this.height=Math.min(top-bottom,676);this.panel=this.hud.panel(this.hud.modal,(left+right)/2,(top+bottom)/2,this.width,this.height,C.background);this.panel.name='CharacterPanel';
  this.leftW=this.mobile?250:224;this.middleW=440;this.rightW=this.width-this.leftW-this.middleW-64;this.bodyH=this.height-this.hit-112;
  const headerY=this.height/2-this.hit/2-10;this.label(this.panel,'拉斐尔',-this.width/2+this.hit+115,headerY,190,this.mobile?32:25,C.gold,this.hit);
 const tabs:[CharacterTab,string,string][]=[['inventory','装备与背包','inventory'],['attributes','属性成长','attributes'],['skills','战斗技能','checks'],['catalog','装备图谱','equipment-catalog']];const tabW=this.mobile?156:126;
 tabs.forEach(([id,title,action],i)=>this.button(this.panel,title,-100+i*(tabW+Math.max(8,8*this.hud.height/390)),headerY,tabW,this.hit,'character:tab:'+id,()=>this.hud.actions.click(action),this.tab===id&&id!=='skills'));
  GoldPanelHeader.attach(this.panel,{width:this.width,unit:this.hud.uiUnit,hit:this.hit,centerY:headerY,viewport:this.hud,action:'character:return'},()=>{if(this.tab==='inventory')this.state.filter='all';this.hud.actions.click(this.tab==='inventory'?'inventory':'close');});
  this.rule(this.panel,this.height/2-this.hit-15,this.width-36);
  const bodyY=-8;const leftX=-this.width/2+16+this.leftW/2,middleX=-this.width/2+this.leftW+32+this.middleW/2,rightX=this.width/2-16-this.rightW/2;
  if(this.tab==='catalog'){
   const host=this.hud.node('EquipmentGalleryHost',this.panel,0,bodyY,this.width-32,this.bodyH);renderEquipmentGallery(this.hud,this.game,host,this.width-32,this.bodyH);
  }else{
   const left=this.hud.panel(this.panel,leftX,bodyY,this.leftW,this.bodyH,C.panel);left.name='CharacterSummary';this.summaryHost=left;this.summary(left);
   const middle=this.hud.node('CharacterPaperDoll',this.panel,middleX,bodyY,this.middleW,this.bodyH);this.paperDoll(middle);
   this.right=this.hud.panel(this.panel,rightX,bodyY,this.rightW,this.bodyH,C.dark);this.right.name='CharacterContent';this.paintRight();
  }
 this.label(this.panel,'旅程 · '+getArea(this.game.state.area).name,-this.width/2+235,-this.height/2+27,440,this.mobile?24:15,C.muted,34);
 }
 private summary(host:Node){
  if(this.tab==='skills'){this.skillSummary(host);return;}
 const p=this.game.state.player,progress=this.game.progressionView(),eq=this.game.state.equipment,armor=Object.entries(eq).reduce((n,[slot,id])=>n+(slot!=='spells'&&typeof id==='string'?(this.game.itemView(id)?.armor??0):0),0),content=this.scroll(host,0,0,this.leftW-24,this.bodyH-24,this.mobile?1120:820);
  let y=-24;this.label(content,'自由探险者',0,y,this.leftW-40,this.font+2,C.gold,40).horizontalAlign=Label.HorizontalAlign.CENTER;y-=46;
  const emblem=this.hud.node('CharacterEmblem',content,0,y-22,58,58);const g=emblem.addComponent(CompactGraphics);g.strokeColor=C.gold;g.lineWidth=2;g.circle(0,0,24);g.stroke();for(let i=0;i<8;i++){const a=i*Math.PI/4;g.moveTo(Math.cos(a)*27,Math.sin(a)*27);g.lineTo(Math.cos(a)*33,Math.sin(a)*33);}g.stroke();UiSkin.sprite(emblem,'ui/icons/attack',30,30,C.gold);y-=78;
 const rows:[string,string][]=[['角色等级',`Lv${progress.level} / ${progress.maxLevel}`],['生命',`${Math.ceil(p.hp)} / ${p.maxHp}`],['技能威力',progress.baseSkillPower.toFixed(1)],['命中值',progress.accuracy.toFixed(1)],['闪避值',progress.evasion.toFixed(1)],[resourceProfile(this.game.state).name,`${Math.floor(p.focus)} / ${p.maxFocus}`],['装备护甲',`${Math.min(40,armor)}%`],['余烬',`${this.game.state.dice.inspiration} / 4`]];
  for(const [name,value]of rows){if(this.mobile){this.label(content,name,0,y,this.leftW-42,this.font-2,C.muted,36).horizontalAlign=Label.HorizontalAlign.CENTER;this.label(content,value,0,y-34,this.leftW-36,this.font+2,C.ink,42).horizontalAlign=Label.HorizontalAlign.CENTER;y-=78;}else{this.label(content,name,-this.leftW*.2,y,this.leftW*.44,this.font,C.muted,40);this.label(content,value,this.leftW*.21,y,this.leftW*.42,this.font,C.ink,40).horizontalAlign=Label.HorizontalAlign.RIGHT;y-=44;}}
  this.rule(content,y+8,this.leftW-46);y-=26;this.label(content,'装备效果',0,y,this.leftW-40,this.font,C.gold,40).horizontalAlign=Label.HorizontalAlign.CENTER;y-=48;
 const sets=this.game.setCounts(),names:Record<string,string>={oath:'誓卫',wind:'逐风',seeker:'寻宝客',ember:'灰烬',bell:'沉钟',seal:'缄印'};const active=Object.entries(sets).map(([id,count])=>`${names[id]??id}  ${count}件`),setHeight=Math.max(60,active.length*this.font*1.34+12);
 this.label(content,active.join('\n')||'尚未激活套装',0,y-setHeight/2,this.leftW-40,this.font,C.muted,setHeight);y-=setHeight+24;
 this.label(content,`金币  ${p.gold}\n废铁  ${p.iron}\n符纹  ${p.runes}\n锻造芯  ${p.cores}`,0,y-65,this.leftW-40,this.font,C.ink,160);
 }
 private paperDoll(host:Node){
  const well=this.hud.node('PortraitWell',host,0,0,this.middleW,this.bodyH),back=well.addComponent(CompactGraphics);back.fillColor=C.dark;back.roundRect(-this.middleW/2,-this.bodyH/2,this.middleW,this.bodyH,3);back.fill();
  const canStyle=this.tab==='inventory'&&this.hud.hairstyles.length>0;
  const gap=Math.max(8,8*this.hud.height/390),portraitW=this.middleW-48,portraitH=this.bodyH-this.hit-2*gap-(canStyle?this.hit+gap:0),portraitY=canStyle?0:this.hit/2;
  const portrait=this.hud.node('CharacterPortrait',host,0,portraitY,portraitW,portraitH);
  const source=(this.hud as Hud&{previewSource?:Node}).previewSource;
  const flatViews=this.hud.flatPortraitViewsForWeapon?.(this.game.state.equipment.weapon)??[];
  if(this.hud.flatPortrait?.isValid)this.preview=new FlatCharacterPreview(portrait,flatViews[0]??this.hud.flatPortrait,portraitW,portraitH,flatViews);
  else if(!this.hud.flatMode&&source?.isValid)this.preview=new CharacterPreview(portrait,source,portraitW,portraitH,this.game.state.equipment);
  else this.label(portrait,'人物正在准备',0,0,portraitW,this.font,C.muted,60).horizontalAlign=Label.HorizontalAlign.CENTER;
  if(this.preview){const preview=this.preview;this.hud.modalDisposers.add(()=>preview.destroy());}
  if(canStyle){const current=this.hud.hairstyles.find(s=>s.selected);this.button(host,'发型 · '+(current?.label??'银白卷发'),0,this.bodyH/2-this.hit/2-8,portraitW-(this.mobile?32:0),this.hit,'character:hairstyles',()=>{this.state.filter='hairstyle';this.paintRight();},this.state.filter==='hairstyle');}
  // Worn sockets already belong to the equipment page; keep this preview clear for styling.
  const arrowY=-this.bodyH/2+this.hit/2+8;this.button(host,'左转',-(this.hit+gap)/2,arrowY,this.hit,this.hit,'character:rotate:left',()=>this.preview?.rotate(this.hud.flatMode?-90:-30));this.button(host,'右转',(this.hit+gap)/2,arrowY,this.hit,this.hit,'character:rotate:right',()=>this.preview?.rotate(this.hud.flatMode?90:30));
 }
 private paintRight(){this.hover?.destroy();this.hover=null;for(const child of this.right.children)child.destroy();this.right.removeAllChildren();this.detail=null;const hair=this.tab==='inventory'&&this.state.filter==='hairstyle'&&this.hud.hairstyles.length>0;if(this.preview instanceof CharacterPreview)this.preview.focusHead(hair);if(hair)this.hairstyles();else if(this.tab==='inventory')this.inventory();else if(this.tab==='skills')this.skills();else this.attributes();}
 private hairstyles(){
  const w=this.rightW,h=this.bodyH,rowH=this.hit+this.font+20,footer=this.hit+14,viewH=h-96-footer;
  this.label(this.right,'发型款式',0,h/2-24,w-28,this.font+3,C.gold,42).horizontalAlign=Label.HorizontalAlign.CENTER;
  this.label(this.right,this.game.state.equipment.head==='A02'?'头罩会遮住发型，摘下后显示所选款式':'选择即生效 · 拖动人物可查看侧面',0,h/2-60,w-28,this.font-2,C.muted,32).horizontalAlign=Label.HorizontalAlign.CENTER;
  const content=this.scroll(this.right,0,-(96-footer)/2,w-20,viewH,this.hud.hairstyles.length*rowH+8);
  this.hud.hairstyles.forEach((style,i)=>{const y=-i*rowH-this.hit/2-4;this.button(content,style.label+(style.selected?' · 已使用':''),0,y,w-44,this.hit,'character:hairstyle:'+style.id,()=>this.hud.actions.click('hairstyle:'+style.id),style.selected);this.label(content,style.description,0,y-this.hit/2-this.font*.65-7,w-48,this.font-2,C.muted,this.font+12).horizontalAlign=Label.HorizontalAlign.CENTER;});
 }
 private inventory(){
 const w=this.rightW,h=this.bodyH,top=h/2-12,filterH=this.hit,gap=Math.max(8,8*this.hud.height/390),filterW=(w-24-3*gap)/4,filterNames:[Filter,string][]=[['all','全部'],['weapon','武器'],['armor','防具'],['jewelry','首饰']];
  filterNames.forEach(([filter,label],i)=>this.button(this.right,label,(i-1.5)*(filterW+gap),top-filterH/2,filterW,filterH,'inventory:filter:'+filter,()=>{this.state.filter=filter;this.state.selected='';this.paintRight();},this.state.filter===filter));
 const ids=Object.keys(this.game.state.inventory).filter(id=>this.game.state.inventory[id]>0).filter(id=>{const d=EQUIPMENT[id];return !!d&&d.kind!=='spell'&&(this.state.filter==='all'||this.state.filter==='weapon'&&['sword','bow','staff'].includes(d.kind)||this.state.filter==='armor'&&d.kind==='armor'||this.state.filter==='jewelry'&&['ring','necklace'].includes(d.kind));});
  const detailH=this.mobile?128:144,actionH=this.hit,gridH=h-filterH-detailH-actionH-38,cols=this.mobile?Math.max(1,Math.min(8,Math.floor((w-30+gap)/(this.hit+gap)))):7,cell=(w-30-gap*(cols-1))/cols,rows=Math.max(4,Math.ceil(ids.length/cols)),content=this.scroll(this.right,0,top-filterH-gap-gridH/2,w-20,gridH,rows*(cell+gap)+12);
  const worn=new Set(Object.entries(this.game.state.equipment).filter(([k,v])=>k!=='spells'&&v).map(([,v])=>v));
  for(let i=0;i<rows*cols;i++){const id=ids[i],item=id?EQUIPMENT[id]:null,x=-w/2+15+cell/2+(i%cols)*(cell+gap),y=-cell/2-Math.floor(i/cols)*(cell+gap)-4;const n=this.hud.node(id?'inventory:item:'+id:'inventory:empty:'+i,content,x,y,cell,cell),frame=equipmentIconFrame(n,cell,cell,{quality:item?.quality,selected:!!id&&id===this.state.selected});
 if(!item)continue;EquipmentArt.rawIcon(frame.content,item,cell*.90,cell*.90);const button=n.addComponent(Button);button.transition=Button.Transition.SCALE;button.zoomScale=.95;n.on(Button.EventType.CLICK,()=>{this.state.selected=id;this.paintRight();});
   if(worn.has(id))this.label(n,'◆',-cell/2+12,cell/2-12,22,this.mobile?22:14,C.green,24).horizontalAlign=Label.HorizontalAlign.CENTER;
   if(this.game.state.inventory[id]>1){const count=this.label(n,'×'+this.game.state.inventory[id],cell/2-23,-cell/2+13,42,this.mobile?20:14,C.ink,26);count.horizontalAlign=Label.HorizontalAlign.RIGHT;count.enableWrapText=false;count.enableOutline=true;count.outlineColor=C.dark;count.outlineWidth=2;}
   n.on(Node.EventType.MOUSE_ENTER,()=>{if(!this.mobile)this.showHover(item);});n.on(Node.EventType.MOUSE_LEAVE,()=>{this.hover?.destroy();this.hover=null;});
  }
  if(!ids.length)this.label(content,'尚未获得此类物品',0,-58,w-40,this.font,C.muted,60).horizontalAlign=Label.HorizontalAlign.CENTER;
  this.paintDetail(top-filterH-gridH-25,detailH);
 const selected=EQUIPMENT[this.state.selected],isOwned=!!this.game.state.inventory[this.state.selected],equipped=worn.has(this.state.selected);
 const access=this.availability(),canChange=!equipped,actionW=(w-24-gap)/2,actionX=(i:number)=>-w/2+12+actionW/2+i*(actionW+gap);const equip=this.button(this.right,equipped?'已装备':!access.available?'暂时无法换装':'装备选中物品',actionX(1),-h/2+actionH/2+8,actionW,actionH,'inventory:equip',()=>{if(selected&&isOwned&&canChange&&access.available)this.hud.actions.click('equip:'+selected.id);});equip.getComponent(Button)!.interactable=!!selected&&isOwned&&canChange&&access.available;
 this.button(this.right,'养成',actionX(0),-h/2+actionH/2+8,actionW,actionH,'inventory:craft',()=>this.hud.actions.click(selected&&isOwned?'forge-item:'+selected.id:'forge'));
 }
 private availability(){return (this.game as GameSession&{equipmentAvailability?:()=>{available:boolean;reason:string}}).equipmentAvailability?.()??{available:true,reason:''};}
 private showHover(item:ItemDef){
  this.hover?.destroy();const w=Math.min(370,this.rightW-20),h=180,x=this.right.position.x-this.rightW/2-w/2-10;const tooltip=this.hud.panel(this.panel,x,20,w,h,C.button);this.hover=tooltip;tooltip.name='ItemHoverTooltip';
  this.label(tooltip,item.name,0,h/2-28,w-30,this.font+2,F.color(qualityFeedbackRole(item.quality)),38);this.label(tooltip,item.quality,0,h/2-62,w-30,this.font-2,C.muted,28);this.rule(tooltip,h/2-80,w-26);this.label(tooltip,this.game.itemView(item.id).description,0,-40,w-30,this.font,C.ink,88);
 }
 private paintDetail(y:number,height:number){
  this.detail?.destroy();this.detail=this.hud.node('ItemDetail',this.right,0,y-height/2+12,this.rightW-28,height);const d=this.game.itemView(this.state.selected),w=this.rightW-40;if(!d){this.label(this.detail,'选择物品或装备部位查看详情',0,0,w,this.font,C.muted,height);return;}
  this.label(this.detail,d.name,-w*.10,height/2-24,w*.80,this.font+2,F.color(qualityFeedbackRole(d.quality)),40);this.label(this.detail,d.quality,w*.39,height/2-24,w*.20,this.font-2,F.color(qualityFeedbackRole(d.quality)),40).horizontalAlign=Label.HorizontalAlign.RIGHT;
 const access=this.availability(),equipped=Object.entries(this.game.state.equipment).some(([k,v])=>k!=='spells'&&v===d.id),blocked=!access.available&&!equipped,text=blocked?access.reason+'\n'+d.description:d.description,textH=Math.max(height-60,(Math.ceil(text.length/Math.max(10,Math.floor(w/this.font)))+text.split('\n').length)*this.font*1.34+8),body=this.scroll(this.detail,0,-24,w,height-56,textH);
 this.label(body,text,0,-textH/2,w-12,this.font,blocked?C.red:C.ink,textH);this.rule(this.detail,height/2,w);
 }
 private attributes(){
 const w=this.rightW,h=this.bodyH,s=this.game.state,progress=this.game.progressionView(),weapon=this.game.itemView(s.equipment.weapon);const rows:[string,string][]=[['角色等级',`Lv${progress.level} / ${progress.maxLevel}`],['当前武器',weapon?.name??'未装备'],['装备效果',weapon?.description??'脱战后可随时选择装备。'],['技能威力',progress.baseSkillPower.toFixed(1)],['命中值',progress.accuracy.toFixed(1)],['闪避值',progress.evasion.toFixed(1)],[resourceProfile(s).name,`${Math.floor(s.player.focus)} / ${s.player.maxFocus}`],['主线目标',this.game.objective()],['地点',getArea(s.area).name],['本次行程',Math.floor(s.movedDistance)+' 米']];
  const content=this.scroll(this.right,0,0,w-20,h-24,rows.length*(this.mobile?104:78)+60);let y=-28;this.label(content,'人物概览',0,y,w-40,this.font+4,C.gold,45).horizontalAlign=Label.HorizontalAlign.CENTER;y-=58;
  for(const [label,value]of rows){this.label(content,label,-w*.30,y,w*.30,this.font,C.muted,45);this.label(content,value,w*.13,y-8,w*.59,this.font,C.ink,this.mobile?82:58);y-=this.mobile?104:78;this.rule(content,y+40,w-46);}
 }
 private skillSummary(host:Node){
  const skill=SKILLS[this.state.skill],w=this.leftW-36,content=this.scroll(host,0,0,this.leftW-20,this.bodyH-20,this.mobile?660:520);content.name='SkillTooltip';
  this.label(content,ACTION_NAMES[this.state.skill]+'  +'+(skill.modifier+skill.proficiency),0,-30,w,this.font+4,C.gold,46).horizontalAlign=Label.HorizontalAlign.CENTER;
  this.rule(content,-66,w);this.label(content,'探索行动 · 准备加成',0,-100,w,this.font,C.muted,40).horizontalAlign=Label.HorizontalAlign.CENTER;
  this.label(content,`行动准备  +${skill.modifier}\n经验准备  +${skill.proficiency}`,0,-161,w,this.font,C.ink,96).horizontalAlign=Label.HorizontalAlign.CENTER;
  const detail=this.hud.panel(content,0,-316,w,this.mobile?214:180,C.button);this.label(detail,SKILL_TEXT[this.state.skill],0,0,w-20,this.font,C.ink,this.mobile?194:160);
  this.label(content,'行动：掷骰 + 准备达到目标\n装备：获得时查看说明与基础属性\n随机属性在装备强化中追加',0,-486,w,this.font-2,C.muted,100).horizontalAlign=Label.HorizontalAlign.CENTER;
 }
 private selectSkill(id:SkillId){
  this.state.skill=id;for(const child of this.summaryHost.children)child.destroy();this.summaryHost.removeAllChildren();this.skillSummary(this.summaryHost);
  for(const [key,node]of this.skillButtons){const g=node.getComponent(Graphics)??node.addComponent(CompactGraphics);g.clear();if(key===id){const t=node.getComponent(UITransform)!;g.strokeColor=C.route;g.lineWidth=2;g.roundRect(-t.width/2+2,-t.height/2+2,t.width-4,t.height-4,4);g.stroke();}node.getComponentInChildren(Label)!.color=C.ink;}
 }
 private skills(){
  const w=this.rightW,h=this.bodyH,rows=Object.entries(SKILLS),rowH=this.mobile?this.hit+8:64,top=h/2-38;
 this.label(this.right,'探索手段与机遇',0,top,w-32,this.font+3,C.gold,48).horizontalAlign=Label.HorizontalAlign.CENTER;
  const listH=h-80-this.hit-16,content=this.scroll(this.right,0,h/2-80-listH/2,w-20,listH,rows.length*rowH);this.skillButtons.clear();
  for(let i=0;i<rows.length;i++){const [id,skill]=rows[i],bonus=skill.modifier+skill.proficiency,n=this.button(content,`${ACTION_NAMES[id as SkillId]}    准备 +${bonus}`,0,-rowH/2-i*rowH,w-34,rowH-8,'character:skill:'+id,()=>this.selectSkill(id as SkillId),this.state.skill===id);this.skillButtons.set(id as SkillId,n);}
  this.button(this.right,'查看机遇记录',0,-h/2+this.hit/2+8,w-28,this.hit,'character:history',()=>this.hud.actions.click('check-history'));
 }
}
