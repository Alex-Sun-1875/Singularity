# 当前人物与武器按v5重设计

**Goal:** 在当前可玩Cocos3.8.8人物上重做外貌、服装与武器，直接使用/整理UV和PBR贴图，并落实此前v5概念设计的脸、发型、衣装剪影与随身物件。

**Reference:** `docs/story/revision-v5/art-direction.md`与hero-v5-balanced、explorers-v5-recast、rivals-v5-balanced；Lorn面部按explorers-v5-elegant第二人。当前10名actor为raphael/mira/lorn/nightqi/kael/evelyn/captain/raider/raider-shield/raider-archer。captain是灰披队长，不能套未来Adrian；Severin/Elys/Adrian当前未进入本章运行范围，不虚报已建模。

**Approach:** 保留当前65蒙皮骨+2动态弓附件骨、11动作、原rest/bind与动作曲线。现成人体/服装/发型/武器优先适配；精确v5剪影没有可用成品时，用Blender原生编辑/Curve/Solidify/Data Transfer完成必要衣装与道具，绝不重造骨骼、UV或动作求解器。现有材质原图、社区低模发型和PBR扫描图继续复用；新源/UV烘焙与运行资产均保留可复现入口。

## Shared pipeline contract

- 从`src/.tmp/native-production/source/{id}.blend`读取，绝不再次调用prepare重建覆盖设计。
- 新可编辑源：`source-art/characters/redesign-v6/{id}.blend`；候选FBX/manifest先放`src/.tmp/character-redesign-v6/actors/`。运行安装前备份当前10角色与原武器。
- 两个适配模块提供`apply(identity, rig, manifest) -> dict`，处理当前已加载场景，返回JSON可序列化的来源/修改记录。新增mesh必须设置`nativePart`和`defaultVisible`；名字保留`{id}_native_hair_`等运行选择语义。不要写入正式assets或重建rig/actions。
- Root调用face/hair→garments→原生UV/PBR导出；导出只选择nativePart及明确新增网格，排除3个QA Icosphere。新UV需绑定原UV作为源采样，烘焙目标独占，运行只输出最终UV0；alpha发片单独处理。
- 材质按当前native-kit-v1契约，保留/正确更新sourcePBR有效因子，ORM为R遮蔽/G粗糙/B金属；武器附着后也应用真实PBR。图名唯一，路径兼容native-shared；清理无引用旧候选，避免盲目叠加手机纹理预算。

## Tasks

- [ ] Face/hair：10角色个性化脸部体积；六名具名人物按v5，浅肤自然面颊。原低模系统/社区发型适配卷发/bob/马尾/半束，保留UV与来源，避免旧10万三角发片。
- [ ] Garments：主角青绿短披布/棕皮甲/米色卷袖/单肩钢甲；Mira酒红长马甲；Lorn靛灰厚甲/健壮轮廓；Nightqi灰绿长披风/箭袋；Kael赭黄短外套/地图筒测距物；Evelyn沉蓝卫甲/白补布。敌型按已有职责区分，Captain灰披盾锤，不用Adrian概念板冒名。
- [ ] Weapons：重UV/细化当前剑、大剑、双短刃、长弓、箭、杖、盾；落实Captain战锤/盾、Lorn拼修大盾、Evelyn炉灯与Kael地图物；保留弓Draw形变与原动态握点。装备ID外观映射如增加应真实展示而不是仅改名称。
- [ ] Root：浅肤手臂与头部一致，UV/PBR实际烘焙和接缝检查；统一导出/安装，手机纹理/几何预算报告；更新真实模型头像和物品缩略图。
- [ ] 验证：原骨架/11动作曲线完整，现有FBX回读、角色检查及Web构建；真实引擎十人/装备/慢走跑步/剑弓杖/握持/预览/存档及首章合法指令流程。截图同时给正常手机镜头与人物预览，不用源渲染代替运行。

## Completion requirements

当前10人和在用武器全部有实质更新；概念规定的脸/发型/衣装/随身物件逐项对照，不把纯染色当成几何完成。贴图需实际对应UV且有albedo/normal/ORM语义证据；所有新角色与武器必须在正式游戏中可见、可操作，骨架/握持/动作/存档无回退。既有暖金界面与首章玩法保留。对未能达到的细节如实记录并继续工作，不能自行缩成只做主角或只出配色稿。
