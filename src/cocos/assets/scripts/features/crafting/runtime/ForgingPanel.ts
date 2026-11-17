import type {GameSession} from '../../../core/GameSession';
import {Label} from 'cc';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import {equipmentText as et} from '../../equipment/locales';
import {forgingSlot} from '../data/EquipmentForging';
import {Hud} from '../../../app/Hud';
import {equipmentIcon} from '../../equipment/runtime/EquipmentPresentation';
import {renderForgeWorkshop,workshopHeader,workshopStatus,workshopConfirm} from './ForgeWorkshop';
import {RpgPanel,type RpgFooterAction} from '../../../shared/ui/RpgPanel';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {PreparationSkin as P} from '../../../shared/ui/PreparationSkin';
import {PREPARATION_DESIGN as D} from '../../../shared/ui/PreparationTheme';
import {materialName,materialStock,materialBalance,MATERIAL_TIER_LEVELS,MATERIAL_RANK_TIERS} from '../common/CultivationRewards';

/** Workshop services share the approved shell and guarded cost previews. */
export function renderForging(hud:Hud,game:GameSession,menu:string):boolean {
 if(menu!=='forge'&&!menu.startsWith('forge-'))return false;
 if(menu==='forge'||/^forge-(item|result|pool|cost):/.test(menu)){renderForgeWorkshop(hud,game,menu);return true;}
 const s=game.state,p=s.player,parts=menu.split(':'),item=parts[1],d=EQUIPMENT[item],balance=`金币 ${p.gold} · 废铁 ${p.iron} · 符纹 ${p.runes} · 锻造芯 ${p.cores}`,footer=[{label:'装备培养',action:'forge'},{back:true,label:'返回背包',action:'inventory'}];
 const show=(title:string,subtitle:string,rows:Parameters<Hud['showList']>[2],buttons:RpgFooterAction[]=footer)=>{
  const ui=new RpgPanel(hud,game,'forge','ForgeServices',true),u=ui.scale,top=ui.bodyTop-ui.hit-ui.gap,h=top-ui.bodyBottom;
  const body=ui.surface(ui.panel,ui.x(422),(top+ui.bodyBottom)/2,828*u,h,C.background);body.name='ForgeServiceRows';
  const width=(828-2*D.contentInsets.text)*u,summaryHeight=subtitle.split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil(line.length/55)),0)*19*u,heights=rows.map(r=>Math.max(ui.hit,(30+(r.detail??'').split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil(line.length/55)),0)*19)*u)),introHeight=58*u+summaryHeight,content=ui.scroll(body,0,0,804*u,h,introHeight+heights.reduce((n,r)=>n+r+ui.gap,0));
  ui.text(content,title,0,-18*u,width,32*u,C.ink,18*u);P.rule(ui,content,0,-36*u,804-2*D.contentInsets.rule);const summary=ui.text(content,subtitle,0,-(48*u+summaryHeight/2),width,summaryHeight,C.muted,13*u);summary.verticalAlign=Label.VerticalAlign.TOP;let y=-introHeight;
  rows.forEach((row,i)=>{const height=heights[i],node=ui.button(content,'',0,y-height/2,796*u,row.action,!row.disabled,false,height,undefined,'catalog');ui.feedback(node,796*u,height);const name=ui.text(node,row.label+(row.disabled?'':' ›'),0,height/2-15*u,width,26*u,row.disabled?C.gold:C.ink,15*u);name.horizontalAlign=Label.HorizontalAlign.LEFT;if(row.detail){const detail=ui.text(node,row.detail,0,-13*u,width,Math.max(22*u,height-30*u),C.muted,12.5*u);detail.verticalAlign=Label.VerticalAlign.TOP;}P.rule(ui,content,0,y-height-3*u,804-2*D.contentInsets.rule);y-=height+ui.gap;});
  ui.footer(workshopStatus(game),buttons);buttons.filter(b=>b.primary).forEach(b=>workshopConfirm(ui,b.action,b.enabled!==false));workshopHeader(ui,item||s.equipment.weapon,menu==='forge-materials'?'enhance':'transfer');
 };
 if(menu==='forge-materials'){
  const rows=[1,2,3,4,5].map(tier=>{const q=game.cultivation.synthesis(tier),uses=MATERIAL_RANK_TIERS.flatMap((value,i)=>value===tier?['＋'+(i+1)]:[]).join('／');return {label:`${materialName(tier)} · 拥有 ${materialStock(s,tier)}`,detail:`用于强化 ${uses}\n`+(tier===5?'最高阶强化材料':`Lv${MATERIAL_TIER_LEVELS[tier]}合成下阶 · 3 → 1 · ${q.gold}金币${q.allowed?'':'\n'+q.reason}`),action:tier===5?'forge-info':`forge-stone-synthesize:${tier}:${q.token}`,disabled:tier===5||!q.allowed};});
  rows.push({label:et('dismantle.title'),detail:et('dismantle.source'),action:'dismantle:'+s.equipment.weapon,disabled:false});
  rows.push({label:'强化石来源',detail:'真实击杀后自动收集：普通怪约3杀1石，精英每杀1石，Boss每杀3石。任务完成也有培养奖励。',action:'forge-info',disabled:true});
  show('分级强化材料',`强化石 ${materialBalance(s)}\n每次强化消耗对应阶材料。\n3枚低阶石合成1枚高阶石，合成随角色等级开放。`,rows,[{back:true,label:'返回强化',action:'forge'},{label:et('dismantle.action'),action:'dismantle:'+s.equipment.weapon},{label:'宝石材料',action:`gem-stock:${s.equipment.weapon}`}]);return true;
 }
 if(!d||!s.inventory[item]){show('装备养成','尚未拥有这件装备。',[]);return true;}
 if(menu.startsWith('forge-targets:')){
  const ids=Object.keys(s.inventory).filter(id=>id!==item&&s.inventory[id]>0&&EQUIPMENT[id]&&forgingSlot(d)===forgingSlot(EQUIPMENT[id]));
  show('选择传承目标',`来源：${game.itemView(item).name}\n${ids.length?'传给未培养的同部位装备，强化等级不变；原装备与特效保留。':'尚无其他同部位装备，可以先继续探索。'}`,ids.map(id=>{const q=game.forging.transfer(item,id);return {label:EQUIPMENT[id].name,detail:q.allowed?`传承后＋${q.after} · 费用 ${q.gold} 金币`:q.reason,action:`forge-transfer:${item}:${id}`,icon:equipmentIcon(EQUIPMENT[id]),disabled:!q.allowed};}),[{back:true,label:'返回来源装备',action:`forge-item:${item}`},{label:'装备列表',action:'forge'}]);return true;
 }
 if(menu.startsWith('forge-transfer:')){
  const q=game.forging.transfer(item,parts[2]),target=EQUIPMENT[q.to];
  show('确认强化传承',`${balance}\n${q.allowed?'来源强化等级归零，目标获得同等强化等级；装备与原生特效保留。':q.reason}`,[
   {label:'来源 · '+d.name,detail:`＋${q.source?.rank??0} → ＋0 · 保留装备与随机记录`,action:'forge-info',disabled:true,icon:equipmentIcon(d)},
   {label:'目标 · '+(target?.name??'请选择装备'),detail:`＋${q.target?.rank??0} → ＋${q.after} · 按目标装备生成既定词条`,action:'forge-info',disabled:true,icon:target?equipmentIcon(target):undefined},
   {label:'传承条件',detail:'目标须未培养且上限足够；强化不叠加。',action:'forge-info',disabled:true},
  ],[{back:true,label:'取消传承',action:`forge-item:${item}`},{label:'重新选择目标',action:`forge-targets:${item}`},{label:`确认传承 · ${q.gold}金币`,action:`forge-inherit:${item}:${q.to}:${q.token}`,enabled:q.allowed,primary:true}]);return true;
 }
 return false;
}
