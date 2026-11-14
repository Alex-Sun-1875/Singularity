# 可切换发型 v1

> 历史版本：用户随后指出侧面造型及与 2D 稿的差距，后续修改见 [发型重整 v2](../3d-hairstyles-v2/README.md)。下述检查是 v1 当时的工程与渲染记录，不代表用户已认可其美术造型。

保留拉斐尔已接入的银白卷发，新增三款《鬼泣5》角色风格的银白发型：但丁的中长分帘、尼禄的短碎剪裁、维吉尔的整齐后梳。仅更换头发，脸、服装、武器与原有 14 组动作继续共用。

入口：打开行囊（B），点击人物上方的“发型”，选择款式；人物切成头部特写，可拖动或使用转向按钮查看。当前款式带“已使用”标记；浏览器记住选择，链接中的 `hair=curly/dante/nero/vergil` 也可指定款式。头罩照常遮住头发，摘下后恢复选中的发型。

模型：[raphael.blend](raphael.blend)、[游戏 GLB](raphael-polish.glb)。按本轮“头显宽”的反馈，四款统一收紧耳侧与后脑转角；原作卷发保留卷度、UV、权重和材质，只局部调整两侧体积。三款新发型使用现有 Blender/SciPy/Pillow 管线，独立网格、独立 2048 纹理，共用原 Head 骨骼，每次只显示一款。脸和身体网格没有缩放。

造型参考：[官方联动角色视觉](https://tsukuyomi-game.com/jp/)。已检查本地 Quaternius Standard 发型库；现有款式未直接满足这三种轮廓，因此复用已有重建流程制作新发型。没有下载或提取《鬼泣》游戏模型。

三张头发四视图使用 **云端 OpenAI image_gen 内置工具**生成，生成结果与实际 3D 美术检查分别记录：

- 但丁：[提示词](dante/generation-prompt.txt)、[来源记录](dante/provenance.json)。
- 尼禄：[提示词](nero/generation-prompt.txt)、[来源记录](nero/provenance.json)。
- 维吉尔：[提示词](vergil/generation-prompt.txt)、[来源记录](vergil/provenance.json)。

四视图遮罩恢复轮廓，圆润头型约束俯视截面，并保护额前与脸部空间；耳后视为正面不可见区域，以侧/背视图恢复体积。Blender 原生体素重网格、平滑、减面、UV 打包和投射烘焙，贴图完整扩色与线性 mip 过滤。没有新增依赖或测试框架。

保存后结构检查：[source-verification.json](source-verification.json)。实际游戏选择、记忆选择、头罩遮挡及移动端横屏操作记录：[selection/report.json](runtime/selection/report.json)。近景和全身多角度记录在 runtime/after 下。最终图片与界面须以本轮实际 Cocos 渲染为准，源图生成完成不代表模型通过美术检查。

实际对比：[四款发型](runtime/hairstyles-comparison.jpg)、[收窄前后](runtime/hairstyles-width-comparison.jpg)、[八方向预览](runtime/hairstyles-eight-views.gif)。[本地游戏](http://127.0.0.1:7469/?view=2d&player=3d&revision=hairstyles-v1)。

本轮已完成实际渲染检查并更新本地入口：[美术记录](art-review.json)、[入口复核](runtime/canonical-smoke.json)、[安装记录](install-record.json)。四款在本地入口均只显示一个发型，2048 纹理的 12 级 mip 与线性过滤已生效。
