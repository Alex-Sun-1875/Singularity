"""Apply the local Qwen review to a complete exploration cycle.

Default is a dry run. --install overwrites the four existing atlases and three
action records, without original/backup copies. Existing .meta files are kept.
All generation was performed by local Qwen in the parent directory; this is
deterministic Pillow/SciPy integration, not another model invocation.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import io
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import runtime_frames as runtime

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent
REVISION = "qwen21-consistency-v2"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png_bytes(image):
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def native_patch(before, after, record, source_sheet):
    """Resample only changed regions; retain native pixels elsewhere.

    Unchanged phases bypass this entirely. Alpha is never altered by a colour
    edit. Premultiplied resampling avoids leaking hidden transparent RGB.
    """
    a, b = np.asarray(before), np.asarray(after)
    visible = (a[..., 3] > 0) | (b[..., 3] > 0)
    changed = np.any(a != b, axis=2) & visible
    s = record["scale"]
    x, y, w, h = record["rect"]
    own_original = source_sheet.crop((x, y, x + w, y + h))
    if not np.any(changed):
        return own_original, (x, y), {"changedCanvasPixels": 0, "nativePixelsChanged": 0}
    ax, ay = record["absolute_anchor"]
    # Nominal grid cells are not ownership domains: several accepted phases
    # spill across a grid line. Read only this phase's semantic source crop.
    ys, xs = np.where(b[..., 3] > 0)
    left = max(0, min(x, int(np.floor(ax + (xs.min() - 256) / s)) - 2))
    top = max(0, min(y, int(np.floor(ay + (ys.min() - 712) / s)) - 2))
    right = min(source_sheet.width, max(x + w, int(np.ceil(ax + (xs.max() + 1 - 256) / s)) + 2))
    bottom = min(source_sheet.height, max(y + h, int(np.ceil(ay + (ys.max() + 1 - 712) / s)) + 2))
    size = (right - left, bottom - top)
    original_patch = Image.new("RGBA", size)
    original_patch.paste(own_original, (x - left, y - top))
    affine = (s, 0, 256 + (left - ax) * s,
              0, s, 712 + (top - ay) * s)
    edited = after.convert("RGBa").transform(size, Image.Transform.AFFINE,
        affine, Image.Resampling.BICUBIC).convert("RGBA")
    mask = Image.fromarray((ndi.binary_dilation(changed, iterations=2) * 255).astype(np.uint8))
    mapped = np.asarray(mask.transform(size, Image.Transform.AFFINE,
        affine, Image.Resampling.BILINEAR)) > 8
    original = np.asarray(original_patch).copy()
    replacement = np.asarray(edited).copy()
    if np.array_equal(a[..., 3], b[..., 3]):
        replacement[..., 3] = original[..., 3]
    original[mapped] = replacement[mapped]
    return Image.fromarray(original), (left, top), {
        "changedCanvasPixels": int(changed.sum()),
        "nativePixelsChanged": int(np.any(original != np.asarray(original_patch), axis=2).sum()),
        "alphaChanged": not np.array_equal(a[..., 3], b[..., 3]),
        "nativeWorkingRect": [left, top, *size],
        "sourceOwnership": "only this phase's complete original semantic crop; transparent outside",
    }


def bounds(cell, threshold=16):
    ys, xs = np.where(np.asarray(cell)[..., 3] >= threshold)
    if not len(xs):
        raise ValueError("Empty character frame")
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def approved_side_cloth(image, record):
    """Transfer only the approved cloth pixels across its historical crop offset.

    The sampled right/p4 source used atlas crop (14,399), while the true current
    frame starts at (13,397). No whole-frame replacement or anchor change.
    """
    sample_before = Image.open(SOURCE / "palette/side-inputs/run-right-p4-rgba.png").convert("RGBA")
    sample_after = Image.open(SOURCE / "final/run-right.png").convert("RGBA")
    cloth = np.asarray(Image.open(SOURCE / "palette/side-inputs/cloth-edit-union-mask.png").convert("L"))
    a, b = np.asarray(sample_before), np.asarray(sample_after)
    changed = (np.any(a[..., :3] != b[..., :3], axis=2) & (a[..., 3] >= 250) & (cloth > 0))
    # Same density/local origin, different atlas crop start.
    dx, dy = record["scale"], 2 * record["scale"]
    affine = (1, 0, -dx, 0, 1, -dy)
    shifted = sample_after.convert("RGBa").transform((512, 768), Image.Transform.AFFINE,
        affine, Image.Resampling.BICUBIC).convert("RGBA")
    mask = Image.fromarray((changed * 255).astype(np.uint8)).transform((512, 768),
        Image.Transform.AFFINE, affine, Image.Resampling.BILINEAR)
    output = Image.composite(shifted, image, mask)
    output.putalpha(image.getchannel("A"))
    return output, {"approvedQwenSample": "run-right", "clothOnly": True,
        "historicalCropToCurrentCanvasTranslation": [dx, dy], "alphaUnchanged": True}


def small_reviews(processed):
    # New edited frames only. No full-size source atlases are sent for review.
    for state, count in [("walk", 4), ("run", 8)]:
        sheet = Image.new("RGB", (128 * count, 208 * 4), "#252628")
        draw = ImageDraw.Draw(sheet)
        for di, direction in enumerate(runtime.DIRECTIONS):
            for phase in range(count):
                frame = processed[(state, direction, phase)].resize((128, 192), Image.Resampling.LANCZOS)
                sheet.paste(frame, (phase * 128, di * 208 + 16), frame)
                draw.text((phase * 128 + 4, di * 208 + 2), f"{direction} {phase}", fill="white")
        sheet.save(HERE / f"{state}-cycle-review.jpg", quality=88)


def run(install=False):
    from body_batch import apply_body
    from sword_batch import apply_sword
    from palette_batch import apply_colors

    original_manifest_bytes = runtime.MANIFEST.read_bytes()
    original = runtime.read_manifest()
    if original.get("localQwenInstall", {}).get("revision") == REVISION:
        raise RuntimeError("This revision is already installed; refusing to apply geometry twice.")
    manifest = copy.deepcopy(original)
    names = sorted({runtime.frame_record(original, s, d, p)["image"]
        for s in runtime.KEYS for d in runtime.DIRECTIONS
        for p in range(original["actions"][runtime.KEYS[s]]["frames"])})
    original_bytes = {n: (runtime.ACTOR / n).read_bytes() for n in names}
    meta_hashes = {str(p): sha(p.read_bytes()) for p in
        [runtime.MANIFEST.with_suffix(".json.meta")] + [Path(str(runtime.ACTOR / n) + ".meta") for n in names]
        if p.exists()}
    images = {n: Image.open(io.BytesIO(b)).convert("RGBA") for n, b in original_bytes.items()}
    new_images = {n: im.copy() for n, im in images.items()}
    refs = {d: runtime.canvas(original, "idle", d, 0, images)[0] for d in runtime.DIRECTIONS}
    processed, reports, geometry, patches = {}, [], {}, []

    for state in runtime.KEYS:
        for direction in runtime.DIRECTIONS:
            for phase in range(original["actions"][runtime.KEYS[state]]["frames"]):
                before, record = runtime.canvas(original, state, direction, phase, images)
                key = (state, direction, phase)
                approved = {("idle", "up", 0): "standing-back",
                            ("run", "down", 0): "run-front",
                            ("run", "up", 0): "run-back"}.get(key)
                if approved:
                    after = Image.open(SOURCE / "final" / (approved + ".png")).convert("RGBA")
                    detail = {"approvedQwenSample": approved}
                else:
                    after, body = apply_body(before, record)
                    after, sword = apply_sword(after, record)
                    after, colors = apply_colors(after, record, refs[direction])
                    detail = {"body": body, "sword": sword, "colors": colors}
                    if key == ("run", "right", 4):
                        after, detail["approvedSideCloth"] = approved_side_cloth(after, record)
                if after.size != (512, 768) or after.mode != "RGBA":
                    raise ValueError(f"Unexpected processed canvas: {key}")
                processed[key] = after
                edited, (px, py), packing = native_patch(before, after, record, images[record["image"]])
                patches.append((record["image"], (px, py), edited, key))
                b = bounds(edited)
                # Keep two native AA pixels around the alpha16 silhouette.
                crop = [max(0, b[0] - 2), max(0, b[1] - 2),
                        min(edited.width, b[2] + 2), min(edited.height, b[3] + 2)]
                rect = [px + crop[0], py + crop[1], crop[2] - crop[0], crop[3] - crop[1]]
                origin = [record["absolute_anchor"][0] - rect[0], record["absolute_anchor"][1] - rect[1]]
                geometry[key] = dict(record=record, rect=rect, origin=origin,
                    bounds=[b[0]-crop[0], b[1]-crop[1], b[2]-crop[0], b[3]-crop[1]])
                reports.append(dict(state=state, direction=direction, phase=phase,
                    processing=detail, packing=packing, rect=rect, origin=origin,
                    absoluteAnchor=record["absolute_anchor"]))

    # Clear the old phase-owned domains first, then copy each independent new
    # patch by binary support. Do not square AA alpha by using it as paste weight.
    owners = {n: np.zeros((im.height, im.width), np.uint16) for n, im in images.items()}
    for g in geometry.values():
        x, y, w, h = g["record"]["rect"]
        new_images[g["record"]["image"]].paste((0, 0, 0, 0), (x, y, x+w, y+h))
    for number, (name, (px, py), patch, key) in enumerate(patches, 1):
        alpha = np.asarray(patch)[..., 3]
        region = owners[name][py:py+patch.height, px:px+patch.width]
        if np.any((alpha >= 16) & (region != 0)):
            raise ValueError(f"Overlapping phase alpha16 support: {key}")
        region[alpha >= 16] = number
        support = Image.fromarray(np.uint8(alpha > 0) * 255)
        new_images[name].paste(patch, (px, py), support)
    for number, (name, _, patch, key) in enumerate(patches, 1):
        x, y, w, h = geometry[key]["rect"]
        labels = owners[name][y:y+h, x:x+w]
        if np.any((labels != 0) & (labels != number)):
            raise ValueError(f"Frame crop includes another phase's alpha16: {key}")

    encoded = {n: png_bytes(im) for n, im in new_images.items()}
    new_hashes = {n: sha(b) for n, b in encoded.items()}
    for state, action_key in runtime.KEYS.items():
        action = manifest["actions"][action_key]
        count = action["frames"]
        action_names = list(dict.fromkeys(action.get("frameImages", [action["image"]])))
        by_image = {}
        origins = {d: [] for d in runtime.DIRECTIONS}
        alpha = {d: [] for d in runtime.DIRECTIONS}
        for direction in runtime.DIRECTIONS:
            for phase in range(count):
                g = geometry[(state, direction, phase)]
                record = g["record"]
                name = record["image"].removesuffix(".png")
                by_image.setdefault(name, [None] * (4 if state == "idle" else 16))[record["index"]] = g["rect"]
                origins[direction].append(g["origin"])
                alpha[direction].append(g["bounds"])
        if any(any(v is None for v in rects) for rects in by_image.values()):
            raise ValueError("Incomplete animation page")
        action["perFrameRects"] = by_image[action["image"].removesuffix(".png")]
        if len(action_names) > 1:
            action["frameRectsByImage"] = by_image
        action["perFrameOrigins"] = origins if state == "run" else [
            origins[d][p] for d in runtime.DIRECTIONS for p in range(count)]
        action["alphaBounds"] = [alpha[d][p] for d in runtime.DIRECTIONS for p in range(min(count, 4))]
        if state == "run":
            action["perPhaseAlphaBounds"] = alpha
        action["originMethod"] = "Complete alpha16 crops; each pre-edit native support/flight anchor and UPP retained; local Qwen v2 bounded phase adaptation."
        action["sourcePNGs"] = [str(runtime.ACTOR / n) for n in action_names]
        action["sourcePNGSHA256s"] = [new_hashes[n] for n in action_names]
        for stale in ("rawOutputPNGs", "rawOutputPNGSHA256s"):
            action.pop(stale, None)
        action["localQwenProcessing"] = {
            "revision": REVISION,
            "record": str(HERE / "installation-report.json"),
            "method": "Reviewed local-Qwen masked samples plus per-phase local pixel geometry/palette adaptation; not individual model generation of every phase.",
        }
        action["identityReferenceScope"] = "Current standing head remains canonical; local Qwen v2 integrates bounded clothing, leg-projection and back-scabbard edits while retaining original pose phases, hands, boot anchors and timing."
    # Only the three exploration action records change. Held and other actions
    # retain their original values and texture bytes.
    for key, action in original["actions"].items():
        if key not in runtime.KEYS.values() and action != manifest["actions"][key]:
            raise ValueError(f"Unrelated action changed: {key}")
    manifest["localQwenInstall"] = {"revision": REVISION, "scope": list(runtime.KEYS.values()),
        "frames": len(reports), "model": "local Qwen-Image-2.1-Turbo INT8",
        "report": str(HERE / "installation-report.json"), "extraOriginalBackups": False}
    manifest["revision"] = "concept-image-2d-qwen21-consistency-v2"
    idle_hash = new_hashes[original["actions"][runtime.KEYS["idle"]]["image"]]
    for key in runtime.KEYS.values():
        if manifest["actions"][key].get("identityReference", "").endswith("W01-explore-idle.png"):
            manifest["actions"][key]["identityReferenceSHA256"] = idle_hash
        if manifest["actions"][key].get("sourceDesign", "").endswith("W01-explore-idle.png"):
            manifest["actions"][key]["sourceDesignSHA256"] = idle_hash
    payload = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    report = {"status": "installed" if install else "dry-run", "revision": REVISION,
        "extraOriginalBackups": False, "modelCallsInThisInstall": 0,
        "manifestBeforeSHA256": sha(original_manifest_bytes), "manifestAfterSHA256": sha(payload),
        "atlases": [{"path": str(runtime.ACTOR / n), "size": list(images[n].size),
            "beforeSHA256": sha(original_bytes[n]), "afterSHA256": new_hashes[n]} for n in names],
        "frames": reports, "unrelatedActionsUnchanged": True,
        "metaSHA256s": meta_hashes,
        "invariants": {"supportAndFlightAnchorsRetained": True,
            "timingAndUPPRetained": True, "atlasDimensionsRetained": True,
            "heldAndOtherActionRecordsRetained": True,
            "semanticFrameOwnershipAndNoNeighborAlpha16InCrops": True}}
    small_reviews(processed)
    if install:
        # All transformations/checks finish first. Originals exist only in memory;
        # only new bytes are staged, and manifest is replaced last.
        for n in names:
            if sha((runtime.ACTOR / n).read_bytes()) != sha(original_bytes[n]):
                raise RuntimeError("Runtime atlas changed during preparation")
        if runtime.MANIFEST.read_bytes() != original_manifest_bytes:
            raise RuntimeError("Runtime manifest changed during preparation")
        entries = [(runtime.ACTOR / n, encoded[n]) for n in names] + [(runtime.MANIFEST, payload)]
        for path, data in entries:
            stage = path.with_name(path.name + ".qwen-stage")
            stage.write_bytes(data)
        for path, data in entries:
            os.replace(path.with_name(path.name + ".qwen-stage"), path)
            if path.read_bytes() != data:
                raise RuntimeError(f"Written byte verification failed: {path}")
        for filename, value in meta_hashes.items():
            if sha(Path(filename).read_bytes()) != value:
                raise RuntimeError(f"Unexpected meta mutation: {filename}")
    (HERE / ("installation-report.json" if install else "dry-run-report.json")).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "frames": len(reports),
        "atlases": len(names), "extraOriginalBackups": False}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true")
    run(parser.parse_args().install)
