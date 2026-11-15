# TapTap 小游戏发布配置

**打包规范（2026-11-15）：** dev / test / release 已接入，`npm run pack:taptap`、`build:tap` 和脚本无参数均默认 test。开发加速用 `pack:taptap:dev`，默认技能无冷却、怪物经验 ×5、每日经验不限、Boss 传奇与神器分别保底，并隔离本机数据；只有明确要求正式包时才用 `pack:taptap:release`。三档共用持续递增的根版本，目录以 `-<档位>`、ZIP 以 `_<档位>.zip` 结尾。release 自动汇总上一正式清单至当前输入的更新条目与资源差异，将 `RELEASE_NOTES.md`、源码清单和差异明细纳入 ZIP 并随包提供，校验通过后归档。实际上线后才登记发布基线，打包不会自动推进。详见[开发与打包规范](../../../docs/development/build-profiles.md)与[开发 skill](../../../.agents/skills/singularity-development/SKILL.md)。

2026-11-15 **dev 加速追加**：怪物经验由 2 倍提高到 5 倍，Boss 每次有效击杀分别结算传奇与神器，沿用职业／章节池、唯一装备重复补偿和复战间隔；test / release 正常概率不变。已完成类型、140 项既有检查及三档共 288 组击杀／拾取／存读档专项验证。本次仅更新代码，旧 0.3.42 dev 包仍为原 2 倍规则，尚未重打新包。[验证记录](dev-loot-validation.json)。

2026-11-15 本轮已实际生成 **0.3.42 dev** 与默认命令的 **0.3.43 test**，均通过 Cocos 导出、官方转换、档位标记、分包、ZIP CRC 与交付 SHA-256 校验；每包约 221.31 MB，离线主包约 1.31 MiB，76 个分包。140 项既有检查、类型检查、三档机制探针及发布基线／日志隔离样例通过；release 隔离样例另验证了日志入包、旁置清单和校验后归档。未制作生产 release 包、未上传，TapTap 平台和真机待验。[验证记录](build-profiles-validation.json)。

2026-11-15 **DEV 快速验证工具**：暂停与设置 → 旅途新增手动补满生命／职业资源、补齐药水、金币与锻造材料各补至 9999、等级＋5／升至40、清除 Boss 再战等待，另复用原独立技能训练场。140 项既有检查、类型、三档执行权限及存读档检查通过；844×390、932×430（3倍密度）与1280×720实际 Web 预览中，通过指针／触控使用工具并往返训练场，保留旅程状态。普通本地构建与 TapTap 构建已共用锁，验证并行请求在改配置前被拒绝。仅生成 Web 验证构建，未重打或上传 TapTap ZIP。[验证记录](dev-tools-validation.json)。

**当前登录方案（2026-11-13）：直接使用 TapTap 小游戏平台能力，不部署自建登录服务。** 普通小游戏构建调用 `tap.login`，前台恢复调用 `tap.checkSession`、失效后重登；不再要求服务器、Secret 或 `serviceUrl`。下方带版本日期的自建服务待办是历史记录，不作为当前构建前置条件。[本轮验证和待验项](taptap-platform-login-validation.json)。

2026-11-14 **0.3.41 当前工作区测试包**：绑定真实 AppID，使用 TapTap 平台登录；纳入本次打包开始时的全部当前资源与玩法代码。完整 ZIP **221.31 MB**，离线主包审计 **1.31 MiB**，76 个分包；导航 WASM 已在引擎资源分包中，主包无 WASM。类型、140 项现有测试、Cocos 导出、官方转换、ZIP CRC、交付 SHA-256、场景脚本绑定及渲染／启动策略校验通过。修复导航 WASM 后处理只识别 TapTap `subPackages`、不识别 Cocos 中间产物 `subpackages` 的误报后，沿用本次导出继续转换，版本仅分配一次。3523 份源文件的构建前后核对中，只有生成版本与该工具修复改变，玩法与美术未变；清单随包保存。未上传，实际平台首包、可玩前下载量及真机验收仍待完成。[0.3.41 测试包](../artifacts/taptap-20261114-current/SwordAndFire_0.3.41_TapTap_test_20261114T155119Z/SwordAndFire_0.3.41_TapTap_test_20261114T155119Z.zip)、[验证记录](taptap-package-0.3.41-validation.json)。

2026-11-14 **0.3.40 移除 Cocos 品牌首屏**：0.3.39 只禁用了引擎插屏，独立小游戏首屏仍显示默认 Logo、标语和进度条。现在使用项目 `build-templates/wechatgame/first-screen.js`，保留 WebGL 2 初始化，移除这套独立画面；游戏自身加载页继续负责资源进度。最终包内首屏无图片请求、无独立 RAF 循环，启动 Promise 链及引擎交换链检查通过；140项已有检查、场景脚本绑定、官方转换、CRC 和 SHA-256 通过。完整 ZIP 219.02 MB，离线主包审计 1.30 MiB；使用与0.3.39一致的玩法脚本快照，随后工作区的三处并行修改未纳入本启动页修复包。未上传，真实平台冷启动与收起恢复仍待验。[修复包](../artifacts/taptap-no-cocos-splash-v40/SwordAndFire_0.3.40_TapTap_test_20261114T020225Z/SwordAndFire_0.3.40_TapTap_test_20261114T020225Z.zip)、[验证记录](taptap-no-cocos-splash-v40-validation.json)。

