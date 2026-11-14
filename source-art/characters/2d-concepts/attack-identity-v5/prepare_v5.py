"""Inventory the current sprites and adapt existing local pose measurements.

This preparation step does not edit runtime artwork or run a model.  The v4
installer translated body pixels when recropping and changed their world scale
in the manifest; it only resampled heads.  Consequently body landmarks have an
exact crop-translation mapping as well as a separate world-preserving mapping.
Both are recorded explicitly so a texture edit cannot confuse the two.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import importlib.util
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi


HERE = Path(__file__).resolve().parent
V3 = HERE.parent / "local-qwen21-unified-v3"
V4 = HERE.parent / "body-scale-v4"
spec = importlib.util.spec_from_file_location("attack_v5_inventory_tools", V3 / "prepare.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)

JOINTS = {
    "left_shoulder": 11, "right_shoulder": 12,
    "left_elbow": 13, "right_elbow": 14,
    "left_wrist": 15, "right_wrist": 16,
    "left_hip": 23, "right_hip": 24,
    "left_knee": 25, "right_knee": 26,
    "left_ankle": 27, "right_ankle": 28,
}
WEAPONS = ("W01", "W02", "L01", "W07", "W08", "L02", "W11")
SPECIALS = {"dodge", "hit", "death", "spell", "interact"}
NON_BOW_CARRY = ("W01", "W02", "L01", "W11")


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reasons(record):
    actions = {ref["action"] for ref in record["refs"]}
    result = []
    if actions & {f"explore_idle_{w}" for w in WEAPONS}:
        result.append("exploration idle: short vest / inconsistent belt and pouches")
    if actions & {f"{kind}_{w}" for kind in ("idle", "walk") for w in ("W01", "W07", "W11")}:
        result.append("held idle/walk W01/W07/W11: inconsistent garment and waist kit")
    if actions & SPECIALS:
        result.append("non-bow special action: inconsistent garment and waist kit")
    if actions & {f"explore_dodge_{w}" for w in NON_BOW_CARRY}:
        result.append("non-bow exploration dodge: inconsistent waist kit")
    return result


def finite(value):
    return isinstance(value, (float, int)) and math.isfinite(value)


def adapt_pose(record, old_record, pose, sheet):
    """Map MediaPipe crop-local pixels to current crop-local texture pixels."""
    raw = pose.get("landmarks", []) if pose else []
    available = old_record is not None and len(raw) == 33
    crop = sheet.crop((record["rect"][0], record["rect"][1],
                       record["rect"][0] + record["rect"][2],
                       record["rect"][1] + record["rect"][3]))
    alpha = np.asarray(crop)[..., 3]
    distance = ndi.distance_transform_edt(alpha < 64)
    ox, oy = record["origin"]
    scale = record["scale"]
    issues = []
    joints = {}
    mapping_error = 0.0
    if not available:
        issues.append("old physical frame or complete 33-point pose missing")
    for name, index in JOINTS.items():
        lm = raw[index] if available else None
        if not lm or not all(finite(lm.get(k)) for k in ("x", "y", "visibility", "presence")):
            joints[name] = dict(mediapipeIndex=index, native=None, review=None,
                                worldPreservedNative=None, confidence=0.0, usable=False,
                                reason="missing or non-finite landmark; preserve source pixels")
            continue
        old_x, old_y = old_record["origin"]
        old_scale = old_record["scale"]
        # v4 kept body pixels intact; gutters/padding only changed crop offsets.
        nx, ny = lm["x"] - old_x + ox, lm["y"] - old_y + oy
        review = [256 + (nx - ox) * scale, 712 + (ny - oy) * scale]
        # This alternative keeps the PRE-v4 world position.  It does not locate
        # the current body texture and must not be used for waist patching.
        wn = [ox + (lm["x"] - old_x) * old_scale / scale,
              oy + (lm["y"] - old_y) * old_scale / scale]
        check = [256 + (wn[0] - ox) * scale, 712 + (wn[1] - oy) * scale]
        expected = [256 + (lm["x"] - old_x) * old_scale,
                    712 + (lm["y"] - old_y) * old_scale]
        mapping_error = max(mapping_error, abs(check[0] - expected[0]), abs(check[1] - expected[1]))
        ix, iy = round(nx), round(ny)
        inside = 0 <= ix < crop.width and 0 <= iy < crop.height
        support_distance = float(distance[iy, ix] * scale) if inside else None
        confidence = min(float(lm["visibility"]), float(lm["presence"]))
        usable = confidence >= .55 and inside and support_distance <= 18
        flags = []
        if confidence < .55:
            flags.append("low detection confidence / possibly occluded")
        if not inside:
            flags.append("landmark outside current semantic crop")
        elif support_distance > 18:
            flags.append("landmark too far from opaque character support")
        joints[name] = dict(mediapipeIndex=index, native=[nx, ny], review=review,
                            worldPreservedNative=wn, visibility=float(lm["visibility"]),
                            presence=float(lm["presence"]), confidence=confidence,
                            insideCrop=inside, supportDistanceReviewPixels=support_distance,
                            usable=usable, flags=flags)

    def center(kind):
        parts = [joints[f"{side}_{kind}"] for side in ("left", "right")]
        if not all(p["native"] is not None for p in parts):
            return None
        return np.mean([p["native"] for p in parts], axis=0)

    shoulder = center("shoulder")
    hip = center("hip")
    torso_length = None
    tilt = None
    if shoulder is not None and hip is not None:
        vector = (hip - shoulder) * scale
        torso_length = float(np.linalg.norm(vector))
        tilt = float(math.degrees(math.atan2(abs(vector[0]), abs(vector[1]))))
        if not 55 <= torso_length <= 320:
            issues.append("implausible projected shoulder-to-hip length")
    key_joint_names = ("left_shoulder", "right_shoulder", "left_hip", "right_hip")
    torso_good = all(joints[n]["usable"] for n in key_joint_names) and not issues
    hip_good = all(joints[n]["usable"] and joints[n]["confidence"] >= .70
                   for n in ("left_hip", "right_hip"))
    waist_usable = bool(torso_good and hip_good)
    actions = {ref["action"] for ref in record["refs"]}
    idle_roles = sorted(a for a in actions if "idle" in a)
    if tilt is not None and tilt > 60:
        issues.append("strongly tilted / lying torso: manual pose-aware patch review required")
        waist_usable = False
    if any(v["action"] == "death" and v["phase"] == 1 for v in record["refs"]):
        issues.append("final death pose: review foreshortening even when torso points vertically")
        waist_usable = False
    result = dict(image=record["image"], index=record["index"], direction=record["direction"],
                  action=record["action"], refs=record["refs"], rect=record["rect"],
                  origin=record["origin"], scale=scale, selectedReasons=reasons(record),
                  oldRect=old_record["rect"] if old_record else None,
                  oldOrigin=old_record["origin"] if old_record else None,
                  oldScale=old_record["scale"] if old_record else None,
                  poseAvailable=available, joints=joints,
                  shoulderCenterNative=shoulder.tolist() if shoulder is not None else None,
                  hipCenterNative=hip.tolist() if hip is not None else None,
                  projectedTorsoLengthReviewPixels=torso_length,
                  torsoTiltFromVerticalDegrees=tilt,
                  staticRole=bool(idle_roles), staticActions=idle_roles,
                  waistUsable=waist_usable, armProtectionReliable=all(joints[n]["usable"] for n in
                      ("left_elbow", "right_elbow", "left_wrist", "right_wrist")),
                  recommendation="waist-retarget candidate; inspect actual garment boundary" if waist_usable
                      else "preserve source; manual review or existing-pixel fallback required",
                  issues=issues, worldPreservingRoundtripMaxError=mapping_error)
    return result


def waist_boards(rows, sheets):
    """Local-only small waist contacts, grouped by facing; no cloud upload."""
    files = []
    font_color = "#f2f1ec"
    for direction in prepare.DIRECTIONS:
        selected = [r for r in rows if r["direction"] == direction]
        cols = 8
        tile_w, tile_h = 160, 158
        page = Image.new("RGB", (cols * tile_w, math.ceil(len(selected) / cols) * tile_h), "#25272a")
        draw = ImageDraw.Draw(page)
        for ordinal, r in enumerate(selected):
            x, y, w, h = r["rect"]
            crop = sheets[r["image"]].crop((x, y, x+w, y+h))
            center = r["hipCenterNative"]
            if center is None:
                # This is preview-only framing, never a replacement landmark.
                center = [w / 2, h / 2]
            scale = r["scale"]
            side = 185 / scale
            cx, cy = center[0], center[1] - 16 / scale
            # Rectangular preview viewport with isotropic pixels.  Do not
            # stretch the costume to fill a differently shaped thumbnail.
            box = (cx-side/2, cy-side*124/288, cx+side/2, cy+side*124/288)
            patch = crop.transform((144, 124), Image.Transform.AFFINE,
                (side/144, 0, box[0], 0, side/144, box[1]), Image.Resampling.BICUBIC)
            tx, ty = (ordinal % cols) * tile_w + 8, (ordinal // cols) * tile_h + 30
            page.paste(patch, (tx, ty), patch)
            label = f'{ordinal:02} #{r["index"]} {r["action"]}'
            draw.text((tx-5, ty-27), label[:27], fill=font_color)
            draw.text((tx-5, ty-14), "static" if r["staticRole"] else "pose", fill="#96c6e0")
            draw.rectangle((tx-1, ty-1, tx+144, ty+124),
                           outline="#75bd89" if r["waistUsable"] else "#d4a067")
            for name, joint in r["joints"].items():
                if not joint["native"] or not any(k in name for k in ("hip", "wrist", "elbow")):
                    continue
                px = tx + (joint["native"][0]-box[0])*144/side
                py = ty + (joint["native"][1]-box[1])*144/side
                if tx <= px < tx+144 and ty <= py < ty+124:
                    color = "#ffca6b" if "hip" in name else "#7bb4ff"
                    draw.ellipse((px-2, py-2, px+2, py+2), fill=color)
        path = HERE / f"waist-grid-{direction}.jpg"
        page.save(path, quality=88)
        files.append(dict(file=path.name, direction=direction, frames=len(selected), size=list(page.size),
                          frameKeys=[dict(image=r["image"], index=r["index"]) for r in selected]))
    return files


def main():
    manifest_hash = prepare.digest(prepare.MANIFEST)
    manifest = json.loads(prepare.MANIFEST.read_text(encoding="utf-8-sig"))
    current = list(prepare.inventory(manifest).values())
    current.sort(key=lambda r: (r["image"], r["index"]))
    chosen = [r for r in current if reasons(r)]
    if len(current) != 996 or len(chosen) != 188:
        raise RuntimeError(f"Current inventory changed: {len(current)} total / {len(chosen)} selected")
    names = sorted({r["image"] for r in current})
    image_records = []
    sheets = {}
    selected_names = {r["image"] for r in chosen}
    for name in names:
        path = prepare.ACTOR / name
        with Image.open(path) as im:
            size = list(im.size)
            if name in selected_names or name == manifest["actions"]["attack_sword_W01"]["image"]:
                sheets[name] = im.convert("RGBA")
        image_records.append(dict(image=name, sha256=prepare.digest(path), size=size,
                                  metaSHA256=prepare.digest(str(path)+".meta")))
    old_inventory = json.loads((V4 / "inventory.json").read_text(encoding="utf-8-sig"))
    old_by_key = {(r["image"], r["index"]): r for r in old_inventory["frames"]}
    old_pose = json.loads((V4 / "pose-landmarks.json").read_text(encoding="utf-8-sig"))
    poses = {(r["image"], r["index"]): r for r in old_pose["frames"]}
    rows = [adapt_pose(r, old_by_key.get((r["image"], r["index"])),
                       poses.get((r["image"], r["index"])), sheets[r["image"]]) for r in chosen]
    reference_records = [r for r in current if any(v["action"] == "attack_sword_W01" for v in r["refs"])]
    reference_rows = [adapt_pose(r, old_by_key.get((r["image"], r["index"])),
                                poses.get((r["image"], r["index"])), sheets[r["image"]])
                      for r in reference_records]
    authority = dict(identity="current attack_sword_W01 phase0; user screenshot image 3",
                     pose="each original phase, facing, equipment, support/flight anchor and timing",
                     scope="repair inconsistent garment/belt/pouches; preserve the other 808 physical frames")
    write(HERE / "inventory.json", dict(manifestSHA256=manifest_hash,
        actionCount=len(manifest["actions"]), physicalFrameCount=len(current), images=image_records,
        frames=current, authority=authority))
    write(HERE / "selection.json", dict(manifestSHA256=manifest_hash,
        selectedPhysicalFrames=len(chosen), selectedImageCount=len(selected_names),
        retainedPhysicalFrames=len(current)-len(chosen), authority=authority,
        selectionBasis="visual garment audit; selection is a candidate repair set, not an acceptance verdict",
        images=sorted(selected_names),
        frames=[dict(r, selectedReasons=reasons(r)) for r in chosen]))
    coordinate_notes = {
        "native": "current semantic crop-local texture pixels; old landmark - old origin + current origin",
        "review": "current 400px/world display; [256,712] + (native-currentOrigin)*currentScale",
        "worldPreservedNative": "current crop coordinates of PRE-v4 world position; currentOrigin + (oldLandmark-oldOrigin)*oldScale/currentScale; do not use for texture retarget",
        "mappingJustification": "v4 apply.py keeps torso/limb texture pixels unchanged, recrops/translates the atlas, and applies body scale at runtime; its head-only resampling does not move these body joints",
        "confidence": "minimum of existing MediaPipe visibility/presence; not independent anatomical truth",
        "fallback": "missing, unsupported, low-confidence or lying poses are flagged; no fabricated replacement landmarks",
    }
    write(HERE / "pose-data.json", dict(manifestSHA256=manifest_hash,
        sourcePoseFile=str(V4 / "pose-landmarks.json"),
        sourcePoseSHA256=prepare.digest(V4 / "pose-landmarks.json"),
        sourceInventorySHA256=prepare.digest(V4 / "inventory.json"),
        newInference=False, coordinateNotes=coordinate_notes, frames=rows, attackReferenceFrames=reference_rows))
    boards = waist_boards(rows, sheets)
    issues = Counter(issue for r in rows for issue in r["issues"])
    missing = [dict(image=r["image"], index=r["index"], issues=r["issues"])
               for r in rows if not r["poseAvailable"]]
    manual = [dict(image=r["image"], index=r["index"], direction=r["direction"],
                   lowConfidenceJoints=[n for n, p in r["joints"].items() if not p["usable"]],
                   issues=r["issues"], recommendation=r["recommendation"])
              for r in rows if not r["waistUsable"]]
    report = dict(manifestSHA256=manifest_hash, selectedFrames=len(rows),
        existingPoseAvailable=sum(r["poseAvailable"] for r in rows), missingPoses=missing,
        waistRetargetCandidates=sum(r["waistUsable"] for r in rows),
        manualReviewRequired=len(manual), staticRoleFrames=sum(r["staticRole"] for r in rows),
        reliableArmProtectionFrames=sum(r["armProtectionReliable"] for r in rows),
        issueCounts=dict(issues), manualReviewFrames=manual,
        mappingRoundtripMaxError=max(r["worldPreservingRoundtripMaxError"] for r in rows),
        currentImages=len(names), selectedImages=len(selected_names),
        gridFiles=boards, newInference=False, runtimeAssetsModified=False,
        acceptance="prepared for deterministic local retargeting; no artwork accepted or installed")
    write(HERE / "pose-reliability.json", report)
    if prepare.digest(prepare.MANIFEST) != manifest_hash:
        raise RuntimeError("Runtime manifest changed during preparation; rerun before consuming output")
    print(json.dumps({k:report[k] for k in ("selectedFrames", "existingPoseAvailable", "waistRetargetCandidates",
        "manualReviewRequired", "staticRoleFrames", "reliableArmProtectionFrames", "mappingRoundtripMaxError")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
