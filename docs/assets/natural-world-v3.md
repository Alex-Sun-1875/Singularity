# 地图自然配色 v3

本轮修正全图偏金黄的问题。用户图二的冷灰石砖、苔绿与灯边局部暖光作为材质/照明方向，图一作为真实绿色的方向；没有把参考图的建筑布局搬入玩法地图。旅店保留原家具、隔墙、门洞和灯的位置；其余31区保留原地表、米制UV、原地理位置与图块排列。HUD、角色、武器、存档、导航、碰撞和高度数据均不在本文件所述修改范围。

## 复用与实现

先审查现有依赖、引擎能力、授权albedo与6张环境PNG。工程已经使用Cocos Creator 3.8.8的`builtin-unlit`、`SpriteFrame`裁切、原生平面和alpha test，足以承载这次颜色修正；不新增库、着色器或依赖。官方[无光照材质说明](https://docs.cocos.com/creator/3.8/manual/zh/shader/effect-builtin-unlit.html)明确unlit不受场景光影响，因此旅店整图与物件上已经画入的黄光必须修正源图，单改场景灯颜色不能去除它。

继续直接复用现有木板、石路、土壤、岩石和草地albedo；其来源为Poly Haven/ambientCG的CC0资源，实际SHA与来源沿用`src/cocos/assets/resources/surfaces/pbr-v3/provenance.json`并在本轮`sources.json`再次记录。原木板本身就是灰褐旧木，原cobble也是自然灰，无需另写核心实现或再找一套替代地表。旧`water-v1.png`已经是蓝绿水色，继续原样使用。

`FlatWorldPresentation`默认加载`flat2d/maps/inn-natural-v3`。`FlatWorldLayers`加载独立`flat2d/world/manifest-natural-v3`，保留旧manifest和全部原图。43个图块均按新图实际alpha重查裁切rect，继续由原生`SpriteFrame`生成UV；未沿用未经核对的旧裁切范围。

草地表面使用`(220,234,224)`的自然绿色倍乘，避免继承3D光照版刻意减绿的`(255,216,246)`，保留原草地albedo细节。stone区域土面倍乘从`(190,184,173)`改为中性的`(202,207,205)`，室内地面从`(215,205,191)`改为`(232,235,233)`；岩石图块压亮倍乘改为`(191,196,198)`。地下已有中性压亮继续使用。没有将全场景应用统一灰色滤镜。

## 新资源与来源

所有栅格修改均通过内置`image_gen__imagegen`编辑完成，不使用CLI、PIL改色、图像滤镜、重采样、裁剪或重画。每个输入target均先实际查看，生成结果也逐张目视。原始输出原字节复制到`source-art/maps/natural-v3/`与运行资源目录；原图保留。

| 新图 | 实际尺寸 | 变化 |
| --- | --- | --- |
| inn-natural-v3.png | 1330×1182 | 灰褐旧木地、冷灰边框；红桌布和绿植保色；灯边局部暖光 |
| world-props-natural-v3.png | 1254×1254 | 4×4原图格；林绿树叶、冷灰石/瓦、旧木、亚麻；火/窗保暖 |
| small-props-natural-v3.png | 1254×1254 | 4×4原图格；灰褐家具、自然绿植、冷灰石框；灯烛/火保暖 |
| structures-natural-v3.png | 1254×1254 | 3×3原图格；冷灰石、旧木、水晶蓝、苔绿；原灯保暖 |
| house-natural-v3.png | 1254×1254 | 原单体建筑；灰褐木构、冷灰瓦石、中性灰白墙；原窗保暖 |
| tower-natural-v3.png | 1254×1254 | 原单体塔；冷灰石、真实绿苔、灰褐门/木板 |

完整六条最终提示、内置生成输出路径、输入/输出SHA256、参考图SHA256、真实alpha范围、复用albedo SHA与运行落点见[`sources.json`](../../source-art/maps/natural-v3/sources.json)。生成过程为六次独立内置图片编辑，没有声称来自第三方素材库。

[`prepare_metadata.py`](../../source-art/maps/natural-v3/prepare_metadata.py)只复制原字节、读取尺寸/alpha、核对SHA并生成JSON/`.meta`；Pillow从不保存任何PNG。可再次运行以复核43个切片的元数据。所有新图实际尺寸与旧图一致，但仍逐一重算rect，因为编辑可能改变细微alpha边缘。

## 已验证与限制

源资源检查已确认6张运行图与保存的生成原图SHA一致、5张透明环境图alpha最小值为0、43个图格非空且裁切位于对应图格内、全部旧环境atlas SHA与旧manifest一致。实际运行图不从用户附件路径加载；附件仅作来源审查记录。

资源检查已确认6张图/43个图块与原图SHA。之后的统一构建复用了既有类型检查、95项规则检查、合法指令首章通关和32区加载/销毁审查；未新增测试框架或依赖。自然色世界与图库的原生视觉证据见`test-results/natural-v3-final-candidate-qa/`，连续跨区的纹理生命周期证据见`src/cocos/test-results/flat2d-area-review.json`。

用户随后指出地面与主角融色，旅店进一步采用`inn-readable-v4.png`的冷灰风化旧木与适度降低的背景明度，保留现有灯烛局部暖色；人物保持青绿披风、象牙白袖和深棕皮革。新图的原字节与提示/SHA见`source-art/maps/readability-v4/`；正常镜头证据见`test-results/hero-v4-final-preview/`，图库与地图的增量审查见`test-results/natural-v4-gallery-final/`。

图像编辑按提示与人工目视保留地图布局/atlas网格，不声称每个家具细节或轮廓像素与原图完全相同。图块仍共享原有建筑家族，不是32区独绘；既有方向、遮挡、地图整图与原碰撞之间的局限继续存在。浏览器手机尺寸检查不代表实体手机帧率、发热或内存验收。
