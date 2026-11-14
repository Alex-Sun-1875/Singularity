"""Local cloth grading for every exploration phase, using its standing palette.

Reuses the project's ICC-Lab low-frequency grader and installed Pillow/SciPy.
The masks are derived from each input pose, not copied from a sampled run pose.
No model/network calls, original copies, atlas writes, or alpha changes.
"""
from pathlib import Path
import importlib.util
import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
_spec = importlib.util.spec_from_file_location("qwen_existing_palette", HERE.parent / "palette/apply_palette.py")
palette = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(palette)

MATERIALS = palette.MATERIALS
Y, X = np.mgrid[:768, :512]
_REFERENCES = {}


def _standing(direction):
    if direction not in _REFERENCES:
        import runtime_frames
        _REFERENCES[direction] = runtime_frames.canvas(runtime_frames.read_manifest(), "idle", direction, 0)[0]
    return _REFERENCES[direction].copy()


def _mask_array(value):
    if value is None:
        return np.zeros((768, 512), bool)
    if not isinstance(value, Image.Image):
        value = Image.open(value)
    if value.size != (512, 768):
        raise ValueError("External protection mask must use the 512x768 canvas")
    return np.asarray(value.convert("L")) > 0


def _large_components(mask, minimum=24):
    labels, _ = ndi.label(mask)
    sizes = np.bincount(labels.ravel())
    allowed = sizes >= minimum
    allowed[0] = False
    return mask & allowed[labels]


