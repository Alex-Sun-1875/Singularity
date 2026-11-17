# 陨石落点法阵动画设计

当前使用范围按用户最新意见限定为陨石落点，对应技能 FIR_02。其他技能均不使用这套法阵。银金、青绿、蓝紫三套纹样作为设计素材保留。

[陨石法阵动画](media/fire-area-seal-motion.mp4) · [内嵌动画 GIF](media/fire-area-seal-motion.gif) · [陨石法阵静态效果](media/fire-area-seal-effects.jpg) · [四职业修订版预览](media/profession-effects-v3-3d.mp4) · [陨石施放过程](media/meteor-design.mp4)

陨石落点使用火系法阵，选用范围按技能 ID 记录在 [usage.json](usage.json)。施放预览根据 FIR_02 选择法阵，不按职业或圆形范围自动套用。

四系原稿与透明纹样继续保存在本目录。早先的四系同时起阵动画作为设计存档，最新施放使用规则以上方修订版为准。

动画从双圈和刻纹亮起开始，内纹逐渐连通，随后保持轻微呼吸光。释放时线条短暂增亮，余光沿原位淡出。图案本身保持固定，地面从所有留白区域透出。

法阵纹样来自 [本轮附件](reference.png)，对应项目历史文件 [首版风格配色稿](../four-class-vfx-redesign-v1/02-first-style-class-colors-v5.png)。透明层提取、透视复原和排版采用确定性图像处理，参数记录在 [extraction.json](extraction.json)。输出为设计审稿素材。

`extract.py` 使用 Pillow 和 NumPy 提取纹样并还原平视透明层。`animate.py fire` 生成陨石法阵动画，通过 PyAV 输出 30 帧/秒 MP4、20 帧/秒的 GIF 和 WebP。`animate.py design` 保留四系纹样的设计存档输出。

`capture.cjs` 复用当前 Cocos Web 导出的 3D 场景与骨骼动作，记录施放过程和法阵落点的屏幕投影。陨石审稿前摇暂设为 1.45 秒，用于观察起阵。`animate.py native` 只给 FIR_02 合成法阵，其他技能使用场景录制画面。人物与接触阴影的遮挡通过画面亮度近似处理，属于设计合成预览。正式引擎材质与深度遮挡仍待接入时验证。
