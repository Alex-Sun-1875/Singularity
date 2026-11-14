import type {GameSession} from '../../../core/GameSession';
import {Label} from 'cc';
import {EQUIPMENT,RECIPES} from '../../equipment/data/Equipment';
import {forgingSlot} from '../data/EquipmentForging';
import {Hud} from '../../../app/Hud';
import {equipmentIcon} from '../../equipment/runtime/EquipmentPresentation';
import {renderForgeWorkshop,workshopHeader,workshopStatus} from './ForgeWorkshop';
import {RpgPanel} from '../../../shared/ui/RpgPanel';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {PreparationSkin as P} from '../../../shared/ui/PreparationSkin';
import {PreparationControls as Controls} from '../../../shared/ui/PreparationControls';

/** Workshop services share the approved shell and guarded cost previews. */
export function renderForging(hud:Hud,game:GameSession,menu:string):boolean {
 if(menu!=='craft'&&!menu.startsWith('craft-preview:')&&menu!=='forge'&&!menu.startsWith('forge-'))return false;
 if(menu==='forge'||/^forge-(item|result|pool):/.test(menu)){renderForgeWorkshop(hud,game,menu);return true;}
 const s=game.state,p=s.player,access=game.forgingAvailability(),parts=menu.split(':'),item=parts[1],d=EQUIPMENT[item],balance=`金币 ${p.gold} · 废铁 ${p.iron} · 符纹 ${p.runes} · 锻造芯 ${p.cores}`,footer=[{label:'装备养成',action:'forge'},{label:'锻造配方',action:'craft'},{label:'返回行囊',action:'inventory'}];
 const show=(title:string,subtitle:string,rows:Parameters<Hud['showList']>[2],buttons=footer)=>{
  const ui=new RpgPanel(hud,game,'forge','ForgeServices',true),u=ui.scale,craft=menu.startsWith('craft'),top=ui.bodyTop-ui.hit-ui.gap,h=top-ui.bodyBottom;
  const intro=ui.surface(ui.panel,ui.x(146),(top+ui.bodyBottom)/2,276*u,h,C.background),body=ui.surface(ui.panel,ui.x(564),(top+ui.bodyBottom)/2,544*u,h,C.background);intro.name='ForgeServiceSummary';body.name='ForgeServiceRows';
  ui.text(intro,title,0,h/2-18*u,250*u,32*u,C.ink,18*u);P.rule(ui,intro,0,h/2-38*u,246);const summary=ui.text(intro,subtitle,0,-18*u,248*u,h-62*u,C.muted,13*u);summary.verticalAlign=Label.VerticalAlign.TOP;
  const heights=rows.map(r=>Math.max(ui.hit,(28+Math.ceil((r.detail?.length??0)/34)*18)*u)),content=ui.scroll(body,0,0,524*u,h,heights.reduce((n,r)=>n+r+ui.gap,0));let y=0;
  rows.forEach((row,i)=>{const height=heights[i],node=ui.button(content,'',0,y-height/2,516*u,row.action,!row.disabled,false,height,undefined,'catalog');Controls.rowBackground(ui,node,516,height/u-3);const title=ui.text(node,row.label,0,height/2-14*u,486*u,24*u,row.disabled?C.gold:C.ink,15*u);title.horizontalAlign=Label.HorizontalAlign.LEFT;if(row.detail){const detail=ui.text(node,row.detail,0,-12*u,486*u,Math.max(22*u,height-28*u),C.muted,12.5*u);detail.verticalAlign=Label.VerticalAlign.TOP;}y-=height+ui.gap;});
  ui.footer(workshopStatus(game),buttons);workshopHeader(ui,item||s.equipment.weapon,craft?'craft':'transfer');
 };
 if(menu==='craft'){
  const recipes=s.recipes.filter(id=>RECIPES[id]&&EQUIPMENT[RECIPES[id].item]);
  show('洛恩的锻造手艺',`${balance}\n${access.available?'首件教学免金币工费；图纸与材料仍需备齐。':access.reason}`,recipes.length?recipes.map(id=>{const q=game.forging.craft(id),item=EQUIPMENT[q.item!];return {label:item.name,detail:`${s.inventory[item.id]?'已经拥有':q.teaching?'教学工费 0 金币':`工费 ${q.gold} 金币`} · 铁 ${q.iron} / 符纹 ${q.runes} / 芯 ${q.cores}`,action:`craft-preview:${id}`,icon:equipmentIcon(item)};}):[{label:'尚未学习锻造图纸',detail:'任务与探索可以获得图纸，学会后永久保留。',action:'forge-info',disabled:true}]);return true;
 }
 if(menu.startsWith('craft-preview:')){
  const q=game.forging.craft(item),result=EQUIPMENT[q.item!];if(!result){show('锻造图纸','这张图纸暂不可用。',[]);return true;}
  show('锻造 · '+result.name,`${balance}\n${q.allowed?'确认后一次扣除费用并获得装备。':q.reason}`,[
   {label:'成品与强化极限',detail:`${result.quality} · 装备极限＋${result.maxEnhance} · 每旅程唯一`,action:'forge-info',disabled:true,icon:equipmentIcon(result)},
   {label:q.teaching?'确认锻造 · 免工费':'确认锻造',detail:`金币 ${q.gold} · 铁 ${q.iron} · 符纹 ${q.runes} · 锻造芯 ${q.cores}`,action:`craft-submit:${item}:${q.token}`,disabled:!q.allowed},
   {label:'查看装备效果',detail:result.description,action:'forge-info',disabled:true},
  ]);return true;
 }
 if(!d||!s.inventory[item]){show('装备养成','尚未拥有这件装备。',[]);return true;}
 if(menu.startsWith('forge-targets:')){
  const ids=Object.keys(s.inventory).filter(id=>id!==item&&s.inventory[id]>0&&EQUIPMENT[id]&&forgingSlot(d)===forgingSlot(EQUIPMENT[id]));
  show('选择传承目标',`来源：${game.itemView(item).name}\n${ids.length?'原装备与独有特效保留；强化经验转移，不复制。':'尚无其他同部位装备，可以先继续探索。'}`,ids.map(id=>{const q=game.forging.transfer(item,id);return {label:EQUIPMENT[id].name,detail:`传承后＋${q.after} · 费用 ${q.gold} 金币${q.reserve?` · 保留经验 ${q.reserve}`:''}`,action:`forge-transfer:${item}:${id}`,icon:equipmentIcon(EQUIPMENT[id])};}),[{label:'返回来源装备',action:`forge-item:${item}`},{label:'装备列表',action:'forge'}]);return true;
 }
 if(menu.startsWith('forge-transfer:')){
  const q=game.forging.transfer(item,parts[2]),target=EQUIPMENT[q.to];
  show('确认强化传承',`${balance}\n${q.allowed?'转出后来源装备的强化经验清零，物品与骰印保留。':q.reason}`,[
   {label:'来源 · '+d.name,detail:`＋${q.source?.rank??0} → ＋0 · 转移 ${q.experience} 经验`,action:'forge-info',disabled:true,icon:equipmentIcon(d)},
   {label:'目标 · '+(target?.name??'请选择装备'),detail:`＋${q.target?.rank??0} → ＋${q.after} · 未生效经验 ${q.reserve}`,action:'forge-info',disabled:true,icon:target?equipmentIcon(target):undefined},
   {label:`确认传承 · ${q.gold}金币`,detail:'保留超额经验；原生特效、免费骰印不转移。',action:`forge-inherit:${item}:${q.to}:${q.token}`,disabled:!q.allowed},
  ],[{label:'重新选择目标',action:`forge-targets:${item}`},{label:'取消传承',action:`forge-item:${item}`}]);return true;
 }
 return false;
}
