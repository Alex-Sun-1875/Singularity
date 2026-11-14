# FairyGUI 与 MPFB2 实施计划

> **For agentic workers:** 使用 executing-plans 执行主界面接入；独立人物任务按 dispatching-parallel-agents 并行推进。用户要求避免新增测试代码，改用现有检查、构建和实际画面。

**Goal:** 将两项候选变为实际使用的地图 UI 和人物资源流程。

**Architecture:** FairyGUI 官方 Cocos 3 分支固定提交，接入 `MapPanel`，保留 Hud/GameSession 接口。MPFB2 在项目本地 Blender 环境运行，产出兼容现有骨架动作的角色资源。统一运行现有 Cocos 类型检查、本地 Web 构建和浏览器验证。

**Tech Stack:** Cocos Creator 3.8.8、FairyGUI Cocos、Blender 4.5、MPFB2。

**Spec:** `docs/superpowers/specs/2026-11-04-fairygui-mpfb-design.md`。

## Global Constraints

保留 v5 角色与 v3 地理。许可逐项记录。只写接入代码，不写已有成熟算法。保留无关工作区修改，不提交远端。

## Review Focus

重复开关释放 FairyGUI 控件和输入监听；地图遮挡游戏输入；触屏拖动不误触选点；桌面及小屏不溢出；人物骨骼动作及手持道具不退化。

## Tasks

- [x] 固定 FairyGUI 官方版本及 MIT 许可，核对 Cocos 导出与编译兼容性。
- [x] `MapPanel.ts` 接入 FairyGUI 组件、控制器、拖动与事件，保持 `show/key/refreshLayout` 外部接口；更新必要 Hud 生命周期。
- [x] 人物任务安装并实际调用 MPFB2，复用现成资源改善造型/材质，使用现有 Blender 验证工具及实际渲染记录变化。
- [x] 更新开源复用记录、许可与重建说明。
- [x] 运行 `npm run check`、`npm run build`，实际验证地图功能、输入阻断、反复开关和人物渲染，输出实际截图。

记录：FairyGUI 1.2.2 需要 Cocos Mask 显式类名和有符号滚轮适配；Radio 重建推迟到当前事件结束，平移边界完全使用库的 dragBounds。实际浏览器验证切层/筛选/标记、滚轮双向、拖动回拉、十次开关、触屏及横竖屏切换。视窗同步使用引擎 Root.resize 与固定高度策略。审查指出的控件销毁、侧栏重叠、滚轮方向和拖动基线问题均已修正。

早期产物 `src/cocos/artifacts/first-chapter-playable-web-2026-11-04.zip` 为历史版本。2026-11-05 当前默认目标为web-mobile，交付包 `first-chapter-playable-web-mobile-2026-11-05.zip`；最新体积/CRC/SHA分别见 `test-results/build-size.json` 与 `artifacts/test-package.json`。

用户后续要求先研究并制作资源；现已完成暖古铜/烟黑配色、独立UI切图和手机布局接入。人物当前是十名53骨骼/11动作（含walk），以 `source-art/characters/cocos/library-integration-record.json` 为准。最新发布通关、手机动作/UI及真实D20记录在工程README列出的报告中；完整美术与真机性能仍待验收。
