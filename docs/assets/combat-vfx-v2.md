# 第一章战斗特效 v2

2026-11-08 最新材质与设计稿对齐见 [战斗特效 v3](combat-vfx-v3.md)。本页保留早期接线和历史迭代；当前默认包与实机对比以 v3 记录为准。

2026-11-08 后续补齐[完整动作衔接](action-sequence-v1.md)：人物抬手、挥砍/施法、发射端、连段及收势同步；多箭与多拍雷法保持角色动作到末拍后完整后摇。当前连续实机证据以该记录为准。

2026-11-08：已按[四系逐级特效v2](../design/skill-vfx-v2.md)接入30技能/150阶的原生运行表现，奥术暂撤、冰系退出。WAR按本次明确反馈恢复近身刃弧；BOW保留首击后分裂方向，火雷采用真实范围、限额目标与接触事件。[四系强化概念板](../../source-art/skills/pure-skills-v2/README.md)仅为美术参考，不是游戏截图，也不代表150阶已逐项通过美术验收。

本轮由 `Effects.ts` 转发权威事件，`NativeSkillVfx.ts` 只观察 `GameSession` 弹体、接触和状态，`VfxAssets.ts` 保留 Kenney CC0 基础遮罩，并接入独立来源登记的生产火舌RGBA。引擎为 Cocos Creator 3.8.8；使用原生 ParticleSystem、Burst、CurveRange、ColorOvertimeModule、SizeOvertimeModule 与 Line，没有新增运行依赖、粒子引擎或着色器，没有把概念图铺到地面。新增火舌由内置云端image_gen生成，原始图/提示词/来源与运行审阅分别记录在[fire-particle-v1](../../source-art/skills/pure-skills-v2/fire-particle-v1/provenance.json)；这张资产不冒充Kenney CC0素材。

## 近战与设计稿对齐修订（2026-11-08）

用户明确要求“破军战技也改回近战”。WAR_01/05已从远程弹体改为角色身前的近战扇形，WAR_02实际沿碰撞路径突进，到真实停止点交叉斩，WAR_04恢复短距圆盘落刃。预瞄、判伤、镜头和多段武器动作同步调整；取消后不再补出剩余近身刀。范围、数据覆盖、旧存档兼容及现有95项检查见[近战恢复记录](../design/melee-restoration-v1.md)。

近战以原v1近身刃弧为参考，使用`MeleeBladeSurfaces`实体刃面、暗背、冷白锋与窄金背边；普通剑普攻另有1.45m短扫。弓术保留真实箭杆、首击后子箭及已飞短尾；雷电沿真实连接显示不规则冷白电芯/电蓝边、薄晕和短叉。火焰由云端OpenAI image_gen制作[四相体积火材质](../../source-art/skills/pure-skills-v2/fire-volume-v2/README.md)，原始图、[完整提示词](../../source-art/skills/pure-skills-v2/fire-volume-v2/prompt.txt)、必要参考局部及Pillow裁切记录分别保存；`SkillFireSprites`按共同脚锚呈现压缩、爆开、翻卷和退焰，不生成额外伤害或目标。

最终默认包实际加载`index.e678c.js`，桌面1280×720与844×390手机视口的代表技能均经真实GameSession施放和Cocos渲染；7个释放边界、贴身普攻、WAR三种近战招式、四系接触、材质池复用及清池通过，运行异常0。WAR_01/05没有飞刃弹体，5m以外样本无近战伤害；突进碰墙/取消连招/旧档兼容另有规则探针。见[代表画面](../../src/cocos/test-results/combat-design-alignment-final/four-families-current.jpg)、[实际运行报告](../../src/cocos/test-results/combat-design-alignment-final/actual-render-report.json)和[汇总](../../src/cocos/test-results/combat-design-alignment-final/summary.json)。已对代表帧的主形、材质与锚点进行对照，150阶逐项外观和硬件帧率仍独立验收。此前远距WAR v4和上一轮接线截图保留历史用途，不能当成本次近战外观。此次按每个规则步让出真实渲染帧，使原生粒子年龄和逻辑时间共同推进；旧同步循环可能将多段短闪压在一帧形成白块。已实读GPU纹理角alpha=0、正确mask descriptor及UV，未因该采样问题改写正确纹理或假装修复材质。诊断见[纹理与材质记录](../../src/cocos/test-results/particle-alpha-probe/mask-and-material-diagnostic.json)。

