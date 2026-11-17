import type {GameSession} from '../../../core/GameSession';
import type {Hud} from '../../../app/Hud';
import {EQUIPMENT} from '../data/Equipment';
import {equipmentText as et} from '../locales';
import {dismantlingYield,materialName,type DismantlingMode} from '../../crafting/common/CultivationRewards';
import {equipmentIcon} from './EquipmentPresentation';

/** Reuse the standard scrollable list, fixed actions and safe-area shell. No inventory changes while browsing. */
export function renderEquipmentDismantling(hud:Hud,game:GameSession,menu:string):boolean{
 if(!menu.startsWith('dismantle:')&&!menu.startsWith('dismantle-preview:'))return false;
 const parts=menu.split(':'),preview=parts[0]==='dismantle-preview',mode=(preview?parts[1]:'stack') as DismantlingMode,item=preview?parts[2]:parts[1],q=game.cultivation.dismantling(item??'',mode);
 const materials=(bank:Record<number,number>)=>Object.entries(bank).map(([tier,count])=>`${materialName(Number(tier))} ×${count}`).join(' · ');
 if(preview){
  hud.showList(et('dismantle.confirmTitle'),[et('dismantle.hint'),et('dismantle.summary',{count:q.count,materials:materials(q.materials)||'—'}),q.reason||et('dismantle.confirmHint')].join('\n'),q.entries.map(e=>({label:et('dismantle.previewItem',{name:EQUIPMENT[e.id].name,count:e.count}),detail:et('dismantle.previewDetail',{owned:e.owned,remaining:e.owned-e.count,material:materialName(e.tier),count:e.materials}),action:'dismantle-info',disabled:true,icon:equipmentIcon(EQUIPMENT[e.id])})),[
   {label:et('dismantle.confirm',{count:q.count}),action:`dismantle-submit:${mode}:${q.id}:${q.token}`,disabled:!q.allowed,primary:true},
   {back:true,label:et('dismantle.cancel'),action:'dismantle:'+q.id},
  ],hud.touchTargetSize,{placement:'right'});return true;
 }
 const all=game.cultivation.dismantling(q.id,'all'),one=game.cultivation.dismantling(q.id,'one'),entries=all.entries.slice().sort((a,b)=>Number(b.id===q.id)-Number(a.id===q.id)||a.id.localeCompare(b.id));
 hud.showList(et('dismantle.title'),[et('dismantle.hint'),et('dismantle.rule'),all.reason||et('dismantle.allHint')].join('\n'),entries.map(e=>({label:et('dismantle.item',{name:EQUIPMENT[e.id].name,owned:e.owned}),detail:et('dismantle.itemDetail',{count:e.count,material:materialName(e.tier),yield:dismantlingYield(e.id)!.count}),action:'dismantle-preview:stack:'+e.id,selected:e.id===q.id,icon:equipmentIcon(EQUIPMENT[e.id])})),[
  {label:et('dismantle.one'),action:'dismantle-preview:one:'+q.id,disabled:!one.allowed},
  {label:et('dismantle.all'),action:'dismantle-preview:all:'+q.id,disabled:!all.allowed},
  {back:true,label:et('dismantle.back'),action:'inventory'},
 ],hud.touchTargetSize,{placement:'right'});return true;
}
