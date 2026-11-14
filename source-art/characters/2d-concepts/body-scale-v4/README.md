# 四方向与动作尺度校准 v4

基准为用户当前认可的 `explore_idle_W01` 四方向站姿，保留 v3 的站姿头型与挥剑服装配色。覆盖主角全部 88 个动作配置、69 张图集、996 个独立物理帧；共用帧的武器/动作别名复用同一校准值。

## 修改

- 旧版只沿用了各动作原有的 `worldUnitsPerPixel`，外貌统一后仍存在尺度差异。本版在 manifest 根部增加 `frameScaleFactors`，以图像名称（无扩展名）和物理帧索引取值；游戏 quad、相对落点和 HUD 预览统一使用有效像素世界尺度。
- 四个基准站姿的校准值固定为 1。52 个其他待机物理帧额外按同方向的颈部到地面距离对齐，解决收剑/拔剑待机约 4%–6% 的高度变化。
- 活动帧按肩胯躯干、大小腿的等效长度校准，使用本地姿态模型的三维方向估计补偿投影缩短，排除剑、展开的手臂、发型和外接框。按动画族及方向取稳健中值，步态只保留有界平滑残差，防止膝盖抬起时整人被机械拉高。实际因弯腰、弯腿、腾空造成的轮廓高度变化仍保留。
- 尺度修正范围约为 0.9085–1.1230。身体缩放时，头部围绕原颈根做反向像素缩放，继续使用站姿头型；低于千分之一的变化省略再次采样。手、武器和其他身体区域的源纹理不做生成式重绘，服装不重新调色。
- 更新语义裁切与 atlas gutter，确保头部反向缩放不被旧裁切截断，且裁切中不混入邻帧。最终最大纹理边长 1623px，保留全部 `.meta`，脚底/腾空的原语义锚点不改。
- 直接覆盖当前资源，不新增原件或完整图集备份。`candidate-runtime` 是处理结果，不是原件副本。

## 本地工具与测量

复用已有 Pillow、NumPy、SciPy、Cocos Quad/SpriteFrame 和项目 Playwright。普通尺度与透明像素处理不需要自由生成，本次 **没有新增 Qwen 推理，也没有云端生成/编辑**。

姿态测量使用 [Google MediaPipe Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker) 的 full 模型和官方 `@mediapipe/tasks-vision` 1.2.2。工具许可为 Apache-2.0；仅部署在 `F:\Models\PoseCalibration`，没有加入游戏包或修改 ComfyUI 依赖。模型与依赖直连下载，显式禁代理并绑定 WLAN 192.168.1.14，实际路由及官方完整性/MD5 校验记录在 `F:\Models\deployment\pose-calibration-verification.json`。

浏览器的全部脚本、WASM、模型、图片由本地磁盘 route 提供，其他地址全部拒绝，没有把帧发送给外部姿态服务。996 帧中 981 帧检出姿态，967 帧通过骨段可见度、投影和异常范围筛选；剩余帧继承同族同方向的稳健值。姿态估计并非真实骨骼数据，不能单独代替实机美术检查。

在未施加待机颈高约束的有效测量中，等效身体长度相对基准的绝对误差中位数由约 2.33% 降至 0.94%，90 分位由约 6.84% 降至 2.88%。这些数字是同一估计器的内部校准结果，并非独立人体真值或美术无误保证。

## 复查入口

- `inventory.json`：修改前的尺寸、裁切、来源哈希清单，不包含整套原图片副本。
- `measure-pose.cjs` / `pose-landmarks.json`：本地姿态测量与结果。
- `calibrate.py` / `calibration.json`：校准公式、族级平滑、待机约束和各物理帧数值。
- `apply.py` / `apply-report.json`：原头像素反向缩放、独立帧打包、覆盖记录。
- `calibrated-states-small.jpg`：同一世界像素密度的静态对照；不是按各帧包围框分别拉满。
- `audit-runtime.cjs` / `runtime-audit.json`：构建后真实资源哈希、88 动作四方向全相位、有效缩放与锚点公式验证，以及同镜头游戏截图。

后续修图工具读取 `worldUnitsPerPixel` 时，必须同时乘上当前物理帧的 `frameScaleFactors`；v3 的共用 inventory 适配器已更新，避免新一轮修图又忽略本版尺度。

## 已完成验证

- `npm run check`、Cocos Creator 3.8.8 `web-mobile / concept-2d` 构建通过。
- 构建后 manifest 与源文件完全相同，69 张运行贴图 SHA-256 均匹配；88 动作、1364 次方向/相位采样没有动作、贴图、有效缩放或锚点公式不一致，页面异常为 0。
- 复用正常输入的 sword/bow/staff/spell/dodge/run 动作检查通过。所有贴图 `.meta` 哈希保留。
- `game-four-directions-small.jpg` 为真实构建下站立/持剑/跑步/挥剑的 16 张同镜头截图，`orthoHeight=2`，地面锚点屏幕位置差为 0。截图只做相同比例缩略，没有逐帧拉满。原始截图和读数见 `runtime-audit.json`。
- 头部几何补偿后尺寸变化上限小于 0.1%（该部分为省略的微小重采样）；图像重采样带来的亚像素边缘差异仍以实机截图为准。

本地游戏入口：`http://127.0.0.1:7469/desktop-preview.048c2.html?view=2d&revision=body-scale-v4`。
