# 剑与火资源基线与区域扩量登记

> **版本状态 2026-11-02 09:42 UTC：用户再次否决区域v2的尺度与过度寻宝定位。** 本文保留的12子区/4宏路、包围盒、20—40/35—60分钟、8新增母项和212计数均是该被否决候选的记录，不是v3获认可愿景、预算或交付。v3须重新以真实地图参考及剧情、战斗、探索共同作用研究；本次不另造尺寸、支线或奖励。单人演示只限制生产批次，不限制世界规模；40永久装备+8消耗符类型保持。

## 既有基线与被否决候选的计数边界

保持的物品基线是**40件永久装备与8类一次性符咒、6套各5候选的2/4件套和4种试玩构筑**。下表是区域扩张前的204项已登记设计基线，不是区域v2当前全量或已完成文件数；规则与物品目录只以[装备与合成](../interactions/equipment-and-crafting.md)为准。代码与既有JSON均未同步，正式角色、正式动作和实机验收通过数仍为0。

| 前版设计基线类别 | 已登记独立设计数 | 去重依据 |
| --- | ---: | --- |
| 角色定义 | 11 | 原6基础+2佣兵变体，加3特色商人；艾妲/布兰复用既有身份，四构筑共用主角 |
| 非装备道具与故事物件/贴花 | 49 | 旧50中基础铁剑移入40永久装备；其他环境、故事、探索物件保留 |
| 永久装备物品设计 | 40 | 16武器=6近战+4弓+4杖+2副手；16护甲=头/身/手/足各4；8首饰=戒指/项链各4 |
| 一次性符咒消耗物设计 | 8 | T01—T08各1类，张数/堆叠/已耗状态是同类输出，不因补给次数重复计设计 |
| 共享地形模块 | 6 | terrain_demo_kit展开；不再加父集合 |
| 通用与训练图标 | 28 | 旧22+弓/杖/符咒/副手4+金币/商人标记2；48类物品缩图不重计 |
| 共享界面设计 | 13 | 原11面板+交易1+四区域分层地图日志1；不按商人数、地图布局、槽或配方重复计页 |
| 特效设计 | 19 | 旧15+玩家箭/杖投射/法术地面/符咒发动4；状态/字形变体不重复计设计 |
| 声音设计 | 30 | 旧25+弓拉放2/杖释放/法术命中/符咒发动共5；27短音+3环境循环 |
| **前版基线小计** | **204** | **区域v2另列8母项形成212候选；完整变体/实例/实施工作量未估，不把204当全量或上限** |

48类物品各自包含独立形体/物品母稿、近景卡、64/128图标与静态掉落输出；多尺寸和同源卡图不另计。套装标识、2/4件状态、品质边框和数值差值属于共享界面/覆盖层；每套5件候选、装备其中2/4件触发，6套成员直接取自40永久装备目录，不另外制造30件，也不是6套新人物。弓、杖、符咒、护甲附件、混搭与逐武器手持的动作/四向输出另列[动画增量](characters-and-animation.md)，**尚未完成帧数、工时或内存预算**。

前版197为装备/消耗符咒基底；按[商人合同](../interactions/merchants-and-trade.md)与[地图逻辑](../story/exploration-map-logic.md)追加3角色、2图标、2界面，共204。5份商人头像属于角色静帧裁切，4区域地图布局属于共享地图界面输出；变体、制图与装配工时另估，不能因为未增独立设计而报零工作量。

## 旧148至204基线的追溯

旧119→130→148记录属于12剑时期，保留为历史，不再称完整装备总量。旧148由58个既有展开设计+90个历史增补组成；其中基础剑原计环境道具，追加11剑原计武器，护符/铜芯/破阵扣3图标仍属训练，不是当前40永久装备或8符咒消耗类型。当前去重重算为：

`148 - 11旧追加剑设计 - 1移出环境的基础剑 + 40永久装备设计 + 8符咒消耗物设计 + 4通用图标 + 4特效 + 5声音 = 197`

`197 + 3特色商人角色 + 2共享界面 + 2通用图标 = 204前版基线`

旧11武器美术ID保留作历史/迁移来源，不与48类当前物品再次相加；3古物/扣图标仍是传承训练设计，不冒称新首饰，也不从通用图标扣除；旧剑转为何种装备只按权威迁移表，不猜测发两份。原首章104、后续44也只是旧快照；物品类型首次发现17/14/11/6，制作验证18/10/10/10，均合计48类但不是张数或同一分组。四构筑试玩配发不等于主线拥有；旧204设计的章节制作包须连同区域v2新增地形/室内/地标/实例与实施重新排期，不拿104冒称本轮首章全量。

旧剑系动作57条、每向430帧、四向1720帧、首章920帧保留为历史基线，不覆盖本轮弓/杖/符/护甲附件增量，也不与旧204种设计或扩区新增设计混加。`story_asset_surrender_pose`是动作末帧状态复用，不独立加设计。

## 已有文件与通过状态

- 参考6张，其中只有原始角色方向获批为美术方向；并非6张正式角色或6张已校准精灵。
- 占位15个GLB：6角色+9道具。33张独立静态PNG：24角色方向帧+9道具图；另2张排版预览，磁盘PNG合计35，不应把预览计为新角色。
- 主角研究3项/2个研究GLB：旧静态结构研究、已被用户拒绝的绑定/材质研究、首张胸像检查失败后停止的第二次静态重做。最后一项无GLB、骨架或动作。15占位+2研究=17个GLB文件，不是17个角色。
- 前版v1图册6PNG+6SVG已交付，但其小尺度被用户否决，不能作为区域v2成品或空间足够的证据；首章v2预览曾展示，但用户于09:42再次否决其尺度与定位；相关总览/预览均非v3获接受交付。图册属于设计/审核输出，不替代可玩关卡、游戏内地图UI或候选母项预算。 不把12个文件直接加为12个新母项。
- 失败研究、纹理、四向静图、动作采样、视频与排版均为衍生证据，不加入204；没有新增获接受角色。详见下方记录及[制作门槛](production-roadmap.md)。

