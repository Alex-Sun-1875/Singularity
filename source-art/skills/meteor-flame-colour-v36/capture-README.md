# v36 实景录制工具

仅确定性校色：让法阵贴合中央火焰亮橙，保持 v35 同心圆、完整纹路、alpha、清晰度、范围、UV、中心点燃及余火时序。云端源/提示词只引用 meteor-complete-sigil-v35/seal 中已有文件，本轮不调用模型。

收到 root 唯一标准 test build + frozen snapshot 后，只录 FIR02 normal + empty 各9秒。正式1级旅程 → 独立合法满级训练会话 → 原旅程恢复；使用真实 ultimate 输入、默认相机和完整HUD，不隐藏人物或改规则/seed。before 为 v35 final2，两段实际原片与 metadata 保留独立 compiled SHA。

默认工程素材 provenance 为 assets/provenance.json；capture 可通过 --seal-provenance 指定，media 跟随 capture 路径。最终两纹理为 colour/light-v36，effect复用fire-seal-v35r2；资源 source/served SHA 以最终美术 ready 为准，源生成/材质计算/实际 native 三类分开记录。

freeze-build.py 仅在真实构建完成、锁释放后逐字节复制并核验输出，不调用构建器。capture.cjs 的 --build-dir 必须匹配 snapshot.json 与 copy proof；不读取正在导出的半产物。

重点板为 sigil-flame-v35-vs-v36-native.jpg：同一实际帧内保留法阵和中央火焰，按 .65/2.8/3.5 秒分别比较 v35 与 v36。近景/阶段板只固定裁切、等比缩放与排版，不改色、亮度、alpha、时间或透视。亮橙匹配是视觉色系判断，不宣称受透明度/辉光影响的像素RGB完全相同。

沿用已存在的触地误差<0.0001m、9阶段保持/清空、固定support点燃、退火连续与normal生命周期流程。渐退暂停在blast age约3.7s进行，暂停active隐藏但缓存last-draw opacity与权威clock不变，恢复后继续下降；原重置/切职业在seal仍active时触发。没有新增场景、测试依赖或其它技能回归。

先录empty，并在.65秒真实帧供root快速审同帧色彩，再继续normal。root实际目视候选通过并技术检查完成后，才编码完整 native / 固定裁切 closeup，均270帧、30fps、9秒。最终标本地候选、用户美术与TapTap真机待验，不用计算材质样张冒充游戏实景。