def build_phase_masks(image, record, *, reference=False):
    """Conservative material ROIs on the current pose with semantic exclusions.

    The narrow waist transition is deliberately excluded where sleeves and
    trousers cannot be disambiguated. Warm leather/metal/skin and their edge
    neighbourhoods stay unchanged. Newly lengthened swords can supply their
    exact mask in record['palette_protect_mask'].
    """
    source = image.convert("RGBA")
    a = np.asarray(source)
    rgb = a[..., :3].astype(np.float32)
    r, g, b = np.moveaxis(rgb, -1, 0)
    lab = palette.lab8(source)
    l, ca, cb = np.moveaxis(lab, -1, 0)
    hsv = np.asarray(source.convert("RGB").convert("HSV"), np.float32)
    saturation = hsv[..., 1]
    opaque = ndi.binary_erosion(a[..., 3] >= 250, iterations=2)
    # Gold embroidery, bare skin, leather and the warm edge of those materials.
    warm = ((cb > 9) & (g - b > 4) & (r - g > 3)) | ((g - b > 10) & (r > b + 12))
    warm = ndi.binary_dilation(warm, iterations=2)
    protected = ~opaque | warm | (Y < 225)
    # Boots have some neutral shaded/highlight pixels. Anchor each boot on its
    # own brown leather pixels rather than a fixed p0 ankle rectangle.
    boot_seeds = (Y >= 445) & (cb > 7) & (ca > 4) & (g - b > 5) & (r - g > 3) & opaque
    boot_seeds = _large_components(boot_seeds, 45)
    boot_guard = ndi.binary_dilation(ndi.binary_closing(boot_seeds, iterations=3), iterations=9)
    protected |= boot_guard
    if not reference:
        protected |= _mask_array(record.get("palette_protect_mask"))
        protected |= _mask_array(record.get("hands_protection_mask"))
        protected |= _mask_array(record.get("body_boots_protection_mask"))

    # A pose-specific vest observation locates the hip; neutral clothes are then
    # separated anatomically. Sideways running legs may extend across the full
    # canvas below the hip, so no p0 polygon limits those legs.
    wine = ((ca >= 7) & (ca <= 35) & (cb >= -4) & (cb <= 11)
            & (r > g + 7) & (r > b + 7) & (g - b < 10)
            & (saturation >= 38) & (l > 18) & (l < 190)
            & (Y >= 225) & (Y <= 435))
    hip_samples = wine & (Y >= 330) & (Y <= 400) & opaque
    hip_x = float(np.median(X[hip_samples])) if hip_samples.sum() >= 50 else 256.0
    direction = record["direction"]
    side = direction in ("left", "right")
    hip_half_width = 54 if side else 70
    # Standing sample ROIs correspond to the established conservative references.
    # In motion, the broad neutral lower-body region follows all actual alphas.
    if reference:
        if side:
            pp = palette._polygons(palette.REF_PANTS["right"])
            ss = palette._polygons(palette.REF_SLEEVES["right"])
            if direction == "left":
                pp, ss = pp[:, ::-1], ss[:, ::-1]
        else:
            key = "front" if direction == "down" else "back"
            pp = palette._polygons(palette.REF_PANTS[key])
            ss = palette._polygons(palette.REF_SLEEVES[key])
    else:
        # A body adapter can supply its measured raised-waist boundary; otherwise
        # infer the known 22px front/back running adjustment from its record.
        raised = 22 if record["state"] == "run" and not side and record.get("body_warp_applied", False) else 0
        split = 402 - raised
        pp = (Y >= split + 22) | ((Y >= split - 18) & (np.abs(X - hip_x) <= hip_half_width))
        ss = (Y >= 242) & ((Y <= split - 12) | ((Y <= split + 22) & (np.abs(X - hip_x) > hip_half_width + 8)))
    neutral_sleeve = ((ca >= -4) & (ca <= 7) & (cb >= -11) & (cb <= 4)
                      & (saturation <= 72) & (l > 18) & (l < 178))
    neutral_pants = ((ca >= -4) & (ca <= 9) & (cb >= -7) & (cb <= 7)
                     & (saturation <= 78) & (l > 18) & (l < 200))
    if not reference:
        # A raised knee can occupy the same screen row as a forearm. Follow
        # each pose's connected neutral fabric from upper-arm/lower-leg seeds;
        # use the anatomical envelope only for ambiguous touching components.
        neutral = ((ca >= -5) & (ca <= 11) & (cb >= -12) & (cb <= 9)
                   & (saturation <= 95) & (l > 17) & (l < 210)
                   & ~protected & (Y >= 242))
        connected = ndi.binary_closing(neutral, iterations=2) & ~protected
        labels, count = ndi.label(connected, structure=np.ones((3,3)))
        upper_labels = np.bincount(labels[((Y >= 250) & (Y <= 330) & connected)], minlength=count+1)
        lower_labels = np.bincount(labels[((Y >= 415) & connected)], minlength=count+1)
        # A few neutral cuff/hand boundary pixels can touch the hip. Require
        # a substantial upper-arm seed, not a handful of pixels, to call the
        # whole connected leg/sleeve component ambiguous.
        is_sleeve = (upper_labels >= 200) & (lower_labels < 150)
        is_pants = (lower_labels >= 150) & (upper_labels < 200)
        is_sleeve[0] = is_pants[0] = False
        classified = is_sleeve[labels] | is_pants[labels]
        ss = (ss & ~classified) | is_sleeve[labels]
        pp = (pp & ~classified) | is_pants[labels]
    eligible = {
        "wine_vest": wine,
        "charcoal_sleeves": neutral_sleeve & ss,
        "dark_gray_trousers": neutral_pants & pp & (Y <= 711),
    }
    result = {}
    for material, mask in eligible.items():
        mask = _large_components(mask & ~protected, 18)
        feather = np.clip(ndi.distance_transform_edt(mask) / 1.5, 0, 1)
        result[material] = Image.fromarray(np.rint(mask * feather * 255).astype(np.uint8))
    return result, protected, {"hip_x": hip_x, "boot_guard_pixels": int(boot_guard.sum())}


