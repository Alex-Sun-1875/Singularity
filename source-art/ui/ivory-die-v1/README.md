# 骨质铜角锻造骰 v1

2026-11-10。按用户确认保留原有暗金奇幻风。使用云端 OpenAI 内置 `image_gen` 生成一个空白骨质铜角骰体，无参考图输入。原图 `original.png` 保留透明 RGBA；仅用 Pillow 做透明边界裁切和 Lanczos 缩放。

运行资源：`src/cocos/assets/resources/ui/dice/ivory-bronze-v1.png`，369×384，276,052 字节。完整提示词见 `prompt.txt`，处理和 SHA256 见 `processing.json`。实际点数、投掷状态和奖励由 Cocos/core 实时控制，图片不含点数或规则。

生成状态：完成。美术检查：已检查骨质表面、铜角、空白正面和透明边缘，并查看1280×720、915×412及667×375的真实Cocos画面；用户最终美术验收待定。