## 战斗动作接线复核（2026-11-08）

实际伤害、弹体、护盾、治疗与原生特效原已接入；本轮补齐 `FlatActors.ts` 中10个敌方副招的动作映射，并将非弓玩家技能的释放帧与权威 `releaseAt` / `emitted` 对齐。副招复用各自角色已有主动作，`inspect().primaryPoseReused` 明确记录复用；没有新增独立动作美术，也没有改变伤害、目标或段数。敌方前摇、有效段、后摇按最终选用图集的 `phaseStarts` 取样，包含 `ELITE_02` 复用弓动作的 `.75/.875` 边界。

默认 `build/concept-2d/` 于14:14完成重建，7469入口实际加载 `assets/main/index.1f412.js`。类型检查及已有95项规则检查通过；实际采样分支覆盖57招敌人和21个玩家主动/终极技能。浏览器另验证10招真实 `beginMove → advance → FlatActors.update` 的有效动作格与暂停恢复，以及7个玩家技能释放前后和四系实际接触，运行异常及敌方验证的失败请求均为0。证据为[敌方动作运行记录](../../temp/combat-integration-2026-11-08/enemy-actions-verified.json)、[玩家动作与特效运行记录](../../src/cocos/test-results/combat-integration-2026-11-08/vfx/actual-render-report.json)及[四系代表画面](../../src/cocos/test-results/combat-integration-2026-11-08/vfx/current-four-families.jpg)。这些是受控运行验证，尚未逐关完成自然实战或150阶美术终验。

## 当前四系与自身功能层

| 运行内容 | 实际接线 |
| --- | --- |
| WAR_01/05 | 角色身前扇形内的实体银刃随近身连斩分段扫掠；没有远程飞刃，真实触点金属尘闪。 |
| WAR_02/04 | 碰撞安全突进后在实际停止点±45°交叉斩；短距圆盘落刃及同圆盘余震，裂痕不扩判伤。 |
| BOW_01/02/03/05 | 每个权威 projectileId 对应一个木杆、金属头与尾羽箭体。分裂箭首击之前只有主箭，之后才出现已分配子箭；尾迹只保留已经飞过的短段，不提前画未来路径。 |
| FIR_01/02/04/05 | 下坠/飞行热核、密实红橙 billow 与短加法翻卷边；火墙按真实长条，火海第0段随0.30s前缘推进，其余4拍只有低位余焰。 |
| THU_01/02/04/05 | 只为真实 `from/to/targetId` 连接画横向蓝干线、短紫枝；每个真实 `skill_hit` 独立产生短接点，装饰枝不招募目标或增加命中。 |
| WAR_03 / FIR_03 / THU_03 | 钢甲片、窄火羽、武器三枚短电片分别贴身；受击局部闪，附雷只在实际基础命中处亮。 |
| BOW_04、8被动、COM_01/02 | 细猎刻、真实被动触发、真实移动步迹与三次实际治疗光瓣，不共用全身圆冠。 |
| A12 / 敌弩手 | `clue_reveal` 显示暖金四角提示；弩手按核心18m弹程、锁定方向和遮挡/同层截断显示细预警。 |

基础杖普攻保留低亮中性色小芯与短尾，不能据此重新开放退役ARC职业。正式运行接口仍为 `effects.onEvents(events, game)` / `consume` 和 `effects.update(game, preview?)`；技能预瞄直接读取 `rank.geometry` 的米/度字段，区分直道、交叉并集、圆盘与条带并集、矩形、扇面和首击范围。

## 生命周期与运行证据

当前实例上限为96个原生发射器、160条 Line、64个实体箭/油瓶节点；闲置按类型复用。表现记录、轨迹和事件去重均有界。暂停停止原生粒子并清掉短接触；恢复沿同一个 session 时钟显示仍有效的护盾、标记和场，不重播爆发。换区、重置与销毁清空全部池状态。Line 使用引擎 worldSpace 语义，节点重心仅用于透明队列排序；2D胸手接触仅施加视觉深度偏置，不改变动作、弹道或碰撞坐标。

### v4当前材质与实际画面

