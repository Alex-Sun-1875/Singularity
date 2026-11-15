import {trainingText} from '../features/debug/locales';
import {BUILD_INFO} from './BuildInfo';
import {currentLocale} from '../shared/i18n/Localization';
import {cinematicText as ct} from '../features/cinematics/locales';
import type {GameSession} from '../core/GameSession';
import {EQUIPMENT,MERCHANTS,RECIPES,canonicalMerchant,type EquipmentSlot} from '../features/equipment/data/Equipment';
import {getArea} from '../features/world/data/WorldData';
import {Hud} from './Hud';
import {ACTION_NAMES} from '../features/progression/common/SkillChecks';
import {equipmentOutcome,bonusText} from '../features/equipment/common/EquipmentDice';
import {SKILL_CHECKS} from '../features/progression/data/SkillChecks';
import {COMBAT_RULES} from '../features/combat/data/PureSkills';
import {renderCharacterPanel} from '../features/equipment/runtime/CharacterPanel';
import {renderCombatPanel,discardCombatSkillPreview} from '../features/progression/runtime/CombatPanel';
import {renderJourney} from '../features/journey/runtime/JourneyPanel';
import {renderForging} from '../features/crafting/runtime/ForgingPanel';
import {renderEquipmentPanel,renderCharacterStats,discardAttributePreview} from '../features/equipment/runtime/EquipmentPanels';
import {CAMPAIGN_SCENES,campaignScene} from '../features/cinematics/data/CampaignScenes';
import {HUNTING_GROUNDS} from '../features/world/data/MonsterEcology';
import {sys} from 'cc';
import type {MenuRow} from '../shared/ui/MenuPanel';
import {UI_SETTINGS_REFERENCE} from '../shared/ui/UiChrome';
import {showJourneyStart} from '../features/journey/runtime/JourneyStartScreen';
import {renderProfessionPanel,renderAllocationPanel,discardPreparationPreview} from '../features/progression/runtime/PreparationPanels';
import {automationText as autoText} from '../features/automation/locales';
import {worldText} from '../features/world/locales';
export function renderMenu(hud:Hud,game:GameSession,menu:string,loading:boolean,failure:string,page:number,merchantId:string,visited:Record<string,boolean>,saved:string,updateReady=false,guestTest=false,musicLabel='背景音乐：开',skillEffectDebug=false){
 const s=game.state,d=s.dialogue;
 if(menu!=='checks')discardCombatSkillPreview(game);
 if(menu!=='attributes')discardAttributePreview(game);
 if(!menu.startsWith('allocation:'))discardPreparationPreview(game);
 if(d){hud.show(d.speaker,d.text,d.options.map(o=>({label:o.label,action:'choice:'+o.id})));return;}
 if(s.status==='dead'){hud.show('旅途尚未结束','返回最近检查点。已击败的敌人、证据与战利品仍然保留。',[{label:'返回检查点',action:'retry'}]);return;}
 if(!menu){hud.clearModal();return;}
 if(menu==='dev-tools'&&game.developmentTools.enabled){
  const v=game.developmentTools.view();
  hud.showList('DEV 快速验证',`Lv${v.level} · 生命 ${Math.ceil(v.hp)}/${v.maxHp} · 职业资源 ${Math.floor(v.resource)}/${v.maxResource}\n金币 ${v.gold} · 铁 ${v.iron} · 符文 ${v.runes} · 核心 ${v.cores}\n${v.feedback||'手动操作，仅修改当前独立 dev 旅程。'}`,[
   {label:'补满生命与职业资源',detail:'保留敌人、伤害与技能消耗规则',action:'dev:refill'},
   {label:'补齐药水',detail:'四类药水补至正常携带上限',action:'dev:supplies'},
   {label:'补充金币与锻造材料',detail:'金币、铁、符文、核心各 9999',action:'dev:materials'},
   {label:'等级＋5',detail:'保留剧情、任务和已持有装备',action:'dev:level5',disabled:v.level>=40},
   {label:'升至40级',detail:'按正常成长获得技能与属性点',action:'dev:level40',disabled:v.level>=40},
   {label:'清除 Boss 再战等待',detail:'从旅程页重新挑战，仍需真实击杀',action:'dev:boss-ready',disabled:!v.bossWaits},
   {label:'技能训练场',detail:'技能1—5级、靶阵、群怪与伤害统计',action:'training:enter'},
  ],[{label:'返回暂停',action:'pause'},{label:'继续旅途',action:'close'}],hud.touchTargetSize,{placement:'right',width:sys.isMobile?620:560});return;
 }
 if(menu.startsWith('interaction:')){
  const object=getArea(s.area).objects.find(o=>o.id===menu.slice(12)&&game.interactionVisible(o));
  if(!object){hud.show(autoText('interaction.unavailable'),autoText('task.failed'),[{label:autoText('interaction.cancel'),action:'close'}]);return;}
  const merchant=object.action==='merchant'?MERCHANTS[canonicalMerchant(object.merchant??object.actor??'')]:undefined;
  const title=merchant?.name??(object.actor?object.label.split(/[：:]/)[0]:object.label);
  const body=merchant?worldText('talk.merchant'):object.actor==='kael'?worldText('talk.kael'):`${object.description}\n\n${worldText(object.action==='journey_task'?'talk.task':'talk.proceed')}`;
  const choice=merchant?worldText('talk.shop'):object.action==='journey_task'?autoText('interaction.investigate'):object.actor==='kael'?worldText('talk.route'):worldText('talk.ready');
  hud.show(title,body,[{label:choice,action:'interaction-confirm:'+object.id},{label:worldText(merchant?'talk.noThanks':'talk.later'),action:'close'}]);return;
 }
 if(menu==='hunting'){
  const high=s.progression.level>=11,ids=high?['H03','H04','H07','H17','S02','S08']:['S02','S03','S04','S08','S17'];
  hud.showList('出发狩猎','旅店与石桥镇是安全区。第一猎区：出旅店 → 石桥镇东侧通道 → 南渡码头。抵达后，兽群就在落点西北侧。\n普通怪28秒、群首50秒补充；离开刷新点20米后刷新。任务与刷怪都能升级、获得武器。',ids.map(id=>({label:`${getArea(id).name} · Lv${HUNTING_GROUNDS[id].level}`,detail:`${id} · ${HUNTING_GROUNDS[id].packs.flat().length}只游荡怪${id==='H17'?' · 可选巨兽首领':''} · 点击查看路线`,action:'journey-map:'+id})),[{label:'八章旅程',action:'journey'},{label:'战役见闻',action:'campaign-log'},{back:true,label:'返回旅途',action:'close'}]);return;
 }
 if(menu==='campaign-log'){const scenes=CAMPAIGN_SCENES.filter(d=>s.receipts[`campaign:seen:${d.id}`]);hud.showList(ct('ui.logTitle'),ct('ui.logDescription'),scenes.map(d=>({label:ct(d.title),detail:ct('ui.chapter',{chapter:d.chapter,area:getArea(d.area).name}),action:'campaign-log:'+d.id})),[{label:ct('ui.journey'),action:'journey'},{label:ct('ui.return'),action:'close'}]);return;}
 if(menu.startsWith('campaign-log:')){const d=campaignScene(menu.slice(13));if(d&&s.receipts[`campaign:seen:${d.id}`])hud.show(ct(d.title),d.beats.map(b=>`${ct(b.speaker)}: ${ct(b.text)}`).join('\n\n'),[{back:true,label:ct('ui.logIndex'),action:'campaign-log'},{label:ct('ui.return'),action:'close'}]);return;}
 if(menu==='journey-finish'){hud.show('前两章战役完成','兽潮之夜与群山战火的共同关底均已击败。\n\n八章旅程目前开放第一、第二章；可以继续战役任务、狩猎、Boss再战与收集装备。后续章节的军团与永夜君主尚未开放。',[{label:'查看章节与战利品',action:'journey'},{label:'继续探索',action:'close'}]);return;}
 if(menu.startsWith('journey')){renderJourney(hud,game,menu);return;}
 if(menu==='title'){showJourneyStart(hud,loading,failure,guestTest);return;}
 if(menu==='confirm-new'){hud.show('开始新的旅程','当前旅途会先完整备份，再创建独立的新进度。',[{label:'确认新建旅程',action:'confirm-new'},{back:true,label:'返回',action:'cancel-new'}],false,{dismissOnBackdrop:false});return;}
 if(menu==='map'){hud.atlas(game,visited);return;}
 if(menu==='navigation'){
  const area=getArea(s.area),p=s.player,metres=(q:{x:number;z:number})=>Math.ceil(Math.hypot(p.x-q.x,p.z-q.z));
  const rows=[...area.objects.filter(o=>game.interactionVisible(o)&&(o.action!=='journey_task'||game.journey.currentTask()?.id===o.eventId&&game.journey.currentTask()?.goal==='observe')).map(o=>({label:o.label,detail:`${metres(o)}米 · 抵达后自动打开交互`,action:'auto:object:'+o.id})),...area.exits.map(e=>({label:e.label,detail:game.exitRequirement(e)??`${metres(e)}米 · 自动步行并通过出口`,action:'auto:exit:'+e.id,disabled:!!game.exitRequirement(e)}))];
  hud.showList('前往场景目标','移动可随时接管，抵达目标后自动打开交互。',rows,[{label:'打开地图',action:'map'},{back:true,label:'返回旅途',action:'close'}],hud.touchTargetSize,{placement:'left',width:sys.isMobile?620:500,quiet:true});return;
 }
 if(menu==='checks'){renderCombatPanel(hud,game,'skills');return;}
 if(menu==='attributes'){renderCharacterStats(hud,game);return;}
 if(menu==='profession'){renderProfessionPanel(hud,game);return;}
 if(menu==='allocation:attributes'||menu==='allocation:skills'){renderAllocationPanel(hud,game,menu==='allocation:skills'?'skills':'attributes');return;}
 if(menu==='appearance'){renderCharacterPanel(hud,game,'inventory');return;}
 if(menu==='exploration-skills'){renderCharacterPanel(hud,game,'skills');return;}
 if(menu==='equipment-catalog'){renderCharacterPanel(hud,game,'catalog');return;}
 if(menu==='check-history'){
  const entries=Object.entries(s.dice.records),gears=Object.entries(s.dice.gear??{});if(!entries.length&&!gears.length){hud.show('机遇记录','获得装备后可以免费摇骰追加铸印。行囊中选择装备，点击摇骰锻印；每件一次，原装备保底。也可以核对信件，或拆解铜簧匣。',[{label:'探索手段',action:'exploration-skills'},{back:true,label:'返回旅途',action:'close'}]);return;}
  const rows=entries.map(([id,r])=>{const d=SKILL_CHECKS[id],roll=r.rolls[r.rolls.length-1];return {label:`${roll.success?'达成':'转机'} · ${d.title}`,detail:`掷骰 ${roll.faces.join(' / ')} → ${roll.kept} +准备${roll.bonus}${roll.assist?' +线索'+roll.assist:''} = ${roll.total} / 目标${d.dc}${r.committed?' · 已记录':' · 待确认'}`,action:'check-log:'+id};});
  rows.push(...gears.map(([id,r])=>{const outcome=equipmentOutcome(s.seed,r);return {label:`${outcome?.name??'未掷骰'} · ${EQUIPMENT[id].name}`,detail:`${outcome?bonusText(outcome.bonus)||'保留原装':'免费机遇尚未使用'} · ${r.claimed?'已结算':'待结算'}`,action:'check-log:gear:'+id};}));
  hud.showList('机遇记录',`余烬 ${s.dice.inspiration}/4 · 装备免费锻印一次，原装备保底。`,rows,[{label:'探索手段',action:'exploration-skills'},{back:true,label:'返回旅途',action:'close'}]);return;
 }
 if(menu.startsWith('check-log:gear:')){const id=menu.slice(15),r=s.dice.gear?.[id];if(r){const o=equipmentOutcome(s.seed,r);hud.show(EQUIPMENT[id].name,`${o?.name??'未使用锻造骰'}\n${o?bonusText(o.bonus)||o.description:'每件装备可以免费掷骰一次。'}${o?.upgrade?'\n额外发现：'+EQUIPMENT[o.upgrade].name:''}\n\n${r.claimed?'铸印已封存，穿戴该装备时生效。':'在行囊中选择这件装备可继续结算。'}`,[{back:true,label:'返回记录',action:'check-history'},{label:'行囊',action:'inventory'}]);return;}}
 if(menu.startsWith('check-log:')){const id=menu.slice(10),r=s.dice.records[id],d=SKILL_CHECKS[id];if(r&&d){const roll=r.rolls[r.rolls.length-1];hud.show(d.title,`${ACTION_NAMES[d.skill]} · 目标 ${d.dc}\n${r.context.mode==='advantage'?'线索充分：两骰择高':r.context.mode==='disadvantage'?'局势不利：两骰取低':'行动掷骰'}\n\n${r.rolls.map(v=>`第${v.attempt}次：${v.faces.join(' / ')} → ${v.kept} +${v.bonus}${v.assist?' +'+v.assist:''} = ${v.total} · ${v.success?'成功':'失败'}`).join('\n')}\n\n${roll.success?d.successText:d.failureText}`,[{back:true,label:'返回记录',action:'check-history'},{back:true,label:'返回旅途',action:'close'}]);return;}}
 if(menu==='inventory'||menu==='equipment'){renderEquipmentPanel(hud,game);return;}
 if(renderForging(hud,game,menu))return;
 if(menu==='shop'){const merchant=MERCHANTS[merchantId];if(!merchant){hud.clearModal();return;}hud.showList(`${merchant.name}的货物`,`金币 ${s.player.gold} · 本趟余货；休整不会补货。`,Object.keys(merchant.stock).map(id=>({label:`${EQUIPMENT[id].name} ${merchant.prices[id]}币`,detail:`余${s.merchantStock[merchantId][id]} · ${EQUIPMENT[id].description}`,action:'buy:'+id,disabled:!s.merchantStock[merchantId][id]||!!s.inventory[id]||s.player.gold<merchant.prices[id]})),[...(merchantId==='lorn'?[{label:'锻造与强化',action:'forge'}]:[]),{label:'结束交易',action:'close'}],hud.touchTargetSize);return;}
 if(menu==='help'){hud.show('旅途手册','WASD / 左摇杆移动，Shift慢行，鼠标瞄准，J / 鼠标左键基础攻击；弓按住蓄力、松手放箭。\nQ/E/R/T（或1—4）使用四个普通技能，G使用终极，空格独立闪避。技能默认自动瞄准射程内无遮挡的最近怪物，轻点释放；按住时实时跟随，目标失效后重新索敌。鼠标／触摸板按住或触屏原地长按技能、终极、闪避按钮3.6秒可查看说明，松开关闭且不施放。触屏拖动改为本次手动瞄准，键盘按住技能键后移动鼠标也可手动选点，松开释放。设置→操作可切换默认自动/手动瞄准。移入取消区放弃。Esc或鼠标右键也可取消瞄准。技能超距或被墙阻挡不会自动跑近。\n主要输出无冷却；战术、防守和闪避按各自冷却恢复；终极消耗45点当前职业资源，有短暂释放间隔。普攻与闪避不耗资源；技能消耗体力／专注／法力并自动恢复。命中值与目标闪避值决定接触后的命中率，范围60%—100%；弓术专注上限提高命中，当前专注多少不影响命中。敏捷同时提升闪避。实体箭仍须碰到目标，落空与被闪避均显示MISS；主动闪避仍按动作时机避开攻击。5使用生命药水，6使用对应职业药水，共享5秒冷却。C打开战斗技能，V打开成长属性，B行囊，M地图，F交互。火墙与陷阱用于延缓追击，护盾和机动技能用于应对危险。\n脱战后可随时更换装备。安全检查点可以配置技能、锻造与重配属性。怪物倒地后尸体保留约30秒，掉落装备会留在地面。靠近后点击拾取（键盘F）；顶部自动任务会连续寻路、战斗，抵达调查目标后弹出交互，确认后继续推进；挂机只在当前场景刷怪。左侧寻路抵达人物或物件后也会自动打开交互。仅挂机刷怪经验受每日递减与5000上限限制，在挂机顶栏查看；自动任务与手动战斗不占用挂机额度。自动任务与挂机会自动寻路拾取，未拾取装备随存档保留。拾取装备后可免费摇骰追加铸印，可能增加生命、护甲或伤害，也可能额外获得高品质装备。行囊中选择装备，点击摇骰锻印；每件一次，原装备保底。探索行动中Enter/空格掷骰，R消耗余烬重掷，G采用线索。',[{label:'战斗技能',action:'checks'},{back:true,label:'返回旅途',action:'close'}]);return;}
 if(menu==='settings'){
  const musicState=musicLabel.replace(/^背景音乐[：:]\s*/,''),musicFailed=musicState!=='开'&&musicState!=='关',tab=hud.settingsTab;
  const names:MenuRow={label:'技能名称',detail:'',skin:'menu-skillnames-v5',action:'toggle-skill-names',value:hud.skillNamesVisible?'开':'关',selected:hud.skillNamesVisible,toggle:true};
  const rows:MenuRow[]=tab==='audio'?[
   {label:'背景音乐',detail:musicFailed?musicState:'',skin:'menu-music-v5',action:'toggle-music',value:musicFailed?'重试':musicState,selected:musicState==='开',toggle:!musicFailed},
   {label:'减少动态',detail:'',skin:'menu-motion-v5',action:'toggle-impact-motion',value:hud.reducedMotion?'开':'关',selected:hud.reducedMotion,toggle:true},names,
  ]:tab==='controls'?[
   {label:'技能瞄准',detail:hud.skillAimMode==='auto'?'轻点锁敌 · 拖动手动':'拖动选点 · 松开释放',action:'toggle-skill-aim',value:hud.skillAimMode==='auto'?'自动':'手动',selected:hud.skillAimMode==='auto'},
   names,{label:'操作说明',detail:'移动、瞄准与取消',action:'help'},{label:'技能配置',detail:'主动槽位与流派',action:'checks'},
  ]:[
   {label:'当前旅程',detail:getArea(s.area).name,action:'journey'},
   {label:ct('ui.language'),detail:'',action:'toggle-story-locale',value:currentLocale()==='en'?'EN':'中文'},
   {label:'暂停与旅途',detail:`${saved} · v${BUILD_INFO.version}`,action:'pause'},
   ...(game.developmentTools.enabled?[{label:'DEV 快速验证',detail:'补给、成长与 Boss 再战',action:'dev-tools'}]:[]),
   {label:trainingText('title'),detail:trainingText('entryDetail'),action:'training:enter'},
   ...(skillEffectDebug?[{label:'技能效果调试',detail:'1—5级技能预览',action:'skill-effect-debug'}]:[]),
  ];
  hud.showList('设置','',rows,[{label:'操作帮助',action:'help'},{label:'检查点补给',action:'rest'},{back:true,label:'返回旅途',action:'close'}],hud.touchTargetSize,{
   placement:'right',width:sys.isMobile?UI_SETTINGS_REFERENCE.mobileWidth*hud.touchTargetSize/48:400,rightInset:sys.isMobile?144*hud.touchTargetSize/48:120,keepCenterClear:true,centeredTitle:true,quiet:false,crest:true,variant:'settings',
   tabs:[{label:'音画',action:'settings-tab:audio',selected:tab==='audio'},{label:'操作',action:'settings-tab:controls',selected:tab==='controls'},{label:'旅途',action:'settings-tab:journey',selected:tab==='journey'}],
  });return;
 }
 if(menu==='complete'){hud.show('破晓之战 · 终局','黑冠之战已结束，你在终局留下的选择与同伴的去向已记录。\n\n可以继续回访各地，寻找尚未发现的隐匣，完成支线并收集装备。',[{label:'继续探索',action:'close'},{label:'旅途地图',action:'map'}]);return;}
 hud.showList('旅途暂停',`${getArea(s.area).name}\n${saved} · v${BUILD_INFO.version}${guestTest?'\n游客测试 · 仅本机存档，无云端同步':''}`,[
  ...(updateReady?[{label:'安装已下载更新',detail:'',action:'update:show'}]:[]),
  {label:'旅程',detail:game.objective(),action:'journey'},
  {label:'检查点休整',detail:'',action:'rest'},
  {label:'游戏设置',detail:'音乐、动态与技能名称',action:'settings'},
  ...(game.developmentTools.enabled?[{label:'DEV 快速验证',detail:'补给、成长与 Boss 再战',action:'dev-tools'}]:[]),
  {label:'操作与帮助',detail:'',action:'help'},
  {label:trainingText('title'),detail:trainingText('entryDetail'),action:'training:enter'},
   ...(skillEffectDebug?[{label:'技能效果调试',detail:'1—5级技能预览',action:'skill-effect-debug'}]:[]),
  {label:'主菜单',detail:'保留当前旅程',action:'title'},
  {label:'新建旅程',detail:'先备份当前进度',action:'new'},
 ],[{label:'继续旅途',action:'close'}],hud.touchTargetSize,{placement:'right',width:sys.isMobile?620:500});
}
