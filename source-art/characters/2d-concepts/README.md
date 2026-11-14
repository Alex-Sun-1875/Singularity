# 由已设计人物图派生的2D素材

工具：内置 `image_gen.imagegen`，未调用CLI/API后备路径。日期：2026-11-06。

输入为本项目既有主角、探索者、对手及劫匪/队长设计图。当前运行资源位于 `src/cocos/assets/resources/flat2d/`，不再使用早期 `src/prototype-2d/assets/characters/` 的3D烘焙人物。所有10个已放置角色均有独立身份资源，没有概念图互借回退。

主角和弥菈的walk图集为1536×1024、4列×4行，每格384×256。行依次为正面/右侧/背面/左侧；列依次为待机、左步、经过、右步。主角另有相同布局的4帧剑击图。游戏每张图集共享纹理，通过原生UV切帧及逐格脚底锚点显示，不新增骨骼系统。

主角主提示：严格保留已设计的成年面孔、深棕卷发、青绿刺绣短披布、合身棕色皮甲、象牙衬袖、单肩钢甲和测绘工具；固定俯视3/4正交机位、均匀四方向逐帧布局、透明背景。背景提取另用内置imagegen完成，保持人物位置/尺寸/身份不变。未以程序重绘或换色人物；PIL只读取alpha以生成锚点和包围框元数据。

完整旅店、弥菈、剑击生成提示及默认原始输出路径见 `generation-prompts.json`。主角源图与透明提取结果也保留在Codex generated_images；选用结果已复制进项目。`raphael-walk.png`、`raphael-attack.png`、`mira-walk.png` 是当前源文件副本。

后续整合已补齐主角11种状态、剑/弓/杖站立/行走与攻击，以及跑、翻滚、受击、倒地、施法和交互。见 `player-actions/final-verification.json`、`player-actions/root-generation-prompts.json` 与安装记录。NPC独立方向图来源见 `npcs/README.md`；四类敌人的移动、攻击准备/接触/恢复与死亡图见 `enemies/README.md`。单帧受击与站立NPC按实际帧数记录，没有重复帧凑动作。

动作是依据已确认形象派生的低帧2D姿态序列，侧背面、扣件和装备小细节可能存在差异。装备表现按剑、弓、杖类别共享；并非每件数值装备都独立重画纸娃娃。运行验证与可玩范围见 `docs/assets/concept-2d-preview.md`；源图alpha/哈希检查不能替代引擎内视觉验收。
