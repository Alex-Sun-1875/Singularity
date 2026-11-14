"""Prepare local-only original inputs; does not invoke a model or edit source assets."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "local-klein-consistency-v1"
GEOMETRY = PREVIOUS / "geometry-inputs"
SOURCE = json.loads((GEOMETRY / "inputs.json").read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def describe(path):
    with Image.open(path) as image:
        return {"path": str(path.resolve()), "sha256": sha(path),
                "size": list(image.size), "mode": image.mode}


def same_pixels(a, b):
    return a.mode == b.mode and a.size == b.size and a.tobytes() == b.tobytes()


selection = {
    "standing-front": ("idle", "down"),
    "standing-back": ("idle", "up"),
    "run-front": ("run", "down"),
    "run-back": ("run", "up"),
}
originals = {}
snapshot = {}
for label, (state, direction) in selection.items():
    entry = next(e for e in SOURCE["inputs"] if e["family"] == "explore"
                 and e["state"] == state and e["direction"] == direction
                 and e["phase"] == 0)
    source = SOURCE["sources"][entry["image"]]
    source_path = Path(source["sourceArtPath"])
    assert sha(source_path) == source["sourceArtSHA256"], source_path
    assert sha(source["runtimePath"]) == source["runtimeSHA256"]
    snapshot[str(source_path)] = sha(source_path)
    snapshot[source["runtimePath"]] = sha(source["runtimePath"])
    native_source = Path(entry["nativeCropPath"])
    snapshot[str(native_source)] = sha(native_source)
    x, y, w, h = entry["cropRectAbsoluteXYWH"]
    native = Image.open(source_path).convert("RGBA").crop((x, y, x + w, y + h))
    assert same_pixels(native, Image.open(native_source)), "native crop differs from installed source"
    native_dir = HERE / "originals-native"
    native_dir.mkdir(exist_ok=True)
    native_copy = native_dir / f"{label}-p0.png"
    shutil.copy2(native_source, native_copy)
    assert sha(native_copy) == sha(native_source)

    # These historical 512x768 files are RGB plus separate alpha, not RGBA.
    # Reconstruct their unedited RGBA canvas directly from native original pixels.
    # Retain the exact original action scale and foot anchor; never fit the bbox.
    scale = entry["uniformScaleNativeToCanvas"]
    ox, oy = entry["footAnchorLocalXY"]
    ax, ay = entry["canvasAnchorXY"]
    inverse = (1 / scale, 0, ox - ax / scale, 0, 1 / scale, oy - ay / scale)
    rgba = native.transform((512, 768), Image.Transform.AFFINE, inverse, Image.Resampling.BICUBIC)
    assert same_pixels(rgba.getchannel("A"), Image.open(entry["canvasAlphaPath"]))
    rendered = Image.new("RGB", rgba.size, tuple(entry["canvasRGBBackground"]))
    rendered.paste(rgba, (0, 0), rgba.getchannel("A"))
    original_rgb = Image.open(entry["inputPath"])
    assert same_pixels(rendered, original_rgb), "reconstructed original does not match historical before canvas"
    canvas_dir = HERE / "originals-512x768"
    canvas_dir.mkdir(exist_ok=True)
    rgba_path = canvas_dir / f"{label}-p0-rgba.png"
    rgb_path = canvas_dir / f"{label}-p0-model-rgb.png"
    rgba.save(rgba_path)
    shutil.copy2(entry["inputPath"], rgb_path)
    assert sha(rgb_path) == entry["inputSHA256"]
    originals[label] = {
        "label": label,
        "source_original": describe(source_path),
        "source_crop_xywh": [x, y, w, h],
        "runtime_original": describe(Path(source["runtimePath"])),
        "native_original": describe(native_source),
        "native_byte_copy": describe(native_copy),
        "original_rgb_canvas": describe(Path(entry["inputPath"])),
        "rgba_canvas": describe(rgba_path),
        "model_rgb_byte_copy": describe(rgb_path),
        "rgba_canvas_provenance": "Reconstructed from unedited native RGBA with the historical action-wide affine; no model, guide, body warp or candidate pixels. Not a byte copy of a pre-existing 512x768 RGBA file.",
        "rgba_raw_pixel_sha256": hashlib.sha256(rgba.tobytes()).hexdigest(),
        "native_to_canvas_affine": entry["nativeToCanvasAffine"],
        "canvas_foot_anchor_xy": entry["canvasAnchorXY"],
        "pixels_per_world_unit": entry["pixelsPerWorldUnit"],
        "alpha_matches_original_canvas": True,
        "flattened_rgb_pixels_match_original_canvas": True,
    }

front_prompt = """编辑图1的正面跑步角色，图2仅作为同一角色的已认可站姿、服装和裤色参考，不改成站姿。将图1上衣校准为图2的暗酒红色，袖子为暗炭灰，长裤的色相和明暗材质与图2一致；保留原有金色刺绣、褶皱和阴影。保留图1头型、银发、脸部朝向、头部大小及位置，保留原跑步相位、身体前倾、手臂和弯腿姿势、两只手指与手腕、剑及剑鞘和固定点、腰带、包袋、靴子。保持512×768画布、原人物尺度和原脚部位置；不得整体放大或移动人物。仅一个完整角色，保持透明背景，输出带Alpha通道的RGBA PNG，不添加背景/地面/投影。"""
front_proportions = """编辑图1正面跑步角色，图2仅为同一角色的站姿身份、服装裤色和成年修长身材参考。将图1腿与躯干比例调整为图2的高挑修长比例，提高腰线并适度延长大腿与小腿，避免矮壮或短腿；保持图1原跑步相位、身体前倾、交替手臂和弯曲后腿。头型、银发、脸部朝向、头部大小和位置、手指与腕部、双脚位置、剑与剑鞘细节及固定点、金色刺绣、腰带包袋和靴子全部保留。上衣、袖子与裤色对齐图2。保持512×768画布和原脚部锚点，不通过整体拉伸或放大实现腿长。一个完整角色，保持透明背景，输出带Alpha通道的RGBA PNG，不添加背景/地面/投影。"""
sword_prompt = """只编辑图1背面站姿角色的棕色背负剑鞘中段，将剑鞘沿当前右上至左下的轴线延长约35%，末端从原位置约(198,380)移至(167,445)。保留剑柄、金色柄头、护手、肩部固定点、鞘宽、原金属鞘帽的形状、角度和细节；增加中段长度，不把末端拉扁或重画。保留原头型、银发、暗酒红服装、裤色、身材、手指与腕部、腰带包袋、双脚位置及站姿；剑鞘经过手部时保持原手在前的遮挡及指间空隙。保持512×768画布、原人物尺度和脚部锚点，一个完整背面角色，保持透明背景，输出带Alpha通道的RGBA PNG，不添加背景/地面/投影。"""
back_run_prompt = """编辑图1背面跑步角色，图2只提供同一角色的背面站姿、头型、服装裤色和成年修长身材参考。适度提高腰线，协调大腿小腿与躯干比例，保持原跑步相位、前倾、交替手臂和弯曲后腿。保留图1头型、银发、头部大小和位置、手指与腕部、双脚位置、剑柄与剑鞘细节和固定点、腰带包袋、靴子；上衣、袖子和长裤颜色对齐图2。保持512×768画布、原人物尺度和脚部锚点，不能整体放大人物。一个完整背面跑步角色，保持透明背景，输出带Alpha通道的RGBA PNG，不添加背景/地面/投影。"""

front_dir = HERE / "front-run"
back_dir = HERE / "back-sword"
front_dir.mkdir(exist_ok=True)
back_dir.mkdir(exist_ok=True)
(front_dir / "prompt.txt").write_text(front_prompt + "\n", encoding="utf-8")
(front_dir / "prompt-proportions.txt").write_text(front_proportions + "\n", encoding="utf-8")
(back_dir / "prompt.txt").write_text(sword_prompt + "\n", encoding="utf-8")
(back_dir / "prompt-run-back-optional.txt").write_text(back_run_prompt + "\n", encoding="utf-8")
(HERE / "prompt.txt").write_text(
    "先试 front-run/prompt.txt：图1=run-front，图2=standing-front，仅衣色/裤色。\n"
    "默认使用对应*-rgba.png；ComfyUI的LoadImage之后用JoinImageWithAlpha保留原alpha，原生透明编辑输入。\n"
    "通过后才另开一张原始run-front，试 front-run/prompt-proportions.txt；不用上一张模型输出串联。\n"
    "第二组背剑只用standing-back原件 + back-sword/prompt.txt，不需第二张角色参考。\n"
    "备用背跑：图1=run-back，图2=standing-back，使用back-sword/prompt-run-back-optional.txt。\n"
    "图像绑定与SHA256以input-manifest.json为准。先单帧，局部保护合成并验收后再考虑批量。\n",
    encoding="utf-8")


def binding(label, role, index=None):
    o = originals[label]
    return {"image_index": index, "role": role, "original_label": label,
            "model_input": o["rgba_canvas"], "preserved_rgba": o["rgba_canvas"],
            "optional_rgb_review_or_compatibility_copy": o["model_rgb_byte_copy"],
            "comfyui_alpha_loading": "Use LoadImage followed by JoinImageWithAlpha to reconstruct the RGBA tensor from the preserved original alpha; verify/invert the LoadImage MASK convention as needed. Do not send only the IMAGE RGB tensor or substitute the grey-matte copy for the alpha trial.",
            "source_original": o["source_original"], "source_crop_xywh": o["source_crop_xywh"]}


manifest = {
    "status": "inputs and draft prompts only; model not invoked; not approved or installed",
    "model_family_requested": "Qwen2.1Turbo (runtime/model selection remains the parent task)",
    "scope": "All new files stay inside this pilot directory. Production and previous trials are read-only.",
    "preferred_model_input_policy": "RGBA originals for native transparent editing. In ComfyUI preserve the original alpha using JoinImageWithAlpha after LoadImage; RGB grey-matte copies remain only for provenance verification or an explicit compatibility comparison.",
    "canvas_policy": SOURCE["canvasPolicy"],
    "originals": originals,
    "groups": [
        {"name": "front-run", "goal": "Standing-reference costume/trouser palette first, then a separate original-input leg proportion trial.",
         "images": [binding("run-front", "edit_target_original_running_pose", 1),
                    binding("standing-front", "approved_identity_costume_trouser_and_body_proportion_reference_only", 2)],
         "first_prompt": str((front_dir / "prompt.txt").resolve()),
         "separate_geometry_prompt": str((front_dir / "prompt-proportions.txt").resolve()),
         "protected_regions_from_previous_audit_xyxy": {"hands_context": [[190,266,276,351],[335,360,383,428]],
                                                       "hands_cores": [[202,290,263,339],[343,368,375,420]]}},
        {"name": "back-sword", "goal": "Extend only original rear standing scabbard; preserve original tip and hands. Rear runner retained as optional subsequent trial.",
         "images": [binding("standing-back", "edit_target_original_rear_standing_sword", 1)],
         "first_prompt": str((back_dir / "prompt.txt").resolve()),
         "protected_regions_from_previous_audit_xyxy": {"hands_context": [[146,368,187,437],[323,368,364,437]],
                                                       "hands_cores": [[152,374,181,431],[329,374,358,431]]},
         "sword_geometry": {"upper_attachment_xy": [283,192], "original_actual_tip_xy": [198.016,380.206],
                            "requested_tip_xy": [167.016,445.206], "original_tip_translation_xy": [-31,65],
                            "tip_detail_source": "original standing-back pixels, not revision candidate"},
         "optional_back_run_images": [binding("run-back", "optional_edit_target_original_rear_runner", 1),
                                      binding("standing-back", "optional_approved_rear_identity_costume_and_proportions_reference_only", 2)],
         "optional_back_run_prompt": str((back_dir / "prompt-run-back-optional.txt").resolve())},
    ],
    "recommended_single_frame_order": ["front-run colour-only from original", "front-run proportions from original, only if colour trial is useful", "back-sword from original", "optional run-back from original"],
    "postprocess_contract": [
        "A prompt does not freeze pixels. Keep model output as a candidate and composite only a reviewed local edit mask over the preserved RGBA original.",
        "Restore original head, hands/wrists, sword details outside the intended edit, feet and transparent edges after all geometry and colour work; audit changed pixels outside the final edit mask.",
        "For sword extension keep the original tip with an integer translation and preserve foreground-hand occlusion/finger gaps; do not paste an opaque grey hand rectangle over the scabbard.",
        "Check head identity, hairstyle, leg proportions, forward lean, costume/trouser colour, hand anatomy, sword cap, attachment, feet anchors and alpha before acceptance.",
        "No candidate may replace production, source art or runtime manifest before explicit visual acceptance.",
    ],
    "cautions": [
        "Historical 512x768 inputs are RGB and separate alpha; preserved true RGBA canvases are reconstructed from the original native RGBA with exactly the historical affine. Native source PNGs are also byte-copied.",
        "Optional model RGB copies are exact byte copies of original unwarped geometry-inputs RGB files on (228,228,228). The first trial should instead use RGBA + JoinImageWithAlpha to evaluate native transparent editing.",
        "Existing before is unwarped; guides, raw-model, candidate, constrained-candidate and candidate-v2 are deliberately excluded from all input pixel sources.",
        "Audit rectangles are guidance from the previous trial, not accepted new edit masks. No artistic acceptance is claimed by the metadata checks.",
    ],
    "source_records_used": [str((PREVIOUS / p).resolve()) for p in ("cases.json", "prepare-cases.py", "geometry-inputs/inputs.json", "revision-v2/README.md", "revision-v2/revision-report.json", "revision-v2/hand-audit/hand-regions.json")],
    "verification": {"native_byte_copies_equal": True, "source_crop_pixels_equal_native": True,
                     "rgba_alpha_matches_historical_alpha": True, "rgba_flatten_matches_historical_unedited_RGB": True,
                     "original_sources_unchanged": all(sha(path) == value for path, value in snapshot.items()),
                     "model_inference_called": False, "network_used": False, "production_modified": False},
}
assert manifest["verification"]["original_sources_unchanged"]
(HERE / "input-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Small local overview only: never emit/upload from this preparation script.
thumb = (224,336)
preview = Image.new("RGB", (thumb[0] * 4, thumb[1] + 42), (244,244,244))
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
draw = ImageDraw.Draw(preview)
for col, label in enumerate(("standing-front", "run-front", "standing-back", "run-back")):
    tile = Image.open(originals[label]["model_rgb_byte_copy"]["path"]).resize(thumb, Image.Resampling.LANCZOS)
    preview.paste(tile, (col * thumb[0],42))
    draw.text((col * thumb[0] + 6,8), label + " ORIGINAL", font=font, fill=(32,32,32))
    anchor_y = 42 + round(712 * thumb[1] / 768)
    draw.line((col * thumb[0],anchor_y,(col+1)*thumb[0]-1,anchor_y), fill=(180,180,180))
preview.save(HERE / "original-input-preview.jpg", quality=82, optimize=True)
print(json.dumps({"manifest": str(HERE / "input-manifest.json"), "preview": str(HERE / "original-input-preview.jpg"),
                  "preview_size": list(preview.size), "original_count": len(originals), "verification": manifest["verification"]}, indent=2))
