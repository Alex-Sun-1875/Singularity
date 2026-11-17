import {gemArtworkPath} from '../../gems/runtime/GemArtwork';
import type {RedemptionReward} from '../data/RedemptionCampaigns';
import {SUPPLIES} from '../../equipment/data/Supplies';
import {BlockInputEvents,Color,EditBox,Label,Node,sys,UITransform} from 'cc';
import type {Hud} from '../../../app/Hud';
import type {GameSession} from '../../../core/GameSession';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {GoldPanelShell} from '../../../shared/ui/GoldPanelShell';
import {GoldMenuButton} from '../../../shared/ui/GoldMenuButton';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {UI_FRAME_LAYOUT as L,UI_GOLD_PANEL_CONTENT as CONTENT} from '../../../shared/ui/UiChrome';
import {applyRpgFont} from '../../../shared/ui/RpgFont';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import type {MenuRow,MenuChoice} from '../../../shared/ui/MenuPanel';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import {GROWING_EQUIPMENT,growingStats} from '../../equipment/data/GrowingEquipment';
import {equipmentIcon} from '../../equipment/runtime/EquipmentPresentation';
import {weaponPowerBonusPercent} from '../../equipment/data/WeaponPower';
import {GEM_STATS,GEM_TIER_NAMES,GEM_TIER_LEVELS,gemValueText,gemName,gemLevelName,type GemStat} from '../../gems/data/Gems';
import {redemptionUiText as t} from '../locales/RedemptionUiText';
import {redemptionCampaignById} from '../data/RedemptionCampaigns';

export interface RedemptionViewState {
 code:string;selection:{weapon?:string;gems:GemStat[]};feedback:string;
 savePending:boolean;saveFailure:string;lastGrantId:string;
}
export interface RedemptionUiAction {
 menu?:string;claim?:{code:string;selection:RedemptionViewState['selection'];token:string};saveOnly?:boolean;collectPending?:string;
}
export const createRedemptionViewState=():RedemptionViewState=>({code:'',selection:{gems:[]},feedback:'',savePending:false,saveFailure:'',lastGrantId:''});
export const redemptionSavedFeedback=()=>t('save.success');
const inputs=new WeakMap<Hud,{edit:EditBox;focused:boolean;lastBlur:number}>();
/** The app checks this before global Enter/Esc/movement shortcuts. */
export function isRedemptionInputFocused(hud:Hud):boolean {
 const input=inputs.get(hud);return !!input&&(input.focused||input.edit.isValid&&input.edit.isFocused()||Date.now()-input.lastBlur<100);
}
/** Backgrounding and leaving the page dismiss the native keyboard without losing the code. */
export function suspendRedemptionInput(hud:Hud):void {
 const input=inputs.get(hud);if(input?.edit.isValid)input.edit.blur();if(input){input.focused=false;input.lastBlur=Date.now();}
}
const rewardLabel=(reward:RedemptionReward)=>{const name=reward.kind==='equipment'?EQUIPMENT[reward.item]?.name??reward.item:reward.kind==='supply'?SUPPLIES[reward.item].name:reward.kind==='stone'?`强化石${GEM_TIER_NAMES[reward.tier]}阶`:({gold:'金币',iron:'铁',runes:'符纹',cores:'锻造芯',drills:'开孔材料'} as const)[reward.kind];return `${name} ×${reward.amount}`;};
const units=(bank:Record<string,number>|undefined)=>Object.values(bank??{}).reduce((sum,n)=>sum+n,0);
const route=(suffix:string)=>'redemption:'+suffix;
const ui=(suffix:string)=>'redemption-ui:'+suffix;
const copySelection=(s:RedemptionViewState['selection'])=>({weapon:s.weapon,gems:[...s.gems]});
const gemRule=()=>t('gem.rule',{tier3:GEM_TIER_LEVELS[3],tier4:GEM_TIER_LEVELS[4],tier5:GEM_TIER_LEVELS[5]});
const nextSelectionMenu=(game:GameSession,v:RedemptionViewState)=>{
 const q=game.redemption.quote(v.code,v.selection);
 if(q.campaign?.weapon&&!q.compensation&&!v.selection.weapon)return route('weapon');
 const missing=q.gemChoices.findIndex((_,i)=>!GEM_STATS.includes(v.selection.gems[i]));
 return missing>=0?route('gem:'+missing):route('confirm');
};

