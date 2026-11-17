# v33 陨石密度、法阵与消散连续性实景检查

只录FIR02正常训练场与空地轮廓两段，各9秒／270帧；沿用正式1级test新旅程 → 既有独立合法满级训练会话 → 正式退出并恢复同一原旅程的流程。无 `test=max`，不改玩法、seed、存档、相机或人物可见性。当前只准备工具，必须等根代理真实完整源码build-ready后才录制，不构建或改生产。

旧v32缺口已逐帧检查：后侧中央在约1.42秒开始收窄，frame82／1.5167秒跨过局部投影映射反折阈值，frame85／1.6167秒后形成明显深V缺口。检查包含frame72–109的38张连续原帧局部，不用4.62秒清空代替消散过程。相同effect key、884顶点、3.8米半径保持，clippedDirections=0；统一tail alpha在1.65秒才开始退，配合匹配历史SHA的非线性screenY导数推导，指向局部压缩反折。证据在 [audit-before/native-gap-audit.json](audit-before/native-gap-audit.json) 与 [逐帧局部图](audit-before/v32-rear-roi-every-frame-072-109.jpg)。

新录制逐帧保留真实事件、落点、meteor鼻锚／target、飞行投影倾角、密集火面inspect、伤害／命中／冷却与生命周期清理。保持真实触地证据：同帧blast.age≤0.045、meteor.progress≥0.999、nose→target三维误差<0.0001米。生产PNG/effect、Cocos导出资源与编译哈希在开始／结束核对。基线使用v32 contact-final的真实80级训练记录；若当前合法满级变化则明确跨级比较限制。

除下落、触地、主爆燃与退尽外，固定保存实际冲击后1.2／1.4／1.6／1.8／2.2／2.8／3.5秒完整原帧，另生成消散阶段拼图、1.2–2.4秒每帧后侧局部图、修改前后1.6秒对照。每帧局部按实际camera投影的事件落点选择，只裁切缩放，不改镜头或补火焰。active记录、顶点数及末帧清理均不能替代实际画面连续性验收。

```powershell
node source-art/skills/meteor-density-seal-v33/capture.cjs --stage final --rank 1 --build-dir <已验证冻结目录>
node source-art/skills/meteor-density-seal-v33/capture.cjs --stage final --rank 1 --empty --build-dir <已验证冻结目录>
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/meteor-density-seal-v33/media.py --stage final --verify-only
```

支持 `--build-dir src/.tmp/meteor-v33-frozen-build`：仅在根代理完成真实构建、逐文件复制并核实SHA后使用。默认仍服务原concept-2d；metadata分别记录sourceBuild、servedBuild与snapshotPath。冻结目录不会受其他聊天重导出原目录影响，编译主文件及实际served import/native资产在录制前后独立校验；workspace source hash仅标为录制启动时采样，不能冒充snapshot编译来源。工具不负责复制或改写bundle。

法阵会另保存无陨石遮挡的实际 `seal-preview-crop.jpg`。`seal-texture-front.png`直接复制所服务构建的native PNG原始字节，附源路径／UUID绑定／SHA；`seal-texture-front-on-dark.png`仅将同一RGBA叠在固定暗底供正视核验。纹理正视图与实际地面透视明确分开，不扭UV或压扁真实范围来套CG。

最终R4恢复原稿卷纹长回旋，并保留规则同心圆边界；R3的等角花瓣与三叶新符号已撤回，不作为最终设计。暖橙／琥珀半透明底色、近纹柔光及卷纹均以正式构建中的实际纹理和实景预告核验；工具不在截图上另加底色或改亮度。只在最终纹理／材质已真正接入、重建并复制验证后的snapshot录制。

`after-r1`／`after-empty-r1`保留为本轮R3旧实景；最终使用独立`final`标签。工具拒绝覆盖已完成capture.json的标签。最终另存原稿图片／R3旧实际截图／R4新实际截图的同量级圈宽颜色对照，只做裁切与等比缩放，保留各自透视，不改色或亮度。

真实native复核符合本轮要求后才编码；原生MP4保持完整HUD、默认4.3镜头、原速9秒，closeup仅裁切原画布。用户美术反馈与TapTap／真机验收另记，不把Cocos曲面／贴图动画称为流体模拟。
