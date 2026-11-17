# 选中态修订候选

2026-11-17，用户否定上一版选中态审美。`equipment-selection-v1` 的象牙白四角方向作废；`skill-selection-v1` 是同方向派生稿，不再作为后续设计基线。历史稿保留，确认状态见各自 `design-spec.json`。

本轮回到当前游戏的原材质、字库、细铜边和紧凑比例。候选选中态采用低饱和青灰内衬与压低亮度的细内边，取消上一稿的白色角标。普通长剑的紫色背景中性化，已穿戴标记独立，主手槽不重复高亮。技能列表保留原五行可见密度和行中心距，将图标与两行文字收进行框，等级固定右对齐；防御技能的金盾原样保留。

- `selection-before-after.png`：真实用户截图局部的前后对照，推荐先查看。
- `equipment-context-revised.png`、`skills-context-revised.png`：分别合成回原界面的修订候选。
- `revised-context-panels.png`：两个完整界面合并预览。
- `material-study-generated.png`：云端 OpenAI image_gen 生成的材质小样。调用成功；整张人物和文字不作为替换资产。其过亮选中边已在合成阶段压低。
- `prompt.txt`：该次实际提示词。`equipment-current-context.jpg`、`skills-current-context.jpg` 是必要界面参考裁片。
- `compose-review.py`：Pillow/NumPy 确定性处理与局部合成；只改状态部位与红色批注清理，保留原截图中其他人物、文字、布局。
- `review.json`：生成结果、视觉检查、用户确认及接入状态分别记录。

生成只用于代表性材质试样，没有批量生成运行组件。最终静态稿已经查看，仍待用户审阅，未修改 Cocos 运行代码、运行资源、公共语义 token 或发布条目，也没有进行游戏触控／TapTap 真机验收。脚本内坐标均为截图物理像素，不能直接当作逻辑触控尺寸。