P0优先确保四构筑可判断、关键预警/交互/固定奖励可读，P1做完整动作与打磨，P2用于后章。优先级是生产排序，不更改旧JSON字段；没有通过的项仍是计划或占位。

## 被否决v2的8项母项候选与未估工作

[被否决区域尺度第二版](../maps/regional-scale-v2.md)曾提出每章主线20—40分钟、含可选探索的总游玩35—60分钟为未测试目标，不以延长空跑满足。原18主线obj、12route、12cp、40永久装备+8符类型、5商人及唯一来源保持；原12area是兼容索引，不是地理子区总数。

| 新候选ID | 类别 | 独立候选数 | 母项 | 用途与状态 |
| --- | --- | ---: | --- | --- |
| `terrain_v2_tree_canopy_pine` | 地形母项 | 1 | 松针乔木与树冠层 | 松根林/塔脊等地貌；树干可见、树冠前后层与角色遮挡分别输出；被否决v2候选，未制作/验收 |
| `terrain_v2_tree_canopy_broadleaf` | 地形母项 | 1 | 阔叶乔木与树冠层 | 果园/聚落边界等地貌；冠层透明/淡出、季相材质变体另估；被否决v2候选，未制作/验收 |
| `prop_v2_inn_facade` | 环境母项 | 1 | 驿店与客栈立面 | 聚落街面/门窗/出入口识别；不以一张立面图假装完整室内完成；被否决v2候选，未制作/验收 |
| `prop_v2_watchtower_shell` | 环境母项 | 1 | 瞭望塔壳体 | 塔脊/测绘塔等垂直地标；拆层、楼梯/坡台接口与遮挡另核；被否决v2候选，未制作/验收 |
| `prop_v2_ruined_cellar_arch` | 环境母项 | 1 | 废地窖拱券 | 双入口地窖/废墟室内连接；拱券、前墙淡出与地面根点；被否决v2候选，未制作/验收 |
| `prop_v2_mine_gallery_support` | 环境母项 | 1 | 矿廊支撑与廊段 | 矿道/检验所接合；支撑与可走净宽、射线和转角清楚；被否决v2候选，未制作/验收 |
| `prop_v2_cistern_arch` | 环境母项 | 1 | 蓄水廊拱券 | 河湾蓄水墓廊等干燥内部；水线与可走边界可辨，不要求游泳；被否决v2候选，未制作/验收 |
| `prop_v2_stone_drain_entry` | 环境母项 | 1 | 石砌排水入口 | 干护城壕/墓室入口识别；固定通路而非隐藏付费或符咒门；被否决v2候选，未制作/验收 |

v2留档候选计数为`204旧基线+2地形+6环境=212`，用户已否决该版，不能把212当v3预算。分类仅地形6→8、非装备环境49→55，其余原11角色/40永久装备/8符类型/28图标/13界面/19特效/30声音作为基线复用。首用为松冠/驿馆/瞭望塔/地窖ch01，矿廊ch02，阔叶冠/蓄水廊ch03，排水入口ch04；塔可复用于ch02。8项是候选母稿/模块家族，不是8个完整建筑文件，也不是48子区各造一项；拆分模块、状态/材质变体、实例、完整制图与实施工时尚未估。212不是当前全区域生产工作量已核算或已通过的证明。

| 扩量账项 | 明确范围 | 仍未估算的部分 |
| --- | --- | --- |
| 荒野/聚落/室内 | 四章各12子区、4宏路径，合48子区/16宏路径 | 可走面积、母项拆分/变体、植被遮挡、装配/光照/碰撞 |
| 区域候选母项 | 上表8项，形成212候选索引 | 每项源制作、方向/状态输出、图集/包体、工时与验收 |
| 敌人实例 | 每章4组×2既有模板=8新可选实例；四章32，该候选未提新敌人身体，均可绕行或沿无耗原路退出 | 摆位/巡逻/导航/并发/持久化与性能；复用身体不等于0成本 |
| 地牢匣与材料 | 每章1个铁2匣，共4；32敌各铁1，新增可选铁40 | 独立收据/可达/掉落与反复读档验证；袋/箱图复用不重复计设计 |
| 地图与实施 | 4区域/48子区/16宏路径的分层地图、发现层和回环 | 流式加载、AI/导航、存档/旧点映射、射线、设备与时长测试 |

该被否决版本曾提的新增可选材料仅铁40，金币/符纹/锻芯/装备均0；原主线材料保底66/18/2、金币540及四可选袋60不变。新可选敌/匣与旧主线实例/收据分开，不能把一敌或同一双入口匣算两次；不重发原装备、图纸、圣印、商人库存。真正新角色/敌人原型若后续需要另提案登记，不以本版复用策略作为全局禁增上限。

## 全部既有ID与状态映射

“文件”仅链接本次确实存在的第一份主文件；完整关联见[原资源清单](../../data/story/asset-manifest.json)。文件存在不证明正式风格、绑定、动画或接入通过。

