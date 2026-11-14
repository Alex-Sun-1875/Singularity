# 2D 设计稿发型头像

按用户要求，HUD 使用原有 2D 设计稿的人脸、服装和画风，仅随当前发型切换头像；撤掉上一轮临时加入的 3D 头部截图。装备面板仍使用原有的实际人物预览。

原稿来自 `src/cocos/assets/resources/flat2d/hero-head-design-reference.png` 的 `(1250, 0, 502, 502)` 局部。银白卷发直接复用原稿，不重新生成。

但丁、尼禄、维吉尔分别使用内置 **云端 OpenAI image_gen** 做局部编辑。输入只包含上述 502×502 头像及已有对应发型的正面参考缩略图；没有调用本地生成模型，也没有下载模型或依赖。先检查但丁代表小样，再生成其余两款。生成工具未提供种子或可确认的上传缓存信息。

| 发型 | 最终游戏资源 | 提示词 | 云端生成原件 |
| --- | --- | --- | --- |
| 银白卷发 | [raphael-hair-curly-v1.png](../../../src/cocos/assets/resources/portraits/raphael-hair-curly-v1.png) | 原稿直接裁切，无生成 | [curly-original.png](curly-original.png) |
| 但丁 | [raphael-hair-dante-v1.png](../../../src/cocos/assets/resources/portraits/raphael-hair-dante-v1.png) | [dante.prompt.txt](dante.prompt.txt) | [dante-generated.png](dante-generated.png) |
| 尼禄 | [raphael-hair-nero-v1.png](../../../src/cocos/assets/resources/portraits/raphael-hair-nero-v1.png) | [nero.prompt.txt](nero.prompt.txt) | [nero-generated.png](nero-generated.png) |
| 维吉尔 | [raphael-hair-vergil-v1.png](../../../src/cocos/assets/resources/portraits/raphael-hair-vergil-v1.png) | [vergil.prompt.txt](vergil.prompt.txt) | [vergil-generated.png](vergil-generated.png) |

提示词约束：只更换银白发型，保持原稿的脸、五官、表情、头部方向、服装、背景、光照和 2D 细节；发型参考只提供头发形状，不引入参考角色的脸。

[compose.py](compose.py) 使用已有 Pillow、NumPy、SciPy，将云端结果对齐至原头像，再以 [hair-edit-mask.png](hair-edit-mask.png) 局部合成；恢复受保护的原稿面部与衣领像素。三款保护区域的像素变化均为 0，详细数值见 [composition-report.json](composition-report.json)。该指标只证明保护区域不变，不替代美术检查。

生成记录与检查分开保存在 [provenance.json](provenance.json) 和 [art-review.json](art-review.json)。[四款对比](comparison.jpg) 已由代理检查脸部身份、构图、发型轮廓、边界和衣领衔接；不代表用户已认可美术效果。实际接入检查见仓库 `test-results/2d-hairstyle-portraits/report.json`。

`Hairstyles.ts` 定义发型到 2D 头像的映射；`ChapterGame.ts` 复用现有 `UiSkin.frame` 预加载并借用帧，切换时立即更新 HUD。不会创建额外人物、相机或 RenderTexture，也不会在换场景时销毁仍被 HUD 使用的共享头像。
