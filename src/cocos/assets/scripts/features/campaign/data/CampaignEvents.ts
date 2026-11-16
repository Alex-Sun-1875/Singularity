import {CAMPAIGN_LEVEL_LIST} from './Campaign';
import {campaignText} from '../locales';
import {GROWING_QUESTS} from '../../equipment/data/GrowingEquipment';
import {CHAPTER_TWO_ACTIONS,chapterTwoEventId,type ChapterTwoActionId} from './ChapterTwoEncounters';
import {encounterText} from '../locales/ChapterTwoEncounterText';
import {CHAPTER_TWO_SIDE_QUEST_EVENTS} from './ChapterTwoSideQuests';
/** Physical actions and their persistent outcomes. Walking into a region never pays a quest. */
export interface CampaignChoiceDef {id:string;label:string;text:string;sets:string[]}
export interface CampaignEventDef {
 id:string;area:string;label:string;description:string;requires?:string[];requiresAny?:string[];
 at?:{x:number;z:number};actor?:string;actorModel?:string;
 clearEncounter?:boolean;sets?:string[];gold?:number;iron?:number;runes?:number;cores?:number;
 items?:string[];recipes?:string[];experienceEvent?:string;experience?:number;
 choices?:CampaignChoiceDef[];peacefulResolution?:boolean;choiceItems?:string[];optional?:boolean;
 confirmLabel?:string;completionText?:string;prerequisiteHints?:Record<string,string>;
 chapterTwoAction?:ChapterTwoActionId;
}
const event=(id:string,area:string,label:string,description:string,extra:Omit<CampaignEventDef,'id'|'area'|'label'|'description'>={}):CampaignEventDef=>({id,area,label,description,...extra});
export const CAMPAIGN_EVENT_LIST:CampaignEventDef[]=[
 event('s07-skill-archive','S07','阅读磨坊的永久技能档案','把旧驿房的练习记录与水轮院猎记逐页比对，保存一次档案经验。旧符咒已退役，不因阅读补回任何消耗品。',{experience:220}),
 event('s13-evacuate','S13','先疏散工人，固定吊料机','沿旧石场侧面打开工棚出口，让工人离开吊料落区，再把机台固定在地面的安全卡位。',{sets:['s13_workers_safe']}),
 event('s13-dismiss-overseer','S13','出示扣押令，解除监工职权','在工人已经离开危险面后，把现场扣押原令与工役名单当面对照，取消这份没有合法期限的监工任命。',{requires:['s13_workers_safe','s10-detention'],peacefulResolution:true,sets:['s13_overseer_dismissed']}),
 event('h14-cancel-hunt','H14','缴销猎契，撤下督猎封锁','读过被转卖的猎径副图后，将同一份猎契交到岩林登记台，明确沿线藏身处不属于可出售的追猎目标。',{requires:['s14-huntroute'],peacefulResolution:true,sets:['h14_hunt_cancelled'],confirmLabel:campaignText('event.cancelHunt'),completionText:campaignText('event.huntComplete'),prerequisiteHints:{'s14-huntroute':campaignText('event.huntPrerequisite')}}),
 event('b14-return-contract','B14','核对返还凭据，解除打捞封锁','核对归帆镇鉴定过的绳结货号，再将合法返还凭据交给封锁者；同一首领事件不因和平处理少领固定装备。',{requires:['campaign-clue-B03'],peacefulResolution:true,sets:['b14_salvage_released']}),
 event('f17-release','F17','从检修面解除典狱长扣押','先沿检修侧路核实出口，再当面出示当前征掘令的权限限制，解除这处超出原令的扣押。',{requires:['current_order_verified','f07_exit_verified'],peacefulResolution:true,sets:['f17_detention_lifted']}),
 event('h03-evacuate','H03','疏散工位，插入固定卡销','先让工匠离开镜架的转动面，再从地面的控制台插入固定卡销；不用指定同伴或消耗材料。',{sets:['h03_workers_safe'],peacefulResolution:true}),
 event('m3-heat-test','H03','转开散热叶片，完成回退试验','在停稳的镜架旁实际转动散热叶片，读取升温与回落的两组刻线。试验可以安全中止，工艺图纸来自完成后的记录。',{requires:['h03_workers_safe','workers_released','gate_raised'],sets:['m3_heat_test'],gold:180,iron:10,runes:8,recipes:['C01','C03','C04','C05','C06','C07','C08'],experienceEvent:'M3_XP_1',clearEncounter:true}),
 event('h05-stop-hoist','H05','停下采掘机，打开井架安全锁','把采掘机停在标定的地面安全位，再打开上方机械锁。井下的人不能隔墙操作，未开井仍可从山路返回。',{clearEncounter:true,sets:['e05_open'],iron:3,gold:30}),
 event('h07-skill-archive','H07','查阅石柜中的永久技能档案','旧石柜保存的是军中练习记录。按自己的角色等级学习，档案只结算一次经验，不再补充任何战斗符咒。',{experience:450}),
 event('h08-lower-bridge','H08','接上近侧手柄，放下矿桥','清除固定桥头组后，把同侧的原手柄接回绞盘并放桥。桥后的军械岸没有矿井后门，放下后保留双向道路。',{requires:['m3_heat_test'],clearEncounter:true,sets:['m4_bridge_open']}),
 event('m4-bridge-reward','H09','打开桥后武备台','站在已放下的桥同岸，解开武备台的封扣；固定装备与工艺自选属于同一个主线奖包。',{requires:['m4_bridge_open'],sets:['m4_bridge_reward'],gold:180,iron:12,runes:4,items:['W03','A05'],choiceItems:['DR2-01','DR2-02','DR2-03','DR2-04'],experienceEvent:'M4_XP_1'}),
 event('u106-stop-array','U1-06',encounterText('action.oath-read.label'),encounterText('action.oath-read.description'),{chapterTwoAction:'oath-read'}),
 event('u107-pressure','U1-07','先护住工位，再泄压停炉','沿检修侧路逐段放开泄压轮，工位后的退路始终保留。停机后巨像失去驱动，不要求用某个职业或稀有物品解锁。',{sets:['u107_furnace_stopped'],peacefulResolution:true}),
 event('m4-contact','U1-08','建立可中止的第一次接触','把手放在外侧的冷白接触台，听取核心的回应，再主动断开连接；不同意它的请求也能完成观察与记录。',{requires:['m4_bridge_reward'],sets:['m4_contact'],gold:80,iron:4,experienceEvent:'M4_XP_2'}),
 event('u108-exit-check','U1-08','实走迁行口并核验两端安全线','从接触台走到迁行口，核对两侧回退刻线。看过迁行和静眠原图后，最终行动才有可执行的安全方案。',{requires:['m5_archive'],sets:['core_exit_verified']}),
 event('u110-open-exit','U1-10','从内侧解除见日长廊的出口门','用洞内可见的旧门闩打开旱谷出口，再实际踏上采光的平台；首次从地表无法隔门开闩。',{sets:['e07_open'],gold:30}),
 event('b04-mirror-test','B04','校准反光壶，确认影船只是重播','把灯坊的反光壶摆到两道刻线之间，先遮光再重放。校光的结果记录为旁证，不把别人的旧声音当成现在的同意。',{sets:['shadowship_calibrated']}),
 event('b08-oath-reading','B08','读完旧堂的退出协议','核对钟纹旁明确写下的退出条件；拒绝阿德里安的条件不会触发整片地图敌对，地宫干阶仍有原路返回。',{sets:['oath_exit_protocol']}),
 event('b11-open-arm','B11','固定吊臂，放开通往码头的接近桥','把吊臂停在地面的固定卡位，移开接近码头的障碍。操作在本平台完成，失败可以回退，不需要远处再找手柄。',{clearEncounter:true,sets:['harbor_access'],iron:3}),
 event('m6-verify-cargo','B10','校光、复秤并打开完整宝匣','击败码头的固定守军后，在同一平台逐一校光、复秤、核对封签，最后打开宝匣。技能外观的两种保存方案互斥且价值相同。',{requires:['m5_archive'],clearEncounter:true,sets:['m6_verified'],gold:320,iron:18,items:['W10','J05'],experienceEvent:'M6_XP_1',choices:[
  {id:'preserve','label':'保留完整护符的外观','text':'保存完整护符与鉴定记录，获得核心护持外观；它不提供提前的技能等级。',sets:['cosmetic_core_guard']},
  {id:'study','label':'保存余烬铜芯的外观','text':'完整记录铜芯的构造，获得焚星技能外观；不把非人生命当作战利品。',sets:['cosmetic_cinder_star']},
 ]}),
 event('u203-pressure','U2-03','分区泄压，停下镇守并打开深闸','从内侧安全控制面按刻线释放三段压力，再打开通向前厅的深闸。停机与击败镇守共享首领收据；主线试验始终可重试。',{requires:['m4_contact'],sets:['m5_pressure','u2_deep_gate_open'],peacefulResolution:true,gold:100,iron:6,experienceEvent:'M5_XP_1'}),
 event('u204-recipe','U2-04','查阅守库人的静思银环图纸','退出协议压在配方下方。读图只学习制作方法，戒指仍需在安全检查点消耗对应材料制作，不能无限领取。',{recipes:['C10'],gold:40}),
 event('u205-skill-archive','U2-05','阅读钟纹下的永久技能档案','将钟纹与练习图逐行对照，保存一次档案经验；旧符咒的库存来源已经退役，阅读不会补出消耗品。',{experience:900}),
 event('u206-angle-one','U2-06','从正面读取封炉原刻','站在正面的干石阶上，记录第一层凿痕与日期。当前征用者的侧室不会封住主线原刻。',{sets:['archive_angle_one']}),
 event('u206-angle-two','U2-06','从侧光角度复核被覆写的原刻','绕到侧面干路，让擦过石面的光线显出第二层凿痕；这与正面的读法共同组成可复核的证据。',{sets:['archive_angle_two']}),
 event('m5-archive','U2-06','比较两角度原刻与现代拓本','同时核对两种角度的原刻和瑟维恩的现代拓本，明确封炉决定与当前征用的不同责任。护腕只按唯一收据补领。',{requires:['m5_pressure','archive_angle_one','archive_angle_two'],sets:['m5_archive'],gold:140,iron:8,runes:4,items:['A11'],recipes:['C09','C10'],choiceItems:['DR3-01','DR3-02','DR3-03','DR3-04','DU2-01','DU2-02','DU2-03','DU2-04'],experienceEvent:'M5_XP_2'}),
 event('u207-stop-mirrors','U2-07','沿侧廊解除镜阵，取迁行与静眠原图','沿两条相通侧廊找到镜阵的安全断开面，关闭供能再取出原图。停机与战斗是同一事件，主线图不以杀死守秘者为条件。',{sets:['u207_mirrors_stopped','core_plans_known'],peacefulResolution:true}),
 event('u209-open-service','U2-09','从地宫内侧打开堡外检修门','解除检修道内侧的旧门扣并走向干壕，出口只到外城地面，不会绕过外弩台、决战庭和军械库。',{clearEncounter:true,sets:['e08_open'],iron:4}),
 event('f04-safety','F04','解除危险工位，固定备用镜组','先解开危险工位，再让备用镜组回到可锁定的位置。侧入或局部交涉完成同一现场处置，不会把已获救的凯尔重新囚禁。',{requires:['m6_verified','m3_heat_test','m5_pressure'],sets:['m7_prepared','f04_workers_safe'],peacefulResolution:true,gold:160,iron:8,runes:4,cores:2,recipes:['C02'],experienceEvent:'M7_XP_1'}),
 event('f07-safety','F07','实走接应出口并核验撤离道路','沿旧仓后的坡道实走出口，再确认接应人能从同一条路离开。拒绝付钱仍可使用已经核验的主线出口。',{requires:['m6_verified','m3_heat_test','m5_pressure'],sets:['m7_prepared','f07_exit_verified'],clearEncounter:true,gold:160,iron:8,runes:4,cores:2,recipes:['C02'],experienceEvent:'M7_XP_1'}),
 event('f06-original','F06','取正本，对照当前征掘令','通过文书院的侧道读取征掘令正本，比较签字与权限；未公开过副本也能取得证据，不替任何人默认同意。',{sets:['current_order_verified']}),
 event('f09-disarm','F09','亲手拔下西弩台的固定销','清除本台守军后，从同侧地面拔下固定销并卸开弩机。拆掉的弩台永不复活，先拆东台或西台都可。',{requires:['m7_prepared'],clearEncounter:true,sets:['west_tower_down']}),
 event('f10-disarm','F10','亲手拔下东弩台的固定销','清除本台守军后拆下东侧弩机，实际卸销与西弩台分别记账。只限制最终战场入口，外城的返回道路保持开放。',{requires:['m7_prepared'],clearEncounter:true,sets:['east_tower_down']}),
 event('m7-open-vault','F14','转动同侧绞盘，开启黑冠主箱','阿德里安败北且两座外弩台拆除后，在战场同侧转动绞盘开启主箱；双生契约沿用检修箱的唯一领取记录。',{requires:['final_ready','boss_defeated:BOSS_R4'],clearEncounter:true,sets:['m7_vault'],gold:280,iron:16,runes:4,items:['W06','J07'],experienceEvent:'M7_XP_4'}),
 event('f14-side-cosmetic','F14','搜索独立侧格中的终誓图样','主箱旁的窄侧格保存万钧雷潮·终誓外观，只记录一次；外观不提前开放终极技能、五级范围或连接人数。',{requires:['m7_vault'],sets:['cosmetic_thunder_oath'],optional:true}),
 event('m8-final-choice','U1-08','再接触核心，选择并执行终局方案','核验原图与迁行口后回到接触台，亲手完成选择的局部操作。迁行、静眠与维持边界获得同等报酬，不把非人生命兑换成装备。',{requires:['m7_vault','core_exit_verified','core_plans_known'],sets:['m8_complete'],gold:240,iron:8,experienceEvent:'M8_XP_1',choices:[
  {id:'migrate','label':'打开迁行路线','text':'沿已核验的两端刻线分段开放迁行口，核心通过后将隔离闸恢复；附近仍有未重置的世界与人物。',sets:['ending_migration']},
  {id:'sleep','label':'协助核心进入静眠','text':'按原图逐段降低共鸣，确认冷白炉光稳定后断开接触；不是一次无声的击杀。',sets:['ending_sleep']},
  {id:'boundary','label':'保留核心并维持安全边界','text':'恢复已核验的退路与隔离线，约定可中止的后续接触，人物各自保有离开的选择。',sets:['ending_boundary']},
 ]}),
];
// Small authored investigation rewards use the same persistent transaction as
// main events. Their numbers come from each location's reward field.
for(const level of CAMPAIGN_LEVEL_LIST){
 const gold=Number(/金币(\d+)/.exec(level.reward)?.[1]??0),iron=Number(/铁(\d+)/.exec(level.reward)?.[1]??0);
 if((!gold&&!iron)||['H05','U1-10','U2-03','U2-04','U2-09','B11'].includes(level.id))continue;
 CAMPAIGN_EVENT_LIST.push(event(`investigate-${level.id}`,level.id,`完成现场调查 · ${level.name}`,`${level.objective}。在现场核对可复查的痕迹与退路后结算这一处有限调查奖励；普通回访不会重发。`,{gold,iron,clearEncounter:level.encounter!=='无'}));
}
CAMPAIGN_EVENT_LIST.push(
 event('q1-old-command','S12','记录旧命令与空基座原件','从空基座旁的原命令与搬运簿记录三天轮换的承诺。这里只取得证据，不需要先表态支持任何阵营。',{requires:['s12-command'],sets:['q1_original']}),
 event('q1-witness','U1-06','向留守者核对当年停机记录','守誓阵停止后，让留守者逐段核对停机记录，保留与原命令不同的见证版本。不同意对方的立场也能保存事实。',{requires:['q1_original'],requiresAny:['u106_array_stopped','boss_defeated:ELITE_06'],sets:['q1_witness']}),
 event('q1-settle','F05','公开原件与证词的差异','把原命令、停机记录和证词同时放在旧营办公桌上，分别确认谁签令、谁执行与谁有权离开。',{requires:['q1_witness'],sets:['q1_complete'],gold:140,iron:6,experience:818,choiceItems:['DR1-01','DR2-02','DU1-03']}),
 event('q2-hunter','S19','救护猎人，记录人和古兽的去向','先从侧坡找到受伤猎人，核对沿猎径离开的居民与古兽。保留未同意公开的住处，不用击杀兽群交换好装备。',{sets:['q2_hunter_safe']}),
 event('q2-route','B15','沿旧渠观察迁徙并保存路线版本','沿干岸实看古兽迁徙方向，将猎人的记录与南岸脚印对上；由当事人决定哪一版道路可以交给接应者。',{requires:['q2_hunter_safe'],sets:['q2_route_confirmed'],choices:[{id:'private',label:'保留隐蔽住处','text':'只保存可公开的干岸道路，隐蔽住处留给沿线居民自己决定。',sets:['q2_private_route']},{id:'open',label:'公开已同意的接应道路','text':'只将获得同意的公共接应路线交给同行者，未公开的藏身处继续保密。',sets:['q2_public_route']}]}),
 event('q2-settle','F07','实走接应道路，结清猎径旧账','确认南岸的路线版本与眼前的接应出口对应，再核对沿路的人确实能够离开；不以出卖兽群或藏身者结算。',{requires:['q2_route_confirmed'],sets:['q2_complete'],gold:160,iron:6,experience:1605,choiceItems:['DR1-04','DR2-04','DR3-01']}),
 event('q3-cancel-letter','S18','稳定读取取消信和绳结货号','将残旗军需站的取消信抄件与旧绳结货号分别保存；转运副本不是主箱，也不要求先买任何货物。',{sets:['q3_letter_read']}),
 event('q3-identify','B03','交叉鉴定旧绳与封签','请艾莉丝只对可查验的货号、封签和日期作出鉴定，原信归谁保管由持有人决定；鉴定不要求购买礼袍。',{requires:['q3_letter_read'],sets:['q3_identified']}),
 event('q3-settle','B18','提交选定的双契证据版本','核对归帆鉴定、沉船潮痕与双契付款原件后，提交自己愿意公开的证据版本。公开与保留原件的报酬一致。',{requires:['q3_identified','campaign-clue-B14'],sets:['q3_complete'],gold:180,iron:8,experience:2468,choiceItems:['DR3-02','DR3-03','DR4-01']}),
 event('q4-demonstrate','U1-07','完成可复核的炉槽演示','炉槽安全后，把同一组刻线从两个角度重放，记录控制量和回退点；旁观者可以重复核对，而不是只能相信一句解释。',{requiresAny:['u107_furnace_stopped','boss_defeated:ELITE_05'],sets:['q4_demonstrated']}),
 event('q4-evidence','U2-06','保存演示与原刻的反证','将炉槽演示和两角度原刻并列，明确哪些相同、哪些不同。技术推测不能抹掉誓言对当事人的约束。',{requires:['q4_demonstrated','m5_archive'],sets:['q4_evidence']}),
 event('q4-settle','F06','请在场者复核并见证记录','在征掘令正本旁完成最后的重复演示，让见证者自行说明结论与限制；保留不同解释而完成同一调查。',{requires:['q4_evidence','current_order_verified'],sets:['q4_complete'],gold:180,iron:8,experience:3075,choiceItems:['DU1-04','DU2-02','DU2-03']}),
 event('q5-route','U1-03','亲自复核两段可折返路图','把凯尔留下的两段测距线从岔口实走到固定梯下方，分别核对当前通路与尚未放下的梯；路线事实不依赖购买或战斗表现。',{sets:['q5_route_checked']}),
 event('q5-return','S01-T6','核对工匠实际回镇并完成回访','确认获释者已经离开监区、拥有实走过的回返路，再在广场与他们复核各自的去向；不会复制一位仍在地下的人。',{requires:['workers_returned','q5_route_checked'],sets:['q5_complete'],gold:140,iron:6,experience:615,choiceItems:['DR1-02','DU1-02','DU2-01']}),
 event('q6-weigh','B14','核对船体潮痕和装载重量','先将船体潮痕与灯坊校光后的影像分开，再复秤能够实际接触的货件；旧影像不替任何藏品持有人作决定。',{requires:['shadowship_calibrated'],sets:['q6_weighed']}),
 event('q6-settle','B09','比较退款原件与装载副页','将稳定校光、复秤和实际船体的记录与退款原件并列，明确归还与收藏的边界；保留完整藏品，账目按唯一收据结清。',{requires:['q6_weighed'],sets:['q6_complete'],gold:160,iron:6,experience:3293,choiceItems:['DR3-04','DU2-04','DR4-04']}),
);
CAMPAIGN_EVENT_LIST.push(...CHAPTER_TWO_ACTIONS.map(action=>event(chapterTwoEventId(action.id),action.area,encounterText(`action.${action.id}.label`),encounterText(`action.${action.id}.description`),{at:action.point,chapterTwoAction:action.id})),...CHAPTER_TWO_SIDE_QUEST_EVENTS,...GROWING_QUESTS);
export const CAMPAIGN_EVENTS:Record<string,CampaignEventDef>=Object.fromEntries(CAMPAIGN_EVENT_LIST.map(def=>[def.id,def]));
