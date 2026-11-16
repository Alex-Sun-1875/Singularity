# 开发约定

## 开发与设计技能

- 当前 Cocos / TapTap 小游戏开发、修复、构建与交付使用 [`singularity-development`](.agents/skills/singularity-development/SKILL.md)。
- UI、HUD、交互的新增、调整和验收使用 [`singularity-ui-design`](.agents/skills/singularity-ui-design/SKILL.md)，完整长期规范维护在其[参考规范](.agents/skills/singularity-ui-design/references/ui-layout-guidelines.md)。通用前端技能不能替代已确认的项目规则。
- 两个技能的源文件随仓库维护；用户技能目录的入口链接到同一份源文件，避免维护多份规则。

## 当前主目标：TapTap 小游戏

- **用户已明确：当前游戏主要针对 TapTap 小游戏平台开发和发布。** 主工程为 `src/cocos/`，使用 Cocos Creator 3.8.8 / TypeScript，优先适配 Android 手机横屏。功能实现、依赖选型、资源组织和性能优化均应以 TapTap 小游戏运行环境为主要约束。
- **开发必须遵守 TapTap 小游戏官方接口、接入流程和实现规范。** 涉及平台能力、SDK、基础库兼容性或不确定的 API 时，先核对当前官方文档和已有适配实现，再编写代码；不得臆造 `tap.*` 接口、参数、回调或平台能力。
- 涉及登录、存储、云存档、前后台生命周期、网络、文件、触控、音频、桌面入口及商业化等功能时，使用对应的 TapTap 小游戏 API，或已经完成官方平台适配的 Cocos 接口。优先复用现有适配层，集中处理平台差异、错误和恢复，不把平台专用调用散落到玩法规则中。
- 业务代码不得假定浏览器 DOM/BOM、URL 查询参数、网页缓存或桌面文件系统在小游戏中可用。浏览器专用实现应隔离为调试或兼容分支，小游戏的启动、场景选择、存档和核心玩法不得依赖这些分支。Web 预览用于开发验证，平台兼容性须另行验证。
- **TapTap 与 HTML 平台能力分开实现和验收。** 统一按 Cocos 构建／运行标志选择平台，不用 `tap` 等全局对象、资源预览标记或 dev/test/release 猜平台；共用玩法，差异集中到平台适配。所有存档与偏好复用带档位隔离的公共存储，缺失平台能力不得静默换后端。差异表与实施约束见 [平台隔离规范](docs/development/platform-adapters.md)。
- **TapTap 打包统一执行 `npm run pack:taptap`。** 唯一实现为 `src/cocos/tools/build-taptap.cjs`，交付目录固定为 `src/out/<版本号>/`、ZIP 固定为 `SwordAndFire_<版本号>.zip`（英文游戏名取自发布配置的 `projectName`）；`src/out/` 加入 `.gitignore`。不要再创建带任务名或日期前后缀的交付目录，流程和预检见 `src/cocos/release/README.md`。
- 资源、分包、加载与缓存按 Cocos 官方 TapTap 适配流程及 TapTap 小游戏规范实现；复用 `release/taptap.json`、`Build-TapTap.ps1` 和现有资源加载层。分别记录完整上传包、首包及可玩前所需资源量，内部预算与平台实际限制分开标注。
- 验证需覆盖小游戏入口、登录、触控、前后台恢复、持久化、资源分包与目标设备表现；复用现有检查和手动验证。浏览器通过、本地转换成功或无身份审计包均不能替代真实 TapTap AppID 下的平台与真机验收；待验证项应明确登记。
- **旧 TapTap Maker / UrhoX / Lua 工程及其自动维护规则仅适用于历史工程。** 当前主工程使用 TapTap **小游戏**文档与 Cocos 工作流；不得将下方 Maker 专用的文档来源限制、提交/构建流程或资源元数据规则套用到 `src/cocos/`。细则见 [`src/cocos/AGENTS.md`](src/cocos/AGENTS.md)。
- 官方依据：[小游戏文档总览](https://developer.taptap.cn/minigameapidoc/quick-start/document-guide/)、[Cocos 官方适配](https://developer.taptap.cn/minigameapidoc/dev/engine/Cocos-Laya-Egret/)、[分包加载规范](https://developer.taptap.cn/minigameapidoc/dev/tutorial/basic/subpackage/)。

## 打包档位与 release 日志

- 打包区分 `dev`、`test`、`release`。**默认 test；只有用户明确要求 release／正式发布包时才制作 release。** 一次指定不改变后续默认值，已明确指定时不重复确认。
- dev 用于明确要求的开发加速流程，技能采用正常冷却、怪物经验 ×5、取消每日经验获取限制、Boss 分别保底结算传奇与神器；当次明确指定的覆盖优先。加速集中配置，仅对 dev 生效，不污染正常存档和 test / release 的冷却、经验及每日限额。
- test 是采用正常玩法规则的测试包；release 采用正常规则，关闭开发加速与游客绕过。审计／Web 预览和游客登录方式单独记录，不替代三种玩法档位。
- release 必须附“上一已发布正式版本 → 当前产物”的更新日志，覆盖中间 dev / test 的实际变化；归档到 `docs/releases/<版本>.md`，并以 `RELEASE_NOTES.md` 随 release 交付。首次发布、基线缺失、未验收及未上线状态据实说明，不编造差异。
- 详细规则见[开发与打包规范](docs/development/build-profiles.md)。`npm run pack:taptap`、`build:tap` 和脚本无参数均默认 test；显式使用 `pack:taptap:dev` / `pack:taptap:release` 或 `-Profile` 选择档位。三档共用根版本序列，每次实际打包 patch +1，失败不回退、内部重试不重复递增；交付固定为 `src/out/<版本号>/SwordAndFire_<版本号>.zip`，档位单独记录到编译配置与清单。打包不自动授权上传、提审或公开发布。
- 已完成的实际变更追加到 `src/cocos/release/changes.json`。release 自动汇总上一已发布清单未包含的更新条目与源码／资源差异；真实上线后才登记 `release/published-release.json`，打包不会推进正式发布基线。

dev 的“快速验证”仅在暂停和设置 → 旅途中按需开启，提供手动补给、有限材料、等级推进、清除 Boss 再战等待及既有训练场入口；test / release 拒绝执行。工具不在开局自动修改进度，不自动完成剧情或发放未验证来源的装备。

## 项目 Agent Skills

- 项目共享 skill 统一维护在 `.agents/skills/<skill-name>/SKILL.md`，相关脚本与参考资料随 skill 保存；工具专用目录通过链接指向同一份内容。
- 涉及 TapTap 小游戏真机连接、卡顿、发热、内存或性能优化时，读取 [taptap-device-performance](.agents/skills/taptap-device-performance/SKILL.md)。该 skill 包含 iPhone／Android 的准备、连接、采样、分析与清理流程。

## HUD与界面设计

- **默认按iPhone 14及以上机型的横屏规格设计UI。** 基准为2532×1170物理像素、844×390逻辑视口（3倍像素密度），适配Pro/Plus/Max及后续更大视口、刘海/灵动岛和底部手势安全区。TapTap小游戏仍是主要运行平台；不得把物理像素直接当成按钮与文字的布局单位。
- **正常探索和战斗时，HUD不得遮挡游戏的主要区域。** 人物、目标、攻击预警、弹道、移动与交互的观察和操作优先；控件沿边缘紧凑布局，次要内容折叠或按需展示，不得为装饰、对称或完整展开挤占主画面。
- 所有界面新增与调整遵守 [`singularity-ui-design` 技能](.agents/skills/singularity-ui-design/SKILL.md)及其[界面布局设计规范](.agents/skills/singularity-ui-design/references/ui-layout-guidelines.md)。原 `docs/design/ui-layout-guidelines.md` 保留跳转。透明底板、文字及不可见触控区也纳入遮挡检查；控件不重叠或占用面积减小不能代替实际游戏画面的验收。

## 实现与验证

- 优先实现用户需要的功能，以功能可用、满足需求为目标，尽量不要额外编写或扩展测试代码。
- 除非用户明确要求或确有必要，否则不新增测试用例、测试脚手架或测试依赖；验证时优先复用现有检查、构建或手动验证。
- 实现功能前，先检查项目已有依赖、引擎能力，并检索成熟开源库、官方组件和现成资源；优先直接复用，不重复手写已有成熟方案。
- 选型确认技术栈兼容性、维护情况与许可证；自定义代码以接入和适配为主，确无合适的成熟方案时才编写核心实现，并说明原因。

## 图像处理约定

- 裁切、缩放、透明通道、比例对齐、序列帧排版与确定性局部合成优先复用 Pillow、OpenCV 或项目现有工具。
- 自2026-11-08起，生图与生成式编辑默认使用云端 OpenAI image_gen；沿用任务授权，不额外增加逐次确认流程。Qwen 等本地模型不再作为默认方案，也不自动回退本地；只有用户明确要求本地推理时才启动。生成结果与美术验收分别记录，先核实代表小样再扩大批量。
- 已部署的 Qwen/ComfyUI 与历史工作流保留供按需复用。明确使用本地模型时仍按连续空闲600秒、执行/等待队列非空不卸载、到期只释放缓存并保留服务进程的约定执行；正常完成不主动调用 `/free`。不因默认方式改变删除本地部署。
- 云端生成仅提供必要参考图、局部和遮罩；接口支持时复用上传引用。不能确认缓存行为时不声称只上传一次。项目素材保存到仓库，记录提示词、来源与验收状态；概念图不直接冒充已接入的动画、碰撞或玩法。
- 模型、依赖和运行环境下载不得走代理，也不得在直连失败后自动切换代理。下载前核实系统代理、透明代理/TUN 与实际路由，采用显式禁代理的直连方式；更换直连来源时核对官方校验值。
- 角色修图以当前已验收设计为准，统一站姿与动作中的头型、发型、身体尺度及脚部锚点；局部生成后用本地遮罩合成保护其他区域，验收身份、姿势、装备和边缘，不能把“模型运行成功”视为美术验收通过。
- 操作细则、现有启动入口、下载约束和试验记录见 [图像处理规范](docs/assets/image-processing.md)。
