"""Thin short-curly restoration adapter; default is read-only measurement.

python install-runtime.py --print-config          # complete 70-image schema
python install-runtime.py --config selections.json --report dryrun.json
python install-runtime.py --pilot --config selections.json
Only --install may change runtime; no Cocos build or PNG editing is performed.
Relative paths resolve against this directory, then the repository when present.

Configuration is {"images": {"carry-v1/explore-W01-dodge.png": {
  "sourcePath":"assets/carry-v1/explore-W01-dodge.png",
  "geometryTarget":"../appearance-v5/male-reactions/hero-v4-dodge-readable.png",
  "bodyProportionAccepted":true, "poseReviewAccepted":true,
  "provenance":{"rawOutputPath":"C:/.../generated.png","sha256":"..."},
  "measurement":{"registrationRois":{"0":[x,y,w,h]},
                 "registrationOverrides":{"0":[dx,dy]},
                 "registrationAccepted":true,"frameRects":[...],
                 "semanticCropReview":"independent complete-alpha audit"}}},
 "actions":{"explore_dodge_W01":{"geometryActionKey":"dodge",
              "geometryOverrides":{"perFrameRects":[...],
                                   "perFrameOrigins":[...]}}},
 "runGeometry":{"reviewed":true,"targets":{"a":"masters/run-a.png","b":"masters/run-b.png"},
                "action":{"worldUnitsPerPixel":0.0044,"perFrameRects":[...],
                          "frameRectsByImage":{"a":[...],"b":[...]},
                          "perFrameOrigins":{"down":[8 points],"right":[8 points],
                                             "up":[8 points],"left":[8 points]}}},
 "hud":{"sourcePath":"../appearance-v5/hud-head.png","provenance":{...}}}.
Image keys omit the old face-v1/ prefix. Overrides are field merges. Geometry
overrides may only change geometry/UPP, never frames/fps/phases/direction lookup.
Every selected carry image needs bodyProportionAccepted after comparison with
the approved long-legged reference; all run images additionally need a reviewed
real eight-phase run matching its fourth complete figure. These flags attest
visual selection; binary-alpha registration cannot establish either property.

Timeline baseline is the pinned current 88 actions. Non-run geometry templates
come from the original short-curly metadata, with explicit target PNGs. All seven
carry idles use its 2x2 idle: W01/W02 now get independent PNGs and [0,1,2,3]
directionFrameIndices; only those two lookups/layouts may change. Run targets and
support/crops/UPP must be newly authored from the approved run master A/B; old run
geometry is never a measurement fallback. Run A/B/order, eight phases, FPS and
all action timing remain exactly the timeline baseline. Runtime has 70 sprite
PNGs plus one HUD, while action keys remain 88.
Registration defaults to boot regions, so changed thigh/torso proportions are
not forced into a full-lower-body translation. UPP and accepted support/ground
positions come from the chosen geometry template, never weapon/head extents.

The face adapter supplies provenance, complete-alpha measurement, anchor/action
transfer and staged atomic installation/rollback. The carry helper supplies
alpha/native_geometry/translation. Small adaptations here are needed because
the former hardcodes the old runtime PNG as its geometry target and assumes
its frozen UPP; this profile deliberately restores different approved geometry.
No old script/report/baseline is rewritten. HUD selection is recorded/copied;
the runtime HUD resource reference is maintained separately.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = HERE.parent / "appearance-v5"
BASELINE = HERE / "baseline-manifest.json"
BASELINE_SHA = "e1641ddd0083a8088284dceba297d6f2f14d987de31df8c746eae7922218fd9e"
REFERENCE = HERE / "approved-reference.png"
REFERENCE_SHA = "75af3fdc4dedd5e5994045786acb1cfe73866db62c88a38227f87ea2b0972e7c"
OWNER_SHA = {"male-sword-staff": "8242c58696d7009777fcc8d28efeca14c8b3dda2e30a44960ae9b8a408efd66a",
             "male-bows": "c3e83029a216402dceee8f47a750ffa02d635b776423bf29a13631bbf83b4bd4",
             "male-reactions": "f996a6e302645e093f5d1262d317da8ffe5311b2ebb4b33199848330f849ed2e"}
GEOMETRY = {"perFrameRects", "frameRectsByImage", "perFrameOrigins", "alphaBounds",
            "perPhaseAlphaBounds", "alphaBoundsThreshold", "worldUnitsPerPixel", "originMethod"}
LOOKUP = {"columns", "frameWidth", "frameHeight", "directionFrameIndices"}
NEW_IDLE = {"explore_idle_W01", "explore_idle_W02"}
MUTABLE = GEOMETRY | LOOKUP | {"image", "frameImages", "sourcePNG", "sourcePNGSHA256", "sourcePNGs",
                      "sourcePNGSHA256s", "sourceDesign", "sourceDesignSHA256"}
TIMING = ("frames", "fps", "loop", "frameIndices", "directionFrameIndices", "phaseStarts",
          "row", "absoluteFrameIndices")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


face = load_module("curly_face_adapter", HERE.parent / "face-blend-v1/install-face-runtime.py")
carry = load_module("curly_native_measurement", HERE.parent / "weapon-carry-v1/measure-install.py")


def path(value):
    p = Path(value)
    if p.is_absolute():
        return p.resolve()
    return next((q.resolve() for q in (HERE / p, ROOT / p) if q.exists()), (HERE / p).resolve())


def canonical(image):
    return face.safe_image(image.removeprefix("face-v1/"))


def output_image(image):
    return "curly-v1/" + canonical(image)


def unchanged_timing(before, after, key):
    if any(before.get(field) != after.get(field) for field in TIMING if field not in LOOKUP):
        raise ValueError(f"Frozen timing/direction/frame lookup changed: {key}")
    if key in NEW_IDLE:
        if {field: after.get(field) for field in LOOKUP} not in (
                {field: before.get(field) for field in LOOKUP},
                {"columns": 2, "frameWidth": 768, "frameHeight": 512, "directionFrameIndices": [0, 1, 2, 3]}):
            raise ValueError(f"Only the reviewed 2x2 idle lookup is allowed: {key}")
    elif any(before.get(field) != after.get(field) for field in LOOKUP):
        raise ValueError(f"Unapproved geometry lookup change: {key}")
    if {k: v for k, v in before.items() if k not in MUTABLE} != {k: v for k, v in after.items() if k not in MUTABLE}:
        raise ValueError(f"Non-appearance action fields changed: {key}")


def geometry_key(key):
    if not key.startswith("explore_"):
        return key
    _, kind, weapon = key.split("_")
    if kind == "idle":
        return "idle"
    if kind == "dodge":
        return "dodge_W07" if weapon in ("W07", "W08", "L02") else "dodge"
    return f"{kind}_{weapon}"


def source_for(owner, image):
    original = ART / owner / Path(image).name
    candidate = ART / owner / "alpha-candidates" / original.name
    return candidate if candidate.is_file() else original


def templates(timeline, selections, hashes):
    old, owners = {}, {}
    for owner, expected in OWNER_SHA.items():
        p = ART / owner / "owned-actions.json"
        if face.sha(p) != expected:
            raise ValueError(f"Pinned curly metadata changed: {p}")
        hashes[str(p)] = expected
        actions = face.read_json(p)["actions"]
        if set(old) & set(actions):
            raise ValueError("Conflicting curly action owners")
        old.update(actions)
        owners.update({key: owner for key in actions})
    if len(old) != 60 or set(old) != {key for key in timeline["actions"] if not key.startswith("explore_")}:
        raise ValueError("Expected exact 60 combat + 28 preserved exploration actions")
    if set(selections.get("actions", {})) - set(timeline["actions"]):
        raise ValueError("Unknown action override key")
    run_spec = selections.get("runGeometry", {})
    run_action = run_spec.get("action", {})
    run_ready = bool(run_spec.get("reviewed"))
    if run_ready:
        if set(run_action) - (GEOMETRY | LOOKUP):
            raise ValueError("Authored run metadata may contain only geometry/UPP/layout")
        required = {"worldUnitsPerPixel", "perFrameRects", "frameRectsByImage", "perFrameOrigins"}
        if not required <= set(run_action) or run_action["worldUnitsPerPixel"] <= 0:
            raise ValueError("Reviewed run master must provide authored crops/support/UPP")
        if (len(run_action["perFrameRects"]) != 16
                or set(run_action["frameRectsByImage"]) != {"a", "b"}
                or any(len(value) != 16 for value in run_action["frameRectsByImage"].values())
                or set(run_action["perFrameOrigins"]) != set(timeline["directions"])
                or any(len(value) != 8 for value in run_action["perFrameOrigins"].values())):
            raise ValueError("Authored run requires two 16-cell sheets and eight supports per direction")
    virtual, images = copy.deepcopy(timeline), {}
    for key, current in timeline["actions"].items():
        options = selections.get("actions", {}).get(key, {})
        base_key = options.get("geometryActionKey", geometry_key(key))
        base = copy.deepcopy(old[base_key])
        is_run = key.startswith("run") or key.startswith("explore_run")
        if is_run and run_ready:
            base.update(copy.deepcopy(run_action))
        overrides = options.get("geometryOverrides", {})
        if set(overrides) - GEOMETRY:
            raise ValueError(f"Only geometry overrides permitted: {key}")
        base.update(overrides)
        before_names = face.action_images(base)
        action = copy.deepcopy(current)
        if key in NEW_IDLE:
            weapon = key.rsplit("_", 1)[1]
            action["image"] = f"face-v1/carry-v1/explore-{weapon}-idle.png"
            for field in LOOKUP:
                if field in base:
                    action[field] = copy.deepcopy(base[field])
                else:
                    action.pop(field, None)
        names = face.action_images(action)
        if len(before_names) != len(names):
            raise ValueError(f"Geometry/timeline sheet count differs: {key}")
        for field in GEOMETRY:
            if field in base:
                action[field] = copy.deepcopy(base[field])
            else:
                action.pop(field, None)
        if "frameRectsByImage" in base:
            action["frameRectsByImage"] = {
                name.removesuffix(".png"): copy.deepcopy(base["frameRectsByImage"][label] if is_run and run_ready else face.sheet_rects(base, before))
                for label, before, name in zip(("a", "b"), before_names, names)}
        unchanged_timing(current, action, key)
        virtual["actions"][key] = action
        for label, before, name in zip(("a", "b"), before_names, names):
            target = (ART / owners[base_key] / Path(before).name).resolve()
            original_sources = old[base_key].get("sourcePNGs", [])
            original_hashes = old[base_key].get("sourcePNGSHA256s", [])
            for recorded, expected in zip(original_sources, original_hashes) if not is_run else []:
                if Path(recorded).name == target.name and face.sha(target) != expected:
                    raise ValueError(f"Pinned original curly PNG changed: {target}")
            chosen_source = source_for(owners[base_key], before).resolve()
            if is_run:
                target = path(run_spec.get("targets", {}).get(label, f"masters/run-master-{label}.png"))
            entry = {"sourcePath": str((HERE / "assets" / canonical(name)).resolve()) if key.startswith("explore_") or is_run else str(chosen_source),
                     "geometryTarget": str(target), "bodyProportionAccepted": not key.startswith("explore_"),
                     "poseReviewAccepted": not is_run, "geometryReady": not is_run or run_ready,
                     "measurement": {}, "provenance": {}}
            if name in images and images[name]["geometryTarget"] != entry["geometryTarget"]:
                raise ValueError(f"Conflicting shared-image geometry target: {name}")
            images.setdefault(name, entry)
    if len(images) != 70 or len({output_image(name) for name in images}) != 70:
        raise ValueError("Image map must be one-to-one for 70 PNGs (including two independent new idles)")
    if set(selections.get("images", {})) - {canonical(name) for name in images}:
        raise ValueError("Unknown canonical image selection key")
    for name, entry in images.items():
        override = selections.get("images", {}).get(canonical(name), {})
        if set(override) - set(entry):
            raise ValueError(f"Unknown image selection fields for {name}: {set(override) - set(entry)}")
        if override.get("geometryReady", entry["geometryReady"]) != entry["geometryReady"]:
            raise ValueError("geometryReady is derived from reviewed authored runGeometry, not an image-level override")
        entry.update(copy.deepcopy(override))
        for field in ("sourcePath", "geometryTarget"):
            entry[field] = str(path(entry[field]))
    return virtual, images


def provenance_catalog(hashes):
    """Normalize historical record field names; never infer raw byte identity."""
    catalog = {}
    record_paths = [ART / "male-sword-staff/generation-records.json", ART / "male-sword-staff/alpha-correction-records.json",
                    ART / "male-bows/generation-record.json", ART / "root-generation-records.json",
                    ART / "hud-head.provenance.json", ART / "male-reactions/dodge-extraction.provenance.json"]
    def visit(value):
        if isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, dict):
            raw = value.get("rawOutputPath") or value.get("generatedPath") or value.get("raw")
            source = value.get("sourcePath") or value.get("sourcePNG") or value.get("source")
            if raw and source:
                catalog[str(path(source))] = {"rawOutputPath": str(path(raw)), "pixelEdits": False}
            if raw and value.get("name") and not source:
                candidate = ART / "male-sword-staff/alpha-candidates" / value["name"]
                if candidate.is_file():
                    catalog[str(candidate.resolve())] = {"rawOutputPath": str(path(raw)), "pixelEdits": False}
            for child in value.values():
                if isinstance(child, (dict, list)):
                    visit(child)
    for p in record_paths:
        if p.is_file():
            hashes[str(p)] = face.sha(p)
            visit(face.read_json(p))
    return catalog


class ExplicitTarget:
    """Redirect only the face helper's hardcoded old-alpha read, read-only."""
    def __init__(self, image, target):
        self.old = (face.ACTOR / image).resolve()
        self.target = target

    def __getattr__(self, name):
        return getattr(carry, name)

    def alpha(self, p):
        return carry.alpha(self.target if Path(p).resolve() == self.old else p)


