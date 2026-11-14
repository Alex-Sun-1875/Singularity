# Cocos 功能模块与剧情过场

2026-11-11 起采用。当前主工程仍为 Cocos Creator 3.8.8 / TypeScript，发布目标仍为 TapTap 小游戏。

## 目录与职责

```text
src/cocos/assets/scripts/
  app/                   启动、主循环、HUD 组合、菜单路由、生成版本信息
  core/                  跨功能状态契约与 GameSession 会话编排
  platform/              TapTap 登录、更新、存储与 Cocos 生命周期适配
  shared/
    assets/              统一资源访问、分包与缓存
    input/               输入归属
    ui/                  字体、颜色语义、皮肤、边框和公共菜单组件
    i18n/                无 DOM 的 i18next 适配
  features/
    cinematics/          全部剧情过场
    campaign/            战役事件、敌军波次和奖励内容
    journey/             章节任务与引导
    combat/              战斗规则、敌人行为与战斗反馈
    progression/         属性、技能成长与配置
    equipment/           装备、掉落与行囊
    crafting/            锻造
    persistence/         存档及持久化校验
    actors/              2D/3D 人物呈现
    world/               地理、环境、场景与碰撞
    navigation/          寻路、小地图与镜头辅助
    portals/             传送入口
    automation/          自动操作
    dice/                掷骰呈现
    audio/               音频
    loading/             加载界面
    debug/               开发调试呈现
```

功能内以 `common/` 保存不依赖 Cocos 的规则、类型及布局计算，以 `data/` 保存内容，以 `runtime/` 保存 Cocos 呈现与接入，以 `locales/` 保存该功能的词条。已有资源路径、场景 UUID、存档键、剧情 ID 和回执 ID 保持稳定。目录改动同时搬迁 `.meta`；生成工具必须同步修改输出路径。

参考 dsh 的功能归属与模块内词条，以及 slash 的共享国际化库、功能命名空间与公共逻辑分层。参考项目仅供结构比较；没有复制其产品业务代码，也没有引入 Cordis、React 或桌面架构。继续复用 Cocos、公共 UI 和现有平台资源层。

## 剧情过场

`features/cinematics/` 集中管理当前全部 21 段过场、54 条对白。章节内容在 `data/chapter-1.ts`、`data/chapter-2.ts`；`CampaignScenes.ts` 是显式内容入口。

- `common/CampaignDirector.ts`：触发、排队、已看回执；存档逻辑不依赖字幕与镜头。
- `common/CinematicTypes.ts`：稳定内容契约；文案使用语义键。`focusActor` 指向已有场景人物，仅在该人物实际存在时参与取景。
- `common/CinematicLayout.ts`：设计尺寸、触控区、两行分页和阅读时间。
- `runtime/CampaignPresentation.ts`：播放编排、推进、跳过、暂停、收尾与 HUD 恢复。
- `runtime/CinematicSubtitles.ts`：柔和渐变、说话人、字幕及两个文字按钮。
- `runtime/CinematicCamera.ts`：等距中景、取景与恢复；不会逐句重新拉近。
- `runtime/CinematicCues.ts`：保留原有烽光、炉心、号令等提示，与字幕和镜头分离。

统一对齐确认稿 `source-art/ui/campaign-dialogue-v1/cinematic-dialogue-proposal-v2.png`。844×390 逻辑参考下，正文 18、行高 27、说话人 14；正文中心参考为 `(422,323)`，说话人中心 y 为 274。独立控制触区至少 48×48，相邻区域至少间隔 8。安全区约束优先于图片中的固定边距。

UI 取消实心上下黑条、常驻章名、句数、边框和大按钮。底部为 148 逻辑像素高的柔和黑色渐变；右上“跳过剧情”，右下“继续”。正文不缩字，长句按阅读宽度分页。点击空白不推进剧情。进入 180ms、换句 120ms、退出 160ms；减少动态时直接显隐并停止缓慢取景。

剧情播放暂停正常规则推进并清空输入；失去允许条件或进入后台时隐藏字幕与临时演员，保留当前句与页；结束后恢复镜头位置、旋转、缩放及 HUD。跳过只完成原有已看回执，不直接结算任务或额外奖励。剧情回看读取同一份已翻译内容。

设计稿中的生成场景只作构图参考。实装使用真实游戏场景和人物，不把设计图当成已完成的角色动画、矿区救援或交火镜头。

## 翻译

使用已安装缓存中的 i18next 26.4.0（MIT），仅核心库；全部词库随包携带，不使用浏览器语言探测、网络翻译、远程词库或 URL 参数。共享入口为 `shared/i18n/Localization.ts`。界面通过 `PlatformServices` 保存剧情语言偏好，设置 → 旅途 → 剧情语言可切换简体中文和 English。

`features/cinematics/locales/zh-CN.ts` 是键集合基准，`en.ts` 使用同一键类型强制覆盖，`index.ts` 只注册 `cinematics` 命名空间。所有 21 段过场的标题、说话人、54 条对白、推进／跳过和剧情回看操作均已接入，共 104 个词条。其他功能的中文内容尚未翻译，因此设置名明确为“剧情语言”；不宣称整个游戏已经支持英文。

新增功能词条放入自身 `locales/`，命名使用稳定语义键，不以中文原句充当键。不要把存档 ID、玩法比较条件、平台错误码、资产路径或关卡 ID 翻译成本地化文案；参数用 `{name}` 插值，避免在 UI 内拼接可翻译句子。

## 维护与验证

迁移表见 `script-migration.json`，记录 136 个原脚本的目标路径和原 UUID。启动场景继续引用原 `ChapterGame` UUID。`tools/taptap-config.cjs`、资源分包生成器、玩法数据生成器、资产流水线、既有检查和文档代码链接均指向新目录；生成的版本与登录配置仍由原构建流程管理。

验证复用 `npm run check`、`npm --prefix src/cocos run check:core`、`npm test`、`npm run check:tap`、`npm run build` 和真实 `concept-2d` Web 画面。静态设计、Web 与本地构建不能代替 TapTap 真机验收。运行截图、各过场覆盖、触控、前后台及恢复结果见 `test-results/cinematic-v1/`。

依据：[Cocos 资源工作流与 meta](https://docs.cocos.com/creator/3.8/manual/en/asset/asset-workflow.html)、[Label 公共 API](https://docs.cocos.com/creator/3.8/api/en/class/Label)、[i18next API](https://www.i18next.com/overview/api)。
