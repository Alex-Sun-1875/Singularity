"""Thin identity profile for the frozen 5f / 88-action / 68-PNG native baseline.

Default measures available assets/{baseline image}; missing inputs are reported,
not installed. --images accepts a subset of complete baseline PNG paths. A/B
actions adapt only when both sheets are measured. Relative CLI paths use this
directory. --install requires all 68 sheets, strict provenance, accepted body
registration, and the exact original RGB HUD bytes. It never edits PNG pixels.

Adjacent *.provenance.json: {rawOutputPath, sha256, pixelEdits:false}.
Optional --records JSON: {images:{"face-v1/...png":{frameRects,
semanticCropReview, registrationRois, registrationOverrides,
registrationSearchMaxRadius:32|96, registrationAccepted:true,
registrationReview:"explicit visual review"}}}. Fields merge over adjacent
provenance. Documented reusedFrom inputs default to max radius96; other inputs
default to32. Max-radius uses the existing search, not a new matcher.
ROIs/overrides accept arrays or cell-indexed objects, as in the face adapter.
Acceptance is never invented: a supplied true flag also needs a review note.

Run anchors use each phase's measured XY translation (no median Y), retaining
baseline contact/flight, phase lookups and UPP. HUD copies the original design
1752x897 RGB PNG unchanged; ChapterGame directly samples [1250,0,502,502].
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ACTOR = ROOT / "src/cocos/assets/resources/flat2d/characters/raphael"
FLAT = ACTOR.parents[1]
MANIFEST = ACTOR / "manifest.json"
BASELINE = HERE / "baseline-manifest.json"
INVENTORY = HERE / "baseline-images.json"
BASELINE_SHA = "5f438265f874fc45785f0a596c1ba328f889bfc369c28f3480ab6af2e2f9240c"
DESIGN = HERE.parent / "appearance-v5/male-direction.png"
HUD = HERE / "hud-reference-source.png"
HUD_SHA = "4e9e8c3451c64a48554aaac4bcdc95745a92826206fdb72f4e8c1a151c2a45b6"
MASTER = HERE / "head-identity-master.png"
MASTER_SHA = "4d35d738d50e6451a099720f0bbec50448849dc71281ea9d9bec961450798c88"
HUD_RUNTIME = FLAT / "hero-head-design-reference.png"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def data_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf8")


def cli_path(value):
    path = Path(value)
    return (path if path.is_absolute() else HERE / path).resolve()


def load_module(name, path):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def current_hash(path):
    return sha(path) if path.is_file() else None


def check(path, digest):
    if current_hash(Path(path)) != digest:
        raise ValueError(f"SHA256/concurrent-state mismatch: {path}")


def snapshot(path, hashes):
    path = Path(path).resolve()
    hashes[str(path)] = current_hash(path)
    return hashes[str(path)]


def adapt(face, key, original, sheets, directions, phase_records):
    # Reuse all native crop/lookup/provenance adaptation. Replace only the
    # previous run median-ground policy with each phase's observed translation.
    action = face.adapt_action(key, original, sheets, directions, [], [])
    if isinstance(original["perFrameOrigins"], dict):
        origins = {}
        for row, direction in enumerate(directions):
            points, deltas = [], []
            for phase, image in enumerate(original["frameImages"]):
                sheet = sheets[image]
                index = face.runtime_index(original, row, phase)
                delta = sheet["registrations"][index]["bodyOnlyTranslationXY"]
                deltas.append(delta)
                points.append(face.transfer(original["perFrameOrigins"][direction][phase],
                                            sheet["oldRects"][index], sheet["rects"][index], delta))
            origins[direction] = points
            phase_records.append({"action": key, "direction": direction,
                                  "perPhaseMeasuredXY": deltas,
                                  "phaseYSpread": max(d[1] for d in deltas)-min(d[1] for d in deltas),
                                  "policy": "Each measured XY applied independently; baseline contact/flight retained, no median ground or new boot/head/weapon anchoring."})
        action["perFrameOrigins"] = origins
    action["originMethod"] = "Frozen 5f support anchors transferred by measured body-only XY for each native cell/phase; original UPP, contact/flight, timing and direction lookup retained; complete alpha>=16 crops; native bytes unchanged."
    action.update({"sourceDesign": DESIGN.relative_to(ROOT).as_posix(), "sourceDesignSHA256": HUD_SHA,
                   "identityReference": MASTER.relative_to(ROOT).as_posix(), "identityReferenceSHA256": MASTER_SHA,
                   "rawOutputPNGs": [sheets[image]["rawOutputPath"] for image in face.action_images(original)],
                   "rawOutputPNGSHA256s": [sheets[image]["sourceSHA256"] if sheets[image]["rawSourceSHAEqual"] else None for image in face.action_images(original)]})
    return action


def install(candidate, sheets, hud, hashes, report):
    """Stage every write, preserve backups, and roll back only our known bytes."""
    folder = Path(tempfile.mkdtemp(prefix="identity-install-", dir=HERE))
    entries, replaced = [], []
    files = [(Path(s["sourcePath"]), Path(s["runtimePath"])) for s in sheets.values()] + [(HUD, HUD_RUNTIME)]
    for index, (source, destination) in enumerate(files):
        staged, backup = folder / f"new-{index}.png", folder / f"before-{index}.png"
        shutil.copyfile(source, staged)
        check(staged, hashes[str(source.resolve())])
        before = hashes[str(destination.resolve())]
        check(destination, before)
        if before is not None:
            shutil.copyfile(destination, backup)
            check(backup, before)
        entries.append({"destination": destination, "staged": staged, "backup": backup,
                        "before": before, "after": sha(staged)})
    stage, backup = folder / "new-manifest.json", folder / "before-manifest.json"
    stage.write_bytes(data_bytes(candidate))
    shutil.copyfile(MANIFEST, backup)
    check(backup, BASELINE_SHA)
    entries.append({"destination": MANIFEST, "staged": stage, "backup": backup,
                    "before": BASELINE_SHA, "after": sha(stage)})
    transaction = {"status": "staged", "entries": [{k: str(v) if isinstance(v, Path) else v for k, v in entry.items()} for entry in entries]}
    transaction_path = folder / "transaction.json"
    transaction_path.write_bytes(data_bytes(transaction))
    try:
        for path, digest in hashes.items():
            check(path, digest)
        for entry in entries:
            check(entry["destination"], entry["before"])
            check(MANIFEST, BASELINE_SHA)
            check(entry["staged"], entry["after"])
            os.replace(entry["staged"], entry["destination"])
            replaced.append(entry)
            check(entry["destination"], entry["after"])
        # Existing native .meta files are never changed or replaced. Missing
        # HUD .meta may legitimately be created by the official Cocos importer.
        written_paths = {str(entry["destination"].resolve()) for entry in entries}
        for path, digest in hashes.items():
            if path in written_paths or (path.endswith(".meta") and digest is None):
                continue
            check(path, digest)
        # Recheck the complete final set: an earlier destination may have
        # changed externally while later files were being installed.
        for entry in entries:
            check(entry["destination"], entry["after"])
        transaction["status"] = "installed"
        transaction_path.write_bytes(data_bytes(transaction))
    except Exception as error:
        notes = []
        for entry in reversed(replaced):
            try:
                destination = entry["destination"]
                check(destination, entry["after"])
                if entry["before"] is None:
                    destination.unlink()
                else:
                    check(entry["backup"], entry["before"])
                    recovery = folder / ("restore-" + entry["backup"].name)
                    shutil.copyfile(entry["backup"], recovery)
                    os.replace(recovery, destination)
                    check(destination, entry["before"])
            except Exception as rollback_error:
                notes.append(str(rollback_error))
        transaction.update({"status": "rollback needs review" if notes else "rolled back", "error": str(error), "rollbackNotes": notes})
        transaction_path.write_bytes(data_bytes(transaction))
        raise ValueError(f"Installation failed: {error}; retained backups {folder}; rollback notes {notes}") from error
    report.update({"status": "installed 68 native atlases, original HUD and 88 action metadata records",
                   "backupDirectory": str(folder), "manifestOutputSHA256": sha(MANIFEST)})


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--assets", type=cli_path, default=HERE / "assets")
    parser.add_argument("--images", nargs="+", help="Exact baseline image paths to measure; no partial installation")
    parser.add_argument("--records", type=cli_path, action="append", help="Repeatable image-keyed provenance/visual-review records")
    parser.add_argument("--report", type=cli_path, default=HERE / "measurement-report.json")
    parser.add_argument("--install", action="store_true", help="Install only a complete, validated 68-image candidate and exact original HUD")
    args = parser.parse_args()
    face_path = HERE.parent / "face-blend-v1/install-face-runtime.py"
    helper_path = HERE.parent / "weapon-carry-v1/measure-install.py"
    face, helper = load_module("identity_face_adapter", face_path), load_module("identity_alpha_helper", helper_path)
    face.renamed = face.safe_image  # Existing runtime paths; never face-v1/face-v1.
    hashes = {}
    for path, expected in ((BASELINE, BASELINE_SHA), (MANIFEST, BASELINE_SHA), (DESIGN, HUD_SHA), (MASTER, MASTER_SHA), (HUD, HUD_SHA)):
        check(path, expected)
        snapshot(path, hashes)
    for path in (INVENTORY, face_path, helper_path, Path(__file__).resolve()):
        snapshot(path, hashes)
    baseline, inventory = face.read_json(BASELINE), face.read_json(INVENTORY)
    references = {}
    for key, action in baseline["actions"].items():
        for image in face.action_images(action):
            references.setdefault(face.safe_image(image), []).append((key, action))
    listed = {item["image"]: item for item in inventory["images"]}
    if (len(baseline["actions"]) != 88 or len(references) != 68 or set(listed) != set(references)
            or len(inventory["images"]) != 68 or inventory["manifestSHA256"] != BASELINE_SHA):
        raise ValueError("Frozen 88-action/68-PNG manifest and inventory disagree")
    for image, item in listed.items():
        path = ACTOR / image
        check(path, item["sha256"])
        snapshot(path, hashes)
        snapshot(Path(str(path) + ".meta"), hashes)
    if current_hash(HUD_RUNTIME) not in (None, HUD_SHA):
        raise ValueError("New HUD resource already contains unknown bytes; refusing to overwrite")
    snapshot(HUD_RUNTIME, hashes)
    snapshot(Path(str(HUD_RUNTIME) + ".meta"), hashes)
    old_hud = Path(inventory["hud"]["runtimePath"])
    check(old_hud, inventory["hud"]["sha256"])
    snapshot(old_hud, hashes)
    with helper.Image.open(HUD) as image:
        if image.format != "PNG" or image.mode != "RGB" or image.size != (1752, 897):
            raise ValueError("HUD must be the exact original 1752x897 RGB design PNG")
    records = {}
    for path in args.records or []:
        incoming = face.read_json(path)
        for image, entry in incoming.get("images", {}).items():
            if image not in references:
                raise ValueError(f"Unknown image review key: {image}")
            record = copy.deepcopy(entry)
            if record.get("rawOutputPath"):
                record["rawOutputPath"] = str(face.provenance_path(record["rawOutputPath"], path.parent))
            records.setdefault(image, {}).update(record)
        snapshot(path, hashes)
    selected = list(dict.fromkeys(args.images or sorted(references)))
    if any(image not in references for image in selected):
        raise ValueError("--images must contain exact baseline PNG paths")
    sheets, errors, issues, missing, findings = {}, [], [], [], []
    for image in selected:
        source = (args.assets / image).resolve()
        if not source.is_file():
            missing.append(image)
            continue
        try:
            if source.is_relative_to(ACTOR):
                raise ValueError("Source PNG must stay outside runtime resources")
            print(f"Measuring {image}", file=sys.stderr, flush=True)
            record, identity = face.load_provenance(source, records.get(image, {}), HERE, hashes)
            if record.get("editTargetSHA256") not in (None, listed[image]["sha256"]):
                raise ValueError("Head-edit target SHA does not match this frozen runtime image")
            if record.get("identityMasterSHA256") not in (None, MASTER_SHA):
                raise ValueError("Recorded head master SHA differs from the approved fixed master")
            with helper.Image.open(source) as native:
                if native.format != "PNG":
                    raise ValueError("Native source must contain PNG bytes")
            if record.get("pixelEdits") is not False or record.get("sha256") != identity["sourceSHA256"] or identity["rawSourceSHAEqual"] is not True:
                issues.append(f"{image}: explicit sha256, pixelEdits:false and native rawOutputPath required for installation")
            if record.get("registrationAccepted") and not record.get("registrationReview"):
                record["registrationAccepted"] = False
                issues.append(f"{image}: registrationAccepted needs a recorded explicit visual registrationReview")
            radius = record.get("registrationSearchMaxRadius", 96 if record.get("reusedFrom") else 32)
            if type(radius) is not int or radius not in (32, 96):
                raise ValueError("registrationSearchMaxRadius must be 32 or 96")
            profile_helper = SimpleNamespace(**vars(helper))
            profile_helper.translation = lambda old, new, roi, override=None: helper.translation(old, new, roi, override, max_radius=radius)
            sheets[image] = face.measure_image(image, source, references[image], baseline, profile_helper, record, identity)
            sheets[image]["registrationSearchMaxRadius"] = radius
            sheets[image]["registrationReview"] = record.get("registrationReview")
            sheets[image]["generationRecord"] = copy.deepcopy(record)
            issues.extend(f"{image}: {issue}" for issue in sheets[image]["issues"])
            for reg in sheets[image]["registrations"]:
                if reg["lowerBodyMaskIoU"] < .85 and not (record.get("registrationAccepted") is True and record.get("registrationReview")):
                    issues.append(f"{image}: Cell {reg['index']}: lower-body IoU below0.85 requires explicit visual registrationAccepted and registrationReview")
                if reg["lowerBodyMaskIoU"] < .85 or reg.get("atSearchBoundary") or max(map(abs, reg["bodyOnlyTranslationXY"])) > 32:
                    findings.append({"image": image, "cell": reg["index"], "bodyOnlyTranslationXY": reg["bodyOnlyTranslationXY"],
                                     "lowerBodyMaskIoU": reg["lowerBodyMaskIoU"], "atSearchBoundary": reg.get("atSearchBoundary", False),
                                     "visualReview": record.get("registrationReview"),
                                     "note": "Translation-only evidence; inspect body scale/pose/phase. Large original-reuse shifts may be valid; no scale/identity acceptance inferred."})
        except (ValueError, OSError, KeyError, IndexError) as error:
            errors.append(f"{image}: {error}")
    candidate, phase_records, adapted, pending = copy.deepcopy(baseline), [], [], []
    for key, original in baseline["actions"].items():
        if not all(image in sheets for image in face.action_images(original)):
            pending.append(key)
            continue
        try:
            candidate["actions"][key] = adapt(face, key, original, sheets, baseline["directions"], phase_records)
            adapted.append(key)
        except (ValueError, KeyError, IndexError) as error:
            errors.append(f"{key}: {error}")
    if "idle" in adapted:
        for field in ("image", "perFrameOrigins", "alphaBounds"):
            candidate[field] = copy.deepcopy(candidate["actions"]["idle"][field])
    for field in ("faceDesign", "faceDesignSHA256", "faceProfile", "faceProfileSHA256", "faceProfileScope"):
        candidate.pop(field, None)
    identity_fields = {"sourceDesign": DESIGN.relative_to(ROOT).as_posix(), "sourceDesignSHA256": HUD_SHA,
                       "identityReference": MASTER.relative_to(ROOT).as_posix(), "identityReferenceSHA256": MASTER_SHA,
                       "identityReferenceScope": "Original male-direction.png is authoritative; fixed four-direction head master is a derived alignment reference. Short silver curls, narrow oval face and rounded chin; HUD directly samples original design."}
    candidate.update(identity_fields)
    action_mutable = face.GEOMETRY_FIELDS | {"sourceDesign", "sourceDesignSHA256", "identityReference", "identityReferenceSHA256", "rawOutputPNGs", "rawOutputPNGSHA256s"}
    for key, original in baseline["actions"].items():
        if {k: v for k, v in original.items() if k not in action_mutable} != {k: v for k, v in candidate["actions"][key].items() if k not in action_mutable}:
            raise ValueError(f"Immutable timing/scale/direction fields changed: {key}")
    root_mutable = set(identity_fields) | {"faceDesign", "faceDesignSHA256", "faceProfile", "faceProfileSHA256", "faceProfileScope", "image", "perFrameOrigins", "alphaBounds", "actions"}
    if {k: v for k, v in baseline.items() if k not in root_mutable} != {k: v for k, v in candidate.items() if k not in root_mutable}:
        raise ValueError("Unrelated root manifest fields changed")
    if candidate["actions"]["run"] != candidate["actions"]["run_W01"]:
        raise ValueError("Held run aliases differ")
    hud = {"sourcePath": str(HUD), "sourceSHA256": HUD_SHA, "runtimePath": str(HUD_RUNTIME),
           "runtimeResource": "flat2d/hero-head-design-reference", "size": [1752, 897],
           "mode": "RGB", "rect": [1250, 0, 502, 502], "pixelEditsAfterGeneration": False}
    report = {"status": "measured; not installed", "baselineManifestSHA256": BASELINE_SHA,
              "selectedPNGCount": len(selected), "measuredPNGCount": len(sheets), "baselinePNGCount": 68,
              "baselineActionCount": 88, "adaptedActionKeys": adapted, "pendingActionKeys": pending,
              "missingInputs": missing, "errors": errors, "installationIssues": issues,
              "registrationReviewFindings": findings, "images": sheets, "hud": hud,
              "runPhaseTransfers": phase_records, "identityReferences": identity_fields,
              "candidateManifest": candidate, "fullPathSHA256s": hashes, "pixelEditsAfterGeneration": False}
    report_path = args.report.resolve()
    if str(report_path) in hashes or report_path.is_relative_to(ACTOR) or report_path == HUD_RUNTIME:
        raise ValueError("Report destination overlaps protected input/runtime paths")
    # Establish report writability before any runtime installation.
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(data_bytes(report))
    if args.install:
        if errors or issues or len(sheets) != 68 or len(adapted) != 88 or set(selected) != set(references):
            errors.append("Installation refused: all 68 PNGs / 88 actions and native provenance/registration must validate; no partial installation")
        else:
            install(candidate, sheets, hud, hashes, report)
    if not report["status"].startswith("installed"):
        for path, digest in hashes.items():
            check(path, digest)
    report_path.write_bytes(data_bytes(report))
    print(json.dumps({k: report[k] for k in ("status", "measuredPNGCount", "selectedPNGCount", "baselineActionCount", "errors", "installationIssues", "missingInputs")}, ensure_ascii=False, indent=2))
    print(f"Report: {report_path}")
    return 1 if errors or issues else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
