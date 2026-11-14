# 既有云端装备板的确定性图标接入

2026-11-08。没有新生图、没有模型推理、没有下载依赖。原始13张选用板与生成来源保持不变。

- `manifest.json`：50个明确ID候选的源图、裁切矩形、源/结果SHA256、真实生成提示词来源与像素处理记录。
- `review.json`：独立输出审阅。49件通过行囊图标检查；J06因原板链条不完整暂不接入。
- `runtime-install.json`：实际接入49件的记录。加原v3明确16件，当前图标覆盖65/74。
- `icons-review.jpg`、`legacy-icons-review.jpg`：本地缩略图排版。不能作为持武器、穿戴或动画验收证据。

复现：`python tools/design/prepare-campaign-equipment.py`；通过当前独立审阅后安装：`python tools/design/prepare-campaign-equipment.py --install`。脚本使用已安装Pillow/numpy/scipy，拟合纸底并以成熟连通域操作生成alpha，保留物品原色，等比缩放到512×512透明画布。

DE06长剑、DR3-03弯刀和DU2-03闭合链吊坠跨过原板的均匀网格，采用独立实裁矩形；不能按等分网格硬切。六区板下排仅接明确永久物编号，历史T03/T06/T08不接入。

运行资源使用独立`equipment/campaign-v1/index`，`EquipmentArt.icon`优先原v3映射，再读该索引，最后保留类别图标。原每类五阶设计图谱未插入额外卡片。

本轮仅审阅图标大小下的身份、完整主体、透明边与比例；未宣称用户接受、全尺寸边缘生产通过或97场景视觉验收。独立生命药/火油/检查点补给保持用户最新约定，与纯技能资源分开。