2026-11-13 **0.3.37 修复 Cocos Logo 卡住**：0.3.36 的项目配置禁用 WebGL 1，但小游戏构建默认同时关闭 WebGL 2，成品缺少渲染后端；实际包内引擎已本地复现交换链创建失败。构建现在显式启用 WebGL 2，检查实际导出的设备实现和首屏上下文，并在官方转换后再次检查。0.3.37 的包内引擎在本地实际创建 WebGL 2 设备／交换链成功，图形错误为0；类型、140项现有检查、官方转换、CRC／SHA-256通过。完整ZIP224.50MB，离线主包审计1.29MiB；游客模式和本机存档逻辑未改。**0.3.36 请改用本修复包**。本地引擎检查不代替完整 TapTap 真机启动，未上传，平台启动／触控／前后台／存档仍待复测。[0.3.37游客包](../artifacts/taptap-startup-fix/SwordAndFire_0.3.37_TapTap_guest-test_20261113T125629Z/SwordAndFire_0.3.37_TapTap_guest-test_20261113T125629Z.zip)、[验证记录](taptap-startup-fix-validation.json)。

2026-11-13 **0.3.35 万箭齐发性能游客包**：保留60帧设置与画质，箭体实例化、加法命中特效合批和分帧预热。同环境模拟器首次最长帧79.9→35.4ms，重复施放CPU约少10%、峰值绘制提交约少23%；普通5分钟走打两边平均约60帧、最低一秒58，进程CPU仅少约2.1%。202份脚本、16份实际包内网格与本地转换／CRC／SHA-256核对通过；完整ZIP224.49MB，离线主包1.29MiB。未上传；iPhone14发热与平台真机表现待验，Android的条带上传收益不直接套到iOS。[下载游客包](../artifacts/taptap-volley-performance-v35/SwordAndFire_0.3.35_TapTap_guest-test_20261113T050635Z/SwordAndFire_0.3.35_TapTap_guest-test_20261113T050635Z.zip)、[验证记录](taptap-volley-performance-v35-validation.json)、[优化说明](../../../docs/performance/volley-performance-v35.md)。

2026-11-13 **0.3.34 药品栏默认隐藏游客测试包**：小地图旁、设置右侧的药瓶按钮继续收展。0.3.33包开关仍在，桌面与模拟手机触控正常，平台失效未复现。类型检查、日常预览、默认隐藏／收展／尺寸变化／隐藏输入验证、官方转换与包内代码核对通过；201份脚本相对0.3.33仅HUD默认值与版本信息改变。完整ZIP 224.52MB，本地主包审计ZIP 1.29MiB，可玩前资源下载未测量。未上传，TapTap真机验收待完成。[游客测试包](../artifacts/taptap-supplies-hidden/SwordAndFire_0.3.34_TapTap_guest-test_20261113T021323Z/SwordAndFire_0.3.34_TapTap_guest-test_20261113T021323Z.zip)、[验证记录](taptap-supplies-hidden-validation.json)。

2026-11-13 已生成 **0.3.33 HUD性能游客测试包**：预裁切7个常驻技能图标遮罩、预合成公共按钮底图，保留60帧、布局、触控与画质。两次原版和最终版各5分钟Android模拟器走打，主线程CPU观测下降3%–6%、进程族CPU下降1%–4%，绘制中位数214/215→183，最低1秒57FPS；冻结同帧少28次绘制。整进程改善有限，未测得GPU硬件耗时或物理降温。新增PNG 4.69MB、沿用原分包；完整ZIP **224.52MB**，本地主包离线审计ZIP **1.29MiB**，76个分包。类型、140项现有检查、Cocos构建、官方转换、游客入口/版本/资源标记、201份脚本一致性、ZIP CRC及SHA-256检查通过，未上传。平台首包与可玩前资源下载、真机和正式登录服务仍待验。[游客测试包](../artifacts/taptap-hud-performance-v19/SwordAndFire_0.3.33_TapTap_guest-test_20261113T015321Z/SwordAndFire_0.3.33_TapTap_guest-test_20261113T015321Z.zip)、[验证记录](taptap-hud-performance-v19-validation.json)、[完整性能记录](../../../docs/performance/performance-regression.md)。

2026-11-13 已生成 **0.3.31 游客测试包**，用于替换要求登录的0.3.30测试包；跳过业务登录，沿用现有本机存档。完整ZIP **219.80 MB**，本地主包审计ZIP **1.29 MiB**，76个分包；197份非生成脚本打包前后哈希一致。类型、140项现有检查、Cocos构建、官方转换、版本／游客入口／分包／ZIP CRC／交付SHA-256检查通过。未上传；真实TapTap平台、真机存档延续及实际首包下载量待验证。正式登录服务仍待部署。[游客测试包](../artifacts/taptap-guest-20261113/SwordAndFire_0.3.31_TapTap_guest-test_20261112T162638Z/SwordAndFire_0.3.31_TapTap_guest-test_20261112T162638Z.zip)、[验证记录](taptap-guest-0.3.31-validation.json)。

2026-11-12 已生成 **0.3.25 游客测试包**，包含技能、终极及闪避按钮长按 **3.6秒**查看说明，保留短按施放与拖动瞄准；查看后松手不施放。完整ZIP **219.82 MB**，本地主包审计ZIP **1.31 MiB**。191份非生成脚本在打包期间哈希一致；类型、120项现有检查、Cocos构建、官方转换、入口／版本／游客模式／分包／ZIP CRC／SHA-256及包内技能说明标记检查通过。仅本机存档，未上传；正式登录服务、真实TapTap平台及真机验收待完成。[下载测试包](../artifacts/taptap-skill-tooltips-v1/SwordAndFire_0.3.25_TapTap_guest-test_20261112T015943Z/SwordAndFire_0.3.25_TapTap_guest-test_20261112T015943Z.zip)、[验证记录](taptap-skill-tooltips-v1-package-validation.json)。

