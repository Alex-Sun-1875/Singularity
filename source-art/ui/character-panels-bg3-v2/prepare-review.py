"""Archive the cloud-generated mockups and build a deterministic Pillow overview."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
CLOUD = Path(r"C:\Users\Alexa\.codex\generated_images\01a1c46b-eff4-7a71-a1ee-6621fccd0eb5")
REFERENCE = ROOT.parent / "character-panels-bg3-v1/screens/04-forging.png"
ITEMS = [
    ("01-preview", "exec-58abc338-1067-4fe7-89ea-add02b2c591e.png", "强化前：查看随机候选"),
    ("02-result", "exec-110fd9cc-e877-48ea-98a5-2e2a10aa74bc.png", "强化后：揭晓第三条属性"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare() -> None:
    (ROOT / "screens").mkdir(exist_ok=True)
    (ROOT / "review").mkdir(exist_ok=True)
    records = []
    for name, filename, title in ITEMS:
        source = CLOUD / filename
        target = ROOT / "screens" / f"{name}.png"
        shutil.copyfile(source, target)
        with Image.open(target) as screen:
            size = list(screen.size)
            screen.verify()
        records.append({
            "title": title,
            "file": f"screens/{name}.png",
            "prompt": f"prompts/{name}.txt",
            "native_size": size,
            "original_cloud_file": str(source),
            "sha256": sha256(target),
            "postprocess": "None; copied byte-for-byte from cloud output",
        })

    board = Image.new("RGB", (1884, 496), "#110D09")
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 25)
    for index, (name, _, title) in enumerate(ITEMS):
        x = 10 + index * 942
        image = Image.open(ROOT / "screens" / f"{name}.png").convert("RGB")
        board.paste(image.resize((922, 427), Image.Resampling.LANCZOS), (x, 52))
        draw.text((x + 2, 10), title, font=font, fill="#DAAE65")
    board.save(ROOT / "review/overview.jpg", quality=95, subsampling=0)

    metadata = {
        "date": "2026-11-10",
        "method": "OpenAI built-in image_gen, cloud; two separate image calls, one state per call",
        "generation_status": "complete",
        "art_review_status": "Assistant checked three-slot count, rarity, existing values, one newly revealed affix, phase limit and currency arithmetic; user review pending",
        "scope": "Visual design only; no runtime UI, combat rules or saves changed",
        "design": "../../../docs/design/equipment-random-enhancement-v2.md",
        "reference_inputs": [{
            "file": "../character-panels-bg3-v1/screens/04-forging.png",
            "sha256": sha256(REFERENCE),
            "role": "Style and shell reference; earlier deterministic enhancement values superseded by the new prompts",
        }],
        "illustrated_transaction": {
            "item": "最后一班岗",
            "catalog_id": "DG_L01",
            "rarity": "传奇",
            "rank_before": 5,
            "rank_after": 6,
            "affix_capacity": 3,
            "phase_cap": 6,
            "item_cap": 12,
            "gold": {"before": 868, "cost": 130, "after": 738},
            "iron": {"before": 96, "cost": 3, "after": 93},
            "new_affix": "力量 +2",
            "values_status": "Illustrative affix ranges and probabilities; not implemented balance data",
        },
        "target": {"logical_viewport": [844, 390], "platform": "TapTap minigame / Cocos Creator 3.8.8", "validation": "Raster concepts only; touch targets, safe area and actual device validation pending implementation"},
        "screens": records,
        "overview": {"file": "review/overview.jpg", "method": "Pillow side-by-side review layout; Lanczos downsampling and rasterized Windows UI label text; no font file redistributed"},
    }
    (ROOT / "provenance.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Saved two original screens, review overview and provenance.")


if __name__ == "__main__":
    prepare()
