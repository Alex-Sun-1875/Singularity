# 可编辑美术源文件

`blockout/` 保存6角色、9道具的共享 Blender 场景；`player-refined/` 保存主角结构研究场景。均为静态内部研究，非最终美术。没有骨架或动画。

需要 Blender 4.3；从仓库根目录运行：

```sh
blender -b -t 4 --python source-art/blockout/build_assets.py
blender -b -t 4 --python source-art/blockout/validate_exports.py
blender -b -t 4 --python source-art/player-refined/build_refined.py
blender -b -t 4 --python source-art/player-refined/validate_refined.py
```

生成脚本会覆盖对应 assets 目录导出物及本目录的 .blend。概念图不是脚本生成物。现有 validation.json 为原始导出检查快照；更改后应重新验证。场景渲染输出使用相对路径。未指定公开许可。
