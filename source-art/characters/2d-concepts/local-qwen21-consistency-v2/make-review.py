"""Render fixed-scale local before/after previews without modifying artwork."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

ROOT = Path(__file__).resolve().parent
FONT = r"C:\Windows\Fonts\msyh.ttc"
TITLE = ImageFont.truetype(FONT, 14)
SMALL = ImageFont.truetype(FONT, 11)
CELL_W, CELL_H = 208, 324
VIEW = (192, 288)


def checker(size):
    im = Image.new("RGBA", size, (226, 226, 226, 255))
    draw = ImageDraw.Draw(im)
    for y in range(0, size[1], 12):
        for x in range(0, size[0], 12):
            if (x // 12 + y // 12) % 2:
                draw.rectangle((x, y, x + 11, y + 11), fill=(242, 242, 242, 255))
    return im


def card(canvas, position, path, title, subtitle):
    x, y = position
    draw = ImageDraw.Draw(canvas)
    draw.text((x + 8, y + 3), title, fill=(25, 25, 25), font=TITLE)
    draw.text((x + 8, y + 21), subtitle, fill=(75, 75, 75), font=SMALL)
    original = Image.open(path).convert("RGBA")
    if original.size != (512, 768):
        raise ValueError("Do not stretch or fit a changed canvas to make the result look aligned")
    panel = checker((512, 768))
    panel.alpha_composite(original)
    canvas.paste(panel.convert("RGB").resize(VIEW, Image.Resampling.LANCZOS), (x + 8, y + 37))


def details(canvas, position, path, cap_box, title):
    x, y = position
    draw = ImageDraw.Draw(canvas)
    draw.text((x + 8, y + 3), title, fill=(25, 25, 25), font=TITLE)
    original = Image.open(path).convert("RGBA")
    for box, scale, offset, label in [
        (cap_box, 3, 32, "剑帽原像素 3×"),
        ((146, 368, 187, 437), 1.5, 196, "同位置手部 1.5×"),
    ]:
        crop = original.crop(box)
        panel = checker(crop.size)
        panel.alpha_composite(crop)
        panel = panel.convert("RGB").resize((round(crop.width * scale), round(crop.height * scale)), Image.Resampling.NEAREST)
        canvas.paste(panel, (x + (CELL_W - panel.width) // 2, y + offset))
        draw.text((x + 8, y + offset - 15), label, fill=(75, 75, 75), font=SMALL)


def main():
    canvas = Image.new("RGB", (CELL_W * 4 + 16, CELL_H * 3 + 16), (250, 250, 248))
    items = [
        ("body/front/original-rgba.png", "正面跑步 · 原件", "统一画布与尺度"),
        ("final/run-front.png", "正面跑步 · 本轮", "Qwen补绘＋原件保护＋校色"),
        ("body/back/original-rgba.png", "背面跑步 · 原件", "统一画布与尺度"),
        ("final/run-back.png", "背面跑步 · 本轮", "比例＋背剑＋衣裤色"),
        ("sword/original-rgba.png", "背剑站姿 · 原件", "原头、手和服装"),
        ("final/standing-back.png", "背剑站姿 · 本轮", "整剑视觉长度约＋26%"),
        ("palette/side-inputs/run-right-p4-rgba.png", "侧面跑步 · 原件", "服装颜色对照"),
        ("final/run-right.png", "侧面跑步 · 本轮", "站姿参考校色，保护手剑"),
    ]
    for index, (path, title, subtitle) in enumerate(items):
        card(canvas, (8 + index % 4 * CELL_W, 8 + index // 4 * CELL_H), ROOT / path, title, subtitle)
    y = 8 + CELL_H * 2
    card(canvas, (8, y), ROOT / "body/front/reference-standing-rgba.png", "正面站姿参考", "本轮头型与布料颜色基准")
    card(canvas, (8 + CELL_W, y), ROOT / "body/back/reference-standing-rgba.png", "背面站姿参考", "本轮头型与布料颜色基准")
    details(canvas, (8 + CELL_W * 2, y), ROOT / "sword/original-rgba.png", (178, 358, 220, 401), "背剑细节 · 原件")
    details(canvas, (8 + CELL_W * 3, y), ROOT / "final/standing-back.png", (147, 423, 189, 466), "背剑细节 · 本轮")
    canvas.save(ROOT / "comparison-final.jpg", quality=92, subsampling=0)
    print(json.dumps({"path": str(ROOT / "comparison-final.jpg"), "size": list(canvas.size),
                      "scale": "all full figures 0.375x; no individual bbox fitting", "artwork_modified": False}))


if __name__ == "__main__":
    main()
