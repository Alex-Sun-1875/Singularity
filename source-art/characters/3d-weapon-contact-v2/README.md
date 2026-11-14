# 3D武器握持与动作修复 v2

后续[3D动作节奏优化](../3d-motion-tempo-v1/README.md)适配跑步步幅并加快动作衔接；本页弓箭/手部曲线继续复用，当前生产FBX及正常速度预览以新记录为准。

后续[24件武器重建与对齐](../../weapons/3d-design-v1/README.md)已按2D设计替换全部武器外形；本页修正后的身体FBX、肩肘腕动作与箭轴继续复用。当前逐件弓弦校准、法杖收持和实机动图见新记录。

后续背负位置、剑鞘和脱战收持以[背剑对齐记录](../3d-sword-carry-v1/README.md)及新动图为准；本页动图保留为此前握持动作的历史记录。

2026-11-09。用户要求修复拉弓时手、弓与躯干融合，检查其他武器并提供各件武器动画；追加指出手腕看似断开，以及弓身应与持弓前臂形成夹角。

当前仅更新可选[3D主角入口](http://127.0.0.1:7469/?view=2d&player=3d)，默认2D入口保留。复用原有Quaternius/KayKit CC0模型、骨骼、动作、武器与Cocos 3.8.8蒙皮/Morph能力，没有下载、引入依赖或生成图像。

## 最终实现

- 弓使用既有KayKit Draw帧14—40及Release帧1—9的完整上身动作，保留原生站立下身；肩、肘、腕按原动作整链运动，未单独平移手部，也没有运行时/离线手腕IK。原手指握持沿用。
- 在实际掌心握点校正弓与箭的刚性附件坐标，通过现有Draw形变适配弓弦到拉弦手；弓身长轴与前臂保持明显夹角。三种弓沿用相同接触契约。
- 法杖复用UAL1 `Idle_Torch_Loop`完整左臂的作者持物姿势，用Blender原生镜像粘贴转为右臂，覆盖肩、肘、腕及手指。原施法左手与走跑身体保留；新增`idle_staff/walk_staff/run_staff`三个武器姿势，持杖不再用横放剑的握持方向。
- 三种剑保持原握持和挥击。导出仍使用原网格、UV、权重和骨架；禁用材质未使用的多余顶点颜色通道，避免Cocos只支持COLOR_0的导入错误。道具FBX导入会改场景FPS，最终导出前明确恢复30fps，防止采样与步频偏移。
- 弓的最终朝向以实际Cocos搭箭网格复核，校准记录为`arrow-axis-calibration.json`；玩法时钟、命中、射程、存档和固定相机保持原规则。

生产源为`authored-bow.py`、`authored-bow.blend`与`authored-raphael.fbx`，动作/弓弦参数见`authored-pose-report.json`。源资源许可证见[原生库记录](../../../docs/assets/native-library-runtime.md)。

## 验证与动画

`inspect-contact.py`复用Blender原生BVH，对实际蒙皮后的手/手指三角形与躯干衣物逐源帧检查；结果为`mesh-contact-review.json`。该检查不含肩部衣片连接，不能解释成任意动作、全身、全装备的完美无碰撞证明。

`capture-weapons.cjs`使用现有Playwright从当前真实Cocos构建采集：四个代表方向的握持静帧、两个斜向的完整普通攻击/收招。独立`test=max`浏览器配置补齐展示武器，没有改用户存档。`runtime/after`保留原始图像和逐帧信息；搭箭轴向、实际飞箭与行囊由既有检查方法复核，记录在`runtime/verification`。

`assemble-previews.py`只进行确定性裁切、缩放、字幕和GIF编码。输出为[七件武器对比](runtime/all-weapons.gif)与`runtime/weapon-{ID}.gif`，包含W01、W02、L01三种剑，W07、W08、L02三种弓及W11法杖；均为实际模型和游戏动作，约0.42倍速播放。模型外观仍是既有简化3D资源，不代表原2D脸型与服装精确复刻，也未新增逐技能专属动作。

| 武器 | 单独动图 |
| --- | --- |
| 佣兵长剑 W01 | [近景慢放](runtime/weapon-W01.gif) |
| 未熄之誓 W02 | [近景慢放](runtime/weapon-W02.gif) |
| 风暴王的遗嘱 L01 | [近景慢放](runtime/weapon-L01.gif) |
| 白蜡木短弓 W07 | [近景慢放](runtime/weapon-W07.gif) |
| 银鹿的足迹 W08 | [近景慢放](runtime/weapon-W08.gif) |
| 阿斯特拉的回信 L02 | [近景慢放](runtime/weapon-L02.gif) |
| 灰木短杖 W11 | [近景慢放](runtime/weapon-W11.gif) |

最终类型检查和构建通过。三个攻击类别共95个源帧的双手/衣物三角形检查相交为0；73个实际转向和9个放箭方向检查通过，相机保持稳定，实际行囊仍为13个蒙皮渲染器。1064张动画采样按7件×152帧合成为6.08秒循环动图；重复静帧允许编码合并。详细数值、实际武器Mesh UUID和生产FBX哈希见`runtime/final-verification.json`。代理代表帧审阅与用户美术认可分开记录，没有把数值检查当成用户已认可姿势。

## 未采用的修补

`repair-rig.py`、`raphael-contact-v2.blend`与本目录的`raphael.fbx`是本轮被否决的IK避让尝试。用户指出手的位置和连接不自然后，已撤出生产，不能视为验收通过；`rig-report.json`及`mesh-contact-review-rejected.json`保留过程依据。原生产FBX与manifest保存在`before/`，最终生产不使用该IK姿势或其独立移手做法。
