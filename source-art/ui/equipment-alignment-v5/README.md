# 装备页对齐与主副手位置调整 v5

2026-11-10，按用户提供的[原稿](references/approved-equipment.png)、[红框运行图](references/annotated-runtime.png)和[主副手目标位置](references/weapon-position.png)调整原生Cocos装备页。

主手、副手移到人物脚下，横向并排，逻辑中心约为(138,300)和(194.3,300)；副手横坐标按实际触控尺寸计算，确保像素取整后仍保留8逻辑像素间隔。人物两侧改为左三、右四个防具／首饰槽。空槽显示暗色部位示意和名称，已装备物品显示正常插画、实际品质边框及选中反馈；没有向库存添加原稿示例装备。

装备页改用已有原稿插画，不再被世界模型缩略图异步覆盖。物品格复用原稿切角边框、选中角饰和空格纹章；强化角标仅来自真实存档。分类改成连续材质底栏，选中项单独发光；分类触控区仍为48逻辑像素高，间隔至少8。列表按真实品质排序，固定规则以“按品质”说明，不画未接入的下拉按钮。“武器”包含副手，“防具”不再重复列出副手。

详情恢复横向武器展示、品质与可装备等级、分栏比较值、细分隔线和来源图案。当前物品的数值、强化词条、上限与来源来自现有装备数据；描述及较多词条在原生滚动区域查看。当前使用按类别复用的插画，不宣称106件装备已各有专属原画。世界模型及其他面板的EquipmentArt实现保留。

[完整原稿／旧版／新版对照](review/equipment-comparison.jpg) · [局部放大对照](review/details-comparison.jpg) · [1级真实运行图](review/equipment-runtime.jpg) · [16级审阅档运行图](review/equipment-developed.jpg)。截图只去除黑边、缩放及排版，没有修图替换运行像素。主副手脚下位置是用户本轮指定的变更；分类栏及首排物品为手机触控范围保留少量纵向空间，不宣称整屏逐像素相同。

本轮没有生成新图，也没有增加依赖，复用Cocos Sprite、Button、ScrollView、UiSkin和Pillow。20项裁切资源的矩形、来源和SHA256见[runtime-assets.json](runtime-assets.json)，可通过[prepare-assets.py](prepare-assets.py)重建。源码和构建镜像一致性见[build-source-review.json](build-source-review.json)，运行截图校验见[runtime-review.json](runtime-review.json)，对照图生成方式见[prepare-review.py](prepare-review.py)。随包字体已核对新增中文，无缺字。

验证复用现有TypeScript、Cocos Creator 3.8.8构建和[多视口浏览器检查](../../../src/cocos/test-results/equipment-alignment-v5/browser-review.json)。另用[1级新档检查](../../../src/cocos/test-results/equipment-alignment-v5/fresh-review.json)核对两个武器槽、插画资源、分类栏，以及实际手机点击副手筛选、选择弓、装备弓、恢复剑和选择主手；隔离浏览器不修改用户存档。[默认本地试玩](http://127.0.0.1:7469/?view=2d&player=3d&progression=natural)同步记录见[default-preview.json](../../../src/cocos/test-results/equipment-alignment-v5/default-preview.json)。

实现和助手运行视觉复核完成，用户最终美术验收待进行；本轮仅更新本地Web预览，没有上传或发布TapTap版本。Web运行结果不替代真实TapTap AppID和目标手机下的安全区、触控、生命周期、存档、分包及性能验收。
