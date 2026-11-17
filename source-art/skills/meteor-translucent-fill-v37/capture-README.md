# v37 实景录制工具

仅准备工具，不构建或提前录制。目标是将黑色中央填为淡的火焰橙色，同时让整个法阵更透明；保留同心圆、完整纹路、颜色族、几何范围、UV和生命周期，其它特效不改。最终素材/provenance以root ready为准，默认 assets/provenance.json，effect复用v35r2。

before精确引用v36 final-r1/final-empty-r1。收到唯一标准test冻结快照后，先empty预警与.65秒原帧供root审中央填色/透地，通过再normal。最终仅两条FIR02 9秒，真实1级旅程→独立合法满级训练会话→恢复原旅程，默认相机、完整HUD和角色保留，不改规则/seed/范围。

renderer ground.inspect.opacity按既有逻辑保持.9，贴图alpha本轮允许且预期变化。两者分开记录，不要求v36/v37像素alpha相同，不把alpha非零或绘制计数当成填色/透明视觉验收。

同镜头固定裁区预警板展示v36/v37；.65/2.8/3.5秒同帧板保留法阵与中央火焰。只裁切、等比缩放与排版，不后期改色/提亮/变透视/抠人。沿用原有触地/9阶段保持清空/normal生命周期流程，不新增场景、测试依赖或冗长统计。

云端源/生成JSON/提示词只引用v35一份，v37为确定性填充与透明调整，不运行模型。材质计算样张明确非native；最终只用实际Cocos画布判断中央淡橙、连续填色和透地。

freeze-build.py仅在真实构建完成与锁释放后做逐文件SHA一致的只读副本；capture --build-dir必须匹配snapshot/copy proof。root目视通过后编码native与固定裁切closeup，各270帧/30fps/9秒，最终记录本地候选、用户美术/TapTap真机待验。
