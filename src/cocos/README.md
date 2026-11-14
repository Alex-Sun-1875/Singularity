# 第一章 · 阵亡者的晚饭

2026-11-13 当前登录统一为小游戏原生 `tap.login` / `tap.checkSession`，不再使用自建账号后端、`serviceUrl`、openid 换码或自定义 token。浏览器仍为显式预览，普通小游戏测试和正式构建使用平台登录，独立游客构建保留原有测试边界。本机存档不因登录调整而清空或迁移；账号云同步尚未接入。详见 [当前发布与登录说明](release/README.md)。

2026-11-12 技能库恢复为33项、165阶；战斗布局为大普攻＋闪避＋四普通技能＋独立终极，总共七按钮。原30项技能、减速火墙、陷阱与撤射均保留，终极继续使用职业资源。旧档迁移与可选技能见[当前方案](../../docs/design/restored-skill-library-v1.md)。

正式工程：Cocos Creator 3.8.8，入口 `assets/FirstChapter.scene`。这是独立的 TypeScript/Cocos 工程，旧 Lua 规则作为迁移用例基线保留。

## 当前试玩入口（2026-11-10）

根目录 `npm start` 启动 7469，默认在既有绘制场景中显示3D主角：[当前入口](http://127.0.0.1:7469/?view=2d&player=3d)。省略 `player` 参数也默认使用3D主角；显式 `player=2d` 可查看历史2D人物。`view=2d` 表示绘制场景模式，不再代表主角必须使用2D图集。攻击射程、移除脚边定位圈和小地图朝向箭头继续生效。

独立技能测试从主菜单「技能靶场」进入（[本次独立试玩](http://127.0.0.1:7471/?view=2d&player=3d&progression=natural)），设置 → 旅途和暂停菜单也有入口。靶场使用不保存的临时 Lv40 角色，提供5／10／20只近战＋盾兵＋远程的群怪实战（可击杀、再来一波），以及单靶／密集五靶／直线五靶、1.5—12米起始靶距、无限或正常资源、治疗用生命减半及可选反击演练。顶部「靶场设置」修改靶位、重置和查看统计；C / F8选择技能与1—5级，再点「装入选中技能与武器」，主动／终极／被动均可测试。统计读取实际伤害、命中、MISS、暴击和DPS，退出恢复原旅程。详见[独立靶场](../../docs/design/skill-training-range-v1.md)。

技能效果对比使用[临时调试入口](http://127.0.0.1:7469/?view=2d&player=3d&test=max)。在标题页、设置或暂停菜单打开「技能效果调试」，桌面可按 F8 开关面板。选择流派与技能后直接点1—5级，实际施放、预瞄范围和技能说明立即使用对应等级；「本系同级」「全部同级」跟随当前选中技能的等级。选择技能会自动装入对应技能与武器，也可点「装入选中技能与武器」重新装配；额外主动技能放入第一槽，被动自动装入被动槽。「补满状态」恢复生命和当前职业资源。

此面板仅允许本机 localhost / 127.0.0.1 的 `test=max` 临时配置使用；角色等级固定40，技能等级可独立切换，不受正常技能点预算限制。切换清除旧动作、技能、玩家弹体、灼烧、护盾和增益，避免混入上一等级效果。本次测试和新建测试旅程均不写入普通存档；返回普通链接恢复原进度。TapTap发布入口关闭此功能。当前已接入按实际技能范围绘制的强化刃面、三段普攻骨骼动作，以及更实的火焰爆发／炎墙／火浪。概念整图仍保留为方向参考，实际接入、素材来源与验证边界见[技能特效范围接入记录](../../docs/design/skill-vfx-range-integration-v1.md)。

## 历史2D人物入口（2026-11-06）

根目录 `npm start` 启动7469的设定图2D版；`npm run build` 构建 `build/concept-2d/`，入口默认进入2D。原暖金界面、地图/行囊、检定、装备、存档与剧情复用原实现。最新face-v3统一主角阿斯代伦/盖尔/杰洛特气质的原创融合脸：68张动作图、独立头像、88动作和七件武器完整接入；原身体UPP、动作时序及探索背负/战斗持握保留。35款五阶装备图谱继续可用。当前证据见[最终验收](test-results/face-blend-v3/final-audit.json)，美术与历史阶段见[人物记录](../../docs/assets/appearance-v5.md)和[2D版本记录](../../docs/assets/concept-2d-preview.md)。

```powershell
# 本目录，最后一次构建与验证之后打包
python tools/report-build.py build/concept-2d test-results/face-v3-build-size.json
python tools/package-test.py --platform web-mobile --build-name concept-2d --view 2d --revision face-v3 --report test-results/face-v3-build-size.json
```

恢复或替换 `library` 后，旧 `temp/asset-db` 的网格构建缓存可能仍然描述之前的顶点布局。`Build-Local.ps1` 现在会先校验形变网格缓存，将不匹配项备份后让 Cocos 重新生成，避免拉弓时出现异常三角面。[修复与画面记录](../../source-art/weapons/3d-bow-artifact-v1/README.md)。

使用 C 盘临时镜像构建时，先同步完整 `assets/scripts`（包括 `app`、`core`、`features`、`shared` 与 `platform`），并核对与当前源码一致，再构建、复核与接入。仅复制正在编辑的文件会混用旧规则配置，曾导致 `playerProjectileSpeeds` 缺失，放箭时报错。当前同步和修复记录见 [箭矢生成修复](../../source-art/weapons/3d-arrow-visibility-v1/README.md)。

以下是保留的3D对比版及通用操作说明；3D启动用根目录 `npm run start:3d`，重建用 `npm run build:3d`。通用玩法按相同规则执行。

## 启动

```powershell
# 仓库根目录
npm run start:3d
npm run build:3d

# 单独打开工程
& 'C:/ProgramData/cocos/editors/Creator/3.8.8/CocosCreator.exe' --project 'F:/workspace/Singularity/src/cocos'
```

默认目标为手机横屏 **web-mobile**，本地发布构建在 `build/web-mobile/`；`Run-Local.ps1` 使用 Python 在 `127.0.0.1:7458` 提供服务。编辑器预览通常在 `localhost:7456`；本轮引擎模块配置更新后，仍打开的编辑器预览出现过陈旧导入图，应以7458正式构建作为本轮试玩入口。浏览器需启用 WebGL，进入旅程后启用音效。

交付包为 `artifacts/first-chapter-playable-web-mobile-2026-11-05.zip`，包含蜂蜜暖金/棕铜暗边/深棕黑内凹/古典角饰界面、D20、FairyGUI地图、11动作原生人物、配套PBR与原生VFX。最新视觉见[暖金校准v6](../../docs/assets/warm-gold-alignment-v6.md)。打包默认使用`build/web-mobile/`，校验对应体积报告并执行ZIP CRC，SHA-256记录在`artifacts/test-package.json`：

```powershell
# 本目录；完成构建后
python tools/report-build.py build/web-mobile
python tools/package-test.py
# 桌面目标仍可显式选择
python tools/package-test.py --platform web-desktop
```

解压后可在解压目录运行 `python -m http.server 7459 --bind 127.0.0.1`，电脑访问 `http://127.0.0.1:7459/`。手机与电脑处于同一 Wi-Fi 时，改用 `python -m http.server 7459 --bind 0.0.0.0`，在手机横屏浏览器访问 `http://电脑局域网IPv4:7459/`；电脑当前地址可由 `ipconfig` 查看。完整 Web 体积与首屏下载见 `test-results/build-size.json`、`browser-release.json`，不是 TapTap 首包。

## 操作与流程

怪物击败后保留倒地尸体约30秒（游荡怪刷新时复用原节点）。怪物、首领和战斗事件掉落的装备先显示在地面，靠近后点击「拾取」或按F才进入行囊；自动战斗/挂机会在近处拾取，并在附近无威胁时沿现有路径前往掉落处。装备独立于尸体保存，切换区域、死亡重试和读档均保留未拾取物；已有同款装备仍按原规则折算金币与铁。金币、铁、经验及任务/商店/制作奖励沿用原结算方式。

画面上方新增自动寻路（P）、自动战斗（Y）、挂机（H）。寻路可选择本区域目标，或在地图选地点后点「前往此处」，按真实道路跨区域步行；自动战斗使用当前普攻与已装配技能；挂机在本区域持续狩猎，按原刷新条件远离出生点等待。生命偏低自动使用已有生命药，低生命无药或倒下时停止。移动、手动攻击/技能立即接管，菜单、剧情、检定、后台中断停止，重新进入游戏不自动开启；无离线收益。[完整说明与验证](../../docs/interactions/automation.md)。

WASD 移动，Shift 慢走，鼠标瞄准，J/鼠标左键攻击，F 交互，空格闪避，L 推击，R 武器技，K 按住瞄准并松开投油，Q/E 松开施符，B 行囊，M 地图，Esc 暂停。弓需要按住蓄力后松开。右键或 Esc 取消预备动作。

地图支持地表／旧誓下城／沉钟地宫切换，拖动平移、滚轮或加减按钮缩放、全览、定位队伍和地点筛选。点击地点查看详情并标记道路参考，M 或 Esc 返回旅途；桌面另可用方向键平移、Home 定位。地图标记仅保留在本次运行中，底图与地点尚未逐像素配准，详见[地图 UI 与本地 BG3 参考](../../docs/maps/map-ui-bg3-reference.md)。

手机横屏左侧摇杆小幅推动慢走、推满奔跑，右侧按钮操作；按住攻击蓄弓，拖动瞄准，松开释放。火油/符咒同样按住预瞄。拖至“取消”区松开可保留箭、油与符咒，再按闪避。触控遵循两拇指设计：一根移动手指与一根动作手指，各自锁定控件；第三根动作手指不会额外触发攻击。行囊、技能与长说明使用可滚动弹窗，竖屏显示旋转提示。

手机使用3米正交半高镜头，正常站立人物约92px；半球环境填光改善衣物和手部暗区，未增加实时灯。当前草簇、建筑外壳与区域布景仍属可继续提升的美术范围。

开局在第三杯旅店。可接弥菈的契约，也可拒约独立调查；夺匣前仍能补签一次。可先下城，完成晚饭与工匠救援，但首章结算仍需返回北岭哨关击败灰披队长并抬杆，再领取原来源的钢剑、交还星匣并作出幕末选择。地图中的后续地区入口明确标注版本边界。

自动保存到平台本地存储，双槽校验恢复。损坏或未知版本原档保留；“新建旅程”先备份旧存档。本工程使用独立 `SaveSnapshotV1`，没有静默导入旧 Lua/网页原型进度。D20 更新兼容之前的 Cocos V1 进度。退出恢复保留已保存的位置、资源、战利品与商货；敌我临时出招清空，死亡通过最近检查点重试。休整恢复生命与火油，不刷新商货、符咒或灵感。

## D20 剧情与探索检定

新旅程在旅店与弥菈交谈，选择标有 `[洞悉 DC12]` 或 `[游说 DC14]` 的选项即可掷骰。厅内铜簧匣、S03 空墓刻痕、S13 检修记号与 U1-05 连动锁也有检定。原有即时战斗保持原规则，失败不会永久卡住首章通关。

结算为 **D20 + 属性 + 熟练 + 可选协助 ≥ DC**。自然1必败、自然20必成；优势两骰取高，劣势取低，两者抵消。已获得的线索会改变后续优势／劣势；洛恩指导或已核对的信件可在指定检定提供1d4协助。面板逐项显示加值、成功率和实际结果。

初始灵感2点、上限4点，失败可消耗1点重掷。读原信、追问旧约、救援、队长战及部分调查各奖励一次；不能通过重复互动或休整刷灵感。掷骰前可取消，掷骰后要接受结果或用灵感；已接受的失败不能免费重抽。骰面、所选加值、灵感消耗和未确认结果全部保存，退出恢复不会重抽。

**C** 打开技能与检定历史。检定中 Enter／空格掷骰或确认，R 重掷，G 切换协助，Esc 仅在掷骰前取消。触屏直接点面板按钮。打开检定时暂停世界移动与战斗。

## 内容与结构

- `assets/scripts/core/`：跨功能状态契约与 `GameSession` 会话编排。
- `assets/scripts/features/`：按战斗、装备、过场、世界等功能组织；内部以 `common/data/runtime/locales` 分层。
- `assets/scripts/app/`、`shared/`、`platform/`：应用组合、资源／输入／公共 UI／翻译，以及平台边界。
- `assets/resources/actors/`：10 名实际登场角色的骨骼 FBX、材质贴图、动作与许可记录；源文件在仓库 `source-art/characters/cocos/`。
- `tools/`：本机编辑器 MCP、浏览器检查、音效与工程初始化工具。

场景按区域切换并销毁几何、材质和战斗特效，10 个角色各有独立 AssetBundle，按区域所需异步加载并解析共享材质依赖。地图和建筑使用米制代码生成的实际 3D 几何。地表、桥面和地下坡道具有真实碰撞；U1-02 高差 5 米。运行时模型已进行网格和纹理降级，完整细节源文件保留。当前环境材质、面部雕刻、头发和动作仍属于可玩测试版水准，最终烘焙和多级 LOD 尚未完成，详见[角色记录](../../docs/assets/cocos-characters.md)。

木板、铺石、岩石、中性细平织布、林土和草地已替换为六套完整配套来源 PBR，运行图为 18 张 512² Color/Normal/PBR。底色 sRGB、OpenGL +Y 法线、AO/roughness/metallic 线性通道正确分开；原图与 SHA-256 保留，移除旧岩石与蓝布的强 RGB 补偿，人物服装保留身份染色。真实 GPU 的 RGBA8/完整 mip 共约 24MiB，另有环境与人物纹理预算；详见[运行材质记录](../../docs/assets/pbr-runtime-v3.md)。Fabric082A 是纤维种类未知的程序细平织布，不能称为已确认扫描亚麻。

地图使用FairyGUI1.2.2的官方按钮、控制器、裁剪和拖动，配合既有Kenney资源；`npm ci`会自动应用固定版本的Cocos兼容适配。10名人物复用Quaternius模型/服装及UAL1/2动作，弓动作与武器复用KayKit，保留65蒙皮骨骼和67层级关节，均有 **11个实际动作，包含walk**；轻推摇杆对应walk，推满对应run。17张原创SVG皮肤现统一烟黑渐变、内凹暗槽、细金属明暗包边与角饰；清亮白日加载图和场景自然材质/冷暖光已实际接入。来源、截图与当前美术边界见[最新视觉统一](../../docs/assets/bg3-visual-alignment-v5.md)与[现成库接入](../../docs/assets/native-library-runtime.md)。

战斗反馈使用 Cocos 原生 ParticleSystem、Burst 和 Line 及 Kenney CC0 遮罩，覆盖剑弧、命中、蓄力、符咒、箭/瓶体、火油与敌预警。已修复暂停恢复重复发射火区焦痕，正常火区结束后活动粒子、线和投射体归零。真实触屏操作与独立视觉 fixture 的边界分别记录在[手机 VFX 复查](../../docs/assets/vfx-mobile-review-v3.md)。

## 验证

在本目录执行：

```powershell
npm ci
npm test
npm run check:core
npm run check
# 编辑器预览已启动后
node tools/browser-smoke.cjs
node tools/browser-ui-regression.cjs
node tools/browser-touch.cjs
node tools/browser-physics.cjs
node tools/browser-terrain.cjs
node tools/browser-motion.cjs
node tools/browser-dice.cjs
node tools/browser-dice-visual.cjs
node tools/browser-playthrough.cjs
# 本地发布包服务启动后
node tools/browser-release.cjs
python tools/report-build.py build/web-mobile
```

既有规则/地图/检定检查覆盖三种剧情顺序、四种战斗构筑、有限消耗品与零油零符通关、入口/奖励去重、固定随机、死亡/保存恢复/写入故障、装备效果、实际导航、自然1/20、优势/劣势、灵感和检定存档。本轮复用这些检查，没有新增测试代码或依赖。当前证据分别为：

| 报告 | 已证明的范围 |
| --- | --- |
| [browser-release.json](test-results/browser-release.json) | 发布版桌面/手机横屏移动、输入、行囊与保存/重载，错误和失败请求为 0 |
| [browser-playthrough-release.json](test-results/browser-playthrough-release.json) | 合法游戏命令完成 11 个独立区域、4 次实际击杀、队长战、抬杆与首章结算；10 个角色 Bundle 均实例化、11 动作/53 骨骼；没有直接授予生命、装备或任务标志 |
| [final-mobile-motion.json](test-results/final-mobile-motion.json) | 手机输入的剑/弓/杖武器对应与实际走路/奔跑采样；本报告自身不证明完整粒子生命周期 |
| [vfx-real-review.json](test-results/vfx-real-review.json) | 真实触屏剑、推击、闪避、杖、蓄弓、T01、火油与暂停恢复；逐帧原生粒子及自然结束回收，错误为 0 |
| [release-ui-independent.json](test-results/release-ui-independent.json) | 844×390、915×412 横屏/DPR2 的触屏、双指、滚动、地图、字号/边界；其中 D20 明确为独立展示 fixture，不作为真实检定输入或通关证明 |
| [final-mobile-dice.json](test-results/final-mobile-dice.json) | 固定种子 19 的新旅程，844×390 Android UA 真实触屏滚动选择洞悉、自然1、刷新保留原结果、消耗1灵感重掷19成功、拒约金币0与检定历史；错误/失败请求为0；与纯展示 fixture 分开 |

报告及截图/录像保存在忽略版本控制的 `test-results/`。开发预览提供 `__chapter` 检查接口；发布构建不包含该接口。手机 UA、视窗和软件 GPU 模拟用于浏览器验收，不能证明真机实际帧率或最终美术达到 BG3 水准。

## TapTap 小游戏发布准备（2026-11-10）

**基础接入更新 0.3.2：** 版本、标识、运行配置、分包审计和上传清单已统一；新增保存后更新提示与启动资源失败重试。后续统一使用根目录 `npm run version:tap -- patch` 更新版本。当前要求、操作命令和仍待后台完成的事项见 [`release/README.md`](release/README.md)，下方 0.3.0/0.3.1 内容为此前阶段记录。

**历史登录更新 0.3.1（已被 2026-11-13 平台登录方案替代）：** 客户端已接入 `tap.login → 服务端 code2Session → 自定义会话`，增加登录门禁、失败重试、`tap.checkSession` 前台恢复及过期重登。可部署服务和操作步骤见 [登录服务](../../services/taptap-auth/README.md)。公开配置为 [`release/taptap-auth.json`](release/taptap-auth.json)，Secret 只配置在服务器。当前 `serviceUrl` 为空，正式身份构建会拒绝，需部署及配置请求域名后再出上传包；本地审计和 Web 预览仍可构建。旧 `build/taptap-release-package/game.zip`（0.3.0）不包含完整登录，请勿作为本次登录更新包上传。真实 TapTap 身份交换与真机验收尚未进行。

本次类型检查、100 项客户端/规则检查及 3 项登录服务检查通过。浏览器以隔离响应 fixture 验证登录门禁、重试、前台失败暂停和过期重登，未访问真实 TapTap；915×412 横屏重试按钮高约55px，375×812 竖屏保留旋转提示。桌面/手机横屏既有移动、攻击、行囊、存档重载检查通过，运行错误和失败请求为0。细节见 [`release/taptap-auth-validation.json`](release/taptap-auth-validation.json)。

发布配置在 [`release/taptap.json`](release/taptap.json)。复用已安装的官方 `taptap-minigame-tools` 1.2.2、Cocos 原生 Bundle 和小游戏分包；下载来源与 SHA-256 保留在 `tools/tap-extension-source.json`。没有新增运行依赖、上传或公开发布。

2026-11-10 已在开发者中心创建「剑与火：破晓之战」。游戏 ID 为 `1046344`，**小游戏专用 MiniApp ID 为 `tapmcddcmbhf5lxqng`**，由后台「小游戏管理 → 开放能力 → 小游戏基本信息」读取。两者不同，构建参数 `-TapAppId` 使用后者。公开标识与后台地址记录在 [`release/taptap-project.json`](release/taptap-project.json)，未读取或保存 Secret。

在仓库根目录执行：

```powershell
npm run build:tap:audit       # 无平台身份，本地构建、官方转换、包体测量
npm run build:tap:preview     # 同一资源方案的 Web 验证构建
npm run build:tap -- -TapAppId 'tapmcddcmbhf5lxqng'
```

`Build-TapTap.ps1` 统一准备配置并执行 Cocos；旧的 `Build-Local.ps1 -Platform wechatgame` 也转到此入口。正式身份构建不允许空 AppID；审计模式不填造 AppID，并清除 Cocos 中间产物自动插入的微信示例身份。AppID 是 TapTap 小游戏身份，不是 Maker 项目 ID。转换前将 `game.json` 分包键统一为官方要求的 `subPackages`。

发布版本固定为当前绘制场景与 3D 主角，横屏，从 Lv1 新旅程开始；不执行 localhost 满级或 `test=max` 入口。既有技能免冷却等已确认玩法规则保持不变。普通 Web 试玩仍使用原路径和既有试玩设置。

资源按地图图册、室内、地形、场景物件、传送点、环境、装备、战斗特效、3D 主角、材质和各个 2D NPC/敌人拆包。只在发布构建中过滤历史 2D 主角图集、旧主角模型和未使用的旧地图/传送点图片，源素材与原 UUID 不移动、不删除。`GameResources.ts` 将既有资源路径接到 Cocos 按需 Bundle 加载，Web 验证使用相同路径规则。构建参数使用本机 3.8.8 自带的 `bundleConfigs` 与资源过滤能力，未修改官方插件。

本轮实测：同平台小游戏全量原始体积由 699.32 MiB 降至 280.75 MiB（约减少 59.9%），官方转换器生成的完整上传 ZIP 为 259.84 MiB。声明分包之外的本地首包为原始 4.62 MiB、ZIP 1.09 MiB。按开场观察到的 Bundle 加上两份生成的 WASM 分包计算，开场依赖原始资源约 163.30 MiB；首包数字不代表已经可以开始游玩的总下载量。当前优先需要优化的是开场资源量及真机内存。汇总证据见 [`release/taptap-size-report.json`](release/taptap-size-report.json)。

既有95项规则与类型检查通过。复用现有发布版浏览器检查，桌面和手机横屏通过 Lv1 新旅程、3D 主角、移动、手机触控攻击、行囊及存档重载；行囊检查等待实际图片 Promise 完成后再重载，避免将主动换页取消的请求当成加载失败。另通过 S01、S03、U1-01、H01、H04 的受控资源加载检查，未发现运行错误或失败请求；这些切区检查不代表自然通关或真机性能验收。

官方转换器的上传 `game.zip` 包含所有分包目录；不要把它与本地首包 ZIP 混淆。本轮文件在 `build/taptap-audit-final-package/game.zip`，详细测量及首包审计 ZIP 在 `artifacts/taptap-audit-final/`。首包审计 ZIP 仅用于测量，不能替代完整上传包。配置使用 20 MiB 的保守内部首包预算；平台文档存在 20MB 与“60M+”两种表述，上传总包限制、平台实际首包、真机启动、30fps、发热、登录及持久化均尚待真实项目验收。

已使用真实 MiniApp ID 重新生成上传测试包 `build/taptap-release-package/game.zip`，版本为 `0.3.0`；本次构建报告位于 `artifacts/taptap-release/report.json`。后台 TAP 上传界面显示完整包须小于 300MB，应以完整 ZIP 字节数核对；通过本地大小核对不代表平台已经接收或真机验证通过。小游戏基础配置的服务内容声明仍待提交，正式上传自测前需按实际功能完善相应声明。

需要开发者提供或在后台完成：

| 阶段 | 必要资料或操作 |
| --- | --- |
| 绑定与扫码自测 | 项目及 MiniApp ID 已取得；使用真实身份重新出包，上传后由平台解析并进行扫码自测；开发者认证状态按后台实际要求完善 |
| 对外发布资料 | 最终游戏名、工作室/厂商名、联系及客服邮箱、计划开放内容和是否有内购；隐私政策公开链接及实际数据收集说明 |
| 小游戏前置备案 | 著作权人和权属资料、游戏内容说明、负责人及联系方式、后台按主体要求列出的身份/授权材料；身份扫描件和电子化核验由负责人直接在后台提交 |
| 可由项目整理 | 图标、横版/方形宣传图、至少三张实机截图、实机录屏、版本说明、第三方素材与字体授权清单 |

无需提供账号密码、验证码、App Secret 或私钥。历史审计包保留无身份状态；新测试包使用上述真实 MiniApp ID，但尚未上传或通过平台及真机验收。仅小游戏时防沉迷依托平台；无内购小游戏目前无需提交版号，但普通小游戏上线前仍需完成前置备案。若增加内购，需另核对版号及接入要求。

官方入口：[Cocos 适配](https://developer.taptap.cn/minigameapidoc/dev/engine/Cocos-Laya-Egret/)、[分包规则](https://developer.taptap.cn/minigameapidoc/dev/tutorial/basic/subpackage/)、[创建与资质要求](https://developer.taptap.cn/minigameapidoc/quick-start/guide/creation-improvement/)、[前置备案](https://developer.taptap.cn/minigameapidoc/quick-start/guide/pre-filing/)、[物料规格](https://developer.taptap.cn/minigameapidoc/quick-start/guide/game-publish/material/)。


## 公共颜色与状态反馈

状态、阵营、伤害类型、技能流派和装备品质统一在 [`FeedbackPalette.ts`](assets/scripts/shared/ui/FeedbackPalette.ts) 配置，Cocos 显示复用 [`FeedbackView.ts`](assets/scripts/shared/ui/FeedbackView.ts)。使用语义名称，不在新面板复制 RGB。

```ts
FeedbackView.tint(label, 'state.paused');
FeedbackView.tint(icon, qualityFeedbackRole(item.quality));
FeedbackView.bar(fill, hp, maxHp, 'health.enemy');
FeedbackView.ink(graphics, 'map.task', 'stroke'); // 绘制路径之前调用
```

`navigationFeedback` 同时提供任务按钮文案与颜色语义；`damageFeedbackRole`、`playerHealthFeedbackRole`、`qualityFeedbackRole` 统一处理对应状态。共享 Color 不修改通道；透明度使用 `FeedbackView.color(role, alpha)`。颜色配置不写入存档，不改变战斗判定。伤害数字使用实际扣血和已有暴击结果，同目标、同类型短时间合并，24个飘字节点循环复用；未命中仅由明确事件触发。验证记录位于 `test-results/feedback-colors-v1/`，Web 验证不能替代 TapTap 真机验收。


## 命中与打击反馈

[`CombatImpact.ts`](assets/scripts/features/combat/data/CombatImpact.ts) 统一普通、重击、暴击、格挡、火焰、雷电、击杀和持续灼烧的显示参数。[`CombatImpactFeedback.ts`](assets/scripts/features/combat/runtime/CombatImpactFeedback.ts) 复用公共配色，负责按怪物实际身体高度投影的局部冲击、分层音效与有上限的镜头冲击。角色复用原动画、材质与碰撞击退；32—65毫秒接触姿态停顿只影响显示，游戏时间、输入、判定与敌方预警正常推进。持续伤害不反复触发完整停顿与镜头冲击。

接触效果池最多12个、同批次音效择强播放并限频；镜头强度配置上限2逻辑像素，每帧先还原偏移以防漂移。菜单、后台、过图和重建清理效果。设置中的“减少动态”关闭镜头冲击、短闪和接触姿态停顿，保留局部命中提示。

七种音效为项目原有生成器 `python tools/make-audio.py` 的确定性原创合成，单声道22050Hz，原始WAV合计68660字节。音源峰值与时长已检查，主观听感与TapTap实际设备表现仍需试玩验收。验证脚本和记录在 `test-results/combat-impact-v1/`；画面/视频使用高生命、长后摇的隔离目标，主攻击和挥空通过真实触控或鼠标输入，其他元素分类为受控表现夹具，不代表完整章节实战验收。
