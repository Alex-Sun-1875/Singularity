import {Label,Node,Sprite} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import {itemForgingView} from '../common/EquipmentForging';
import {EQUIPMENT,type ItemDef} from '../../equipment/data/Equipment';
import {forgingAffixText,forgingValue,FORGING_STAT_NAMES,type ForgingStat} from '../data/EquipmentForging';
import {qualityFeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {equipmentTypeName} from '../../equipment/runtime/EquipmentPresentation';
import {RpgPanel} from '../../../shared/ui/RpgPanel';
import {equipmentIconFrame} from '../../equipment/runtime/EquipmentIconFrame';
import type {Hud} from '../../../app/Hud';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {PreparationSkin as P} from '../../../shared/ui/PreparationSkin';
import {PreparationControls as Controls} from '../../../shared/ui/PreparationControls';
import {PREPARATION_DESIGN as D,preparationSkinAsset} from '../../../shared/ui/PreparationTheme';
function art(ui:RpgPanel,parent:Node,id:string,x:number,y:number,w:number,h:number){const sprite=UiSkin.asset(parent,id,w*ui.scale,h*ui.scale,false);sprite.node.setPosition(x,y);return sprite;}
export function workshopStatus(game:GameSession){const access=game.forgingAvailability();return access.available?(game.preparationAvailability().available?'安全检查点 · 可强化':'洛恩工坊 · 可强化'):access.reason.includes('请前往')?'前往检查点或洛恩工坊整备':access.reason;}
/** Shared workshop navigation, with compact art inside independent mobile hit areas. */
export function workshopHeader(ui:RpgPanel,id:string,active:'craft'|'enhance'|'transfer'){
 const u=ui.scale,cy=ui.contentTop+ui.hit/u/2;art(ui,ui.panel,'rpg-anvil-v2',ui.x(43),ui.y(cy),34,23);ui.text(ui.panel,'洛恩的工坊',ui.x(178),ui.y(cy),198*u,30*u,C.ink,20*u);
 const tabs:[string,string,string][]=[['锻造','craft','craft'],['强化',`forge-item:${id}`,'enhance'],['传承',`forge-targets:${id}`,'transfer']];
 tabs.forEach(([label,action,key],i)=>{const n=ui.tab(ui.panel,label,ui.x(344+i*88),ui.y(cy),76*u,action);P.art(ui,n,'button-dark',0,0,76,32,true).node.setSiblingIndex(0);if(key===active)P.art(ui,n,'card-selected',0,0,77,33,true);n.children.filter(c=>c.getComponent(Label)).forEach(c=>c.getComponent(Label)!.color=key===active?F.color('state.selected'):C.ink);});
 P.rule(ui,ui.panel,ui.x(704),ui.y(cy),218);
}
function painted(ui:RpgPanel,parent:Node,item:ItemDef,size:number){const kind=['sword','bow','staff'].includes(item.kind)?item.kind:item.kind==='ring'?'ring':item.slot;return art(ui,parent,kind==='offhand'?D.artwork.offhand:preparationSkinAsset('item-'+kind),0,0,size,size);}
function statArt(ui:RpgPanel,parent:Node,stat:ForgingStat,x:number,y:number,size=16){const path=['strength','dexterity','intellect','vitality'].includes(stat)?'rpg-attribute-'+stat:'rpg-stat-'+(stat==='power'||stat==='armor'?stat:'criticalChance')+'-v3';return art(ui,parent,path,x,y,size,size);}
export function renderForgeWorkshop(hud:Hud,game:GameSession,menu:string){
 const s=game.state,worn=new Set(Object.values(s.equipment)),ids=Object.keys(s.inventory).filter(id=>s.inventory[id]>0&&EQUIPMENT[id]?.kind!=='spell').sort((a,b)=>Number(a!==s.equipment.weapon)-Number(b!==s.equipment.weapon)||Number(worn.has(b))-Number(worn.has(a))||a.localeCompare(b));
 const requested=menu.split(':')[1],id=ids.includes(requested)?requested:s.equipment.weapon,item=EQUIPMENT[id],q=game.forging.enhancement(id),v=q.view!,result=menu.startsWith('forge-result:'),pool=menu.startsWith('forge-pool:'),ui=new RpgPanel(hud,game,'forge','ForgeWorkshop',true),u=ui.scale,hu=ui.hit/u,gap=ui.gap/u,a=ui.contentTop+hu+gap,b=ui.contentBottom,h=b-a;
 const T=(value:string,x:number,y:number,w:number,h=25,size=14,color=C.ink)=>ui.text(ui.panel,value,ui.x(x),ui.y(y),w*u,h*u,color,size*u),center=(value:string,x:number,y:number,w:number,h=25,size=14,color=C.ink)=>{const label=T(value,x,y,w,h,size,color);label.horizontalAlign=Label.HorizontalAlign.CENTER;return label;};
 const pane=(left:number,w:number,name:string)=>{const n=ui.surface(ui.panel,ui.x(left+w/2),ui.y((a+b)/2),w*u,h*u,C.background);n.name=name;return n;},left=pane(8,230,'ForgeEquipmentList'),middle=pane(246,316,'ForgeItem'),right=pane(572,264,'ForgeAction');ui.drape(right,264*u,h*u);
 const row=ui.hit+ui.gap,content=ui.scroll(left,0,0,218*u,h*u,ids.length*row);
 ids.forEach((key,i)=>{const d=EQUIPMENT[key],view=itemForgingView(s,key)!,n=ui.button(content,'',0,-ui.hit/2-i*row,210*u,'forge-item:'+key,true,false,ui.hit,undefined,'catalog');Controls.rowBackground(ui,n,210,hu-3,key===id);const icon=hud.node('ForgeListArt',n,-78*u,0,39*u,39*u),frame=equipmentIconFrame(icon,39*u,39*u,{quality:d.quality,scale:u});painted(ui,frame.content,d,37);const name=ui.text(n,`${d.name} +${view.rank}`,27*u,9*u,148*u,24*u,C.ink,14*u);name.enableWrapText=false;name.overflow=Label.Overflow.SHRINK;ui.text(n,`${d.quality} · ${equipmentTypeName(d)}`,27*u,-13*u,148*u,20*u,F.color(qualityFeedbackRole(d.quality)),11.5*u);});
 art(ui,ui.panel,'rpg-forge-approved-room-v7',ui.x(404),ui.y((a+b)/2),310,h);
 const weapon=hud.node('ForgeWeaponArt',ui.panel,ui.x(354),ui.y(a+h*.47),104*u,130*u);
 if(item.kind==='sword')art(ui,weapon,'rpg-approved-sword-v3',0,0,55,127);else{const frame=equipmentIconFrame(weapon,94*u,94*u,{quality:item.quality,scale:u});painted(ui,frame.content,item,92);}
 const title=T(`${item.name} +${v.rank}`,482,a+21,144,29,16.5);title.enableWrapText=false;title.overflow=Label.Overflow.SHRINK;T(`${item.quality} · ${equipmentTypeName(item)}`,482,a+45,144,24,12.5,F.color(qualityFeedbackRole(item.quality)));
 P.rule(ui,ui.panel,ui.x(482),ui.y(a+64),126);P.badge(ui,ui.panel,`阶段 +${v.cap}`,ui.x(482),ui.y(a+83),102,'gold');
 const affix=ui.button(ui.panel,'',ui.x(482),ui.y(b-hu/2),138*u,'ForgeAffixDetails',true,false,ui.hit,()=>hud.actions.click('forge-pool:'+id),'catalog');P.art(ui,affix,'button-dark',0,0,138,34,true);ui.text(affix,`词条 ${v.affixes.length}/${v.capacity} ›`,0,0,126*u,25*u,C.gold,14*u).horizontalAlign=Label.HorizontalAlign.CENTER;
 const stamped=!!s.dice.gear?.[id]?.claimed;P.art(ui,ui.panel,'plaque',ui.x(404),ui.y(b-15),300,27);center(stamped?'锻印已封存':'余火锻印',337,b-15,140,22,11.5,C.muted);affix.setSiblingIndex(ui.panel.children.length-1);
 if(pool){
  const candidates=q.next?.candidates??[],rows=[...Array.from({length:v.capacity},(_,i)=>v.affixes[i]?forgingAffixText(v.affixes[i]):`＋${[1,3,6][i]} 解锁随机属性`),'下一次随机候选',...candidates.map(c=>FORGING_STAT_NAMES[c.stat]+' '+(c.min===c.max?forgingValue(c.stat,c.min):forgingValue(c.stat,c.min)+'～'+forgingValue(c.stat,c.max)))],ch=40+rows.length*27,list=ui.scroll(right,0,0,246*u,h*u,ch*u);ui.text(list,`当前词条 ${v.affixes.length} / ${v.capacity}`,0,-15*u,236*u,28*u,C.gold,17*u);rows.forEach((text,i)=>ui.text(list,text,0,(-42-i*27)*u,236*u,26*u,C.ink,13*u));
 }else{
  const from=result?Math.max(0,v.rank-1):v.rank,to=result?v.rank:q.step?.rank??v.rank,preview=ui.button(ui.panel,'',ui.x(704),ui.y(a+42),248*u,'ForgeRandomDetails',true,false,84*u,()=>hud.actions.click('forge-pool:'+id),'catalog');
  Controls.cardBackground(ui,preview,248,82);ui.text(preview,result?'强化完成':'强化预览',0,27*u,234*u,25*u,C.ink,18*u).horizontalAlign=Label.HorizontalAlign.CENTER;ui.text(preview,`+${from}  →  +${to}`,0,0,232*u,34*u,F.color('state.selected'),23*u).horizontalAlign=Label.HorizontalAlign.CENTER;ui.text(preview,`阶段 +${v.cap} / 极限 +${v.maximum} · 词条 ›`,0,-28*u,234*u,23*u,C.gold,11.5*u).horizontalAlign=Label.HorizontalAlign.CENTER;
  const transaction=result?s.forging.transactions.slice().reverse().find(t=>t.kind==='enhance'&&t.item===id):undefined,cost=transaction?.kind==='enhance'?transaction:q.step;
  center(cost?`消耗 ${cost.gold} 金币 · ${cost.iron} 废铁`:'当前阶段已满',704,a+105,240,28,15);center(`拥有 ${s.player.gold} 金币 · ${s.player.iron} 废铁`,704,a+130,240,24,12,C.muted);
  const reason=q.reason.includes('请前往')?'需在检查点或洛恩工坊操作':!q.step?(v.rank>=v.maximum?'已达装备强化极限':'阶段已满，下阶段可继续培养'):q.reason,roll=v.lastRoll;
  center(result?(roll?(roll.added?'新增 ':'增强 ')+FORGING_STAT_NAMES[roll.stat]+' '+forgingValue(roll.stat,roll.amount):'强化记录已保存'):q.allowed?'成功率 100%':reason,704,b-19,240,38,12.5,result||q.allowed?F.color('state.success'):F.color('state.blocked'));
 }
 const primary=result?{label:q.step?'继续强化':'返回强化',action:'forge-item:'+id,enabled:true,primary:true}:{label:q.step?`强化 · ${q.step.gold}金币`:v.rank>=v.maximum?'已达装备极限':'已达阶段上限',action:q.step?`forge-submit:${id}:${q.token}`:'forge-info',enabled:q.allowed,primary:true};
 ui.footer(workshopStatus(game),[{label:pool?'返回预览':'传承预览',action:pool?'forge-item:'+id:'forge-targets:'+id},primary,{label:'返回旅途',action:'close'}]);workshopHeader(ui,id,'enhance');
}
