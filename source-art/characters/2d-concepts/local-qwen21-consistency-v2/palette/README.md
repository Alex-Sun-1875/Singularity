# 局部衣料颜色约束（本地）

`apply_palette.py` 复用此前 `pants_palette.py` 的 Pillow ImageCms signed-Lab D50 转换和 SciPy 低频亮度适配；没有调用模型、服务器、网络或新增依赖。所有本目录产物都是源素材实验，不是正式资源替换或美术验收通过的结果。

```python
from apply_palette import apply_palette

result, report = apply_palette(
    candidate_rgba, standing_rgba, "front",  # front / back / right / side
    geometry_image=body_guide_rgba,
    protect_mask=body_protect_mask,          # 白/任意非零=必须保留
    mask_output_dir=output_directory,
)
result.save(output_path)
```

也可使用命令行：`python -B apply_palette.py --candidate CANDIDATE --reference STANDING --direction front --geometry GUIDE --protect-mask PROTECT --out OUTPUT_DIRECTORY`。

模型结果应先与原始/比例引导像素做局部受限合成，恢复头、手、装备与 alpha，再调色。`geometry_image` 必须是最终实际姿势的原始图或比例引导图；比例改变后不能仍拿未变形原跑作为位置权威。接口在候选和引导图上分别判断衣料后取交集，并将原始和新增金绣/暖装备共同排除；它不负责修复模型已经改坏的身份、手或武器。

- 酒红背心、炭灰衣袖、深灰长裤独立取样与校准。各自以同方向站姿为颜色基准，修正不受上一轮 Qwen 过暗的酒红颜色牵引。
- 只修改颜色与几何门限共同认可的内侧衣料；细金绣、暖皮革、明确手部包络、头部、武器走廊、透明边缘及调用方保护遮罩全部排除。遮罩只向内羽化，绝不向皮肤/装备/背景扩散。
- 原素材大部分不透明布料 alpha 为 250–253，因此内部判定使用 alpha≥250 后向内腐蚀 2px，不能把 alpha=255 作为唯一不透明标准。输出仍逐字节锁定输入候选 alpha，所有遮罩外 RGBA 逐字节相同。
- 亮度只适配 sigma=1.2 的低频项，比例限于 0.90–1.08，单次 L8 偏移限于 ±36；保留原高频褶皱残差与局部色彩变化，不把衣料涂为单色。深黑褶皱有渐弱保护。
- 遮罩是保守的颜色/几何代理，并非已逐像素美术验收的语义分割。细缝、边缘和排除区有意保留原颜色；衣带与装备的灰暗交界、未覆盖的剑轮廓仍依赖调用方准确保护遮罩及局部目视检查。

`side-inputs/` 提供侧跑第4相位与同方向站姿第0相位的原始 RGBA、中文提示词和布料/保护遮罩。原始 native 图按旧的统一动作仿射重建到 512×768，保持脚锚 (256,712)，已核实 alpha 与历史 canvas alpha 完全相等，复合旧灰底后的 RGB 与历史输入完全相等。没有引入旧模型候选、比例引导或生图像素。

`original-reference-audit.json` 与 `original-only-calibration/` 是三向原跑→站姿的纯确定性校色小样，没有 Qwen 新生成像素。`palette-report.json` 分别记录原跑/引导、候选前、站姿、候选后采样分位数与 ΔL*/Δa*/Δb*、ROI 中位数 ΔE76。不同姿态的烘焙光照、衣料遮挡和褶皱分布不同；这些数值只能说明取样区域的颜色偏差，不能作为美术合格、固有材质完全相等或全帧颜色连续性的证明。

已完成的本地数值核验：三向全部三种材质均有60个以上内侧采样；一次校准后对应站姿的 ROI 中位数 ΔE76 为 0–0.393，输出 alpha、遮罩外像素及硬保护像素全部逐字节不变。此为数值与运行核验，未进行云端视觉检查或完整美术验收。

`final-feature-protection/` 供最终正背跑调色使用：`front-feature-protect-mask.png` 绑定 `body/front/guide-rgba.png`，`back-feature-protect-mask.png` 绑定 `sword/back-run/merged-guide-rgba.png`。旧的 `all-protection-mask`/背剑 `palette-protection-mask` 连同整只手臂布料一起锁定，因此这里只解除整臂颜色锁，并重新独立保护完整头、手和腕部包络、靴、原剑与新剑所有覆盖以及金绣等细节。外形和 alpha 始终锁定，不因开放袖布 RGB 校准而改变。前/背袖布有效选区分别3988/3949像素；原手纯亮肤证据分别2590/797像素与原跑完全相等，局部校色核验后仍完全相等。全部特征与布料选区交集为0，见 `feature-protection-report.json`。这些数值验证未调用模型、看图或上传素材；完整手部阴影采用大包络保护，亮肤证据不代表自动分割了所有肤色。
