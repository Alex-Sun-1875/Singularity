# 手机战斗表现复查 v3

2026-11-04。在实际 Cocos Creator 3.8.8 的 7456 预览中，使用现有 Playwright/Chrome、Android UA、960×540 横屏和 CDP 真实触点检查。未新增测试文件、框架或依赖。此为本机浏览器的手机界面模拟，不能代表真机 GPU / 帧率验收。

## 修复

`Effects.clear(true)` 在暂停时会清掉原生 loop 池。火区原先用 `loops.has('fire:'+id)` 判断新火区，恢复同一火区会重复发射一次 scorch Burst。实际火油投掷复现同一个 `fire:13` 的 scorch 数 1→2；第二次暂停还会继续增加。

现将一次性火区 cue 与原生 loop 池分离，暂停保留 `fireCues`；区域清理时清空，已消失火区的记录及时回收。火焰、余烬和轻烟恢复正常持续模拟，已有火区不重发初始焦痕。最终真实触屏复查同火区 scorch **1→1**，同一剑动作的 burst 总数 **13→13**，暂停时活动发射器为 0。

`VfxAssets` 当前使用引擎注册的完整 effect 名 `particles/builtin-particle` / `particles/builtin-particle-trail`。本轮实际读取材质得到 2 个 pass，并在逐帧采样中确认原生粒子存活及消失，未以角色 state 字符串代替特效验证。

## 实际触屏覆盖

新浏览器上下文从新旅程进入，使用游戏原有装备切换和初始物资，未授予物品、敌人、任务旗标或生命。触屏攻击持续至少 220ms；移动平台不会由桌面键盘后端响应测试键，因此使用真正的 `touchStart` / `touchEnd` 走 HUD 触摸处理。

| 操作 | 实际表现证据 |
| --- | --- |
| 剑击、推击、闪避 | slash / dust / rune 原生粒子，短弧 Line；最终观测 cue 分别约 .1333 / .1 / .0499 秒 |
| 杖 | .2099 秒观察到 .2 秒施法 cue、arcane 发射器和 charge 核心、投射轨迹 |
| 蓄弓 | 持续约 .95 秒蓄力、真实 charged=true / damage=30 箭、箭杆/箭头/尾羽节点及 arrowWake |
| 奥术札记 T01 | 真实消耗、.2502 秒 cue、arcane 投射物与核心 |
| 火油 | 原生 Line 落点/抛物线预览、翻转瓶体、落地爆炸 Burst、持续火/余烬/烟、焦痕及细边界 |
| 暂停 / 恢复 | 发射器停止、既有动作及火区一次性 burst 不重放；自然等待火区/投射物结束后，活动 emitter、粒子、Line、瓶/箭体全归 0 |

某次首次冷帧的剑 cue 直到 action.elapsed=.3595 才被渲染帧观察到；后续剑 cue 在 .1353 左右。软件 GPU、首次创建/编译及截图存在长帧，不能把这项浏览器检查写成首击恒定 .12 秒或手机 60fps 证明；规则的动作时点未改动。

完整输入录像：`src/cocos/test-results/vfx-real-input.webm`。逐帧原生粒子数、动作时间、burst 记录和错误日志：`vfx-real-review.json`。截图为同目录 `vfx-review-{sword,push,dash,staff,bow-charge,bow-release,arcane-spell,oil-preview,oil-flight,oil-fire,mobile}.png`。

## 独立视觉 fixture

T02 / T03 尚不属于初始库存，因此使用**单独复制的纯视觉状态**验证封印、祷文、命中闪光及四种敌预警。未将该状态写回 GameSession；不是无授予通关或真实敌遭遇证明。

- 四种预警（挥击扇形、冲锋通道、短击、瞄准线）同时生成 11 条原生 Line；轮廓贴地，没有填满脚下的大块不透明色面。
- 前摇到 active 时真实 slash / dust 粒子；封印、祷文及命中原生峰值分别 9 / 9 / flash 1，实际材质 pass 正常。
- clear 后活动 emitter、粒子、Line、瓶/箭体均归 0。

证据：`src/cocos/test-results/vfx-fixtures-review.json`、`vfx-fixture-enemy-{windups,active}.png`、`vfx-fixture-seal-prayer{,-hit}.png`。截图已实际查看；火区为低位、低不透明度，角色轮廓和周围地面仍可见。

## 预算与现有检查

最终正常触屏序列的 888 帧采样峰值为 **10 个活动 emitter、3 条活动 Line、62 个同时存活粒子**；按类型逐帧峰值记录在输入报告。既有池上限仍为 56 emitter / 64 Line / 18 投射物体，单 emitter 2–28 粒子容量；没有每帧创建新 Node、追加灯光或全屏后处理。

现有 `npm run check` 通过。现有 `tools/browser-touch.cjs` 的火油取消、蓄弓取消不出箭、取消后闪避均通过，错误 0。未将仅采样角色 state 的动作脚本当作完整 VFX 验证。
