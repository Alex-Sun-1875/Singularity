# 箭矢冷银灰材质

2026-11-10。用户指出搭在弓上的箭矢近乎黑色。本轮将现有箭杆纹理从深褐调整为带细纵向纹理的冷银灰，箭头为较亮的缎面钢色，原象牙色箭羽保留；飞行中的简化箭体使用对应银灰与箭羽色。

复用 Pillow、现有 UV 与 Cocos builtin-standard 材质，没有调用图像生成、下载资源或增加依赖。当前场景未启用 IBL，因此采用适度的金属与漫反射混合维持正常镜头下的可读性，没有添加自发光或额外灯光。材质通道依据 [Cocos 3.8 PBR 文档](https://docs.cocos.com/creator/3.8/manual/en/shader/effect-builtin-pbr.html)。

[生产记录](production.json)与[美术观察](art-review.json)分别保存。确定性脚本为 [prepare.py](prepare.py)，默认读取归档的原图，重复运行得到相同结果。未来重新烘焙箭矢图集后，可用 `--input` 指向新烘焙目录、`--output` 指向待接入目录重新应用；当前源 Blender 仍保留历史深褐材质。原图与原 CC0 模型来源沿用 props manifest 的记录。

[实际引擎前后对比](runtime/arrow-comparison.png)为相同镜头和蓄弓时点的裁切放大，没有重绘箭或人物。人物模型、动作、网格、UV、法线图、搭箭绑定及弹道参数未修改。本轮未改变重箭、分裂箭或连穿箭的运行规则，技能提案见 [弓箭手设计](../../../docs/design/archer-skills-v3.md)。

类型检查、web-mobile 构建、搭箭与基础放箭检查通过；弓术和法杖现有验证结果见 [技能运行记录](runtime/final/skills-report.json)，所用源码指纹见 [构建来源](build-source.json)。构建过程中出现的其他装备成长代码在工作区原样保留，专项快照不包含那些进行中的更新。这些受控浏览器检查不等同于用户美术验收或真实手机性能验收。

交付为[独立预览](http://127.0.0.1:7478/?view=2d&player=3d&hair=dante&revision=arrow-steel-v1)，副本在 `src/cocos/build/concept-2d-arrow-steel-v1`。常用入口同期由其他工作重建，本轮未覆盖；其旧检查脚本未取得预期箭矢附件，故不宣称该入口验收通过，见[接入记录](install-record.json)。
