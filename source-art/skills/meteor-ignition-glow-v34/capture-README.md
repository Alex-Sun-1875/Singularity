# v34 实景录制工具

当前只准备工具。法阵 r2 使用原稿实际 RGB 纹样与每像素明暗，分为 colour RGBA 与 RGB light 两张资源，精确公式记录于 `seal/reference-r2/provenance.json`。未经主代理通知真实构建与冻结完成，不运行 freeze/capture，不把已否定的单 mask 固定双色样张当最终候选。

录制复用正式 test 入口：新旅程为 1 级，点击既有训练场入口创建独立合法满级角色（以实际 `progressionView().maxLevel` 为准），通过既有技能调试菜单装配 FIR02，再用真实 ultimate 输入施放。退出核验原旅程、装备和进度恢复。普通视角与空地 -30° 视角各 270 帧、30fps、9 秒，保留默认相机、完整 HUD 与所有角色；空地只改变合法瞄准方向，不隐藏目标或伪造命中。

主代理完成真实 Cocos 构建、释放锁后可冻结输出；此脚本只逐字节复制与核验，不调用构建器：

```powershell
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/meteor-ignition-glow-v34/freeze-build.py --expected-main-sha <真实mainSHA>
```

它拒绝活动构建锁或非唯一 main，复制前后校验源文件集合与 SHA，再核验副本逐文件一致、设为只读。失败保留未发布副本及失败记录，不删除或重写源目录。`snapshot.json` 与完整 copy manifest 为录制来源证据。

收到主代理 build-ready 与 frozen path 后分别启动：

```powershell
node source-art/skills/meteor-ignition-glow-v34/capture.cjs --stage final --build-dir <冻结目录>
node source-art/skills/meteor-ignition-glow-v34/capture.cjs --stage final --empty --build-dir <同一冻结目录>
```

早段请求年龄为 0/.033/.066/.1/.15/.2/.3/.45/.65 秒。每张只选实际导出的 30fps 帧，标注真实年龄；多个请求可能指向同一帧，绝不补帧、重定时或虚构时间精度。`ignition_review.py` 保留连续早段帧与 `footprintRadius/supportWidth/supportDepth/geometryScale`、`frontRadius/ignitionProgress` 原始字段，缺失字段明确列出。`width` 是世界包围宽度，不能冒充固定承载面大小。数值恒定只验证实现状态，仍需原生画面证明中心点燃、向外传播和局部特征没有整片缩放。

保留真实岩尖触地同帧误差 <0.0001m、落点/预警/命中链、暂停/切职业/减弱动态与最终清理核验。收势保留 1.2/1.4/1.6/1.8/2.2/2.8/3.5 秒代表帧和 1.2–2.4 秒逐帧，不能以末帧清空代替无缺口检查。

素材角色以最终冻结的美术 provenance 为准。脚本只复制 served 资源原始字节作为诊断，不假定法阵必须单 mask 或固定双色，不把任意数据通道贴暗底冒充最终材质。颜色以真实预警截图为主，提供原稿 / v33 / v34 同宽裁图，仅裁切与等比缩放，不改色、亮度或透视。

最终 colour 纹理为原稿去背景后的前景 RGB 与雕纹覆盖 A；light 纹理为原稿逐像素颜色的光场 RGB，A 仅用于极弱吸收，不是直接透明度。复制后同时核对生产 source SHA、served PNG SHA 与 provenance 中的两张资源 SHA。`seal-material-reprojection-non-native.jpg` 只能标为按材质公式计算、同椭圆回投的说明样张，不能当作游戏实景或美术验收。

主代理复核原生早段、颜色与退火后才能执行 `media.py --local-candidate` 编码和 `assemble.py` 汇总。原片完整画布；closeup 仅固定裁切。最终状态为本地候选、用户美术反馈待定，不能声称像素完全对齐原稿或代替 TapTap 真机验收。
