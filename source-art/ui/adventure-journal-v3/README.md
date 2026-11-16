# 冒险日志 v3 · 对齐现行游戏风格

2026-11-16。根据用户对v2顶部和整体外观的反馈更新设计稿，游戏运行代码、章节与宠物开关没有修改。

视觉基线是[项目UI技能](../../../.agents/skills/singularity-ui-design/SKILL.md)及其[现行视觉风格](../../../.agents/skills/singularity-ui-design/references/visual-style.md)，引用已经确认的管理页与公共Header。v3本身仍是待审稿，不因为引用了公共素材就视作用户已接受。

本稿直接复用原版`prep-header-v2`、`prep-surface-v2`、`prep-logo-v5`、`prep-active-v5`、`prep-rule-v5`、`prep-shell-rule-v5`、`double-gold-frame-rpg-v4`和管理页按钮／选中框。顶部为64逻辑像素行，纯文字页签为72×48，17像素字级，选中文字按公共语义着色并使用原版金线。关闭图形复用已确认SVG，不再增加圆形徽章；这里展示无胶囊遮挡时的右关闭，真正接入须由`GoldPanelHeader`按安全区判断。

任务页保留左树右正文，地图页保留左图例、中地图、右传送点。章节、调查记录、地图标记、迷雾与传送状态均为现有内容的设计示例，不能当作玩家进度、Cocos运行或平台验收。

- `tasks-2532x1170.png`、`map-2532x1170.png`：默认横屏手机稿。
- `*-2796x1290.png`：较大横屏尺寸补充稿。
- `index.html`、`theme.css`：设计源稿。
- `design-spec.json`、`provenance.json`：设计范围与素材映射／哈希。
- `design-review.json`：静态渲染尺寸与字级检查，独立触区至少48、可见文字至少11，非游戏接入验收。

仓库根运行`node source-art/ui/adventure-journal-v3/render.cjs`复现PNG；无需打包游戏，也没有新增依赖。
