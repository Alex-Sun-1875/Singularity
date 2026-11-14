# 对称石刻传送点 v6

本版作为历史样式留存，当前运行已采用[古代符文传送阵版](../waypoints-runes-v8/README.md)。

对应用户后续要求“需要做成对称的”“风格不好看，换一下”。本版采用用户最初石厅参考中的磨损灰石、雕刻阴影和少量苔痕，传送纹样改为石面内凿出的八角封印与冷蓝光。保持左右中轴对称，采用新的完整材质图，不沿用粉紫圆环徽标外观。

## 原图与材质

- [原始云端图](carved-waystone-generated.png)、[提示词](prompt.txt)、[来源与五张运行图 SHA](generation.json)
- [必要的参考局部](map-style-reference.png)、[材质小样](material-review.jpg)
- 处理脚本：`tools/model-pipeline/prepare_waypoint_carved.py`

使用 OpenAI image_gen 云端生成一张代表石刻立面。原图独立保存；Pillow 以中轴镜像统一材质和轮廓，从冷蓝色差提取凿痕光效，将石材底色、稳定刻纹和柔光分层。窄处复用同一八角雕刻局部作为地嵌。五张运行 RGBA 都逐通道验证水平镜像误差为0。未运行本地生成模型或新增依赖。

## 游戏呈现

石刻面使用 Cocos 原生不透明 alpha-test 材质并写入深度，保留图像外轮廓并正确遮挡后方人物。原生网格作为内藏承托体，避免旧石块轮廓盖过新材质；地嵌承托改为低矮八角石。主视角下石刻正面朝向固定世界角度，纹样对称，视角改变时不转向相机。开放时只有凿痕发出克制冷蓝光，锁定时光效变暗。

原97区、320个定向出口、1.35m交互、剧情开关、到达坐标与旅行规则继续复用。所有摆放与碰撞仍由既有 `PortalPlacement` / `SceneBuilder` / `Navigation` 决定；本轮不改变导航或连接。

## 验收

生成成功、材质查看、实际游戏验收分开记录。最终运行包为 `portal-carved-v2`，已完成 Codex 目视检查；这不代表用户已经确认美术风格。

- [最终运行记录](runtime-review.json)、[构建与原生素材证明](portal-carved-v2-build.json)、[在线预览核验](live-preview-review.json)
- [游戏实景](runtime-preview.jpg)及[实际截图来源](runtime-preview.sources.json)
- [97区、320出口及640个通路目标](navigation-review.json)：316座立碑、4处八角地嵌，无新增通路回归，原角色构造未替换。
- [桌面与触屏交互](input-review.json)：各4段实际往返，锁定拒绝、真实解锁与返程、重复输入仅换图一次、镜头变化不转动符印；6纹理引用稳定，旧网格与材质全部释放。错误与失败请求均为0。
- [承托体与材质轮廓核对](painted-backing-review.json)：最终默认视角下，旧承托体的全部投影像素都在新材质透明轮廓内。石刻面使用不透明 alpha-test，地嵌底改为八角形。

采用真实 Cocos 绘制完成事件等待稳定画面后采样；检查范围为区域渲染、导航与代表输入，不冒充完整战役通关或真机性能测试。首轮 `portal-carved-v1` 留作承托体轮廓对照。

此历史包不再由主预览提供。当前运行及预览见[古代符文版](../waypoints-runes-v8/README.md)。

此前[对称徽标 v5](../waypoints-symmetric-v5/generation.json)已按用户风格反馈弃用，没有被选为运行版本；此前[石面符印 v4](../waypoints-stone-v4/README.md)保留历史构建与检查。