`npm run check` 已通过。当前材质验收来自2026-11-08 11:12:51完成的隔离包 `build/concept-2d-campaign-v4/`，新浏览器上下文访问 `http://127.0.0.1:7476/?view=2d`，实际加载 `assets/main/index.33620.js`。见[最终运行记录](../../src/cocos/test-results/native-skills-v4/actual-render-report.json)、[独立材质审阅](../../src/cocos/test-results/native-skills-v4/final-material-review.json)与[四系实际接触表](../../src/cocos/test-results/native-skills-v4/four-family-actual-contact-sheet.png)。源帧为正式包中的真实技能与原生渲染，拼版仅由Pillow缩放排版。

- WAR保持同一月牙的两尖、20段曲线及真实span；中心宽由0.075增至0.105m，金风痕稍加粗提亮。BOW玩家技能箭体只增加35%横厚，长度与位置不变；已经飞过的短尾宽增加约40–44%，不画未来路径或火箭光带。
- THU保持同一批权威连接与目标；蓝芯宽为0.054–0.070m，低alpha紫晕与约0.36–0.67m短叉仍排入detail余量队列。实际接点的短电碎片不会招募其他目标或增加命中。
- 蓝芯单独复用Creator 3.8.8内置 `particles/builtin-particle-trail` 的alpha technique，并用原生blendState指定 `SRC_ALPHA / ONE_MINUS_SRC_ALPHA`、tintGain 1.8。内置alpha technique原配 `ONE / ONE_MINUS_SRC_ALPHA` 要求预乘RGB，而Line提供直通顶点色；未经适配的低alpha紫晕会覆盖蓝芯。当前仅蓝色 `#367cff` 使用这份材质，紫晕、银锋与暖色敌预警保持原加法材质。每次Line池复用按当前颜色重新选择，不只在创建时设置。
- 来源已核对安装引擎的 `editor/assets/effects/particles/builtin-particle-trail.effect`、`editor/assets/chunks/legacy/output.chunk` 与Material的原生pass overrides接口。该路径的 `CCFragOutput` 直接返回颜色，没有额外linear→sRGB抬亮；因此没有猜测性地再转sRGB，也没有新着色器或依赖。
- 844×390实际源帧：[蓝芯与8个实际目标](../../src/cocos/test-results/native-skills-v4/phone-thunder-rank5-graph-peak.png)、[银白飞刃](../../src/cocos/test-results/native-skills-v4/phone-war-rank5-contact.png)、[首击分裂箭](../../src/cocos/test-results/native-skills-v4/phone-bow-rank5-split.png)。[两份真实构建颜色对照](../../src/cocos/test-results/native-skills-v4/phone-thunder-shipped-build-comparison.png)分别为v3原加法材质和v4蓝芯材质，不以浏览器临时预览冒充正式包。
- [原时长雷弧短片](../../src/cocos/test-results/native-skills-v4/phone-thunder-original-duration.gif)来自同一次真实施法的20ms会话采样；8条蓝边alpha依次225/188/154/123/94/69/47/29/15/4，随后归零。没有延长原事件duration或添加新拍；GIF仅在循环末尾留600ms观看空档，不能当成正常CD或攻击频率。
- 雷弧后复用池的WAR全部恢复原加法材质；160线高压呈现合同中，3主预警与4持久区的前7条线均保持暖色原材质，蓝芯另用独立材质。`clear()`后线、发射器、实体、锚点、敌/技能表现记录与轨迹全部为0，浏览器错误为0。这是renderer合同压力，不能当成合法游戏目标数。

本轮实际手机视口复核确认蓝芯与短叉可读；FIR保留生产火舌，未再改形状、伤害或计数。技能短cue继续使用原权威会话时序；完整人物动作、正常对局手感、150阶逐项美术及手机硬件性能仍是不同验收范围。

### v2阶段历史证据（7473，保留原范围）

2026-11-08 10:03:27完成的隔离包 `build/campaign-combat-v1/`，在 `http://127.0.0.1:7473/?view=2d` 完成以下原生复查；主包为 `assets/main/index.7c952.js`。这是当时的[运行记录](../../src/cocos/test-results/native-skills-v2/actual-render-report.json)，不以v4截图替换旧SHA。7475/main93b53的加粗加法线阶段另保存在 `native-skills-v3/`，该阶段蓝线不是最终颜色。

复查采用S02北侧 `z=45` 的受控场景：真实 `GameSession.castSkill/advance`、八个真实原生敌人actor、正式包Cocos渲染；角色等级取对应技能阶的原门槛。静态取样仅在一帧原生粒子播放后暂停原生粒子，避免截图编码耗时吞掉短峰值。没有修改正式包脚本或用图片代替技能。

