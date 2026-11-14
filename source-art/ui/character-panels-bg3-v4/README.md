# 人物面板细节对齐 v4

2026-11-10，按用户提供的原稿和六处红框运行截图，修正原生 Cocos 人物面板。参考图分别保存在 [原稿](references/approved-character.png)和[用户标注的旧运行界面](references/annotated-runtime.png)。

| 位置 | 本轮修正 |
| --- | --- |
| 导航高亮 | 使用原稿金色光条，修复被后绘制的头部分隔层遮住的问题。 |
| 核心属性分隔线 | 复用原稿渐隐金线与菱形，校准长度、位置及各行间距。 |
| 加号按钮 | 使用原稿小按钮的完整轮廓与加号，替换通用大按钮边框；不可加点时保留禁用反馈。 |
| 战斗属性行 | 移除每行多余的菱形，校准图标比例、文字和数值位置；第四项恢复移动速度，读取现有移动配置。 |
| 当前构筑图标 | 裁掉共享技能图片自带的旧边框，再叠加原稿细切角边框；不修改共享技能素材。 |
| 底栏装饰线 | 恢复长渐隐线和中心菱形，根据状态文字及按钮空间伸缩；可见按钮上移4逻辑像素，触控区域保持原位。 |

[六处放大对照](review/six-details-comparison.jpg)依次展示原稿、用户标注的旧版、修正后的真实1级运行状态。[整屏对照](review/character-comparison.jpg)及[本轮运行图](review/character-runtime.jpg)同时保留。截图仅裁去黑边、缩放和排版，未用原稿替换运行像素。1级角色只显示实际解锁的技能，金币、等级与属性均来自存档，不填入原稿示例值。

本轮没有生成新图；使用 Pillow 裁切、提取细线透明度和制作边框遮罩，保留原稿按钮像素。9项资源的来源矩形与SHA256见[runtime-assets.json](runtime-assets.json)，处理代码见[prepare-assets.py](prepare-assets.py)。[构建来源校验](build-source-review.json)记录了最终源码、资源与C盘构建镜像的一致性；[运行截图校验](runtime-review.json)记录了截图来源、状态和SHA256。[prepare-review.py](prepare-review.py)可重建对照图。

TypeScript检查、Cocos Creator 3.8.8构建及现有111项测试通过。复用[浏览器检查](../../../src/cocos/test-results/ui-detail-v4/browser-review.json)，覆盖844×390、932×430和桌面视口的养成操作、扣费、保存重载及手机48逻辑像素触控区和8像素间隔；另用[1级新档检查](../../../src/cocos/test-results/ui-detail-v4/fresh-review.json)核对844×390和与用户截图相同比例的2048×1017视口。隔离审阅档不修改用户存档。

[本地试玩入口](http://127.0.0.1:7469/?view=2d&player=3d&progression=natural)同步记录见[default-preview.json](../../../src/cocos/test-results/ui-detail-v4/default-preview.json)，入口文件已备份，用户存档未清除。本轮仅更新本地Web预览，没有平台上传或发布。用户最终美术验收待进行；TapTap AppID下的入口、安全区、触控、前后台恢复、持久化、分包与真机性能仍需平台验收。
