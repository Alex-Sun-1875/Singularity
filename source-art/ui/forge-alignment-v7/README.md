# 工坊全页细节对齐 v7

2026-11-11，按用户提供的[工坊原稿](references/approved-forge.png)和[红框运行图](references/annotated-runtime.png)重排强化页，并统一锻造、强化、传承的页签。

- 页签使用原稿相连的深色／金色金属板，去掉清字残留暗线；标题、装饰线和顶部金币位置重新校准。页签图案放在独立48逻辑像素触控区内，保留8像素间隔。
- 装备列表使用已验收插画和原稿选中光框，不再被细长世界模型缩略图覆盖。防具、首饰使用完整部位名称；物品名、品质和强化等级来自库存。
- 复用原稿房间，避免宽幅旧背景被纵向拉伸。旧武器与文字通过干净边界的确定性插值、邻近墙面纹理与羽化局部覆盖，其他背景像素保留。原稿石台、铭牌、宽刃剑和实时标题叠加在完整场景上；余火锻印状态读取实际记录。
- 主预览保留等级变化、随机操作类型、阶段上限、自身极限、独立金币／废铁图块、居中余额及状态。候选概率、范围、当前最多三条属性和未开槽条件在可点击的独立词条页查看，保留已确认的随机强化机制。
- 恢复底栏“传承预览”，缩短地点提示；确认按钮复用本次原稿金色板。结果页显示本次实际消耗，点击“继续强化”先回到下一次预览，不把下一次费用混进本次结果。

[完整原稿／旧版／新档／16级对照](review/forge-comparison.jpg) · [八处细节对照](review/details-comparison.jpg) · [实际运行效果](review/forge-runtime.jpg) · [词条、结果、传承和锻造](review/workshop-services.jpg)。截图只去除黑边、缩放及排版，没有修图替换运行像素。原稿中的固定“强化威力”属于旧方案，当前显示真实随机候选；费用、极限及物品名称也以实际数据为准。顶部两排导航保留手机触控所需的纵向空间，不宣称逐像素相同。

本轮没有新生图或增加依赖。19项原稿细节通过Pillow裁切、清字、透明遮罩和局部像素合成导出；去字区域复用已安装的NumPy／SciPy插值工具，处理程序见[prepare-assets.py](prepare-assets.py)，来源矩形、处理方式和SHA256见[runtime-assets.json](runtime-assets.json)。旧生成房间与历史素材保留。既有装备插画和剑轮廓继续复用，不宣称所有物品都有独立新原画。源码／构建镜像校验见[build-source-review.json](build-source-review.json)，截图来源见[runtime-review.json](runtime-review.json)，对照排版见[prepare-review.py](prepare-review.py)。

验证复用TypeScript、Cocos Creator 3.8.8构建及现有浏览器检查方式，记录见[16级检查](../../../src/cocos/test-results/forge-alignment-v7/browser-review.json)和[1级检查](../../../src/cocos/test-results/forge-alignment-v7/fresh-review.json)。覆盖844×390、932×430、桌面及与用户截图相同比例的宽屏，检查字体、触控尺寸／间距、只读词条预览、强化与传承的扣费和重复提交保护、结果费用及保存重载。审阅使用隔离存档；16级档通过现有授予与强化接口达到＋3、868金币和96废铁，用户存档不改动。

[默认本地试玩](http://127.0.0.1:7469/?view=2d&player=3d&progression=natural)同步记录见[default-preview.json](../../../src/cocos/test-results/forge-alignment-v7/default-preview.json)。实现与助手运行视觉复核完成，用户最终美术验收待进行；本轮没有上传或发布TapTap版本。Web结果不替代真实AppID及目标设备下的安全区、触控、生命周期、存档、分包与性能验收。
