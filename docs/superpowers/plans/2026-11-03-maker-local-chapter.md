# Maker Local Chapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan inline. Steps use checkbox syntax for tracking.

**Goal:** 在当前仓库src下交付可独立运行、无需登录的本地M1小章节。

**Architecture:** 使用官方UrhoXRuntime独立启动。纯Lua规则模块负责状态，真实3D场景负责地图与实体人物，官方UI控件绘制HUD/对白，独立模块处理本地存档。人物以v5造型为准，在本地制作和导入，不依赖云端生成。

**Tech Stack:** UrhoX Lua5.4、NanoVG、urhox-libs/UI、cjson、File、PowerShell。

**Spec:** ../specs/2026-11-03-maker-local-chapter-design.md

## Global Constraints

- Maker本地工程根为src/；旧JS原型列入用户明确授权的全面清理计划。
- 当前用户要求本地完成，不使用云端模型生成，不把登录或绑定作为开发前提；不伪造身份，不擅自提交、构建或发布。
- 1280×720横屏设计；本地功能占位素材不冒称最终美术。
- 官方参考库只读；游戏代码放scripts/，自有素材放assets/。

## Review Focus

- 高帧间隔/斜向移动必须有界，墙和出入口不能穿越。
- 同一箭的出程/返程、雷链和击败奖励不能多次递归结算。
- 保存恢复保留随机结果、已领取物和对话知情状态。
- 损坏存档不能静默覆盖，死亡/暂停不复制奖励。
- 缩放后的鼠标/触摸坐标必须与世界坐标一致，UI不能抢走世界攻击。

## Task 1: 本地环境与失败证据

- [x] 安装官方开发套件与独立Runtime，确认CLI绑定限制。
- [x] 原JS测试基线23/23。
- [x] 创建`src/scripts/validation/TestMain.lua`及规则用例；真实Runtime运行，确认缺失Chapter模块的RED报告。

## Task 2: 章节规则与保存

- [x] 创建`src/scripts/Game/Data.lua`、`Chapter.lua`；公开规则与快照API。
- [x] 覆盖任务流程、墙体、两种传奇、随机结果和奖励幂等；先RED后GREEN。
- [x] 创建`Save.lua`，真实引擎File双槽保存、损坏回退与保护测试通过。

## Task 3: 可玩入口与本地资源

- [x] 创建main/Hud/Scene3D/Environment/SceneInput；旧头像场景已被替换。
- [x] 接入本地v5资料，提供控制界面、对白、背包、暂停与重试；UI回调已验证。
- [x] 创建`src/Run-Local.ps1`，直启官方Runtime；启动无上传副作用。
- [ ] 本地制作或适配v5实体人物网格、材质与骨骼，完成保留动作的引擎格式导入。
- [ ] 导入通过确认的实体人物模型，接入并验证待机、跑动、攻击和受击动作。

## Task 4: 实际运行验收

- [ ] Lua LSP无Error；Runtime规则用例与完整流程验证。
- [ ] 1280×720和窄屏截图，读取真实PNG；受控多帧检查折返箭。
- [x] 当前保留文档链接与入口检查通过；旧JS不作为新版本验收依据。

## Execution Ledger

- 用户要求在当前目录src中开发，因此原地执行，不另建worktree。
- 使用原安装分发及其官方安装脚本；独立Runtime版本20261030-1103-fefb855。
- 开发套件自动生成的AGENTS称“bound”与实际状态不符；以已核实的未绑定状态为准，管理块不修改。
- 未提交Git；已有用户改动保留。
- 规则9项、完整规则流程、真实File存档、UI回调、3D地形/相机测试均在Runtime验证；这些检查不代替实体人物和完整游玩验收。
- 用户否决头像棋子后改用真实3D；最新人物模型与动作尚缺，开局明确显示等待模型，不能标记目标完成。
- 第一次Maker登录等待超时；第二次授权页已打开，CLI会话42839等待用户完成创建token。
- 后续核实：会话42839也已超时退出（exit 1），没有授权凭据；没有自动开启第三次登录。当前原生模型加载接口已通过RED→GREEN；GLB直载失败证据位于src/.tmp/import-probe/。
- Goal continuation: progress — 增加原生MDL加材质导入支持，明确没有骨骼/动作时不能解锁游玩；SceneTests在Runtime先失败再通过。确认本地Blender导出器会丢失Armature，避免作为人物动画导入捷径。当前仍缺用户Maker授权与有效绑定，模型任务未提交。
- 全面删除被自动审批拦截（blocked by policy），没有物理删除旧文件；已提供带路径与保留资产哈希校验的手动脚本。
- Blocked audit: 同一Maker授权/项目上下文缺口已连续出现三轮。当前再次核实pat与tap_auth均missing、project为unbound，src/assets/model不存在。两次登录会话均已超时，未提交模型任务。前一轮属于进展（原生导入接口与验证）；本轮没有可用的授权会话或模型任务可等待。用户选定的v5模型生成和动作验收需要其完成授权，目标标记受阻，不能标记完成或以头像/旧低模替代。
- 当前修正（覆盖上述云端路线）：用户明确表示不需要云端模型生成。撤销登录、Token和Maker项目绑定前置条件；停止云端模型请求。当前缺口是本地v5模型、骨骼与动作，应通过本地制作/适配和原生导入解决。最新阵容、3D画面和动作质量要求不变。
