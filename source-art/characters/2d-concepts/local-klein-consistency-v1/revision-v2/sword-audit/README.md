# 原剑鞘末端保留小样

这是本地几何适配，不是模型生成结果。脚本只读原图、旧 guide 和旧 candidate；不联网、不安装依赖、不调用 ComfyUI，也不写正式素材或共享脚本。复用本机已有 Pillow、NumPy、SciPy。

## 交付与调用

- `tip-preserved-candidate.png`：完整 RGB 候选，512×768；尚未通过美术验收。
- `preserve_tip.py`：`build_candidate(before: PIL.Image.Image) -> (PIL.Image.Image, dict)`；`make_layers(before)` 另外返回所有局部图层与遮罩。
- `source-tip-rgba.png` / `translated-tip-rgba.png`：原帽提取和整数平移后的独立 RGBA；画布都是原图尺寸。
- `source-sword-alpha.png` / `target-sword-alpha.png` / `translated-tip-alpha.png`：局部 item 的覆盖度；不是整个人物 alpha。
- `middle-alpha.png` / `old-tip-cleanup-alpha.png` / `change-mask.png`：中段适配、旧帽露出残片清理与实际修改范围。
- `tip-preservation-config.json`：坐标、手工约束的轮廓、多边形来源和质量边界。
- `source-tip-line-profiles.csv` / `metrics.json`：原图沿轴与法向采样、变换量、像素不变量和 SHA256。

重建命令（在项目根目录）:

```powershell
& 'F:\Models\ComfyUI_windows_portable\python_embeded\python.exe' 'source-art\characters\2d-concepts\local-klein-consistency-v1\revision-v2\sword-audit\preserve_tip.py'
```

## 坐标与旧方案问题

旧 `prepare-cases.py` 沿 `(283,192) -> (200,373)` 轴向拉伸整条 RGB，并用宽 17px 直线取样。该直线既包进左侧衣料，也漏掉右侧实际剑鞘；它的终点位于原金属帽结束之前。`finalize-candidates.py` 再用宽 13px 直线接入重画后的 model 输出，没有锁定原帽。

这里先对原图做色度与法向剖面检查：原帽 `(199,380)` 的 RGB 为 `(122,84,64)`，G−B=20；下一行同列 G−B=11，随后裤/衣料的色差会干扰端点识别。因此完整抗锯齿轮廓末端估计为 `(198.016,380.206)`，定位误差约 1px。旧 `(200,373)` 不能作为完整原帽末端。

使用原轴的正交坐标 s（沿剑鞘）、n（法向）。末端所在原 s≈206.5；完整保留 s≥168 的原帽和相邻短段。平移 `(-31,+65)` 像素后，估计末端为 `(167.016,445.206)`，距目标 `(166.8,445.4)` 约 0.29px。选整数平移是为了原帽 RGB 和覆盖度字节保持一致；精确分数坐标需重采样，反而无法保留原字节。

只有 s=75..168 的中段轴向重采样到新长度（约 1.774 倍），法向宽度保持单位比例，握柄和挂点位置不动。真实可见末端计算的总长度约为原来的 1.349 倍。原帽的几何奇异值恒为 `(1,1)`，无旋转、拉长或重新生成。

## 已验证的范围和质量边界

脚本实测：原帽与平移帽均 484 个非零覆盖像素，alpha 字节和均为 110975；候选中原帽不透明像素 RGB 与原图完全相同。y<250 原像素不变，item 原/新区域并集之外修改为 0。提取帽没有 y≥382 的裤子像素，也没有平灰背景像素。

原图已经把剑鞘和衣服拍平，缺少独立 item alpha。这里的 8 倍采样轮廓由本地像素剖面约束，仍是估计 matte；不能把“字节保持”当作轮廓和美术已经验收的证明。边缘可能含原衣料的亚像素混色。旧帽被新中段遮盖后仍露出的 625 个覆盖像素，使用相邻原衣料插值清理；遮挡下的真实衣料无法从原图恢复，清理遮罩单独保留。

集成时由调用者复原原手部等遮挡。需在本地检查原帽/新帽并排、完整圆尖、宽度、中段接缝、手部层级和旧帽残影后才决定是否接入；本子目录没有改正式素材。
