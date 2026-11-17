# 烈焰喷流：原稿纹样、动态火舌与同色法阵填充

> 用户指出此版法阵仍与原稿不符。法阵素材与前后朝向以 [v25 原图像素修正](../fire-seal-original-pixels-v25/README.md) 为准；v24 火苗动态、填充与渐隐继续复用。下文保留当时记录，不代表法阵已获用户认可。

本次按用户选定的 v18 图片修正实际烈焰喷流，取代 v23 的简化花纹与轻微摆动版本。保持五个出火点沿真实施法方向排列，保留选定的高挑、通透橙金火舌。小法阵恢复圆润成对回纹和前侧圆形泪滴；不再使用 v23 的轴向菱形。

用户随后明确要求火焰可以动、法阵内部填充火苗同色。因此本次在同一参考火焰层内制作连续形变帧，原生材质混合相邻帧并向上输送细节；两个弧面保留前后厚度，根部固定在地面。法阵整个内圈使用流动的半透明橙金火光，包含前半圈，双环和纹路更亮，地面仍可透出。材质时间取自游戏时间，结束后火苗降低、底部火光随既有退火曲线渐隐。没有变更伤害、目标选择、真实范围、持续时间、冷却、技能结构或存档规则。

[正常靶场实录](media/normal-training-fire-jets.mp4) · [实录截图](media/normal-training-fire-jets.jpg) · [实际动态局部](media/fire-flow-detail.webp) · [阶段图](media/normal-training-stages.jpg)

实录保留正常靶场 HUD、默认镜头和合法一级技能。使用完整游戏更新和实际技能输入录制八秒；没有换运行模块、覆盖材质／纹理或后期叠加效果。局部动态图仅裁切、缩放同一录像帧。录制使用浏览器软件 WebGL，只证明当前 Web 构建的实际表现，不代表 TapTap 真机性能结论。

## 素材与处理记录

- 造型基准：[用户选定原图](../fire-selected-reference-v18/user-selected-effect.jpg)，SHA-256 `52b78fa21809693c830796ed479eb42acb545258f19286c0ff80f1d4acc20b36`。
- 模式：内置云端 OpenAI `image_gen` 生成式分层提取，不使用本地模型或 API 回退。参考仅提供必要局部。
- 火焰层：[提取提示词](extract-prompt.txt)、[提取结果](reference-flame-layer-01.png)；法阵层：[提取提示词](seal-prompt.txt)、[提取结果](reference-seal-layer-01.png)。原图是带角色地面的合成图，没有可直接接入的透明动画层；分层结果保持原设计方向，不能声称像素完全一致。
- 开始生成的通用图集 `generated-sheet-01.png` 已弃用，`prepare-candidate.py` 仅保留试验记录，不进入当前资源。当前唯一准备入口是 `prepare.py`。
- 本地 Pillow／NumPy 只负责透明边缘、比例定位、预乘插值、连续形变采样与图集排版；不从 JPEG 猜测火焰透明度，不向 PNG 烘焙额外伽马。法阵提取包含近白亮芯，避免原先筛色造成的断线。
- 生产素材：[连续帧图集](assets/fire-ground-jets-v24.png)、[法阵线纹](assets/fire-jet-seal-v24.png)、[流动噪声](assets/fire-flow-noise-v24.png)。填充由原生地面材质在圈内绘制，颜色与火苗同属橙金色系。
- 来源、处理与哈希见 [provenance.json](provenance.json)。生成成功与美术验收分开记录：本地实景检查完成后登记，最终用户验收仍待反馈。

## 复现与验证

`python source-art/skills/fire-jet-native-sequence-v24/prepare.py` 更新素材。复用项目类型检查和 `Build-Local.ps1 -Platform web-mobile -OutputName concept-2d -Profile test` 构建；`node source-art/skills/fire-jet-native-sequence-v24/capture.cjs` 录制普通靶场，再运行本目录 `media.py` 导出媒体与核验记录。

视频编码复用现有 `F:/Models/ComfyUI_windows_portable/python_embeded/python.exe` 中安装的 PyAV 19.0.2；只执行本地媒体编码，没有启动 ComfyUI 服务或本地模型。系统默认 Python 没有 PyAV，需使用上述已有解释器运行 `media.py`，未安装新依赖。

`capture.cjs --study` 额外保存同一暂停帧的显示传递诊断，不改变正常录像帧或游戏时间；这些诊断图不作为交付录像。正式视频直接编码捕获到的正常画布。

验证详情见 [verification.json](verification.json)：核对构建哈希与实际导出纹理、五个喷发点、前后弧面、有界网格、时间推进、暂停重绘、减少动态模式仍持续流动，以及完整消散后的回收。未新增测试依赖、未打发布包、未升版。TapTap 目标设备画面与性能待验证，最终用户美术验收待反馈。
