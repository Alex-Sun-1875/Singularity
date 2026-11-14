"""Read historical original sources; write side inputs and audits only here."""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True
from PIL import Image
import numpy as np
from apply_palette import apply_palette, build_masks, material_stats, MATERIALS, protection_mask

HERE = Path(__file__).resolve().parent
CONCEPTS = HERE.parents[1]
GEOMETRY = CONCEPTS / "local-klein-consistency-v1/geometry-inputs"
PILOT = CONCEPTS / "local-qwen21-turbo-pilot-v1/originals-512x768"


def describe(path):
    path = Path(path)
    with Image.open(path) as im:
        return {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size": list(im.size), "mode": im.mode}


def side_original(state, phase, out):
    metadata = json.loads((GEOMETRY / "inputs.json").read_text(encoding="utf-8"))
    entry = next(e for e in metadata["inputs"] if e["family"] == "explore"
                 and e["state"] == state and e["direction"] == "right" and e["phase"] == phase)
    native_path = Path(entry["nativeCropPath"])
    native = Image.open(native_path).convert("RGBA")
    scale = entry["uniformScaleNativeToCanvas"]
    ox, oy = entry["footAnchorLocalXY"]
    ax, ay = entry["canvasAnchorXY"]
    inverse = (1 / scale, 0, ox - ax / scale, 0, 1 / scale, oy - ay / scale)
    rgba = native.transform((512, 768), Image.Transform.AFFINE, inverse, Image.Resampling.BICUBIC)
    assert rgba.getchannel("A").tobytes() == Image.open(entry["canvasAlphaPath"]).tobytes()
    flattened = Image.new("RGB", rgba.size, tuple(entry["canvasRGBBackground"]))
    flattened.paste(rgba, (0, 0), rgba.getchannel("A"))
    assert flattened.tobytes() == Image.open(entry["inputPath"]).convert("RGB").tobytes()
    rgba.save(out)
    return rgba, {"native_original": describe(native_path), "rgba_canvas": describe(out),
                  "native_to_canvas_affine": entry["nativeToCanvasAffine"],
                  "canvas_foot_anchor_xy": entry["canvasAnchorXY"],
                  "alpha_matches_historical_canvas": True,
                  "flattened_rgb_matches_historical_canvas": True}


def main():
    side_dir = HERE / "side-inputs"
    side_dir.mkdir(exist_ok=True)
    side_run_path = side_dir / "run-right-p4-rgba.png"
    side_ref_path = side_dir / "standing-right-p0-rgba.png"
    side_run, run_record = side_original("run", 4, side_run_path)
    side_ref, ref_record = side_original("idle", 0, side_ref_path)
    masks = build_masks(side_run, "right", geometry_image=side_run)
    union = np.zeros((768, 512), bool)
    for material, mask in masks.items():
        mask.save(side_dir / f"{material}-cloth-edit-mask.png")
        union |= np.asarray(mask) > 0
    Image.fromarray((union * 255).astype(np.uint8)).save(side_dir / "cloth-edit-union-mask.png")
    # This is an exact hard inverse, not a blurred mask. White=restore from source.
    Image.fromarray((~union * 255).astype(np.uint8)).save(side_dir / "protect-everything-except-cloth-mask.png")
    protection_mask(side_run, "right").save(side_dir / "feature-protect-mask.png")
    prompt = """编辑图1的右向侧面跑步角色。图2只提供同一角色的已认可站姿服装配色，不能把图1改成站姿。准确对齐图2的低饱和暗酒红背心、略带蓝紫倾向的暗炭灰袖子，以及略暖的深灰长裤。三种衣料分别匹配对应参考，不把整个人物统一压暗；暗酒红仍保留可读的柔和褶皱，不变成接近黑色。保留图1原有材质、亮暗层次、褶皱、每一条细金刺绣、缝线与衣边。完全保留原头型、银发、脸、头部大小与位置、原跑步相位、身体前倾、四肢与两只手及指缝、剑和剑鞘、腰带包袋、袖口、靴子、身体尺度与脚部锚点。不要增加装备或改变服装形状，不改变曝光，不增加饱和度。保持512×768画布，原脚部位置不变。输出同一个完整角色、透明背景RGBA PNG，无地面、无投影、无额外角色。"""
    (side_dir / "prompt-zh.txt").write_text(prompt + "\n", encoding="utf-8")
    manifest = {
        "status": "prepared only; no model run, no upload, no production resource writes",
        "image_1_edit_target": run_record,
        "image_2_standing_reference": ref_record,
        "prompt": str(side_dir / "prompt-zh.txt"),
        "restore_mask_white_means_preserve": str(side_dir / "protect-everything-except-cloth-mask.png"),
        "notes": [
            "RGBA reconstructed only from native original with historical uniform affine; no retired-model or body-guide pixels used.",
            "After any model run, restore outside cloth union from run-right-p4-rgba.png and lock its alpha before apply_palette.",
            "Protected cloth seams are intentionally unchanged. Proxy mask and final seam continuity still need visual review.",
            "This script performs no inference, network, upload, package installation or new runtime setup.",
        ],
    }
    (side_dir / "input-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    records = {}
    for direction, source_path, reference_path in [
        ("front", PILOT / "run-front-p0-rgba.png", PILOT / "standing-front-p0-rgba.png"),
        ("back", PILOT / "run-back-p0-rgba.png", PILOT / "standing-back-p0-rgba.png"),
        ("right", side_run_path, side_ref_path),
    ]:
        out = HERE / "original-only-calibration" / direction
        out.mkdir(parents=True, exist_ok=True)
        result, report = apply_palette(source_path, reference_path, direction,
                                       geometry_image=source_path, mask_output_dir=out)
        result.save(out / "deterministic-palette-candidate.png")
        report["input_original"] = describe(source_path)
        report["standing_reference_original"] = describe(reference_path)
        report["warning"] = "Pure local deterministic sample; no Qwen-generated pixels. Numerical diagnostics, not artistic approval."
        (out / "palette-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        records[direction] = report
        for material in MATERIALS:
            row = report["materials"][material]
            print(direction, material, row["status"], "samples", row["candidate_before"]["interior_pixel_count"],
                  row["standing_reference"]["interior_pixel_count"],
                  "error", row.get("before_error_vs_standing"), "->", row.get("after_error_vs_standing"))
    (HERE / "original-reference-audit.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
