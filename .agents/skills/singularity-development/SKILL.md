---
name: singularity-development
description: "开发、修复和打包 Singularity（剑与火）的 Cocos / TapTap 小游戏。处理 dev、test、release 选择、开发加速机制、版本与 release 更新日志；在该项目的开发、构建和交付任务中使用。"
---

# Singularity 开发规范

## 作用域与规范入口

本技能服务于 Singularity / 剑与火。先从当前工作目录或用户指定目录定位包含 `src/cocos/` 的仓库，读取仓库根及工作目录适用的 `AGENTS.md`。下文代码路径均相对仓库根；经用户技能目录链接加载时，也从实际仓库读取项目文件。其他项目不自动继承本项目的玩法和打包规则。

- 当前主工程：`src/cocos/`，Cocos Creator 3.8.8 / TypeScript，TapTap 小游戏，Android 横屏优先。Maker / UrhoX / Lua 仅用于明确指定的历史工程维护。
- 架构调整先读 `docs/architecture/cocos-feature-modules.md`；保持功能模块、公共状态和平台适配的现有边界。
- 打包、版本或发布任务必须读 `docs/development/build-profiles.md` 与 `src/cocos/release/README.md`，并检查当前脚本的真实参数。规范要求与脚本实现状态分别报告。
- UI / HUD / 交互改动读取仓库 `.agents/skills/singularity-ui-design/SKILL.md`，按其中的设计规范执行。

## 实现与验证

- 先检查已有依赖、引擎能力、公共组件与成熟方案，再实现功能。引入方案时确认兼容性、维护情况和许可证；没有合适方案时说明自定义实现的原因。
- 平台能力先核对当前 TapTap 小游戏官方文档、Cocos 官方适配和已有接口定义；不猜测 `tap.*`。优先复用 `PlatformServices.ts`、`GameResources.ts`、`AssetBundles.ts`，集中处理失败与恢复。
- 小游戏入口、核心玩法和存档不得依赖 DOM/BOM、URL 参数或桌面文件系统；浏览器调试分支与小游戏配置隔离。
- 优先完成功能，复用类型检查、已有规则检查、构建和手动验证；除非用户要求或确有必要，不新增测试、脚手架或测试依赖。
- 性能优化保持既有手机帧率，不以新增限帧或降低帧率上限解决发热。
- 浏览器验证、本地转换、TapTap 平台验证和目标真机验收分别记录；缺少平台证据时列出待验证项。

## 打包选择

| 用户意图 | 选择 | 玩法规则 |
| --- | --- | --- |
| 只说“打包”“测试包”“给我一个包”，未指定类型 | `test`，默认 | 正常冷却、正常经验、正常每日限额，无开发加速覆盖 |
| 明确要求 dev / 开发加速包，或要求在本次包中用加速机制跑流程 | `dev` | 默认技能无冷却、怪物经验 ×5、取消每日经验获取限制、Boss 分别保底结算传奇与神器；当次指定的开关和倍率优先 |
| 明确要求 release / 正式发布包 | `release` | 正常游戏规则，关闭开发加速与游客绕过，附 release 更新日志 |

“开发中”“方便测试”或旧脚本的默认值不构成 release 指令。一次 release 请求不改变后续未指定打包任务的 `test` 默认值。用户已明确指定 release 时直接执行所需工作，不重复索要确认；打包本身不等于授权上传、提审或公开发布。

dev 覆盖须集中配置、只对 dev 生效，并记录本次实际开关；不能永久修改正式数值来临时打包。不得自行增加无敌、无限资源、全解锁等未要求的机制。test / release 必须检查无开发覆盖残留；dev 存档、云存档及排行榜等数据须与正常环境隔离，不清空或覆盖既有正常存档。

`audit` / Web 预览是验证方式，游客是独立登录方式，均不替代 dev / test / release 玩法档位；普通 test 保留正常平台登录，不能自动切游客模式。

## 当前入口与交付

