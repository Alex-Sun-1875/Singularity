"""Measure six head-only edits against the installed standing-head authority.

Default is read-only measurement. Only --install writes six NEW locomotion-v2
PNGs and the bounded manifest candidate. Existing PNGs, root/idle/HUD metadata,
all UPP/timing/direction values and82 unrelated actions stay unchanged.

selection-head.json: {"images": {"explore-run-a": {...}, "explore-run-b": {...},
"held-run-a": {...}, "held-run-b": {...}, "explore-walk": {...}, "held-walk": {...}}}.
Data lives in head-scale-v2/ beside this script. Entry sourcePath defaults to
head-scale-v2/assets/W01-<key>.png. Adjacent provenance or entry
must supply rawOutputPath, sha256, pixelEdits:false, nativeBodyReviewed:true,
identityReviewed:true and a nonempty visualReview. A body IoU below.9 or search
boundary additionally needs registrationAccepted:true and registrationReview.
Optional registrationRois/registrationOverrides/frameRects/semanticCropReview
use the existing face adapter schema. Relative CLI paths resolve beside this
script; relative source/provenance paths resolve inside head-scale-v2/.

Reuse: face.measure_image, identity.adapt (each run phase's own measured XY),
and the existing locomotion staged transaction/known-byte rollback. No PNG
reencoding, new registration algorithm, dependencies, tests or build commands.
"""
from __future__ import annotations

import argparse
import copy
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE / "head-scale-v2"
ROOT = HERE.parents[3]
ACTOR = ROOT / "src/cocos/assets/resources/flat2d/characters/raphael"
MANIFEST = ACTOR / "manifest.json"
BASELINE = DATA / "baseline-manifest.json"
BASELINE_SHA = "e1682ed6f1b6000e4ff3e46f4871abcd018532979cca0d891308117003e64443"
SPECS = {
    "explore-run-a": "face-v1/carry-v1/explore-W01-run-a.png",
    "explore-run-b": "face-v1/carry-v1/explore-W01-run-b.png",
    "held-run-a": "face-v1/hero-v6/hero-v4-run-readable-a.png",
    "held-run-b": "face-v1/hero-v6/hero-v4-run-readable-b.png",
    "explore-walk": "locomotion-v1/W01-explore-walk.png",
    "held-walk": "locomotion-v1/W01-held-walk.png",
}
CHANGED = {"run", "run_W01", "explore_run_W01", "walk", "walk_W01", "explore_walk_W01"}
STANDING = {
    "explore": ("locomotion-v1/W01-explore-idle.png", "df887b28a9bef335aa326d86bf2117a07f1faeef192ac1b55145123b549481cd"),
    "held": ("locomotion-v1/W01-held-idle.png", "56fff3bc81b1c2016ded85cd4f315997d7872897cba7bcc87c2d059991a4891c"),
}