/** Only returns intentions. Inventory changes and durable saves remain app-owned. */
export function handleRedemptionAction(game:GameSession,action:string,v:RedemptionViewState):RedemptionUiAction|undefined {
 if(!action.startsWith('redemption-ui:'))return undefined;
 const parts=action.slice('redemption-ui:'.length).split(':');
 if(v.savePending)return parts[0]==='retry-save'||parts[0]==='save'?{saveOnly:true,menu:route('pending')}:{menu:route('pending')};
 if(parts[0]==='preview'){
  const campaign=game.redemption.lookup(v.code);
  if(!campaign){v.feedback=t(v.code.trim()?'entry.invalid':'entry.empty');return {menu:'redemption'};}
  const q=game.redemption.quote(v.code,v.selection);
  if(q.record){v.feedback=t('entry.claimed');return {menu:route('record:'+q.record.grantId)};}
  if(!campaign.weapon||q.compensation)v.selection.weapon=undefined;
  v.feedback='';return {menu:nextSelectionMenu(game,v)};
 }
 if(parts[0]==='weapon'){
  const q=game.redemption.quote(v.code,v.selection),option=q.weaponOptions.find(o=>o.id===parts[1]);
  if(!option?.available){v.feedback=option?.reason??q.reason;return {menu:route('weapon')};}
  v.selection.weapon=option.id;v.feedback='';return {menu:nextSelectionMenu(game,v)};
 }
 if(parts[0]==='gem'){
  const index=Number(parts[1]),stat=parts[2] as GemStat,q=game.redemption.quote(v.code,v.selection);
  if(Number.isInteger(index)&&index>=0&&index<q.gemChoices.length&&GEM_STATS.includes(stat)){v.selection.gems[index]=stat;v.feedback='';}
  return {menu:nextSelectionMenu(game,v)};
 }
 if(parts[0]==='claim'){
  const q=game.redemption.quote(v.code,v.selection);
  if(!q.allowed){v.feedback=q.reason;return {menu:route('confirm')};}
  // The rendered quote token is passed through; the app/rules reject stale choices.
  return {claim:{code:v.code,selection:copySelection(v.selection),token:parts.slice(1).join(':')},menu:route('pending')};
 }
 if(parts[0]==='collect')return {collectPending:parts.slice(1).join(':'),menu:route('records')};
 if(parts[0]==='back')return {menu:'settings'};
 if(parts[0]==='new'){v.code='';v.selection={gems:[]};v.feedback='';return {menu:'redemption'};}
 return {menu:'redemption'};
}

