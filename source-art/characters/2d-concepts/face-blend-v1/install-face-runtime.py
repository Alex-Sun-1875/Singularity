"""Measure face replacements against the immutable 88-action/68-PNG baseline.

Default: read-only dry run. Only --install copies PNG bytes and writes runtime
manifest/installation record. No image is saved, edited, resized or resampled.

Full inputs are assets/{oldImage}, retaining each old relative directory, e.g.
  assets/hero-v6/hero-v4-idle-readable.png
  assets/carry-v1/explore-W01-dodge.png
Every one of the frozen 68 images is required for a full installation. Partial
full measurements are reported but cannot install. --pilot selects only the
W01 carry dodge image (including its existing idle alias) plus the HUD. The
pilot source defaults to assets/carry-v1/explore-W01-dodge.png when present,
otherwise prototype-explore-W01-dodge-v3.png. HUD defaults to prototype-hud-v3.png.

Examples (run from any working directory):
  python install-face-runtime.py --pilot
  python install-face-runtime.py --pilot --report pilot-measurement.json
  python install-face-runtime.py --pilot --install
  python install-face-runtime.py --assets assets --report full-measurement.json
  python install-face-runtime.py --assets assets --install

Relative CLI paths resolve against this script's directory. The optional
--records JSON is {"images": {"old/path.png": {...}}, "hud": {...}}; repeat
--records to merge independent measurement/crop records (later fields win). Per-image
fields: rawOutputPath, sha256, pixelEdits:false, frameRects (only used when old
crops fail complete-alpha validation), registrationRois (cell index -> absolute
[x,y,width,height]), registrationOverrides (cell index -> measured [dx,dy]),
registrationAccepted:true after visual review. Legacy touching-body atlases
may supply frameRects plus a documented semanticCropReview; those reviewed
frozen-layout rectangles are checked for complete unique alpha16 coverage
without assuming each figure is a separate connected component. No segmentation
or pixel changes are performed by this exception. Arrays or index-keyed objects
are accepted for ROIs/overrides. Adjacent *.provenance.json is read by default;
explicit records override its fields. Provenance paths resolve relative to
their JSON file, with repository-relative paths also accepted. A supplied raw
output/recorded hash must match the unchanged source bytes. Missing raw-output
provenance is reported during dry run; installation requires raw/source/runtime
byte identity. Installation permits only the exact frozen manifest SHA or an
exactly verified prior pilot/full install record. All PNGs/manifest are staged
under src/cocos/temp, then atomically replaced with rollback on failure.

The existing weapon-carry-v1 read-only alpha/native_geometry/translation helpers
perform all pixel measurement. This adapter never invokes its action builder.
Old complete crops are retained whenever they contain every alpha>=16 pixel
exactly once. Otherwise outgrown cells expand to complete native alpha. If old
padding includes a neighbour, or tiny alpha16 bridges connect cells, reuse the
helper's validated automatic ownership/crops (alpha64 body seeds, all alpha16
pixels retained). This can trim neighbour-only padding, never figure/weapon
pixels. Coverage must remain complete and unique for every alpha>=16 pixel.
Each old absolute support anchor is transferred into the chosen crop. Runs keep
the accepted per-direction ground relation; a common measured Y translation is
allowed only when phase offsets span <=2px. Larger disagreement blocks install.
Timing, phase order, direction lookup, frame lookup, and each action's UPP are
copied exactly from baseline, including existing aliases.

Limitations: binary lower-body registration measures translation, not identity,
pose correctness, rotation or scale; those require visual review. No build is
started. The HUD is copied to flat2d/hero-head-face-v3.png; this script does not
edit the game's HUD resource reference. Old assets and baseline remain intact.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import statistics
import sys
import tempfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ACTOR = ROOT / "src/cocos/assets/resources/flat2d/characters/raphael"
FLAT = ACTOR.parents[1]
BASELINE = HERE / "baseline-manifest.json"
INVENTORY = HERE / "baseline-images.json"
HELPER = HERE.parent / "weapon-carry-v1/measure-install.py"
PILOT_IMAGE = "carry-v1/explore-W01-dodge.png"
FACE_DESIGN = HERE / "face-front-v3.png"
FACE_PROFILE = HERE / "face-study-v1.png"
EXPECTED_BASELINE_SHA = "c1615afe98a69dbf450e2fce1ffdd8c5bce8c5389663d2d93719df252a2bc097"
GEOMETRY_FIELDS = {"image", "frameImages", "perFrameRects", "frameRectsByImage",
                   "perFrameOrigins", "alphaBounds", "perPhaseAlphaBounds",
                   "alphaBoundsThreshold", "originMethod", "sourcePNG",
                   "sourcePNGSHA256", "sourcePNGs", "sourcePNGSHA256s"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def cli_path(value):
    path = Path(value)
    return (path if path.is_absolute() else HERE / path).resolve()


def provenance_path(value, directory):
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    choices = [directory / path, ROOT / path]
    return next((p.resolve() for p in choices if p.is_file()), choices[0].resolve())


def safe_image(value):
    path = PurePosixPath(value)
    if "\\" in value or path.is_absolute() or ".." in path.parts or path.suffix != ".png":
        raise ValueError(f"Unsafe baseline PNG path: {value}")
    return path.as_posix()


def renamed(image):
    return "face-v1/" + safe_image(image)


def action_images(action):
    return list(dict.fromkeys([action["image"]] + action.get("frameImages", [])))


def sheet_rects(action, image):
    mapping = action.get("frameRectsByImage", {})
    return mapping.get(image.removesuffix(".png"), action.get("perFrameRects"))


def semantic_fields(action):
    # A whitelist of mutable geometry/provenance makes every other field an
    # exact invariant, including unknown future timing/direction/scale fields.
    return {k: v for k, v in action.items() if k not in GEOMETRY_FIELDS}


def runtime_index(action, direction_index, ordinal):
    column = action.get("frameIndices", list(range(action["frames"])))[ordinal]
    if "directionFrameIndices" in action:
        return action["directionFrameIndices"][direction_index]
    if action.get("absoluteFrameIndices"):
        return column
    return action.get("row", direction_index) * action["columns"] + column


def origin_at(action, image, index, directions):
    origins = action["perFrameOrigins"]
    if isinstance(origins, list):
        return origins[index]
    matches = []
    for row, direction in enumerate(directions):
        for ordinal in range(action["frames"]):
            phase_image = action.get("frameImages", [action["image"]] * action["frames"])[ordinal]
            if phase_image == image and runtime_index(action, row, ordinal) == index:
                matches.append(origins[direction][ordinal])
    if not matches or any(point != matches[0] for point in matches):
        raise ValueError(f"No unique accepted anchor for {image}, cell {index}")
    return matches[0]


def load_provenance(source, explicit, directory, hashes):
    adjacent = source.with_suffix(".provenance.json")
    record, record_dir = {}, source.parent
    if adjacent.is_file():
        record = read_json(adjacent)
        record_dir = adjacent.parent
        hashes[str(adjacent.resolve())] = sha(adjacent)
        # Resolve before overlaying an explicit record from another directory.
        if record.get("rawOutputPath"):
            record["rawOutputPath"] = str(provenance_path(record["rawOutputPath"], record_dir))
    if explicit:
        overlay = copy.deepcopy(explicit)
        if overlay.get("rawOutputPath"):
            overlay["rawOutputPath"] = str(provenance_path(overlay["rawOutputPath"], directory))
        record.update(overlay)
    digest = sha(source)
    hashes[str(source)] = digest
    if record.get("sha256") and record["sha256"] != digest:
        raise ValueError(f"Recorded source SHA256 mismatch: {source}")
    if record.get("pixelEdits") is True or record.get("pixelEditsAfterGeneration") is True:
        raise ValueError(f"Provenance declares edited pixels: {source}")
    raw = record.get("rawOutputPath")
    if raw:
        raw_path = provenance_path(raw, record_dir)
        if not raw_path.is_file() or sha(raw_path) != digest:
            raise ValueError(f"Raw/source byte identity failed: {raw_path} -> {source}")
        hashes[str(raw_path)] = digest
    return record, {"sourcePath": str(source), "sourceSHA256": digest,
                    "rawOutputPath": str(provenance_path(raw, record_dir)) if raw else None,
                    "rawSourceSHAEqual": True if raw else None,
                    "warning": None if raw else "No raw-generation provenance supplied; source/runtime byte equality remains mandatory."}


def reviewed_semantic_geometry(a, layout, rects, review, helper):
    """Adapt reviewed frozen-layout crops; no connected-component ownership."""
    height, width = a.shape
    if not review or len(rects) != layout[0] * layout[1]:
        raise ValueError("Reviewed semantic frameRects must match the frozen cell count")
    mask = a >= 16
    corners = helper.np.concatenate([a[:8, :8].ravel(), a[:8, -8:].ravel(),
                                    a[-8:, :8].ravel(), a[-8:, -8:].ravel()])
    empty, corner_max = float((a < 16).mean()), int(corners.max())
    if empty < .65 or corner_max >= 16:
        raise ValueError(f"Semantic crops cannot bypass native transparency: alphaBelow16Fraction={empty:.6f}, corner8x8MaxAlpha={corner_max}")
    frames, normalized = [], []
    for index, original in enumerate(rects):
        rect = list(map(int, original))
        if rect != original or len(rect) != 4:
            raise ValueError(f"Non-integer semantic crop: {index}")
        x, y, w, h = rect
        if min(x, y) < 0 or min(w, h) <= 0 or x+w > width or y+h > height:
            raise ValueError(f"Out-of-image semantic crop: {index}/{rect}")
        bounds = helper.local_bounds(mask, rect)
        normalized.append(rect)
        frames.append({"index": index, "rect": rect, "alphaBounds": bounds,
                       "ownershipPolicy": "Reviewed frozen frame semantics; complete unique alpha16 coverage checked independently."})
    return {"size": [width, height], "layout": layout, "rects": normalized,
            "alphaBounds": [frame["alphaBounds"] for frame in frames], "frames": frames,
            "alphaExtrema": [int(a.min()), int(a.max())], "alphaBelow16Fraction": empty,
            "alphaZeroFraction": float((a == 0).mean()), "corner8x8MaxAlpha": corner_max,
            "alphaThreshold": 16, "bodySeedThreshold": None,
            "cropPolicy": "Reviewed immutable frame semantics permit already-touching figures; every native alpha>=16 pixel must occur in exactly one crop.",
            "semanticCropReview": review}


def measure_image(image, source, references, baseline, helper, record, identity):
    key, original = references[0]
    before = sheet_rects(original, image)
    if not before or len(before) % original["columns"]:
        raise ValueError(f"Invalid frozen crop topology: {key}/{image}")
    for other_key, other in references:
        if sheet_rects(other, image) != before or other["columns"] != original["columns"]:
            raise ValueError(f"Shared image has conflicting frozen crop topology: {other_key}/{image}")
    old, new = helper.alpha(ACTOR / image), helper.alpha(source)
    if old.shape != new.shape:
        raise ValueError(f"Native dimensions changed: {image}: {list(old.shape[::-1])} -> {list(new.shape[::-1])}")
    layout = [original["columns"], len(before) // original["columns"]]
    crop_issue, union_issue, automatic_rects, expanded_indices = None, None, None, []
    try:
        geometry = helper.native_geometry(new, layout, before)
        crop_policy = "Frozen crops retained: complete alpha>=16 coverage verified."
    except ValueError as error:
        crop_issue = str(error)
        if record.get("frameRects") and record.get("semanticCropReview"):
            geometry = reviewed_semantic_geometry(new, layout, record["frameRects"], record["semanticCropReview"], helper)
            crop_policy = geometry["cropPolicy"]
        else:
            automatic = helper.native_geometry(new, layout, record.get("frameRects"))
            automatic_rects = automatic["rects"]
            expanded = []
            for index, (old_rect, native_rect, local) in enumerate(zip(before, automatic_rects, automatic["alphaBounds"])):
                ox, oy, ow, oh = old_rect
                nx, ny = native_rect[:2]
                left, top = min(ox, nx + local[0]), min(oy, ny + local[1])
                right, bottom = max(ox + ow, nx + local[2]), max(oy + oh, ny + local[3])
                rect = [left, top, right - left, bottom - top]
                expanded.append(rect)
                if rect != old_rect:
                    expanded_indices.append(index)
            # Existing registration/crop code owns all pixel assignment. This
            # adapter only unions coordinates and asks it to validate coverage.
            try:
                geometry = helper.native_geometry(new, layout, expanded)
                crop_policy = "Frozen crops retained per cell; only outgrown cells expanded to complete alpha>=16 bounds, validated without clipping/neighbour overlap."
            except ValueError as expansion_error:
                union_issue = str(expansion_error)
                # Successful alpha64-seeded ownership still retains alpha16.
                # Explicit alpha16 connectivity must not reject that result.
                if any(frame.get("foreignAlphaPixelsInsideRect", 0) for frame in automatic["frames"]):
                    raise ValueError("Automatic complete crops contain neighbour alpha")
                geometry = automatic
                crop_policy = "Validated helper automatic crops: remove neighbour-only old padding / separate tiny alpha16 bridges using alpha64 seeds when needed; every alpha>=16 body/weapon/detached pixel retained, foreign alpha zero."
    mask = new >= 16
    coverage = helper.np.zeros(new.shape, dtype=helper.np.uint16)
    for rect in geometry["rects"]:
        x, y, width, height = map(int, rect)
        coverage[y:y+height, x:x+width] += mask[y:y+height, x:x+width]
    coverage_report = {"threshold": 16, "totalAlphaPixelCount": int(helper.np.count_nonzero(mask)),
                       "uncoveredAlphaPixelCount": int(helper.np.count_nonzero(mask & (coverage == 0))),
                       "multiplyCoveredAlphaPixelCount": int(helper.np.count_nonzero(mask & (coverage > 1)))}
    if coverage_report["uncoveredAlphaPixelCount"] or coverage_report["multiplyCoveredAlphaPixelCount"]:
        raise ValueError(f"Complete/unique alpha16 crop coverage failed: {coverage_report}")
    legacy_coverage = None
    if geometry.get("semanticCropReview"):
        old_mask = old >= 16
        old_coverage = helper.np.zeros(old.shape, dtype=helper.np.uint16)
        for rect in geometry["rects"]:
            x, y, width, height = map(int, rect)
            old_coverage[y:y+height, x:x+width] += old_mask[y:y+height, x:x+width]
        legacy_coverage = {"threshold": 16, "totalAlphaPixelCount": int(helper.np.count_nonzero(old_mask)),
                           "uncoveredAlphaPixelCount": int(helper.np.count_nonzero(old_mask & (old_coverage == 0))),
                           "multiplyCoveredAlphaPixelCount": int(helper.np.count_nonzero(old_mask & (old_coverage > 1)))}
        if legacy_coverage["uncoveredAlphaPixelCount"] or legacy_coverage["multiplyCoveredAlphaPixelCount"]:
            raise ValueError(f"Reviewed semantic crops must also contain complete unique frozen old bodies: {legacy_coverage}")
    registrations, issues = [], []
    for index, old_rect in enumerate(before):
        anchor = origin_at(original, image, index, baseline["directions"])
        ground = [old_rect[0] + anchor[0], old_rect[1] + anchor[1]]
        stature = 1.556 / original["worldUnitsPerPixel"]
        left, top = max(0, round(ground[0] - .22 * stature)), max(0, round(ground[1] - .45 * stature))
        right, bottom = min(old.shape[1], round(ground[0] + .22 * stature)), min(old.shape[0], round(ground[1]) + 2)
        roi = helper.get_item(record.get("registrationRois"), index, [left, top, right - left, bottom - top])
        measured = helper.translation(old, new, roi, helper.get_item(record.get("registrationOverrides"), index))
        measured.update({"index": index, "oldRect": old_rect, "oldAbsoluteOrigin": ground})
        registrations.append(measured)
        if (measured["lowerBodyMaskIoU"] < .65 or measured.get("atSearchBoundary")) and not record.get("registrationAccepted"):
            issues.append(f"Cell {index}: weak/boundary lower-body registration requires visual review and registrationAccepted:true")
    return {**identity, **geometry, "oldImage": image, "newImage": renamed(image),
            "runtimePath": str((ACTOR / renamed(image)).resolve()),
            "oldRuntimePath": str((ACTOR / image).resolve()),
            "referenceActions": [name for name, _ in references],
            "oldRects": copy.deepcopy(before), "cropSelectionPolicy": crop_policy,
            "frozenCropRejection": crop_issue, "diagnosticAutomaticRects": automatic_rects,
            "unionCropRejection": union_issue, "completeAlphaCoverage": coverage_report,
            "frozenSourceAlphaCoverageInSemanticCrops": legacy_coverage,
            "expandedFrameIndices": expanded_indices, "registrations": registrations,
            "issues": issues, "pixelEditsAfterGeneration": False}


def transfer(point, old_rect, new_rect, delta):
    return [point[0] + old_rect[0] + delta[0] - new_rect[0],
            point[1] + old_rect[1] + delta[1] - new_rect[1]]


def adapt_action(key, original, sheets, directions, issues, run_records):
    action = copy.deepcopy(original)
    selected = [image for image in action_images(original) if image in sheets]
    if not selected:
        return action
    if len(selected) != len(action_images(original)):
        raise ValueError(f"Cannot install half of a multi-image action: {key}")
    first = sheets[original["image"]]
    action["image"] = first["newImage"]
    action["perFrameRects"] = copy.deepcopy(first["rects"])
    action["alphaBounds"] = copy.deepcopy(first["alphaBounds"])
    if "frameImages" in original:
        action["frameImages"] = [sheets[name]["newImage"] for name in original["frameImages"]]
    if "frameRectsByImage" in original:
        action["frameRectsByImage"] = {
            renamed(image).removesuffix(".png"): copy.deepcopy(sheets[image]["rects"])
            for image in action_images(original)}
        if set(action["frameRectsByImage"]) != {image.removesuffix(".png") for image in action["frameImages"]}:
            raise ValueError(f"Incomplete runtime frameRectsByImage paths: {key}")
    if isinstance(original["perFrameOrigins"], list):
        action["perFrameOrigins"] = [
            transfer(point, first["oldRects"][index], first["rects"][index],
                     first["registrations"][index]["bodyOnlyTranslationXY"])
            for index, point in enumerate(original["perFrameOrigins"])]
    else:
        # Preserve the accepted absolute ground across all old phases; never
        # derive a new ground from newly drawn boot/weapon/head alpha extents.
        origins, bounds = {}, {}
        for row, direction in enumerate(directions):
            phases = [(sheets[image], runtime_index(original, row, ordinal))
                      for ordinal, image in enumerate(original["frameImages"])]
            dys = [sheet["registrations"][index]["bodyOnlyTranslationXY"][1] for sheet, index in phases]
            ground_dy = statistics.median(dys)
            if max(dys) - min(dys) > 2:
                issues.append(f"{key}/{direction}: measured phase Y translations disagree by >2px: {dys}; regeneration/visual remeasurement required")
            origins[direction], bounds[direction] = [], []
            for ordinal, (sheet, index) in enumerate(phases):
                delta = sheet["registrations"][index]["bodyOnlyTranslationXY"]
                origins[direction].append(transfer(original["perFrameOrigins"][direction][ordinal],
                                                   sheet["oldRects"][index], sheet["rects"][index],
                                                   [delta[0], ground_dy]))
                bounds[direction].append(sheet["alphaBounds"][index])
            run_records.append({"action": key, "direction": direction,
                                "measuredPhaseYTranslations": dys, "appliedCommonYTranslation": ground_dy,
                                "oldAbsoluteGroundY": [sheet["oldRects"][index][1] + original["perFrameOrigins"][direction][ordinal][1]
                                                       for ordinal, (sheet, index) in enumerate(phases)],
                                "newAbsoluteGroundY": [sheet["rects"][index][1] + origins[direction][ordinal][1]
                                                       for ordinal, (sheet, index) in enumerate(phases)]})
        action["perFrameOrigins"] = origins
        if "perPhaseAlphaBounds" in original:
            action["perPhaseAlphaBounds"] = bounds
    action["alphaBoundsThreshold"] = 16
    action["originMethod"] = "Frozen accepted support anchors transferred by measured lower-body alpha translation; original UPP/timing/directions retained; complete alpha>=16 native crops; unchanged PNG bytes."
    for field in ("sourcePNG", "sourcePNGSHA256"):
        action.pop(field, None)
    action["sourcePNGs"] = [sheets[image]["sourcePath"] for image in action_images(original)]
    action["sourcePNGSHA256s"] = [sheets[image]["sourceSHA256"] for image in action_images(original)]
    if semantic_fields(action) != semantic_fields(original):
        raise ValueError(f"Animation/scale semantics changed: {key}")
    if action["worldUnitsPerPixel"] != original["worldUnitsPerPixel"]:
        raise ValueError(f"Accepted worldUnitsPerPixel changed: {key}")
    return action


def validate_live_manifest(current, baseline):
    if set(current["actions"]) != set(baseline["actions"]) or current["directions"] != baseline["directions"]:
        raise ValueError("Runtime action/direction coverage differs from frozen baseline; refusing to replace unrelated changes")
    for key, action in current["actions"].items():
        old = baseline["actions"][key]
        if semantic_fields(action) != semantic_fields(old):
            raise ValueError(f"Runtime animation/scale semantics changed since freeze: {key}")
        for field in ("image", "frameImages"):
            if field not in old:
                continue
            before = old[field] if isinstance(old[field], list) else [old[field]]
            now = action.get(field, []) if isinstance(old[field], list) else [action.get(field)]
            if len(now) != len(before) or any(n not in (o, renamed(o)) for o, n in zip(before, now)):
                raise ValueError(f"Runtime image/phase references changed since freeze: {key}/{field}")


def known_manifest_input(manifest_bytes):
    """Permit only the frozen bytes or an exactly recorded prior installation."""
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    if digest == EXPECTED_BASELINE_SHA:
        return {"kind": "frozen baseline", "sha256": digest}
    current = json.loads(manifest_bytes)
    for path in (HERE / "pilot-install-record.json", HERE / "runtime-install-record.json"):
        if not path.is_file():
            continue
        record = read_json(path)
        if record.get("manifestOutputSHA256") != digest or record.get("candidateManifest") != current:
            continue
        serialized = json.dumps(record["candidateManifest"], ensure_ascii=False, indent=2) + "\n"
        # Earlier installer records used Windows text-mode CRLF. New atomic
        # writes use explicit UTF-8 bytes/LF; both must verify exactly.
        encodings = (serialized.encode("utf8"), serialized.replace("\n", "\r\n").encode("utf8"))
        if digest not in {hashlib.sha256(value).hexdigest() for value in encodings}:
            continue
        return {"kind": "known prior face installation", "sha256": digest,
                "recordPath": str(path), "recordSHA256": sha(path)}
    raise ValueError("Runtime manifest SHA256 is neither frozen baseline nor an exactly verified known face installation; refusing unknown top-level/geometry changes")


def install_measured(args, candidate, report, hashes, baseline, sheets, hud,
                     baseline_bytes, inventory_bytes):
    """Stage/verify all bytes outside imported assets, then commit or roll back."""
    manifest_bytes = args.manifest.read_bytes()
    trusted = known_manifest_input(manifest_bytes)
    current = json.loads(manifest_bytes)
    validate_live_manifest(current, baseline)
    if args.manifest.resolve().parent != ACTOR.resolve():
        raise ValueError("Install manifest must reside in the existing Raphael runtime asset directory")
    if args.pilot:
        pilot_candidate = copy.deepcopy(current)
        for key in report["adaptedActionKeys"]:
            pilot_candidate["actions"][key] = candidate["actions"][key]
        pilot_candidate.update(report["identityReferences"])
        pilot_candidate["revision"] = candidate["revision"]
        candidate = pilot_candidate
        report["candidateManifest"] = candidate
    measured_files = list(sheets.values()) + [hud]
    if any(measured.get("rawSourceSHAEqual") is not True for measured in measured_files):
        raise ValueError("Installation requires raw/source PNG SHA256 equality for every selected image and HUD")
    manifest_output = (json.dumps(candidate, ensure_ascii=False, indent=2) + "\n").encode("utf8")
    output_sha = hashlib.sha256(manifest_output).hexdigest()
    temp_root = (ROOT / "src/cocos/temp").resolve()
    temp_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="face-blend-v1-install-", dir=temp_root)).resolve()
    if not staging.is_relative_to(temp_root):
        raise ValueError(f"Invalid staging directory: {staging}")
    entries, replaced, rollback_errors = [], [], []
    manifest_replaced = False
    record_path = HERE / ("pilot-install-record.json" if args.pilot else "runtime-install-record.json")
    try:
        for index, measured in enumerate(measured_files):
            source, destination = Path(measured["sourcePath"]), Path(measured["runtimePath"])
            if source.resolve() == destination.resolve():
                raise ValueError(f"Source must remain separate from runtime destination: {source}")
            staged, backup = staging / f"new-{index}.png", staging / f"before-{index}.png"
            shutil.copyfile(source, staged)
            if sha(staged) != measured["sourceSHA256"] or sha(source) != measured["sourceSHA256"]:
                raise ValueError(f"Staged/source PNG bytes changed: {source}")
            before_sha = sha(destination) if destination.is_file() else None
            if before_sha is not None:
                shutil.copyfile(destination, backup)
                if sha(backup) != before_sha:
                    raise ValueError(f"Runtime PNG changed while staging backup: {destination}")
            entries.append({"destination": destination, "staged": staged, "backup": backup,
                            "beforeSHA256": before_sha, "newSHA256": measured["sourceSHA256"]})
        staged_manifest = staging / "new-manifest.json"
        staged_manifest.write_bytes(manifest_output)
        if sha(staged_manifest) != output_sha:
            raise ValueError("Staged manifest SHA256 mismatch")
        if BASELINE.read_bytes() != baseline_bytes or INVENTORY.read_bytes() != inventory_bytes:
            raise ValueError("Frozen baseline/inventory changed during measurement")
        for path, digest in hashes.items():
            if sha(path) != digest:
                raise ValueError(f"Input changed during measurement/staging: {path}")
        if trusted.get("recordPath") and sha(trusted["recordPath"]) != trusted["recordSHA256"]:
            raise ValueError("Known installation input record changed during staging")
        if args.manifest.read_bytes() != manifest_bytes:
            raise ValueError("Runtime manifest changed during staging; runtime not modified")
        for entry in entries:
            destination = entry["destination"]
            current_sha = sha(destination) if destination.is_file() else None
            if current_sha != entry["beforeSHA256"]:
                raise ValueError(f"Runtime PNG changed during staging: {destination}")
        backup = HERE / "manifest-before-face-v1.json"
        if not backup.exists():
            with backup.open("xb") as stream:
                stream.write(manifest_bytes)
        report.update({"manifestBeforeSHA256": trusted["sha256"], "trustedManifestInput": trusted,
                       "manifestBackupPath": str(backup), "manifestOutputPath": str(args.manifest.resolve()),
                       "manifestOutputSHA256": output_sha, "installationRecordPath": str(record_path),
                       "status": "installed unchanged PNG bytes and frozen-baseline action adaptations",
                       "installationWritePolicy": "All native PNGs/backups and manifest staged/verified under src/cocos/temp; os.replace commits; failures roll back committed PNGs/owned manifest, preserving concurrent external changes."})
        hashes[str(backup)] = sha(backup)
        hashes[str(args.manifest.resolve())] = output_sha
        for measured in measured_files:
            measured["runtimeSHA256"] = measured["sourceSHA256"]
            measured["sourceRuntimeSHAEqual"] = True
            hashes[measured["runtimePath"]] = measured["sourceSHA256"]
        staged_record = staging / "new-install-record.json"
        staged_record.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf8"))
        for entry in entries:
            destination = entry["destination"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(entry["staged"], destination)
            replaced.append(entry)
            if sha(destination) != entry["newSHA256"]:
                raise ValueError(f"Committed PNG SHA256 mismatch: {destination}")
        if args.manifest.read_bytes() != manifest_bytes:
            raise ValueError("Runtime manifest changed concurrently; rolling back PNG replacements and preserving that manifest")
        os.replace(staged_manifest, args.manifest)
        manifest_replaced = True
        if sha(args.manifest) != output_sha:
            raise ValueError("Committed manifest SHA256 mismatch")
        os.replace(staged_record, record_path)
    except Exception as error:
        if manifest_replaced:
            try:
                if args.manifest.read_bytes() == manifest_output:
                    rollback_manifest = staging / "rollback-manifest.json"
                    rollback_manifest.write_bytes(manifest_bytes)
                    os.replace(rollback_manifest, args.manifest)
                else:
                    rollback_errors.append("Concurrent external manifest preserved")
            except OSError as rollback_error:
                rollback_errors.append(f"Manifest rollback: {rollback_error}")
        for entry in reversed(replaced):
            try:
                destination = entry["destination"]
                if not destination.is_file() or sha(destination) != entry["newSHA256"]:
                    rollback_errors.append(f"Concurrent external PNG preserved: {destination}")
                elif entry["beforeSHA256"] is None:
                    destination.unlink()
                else:
                    os.replace(entry["backup"], destination)
            except OSError as rollback_error:
                rollback_errors.append(f"PNG rollback: {rollback_error}")
        detail = f"; rollback notes: {rollback_errors}; retained staging: {staging}" if rollback_errors else "; staged/committed PNG changes rolled back"
        raise ValueError(str(error) + detail) from error
    finally:
        # The absolute deletion target is verified to stay in the dedicated
        # non-imported temp root. Preserve backups when rollback needs review.
        if not rollback_errors and staging.is_relative_to(temp_root):
            shutil.rmtree(staging)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pilot", action="store_true", help="Measure/install only W01 carry dodge, its existing idle alias, and HUD")
    parser.add_argument("--assets", type=cli_path, default=HERE / "assets", help="Full source root: {root}/{oldImage}")
    parser.add_argument("--pilot-source", type=cli_path, help="Override pilot native PNG (same dimensions as frozen W01 dodge)")
    parser.add_argument("--hud-source", type=cli_path, default=HERE / "prototype-hud-v3.png")
    parser.add_argument("--records", type=cli_path, action="append", help="Optional image-keyed registration/provenance JSON (repeatable; fields merge); see input schema above")
    parser.add_argument("--manifest", type=cli_path, default=ACTOR / "manifest.json", help="Runtime manifest destination; frozen baseline is never writable")
    parser.add_argument("--report", type=cli_path, help="Optional full measurement JSON; permitted in dry run")
    parser.add_argument("--install", action="store_true", help="Copy native bytes and install measured metadata only after all selected inputs validate")
    args = parser.parse_args()
    if args.pilot_source and not args.pilot:
        parser.error("--pilot-source requires --pilot")
    if args.manifest.resolve() in (BASELINE.resolve(), INVENTORY.resolve()):
        parser.error("Frozen baseline/inventory cannot be an output manifest")
    baseline_bytes, inventory_bytes = BASELINE.read_bytes(), INVENTORY.read_bytes()
    if hashlib.sha256(baseline_bytes).hexdigest() != EXPECTED_BASELINE_SHA:
        raise ValueError("Frozen baseline SHA256 changed; do not regenerate/rebuild actions")
    baseline, inventory = json.loads(baseline_bytes), json.loads(inventory_bytes)
    references = {}
    for key, action in baseline["actions"].items():
        for image in action_images(action):
            references.setdefault(safe_image(image), []).append((key, action))
    if len(baseline["actions"]) != 88 or len(references) != 68:
        raise ValueError("Frozen baseline must contain exactly 88 actions/68 unique PNGs")
    listed = {item["image"]: item for item in inventory["images"]}
    if inventory["manifestSHA256"] != EXPECTED_BASELINE_SHA or set(listed) != set(references) or len(inventory["images"]) != 68:
        raise ValueError("Frozen inventory and manifest disagree")
    hashes = {str(BASELINE): EXPECTED_BASELINE_SHA, str(INVENTORY): sha(INVENTORY), str(HELPER): sha(HELPER), str(Path(__file__).resolve()): sha(__file__)}
    identity_fields = {"faceDesign": FACE_DESIGN.relative_to(ROOT).as_posix(),
                       "faceDesignSHA256": sha(FACE_DESIGN),
                       "faceProfile": FACE_PROFILE.relative_to(ROOT).as_posix(),
                       "faceProfileSHA256": sha(FACE_PROFILE),
                       "faceProfileScope": "Accepted far-right true profile only; front identity is face-front-v3.png. Existing sourceDesign retains the original body/clothing design."}
    hashes[str(FACE_DESIGN)] = identity_fields["faceDesignSHA256"]
    hashes[str(FACE_PROFILE)] = identity_fields["faceProfileSHA256"]
    # Check every frozen runtime source, including images outside a pilot.
    for image, item in listed.items():
        path = (ACTOR / image).resolve()
        if item.get("newImage") != renamed(image) or sha(path) != item["sha256"]:
            raise ValueError(f"Frozen original PNG/inventory changed: {path}")
        hashes[str(path)] = item["sha256"]
    old_hud = (ROOT / inventory["hud"]["runtimePath"]).resolve()
    if sha(old_hud) != inventory["hud"]["sha256"]:
        raise ValueError("Frozen original HUD bytes changed")
    hashes[str(old_hud)] = inventory["hud"]["sha256"]
    spec = importlib.util.spec_from_file_location("face_carry_measurement", HELPER)
    helper = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(helper)
    records, record_dir = {"images": {}, "hud": {}}, HERE
    for record_path in args.records or []:
        incoming = read_json(record_path)
        for image, original in incoming.get("images", {}).items():
            entry = copy.deepcopy(original)
            if entry.get("rawOutputPath"):
                entry["rawOutputPath"] = str(provenance_path(entry["rawOutputPath"], record_path.parent))
            records["images"].setdefault(image, {}).update(entry)
        hud_entry = copy.deepcopy(incoming.get("hud", {}))
        if hud_entry.get("rawOutputPath"):
            hud_entry["rawOutputPath"] = str(provenance_path(hud_entry["rawOutputPath"], record_path.parent))
        records["hud"].update(hud_entry)
        hashes[str(record_path)] = sha(record_path)
    selected = [PILOT_IMAGE] if args.pilot else sorted(references)
    sheets, errors, issues, missing = {}, [], [], []
    for image in selected:
        source = (args.assets / image).resolve()
        if args.pilot:
            source = args.pilot_source or (source if source.is_file() else HERE / "prototype-explore-W01-dodge-v3.png")
        if not source.is_file():
            missing.append(str(source))
            continue
        try:
            print(f"Measuring {image}", file=sys.stderr, flush=True)
            record, identity = load_provenance(source, records.get("images", {}).get(image, {}), record_dir, hashes)
            sheets[image] = measure_image(image, source, references[image], baseline, helper, record, identity)
            issues.extend(f"{image}: {issue}" for issue in sheets[image]["issues"])
        except (ValueError, OSError, KeyError, IndexError) as error:
            errors.append(f"{image}: {error}")
    hud = None
    if not args.hud_source.is_file():
        missing.append(str(args.hud_source))
    else:
        try:
            _, identity = load_provenance(args.hud_source, records.get("hud", {}), record_dir, hashes)
            old_alpha, new_alpha = helper.alpha(old_hud), helper.alpha(args.hud_source)
            if old_alpha.shape != new_alpha.shape:
                raise ValueError(f"HUD native dimensions changed: {old_alpha.shape} -> {new_alpha.shape}")
            hud = {**identity, "size": list(new_alpha.shape[::-1]), "alphaThreshold": 16,
                   "absoluteAlphaBounds": helper.bbox(new_alpha >= 16),
                   "alphaExtrema": [int(new_alpha.min()), int(new_alpha.max())],
                   "runtimePath": str((FLAT / "hero-head-face-v3.png").resolve()),
                   "runtimeResource": "flat2d/hero-head-face-v3", "retainedRuntimeCrop": inventory["hud"]["crop"],
                   "pixelEditsAfterGeneration": False}
        except (ValueError, OSError, KeyError) as error:
            errors.append(f"HUD: {error}")
    # A candidate is always a frozen-baseline deepcopy, never an installer-built
    # subset. Unselected pilot actions remain byte-for-byte equivalent as data.
    candidate = copy.deepcopy(baseline)
    run_records = []
    for key, original in baseline["actions"].items():
        try:
            candidate["actions"][key] = adapt_action(key, original, sheets, baseline["directions"], issues, run_records)
        except (ValueError, KeyError, IndexError) as error:
            errors.append(f"{key}: {error}")
    if baseline["image"] in sheets:
        idle = candidate["actions"]["idle"]
        for field in ("image", "perFrameOrigins", "alphaBounds"):
            candidate[field] = copy.deepcopy(idle[field])
    candidate["revision"] = "concept-image-2d-face-v1-pilot" if args.pilot else "concept-image-2d-face-v1"
    candidate.update(identity_fields)
    installed_actions = [key for key, action in baseline["actions"].items() if any(image in sheets for image in action_images(action))]
    report = {"version": "face-blend-v1", "createdAtUTC": datetime.now(timezone.utc).isoformat(),
              "status": "measured; not installed", "mode": "pilot" if args.pilot else "full",
              "baselineManifestPath": str(BASELINE), "baselineManifestSHA256": EXPECTED_BASELINE_SHA,
              "baselineActionCount": 88, "baselineUniquePNGCount": 68,
              "measuredPNGCount": len(sheets), "selectedPNGCount": len(selected), "adaptedActionKeys": installed_actions,
              "missingInputs": missing, "errors": errors, "installationIssues": issues,
              "images": sheets, "hud": hud, "runGroundTransfers": run_records,
              "identityReferences": copy.deepcopy(identity_fields),
              "candidateManifest": candidate, "fullPathSHA256s": hashes,
              "pixelEditsAfterGeneration": False,
              "dependencies": "Existing Pillow/numpy/scipy via weapon-carry-v1 read-only helpers; no new dependency.",
              "limitations": ["Lower-body alpha translation does not assess identity, expression, pose, rotation or scale; visual review remains required.",
                              "HUD PNG copied only; runtime HUD resource reference is maintained separately.",
                              "Old PNGs and immutable baseline are retained; no automatic deletion, archive or Cocos build."]}
    if missing:
        errors.append(f"Selected inputs incomplete: {len(missing)} missing; full mode requires all 68 PNGs plus HUD")
    protected = set(hashes) | {str(args.manifest.resolve())} | {str(BASELINE), str(INVENTORY)}
    protected.update(sheet["runtimePath"] for sheet in sheets.values())
    if hud:
        protected.add(hud["runtimePath"])
    if args.report and str(args.report) in protected:
        raise ValueError("Report destination overlaps an input/runtime manifest")
    if args.install and (errors or issues or len(sheets) != len(selected) or hud is None):
        errors.append("Installation refused: selected source/measurement/registration requirements are not satisfied")
    elif args.install:
        install_measured(args, candidate, report, hashes, baseline, sheets, hud,
                         baseline_bytes, inventory_bytes)
        if args.report and str(args.report) == report["installationRecordPath"]:
            args.report = None
    if BASELINE.read_bytes() != baseline_bytes or INVENTORY.read_bytes() != inventory_bytes:
        raise ValueError("Frozen baseline/inventory changed during execution")
    if args.report:
        write_json(args.report, report)
    print(json.dumps({"status": report["status"], "mode": report["mode"],
                      "measuredPNGCount": len(sheets), "baselineActionCount": 88,
                      "baselineUniquePNGCount": 68, "adaptedActionKeys": installed_actions,
                      "oldCropsRetained": sum(s["frozenCropRejection"] is None for s in sheets.values()),
                      "minLowerBodyIoU": min((reg["lowerBodyMaskIoU"] for sheet in sheets.values() for reg in sheet["registrations"]), default=None),
                      "errors": errors, "installationIssues": issues, "missingInputs": missing,
                      "reportPath": str(args.report) if args.report else report.get("installationRecordPath")}, ensure_ascii=False, indent=2))
    return 1 if errors or issues else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, IndexError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