| 既有 ID | 名称／类别 | 当前状态 | 原优先级／章节 | 主文件或来源 | 本规格归属 |
| --- | --- | --- | --- | --- | --- |
| `model_player` | 自由剑士静态基模／character | 占位 | P0／ch01、ch02、ch03、ch04 | [查看](../../assets/blockout/models/model_player.glb) | [规格](characters-and-animation.md) |
| `model_raider` | 灰披佣兵静态基模／character | 占位 | P0／ch01、ch02、ch03、ch04 | [查看](../../assets/blockout/models/model_raider.glb) | [规格](characters-and-animation.md) |
| `model_roadblock_boss` | 灰披队长静态基模／character | 占位 | P0／ch01 | [查看](../../assets/blockout/models/model_roadblock_boss.glb) | [规格](characters-and-animation.md) |
| `model_ahe` | 艾妲／character | 占位 | P1／ch01、ch02、ch03、ch04 | [查看](../../assets/blockout/models/model_ahe.glb) | [规格](characters-and-animation.md) |
| `model_zhou` | 布兰／character | 占位 | P1／ch01、ch02、ch04 | [查看](../../assets/blockout/models/model_zhou.glb) | [规格](characters-and-animation.md) |
| `model_shield_variant` | 盾兵变体／character_variant | 计划 | P2／ch02、ch03、ch04 | 无成品文件 | [规格](characters-and-animation.md) |
| `model_archer_variant` | 弩手变体／character_variant | 计划 | P2／ch02、ch03、ch04 | 无成品文件 | [规格](characters-and-animation.md) |
| `model_luoduo` | 洛德里克／character | 占位 | P2／ch04 | [查看](../../assets/blockout/models/model_luoduo.glb) | [规格](characters-and-animation.md) |
| `prop_barrel_oil` | 油桶／prop | 占位 | P0／ch01、ch02、ch03、ch04 | [查看](../../assets/blockout/props/prop_oil_barrel.glb) | [规格](environment-and-props.md) |
| `prop_crate_supply` | 补给木箱／prop | 占位 | P0／ch01、ch02、ch03、ch04 | [查看](../../assets/blockout/props/prop_supply_crate.glb) | [规格](environment-and-props.md) |
| `prop_barricade_wood` | 木路障／prop | 占位 | P0／ch01、ch02、ch04 | [查看](../../assets/blockout/props/prop_breakable_fence.glb) | [规格](environment-and-props.md) |
| `prop_gate_wood` | 首章木门／prop | 计划 | P0／ch01 | 无成品文件 | [规格](environment-and-props.md) |
| `prop_cart_supply` | 委托货车／prop | 计划 | P0／ch01、ch03、ch04 | 无成品文件 | [规格](environment-and-props.md) |
| `prop_rock_large` | 大岩石／prop | 计划 | P0／ch01、ch02、ch04 | 无成品文件 | [规格](environment-and-props.md) |
| `prop_bridge_plank` | 木板短桥／prop | 占位 | P1／ch01、ch02、ch03 | [查看](../../assets/blockout/props/prop_bridge_segment.glb) | [规格](environment-and-props.md) |
| `prop_brazier` | 营火盆／prop | 占位 | P0／ch01、ch02、ch03 | [查看](../../assets/blockout/props/prop_campfire.glb) | [规格](environment-and-props.md) |
| `prop_checkpoint_banner` | 检查点布旗／prop | 计划 | P0／ch01、ch02、ch03、ch04 | 无成品文件 | [规格](environment-and-props.md) |
| `prop_loot_bag` | 掉落物袋／prop | 计划 | P1／ch01、ch02、ch03、ch04 | 无成品文件 | [规格](environment-and-props.md) |
| `prop_grain_sacks` | 普通粮袋背景组／prop | 计划 | P2／ch03、ch04 | 无成品文件 | [规格](environment-and-props.md) |
| `prop_crane` | 装卸吊臂／prop | 计划 | P2／ch03 | 无成品文件 | [规格](environment-and-props.md) |
| `prop_gate_stone` | 堡内军械库石框栅门／prop | 计划 | P2／ch04 | 无成品文件 | [规格](environment-and-props.md) |
| `prop_winch` | 绞盘／prop | 计划 | P2／ch02、ch04 | 无成品文件 | [规格](environment-and-props.md) |
| `fx_fire_patch` | 有限火区／vfx | 计划 | P0／ch01、ch02、ch03、ch04 | 无成品文件 | [规格](ui-icons-vfx-audio.md) |
| `fx_hit` | 命中与推击反馈／vfx | 计划 | P0／ch01、ch02、ch03、ch04 | 无成品文件 | [规格](ui-icons-vfx-audio.md) |
| `fx_loot` | 掉落可见提示／vfx | 计划 | P0／ch01、ch02、ch03、ch04 | 无成品文件 | [规格](ui-icons-vfx-audio.md) |
| `fx_water_flush` | 水槽灭火／vfx | 计划 | P2／ch03 | 无成品文件 | [规格](ui-icons-vfx-audio.md) |
| `terrain_demo_kit` | 首章地形模块组／terrain | 计划 | P0／ch01、ch02、ch03、ch04 | 无成品文件 | [规格](environment-and-props.md) |
| `ui_demo_icons` | 首章图标组／ui | 计划 | P0／ch01、ch02、ch03、ch04 | 无成品文件 | [规格](ui-icons-vfx-audio.md) |
| `audio_demo_sfx` | 首章音效组／audio | 计划 | P0／ch01、ch02、ch03、ch04 | 无成品文件 | [规格](ui-icons-vfx-audio.md) |
| `sprite_demo_pack` | 六角色四方向静态透明图／sprite | 占位 | P0／ch01 | [查看](../../assets/blockout/sprites/model_player_front_right.png) | [规格](characters-and-animation.md) |
| `prop_stone_wall` | 石墙模块／prop | 占位 | P0／ch01、ch02、ch04 | [查看](../../assets/blockout/props/prop_stone_wall.glb) | [规格](environment-and-props.md) |
| `prop_loot_chest` | 战利品箱／prop | 占位 | P0／ch01、ch02、ch03、ch04 | [查看](../../assets/blockout/props/prop_loot_chest.glb) | [规格](environment-and-props.md) |
| `prop_steel_sword` | 钢剑道具／prop | 占位 | P0／ch01、ch02、ch03、ch04 | [查看](../../assets/blockout/props/prop_steel_sword.glb) | [规格](environment-and-props.md) |
| `prop_wood_shield` | 方木盾道具／prop | 占位 | P1／ch01、ch02、ch03、ch04 | [查看](../../assets/blockout/props/prop_wood_shield.glb) | [规格](environment-and-props.md) |
| `concept_character_direction` | 已选角色美术方向概念图／design_reference | 参考，方向获批；非生产成品 | P0／ch01 | [查看](../../assets/concepts/character-direction-v1.png) | [规格](art-direction.md) |
| `concept_ch01_environment` | 首章场景美术方向概念图／design_reference | 参考 | P0／ch01 | [查看](../../assets/concepts/chapter01-environment-v1.png) | [规格](art-direction.md) |
| `ref_player_four_view_v2` | 高细节主角四向设计参考／design_reference | 参考 | P0／ch01、ch02、ch03、ch04 | [查看](../../assets/concepts/player-four-view-v2.png) | [规格](art-direction.md) |
| `ref_raider_detail_v2` | 灰披佣兵高细节正背面设计参考／design_reference | 参考 | P0／ch01 | [查看](../../assets/concepts/raider-detail-reference-v2.png) | [规格](art-direction.md) |
| `ref_captain_detail_v2` | 灰披队长高细节正背面设计参考／design_reference | 参考 | P0／ch01 | [查看](../../assets/concepts/captain-detail-reference-v2.png) | [规格](art-direction.md) |
| `study_player_refined_mesh` | 主角中等精度结构研究／geometry_study | 结构研究，未获批 | P1／ch01 | [查看](../../assets/studies/player-refined/models/model_player_refined.glb) | [规格](art-direction.md) |

