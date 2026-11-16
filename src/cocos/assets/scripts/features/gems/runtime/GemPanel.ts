import {Label,Node} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import type {Hud} from '../../../app/Hud';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import {equipmentIcon} from '../../equipment/runtime/EquipmentPresentation';
import {equipmentIconFrame} from '../../equipment/runtime/EquipmentIconFrame';
import {forgingSlot} from '../../crafting/data/EquipmentForging';
import {workshopHeader} from '../../crafting/runtime/ForgeWorkshop';
import {itemGemView,pendingGemView} from '../common/GemWorkshop';
import {GEM_STATS,gemValueText,type GemStat} from '../data/Gems';
import {gemText as t,type GemMessageKey} from '../locales';
import {RpgPanel} from '../../../shared/ui/RpgPanel';
import {PreparationSkin as P} from '../../../shared/ui/PreparationSkin';
import {PreparationControls as Controls} from '../../../shared/ui/PreparationControls';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {qualityFeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {PREPARATION_DESIGN as D,preparationSkinAsset} from '../../../shared/ui/PreparationTheme';
import type {MenuRow,MenuChoice} from '../../../shared/ui/MenuPanel';

type Quote={allowed:boolean;reason?:string;reasonKey?:string;token:string;gold:number;drills:number;shards:number;units:number;stock:number};
const tierName=(tier:number)=>['','Ⅰ','Ⅱ','Ⅲ','Ⅳ','Ⅴ'][tier]??String(tier);
const statName=(stat:GemStat)=>t(('stat.'+stat) as GemMessageKey);
const reason=(q:Quote)=>q.reasonKey==='reason.busy'?q.reason??t('reason.busy'):q.reasonKey?t(q.reasonKey as GemMessageKey):q.reason??'';
const quoteDetail=(q:Quote,detail:string)=>q.allowed?detail:detail+'\n'+reason(q);
const stock=(g:GameSession,stat:GemStat,tier:number)=>g.state.gems.bank[`${stat}:${tier}`]??0;
const returnMenus=new WeakMap<GameSession,string>();
/** Called only when entering gem cultivation from a different feature. */
export function beginGemVisit(game:GameSession,previousMenu:string){
 if(previousMenu==='gems'||previousMenu.startsWith('gems:')||previousMenu.startsWith('gem-'))return;
 const requested=previousMenu.split(':')[1],item=EQUIPMENT[requested]?requested:game.state.equipment.weapon;
 returnMenus.set(game,previousMenu==='forge'||previousMenu.startsWith('forge-')?'forge-item:'+item:previousMenu==='craft'||previousMenu.startsWith('craft-preview:')?previousMenu:'inventory');
}

/** Gem operations are explicit, quoted actions. The app owns all mutations and routes. */
export function renderGemPanel(hud:Hud,game:GameSession,menu:string):boolean {
 if(menu!=='gems'&&!/^(gems|gem-select|gem-preview|gem-synthesis|gem-exchange|gem-targets|gem-transfer-preview|gem-recycle-preview|gem-pending|gem-sources):/.test(menu))return false;
 const parts=menu.split(':'),requested=parts[1],id=EQUIPMENT[requested]&&game.state.inventory[requested]>0?requested:game.state.equipment.weapon;
 const item=EQUIPMENT[id],v=itemGemView(game.state,id),back={back:true,label:t('action.back'),action:'gems:'+id};
 const show=(title:string,body:string,rows:MenuRow[],buttons:MenuChoice[]=[back])=>hud.showList(title,body,rows,buttons,0,{placement:'center',dismissOnBackdrop:false});
 if(menu.startsWith('gem-sources:')){
  show(t('sources.title'),t('sources.description'),[
   {label:t('sources.quality'),detail:t('item.qualityRule')+'\n'+t('tier.unlocks'),action:'gem-sources:'+id,disabled:true},
   {label:t('sources.hunting'),detail:t('sources.huntingDetail'),action:'gem-sources:'+id,disabled:true},
   {label:t('sources.journey'),detail:t('sources.journeyDetail'),action:'gem-sources:'+id,disabled:true},
   {label:t('sources.exchange'),detail:t('sources.exchangeDetail'),action:'gem-exchange:'+id},
   {label:t('sources.weights'),detail:t('sources.weightsDetail'),action:'gem-sources:'+id,disabled:true},
  ]);return true;
 }
 if(menu.startsWith('gem-pending:')){
  const pending=pendingGemView(game.state),q=game.gems.claimPending(),rows:MenuRow[]=[];
  if(pending.gold)rows.push({label:t('pending.gold',{count:pending.gold}),detail:'',action:'gem-pending:'+id,disabled:true});
  if(pending.drills)rows.push({label:t('pending.drills',{count:pending.drills}),detail:'',action:'gem-pending:'+id,disabled:true});
  for(const [key,count]of Object.entries(pending.bank)){const [stat,tier]=key.split(':');rows.push({label:t('pending.crystal',{name:statName(stat as GemStat),tier:tierName(Number(tier)),count}),detail:'',action:'gem-pending:'+id,disabled:true});}
  show(t('pending.title'),t('pending.summary',{gold:pending.gold,drills:pending.drills,crystals:pending.totalUnits})+'\n'+t('pending.claimPreview',{gold:q.refundGold,drills:q.returned??q.drills,crystals:q.result})+'\n'+t('pending.description')+(q.allowed?'':'\n'+(pending.available?reason(q):t('pending.empty'))),rows.length?rows:[{label:t('pending.empty'),detail:'',action:'gem-pending:'+id,disabled:true}],[back,{label:t('action.sources'),action:'gem-sources:'+id},{label:t('pending.claim'),action:`gem-claim:${id}:${q.token}`,primary:true,disabled:!q.allowed}]);return true;
 }
 if(menu.startsWith('gem-exchange:')){
  show(t('exchange.title'),t('exchange.description')+'\n'+t('balance',{shards:game.state.gems.shards,drills:game.state.gems.drills}),GEM_STATS.map(stat=>{
   const q=game.gems.exchange(stat);return {label:statName(stat),detail:quoteDetail(q,t('cost.exchange')+' · '+t('balance.tier',{tier:'Ⅰ',count:stock(game,stat,1)})),action:`gem-convert:${id}:${stat}:${q.token}`,disabled:!q.allowed};
  }));return true;
 }
 if(menu.startsWith('gem-synthesis:')){
  const rows:MenuRow[]=[];
  for(let tier=1;tier<v.tierCap;tier++)for(const stat of GEM_STATS){
   const q=game.gems.synthesis(stat,tier);rows.push({label:statName(stat)+' · '+t('tier',{tier:tierName(tier)})+' → '+t('tier',{tier:tierName(tier+1)}),detail:quoteDetail(q,t('cost.synthesis',{from:tierName(tier),to:tierName(tier+1),gold:q.gold})+'\n'+t('balance.tier',{tier:tierName(tier),count:stock(game,stat,tier)})),action:`gem-synthesize:${id}:${stat}:${tier}:${q.token}`,disabled:!q.allowed});
  }
  show(t('synthesis.title'),t('synthesis.description')+'\n'+t('tier.cap',{tier:tierName(v.tierCap)}),rows.length?rows:[{label:t('synthesis.maximum'),detail:t('tier.unlocks'),action:'gem-synthesis:'+id,disabled:true}]);return true;
 }
 if(menu.startsWith('gem-targets:')){
  const ids=Object.keys(game.state.inventory).filter(key=>key!==id&&game.state.inventory[key]>0&&EQUIPMENT[key]&&forgingSlot(EQUIPMENT[key])===forgingSlot(item));
  const reclaim=game.gems.reclaim(id);
  show(t('transfer.title'),t('transfer.description',{item:item.name}),ids.length?ids.map(to=>{
   const q=game.gems.transfer(id,to);return {label:EQUIPMENT[to].name,detail:quoteDetail(q,t('cost.transfer')),action:`gem-transfer-preview:${id}:${to}`,disabled:!q.allowed,icon:equipmentIcon(EQUIPMENT[to])};
  }):[{label:t('transfer.none'),detail:'',action:'gem-targets:'+id,disabled:true}],[back,{label:t('action.recycle'),action:'gem-recycle-preview:'+id,disabled:!reclaim.allowed}]);return true;
 }
 if(menu.startsWith('gem-recycle-preview:')){
  const q=game.gems.reclaim(id);
  hud.show(t('recycle.title'),t('recycle.description',{item:item.name,drills:q.returned??0,gold:q.refundGold,baseOpened:v.capacity>0?1:0,capacity:v.capacity})+(q.allowed?'':'\n'+reason(q)),[
   {back:true,label:t('action.backSelection'),action:'gem-targets:'+id},
   {label:t('action.recycle'),action:`gem-recycle:${id}:${q.token}`,primary:true,disabled:!q.allowed},
  ],false,{placement:'center',dismissOnBackdrop:false});return true;
 }
 if(menu.startsWith('gem-transfer-preview:')){
  const to=parts[2],q=game.gems.transfer(id,to),target=itemGemView(game.state,to);
  hud.show(t('transfer.preview'),t('transfer.summary',{from:item.name,to:EQUIPMENT[to]?.name??'',opened:v.opened,capacity:v.capacity,description:t('cost.transfer')})+'\n'+t('transfer.effects',{before:v.opened,beforeCapacity:v.capacity,after:q.target?.opened??target.opened,afterCapacity:target.capacity,drills:q.returned??0,gold:q.refundGold})+'\n'+t('transfer.returned')+(q.allowed?'':'\n'+reason(q)),[
   {back:true,label:t('action.backSelection'),action:'gem-targets:'+id},
   {label:t('action.confirmTransfer'),action:`gem-transfer:${id}:${to}:${q.token}`,primary:true,disabled:!q.allowed},
  ],false,{placement:'center',dismissOnBackdrop:false});return true;
 }
 if(menu.startsWith('gem-preview:')){
  const hole=Number(parts[2]),stat=parts[3] as GemStat,tier=Number(parts[4]),q=game.gems.inset(id,hole,stat,tier),previous=v.sockets[hole];
  if(!Number.isInteger(hole)||hole<0||hole>=v.capacity)return renderGemPanel(hud,game,'gems:'+id);
  hud.show(t('preview.title'),t('preview.description',{item:item.name,number:hole+1,stat:statName(stat),tier:tierName(tier),effect:gemValueText(stat,tier,v.units)})+'\n'+t('cost.inset',{units:q.units,tier:tierName(tier),gold:q.gold})+'\n'+t('preview.owned',{stock:q.stock,units:q.units})+'\n'+t(previous?'preview.replace':'preview.first')+(q.allowed?'':'\n'+reason(q)),[
   {back:true,label:t('action.backSelection'),action:`gem-select:${id}:${hole}`},
   {label:t(previous?'action.replace':'action.inset'),action:`gem-socket:${id}:${hole}:${stat}:${tier}:${q.token}`,disabled:!q.allowed,primary:true},
  ],false,{placement:'center',dismissOnBackdrop:false});return true;
 }
 if(menu.startsWith('gem-select:')){
  const hole=Number(parts[2]);
  if(!Number.isInteger(hole)||hole<0||hole>=v.capacity)return renderGemPanel(hud,game,'gems:'+id);
  const current=v.sockets[hole],open=hole<v.opened;
  if(!open){
   const q=game.gems.open(id,hole);show(t('slot.open',{number:hole+1}),item.name+'\n'+t('cost.open',{drills:q.drills,gold:q.gold})+(q.allowed?'':'\n'+reason(q)),[
    {label:t('action.open'),detail:t('cost.open',{drills:q.drills,gold:q.gold}),action:`gem-open:${id}:${hole}:${q.token}`,disabled:!q.allowed,primary:true},
    {label:t('action.sources'),detail:t('sources.description'),action:'gem-sources:'+id},
   ]);return true;
  }
  const rows:MenuRow[]=[];
  if(current){const q=game.gems.remove(id,hole);rows.push({label:t('action.remove'),detail:quoteDetail(q,t('cost.free')),action:`gem-remove:${id}:${hole}:${q.token}`,disabled:!q.allowed});}
  for(let tier=1;tier<=v.tierCap;tier++)for(const stat of GEM_STATS){const q=game.gems.inset(id,hole,stat,tier);rows.push({label:statName(stat)+' · '+t('tier',{tier:tierName(tier)}),detail:quoteDetail(q,gemValueText(stat,tier,v.units)+' · '+t('cost.inset',{units:q.units,tier:tierName(tier),gold:q.gold})+'\n'+t('balance.tier',{tier:tierName(tier),count:q.stock})),action:`gem-preview:${id}:${hole}:${stat}:${tier}`,disabled:!q.allowed});}
  show(t('slot.select',{number:hole+1}),item.name+'\n'+(current?t('slot.current',{name:statName(current.stat),tier:tierName(current.tier)}):t('slot.none'))+' · '+t('slot.units',{units:v.units}),rows,[back,{label:t('action.exchange'),action:'gem-exchange:'+id},{label:t('action.synthesis'),action:'gem-synthesis:'+id}]);return true;
 }
 renderSockets(hud,game,id);return true;
}

function drawGem(ui:RpgPanel,parent:Node,tier:number){
 const u=ui.scale,g=parent.addComponent(CompactGraphics),r=17*u;
 // Gem levels use numerals, not equipment-quality colors.
 g.fillColor=F.color('state.ready',180);g.strokeColor=F.color('state.ready');g.lineWidth=1.3*u;
 g.moveTo(0,r);g.lineTo(r*.75,0);g.lineTo(0,-r);g.lineTo(-r*.75,0);g.close();g.fill();g.stroke();
 g.moveTo(-r*.75,0);g.lineTo(r*.75,0);g.moveTo(0,r);g.lineTo(r*.3,0);g.lineTo(0,-r);g.stroke();
}
function renderSockets(hud:Hud,game:GameSession,id:string){
 const s=game.state,item=EQUIPMENT[id],v=itemGemView(s,id),ui=new RpgPanel(hud,game,'forge','GemWorkshop',true),u=ui.scale,a=ui.contentTop+ui.hit/u+ui.gap/u,b=ui.contentBottom,h=b-a;
 const left=ui.surface(ui.panel,ui.x(116),ui.y((a+b)/2),216*u,h*u,C.background),right=ui.surface(ui.panel,ui.x(536),ui.y((a+b)/2),596*u,h*u,C.background);left.name='GemEquipmentList';right.name='GemSocketWorkspace';
 const worn=new Set(Object.values(s.equipment)),ids=Object.keys(s.inventory).filter(key=>s.inventory[key]>0&&EQUIPMENT[key]&&EQUIPMENT[key].kind!=='spell').sort((x,y)=>Number(!worn.has(x))-Number(!worn.has(y))||x.localeCompare(y));
 const row=ui.hit+ui.gap,list=ui.scroll(left,0,0,204*u,h*u,ids.length*row);
 ids.forEach((key,i)=>{
  const d=EQUIPMENT[key],gv=itemGemView(s,key),n=ui.button(list,'',0,-ui.hit/2-i*row,196*u,'gems:'+key,true,false,ui.hit,undefined,'catalog');Controls.rowBackground(ui,n,196,ui.hit/u-3,key===id);
  const icon=hud.node('GemEquipmentIcon',n,-73*u,0,34*u,34*u),frame=equipmentIconFrame(icon,34*u,34*u,{quality:d.quality,scale:u});
  const kind=['sword','bow','staff'].includes(d.kind)?d.kind:d.kind==='ring'?'ring':d.slot;
  UiSkin.asset(frame.content,kind==='offhand'?D.artwork.offhand:preparationSkinAsset('item-'+kind),31*u,31*u,false);
  const name=ui.text(n,d.name,25*u,10*u,135*u,22*u,F.color(qualityFeedbackRole(d.quality)),13*u);name.enableWrapText=false;name.overflow=Label.Overflow.SHRINK;
  ui.text(n,t('item.sockets',{count:gv.sockets.slice(0,gv.capacity).filter(Boolean).length,capacity:gv.capacity}),25*u,-13*u,135*u,20*u,C.muted,11.5*u);
 });
 const title=ui.text(ui.panel,item.name,ui.x(536),ui.y(a+17),560*u,28*u,C.ink,19*u);title.enableWrapText=false;title.overflow=Label.Overflow.SHRINK;
 const tileW=Math.max(ui.hit,90*u),gap=Math.max(ui.gap,12*u),total=tileW*v.capacity+gap*Math.max(0,v.capacity-1),start=ui.x(536)-total/2+tileW/2,cardH=Math.max(ui.hit,88*u),cardY=ui.y(a+42+cardH/u/2);
 for(let hole=0;hole<v.capacity;hole++){
  const gem=v.sockets[hole],open=hole<v.opened,n=ui.button(ui.panel,'',start+hole*(tileW+gap),cardY,tileW,`gem-select:${id}:${hole}`,true,false,cardH,undefined,'catalog');Controls.cardBackground(ui,n,tileW/u,cardH/u,!!gem);
  const number=ui.text(n,t('slot.number',{number:hole+1}),0,cardH/2-13*u,tileW-8*u,20*u,C.muted,11.5*u);number.horizontalAlign=Label.HorizontalAlign.CENTER;
  if(gem){const shape=hud.node('GemCrystal',n,0,6*u,38*u,38*u);drawGem(ui,shape,gem.tier);}
  else{const empty=ui.text(n,open?'◇':'○',0,6*u,tileW-8*u,38*u,open?C.gold:F.color('text.disabled'),31*u);empty.horizontalAlign=Label.HorizontalAlign.CENTER;}
  const status=ui.text(n,gem?statName(gem.stat)+' '+t('tier',{tier:tierName(gem.tier)}):t(open?'slot.empty':'slot.closed'),0,-cardH/2+15*u,tileW-8*u,25*u,gem?C.ink:open?C.gold:F.color('text.disabled'),11.5*u);status.horizontalAlign=Label.HorizontalAlign.CENTER;
 }
 if(v.capacity===0){
  const unavailable=ui.text(ui.panel,t('item.noSockets'),ui.x(536),ui.y(a+82),530*u,64*u,C.muted,17*u);unavailable.horizontalAlign=Label.HorizontalAlign.CENTER;
  const qualityRule=ui.text(ui.panel,t('item.qualityRule'),ui.x(536),ui.y(a+137),548*u,40*u,C.gold,12*u);qualityRule.horizontalAlign=Label.HorizontalAlign.CENTER;
 }
 const summaryY=a+42+cardH/u+20;
 if(v.capacity>0&&summaryY+14<b){const summary=ui.text(ui.panel,t('item.capacity',{quality:item.quality,capacity:v.capacity})+' · '+t('tier.cap',{tier:tierName(v.tierCap)}),ui.x(536),ui.y(summaryY),558*u,24*u,C.muted,12*u);summary.horizontalAlign=Label.HorizontalAlign.CENTER;}
 if(v.duplicate&&summaryY+39<b){const note=ui.text(ui.panel,t('item.shared'),ui.x(536),ui.y(summaryY+24),558*u,26*u,C.gold,11.5*u);note.horizontalAlign=Label.HorizontalAlign.CENTER;}
 const pending=pendingGemView(s);
 ui.footer(t('balance',{shards:s.gems.shards,drills:s.gems.drills}),[
  {back:true,label:t((returnMenus.get(game)??'inventory').startsWith('forge')?'action.backForge':'action.backEquipment'),action:returnMenus.get(game)??'inventory'},
  {label:t(pending.available?'action.pending':'action.sources'),action:(pending.available?'gem-pending:':'gem-sources:')+id},
  {label:t('action.synthesis'),action:'gem-synthesis:'+id},
  v.capacity>0?{label:t('action.transfer'),action:'gem-targets:'+id}:{label:t('action.exchange'),action:'gem-exchange:'+id},
 ]);workshopHeader(ui,id,'gems');
}