def boot_rois(action, image, directions):
    rois = {}
    stature = 1.556 / action["worldUnitsPerPixel"]
    for index, rect in enumerate(face.sheet_rects(action, image)):
        point = face.origin_at(action, image, index, directions)
        gx, gy = rect[0] + point[0], rect[1] + point[1]
        left, top = max(0, round(gx - .22 * stature)), max(0, round(gy - .16 * stature))
        rois[str(index)] = [left, top, round(gx + .22 * stature) - left, round(gy) + 2 - top]
    return rois


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=path)
    parser.add_argument("--print-config", action="store_true")
    parser.add_argument("--pilot", action="store_true", help="Only W01 carry dodge plus old curly HUD; independent idle is a separate full-profile image")
    parser.add_argument("--pilot-source", type=path)
    parser.add_argument("--report", type=path)
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()
    baseline_bytes = BASELINE.read_bytes()
    if face.sha(BASELINE) != BASELINE_SHA or face.sha(REFERENCE) != REFERENCE_SHA:
        raise ValueError("Frozen timeline/reference SHA mismatch")
    timeline = json.loads(baseline_bytes)
    hashes = {str(BASELINE): BASELINE_SHA, str(REFERENCE): REFERENCE_SHA, str(Path(__file__).resolve()): face.sha(__file__),
              str(Path(face.__file__).resolve()): face.sha(face.__file__), str(Path(carry.__file__).resolve()): face.sha(carry.__file__)}
    selections = face.read_json(args.config) if args.config else {}
    if args.config:
        hashes[str(args.config)] = face.sha(args.config)
    virtual, entries = templates(timeline, selections, hashes)
    if args.print_config:
        print(json.dumps({"images": {canonical(k): v for k, v in entries.items()}, "actions": {},
                          "runGeometry": {"reviewed": False, "targets": {"a": "masters/run-master-a.png", "b": "masters/run-master-b.png"},
                                          "action": {"worldUnitsPerPixel": None, "perFrameRects": [], "frameRectsByImage": {"a": [], "b": []},
                                                     "perFrameOrigins": {direction: [] for direction in timeline["directions"]}}},
                          "hud": {"sourcePath": str(ART / "hud-head.png"), "provenance": {}}}, ensure_ascii=False, indent=2))
        return 0
    catalog = provenance_catalog(hashes)
    # Isolated imported module only; no source file/global runtime is changed.
    face.HERE, face.BASELINE, face.INVENTORY = HERE, BASELINE, BASELINE
    face.EXPECTED_BASELINE_SHA, face.renamed = BASELINE_SHA, output_image
    references = {}
    for key, action in virtual["actions"].items():
        for image in face.action_images(action):
            references.setdefault(image, []).append((key, action))
    selected = [name for name in entries if not args.pilot or canonical(name) == "carry-v1/explore-W01-dodge.png"]
    if args.pilot_source:
        if not args.pilot:
            parser.error("--pilot-source requires --pilot")
        entries[selected[0]]["sourcePath"] = str(args.pilot_source)
    sheets, missing, errors, issues, run_records = {}, [], [], [], []
    for image in selected:
        entry = entries[image]
        source, target = path(entry["sourcePath"]), path(entry["geometryTarget"])
        for p in (source, target):
            if not p.is_file():
                missing.append(str(p))
        if not entry["geometryReady"]:
            issues.append(f"{canonical(image)}: authored/reviewed run-master A/B geometry required; old run geometry is not measured")
            continue
        if not source.is_file() or not target.is_file():
            continue
        try:
            print(f"Measuring {canonical(image)}", file=sys.stderr, flush=True)
            hashes[str(target)] = face.sha(target)
            provenance = {**catalog.get(str(source), {}), **entry["provenance"]}
            record, identity = face.load_provenance(source, provenance, HERE, hashes)
            record.update(entry["measurement"])
            record.setdefault("registrationRois", boot_rois(references[image][0][1], image, timeline["directions"]))
            measured = face.measure_image(image, source, references[image], virtual, ExplicitTarget(image, target), record, identity)
            measured.update({"geometryTarget": str(target), "geometryTargetSHA256": hashes[str(target)],
                             "oldRuntimePath": str(target),
                             "timelineImagePaths": sorted({name for key, _ in references[image] for name in face.action_images(timeline["actions"][key])}),
                             "registrationPolicy": "Boot-only alpha translation; torso/thigh changes are not normalized or forced into translation."})
            sheets[image] = measured
            issues.extend(f"{canonical(image)}: {value}" for value in measured["issues"])
            if not entry["bodyProportionAccepted"] or not entry["poseReviewAccepted"]:
                issues.append(f"{canonical(image)}: approved-reference leg/body or run-pose selection still needs review")
        except (ValueError, OSError, KeyError, IndexError) as error:
            errors.append(f"{canonical(image)}: {error}")
    candidate, adapted = copy.deepcopy(timeline), []
    for key, template in virtual["actions"].items():
        if not any(image in sheets for image in face.action_images(template)):
            continue
        try:
            action = face.adapt_action(key, template, sheets, timeline["directions"], issues, run_records)
            if any(image in sheets for image in face.action_images(template)):
                action.update({"sourceDesign": str(REFERENCE.relative_to(ROOT)), "sourceDesignSHA256": REFERENCE_SHA,
                               "originMethod": "Original short-curly support/UPP transferred by boot-region alpha; approved-reference proportions are reviewed in the PNG, not inferred/rescaled from alpha."})
            unchanged_timing(timeline["actions"][key], action, key)
            candidate["actions"][key] = action
            adapted.append(key)
        except (ValueError, KeyError, IndexError) as error:
            errors.append(f"{key}: {error}")
    identity_fields = {"sourceDesign": REFERENCE.relative_to(ROOT).as_posix(), "sourceDesignSHA256": REFERENCE_SHA,
                       "appearanceProfile": "short silver curls / original chin / reference long legs and fourth-figure run"}
    for field in ("faceDesign", "faceDesignSHA256", "faceProfile", "faceProfileSHA256", "faceProfileScope"):
        candidate.pop(field, None)
    candidate.update(identity_fields)
    candidate["revision"] = "concept-image-2d-curly-v1-pilot" if args.pilot else "concept-image-2d-curly-v1"
    if timeline["image"] in sheets:
        idle = candidate["actions"]["idle"]
        for field in ("image", "perFrameOrigins", "alphaBounds"):
            candidate[field] = copy.deepcopy(idle[field])
        candidate["camera"]["worldUnitsPerPixel"] = idle["worldUnitsPerPixel"]
    hud_config = selections.get("hud", {})
    hud_source, hud = path(hud_config.get("sourcePath", str(ART / "hud-head.png"))), None
    try:
        _, proof = face.load_provenance(hud_source, {**catalog.get(str(hud_source), {}), **hud_config.get("provenance", {})}, HERE, hashes)
        a = carry.alpha(hud_source)
        if list(a.shape[::-1]) != [1254, 1254]:
            raise ValueError("HUD native 1254x1254 dimensions required")
        hud = {**proof, "runtimePath": str(face.FLAT / "hero-head-curly-v1.png"),
               "runtimeResource": "flat2d/hero-head-curly-v1", "retainedRuntimeCrop": [190, 0, 850, 850]}
    except (ValueError, OSError) as error:
        errors.append(f"HUD: {error}")
    report = {"version": "curly-restore-v1", "mode": "pilot" if args.pilot else "full", "status": "measured; not installed",
              "timelineBaselineSHA256": BASELINE_SHA, "actionCount": 88, "imageMapCount": len(entries),
              "selectedImageCount": len(selected), "measuredImageCount": len(sheets), "adaptedActionKeys": adapted,
              "candidateManifest": candidate, "identityReferences": identity_fields, "images": sheets, "hud": hud,
              "sourceSelections": {canonical(k): entries[k] for k in selected}, "runGroundTransfers": run_records,
              "missingInputs": sorted(set(missing)), "errors": errors, "installationIssues": issues,
              "fullPathSHA256s": hashes, "pixelEditsAfterGeneration": False,
              "transactionFrozenInput": "The shared transaction verifies the same pinned timeline bytes in both frozen-input slots; geometry/source metadata and PNGs are separately hashed above.",
              "limitations": ["Boot registration cannot validate hair, chin, leg ratio, or the approved eight-phase running pose.",
                              "Complete alpha16 coverage is required; touching legacy bodies need independently reviewed semantic crop records.",
                              "Only this adapter is new; old measure/transfer/transaction code and all old artifacts remain unchanged."]}
    if args.report and (args.report.suffix.lower() != ".json" or not args.report.is_relative_to(HERE)
                        or args.report in (BASELINE, REFERENCE) or str(args.report) in hashes):
        raise ValueError("Report must be a new JSON path inside this profile directory, separate from inputs")
    if args.install:
        if errors or issues or missing or len(sheets) != len(selected) or not hud:
            errors.append("Installation refused: missing sources/measurement errors/unreviewed proportions or run poses")
        else:
            # Transaction already checks known exact current bytes. This extra
            # semantic guard permits only frozen or approved curly UPP/identity,
            # while retaining every timing/lookup field from the 88 baseline.
            def validate_current(current, frozen):
                if set(current["actions"]) != set(frozen["actions"]) or current["directions"] != frozen["directions"]:
                    raise ValueError("Runtime 88-action/direction coverage changed")
                for key, action in current["actions"].items():
                    unchanged_timing(frozen["actions"][key], action, key)
            face.validate_live_manifest = validate_current
            if args.pilot:
                current_bytes = (face.ACTOR / "manifest.json").read_bytes()
                face.known_manifest_input(current_bytes)
                live_candidate = json.loads(current_bytes)
                validate_current(live_candidate, timeline)
                for key in adapted:
                    live_candidate["actions"][key] = candidate["actions"][key]
                live_candidate.update(identity_fields)
                live_candidate["revision"] = candidate["revision"]
                for field in ("faceDesign", "faceDesignSHA256", "faceProfile", "faceProfileSHA256", "faceProfileScope"):
                    live_candidate.pop(field, None)
                candidate = live_candidate
                report["candidateManifest"] = candidate
            # Candidate is already the exact selected-action merge, including
            # removal of obsolete identity fields. Disable only the former
            # profile's extra pilot merge; reuse its complete transaction.
            transaction_args = SimpleNamespace(manifest=face.ACTOR / "manifest.json", pilot=False)
            face.install_measured(transaction_args, candidate, report, hashes, timeline, sheets, hud,
                                  baseline_bytes, baseline_bytes)
    if BASELINE.read_bytes() != baseline_bytes or face.sha(REFERENCE) != REFERENCE_SHA:
        raise ValueError("Frozen timeline/reference changed during measurement")
    if args.report:
        face.write_json(args.report, report)
    print(json.dumps({k: report[k] for k in ("status", "mode", "actionCount", "imageMapCount", "selectedImageCount",
                                           "measuredImageCount", "adaptedActionKeys", "missingInputs", "errors", "installationIssues")}, ensure_ascii=False, indent=2))
    return 1 if missing or errors or issues else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, IndexError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