function entry(hud:Hud,v:RedemptionViewState):void {
 hud.clearModal();const mobile=sys.isMobile,hit=hud.touchTargetSize,u=mobile?hit/L.hit:1,gap=L.gap*u,pad=(L.padding+CONTENT.textInset)*u;
 const safe=sys.getSafeAreaRect(false),left=-hud.width/2+Math.max(12,safe.x),right=-hud.width/2+Math.min(hud.width-12,safe.x+safe.width),bottom=-hud.height/2+Math.max(12,safe.y),top=-hud.height/2+Math.min(hud.height-12,safe.y+safe.height);
 const width=Math.min(mobile?760:600,right-left),font=mobile?26:17,line=font*1.5,bodyTop=GoldPanelShell.measure({width,hit,unit:u,mobile}).bodyTop;
 const message=v.feedback||t('entry.hint'),messageH=line*(v.feedback?2:1.5),height=Math.min(top-bottom,bodyTop+messageH+hit+gap+line*2.6+gap+hit+pad*2);
 const shade=hud.node('RedemptionBackdrop',hud.modal,0,0,hud.width,hud.height),g=shade.addComponent(CompactGraphics);
 g.fillColor=new Color(C.background.r,C.background.g,C.background.b,96);g.rect(-hud.width/2,-hud.height/2,hud.width,hud.height);g.fill();shade.addComponent(BlockInputEvents);
 const panel=hud.node('RedemptionSheet',hud.modal,(left+right)/2,(top+bottom)/2,width,height),shell=panel.addComponent(GoldPanelShell);
 shell.configure({title:t('title'),width,height,hit,unit:u,mobile,viewport:hud,dismissAction:ui('back')},action=>hud.actions.click(action));
 const text=(value:string,y:number,h:number,color=C.ink)=>{const l=hud.text(panel,value,0,y,width-pad*2,font,color,h);applyRpgFont(l);l.lineHeight=line;l.overflow=Label.Overflow.CLAMP;l.enableWrapText=true;return l;};
 const contentTop=height/2-bodyTop;text(message,contentTop-messageH/2,messageH,v.feedback?F.color('state.failure'):C.muted);
 const inputY=contentTop-messageH-gap-hit/2,fieldWidth=width-pad*2,field=hud.node('RedemptionCodeField',panel,0,inputY,fieldWidth,hit),inputWidth=fieldWidth-2*CONTENT.iconGap*u,input=hud.node('RedemptionCodeInput',field,0,0,inputWidth,hit);
 // EditBox owns a background Sprite on its host; keep the field face on a child
 // so two UI renderers never compete for that host's render component.
 const bg=hud.node('RedemptionCodeFieldFace',field,0,0,fieldWidth,hit).addComponent(CompactGraphics);
 bg.node.setSiblingIndex(0);
 bg.fillColor=C.button;bg.roundRect(-fieldWidth/2,-hit/2,fieldWidth,hit,6*u);bg.fill();bg.strokeColor=C.gold;bg.lineWidth=u;bg.roundRect(-fieldWidth/2,-hit/2,fieldWidth,hit,6*u);bg.stroke();
 const edit=input.addComponent(EditBox);edit.inputMode=EditBox.InputMode.SINGLE_LINE;edit.inputFlag=EditBox.InputFlag.DEFAULT;edit.returnType=EditBox.KeyboardReturnType.DONE;edit.maxLength=64;
 field.on(Node.EventType.TOUCH_END,()=>edit.focus());
 edit.textLabel??=hud.text(input,'',0,0,inputWidth-4,font,C.ink,hit);
 edit.placeholderLabel??=hud.text(input,'',0,0,inputWidth-4,font,C.muted,hit);
 for(const label of [edit.textLabel,edit.placeholderLabel]){
  // The engine places EditBox labels at the upper-left corner. Its editor prefab
  // supplies this anchor, whereas dynamically-created Label nodes default to .5/.5.
  const transform=label.node.getComponent(UITransform)!;transform.setAnchorPoint(0,1);transform.setContentSize(inputWidth-4,hit);label.node.setPosition(-inputWidth/2+2,hit/2);
  label.fontSize=font;label.lineHeight=line;label.color=label===edit.textLabel?C.ink:C.muted;label.horizontalAlign=Label.HorizontalAlign.LEFT;label.verticalAlign=Label.VerticalAlign.CENTER;label.enableWrapText=false;label.overflow=Label.Overflow.CLAMP;applyRpgFont(label);
 }
 edit.string=v.code;edit.placeholder=t('entry.placeholder');
 const inputState={edit,focused:false,lastBlur:0};inputs.set(hud,inputState);
 input.on('editing-did-began',()=>{inputState.focused=true;});
 input.on('editing-did-ended',()=>{v.code=edit.string;inputState.focused=false;inputState.lastBlur=Date.now();});
 input.on('text-changed',()=>{if(v.code!==edit.string){v.code=edit.string;v.selection={gems:[]};v.feedback='';}});
 input.on('editing-return',()=>{edit.blur();});
 hud.modalDisposers.add(()=>{v.code=edit.string;if(edit.isValid)edit.blur();inputs.delete(hud);});
 text(t('entry.rule'),inputY-hit/2-gap-line*1.3,line*2.6,C.muted);
 const actionWidth=(fieldWidth-gap)/2,y=-height/2+pad+hit/2;
 [{label:t('entry.preview'),action:ui('preview'),primary:true},{label:t('entry.records'),action:route('records'),primary:false}].forEach((b,i)=>{
  const n=hud.node(b.action,panel,(i-.5)*(actionWidth+gap),y,actionWidth,hit);n.addComponent(GoldMenuButton).configure({label:b.label,width:actionWidth,height:hit,unit:u,fontSize:font,primary:b.primary,wrap:true},()=>{edit.blur();hud.actions.click(b.action);});
 });
}

