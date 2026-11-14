# 可选发型游戏级减面

2026-11-14，按用户“头发能不能搞简单一点”及“其他的也一样”的要求，在原设计上简化四款可选发型。

- `hair-*-high.glb`：完整原模型，SHA-256 见各几何报告，不进入 Cocos 资源包。
- 运行资源：`src/cocos/assets/resources/actors/raphael/hair-*.glb`。
- 保留原节点、骨骼顺序、逆绑定矩阵、网格名、材质与 Head 权重；Creator 资源 UUID 不变。
- 复用原生蒙皮、动画和阴影。没有增加运行时 LoD 切换、挂点适配或帧率限制。

| 发型 | 三角形原版 → 简化版 | 顶点原版 → 简化版 | GLB 字节原版 → 简化版 |
| --- | ---: | ---: | ---: |
| Curly 卷发 | 18,366 → 4,500 | 14,193 → 4,300 | 982,620 → 274,880 |
| Dante | 10,796 → 2,700 | 9,159 → 2,901 | 630,012 → 191,336 |
| Nero | 6,452 → 1,600 | 4,814 → 1,509 | 351,936 → 112,344 |
| Vergil | 8,434 → 2,100 | 6,303 → 1,930 | 453,152 → 137,244 |

四款源文件合计 44,048 → 10,900 三角形、2,417,720 → 715,804 字节。这是资源合计量，角色运行时只选一款，不能当作每帧同时减少的绘制量。

从仓库根运行：

```powershell
& 'src/.tools/blender-4.5.15-windows-x64/blender.exe' --background --factory-startup --python tools/model-pipeline/simplify_rigid_hair.py -- --source source-art/characters/3d-hair-lod-v1/hair-curly-high.glb --output src/cocos/assets/resources/actors/raphael/hair-curly.glb --triangles 4500 --report source-art/characters/3d-hair-lod-v1/geometry-report.json

$hairTargets = @{ dante=2700; nero=1600; vergil=2100 }
foreach ($styleId in @('dante','nero','vergil')) {
  & 'src/.tools/blender-4.5.15-windows-x64/blender.exe' --background --factory-startup --python tools/model-pipeline/simplify_rigid_hair.py -- --source "source-art/characters/3d-hair-lod-v1/hair-$styleId-high.glb" --output "src/cocos/assets/resources/actors/raphael/hair-$styleId.glb" --triangles $hairTargets[$styleId] --report "source-art/characters/3d-hair-lod-v1/geometry-$styleId-report.json"
}
```

几何处理使用 [Blender Decimate Collapse](https://docs.blender.org/manual/en/5.0/modeling/modifiers/generate/decimate.html)，沿用项目 `cocos_optimize_exports.py` 的 Collapse/Triangulate 方案。适配脚本仅重打包减面几何，避免 Blender 重导出改变共享骨骼的关节编号。

Creator 3.8.8 新 Web 构建已完成。Android 模拟器 3 个游戏姿势、4 个头像方向检查通过，见 [视觉检查](art-review.json)、[近景对比](head-comparison.jpg) 与 [游戏对比](game-comparison.jpg)。近景诊断将两版头像点光源光通量同时降为 2%，用来避免原预览过曝遮住细节；游戏灯光配置未改。

其余三款在新构建 `perf-render-all-hair-lod-v2-20261114` 同样通过各 3 个游戏姿势、4 个头像方向与切换检查，见 [其他发型检查](other-art-review.json)、[Dante](head-dante-comparison.jpg)、[Nero](head-nero-comparison.jpg)、[Vergil](head-vergil-comparison.jpg) 和 [游戏对比](other-game-comparison.jpg)。同时修复原有的发型销毁顺序：禁用后交给 Cocos 原生 renderer.destroy() 清理，避免先清空骨骼再重建材质引发空引用。首轮失败及修复后的 27 张游戏截图／24 张头像截图保留在 `test-results/performance/all-hair-lod-neutral-qa-v{1,2}/`。

原版／简化版同进程性能对照记录于 `test-results/performance/hair-lod-moving-abba-v{1,2}/`：V1 两版均低帧率、V2 与其他 Creator 构建重叠，均不批准整体 CPU/GPU 收益。最终结果见 `docs/performance/continuous-spawn-cpu-20261114.md`。Web 模拟器结果不代表 TapTap 真机验收，未制作或上传新 TapTap 包。
