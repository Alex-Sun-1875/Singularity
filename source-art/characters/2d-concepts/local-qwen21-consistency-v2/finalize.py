"""Combine native local Qwen retouches with protected geometry and cloth palette.

Raw images remain untouched. Transparent model RGB must never contaminate the
opaque source silhouette; generated RGB is admitted only with foreground alpha.
"""
from pathlib import Path
import importlib.util
import json
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def compose(guide_path, raw_path, mask_path):
    guide = np.asarray(Image.open(guide_path).convert("RGBA"))
    raw = np.asarray(Image.open(raw_path).convert("RGBA"))
    mask = np.asarray(Image.open(mask_path).convert("L"), dtype=float) / 255
    confidence = np.clip((raw[..., 3].astype(float) - 230) / 20, 0, 1)
    confidence *= np.clip((guide[..., 3].astype(float) - 230) / 20, 0, 1)
    weight = mask * confidence
    out = guide.copy()
    out[..., :3] = np.rint(guide[..., :3] * (1 - weight[..., None]) + raw[..., :3] * weight[..., None]).clip(0, 255).astype("uint8")
    assert np.array_equal(out[..., 3], guide[..., 3])
    assert np.array_equal(out[mask == 0], guide[mask == 0])
    return Image.fromarray(out), {"qwen_rgb_blend_pixels": int((weight > 0).sum()),
                                 "masked_pixels_with_reduced_alpha_confidence": int(((mask > 0) & (confidence < 1)).sum()),
                                 "guide_alpha_preserved_before_neck_repair": True}


def main():
    palette = module("palette_constraints", ROOT / "palette/apply_palette.py")
    neck_path = ROOT / "body/head-neck-repair.py"
    neck = module("neck_repair", neck_path) if neck_path.exists() else None
    plans = [
        ("run-front", "body/front/guide-rgba.png", "results/run-front-refined/raw-model.png", "body/front/edit-mask.png", "front", "body/front/reference-standing-rgba.png", "palette/final-feature-protection/front-feature-protect-mask.png"),
        ("run-back", "sword/back-run/merged-guide-rgba.png", "results/run-back/raw-model.png", "sword/back-run/merged-edit-mask.png", "back", "body/back/reference-standing-rgba.png", "palette/final-feature-protection/back-feature-protect-mask.png"),
        ("standing-back", "sword/guide-rgba.png", "results/sword-back/raw-model.png", "sword/edit-mask.png", None, None, None),
        ("run-right", "palette/side-inputs/run-right-p4-rgba.png", "results/clothing-side/raw-model.png", "palette/side-inputs/cloth-edit-union-mask.png", "right", "palette/side-inputs/standing-right-p0-rgba.png", "palette/side-inputs/protect-everything-except-cloth-mask.png"),
    ]
    output_dir = ROOT / "final"
    output_dir.mkdir(exist_ok=True)
    reports = {}
    for name, guide, raw, mask, direction, reference, protect in plans:
        candidate, report = compose(ROOT / guide, ROOT / raw, ROOT / mask)
        candidate.save(output_dir / (name + "-before-palette.png"))
        if direction:
            candidate, palette_report = palette.apply_palette(candidate, ROOT / reference, direction,
                geometry_image=ROOT / guide, protect_mask=ROOT / protect,
                mask_output_dir=output_dir / (name + "-palette-masks"))
            (output_dir / (name + "-palette.json")).write_text(json.dumps(palette_report, ensure_ascii=False, indent=2), encoding="utf-8")
        if neck is not None and direction in ("front", "back"):
            candidate, neck_report = neck.apply_neck_repair(candidate, direction)
            report["neck_repair"] = neck_report
        candidate.save(output_dir / (name + ".png"))
        report.update({"final": str(output_dir / (name + ".png")), "raw": raw,
                       "method": "Actual masked local Qwen inference, protected source geometry, alpha-aware RGB composite and separate deterministic palette calibration",
                       "raw_model_modified": False, "production_modified": False})
        reports[name] = report
    (ROOT / "finalization-report.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({name: {k: value[k] for k in ["qwen_rgb_blend_pixels", "masked_pixels_with_reduced_alpha_confidence"]} for name, value in reports.items()}))


if __name__ == "__main__":
    main()
