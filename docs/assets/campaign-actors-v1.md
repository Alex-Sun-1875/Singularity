# Campaign actors v1

2026-11-08。当前是独立2D图像角色接入，生成、素材静态审阅和游戏验收分别记录。没有制作新的原生3D网格、骨骼或骨骼动画。

| 范围 | 数量 | 当前状态 |
|---|---:|---|
| 保留旧独立身份 | 4 | R1-1、R1-2、R1-3、BOSS_R1继续使用raider、shield、archer、captain原资源 |
| 两个新代表 | 2 | R2-1→mine-worker、R2-3→mine-crawler；H03/H04真实walk0/1、attack、掉血与转场释放/重入已验收 |
| 本轮新批次 | 30 | 19普通敌、11Boss；30/30静态审阅、安装及v3受控实际渲染检查已通过；自然主线遍历不在此验收范围 |
| 完整模板映射 | 36 | 24普通敌、12Boss；32个新身份与4个保留身份都有明确映射 |

[运行资产索引](../../src/cocos/assets/resources/flat2d/characters/campaign-v1-index.json)记录36项映射、30个新资源目录、图集/manifest哈希与动作键。[安装报告](../../source-art/encounters/cloud-world-v2/actor-production-v1/runtime-installation.json)记录373个既有人物、旧敌人与两个代表小样文件的前后哈希一致；没有覆盖这些资源。

## 源与处理

每个ID的`generation.json`、原始sheet、实际提示词、来源参考和`art-review.json`位于[生产目录](../../source-art/encounters/cloud-world-v2/actor-production-v1)。生产者各写各自记录；[聚合状态](../../source-art/encounters/cloud-world-v2/actor-production-v1/batch-status.json)是读取这些记录后的派生索引。[接触表分组](../../source-art/encounters/cloud-world-v2/actor-production-v1/review-groups)供静态复核，不能替代游戏截图。

复用Pillow、NumPy、SciPy与两个已通过游戏的小样流程，不安装新依赖。`prepare-enemy-actor.py`按完整主体归属保留跨名义格线的长钩、弓尖、附肢和共用基座，所有帧使用同一像素/世界尺度。人形walk以头盔/头部、机械以刚性核心作平移配准；不按每帧bbox放大。攻击按承重足、基座或核心投影校准，不拿武器尖当脚。

原始1254等实际尺寸均记录。源重排通常1536²；宽动作或完整低alpha包络需要时统一扩为2048²。生产图集整张缩为1024²，原点/矩形同比变换、worldUnitsPerPixel反比变换，物理尺寸不变；没有单独缩小某个宽动作。每张RGBA8 level0约4MiB，32种新身份若同时全部加载约128MiB，另有图像/驱动等开销；实际按场景需要加载。

R1-4、R2-4只替换真实LEFT列，其他12格RGBA精确保留。R3-4新长钩超过原313px格宽，因此统一扩格并重排：其他12主体原RGBA保留，坐标改变。ELITE_02修正front/back弓瞄后保留其他14主体，完整弓尖使用42个原空白gutter像素，不声称其他14整格字节未变。ELITE_06仅替换一个修正方向的主体，其他15主体保留。

## 动作边界与特殊身份

新身份每方向只有idle、两个实际walk姿态和一个primary姿态；E06例外使用三剑分行。当前不是完整逐招动作库，没有独立受击、死亡或斜向画面。缺失受击用本人idle，缺失死亡隐藏角色，不借另一人物补图。原生3D视图仍使用旧四类敌人资源。

E06是三具机械像与同一个静态基座，未生成走路。`attack_sword_step0/1/2`分别取对应剑姿态，普通`attack_sword`别名为step0；FlatActors按当前step优先使用存在的专用clip，再回本人通用clip，不改core时序。基座锚取plinth，不取举起的剑尖。U2-3是零足、三轨道、单镜片实体，锚取镜芯的地面投影，四行保持0.65m核心高度，不取finial或地影。

## 透明通道例外

默认只清alpha≤3；主体更高alpha像素逐字节保留。以下是独立、明确限定的派生处理，原raw均保留，不能推广为全批删低alpha：

