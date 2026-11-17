# 草地自然绿微调

2026-11-17。用户反馈上版草地过艳，希望略微收敛、保持明亮，并接近启动山谷图的自然绿。

仅调整现有 `meadow-v2.png` 的色彩强度：`RGB' = Y + 0.80 × (RGB − Y)`，其中 `Y = 0.2126R + 0.7152G + 0.0722B`。这是 Pillow/numpy 的确定性本地调色，没有再次生图、改变草叶细节或加灰色覆盖层。平均亮度从129.476变为129.4749，8位取整引起的平均逐像素亮度绝对误差约0.233。

- [上一版草地](previous-meadow.png)、[当前草地](meadow-candidate.png)、[贴图对照](texture-comparison.jpg)、[游戏前后对照](before-after.jpg)
- [处理、原始数值、哈希和保护范围](processing.json)
- [当前实景检查](runtime-review.json)及[新版截图](after/)

原始云端生成图和提示词沿用[原记录](../generation.json)，制作脚本为[refine_map_materials.py](../../../../tools/model-pipeline/refine_map_materials.py)。本次不改其他八类地表、树冠、导入采样设置、米制平铺、地形、碰撞、导航、角色、HUD或玩法。Web预览为正常test；浏览器检查不代替TapTap真机验收。

正常test Web构建及6张同机位实景复核通过，错误和失败请求为0，绘制次数不变。S01固定草地局部的屏幕HSV饱和度下降约19.42%，加权字节亮度变化约+0.69%；这些只是同机位像素对照，不是物理显示亮度测量。
