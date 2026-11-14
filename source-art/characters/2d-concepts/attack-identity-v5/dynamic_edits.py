"""Local, pose-aligned waist kit transfers from existing same-action artwork.

Default prepares a bounded four-facing pilot.  --batch prepares all 148 selected
non-static physical frames.  Nothing is packed or installed by this script.
The source and target crop bytes are loaded from the recorded runtime inventory;
only a colour/pose-gated waist region is composited.  Limbs, face, weapons and
lower-body pixels are hard protected.  Final death poses remain manual-review.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
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
OUT = HERE / "edits/dynamic"
spec = importlib.util.spec_from_file_location("dynamic_pose_helpers", HERE / "prepare_v5.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
prepare = helpers.prepare


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def sha_pixels(image):
    return hashlib.sha256(image.tobytes()).hexdigest()


def source_action(record):
    """Return the matching donor action, retaining phase and facing semantics."""
    refs = record["refs"]
    for ref in refs:
        action = ref["action"]
        if action in ("walk", "walk_W01"):
            return "walk_W02", ref["phase"]
        if action == "walk_W07":
            return "walk_W08", ref["phase"]
        if action in ("walk_W11", "walk_staff"):
            return "walk_W02", ref["phase"]
        if action in helpers.SPECIALS:
            return action+"_W07", ref["phase"]
        if action in {"explore_dodge_"+w for w in helpers.NON_BOW_CARRY}:
            return "explore_dodge_W07", ref["phase"]
    raise ValueError("No bounded donor route: "+str((record["image"], record["index"])))


def crop_frame(record, sheets):
    x, y, w, h = record["rect"]
    return sheets[record["image"]].crop((x, y, x+w, y+h))


def center(pose, kind):
    pts = [pose["joints"][side+"_"+kind]["native"] for side in ("left", "right")]
    return np.mean(pts, axis=0) if all(p is not None for p in pts) else None


def basis(pose):
    shoulder, hip = center(pose, "shoulder"), center(pose, "hip")
    if shoulder is None or hip is None:
        return None
    vector = hip-shoulder
    length = np.linalg.norm(vector)
    if length < 20:
        return None
    axis = vector/length
    return shoulder, hip, axis, np.array([-axis[1], axis[0]]), float(length)


def capsule(shape, a, b, radius):
    yy, xx = np.mgrid[:shape[0], :shape[1]]
    vx, vy = b[0]-a[0], b[1]-a[1]
    t = np.clip(((xx-a[0])*vx+(yy-a[1])*vy)/max(vx*vx+vy*vy, .001), 0, 1)
    return (xx-a[0]-t*vx)**2+(yy-a[1]-t*vy)**2 <= radius*radius


def materials(array):
    rgb = array[..., :3].astype(float)
    r, g, b = np.moveaxis(rgb, -1, 0)
    maximum, minimum = rgb.max(-1), rgb.min(-1)
    wine = (r > g+7) & (r > b+8) & (g-b < 14) & (r > 35)
    leather = (r > g+5) & (g > b+4) & (r > 38) & (r-g < 68)
    neutral = (maximum-minimum < 24) & (maximum < 170)
    # Skin is protected separately from the warm leather belt and pouches.
    skin = (r > g+14) & (g > b+6) & (r > 105) & (g > 65) & (b > 45)
    metal = (maximum-minimum < 26) & (maximum > 160)
    return wine, leather, neutral, skin, metal


def alpha_support(array):
    return array[..., 3] >= 32


def cloth_location(image):
    array = np.asarray(image)
    wine = materials(array)[0] & (array[..., 3] >= 128)
    wine = ndi.binary_closing(wine, iterations=2)
    labels, count = ndi.label(wine)
    if not count:
        return None
    sizes = np.bincount(labels.ravel()); sizes[0] = 0
    mask = labels == sizes.argmax()
    yy, xx = np.nonzero(mask)
    if len(xx) < 60:
        return None
    points = np.column_stack((xx, yy)).astype(float)
    centroid = points.mean(0)
    values, vectors = np.linalg.eigh(np.cov(points.T))
    return centroid, vectors[:, -1], float(values[-1]/max(values[0], 1))


def source_equipment_guard(array, body_basis, scale):
    """Find elongated brown upper-body tubes before extracting a waist band.

    The bow/quiver art has no editable layers.  This conservative colour and
    shape guard removes a quiver tube plus its end cap, rather than assuming
    every warm pixel near the belt belongs to a pouch.
    """
    _, hip, axis, perp, length = body_basis
    yy, xx = np.mgrid[:array.shape[0], :array.shape[1]]
    along = (xx-hip[0])*axis[0]+(yy-hip[1])*axis[1]
    across = (xx-hip[0])*perp[0]+(yy-hip[1])*perp[1]
    rgb = array[..., :3].astype(int)
    rr, gg, bb = np.moveaxis(rgb, -1, 0)
    brown = ((rr-gg > 13) & (gg-bb > 10) & (rr > 60) & (array[..., 3] >= 160)
             & (along > -1.45*length) & (along < -.06*length)
             & (abs(across)*scale < 110))
    brown = ndi.binary_closing(brown, iterations=max(1, round(2/scale)))
    brown = ndi.binary_opening(brown, iterations=max(1, round(2/scale)))
    labels, count = ndi.label(brown)
    protected = np.zeros(array.shape[:2], bool)
    regions = []
    for label in range(1, count+1):
        py, px = np.nonzero(labels == label)
        if len(px)*scale*scale < 100:
            continue
        points = np.column_stack((px, py)).astype(float)
        center = points.mean(0)
        eigenvalues, eigenvectors = np.linalg.eigh(np.cov(points.T))
        if eigenvalues[-1]/max(eigenvalues[0], 1) < 5:
            continue
        direction = eigenvectors[:, -1]
        normal = np.array([-direction[1], direction[0]])
        projected = (points-center)@direction
        lateral = abs((points-center)@normal)
        lo, hi = np.percentile(projected, [2, 98])
        if (hi-lo)*scale < 45:
            continue
        radius = float(np.clip(np.percentile(lateral, 97)+4/scale, 7/scale, 25/scale))
        a, b = center+direction*(lo-15/scale), center+direction*(hi+18/scale)
        protected |= capsule(array.shape[:2], a, b, radius)
        regions.append(dict(center=center.tolist(), endpoints=[a.tolist(), b.tolist()], radius=radius,
                            lengthReviewPixels=float((hi-lo)*scale)))
    return protected, regions


def donor_cloth_fallback(target, donor, target_pose, donor_pose, target_record, donor_record):
    """Conservative same-phase garment registration for missing donor poses.

    These are inferred edit guides, not new detected anatomy.  They only make
    a bounded waist candidate reviewable; every such edit remains manual.
    """
    target_basis = basis(target_pose)
    tc, sc = cloth_location(target), cloth_location(donor)
    if target_basis is None or tc is None or sc is None:
        return donor_pose, False
    _, _, target_axis, _, _ = target_basis
    source_axis = sc[1] if sc[2] > 1.2 else target_axis.copy()
    if np.dot(source_axis, target_axis) < 0:
        source_axis = -source_axis
    # The matched action/direction/phase should not require a large rotation.
    if np.dot(source_axis, target_axis) < .75:
        source_axis = target_axis.copy()
    target_perp = np.array([-target_axis[1], target_axis[0]])
    source_perp = np.array([-source_axis[1], source_axis[0]])
    scale = donor_record["scale"]/target_record["scale"]
    forward = scale*(np.outer(target_axis, source_axis)+np.outer(target_perp, source_perp))
    inverse = np.linalg.inv(forward)
    result = dict(donor_pose, joints={})
    for name, joint in target_pose["joints"].items():
        native = joint["native"]
        inferred = (sc[0]+inverse@(np.array(native)-tc[0])).tolist() if native is not None else None
        result["joints"][name] = dict(joint, native=inferred, usable=False,
            confidence=min(joint["confidence"], .35),
            reason="inferred same-pose cloth registration; manual review, not detected anatomy")
    result["garmentRegistrationFallback"] = True
    return result, True


def affine_layer(image, matrix, offset, size):
    inverse = np.linalg.inv(matrix)
    shift = -inverse @ offset
    coeff = (inverse[0, 0], inverse[0, 1], shift[0],
             inverse[1, 0], inverse[1, 1], shift[1])
    return image.convert("RGBa").transform(size, Image.Transform.AFFINE, coeff,
        Image.Resampling.BICUBIC).convert("RGBA")


def transplant(target, donor, target_pose, donor_pose, target_record, donor_record):
    original = np.asarray(target).copy()
    ta = original
    sa = np.asarray(donor)
    tb, sb = basis(target_pose), basis(donor_pose)
    if tb is None or sb is None:
        return target.copy(), Image.new("L", target.size), Image.new("L", target.size), dict(
            changedPixels=0, status="source-preserved", reason="missing usable torso basis", outsideGuardChanged=0)
    ts, th, tu, tv, tl = tb
    ss, sh, su, sv, sl = sb
    along_scale = tl/sl
    across_scale = donor_record["scale"]/target_record["scale"]
    if not .55 < along_scale < 1.85 or not .5 < across_scale < 2:
        return target.copy(), Image.new("L", target.size), Image.new("L", target.size), dict(
            changedPixels=0, status="source-preserved", reason="pose alignment ratio out of bounds", outsideGuardChanged=0)
    matrix = along_scale*np.outer(tu, su)+across_scale*np.outer(tv, sv)
    offset = th-matrix@sh
    sy, sx = np.mgrid[:donor.height, :donor.width]
    along = (sx-sh[0])*su[0]+(sy-sh[1])*su[1]
    across = (sx-sh[0])*sv[0]+(sy-sh[1])*sv[1]
    swine, sleather, sneutral, sskin, smetal = materials(sa)
    # Costume-only band: belt and pouches below the upper torso/quiver, above
    # the legs.  Dilate broad cloth support so real pouch silhouettes survive.
    band = (along > -.32*sl) & (along < .29*sl)
    broad = ndi.binary_opening(alpha_support(sa), iterations=max(2, round(3/donor_record["scale"])))
    # Width is measured in the existing 400px/world review coordinates rather
    # than the tiny projected hip separation of a side-facing pose.
    width = (88 if donor_record["direction"] in ("up", "down") else 73)/donor_record["scale"]
    band &= abs(across) < width
    cloth_seed = ndi.binary_dilation(swine, iterations=max(1, round(22/donor_record["scale"])))
    source_mask = band & broad & (swine | sleather) & cloth_seed
    equipment_guard, equipment_regions = source_equipment_guard(sa, sb, donor_record["scale"])
    source_mask &= ~equipment_guard
    # Explicitly reject skin, bright weapon glints and thin detached equipment.
    # Warm leather and skin share RGB ranges.  Skin is excluded by the limb
    # capsules below, never by a global warm-colour veto that erases pouches.
    source_mask &= ~ndi.binary_dilation(smetal, iterations=max(1, round(3/donor_record["scale"])))
    # Source arms are never part of the transferred costume.  Existing source
    # joints are useful even when one side is occluded; expand conservatively.
    for side in ("left", "right"):
        for p1, p2, radius in (("shoulder", "elbow", 24), ("elbow", "wrist", 23)):
            a = donor_pose["joints"][side+"_"+p1]["native"]
            b = donor_pose["joints"][side+"_"+p2]["native"]
            if a is not None and b is not None:
                source_mask &= ~capsule(sa.shape[:2], a, b, radius/donor_record["scale"])
    source_layer = sa.copy()
    source_layer[~source_mask] = 0
    warped = affine_layer(Image.fromarray(source_layer), matrix, offset, target.size)
    wa = np.asarray(warped)
    ty, tx = np.mgrid[:target.height, :target.width]
    talong = (tx-th[0])*tu[0]+(ty-th[1])*tu[1]
    tacross = (tx-th[0])*tv[0]+(ty-th[1])*tv[1]
    twine, tleather, tneutral, tskin, tmetal = materials(ta)
    target_band = (talong > -.34*tl) & (talong < .31*tl)
    guard = ~target_band
    # Protect the target's original trousers and all lower leg/boot pixels.
    leg_guard = (talong > -.04*tl) & tneutral & alpha_support(ta)
    guard |= ndi.binary_dilation(leg_guard, iterations=max(1, round(1/target_record["scale"])))
    guard |= ndi.binary_dilation(tmetal, iterations=max(1, round(2/target_record["scale"])))
    for side in ("left", "right"):
        for p1, p2, radius in (("shoulder", "elbow", 25), ("elbow", "wrist", 25)):
            a = target_pose["joints"][side+"_"+p1]["native"]
            b = target_pose["joints"][side+"_"+p2]["native"]
            if a is not None and b is not None:
                guard |= capsule(ta.shape[:2], a, b, radius/target_record["scale"])
    # Preserve thin target equipment even if it crosses the waist band.
    broad_target = ndi.binary_opening(alpha_support(ta), iterations=max(2, round(4/target_record["scale"])))
    thin = alpha_support(ta) & ~broad_target
    guard |= ndi.binary_dilation(thin, iterations=max(1, round(2/target_record["scale"])))
    # Solid original pixels may only be replaced if they are existing waist
    # fabric/leather.  Do not paste donor clothing over unknown limb pixels.
    replaceable = twine | tleather | (ta[..., 3] < 16)
    permitted = target_band & ~guard & replaceable & (wa[..., 3] > 0)
    # Feather only inward inside the permitted region; outside remains byte
    # exact, including transparent RGB and antialiased source contours.
    feather = np.clip(ndi.distance_transform_edt(permitted)/(1.6/target_record["scale"]), 0, 1)
    mask = Image.fromarray(np.uint8(np.rint(feather*255)))
    composed = Image.alpha_composite(target, warped)
    result = Image.composite(composed, target, mask)
    out = np.asarray(result)
    changed = np.any(out != original, axis=-1)
    outside = int((changed & (~permitted | guard)).sum())
    if outside:
        raise RuntimeError("Pixel transfer escaped bounded costume mask")
    protected_leg_changes = int((changed & leg_guard).sum())
    if protected_leg_changes:
        raise RuntimeError("Original leg pixels changed")
    return result, mask, Image.fromarray(np.uint8(guard)*255), dict(
        status="candidate", changedPixels=int(changed.sum()), permittedPixels=int(permitted.sum()),
        originalLegPixelsProtected=int(leg_guard.sum()), originalLegPixelChanges=protected_leg_changes,
        outsideGuardChanged=outside, targetPixelsPreserved=int((~changed).sum()),
        targetTorsoLengthPixels=tl, donorTorsoLengthPixels=sl,
        affineMatrix=matrix.tolist(), affineOffset=offset.tolist(), alongScale=along_scale,
        acrossScale=across_scale, manualReview=not target_pose["waistUsable"],
        excludedSourceEquipmentRegions=equipment_regions,
        armProtectionReliable=target_pose["armProtectionReliable"],
        originalRGBA_SHA256=sha_pixels(target), candidateRGBA_SHA256=sha_pixels(result),
        review="generation-free candidate; waist, arms, equipment and seam require visual acceptance")


def normalized(crop, record, size=(512, 768), anchor=(256, 712)):
    s = record["scale"]
    ox, oy = record["origin"]
    return crop.transform(size, Image.Transform.AFFINE,
        (1/s, 0, ox-anchor[0]/s, 0, 1/s, oy-anchor[1]/s), Image.Resampling.BICUBIC)


def board(results, path, full=False):
    # Original / donor / candidate / edit heatmap.  All share world pixel scale.
    cell_w, cell_h = (360, 290) if full else (155, 250)
    im = Image.new("RGB", (4*cell_w, len(results)*cell_h), "#25272a")
    draw = ImageDraw.Draw(im)
    for row, r in enumerate(results):
        for col, (title, crop, rec) in enumerate([
            ("target", r["original"], r["record"]), ("donor", r["donor"], r["donor_record"]),
            ("candidate", r["candidate"], r["record"]), ("edit mask", r["mask"].convert("RGBA"), r["record"])]):
            pic = (normalized(crop, rec, (1200, 900), (600, 780)).resize((360, 270), Image.Resampling.LANCZOS)
                   if full else normalized(crop, rec).resize((154, 230), Image.Resampling.LANCZOS))
            x, y = col*cell_w, row*cell_h+20
            im.paste(pic, (x, y), pic)
            draw.text((x+2, row*cell_h+2), title, fill="#f1ede4")
        draw.text((3*cell_w+2, row*cell_h+17), f'{r["record"]["direction"]} #{r["record"]["index"]}', fill="#e7bd68")
        draw.text((3*cell_w+2, row*cell_h+32), r["record"]["action"][:23], fill="#e7bd68")
    im.save(path, quality=88)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", action="store_true")
    args = parser.parse_args()
    inventory = read(HERE / "inventory.json")
    if prepare.digest(prepare.MANIFEST) != inventory["manifestSHA256"]:
        raise RuntimeError("Runtime manifest changed after preparation")
    manifest = read(prepare.MANIFEST)
    frames = {(r["image"], r["index"]):r for r in inventory["frames"]}
    selected = read(HERE / "selection.json")["frames"]
    poses = read(HERE / "pose-data.json")
    current_pose = {(r["image"], r["index"]):r for r in poses["frames"]}
    old_inventory = {(r["image"], r["index"]):r for r in read(helpers.V4/"inventory.json")["frames"]}
    old_pose = {(r["image"], r["index"]):r for r in read(helpers.V4/"pose-landmarks.json")["frames"]}
    targets = [r for r in selected if not current_pose[r["image"], r["index"]]["staticRole"]]
    if len(targets) != 148:
        raise RuntimeError("Dynamic candidate selection changed")
    if not args.batch:
        pilot_actions = {"walk_W01", "spell", "dodge", "explore_dodge_W11"}
        targets = [r for r in targets if any(v["action"] in pilot_actions and v["phase"] == 1 for v in r["refs"])]
    routes = []
    names = set()
    for target in targets:
        action, phase = source_action(target)
        donor = prepare.find(frames, action, target["direction"], phase)
        routes.append((target, donor, action, phase))
        names |= {target["image"], donor["image"]}
    hashes = {r["image"]:r["sha256"] for r in inventory["images"]}
    sheets = {}
    for name in names:
        if prepare.digest(prepare.ACTOR/name) != hashes[name]:
            raise RuntimeError("Source image changed: "+name)
        sheets[name] = Image.open(prepare.ACTOR/name).convert("RGBA")
    stage = OUT if args.batch else OUT/"pilot"
    (stage/"frames").mkdir(parents=True, exist_ok=True)
    (stage/"reports").mkdir(parents=True, exist_ok=True)
    edits, reports, samples = [], [], []
    for target, donor, action, phase in routes:
        key = target["image"], target["index"]
        dkey = donor["image"], donor["index"]
        tp = current_pose[key]
        dp = helpers.adapt_pose(donor, old_inventory.get(dkey), old_pose.get(dkey), sheets[donor["image"]])
        original, source = crop_frame(target, sheets), crop_frame(donor, sheets)
        used_fallback = False
        if basis(dp) is None:
            dp, used_fallback = donor_cloth_fallback(original, source, tp, dp, target, donor)
        candidate, mask, guard, report = transplant(original, source, tp, dp, target, donor)
        report["garmentRegistrationFallback"] = used_fallback
        report["manualReview"] = bool(not tp["waistUsable"] or used_fallback)
        filename = target["image"].replace("/", "__").removesuffix(".png")+f'--{target["index"]:02}.png'
        candidate.save(stage/"frames"/filename)
        mask.save(stage/"reports"/(filename.removesuffix(".png")+"-mask.png"))
        guard.save(stage/"reports"/(filename.removesuffix(".png")+"-guard.png"))
        edits.append(dict(image=target["image"], index=target["index"], cropPath="frames/"+filename,
                          origin=target["origin"], sourceManifestSHA256=inventory["manifestSHA256"],
                          donorImage=donor["image"], donorIndex=donor["index"], manualReview=report["manualReview"]))
        reports.append(dict(image=target["image"], index=target["index"], direction=target["direction"],
                            action=target["action"], donorAction=action, donorPhase=phase, **report))
        samples.append(dict(original=original, donor=source, candidate=candidate, mask=mask,
                            record=target, donor_record=donor))
    # Batch contacts are bounded pages, so normal review need not open 148 full
    # frames or upload the entire material set.
    for page, start in enumerate(range(0, len(samples), 4)):
        board(samples[start:start+4], stage/"reports"/f"comparison-{page:02}.jpg")
    manual_samples = [sample for sample, report in zip(samples, reports) if report.get("manualReview")]
    if manual_samples:
        board(manual_samples, stage/"reports"/"manual-death-review.jpg", full=True)
    write(stage/"edits.json", dict(edits=edits))
    summary = dict(status="candidate-only", mode="batch" if args.batch else "pilot",
                   frames=len(edits), selectedImages=len({r["image"] for r in edits}),
                   sourceManifestSHA256=inventory["manifestSHA256"],
                   changedPixels=sum(r["changedPixels"] for r in reports),
                   noChangeFrames=sum(r["changedPixels"] == 0 for r in reports),
                   outsideAllowedMaskChanges=sum(r["outsideGuardChanged"] for r in reports),
                   manualReviewFrames=[dict(image=r["image"], index=r["index"]) for r in reports if r.get("manualReview")],
                   sourceAssetsModified=False, newModelInference=False,
                   artAcceptance="pending; donor waist is a local candidate, never automatic acceptance",
                   framesReport=reports)
    write(stage/"reports"/"guard-validation.json", summary)
    print(json.dumps({k:summary[k] for k in ("status", "mode", "frames", "changedPixels", "noChangeFrames", "outsideAllowedMaskChanges")}))


if __name__ == "__main__":
    main()
