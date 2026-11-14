# 原稿控件与颜色校正

本轮按用户圈出的控件校正，保留已确认的当前技能方案。运行截图不作额外曝光或颜色处理。

- [原稿与最新运行逐页对照](F:/workspace/Singularity/source-art/ui/rpg-alignment-v5/design-runtime-comparison.jpg)
- [圈出区域：原稿、上一版、本次](F:/workspace/Singularity/source-art/ui/rpg-alignment-v5/marked-regions-comparison.jpg)
- [颜色调整前后](F:/workspace/Singularity/source-art/ui/rpg-alignment-v5/tone-before-after.jpg)
- [同一区域取色结果](F:/workspace/Singularity/source-art/ui/rpg-alignment-v5/color-review.json)
- [实现与运行记录](F:/workspace/Singularity/source-art/ui/rpg-alignment-v5/implementation-result.json)

姓名牌、侧栏页签、装备暗金框及选中边框从原稿提取；属性条、技能条、卡片、点数盒和费用牌的动态文字区使用原稿空白材质，修正纯黑补底。金线去底色后还原，暖白与强调文字由公共反馈色配置管理。

装备按实际数量排4列：8件排2行、12件排3行。主副手两个底部槽位下方保留名称，两个戒指槽通过同一个戒指入口选择。不同剑、弓与法杖使用原稿对应图像，当前装备名称、品质与规则数值仍由实际数据提供。

技能列表与详情保持当前配置。成长预览显示实际变化的伤害倍率；陷阱和撤射的简短说明后仍可滚动查看完整规则，没有修改技能效果或成长数据。

## 新绘制图标

两枚线框占位图使用 **OpenAI 内置 image_gen** 补为同一绘制风格。每次仅提供现有256像素箭矢图标作为风格参考；不声称接口缓存了重复上传。

- [陷阱图标，已接入](F:/workspace/Singularity/src/cocos/assets/resources/ui/combat-relief/rpg-bow-06-painted-v5.png)
- [撤射图标，已接入](F:/workspace/Singularity/src/cocos/assets/resources/ui/combat-relief/rpg-bow-07-painted-v5.png)
- [完整提示词与输入说明](F:/workspace/Singularity/source-art/ui/rpg-alignment-v5/painted-icon-prompts.json)
- [生成来源、后处理与美术检查状态](F:/workspace/Singularity/source-art/ui/rpg-alignment-v5/painted-icons.json)
- [原稿组件与取样记录](F:/workspace/Singularity/source-art/ui/rpg-alignment-v5/reference-parts.json)

生成状态：完成。美术状态：已检查原始图与256像素导出，形象含义和材质风格符合当前技能；最终用户验收待确认。原始生成结果保存在本目录，接入文件保存在项目资源目录；旧图保留。

默认预览为 [7469](http://127.0.0.1:7469/?preview=rpg-alignment-v5)。浏览器验证使用独立存档上下文，没有清除或替换用户存档；TapTap平台和真机仍需另行验收。
