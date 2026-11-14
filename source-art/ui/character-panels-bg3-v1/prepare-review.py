"""Prepare review assets; Pillow-only layout and a deterministic text correction."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
CLOUD = Path(r"C:\Users\Alexa\.codex\generated_images\01a1c46b-eff4-7a71-a1ee-6621fccd0eb5")
GENERATIONS = [
    ("01-character", "exec-6f5abce3-d112-402a-92c4-eb473b944899.png", "人物"),
    ("02-equipment", "exec-5ec92e73-12d1-48f7-96c6-7bf16dadb2c8.png", "装备"),
    ("03-skills", "exec-55897f73-e755-48a5-bcd1-dbb02f360bc9.png", "技能"),
    ("04-forging", "exec-dc88f04c-4761-4a90-99d9-c632ace6c7b4.png", "锻造强化"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def correct_skill_label() -> None:
    """Replace only the generated first glyph 破 with the actual skill's 铁."""
    original = Image.open(CLOUD / GENERATIONS[2][1]).convert("RGB")
    shutil.copyfile(CLOUD / GENERATIONS[2][1], ROOT / "review/03-skills-generated.png")
    result = original.copy()
    left, top, right, bottom = 836, 232, 870, 267
    # Interpolate the nearby dark background, keeping the rest of the art exact.
    patch = Image.new("RGB", (right - left, bottom - top))
    for y in range(patch.height):
        a = original.getpixel((left - 1, top + y))
        b = original.getpixel((right, top + y))
        for x in range(patch.width):
            t = (x + 1) / (patch.width + 1)
            patch.putpixel((x, y), tuple(round(v * (1 - t) + w * t) for v, w in zip(a, b)))
    result.paste(patch, (left, top))
    scale = 4
    glyph = Image.new("RGBA", (36 * scale, 38 * scale))
    draw = ImageDraw.Draw(glyph)
    font = ImageFont.truetype(r"C:\Windows\Fonts\STSONG.TTF", 29 * scale)
    draw.text((2 * scale, 3 * scale), "铁", font=font, anchor="lt", fill="#F0E5C8", stroke_width=1)
    glyph = glyph.resize((36, 38), Image.Resampling.LANCZOS)
    result.paste(glyph, (836, 232), glyph)
    result.save(ROOT / "screens/03-skills.png")
    result.crop((825, 225, 975, 278)).resize((750, 265)).save(ROOT / "review/skill-label-final.png")


def make_overview() -> None:
    board = Image.new("RGB", (1884, 992), "#110D09")
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 25)
    for index, (name, _, title) in enumerate(GENERATIONS):
        x, y = 10 + (index % 2) * 942, 52 + (index // 2) * 496
        screen = Image.open(ROOT / "screens" / f"{name}.png").convert("RGB")
        board.paste(screen.resize((922, 427), Image.Resampling.LANCZOS), (x, y))
        draw.text((x + 2, y - 42), f"{index + 1:02} {title}", font=font, fill="#DAAE65")
    board.save(ROOT / "review/overview.jpg", quality=95, subsampling=0)


def write_provenance() -> None:
    records = []
    for name, filename, title in GENERATIONS:
        source = CLOUD / filename
        final = ROOT / "screens" / f"{name}.png"
        records.append({
            "screen": title,
            "file": final.relative_to(ROOT).as_posix(),
            "prompt": f"prompts/{name}.txt",
            "original_cloud_file": str(source),
            "original_sha256": sha256(source),
            "final_sha256": sha256(final),
            "native_size": list(Image.open(source).size),
            "reference_inputs": ["references/hero-identity.jpg"] if name == "01-character" else ["screens/01-character.png", "references/hero-identity.jpg"],
            "postprocess": "Pillow: first glyph 破 → 铁 in 铁誓壁垒; raw generation preserved in review/03-skills-generated.png" if name == "03-skills" else "None; original generation copied without pixel edits",
        })
    metadata = {
        "date": "2026-11-10",
        "method": "OpenAI built-in image_gen, cloud generation; no local generative model",
        "generation_status": "complete",
        "art_review_status": "Assistant reviewed visual consistency and corrected one generated skill-name glyph; user approval pending",
        "scope": "Visual concepts only; no runtime UI or game assets replaced",
        "target": {"logical_viewport": [844, 390], "platform": "TapTap minigame / Cocos Creator 3.8.8", "touch_validation": "Pending implementation; bitmap concepts do not certify touch targets or safe areas"},
        "design_reference": {
            "title": "Baldur's Gate 3 Community Update #15: Absolute Frenzy (2022 early-access UI case study)",
            "url": "https://www.baldursgate3.game/news/community-update-15-absolute-frenzy_49",
            "usage": "Reference research for character sheet / inventory / spellbook hierarchy, filters, and tooltips; no official screenshot supplied to image_gen",
        },
        "hero_board": {
            "file": "references/hero-identity.jpg",
            "sha256": sha256(ROOT / "references/hero-identity.jpg"),
            "sources": ["source-art/characters/2d-hairstyle-portraits-v1/curly-original.png", "source-art/characters/3d-sword-carry-v1/runtime/comparison/W01-front.png"],
            "instructions": "Face and curly silver hair from portrait; burgundy vest, dark sleeves, belts and boots from body reference",
        },
        "notes": [
            "The first generated screen was selected as a style reference for the other three; this does not mean the user approved it.",
            "Illustrated values and item art are examples, not live game screenshots or final production assets.",
            "Fonts from Windows are used only for rasterized deterministic review layout/correction; no font file is redistributed.",
        ],
        "screens": records,
        "overview": {"file": "review/overview.jpg", "method": "Pillow 2×2 review layout; generated screens reduced with Lanczos"},
    }
    (ROOT / "provenance.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    correct_skill_label()
    make_overview()
    write_provenance()
    print("Prepared four screens, overview and provenance.")