2026-11-12 已生成 **0.3.24 游客测试包**，包含屏幕外静态装饰分组剔除，保持跑动5米／慢走2米每秒及60帧设置。完整ZIP **219.77 MB**，本地主包审计ZIP **1.26 MiB**；类型、120项现有规则、Cocos构建、官方转换、版本／游客入口／分包／CRC／SHA-256与编译优化标记通过。安卓同一战斗画面渲染主线程CPU约下降25.7%，不代表iPhone温度降幅；GPU稳定收益尚未证实。编译快照包含182份非生成脚本，03:27之后其他源码修改不在本包；0.3.23保留审计未交付。未上传，iPhone 14持续战斗与平台验收待复测。[下载测试包](../artifacts/taptap-combat-heat-v1/SwordAndFire_0.3.24_TapTap_guest-test_20261111T192620Z/SwordAndFire_0.3.24_TapTap_guest-test_20261111T192620Z.zip)、[验证记录](taptap-iphone14-combat-heat-validation.json)、[分析](../../../docs/performance/iphone14-moving-combat-2026-11-12.md)。

2026-11-12 已生成 **0.3.22 游客测试包**，包含跑动5米/秒、慢走2米/秒及任务指引寻路／静态网格边／CompactMask优化。完整ZIP **219.62 MB**，本地主包审计ZIP **1.25 MiB**，Cocos构建、官方转换、版本／游客入口／分包／ZIP CRC／SHA-256及编译移速／寻路标记通过。177份非生成玩法脚本在打包期间哈希一致。未上传，真机温度与平台验收待复测。[下载测试包](../artifacts/taptap-movement-v4/SwordAndFire_0.3.22_TapTap_guest-test_20261111T183446Z/SwordAndFire_0.3.22_TapTap_guest-test_20261111T183446Z.zip)、[验证记录](taptap-movement-v4-package-validation.json)。

2026-11-12 已生成 **0.3.19 游客测试包**，纳入本轮火系彗星、短尾焰与离手间距、移除三职业范围/弹道辅助框、近战动作衔接及向前攻击距离调整。完整 ZIP 为 **218.39 MB**，本地主包审计 ZIP 为 **1.26 MiB**；Cocos 构建、官方转换、类型/版本/身份/分包检查、ZIP 全文件 CRC 和 SHA-256 核对通过，五张运行火焰贴图与 ZIP 内文件哈希一致。构建期间玩法源码未变化，仅生成的运行版本更新。首两次配置同步遇到 Windows 截断打开错误，保留已分配的0.3.17/0.3.18版本；配置工具增加仅针对该错误的现有文件 r+ 写入回退后完成构建。[完整测试包](../artifacts/taptap-fire-melee-v1/SwordAndFire_0.3.19_TapTap_guest-test_20261111T161419Z/SwordAndFire_0.3.19_TapTap_guest-test_20261111T161419Z.zip)，[验证记录](taptap-fire-melee-validation.json)。游客模式保留本机存档，本次未上传；正式登录、平台解析/首包与目标设备验收仍待完成。

2026-11-11 用户已授权上传，本次重新生成0.3.16游客测试包，纳入13:51当前源码快照与内存修复。完整ZIP为211.72 MB，首包离线审计ZIP为1.23 MiB；构建、官方转换、版本/身份/游客入口/资源分包/ZIP/SHA-256检查与116项现有测试通过。上传在选文件前被Computer Use停止，原因是无法可靠识别Windows当前浏览器网址；未上传、提审或发布。[测试包](../artifacts/taptap-memory-upload/SwordAndFire_0.3.16_TapTap_guest-test_20261111T055236Z/SwordAndFire_0.3.16_TapTap_guest-test_20261111T055236Z.zip)，[验证及上传阻塞记录](taptap-memory-upload-validation.json)。游客模式保留本机存档；正式登录服务、真实平台/iPhone 14验收与平台首包仍待完成。

2026-11-11 S13内存修复已生成0.3.15游客测试包：共享 `CompactGraphics` 按实际几何分配图形缓冲，保留原路径、颜色、遮罩与帧率设置；同画面对照节省约62.1 MiB缓冲，WebGL 1/2绘制及增长/清空检查通过。连续两分钟移动施法与116项规则检查通过，但iPhone 14真实退出/温度和TapTap平台验收仍待复测。官方内存告警记录键为 `sword-fire-last-memory-warning`，日志前缀为 `[MemoryPressure]`；图形计数不代表整个进程内存。包体201.90 MiB，首包离线审计ZIP为1.22 MiB，实际平台首包与可玩前下载仍待测。产物未上传，游客模式沿用本机存档；源码快照及并行修改边界见 [`taptap-quarry-memory-validation.json`](taptap-quarry-memory-validation.json)。[0.3.15测试包](../artifacts/taptap-quarry-memory-v1/SwordAndFire_0.3.15_TapTap_guest-test_20261111T053335Z/SwordAndFire_0.3.15_TapTap_guest-test_20261111T053335Z.zip)。

2026-11-11 启动与切图加载优化已进入源码和Creator预览：复用原生主角实例，按需并行准备地图/人物/当前装备，直接读取有效Cocos资源缓存，移除无光照地形的无用属性计算与加载结束后的固定停留。本地七次切图约缩短60%–86%，未新增全地图常驻缓存或修改帧率。装备可见性、地形、触控、失败重试与资源销毁已复核；本轮未打包、未上传，真实TapTap与iPhone 14仍待验，详细采样和局限见 [`taptap-loading-performance-validation.json`](taptap-loading-performance-validation.json)。