- [四系实际接触表](../../src/cocos/test-results/native-skills-v2/four-family-actual-contact-sheet.png)：Pillow只做拼版与缩放，四个源帧分别为 [WAR](../../src/cocos/test-results/native-skills-v2/war-rank5-contact.png)、[BOW](../../src/cocos/test-results/native-skills-v2/bow-rank5-split.png)、[FIR](../../src/cocos/test-results/native-skills-v2/fire-rank5-impact.png)、[THU](../../src/cocos/test-results/native-skills-v2/thunder-rank5-graph.png)。
- 844×390手机横屏源帧：[5阶分裂箭](../../src/cocos/test-results/native-skills-v2/phone-bow-rank5-split.png)、[5阶万钧雷潮](../../src/cocos/test-results/native-skills-v2/phone-thunder-rank5-wave.png)。
- WAR实际存在3个在途弹体，并捕获1个已抵达触点；BOW首击命中1人后才出现5支独立子箭；THU_02实际连接8个不同目标。FIR_02该布阵内有4个合法目标真实受击，中心和火体均填实。
- THU胸前接点与短枝可见，实际原生线色为蓝 `#367cff` / 紫 `#926bf1`。远离原点的 `z=45` 位置未被误剔除；实际 Line 的 `worldBounds=null`，节点重心在 `z≈35.82`，与官方按节点计算透明深度的路径一致。
- 护盾暂停时0条活动线，恢复后10条；实际吸收使护盾33.6降到19.6，并收到 `shieldHit`。治疗计数恰为3拍。A12渲染契约抽查出现4个暖金角标；该项只验证 `clue_reveal` 视觉事件，不冒充另一次实际装备掉落/拾取验证。
- 弩手在空旷处显示18m冻结射线，真实仓房墙前截断到4.75m。`clear()` 后活动发射器、线、实体、轨迹和表现记录全部为0；整个浏览器过程无pageerror/console error。

**美术状态：**已确认运行接线、四系剪影和上述代表帧，未声称150阶逐项通过美术终验。银锋内部细纹仍用原生线；FIR已用生产火舌替换被否定的花椰菜烟球外壳，代表帧可见锐薄翻卷和红色空腔，不再使用大白圆核。当前代表帧不是概念板的逐像素还原；手机上的细子箭、弱点刻痕与治疗光瓣仍适合后续按实际设备调对比。此轮使用桌面Chrome的844×390视口，不作为真机帧率或全机型可读性的结论。

## 敌方招式与可拆锚点（当前实现、7473阶段证据）

`NativeEnemyVfx.ts` 读取 `EnemyCombat` 的 `telegraphGeometry` / 实时 `geometry` 与 `enemyHazards`。新profile不重复画旧kind扇/弩线；保留4项legacy路线。锁前暖红、锁定琥珀、实际释放短亮；扇面/矩形/线/圆/缺口环直接取世界坐标。线与冲锋预警仅裁切呈现副本，正常放置AOE不缩短，伤害/移动/目标均由core决定。

[敌方实际接触表](../../src/cocos/test-results/native-enemies-v1/enemy-authoritative-contact-sheet.png)与[运行记录](../../src/cocos/test-results/native-enemies-v1/actual-enemy-render-report.json)来自同一7473正式包。EnemyCombat.beginMove/advance为受控招式入口，相机只用项目既有framing容纳完整几何；4持久区是core生成的字段合同样本，不伪称一场自然战斗。

- U2-4锁前/锁后都保留内外环与90°缺口；BOSS_R2完整冲锋预警与随caster移动的active几何分开读取。
- 索桩、镜架和链锁复用原生道具几何，HP条来自实际hp/maxHp。镜架验证12→6→0，hit/broken事件齐，破坏后body为0且owner进入stagger；道具不是新增NPC或完整道具美术终稿。
- 真实墙前：新弩线4.75m、实际箭最后4.96m（墙在5m）并移除；冲锋预警0.75m、caster移动0.514m后在1m墙前collision结束。普通放置矩形仍18m，authority未被renderer改动。
- 4个持久火区的4条边界全部保留，仅近3区各使用6个可选火舌发射器，第4区没有装饰但危险边界仍可见。
- 独立高压renderer合同样本中，4个输入windup只显示3主预警；池满160线时最前7条敌预警/持久区边界完整，玩家细叉使用余量。该高压事件不是合法目标数或伤害测试，HP未变。
- 暂停时活动线/锚点0；恢复后4持久区边界按权威状态出现；clear后活动线、锚点、发射器、敌表现记录与轨迹均0。浏览器无pageerror/console error。

