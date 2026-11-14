"""Measure four native W01 locomotion sheets; only --install writes runtime.

selection.json is {"images": {"explore-idle": {...}, "explore-walk": {...},
"held-idle": {...}, "held-walk": {...}}}; direct image keys also work.
Each entry supplies sourcePath, rawOutputPath, sha256, pixelEdits:false,
layout:[2,2] for idle / [4,4] for walk, worldUnitsPerPixel, and origins:
absolute atlas XY foot anchors in reading order. Optional frameRects require
semanticCropReview. Installation additionally requires bodyProportionAccepted,
poseReviewAccepted, calibrationAccepted all true and a nonempty visualReview.
Those are explicit visual-review attestations, never inferred from alpha geometry.

Reuses existing read-only alpha/native_geometry and semantic-crop helpers.
PNG bytes are copied, never repainted or reencoded. All runs stay untouched.
Relative input/report paths resolve against this script's directory.
"""
from __future__ import annotations

import argparse
import copy
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ACTOR = ROOT / "src/cocos/assets/resources/flat2d/characters/raphael"
MANIFEST = ACTOR / "manifest.json"
BASELINE = HERE / "baseline-manifest.json"
BASELINE_SHA = "e1e1d5bdde78dff15892acecbd1c460551855a776cc60f7441a125eb1e772541"
SPECS = {
    "explore-idle": ("locomotion-v1/W01-explore-idle.png", [2, 2], ["explore_idle_W01"]),
    "explore-walk": ("locomotion-v1/W01-explore-walk.png", [4, 4], ["explore_walk_W01"]),
    "held-idle": ("locomotion-v1/W01-held-idle.png", [2, 2], ["idle", "idle_W01"]),
    "held-walk": ("locomotion-v1/W01-held-walk.png", [4, 4], ["walk", "walk_W01"]),
}
CHANGED = {key for _, _, keys in SPECS.values() for key in keys}
STALE = {"image", "frameImages", "frameRectsByImage", "perFrameRects", "perFrameOrigins",
         "alphaBounds", "perPhaseAlphaBounds", "origin", "directionFrameIndices", "row",
         "absoluteFrameIndices", "sourcePNG", "sourcePNGSHA256", "sourcePNGs",
         "sourcePNGSHA256s", "rawOutputPNGs", "rawOutputPNGSHA256s", "identityReference",
         "identityReferenceSHA256", "identityReferenceScope", "sourceDesign", "sourceDesignSHA256"}


def path(value):
    p = Path(value)
    return (p if p.is_absolute() else HERE / p).resolve()


def number(value):
    return type(value) in (float, int) and math.isfinite(value)