2026-11-11 地图分块与血条缓冲优化已进入源码和Creator预览，保持原帧率，未另行出包：五张地图整帧三角形提交减少13%–16%，绘制调用增加3–4次；共享卡片网格使同区域往返缓冲增长由约508 KiB降至28 KiB，仍非零增长。四条血条样例减少约18 MiB图形缓冲。地形、触控、规则及类型检查通过；全原生3D调试入口资源/材质失败已登记。上述均为桌面本地证据，不能换算为手机降温百分比，TapTap和iPhone 14持续战斗对照待验。详见 [`taptap-map-chunk-performance-validation.json`](taptap-map-chunk-performance-validation.json)。

2026-11-11 移动战斗运行优化：本轮源码保持原帧率，减少重复的 HUD 属性推导、角色变换／材质提交和远处标签投影；雷电改用 Cocos 动态网格复用缓冲。已有116项规则、类型、移动攻击与暂停换装检查通过。本地同种子战斗的位置／材质提交约减少71%／75%，绘制调用与三角形量基本不变；这些数据不能代替 iPhone 14 发热验收。本轮未生成新上传包，真机对照与证据见 [`taptap-combat-thermal-validation.json`](taptap-combat-thermal-validation.json)。

运行版本由仓库根 `package.json.version` 读取；Cocos Creator 3.8.8，Android 横屏优先。当前完成客户端平台登录接入；平台账号、实名/防沉迷能力与真机验收仍未完成，不能把本地检查或审计包当作已就绪的正式上传包。

## 统一修改入口

图标与封面 v1 已制作并登记在 `taptap-project.json.branding`，可上传文件位于 [`branding/taptap-v1/`](branding/taptap-v1/README.md)，原图/提示词/验收记录位于 [`source-art/branding/taptap-v1/`](../../../source-art/branding/taptap-v1/README.md)。Web 构建自动使用小尺寸图标；店铺物料在开发者中心上传配置，不放进运行资源分包。

| 内容 | 唯一配置来源 | 自动生成/检查 |
| --- | --- | --- |
| 游戏版本 | 仓库根 `package.json.version` | Cocos package/lock、游戏标题/暂停页/登录页、`game.json.productVersion`、`release-info.json`、上传清单 |
| 游戏名、MiniApp ID、游戏 ID、网络超时 | `taptap-project.json` | 包体项目配置、运行配置及身份审计。数字游戏 ID 不能代替 MiniApp ID |
| 横竖屏、首包内部预算、资源分包及 `engineWasmSubpackage` | `taptap.json` | Cocos Bundle 配置、资源路由、引擎 WASM 分包和 `game.json.subPackages` |
| 平台登录模式、登录超时 | `taptap-auth.json` | `TapAuthConfig.ts`；仅 `mode: platform` 与超时，禁止自建服务 URL 或 Secret |
| 已提审/发布版本基线 | `taptap-project.json.lastSubmittedVersion` | 已确认后台状态后填写；非空时拒绝相同或更低版本。目前未知，不能据此宣称后台版本唯一性已经验证 |
| 最低小游戏基础库 | 后台解析结果；确认后可记入 `minimumBaseLibraryVersion` | 写入上传清单供核对。未确认时保留 null，不猜版本，也不使用微信的 `libVersion` 代替 |

`BuildInfo.ts`、`TapAuthConfig.ts`、`ResourcePacks.ts`、`NativeTextureReuse.ts` 由工具生成，不手动修改。TapTap 构建会校验当前主角 GLB 内嵌图片与运行时 PNG 的 RGBA 内容及采样方式，仅复用一致的已加载纹理；图片不一致时仍走原加载路径。`taptap-auth-validation.json` 等历史记录保留其原验收版本，不作为当前配置来源。

在仓库根目录执行：

```powershell
npm run version:tap -- minor       # 可选：手动调整 minor / major / 明确版本；每次打包仍会自动 patch +1
npm run check:tap                  # 核对版本、标识及生成文件的一致性
npm run pack:taptap                # 默认：一键生成真实 AppID、正常玩法的上传测试包
npm run pack:taptap:guest          # 游客测试包：跳过业务登录，仅使用现有本机存档
npm run build:tap:audit            # 无平台包体身份的审计构建
npm run build:tap:preview          # 相同资源组织的 Web 验证
npm run pack:taptap:dev            # 开发加速，独立本机存档
npm run pack:taptap:release        # 仅明确要求 release 时；自动生成正式版本更新日志
```

TapTap 打包入口 `Build-TapTap.ps1` 在每次打包前自动将根 `package.json.version` 的末位加 1（例如 `0.3.7` → `0.3.8`），再同步 Cocos package/lock 和运行配置。正式、上传测试、游客测试及审计包均适用，直接调用脚本或通过 `Build-Local.ps1 -Platform wechatgame` 转入也适用；Web 预览不递增。平时打包无需先执行 `version:tap`。

`npm run pack:taptap` 自动递增版本并读取 MiniApp ID，依次准备配置、执行 Cocos、调用官方转换器、校验入口/版本/分包/体积和 ZIP 完整性，最后打印完整输出路径。参数、编辑器路径和发布配置预检失败时不递增；版本分配后若资源准备、构建或转换失败，保留已递增版本，下次重新调用打包再加 1；同次调用内部的 Creator 启动重试及重复配置同步不再次递增。打包不会自动上传。

