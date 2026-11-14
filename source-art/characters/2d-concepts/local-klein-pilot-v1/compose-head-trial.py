"""Composite the locally edited head into a copy; preserve all pixels outside mask."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
original_path = ROOT / "running-right-input.png"
head_path = ROOT / "results/head-local/head-local_00001_.png"
original = Image.open(original_path).convert("RGB")
head = Image.open(head_path).convert("RGB").resize((128, 128), Image.Resampling.LANCZOS)
box = (231, 79, 359, 207)
local_mask = Image.new("L", (128, 128), 0)
ImageDraw.Draw(local_mask).rounded_rectangle((34, 0, 110, 84), radius=12, fill=255)
local_mask = local_mask.filter(ImageFilter.GaussianBlur(1.25))
mask = Image.new("L", original.size, 0)
mask.paste(local_mask, box[:2])
candidate = original.copy()
candidate.paste(head, box[:2])
composited = Image.composite(candidate, original, mask)
output = ROOT / "results/head-local/running-head-local-composited.png"
composited.save(output)
mask.save(ROOT / "results/head-local/composite-mask.png")
a, b, m = np.asarray(original), np.asarray(composited), np.asarray(mask)
unchanged = bool(np.array_equal(a[m == 0], b[m == 0]))
assert unchanged
assert np.array_equal(a[180:], b[180:])
report = {"method": "Local Klein crop edit, downsampled and composited with Pillow onto an unchanged copy of the original input", "model_head_output": str(head_path), "output": str(output), "head_crop_xyxy": box, "outside_mask_pixels_identical": unchanged, "all_pixels_below_y180_identical": True, "production_assets_modified": False, "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
(ROOT / "results/head-local/composition.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

sources = [ROOT / "standing-right-input.png", original_path, ROOT / "results/running-head-reference-512/running-head-reference-512_00001_.png", output]
labels = ["Standing reference", "Current running", "Full-frame Klein", "Local head composite"]
crops = [(179, 66, 307, 194), box, (256, 77, 384, 205), box]
board = Image.new("RGB", (1024, 680), (245, 245, 245))
draw = ImageDraw.Draw(board)
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
except OSError:
    font = ImageFont.load_default()
for i, (source, label, crop) in enumerate(zip(sources, labels, crops)):
    im = Image.open(source).convert("RGB")
    draw.text((i * 256 + 8, 10), label, font=font, fill=(25, 25, 25))
    board.paste(im.resize((240, 360), Image.Resampling.LANCZOS), (i * 256 + 8, 40))
    board.paste(im.crop(crop).resize((240, 240), Image.Resampling.LANCZOS), (i * 256 + 8, 426))
board.save(ROOT / "comparison-final.jpg", quality=88, optimize=True)
print(json.dumps(report, indent=2))
