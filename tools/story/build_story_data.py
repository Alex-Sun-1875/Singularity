from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'data/story'

def write(name,data):
    (P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

characters={
 'schema_version':'1.0.0','project_id':'sword_and_fire','title':'剑与火','language':'zh-CN',
 'visual_direction':{'camera':'2.5D 俯视斜角；固定相机为主，遮挡物可淡出','reference_boundary':'借鉴写实奇幻的皮革、金属、布料层次与可信功能性装备；人物、脸、服装组合及标志全部原创，不复刻现有游戏角色。','readability':'玩家青绿布料，敌人锈红布料；轮廓优先于细密纹理；无血腥表现。'},
 'characters':[
 {'id':'char_player','name':'行路人','role':'玩家','faction':'caravan','chapters':['ch01','ch02','ch03','ch04'],'silhouette':'中等身形，短肩披布，单手钢剑，腰侧油壶；短衣摆避免遮住腿部动作。','palette':['palette_teal','palette_iron','palette_leather'],'motivation':'原本接护送差事，运粮车被截后决定把车和人一起带回。','arc':'收取报酬的护送者 → 连接营地与城内补给的行动者；不设天命或身世反转。','voice':'台词少，直接问路和办事；不设置默认姓名、性别台词或宏大自述。','model_asset_id':'model_player','model_scope':'首章静态分件基模与四方向透明图；绑定、战斗动画及引擎接入另行验收。','combat':'挥剑、闪避或短冲、推击、投油点火；剑与火共用此角色，不制作两套职业身体。'},
 {'id':'char_ahe','name':'阿禾','role':'营地管事','faction':'camp','chapters':['ch01','ch02','ch03','ch04'],'silhouette':'女性，结实短外套，米褐工作衣，红围巾，账册与小挎包；装备重实用不性感化。','palette':['palette_cloth','palette_rust','palette_leather'],'motivation':'先把人喂饱，再核对每一袋粮；不赞同为复仇毁掉仓库。','arc':'守住营地物资 → 协调补给线 → 在城门接车。','voice':'简短、务实，不长篇解释世界观。','model_asset_id':'model_ahe','model_scope':'仅文字设定，首章可用无动画半身头像或简化营地标记代替。'},
 {'id':'char_zhou','name':'老周','role':'铁匠与旧矿工','faction':'camp','chapters':['ch01','ch02','ch04'],'silhouette':'宽肩，深色皮围裙，卷袖，腰挂小锤；少量银白胡茬，脸不靠复杂细节辨认。','palette':['palette_leather','palette_charcoal','palette_iron'],'motivation':'修好能用的工具，把熟悉的矿道重新连上路。','arc':'修车修剑 → 指出旧矿道 → 修复城门绞盘。','voice':'只说眼前能怎么做，用一句话给出可玩的提示。','model_asset_id':'model_zhou','model_scope':'仅文字设定；首章先用交互点和短台词。'},
 {'id':'char_luoduo','name':'罗铎','role':'封路守备官与最终头目','faction':'blockade','chapters':['ch02','ch03','ch04'],'silhouette':'暗钢胸甲，锈色短披风，宽肩长盾；脸部可见，不戴夸张角盔。','palette':['palette_charcoal','palette_iron','palette_rust'],'motivation':'以保城为由截留粮油，按自身指令分配物资；将道路失控视为权威失效。','arc':'盖章命令与缴获账单先出现 → 城门当面阻拦 → 失去补给和部下支持后投降。','voice':'镇定、命令式，不自称恶人；论点被玩家搬走粮袋和打开城门的行动反驳。','model_asset_id':'model_luoduo','model_scope':'后续章节文字设定，不在首章建模范围。','combat':'长盾冲锋、两段重斩、号令弩兵；只复用近战骨架，新增动作后再做终章。'},
 {'id':'enemy_raider','name':'围路兵','role':'基础近战敌人','faction':'blockade','chapters':['ch01','ch02','ch03','ch04'],'silhouette':'锈红布甲，短刀，裸露前臂，低肩线；与玩家青绿披布明显区分。','palette':['palette_rust','palette_leather','palette_iron'],'motivation':'受命收取路费、看守缴获物；逃跑或倒地退出，不做死亡特写。','model_asset_id':'model_raider','model_scope':'首章静态分件基模与四方向透明图。','combat':'抬手预警后短距离挥击；可被推离窄道、被火逼走。'},
 {'id':'enemy_shield','name':'盾兵','role':'围路兵变体','faction':'blockade','chapters':['ch02','ch03','ch04'],'silhouette':'复用围路兵身体，加宽木盾；低盾时可见攻击前摇。','palette':['palette_rust','palette_wood','palette_iron'],'motivation':'守住窄口和搬运路线。','model_asset_id':'model_shield_variant','model_scope':'计划复用围路兵，不增加新身体或独立职业。','combat':'正面减伤但不能抵挡背击与脚边火；推击可打断抬盾。'},
 {'id':'enemy_archer','name':'弩手','role':'围路兵远程变体','faction':'blockade','chapters':['ch02','ch03','ch04'],'silhouette':'复用围路兵身体，短弩横向轮廓，肩部布片更短。','palette':['palette_rust','palette_wood','palette_iron'],'motivation':'控制高台和桥面。','model_asset_id':'model_archer_variant','model_scope':'后续计划复用围路兵；首章不要求。','combat':'瞄准线提前可见，单发射击后长装填；掩体完全阻挡弹体。'},
 {'id':'boss_roadblock','name':'路障头目','role':'首章木门小头目','faction':'blockade','chapters':['ch01'],'silhouette':'围路兵体型加宽约 15%，双肩皮片，双手短柄铁锤，腰挂门钥匙；不做巨型怪物。','palette':['palette_rust','palette_iron','palette_charcoal'],'motivation':'截住运粮车并把粮油交往城门；只关心眼前差事。','model_asset_id':'model_roadblock_boss','model_scope':'首章独立静态分件基模，允许复用围路兵材质与将来骨架。','combat':'扇形横扫、直线冲撞；半血后增加一次短横扫，不加独立变身阶段。'}
 ]
}

chapters={'schema_version':'1.0.0','project_id':'sword_and_fire','title':'剑与火','status':'preproduction_design_not_implemented','language':'zh-CN',
'canon':{'city':'灰石城','camp':'石桥营地','player_id':'char_player','premise':'边境贸易城的守备以保城为由封路并扣下粮油。行路人从找回一辆粮车开始，经旧矿道和河岸粮仓，最后打开灰石城门，让补给重新到达沿途聚落。','resolution':'罗铎战败投降，守备放行，粮车进入城门；阿禾在路旁分发食物，老周修好绞盘。此事在本篇结束，不以更大的神秘灾难续命。'},
'scope':{'camera':'2.5D','genre':'可存档的连续探索动作小游戏','demo_chapter_ids':['ch01'],'future_chapter_ids':['ch02','ch03','ch04'],'estimated_full_chapter_minutes':[20,40],'estimated_demo_minutes':[20,30],'session_rule':'可在检查点中断并继续；不是每局清空的短局肉鸽。时长均为设计估计，须试玩验证。','prototype_boundary':'现有原型验证连续区域、推击、火、拾取及头目等基础循环；不等同于以下四章已完成。'},
'global_rules':{'branching':'每章三条局部路线连接同一必经目标；可以回访，不产生剧情分支。每条路线都有无消耗的近战或推击解法。','critical_resources':'主线粮车、关键粮袋、钥匙和任务交互点不可烧毁或永久遗失；油可用于捷径但不是通关钥匙。','enemy_limits_estimate':{'active_regular_target':8,'active_regular_peak':12,'simultaneous_bosses':1},'dialogue':'入场与收尾各不超过两句；可跳过，目标与路标仍明确。','loot':'敌人、箱子和唯一奖励均有稳定 ID；首章只提供少量固定奖励，不靠重复刷取推进。','save':{'version':1,'trigger':['进入已解锁检查点','完成主线目标','领取唯一奖励','拾取资源或打开箱子后'],'fields':['chapterId','checkpointId','completedObjectiveIds','defeatedEnemyIds','openedContainerIds','acquiredUniqueRewardIds','openedShortcutIds','inventory','selectedBuildModifierId'],'death':'回最近检查点，恢复生命；已完成目标、已击败敌人和已领物品保留；未击败头目恢复满血，仍存活普通敌人回到出生位置。','atomicity':'先验证交互实体 ID 未结算，再一次性写入奖励与已结算标记；存档迁移按 save version 执行。'}},
'chapters':[]}

def chapter(id,number,title,minutes,summary,areas,goals,routes,enemies,boss,terrain,rewards,cps,unlock,intro,outro,ending,assets):
 return {'id':id,'number':number,'title':title,'status':'demo_planned' if id=='ch01' else 'future_planned','target_minutes_estimate':minutes,'summary':summary,'areas':areas,'objectives':goals,'routes':routes,'enemy_character_ids':enemies,'boss':boss,'terrain_interactions':terrain,'rewards':rewards,'checkpoints':cps,'unlock_after':unlock,'intro_dialogue':intro,'outro_dialogue':outro,'completion':ending,'required_asset_ids':assets}
def goal(id,text,prereq,kind='main'): return {'id':id,'text':text,'prerequisite_objective_ids':prereq,'kind':kind,'persistent':True}
def cp(id,name,area): return {'id':id,'name':name,'area_id':area,'persistent_unlock':True}
def route(id,name,start,end,method,risk,prize):return {'id':id,'name':name,'start_area_id':start,'end_area_id':end,'method':method,'risk':risk,'optional_reward':prize,'rejoins_main_path':True,'required_consumable':None}
def reward(id,name,when,effect):return {'id':id,'name':name,'objective_id':when,'effect':effect,'unique':True}
def line(who,text):return {'character_id':who,'text':text,'skippable':True}

chapters['chapters'].append(chapter('ch01',1,'断路',[20,30],
'石桥营地的口粮只够支撑眼前几天。行路人沿山路找回被扣的粮车，拆掉第一道木门，看到缴获粮油正在运往灰石城。目标从一辆车变成一条路。',
[{'id':'area_ch01_camp','name':'石桥营地','purpose':'安全起点、移动与挥剑、短任务交互'}, {'id':'area_ch01_road','name':'山路转弯','purpose':'找车、学推击与火、三路汇合'}, {'id':'area_ch01_gate','name':'木门路障','purpose':'头目与开门、首章结算'}],
[goal('obj_ch01_01','在石桥营地领取送粮委托',[]),goal('obj_ch01_02','赶开粮车旁围路兵并放下车轴支撑',['obj_ch01_01']),goal('obj_ch01_03','打通通往木门的山路并打开近路',['obj_ch01_02']),goal('obj_ch01_04','击败路障头目并抬起木门横杆',['obj_ch01_03']),goal('obj_ch01_05','将车交给阿禾并查看缴获清单',['obj_ch01_04'])],
[route('route_ch01_front','正面山路','area_ch01_road','area_ch01_gate','连续两组近战，沿路箱子提供掩体；全部可用挥剑与推击解决。','敌人最密，但地面宽。','少量废铁'),route('route_ch01_slope','侧坡高处','area_ch01_road','area_ch01_gate','绕坡走上岩台，从背侧推开守兵；落差用坡道连通，不做跳跃系统。','窄道移动需要留意边缘；玩家受安全边界保护。','包扎布'),route('route_ch01_shed','废棚后路','area_ch01_road','area_ch01_gate','搬开可推箱子，点燃可选油迹逼退守兵；也可破开脆木栏走近战路线。','火区暂时封住小路，要等火熄灭或走侧边。','一份火油')],
['enemy_raider','boss_roadblock'],{'character_id':'boss_roadblock','arena':'木门前开阔空地，左右各一个硬掩体，外侧不设必死落点。','telegraphs':['横扫前举锤并显示扇形约 0.8 秒','冲撞前脚下直线提示约 1 秒'],'actions':['横扫后约 1 秒硬直可近身输出','冲撞撞上固定石墩会短暂失衡','半血后横扫追加一次短击，预警保持可读'],'terrain_solution':'可把油桶推到冲撞路线上；火造成额外压制而非强制破盾。无油仍可闪避后攻击。','adds':'开场不加小兵；首次调优通过后才考虑半血召入最多 2 名围路兵。','reward_id':'reward_ch01_gate_sword'},
[{'id':'interact_ch01_crate','rule':'箱子只能推到网格安全位，不可堵死必经路；重置点将其送回。'}, {'id':'interact_ch01_oil','rule':'油迹可点燃并在约 4 秒后熄灭；首版不让火无限传播。'}, {'id':'interact_ch01_gate','rule':'头目击败后横杆常驻可交互，钥匙不作为可丢弃背包物。'}],
[reward('reward_ch01_flask','油壶','obj_ch01_02','永久解锁投油点火基础动作；不消耗或移除近战能力。'), reward('reward_ch01_modifier','首个战斗改装','obj_ch01_03','在剑路重击与火路省油中选择一个，检查点免费切换。'),reward('reward_ch01_gate_sword','磨好的钢剑','obj_ch01_04','固定小幅近战提升；不替换人物模型。'),reward('reward_ch01_route','矿道线索','obj_ch01_05','解锁第二章入口；试玩版显示后续规划，不跳入未制作场景。')],
[cp('cp_ch01_camp','石桥营地','area_ch01_camp'),cp('cp_ch01_cart','粮车旁','area_ch01_road'),cp('cp_ch01_gate','木门前','area_ch01_gate')],
None,[line('char_ahe','车就在前面的山路上。人和粮，都带回来。'),line('char_player','我先去看路。')],[line('char_zhou','清单上写着旧矿道。车还能走，换条路试试。'),line('char_ahe','先把这车粮卸下。下一趟，我跟上。')],
{'required_objective_ids':['obj_ch01_05'],'next_chapter_id':'ch02','world_change':'营地多出粮袋，山路木门保持开启，粮车移到安全点。'},
['model_player','model_raider','model_roadblock_boss','prop_cart_supply','prop_gate_wood','prop_barricade_wood','prop_crate_supply','prop_barrel_oil','prop_rock_large','prop_checkpoint_banner','fx_fire_patch']))

chapters['chapters'].append(chapter('ch02',2,'旧矿道',[20,35],
'老周认出缴获清单上的旧运矿标记。行路人进入停用矿道，恢复桥边绞盘，找回转运粮油；账页显示这些物资并非外敌抢走，而是按罗铎的命令被截留。',
[{'id':'area_ch02_entrance','name':'矿口工棚','purpose':'安全补给与矿道入口'},{'id':'area_ch02_mine','name':'分岔矿道','purpose':'三路探索与绞盘'},{'id':'area_ch02_bridge','name':'旧矿桥','purpose':'守桥战与运货出口'}],
[goal('obj_ch02_01','从矿口找到旧运货线路',[]),goal('obj_ch02_02','解除绞盘旁路障并接上手柄',['obj_ch02_01']),goal('obj_ch02_03','击退守桥小队并放下矿桥',['obj_ch02_02']),goal('obj_ch02_04','带出补给箱和缴获账页',['obj_ch02_03'])],
[route('route_ch02_track','主轨道','area_ch02_mine','area_ch02_bridge','沿轨道推进，用矿车挡弩箭；推击打断盾兵。','有正面盾兵，但掩体最多。','废铁'),route('route_ch02_ledge','上层检修道','area_ch02_mine','area_ch02_bridge','经坡道到高台，绕到弩手后侧再放下短梯。','路径更窄，单人巡逻更多。','包扎布'),route('route_ch02_storage','侧仓通道','area_ch02_mine','area_ch02_bridge','打开侧仓插销，用火驱散入口守兵或近战清理，推箱穿过。','仓里油桶密集；可不点火。','火油与固定装备箱')],
['enemy_raider','enemy_shield','enemy_archer'],{'character_id':'enemy_shield','arena':'矿桥入口，侧边平台和固定矮墙提供空间。','telegraphs':['盾兵架盾后向前推进','弩手瞄准线约 1 秒后开火'],'actions':['一名强化盾兵与两名弩手组成守桥小队，不新建头目模型','可绕侧面先打弩手，再近身破开阵线'],'terrain_solution':'矿车遮挡弩箭；绞盘在敌人清除后可无限尝试。','adds':'不刷新增援，已击败小队成员保持完成。','reward_id':'reward_ch02_kit'},
[{'id':'interact_ch02_cart','rule':'矿车只沿固定轨道推移；不可把敌人或关键手柄卡进场景。'}, {'id':'interact_ch02_bridge','rule':'矿桥只在交互时下降，不做实时破坏或坍塌模拟。'}, {'id':'interact_ch02_fire','rule':'火在预设区域内有效；不扩散到关键木桥。'}],
[reward('reward_ch02_kit','加固护具','obj_ch02_03','小幅生存提升，并开放第二个改装选择组。'),reward('reward_ch02_ledger','缴获账页','obj_ch02_04','指出河岸粮仓与罗铎签令；解锁第三章。')],
[cp('cp_ch02_entry','矿口工棚','area_ch02_entrance'),cp('cp_ch02_winch','绞盘平台','area_ch02_mine'),cp('cp_ch02_bridge','矿桥入口','area_ch02_bridge')],
'ch01',[line('char_zhou','沿着旧轨道走。桥没坏，绞盘被他们锁住了。'),line('char_player','我把桥放下来。')],[line('char_ahe','账上每一批粮，都盖着罗铎的印。'),line('char_zhou','下一车要从河岸走。那边有他们的总仓。')],
{'required_objective_ids':['obj_ch02_04'],'next_chapter_id':'ch03','world_change':'矿桥保持放下，营地到河岸出现稳定运货路线。'},
['model_player','model_raider','model_shield_variant','model_archer_variant','prop_bridge_plank','prop_crate_supply','prop_barrel_oil','prop_rock_large','prop_checkpoint_banner','fx_fire_patch']))

chapters['chapters'].append(chapter('ch03',3,'河岸粮仓',[20,35],
'粮仓的货正准备全部转进城内。行路人夺回装卸口，放下吊臂，护住关键粮袋；不是烧光敌人的仓库，而是把货完整送回需要它的人手中。罗铎下令关闭城门，迫使众人向城门推进。',
[{'id':'area_ch03_bank','name':'河岸坡道','purpose':'进入仓区与观察火险'},{'id':'area_ch03_storage','name':'仓院货场','purpose':'三路绕行、灭火与装卸'},{'id':'area_ch03_dock','name':'装卸码头','purpose':'货台防守战和补给交接'}],
[goal('obj_ch03_01','找到被扣粮袋并清理仓院入口',[]),goal('obj_ch03_02','开启水槽并放下装卸吊臂',['obj_ch03_01']),goal('obj_ch03_03','清除码头守兵并拉下封锁链',['obj_ch03_02']),goal('obj_ch03_04','标记三处关键粮堆交给营地搬运队',['obj_ch03_03'])],
[route('route_ch03_yard','仓院正门','area_ch03_storage','area_ch03_dock','在宽场上借箱垛掩护推进，先清近战再打弩手。','敌人多，掩体也多。','废铁'),route('route_ch03_river','河边栈道','area_ch03_storage','area_ch03_dock','沿靠水的一侧绕行，通过可推木板搭出短通路。','空间窄但水边能截断火区。','包扎布'),route('route_ch03_loading','装卸后门','area_ch03_storage','area_ch03_dock','先开后门插销，再把可燃杂物推离货道；可点火吸引守兵也可近战潜入方向。','误点油桶会堵路数秒，不会摧毁任务粮食。','火油与固定护具箱')],
['enemy_raider','enemy_shield','enemy_archer'],{'character_id':'enemy_raider','arena':'码头货台，三块掩体围住开链绞盘；水槽旁是无火安全区。','telegraphs':['搬油兵举起油壶后出现落点提示','弩手在高处缓慢瞄准'],'actions':['一名复用围路兵的搬油头领配两名近战与一名弩手','头领投出的油只落在预设区域；打断投掷会使其停手'],'terrain_solution':'开放水槽移除指定火区；可先打头领减少危险，或绕掩体拆掉远程。','adds':'总数固定，不按时间无限刷怪。','reward_id':'reward_ch03_cargo'},
[{'id':'interact_ch03_water','rule':'水槽交互立即清除指定燃烧片区；表现用短水幕而非流体模拟。'}, {'id':'interact_ch03_grain','rule':'关键粮堆不可燃，普通杂物可燃；两者用图标和颜色区分。'}, {'id':'interact_ch03_crane','rule':'吊臂仅切换上升与下降两个状态；无需物理摆动。'}],
[reward('reward_ch03_cargo','稳定补给','obj_ch03_04','解锁第三个改装选择组；战前补给点充足。'),reward('reward_ch03_gate_order','关城命令','obj_ch03_04','解锁第四章；目标明确为开城门而非夺取统治权。')],
[cp('cp_ch03_bank','河岸营火','area_ch03_bank'),cp('cp_ch03_storage','仓院水槽','area_ch03_storage'),cp('cp_ch03_dock','码头入口','area_ch03_dock')],
'ch02',[line('char_ahe','粮袋留着。要烧，就烧挡路的木栏。'),line('char_player','先开水槽，再搬粮。')],[line('char_ahe','这批够沿路的人吃上一阵。'),line('char_player','城门还关着。我们送到门口去。')],
{'required_objective_ids':['obj_ch03_04'],'next_chapter_id':'ch04','world_change':'码头与仓院清空封锁，满载粮车驶向灰石城。'},
['model_player','model_raider','model_shield_variant','model_archer_variant','prop_crate_supply','prop_barrel_oil','prop_bridge_plank','prop_checkpoint_banner','prop_grain_sacks','prop_crane','fx_fire_patch','fx_water_flush']))

chapters['chapters'].append(chapter('ch04',4,'灰石城门',[25,40],
'粮车抵达城门外，罗铎仍以城中安全为由拒绝放行。行路人先拆除外侧封锁，进入绞盘平台，再打败亲自守门的罗铎。守备看见粮食和沿路来的人后停止抵抗，城门重新打开。',
[{'id':'area_ch04_road','name':'城外车道','purpose':'补给和最后准备'},{'id':'area_ch04_wall','name':'城墙外沿','purpose':'三路进城门平台'},{'id':'area_ch04_gate','name':'城门绞盘台','purpose':'罗铎战与开门结局'}],
[goal('obj_ch04_01','清理城外路障并给粮车留出车道',[]),goal('obj_ch04_02','切断两处外侧弩台的封锁',['obj_ch04_01']),goal('obj_ch04_03','到达城门绞盘台并击败罗铎',['obj_ch04_02']),goal('obj_ch04_04','转动绞盘打开城门',['obj_ch04_03']),goal('obj_ch04_05','与阿禾在入城粮车旁交接',['obj_ch04_04'])],
[route('route_ch04_front','城门大道','area_ch04_wall','area_ch04_gate','沿固定路障推进，利用盾兵站位反推并拆开阵型。','正面战斗最密集，路宽易闪避。','最后一箱补给'),route('route_ch04_service','墙侧维修坡道','area_ch04_wall','area_ch04_gate','沿坡道登上侧台，先拔除弩手；打开侧门形成重试近路。','行进距离长，弩线可由石垛阻挡。','固定饰物箱'),route('route_ch04_cargo','货运侧门','area_ch04_wall','area_ch04_gate','经已打通的旧货道进入，推动货车作掩体，破开内侧插销。','转角近战多；无需提前保留火油或特定装备。','少量废铁与火油')],
['enemy_raider','enemy_shield','enemy_archer','char_luoduo'],{'character_id':'char_luoduo','arena':'宽阔绞盘台，左右石垛挡远程；绞盘和关键支架不可破坏。','telegraphs':['长盾冲锋直线约 1 秒预警','两段重斩每段均有明显抬手','号令前指向弩台并出现可读标记'],'actions':['第一阶段盾冲后重斩，侧绕或火迫使其转身','半血后号令两个固定弩位各射一轮，射完可继续近战','冲锋撞上石垛造成短暂硬直；不设瞬移或全屏秒杀'],'terrain_solution':'石垛截断箭线，油迹改变行走区域；任何构筑都能以躲避和近战完成。','adds':'终章至多 2 名弩手，无无限增援；若首轮调优太难改为场景弩箭。','reward_id':'reward_ch04_clear'},
[{'id':'interact_ch04_cover','rule':'石垛既是掩体也是冲锋碰撞物，碰撞轮廓比装饰边缘略大。'}, {'id':'interact_ch04_winch','rule':'罗铎败后自动解除绞盘锁定；玩家亲手开门而非纯过场。'}, {'id':'interact_ch04_return','rule':'结局后可继续当前章节拾取遗漏内容，已获唯一奖励不再生成。'}],
[reward('reward_ch04_clear','道路重开','obj_ch04_05','本篇完成；展示总救回物资与已开路线，不设影响结局的评分惩罚。')],
[cp('cp_ch04_road','城外粮车','area_ch04_road'),cp('cp_ch04_side','城墙侧门','area_ch04_wall'),cp('cp_ch04_arena','绞盘台前','area_ch04_gate')],
'ch03',[line('char_luoduo','城里还没稳下来。粮车留下，人退回去。'),line('char_player','路上的人也要吃饭。开门。')],[line('char_ahe','第一车往南街，第二车回营地。'),line('char_zhou','门修好了。往后，别再让它把路堵住。')],
{'required_objective_ids':['obj_ch04_05'],'next_chapter_id':None,'world_change':'罗铎缴械投降；粮车进城，营地和沿途聚落恢复供应；镜头停在来往的普通人和车。'},
['model_player','model_raider','model_shield_variant','model_archer_variant','model_luoduo','prop_cart_supply','prop_crate_supply','prop_gate_stone','prop_winch','prop_checkpoint_banner','fx_fire_patch']))

palettes=[
('palette_stone','暖灰石','#8B8273',1.0,0,'墙、岩台、台阶；避免与角色同色'),('palette_charcoal','炭灰','#2D2D30',0.85,0,'阴影、护具内衬'),('palette_teal','青绿布','#2C6763',0.95,0,'玩家识别色，面积约 20%'),('palette_rust','锈红布','#87513B',0.95,0,'封路势力布片，不作为血迹'),('palette_fire','火橙','#EF8839',0.5,0,'火焰和危险提示，发光分层'),('palette_leather','旧棕皮','#6B4E36',0.78,0,'皮甲、包带、围裙'),('palette_iron','磨旧铁','#6C7275',0.58,0.6,'剑、锤与边缘磨损'),('palette_cloth','米褐布','#B29B75',0.98,0,'营地衣物、粮袋'),('palette_wood','深棕木','#70513C',0.88,0,'箱、车、门与棚架')]
manifest={'schema_version':'1.0.0','project_id':'sword_and_fire','language':'zh-CN','snapshot_note':'设计清单；制作中资产只有经核对文件与预览后才标记 delivered_static_base。无状态代表已接入引擎。','status_definitions':{'planned':'文字规划，无交付文件','in_production':'已安排制作，未在此清单核验','delivered_static_base':'可打开静态基模或方向图已核验；不代表已有骨骼、动画或游戏接入','integrated_tested':'已进入原型且对应验收通过'},'priorities':{'P0':'首章必需','P1':'首章打磨与复用扩充','P2':'第二至第四章'},'palettes':[{'id':x[0],'name':x[1],'hex':x[2],'roughness_estimate':x[3],'metallic_estimate':x[4],'use':x[5]} for x in palettes],
'budgets_estimate':{'note':'以下为移动端2.5D起始预算，不是TapTap官方限制或已测性能；以目标设备和引擎实测再收紧。','character_triangles':{'player':[1500,3000],'regular_enemy':[800,1800],'boss':[1800,3500]},'prop_triangles':[50,600],'visible_triangles_target_max':60000,'draw_calls_target_max':60,'shared_texture_atlas_px':[1024,1024],'texture_policy':'首版顶点色或共享小图集；不为每个道具建立独立4K贴图。法线与高精贴图后置。','sprite_direction_count_initial':4,'sprite_direction_count_later':8,'sprite_frame_size_px_estimate':[192,192],'sprite_animations_later':['idle','walk','attack','hit','down','cast'],'runtime_target_fps':30,'active_enemies_target':8,'active_enemies_peak':12,'fire_patch_concurrent_target_max':4,'initial_asset_compressed_mb_target_max':10,'chapter_asset_compressed_mb_target_max':20,'memory_mb_soft_target_max':200,'estimated_only':True},'assets':[]}

def asset(id,name,kind,priority,count,reuse,chapters,status='planned',dependencies=None):
 return {'id':id,'name':name,'kind':kind,'priority':priority,'unique_asset_count':count,'status':status,'chapter_ids':chapters,'reuse':reuse,'depends_on_asset_ids':dependencies or [],'file_paths':[],'verified':False}
A=manifest['assets']
for id,name,kind,prio,chs,status,dep in [
('model_player','行路人静态基模','character','P0',['ch01','ch02','ch03','ch04'],'in_production',[]),
('model_raider','围路兵静态基模','character','P0',['ch01','ch02','ch03','ch04'],'in_production',[]),
('model_roadblock_boss','路障头目静态基模','character','P0',['ch01'],'in_production',['model_raider']),
('model_ahe','阿禾','character','P1',['ch01','ch02','ch03','ch04'],'planned',[]),
('model_zhou','老周','character','P1',['ch01','ch02','ch04'],'planned',[]),
('model_shield_variant','盾兵变体','character_variant','P2',['ch02','ch03','ch04'],'planned',['model_raider']),
('model_archer_variant','弩手变体','character_variant','P2',['ch02','ch03','ch04'],'planned',['model_raider']),
('model_luoduo','罗铎','character','P2',['ch04'],'planned',[]),
('prop_barrel_oil','油桶','prop','P0',['ch01','ch02','ch03','ch04'],'in_production',[]),
('prop_crate_supply','补给木箱','prop','P0',['ch01','ch02','ch03','ch04'],'in_production',[]),
('prop_barricade_wood','木路障','prop','P0',['ch01','ch02','ch04'],'in_production',[]),
('prop_gate_wood','首章木门','prop','P0',['ch01'],'in_production',[]),
('prop_cart_supply','运粮车','prop','P0',['ch01','ch03','ch04'],'in_production',[]),
('prop_rock_large','大岩石','prop','P0',['ch01','ch02','ch04'],'in_production',[]),
('prop_bridge_plank','木板短桥','prop','P1',['ch01','ch02','ch03'],'in_production',[]),
('prop_brazier','营火盆','prop','P0',['ch01','ch02','ch03'],'in_production',[]),
('prop_checkpoint_banner','检查点布旗','prop','P0',['ch01','ch02','ch03','ch04'],'in_production',[]),
('prop_loot_bag','掉落物袋','prop','P0',['ch01','ch02','ch03','ch04'],'in_production',[]),
('prop_grain_sacks','关键粮袋组','prop','P2',['ch03','ch04'],'planned',[]),
('prop_crane','装卸吊臂','prop','P2',['ch03'],'planned',[]),
('prop_gate_stone','石城门','prop','P2',['ch04'],'planned',[]),
('prop_winch','绞盘','prop','P2',['ch02','ch04'],'planned',[]),
('fx_fire_patch','有限火区','vfx','P0',['ch01','ch02','ch03','ch04'],'planned',[]),
('fx_hit','命中与推击反馈','vfx','P0',['ch01','ch02','ch03','ch04'],'planned',[]),
('fx_loot','掉落可见提示','vfx','P0',['ch01','ch02','ch03','ch04'],'planned',[]),
('fx_water_flush','水槽灭火','vfx','P2',['ch03'],'planned',[]),
]:
 reuse='全篇共用比例与材质；无需每章重做。' if len(chs)>1 else '只在所属章节使用，优先复用已有材质。'
 A.append(asset(id,name,kind,prio,1,reuse,chs,status,dep))
A.extend([
asset('terrain_demo_kit','首章地形模块组','terrain','P0',6,'平地、坡道、岩壁、低台、路边、棚顶共6件，旋转与缩放复用。',['ch01','ch02','ch03','ch04']),
asset('ui_demo_icons','首章图标组','ui','P0',12,'剑、火、推、生命、油、布、废铁、目标、检查点、箱、返回、继续。',['ch01','ch02','ch03','ch04']),
asset('audio_demo_sfx','首章音效组','audio','P0',10,'脚步2、挥剑1、命中2、推击1、点火1、拾取1、开门1、界面1；需原创或明确授权。',['ch01','ch02','ch03','ch04']),
asset('sprite_demo_pack','首章四方向静态透明图','sprite','P0',12,'3角色×4方向；静态图不是行走或攻击动画。',['ch01'],'in_production',['model_player','model_raider','model_roadblock_boss']),
])
manifest['gameplay_materials']=[
{'id':'mat_iron_scrap','name':'废铁','purpose':'在营地做少量固定强化；首章演示可直接随主线给一次，不开放制作树。','cap_demo_estimate':20,'mandatory_for_progress':False,'source':'一次性箱子、可选路线与任务奖励'},
{'id':'mat_oil','name':'火油','purpose':'补充投油动作；检查点提供基础补给，无油仍可近战通关。','cap_demo_estimate':5,'mandatory_for_progress':False,'source':'补给箱、固定油桶与检查点'},
{'id':'mat_cloth','name':'包扎布','purpose':'在脱战或检查点快速恢复；不叠加复杂药剂系统。','cap_demo_estimate':3,'mandatory_for_progress':False,'source':'营地补给、路边货袋'}]
manifest['count_summary_design']={'character_bases_demo':3,'character_variants_future':2,'npc_or_final_boss_future':3,'prop_slots_demo':10,'prop_slots_future':4,'static_direction_sprite_slots_demo':12,'terrain_modules_demo':6,'ui_icon_slots_demo':12,'audio_sfx_slots_demo':10,'note':'这是设计槽位数量，不是当前交付数量；当前交付统计以 status 与 verified 字段为准。'}

write('characters.json',characters);write('chapters.json',chapters);write('asset-manifest.json',manifest)

source={
 'title':'剑与火 剧情章节与首章制作方案','version':'v1','date':'2026年11月2日','document_purpose':'作为独立开发的首版设计基线，固定完整故事与四章结构，明确首章应该先做什么，以及角色、道具和材料如何复用。正文中的时长、数量和性能均为起始目标，不是已测结果。',
 'decision':'先做一章可以存档、可以从头走到结尾的2.5D动作试玩。故事用找车、开桥、搬粮和开城门来推进；剑与火是同一角色的两种打法，不做多职业和长篇分支剧情。',
 'delivery_boundary':'本版完成剧情与数据定义。现有JS原型只验证连续区域、推击、火、拾取和头目等基础循环；新章节尚未接入。角色和道具处于首批制作阶段，静态基模或方向图交付后仍需绑定、动画、碰撞、引擎接入与实机验收。',
 'navigation':[{'page':1,'topic':'开发边界与体验目标'},{'page':2,'topic':'完整主线与叙事规则'},{'page':3,'topic':'第一章 断路'},{'page':4,'topic':'第二章 旧矿道'},{'page':5,'topic':'第三章 河岸粮仓'},{'page':6,'topic':'第四章 灰石城门'},{'page':7,'topic':'人物与美术识别'},{'page':8,'topic':'剑火成长与游戏材料'},{'page':9,'topic':'首批素材与技术预算'},{'page':10,'topic':'首章任务与验收'}],
 'principles':[
 '爽感来自短前摇、清晰命中停顿、可读击退、掉落马上看见，以及利用地形把一群敌人拆开；不依靠全屏数字或大量按钮。',
 '每章是可保存进度的连续区域，目标约20至40分钟。首章目标20至30分钟，分营地、山路、木门三个衔接区；退出后从已解锁检查点继续，不按短局重开。',
 '全篇只围绕把粮运到人手里这件事。剧情不谈神明、天命或世界末日；角色对白可跳过，跳过后目标仍清楚。',
 '俯视斜角2.5D呈现。角色采用原创的皮革、金属、布料层次和可信装备；镜头距离下首先看清敌我、武器和攻击，不照搬参考游戏的人脸、服装或标志。'],
 'scope_now':['第一章三个连续区、三条局部路线、一个复用式头目','单角色挥剑、推击、投油点火与一次改装选择','三个检查点、稳定ID存档、固定箱子与少量奖励','三名首批战斗角色基模、共享材料、约十个基础道具'],
 'scope_later':['第二至第四章、盾兵与弩手、罗铎战','骨骼绑定与正式动画、八方向扩展、更多音效和地形细节','有限装备差异和最多三个战斗改装槽'],
 'scope_excluded':['联机攻城、开放世界、随机无限词条、宠物养成、职业转职树','分支长篇对话、过场电影、昼夜与天气模拟、复杂制造树','可燃建筑全破坏、真实流体、实时物理桥梁、不断刷新的防守波次'],
 'plot':{
 'opening':'石桥营地等不到运粮车。行路人原本只是受雇护送，接下阿禾的委托，沿山路找车。第一次胜利是把人和粮带回来，不是卷入宏大的预言。',
 'development':'木门处的缴获清单指向旧矿道。老周认出旧轨道，行路人重新放下矿桥，发现粮油正依罗铎的命令被集中到河岸粮仓。此后目标明确为夺回补给线。',
 'turn':'河岸粮仓让“火”不只是伤害：玩家可以烧路障，但要保住粮食，并用水槽清出安全货道。阿禾开始组织搬运，营地不再只是领任务的菜单。',
 'ending':'罗铎关城门，声称只有把粮留在自己手里才能保城。玩家打败他，亲手转动绞盘，粮车入城，也给沿路聚落留粮。罗铎缴械，守备停止抵抗；普通人的来往恢复，故事收束。',
 'environmental_evidence':['首章：断车轴、被划掉目的地的货签、木门上的收缴清单。','第二章：旧矿工记号、重新转动的绞盘、盖着罗铎印记的账页。','第三章：满仓与缺粮营地形成对照；粮袋可保全，杂物可燃。','第四章：城外满载粮车与紧闭城门；战后开门与分粮是可见结果。'],
 'rules':['目标由动作完成，不由读完文本完成；每次交互只给一条明确动词目标。','开场和收尾对白各不超过两句；字幕可跳过，无强制镜头锁定。','三条路线是同一目标的不同战术，不产生互斥剧情或多个结局。','关键粮食和任务交互不可烧毁；失误带来局部战斗压力，不让主线软锁。']},
 'chapters':chapters['chapters'],'characters':characters['characters'],'palettes':manifest['palettes'],
 'builds':{
 'shared_base':'所有玩家共用行路人。开场能挥剑和推击，救回粮车后获得油壶；任何路线和头目都不要求某种构筑或耗材。',
 'sword':{'name':'剑路','style':'贴身拆阵与打断','demo_modifier_id':'build_sword_heavy','demo_modifier':'重击：每次完整连击的末击增强推退，给出明显停顿和音效；不新增按键。','later_modifiers':['破盾：推击对架盾敌人延长硬直','回转：重击小幅扩大侧向范围，不做全屏剑气']},
 'fire':{'name':'火路','style':'压制走位与地形连动','demo_modifier_id':'build_fire_efficient','demo_modifier':'省油：每次基础投油覆盖略宽，使用间隔保持不变；效果受并发火区上限约束。','later_modifiers':['余火：预设火区持续稍长，但同时存在数仍受限','引燃：在指定可燃道具间触发一次有限传播，不无限蔓延']},
 'progression':[
 {'milestone':'开场','unlock':'挥剑与推击','choice':'无构筑锁定'},
 {'milestone':'首章救车','unlock':'油壶与火基础动作','choice':'所有玩家都获得'},
 {'milestone':'首章开近路','unlock':'第一个改装槽','choice':'重击或省油二选一，检查点免费换'},
 {'milestone':'第二章放矿桥','unlock':'第二个改装选择组','choice':'未来实施；同类效果不无限叠加'},
 {'milestone':'第三章运粮','unlock':'第三个改装选择组','choice':'全篇最多三个生效改装'},
 {'milestone':'第四章通关','unlock':'结局与已走路线回看','choice':'不再追加强制刷取的成长门槛'}],
 'equipment':'首章只做固定基础剑和头目奖励剑，外观共用。装备颜色最多普通、精良、稀有三档；未来最多武器、护具、饰物三个部位，不堆随机词条。强化和包扎是补充，不做制作配方树。',
 'materials':manifest['gameplay_materials'],
 'balance':'起始估计：普通兵在几次有效命中内退出；头目约1至2分钟，不靠高血量拖时间。所有具体伤害与持续时间须试玩后调整，优先保留明确的前摇、后摇与退路。'},
 'asset_plan':{'summary':'首批目标是3个战斗角色、各4方向静态图和约10个基础道具；这些是可继续制作的原创基底，不是已完成的动画角色包。营地NPC与终章人物先使用文字设定，避免在玩法稳定前扩大建模。','completion_snapshot':'当前故事数据和人物设定已完成；模型、道具、方向图以清单中的核验状态为准。素材尚未接入现有JS原型。','rows':[
 {'item':'战斗角色','unique':'3','priority':'P0','reuse':'行路人、围路兵、路障头目；后者复用比例和材质'},
 {'item':'静态方向图','unique':'12','priority':'P0','reuse':'3角色乘4方向；不等同于动作帧'},
 {'item':'基础道具','unique':'约10','priority':'P0至P1','reuse':'箱、油桶、路障、木门、粮车、岩石、木板桥、火盆、检查点旗、掉落袋'},
 {'item':'地形模块','unique':'6','priority':'P0','reuse':'平地、坡道、岩壁、低台、路边、棚顶'},
 {'item':'界面图标','unique':'12','priority':'P0','reuse':'共用视觉风格；先保证可读再做描边细节'},
 {'item':'音效','unique':'10','priority':'P0','reuse':'少量脚步、挥剑、命中、火、拾取与开门声音'},
 {'item':'后续角色','unique':'5','priority':'P1至P2','reuse':'阿禾、老周、罗铎，外加盾兵与弩手两个变体'}],
 'technical':manifest['budgets_estimate'],
 'pipeline':'先检查静态模型朝向、比例和透明边缘，再决定主运行路线：预渲染精灵进入现有JS画面，或以后导入2.5D引擎。GLB与可编辑源文件保留复用；未验证引擎导入前不称为即插即用角色。',
 'palette_note':'暖石与炭灰组成场景底色，玩家青绿、敌人锈红、火为橙色。基础表面按木、布、皮、铁共享材质；细小磨损用大色块和少量边缘变化表达，避免移动端噪点。'},
 'implementation':[
 {'id':'task01','task':'冻结首章数据与白盒路线','done':'三个区可连续抵达，三条侧路都汇回木门；禁用第二至第四章入口。','depends':[]},
 {'id':'task02','task':'完成挥剑推击与火反馈','done':'攻击预警可见，推箱不堵路，火在有限区域熄灭；无油也能通关。','depends':['task01']},
 {'id':'task03','task':'实现五个主线目标与检查点','done':'按稳定ID结算；粮车救回、木门打开与营地粮袋变更可见。','depends':['task01']},
 {'id':'task04','task':'实现路障头目与固定掉落','done':'至少两种可读动作，存在后摇；死亡重试不重复发剑。','depends':['task02','task03']},
 {'id':'task05','task':'接入首批原创角色与道具','done':'朝向、脚底落点、遮挡和敌我识别一致；静态图仅作为过渡，正式动作另验。','depends':['task02']},
 {'id':'task06','task':'完成原子存档与恢复测试','done':'刷新或退出后目标、箱子、奖励、检查点保持一致，无丢失无刷取。','depends':['task03','task04']},
 {'id':'task07','task':'触屏与性能实测','done':'在目标手机或平台环境测可读性、输入误触与帧耗时；不以桌面结果替代。','depends':['task05','task06']},
 {'id':'task08','task':'首章试玩后再扩第二章','done':'问题清单中的阻断与软锁清零，爽感和时长基本成立，再复用资源做矿道。','depends':['task07']}],
 'acceptance':[
 {'id':'gate01','name':'可完整通关','test':'从新档到交车结算；三个局部路线分别验证；全程不需要读完对白。'},
 {'id':'gate02','name':'不会软锁','test':'推箱靠墙、油耗尽、重复开门、跳过对白、主线粮食靠近火均不锁死；必要交互可重试。'},
 {'id':'gate03','name':'不会重复奖励','test':'每个检查点退出继续；拾取后立即刷新；头目掉落前后退出；唯一物品最多领取一次。'},
 {'id':'gate04','name':'战斗清楚且有退路','test':'剑路与火路均能无特殊消耗通关；头目预警可区分，硬直可利用，没有不可读的同屏围攻。'},
 {'id':'gate05','name':'素材真实可用','test':'3个基模与约10道具可打开；四方向PNG透明边缘干净；实际动画、碰撞与引擎接入分别标记，不混称完成。'},
 {'id':'gate06','name':'移动端达到初始预算','test':'以目标设备测试30FPS目标、内存与包体；记录设备和数据。当前60次绘制、6万可见三角面等仅为起始估计。'},
 {'id':'gate07','name':'版本范围诚实','test':'试玩只有首章；未来章节标为规划。上架前单独核对平台SDK、存储、包体和素材授权要求。'}],
 'id_contract':'chapters.json固定章节、区域、目标、检查点和奖励ID；characters.json固定角色及模型映射；asset-manifest.json固定素材槽位、状态和文件路径。文案可改，已进入存档的ID不能随意改名。',
 'save_summary':chapters['global_rules']['save'],
 'next_action':'先把第一章做成可通关与可恢复的白盒，随后替换角色和道具。第二至第四章只保留设计与数据，不在首章验收前同时开工。'
}
write('story-source.json',source)
print('Wrote chapters.json, characters.json, asset-manifest.json, story-source.json')

# Reconcile the content snapshot with the actual delivered static asset manifest.
import reconcile_story_assets

import apply_approved_style

import register_additional_studies
