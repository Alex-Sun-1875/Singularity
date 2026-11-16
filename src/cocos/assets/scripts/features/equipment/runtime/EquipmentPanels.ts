import {resourceProfile} from '../../combat/common/ClassResource';
import {Label,Node,ScrollView,Vec2} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import {ATTRIBUTES,type Attribute} from '../../progression/common/Progression';
import {EQUIPMENT,type EquipmentSlot,type ItemDef} from '../data/Equipment';
import {GROWING_EQUIPMENT,growingStats} from '../data/GrowingEquipment';
import {qualityFeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {itemForgingView} from '../../crafting/common/EquipmentForging';
import {forgingAffixText} from '../../crafting/data/EquipmentForging';
import {EQUIPMENT_SLOT_NAMES,equipmentTypeName} from './EquipmentPresentation';
import {RpgPanel} from '../../../shared/ui/RpgPanel';
import {equipmentIconFrame} from './EquipmentIconFrame';
import type {Hud} from '../../../app/Hud';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {COMBAT_SKILL_ICONS} from '../../combat/runtime/CombatSkillIcons';
import {equipmentText as et,equipmentChangeReason} from '../locales';
import {professionAcceptsItem} from '../../progression/common/CombatLoadouts';
import {preparationText as pt} from '../../progression/locales';
import {PreparationSkin as P} from '../../../shared/ui/PreparationSkin';
import {PreparationControls as Controls} from '../../../shared/ui/PreparationControls';
import {PREPARATION_DESIGN as D,preparationSkinAsset} from '../../../shared/ui/PreparationTheme';
import {gemText} from '../../gems/locales';
type Filter='all'|'weapon'|'armor'|'jewelry';
type View={selected:string;filter:Filter;scope:'current'|'all';scroll?:number;slot?:EquipmentSlot;equipmentNotice?:string;preparing?:string;draft?:Record<Attribute,number>;token?:string;notice?:string};
const views=new WeakMap<GameSession,View>();
const names:Record<Attribute,string>={strength:'力量',dexterity:'敏捷',intellect:'智力',vitality:'体质'};
function state(g:GameSession){let v=views.get(g);if(!v){v={selected:g.state.equipment.weapon,filter:'all',scope:'current'};views.set(g,v);}return v;}
export function beginEquipmentVisit(g:GameSession){const v=state(g);v.scope='current';v.scroll=0;v.filter='all';v.slot=undefined;v.selected=g.state.equipment.weapon;v.equipmentNotice='';}
export function selectEquipmentSocket(g:GameSession,slot:string){if(!Object.prototype.hasOwnProperty.call(EQUIPMENT_SLOT_NAMES,slot))return;const v=state(g),key=slot as EquipmentSlot;v.slot=key;v.scroll=0;v.selected=g.state.equipment[key]??'';v.filter=key==='weapon'||key==='offhand'?'weapon':key.startsWith('ring')||key==='necklace'?'jewelry':'armor';v.equipmentNotice='';}
export function selectEquipmentCategory(g:GameSession,filter:string){if(!['all','weapon','armor','jewelry'].includes(filter))return;const v=state(g);v.filter=filter as Filter;v.scroll=0;v.slot=undefined;v.selected='';v.equipmentNotice='';}
export function discardAttributePreview(g:GameSession){const v=views.get(g);if(v){delete v.draft;delete v.token;delete v.notice;}}
export function recordEquipmentChange(g:GameSession,id:string,notice:string){const v=state(g);v.selected=id;v.equipmentNotice=notice;}
export function recordEquipmentPreparing(g:GameSession,id?:string){state(g).preparing=id;}
function text(ui:RpgPanel,value:string,x:number,y:number,w:number,h:number,size=14,color=C.ink){return ui.text(ui.panel,value,ui.x(x),ui.y(y),w*ui.scale,h*ui.scale,color,size*ui.scale);}
export function renderCharacterStats(hud:Hud,game:GameSession){
 const p=game.progressionView(),s=game.state,ui=new RpgPanel(hud,game,'character','CharacterStatsPanel',true),u=ui.scale,a=ui.contentTop,b=ui.contentBottom;
 const layout=D.layouts.character,left=ui.column(...layout.portrait,'CharacterPortrait'),middle=ui.column(...layout.attributes,'CharacterCoreAttributes'),right=ui.column(...layout.overview,'CharacterCombatOverview');ui.drape(right,layout.overview[1]*u,ui.bodyHeight);
 const art=(id:string,x:number,y:number,w:number,h:number)=>P.art(ui,ui.panel,id,ui.x(x),ui.y(y),w,h),rule=(x:number,y:number,w:number)=>P.rule(ui,ui.panel,ui.x(x),ui.y(y),w);
 const heroTop=ui.referenceLayout?32:a,heroH=b-heroTop-57;art('hero',112,heroTop+heroH/2,heroH*435/560,heroH);Controls.identity(ui,{skin:'plaque',value:pt('hero',{level:p.level}),x:112,y:b-46,width:198,height:22,textWidth:188,labelHeight:24,fontSize:15.5});
 text(ui,pt(`name.${s.combat.family}`),112,b-27,198,21,12,F.color('state.selected')).horizontalAlign=Label.HorizontalAlign.CENTER;
 ui.progress(ui.panel,ui.x(112),ui.y(b-10),184*u,12*u,s.player.hp,s.player.maxHp,true);text(ui,`${Math.ceil(s.player.hp)} / ${s.player.maxHp}`,112,b-10,178,18,11).horizontalAlign=Label.HorizontalAlign.CENTER;
 text(ui,'核心属性',324,a+14,152,28,20);P.badge(ui,ui.panel,`余点 ${s.progression.unspentPoints}`,ui.x(513),ui.y(a+14),84,'gold');rule(398,a+32,306);
 const rowH=(b-a-43)/4;
 ATTRIBUTES.forEach((key,i)=>{const cy=a+43+rowH*(i+.5);art('attribute-row',398,cy,318,rowH-5);art('attribute-'+key,268,cy,43,36);text(ui,names[key],329,cy-2,62,28,17);text(ui,String(p.attributes[key]),509,cy-2,64,30,21).horizontalAlign=Label.HorizontalAlign.RIGHT;if(p.equipmentAttributes[key])text(ui,`装备 +${p.equipmentAttributes[key]}`,411,cy+15,136,17,11,C.muted);});
 text(ui,'战斗概览',714,a+14,244,28,20);rule(708,a+32,236);
 const armor=Object.values(s.equipment).filter((id):id is string=>typeof id==='string').reduce((n,id)=>n+(game.itemView(id).armor??0),0),stats=[['技能威力',p.baseSkillPower.toFixed(1),'power'],['装备护甲',`${Math.min(40,armor).toFixed(1)}%`,'armor'],['暴击几率',`${p.criticalChance.toFixed(1)}%`,'criticalChance'],['移动速度',p.movementSpeed.toFixed(1),'speed'],['命中值',p.accuracy.toFixed(1),'accuracy'],['闪避值',p.evasion.toFixed(1),'evasion'],[resourceProfile(s).name,`${Math.floor(s.player.focus)}/${s.player.maxFocus}`,'power']];
 stats.forEach(([name,value,icon],i)=>{const y=a+49+i*21,skin=icon==='accuracy'||icon==='evasion'?UiSkin.sprite(ui.panel,'ui/icons/'+(icon==='accuracy'?'attack':'dash'),18*u,18*u):UiSkin.asset(ui.panel,'rpg-stat-'+icon+'-v3',18*u,18*u,false);skin.node.setPosition(ui.x(597),ui.y(y));text(ui,name,667,y,111,25,14);text(ui,value,797,y,54,25,15).horizontalAlign=Label.HorizontalAlign.RIGHT;});
 rule(708,a+185,236);text(ui,'当前构筑',713,a+197,238,26,16);
 [...s.combat.activeSlots,s.combat.ultimate].filter((id):id is string=>!!id).slice(0,5).forEach((id,i)=>{const sprite=UiSkin.sprite(ui.panel,'ui/combat-relief/'+COMBAT_SKILL_ICONS[id],32*u,32*u);sprite.node.setPosition(ui.x(603+i*49),ui.y(a+225));});
 const experience=text(ui,p.level>=40?'等级已满':`经验 ${p.xp} / ${p.xpToNext}`,774,a+14,120,20,11.5,C.muted);experience.horizontalAlign=Label.HorizontalAlign.RIGHT;experience.enableWrapText=false;experience.overflow=Label.Overflow.SHRINK;
 ui.footer(game.equipmentAvailability().reason,[{label:'外观发型',action:'appearance'},{label:'属性加点',action:'allocation:attributes',primary:true},{back:true,label:'返回旅途',action:'close'}]);
}
/** Inventory illustrations stay in the approved painted style; world-model thumbnails remain separate. */
function paintedEquipment(parent:Node,item:ItemDef|undefined,slot:EquipmentSlot,w:number,h:number,ghost=false){
 const kind=item?(['sword','bow','staff'].includes(item.kind)?item.kind:item.kind==='ring'?'ring':item.slot):slot==='weapon'?'sword':slot.startsWith('ring')?'ring':slot;
 const id=item?.id==='W03'?preparationSkinAsset('item-steel-sword'):item?.id==='W09'?preparationSkinAsset('item-blue-bow'):item?.id==='W12'?preparationSkinAsset('item-lightning-staff'):kind==='offhand'?D.artwork.offhand:preparationSkinAsset('item-'+kind),art=UiSkin.asset(parent,id,w,h,false);
 if(ghost)art.color=F.color('text.disabled',90);
 return art;
}
function equipmentTile(ui:RpgPanel,node:Node,item:ItemDef|undefined,w:number,h:number,selected=false,emptyStar=false){
 const frame=equipmentIconFrame(node,w,h,{scale:ui.scale,quality:item?.quality,selected,emptyStar,appearance:'preparation'});
 if(item)paintedEquipment(frame.content,item,item.slot as EquipmentSlot,w-4*ui.scale,h-4*ui.scale);
 return frame;
}
export function renderEquipmentPanel(hud:Hud,game:GameSession){
 const v=state(game),s=game.state,p=game.progressionView(),family=s.combat.family,ui=new RpgPanel(hud,game,'equipment','EquipmentPanel',true),u=ui.scale,hu=ui.hit/u,gap=ui.gap/u,a=(ui.height/2-ui.bodyTop)/u,b=(ui.height/2-ui.bodyBottom)/u,H=ui.height/u,all=v.scope==='all';
 const reference=ui.referenceLayout,pane=(x:number,w:number,name:string)=>ui.column(x,w,name),Y=(v:number)=>reference?v:a+(v-32)*(b-a)/310;
 const layout=D.layouts.equipment,design=D.inventory,columns=design.columns;pane(...layout.portrait,'EquipmentPortrait');const bag=pane(...layout.inventory,'EquipmentInventory'),detail=pane(...layout.detail,'EquipmentDetail');ui.drape(detail,layout.detail[1]*u,ui.bodyHeight);
 P.art(ui,ui.panel,'hero',ui.x(132),ui.y(reference?198:(a+b+34)/2),reference?186:168,reference?240:b-a-34);
 const identity=reference?design.identity.reference:design.identity.compact;
 Controls.identity(ui,{value:pt('hero',{level:p.level}),x:identity.x,y:reference?design.identity.reference.y:a+11,width:identity.width,height:identity.height,textWidth:identity.textWidth,labelHeight:24,fontSize:identity.font});
 if(reference)P.caption(ui,ui.panel,pt('currentProfession',{name:''}),pt(`name.${family}`),ui.x(139),ui.y(72),174,11.5);else text(ui,pt(`name.${family}`),132,a+31,114,20,11.5,F.color('state.selected')).horizontalAlign=Label.HorizontalAlign.CENTER;
 const sockets=design.sockets,row=(index:number)=>reference?index<3?sockets.top+index*sockets.step:sockets.handY:a+hu/2+index*(hu+gap),ringSlot=v.slot==='ringLeft'?'ringLeft':s.equipment.ringRight?'ringRight':'ringLeft',slots:[EquipmentSlot,number,number][]=[['head',reference?sockets.left:43,row(0)],['chest',reference?sockets.left:43,row(1)],['hands',reference?sockets.left:43,row(2)],['necklace',reference?sockets.right:221,row(0)],[ringSlot,reference?sockets.right:221,row(1)],['feet',reference?sockets.right:221,row(2)],['weapon',reference?sockets.mainX:43,row(3)],['offhand',reference?sockets.offX:221,row(3)]];
 slots.forEach(([slot,x,y])=>{
  const hand=slot==='weapon'||slot==='offhand',id=s.equipment[slot],item=id?EQUIPMENT[id]:undefined,size=(hand?(reference?sockets.handSize:sockets.compactHandSize):sockets.sideSize)*u,slotHit=Math.max(ui.hit,size),n=ui.button(ui.panel,'',ui.x(x),ui.y(y),slotHit,'character:slot:'+slot,true,false,slotHit,()=>{
   if(slot.startsWith('ring')){hud.showList('戒指槽位','选择要查看的戒指槽',(['ringLeft','ringRight'] as const).map(key=>({label:EQUIPMENT_SLOT_NAMES[key],detail:s.equipment[key]?game.itemView(s.equipment[key]!).name:'尚未装备',action:'inventory-slot:'+key})),[{back:true,label:'返回装备',action:'inventory'}]);return;}
   selectEquipmentSocket(game,slot);renderEquipmentPanel(hud,game);
  },'catalog');
  const tile=equipmentTile(ui,n,item,size,size,v.slot?slot===v.slot:slot==='weapon'&&!!id);
  if(hand&&!reference)tile.host.setPosition(0,7*u);
  if(!item){const ghost=slot==='offhand'?UiSkin.asset(tile.content,preparationSkinAsset('empty-offhand'),24*u,30*u,false):paintedEquipment(tile.content,undefined,slot,26*u,29*u,true);ghost.node.setPosition(0,0);}
  if(hand){const label=ui.text(n,EQUIPMENT_SLOT_NAMES[slot],0,reference?-(size/2+sockets.handLabelGap*u):sockets.compactLabelY*u,58*u,18*u,C.ink,12*u);label.horizontalAlign=Label.HorizontalAlign.CENTER;}
 });
 const worn=new Set(Object.values(s.equipment)),qualityOrder=['普通','精良','稀有','史诗','传奇','神器'];
 const ids=Object.keys(s.inventory).filter(id=>s.inventory[id]>0&&EQUIPMENT[id]?.kind!=='spell'&&!!EQUIPMENT[id]).filter(id=>all||professionAcceptsItem(family,id))
  .filter(id=>{const d=EQUIPMENT[id];return v.filter==='all'||v.filter==='weapon'&&['weapon','offhand'].includes(d.slot)||v.filter==='armor'&&d.kind==='armor'&&d.slot!=='offhand'||v.filter==='jewelry'&&['ring','necklace'].includes(d.kind);})
  .filter(id=>!v.slot||(EQUIPMENT[id].kind==='ring'?v.slot==='ringLeft'||v.slot==='ringRight':EQUIPMENT[id].slot===v.slot))
  .sort((x,y)=>{const order=(id:string)=>{const d=EQUIPMENT[id];return d.slot==='weapon'?(all&&id===s.equipment.weapon?-1:0):({head:1,chest:2,hands:3,feet:4,necklace:all?6:5,ringLeft:all?5:6,ringRight:all?5:6,offhand:7,spell:8} as Record<string,number>)[d.slot]??8;};return order(x)-order(y)||x.localeCompare(y);});
 if(!ids.includes(v.selected))v.selected=ids.includes(s.equipment.weapon)?s.equipment.weapon:ids[0]??'';
 const cy=reference?(all?design.scopeAllY:design.scopeCurrentY):a+hu/2,categoryW=design.categoryWidth,scopeW=(design.gridWidth-(reference?0:categoryW+gap)-gap)/2;P.art(ui,ui.panel,'scope',ui.x(design.gridLeft+scopeW+gap/2),ui.y(cy),2*scopeW+gap,design.scopeHeight,true);
 (['current','all'] as const).forEach((scope,i)=>{const x=design.gridLeft+scopeW/2+i*(scopeW+gap),n=ui.button(ui.panel,'',ui.x(x),ui.y(cy),scopeW*u,'inventory:scope:'+scope,true,false,reference?design.scopeHeight*u:ui.hit,()=>{v.scope=scope;v.scroll=0;v.selected='';v.equipmentNotice='';renderEquipmentPanel(hud,game);},'catalog');if(v.scope===scope){const plate=P.art(ui,n,'scope-active',0,0,scopeW,design.scopeHeight,true);plate.node.setSiblingIndex(0);if(scope==='all')plate.node.setScale(-plate.node.scale.x,plate.node.scale.y,1);}const label=ui.text(n,pt(scope==='current'?'inventory.current':'inventory.all'),0,0,(scopeW-6)*u,28*u,v.scope===scope?F.color('state.selected'):C.ink,14*u);label.horizontalAlign=Label.HorizontalAlign.CENTER;if(v.scope===scope)P.art(ui,n,'active',0,-16*u,scopeW-8,6);});
 const filters:[Filter,string][]=[['all','全部'],['weapon','武器'],['armor','防具'],['jewelry','首饰']],cellW=(design.gridWidth-(columns-1)*gap)/columns;
 if(reference){
  const categoryY=all?design.categoryAllY:design.categoryCurrentY;P.art(ui,ui.panel,'categories',ui.x(414),ui.y(categoryY),design.gridWidth,design.categoryHeight,true);
  filters.forEach(([key,label],i)=>{const n=ui.button(ui.panel,'',ui.x(design.gridLeft+cellW/2+i*(cellW+gap)),ui.y(categoryY),cellW*u,'inventory-category:'+key,true,false,design.categoryHeight*u,()=>{v.filter=key;v.slot=undefined;v.scroll=0;v.selected='';v.equipmentNotice='';renderEquipmentPanel(hud,game);},'catalog');if(v.filter===key)P.art(ui,n,'chip',0,0,cellW,design.categoryHeight,true);const l=ui.text(n,label,0,0,(cellW-4)*u,24*u,v.filter===key?F.color('state.selected'):C.ink,14*u);l.horizontalAlign=Label.HorizontalAlign.CENTER;});
  P.rule(ui,ui.panel,ui.x(306),ui.y(all?design.countAllY:design.countCurrentY),60);P.rule(ui,ui.panel,ui.x(523),ui.y(all?design.countAllY:design.countCurrentY),60);text(ui,`${all?'所有职业':'本职业及通用'} · ${ids.length}件`,414,all?design.countAllY:design.countCurrentY,142,20,12).horizontalAlign=Label.HorizontalAlign.CENTER;
 }else{
  const category=ui.button(ui.panel,'',ui.x(556-categoryW/2),ui.y(cy),categoryW*u,'inventory:categories',true,false,ui.hit,()=>hud.showList('装备分类','选择要浏览的装备类型',filters.map(([key,label])=>({label,detail:key===v.filter?'当前分类':'',selected:key===v.filter,action:'inventory-category:'+key})),[{back:true,label:'返回装备',action:'inventory-category:'+v.filter}]),'catalog');
  P.art(ui,category,'button-dark',0,0,categoryW,32,true);const categoryLabel=ui.text(category,`${filters.find(f=>f[0]===v.filter)![1]} ${ids.length}⌄`,0,0,(categoryW-6)*u,26*u,C.gold,13*u);categoryLabel.horizontalAlign=Label.HorizontalAlign.CENTER;
 }
 const gridTop=reference?(all?design.gridAllTop:design.gridCurrentTop):a+hu+gap,gridH=reference?(all?design.gridAllHeight:design.gridCurrentHeight):b-gridTop,targetH=reference?(all?design.allRowHeight:design.currentRowHeight):hu,rowH=targetH+(reference?design.referenceRowGap:gap),rows=Math.max(1,Math.ceil(ids.length/columns)),grid=ui.scroll(bag,0,ui.y(gridTop+gridH/2)-ui.bodyY,design.gridWidth*u,gridH*u,(rows*rowH-(reference?design.referenceRowGap:gap))*u);grid.name='EquipmentGridContent';grid.parent!.name='EquipmentGridViewport';const scroll=grid.parent!.parent!.getComponent(ScrollView)!;if(v.scroll)scroll.scrollToOffset(new Vec2(0,v.scroll),0);
 for(let i=0;i<rows*columns;i++){
  const id=ids[i],item=id?EQUIPMENT[id]:undefined,foreign=!!item&&!professionAcceptsItem(family,id),n=ui.button(grid,'',(-design.gridWidth/2+cellW/2+i%columns*(cellW+gap))*u,(-targetH/2-Math.floor(i/columns)*rowH)*u,cellW*u,'inventory:item:'+(id??i),!!item,false,targetH*u,()=>{if(id){v.scroll=scroll.getScrollOffset().y;v.selected=id;v.equipmentNotice='';renderEquipmentPanel(hud,game);}},'catalog');
  const size=reference?Math.min(design.maxTileWidth,cellW):Math.min(hu-1,cellW-4);equipmentTile(ui,n,item,size*u,(reference?targetH-2:size)*u,!!item&&v.selected===id,!item);
  if(item){const badge=foreign?pt('foreign'):item.slot==='weapon'&&worn.has(id)?et('badge.equipped'):(!all||item.kind==='necklace')&&item.slot!=='weapon'?pt('common'):'';if(badge)P.badge(ui,n,badge,0,-((reference?targetH-2:size)/2-8)*u,foreign?58:item.slot==='weapon'&&worn.has(id)?53:42,item.slot==='weapon'&&worn.has(id)&&!foreign?'teal':'gold',14);const rank=itemForgingView(s,id)!.rank;if(rank){const label=ui.text(n,'+'+rank,(size/2-13)*u,(size/2-10)*u,24*u,18*u,C.gold,11.5*u);label.horizontalAlign=Label.HorizontalAlign.RIGHT;}if(s.inventory[id]>1){const label=ui.text(n,'×'+s.inventory[id],(-size/2+19)*u,((reference?targetH-2:size)/2-11)*u,34*u,20*u,C.ink,13*u);label.node.name='InventoryCount:'+id;label.horizontalAlign=Label.HorizontalAlign.LEFT;label.enableWrapText=false;label.enableOutline=true;label.outlineColor=C.dark;label.outlineWidth=2;}}
 }
 if(!v.selected){text(ui,v.slot?et('slot.empty',{slot:EQUIPMENT_SLOT_NAMES[v.slot]}):pt(all?'inventory.emptyAll':'inventory.empty'),706,170,250,70,18,C.muted).horizontalAlign=Label.HorizontalAlign.CENTER;ui.footer(pt('inventory.default'),[{label:pt('inventory.viewAll'),action:'inventory:show-all',enabled:!all||!!v.slot,run:()=>{v.scope='all';v.scroll=0;v.slot=undefined;renderEquipmentPanel(hud,game);}},{label:et('action.select'),action:'inventory:equip',enabled:false,primary:true},{label:pt('return'),action:'close'}]);return;}
 const item=EQUIPMENT[v.selected],change=game.equipmentChange(item.id,v.slot),foreign=!professionAcceptsItem(family,item.id),view=itemForgingView(s,item.id)!,iv=game.itemView(item.id),staff=item.kind==='staff';
 const artScale=reference?1:(b-a)/310,art=(name:string,x:number,y:number,w:number,h:number)=>P.art(ui,ui.panel,name,ui.x(x),ui.y(Y(y)),w,h*artScale),rule=(y:number)=>P.rule(ui,ui.panel,ui.x(710),ui.y(Y(y)),238),L=(value:string,x:number,y:number,w:number,size=15,color=C.ink,h=25)=>text(ui,value,x,Y(y),w,h,size,color);
 if(staff)art('inspect-staff',770,94,143,120);else if(item.kind==='sword')art('inspect-sword',709,81,266,92);else if(item.kind==='bow'){const s=UiSkin.asset(ui.panel,'rpg-profession-bow-v1',250*u,92*u*artScale,false);s.node.setPosition(ui.x(709),ui.y(Y(81)));}else art('item-'+(item.kind==='ring'?'ring':item.slot),707,80,87,82);
 const title=L(iv.name,staff?652:709,staff?68:146,staff?146:250,staff?23:23.5);title.node.name='EquipmentDetailTitle';title.enableWrapText=false;title.overflow=Label.Overflow.SHRINK;
 L(`${item.quality} · ${equipmentTypeName(item)}`,staff?652:709,staff?109:171,staff?146:250,14);
 const suitable=item.kind==='sword'?'破军':item.kind==='bow'?'逐风':staff?'烈焰 / 雷霆':pt('common');P.badge(ui,ui.panel,pt('inventory.suitable',{name:suitable}),ui.x(staff?649:785),ui.y(Y(staff?138:154)),staff?136:86,staff?'gold':'teal');rule(staff?171:185);
 const lines:{label:string;value:string;icon:string}[]=[{label:'等级要求',value:`Lv${item.requiredLevel??1}`,icon:'stat-level'}],power=(id:string)=>GROWING_EQUIPMENT[id]?growingStats(id,p.level).power:EQUIPMENT[id]?.power??0;
 if(item.slot==='weapon')lines.push({label:'武器强度',value:power(item.id)===power(s.equipment.weapon)?String(power(item.id)):`${power(s.equipment.weapon)} → ${power(item.id)}`,icon:'stat-weapon'});
 if(iv.maxHp)lines.push({label:'装备生命',value:'+'+iv.maxHp,icon:'stat-life'});if(iv.armor)lines.push({label:'装备护甲',value:'+'+Number(iv.armor.toFixed(1))+'%',icon:'stat-plan'});
 if(view.affixes.length)for(const affix of view.affixes){const full=forgingAffixText(affix),m=full.match(/^(.*?)\s*([+＋][\d.]+%?)$/);lines.push({label:m?.[1]??full,value:m?.[2]??'',icon:'stat-upgrade'});}else if(!foreign)lines.push({label:'强化属性',value:`0／${view.capacity}`,icon:'stat-upgrade'});
 const first=Y(staff?192:207),rowSpace=22,sh=Y(foreign?256:269)-first+rowSpace,content=ui.scroll(detail,0,ui.y(first-rowSpace/2+sh/2)-ui.bodyY,252*u,sh*u,lines.length*rowSpace*u);
 lines.forEach((line,i)=>{const y=(-rowSpace/2-i*rowSpace)*u;P.art(ui,content,line.icon,-108*u,y,18,19);const label=ui.text(content,line.label+(line.value?'：'+line.value:''),17*u,y,218*u,26*u,C.ink,15*u);label.enableWrapText=false;label.overflow=Label.Overflow.SHRINK;});
 if(foreign){art('info',593,266,18,19);L(pt('inventory.foreign',{name:pt(`name.${family}`).slice(0,2)}),726,266,218,14.5,C.gold,44);}
 else{P.rule(ui,ui.panel,ui.x(710),ui.y(reference?274:first+2*rowSpace+14),238);art('stat-source',603,295,19,17);L('来源：'+(item.source??'已记录'),723,295,213,14.5,C.ink,30);L(`当前上限＋${view.cap} · 装备极限＋${view.maximum}`,710,323,238,11.5,C.muted,21);}
 const access=game.equipmentAvailability(),blocked=change.block&&change.block!=='equipped',label=foreign?pt('profession.choose'):v.preparing?et('action.preparing'):change.available?(item.kind==='ring'?et(change.slot==='ringRight'?'action.rightRing':'action.leftRing'):et('action.equip')):et(change.block==='equipped'?'action.equipped':change.block==='level'?'action.level':change.block==='two-handed'?'action.offhand':'action.blocked');
 const status=v.preparing?et('notice.loading'):v.equipmentNotice||(!access.available?access.reason:foreign?pt('inventory.browse'):blocked?equipmentChangeReason(change):change.offhand?et('notice.twoHanded'):v.slot?et('slot.target',{slot:EQUIPMENT_SLOT_NAMES[v.slot]}):pt(all?'inventory.browse':'inventory.default'));
 ui.footer(status,[{label:'养成',action:'forge-item:'+item.id},{label,action:foreign?'profession-for:'+item.id:'inventory:equip',enabled:!v.preparing&&(foreign||change.available),primary:true,run:()=>hud.actions.click(foreign?'profession-for:'+item.id:'equip:'+item.id+(v.slot?':'+v.slot:''))},{label:gemText('workshop.tab'),action:'gems:'+item.id},{back:true,label:pt('return'),action:'close'}]);
}
