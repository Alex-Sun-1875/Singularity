# 统一护盾效果设计 v20

后续脚部包覆已按用户反馈修正，最新运行图与验证见 [v21 脚部修正](../unified-shields-v21-feet/README.md)。下文 v20 录制保留作历史对照。

用户已批准按此稿实施，见 [确认记录](acceptance.json)。本轮原生 3D 接入说明及验证边界见 [runtime-implementation.md](runtime-implementation.md)；下文保留原设计阶段说明，原设计合成动画不冒充运行录像。

实际产物：[四系运行效果](media/unified-shields-runtime.mp4)、[运行对照图](media/unified-shields-runtime.jpg)、[实际击破](media/shield-break-runtime.mp4)。类型检查、已有两项护盾规则用例、Cocos Web 构建和五段原生场景录制均通过；移动跟随、暂停不重播与清理检查见 [runtime-verification.json](runtime-verification.json)。运行录制没有脚本／纹理覆盖或护盾图片后期合成。TapTap 真机效果与性能仍待验证。

用户要求：整体重新设计护盾，共用同一套效果，仅花纹与颜色不同。当前交付为设计稿和合成动画，不接入正式游戏。

## 设计

- 所有实际护盾共用全身半透明立体护罩，外形、尺寸、轮廓光、透明度、成形方式、维持方式、受击与消散一致。护罩比人物稍高，留出武器和动作空间；主体仍可看清。
- 战士：银金刃纹；弓系：青绿风纹；火系：橙金焰纹；雷系：蓝紫雷纹。只有颜色和纹样曲线不同，没有按职业额外增加火焰、闪电、金属甲片或其他不同动画。
- 共用节奏：0.32 秒由下向上成形，维持时轻微呼吸；受击时在接触侧出现约 0.22 秒局部波纹；自然结束约 0.48 秒逐渐淡出；击破约 0.28 秒碎光淡出。
- 稀疏粗纹沿护罩曲面分布，不给中心增加徽章或遮人的纹样。这里的纹样借用先前职业稿的曲线语汇，移除了原法阵的双地圈、中心徽记和直线辐条；不会在地面放一个范围技能法阵。
- 预览用同一现有 3D 角色和相同机位对比材质，避免人物差异干扰对比。护盾时长、吸收量和冷却仍应读取原有玩法状态，不通过此设计给职业新增护盾技能。

数值仅为设计播放参数，不是已调好的正式技能参数。适用范围为真正产生护盾状态的主动、被动或装备效果；纯减伤、闪避等不同状态的归属要在接入时核对，不因视觉统一自动改写规则。

## 交付

- `media/unified-shields-design.jpg`：四系对照与共同动画分镜。
- `media/unified-shields-motion.mp4`：四系同屏、5.5 秒、30fps，共同展示成形、维持、受击和自然结束。
- `media/unified-shields-motion.gif`：同过程的较小预览。
- `media/shield-break-study.mp4`：共用击破节奏，火系配色示意。
- `assets/*-shield.png`：静态透明设计合成层；不是引擎已经使用的材质或精灵资源。

## 来源与图像处理

本轮使用 **云端 OpenAI image_gen 内置工具** 生成一份公共护罩素材，两次输出均存档在 `raw/`。完整提示词为 `prompt-shell-v1.txt` 与 `prompt-shell-v2.txt`。

第 1 次输出轮廓的环带过宽，不用作最终材质。第 2 次只修正透明薄膜与细边缘，用作共同材质源。生成完成与美术验收分别记录：**已生成并完成合成稿；尚待用户美术审阅**。

必要参考仅提供现有原生角色画面的小裁切 `inputs/native-player-crop.png`，原始帧来自 `src/.tmp/fire-kit-showcase-v19/current/FIR_03/000.jpg`。参考用于镜头、风格与尺度；原始角色、武器和地面像素没有交给模型重绘后替换。

后期由本地 Pillow / NumPy / PyAV 完成：公共透明度与轮廓裁切、等比锚点、四系确定性着色、既有内纹提取、曲面投影、成形和消散示意、文字排版和编码。没有启动本地生成模型。

纹样来源为 `../reference-seals-v3/assets/{WAR,BOW,FIR,THU}.png`。提取内纹、粗化可读线条后投影到同一个护罩曲面；不把整张平面地圈贴到人物身前。详细源文件 SHA256 和编码检查见 `verification.json`。

这是后期合成设计动画，接触波纹为设计演示，不是实际敌人伤害事件。引擎深度遮挡、人物移动时的跟随、真实命中面、材质渲染和 TapTap 真机性能尚未实现或验收。本次没有改动 `src/cocos/` 的源码、资源、技能规则、版本或包。

## 复现

```powershell
& 'F:/Models/ComfyUI_windows_portable/python_embeded/python.exe' -X utf8 source-art/skills/unified-shields-v20/prepare.py
& 'F:/Models/ComfyUI_windows_portable/python_embeded/python.exe' -X utf8 source-art/skills/unified-shields-v20/render.py
```