- 对外交付包：`artifacts/taptap-test/<包名去掉.zip>/<包名>.zip`，上传时直接选择该 ZIP。
- 命名规则：`英文名_版本_TapTap_UTC构建时间_档位.zip`，例如 `SwordAndFire_0.3.43_TapTap_20261115T083000Z_test.zip`。英文名来自 `taptap-project.json.projectName`，只允许英文字母、数字、下划线及连字符；版本来自根配置。档位为 `dev`、`test` 或 `release`；游客／审计变体在时间前另加 `guest_`／`audit_`，仍以 `_test.zip` 结尾。目录以 `-<档位>` 结尾，时间中的 `Z` 表示 UTC。构建时间区分同版本重打包，同名不同内容拒绝覆盖。
- 包旁附带 `BUILD_README.txt`、`upload-settings.json`、`report.json` 和 `<包名>.zip.sha256`；说明包括内容范围、时间、引擎/转换器版本、AppID、体积和待完成项。SHA-256 对应完整 ZIP，本身放在包外，避免循环校验。
- ZIP 内保留官方转换器生成的根入口与全部分包，附 `release-info.json` 和 `BUILD_README.txt`；不会再套一层目录。店铺封面等上传物料仍由清单指向独立文件，不混入游戏包。
- 官方转换原件：`build/taptap-test-package/game.zip`，与交付 ZIP 的字节和 SHA-256 完全一致。
- 版本、AppID、SHA-256、素材路径和待办：`artifacts/taptap-test/upload-settings.json`。
- 体积/分包检查：`artifacts/taptap-test/report.json`；构建日志：`temp/build-taptap-test-out.log`。

不同命名包各自保留一份配套报告；上层报告指向最近一次构建。`Build-TapTap.ps1 -ArtifactDirectory <目录>` 可指定交付位置，不改变包内根目录结构。Web 预览不生成上传 ZIP。

上传测试模式绑定真实 AppID，报告标记 `buildMode: test`、`loginMode: platform`、`customAuthService: false`、`releasePreflightPassed: false`。客户端直接调用平台登录，不再因缺少业务服务地址停住；平台接口缺失、空凭证、超时或失败仍显示重试并暂停玩法。`npm run pack:taptap:release` 执行本地正式预检，不要求自建登录服务。审计模式不绑定平台身份，不能代替真实小游戏登录验收。

2026-11-10 经用户明确选择，增加独立的游客试玩命令 `npm run pack:taptap:guest`。它等价于 `Build-TapTap.ps1 -TestPackage -GuestTest`，输出到 `artifacts/taptap-guest-test/`，报告类型为 `guest-test`，目录及 ZIP 分别以 `-test` / `_test.zip` 结尾。原生 `game.js` 在加载 Cocos 前显式设置游客构建标志；游戏标题和暂停页显示“游客测试 / 仅本机存档”，不调用业务登录、不创建账号或登录 token，也无云端同步。复用现有 TapTap 本地存储和存档键，不清空已有进度。包内说明和上传报告记录 `loginMode: guest`；正式预检与平台验收状态继续为 false。`-GuestTest` 不得单独用于正式、审计或 Web 构建，普通测试包仍保留登录门禁。

Creator 若在启动阶段遇到 Windows 的 `engine.json` 临时打开失败，脚本保存首轮日志并只重试一次；实际构建失败和配置错误直接报错，旧 ZIP 不作为本次成功结果。

正式构建默认读取真实 MiniApp ID；仍可传 `-TapAppId`，但必须与项目配置一致。`-PreviousVersion` 是本次额外基线检查；不能替代检查后台正在审核和已上线的版本。

## 官方要求与当前实现

| 项目 | 要求及处理方式 | 状态 |
| --- | --- | --- |
| 版本 | `x.y.z` 三段整数；新版本高于旧版；提审/发布版本不能重复 | 本地格式、递增和已知基线检查已接入；后台唯一性待核对 |
| 包入口 | 根目录包含 `game.js`、`game.json`、`project.config.json`，由官方转换器生成 ZIP | 构建后校验入口、身份、版本和 ZIP 完整性 |
| 基础配置 | 横屏、隐藏状态栏；统一四类网络超时，登录请求 12 秒、下载 60 秒 | 已自动写入 `game.json` |
| 资源分包 | 驼峰 `subPackages`，每项有唯一 name/root，Cocos 目录包含 `game.js`；通过已适配的 Cocos Asset Manager 加载 | 检查路径、重复/嵌套、入口、依赖图和 Cocos 注册表；失败后可重试启动资源 |
| 更新 | `tap.getUpdateManager`；平台启动/热启动自动检查并下载；`onUpdateReady` 后才能 `applyUpdate` | 下载后在标题/暂停时提示，支持稍后；保存失败不重启；不打断正在进行的战斗 |
| 登录 | 正确取得 code 并在服务器交换身份 | 代码已接入，服务部署/HTTPS 请求域名/真实登录仍待完成 |
| 网络与隐私 | 配置合法 HTTPS 请求域名，按实际 openid/unionid 和会话用途完善声明 | 待服务器与后台配置，不编造地址或声明 |
| WASM | Cocos 导出的 WASM 文件分包与后台的函数采集/代码分包分别记录 | 已检查模块头、归属、加载器与体积；当前后台包不支持函数分包，见下文 |
| 平台验收 | 最低库版本、包体扫码自测、隐私/服务内容声明及资质按后台实际状态完成 | 本地构建不能替代这些操作 |

更新流程单测和浏览器 fixture 可验证交互逻辑；官方说明开发版/体验版不能验证线上版本更新，需要已发布版本之间的真机验证。缺少更新 API 时保持原游戏可用，不伪造检查成功。

## WASM 分包：当前能用的部分和平台限制