`npm run pack:taptap`、`npm run build:tap` 和脚本无参数调用均默认 test。显式档位入口为 `npm run pack:taptap:dev`、`npm run pack:taptap:test`、`npm run pack:taptap:release`，统一 Node 脚本参数为 `--mode dev|test|release`，兼容入口接受 `-Profile dev|test|release`。只有明确要求正式发布包时才选择 release。旧 `-TestPackage` 作为 test 兼容别名保留；游客测试仍单独使用 `pack:taptap:guest`。`--check`（兼容 `-ValidateOnly`）只检查参数与配置，不升版、不导出。

dev 覆盖来自生成的只读 `shared/BuildProfile.ts`，导出与转换核对实际编译标记，不能靠改包名转换档位。dev 在平台存储层使用 `singularity.dev.` 前缀隔离所有本机数据，打包结束或失败后恢复编辑器的正常 test 配置。无冷却保留动作与资源消耗；经验倍率只作用于怪物奖励，不放大任务经验；每日经验不限同时跳过共享限额、挂机子限额及其衰减。 Boss 每次有效击杀按当前职业与章节分别结算一件传奇和一件神器，未拥有优先；唯一装备已集齐或数量已满时沿用原重复补偿。保留真实击杀、复战间隔、拾取与来源凭证校验，不通过加载同一尸体重复领奖。test / release 保持正常概率与保底，并拒绝 dev 强制掉落凭证。规则变更会更新编译标记的配置摘要，旧包不能只改名或改报告冒充新规则。

dev 另提供按需点击的“DEV 快速验证”，入口在暂停与设置 → 旅途：补满生命／职业资源、补齐药水、金币与锻造材料补至 9999、等级＋5／升至40级、清除 Boss 再战等待，并可进入既有技能训练场。操作通过 `GameSession.developmentTools` 集中处理，test / release 禁止执行。新旅程不自动补给或升满级；死亡、剧情、装备凭证、消耗与真实再战仍沿用正常流程。验证时区分工具辅助与正常流程结论，工具验证不能用来宣称经济、成长节奏或 Boss 等待已经通过正常包验收。

本地 `Build-Local.ps1` 与 `Build-TapTap.ps1` 共用项目构建锁，忙碌时在改配置或升版前拒绝第二次导出；不能绕过锁并行导出不同档位。

版本只取根 `package.json.version`；dev / test / release 共用一直递增的版本序列，单次实际打包 patch +1、内部重试不重复递增，失败不回退版本，Web 预览和参数校验不递增。交付固定为 `src/out/<版本号>/SwordAndFire_<版本号>.zip`；不创建自定义交付目录或档位后缀，档位单独进入编译配置、说明与清单。保留真实 AppID、现有官方转换、分包与包体检查；不手改生成配置或伪造平台验收。

release 打包须先确定“上次已发布 release → 本次产物”的差异基线，整理功能、调整、修复、兼容／存档变化和已知问题。test / dev 的中间版本不能替代上一正式发布基线；从未发布时写“首次发布”，基线无法核实时明确记录并取得必要信息，不捏造。日志归档到 `docs/releases/<版本>.md`，作为 `RELEASE_NOTES.md` 随本次 release 交付目录提供。内容以实际代码、资源、历史产物与验证记录为据，不照抄提交标题，不把未接入或未验收内容写成完成。

完成功能、调整或修复时，在 `src/cocos/release/changes.json` 追加唯一 ID、分类与实际效果说明；既有已发布条目不改写，新修正用新 ID。`release-notes.cjs` 自动汇总上一正式清单尚未包含的条目及全部源码／资源哈希差异，包括工作区修改；Cocos 导出期间输入发生变化则停止。日志、差异与源码清单进入 ZIP 并随包提供，只有包体校验通过后才归档日志。正式发布基线维护在 `release/published-release.json`；实际上线后才在获授权的任务中执行 `npm run release:tap:record -- <本次交付目录>`，核对 ZIP 与内嵌清单后记录，制作包不自动推进基线。

交付说明写明版本、dev / test / release 类型、实际机制覆盖、登录方式、包路径、日志（release 必需）、验证结果和待办。完整上传包、首包与可玩前资源量分开记录。文档约定、实现完成与包体验证通过必须分别说明。
