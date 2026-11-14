# R2-3 独立矿机2D小样

云端原始生成见上级`r2-3-generation.json`、`r2-3-sheet-v1.png`、提示词与最小参考；本目录是独立的确定性切帧、脚锚与输出审阅，不改写生成证据。

- `processing.json`：1254²原图中16个独立主体的实裁矩形、方向、原点和逐像素校验。原图实际方向为down/left/up/right，不翻图。
- `review.json`：静态小样审阅，以及根据反馈修正down walking投影原点的记录。运行步态、转向、碰撞仍等实际sample。
- `anchor-contact.jpg`、`front-anchor-review.jpg`：共同投影原点的16帧及前向对照；`walk-loop.gif`是两张真实接触帧的循环。
- `runtime-install.json`：仅R2-3→mine-crawler独立2D资源；真实3D模式不包含新矿机模型。

`prepare-mine-crawler-pilot.py`只清除alpha<=3，保留所有更高alpha原始RGBA像素各一次。16主体存在少量跨名义格线，因此按归属扩出实际裁切，不硬切钳尖/腿。重排384格不拉伸，不重绘，全部frameScaleFactors=1，统一初始尺度0.0065m/像素。

原点不是逐帧最低脚尖：down走路以矿斗/主机核心基准保持idle高度连续，保留腿部接触动作；attack继续保持原来的压低姿势。其余三个方向和14个其他原点未随该次修正改变，图集字节不变。

小样只有四个真实方向、每方向idle/两个walk接触/一个attack画面。attack用已有idle→钳击→idle相位，没有虚构中间动画；没有独立受击/死亡图，缺口如实记录。静态通过不代表已经通过所有步态/遮挡/手机实机验收，也不支持立刻把其余31种扩成同一张模板。


生产运行副本现为`runtime-1024/atlas.png`和manifest：整张1536→1024统一LANCZOS重采样，格宽384→256、原点/矩形×2/3、UPP0.0065→0.00975，世界尺度不变，原1536及像素断言保留。详见`runtime-resample.json`与`runtime-production-review.json`；RGBA level0预算9→4MiB/身份（不含driver/image/mesh）。敌纹理scene引用释放策略及待实测转场项见上级`enemy-texture-lifecycle.json`。
