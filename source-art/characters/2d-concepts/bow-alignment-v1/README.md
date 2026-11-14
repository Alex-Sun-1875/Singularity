# 背跑腿形与放箭稳定性修正

2026-11-09，已接入默认7469本地试玩。

复查确认背跑四帧小腿/靴子仍有侧扭，本轮修复up方向run阶段2、3、6、7。一次云端OpenAI image_gen仅提供下肢局部；其他28个跑步身体帧逐字节保留，四个修改帧标准画布y475以上的原生像素也逐字节保留。步行、武器图集、头部、上衣、握持点与世界根锚点保留。脚端因纠正靴形有小幅变化，正常屈膝与腾空仍保留。两张跑步图集复用已有UUID，既有原生打包工具重排UV，不新增运行纹理。

输入为`rear-run-edit-target.png`四格局部及`rear-leg-reference.png`已审阅裤靴。完整提示词见[rear-run.prompt.txt](rear-run.prompt.txt)，原始云端输出为`rear-run-cloud.png`（2170×725 RGBA，Codex generated_images中的`exec-186f000f-9488-4737-98ee-e9490001a23a.png`）。未运行本地模型或下载依赖。生成、[美术审阅](rear-run-review.json)、[原生像素保护核验](rear-run-native-preservation.json)及[安装](rear-run-install.json)分开记录。[repair-rear-run.py](repair-rear-run.py)复用Pillow与既有atlas packer，候选通过审阅后才安装。

2D相机稳定跟随角色，瞄准、技能范围和释放后的焦点不再自动改变取景中心与缩放；滚轮手动缩放、3D取景规则保留。原手部偏移在0.14秒内快速归零，造成箭身方向与实际位移不一致；现在直线箭从可见出箭点到原权威射线末端作线性对应，原生箭网格沿显示轨迹定向。命中、伤害、射程及BOW02权威折线路径不变。复用现有Cocos正交相机、Quat.rotationTo与箭网格，无新增库。

## 验证

- 游戏及核心类型检查、默认本地构建成功，既有`browser-motion.cjs`剑/弓/杖/施法/闪避回归通过。
- [inspect-runtime.cjs](inspect-runtime.cjs)在独立满物品测试档执行，为隔离镜头与箭体，在S02受控场景省略敌人。12种情形的相机高度与静止角色屏幕位置均无变化；10种实际出箭情形覆盖四向W07、W08/L02、轻点/蓄满及BOW01/03，箭头与位移夹角小于0.001°。BOW02/05无目标时只验瞄准镜头，不声称出箭覆盖。旧普通箭最差约22.8°，见`before/report.json`；修正结果见[after/verified.json](after/verified.json)。
- 最终图集重建后复用走跑实机检查，覆盖816次阶段/方向及5场景正常移动；4张运行PNG均与源字节一致。真实Cocos背面4帧步行、8帧跑步已放大审阅，[动画](after/rear-legs-final.gif)与[逐帧图](after/rear-leg-final-runtime.jpg)保留。
- 普通存档已刷新，通过界面换弓并实际长按J释放；截图确认直线离弦，等级40及无需蓄能保留，见[after/current-save-release.png](after/current-save-release.png)。

总验收见[final-verification.json](final-verification.json)。本轮未新增单元测试、测试依赖或完整动画系统，未将隔离检查声称为全地图自然通关或手机性能验收。
