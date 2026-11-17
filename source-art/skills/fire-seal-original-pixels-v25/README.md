# 烈焰喷流法阵：直接使用选定原图像素

> 用户继续指出颜色未对齐。颜色、透明度和光晕以 [v26 原稿色彩校正](../fire-reference-colour-v26/README.md) 为准；本页保留纹样与朝向修正记录，不代表颜色已获用户认可。

用户指出 v24 法阵仍与设计稿不同。本次确认两个具体问题：v24 使用生成式重构的扇状内纹和放大的前侧环，改变了原图；小法阵贴地纹理的前后方向也反了，前侧小纹样显示在远端。

本次直接使用最终选定图片中最近的法阵像素。Pillow／NumPy 提取暖色发光部分，再将原图椭圆还原为圆形贴图，保留原有双环、两侧曲纹与前侧小环的位置、比例和自然不规则。没有调用生成模型，也没有重新描出另一套图案。只修正小法阵贴图的纵向 UV，使前侧纹样位于面向镜头的一侧；陨石法阵的 UV 保持。v24 的同色半透明内圈填充、底光流动、火苗动态及渐隐继续使用。

[原图／实际游戏对照](media/reference-vs-native-seal.jpg) · [原图／上一版／原像素提取对照](media/original-vs-redrawn-vs-restored.jpg) · [正常靶场实录](media/normal-training-fire-jets.mp4) · [实际动态图局部](media/fire-flow-detail.webp)

原图为带地面和火焰的 1280×626 合成图，所选法阵直径约 111 像素，没有独立矢量层。其后部中央被竖直火苗遮挡，提取保留图中可见的根部亮纹，不声称恢复了被遮住的原始线条。纹理保留原图的软边，不能将放大后细节不足冒充高分辨率原始素材。实际动态图仅裁切、缩放正常靶场画布；完整视频保留原镜头与 HUD，没有替换材质、纹理或后期叠加效果。

## 来源与复现

- [最终选定源图](../fire-selected-reference-v18/user-selected-effect.jpg)，SHA-256：`52b78fa21809693c830796ed479eb42acb545258f19286c0ff80f1d4acc20b36`。
- [实际提取区域](assets/selected-original-seal.png)、[生产纹理](assets/fire-jet-seal-v25.png)、[提取脚本](prepare.py)、[参数与来源](provenance.json)。本轮生成方式为确定性像素处理，没有新增云端或本地生成结果。
- `python source-art/skills/fire-seal-original-pixels-v25/prepare.py` 仅更新法阵贴图，火焰图集和流动纹理继续复用 v24。
- 复用 `npm run check --prefix src/cocos` 和正常 test Web 构建；`capture.cjs` 使用实际训练场、默认镜头与真实技能输入，录制完整施放及消散。
- `F:/Models/ComfyUI_windows_portable/python_embeded/python.exe` 运行 `media.py`，只复用已有 PyAV 编码视频，不启动 ComfyUI 或本地模型；无新增依赖。

验证见 [verification.json](verification.json)。本轮只调整法阵素材和朝向，伤害、范围、技能结构、冷却及存档规则保持；未打发布包、未升版。Web 验证、用户美术验收与 TapTap 真机验收分别记录。