## 新增支持性概念参考

这一行是第6张设计参考，不写入既有40项JSON快照，也不改变旧204项设计基线。

| 参考 ID | 内容 | 状态 | 文件 | 限制 |
| --- | --- | --- | --- | --- |
| `concept_supporting_cast_direction` | 旧阿禾、老周、罗铎同画面方向研究 | 旧版参考；本次未重画；未获用户单独批准；非新身份定稿 | [配角方向参考](../../assets/concepts/supporting-cast-direction-v1.png) | 非模型、非绑定、非动画、非已校准四向图；洛德里克持盔、钢剑未完整展示，需要按角色规格补齐 |

新显示名与旧文件的关系：`model_ahe` 原阿禾→艾妲，`model_zhou` 原老周→布兰，`model_luoduo` 原罗铎→洛德里克；其余人物按[角色表](characters-and-animation.md)。这些配角文件仍是旧占位，复用的是接口与材质方向，不是已达新身份的正式造型。2026-11-02新增研究均在独立studies目录，没有替换这些旧图或占位；第二次静态重做也未形成可接受角色。

## 新增主角技术研究（不增角色定义，不计正式通过）

此表独立于上方40个既有ID快照，未改旧 `asset-manifest.json`。与旧 `study_player_refined_mesh` 合计**3项研究/2个研究GLB**；第二次静态重做只有blend与失败胸像、没有GLB。15个占位GLB加2个研究GLB仍是17个GLB文件，不是17个角色或17项正式成品。失败研究和动作采样不增加生产设计或通过数量。

| 研究 ID | 内容 | 实际文件/衍生输出 | 当前状态 | 来源与证据 |
| --- | --- | --- | --- | --- |
| `hero_g1_motion_study` | 同一自由剑士的造型、UV材质和21骨架待机研究 | 1个GLB、1个blend、20张源纹理；四向首帧+单方向8采样共11张不同PNG；1个2秒源待机，预览MP4重复为8秒 | **用户拒绝／不合格，当前路线停止**；非正式精细角色；walk/sword、完整关节蒙皮、图集和游戏接入未完成 | [研究说明/实际对照/技术验证](../../assets/studies/hero-g1-motion-study/README.md) |
| `hero_static_bust_feasibility` | 第二次独立主角静态重做的胸像可行性研究 | 1个blend、1张820×1000实际渲染，无GLB、骨架或动作 | **首张可行性检查失败，生产停止**；眼眶、面部、发型、披巾与肩袖结构未通过，不扩做全身 | [失败记录与可重现证据](../../assets/studies/hero-static-remake/README.md) |

纹理、每向静帧、动作采样、预览排版和视频不各算一个角色或独立生产设计；“有21骨架”也不代表完整动作通过。胸腰/裤膝/披布有部分渐变权重，大部分装备/衣袖单骨权重；样板风格仍偏程序化，正式通过数保持0。

### 文件名别名不是新增设计

| 逻辑资源ID | 已有源文件ID／路径尾名 | 说明 |
| --- | --- | --- |
| `prop_barrel_oil` | `prop_oil_barrel` | 同一个油桶设计 |
| `prop_crate_supply` | `prop_supply_crate` | 同一个木箱设计 |
| `prop_barricade_wood` | `prop_breakable_fence` | 同一个木栏占位 |
| `prop_bridge_plank` | `prop_bridge_segment` | 同一个桥段占位 |
| `prop_brazier` | `prop_campfire` | 同一营火占位，正式外观按安全营火规格重做 |
| `study_player_refined_mesh` | `model_player_refined` | 主角额外结构研究，不是第9个角色 |
| `sprite_demo_pack` | 6角色×4方向静态PNG | 24张衍生静帧，已经属于六角色；不再加24个人物 |

旧清单中的 `delivered_blockout` 不提升为 `integrated_tested`。`verified:true` 只证明旧静态文件的对应检查，不证明质量目标、动作或游戏性能。

## 集合子项展开

以下子ID是本规格的稳定设计键，暂未写入旧JSON。父集合只保留管理关系、不再多算一个生产设计。