def apply_colors(image, record, standing_reference=None):
    """Return graded RGBA and JSON-safe report; never modifies input or record.

    record['palette_protect_mask'] may be a PIL L mask from the sword adapter.
    record['body_warp_applied'] may identify raised front/back running waists.
    """
    source = image.convert("RGBA")
    if source.size != (512, 768):
        raise ValueError("Expected established 512x768 frame canvas")
    if record["state"] == "idle":
        return source.copy(), {"method": "standing palette baseline unchanged", "alpha_bytes_identical": True}
    reference = _standing(record["direction"]) if standing_reference is None else standing_reference.convert("RGBA")
    masks, protected, mask_report = build_phase_masks(source, record)
    ref_masks, _, _ = build_phase_masks(reference, record, reference=True)
    values, ref_values = palette.lab8(source), palette.lab8(reference)
    low = ndi.gaussian_filter(values[..., 0], 1.2)
    ref_low = ndi.gaussian_filter(ref_values[..., 0], 1.2)
    before = np.asarray(source).copy()
    result = source.copy()
    union = np.zeros((768, 512), bool)
    report = {
        "state": record["state"], "direction": record["direction"], "phase": record["phase"],
        "method": "per-pose cloth gates/hip observation and warm-feature/boot/exact-sword exclusions; existing ICC-Lab low-frequency material grader",
        "mask_geometry": mask_report, "materials": {},
    }
    for material in MATERIALS:
        mask, ref_mask = masks[material], ref_masks[material]
        sample, ref_sample = palette._samples(mask), palette._samples(ref_mask)
        row = {"before": palette.material_stats(source, mask),
               "standing": palette.material_stats(reference, ref_mask)}
        if min(int(sample.sum()), int(ref_sample.sum())) < 60:
            row["status"] = "skipped: fewer than 60 conservative pixels"
            report["materials"][material] = row
            continue
        sq = np.percentile(low[sample], [25, 50, 75])
        rq = np.percentile(ref_low[ref_sample], [25, 50, 75])
        scale = float(np.clip((rq[2] - rq[0]) / max(sq[2] - sq[0], 1), .90, 1.08))
        offset = float(rq[1] - scale * sq[1])
        chroma_delta = np.clip(np.median(ref_values[ref_sample, 1:], axis=0) - np.median(values[sample, 1:], axis=0), -7, 7)
        corrected = values.copy()
        corrected[..., 0] += np.clip(scale * low + offset - low, -36, 36) * np.clip((values[..., 0] - 15) / 22, 0, 1)
        corrected[..., 1:] += chroma_delta
        grade = palette.from_lab8(corrected).convert("RGBA")
        grade.putalpha(source.getchannel("A"))
        result = Image.composite(grade, result, mask)
        union |= np.asarray(mask) > 0
        row.update(status="calibrated", L_scale=scale, L_offset=offset,
                   chroma_delta_ab=chroma_delta.tolist(), after=palette.material_stats(result, mask))
        row["before_error_vs_standing"] = palette._median_error(row["before"], row["standing"])
        row["after_error_vs_standing"] = palette._median_error(row["after"], row["standing"])
        report["materials"][material] = row
    result.putalpha(source.getchannel("A"))
    after = np.asarray(result)
    assert np.array_equal(after[..., 3], before[..., 3]), "alpha changed"
    assert np.array_equal(after[~union], before[~union]), "outside material masks changed"
    assert np.array_equal(after[protected], before[protected]), "protected pixels changed"
    report.update(alpha_bytes_identical=True, protected_RGBA_bytes_identical=True,
                  outside_mask_RGBA_bytes_identical=True, union_pixels=int(union.sum()),
                  limitations=["Conservative pose/material proxies, not semantic ground truth; ambiguous waist seams and boundaries preserve input colour.",
                               "ROI median agreement diagnoses palette only, not artistic acceptance."])
    return result, report


def audit():
    """Manual local audit artefact, not a test or a runtime-resource writer."""
    import runtime_frames
    manifest = runtime_frames.read_manifest()
    rows, thumbs = [], []
    for source, record in runtime_frames.phases(manifest):
        image, report = apply_colors(source, record)
        rows.append(report)
        bg = Image.new("RGBA", image.size, "#252525")
        bg.alpha_composite(image)
        thumb = bg.convert("RGB").resize((112,168))
        masks, _, _ = build_phase_masks(image, record)
        overlay = image.copy()
        for material, color in zip(MATERIALS, ("red", "lime", "dodgerblue")):
            layer = Image.new("RGBA", image.size, color)
            layer.putalpha(masks[material].point(lambda p: p//2))
            overlay.alpha_composite(layer)
        bg2 = Image.new("RGBA", image.size, "#252525")
        bg2.alpha_composite(overlay)
        pair = Image.new("RGB", (224,184), "#252525")
        pair.paste(thumb,(0,0));pair.paste(bg2.convert("RGB").resize((112,168)),(112,0))
        ImageDraw.Draw(pair).text((2,169), "%s %s %d" % (record["state"],record["direction"],record["phase"]), fill="white")
        thumbs.append(pair)
    sheet = Image.new("RGB", (896, (len(thumbs)+3)//4*184), "#252525")
    for i,thumb in enumerate(thumbs):
        sheet.paste(thumb, ((i%4)*224,(i//4)*184))
    sheet.save(HERE / "palette-cycle-audit-small.jpg",quality=90)
    (HERE / "palette-cycle-audit.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"frames":len(rows),"output":str(HERE / "palette-cycle-audit.json")},ensure_ascii=False))


if __name__ == "__main__":
    audit()