业务运算使用 `taptap.json.computationWasm` 作为启动总开关，默认 `true`。本轮覆盖寻路 A*、线段内的密集碰撞／可见性、网格连接点选择、路径简化和地图探索批量可见性；轻量的单点碰撞检查保留 JS，避免桥接开销。设为 `false` 后启动直接使用 TypeScript 编译出的 JS，不请求业务 WASM 模块。模块仍随包保留，以便同一份构建进行运行时对照；`engineWasmSubpackage: false` 则禁用其可用性。Cocos 自带的 Bullet 物理由引擎配置管理，不受这个业务计算开关控制。

测试可导入 `chunks:///_virtual/NavigationWasm.ts`，调用 `await setComputationWasmEnabled(true/false)` 即时切换，调用 `navigationWasmState()` 查看请求状态、实际后端及各计算计数。开发调试入口也提供 `__chapter.wasm.setEnabled(true/false)` 和 `__chapter.wasm.inspect()`。关闭会移除后端并释放地图上下文，正在加载的模块完成后不会自行重新启用；重新开启复用已加载模块。没有 UI 开关或持久化偏好，重启按构建配置恢复。加载／执行失败自动使用 JS；显式关闭再开启可重试加载。对照时应使用同一构建和同样的预热、场景与 60 FPS 设置。

