# 当前美术与资源

2026-11-12 战士连斩改用当前角色骨架和一致的 GLB 坐标表示，修复腿长与脚部绑定偏差；保留原动作并关闭战士独立踏步层。见[脚部绑定修复 v5](warrior-foot-bind-v5.md)。

2026-11-10 箭矢从深褐近黑调整为冷银灰金属观感，搭箭与飞行配色同步；原模型、UV、动作和绑定保留。见[制作与实机前后对比](../../source-art/weapons/3d-arrow-steel-v1/README.md)。

最新雷电按用户照片改为覆盖命中区域的片状散射电弧场，含游离支叉、蓝白主干、光团与三次放电，见[雷电参考对齐v6](thunder-reference-v6.md)及[实机对照](../../src/cocos/test-results/thunder-reference-v6/reference-comparison.jpg)。

2026-11-08后续修订：战技已恢复近战，BOW_02已改为同一支箭转向连穿；雷电使用近邻互连网、三次放电与首击即出现的雷晕。另已接入荆背猎兽、沼囊吐兽和裂岳獠王，累计26普通/13首领身份。以[连穿与雷网](combat-connections-v4.md)、[雷电与头顶反馈](thunder-feedback-v5.md)、[首击雷晕与有机怪兽](monster-ecology-v1.md)为当前运行记录；下方飞刃、子箭与原12首领数量保留为先前快照。

换图入口已改为青紫符文阵，显示目的地、屏外方向距离与未开启状态，并修正六地区地图定位。见[符文素材、提示词与实现](../../source-art/maps/waypoints-v1/README.md)、[最终运行验收](../../source-art/maps/waypoints-v1/runtime-review.json)及[游戏内画面对照](../../source-art/maps/waypoints-v1/runtime-portal-review.jpg)。

最新地图画风按用户石厅参考统一为低饱和手绘材质、自然磨损与局部冷暖光，九类材质与地形表现已接入当前97区源码。原32区地形保持；扩展65区已有52区广坡、16区水体、15区完整桥栈、7区干沟采坑与13区刻意平整干地。见[地图规范与当前接入状态](../maps/map-art-style-v1.md)、[97地点分区清单](../maps/map-art-area-catalog-v1.md)、[实际素材与处理记录](../../source-art/maps/terrain-production-v1/README.md)和[当前源码覆盖](../../source-art/maps/terrain-production-v1/current-area-coverage.json)。早期32/65目录保留为历史基线；最终包已通过97区生产渲染、76组桌面/手机尺寸画面及桥坡行走、输入和存档检查，见[运行验收](../../source-art/maps/terrain-production-v1/runtime-review.json)与[实景总览](../../source-art/maps/terrain-production-v1/runtime-style-review.jpg)。

2026-11-08 当前为**四系WAR/BOW/FIR/THU＋通用，共30技能、150阶**。奥术秘法暂撤、冰系职业移除，ARC/FRO各7技仅作历史保留；奥术不是当前待必须补完的项目。飞刃走廊与BOW_02分裂箭沿用最初原图结构，本轮另存四系强化候选；BOW_01/03/05仍走直线，雷电保留用户认可的既有`combat-thu.png`方向。四系加强材质层次、真实接触、短尾迹和逐级轻重节奏，不暗增伤害、段数或目标。

当前入口：[技能v2](../design/combat-skills-v2.md)、[空间规则v2](../design/skill-spatial-v2.md)、[特效v2](../design/skill-vfx-v2.md)、[97地点战斗v4](../design/world-combat-v4.md)、[74装备联动v4](../design/equipment-skills-v4.md)。人物1—40级、属性成长及保留技能的等级门槛沿用[成长基础](../design/character-progression-v1.md)，原97节点、12首领和74装备保留。

BOW_02“分裂箭”主箭有效命中后，从首击点分出1/2/3/4/5支子箭，总共最多命中2/3/4/5/6个不同目标；首目标射程12/13.5/15/16.5/18m，固定首击包络半径3/4/5/6/7m。子箭在首击时冻结各自平滑弹道弧线（fixedBallisticPath/noMidflightRetarget），不在飞行中追踪、不补位、不递归分裂、不穿墙，细淡青箭路清楚区分主箭与子箭。THU_02固定原首击中心，五级连接半径3/4/5/6.5/8m、总目标2/3/4/6/8（含首目标），不从接点向圈外递推。

[当前图集与审阅](../../source-art/skills/pure-skills-v2/README.md)只登记静态概念及其选用状态，不代表运行实现或动画。飞刃走廊以[WAR最初原图](../../source-art/skills/pure-skills-v2/combat-war.png)、弓术以[首版分裂箭](../../source-art/skills/pure-skills-v2/combat-bow.png)为基础，当前四系强化候选与审阅以图集为准；曲线单箭和后续直线版退为过程对照。奥术历史方案保留过程记录，已撤出当前交付与待补完列表，v1图保留可复用材质基础。当前运行已读取各阶真实远距几何、世界坐标瞄准与动态镜头，旧1.2—4.5m夹取及3m半高已替换；证据与范围见[远距接入记录](../design/ranged-combat-integration-v2.md)。

采用[最新v5人物外观](../story/revision-v5/art-direction.md)和[当前v3地图](../maps/world-atlas-v3.md)。角色、环境、装备、特效与声音按[制作路线](production-roadmap.md)分批实现。

- [方向与质量要求](art-direction.md)
- [图像处理规范：云端生图、本地常规处理与直连下载](image-processing.md)
- [36敌人身份、32新2D角色与图集生产/运行记录](campaign-actors-v1.md)
- [六区首领、怪物与装备设计](../design/encounters-and-loot-v2.md)
- [13张云端首领/怪物/装备概念板与生成、审阅记录](../../source-art/encounters/cloud-world-v2/README.md)
- [当前文件登记](resource-register.md)
- [角色与动画规格](characters-and-animation.md)
- [主角按图三挥剑模型统一：衣型、大小腿与靴筒](../../source-art/characters/2d-concepts/attack-identity-v5/README.md)
- [环境与道具规格](environment-and-props.md)
- [UI、特效与声音规格](ui-icons-vfx-audio.md)
- [7张参考界面实际落地与验收](reference-ui-v4.md)
- [最新BG3方向整体配色与界面质感](bg3-visual-alignment-v5.md)
- [用户新参考校准：蜂蜜金与深棕黑](warm-gold-alignment-v6.md)
- [现成人物、武器与动作库接入](native-library-runtime.md)

三张角色概念板不等于模型或动作。不得使用已停用的低模、失败模型或不匹配的旧人物作为回退。物品设计数量、图片张数、模型数量和运行验收分别统计。
