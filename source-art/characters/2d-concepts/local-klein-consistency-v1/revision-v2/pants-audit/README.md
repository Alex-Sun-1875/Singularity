# 裤子颜色局部审计／适配

仅本地读取已有站姿及 `results/*/constrained-candidate.png`。没有联网、安装、模型调用、图片预览或生产素材写入。本目录输出属于未验收小样；统计不能替代本地美术验收。

| 对应方向 | 当前裤子 RGB 中位数 | 站姿裤子 RGB 中位数 | 当前／站姿／适配后 L8 中位数 |
| --- | --- | --- | --- |
| right 跑 p4 | 121 / 114 / 114 | 96 / 88 / 87 | 124 / 97 / 97 |
| front 跑 p0 | 89 / 81 / 79 | 94 / 85.5 / 85 | 90 / 95 / 95 |
| back 跑 p0 | 104 / 94 / 93 | 103 / 94 / 94 | 104 / 104 / 103 |

站姿裤子是略暖的深灰布料：signed Lab a 中位数为 3，b 为 2。右向当前裤子明显偏亮；正背向裤子的亮暗分布较宽，不能依据全角色或一个全局亮度系数一起压暗。`finalize-candidates.py` 的 `palette_lock()` 只约束酒红衣身与袖区，未约束裤子，是本项修正的直接缺口。

`pants-audit.json` 保存六个 ROI 的 RGB、signed Lab、L* 的 5/10/25/50/75/90/95 分位数、像素数、坐标包络和修正前后数据。图像按 sRGB 假设，由现有 Pillow ImageCms 转换到 ICC Lab D50；NumPy 的 a/b 字节按 `>=128 -> value-256` 解码。L8 为 0..255，L* = L8 / 2.55。没有使用 OpenCV 的偏置 Lab 编码。

## 遮罩与限制

- 六张图均在原 512×768 审阅画布坐标取裤腿包络，不缩放角色、不改变锚点。正背站姿 ROI 从 y407 到 y627；右向站姿从 y439 起，以避开覆盖大腿上部的手。跑姿按弯腿形态分别限制，尤其提前截止抬起的靴子，未使用整幅下半身矩形。
- 灰色背景、透明边缘混色、暖皮肤、酒红衣摆、腰带与暖棕靴子由几何及 signed a/b 门限共同排除。只向遮罩内部羽化 1.5px，遮罩外保持原 RGB 完全相同。靴子暗部可能接近灰布，因此优先用局部包络挡住，不能只靠低饱和度选区。
- 这仍是数值代理遮罩，不是人工描线的语义遮罩。边缘、极暗缝、材料混合像素和被排除的窄缝会保留原像素。ROI 无法独立辨认固有色、光照与材质，不能保证裤子语义覆盖完整。站姿侧面上大腿没被用来拟合。

## 主流程调用

```python
import importlib.util
from pathlib import Path

module_path = Path('source-art/characters/2d-concepts/local-klein-consistency-v1/revision-v2/pants-audit/pants_palette.py')
spec = importlib.util.spec_from_file_location('pants_palette', module_path)
pants_palette = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pants_palette)
result, report = pants_palette.match_pants(
    image, standing_reference, direction, mask_output=output_folder / 'pants-mask.png')
```

`direction` 为 `right`、`front` 或 `back`；输入均为当前 512×768 RGB 画布。函数返回 `(PIL.Image.Image, JSON-ready dict)`；也公开 `build_pants_mask(image, direction, reference=False)` 和 `stats(image, mask)`。

适配仅拟合裤子内部：低频 L 用参考中位数与四分位距拟合，斜率限制在 0.8–1.1，保留至少 80% 宽尺度褶皱对比；原 L 的高频残差不参与压缩，a/b 只平移到参考中位数。L8<46 的极暗缝逐步减少修正，避免把遮挡深缝抬成灰片。ICC 量化、RGB 色域裁剪与遮罩混合后不保证逐像素纹理数值恒等。相比硬直方图匹配，亮暗尾部分布会有剩余差异，详见报告，不宣称已与站姿逐分位完全一致。

运行 `python .../pants-audit/pants_palette.py` 会在本目录重建报告、参数、遮罩与独立 `*-pants-candidate.png`；不会写回既有候选或生产图。复用本机已装 Pillow 12.2.0、NumPy 2.4.4、SciPy 1.17.1，不新增依赖。
