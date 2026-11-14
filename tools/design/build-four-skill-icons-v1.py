"""Deterministic relief motifs on the existing approved skill-icon frame.

No generated editing, model inference, downloads or additional dependencies.
"""
from pathlib import Path
import json
import math
import random
import uuid
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "src/cocos/assets/resources/ui/combat-relief"
SOURCE = ROOT / "source-art/ui/four-skill-kit-v1"


def icon(name, paths, polygons):
    size, scale = 256, 3
    rng = random.Random(1112)
    background = Image.new("RGBA", (size, size))
    pixels = background.load()
    for y in range(size):
        for x in range(size):
            light = max(0, 1 - math.hypot(x - 112, y - 92) / 180)
            grain = rng.randint(-2, 2)
            pixels[x, y] = (int(13 + light * 19) + grain, int(10 + light * 13) + grain, int(7 + light * 7) + grain, 255)
    base = background.resize((size * scale, size * scale))
    glow = Image.new("RGBA", base.size)
    draw = ImageDraw.Draw(glow)
    for points, width in paths:
        draw.line([(int(x * scale), int(y * scale)) for x, y in points], fill=(191, 132, 50, 150), width=int((width + 5) * scale), joint="curve")
    base = Image.alpha_composite(base, glow.filter(ImageFilter.GaussianBlur(5 * scale)))
    draw = ImageDraw.Draw(base)
    for points in polygons:
        coords = [(int(x * scale), int(y * scale)) for x, y in points]
        draw.polygon([(x + 2 * scale, y + 3 * scale) for x, y in coords], fill=(5, 4, 3, 255))
        draw.polygon(coords, fill=(168, 116, 48, 255))
        draw.line(coords + [coords[0]], fill=(255, 218, 137, 255), width=scale)
    for points, width in paths:
        coords = [(int(x * scale), int(y * scale)) for x, y in points]
        draw.line([(x + scale, y + 2 * scale) for x, y in coords], fill=(4, 3, 2, 255), width=(width + 3) * scale, joint="curve")
        draw.line(coords, fill=(150, 100, 41, 255), width=width * scale, joint="curve")
        draw.line([(x, y - scale) for x, y in coords], fill=(248, 202, 114, 255), width=max(1, width - 3) * scale, joint="curve")
    base = base.resize((size, size), Image.Resampling.LANCZOS)
    frame = Image.open(DEST / "rpg-bow-04.png").convert("RGBA")
    mask = Image.new("L", (size, size), 255)
    ImageDraw.Draw(mask).rounded_rectangle((8, 8, 247, 247), radius=5, fill=0)
    base.paste(frame, (0, 0), mask)
    base.save(DEST / f"{name}.png")
    metadata = json.loads((DEST / "rpg-bow-04.png.meta").read_text(encoding="utf-8"))
    old, new = metadata["uuid"], str(uuid.uuid5(uuid.NAMESPACE_URL, "singularity:four-skill-kit-v1:" + name))
    metadata = json.loads(json.dumps(metadata).replace(old, new).replace("rpg-bow-04", name))
    (DEST / f"{name}.png.meta").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    base.save(SOURCE / f"{name}.png")


def main():
    SOURCE.mkdir(parents=True, exist_ok=True)
    loop = [(128 + 63 * math.cos(i * math.tau / 48), 132 + 36 * math.sin(i * math.tau / 48)) for i in range(49)]
    teeth = []
    for side in [-1, 1]:
        for i in range(5):
            x, y = 78 + i * 25, 132 + side * 30
            teeth.append([(x - 7, y), (x + 7, y), (x, y - side * 17)])
    icon("rpg-bow-06", [(loop, 7), ([(62, 156), (51, 192), (77, 199)], 6), ([(193, 155), (206, 191), (179, 199)], 6), ([(95, 101), (128, 79), (160, 101)], 5)], teeth)
    bow = [(148 + 38 * math.sin(i * math.pi / 24), 54 + i * 6) for i in range(25)]
    icon("rpg-bow-07", [(bow, 7), ([(148, 54), (132, 126), (148, 198)], 3), ([(109, 126), (217, 126)], 5), ([(99, 174), (56, 174), (76, 155)], 7), ([(56, 174), (76, 193)], 7)], [[(223, 126), (204, 117), (204, 135)]])
    (SOURCE / "provenance.json").write_text(json.dumps({"date": "2026-11-12", "method": "deterministic Pillow geometry and compositing", "frame": "existing approved rpg-bow-04 outer frame only", "motifs": {"BOW_06": "snare jaws and stakes", "BOW_07": "bow shot and backward movement arrow"}, "generated": True, "artReview": "pending separate visual review", "script": "tools/design/build-four-skill-icons-v1.py"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