- E05：两指定ROI内6个完全分离组件，共2269像素、maxAlpha16；与solid64不连通，机体RGBA不改。
- E07：仅maxAlpha8且连外边/名义gutter的背景flood，避开solid64膨胀3px保护带；全部保护带和alpha>8原RGBA不改。mask、移除计数与哈希在processed报告。
- U2-3：地影与镜体存在极淡桥，未假称isolated；以云端语义alpha与16个floor ROI作派生，保留实体solid128+1px，移除39438像素、maxAlpha105，保留像素RGBA不改。
- U1-3：云端输出仅作背景语义mask，不取其重绘RGB。原solid128+3px与所有保留RGBA精确不变，全部RGB保持原值；仍有约3px淡灰保护边，最终地面/手机QA重点看，若明显再限制matte带，不删除主体。

## 纹理生命周期与验收

FlatActors每实例对每个唯一敌纹理`addRef`一次，销毁节点、材质、frame、mesh后再`decRef`；不用强制`releaseAsset`绕过共享引用检查。迟到的已销毁实例加载成对释放。主角/NPC/行囊预览共享纹理排除在此敌人集合之外，遵循[Cocos 3.8资源释放说明](https://docs.cocos.com/creator/3.8/manual/en/asset/release-manager.html)。

两个代表的实际记录位于[矿机](../../src/cocos/test-results/enemy-combat-v1/mine-crawler-runtime.json)与[矿兵](../../src/cocos/test-results/enemy-combat-v1/mine-worker-runtime.json)：纹理ref1→离场ref0且失效→重入ref1，主角纹理仍有效，无console/request异常。新30种在v3构建中也完成了受控实际渲染和生命周期检查，详见下文。此验收不代表97场景全部视觉或完整主线已自然通关。


`concept-2d-campaign-v3`构建的[历史资产字节验证](../../test-results/campaign-v1/build-v3.json)已通过：32套已准备的1024生产PNG、运行目录PNG、编译PNG完全一致。这里不将1536/2048原像素源包与缩小后的PNG混称字节相同。构建默认2D，入口`index.93b53.js`的SHA256为`d897f333f360670d22256476d2980c6c74e16bf56bd569a759ed9861a2d9cd60`。36身份与E06分段clip的游戏QA完成后只补外部报告；不为改验收文字重写运行index、manifest或角色图。


当前演员验收见[外部QA覆盖层](../../source-art/encounters/cloud-world-v2/actor-production-v1/runtime-qa-overlay.json)，运行index的pending字段保留为安装时快照。

- [36模板实际渲染记录](../../src/cocos/test-results/enemy-actors-v1/actual-actor-render-report.json)：9次场景生命周期，每次最多4个身份，经真实FlatActors.build加载映射；1004个native mesh/UV帧、568个实际方向/gait/primary样本，释放ref0、主角保留、重入通过，console/request异常为0。方法是受控S02注入template，不能称自然关卡通关。
- [E06实际三剑记录](../../test-results/enemy-actors-v1/elite06-live-steps.json)：真实U1-06的phase自然推进，分别采样step0/1/2专用clip；世界位置与朝向固定，实际plinth结构底边三图均y320。整体alphaBounds含剑尖，不用它误判地脚跳动。
- Root独立看过36身份接触图；U1-3约3px保护边在实际地面可接受。此结论不延伸成实体手机或全部97场景视觉验收。

当前`concept-2d-campaign-v4`已按[构建与继承记录](../../test-results/campaign-v1/build.json)确认继承演员证据：整个compiled resources/native与resources/import相对v3的差异均为空；FlatActors、32图集、30个新manifest和运行index哈希未变。原始v3实际演员报告与E06三剑报告保留，不冒称在v4重新执行。当前服务为`http://127.0.0.1:7476/`，默认2D；入口`index.33620.js`的SHA256为`3cedd845c92a40be521e2780ae8773a372d47a9650b0272efae93155ce5e171d`。

VFX专项验收由独立结果另记，此演员说明不据此宣称VFX通过。不为更新验收文字重写图集、manifest、FlatActors或运行索引。