| 子 ID | 所属集合 | 独立数量 | 状态 | 规格 |
| --- | --- | ---: | --- | --- |
| `terrain_ground_dirt` | `terrain_demo_kit` | 1 | 计划 | [规格](environment-and-props.md) |
| `terrain_ground_stone` | `terrain_demo_kit` | 1 | 计划 | [规格](environment-and-props.md) |
| `terrain_cliff` | `terrain_demo_kit` | 1 | 计划 | [规格](environment-and-props.md) |
| `terrain_ramp` | `terrain_demo_kit` | 1 | 计划 | [规格](environment-and-props.md) |
| `terrain_water_bank` | `terrain_demo_kit` | 1 | 计划 | [规格](environment-and-props.md) |
| `terrain_vegetation` | `terrain_demo_kit` | 1 | 计划 | [规格](environment-and-props.md) |
| `ui_icon_sword` | `ui_demo_icons` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `ui_icon_oil` | `ui_demo_icons` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `ui_icon_push` | `ui_demo_icons` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `ui_icon_dodge` | `ui_demo_icons` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `ui_icon_interact` | `ui_demo_icons` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `ui_icon_inventory` | `ui_demo_icons` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `ui_icon_cloth` | `ui_demo_icons` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `ui_icon_scrap` | `ui_demo_icons` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `ui_icon_checkpoint` | `ui_demo_icons` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `ui_icon_objective` | `ui_demo_icons` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `ui_icon_loot` | `ui_demo_icons` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `ui_icon_pause` | `ui_demo_icons` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `sfx_sword_swing` | `audio_demo_sfx` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `sfx_hit_body` | `audio_demo_sfx` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `sfx_hit_metal` | `audio_demo_sfx` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `sfx_push` | `audio_demo_sfx` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `sfx_wood_break` | `audio_demo_sfx` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `sfx_fire_ignite` | `audio_demo_sfx` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `sfx_fire_loop` | `audio_demo_sfx` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `sfx_loot_pickup` | `audio_demo_sfx` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `sfx_interact_confirm` | `audio_demo_sfx` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |
| `sfx_step_dirt` | `audio_demo_sfx` | 1 | 计划 | [规格](ui-icons-vfx-audio.md) |

## 历史增补ID索引与当前复用

本节保留12剑时期90个增补ID作为历史索引，均未因更名成为成品。除11个`weapon_art_*`作为历史来源转入48类物品映射外，其余79个仍在前版基线中；这90行不得整体再加旧204基线或区域扩量账。每项外观、动作/状态与验收见对应规格；旧外观不适合新物品时必须重做，不以ID别名当成质量通过。

