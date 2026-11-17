import {Color,Label,Node,Sprite,UITransform} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import {itemForgingView} from '../common/EquipmentForging';
import {EQUIPMENT,type ItemDef} from '../../equipment/data/Equipment';
import {forgingAffixText,forgingValue,forgingNextUnlock,FORGING_AFFIX_RANKS,FORGING_STAT_NAMES} from '../data/EquipmentForging';
import {qualityFeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {equipmentTypeName} from '../../equipment/runtime/EquipmentPresentation';
import {RpgPanel} from '../../../shared/ui/RpgPanel';
import {equipmentIconFrame} from '../../equipment/runtime/EquipmentIconFrame';
import type {Hud} from '../../../app/Hud';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {CompactMask as Mask} from '../../../shared/ui/CompactMask';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {PreparationControls as Controls} from '../../../shared/ui/PreparationControls';
import {PREPARATION_DESIGN as D,preparationSkinAsset} from '../../../shared/ui/PreparationTheme';
import {gemText} from '../../gems/locales';
import {materialName,materialBalance} from '../common/CultivationRewards';
function art(ui:RpgPanel,parent:Node,id:string,x:number,y:number,w:number,h:number){const sprite=UiSkin.asset(parent,id,w*ui.scale,h*ui.scale,false);sprite.node.setPosition(x,y);return sprite;}
export function workshopStatus(game:GameSession){const access=game.forgingAvailability();return access.available?(game.preparationAvailability().available?'安全检查点 · 可强化':'洛恩工坊 · 可强化'):access.reason.includes('请前往')?'前往检查点或洛恩工坊整备':access.reason;}
/** The approved metal tabs sit inside independent 48px mobile targets. */
export function workshopHeader(ui:RpgPanel,id:string,active:'enhance'|'transfer'|'gems'){
 const u=ui.scale,cy=ui.contentTop+ui.hit/u/2;art(ui,ui.panel,'rpg-anvil-v2',ui.x(43),ui.y(cy),34,23);ui.text(ui.panel,'洛恩的工坊',ui.x(178),ui.y(cy),198*u,30*u,C.ink,20*u);
 const tabs:[string,string,string][]=[['强化',`forge-item:${id}`,'enhance'],[gemText('workshop.tab'),`gems:${id}`,'gems'],['传承',`forge-targets:${id}`,'transfer']];
 tabs.forEach(([label,action,key],i)=>{const selected=key===active,n=ui.tab(ui.panel,label,ui.x(344+i*88),ui.y(cy),76*u,action),plate=art(ui,n,selected?'rpg-forge-tab-gold-v7':'rpg-forge-tab-dark-v7',0,0,selected?79:76,selected?28:25);plate.node.setSiblingIndex(0);n.children.filter(c=>c.getComponent(Label)).forEach(c=>{const text=c.getComponent(Label)!;text.color=selected?C.dark:C.ink;text.fontSize=17*u;});});
 art(ui,ui.panel,'rpg-forge-header-rule-v7',ui.x(704),ui.y(cy),218,9.4);
}
function painted(ui:RpgPanel,parent:Node,item:ItemDef,size:number){const kind=['sword','bow','staff'].includes(item.kind)?item.kind:item.kind==='ring'?'ring':item.slot;return art(ui,parent,kind==='offhand'?D.artwork.offhand:preparationSkinAsset('item-'+kind),0,0,size,size);}
/** Keep the original gold confirmation plate without changing the shared footer. */
export function workshopConfirm(ui:RpgPanel,action:string,enabled=true){
 const button=ui.panel.children.find(n=>n.name===action);if(!button)return;
 button.children.forEach(n=>{if(n.getComponent(Sprite))n.active=false;});
 const bounds=button.getComponent(UITransform)!;art(ui,button,'rpg-forge-confirm-v7',0,0,bounds.width/ui.scale,31.5).color=enabled?Color.WHITE:F.color('text.disabled',185);
 button.children.filter(n=>n.getComponent(Label)).forEach(n=>n.setSiblingIndex(button.children.length-1));
}
export function renderForgeWorkshop(hud:Hud,game:GameSession,menu:string){
 const s=game.state,worn=new Set(Object.values(s.equipment)),ids=Object.keys(s.inventory).filter(id=>s.inventory[id]>0&&EQUIPMENT[id]?.kind!=='spell').sort((a,b)=>Number(a!==s.equipment.weapon)-Number(b!==s.equipment.weapon)||Number(worn.has(b))-Number(worn.has(a))||a.localeCompare(b));
 const requested=menu.split(':')[1],id=ids.includes(requested)?requested:s.equipment.weapon,item=EQUIPMENT[id],q=game.forging.enhancement(id),v=q.view!,result=menu.startsWith('forge-result:')||menu.startsWith('forge-cost:')&&menu.split(':')[2]==='result',pool=menu.startsWith('forge-pool:'),costDetails=menu.startsWith('forge-cost:'),ui=new RpgPanel(hud,game,'forge','ForgeWorkshop',true),u=ui.scale,hu=ui.hit/u,gap=ui.gap/u,a=ui.contentTop+hu+gap,b=ui.contentBottom,h=b-a;
 const unlock=forgingNextUnlock(s.progression.level),next=unlock&&unlock.rank<=v.maximum?unlock:undefined;
 const pane=(left:number,w:number,name:string)=>{const n=ui.surface(ui.panel,ui.x(left+w/2),ui.y((a+b)/2),w*u,h*u,C.background);n.name=name;return n;},left=pane(8,230,'ForgeEquipmentList'),middle=pane(246,316,'ForgeItem'),right=pane(572,264,'ForgeAction');ui.drape(right,264*u,h*u);
 const text=(parent:Node,value:string,x:number,y:number,w:number,height=25,size=14,color=C.ink,center=false)=>{const label=ui.text(parent,value,x*u,y*u,w*u,height*u,color,size*u);if(center)label.horizontalAlign=Label.HorizontalAlign.CENTER;return label;};
 // The heading and independently scrolling rows retain the approved left column.
 text(left,'选择装备',-48,h/2-16,112,28,18);art(ui,left,'rpg-forge-list-rule-v7',49*u,(h/2-16)*u,110,5.7);art(ui,left,'rpg-forge-list-underline-v7',-72*u,(h/2-29)*u,66,5);
 const row=ui.hit+ui.gap,listHeight=Math.max(ui.hit,h*u-37*u),content=ui.scroll(left,0,-18.5*u,218*u,listHeight,ids.length*row);
 ids.forEach((key,i)=>{const d=EQUIPMENT[key],view=itemForgingView(s,key)!,n=ui.button(content,'',0,-ui.hit/2-i*row,210*u,'forge-item:'+key,true,false,ui.hit,undefined,'catalog');Controls.rowBackground(ui,n,210,hu-3,key===id);const icon=hud.node('ForgeListArt',n,-78*u,0,39*u,39*u),frame=equipmentIconFrame(icon,39*u,39*u,{quality:d.quality,scale:u});painted(ui,frame.content,d,37);const name=text(n,`${d.name} +${view.rank}`,27,9,148,24,14);name.enableWrapText=false;text(n,`${d.quality} · ${equipmentTypeName(d)}`,27,-13,148,20,11.5,F.color(qualityFeedbackRole(d.quality)));});
 // Preserve the room's aspect ratio; only its margins crop in the shorter mobile body.
 const scene=hud.node('ForgeRoom',middle,0,0,310*u,h*u);scene.addComponent(Mask).type=Mask.Type.GRAPHICS_RECT;
 const roomWidth=Math.max(310,h*696/556);art(ui,scene,'rpg-forge-approved-room-v7',0,0,roomWidth,roomWidth*556/696);
 const anvilWidth=245,anvilHeight=anvilWidth*145/495;art(ui,scene,'rpg-forge-anvil-v7',0,(-h/2+anvilHeight/2)*u,anvilWidth,anvilHeight);
 const swordHeight=Math.max(96,h-anvilHeight*.87-3),swordY=-h/2+anvilHeight*.87+swordHeight/2,iconSize=Math.min(136,Math.max(1,h-anvilHeight-16)),weaponWidth=item.kind==='sword'?swordHeight*55/127:iconSize,weaponHeight=item.kind==='sword'?swordHeight:iconSize;
 // Short rooms fit the complete square above the stone, with an 8-unit gap
 // on each side. Full-size desktop squares retain their original anchor.
 const weaponY=item.kind==='sword'||iconSize===136?swordY:-h/2+anvilHeight+8+iconSize/2;
 // Reserve the existing name/quality column, including the icon's full frame.
 // Square armour art extends beyond the old 110-wide host into that column.
 const titleX=78,titleWidth=145,weaponX=Math.min(-43,titleX-titleWidth/2-12-weaponWidth/2),weapon=hud.node('ForgeWeaponArt',scene,weaponX*u,weaponY*u,weaponWidth*u,weaponHeight*u);
 if(item.kind==='sword')art(ui,weapon,'rpg-approved-sword-v3',0,0,weaponWidth,swordHeight);else{const frame=equipmentIconFrame(weapon,iconSize*u,iconSize*u,{quality:item.quality,scale:u});painted(ui,frame.content,item,iconSize-2);}
 const title=text(scene,`${item.name} +${v.rank}`,titleX,h/2-29,titleWidth,42,16.5);title.enableWrapText=true;text(scene,`${item.quality} · ${equipmentTypeName(item)}`,titleX,h/2-64,titleWidth,24,12.5,F.color(qualityFeedbackRole(item.quality)));art(ui,scene,'rpg-forge-name-rule-v7',titleX*u,(h/2-81)*u,112,9);
 art(ui,scene,'rpg-forge-stamp-v7',0,(-h/2+18)*u,174,29.4);text(scene,v.rank?'强化锻印 · 已完成':'洛恩的强化台',13,-h/2+18,137,24,12.5,C.ink,true);
 const transaction=result?s.forging.transactions.slice().reverse().find(t=>t.kind==='enhance'&&t.item===id):undefined,cost=transaction?.kind==='enhance'?transaction:q.step;
 const reason=q.reason.includes('请前往')?'需在检查点或洛恩工坊操作':!q.step?(v.rank>=v.maximum?'已达装备强化极限':next?`Lv${next.level} 开放强化 +${next.rank}`:'已达当前等级上限'):q.reason,roll=v.lastRoll;
 const list=ui.scroll(right,0,0,246*u,h*u,(pool?Math.max(h,110+(v.capacity+(q.next?.candidates.length??0))*31):costDetails?Math.max(h,280+hu):Math.max(h,304+2*hu))*u);
 const line=(value:string,y:number,size=14,color=C.ink,center=false,height=25)=>text(list,value,0,-y,236,height,size,color,center);
 const rule=(y:number)=>art(ui,list,'rpg-forge-rule-v7',0,-y*u,238,6.9);
 if(pool){
  line('强化词条',15,18);rule(32);line(`当前词条 ${v.affixes.length} / ${v.capacity}`,51,14,C.gold);
  for(let i=0;i<v.capacity;i++)line(v.affixes[i]?forgingAffixText(v.affixes[i]):`＋${FORGING_AFFIX_RANKS[i]} 解锁随机属性`,78+i*31,13);
  const start=87+v.capacity*31;rule(start-12);line('下一次随机候选',start+4,15,C.gold);
  (q.next?.candidates??[]).forEach((c,i)=>line(`${FORGING_STAT_NAMES[c.stat]} ${c.min===c.max?forgingValue(c.stat,c.min):forgingValue(c.stat,c.min)+'～'+forgingValue(c.stat,c.max)} · ${Math.round(c.probability*100)}%`,start+34+i*31,12.5));
 }else if(costDetails){
  line(result?'本次费用明细':'强化费用明细',15,18);rule(32);
  line(`${cost?.gold??0} 金币 · 拥有 ${s.player.gold}`,55);line(`${cost?.iron??0} 废铁 · 拥有 ${s.player.iron}`,83);
  line(`${materialName(transaction?.kind==='enhance'?transaction.materialTier:q.materialTier)} ×${transaction?.kind==='enhance'?transaction.materialCount:q.materialCount}`,111,14,C.gold);
  line(`强化石库存 ${materialBalance(s)}`,141,12.5,C.muted,false,38);
  line(`符纹 ${cost?.runes??0} / 拥有 ${s.player.runes}`,178);line(`锻造芯 ${cost?.cores??0} / 拥有 ${s.player.cores}`,206);
  line(next?`下一阶：Lv${next.level} 开放 +${next.rank}`:`角色上限 +${v.stage} · ${item.quality}极限 +${v.maximum}`,237,12.5,C.muted);
  const material=ui.button(list,'强化石材料与合成 ›',0,-(270+hu/2)*u,236*u,'forge-materials',true,false,ui.hit,undefined,'catalog');art(ui,material,'rpg-forge-tab-dark-v7',0,0,224,32).node.setSiblingIndex(0);
 }else{
  line(result?'强化完成':'强化预览',15,18);art(ui,list,'rpg-forge-heading-rule-v7',0,-32*u,238,6);
  text(list,`+${result?Math.max(0,v.rank-1):v.rank}`,-64,-57,86,37,26,C.ink,true);art(ui,list,'rpg-forge-arrow-v7',0,-57*u,25,15.7);text(list,`+${result?v.rank:q.step?.rank??v.rank}`,64,-57,86,37,26,F.color('state.success'),true);rule(81);
  const affix=ui.button(list,'',0,-(89+hu/2)*u,236*u,'forge-pool:'+id,true,false,ui.hit,undefined,'catalog');art(ui,affix,'rpg-stat-power-v3',-104*u,0,17,17);text(affix,result&&roll?(roll.added?'新增 ':'增强 ')+FORGING_STAT_NAMES[roll.stat]:q.next?.added?'随机新增属性':'随机增强属性',-12,0,158,28,14);text(affix,result&&roll?forgingValue(roll.stat,roll.amount):`${q.next?.candidates.length??0} 项候选 ›`,88,0,66,26,12.5,C.gold,true);
  const caps=99+hu;rule(caps);art(ui,list,'rpg-forge-stage-v7',-103*u,-(caps+20)*u,17,16.5);text(list,`角色等级上限  +${v.stage}`,15,-caps-20,204,25,14);art(ui,list,'rpg-forge-limit-v7',-103*u,-(caps+45)*u,18.7,16);text(list,`${item.quality}装备极限  +${v.maximum}`,15,-caps-45,204,25,14);rule(caps+64);
  line(result?'本次消耗':'强化消耗',caps+82,16);rule(caps+98);
  const feesY=caps+104+hu/2,fees=ui.button(list,'',0,-(feesY+25)*u,236*u,'forge-cost:'+id+(result?':result':''),true,false,ui.hit+50*u,undefined,'catalog');art(ui,fees,'rpg-forge-coin-v7',-100*u,25*u,34,32.3);text(fees,`${cost?.gold??0} 金币`,-44,25,74,27,14);art(ui,fees,'rpg-forge-iron-v7',23*u,25*u,34.9,32);text(fees,`${cost?.iron??0} 废铁`,79,25,74,27,14);
  line(`拥有：${s.player.gold} 金币 · ${s.player.iron} 废铁`,feesY+hu/2+14,12.5,C.muted,true);
  line('费用含强化石 · 查看明细 ›',feesY+hu/2+36,11.5,C.gold,true);
  const feedback=result?'✓ 强化记录已保存':q.allowed?'✓ 成功率 100%':reason;rule(feesY+hu/2+55);line(feedback,feesY+hu/2+77,12.5,result||q.allowed?F.color('state.success'):F.color('state.blocked'),true,38);
 }
 const primary=result?{label:q.step?'继续强化':'返回强化',action:'forge-item:'+id,enabled:true,primary:true}:{label:q.step?`确认强化 · ${q.step.gold}金币`:v.rank>=v.maximum?'已达装备极限':next?`Lv${next.level} 开放 +${next.rank}`:'已达等级上限',action:q.step?`forge-submit:${id}:${q.token}`:'forge-info',enabled:q.allowed,primary:true};
 const secondary={back:pool||costDetails,label:pool||costDetails?'返回预览':'传承预览',action:pool||costDetails?'forge-item:'+id:'forge-targets:'+id};
 ui.footer(workshopStatus(game),[secondary,primary,{label:'返回旅途',action:'close'}]);
 const confirm=ui.panel.children.find(n=>n.name===primary.action),back=!secondary.back&&ui.panel.children.find(n=>n.name===secondary.action);if(confirm){confirm.getComponent(UITransform)!.width=176*u;confirm.setPosition(ui.x(744),ui.footerY);confirm.children.forEach(n=>{const label=n.getComponent(Label);if(label){n.getComponent(UITransform)!.width=168*u;label.overflow=Label.Overflow.CLAMP;}});}if(back)back.setPosition(ui.x(570),ui.footerY);
 const status=ui.panel.children.find(n=>n.name==='FooterStatus');if(status){const bounds=status.getComponent(UITransform)!,left=status.position.x-bounds.width/2,right=ui.x(secondary.back?656:500)-ui.gap,width=Math.max(90*u,right-left);bounds.width=width;status.setPosition(left+width/2,ui.footerY);status.children.forEach(n=>{const bounds=n.getComponent(UITransform);if(bounds)bounds.width=width;});}ui.panel.children.filter(n=>n.name==='FooterFlourish').forEach(n=>n.active=false);
 workshopConfirm(ui,primary.action,primary.enabled);workshopHeader(ui,id,'enhance');
}
