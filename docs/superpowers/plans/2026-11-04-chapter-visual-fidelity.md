# 第一章视觉与可玩表现实施计划

> **For agentic workers:** 按 dispatching-parallel-agents 分工场景与人物，主代理使用执行计划推进 HUD、相机、灯光、特效和集成。用户明确要求尽量不写测试代码，验证优先既有工具与实际画面。

**Goal:** 改善完整第一章实际游戏画面、人物运动、技能、装备和场景细节，使用户要求的视觉与可玩效果更真实。

**Architecture:** 保留 Cocos 3.8.8 与既有规则；新增成熟资产适配和共享库，HUD 复用引擎组件/现成图标与边框，粒子复用引擎模块，人物通过 MPFB/Blender 资产与成熟动作接入。

**Spec:** `docs/superpowers/specs/2026-11-04-chapter-visual-fidelity.md`。

## 执行顺序与当前状态 · 2026-11-05

用户补充：颜色、布局、背景与整体色调参考《博德之门3》，并明确先整体研究，再做本作设计，先完成贴图资源设计。后续以此顺序为准：参考研究 → 材质与界面方向样张 → 设计反馈与资源定稿 → 正式切图/PBR适配 → 引擎接入与全章验收。不得在设计阶段继续扩大运行时功能。

- [x] 查看本地官方设定集人物/聚落/地下与地图界面参考，记录适用原则。
- [x] 产出8张材质候选与1张组合板，保留提示词、真实尺寸、哈希与状态：`assets/materials/chapter-one-v3/README.md`。
- [x] 完成本轮选材、重复平铺/独立UI切图与六套同来源匹配PBR；原图、许可、哈希和尺度边界保留。
- [x] 完成本轮资源的运行接入和实际浏览器检查；未扩展玩法。
- [ ] 按既定参考完成全章正常镜头的最终美术复核、真机性能与平台验收；这些不由本地浏览器检查替代。

### 资源制作进展

- [x] 原创17张SVG/PNG独立UI资源，四按钮态、细框、状态条分层、遮罩、分隔与白枝；九宫格/尺寸/alpha及哈希记录在`ui-kit/skin.json`、`alpha-report.json`。
- [x] 选择6套完整配套PBR候选（24张1024²通道图），保留官方文件原字节、来源、许可与物理尺度。未选的粉黄绿地单独标记为对照。
- [x] Blender同一中性光渲染、源图哈希/官方可用校验、浏览器24通道和UI图片实际载入、窄屏审阅页检查。证据位于`assets/materials/chapter-one-v3/review/`。
- [x] Cocos九宫格与手机独立布局接入，六套PBR以Blender原生流程导出512²运行图并按官方通道打包；实际读取材质defines、法线/粗糙度与10级mip、约24MiB解压显存。
- [x] 复查正常镜头、真实手机触屏、走/跑/武器对应、特效粒子时点/生命周期和发布版UI。
- [ ] 真机GPU压缩策略、完整LOD/常驻环境内存优化及目标设备帧率；本轮PNG/浏览器证据不代表这些已通过。

研究阶段的方向稿与被回退的人物候选继续归档；当前已完成后续运行接入，不能继续将本轮资源描述为“尚未安装”。十名生产人物现在各有53骨骼/11动作，包含walk；当前记录是 `source-art/characters/cocos/library-integration-record.json`，旧候选和旧十动作统计仅作历史。首章最终美术确认及真机验收仍未完成。

粒子内建effect全名已在真实触屏动作中确认有有效pass、原生粒子存活和消失；新增修复火区暂停恢复重复scorch。完整发布版合法命令通关、手机移动/触控/存档、walk/run和武器对应已复跑。发布UI独立报告内D20是展示fixture；真实D20另由固定种子旅程触屏报告证明，不能混用。

## Global Constraints

v5 身份、v3 地理、完整首章任务/装备/存档保留。所有资源许可可追踪。不得把功能检查替代视觉验收。保留无关工作区改动，不提交远端。

## Review Focus

人物在正常镜头的辨识度；脚底滑步和武器握持；场景/特效遮挡交互；桌面与触屏输入实际可用；缓存与切区资源生命周期。

## Tasks

- [x] 场景：`SceneBuilder.ts` + `EnvironmentAssets`，实际复用模型，家具/植物/岩面与室内空间细化；提供 `SceneBuilder.preload()`。
- [x] 人物：现成资产/动作与米制导出适配，十名53骨骼/11动作，主角与弥菈实际HUD头像；保留身份和武器接口。
- [x] 界面：`UiTheme.ts`、`Hud.ts`、`AtlasUi.ts`、`DicePanel.ts`、菜单；桌面紧凑动作栏、手机双指与滚动弹窗、暖古铜材质、图标、装备与技能反馈。
- [x] 镜头/灯光：正常游戏镜头、室内外光色、跟随与共享资源预加载已接入并由本机画面复核。
- [x] 特效：`Effects.ts` 使用 Cocos 原生粒子/Line和许可纹理，实际触屏斩击/命中/燃烧/奥术/投掷、暂停与回收通过。
- [x] 集成：既有类型检查、本地web-mobile构建、合法命令完整通关与手机输入/存档/动作/UI报告。
- [ ] 最终验收：与已给参考一致的全章正常镜头复核、真机触控/帧率/内存、TapTap真实AppID与平台包体验收；不以新增用户确认来停止已授权工作。

## 证据与交付

