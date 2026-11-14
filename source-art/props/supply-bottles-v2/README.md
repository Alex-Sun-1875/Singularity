# 不透光贴地补给瓶 v2

2026-11-12按用户反馈，修正v1瓶子与阴影随镜头竖起、看似漂浮的问题，并将瓶身改为不透光陶质。

云端OpenAI `image_gen`分别编辑三张v1瓶子参考图，保留圆腹红瓶、棱面蓝瓶、皮带布塞火油瓶的身份，改为正俯视侧躺姿势、哑光不透光材质。只提供512像素参考小图；完整提示词见[prompts.json](prompts.json)，原始生成结果在`raw/`，缩小的输入参考在`refs/`。未使用本地生成模型。

用户随后要求高度一致，蓝瓶追加修改为较宽的棱面瓶型，提示词见[focus-height-prompt.txt](focus-height-prompt.txt)，初版偏细的蓝瓶只作为生成历史保存在`raw/focus-initial-slim.png`。

`tools/design/prepare-supply-bottles-v2.py`复用Pillow和v1元数据生成工具，三瓶轮廓高度统一为136像素、共用0.56米的画布尺度，保持各自瓶型比例。瓶身内部alpha统一为255，仅在轮廓保留抗锯齿，在瓶身下方合成紧贴的中性接触阴影。图片外部保持镂空，避免地面出现矩形底板。运行图是三张256×256 PNG，保存在`src/cocos/assets/resources/equipment/supplies-v2/`，通过已有装备资源包加载。

地面呈现不再让补给朝向镜头：正俯视图映射至世界XZ水平面，四个顶点分别采样实际地形高度。瓶子与接触阴影共用网格，以8毫米间隔避免与地面争抢深度，不添加原有半图高的悬浮偏移。每堆使用由掉落ID决定的固定朝向，读档保持一致，不同掉落自然错开；不会随镜头旋转。装备掉落沿用已有呈现。

来源、生成成功与美术验收分开记在[provenance.json](provenance.json)。本地验证记录及画面位于`test-results/supply-bottles-v2/`；TapTap包与真机验证另行进行。
