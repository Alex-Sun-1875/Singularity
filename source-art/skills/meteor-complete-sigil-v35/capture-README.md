# v35 实景录制工具

当前只准备工具。v35最终路线使用云端 image_gen 完整化/精修的独立 RGBA 源，再做正圆注册和 colour/light 工程分离；不是旧的 Pillow 后部拼贴。重点核对火红/橙色、纹路清晰、后方完整、源明暗变化，以及落地后保持原位并随余火消散。最终 colour/light/effect 资源与 provenance 以美术代理 ready 为准。未经主代理通知真实构建与冻结完成，不运行 freeze/capture。

最终 r2 provenance 默认 `seal/r2/provenance.json`，以 `capture.cjs --seal-provenance` 可显式覆盖；media 跟随实际 capture 记录的路径，不将旧 r1 provenance 绑定给 r2 served 字节。云端源与prompt仍使用同一已冻结源。最终阶段使用 `--stage final2 --rank 1`，原 `final-r1` 两条保留为 before、不覆写。真实三栏仍原稿/v34/final2，可附 r1→r2 同镜头固定裁区对照，仅裁切/等比缩放。

录制复用正式 test 入口：新旅程为 1 级，点击既有训练场入口创建独立合法满级角色（以实际 `progressionView().maxLevel` 为准），通过既有技能调试菜单装配 FIR02，再用真实 ultimate 输入施放。退出核验原旅程、装备和进度恢复。普通视角与空地 -30° 视角各 270 帧、30fps、9 秒，保留默认相机、完整 HUD 与所有角色；空地只改变合法瞄准方向，不隐藏目标或伪造命中。

主代理完成真实 Cocos 构建、释放锁后可冻结输出；此脚本只逐字节复制与核验，不调用构建器：

```powershell
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/meteor-complete-sigil-v35/freeze-build.py --expected-main-sha <真实mainSHA>
```

它拒绝活动构建锁或非唯一 main，复制前后校验源文件集合与 SHA，再核验副本逐文件一致、设为只读。失败保留未发布副本及失败记录，不删除或重写源目录。`snapshot.json` 与完整 copy manifest 为录制来源证据。

收到主代理 build-ready 与 frozen path 后分别启动：

```powershell
node source-art/skills/meteor-complete-sigil-v35/capture.cjs --stage final --build-dir <冻结目录>
node source-art/skills/meteor-complete-sigil-v35/capture.cjs --stage final --empty --build-dir <同一冻结目录>
```

早段请求年龄为 0/.033/.066/.1/.15/.2/.3/.45/.65 秒。每张只选实际导出的 30fps 帧，标注真实年龄；多个请求可能指向同一帧，绝不补帧、重定时或虚构时间精度。`ignition_review.py` 保留连续早段帧与 `footprintRadius/supportWidth/supportDepth/geometryScale`、`frontRadius/ignitionProgress` 原始字段，缺失字段明确列出。`width` 是世界包围宽度，不能冒充固定承载面大小。数值恒定只验证实现状态，仍需原生画面证明中心点燃、向外传播和局部特征没有整片缩放。

保留真实岩尖触地同帧误差 <0.0001m、落点/预警/命中链、暂停/切职业/减弱动态与最终清理核验。收势保留 1.2/1.4/1.6/1.8/2.2/2.8/3.5 秒代表帧和 1.2–2.4 秒逐帧，不能以末帧清空代替无缺口检查。

新增落地后 .25/.65/1.2/1.6/2.2/2.8/3.5/4.3/4.62 秒真实原帧，分别记录 `ground.inspect.active` 中 `kind=meteorSeal` 的实际 `opacity`。法阵应保持至3.3秒后逐渐淡出、4.62秒清空；`impactAge` cue过期后仍以真实释放事件计算年龄，不将null当零。可见纹路需在原生画面单独审看，不能以地火还亮或active/alpha非零代替。预警提供后方局部与原稿/v34/v35实景对照，原稿已有陨石遮挡保持原样，不用重绘图冒充原图。

既有normal生命周期案例按真实blast年龄推进至约3.7秒的法阵渐退期再暂停。暂停菜单沿现有逻辑隐藏并清空active特效，所以同时只读保存surface池的cached last-draw opacity，明确不冒称可见暂停法阵；核验权威clock与缓存alpha不变、恢复后的ground.active opacity继续下降。重置走既有 `training:reset` 动作且触发前seal仍active；首个FIR→THU原按钮也在active渐退seal上执行。没有新增计时器、场景或玩法改动。

素材角色以最终冻结的美术 provenance 为准。脚本只复制 served 资源原始字节作为诊断，不假定法阵必须单 mask 或固定双色，不把任意数据通道贴暗底冒充最终材质。颜色以真实预警截图为主，提供原稿 / v34 / v35 同宽裁图，仅裁切与等比缩放，不改色、亮度或透视。

最终 colour/light 来自已冻结的云端完整源，其 RGB/coverage/光场分离语义以最终 provenance 为准。复制后同时核对生产 source SHA、served PNG SHA 与 provenance 中的两张资源 SHA。`seal-material-sample-non-native.*` 只能标为按材质公式计算的工程样张，不能当作游戏实景或美术验收。

`art-source-evidence.json` 分开记录云端生成 PNG、generation JSON、prompt 和工程 provenance。生成 PNG 不是实景；计算材质样张也不是实景。真实颜色/明暗/清晰度只从实际 Cocos 预警与落地后画布裁图判断，不在后期改色、提亮或补后圈。旧源/材料方案作为历史记录保留，不混进最终 native 证明。

主代理复核原生早段、颜色与退火后才能执行 `media.py --local-candidate` 编码和 `assemble.py` 汇总。原片完整画布；closeup 仅固定裁切。最终状态为本地候选、用户美术反馈待定，不能声称像素完全对齐原稿或代替 TapTap 真机验收。