| 提案 ID | 类别 | 数量 | 首用／优先级 | 复用与规格 |
| --- | --- | ---: | --- | --- |
| `prop_cart_axle_support` | 小型道具/附件 | 1 | ch01／P0 | [完整规格](environment-and-props.md) |
| `prop_latch` | 小型道具/附件 | 1 | ch01／P0 | [完整规格](environment-and-props.md) |
| `prop_camp_canopy` | 小型道具/附件 | 1 | ch01／P0 | [完整规格](environment-and-props.md) |
| `prop_smith_station` | 小型道具/附件 | 1 | ch01／P0 | [完整规格](environment-and-props.md) |
| `prop_club` | 小型道具/附件 | 1 | ch01／P0 | [完整规格](environment-and-props.md) |
| `prop_round_shield` | 小型道具/附件 | 1 | ch01／P0 | [完整规格](environment-and-props.md) |
| `prop_hammer` | 小型道具/附件 | 1 | ch01／P0 | [完整规格](environment-and-props.md) |
| `prop_oil_flask` | 小型道具/附件 | 1 | ch01／P0 | [完整规格](environment-and-props.md) |
| `prop_mine_cart` | 小型道具/附件 | 1 | ch02／P2 | [完整规格](environment-and-props.md) |
| `prop_rail_track` | 小型道具/附件 | 1 | ch02／P2 | [完整规格](environment-and-props.md) |
| `prop_winch_handle` | 小型道具/附件 | 1 | ch02／P2 | [完整规格](environment-and-props.md) |
| `prop_short_ladder` | 小型道具/附件 | 1 | ch02／P2 | [完整规格](environment-and-props.md) |
| `prop_crossbow` | 小型道具/附件 | 1 | ch02／P2 | [完整规格](environment-and-props.md) |
| `prop_bolt` | 小型道具/附件 | 1 | ch02／P2 | [完整规格](environment-and-props.md) |
| `prop_water_trough` | 小型道具 | 1 | ch03／P2 | [完整规格](environment-and-props.md) |
| `prop_blockade_chain` | 小型道具 | 1 | ch03／P2 | [完整规格](environment-and-props.md) |
| `prop_dry_debris` | 小型道具 | 1 | ch03／P2 | [完整规格](environment-and-props.md) |
| `story_asset_cargo_tags` | 故事物件/贴花 | 1 | ch01／P0 | [完整规格](environment-and-props.md) |
| `story_asset_order_papers` | 故事物件/贴花 | 1 | ch01／P0 | [完整规格](environment-and-props.md) |
| `story_asset_grain_covers` | 故事物件/贴花 | 1 | ch01／P0 | [完整规格](environment-and-props.md) |
| `story_asset_signpost_states` | 故事物件 | 1 | ch01可选／P1 | [完整规格](environment-and-props.md) |
| `story_asset_mine_marks` | 故事贴花 | 1 | ch02／P2 | [完整规格](environment-and-props.md) |
| `ui_icon_grain` | 图标 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `ui_icon_ledger` | 图标 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `ui_icon_armor` | 图标 | 1 | ch02／P2 | [完整规格](ui-icons-vfx-audio.md) |
| `ui_icon_water` | 图标 | 1 | ch03／P2 | [完整规格](ui-icons-vfx-audio.md) |
| `ui_hud` | 界面设计 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `ui_action_controls` | 界面设计 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `ui_interact_prompt` | 界面设计 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `ui_dialogue` | 界面设计 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `ui_inventory_gear` | 界面设计 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `ui_build_select` | 界面设计 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `ui_pause_settings` | 界面设计 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `ui_chapter_summary` | 界面设计 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `ui_status_overlay` | 界面设计 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `fx_sword_arc` | 特效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `fx_oil_throw` | 特效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `fx_wood_break` | 特效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `fx_telegraph_sector` | 特效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `fx_telegraph_line` | 特效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `fx_telegraph_drop` | 特效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `fx_interaction_focus` | 特效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `fx_checkpoint` | 特效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `fx_move_dust` | 特效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `fx_shield_block` | 特效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `fx_contact_shadow` | 特效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `sfx_step_stone` | 音效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `sfx_step_wood` | 音效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `sfx_oil_splash` | 音效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `sfx_gate_heavy` | 音效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `sfx_ui_click` | 音效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `sfx_ui_back` | 音效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `sfx_ui_error` | 音效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `sfx_checkpoint` | 音效 | 1 | ch01／P0 | [完整规格](ui-icons-vfx-audio.md) |
| `sfx_crossbow_shoot` | 音效 | 1 | ch02／P2 | [完整规格](ui-icons-vfx-audio.md) |
| `sfx_bolt_impact` | 音效 | 1 | ch02／P2 | [完整规格](ui-icons-vfx-audio.md) |
| `sfx_mechanism_move` | 音效 | 1 | ch02／P2 | [完整规格](ui-icons-vfx-audio.md) |
| `sfx_water_release` | 音效 | 1 | ch03／P2 | [完整规格](ui-icons-vfx-audio.md) |
| `amb_camp_wind` | 环境循环 | 1 | ch01／P1 | [完整规格](ui-icons-vfx-audio.md) |
| `amb_river` | 环境循环 | 1 | ch01／P1 | [完整规格](ui-icons-vfx-audio.md) |
| `amb_mine_air` | 环境循环 | 1 | ch02／P2 | [完整规格](ui-icons-vfx-audio.md) |
| `prop_reliquary_shell` | 遗物道具 | 1 | ch01／P0 | [旧骑士宝匣与状态](environment-and-props.md) |
| `prop_stag_seal` | 遗物道具 | 1 | ch03／P2 | [鹿角圣印](environment-and-props.md) |
| `prop_relic_case` | 遗物道具 | 1 | ch03／P2 | [沉钟宝匣内匣](environment-and-props.md) |
| `prop_oath_scroll_case` | 遗物道具 | 1 | ch03／P2 | [誓约卷筒](environment-and-props.md) |
| `prop_chapel_vessels` | 遗物道具组 | 1 | ch03／P2 | [礼拜器物](environment-and-props.md) |
| `story_asset_oath_relief` | 遗址贴花/浮雕 | 1 | ch02／P2 | [旧骑士团浮雕](environment-and-props.md) |
| `prop_gate_seal_socket` | 藏宝线索附件 | 1 | ch04／P2 | [藏宝铭牌座](environment-and-props.md) |
| `ui_icon_relic` | 图标 | 1 | ch01／P0 | [遗物标记](ui-icons-vfx-audio.md) |
| `ui_icon_oath_charm` | 装备卡图标 | 1 | ch03／P2 | [守誓护符](ui-icons-vfx-audio.md) |
| `ui_icon_ember_core` | 装备卡图标 | 1 | ch03／P2 | [余烬铜芯](ui-icons-vfx-audio.md) |
| `ui_icon_breach_buckle` | 装备卡图标 | 1 | ch04／P2 | [破阵扣](ui-icons-vfx-audio.md) |
| `weapon_art_reforged_traveler` | 武器物品设计 | 1 | ch01／P0 | [重铸旅剑](environment-and-props.md) |
| `weapon_art_oathmark_short` | 武器物品设计 | 1 | ch01／P0 | [誓痕短剑](environment-and-props.md) |
| `weapon_art_ember_steel` | 武器物品设计 | 1 | ch01／P0 | [余烬钢剑](environment-and-props.md) |
| `weapon_art_bridge_warden` | 武器物品设计 | 1 | ch02／P2 | [守桥卫剑](environment-and-props.md) |
| `weapon_art_mine_return` | 武器物品设计 | 1 | ch02／P2 | [矿道回锋剑](environment-and-props.md) |
| `weapon_art_thin_flame` | 武器物品设计 | 1 | ch03／P2 | [细焰导剑](environment-and-props.md) |
| `weapon_art_ash_hunter` | 武器物品设计 | 1 | ch03／P2 | [灰烬猎手剑](environment-and-props.md) |
| `weapon_art_patrol_light` | 武器物品设计 | 1 | ch03／P2 | [巡路轻锋](environment-and-props.md) |
| `weapon_art_starforge_heavy` | 武器物品设计 | 1 | ch04／P2 | [星炉重剑](environment-and-props.md) |
| `weapon_art_gatekeeper` | 武器物品设计 | 1 | ch04／P2 | [守门者长剑](environment-and-props.md) |
| `weapon_art_oathfire` | 武器物品设计 | 1 | ch04／P2 | [誓火长剑](environment-and-props.md) |
| `ui_icon_rune_shard` | 材料图标 | 1 | ch02／P2 | [符纹碎片](ui-icons-vfx-audio.md) |
| `ui_icon_forge_core` | 材料图标 | 1 | ch03／P2 | [锻造芯](ui-icons-vfx-audio.md) |
| `ui_crafting_workbench` | 界面设计 | 1 | ch01／P0 | [合成与分解](ui-icons-vfx-audio.md) |
| `prop_sunken_bell` | 地标道具 | 1 | ch03／P2 | [半陷泥中的断钟](environment-and-props.md) |
| `design_asset_oath_cache_panel` | 探索道具 | 1 | ch01／P0 | [隐匣背板与插销](environment-and-props.md) |
| `design_asset_twin_nail_mark` | 探索贴花 | 1 | ch01／P0 | [双钉记号](environment-and-props.md) |
| `design_ui_replay_panel` | 界面设计 | 1 | ch01／P1 | [复演入口与结算](ui-icons-vfx-audio.md) |