def path(value):
    p = Path(value)
    return (p if p.is_absolute() else HERE / p).resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--selection", type=path, default=DATA / "selection-head.json")
    parser.add_argument("--report", type=path, default=DATA / "measurement-report.json")
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()
    # Import the standard-library-only common profile first; helper imports are
    # deferred until after argparse, so --help never reads or measures assets.
    import importlib.util
    common_path = HERE.parent / "identity-reference-v1/install-identity.py"
    spec = importlib.util.spec_from_file_location("head_alignment_common", common_path)
    common = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(common)
    face_path = HERE.parent / "face-blend-v1/install-face-runtime.py"
    helper_path = HERE.parent / "weapon-carry-v1/measure-install.py"
    transaction_path = HERE / "install-locomotion.py"
    face = common.load_module("head_alignment_face", face_path)
    helper = common.load_module("head_alignment_alpha", helper_path)
    transaction = common.load_module("head_alignment_transaction", transaction_path)
    hashes = {}
    for filename in (BASELINE, MANIFEST):
        common.check(filename, BASELINE_SHA)
        common.snapshot(filename, hashes)
    for filename in (Path(__file__).resolve(), common_path, face_path, helper_path, transaction_path, args.selection):
        common.snapshot(filename, hashes)
    baseline = face.read_json(BASELINE)
    if len(baseline["actions"]) != 88 or not CHANGED <= set(baseline["actions"]):
        raise ValueError("Expected exact frozen88-action baseline")
    references = {old: [] for old in SPECS.values()}
    old_paths = set()
    for key, action in baseline["actions"].items():
        for image in face.action_images(action):
            filename = (ACTOR / face.safe_image(image)).resolve()
            if not filename.is_file():
                raise ValueError(f"Missing frozen runtime PNG: {filename}")
            old_paths.add(filename)
            common.snapshot(filename, hashes)
            common.snapshot(Path(str(filename) + ".meta"), hashes)
            if image in references:
                references[image].append((key, action))
    if any(not refs or any(key not in CHANGED for key, _ in refs) for refs in references.values()):
        raise ValueError("Six fixed input PNGs must belong only to the six selected actions")
    for family, (image, digest) in STANDING.items():
        common.check(ACTOR / image, digest)
        expected = "explore_idle_W01" if family == "explore" else "idle_W01"
        if baseline["actions"][expected]["image"] != image:
            raise ValueError(f"Standing authority action differs: {expected}")
    hud = ACTOR.parents[1] / "hero-head-design-reference.png"
    common.snapshot(hud, hashes)
    common.snapshot(Path(str(hud) + ".meta"), hashes)
    loaded = face.read_json(args.selection) if args.selection.is_file() else {}
    selected = loaded.get("images", loaded)
    if set(selected) - set(SPECS):
        raise ValueError("Unknown head alignment selection key")
    destinations = {old: f"locomotion-v2/W01-{key}.png" for key, old in SPECS.items()}
    face.renamed = lambda image: destinations[image]
    sheets, errors, issues, missing = {}, [], [], []
    for logical, old in SPECS.items():
        source_value = Path(selected.get(logical, {}).get("sourcePath", f"assets/W01-{logical}.png"))
        source = (source_value if source_value.is_absolute() else DATA / source_value).resolve()
        destination = (ACTOR / destinations[old]).resolve()
        if destination in old_paths:
            raise ValueError("New output overlaps an old runtime PNG")
        common.snapshot(destination, hashes)
        common.snapshot(Path(str(destination) + ".meta"), hashes)
        if not source.is_file():
            missing.append(logical)
            continue
        try:
            if source.is_relative_to(ACTOR):
                raise ValueError("Native source must stay outside runtime")
            record, identity = face.load_provenance(source, selected.get(logical, {}), DATA, hashes)
            raw = identity["rawOutputPath"]
            if (record.get("pixelEdits") is not False or record.get("sha256") != identity["sourceSHA256"]
                    or identity["rawSourceSHAEqual"] is not True or not raw or path(raw).is_relative_to(ACTOR)):
                issues.append(f"{logical}: explicit raw native byte provenance required")
            with helper.Image.open(source) as image:
                if image.format != "PNG" or image.mode != "RGBA" or image.size != (1024, 1536):
                    raise ValueError("Native1024x1536 transparent RGBA PNG required")
            for flag in ("nativeBodyReviewed", "identityReviewed"):
                if record.get(flag) is not True:
                    issues.append(f"{logical}: {flag}:true required after visual review")
            if not isinstance(record.get("visualReview"), str) or not record["visualReview"].strip():
                issues.append(f"{logical}: nonempty visualReview required")
            sheet = face.measure_image(old, source, references[old], baseline, helper, record, identity)
            if sheet["layout"] != [4, 4]:
                raise ValueError("Expected fixed4x4 native layout")
            weak = [r["index"] for r in sheet["registrations"]
                    if r["lowerBodyMaskIoU"] < .9 or r.get("atSearchBoundary")]
            if weak and not (record.get("registrationAccepted") is True
                             and isinstance(record.get("registrationReview"), str)
                             and record["registrationReview"].strip()):
                issues.append(f"{logical}: bodyIoU<.9/boundary cells{weak} need explicit registrationAccepted and registrationReview")
            issues.extend(f"{logical}: {issue}" for issue in sheet["issues"])
            if hashes[str(destination)] not in (None, identity["sourceSHA256"]):
                raise ValueError("New runtime destination contains unknown bytes")
            sheet.update(generationRecord=copy.deepcopy(record),
                         minimumBodyMaskIoU=min(r["lowerBodyMaskIoU"] for r in sheet["registrations"]))
            sheets[old] = sheet
        except (ValueError, OSError, KeyError, IndexError, TypeError) as error:
            errors.append(f"{logical}: {error}")
    candidate, adapted, phases = copy.deepcopy(baseline), [], []
    for key in sorted(CHANGED):
        original = baseline["actions"][key]
        if not all(image in sheets for image in face.action_images(original)):
            continue
        action = common.adapt(face, key, original, sheets, baseline["directions"], phases)
        family = "explore" if key.startswith("explore_") else "held"
        image, digest = STANDING[family]
        reference = (ACTOR / image).relative_to(ROOT).as_posix()
        action.update(identityReference=reference, identityReferenceSHA256=digest,
                      identityReferenceScope="User-selected current standing head is canonical; native head-only edit preserves accepted body, scale and every animation phase.",
                      sourceDesign=reference, sourceDesignSHA256=digest,
                      bodyAnimationBaselineManifestSHA256=BASELINE_SHA,
                      originMethod="Each original phase support anchor transferred by its own measured body-only XY; fixed UPP/timing/direction/contact/flight retained; current standing head authority; complete native alpha16 crops.")
        action.pop("identityRunAuthority", None)
        # The shared adapter already checks this before authority metadata changes.
        # Recheck all original nongeometry fields except the explicit provenance.
        mutable = face.GEOMETRY_FIELDS | {"sourceDesign", "sourceDesignSHA256", "identityReference",
                  "identityReferenceSHA256", "identityReferenceScope", "identityRunAuthority",
                  "rawOutputPNGs", "rawOutputPNGSHA256s", "bodyAnimationBaselineManifestSHA256"}
        if {k:v for k,v in original.items() if k not in mutable} != {k:v for k,v in action.items() if k not in mutable}:
            raise ValueError(f"Frozen action timing/scale/direction changed: {key}")
        candidate["actions"][key] = action
        adapted.append(key)
    protected = [key for key in baseline["actions"] if key not in CHANGED]
    if (len(protected) != 82 or set(candidate["actions"]) != set(baseline["actions"])
            or any(candidate["actions"][key] != baseline["actions"][key] for key in protected)
            or {k:v for k,v in candidate.items() if k != "actions"} != {k:v for k,v in baseline.items() if k != "actions"}):
        raise ValueError("Protected root/idle/HUD/82-action content changed")
    report = dict(status="measured head alignment; not installed", baselineManifestSHA256=BASELINE_SHA,
                  measuredPNGCount=len(sheets), baselineActionCount=88, adaptedActionKeys=adapted,
                  protectedActionKeys=protected, rootManifestFieldsUnchanged=True,
                  oldRuntimePNGPaths=sorted(map(str, old_paths)), standingHeadAuthorities=STANDING,
                  phaseXYTransfers=phases, images=sheets, missingInputs=missing,
                  errors=errors, installationIssues=issues, candidateManifest=candidate,
                  fullPathSHA256s=hashes, pixelEditsAfterGeneration=False)
    output = args.report.resolve()
    if str(output) in hashes or output.is_relative_to(ACTOR):
        raise ValueError("Report overlaps protected input/runtime")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(common.data_bytes(report))
    if args.install:
        if errors or issues or missing or len(sheets) != 6 or set(adapted) != CHANGED:
            errors.append("Installation refused: six complete native sheets, six action adaptations and visual/body reviews required")
        else:
            # Reuse the transaction only for this exact frozen installed variant.
            if BASELINE_SHA != "e1682ed6f1b6000e4ff3e46f4871abcd018532979cca0d891308117003e64443":
                raise ValueError("Unknown transaction profile baseline")
            common.check(BASELINE, BASELINE_SHA)
            common.check(MANIFEST, BASELINE_SHA)
            transaction.BASELINE_SHA = BASELINE_SHA
            transaction.HERE = DATA
            transaction.MANIFEST = MANIFEST
            transaction.install(candidate, sheets, hashes, report, common,
                                status="installed six native head-aligned PNGs and six bounded actions; root/idle/HUD preserved")
    if not report["status"].startswith("installed"):
        for filename, digest in hashes.items():
            common.check(filename, digest)
    output.write_bytes(common.data_bytes(report))
    print(common.data_bytes({k:report[k] for k in ("status", "measuredPNGCount", "adaptedActionKeys", "missingInputs", "errors", "installationIssues")}).decode())
    print(f"Report: {output}")
    return 1 if errors or issues or missing else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, IndexError, TypeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
