# 右侧重复衣领修正

2026-11-09，已接入默认7469试玩。用户截图中的“双层脖子”来自原右侧待机图里上下叠着的两圈衣领及凸出的旧领尖；不属于镜头重影。

复用现有走路图的单层衣领作为构造参考，云端OpenAI image_gen仅生成一次右侧局部修图。输入为`collar-edit-target.png`和`single-collar-reference.png`，完整提示词见[collar.prompt.txt](collar.prompt.txt)。输出`collar-cloud.png`为1082×1454 RGBA，原始生成路径为Codex generated_images下的`exec-ad02c2ba-a2b0-4e46-92a8-9520347ada3a.png`。只取衣领衣料作局部候选，生成头脸未使用。没有运行本地模型或下载依赖。

[repair.py](repair.py)复用既有帧清单、头部配准、Pillow与SciPy处理，按头部位置挂接衣领遮罩，保护拉弓手指，并清除裁断后残留的小领尖。原面孔、银发、动作、身体根锚点、UV、UUID及下半身保留。修正44个右侧待机/攻击/施法/交互帧，分布在22张既有PNG中；同图集其余152个帧逐像素核对未变，走跑图集没有修改。

右侧无武器制作母版`attack-identity-v5/masters/neutral-right.png`同步衣领区域，保留其他区域原像素，避免后续附件制作继续引用重复衣领。制作、生成、美术与实机验收分开记录，见[prepare.json](prepare.json)、[review.json](review.json)、[preservation.json](preservation.json)及[install.json](install.json)。当前生产状态以本目录为准，旧衣领制作记录保留为历史来源。

默认本地构建成功。[inspect-runtime.cjs](inspect-runtime.cjs)在独立测试档逐一核对22张编译PNG与源SHA、44个真实姿势的帧/方向/材质；全部通过，无页面错误，见[runtime/report.json](runtime/report.json)和[实机接触表](runtime/contact.jpg)。既有`browser-motion.cjs`剑/弓/杖/施法/闪避/跑动检查通过。普通试玩亦已刷新并现场观察单层衣领，见`runtime-after-live.png`。

本轮未改玩法代码、存档规则或相机规则；没有新增单元测试、依赖或运行图集。最终状态见[verification.json](verification.json)。

![实际Cocos待机领口](runtime/40-explore_idle_W07-0.jpg)
