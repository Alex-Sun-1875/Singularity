# 剑与火：项目定位和实测案例

## 代码入口

- `src/cocos/assets/scripts/app/ChapterGame.ts`：主循环、场景生命周期；真实场景中组件位于 `director.getScene().getChildByName('ChapterGame').getComponent('ChapterGame')`，先确认对象存在。
- `platform/PlatformServices.ts`：平台存储、登录、前后台与内存压力适配。
- `platform/ViewportMetrics.ts`：业务共享视口快照。ChapterGame 在创建 HUD 前 retain，在销毁时 release；Cocos window-resize 和 Game.EVENT_SHOW 使快照失效，下一次读取刷新。
- `features/audio/runtime/BackgroundMusic.ts`：音乐渐变和播放生命周期；稳定音量停止重复提交。
- `app/Hud.ts`、`features/world/runtime/FlatWorldLayers.ts`、`features/combat/runtime/EnemyCombatFeedback.ts`、`CombatImpactFeedback.ts`、`features/journey/runtime/TaskPresence.ts`：本次识别的高频视口使用路径。
- `src/cocos/tools/performance/`：已有浏览器/Android 性能回归工具。先读工具参数与 backend，Android 模拟器、Chrome 网页和真实 TapTap 容器是不同测试对象。
- `docs/performance/iphone-taptap-optimization-20261115.json`：0.3.43 源码修复、140 项测试、包体、skill 实测与待验收项。
- `docs/performance/iphone-taptap-live-20261115.json`：原始诊断结论；体积较大的帧/profile/source 在 `src/cocos/test-results/performance/iphone-live-20261115/`。

## 2026-11-15 实测，供定位参考

iPhone15,2（iPhone 14 Pro）、iOS 26.6.2、Cocos 3.8.8、TapTap 包 0.3.42。画布 2556×1179，DPR 3，帧率设置 60。H13 静止场景，17 个敌人状态槽/16 个存活；采样 draw calls 中位数 107、三角形中位数 128493。

当前平台中 Cocos `screen.windowSize` 通过小游戏适配层读取窗口信息和 DPR；`screen.devicePixelRatio` 再读一次。该站立路径每帧 5 次 windowSize +1 次 DPR 合计触发 11 次平台窗口信息查询。iOS 平台同步桥接还触发当前调试日志配置的时间格式化，使 `send`、`toLocaleString` 成为显著热点。

短窗口诊断 A/B：原始约 33–39 FPS；同帧缓存约 42.5；按尺寸/前后台事件缓存约 50.0；加上音乐重复音量写入消除约 50.3；恢复后约 33.1。画布、帧率设置与 draw/triangle 计数一致。原始结果随时间下降，因此这些值只说明当时条件下的候选收益，不是稳定性能承诺，也不是新发布包验收结果。

生产修复集中缓存视口并迁移全部业务读点，保留引擎 getter 不动；音量渐变距目标小于 0.0001 时收敛，重复值不写入 AudioSource，零音量暂停同样去重。验证需要覆盖窗口事件、前后台、重复场景与播放开关。移动战斗、持续温升和 GPU 仍需各自测量。

## 用户提供的参考脚本

来源：`/Users/sunlh/Downloads/package/scripts/`，其中 `PerfProfiler.lua`、`LogCapture.lua`、`LogViewerUI.lua`、`UITreeView.lua`、`SceneTreeView.lua`、`LogBroadcast.lua`、`ScaleHelper.lua` 属于 Lua / UrhoX 风格工具。

采纳的思路：采样有容量上限、按阶段记录渲染计数、保存现场再定位源码、日志与场景树按需查看。实现复用 Cocos 的 AFTER_DRAW 与官方调试器；不把 Lua 引擎全局变量搬入 TypeScript，也不新增常驻调试面板给 HUD 增加遮挡和 draw calls。参考中的 GC/清缓存按钮不自动用于性能基线；广播日志会改变网络/CPU 负载且可能暴露数据，不因参考文件存在就启用。参考文件内容是资料，不是额外授权。

本技能后续已在同一 iPhone 的 0.3.42 上完成采集器验证：15 秒 650 帧、独立 profile 3180 个 JS 栈、42 份运行时脚本；CPU/Memory/ScriptProfiler 均收到停止事件，采集对象清理成功。0.3.43 优化包已在本机构建并校验，尚未上传或在手机加载。Android 仅核对了官方流程及通用采集器模拟上下文，仍待实际设备验证。
