# 剑与火 · 余烬边境（0.1 可玩原型）

独立、原创程序绘制的 2D 俯视角 JS 探索动作游戏。目标是先验证「剑击击退 → 火油连爆 → 探索遗物 → 流派强化」的爽感，而非定时重开的肉鸽。三片连续区域和一名守门 Boss；体验长度目标 5–10 分钟，尚未经过真实玩家时长校准。

## 立即试玩

零依赖，不需要 npm install。推荐 Node.js 20 或更高。

```sh
cd Singularity
npm run build:web
# 用浏览器打开 dist/sword-and-fire.html（完全内嵌，离线浏览器预览）
# 或在有长期进程支持的本地/云终端启动：
npm start
# http://localhost:8080；PORT=8081 npm start 可换端口
```

云工具的单次 exec 网络/进程可能隔离，输出“预览地址”不代表另一台浏览器一定能访问。此时下载/打开自包含 HTML，或者在浏览器同一机器的终端运行服务。不需要账号、广告、付费素材或外部请求。

## 操作

| 操作 | 桌面 | 触屏 |
|---|---|---|
| 移动 | WASD / 方向键 | 左侧摇杆 |
| 瞄准 | 鼠标；不用鼠标时跟随移动方向 | 攻击时自动瞄准附近敌人 |
| 剑击 | 左键 / J，可按住 | 剑击按钮 |
| 冲刺 | 空格，冷却约 1 秒 | 冲刺按钮 |
| 投掷火油 | F / K，消耗有限火油 | 火油按钮 |
| 互动 | E | 互动按钮 |
| 流派升级 | 1 裂岩刃 / 2 焰心，各 35 金 | 左上升级按钮 |
| 暂停 / 帮助 | Esc 或右上按钮 | 暂停按钮 |

- 左侧篝火互动：恢复生命、补满火油并设定检查点。
- 红色油桶可被剑和火引爆，相近油桶连爆；爆炸和剑击均可击退敌人。
- 敌人可被推落深坑，玩家自身不会误走入坑。敌人出招前有红圈预警，冲刺期间免疫近身攻击。
- 紫色遗物提供金币，黄色补给恢复火油，绿色补给回血；满状态不会浪费补给。
- 清空本区域敌人，靠近右侧光门互动前进。最后一关击败 Boss 后在光门互动通关。
- 失败回到最近篝火检查点，不从整个流程第一关强制重开。
- 战斗/拾取等进度会写入当前浏览器本地存储；区域入口创建检查点。关闭页面前暂停/隐藏也会保存。失败时保存检查点，防止重新加载后 1 HP 复活。
- “新的旅程”会覆盖当前浏览器存档。存档不跨浏览器/设备；隐私模式、禁止存储、file:// 的浏览器策略可能使存档不可用。

## 实现与验证

```sh
npm test          # Node 内置测试器：核心逻辑与 Tap 模拟 API 回归
npm run check     # 所有源文件语法 + 两个 bundle 可解析
npm run build:web # 自包含 HTML 原型
npm run build:tap # 实验性无 DOM Tap Canvas JS bundle
```

- `src/core.js`：纯游戏状态/规则，无 DOM/BOM，无外部依赖，可迁移到 Cocos 组件。
- `src/render.js`：Canvas2D 原创程序美术，摄像机、HUD、小地图。
- `src/browser.js`：浏览器键鼠、多指触屏、暂停、localStorage 与可关闭合成音效。
- `src/tap-adapter.js`：保守的 Tap Canvas/触摸/存储适配实验；双指按 identifier 分离，取消清理，后台保存并暂停。
- `test/`：核心回归、长时间有限值检查、DPR/多触点/后台恢复模拟。模拟测试不等于真机验证。
- `dist/sword-and-fire.html`：自包含浏览器试玩文件。

## TapTap / Cocos 边界（重要）

**当前不是已验证的 TapTap 可上传包，也不是 Cocos Creator 工程。没有发布、登录开发者账号、申请权限或上传。**

