"""Measure explicitly selected native run atlases; runtime writes require --install.

selection.json schema (relative input paths: selection directory, then repo):
  expectedManifestSHA256: the pinned baseline SHA below
  bodyProportionAccepted: true, strideAccepted: true
  images: {explore-a/explore-b/held-a/held-b: {
    sourcePath: path, rawOutputPath: path, sha256: native-byte SHA256,
    frameRects: optional 16 reviewed absolute [x,y,width,height] rectangles}}
  geometry: {explore/held: {worldUnitsPerPixel: positive finite number,
    origins: {down/right/up/left: eight absolute atlas [x,y] points}}}
  sourceDesign: optional {path: path, sha256: SHA256}

Every atlas is native RGBA 1024x1536, 4 columns x 4 directions. Origins are
ordered A0,A1,A2,A3,B0,B1,B2,B3, may lie outside a crop (flight), and are
authored from the selected new body rather than transferred old registration.
Default output is candidate-report.json beside this script. No PNG pixels are
edited. Existing Pillow/NumPy/SciPy and weapon-carry-v1/native_geometry are used.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ACTOR = ROOT / "src/cocos/assets/resources/flat2d/characters/raphael"
MANIFEST = ACTOR / "manifest.json"
BASELINE_SHA = "e1641ddd0083a8088284dceba297d6f2f14d987de31df8c746eae7922218fd9e"
DIRECTIONS = ["down", "right", "up", "left"]
DESTINATIONS = {
    "explore-a": "face-v1/carry-v1/explore-W01-run-a.png",
    "explore-b": "face-v1/carry-v1/explore-W01-run-b.png",
    "held-a": "face-v1/hero-v6/hero-v4-run-readable-a.png",
    "held-b": "face-v1/hero-v6/hero-v4-run-readable-b.png",
}
ACTION_KEYS = {"explore_run_W01", "run_W01", "run"}
ORIGIN_METHOD = (
    "New reference-run body scale and absolute support/pelvis origins explicitly "
    "authored for these native A/B atlases; complete alpha>=16 crops; flight "
    "origins retained outside crops; unchanged native PNG bytes."
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf8")


def display(path):
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def resolve_input(value, directory):
    if not isinstance(value, str) or not value:
        raise ValueError("Input path must be a nonempty string")
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return next((p.resolve() for p in (directory / path, ROOT / path) if p.exists()),
                (directory / path).resolve())


def check_hash(path, expected):
    if not isinstance(expected, str) or len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError(f"Expected lowercase SHA256 for {path}")
    if sha(path) != expected:
        raise ValueError(f"SHA256 mismatch: {path}")


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def measurement_helper():
    # Do not create __pycache__ beside the existing helper when importing it.
    sys.dont_write_bytecode = True
    path = HERE.parent / "weapon-carry-v1/measure-install.py"
    spec = importlib.util.spec_from_file_location("existing_carry_measurement", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def measure(selection, directory, helper):
    if selection.get("expectedManifestSHA256") != BASELINE_SHA:
        raise ValueError("expectedManifestSHA256 must equal the pinned reviewed baseline")
    if any(selection.get(k) is not True for k in ("bodyProportionAccepted", "strideAccepted")):
        raise ValueError("bodyProportionAccepted:true and strideAccepted:true require visual review")
    images = selection.get("images", {})
    if set(images) != set(DESTINATIONS):
        raise ValueError("images must contain exactly explore-a, explore-b, held-a, held-b")
    geometry = selection.get("geometry", {})
    if set(geometry) != {"explore", "held"}:
        raise ValueError("geometry must contain exactly explore and held")
    for family, data in geometry.items():
        upp = data.get("worldUnitsPerPixel")
        if not finite_number(upp) or upp <= 0:
            raise ValueError(f"Finite positive worldUnitsPerPixel required: {family}")
        origins = data.get("origins", {})
        if set(origins) != set(DIRECTIONS):
            raise ValueError(f"Authored origins required for all four directions: {family}")
        for direction, points in origins.items():
            if not isinstance(points, list) or len(points) != 8 or any(
                not isinstance(p, list) or len(p) != 2 or not all(finite_number(v) for v in p)
                for p in points
            ):
                raise ValueError(f"Eight finite absolute origin points required: {family}/{direction}")
    sheets = {}
    inputs = {}
    for key, destination in DESTINATIONS.items():
        record = images[key]
        source = resolve_input(record.get("sourcePath"), directory)
        raw = resolve_input(record.get("rawOutputPath"), directory)
        expected = record.get("sha256")
        check_hash(source, expected)
        check_hash(raw, expected)
        for path in (source, raw):
            if path == MANIFEST or path.is_relative_to(ACTOR):
                raise ValueError(f"Selected native source must be outside runtime resources: {path}")
            inputs[path] = expected
        explicit = record.get("frameRects")
        if explicit is not None and (
            not isinstance(explicit, list) or len(explicit) != 16 or any(
                not isinstance(r, list) or len(r) != 4 or any(type(v) is not int for v in r)
                for r in explicit
            )
        ):
            raise ValueError(f"frameRects must be 16 integer [x,y,width,height] rectangles: {key}")
        with helper.Image.open(source) as image:
            if image.format != "PNG":
                raise ValueError(f"Native PNG bytes required: {source}")
        native_alpha = helper.alpha(source)
        if native_alpha.shape != (1536, 1024):
            raise ValueError(f"Native 1024x1536 required: {key}, got {native_alpha.shape[::-1]}")
        measured = helper.native_geometry(native_alpha, [4, 4], explicit)
        if measured["edgeAlphaPixelCount"]:
            raise ValueError(f"Alpha touches native atlas edge; review/regenerate clipped source: {key}")
        # Recheck global exact ownership even for explicit reviewed rectangles.
        covered = helper.np.zeros(native_alpha.shape, dtype=helper.np.uint8)
        for x, y, width, height in measured["rects"]:
            covered[y:y+height, x:x+width] += native_alpha[y:y+height, x:x+width] >= 16
        if helper.np.any((native_alpha >= 16) & (covered != 1)):
            raise ValueError(f"Every alpha>=16 pixel must belong to exactly one complete crop: {key}")
        measured.update({"sourcePNG": display(source), "sourceSHA256": expected,
                         "rawOutputPNG": display(raw), "rawSHA256": expected,
                         "runtimePNG": destination, "rawSourceSHAEqual": True,
                         "pixelEditsAfterGeneration": False})
        sheets[key] = measured
    design = selection.get("sourceDesign")
    if design is not None:
        path = resolve_input(design.get("path"), directory)
        check_hash(path, design.get("sha256"))
        inputs[path] = design["sha256"]
        design = {"path": display(path), "sha256": design["sha256"]}
    return sheets, inputs, design


def make_action(original, family, sheets, geometry, design):
    a, b = [sheets[f"{family}-{suffix}"] for suffix in ("a", "b")]
    action = copy.deepcopy(original)
    action.update({"image": a["runtimePNG"],
                   "frameImages": [a["runtimePNG"]]*4 + [b["runtimePNG"]]*4,
                   "perFrameRects": copy.deepcopy(a["rects"]),
                   "frameRectsByImage": {s["runtimePNG"].removesuffix(".png"): copy.deepcopy(s["rects"]) for s in (a, b)},
                   "alphaBounds": copy.deepcopy(a["alphaBounds"]),
                   "alphaBoundsThreshold": 16, "perFrameOrigins": {}, "perPhaseAlphaBounds": {},
                   "worldUnitsPerPixel": geometry["worldUnitsPerPixel"],
                   "originMethod": ORIGIN_METHOD})
    for row, direction in enumerate(DIRECTIONS):
        points, bounds = [], []
        for phase, absolute in enumerate(geometry["origins"][direction]):
            sheet = a if phase < 4 else b
            index = row * 4 + phase % 4
            x, y, _, _ = sheet["rects"][index]
            points.append([absolute[0]-x, absolute[1]-y])
            bounds.append(copy.deepcopy(sheet["alphaBounds"][index]))
        action["perFrameOrigins"][direction] = points
        action["perPhaseAlphaBounds"][direction] = bounds
    for name in ("sourcePNG", "sourcePNGSHA256", "sourcePNGs", "sourcePNGSHA256s",
                 "sourceDesign", "sourceDesignSHA256"):
        action.pop(name, None)
    action["sourcePNGs"] = [s["sourcePNG"] for s in (a, b)]
    action["sourcePNGSHA256s"] = [s["sourceSHA256"] for s in (a, b)]
    action["rawOutputPNGs"] = [s["rawOutputPNG"] for s in (a, b)]
    action["rawOutputPNGSHA256s"] = [s["rawSHA256"] for s in (a, b)]
    if design:
        action.update({"sourceDesign": design["path"], "sourceDesignSHA256": design["sha256"]})
    return action


def candidate_manifest(manifest, sheets, selection, design):
    if manifest.get("directions") != DIRECTIONS or len(manifest["actions"]) != 88:
        raise ValueError("Expected 88 baseline actions and down/right/up/left directions")
    actions = manifest["actions"]
    if actions["run"] != actions["run_W01"]:
        raise ValueError("Baseline held run aliases differ")
    for key in ACTION_KEYS:
        action = actions[key]
        if (action.get("frames"), action.get("fps"), action.get("frameIndices"), action.get("columns")) != (8, 14, [0, 1, 2, 3, 0, 1, 2, 3], 4):
            raise ValueError(f"Unexpected baseline run timing/layout: {key}")
    result = copy.deepcopy(manifest)
    result["actions"]["explore_run_W01"] = make_action(actions["explore_run_W01"], "explore", sheets, selection["geometry"]["explore"], design)
    result["actions"]["run_W01"] = make_action(actions["run_W01"], "held", sheets, selection["geometry"]["held"], design)
    result["actions"]["run"] = copy.deepcopy(result["actions"]["run_W01"])
    if {k: v for k, v in result.items() if k != "actions"} != {k: v for k, v in manifest.items() if k != "actions"}:
        raise ValueError("Root manifest fields changed")
    if set(result["actions"]) != set(actions) or any(result["actions"][k] != actions[k] for k in actions.keys() - ACTION_KEYS):
        raise ValueError("An action outside the three allowed run keys changed")
    # Preserve all unmodified fields, including every optional timing field.
    mutable = {"image", "frameImages", "perFrameRects", "frameRectsByImage", "alphaBounds", "alphaBoundsThreshold",
               "perFrameOrigins", "perPhaseAlphaBounds", "worldUnitsPerPixel", "originMethod", "sourcePNG",
               "sourcePNGSHA256", "sourcePNGs", "sourcePNGSHA256s", "sourceDesign", "sourceDesignSHA256",
               "rawOutputPNGs", "rawOutputPNGSHA256s"}
    for key in ACTION_KEYS:
        if {k: v for k, v in actions[key].items() if k not in mutable} != {k: v for k, v in result["actions"][key].items() if k not in mutable}:
            raise ValueError(f"Non-geometry/timing field changed: {key}")
    return result


def install(candidate, sheets, manifest_bytes, input_hashes, selection_path, selection_sha, runtime_hashes, meta_hashes):
    # Unique transaction directories are never removed: backups remain inspectable.
    transaction = Path(tempfile.mkdtemp(prefix="install-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-"), dir=HERE))
    backups, staged = transaction / "backups", transaction / "staged"
    backups.mkdir()
    staged.mkdir()
    operations = []
    for key, relative in DESTINATIONS.items():
        destination = ACTOR / relative
        backup, stage = backups / (key + ".png"), staged / (key + ".png")
        before = runtime_hashes[destination]
        check_hash(destination, before)
        shutil.copyfile(destination, backup)
        check_hash(backup, before)
        shutil.copyfile(resolve_input(sheets[key]["sourcePNG"], ROOT), stage)
        check_hash(stage, sheets[key]["sourceSHA256"])
        operations.append({"destination": destination, "backup": backup, "stage": stage,
                           "before": before, "after": sheets[key]["sourceSHA256"]})
    backup, stage = backups / "manifest.json", staged / "manifest.json"
    backup.write_bytes(manifest_bytes)
    stage.write_bytes(encoded(candidate))
    operations.append({"destination": MANIFEST, "backup": backup, "stage": stage,
                       "before": BASELINE_SHA, "after": sha(stage)})
    record = {"operations": [{k: display(v) if isinstance(v, Path) else v for k, v in op.items()} for op in operations],
              "retainedMetaSHA256s": {display(p): digest for p, digest in meta_hashes.items()}}
    (transaction / "transaction.json").write_bytes(encoded(record))
    written = []
    try:
        check_hash(selection_path, selection_sha)
        for path, digest in input_hashes.items():
            check_hash(path, digest)
        for path, digest in meta_hashes.items():
            check_hash(path, digest)
        for op in operations:
            check_hash(op["destination"], op["before"])
        for op in operations:
            check_hash(op["destination"], op["before"])
            # Concurrent manifest writes during PNG installation abort the transaction.
            check_hash(MANIFEST, BASELINE_SHA)
            os.replace(op["stage"], op["destination"])
            written.append(op)
            check_hash(op["destination"], op["after"])
        for path, digest in meta_hashes.items():
            check_hash(path, digest)
        record["status"] = "installed"
        (transaction / "transaction.json").write_bytes(encoded(record))
    except Exception as error:
        rollback_errors = []
        for op in reversed(written):
            try:
                # Never overwrite unknown concurrent bytes, including on rollback.
                check_hash(op["destination"], op["after"])
                check_hash(op["backup"], op["before"])
                recovery = transaction / ("restore-" + op["backup"].name)
                shutil.copyfile(op["backup"], recovery)
                os.replace(recovery, op["destination"])
                check_hash(op["destination"], op["before"])
            except Exception as rollback_error:
                rollback_errors.append(str(rollback_error))
        record.update({"status": "rolled back" if not rollback_errors else "rollback needs review",
                       "error": str(error), "rollbackErrors": rollback_errors})
        (transaction / "transaction.json").write_bytes(encoded(record))
        raise ValueError(f"Installation failed: {error}; backups: {transaction}; rollback errors: {rollback_errors}") from error
    return display(transaction)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--selection", type=Path, default=HERE / "selection.json")
    parser.add_argument("--report", type=Path, default=HERE / "candidate-report.json")
    parser.add_argument("--install", action="store_true", help="Stage and replace exactly four native PNGs plus the pinned runtime manifest, retaining rollback backups")
    args = parser.parse_args()
    selection_path, report_path = args.selection.resolve(), args.report.resolve()
    selection_bytes = selection_path.read_bytes()
    selection = json.loads(selection_bytes)
    selection_sha = hashlib.sha256(selection_bytes).hexdigest()
    manifest_bytes = MANIFEST.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != BASELINE_SHA:
        raise ValueError("Runtime manifest differs from pinned baseline; refusing stale candidate/install")
    runtime_hashes = {ACTOR / relative: sha(ACTOR / relative) for relative in DESTINATIONS.values()}
    meta_hashes = {Path(str(path) + ".meta"): sha(Path(str(path) + ".meta"))
                   for path in runtime_hashes if Path(str(path) + ".meta").exists()}
    helper = measurement_helper()
    sheets, inputs, design = measure(selection, selection_path.parent, helper)
    if report_path in (selection_path, Path(__file__).resolve()) or report_path in inputs or report_path.is_relative_to(ACTOR):
        raise ValueError("Report must not overwrite selection, native inputs or runtime resources")
    candidate = candidate_manifest(json.loads(manifest_bytes), sheets, selection, design)
    report = {"status": "measured; not installed", "manifestInputSHA256": BASELINE_SHA,
              "selectionPath": display(selection_path), "selectionSHA256": selection_sha,
              "changedActionKeys": sorted(ACTION_KEYS), "preservedActionCount": 85,
              "bodyProportionAccepted": True, "strideAccepted": True,
              "pixelEditsAfterGeneration": False, "sheets": sheets,
              "runtimeInputSHA256s": {display(p): digest for p, digest in runtime_hashes.items()},
              "authoredGeometry": selection["geometry"], "candidateManifest": candidate,
              "candidateManifestSHA256": hashlib.sha256(encoded(candidate)).hexdigest()}
    if args.install:
        report["backupDirectory"] = install(candidate, sheets, manifest_bytes, inputs, selection_path, selection_sha, runtime_hashes, meta_hashes)
        report["status"] = "installed unchanged native PNGs and three run action records"
        report["manifestOutputSHA256"] = sha(MANIFEST)
    elif MANIFEST.read_bytes() != manifest_bytes:
        raise ValueError("Runtime manifest changed during read-only measurement; rerun")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(encoded(report))
    print(json.dumps({k: v for k, v in report.items() if k not in ("sheets", "authoredGeometry", "candidateManifest")}, ensure_ascii=False, indent=2))
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