`taptap.json.engineWasmSubpackage: true` 控制 Cocos 的“引擎 Wasm 分包”。构建自动生成 `__ccWasmAssetSubpkg__`（二进制）和 `__ccWasmChunkSubpkg__`（加载代码），由引擎已有的 `loadSubpackage` 流程加载，不自行切割 WASM 二进制或修改第三方加载器。参考 [Cocos 3.8 WebAssembly 支持](https://docs.cocos.com/creator/3.8/manual/zh/scripting/wasm-support.html)。

`npm run pack:taptap` 会检查未压缩 WASM 的格式头、两个分包的声明/入口、模块归属及导出引擎中的加载调用。发现 WASM 回到主包或分包加载器缺失时构建失败。包旁 `report.json` 和 `upload-settings.json` 的 `wasm` 分别列出模块大小、SHA-256、所属分包及 `platformFunctionSplit.verified: false`。分包可能仍在启动阶段加载；不能据此承诺减少可玩前下载量。

用户指定的 [TapTap WASM 分包教程](https://developer.taptap.cn/minigameapidoc/dev/tutorial/performance/launch/wasm-subpackage/) 描述另一层优化：平台采集函数后，把一个 WASM 模块进一步拆成启动部分和延迟部分。[创建指南](https://developer.taptap.cn/minigameapidoc/quick-start/guide/creation-improvement/) 列出了 Unity 和 Cocos 支持，但当前公开 [Cocos 插件 1.2.2](https://developer.taptap.cn/minigameapidoc/dev/engine/Cocos-Laya-Egret/) 及本地插件只导出 `game.zip`，没有该教程所需的 `game_wasm_split.zip` 生成入口。转换器的 `useSubpackage` 参数未实现函数拆分；`handleWasmSplit` 只修正已有 `wasm-split.js` 的平台兼容，不会生成它。

2026-11-10 读取真实项目后台：开发包 458336（后台版本 0.0.1）显示“不支持分包丨当前小游戏包体无法进行分包”，编辑面板的“开启分包”被禁用。此次只读取，未更改版本、上传或提交。该结论针对这个后台包和现有工具，不能扩大为“Cocos 一律不支持”。当前本地模块只有约 469 KB 的 Bullet，不存在教程示例中的大型 Unity 主程序；6 MB/10 MB 的说明属于文档中的 Unity Brotli 产物，不能直接套到这份 Cocos 包上。

要继续完成平台函数分包，需要先取得 TapTap 提供的、兼容 Cocos Creator 3.8.8 / 插件 1.2.2 的函数分包导出工具或配置。不能通过改 ZIP 文件名、设置假标志或只切字节代替。具体工具来源可由开发者工单确认；未授权代发工单。

平台能识别兼容产物后，按官方教程继续：

1. 上传官方工具生成的 `game_wasm_split.zip`，等待预处理，开启分包进入采集准备。
2. 使用 iOS、Android 各至少 2 台设备扫码采集，覆盖启动、新手流程和全部可玩场景；首包函数每次增加少于 10 后再生成。
3. 点击“生成分包”，等待“已分包”，再“提交”。仅开启采集开关不代表完成。
4. 用未参与采集的两类设备验证；提交版本前按官方建议检查首包函数占比至少 30%、新增函数不超过 10。新增函数超过 100 时重新生成。

真机采集和平台生成结果须另行记录；本地检查不会把上述状态自动改成通过。完整上传 ZIP 仍含资源分包，WASM 分包也不用于绕过后台的 300 MB 上传限制。

本轮 0.3.6 实测：WASM 469,455 字节，全部位于引擎分包；主包原始文件 4,919,180 字节、本地 ZIP 1,169,990 字节（1.12 MiB），完整 ZIP 272,991,680 字节（272.99 MB）。`npm run pack:taptap -- -OutputName taptap-wasm` 构建、官方转换、CRC、SHA-256 和新增校验通过，未上传或采集。现有版本未递增；配置和证据见 [`taptap-wasm-validation.json`](taptap-wasm-validation.json)。

## 包体、首包和可玩前资源

2026-11-11 装备浮层合包（0.3.14游客测试）：包含圆角双层金属弹窗、内侧花纹、缩小字号、去掉右上角×、四列四行装备网格和安全换装。冻结157份当前脚本，完整上传ZIP为211,697,189字节（211.70 MB）；主包原始文件5,252,106字节，本地首包ZIP为1,274,779字节（1.22 MiB）。可玩前所需的TapTap实际下载量尚未测量，首包数字不能替代它。Cocos 3.8.8、官方转换器1.2.2、版本/身份/游客入口、资源分包、ZIP完整性和交付SHA-256检查通过；116项既有测试、类型检查以及七种尺寸的界面预览通过。使用同源隔离工程避开工作目录配置写入问题，版本在主工程只分配一次；源脚本清单与包内最新界面标记已核对。包位于`artifacts/taptap-guest-test/SwordAndFire_0.3.14_TapTap_guest-test_20261111T015632Z/`，配套`source-snapshot.json`、`UI_CHANGES.txt`和`build-validation.json`。仅本机存档，正式登录服务仍待部署；未上传、提审或进行TapTap真机验收。见[本包验证记录](taptap-equipment-ui-v2-validation.json)。

2026-11-11 持续运行与行走优化（0.3.12性能验证快照）：保持既有帧率设置，不新增手机限帧。武器与头像按需加载，换装在资源准备成功后提交；缓存不变的武器显隐与弓形变，静止时跳过空位移，当前敌群不再逐帧深拷贝。十处静态程序化网格启用Cocos包围盒计算，以恢复视锥剔除；迷雾按不透明行与边缘灰度合批。四套发型运行贴图及GLB内嵌图由2048降为1024，高分原件保留，2655个非图片二进制区段及几何／骨骼／UV／动作一致。

Creator 3.8.8预览、发布构建及同为原有60帧的本地对照中：纹理分配339.64 → 264.00 MiB、图形缓冲157.79 → 141.55 MiB、诊断GC后的JS堆107.88 → 82.21 MiB；城镇行走绘制调用247 → 216，主循环采样平均约1.11 → 0.85ms，迷雾单次峰值约9.3 → 3.1ms。它们是Windows Chrome内的Cocos/V8诊断数据，不能相加冒充手机进程总内存，也不代表真机帧率或温度。

两分钟约192米行走、三类武器换装、模拟资源失败后保留旧装备并重试、真实Bullet物理墙、桌面／844×390横屏操作与存档重载、116项既有规则检查及类型检查通过；26个缺少包围盒的活动网格降为0。温度、TapTap进程内存、前后台与十分钟真机数据仍待验证，ADB未检测到连接设备。性能包对应154份冻结脚本及已审阅运行贴图；构建期间继续发生的并行界面改动列入记录，不将冻结包冒充工作区所有最新界面改动的完整合包。详见 [`taptap-movement-performance-validation.json`](taptap-movement-performance-validation.json)，包位于 `artifacts/taptap-movement-optimized/`，完整ZIP约211.68 MB，未上传。

2026-11-11 资源精简（v0.3.9）：绘制地图只加载环境尺寸与锚点，不加载随后被隐藏的3D环境网格和PBR贴图；原有碰撞、导航和布景坐标保留。主角武器已有剑鞘时跳过备用剑鞘材质／网格，启动库与独立武器变体并行加载。角色图片按动作清单筛选，共用PNG按当前主角材质清单筛选；环境只发布 `library.json`，停用旧武器和表面材质分包，补齐原先遗漏的主角连击动画分包。源素材、历史工程和本地模型保留，`temp/taptap-resource-plan.json` 与包旁报告的 `sourceAssetFilters` 记录排除项；排除源文件量不等于实际ZIP节省量。

与最近0.3.8游客包比较，完整ZIP从292,936,658降到238,860,125字节（292.94 → 238.86 MB，减少18.46%）；首包本地ZIP仍约1.18 MiB，不能当作全部启动下载量。同版本0.3.8的可运行Web对照（基线补上连击分包）中，三轮交替新建浏览器上下文的启动中位数4.50 → 3.29秒，已加载资源响应体126.07 → 92.30 MB、请求821 → 667。四种区域及往返的纹理分配均减少约112 MiB，开场约446.3 → 334.3 MiB，返回开场恢复同样纹理占用；这些均为Windows Chrome观测，不代表TapTap下载、进程总内存或真机帧率。111项已有测试、类型检查、桌面与844×390横屏操作／存档重载、三位角色当前图谱加载及官方转换／ZIP校验通过；代表场景截图未见构图与外观变化。详见 [`taptap-resource-optimization-validation.json`](taptap-resource-optimization-validation.json)。游客包位于 `artifacts/taptap-size-optimized/`，未上传；真实TapTap启动、前后台恢复、资源重试与十分钟真机内存／帧率仍待验收。

- 资源拆成现有地图、场景、材质、角色、装备和特效 Bundle；保留原素材与 UUID，不重做源资源目录。Cocos 还可能生成内置/WASM分包和被排除历史 Bundle 的空壳，报告分别列出，空壳不算有效内容分包。
- 完整上传 `game.zip` 包含所有分包，不能拿 `initial-payload.local-audit.zip` 上传。首包审计 ZIP 不包含进入场景前按需下载的分包。
- 当前首包内部预算为 **20 MiB**，同时检查原始文件量和本地 ZIP；它是项目预算，不是平台统一限制。完整 ZIP 采用本次后台界面显示的 **小于 300 MB（300,000,000 字节）** 检查。
- 官方概览仍写整包 60M，创建/上传指南写首包 60M+，与后台上传界面的表述不同。报告保留各自依据；不据此臆造“每个分包20MB”或保证平台接收。实际解析、平台首包及真机性能仍需核验。
- 每次输出 `artifacts/<构建名>/report.json` 和 `upload-settings.json`，列出完整包大小与 SHA-256、原始/ZIP 首包、分包清单/依赖、版本、MiniApp ID、最低库待办和上传阻塞项。`localConfigurationReady` 仅代表本地配置；`platformVerified` 独立保留为 false，直到有真实证据。
- 开场依赖量可通过 `report-taptap.py --browser-report <浏览器报告>` 计算，注明仅为 Web 资源图观察，不能用首包数字代替可玩前下载量。

当前外部事项是核对 TapTap 平台账号/认证能力及隐私声明，生成绑定真实 MiniApp ID 的包后上传解析、核对最低库版本并扫码自测。自建登录服务不再是前置事项；提交审核和公开发布另按授权执行。

本轮 0.3.2 验证：102 项客户端/规则检查、两类 TypeScript 检查和配置一致性检查通过；桌面与手机横屏发布预览的移动、攻击、行囊和存档重载无错误/失败请求。浏览器 fixture 验证保存失败阻止重启、后台更新保留持续输入及资源失败重试；这些不是实际平台更新结论。证据索引见 [`taptap-platform-validation.json`](taptap-platform-validation.json)。

2026-11-10 性能首轮优化：复用主角已加载的相同纹理，小地图按探索变化刷新迷雾、普通图标约 10Hz 刷新。同路线 Web 对比的纹理分配减少约 98MiB，场景往返后回到相同纹理占用；这不是 TapTap 进程总内存或真机帧率结论。102 项现有测试、桌面/手机横屏操作及无身份小游戏审计构建通过，设备异常日志与 10 分钟真机复测待完成。详见 [`taptap-performance-validation.json`](taptap-performance-validation.json)。

官方依据：[创建/版本/上传规范](https://developer.taptap.cn/minigameapidoc/quick-start/guide/creation-improvement/)、[运行配置](https://developer.taptap.cn/minigameapidoc/dev/dev-support/config/)、[分包加载](https://developer.taptap.cn/minigameapidoc/dev/tutorial/basic/subpackage/)、[更新管理](https://developer.taptap.cn/minigameapidoc/dev/api/base/update/UpdateManager/)、[Cocos 适配](https://developer.taptap.cn/minigameapidoc/dev/engine/Cocos-Laya-Egret/)、[WASM 后台分包](https://developer.taptap.cn/minigameapidoc/dev/tutorial/performance/launch/wasm-subpackage/)、[旧概览限制](https://developer.taptap.cn/minigameapidoc/dev/tutorial/overview/)、[网络规则](https://developer.taptap.cn/minigameapidoc/dev/tutorial/basic/network/)。

## 平台账号与游戏身份的边界

- `tap.login` 的成功回调只提供临时 `code`；当前把真实平台调用成功记录为 `platform-ready`。不调用服务端 `code2Session`，不取得 openid，不生成或存储游戏登录 token，不将 code 用作用户 ID。状态名不使用原自建账号的 `authenticated`，不宣称完成游戏服务端身份认证。
- 前台恢复期间关闭玩法输入，调用 `tap.checkSession`；失败或超时后重新调用 `tap.login`，重新登录失败则停在重试入口。并发调用合并，销毁后的回调不会恢复玩法。平台未声明固定会话寿命，因此客户端不再自行设置 24 小时 token 期限。
- 普通浏览器为 `preview`，独立游客测试为 `guest`；两者都不冒充 TapTap 登录。普通小游戏构建仍要求真实平台接口与非空凭证。
- 存档仍是现有本机存档，键和格式不变。当前未取得稳定用户标识，不声称账号切换会隔离本地存档；未接入平台云存档或跨设备同步。
- 小游戏账号体系与旧版 TDS 内建账户 SDK 不混用。实名认证、防沉迷是否由当前 TapTap 容器托管及需开通的能力，必须在真实项目后台和真机核实，不能由 `tap.login` 成功推断已通过认证。
- 旧 `services/taptap-auth/` 与旧验证文件只保留历史来源，不由客户端、打包或运行入口调用。

官方依据：[tap.login](https://developer.taptap.cn/minigameapidoc/dev/api/open-api/login/tap.login/)、[tap.checkSession](https://developer.taptap.cn/minigameapidoc/dev/api/open-api/login/tap.checkSession/)、[小游戏登录态管理](https://developer.taptap.cn/minigameapidoc/dev/tutorial/open-capabilities/login-management/)。

## 2026-11-14 贴图与页面预加载

`PreparationResources` 在解除进入游戏的遮罩前准备常用页面底图、完整 33 个技能图标和当前持有／装备的物品图标；切换技能流派复用已准备的素材。保留的是底图 Texture2D，实际页面 SpriteFrame 随页面关闭释放，避免预热引用一直占住临时动态图集。人物预览、四套发型和世界资源继续使用各自的按需生命周期。

装备图谱的 35 款外观已从大图中无损拆成独立 PNG，保留两像素原图边缘和全部槽位切片；三个初始装备图标的 RGBA 预算由约 18.01 MiB 降为 1.74 MiB。完整原图保留在源码中，发布配置排除七张已替代的大图。复核命令为 `python tools/prepare-equipment-icon-crops.py`；重新生成用 `--write`，原始图谱及逐图验证保存在 `source-art/performance/equipment-icon-crops-v1/`。

`python tools/prepare-mobile-textures.py` 核对 18 张大型不透明颜色图的 ASTC 4×4 / exhaustive 预设，`--write` 更新导入配置。保留原始 PNG 回退、不改分辨率；透明发丝／精灵、UI、法线和 ORM／粗糙度不参与此压缩。桌面 Web 预览的 PNG 回退结果，以及当前 Android 模拟器的 ASTC 路径结果，不能冒充 TapTap／iPhone 的原生 ASTC 或温升验收。引擎内存归因、预加载成本与最终对照见 `taptap-texture-runtime-validation.json`。