## 以下为2026-11-04基础特效历史记录

以下旧符、火油、基础动作及56/64/18预算是上一阶段记录，用于追溯兼容与资源来源，不是当前四系技能方案。资源许可证仍适用；金框生命药、火油与检查点补给HUD的保留按最新界面方案保留。

## 资源选型与来源

- 贴图包：[Kenney Particle Pack](https://kenney.nl/assets/particle-pack)，作者 Kenney Vleugels；官网 2026-11-04 标示 CC0，压缩包 License.txt 标示 1.1。PNG 是与引擎无关的透明遮罩，兼容 Cocos 3.8.8 原生粒子材质。成熟静态纹理无需运行时维护或额外框架。
- 许可证：[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)。原版 License.txt 随资源保留在 `src/cocos/assets/resources/vfx/kenney/LICENSE.txt`，文件字节未修改。原作者另列滤镜模板贡献者；详见该许可证文件。
- 官网下载端点：`https://kenney.nl/download-link/6173736574732f7061727469636c652d7061636b`。官网现使用有时效签名的下载链接，先打开来源页建立会话，再由该端点获取 ZIP，旧 `/media/pages/...zip` 链接会返回 HTML。
- 本次压缩包 `kenney_particle-pack.zip` SHA-256：`B631D4B07F7002549FDCF155F01141AD482F79F3440E4E301EED49CE5F1D8958`。
- 只选用包内 `PNG (Transparent)` 的 12 张原始 512×512 RGBA 贴图，逐字节复制，未重绘或重新编码。PNG 与许可证合计 794648 字节；完整逐文件校验值在 `src/cocos/assets/resources/vfx/source.json`。

| 原文件 | SHA-256 | 用途 |
| --- | --- | --- |
| circle_03.png | ED6C6F082E666C16BCACA89F15AEFB55DF9BF69450090518BCAE1D3D61F82936 | 地面施法符环 |
| dirt_01.png | 6827A0A32A293EC9570FB98D63963B8DD6E6AABA9E1096AFAD932E93A378BEA9 | 脚步冲刺、推击、失衡尘屑 |
| flame_02.png | 7AFFF66979A5A30319D4FA491B13A9027223EBBDADFA38FAE4AE76E31D05D9C5 | 火油火舌、爆炸火焰 |
| light_01.png | CAEDCC5DF5BCAC4470244D2520D6A64B45B20C1CCF4D918DA516C55E3FA365A6 | 蓄力与短促命中闪光 |
| magic_01.png | 398479EA280C8161D0B6D509CA97EEFB27E989C7832B404ABCB65FAAE3E922FF | 法杖、奥术札记 |
| magic_03.png | C2EF5FE86CD2FD08E5B9768389AB6580B346C391DB3C7C09FC9B0A63E00EC4CE | 黑契封印 |
| scorch_01.png | EA72697696638786CCD4795A346D177B1B6A904331B5536A7E85A7ED927B93A5 | 火油地面焦痕 |
| slash_02.png | A79A9E297790E6126B78D41015A3045CDA3F1863B421C88321D2442ED6F9032E | 近战短弧光 |
| smoke_04.png | 2DB2F69874CDB1E5203F2F86803D5DEBDE30402590CF50A810AFABA882184616 | 火油、爆炸轻烟 |
| spark_01.png | 5902DA3A324CAD0A4B5A88CE1E3C9CC18FEE50922C358CE93D8C9F1AD7708F0A | 金属碰撞火星、余烬、引信 |
| star_01.png | 3BA3999C944A0767677449412D306C1F230DAA1743B31F929533CF77A22ECF5D | 回响祷文 |
| trace_01.png | 34DE69BC3F665B23FE9BED15F388EFD8E8E4DC1A99F2FC5DB9BA8715C525711F | 箭矢尾迹 |

## 实现边界与视觉约束

`VfxAssets.ts` 负责资源缓存、内建材质和原生粒子配置；`Effects.ts` 只接入规则状态并摆放发射器。项目已有的 Cocos primitive 用于少量箭杆、箭头和投掷油瓶实体，这是原生组件适配，未新写几何生成器。箭矢不再是一条方块，火油不再是一排圆锥。

- 普通剑击在现有 .12 秒生效点触发短弧光；追步斩沿用 .25 秒技能释放点，增加脚边尘屑与稍大的冷白弧光。推击、冲刺采用低位尘屑，保留人物轮廓。
- 普通箭显示木杆、金属尖端、尾羽；蓄力箭的尾迹略长，弓的 .8 秒蓄力节点由小环与弓前亮点表达。返程箭直接跟随权威投射物位置和朝向。
- 法杖、奥术札记偏蓝，黑契封印偏紫，回响祷文偏象牙金；各有不同原始纹理与命中微粒。
- 火油显示翻转油瓶，落地后低位火舌、稀疏余烬与低不透明度上升烟雾；持续区域只有细边界，深色焦痕会自然淡出。爆炸的闪光与火焰是有限寿命 Burst。
- 敌人前摇使用贴地细轮廓：冲锋为双边通道和箭头，挥击为扇形外缘，弩手为细瞄准线；脚边进度弧随现有 phaseTime 收束。显示范围来自现有判定参数，未改变判定。
- 投掷预览半径仍为 1.1 米；合法点用暖象牙细圆环，非法点用暗红圆环加叉号，两者使用同样高度的完整抛物线。颜色以外有形状差异。
- 贴图使用 clamp 避免边缘平铺；所有粒子保留深度测试并关闭深度写入，烟尘使用 alpha 混合，火星与短弧使用内建加法。没有大面积全屏辉光、额外光源或人物染色。

## 生命周期与预算

每个区域一个 Effects 实例。发射器最多 56 个、原生 Line 最多 64 条、实体投射物节点最多 18 个；每个发射器容量 2–28 个粒子。闲置发射器按类型复用，总池满时回收已结束的闲置类型；忙碌总池已满时跳过次要表现。普通火油每区约 13 火舌、7 余烬、5 轻烟存活，非每帧生成 Node。所有发射器、线和实体在 destroy 时随 VFX 根节点销毁。

原生粒子使用世界空间、原生渐变与大小曲线。Burst 使用公开 Burst 组件数据，避免调用未暴露的 ParticleSystem.emit。Cocos 3.8.8 的模块 getter 在运行时可能返回空，所以通过公开 js.getClassByName 获取已注册的引擎模块类，在未激活节点上配置，然后由原生 onLoad 绑定。锥形默认朝 -Z，形状旋转 +90° 后朝上。

- `await Effects.preload()`：资源 bundle 已加载后、创建场景特效前完成。
- `effects.onEvents(events, game)`：在现有事件分发处调用一次；用于命中、格挡、受伤、爆炸、失衡、标记等精确时点。
- `effects.update(game, preview?)`：原有接口保留，状态驱动持续火焰、投射物、蓄力与前摇。
- `effects.clear()`：菜单、后台、暂停与重建时停止并清空原生系统、轨迹和瞬时提示；对话、掷骰、死亡状态亦由 update 清空。
- `effects.destroy()`：销毁区域实例；`Effects.dispose()` 仅在所有实例销毁、退出整章后释放共享纹理与材质。

引擎配置已同时启用 `particle._value` 和 `includeModules` 的 `particle`。

## 验证与复查

2026-11-04 已运行项目现有 `npm run check`（通过）和 `npm test`（95/95 通过）；未增加测试代码、脚手架或依赖。未由该子任务启动 Cocos 编辑器或构建，以免与整体集成争用。最终应在整体构建后检查日间/洞穴、普通/蓄力弓、三种符咒、前摇、油瓶轨迹、持续火焰和菜单清理的实际画面。

核对的引擎一手资料：[Cocos 3.8 粒子系统](https://docs.cocos.com/creator/3.8/manual/en/particle-system/overview.html)、[主模块](https://docs.cocos.com/creator/3.8/manual/en/particle-system/main-module.html)、[3.8.8 ParticleSystem 源码](https://github.com/cocos/cocos-engine/blob/v3.8.8/cocos/particle/particle-system.ts)。实际 API 同时逐项查验本机 Creator 3.8.8 `cocos/particle`、内建 particle/trail effect 源码。
