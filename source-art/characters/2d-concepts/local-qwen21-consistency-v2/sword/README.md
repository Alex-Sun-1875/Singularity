# 背面站姿：整剑长度局部小样

本目录只包含512×768单帧试验，不替换正式素材，不调用模型、联网或上传图片。生图由主任务使用已部署本地Qwen完成；本目录脚本只做本地Pillow/NumPy/SciPy适配。

- `original-rgba.png`：已保留原始RGBA画布的PNG字节副本。
- `guide-rgba.png`：中段加长、原帽整数平移、手指前景复原后的真实RGBA引导图。
- `edit-mask.png`：白色为Qwen可用于补接缝/少量露出衣料的区域，共1870个非零像素；完整原帽和手前景受到保护。
- `prompt.txt`：中文局部修复提示词。
- `geometry-report.json`：来源SHA256、实际复用的旧模块、几何量、逐像素不变量和局限。
- `source-cap-rgba.png`、`translated-cap-rgba.png`：用于核验完整原帽只做整数平移的独立图层。
- 其余`*-mask.png`与`hand-protection-alpha.png`：局部覆盖度/手前景原alpha诊断；不是整个角色的alpha。

## 几何与透明边缘

实际调用旧`revision-v2/sword-audit/preserve_tip.py::make_layers`生成经过原数值剖面约束的剑鞘覆盖度，并复用其轴向坐标和整数平移工具。旧模块为纯像素处理，文件夹历史命名不代表使用旧FLUX模型。

完整原帽从原位置约(198.016,380.206)整数平移(-31,+65)至(167.016,445.206)，帽不缩放、不转动、不重画，只有中段轴向拉长、法向宽度维持1。肩挂点到鞘尖长度+34.9%；包含上方剑柄/柄头的整把剑，以约(313,125)为上端参考时约+25.7%。后者是本小样目标口径，具体视觉长度仍需美术验收。

旧灰底before在alpha<255处带有(228,228,228)混色，旧模块直接转RGB会丢alpha；本适配器只从原RGBA取色，中段与露出衣料使用预乘alpha插值。手部直接用原RGBA作为剑前方的前景；alpha≥230的内部手指逐字节保留，细边执行source-over，alpha=0的指缝保留后方剑鞘可见，不粘贴灰底矩形。独立帽图层的原/平移RGBA字节相等；成图只在未被手遮挡的帽内部检查原RGBA字节相等。

原图中衣料与剑已经拍平，独立剑帽覆盖度仍是手工受像素剖面约束的估计，边缘可能含少量原衣色。旧帽移走后的衣料没有真实隐藏图层，只能从相邻原衣料估算；这部分遮罩独立保留并允许Qwen小范围修补。运行成功与数值不变量不构成美术验收。

## 准备与最终合成

```powershell
& 'F:\Models\ComfyUI_windows_portable\python_embeded\python.exe' 'F:\workspace\Singularity\source-art\characters\2d-concepts\local-qwen21-consistency-v2\sword\prepare_sword.py'
```

主任务用`guide-rgba.png`和`prompt.txt`调用本地Qwen后，将512×768原始结果交给：

```python
image, report = finalize(raw_path, output_path=None)
```

函数位于`prepare_sword.py`；也可以将raw的绝对路径作为该脚本第一个参数运行。默认输出本目录`candidate-rgba.png`和`final-report.json`。只接入`edit-mask.png`中的模型RGB，alpha保持guide原alpha，最后锁回完整帽、原手内部、头/柄/肩挂点与脚。不同尺寸raw会明确报错，不自动缩放。函数禁止将输出写到本目录外。

本小样的帽轮廓与轴仅适用于背面站姿。背面跑步剑帽有不同扩张形状，不能盲套站姿坐标；跑姿已在`back-run/`单独检查完整帽与衣摆边界，并使用独立几何和同样的“中段变长、完整原帽整数平移”方法适配，详见该子目录README。
