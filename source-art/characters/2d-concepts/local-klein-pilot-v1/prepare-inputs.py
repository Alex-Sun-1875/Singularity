"""Prepare local-only RGB pilot inputs; read production assets without changing them."""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import PIL
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MANIFEST = ROOT / "src/cocos/assets/resources/flat2d/characters/raphael/manifest.json"
BACKGROUND = (224, 224, 224)
CANVAS = (512, 768)
OUTPUT_WORLD_UNITS_PER_PIXEL = 0.0024
FOOT_ANCHOR = (256, 720)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def alpha_info(image: Image.Image) -> dict:
    alpha = image.getchannel("A")
    counts = alpha.histogram()
    return {
        "extrema": list(alpha.getextrema()),
        "nonzero_bbox_xyxy": list(alpha.getbbox()) if alpha.getbbox() else None,
        "zero_pixel_count": counts[0],
        "partial_pixel_count": sum(counts[1:255]),
        "opaque_pixel_count": counts[255],
        "threshold_or_matte_removal": "none",
    }


def prepare(name: str, source: Path, expected_sha: str, crop_xywh: list[int],
            canvas: tuple[int, int], scale: float,
            anchor: list[float] | None = None, **metadata) -> dict:
    before = sha256(source)
    if before != expected_sha:
        raise ValueError(f"Source changed; review selection before running: {source}")
    with Image.open(source) as opened:
        source_mode, source_size = opened.mode, list(opened.size)
        rgba = opened.convert("RGBA")
    x, y, width, height = crop_xywh
    if min(x, y) < 0 or width <= 0 or height <= 0 or x + width > rgba.width or y + height > rgba.height:
        raise ValueError(f"Invalid crop: {crop_xywh}")
    cropped = rgba.crop((x, y, x + width, y + height))
    resized_size = (round(width * scale), round(height * scale))
    resized = cropped.resize(resized_size, Image.Resampling.LANCZOS)
    # Use the rounded dimensions in placement and report both actual axis scales.
    actual_scale = (resized.width / width, resized.height / height)
    if anchor is None:
        paste = ((canvas[0] - resized.width) // 2, (canvas[1] - resized.height) // 2)
    else:
        paste = (round(FOOT_ANCHOR[0] - anchor[0] * actual_scale[0]),
                 round(FOOT_ANCHOR[1] - anchor[1] * actual_scale[1]))
    if min(paste) < 0 or paste[0] + resized.width > canvas[0] or paste[1] + resized.height > canvas[1]:
        raise ValueError(f"Prepared crop would clip: {name}")
    result = Image.new("RGB", canvas, BACKGROUND)
    result.paste(resized.convert("RGB"), paste, resized.getchannel("A"))
    output = HERE / name
    result.save(output)
    if sha256(source) != before:
        raise RuntimeError(f"Source was modified: {source}")
    return {
        "path": relative(output), "absolute_path": str(output), "sha256": sha256(output),
        "source_path": relative(source), "source_absolute_path": str(source),
        "source_sha256": before, "source_size": source_size, "source_mode": source_mode,
        "crop_xywh": crop_xywh, "crop_alpha": alpha_info(cropped),
        "output_mode": "RGB", "canvas_size": list(canvas), "background_rgb": list(BACKGROUND),
        "requested_uniform_scale": scale, "actual_scale_xy": list(actual_scale),
        "resized_crop_size": list(resized_size), "paste_xy": list(paste),
        "resampling": "Pillow LANCZOS; no sharpening or color adjustment",
        "alpha_handling": "Keep original crop alpha, resize RGBA, composite once onto light gray; output has no alpha",
        **metadata,
    }


def main() -> None:
    manifest_sha = sha256(MANIFEST)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    standing = manifest["actions"]["explore_idle_W01"]
    running = manifest["actions"]["explore_run_W01"]
    # standing-head-v2: right profile = index 1 in the 2x2 standing atlas.
    standing_source = Path(standing["sourcePNGs"][0])
    standing_sha = standing["sourcePNGSHA256s"][0]
    standing_crop = standing["perFrameRects"][1]
    standing_input = prepare(
        "standing-right-input.png", standing_source, standing_sha, standing_crop,
        CANVAS, standing["worldUnitsPerPixel"] / OUTPUT_WORLD_UNITS_PER_PIXEL,
        standing["perFrameOrigins"][1], role="standing full-body head-size authority / optional control input",
        action="explore_idle_W01", direction="right", phase_index=0, atlas_index=1,
        source_world_units_per_pixel=standing["worldUnitsPerPixel"],
        output_world_units_per_pixel=OUTPUT_WORLD_UNITS_PER_PIXEL,
        canvas_foot_anchor_xy=list(FOOT_ANCHOR),
    )
    running_source = Path(running["sourcePNGs"][0])
    running_sha = running["sourcePNGSHA256s"][0]
    frame_key = running["image"].removesuffix(".png")
    running_crop = running["frameRectsByImage"][frame_key][4]
    running_input = prepare(
        "running-right-input.png", running_source, running_sha, running_crop,
        CANVAS, running["worldUnitsPerPixel"] / OUTPUT_WORLD_UNITS_PER_PIXEL,
        running["perFrameOrigins"]["right"][0], role="primary head-only edit input; current installed run",
        action="explore_run_W01", direction="right", phase_index=0, atlas_index=4,
        source_world_units_per_pixel=running["worldUnitsPerPixel"],
        output_world_units_per_pixel=OUTPUT_WORLD_UNITS_PER_PIXEL,
        canvas_foot_anchor_xy=list(FOOT_ANCHOR),
    )
    head_reference = prepare(
        "standing-head-right-reference.png", standing_source, standing_sha,
        [1115, 5, 78, 84], (384, 384), 4.0,
        role="optional same-standing right-profile head detail; magnified, never a size authority",
        selection_basis="Top of the authoritative right standing frame; includes complete crown, face and upper collar; excludes most back sword pommel",
    )
    design = ROOT / "source-art/characters/2d-concepts/identity-reference-v1/references/original-design.png"
    identity = design.parents[1] / "head-identity-master.png"
    ancestors = []
    for path, role in [(design, "original approved design board"), (identity, "earlier four-direction high-resolution identity master")]:
        with Image.open(path) as im:
            ancestors.append({"path": relative(path), "absolute_path": str(path), "sha256": sha256(path),
                              "size": list(im.size), "mode": im.mode, "role": role})
    document = {
        "purpose": "Local FLUX.2 klein 4B distilled pilot, at most two single-frame cases",
        "preparation": {"python": platform.python_version(), "pillow": PIL.__version__,
                        "network_used": False, "image_uploads": False,
                        "manifest_path": relative(MANIFEST), "manifest_sha256": manifest_sha,
                        "production_assets_modified": False},
        "files": [standing_input, running_input, head_reference],
        "design_ancestry": ancestors,
        "cases": [
            {"id": "run-right-head-alignment", "priority": 1,
             "images_in_order": [running_input["path"], standing_input["path"]],
             "optional_third_image": head_reference["path"], "prompt_file": relative(HERE / "edit-prompt.txt"),
             "expected_output": "one RGB right-running figure on unchanged light gray; 512x768 at 0.375MP, 416x624 for the 0.25MP smoke run",
             "review": ["same running pose/leg lengths/hand positions/costume/equipment",
                        "whole head volume follows standing body scale",
                        "rounded natural chin; neither pointed V face nor broad swollen face"]},
            {"id": "standing-right-control", "priority": 2,
             "images_in_order": [standing_input["path"], head_reference["path"]],
             "prompt": "Image 1 is the complete approved character standing in right profile. Image 2 is only a magnified detail of the SAME standing head. Preserve image 1's whole figure, standing pose, head size, face shape, short silver swept curls, burgundy embroidered vest, navy sleeves, long trousers, boots, diagonal sheathed sword, framing and light gray background. Return one complete 512x768 image. Do not enlarge the head to the close-up size or sharpen the chin. Preserve the original realistic painted style.",
             "review": ["basic local image conditioning works", "identity and pose stay stable"]},
        ],
        "limitations": [
            "Inputs are deterministic pilot crops/resamples, not production sprite replacements.",
            "Selection follows existing manifest/provenance/prompt geometry; no image-viewing or uploading tool was used.",
            "The original design and identity master are recorded for traceability; current installed standing head takes precedence for head size/shape.",
            "No model output or visual quality claim is made by preparation. Assess outputs locally before production integration.",
        ],
    }
    (HERE / "inputs.json").write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for item in document["files"]:
        print(f'{Path(item["path"]).name}: {item["canvas_size"]} {item["output_mode"]} {item["sha256"]}')
    print(f"manifest_sha256: {manifest_sha}")


if __name__ == "__main__":
    main()