本地报告位于 `src/cocos/test-results/`：`browser-release.json`、`browser-playthrough-release.json`、`final-mobile-motion.json`、`vfx-real-review.json`、`release-ui-independent.json` 与 `final-mobile-dice.json`。后者使用固定种子19的新旅程，真实触屏选择/掷骰/刷新保持/灵感重掷/拒约与历史通过；不是展示夹具。详情见 `docs/PROGRESS.md` 和工程README。

默认发布目标为web-mobile，包名 `first-chapter-playable-web-mobile-2026-11-05.zip`；完整Web字节由 `build-size.json` 记录，CRC/SHA-256由 `artifacts/test-package.json` 记录。所有浏览器UA/DPR模拟不等于真机实际帧率，不把完整Web压缩包大小称作TapTap首包。

## 后续画面精修 · 2026-11-05

上一轮分类为进展：手机镜头、半球填光和草簇已更新，正式发布包、正常触控与材料/GPU证据已形成。完整目标仍保留；目前主要不足是空间空旷、建筑盒状、角色动作和资源预算仍需更细的实际审查。

- [ ] 场景：在 `SceneBuilder.ts` 内重排旅店地毯/桌椅/生活组合，增加城镇立面层次；保留任务与出口坐标，固体装饰同时进入Navigation/Bullet，避免新增资源堆砌。
- [ ] 人物：只针对真实可见的握持、动作衔接与v5身份差距修正 `Actors.ts` 或现有作者管线；先确认问题，不重新生成已通过的整套人物。
- [ ] 环境预算：审计 `EnvironmentAssets.ts` 整库预载和高位深贴图导入后的实际占用，优先引擎已有资源/压缩能力；若需改变preload接口先统一协调。
- [ ] 主光与集成：使用已有Cocos照明/阴影能力检查暗部与空间层次，所有最终声明依赖重新构建后的正常手机镜头和输入；对照夹具仅用来选择方案。
- [ ] 复核与交付：现有类型检查、受影响场景通行、实际武器/动作、手机存档；最终发布包重新测量/CRC。没有新增测试/依赖、提交或公开发布。

文件分工：场景代理拥有SceneBuilder；人物代理拥有Actors/角色管线；材质代理拥有EnvironmentAssets/SurfaceMaterials；主代理拥有ChapterGame与最终集成。接口变化先沟通，避免互相覆写。

### 本轮已形成的状态与下一步

2026-11-05本轮为进展：旅店/城镇空间与结构UV、林土地表分类、实际闭指/木弓握点、全角色重复180度朝向、装备类别图标/九部位查看均已接入；正式包已重新完整通关。压缩试验没有通过跨后端画质审查，48图恢复PNG，原图未改；软件SwiftShader仍有树枝异色，不能据格式/字节或RTX正常宣称手机硬件已验。

用户再次强调直接复用现成库，后续优先使用原生配套人物/服装/动作。已取得3套官方CC0免费Standard原件，见 `source-art/characters/library-kits/README.md`。原生65骨临时候选已组成并离线验证，不再把旧53骨数量当作产品要求。

- [ ] 用临时导出的完整Ranger/Peasant原生角色在Cocos实际小样中检查行走、握持、.44秒剑击接触与恢复；原贴图通过成熟流程适配手机预算。
- [ ] 为弓与杖补齐确有对应动作的成熟官方库，核实实际免费内容、许可与骨架；不拿营销总数当作已取得资源。
- [ ] 保持v5身份/配色与装备含义，将可用候选接入生产前保存可回退原件；优先模块化原部件，避免重写身体/动画核心。
- [ ] 正常手机镜头审查全章及实际设备性能；完整目标继续保留，不将阶段包或离线人物小样视为整章最终完成。

## 原生资源生产接入 · 2026-11-05

上一轮分类为进展：已取得并核实官方Quaternius角色/衣装/UAL及KayKit弓箭/武器，原生65骨离线小样已形成；不是生产人物完成。现在执行实际接入。

- [ ] 角色：`tools/model-pipeline/cocos_native_characters.py` 从完整原衣装/原头发生成10人，源与候选先放 `src/.tmp/native-production/{source,actors}`，保留原Rig/UV/权重与v5身份、预算；先完成主角/弥菈供引擎审查，再安装生产。
- [ ] 动作：`tools/model-pipeline/cocos_native_motions.py` 输出 `animation/native65-actions.blend` 与manifest。11个精确动作名为 idle/walk/run/attack_sword/attack_bow/attack_staff/spell/dodge/hit/death/interact；原生UAL直接使用，弓仅用已安装成熟BVH Retargeter适配一次，并保留原作者动态hand slot。
- [ ] 武器：`tools/model-pipeline/cocos_native_props.py` 直接适配官方KayKit剑/杖/弓/箭，输出 `props` 候选和握点/Morph元数据，FBX往返保留原拓扑/UV/Draw。禁止重造弓弦、人体或动画求解器。
- [ ] 运行：主代理拥有 `Actors.ts` 与必要的原生材质/装备适配，按manifest读取原骨路径、材质、步幅及握点；用Cocos原生Morph驱动作者Draw，保留旧角色作为可回退原件，不改变规则/存档。
- [ ] 验证：既有资产验证适配实际manifest契约（不把旧53骨当需求），类型检查、原生实际导入/握持/正向步态/出手、移动端预算、32区域呈现与首章合法通关。使用正常手机镜头与录像；离线小样与夹具单独标注。

角色与动作代理协商ActionSlot/rest/helper路径，武器代理提供原握点和Morph接口；只由主代理统一构建，禁止构建目录替换与浏览器资产读取交叉造成假网络失败。