export function renderRedemptionMenu(hud:Hud,game:GameSession,menu:string,v:RedemptionViewState):boolean {
 if(menu!=='redemption'&&!menu.startsWith('redemption:'))return false;
 const back:MenuChoice={back:true,label:t('action.back'),action:'redemption'},show=(title:string,body:string,rows:MenuRow[],actions:MenuChoice[]=[back])=>hud.showList(title,body,rows,actions,0,{placement:'center',width:sys.isMobile?900:700,dismissOnBackdrop:false});
 const recordRows=(record:Pick<ReturnType<GameSession['redemption']['records']>[number],'weapon'|'gems'|'rewards'>):MenuRow[]=>[
  ...(record.weapon?[{label:t('confirm.weapon',{name:EQUIPMENT[record.weapon]?.name??record.weapon}),detail:EQUIPMENT[record.weapon]?.description??'',action:route('records'),disabled:true}]:[]),
  ...(record.rewards??[]).map(reward=>({label:rewardLabel(reward),detail:'',action:route('records'),disabled:true})),
  ...record.gems.map(g=>({image:gemArtworkPath(g.tier),label:t('confirm.gem',{name:gemName(g.tier),tier:GEM_TIER_NAMES[g.tier],count:g.units/5,units:g.units}),detail:gemValueText(g.stat,g.tier)+'\n'+t('gem.unlock',{level:GEM_TIER_LEVELS[g.tier]}),action:route('records'),disabled:true})),
 ];
 const pending=game.gems.claimPending(),pendingButton:MenuChoice={label:t('records.claimPending'),action:ui('collect:'+pending.token),disabled:!pending.allowed};
 if(v.savePending){
  const record=game.redemption.records().find(r=>r.grantId===v.lastGrantId),body=t('save.hint')+(v.saveFailure?'\n'+t('save.failed',{reason:v.saveFailure}):'');
  show(t('save.title'),body,record?recordRows(record):[],[{label:t('action.retry'),action:ui('retry-save'),primary:true}]);return true;
 }
 if(menu==='redemption'){entry(hud,v);return true;}
 if(menu===route('records')){
  const records=game.redemption.records(),hasPending=records.some(r=>units(r.remaining)>0);show(t('records.title'),t('records.hint')+(v.feedback?'\n'+v.feedback:'')+(hasPending&&!pending.allowed?'\n'+pending.reason:''),records.length?records.map(r=>({label:redemptionCampaignById(r.campaignId)?.name??r.campaignId,detail:units(r.remaining)?t('records.pending',{count:units(r.remaining)}):r.rewards?.length?t('records.bundleReceived',{count:r.rewards.length+r.gems.length+Number(!!r.weapon)}):t('records.received',{count:r.gems.reduce((sum,g)=>sum+g.units,0)}),action:route('record:'+r.grantId)})):[{label:t('records.empty'),detail:'',action:'redemption',disabled:true}],[back,...(hasPending?[pendingButton]:[])]);return true;
 }
 if(menu.startsWith(route('record:'))||menu===route('result')||menu===route('pending')){
  const grantId=menu.startsWith(route('record:'))?menu.slice(route('record:').length):v.lastGrantId,record=game.redemption.records().find(r=>r.grantId===grantId);
  if(!record){show(t('records.title'),t('records.empty'),[]);return true;}
  const count=units(record.remaining),body=(v.feedback?v.feedback+'\n':'')+(count?t('records.pending',{count}):t('records.saved'));
  show(t('records.detail'),body+(count&&!pending.allowed?'\n'+pending.reason:''),recordRows(record),[{back:true,label:t('action.back'),action:route('records')},...(count?[pendingButton]:[]),{label:t('records.new'),action:ui('new')}]);return true;
 }
 const q=game.redemption.quote(v.code,v.selection),campaign=q.campaign;
 if(!campaign){v.feedback=t('entry.invalid');entry(hud,v);return true;}
 if(q.record){show(t('records.detail'),t('entry.claimed'),recordRows(q.record),[{back:true,label:t('action.back'),action:'redemption'},{label:t('entry.records'),action:route('records')}]);return true;}
 if(menu===route('weapon')){
  const current=EQUIPMENT[game.state.equipment.weapon],currentPower=current&&GROWING_EQUIPMENT[current.id]?growingStats(current.id,game.state.progression.level).power:current?.power??0;show(t('weapon.title'),t('weapon.hint')+'\n'+t('weapon.current',{name:current?.name??'',power:currentPower})+(v.feedback?'\n'+v.feedback:''),q.weaponOptions.map(option=>{
   const item=EQUIPMENT[option.id];return {label:option.name+(v.selection.weapon===option.id?' · '+t('weapon.selected'):''),detail:t('weapon.facts',{quality:item.quality,kind:item.weaponFamily??item.kind,level:item.requiredLevel??item.level})+'\n'+weaponDetail(option.id,game.state.progression.level)+(option.reason?'\n'+option.reason:''),icon:equipmentIcon(item),action:ui('weapon:'+option.id),disabled:!option.available};
  }));return true;
 }
 if(menu.startsWith(route('gem:'))){
  const index=Math.max(0,Math.min(q.gemChoices.length-1,Number(menu.slice(route('gem:').length))||0)),tier=q.gemChoices[index];
  if(!tier){show(t('confirm.title'),q.reason,[]);return true;}
  show(t('gem.title',{number:index+1}),`${campaign.name}\n`+t('gem.hint',{total:q.gemChoices.length,tier:gemLevelName(tier)})+'\n'+(q.compensation?t('weapon.compensation')+'\n':'')+gemRule(),GEM_STATS.map(stat=>({image:gemArtworkPath(tier),label:gemName(tier)+(v.selection.gems[index]===stat?' · '+t('weapon.selected'):''),detail:gemValueText(stat,tier),action:ui(`gem:${index}:${stat}`)})),[{back:true,label:t('action.back'),action:campaign.weapon&&!q.compensation?route('weapon'):'redemption'}]);return true;
 }
 const rows:MenuRow[]=(campaign.rewards??[]).map(reward=>({label:rewardLabel(reward),detail:'',action:route('confirm'),disabled:true}));
 if(campaign.weapon&&!q.compensation){const item=EQUIPMENT[v.selection.weapon??''];rows.push({label:item?t('confirm.weapon',{name:item.name}):t('weapon.title'),detail:item?weaponDetail(item.id,game.state.progression.level):t('selection.missing'),action:route('weapon')});}
 q.gemChoices.forEach((tier,i)=>{const stat=v.selection.gems[i];rows.push({image:stat?gemArtworkPath(tier):undefined,label:t('gem.change',{number:i+1,name:stat?gemName(tier):'—',tier:gemLevelName(tier)}),detail:stat?gemValueText(stat,tier)+'\n'+t('gem.unlock',{level:GEM_TIER_LEVELS[tier]}):t('selection.missing'),action:route('gem:'+i)});});
 const body=`${campaign.name}\n${t('confirm.code',{code:campaign.code})}\n${q.compensation?t('weapon.compensation')+'\n':''}${t('confirm.rule')}${q.allowed?'':'\n'+q.reason}${v.feedback?'\n'+v.feedback:''}`;
 show(t('confirm.title'),body,rows,[back,{label:t('action.confirm'),action:ui('claim:'+q.token),primary:true,disabled:!q.allowed}]);return true;
}

function weaponDetail(id:string,level:number):string {
 const item=EQUIPMENT[id];if(!item)return '';
 if(!GROWING_EQUIPMENT[id])return item.description;
 const s=growingStats(id,level),attribute=t(('attribute.'+(item.growthAttribute??'strength')) as 'attribute.strength'|'attribute.dexterity'|'attribute.intellect');
 return t('weapon.stats',{level,power:s.power,percent:weaponPowerBonusPercent(s.power).toFixed(1),attribute,count:s.attribute})+'\n'+item.description;
}
