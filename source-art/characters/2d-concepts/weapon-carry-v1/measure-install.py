"""Measure native carry PNGs and optionally install their unchanged bytes.

Default invocation only reads PNGs/manifest and prints a compact report. Pass
--report owned-actions.json to save all measurements; only --install copies
PNGs and merges exploration actions. No PNG is ever saved, edited or resampled.

Records may be a list, {"files": [...]}, {"records": [...]}, or individual
*.provenance.json files. Example:
  {"weaponId":"W01", "kind":"walk", "sourcePath":"W01/explore-W01-walk.png",
   "rawOutputPath":"C:/.../generated.png", "editTarget":"src/.../old.png"}
Paths resolve against the repository first, then this directory/record file.
Optional fields: baseActionKey, layout:[columns,rows] (or {columns,rows}), frameRects, targetRects,
registrationRois (absolute [x,y,width,height]), registrationOverrides (index ->
[dx,dy]), registrationAccepted:true after visual review, and inputs:[paths].
Independent 2x2 idle defaults to shared `idle`. Walk col0 aliases idle only
with neutralFirstColumn:true in its record or explicit --idle-mode walk-first.
--idle-mode neutral-dodge prefers independent idle; where absent, it explicitly
uses the reviewed neutral standing column0 of that weapon's complete dodge PNG.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import statistics
import sys

import numpy as np
from PIL import Image
from scipy import ndimage, signal


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ACTOR = ROOT / "src/cocos/assets/resources/flat2d/characters/raphael"
WEAPONS = ("W01", "W02", "L01", "W07", "W08", "L02", "W11")
KINDS = ("idle", "walk", "run-a", "run-b", "dodge", "interact")
TEMPORAL = ("frames", "frameIndices", "directionFrameIndices", "fps", "loop",
            "phaseStarts", "row", "absoluteFrameIndices")
NAME = re.compile(r"explore-(W01|W02|L01|W07|W08|L02|W11)-(idle|walk|run-a|run-b|dodge|interact)\.png$")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf8")).hexdigest()


def display(path):
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def resolve(value, record_dir=HERE):
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    choices = [ROOT / path, HERE / path, record_dir / path, ACTOR / path]
    return next((p.resolve() for p in choices if p.exists()), (HERE / path).resolve())


def alpha(path):
    with Image.open(path) as im:
        if im.mode != "RGBA":
            raise ValueError(f"Native transparent RGBA required: {path} ({im.mode})")
        return np.asarray(im.getchannel("A")).copy()


def bbox(mask):
    yy, xx = np.nonzero(mask)
    if not len(xx):
        raise ValueError("Empty alpha frame")
    return [int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1]


def local_bounds(mask, rect):
    x, y, w, h = map(int, rect)
    return bbox(mask[y:y+h, x:x+w])


def native_geometry(a, layout, explicit_rects=None):
    """Use SciPy components, retaining every alpha>=16 component and pixel.

    Large components locate the bodies; detached alpha is assigned to its
    nearest body. If low-alpha AA joins bodies, alpha>=64 seeds separate the
    ownership of all alpha>=16 pixels. Reject crops containing a neighbour.
    This permits weapons/soles across nominal atlas boundaries.
    """
    height, width = a.shape
    columns, rows = map(int, layout)
    if columns < 1 or rows < 1:
        raise ValueError("Invalid atlas layout")
    mask = a >= 16
    corners = np.concatenate([a[:8, :8].ravel(), a[:8, -8:].ravel(),
                              a[-8:, :8].ravel(), a[-8:, -8:].ravel()])
    empty_fraction, corner_max = float((a < 16).mean()), int(corners.max())
    if empty_fraction < .65 or corner_max >= 16:
        raise ValueError(f"Background transparency rejected: alphaBelow16Fraction={empty_fraction:.6f}, corner8x8MaxAlpha={corner_max}; regenerate native transparency")
    labels, count = ndimage.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
    sizes = np.bincount(labels.ravel())
    slices = ndimage.find_objects(labels)
    components = []
    for label, slc in enumerate(slices, 1):
        if slc is None:
            continue
        ys, xs = slc
        components.append({"label": label, "size": int(sizes[label]),
                           "bounds": [xs.start, ys.start, xs.stop, ys.stop]})
    body_seed_threshold = 16
    if explicit_rects is not None:
        if len(explicit_rects) != columns * rows:
            raise ValueError("Explicit frameRects count differs from layout")
        rects = [list(map(int, r)) for r in explicit_rects]
        covered = np.zeros(a.shape, dtype=np.uint8)
        frames = []
        for index, rect in enumerate(rects):
            x, y, w, h = rect
            if min(x, y) < 0 or min(w, h) <= 0 or x+w > width or y+h > height:
                raise ValueError(f"Out-of-image explicit frame rect {index}: {rect}")
            covered[y:y+h, x:x+w] += mask[y:y+h, x:x+w]
            bounds = local_bounds(mask, rect)
            # A connected body must not be clipped by a supplied rectangle.
            for comp in components:
                l, t, r, b = comp["bounds"]
                touches = np.any(labels[y:y+h, x:x+w] == comp["label"])
                if touches and not (x <= l and y <= t and x+w >= r and y+h >= b):
                    raise ValueError(f"Explicit rect clips alpha component: frame {index}")
            frames.append({"index": index, "rect": rect, "alphaBounds": bounds})
        if np.any(mask & (covered != 1)):
            raise ValueError("Explicit rects must cover each alpha>=16 pixel exactly once")
    else:
        minimum = max(200, round(width * height / (columns * rows) * .008))
        def locate_bodies(parts):
            found = []
            for row in range(rows):
                for col in range(columns):
                    candidates = [c for c in parts if c["size"] >= minimum
                                  and col <= ((c["bounds"][0]+c["bounds"][2])/2)/width*columns < col+1
                                  and row <= ((c["bounds"][1]+c["bounds"][3])/2)/height*rows < row+1]
                    if not candidates:
                        return None
                    found.append(max(candidates, key=lambda c: c["size"]))
            return found
        bodies = locate_bodies(components)
        if bodies is None:
            # Reuse the existing bow-metadata policy: >=64 locates bodies,
            # while the delivered crop still retains every >=16 edge pixel.
            # No high-alpha body may be cut, and source pixels never change.
            body_seed_threshold = 64
            labels, count = ndimage.label(a >= 64, structure=np.ones((3, 3), dtype=np.uint8))
            sizes = np.bincount(labels.ravel())
            components = []
            for label, slc in enumerate(ndimage.find_objects(labels), 1):
                if slc is not None:
                    ys, xs = slc
                    components.append({"label": label, "size": int(sizes[label]),
                                       "bounds": [xs.start, ys.start, xs.stop, ys.stop]})
            bodies = locate_bodies(components)
            if bodies is None:
                raise ValueError("No independent body in every cell at alpha16 or alpha64; regenerate or review source")
        if len({c["label"] for c in bodies}) != columns * rows:
            raise ValueError("Connected neighbouring bodies; regenerate or review source")
        owners = np.full(count + 1, -1, dtype=np.int32)
        body_labels = {c["label"]: i for i, c in enumerate(bodies)}
        for comp in components:
            if comp["label"] in body_labels:
                owners[comp["label"]] = body_labels[comp["label"]]
                continue
            l, t, r, b = comp["bounds"]
            def distance(body):
                bl, bt, br, bb = body["bounds"]
                dx, dy = max(bl-r, l-br, 0), max(bt-b, t-bb, 0)
                return dx*dx+dy*dy+.0001*((l+r-bl-br)**2+(t+b-bt-bb)**2)
            owners[comp["label"]] = min(range(len(bodies)), key=lambda i: distance(bodies[i]))
        owned = owners[labels]
        if body_seed_threshold > 16:
            nearest = ndimage.distance_transform_edt(labels == 0, return_distances=False, return_indices=True)
            owned = owners[labels[tuple(nearest)]]
        rects, frames = [], []
        for index, body in enumerate(bodies):
            own = (owned == index) & mask
            l, t, r, b = bbox(own)
            tight = [l, t, r, b]
            # Remove padding if it alone includes a neighbour; never drop alpha.
            for padding in (2, 1, 0):
                x, y, rr, bb = max(0, l-padding), max(0, t-padding), min(width, r+padding), min(height, b+padding)
                foreign = int(np.count_nonzero(mask[y:bb, x:rr] & (owned[y:bb, x:rr] != index)))
                if foreign == 0:
                    break
            if foreign:
                raise ValueError(f"Complete rectangular crop contains neighbour alpha at frame {index}; regenerate")
            rect = [x, y, rr-x, bb-y]
            rects.append(rect)
            frames.append({"index": index, "rect": rect,
                           "alphaBounds": [l-x, t-y, r-x, b-y],
                           "absoluteAlphaBounds": tight,
                           "bodyComponentArea": body["size"],
                           "bodySeedThreshold": body_seed_threshold,
                           "foreignAlphaPixelsInsideRect": foreign})
    return {"size": [width, height], "layout": [columns, rows], "rects": rects,
            "alphaBounds": [f["alphaBounds"] for f in frames], "frames": frames,
            "alphaExtrema": [int(a.min()), int(a.max())],
            "alphaBelow16Fraction": empty_fraction,
            "alphaZeroFraction": float((a == 0).mean()),
            "corner8x8MaxAlpha": corner_max,
            "edgeAlphaPixelCount": int(np.count_nonzero(np.concatenate(
                [mask[0], mask[-1], mask[:, 0], mask[:, -1]]))),
            "alphaThreshold": 16,
            "bodySeedThreshold": body_seed_threshold,
            "cropPolicy": "Complete alpha>=16 figures and detached parts retained; low-AA bridges use nearest alpha64 body seeds when necessary; no neighbour alpha; native pixels unchanged."}


def read_records(paths):
    result = {}
    for path in paths:
        data = json.loads(path.read_text(encoding="utf8"))
        if isinstance(data, list):
            entries = data
        elif "files" in data or "records" in data:
            entries = data.get("files", data.get("records"))
            if isinstance(entries, dict):
                entries = [dict(v, name=k) for k, v in entries.items()]
        else:
            entries = [data]
        for original in entries:
            entry = copy.deepcopy(original)
            value = entry.get("sourcePath") or entry.get("sourcePNG") or entry.get("name") or ""
            match = NAME.search(Path(value).name)
            weapon = entry.get("weaponId") or (match.group(1) if match else None)
            kind = entry.get("kind") or (match.group(2) if match else None)
            if weapon not in WEAPONS or kind not in KINDS:
                continue
            entry["recordPath"] = display(path)
            entry["recordDirectory"] = str(path.parent)
            entry["sourcePath"] = str(resolve(value or f"{weapon}/explore-{weapon}-{kind}.png", path.parent))
            result[(weapon, kind)] = entry
    return result


def get_item(value, index, default=None):
    if isinstance(value, dict):
        return value.get(str(index), value.get(index, default))
    if isinstance(value, list) and index < len(value):
        return value[index]
    return default


def provenance_hashes(record):
    """Retain hashes of supplied generation stages/rejected raw attempts too."""
    hashes = {}
    directory = Path(record.get("recordDirectory", HERE))
    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key not in ("recordDirectory",):
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str) and value.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            path = resolve(value, directory)
            if path.is_file():
                hashes[display(path)] = sha(path)
    visit(record)
    return hashes


def translation(old, new, roi, override=None, initial_radius=6, max_radius=32):
    """Existing lower-body binary-alpha IoU, accelerated by SciPy correlation.

    Search six pixels first; only expand for a low/edge match. This does not
    align a staff head, bow tip or single lowest boot, or modify image pixels.
    """
    x, y, width, height = map(int, roi)
    image_height, image_width = old.shape
    x, y = max(0, x), max(0, y)
    width, height = min(width, image_width-x), min(height, image_height-y)
    if min(width, height) <= 0:
        raise ValueError(f"Empty registration ROI: {roi}")
    original = old[y:y+height, x:x+width] >= 128
    if int(original.sum()) < 64:
        raise ValueError(f"Insufficient lower-body alpha in registration ROI {roi}")
    def score_at(dx, dy):
        candidate = np.zeros(original.shape, dtype=bool)
        nl, nt, nr, nb = max(0, x+dx), max(0, y+dy), min(image_width, x+dx+width), min(image_height, y+dy+height)
        if nr > nl and nb > nt:
            candidate[nt-y-dy:nb-y-dy, nl-x-dx:nr-x-dx] = new[nt:nb, nl:nr] >= 128
        union = int(np.count_nonzero(original | candidate))
        return float(np.count_nonzero(original & candidate) / union) if union else 0
    if override is not None:
        dx, dy = map(int, override)
        return {"bodyOnlyTranslationXY": [dx, dy], "lowerBodyMaskIoU": round(score_at(dx, dy), 6),
                "registrationROI": [x, y, width, height], "manualOverride": True, "searchRadius": 0}
    radius = initial_radius
    while True:
        padded = np.pad(new >= 128, radius)
        search = padded[y:y+height+2*radius, x:x+width+2*radius]
        intersections = np.rint(signal.correlate(search.astype(np.float32), original.astype(np.float32),
                                                mode="valid", method="fft"))
        integral = np.pad(search.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
        counts = integral[height:, width:] - integral[:-height, width:] - integral[height:, :-width] + integral[:-height, :-width]
        scores = intersections / np.maximum(1, int(original.sum()) + counts - intersections)
        best_score = float(scores.max())
        ys, xs = np.where(scores >= best_score - 1e-7)
        best = min(zip(xs, ys), key=lambda p: (abs(int(p[0])-radius)+abs(int(p[1])-radius), int(p[1]), int(p[0])))
        dx, dy = int(best[0])-radius, int(best[1])-radius
        if radius >= max_radius or (best_score >= .8 and max(abs(dx), abs(dy)) < radius):
            return {"bodyOnlyTranslationXY": [dx, dy], "lowerBodyMaskIoU": round(best_score, 6),
                    "registrationROI": [x, y, width, height], "manualOverride": False,
                    "searchRadius": radius, "atSearchBoundary": max(abs(dx), abs(dy)) == radius}
        radius = min(max_radius, 24 if radius < 24 else max_radius)


def base_key(actions, weapon, kind, layout):
    if kind == "idle" and list(layout) == [2, 2]:
        return "idle"
    action = "run" if kind.startswith("run-") else kind
    return f"{action}_{weapon}" if f"{action}_{weapon}" in actions else action


def sheet_rects(action, image):
    return action.get("frameRectsByImage", {}).get(image.removesuffix(".png"), action.get("perFrameRects"))


def measure_record(record, weapon, kind, manifest):
    path = Path(record["sourcePath"])
    a = alpha(path)
    layout = record.get("layout") or ([2, 2] if kind == "idle" and a.shape[1] > a.shape[0] else [4, 4])
    if isinstance(layout, dict):
        layout = [layout["columns"], layout["rows"]]
    key = record.get("baseActionKey") or base_key(manifest["actions"], weapon, kind, layout)
    original = manifest["actions"][key]
    images = list(dict.fromkeys(original.get("frameImages") or [original["image"]]))
    image = images[1 if kind == "run-b" else 0]
    target = resolve(record.get("editTarget") or record.get("targetPath") or record.get("targetPNG") or str(ACTOR / image), Path(record.get("recordDirectory", HERE)))
    old = alpha(target)
    if old.shape != a.shape:
        raise ValueError(f"Target/source native dimensions differ: {target} {old.shape} vs {path} {a.shape}; choose a matching base action and target")
    before_rects = record.get("targetRects") or sheet_rects(original, image)
    after = native_geometry(a, layout, record.get("frameRects"))
    if not before_rects or len(before_rects) != len(after["rects"]):
        raise ValueError(f"Target action {key} crop count differs from source layout")
    origins = original["perFrameOrigins"]
    registrations = []
    for index, old_rect in enumerate(before_rects):
        row, col = divmod(index, layout[0])
        if isinstance(origins, dict):
            ordinals = [i for i, name in enumerate(original["frameImages"])
                        if name == image and original["frameIndices"][i] == col]
            if not ordinals:
                raise ValueError(f"Missing original run phase {key}/{image}/{col}")
            point = origins[manifest["directions"][row]][ordinals[0]]
        else:
            point = origins[index]
        ground = [old_rect[0]+point[0], old_rect[1]+point[1]]
        stature = 1.556 / original["worldUnitsPerPixel"]
        # Accepted support/pelvis anchors bound this ROI; added gear above the
        # shoulders cannot change its height or position.
        left, top = round(ground[0]-.22*stature), round(ground[1]-.45*stature)
        right, bottom = round(ground[0]+.22*stature), min(old.shape[0], round(ground[1])+2)
        roi = get_item(record.get("registrationRois"), index, [max(0, left), max(0, top), right-max(0, left), bottom-max(0, top)])
        reg = translation(old, a, roi, get_item(record.get("registrationOverrides"), index))
        reg.update({"index": index, "oldRect": old_rect, "oldAbsoluteOrigin": ground})
        registrations.append(reg)
    raw_value = record.get("rawOutputPath") or record.get("generatedPath") or record.get("rawPNG")
    raw = resolve(raw_value, Path(record.get("recordDirectory", HERE))) if raw_value else None
    runtime = ACTOR / "carry-v1" / path.name
    source_sha = sha(path)
    issues = []
    if after["alphaBelow16Fraction"] < .65 or after["corner8x8MaxAlpha"] >= 16:
        issues.append("Source background fails transparency review (empty fraction/corner alpha)")
    if raw is None or not raw.exists():
        issues.append("Missing raw imagegen output path; provenance cannot prove unchanged PNG bytes")
    elif sha(raw) != source_sha:
        issues.append("Raw/source PNG SHA256 mismatch")
    weak = [r["index"] for r in registrations if r["lowerBodyMaskIoU"] < .65 or r.get("atSearchBoundary")]
    if weak and not record.get("registrationAccepted"):
        issues.append(f"Lower-body registration needs visual review/explicit registrationAccepted: {weak}")
    inputs = {}
    input_values = list(record.get("inputs") or [])
    for field in ("reference", "appearanceReferencePNG", "sourceDesign"):
        if record.get(field):
            input_values.append(record[field])
    for value in input_values:
        p = resolve(value, Path(record.get("recordDirectory", HERE)))
        if p.exists():
            inputs[display(p)] = sha(p)
        else:
            issues.append(f"Missing recorded input: {value}")
    after.update({"weaponId": weapon, "kind": kind, "baseActionKey": key,
                  "sourcePNG": display(path), "sourceSHA256": source_sha,
                  "rawOutputPNG": display(raw) if raw else None,
                  "rawSHA256": sha(raw) if raw and raw.exists() else None,
                  "runtimePNG": display(runtime), "runtimeSHA256": sha(runtime) if runtime.exists() else None,
                  "rawSourceSHAEqual": bool(raw and raw.exists() and sha(raw) == source_sha),
                  "sourceRuntimeSHAEqual": runtime.exists() and sha(runtime) == source_sha,
                  "editTargetPNG": display(target), "editTargetSHA256": sha(target),
                  "recordPath": record.get("recordPath"), "inputSHA256s": inputs,
                  "provenanceFileSHA256": sha(resolve(record["recordPath"])) if record.get("recordPath") else None,
                  "recordedPathSHA256s": provenance_hashes(record),
                  "generationRecord": {k: copy.deepcopy(v) for k, v in record.items() if k != "recordDirectory"},
                  "registrations": registrations, "issues": issues,
                  "worldUnitsPerPixel": original["worldUnitsPerPixel"],
                  "pixelEditsAfterGeneration": False})
    return after


def make_action(weapon, kind, sheets, manifest):
    first = sheets[(weapon, "run-a" if kind == "run" else kind)]
    original = manifest["actions"][first["baseActionKey"]]
    action = copy.deepcopy(original)
    image = "carry-v1/" + Path(first["sourcePNG"]).name
    action.update({"image": image, "perFrameRects": copy.deepcopy(first["rects"]),
                   "alphaBounds": copy.deepcopy(first["alphaBounds"]), "alphaBoundsThreshold": 16,
                   "worldUnitsPerPixel": original["worldUnitsPerPixel"],
                   "originMethod": "Accepted support/pelvis origin transferred by lower-body alpha IoU; complete alpha>=16 native crop. Original action UPP retained; no gear-height normalization or pixel edits."})
    used = [first]
    if kind == "run":
        second = sheets[(weapon, "run-b")]
        if second["baseActionKey"] != first["baseActionKey"]:
            raise ValueError(f"Run A/B base actions disagree: {weapon}")
        used.append(second)
        old_images = list(dict.fromkeys(original["frameImages"]))
        if len(old_images) != 2 or len(original["frameImages"]) != 8:
            raise ValueError("Expected existing native eight-phase A/B run")
        mapped = {name: sheet for name, sheet in zip(old_images, used)}
        action["frameImages"] = ["carry-v1/"+Path(mapped[n]["sourcePNG"]).name for n in original["frameImages"]]
        action["frameRectsByImage"] = {("carry-v1/"+Path(s["sourcePNG"]).name).removesuffix(".png"): copy.deepcopy(s["rects"]) for s in used}
        origins, bounds = {}, {}
        for row, direction in enumerate(manifest["directions"]):
            phases = [(mapped[name], row*original.get("columns", 4)+original["frameIndices"][phase])
                      for phase, name in enumerate(original["frameImages"])]
            ground_dy = statistics.median(s["registrations"][index]["bodyOnlyTranslationXY"][1] for s, index in phases)
            points, phase_bounds = [], []
            for phase, (sheet, index) in enumerate(phases):
                rect = sheet["rects"][index]
                reg = sheet["registrations"][index]
                ground = reg["oldAbsoluteOrigin"]
                points.append([round(ground[0]+reg["bodyOnlyTranslationXY"][0]-rect[0], 3),
                               round(ground[1]+ground_dy-rect[1], 3)])
                phase_bounds.append(sheet["alphaBounds"][index])
            origins[direction], bounds[direction] = points, phase_bounds
        action["perFrameOrigins"], action["perPhaseAlphaBounds"] = origins, bounds
        if set(action["frameRectsByImage"]) != {p.removesuffix(".png") for p in action["frameImages"]}:
            raise ValueError("Run image map keys do not match complete runtime paths")
    else:
        points = []
        for rect, reg in zip(first["rects"], first["registrations"]):
            ground, delta = reg["oldAbsoluteOrigin"], reg["bodyOnlyTranslationXY"]
            points.append([round(ground[0]+delta[0]-rect[0], 3), round(ground[1]+delta[1]-rect[1], 3)])
        action["perFrameOrigins"] = points
    for name in ("sourcePNG", "sourcePNGSHA256", "sourcePNGs", "sourcePNGSHA256s"):
        action.pop(name, None)
    action["sourcePNGs"] = [s["sourcePNG"] for s in used]
    action["sourcePNGSHA256s"] = [s["sourceSHA256"] for s in used]
    for field in TEMPORAL:
        if action.get(field) != original.get(field):
            raise ValueError(f"Temporal field changed: {weapon}/{kind}/{field}")
    return action


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--records", action="append", type=Path, help="Explicit provenance JSON (repeatable); default discovers generation-records.json and *.provenance.json")
    parser.add_argument("--manifest", type=Path, default=ACTOR / "manifest.json")
    parser.add_argument("--weapons", default=",".join(WEAPONS), help="Comma-separated weapon IDs, default all seven")
    parser.add_argument("--idle-mode", choices=("auto", "separate", "walk-first", "neutral-dodge"), default="auto",
                        help="neutral-dodge prefers independent idle, otherwise reviewed neutral dodge col0; separate requires independent idle")
    parser.add_argument("--require-all", action="store_true", help="Fail unless each selected weapon has idle/walk/run A+B/dodge")
    parser.add_argument("--require-interact", action="store_true")
    parser.add_argument("--report", type=Path, help="Write full JSON measurements/actions; no PNG/manifest mutation")
    parser.add_argument("--install", action="store_true", help="Copy unchanged PNG bytes and append exploration keys to manifest")
    args = parser.parse_args()
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    combat = {k: copy.deepcopy(v) for k, v in manifest["actions"].items() if not k.startswith("explore_")}
    if len(combat) != 60:
        raise ValueError(f"Expected exactly 60 preserved combat actions, got {len(combat)}")
    combat_images = sorted({name for action in combat.values() for name in (action.get("frameImages") or [action["image"]])})
    combat_image_hashes = {name: sha(ACTOR/name) for name in combat_images}
    weapons = tuple(w.strip() for w in args.weapons.split(",") if w.strip())
    if any(w not in WEAPONS for w in weapons):
        raise ValueError("Unknown weapon ID")
    paths = args.records or ([HERE / "generation-records.json"] if (HERE / "generation-records.json").exists() else [])
    if not args.records:
        paths = list(paths) + sorted(HERE.rglob("*.provenance.json"))
    records = read_records([p.resolve() for p in paths])
    for weapon in weapons:
        for kind in KINDS:
            path = HERE / weapon / f"explore-{weapon}-{kind}.png"
            if path.exists() and (weapon, kind) not in records:
                records[(weapon, kind)] = {"sourcePath": str(path)}
    sheets, actions, errors, missing = {}, {}, [], []
    for (weapon, kind), record in records.items():
        if weapon not in weapons:
            continue
        if args.idle_mode == "walk-first" and kind == "idle":
            continue
        path = Path(record["sourcePath"])
        if not path.exists():
            errors.append(f"Missing source: {path}")
            continue
        try:
            print(f"Measuring {weapon}/{kind}", file=sys.stderr, flush=True)
            sheets[(weapon, kind)] = measure_record(record, weapon, kind, manifest)
        except (ValueError, KeyError, IndexError) as error:
            errors.append(f"{weapon}/{kind}: {error}")
    aliases = []
    for weapon in weapons:
        for kind in ("idle", "walk", "run", "dodge", "interact"):
            key = f"explore_{kind}_{weapon}"
            available = (weapon, kind) in sheets if kind != "run" else all((weapon, p) in sheets for p in ("run-a", "run-b"))
            if available:
                try:
                    actions[key] = make_action(weapon, kind, sheets, manifest)
                except (ValueError, KeyError, IndexError) as error:
                    errors.append(f"{key}: {error}")
            elif kind == "idle" and args.idle_mode == "neutral-dodge" and (weapon, "dodge") in sheets:
                # This explicit mode attests that dodge col0 was visually
                # reviewed as a neutral both-feet-grounded standing pose.
                # Retain the complete dodge image, original UPP and anchors.
                alias = make_action(weapon, "dodge", sheets, manifest)
                alias.update({"frames": 1, "frameIndices": [0], "fps": 1, "loop": True})
                alias.pop("phaseStarts", None)
                actions[key] = alias
                aliases.append({"action": key, "source": f"explore_dodge_{weapon}", "column": 0,
                                "materialScope": "Reviewed neutral standing frame from complete back-carry dodge PNG; no separate idle PNG; dodge UPP/support anchors retained."})
            elif (kind == "idle" and (weapon, "walk") in sheets
                  and (args.idle_mode == "walk-first" or
                       (args.idle_mode == "auto" and records.get((weapon, "walk"), {}).get("neutralFirstColumn")))):
                # A reviewed walk has a neutral first column; the remaining
                # native per-direction indices still address all 16 cells.
                alias = make_action(weapon, "walk", sheets, manifest)
                alias.update({"frames": 1, "frameIndices": [0], "fps": 1, "loop": True})
                alias.pop("phaseStarts", None)
                actions[key] = alias
                aliases.append({"action": key, "source": f"explore_walk_{weapon}", "column": 0})
            elif kind != "interact" or args.require_interact:
                missing.append(key)
    issues = [f"{w}/{k}: {issue}" for (w, k), sheet in sheets.items() for issue in sheet["issues"]]
    errors.extend(f"Required action missing: {key}" for key in missing
                  if args.require_all or (args.require_interact and key.startswith("explore_interact_")))
    material_scope = {"sourcePNGCount": len(sheets),
                      "sourceKindsByWeapon": {weapon: [kind for kind in KINDS if (weapon, kind) in sheets] for weapon in weapons},
                      "independentIdleWeapons": [weapon for weapon in weapons if (weapon, "idle") in sheets],
                      "neutralDodgeIdleWeapons": [weapon for weapon in weapons if any(
                          alias["action"] == f"explore_idle_{weapon}" and alias["source"] == f"explore_dodge_{weapon}" for alias in aliases)],
                      "idleMode": args.idle_mode,
                      "drawStowTransitions": "No authored transition PNGs; pose switching is handled by existing runtime routing."}
    report = {"version": "weapon-carry-v1", "status": "measured; not installed", "directions": manifest["directions"],
              "actions": actions, "records": {f"{w}/{k}": s for (w, k), s in sheets.items()},
              "idleAliases": aliases, "missingActions": missing, "errors": errors, "sourceIssues": issues,
              "materialScope": material_scope,
              "manifestInputSHA256": hashlib.sha256(manifest_bytes).hexdigest(),
              "preservedCombatActionCount": len(combat), "combatActionsSHA256": canonical_sha(combat),
              "retainedCombatRuntimeSHA256s": combat_image_hashes,
              "pixelEditsAfterGeneration": False,
              "dependencies": "Existing Pillow/numpy/scipy; scipy.ndimage.label/find_objects and scipy.signal.correlate; no new dependency.",
              "worldScalePolicy": "Original accepted action-level worldUnitsPerPixel retained exactly; gear alpha never normalizes body size.",
              "originPolicy": "Original support/pelvis transferred by lower-body binary-alpha IoU; running retains original eight support phases plus median per-direction registration Y."}
    if args.install:
        if errors or issues or not actions:
            errors.append("Installation refused: resolve measurement/provenance/source issues first")
        else:
            if args.manifest.read_bytes() != manifest_bytes:
                raise ValueError("Manifest changed during measurement; rerun before installing")
            backup = HERE / "manifest-before-carry-v1.json"
            if not backup.exists():
                backup.write_bytes(manifest_bytes)
            else:
                old_combat = {k: v for k, v in json.loads(backup.read_bytes())["actions"].items() if not k.startswith("explore_")}
                if old_combat != combat:
                    raise ValueError("Prior carry backup has different combat actions; do not overwrite")
            runtime = ACTOR / "carry-v1"
            runtime.mkdir(parents=True, exist_ok=True)
            for sheet in sheets.values():
                source, destination = ROOT / sheet["sourcePNG"], ROOT / sheet["runtimePNG"]
                shutil.copyfile(source, destination)
                if sha(destination) != sheet["sourceSHA256"]:
                    raise ValueError(f"Copied bytes differ: {destination}")
                sheet["runtimeSHA256"] = sha(destination)
                sheet["sourceRuntimeSHAEqual"] = True
            merged = copy.deepcopy(manifest)
            merged["actions"].update(actions)
            merged["revision"] = "concept-image-2d-weapon-carry-v1"
            merged["carryDesign"] = "docs/superpowers/specs/2026-11-06-weapon-carry-design.md"
            if {k: merged["actions"][k] for k in combat} != combat:
                raise ValueError("Combat action changed during merge")
            args.manifest.write_text(json.dumps(merged, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
            report["status"] = "installed unchanged PNG bytes and exploration action metadata"
            report["manifestOutputSHA256"] = sha(args.manifest)
    if not args.install and args.manifest.read_bytes() != manifest_bytes:
        raise ValueError("Read-only measurement unexpectedly changed manifest")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    summary = {k: report[k] for k in ("status", "preservedCombatActionCount", "combatActionsSHA256", "idleAliases", "materialScope", "missingActions", "errors", "sourceIssues")}
    summary.update({"sourceCount": len(sheets), "actionCount": len(actions), "actionKeys": list(actions),
                    "report": str(args.report.resolve()) if args.report else None,
                    "minBodyIoU": min((r["lowerBodyMaskIoU"] for s in sheets.values() for r in s["registrations"]), default=None)})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if errors or (args.install and issues) else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
