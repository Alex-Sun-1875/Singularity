# TapTap 小游戏主工程（Cocos）

**当前项目主要面向 TapTap 小游戏平台开发和发布，必须按照 TapTap 小游戏官方接口与实现规范开发。** 技术栈为 Cocos Creator 3.8.8 / TypeScript，优先适配 Android 手机横屏。

本目录是用户授权的当前主工程。父目录旧 TapTap Maker / UrhoX / Lua 工程作为历史保留，其文档来源限制、提交/构建流程及资源元数据规则不适用于本工程。

开发、修复和打包使用仓库 [`singularity-development`](../../.agents/skills/singularity-development/SKILL.md)；UI / HUD / 交互改动同时使用 [`singularity-ui-design`](../../.agents/skills/singularity-ui-design/SKILL.md)。

## 平台接口与实现要求

- 涉及平台能力、SDK 或不确定的 API 时，先查 [TapTap 小游戏官方文档](https://developer.taptap.cn/minigameapidoc/quick-start/document-guide/)、[Cocos 官方适配说明](https://developer.taptap.cn/minigameapidoc/dev/engine/Cocos-Laya-Egret/)和已安装插件的接口定义，核实参数、回调、基础库版本及支持范围；不得根据其他平台接口名称猜测 `tap.*` 能力。
- 登录、存储、前后台生命周期等平台能力优先集中接入 `assets/scripts/platform/PlatformServices.ts`；新增能力使用官方 `tap.*` API 或已适配的 Cocos 接口，并处理失败、取消、中断及恢复。未接入或未验收的功能应明确登记，不能用空实现或模拟成功宣称已接入。
- **TapTap 与 HTML 按 [平台隔离规范](../../docs/development/platform-adapters.md) 分开。** 统一使用 `RuntimePlatform` 选择运行平台，独立于 dev / test / release 和分包预览；浏览器全局仅进入 HTML 适配，`tap.*` 仅进入小游戏适配。存档、UI 偏好和地图探索均经 `PlatformStorage`／`PlatformServices` 应用档位前缀，平台缺失不换后端、不伪造成功。已有 Cocos 输入、音频、生命周期适配继续复用，分别记录两端及真机验收。
- Cocos 插件的 `wechatgame` 构建是官方转换流程的中间步骤。最终目标为 TapTap 小游戏，业务实现应核对 TapTap 的能力与差异；不能仅凭微信或浏览器能运行就判定兼容。
- 小游戏入口须显式设置发布场景与人物模式，不依赖 HTML 注入、`location` / `history` / URL 查询参数或其他浏览器 DOM/BOM。网页调试参数和本地试玩特例须与发布配置隔离；不得因调试环境改变正式游戏的存档或规则。
- 资源访问优先复用 `GameResources.ts`、`AssetBundles.ts`、Cocos Asset Manager 及官方适配层。按 [TapTap 分包规范](https://developer.taptap.cn/minigameapidoc/dev/tutorial/basic/subpackage/)组织 `game.json` 的 `subPackages` 与按需加载，处理加载失败和重试；不绕过平台文件、网络及缓存约束。
- 复用 `release/taptap.json`、`tools/prepare-taptap.py` 与统一入口 `tools/build-taptap.cjs`（`Build-TapTap.ps1` 仅转发兼容），默认根目录命令为 `npm run pack:taptap`（test），`build:tap` 与脚本无参数也默认 test；`pack:taptap:dev` / `pack:taptap:release` 显式选择档位，release 仅在明确要求时使用。审计和 Web 验证使用 `npm run build:tap:audit`、`npm run build:tap:preview`。保持现有官方插件与第三方许可来源记录；确需升级或引入依赖时先确认版本兼容、维护情况与许可证。
- 分开记录完整上传包、首包、可玩前资源、内存与帧率。内部体积预算不是平台限制；Web 预览和本地转换结果不是 TapTap 真机结论。发布相关改动应复用现有检查并覆盖实际变动的入口、触控、生命周期、存档与资源加载，不默认扩写测试。
- AppID 必须来自真实小游戏项目；无 AppID 时只制作并标注本地审计结果。上传、提审和公开发布按用户授权范围执行，平台或真机尚未验证的部分如实列出。

代码按功能组织于 `assets/scripts/features/<功能>/`，其中 `common/` 放不依赖引擎的规则与契约、`data/` 放内容、`runtime/` 放 Cocos 呈现、`locales/` 放该功能词条。`core/` 仅维护跨功能状态与会话编排，`app/` 组合功能，`shared/` 维护资源、输入、UI 和国际化公共能力，`platform/` 适配平台；保持已确认的 v5 角色身份与 v3 地理基线。目录、依赖和生成工具规则见[功能模块架构](../../docs/architecture/cocos-feature-modules.md)。

所有剧情过场统一在 `features/cinematics/`，复用公共字幕、镜头、动效、播放与恢复流程，不在玩法类中另画对白框。对齐已确认的 [v4 稿](../../source-art/ui/cinematic-dialogue-v4/cinematic-dialogue-proposal-v4.png)：保持原字号和居中排版、底部渐变字幕、右上“跳过剧情”、右下“继续”；箭头按实际字形中线以几何绘制，取消悬浮皇冠，并在真实场景验收。新文案随功能维护语义键与词库；过场和剧情回看使用统一翻译，语言偏好通过现有平台存储保存，不依赖 DOM 或 URL。

dev 的“快速验证”仅在暂停和设置 → 旅途中按需开启，提供手动补给、有限材料、等级推进、清除 Boss 再战等待及既有训练场入口；test / release 拒绝执行。工具不在开局自动修改进度，不自动完成剧情或发放未验证来源的装备。

## HUD布局约束

默认以iPhone 14及以上机型横屏规格作为UI设计基准：2532×1170物理像素对应844×390逻辑视口（3倍像素密度）。Cocos保持720设计单位高度、约1558设计单位参考宽度，按实际视口与安全区适配；Pro/Plus/Max及后续机型作为主要扩展验收，旧小屏只作补充兼容检查。TapTap小游戏运行目标不变。

**正常探索和战斗时，HUD不得遮挡游戏的主要区域；游戏内容的观察与操作优先于界面装饰和完整展开。** 新增或调整HUD必须遵守 [`singularity-ui-design`](../../.agents/skills/singularity-ui-design/SKILL.md) 的[界面布局设计规范](../../.agents/skills/singularity-ui-design/references/ui-layout-guidelines.md)，采用边缘紧凑布局并保持必要触控尺寸；以实际游戏状态检查主区域遮挡，不能仅以控件互不重叠或透明背景判定合格。

## 公共颜色与状态反馈

- 状态、阵营、伤害类型、装备品质、任务与系统提示的颜色统一定义在 `assets/scripts/shared/ui/FeedbackPalette.ts`，通过 `assets/scripts/shared/ui/FeedbackView.ts` 着色。新增场景复用已有语义；确需新增语义时只在公共配置维护，不在各面板重复写 RGB 或另建配色表。装饰、场景材质与原画颜色仍按其美术规范处理。
- 文字／图标用 `FeedbackView.tint`，血条／进度填充用 `FeedbackView.bar`，绘制前的 Graphics 颜色用 `FeedbackView.ink`；任务状态、伤害和品质先使用公共解析函数。共享 Color 不修改通道，需要透明度时调用 `FeedbackView.color(role, alpha)`。
- 反馈使用实际战斗结果，不能根据数字大小推断暴击，也不能从零伤害推断未命中。生命、身份、异常状态与伤害类型分别表达；颜色之外保留文字、图形或数值。

## 开发与测试约定

- 打包先遵守[开发与打包规范](../../docs/development/build-profiles.md)：`test` 为默认正常测试包；明确要求开发加速时使用 `dev`，技能采用正常冷却、怪物经验 ×5、每日经验不限、Boss 分别保底结算传奇与神器，仅对 dev 生效，存储使用独立前缀；只有明确要求 release／正式发布包时才制作 `release`，须关闭开发覆盖与游客绕过。release 自动从已登记的正式清单汇总更新日志、源码和资源差异，随包交付并在包体校验通过后归档于 `docs/releases/<版本>.md`；完成实际变更时追加 `release/changes.json`，只有真实上线后才登记 `release/published-release.json`。
- dev / test / release 版本共用一直递增的序列，每次实际打包 patch +1、失败不回退、同次内部重试不重复递增。交付固定为 `src/out/<版本号>/SwordAndFire_<版本号>.zip`，不再自定义交付目录或增加后缀；档位进入编译配置与清单。`--check`（兼容 `-ValidateOnly`）不打包、不升版。

- 性能优化保持既有帧率设置，不新增或降低手机帧率上限。用户于2026-11-11明确要求不能用限帧解决发热；优先减少计算、渲染提交、常驻资源和重复分配，并在相同帧率下对照验证。

- 版本以仓库根 `package.json.version` 为唯一来源，统一脚本 `tools/build-taptap.cjs` 在每次正式、测试、游客测试或审计打包前自动 patch +1；Web 预览不递增，同次调用内部重试不重复递增。平时无需手动升版；`npm run version:tap -- minor` / `major` 或指定三段整数版本可用于主动调整基线，下一次打包仍会 patch +1。TapTap 构建自动同步 Cocos package/lock、运行版本、包体与上传清单。平台标识只维护在 `release/taptap-project.json`，不得手改生成的 `BuildInfo.ts` / `TapAuthConfig.ts`，或用微信 `libVersion` 冒充 TapTap 上传最低库版本。发布配置及分包/体积校验见 [`release/README.md`](release/README.md)。
- **打包固定入口为 `npm run pack:taptap`。** Mac/Windows 共用 `tools/build-taptap.cjs`，交付固定为仓库根 `src/out/<版本号>/SwordAndFire_<版本号>.zip`（英文游戏名取自发布配置的 `projectName`），该目录必须由 Git 忽略；不要创建任务名、日期或游戏名前后缀的交付文件夹，也不要复制临时脚本维护另一份流程。先运行 `--check` 可无副作用预检，所有默认检查通过并实际导出/转换后才交付；不把旧 ZIP 当成本次成功结果。
- `npm run pack:taptap` 一键生成带真实 AppID 的上传测试包，允许生成尚有登录服务待办的测试产物，必须如实记录待办并保留客户端登录门禁；`npm run pack:taptap:release` 执行正式发布前检查，仅在明确要求 release 时使用。用户于 2026-11-10 明确授权独立的游客测试包：`npm run pack:taptap:guest` 跳过业务登录，仅用现有本机存档，游戏内与包体标明游客测试；该开关仅允许用于测试包，不用于正式或审计构建。打包不代表上传、登录联调或平台验收通过。

与[仓库根目录的开发约定](../../AGENTS.md)保持一致：

- 优先实现用户需要的功能，以功能可用、满足需求为目标，尽量不要额外编写或扩展测试代码。
- 除非用户明确要求或确有必要，否则不新增测试用例、测试脚手架或测试依赖；验证时优先复用现有检查、构建或手动验证。
- 实现功能前，先检查项目已有依赖、引擎能力，并检索成熟开源库、官方组件和现成资源；优先直接复用，不重复手写已有成熟方案。
- 选型确认技术栈兼容性、维护情况与许可证；自定义代码以接入和适配为主，确无合适的成熟方案时才编写核心实现，并说明原因。
- 确需编写测试时，应验证实际规则状态变化，而不是仅统计内容条目。
