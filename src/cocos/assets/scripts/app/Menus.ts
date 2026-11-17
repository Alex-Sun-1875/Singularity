import {renderShopPanel,shopGreeting} from '../features/trading/runtime/ShopPanel';
import {tradingText} from '../features/trading/locales/TradingText';
import {CAMPAIGN_MAX_LEVEL} from '../features/progression/data/CampaignProgression';
import {tacticsText} from '../features/combat/locales/TacticsText';
import {trainingText} from '../features/debug/locales';
import {BUILD_INFO} from './BuildInfo';
import {currentLocale} from '../shared/i18n/Localization';
import {cinematicText as ct} from '../features/cinematics/locales';
import type {GameSession} from '../core/GameSession';
import {EQUIPMENT,MERCHANTS,canonicalMerchant,type EquipmentSlot} from '../features/equipment/data/Equipment';
import {getArea,AREAS} from '../features/world/data/WorldData';
import {campaignPrerequisiteTargets} from '../features/campaign/common/CampaignNavigation';
import {Hud} from './Hud';
import {ACTION_NAMES} from '../features/progression/common/SkillChecks';
import {equipmentOutcome,bonusText} from '../features/equipment/common/EquipmentDice';
import {SKILL_CHECKS} from '../features/progression/data/SkillChecks';
import {COMBAT_RULES} from '../features/combat/data/PureSkills';
import {renderCharacterPanel} from '../features/equipment/runtime/CharacterPanel';
import {renderCombatPanel,discardCombatSkillPreview} from '../features/progression/runtime/CombatPanel';
import {renderJourney} from '../features/journey/runtime/JourneyPanel';
import {adventureJournalRoute} from '../features/journey/common/AdventureJournalRoutes';
import {chapterForArea} from '../features/journey/data/ChapterJourney';
import {taskPanelText} from '../features/journey/locales/TaskPanelText';
import {renderForging} from '../features/crafting/runtime/ForgingPanel';
import {renderGemPanel} from '../features/gems/runtime/GemPanel';
import {redemptionText} from '../features/redemption/locales';
import {renderPetPanel} from '../features/pets/runtime/PetPanel';
import {petUiText} from '../features/pets/locales/PetUiText';
import {renderEquipmentPanel,renderCharacterStats,discardAttributePreview} from '../features/equipment/runtime/EquipmentPanels';
import {renderEquipmentDismantling} from '../features/equipment/runtime/EquipmentDismantlingPanel';
import {CAMPAIGN_SCENES,campaignScene} from '../features/cinematics/data/CampaignScenes';
import {HUNTING_GROUNDS} from '../features/world/data/MonsterEcology';
import {sys} from 'cc';
import type {MenuRow} from '../shared/ui/MenuPanel';
import {UI_SETTINGS_REFERENCE} from '../shared/ui/UiChrome';
import {showJourneyStart,type JourneyStartState} from '../features/journey/runtime/JourneyStartScreen';
import {startMenuText as startText} from '../features/journey/locales/StartMenuText';
import {renderProfessionPanel,renderAllocationPanel,discardPreparationPreview} from '../features/progression/runtime/PreparationPanels';
import {automationText as autoText} from '../features/automation/locales';
import {worldText} from '../features/world/locales';
import {campaignText} from '../features/campaign/locales';
import {chapterTwoChoiceHint} from '../features/campaign/common/ChapterTwoEncounters';
import {encounterText} from '../features/campaign/locales/ChapterTwoEncounterText';
import {SIDE_QUESTS} from '../features/journey/runtime/SideQuestPanel';
export function renderMenu(hud:Hud,game:GameSession,menu:string,loading:boolean,failure:string,page:number,merchantId:string,visited:Record<string,boolean>,saved:string,updateReady=false,guestTest=false,musicLabel='背景音乐：开',skillEffectDebug=false,start:JourneyStartState={canContinue:true,recoveryRequired:false}){
 const s=game.state,d=s.dialogue;
 if(menu!=='checks')discardCombatSkillPreview(game);
 if(menu!=='attributes')discardAttributePreview(game);
 if(!menu.startsWith('allocation:'))discardPreparationPreview(game);
 if(menu==='title'){showJourneyStart(hud,loading,failure,guestTest,start);return;}
 if(menu==='confirm-new'){hud.show(startText('restart.title'),startText('restart.body')+(start.restartError?'\n\n'+start.restartError:''),[{label:startText('restart.confirm'),action:'confirm-new'},{back:true,label:startText('restart.cancel'),action:'cancel-new'}],false,{dismissOnBackdrop:false});return;}
 if(d&&!start.fromTitle){const hints=d.options.map(o=>chapterTwoChoiceHint(d.id,o.id)).filter((hint):hint is string=>!!hint),body=d.text+(hints.length?'\n\n'+hints.map(hint=>encounterText('ui.choiceHint',{hint})).join('\n'):'');hud.show(d.speaker,body,d.options.map(o=>({label:o.label,action:'choice:'+o.id})));return;}
 if(s.status==='dead'&&!start.fromTitle){hud.show('旅途尚未结束','返回最近检查点。已击败的敌人、证据与战利品仍然保留。',[{label:'返回检查点',action:'retry'},{label:startText('menu'),action:'title'}]);return;}
 if(!menu){hud.clearModal();return;}
 const journalRequest=adventureJournalRoute(menu,chapterForArea(s.area));
 if(menu==='journal'||journalRequest){hud.journal(game,visited,journalRequest);return;}
 if(renderPetPanel(hud,game,menu))return;
 if(menu==='dev-tools'&&game.developmentTools.enabled){
  const v=game.developmentTools.view();
  hud.showList('DEV 快速验证',`Lv${v.level} · 生命 ${Math.ceil(v.hp)}/${v.maxHp} · 职业资源 ${Math.floor(v.resource)}/${v.maxResource}\n金币 ${v.gold} · 铁 ${v.iron} · 符文 ${v.runes} · 核心 ${v.cores}\n${v.feedback||'手动操作，仅修改当前独立 dev 旅程。'}`,[
   {label:'补满生命与职业资源',detail:'保留敌人、伤害与技能消耗规则',action:'dev:refill'},
   {label:'补齐药水',detail:'四类药水补至正常携带上限',action:'dev:supplies'},
   {label:'补充金币与培养材料',detail:'金币、铁、符文、核心各 9999',action:'dev:materials'},
   {label:'等级＋5',detail:'保留剧情、任务和已持有装备',action:'dev:level5',disabled:v.level>=CAMPAIGN_MAX_LEVEL},
   {label:`升至${CAMPAIGN_MAX_LEVEL}级`,detail:'按正常成长获得技能与属性点',action:'dev:levelMax',disabled:v.level>=CAMPAIGN_MAX_LEVEL},
   {label:'清除 Boss 再战等待',detail:'从旅程页重新挑战，仍需真实击杀',action:'dev:boss-ready',disabled:!v.bossWaits},
   {label:'技能训练场',detail:'技能1—5级、靶阵、群怪与伤害统计',action:'training:enter'},
  ],[{label:'返回暂停',action:'pause'},{label:'继续旅途',action:'close'}],hud.touchTargetSize,{placement:'right',width:sys.isMobile?620:560});return;

 }
 if(menu.startsWith('campaign-prerequisites:')){
  const id=menu.slice('campaign-prerequisites:'.length),targets=campaignPrerequisiteTargets(game,AREAS,id);
  const taskEvent=SIDE_QUESTS.some(q=>q.steps.some(step=>step===id));
  hud.showList(campaignText('event.choosePrerequisite'),`${game.campaignEventAvailability(id,true).reason}\n\n${campaignText('event.navigationHint')}`,targets.map(target=>({label:target.destination.label,detail:`${getArea(target.destination.area).name} · ${target.blocked?autoText('route.locked'):campaignText('event.navigate')}`,action:`campaign-prerequisite-go:${id}:${target.id}`,disabled:target.blocked})),[{back:taskEvent,label:taskEvent?encounterText('ui.backTask'):campaignText('event.return'),action:taskEvent?'journey-field-task:'+id+':tasks':'close'}]);return;
 }
 if(menu.startsWith('interaction:')){
  const object=getArea(s.area).objects.find(o=>o.id===menu.slice(12)&&(game.interactionVisible(o)||game.interactionAvailability(o).completed));
  if(!object){hud.show(autoText('interaction.unavailable'),autoText('task.failed'),[{label:autoText('interaction.cancel'),action:'close'}]);return;}
  const status=game.interactionAvailability(object);
  if(object.action==='campaign_event'||!status.available||status.readOnly){
   const prerequisites=!status.available&&!status.completed?campaignPrerequisiteTargets(game,AREAS,object.eventId??''):[];
   const navigation=prerequisites.length?{label:campaignText('event.goPrerequisite'),action:prerequisites.length===1&&!prerequisites[0].blocked?`campaign-prerequisite-go:${object.eventId}:${prerequisites[0].id}`:`campaign-prerequisites:${object.eventId}`}:undefined;
   const body=status.completed?`${campaignText('event.completed')}\n\n${status.reason}`:`${status.reason}\n\n${object.description}`;
   hud.show(object.label,body,status.completed||status.readOnly?[{label:worldText('interaction.return'),action:'close'}]:[navigation??{label:status.available?status.confirmLabel:worldText('interaction.locked'),action:'interaction-confirm:'+object.id,disabled:!status.available},{label:worldText('talk.later'),action:'close'}]);return;
  }
  const merchant=object.action==='merchant'?MERCHANTS[canonicalMerchant(object.merchant??object.actor??'')]:undefined;
  const title=merchant?.name??(object.actor?object.label.split(/[：:]/)[0]:object.label);
  const body=merchant?shopGreeting(game):object.actor==='kael'?worldText('talk.kael'):`${object.description}\n\n${object.action==='journey_task'?worldText('talk.task'):status.reason}`;
  const choice=merchant?worldText('talk.shop'):object.action==='journey_task'?autoText('interaction.investigate'):object.actor==='kael'?worldText('talk.route'):status.confirmLabel;
  hud.show(title,body,[{label:choice,action:'interaction-confirm:'+object.id},{label:worldText(merchant?'talk.noThanks':'talk.later'),action:'close'}]);return;
 }
 if(menu==='hunting'){
  const high=s.progression.level>=11,ids=high?['H03','H04','H07','H17','S02','S08']:['S02','S03','S04','S08','S17'];
  hud.showList('出发狩猎','旅店与石桥镇是安全区。第一猎区：出旅店 → 石桥镇东侧通道 → 南渡码头。抵达后，兽群就在落点西北侧。\n普通怪28秒、群首50秒补充；离开刷新点20米后刷新。任务与刷怪都能升级、获得武器。',ids.map(id=>({label:`${getArea(id).name} · Lv${HUNTING_GROUNDS[id].level}`,detail:`${id} · ${HUNTING_GROUNDS[id].packs.flat().length}只游荡怪${id==='H17'?' · 可选巨兽首领':''} · 点击查看路线`,action:'journey-map:'+id})),[{label:encounterText('ui.taskPanel'),action:'journey'},{label:'战役见闻',action:'campaign-log'},{back:true,label:'返回旅途',action:'close'}]);return;
 }
 if(menu==='campaign-log'){const scenes=CAMPAIGN_SCENES.filter(d=>s.receipts[`campaign:seen:${d.id}`]);hud.showList(ct('ui.logTitle'),ct('ui.logDescription'),scenes.map(d=>({label:ct(d.title),detail:ct('ui.chapter',{chapter:d.chapter,area:getArea(d.area).name}),action:'campaign-log:'+d.id})),[{label:encounterText('ui.taskPanel'),action:'journey'},{label:ct('ui.return'),action:'close'}]);return;}
 if(menu.startsWith('campaign-log:')){const d=campaignScene(menu.slice(13));if(d&&s.receipts[`campaign:seen:${d.id}`])hud.show(ct(d.title),d.beats.map(b=>`${ct(b.speaker)}: ${ct(b.text)}`).join('\n\n'),[{back:true,label:ct('ui.logIndex'),action:'campaign-log'},{label:ct('ui.return'),action:'close'}]);return;}
 if(menu==='journey-finish'){hud.show('前两章战役完成',encounterText('ui.finishDescription'),[{label:encounterText('ui.tab.side'),action:'journey-tasks:side'},{label:taskPanelText('tab.chapters'),action:'journey-tasks:chapters'},{label:'继续探索',action:'close'}]);return;}
 if(menu.startsWith('journey')){renderJourney(hud,game,menu);return;}
 if(menu==='map'){hud.atlas(game,visited);return;}
 if(menu==='navigation'){
  const area=getArea(s.area),p=s.player,metres=(q:{x:number;z:number})=>Math.ceil(Math.hypot(p.x-q.x,p.z-q.z));
  const rows=[...area.objects.filter(o=>game.interactionVisible(o)&&(o.action!=='journey_task'||game.journey.currentTask()?.id===o.eventId&&game.journey.currentTask()?.goal==='observe')).map(o=>({label:o.label,detail:`${metres(o)}米 · 抵达后自动打开交互`,action:'auto:object:'+o.id})),...area.exits.map(e=>({label:e.label,detail:game.exitRequirement(e)??`${metres(e)}米 · 自动步行并通过出口`,action:'auto:exit:'+e.id,disabled:!!game.exitRequirement(e)}))];
  hud.showList('前往场景目标','移动可随时接管，抵达目标后自动打开交互。',rows,[{label:tradingText('title'),action:'services'},{label:'打开地图',action:'map'},{back:true,label:'返回旅途',action:'close'}],hud.touchTargetSize,{placement:'left',width:sys.isMobile?620:500,quiet:true});return;
 }
 if(menu==='checks'){renderCombatPanel(hud,game,'skills');return;}
 if(menu==='attributes'){renderCharacterStats(hud,game);return;}
 if(menu==='profession'){renderProfessionPanel(hud,game);return;}
 if(menu==='allocation:attributes'||menu==='allocation:skills'){renderAllocationPanel(hud,game,menu==='allocation:skills'?'skills':'attributes');return;}
 if(menu==='appearance'){renderCharacterPanel(hud,game,'inventory',true);return;}
 if(menu==='exploration-skills'){renderCharacterPanel(hud,game,'skills');return;}
 if(menu==='equipment-catalog'){renderCharacterPanel(hud,game,'catalog');return;}
 if(menu==='check-history'){
  const entries=Object.entries(s.dice.records),gears=Object.entries(s.dice.gear??{});if(!entries.length&&!gears.length){hud.show('机遇记录','这里记录探索行动与装备获得情况。核对信件或拆解铜簧匣时，可以通过掷骰检定推进探索。获得装备后直接入袋，可在背包查看说明与基础属性，随机属性在强化中追加。',[{label:'探索手段',action:'exploration-skills'},{back:true,label:'返回旅途',action:'close'}]);return;}
  const rows=entries.map(([id,r])=>{const d=SKILL_CHECKS[id],roll=r.rolls[r.rolls.length-1];return {label:`${roll.success?'达成':'转机'} · ${d.title}`,detail:`掷骰 ${roll.faces.join(' / ')} → ${roll.kept} +准备${roll.bonus}${roll.assist?' +线索'+roll.assist:''} = ${roll.total} / 目标${d.dc}${r.committed?' · 已记录':' · 待确认'}`,action:'check-log:'+id};});
  rows.push(...gears.map(([id,r])=>{const outcome=r.claimed?equipmentOutcome(s.seed,r):null;return {label:`${outcome?'历史锻印':'获得装备'} · ${EQUIPMENT[id].name}`,detail:outcome?`${outcome.name} · ${bonusText(outcome.bonus)||'保留原装'} · 已记录`:`${EQUIPMENT[id].quality} · 已入袋 · 已记录`,action:'check-log:gear:'+id};}));
  hud.showList('机遇记录',`余烬 ${s.dice.inspiration}/4 · 探索行动与装备获得记录`,rows,[{label:'探索手段',action:'exploration-skills'},{back:true,label:'返回旅途',action:'close'}]);return;
 }
 if(menu.startsWith('check-log:gear:')){const id=menu.slice(15),r=s.dice.gear?.[id];if(r){const o=r.claimed?equipmentOutcome(s.seed,r):null,body=o?`历史锻印 · ${o.name}\n${bonusText(o.bonus)||o.description}${o.upgrade?'\n历史额外发现：'+EQUIPMENT[o.upgrade].name:''}\n\n历史结果已记录，当前获得装备不再追加随机属性。`:`获得记录 · ${EQUIPMENT[id].quality}\n${EQUIPMENT[id].description}\n\n装备已入袋，无需逐件确认。可在背包查看属性，随机属性在装备强化中追加。`;hud.show(EQUIPMENT[id].name,body,[{back:true,label:'返回记录',action:'check-history'},{label:'背包',action:'inventory'}]);return;}}
 if(menu.startsWith('check-log:')){const id=menu.slice(10),r=s.dice.records[id],d=SKILL_CHECKS[id];if(r&&d){const roll=r.rolls[r.rolls.length-1];hud.show(d.title,`${ACTION_NAMES[d.skill]} · 目标 ${d.dc}\n${r.context.mode==='advantage'?'线索充分：两骰择高':r.context.mode==='disadvantage'?'局势不利：两骰取低':'行动掷骰'}\n\n${r.rolls.map(v=>`第${v.attempt}次：${v.faces.join(' / ')} → ${v.kept} +${v.bonus}${v.assist?' +'+v.assist:''} = ${v.total} · ${v.success?'成功':'失败'}`).join('\n')}\n\n${roll.success?d.successText:d.failureText}`,[{back:true,label:'返回记录',action:'check-history'},{back:true,label:'返回旅途',action:'close'}]);return;}}
 if(menu==='inventory'||menu==='equipment'){renderEquipmentPanel(hud,game);return;}
 if(renderEquipmentDismantling(hud,game,menu))return;
 if(renderGemPanel(hud,game,menu))return;
 if(renderForging(hud,game,menu))return;
 if(renderShopPanel(hud,game,menu,merchantId))return;
 if(menu==='help'){hud.show('旅途手册',tacticsText('combatHelp')+'\n'+tacticsText('dodgeHelp')+'\nWASD / 左摇杆移动，Shift慢行，鼠标瞄准，J / 鼠标左键基础攻击；弓按住蓄力、松手放箭。\nQ/E/T（或1/2/4）使用右侧三个普通技能，R（或3）使用左上职业自保，G使用末位终极，空格独立闪避。技能默认自动瞄准射程内无遮挡的最近怪物，轻点释放；按住时实时跟随，目标失效后重新索敌。鼠标／触摸板按住或触屏原地长按技能、终极、闪避按钮3.6秒可查看说明，松开关闭且不施放。触屏拖动改为本次手动瞄准，键盘按住技能键后移动鼠标也可手动选点，松开释放。设置→操作可切换默认自动/手动瞄准。移入取消区放弃。Esc或鼠标右键也可取消瞄准。技能超距或被墙阻挡不会自动跑近。\n所有主动技能与闪避均有独立冷却，终极冷却长于普通技能。相同条件下，单体主力对单总伤害高于群攻终极，群攻终极高于普通群攻；群攻依靠覆盖更多目标取得收益。终极消耗45点当前职业资源，并保留短暂释放间隔。普攻与闪避不耗资源；技能消耗体力／专注／法力并自动恢复。命中值与目标闪避值决定接触后的命中率，范围60%—100%；弓术专注上限提高命中，当前专注多少不影响命中。敏捷同时提升闪避。实体箭仍须碰到目标，落空与被闪避均显示MISS；主动闪避仍按动作时机避开攻击。5使用生命药水，6使用对应职业药水，共享5秒冷却。灵泉复苏位于补给栏第三格，也可按7施放；疾风连射、猎王印和雷霆战印满足条件后自动强化，不占战斗按钮。C打开战斗技能，V打开成长属性，B背包，M地图，F交互。火墙与陷阱用于延缓追击，护盾和机动技能用于应对危险。\n脱战后可随时更换装备。职业技能位置固定，不支持替换；安全检查点可以技能加点、装备强化与重配属性。怪物倒地后尸体保留约30秒，掉落装备会留在地面。靠近后点击拾取（键盘F）；顶部自动任务会连续寻路、战斗，抵达现场行动和剧情分支后选择首个正常推进选项并继续；挂机只在当前场景刷怪。左侧寻路抵达人物或物件后也会自动打开交互。仅挂机刷怪经验受每日递减与5000上限限制，在挂机顶栏查看；自动任务与手动战斗不占用挂机额度。自动任务与挂机会自动寻路拾取，未拾取装备随存档保留。获得装备后直接入袋，无需逐件确认；可在背包查看说明与基础属性。随机属性通过装备强化追加，可从背包装备养成入口查看。探索行动中Enter/空格掷骰，R消耗余烬重掷，G采用线索。',[{label:'战斗技能',action:'checks'},{back:true,label:'返回旅途',action:'close'}]);return;}
 if(menu==='settings'){
  const musicState=musicLabel.replace(/^背景音乐[：:]\s*/,''),musicFailed=musicState!=='开'&&musicState!=='关',tab=hud.settingsTab;
  const names:MenuRow={label:'技能名称',detail:'',skin:'menu-skillnames-v5',action:'toggle-skill-names',value:hud.skillNamesVisible?'开':'关',selected:hud.skillNamesVisible,toggle:true};
  const rows:MenuRow[]=tab==='audio'?[
   {label:'背景音乐',detail:musicFailed?musicState:'',skin:'menu-music-v5',action:'toggle-music',value:musicFailed?'重试':musicState,selected:musicState==='开',toggle:!musicFailed},
   {label:'减少动态',detail:'',skin:'menu-motion-v5',action:'toggle-impact-motion',value:hud.reducedMotion?'开':'关',selected:hud.reducedMotion,toggle:true},names,
  ]:tab==='controls'?[
   {label:'技能瞄准',detail:hud.skillAimMode==='auto'?'轻点锁敌 · 拖动手动':'拖动选点 · 松开释放',action:'toggle-skill-aim',value:hud.skillAimMode==='auto'?'自动':'手动',selected:hud.skillAimMode==='auto'},
   names,{label:'操作说明',detail:'移动、瞄准与取消',action:'help'},{label:'技能与加点',detail:'固定技能与职业强化',action:'checks'},
  ]:[
   {label:encounterText('ui.taskPanel'),detail:getArea(s.area).name,action:'journey'},
   {label:redemptionText('entry'),detail:redemptionText('entry.detail'),action:'redemption'},
   {label:tradingText('title'),detail:tradingText('hint'),action:'services'},
   ...(game.pets.view().enabled?[{label:petUiText('title'),detail:petUiText('index.description'),action:'pets'}]:[]),
   {label:ct('ui.language'),detail:'',action:'toggle-story-locale',value:currentLocale()==='en'?'EN':'中文'},
   {label:'暂停与旅途',detail:`${saved} · v${BUILD_INFO.version}`,action:'pause'},
   ...(game.developmentTools.enabled?[{label:'DEV 快速验证',detail:'补给、成长与 Boss 再战',action:'dev-tools'}]:[]),
   {label:trainingText('title'),detail:trainingText('entryDetail'),action:'training:enter'},
   ...(skillEffectDebug?[{label:'技能效果调试',detail:'1—5级技能预览',action:'skill-effect-debug'}]:[]),
  ];
  hud.showList('设置','',rows,[{label:startText('menu'),action:'title'},{label:'检查点补给',action:'rest'},{back:true,label:'返回旅途',action:'close'}],hud.touchTargetSize,{
   placement:'right',width:sys.isMobile?UI_SETTINGS_REFERENCE.mobileWidth*hud.touchTargetSize/48:400,rightInset:sys.isMobile?144*hud.touchTargetSize/48:120,keepCenterClear:true,centeredTitle:true,quiet:false,crest:true,variant:'settings',
   tabs:[{label:'音画',action:'settings-tab:audio',selected:tab==='audio'},{label:'操作',action:'settings-tab:controls',selected:tab==='controls'},{label:'旅途',action:'settings-tab:journey',selected:tab==='journey'}],
  });return;
 }
 if(menu==='complete'){hud.show('破晓之战 · 终局','黑冠之战已结束，你在终局留下的选择与同伴的去向已记录。\n\n可以继续回访各地，寻找尚未发现的隐匣，完成支线并收集装备。',[{label:'继续探索',action:'close'},{label:'旅途地图',action:'map'}]);return;}
 hud.showList('旅途暂停',`${getArea(s.area).name}\n${saved} · v${BUILD_INFO.version}${guestTest?'\n游客测试 · 仅本机存档，无云端同步':''}`,[
  ...(updateReady?[{label:'安装已下载更新',detail:'',action:'update:show'}]:[]),
  {label:startText('menu'),detail:startText('menu.detail'),action:'title'},
  {label:encounterText('ui.taskPanel'),detail:game.objective(),action:'journey'},
  ...(game.pets.view().enabled?[{label:petUiText('title'),detail:petUiText('index.description'),action:'pets'}]:[]),
  {label:tradingText('title'),detail:'装备、补给、宝石与培养',action:'services'},
  {label:'检查点休整',detail:'',action:'rest'},
  {label:'游戏设置',detail:'音乐、动态与技能名称',action:'settings'},
  ...(game.developmentTools.enabled?[{label:'DEV 快速验证',detail:'补给、成长与 Boss 再战',action:'dev-tools'}]:[]),
  {label:'操作与帮助',detail:'',action:'help'},
  {label:trainingText('title'),detail:trainingText('entryDetail'),action:'training:enter'},
   ...(skillEffectDebug?[{label:'技能效果调试',detail:'1—5级技能预览',action:'skill-effect-debug'}]:[]),
  {label:startText('restart'),detail:startText('restart.detail'),action:'new'},
 ],[{label:'继续旅途',action:'close'}],hud.touchTargetSize,{placement:'right',width:sys.isMobile?620:500});
}