当前云环境是 Linux，未发现 Cocos Creator；因此先建立可迁移 JS 核心，不安装非官方 Linux 构建或大型兼容层。未来在支持的 Windows/macOS 环境安装官方 Creator 后，可保留规则代码，改用 Creator 场景节点、输入组件和其平台导出链路。

`tap/game.js` 是本项目小型 CommonJS 打包器生成的实验脚本；`tap/game.json` 仅保留横屏方向；`tap/project.config.example.json` 是空配置占位，不含臆造的小游戏 ID 或上传字段。需要在官方工具创建项目后使用其实际生成的配置，确认当前适配要求。**不要直接把 tap/ 压缩包当作上架包。**

适配层使用 `tap.createCanvas`、`tap.getWindowInfo`、`tap.onTouchStart/Move/End/Cancel`、`tap.getStorageSync/setStorageSync`，生命周期监听存在时接入。无 `document` / `window`。仍待官方开发工具与真机验证：Canvas 接口支持、横竖屏锁定/安全区、前后台、性能、存档配额、平台小游戏 ID/测试权限、实际打包格式、设备兼容和合规流程。当前适配器窗口尺寸在启动时读取，动态旋转需重启；以横屏为目标。

平台调试可能要求手机与调试端同局域网，当前云环境不保证满足。浏览器 HTML 无外部资源不意味着获得 TapTap 离线小游戏资格或白名单。

官方参考：
- [小游戏运行环境、文件结构、无 DOM/BOM](https://developer.taptap.cn/minigameapidoc/dev/tutorial/overview/)
- [引擎接入](https://developer.taptap.cn/minigameapidoc/dev/engine/Cocos-Laya-Egret/)
- [窗口信息](https://developer.taptap.cn/minigameapidoc/dev/api/base/system/tap.getWindowInfo/)
- [本地读取](https://developer.taptap.cn/minigameapidoc/dev/api/storage/tap.getStorageSync/)

## 已知原型限制 / 下一步

尚未实现完整 20–40 分钟内容、枢纽建设、复杂支路与攻城终章、剧情系统、精细寻路、打击停顿/完整声音、多槽存档、平台发布审核。敌人直线追击并处理碰撞，可能暂时卡在建筑背后，需要玩家绕行。三关布局复用以集中验证玩法。平衡和游玩时长需要真实试玩反馈。

源码和素材按下列目录保存；未选择公开许可证。概念参考与实际模型分开管理。


## 项目资料目录

- `docs/design/`：11 页设计文档与范围说明。
- `data/story/`：四章剧情、人物、素材清单及内容校验报告；这些是设计数据，尚未接入可玩原型。
- `assets/concepts/`：5 张概念/设计参考；不是实际模型渲染或已配准动画图集。
- `assets/blockout/`：6 个角色、9 个道具 GLB 及静态检查图，仅作内部占位。
- `assets/studies/player-refined/`：25,246 三角面的主角结构研究与 4 张静态渲染，未通过最终美术验收。
- `source-art/`：可编辑 Blender 源场景与可复现生成/验证脚本。
- `tools/story/`：剧情生成、素材清单整理及校验；`tools/design/`：DOCX 构建源码。

**已选美术方向要求较细致的角色外观，不接受明显低模作为成品。所有现有 GLB/静态模型渲染均为内部占位或结构研究；尚无通过验收的最终角色、绑定或动画，也未完成引擎集成。**

### 资料校验与重建

```sh
python tools/story/validate_story.py
python tools/validate_paths.py
# 可选，重建完整设计数据（会覆盖 data/story 中的手工编辑）
python tools/story/build_story_data.py
python tools/story/reconcile_story_assets.py
python tools/story/apply_approved_style.py
python tools/story/register_additional_studies.py
python tools/story/validate_story.py
# 可选：安装 python-docx 后重建设计文档
python tools/design/build.py
```

JSON 内资料路径均相对其所在清单目录。美术重建说明见 `source-art/README.md`。
测试、网页构建和实验性 Tap 构建不需要第三方 Node 依赖；`dist/` 与 `tap/game.js` 为可重建产物，不纳入版本控制。