def module(name, filename):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def install(candidate, sheets, hashes, report, common,
            status="installed four native PNGs and six bounded action records"):
    """Stage/check all writes; rollback only destinations still holding our bytes."""
    folder = Path(tempfile.mkdtemp(prefix="locomotion-install-", dir=HERE))
    entries, replaced = [], []
    for index, sheet in enumerate(sheets.values()):
        source, destination = Path(sheet["sourcePath"]), Path(sheet["runtimePath"])
        staged, backup = folder / f"new-{index}.png", folder / f"before-{index}.png"
        shutil.copyfile(source, staged)
        common.check(staged, sheet["sourceSHA256"])
        before = hashes[str(destination)]
        common.check(destination, before)
        if before is not None:
            shutil.copyfile(destination, backup)
            common.check(backup, before)
        entries.append(dict(destination=destination, staged=staged, backup=backup,
                            before=before, after=sheet["sourceSHA256"]))
    staged, backup = folder / "new-manifest.json", folder / "before-manifest.json"
    staged.write_bytes(common.data_bytes(candidate))
    shutil.copyfile(MANIFEST, backup)
    common.check(backup, BASELINE_SHA)
    entries.append(dict(destination=MANIFEST, staged=staged, backup=backup,
                        before=BASELINE_SHA, after=common.sha(staged)))
    transaction = {"status": "staged", "entries": [
        {k: str(v) if isinstance(v, Path) else v for k, v in entry.items()} for entry in entries]}
    record = folder / "transaction.json"
    record.write_bytes(common.data_bytes(transaction))
    created = []
    try:
        for filename, digest in hashes.items():
            common.check(filename, digest)
        for entry in entries:
            common.check(entry["destination"], entry["before"])
            common.check(MANIFEST, BASELINE_SHA)  # manifest is always replaced last
            common.check(entry["staged"], entry["after"])
            parent = entry["destination"].parent
            if not parent.exists():
                parent.mkdir(parents=True)
                created.append(parent)
            os.replace(entry["staged"], entry["destination"])
            replaced.append(entry)
            common.check(entry["destination"], entry["after"])
        written = {str(entry["destination"]) for entry in entries}
        for filename, digest in hashes.items():
            # The official importer may create missing .meta files; never touch them.
            if filename not in written and not (filename.endswith(".meta") and digest is None):
                common.check(filename, digest)
        for entry in entries:
            common.check(entry["destination"], entry["after"])
        transaction["status"] = "installed"
        record.write_bytes(common.data_bytes(transaction))
    except Exception as error:
        notes = []
        for entry in reversed(replaced):
            try:
                common.check(entry["destination"], entry["after"])
                if entry["before"] is None:
                    entry["destination"].unlink()
                else:
                    common.check(entry["backup"], entry["before"])
                    recovery = folder / ("restore-" + entry["backup"].name)
                    shutil.copyfile(entry["backup"], recovery)
                    os.replace(recovery, entry["destination"])
                common.check(entry["destination"], entry["before"])
            except Exception as rollback_error:
                notes.append(str(rollback_error))
        for directory in reversed(created):
            if directory.exists() and not any(directory.iterdir()):
                directory.rmdir()
        transaction.update(status="rollback needs review" if notes else "rolled back",
                           error=str(error), rollbackNotes=notes)
        record.write_bytes(common.data_bytes(transaction))
        raise ValueError(f"Installation failed: {error}; backups: {folder}; rollback: {notes}") from error
    report.update(status=status,
                  backupDirectory=str(folder), manifestOutputSHA256=common.sha(MANIFEST))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--selection", type=path, default=HERE / "selection.json")
    parser.add_argument("--report", type=path, default=HERE / "measurement-report.json")
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()
    common_path = HERE.parent / "identity-reference-v1/install-identity.py"
    face_path = HERE.parent / "face-blend-v1/install-face-runtime.py"
    helper_path = HERE.parent / "weapon-carry-v1/measure-install.py"
    common = module("locomotion_common", common_path)
    face = module("locomotion_face", face_path)
    helper = module("locomotion_alpha", helper_path)
    hashes = {}
    for filename in (BASELINE, MANIFEST):
        common.check(filename, BASELINE_SHA)
        common.snapshot(filename, hashes)
    for filename in (Path(__file__), common_path, face_path, helper_path, args.selection):
        common.snapshot(filename, hashes)
    baseline = face.read_json(BASELINE)
    if len(baseline["actions"]) != 88 or baseline["directions"] != ["down", "right", "up", "left"]:
        raise ValueError("Expected frozen 88-action/four-direction baseline")
    # Protect every currently referenced PNG, not just the four run authorities.
    for action in baseline["actions"].values():
        for image in face.action_images(action):
            filename = ACTOR / face.safe_image(image)
            if not filename.is_file():
                raise ValueError(f"Missing baseline runtime PNG: {filename}")
            common.snapshot(filename, hashes)
            common.snapshot(Path(str(filename) + ".meta"), hashes)
    authority = {"manifestSHA256": BASELINE_SHA, "actions": ["explore_run_W01", "run_W01"], "images": {}}
    for key in authority["actions"]:
        action = baseline["actions"][key]
        for image, digest in zip(face.action_images(action), action["sourcePNGSHA256s"]):
            common.check(ACTOR / image, digest)
            authority["images"][image] = digest
    if len(authority["images"]) != 4:
        raise ValueError("Expected four immutable W01 run authorities")
    selection = face.read_json(args.selection) if args.selection.is_file() else {}
    selected = selection.get("images", selection)
    if set(selected) - set(SPECS):
        raise ValueError("Unknown selection key; only four W01 locomotion sheets allowed")
    candidate, sheets, errors, issues, missing = copy.deepcopy(baseline), {}, [], [], []
    for key, (destination, layout, actions) in SPECS.items():
        runtime = (ACTOR / destination).resolve()
        common.snapshot(runtime, hashes)
        common.snapshot(Path(str(runtime) + ".meta"), hashes)
        if key not in selected:
            missing.append(key)
            continue
        try:
            record = selected[key]
            source, raw = path(record["sourcePath"]), path(record["rawOutputPath"])
            if source.is_relative_to(ACTOR) or raw.is_relative_to(ACTOR):
                raise ValueError("Native source/raw output must stay outside runtime")
            for filename in (source, raw):
                common.check(filename, record["sha256"])
                common.snapshot(filename, hashes)
            if record.get("pixelEdits") is not False:
                issues.append(f"{key}: explicit pixelEdits:false required")
            if record.get("layout") != layout:
                raise ValueError(f"Expected native layout {layout}")
            upp = record["worldUnitsPerPixel"]
            if not number(upp) or upp <= 0:
                raise ValueError("Reviewed worldUnitsPerPixel must be finite and positive")
            origins = record["origins"]
            if len(origins) != layout[0] * layout[1] or any(
                    not isinstance(p, list) or len(p) != 2 or not all(number(v) for v in p) for p in origins):
                raise ValueError("origins must contain one finite absolute XY per native cell")
            with helper.Image.open(source) as image:
                if image.format != "PNG":
                    raise ValueError("Native PNG bytes required")
            alpha = helper.alpha(source)
            if record.get("frameRects") is not None:
                if not isinstance(record.get("semanticCropReview"), str) or not record["semanticCropReview"].strip():
                    raise ValueError("Explicit frameRects need a nonempty semanticCropReview")
                geometry = face.reviewed_semantic_geometry(alpha, layout, record["frameRects"], record["semanticCropReview"], helper)
                covered = helper.np.zeros(alpha.shape, dtype=helper.np.uint16)
                for x, y, w, h in geometry["rects"]:
                    covered[y:y+h, x:x+w] += 1
                if helper.np.any((alpha >= 16) & (covered != 1)):
                    raise ValueError("Semantic crops must cover every alpha>=16 pixel exactly once")
            else:
                geometry = helper.native_geometry(alpha, layout)
            width, height = geometry["size"]
            if width % layout[0] or height % layout[1]:
                raise ValueError("Native atlas dimensions must divide the declared grid")
            for flag in ("bodyProportionAccepted", "poseReviewAccepted", "calibrationAccepted"):
                if record.get(flag) is not True:
                    issues.append(f"{key}: {flag}:true required after visual review")
            if not isinstance(record.get("visualReview"), str) or not record["visualReview"].strip():
                issues.append(f"{key}: nonempty visualReview required")
            local = [[point[0] - rect[0], point[1] - rect[1]] for point, rect in zip(origins, geometry["rects"])]
            for index, (point, rect) in enumerate(zip(origins, geometry["rects"])):
                if not (rect[0] <= point[0] <= rect[0]+rect[2] and rect[1] <= point[1] <= rect[1]+rect[3]+16):
                    raise ValueError(f"Foot anchor outside its reviewed crop: {index}")
            if hashes[str(runtime)] not in (None, record["sha256"]):
                raise ValueError("New runtime destination contains unknown bytes")
            geometry.update(sourcePath=str(source), rawOutputPath=str(raw), runtimePath=str(runtime),
                            sourceSHA256=record["sha256"], rawSourceSHAEqual=True,
                            worldUnitsPerPixel=upp, originsAbsolute=origins, originsLocal=local,
                            visualReview=record.get("visualReview"), generationRecord=copy.deepcopy(record))
            sheets[key] = geometry
            for action_key in actions:
                original = baseline["actions"][action_key]
                idle = layout == [2, 2]
                timing = tuple(original.get(field) for field in ("frames", "fps", "frameIndices", "loop"))
                if timing != ((1, 1, [0], True) if idle else (4, 7, [0, 1, 2, 3], True)):
                    raise ValueError(f"Unexpected baseline temporal values: {action_key}")
                action = {k: copy.deepcopy(v) for k, v in original.items() if k not in STALE}
                action.update(image=destination, columns=layout[0], frameWidth=width//layout[0],
                              frameHeight=height//layout[1], perFrameRects=geometry["rects"],
                              perFrameOrigins=local, alphaBounds=geometry["alphaBounds"],
                              alphaBoundsThreshold=16, worldUnitsPerPixel=upp,
                              sourcePNGs=[str(source)], sourcePNGSHA256s=[record["sha256"]],
                              rawOutputPNGs=[str(raw)], rawOutputPNGSHA256s=[record["sha256"]],
                              identityRunAuthority=copy.deepcopy(authority),
                              originMethod="Reviewed absolute native foot anchors converted to complete-alpha crop coordinates; UPP calibrated to current W01 run; native PNG bytes unchanged.")
                if idle:
                    action["directionFrameIndices"] = [0, 1, 2, 3]
                candidate["actions"][action_key] = action
        except (ValueError, OSError, KeyError, IndexError, TypeError) as error:
            errors.append(f"{key}: {error}")
    if "held-idle" in sheets:
        held = sheets["held-idle"]
        width, height = held["size"]
        cell_w, cell_h = width//2, height//2
        root_origins, root_bounds = [], []
        for index, (origin, rect, bounds) in enumerate(zip(held["originsAbsolute"], held["rects"], held["alphaBounds"])):
            gx, gy = index % 2 * cell_w, index // 2 * cell_h
            b = [bounds[0]+rect[0]-gx, bounds[1]+rect[1]-gy, bounds[2]+rect[0]-gx, bounds[3]+rect[1]-gy]
            if not (0 <= b[0] < b[2] <= cell_w and 0 <= b[1] < b[3] <= cell_h):
                errors.append(f"held-idle: root fallback grid clips frame {index}")
            root_bounds.append(b)
            root_origins.append([origin[0]-gx, origin[1]-gy])
        candidate.update(image=SPECS["held-idle"][0], columns=2, frameWidth=cell_w, frameHeight=cell_h,
                         origin=root_origins[0], perFrameOrigins=root_origins, alphaBounds=root_bounds)
        candidate.setdefault("camera", {})["worldUnitsPerPixel"] = held["worldUnitsPerPixel"]
    unchanged = [key for key in baseline["actions"] if key not in CHANGED]
    if len(unchanged) != 82 or set(candidate["actions"]) != set(baseline["actions"]):
        raise ValueError("Action coverage changed")
    for key in unchanged:
        if candidate["actions"][key] != baseline["actions"][key]:
            raise ValueError(f"Protected action changed: {key}")
    root_mutable = {"actions", "image", "columns", "frameWidth", "frameHeight", "origin", "perFrameOrigins", "alphaBounds", "camera"}
    if {k:v for k,v in candidate.items() if k not in root_mutable} != {k:v for k,v in baseline.items() if k not in root_mutable}:
        raise ValueError("Unrelated manifest root fields changed")
    if {k:v for k,v in candidate.get("camera", {}).items() if k != "worldUnitsPerPixel"} != {k:v for k,v in baseline.get("camera", {}).items() if k != "worldUnitsPerPixel"}:
        raise ValueError("Unrelated camera fields changed")
    report = dict(status="measured; not installed", baselineManifestSHA256=BASELINE_SHA,
                  measuredPNGCount=len(sheets), baselineActionCount=88, changedActionKeys=sorted(CHANGED),
                  protectedActionKeys=unchanged,
                  protectedRunActionKeys=[key for key in unchanged if key.startswith(("run", "explore_run"))],
                  identityRunAuthority=authority, images=sheets,
                  missingInputs=missing, errors=errors, installationIssues=issues,
                  candidateManifest=candidate, fullPathSHA256s=hashes, pixelEditsAfterGeneration=False)
    report_path = args.report.resolve()
    if str(report_path) in hashes or report_path.is_relative_to(ACTOR):
        raise ValueError("Report overlaps protected input/runtime")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(common.data_bytes(report))
    if args.install:
        if errors or issues or missing or set(sheets) != set(SPECS):
            errors.append("Installation refused: all four native sheets, visual reviews and 88-action coverage must validate")
        else:
            install(candidate, sheets, hashes, report, common)
    if not report["status"].startswith("installed"):
        for filename, digest in hashes.items():
            common.check(filename, digest)
    report_path.write_bytes(common.data_bytes(report))
    print(common.data_bytes({k: report[k] for k in ("status", "measuredPNGCount", "missingInputs", "errors", "installationIssues")}).decode())
    print(f"Report: {report_path}")
    return 1 if errors or issues or missing else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, IndexError, TypeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