## 全装备新增共享资源

下表13个ID均为计划，无新图像、动作或声音交付；是装备/符咒版的13项共享增量；商人另加7项见下表，当前分类总账为28图标/13界面/19特效/30声音。名称表示制作任务，不表示已接入。

| 新设计ID | 类别 | 数量 | 首用与规格 |
| --- | --- | ---: | --- |
| `ui_icon_bow` | 通用图标 | 1 | 四构筑试玩；[规格](ui-icons-vfx-audio.md) |
| `ui_icon_staff` | 通用图标 | 1 | 四构筑试玩；[规格](ui-icons-vfx-audio.md) |
| `ui_icon_talisman` | 通用图标 | 1 | 四构筑试玩；[规格](ui-icons-vfx-audio.md) |
| `ui_icon_offhand` | 通用图标 | 1 | 四构筑试玩；[规格](ui-icons-vfx-audio.md) |
| `fx_player_arrow` | 特效 | 1 | 四构筑试玩；[规格](ui-icons-vfx-audio.md) |
| `fx_staff_projectile` | 特效 | 1 | 四构筑试玩；[规格](ui-icons-vfx-audio.md) |
| `fx_spell_ground` | 特效 | 1 | 四构筑试玩；[规格](ui-icons-vfx-audio.md) |
| `fx_talisman_invoke` | 特效 | 1 | 四构筑试玩；[规格](ui-icons-vfx-audio.md) |
| `sfx_player_bow_draw` | 短音效 | 1 | 四构筑试玩；[规格](ui-icons-vfx-audio.md) |
| `sfx_player_bow_release` | 短音效 | 1 | 四构筑试玩；[规格](ui-icons-vfx-audio.md) |
| `sfx_staff_release` | 短音效 | 1 | 四构筑试玩；[规格](ui-icons-vfx-audio.md) |
| `sfx_spell_impact` | 短音效 | 1 | 四构筑试玩；[规格](ui-icons-vfx-audio.md) |
| `sfx_talisman_invoke` | 短音效 | 1 | 四构筑试玩；[规格](ui-icons-vfx-audio.md) |

## 商人地图追加的7个设计

商人玩法与逻辑键见[商人合同](../interactions/merchants-and-trade.md)，以下是美术独立设计键；本轮没有写入旧资源JSON。5商人只有3新角色，艾妲/布兰原ID继续复用。

| 新设计ID | 类别 | 数量 | 范围与状态 |
| --- | --- | ---: | --- |
| `model_merchant_reysa` | 角色定义 | 1 | 猎商蕾萨，`design_merchant_leisa`；计划，无模型/绑定/动作成品 |
| `model_merchant_morren` | 角色定义 | 1 | 符印商墨伦，`design_merchant_moren`；计划，无模型/绑定/动作成品 |
| `model_merchant_navi` | 角色定义 | 1 | 灯油古物商娜薇，`design_merchant_navi`；计划，无模型/绑定/动作成品 |
| `ui_merchant_trade` | 共享界面 | 1 | 五商人共享买卖与事务状态；计划 |
| `ui_region_map_journal` | 共享界面 | 1 | 四区域分层地图日志；4布局/状态输出与制图工时另估；计划 |
| `ui_icon_coin` | 通用图标 | 1 | 第6资源金币，钱包/价格共用；计划 |
| `ui_icon_merchant` | 通用图标 | 1 | 五商人及地图点共用；计划 |

该轮基线由197增至204，不包括本轮区域扩张。艾妲`design_merchant_aida`/`model_ahe`、布兰`design_merchant_bran`/`model_zhou`是原角色复用。商人肖像裁切不加5项，3摊位小组合与4钱袋复用既有母资产、另计装配工时，地图4布局不加4个独立界面，数量/库存/发现状态不每态重计；同时必须记录各输出实际工作量。交易音效复用旧短音，不加专属音库；货架/摊位复用棚、砧、箱、旧纸张与物品图，非装备道具49、地形6仅是该轮基线；区域v2的新室内、地标和地形需求另列独立设计/状态/实例与实施预算，不能继续宣称49和6覆盖扩张后的四区。

## 当前40件装备和8类符咒设计与历史图像别名

[40件装备与8类符咒外观表](environment-and-props.md)逐件登记玩法ID、物品设计键、家族/槽位和独立形体。W01基础旅人铁剑继续使用`prop_steel_sword`为设计键，其他47件以`equipment_art_`前缀登记；这些是48类物品设计，不是48个新增文件。旧`weapon_art_*`按权威迁移映射成为物品的历史设计来源，不能同时作为另一件可获得装备。3旧古物/扣图标仍表示训练；新戒指、项链和W16法器均为永久装备，T01—T08为消耗物，均须独立形体，不能混用剧情铜芯。

### 不计新增独立设计的衍生接口

| ID或用途 | 基础资源 | 状态/复用说明 |
| --- | --- | --- |
| `story_asset_surrender_pose` | `model_roadblock_boss`、`model_luoduo` | 头目down末帧清醒缴械坐姿，洛德里克surrender末帧；保持非敌对，无额外角色/动作帧 |
| 教学木桩 | `prop_barricade_wood`竖桩构件 | 无掉落，不新造人形假人 |
| 守桥铠卫／灰烬掠夺者 | `model_shield_variant`／`model_raider` | 两个小Boss复用身体与招式，装备油壶复用；短头目条和材质区别，不新增角色 |
| 外弩台／内弩口 | 木桥板、石墙、棚支架、`model_archer_variant` | 不新增固定巨弩；两种位置和状态明确区别 |
| 复位牌／安全掉落锚点 | `ui_icon_interact`与基础箭头 | 逻辑点位不制作实体模型 |
| 装备奖励与旧整备 | 旧通用图标与卡框可复用；48类物品各有独立母稿 | 不能以通用图标代替完整物品设计；身体附件/动作另预算 |
| 肖像、故事对白小图 | 已通过角色静帧裁切 | 不独立绘制第二套头像 |
| 明暗/选中/冷却/稀有度 | 通用覆盖层、文本、形状 | 不按每状态重复增加独立图标数 |

