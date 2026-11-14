# 背面跑步：原帽保留的整剑延长

本目录为512×768单帧本地适配，不改正式素材或body产物。`prepare_back_run.py`复用既有纯像素`preserve_tip.py`的坐标、覆盖度、整数平移和中段轴向适配；另为背跑建立独立帽轮廓，未套站姿帽polygon。

只对原图x125..264、y300..439局部做了一次必要云端视觉检查，展示缩略图420×440；图片处理与模型推理仍在本地完成。这次检查确认实际金属帽止于约(205,398)，约(206,413)处的斜金色线是衣摆。`source-cap-hand-local-xy.png`留存这张带原坐标局部；没有上传整帧。

原帽完整整数平移(-28,+68)，终点约(176.7,466.4)，无缩放、旋转或重画。含柄完整剑长约+26.4%，只有中段轴向长度增加，宽度维持1。手与新剑无交叉；原手和指缝不变。独立原/平移帽RGBA字节相等，帽核心在成图中与原图移位RGBA字节相同。

`merged-guide-rgba.png`将body/back的身材guide和这把延长剑合并；`merged-edit-mask.png`为身体连接与剑鞘接缝的联合可编辑区域。`merged-immutable-mask.png`保护原头、双臂/手、靴子及完整帽。`palette-protection-mask.png`进一步保护整把原/新剑及其边缘，供后续服装校色使用；palette的geometry_image必须用merged-guide。`prompt.txt`用于一次本地Qwen合并补绘。

```python
guide, seam_mask, report = extend_sword_rgba(image, source_pose='back-run')
guide, merged_mask, report = merge_back_run(body_guide_path, body_edit_mask_path)
candidate, report = finalize_back_run(raw_path)
```

最后一个函数直接以本目录merged guide为底，只通过merged edit mask采模型RGB，并丢弃模型alpha。最终锁回guide的头、手、靴子和原帽；不调用body旧剑锁定后处理。命令行最终合成用：`prepare_back_run.py finalize <raw绝对路径>`，输出`candidate-rgba.png`、`final-report.json`。

原剑和衣服在来源中已拍平，轮廓仍是局部视觉与色度剖面约束的估计item matte，不能代表恢复了独立原剑图层。旧剑露出碎片的隐藏衣料不可知，单独`exposed-cloth-cleanup-mask.png`标识360个估计清理像素。帽边缘可能含少量旧衣色，运行和数值验证通过不代表美术验收通过。