## 游戏材料与奖励表现

| 已有游戏ID | 资源映射 | 边界 |
| --- | --- | --- |
| `design_res_gold` | `ui_icon_coin` + 复用小掉落袋 | 第6资源，容量9999；主线540与四独立15钱袋分收据，不是旧6藏点补偿；不增世界金币模型 |
| `mat_iron_scrap` | `ui_icon_scrap` + `prop_loot_bag` | 资源数量，非一件新铁块模型 |
| `mat_oil` | `ui_icon_oil` + `prop_oil_flask` | 包含检查点补给，不能要求留油才能通关 |
| `mat_cloth` | `ui_icon_cloth` + `prop_loot_bag` | 包扎补给，不用于造剑 |
| `design_res_rune_shard` | `ui_icon_rune_shard` + `prop_loot_bag` | 后章符纹碎片，容量40，不新增世界矿石模型 |
| `design_res_forge_core` | `ui_icon_forge_core` + `prop_loot_bag` | 后章锻造芯，容量8，不能与余烬铜芯训练混为一种物品 |
| `reward_ch01_flask` | 油壶道具/图标、短解锁卡 | 解锁动作，不做第二套火法身体 |
| `reward_ch01_modifier` | 旧剑/油图标与整备卡框可复用 | 奖励键保留，仍开第一组传承训练；训练独立1槽，与9槽合法永久装备/套装可共存；双符快捷栏不计套数，不重开全局单效果限制 |
| `reward_ch01_gate_sword` | W02余烬钢剑：`equipment_art_w02`、双环、主手槽 | 仍在抬杆目标完成时唯一授予；不叠加旧永久+3 |
| `reward_ch01_route` | 纸张/账页图标、下一章入口提示 | 试玩版不跳进未完成场景 |
| `reward_ch02_kit` | A05旧誓锁甲：`equipment_art_a05`与身体槽 | 真实二章放桥取得；最大生命+15来自穿戴，旧奖励永久+15一次迁移扣除、不治疗 |
| `reward_ch02_ledger` | 共用文书底图+章节文字 | 关键证据不可丢弃 |
| `reward_ch03_cargo` | 沉钟宝匣、J05余灯坠、第三组训练与护符/铜芯互斥近景选择 | 历史ID保留；护符/铜芯仍解锁训练而非新符咒/首饰；J05单独领取；唯一领取 |
| `reward_ch03_gate_order` | 堡库清单/纸张变体 | 指向下层军械宝库，不是治理城民通行的命令 |
| `reward_ch04_clear` | 库门开态、小宝龛主箱、W06`equipment_art_w06` | 主箱唯一授予守门者誓剑并完成故事，不自动换装；旧永久剑伤增量清除 |
| `design_reward_ch01_oath_sword` | W08逐风枝弓：`equipment_art_w08` | 原隐匣主动领取，旧收据名保留，玩家看见弓 |
| `design_reward_ch02_bridge_weapon` | W03守桥钉锤：`equipment_art_w03` | 与放桥/A05同事务但各自记装备条目；旧剑美术ID仅历史来源 |
| `design_reward_ch03_cinder_weapon` | W10雷枝猎弓：`equipment_art_w10` | 与第三次点验同事务，J05/训练各记条目，不增第四次必点 |
| `design_reward_ch04_oathfire_sword` | T08葬誓长卷：`equipment_art_t08`+W06誓火外观 | 主箱后可选侧格；不复制W06、不加第49件，遗漏不影响通关 |

40永久装备+8符咒消耗类型、9装备槽+2快捷栏、品质、固定属性/词条、6套2/4件效果及配方按[装备与合成](../interactions/equipment-and-crafting.md)统一；合成是静态菜单，弓/杖/符的主动动作另列，近景卡不是角色动画。断钟与探索追加资源见[探索与复演](../interactions/exploration-and-replay.md)。

后章侧箱按装备权威表提供能立即试用的正式物品/整备，并与Boss开放内容去重；旧“9候选/8卡/全局1槽”是历史限制，不再代表当前配装。破阵扣、护符与铜芯仍是3份训练图设计，不在48类物品目录，也不能充当新戒指、项链或符咒；9训练候选/本档8/启用1只约束训练栏，与合法装备/套装共同生效。本轮不改装备目录，也不以旧11角色表作为区域角色全局上限；原遭遇可复用身体，确需新角色/敌人原型的提案须由区域规划明确后另登记，尚不当成成品。护甲附件与不同武器家族表现仍是必需的未估制作依赖。

## 资产记录与交付合同

每个进入制作的ID记录：显示名、类别、角色/章节/目标依赖、独立设计数、源文件、输出文件列表、状态、作者/来源、许可依据、版本、尺寸/帧数/方向、pivot、时序/状态事件、图集页/内存、验收截图/视频、审核日期及未通过项。计划文件路径可以写“拟”，不得用不存在的路径假装交付。

当前源文件保存在 `source-art/blockout/` 与 `source-art/player-refined/`，旧成品检查在 `assets/blockout/` 和 `assets/studies/player-refined/`。正式生产将另建清楚的目录与版本，保留占位来源，不覆盖获批参考或把旧文件改名“final”冒充成品。

扩区新增设计必须对应区域规划中的荒野/聚落/室内、地标或遭遇需求，说明是否复用、独立设计/变体/实例数、图集/环境声音、哪个阶段制作与实施成本；旧204不是禁止扩量的上限。没有故事或规则需求的纯装饰先不做。制作顺序与每道验收门见[production-roadmap.md](production-roadmap.md)。
