"""Local-only conservative cloth palette adapter for the 512x768 review canvases.

Reuses Pillow ImageCms signed-Lab and the bounded low-frequency luminance method
from local-klein-consistency-v1/revision-v2/pants-audit/pants_palette.py. Requires
only the already installed Pillow, NumPy and SciPy. Does not invoke any model,
network service or production-resource writer. Geometry/material masks are
conservative proxies; numerical agreement is not artistic acceptance.
"""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from PIL import Image, ImageCms, ImageDraw
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
SIZE = (512, 768)
MATERIALS = ("wine_vest", "charcoal_sleeves", "dark_gray_trousers")
SRGB, LAB = ImageCms.createProfile("sRGB"), ImageCms.createProfile("LAB")
TO_LAB = ImageCms.buildTransformFromOpenProfiles(SRGB, LAB, "RGB", "LAB")
TO_RGB = ImageCms.buildTransformFromOpenProfiles(LAB, SRGB, "LAB", "RGB")

# These are bounding envelopes, NOT a full semantic segmentation. Colour gates,
# original/guide agreement, protected equipment and an inward feather narrow them.
# Arm samples start below shoulder metal. Envelopes contain both the source and
# the modest body-guide waist changes; neutral torso belts are never sleeves.
RUN_SLEEVES = {
    "front": [[(139, 264), (211, 264), (213, 342), (137, 342)],
              [(320, 264), (374, 264), (378, 360), (321, 360)]],
    "back": [[(130, 264), (188, 264), (185, 354), (128, 354)],
             [(299, 264), (365, 264), (365, 328), (299, 328)]],
    "right": [[(162, 257), (215, 257), (216, 326), (166, 326)],
              [(288, 277), (355, 277), (359, 320), (291, 327)]],
}
REF_SLEEVES = {
    "front": [[(153, 263), (208, 263), (198, 365), (153, 365)],
              [(308, 263), (358, 263), (358, 365), (315, 365)]],
    "back": [[(151, 263), (208, 263), (195, 363), (151, 363)],
             [(306, 263), (357, 263), (360, 365), (316, 365)]],
    "right": [[(216, 264), (267, 264), (268, 365), (219, 365)]],
}
RUN_PANTS = {
    "front": [[(178, 386), (326, 386), (327, 470), (313, 510),
               (302, 565), (295, 620), (244, 620), (248, 543),
               (229, 543), (179, 540)]],
    "back": [[(187, 386), (326, 386), (326, 495), (319, 537),
              (270, 534), (260, 630), (201, 630), (198, 501), (186, 446)]],
    "right": [[(189, 401), (340, 398), (373, 447), (389, 498),
               (407, 608), (389, 619), (336, 619), (318, 514),
               (277, 462), (245, 516), (207, 540), (147, 553),
               (115, 542), (117, 513), (169, 481)]],
}
REF_PANTS = {
    "front": [[(179, 407), (330, 407), (329, 627), (177, 627)]],
    "back": [[(178, 407), (331, 407), (330, 627), (177, 627)]],
    "right": [[(202, 439), (300, 439), (269, 553), (262, 627), (200, 627)]],
}
RUN_HAND_BOXES = {
    "front": [(190, 264, 277, 352), (330, 330, 389, 433)],
    # The central back patch is vest/scabbard, not an extra hand. Only the
    # genuine screen-left hand is protected by a rectangle here.
    "back": [(128, 322, 189, 416)],
    "right": [(180, 303, 257, 403), (348, 238, 416, 321)],
}
REF_HAND_BOXES = {
    "front": [(146, 369, 198, 439), (320, 369, 373, 439)],
    "back": [(141, 363, 205, 449), (316, 362, 372, 444)],
    "right": [(237, 367, 290, 441)],
}


def _image(value, mode="RGBA"):
    im = value.copy() if isinstance(value, Image.Image) else Image.open(value).copy()
    if im.size != SIZE:
        raise ValueError(f"Only the existing {SIZE} review canvas is supported, got {im.size}")
    return im.convert(mode)


def lab8(image):
    """ICC Lab D50, L 0..255; signed a/b decoded from NumPy byte storage."""
    a = np.asarray(ImageCms.applyTransform(image.convert("RGB"), TO_LAB)).astype(np.float32)
    a[..., 1:] = np.where(a[..., 1:] >= 128, a[..., 1:] - 256, a[..., 1:])
    return a


def from_lab8(values):
    a = np.array(values, np.float32, copy=True)
    a[..., 0] = np.clip(np.rint(a[..., 0]), 0, 255)
    a[..., 1:] = np.mod(np.clip(np.rint(a[..., 1:]), -128, 127), 256)
    return ImageCms.applyTransform(Image.fromarray(a.astype(np.uint8), "LAB"), TO_RGB)


def _polygons(polygons):
    mask = Image.new("L", SIZE, 0)
    draw = ImageDraw.Draw(mask)
    for p in polygons:
        draw.polygon(p, fill=255)
    return np.asarray(mask) != 0


def _external_protect(value):
    if value is None:
        return np.zeros((SIZE[1], SIZE[0]), bool)
    return np.asarray(_image(value, "L")) > 0


def protection_mask(image, direction, *, reference=False, protect_mask=None):
    """White means preserve. Includes all alpha edges and gold/warm details.

    Use the body guide as image after a geometry change. Explicit caller masks
    should cover exact weapon/equipment contours; built-in sword corridors are a
    conservative fallback only. Gold protection is expanded inward into cloth,
    never feathered into the protected pixels.
    """
    im = _image(image)
    rgb = np.asarray(im.convert("RGB"), np.float32)
    values = lab8(im)
    r, g, b = np.moveaxis(rgb, -1, 0)
    draw_mask = Image.new("L", SIZE, 0)
    draw = ImageDraw.Draw(draw_mask)
    draw.rectangle((0, 0, 511, 204), fill=255)
    for box in (REF_HAND_BOXES if reference else RUN_HAND_BOXES)[direction]:
        draw.rectangle(box, fill=255)
    # Sword fallback. Exact caller masks can add full outline/tip coverage.
    if direction == "back":
        draw.line([(284, 189), (194, 390)], fill=255, width=25)
    elif direction == "front":
        # Main diagonal chest strap is warm; exact neutral hardware is kept too.
        draw.line([(222, 209), (294, 329)], fill=255, width=12)
    else:
        draw.line([(209, 200), (173, 382)], fill=255, width=19)
    hard = np.asarray(draw_mask) > 0
    alpha = np.asarray(im.getchannel("A"))
    # Existing sprites encode most opaque cloth at A=250..253 (not 255).
    # Requiring 254 would incorrectly discard the actual garment interiors.
    opaque = ndi.binary_erosion(alpha >= 250, iterations=2)
    # In these sprites the matte is 228. RGBA edge rejection above also handles
    # zero-alpha RGB without changing those otherwise invisible pixel bytes.
    foreground = np.max(np.abs(rgb - 228), axis=2) > 22
    gold_warm_detail = ((values[..., 2] > 10) & (g - b > 5) & (r - g > 3))
    gold_warm_detail |= ((g - b > 9) & (r > b + 12))
    gold_warm_detail = ndi.binary_dilation(gold_warm_detail, iterations=2)
    hard |= ~opaque | ~foreground | gold_warm_detail
    hard |= _external_protect(protect_mask)
    return Image.fromarray((hard * 255).astype(np.uint8))


def _material_gates(image):
    im = image.convert("RGB")
    rgb = np.asarray(im, np.float32)
    hsv = np.asarray(im.convert("HSV"), np.float32)
    l, a, b = np.moveaxis(lab8(im), -1, 0)
    r, g, blue = np.moveaxis(rgb, -1, 0)
    h, s, v = np.moveaxis(hsv, -1, 0)
    wine = (((h <= 11) | (h >= 239)) & (s >= 42) & (s <= 210)
            & (r > blue + 7) & (r > g + 8) & (g - blue < 9)
            & (a >= 7) & (a <= 32) & (b >= -3) & (b <= 11)
            & (l > 19) & (l < 185))
    sleeve = ((a >= -3) & (a <= 6) & (b >= -10) & (b <= 3)
              & (s <= 60) & (l > 19) & (l < 168))
    pants = ((a >= -3) & (a <= 7) & (b >= -5) & (b <= 5)
             & (s <= 65) & (l > 19) & (l < 192))
    return dict(zip(MATERIALS, (wine, sleeve, pants)))


def build_masks(image, direction, *, reference=False, geometry_image=None,
                protect_mask=None):
    """Return three inward-feathered L masks; no eligible edge spill.

    geometry_image is the untouched original for unchanged pose, or the exact
    body guide for a warped pose. Gate agreement prevents generated equipment
    and hand colours being accepted as cloth merely because their hue changed.
    """
    direction = "right" if direction == "side" else direction
    if direction not in RUN_PANTS:
        raise ValueError(f"Unsupported direction {direction!r}")
    im = _image(image)
    geometry = _image(geometry_image) if geometry_image is not None else im
    protected = np.asarray(protection_mask(geometry, direction, reference=reference,
                                          protect_mask=protect_mask)) > 0
    # Protect newly introduced warm/gold details as well as original details.
    protected |= np.asarray(protection_mask(im, direction, reference=reference)) > 0
    gates, anchors = _material_gates(im), _material_gates(geometry)
    envelopes = {
        "wine_vest": _polygons([[(134, 205), (371, 205), (374, 435), (131, 435)]]),
        "charcoal_sleeves": _polygons((REF_SLEEVES if reference else RUN_SLEEVES)[direction]),
        "dark_gray_trousers": _polygons((REF_PANTS if reference else RUN_PANTS)[direction]),
    }
    result = {}
    for material in MATERIALS:
        eligible = gates[material] & anchors[material] & envelopes[material] & ~protected
        labels, _ = ndi.label(eligible)
        sizes = np.bincount(labels.ravel())
        allowed = sizes >= 18
        allowed[0] = False
        eligible &= allowed[labels]
        inward = np.clip(ndi.distance_transform_edt(eligible) / 1.5, 0, 1)
        result[material] = Image.fromarray(np.rint(eligible * inward * 255).astype(np.uint8))
    return result


def _samples(mask):
    return np.asarray(mask) >= 220


def material_stats(image, mask):
    sample = _samples(mask)
    n = int(sample.sum())
    if n == 0:
        return {"interior_pixel_count": 0, "mask_nonzero_pixel_count": 0}
    values = lab8(image)[sample]
    rgb = np.asarray(image.convert("RGB"), np.float32)[sample]
    q = [10, 25, 50, 75, 90]
    return {
        "interior_pixel_count": n,
        "mask_nonzero_pixel_count": int((np.asarray(mask) > 0).sum()),
        "quantile_percent": q,
        "RGB_quantiles": np.round(np.percentile(rgb, q, axis=0), 3).tolist(),
        "Lab8_signed_quantiles": np.round(np.percentile(values, q, axis=0), 3).tolist(),
        "Lstar_quantiles": np.round(np.percentile(values[:, 0], q) / 2.55, 3).tolist(),
        "Lab_D50_median": np.round(np.median(values, axis=0) / [2.55, 1, 1], 3).tolist(),
        "Lstar_IQR": round(float(np.subtract(*np.percentile(values[:, 0], [75, 25]))) / 2.55, 3),
    }


def _median_error(source, reference):
    if not source.get("interior_pixel_count") or not reference.get("interior_pixel_count"):
        return None
    delta = np.array(source["Lab_D50_median"]) - reference["Lab_D50_median"]
    return {"signed_delta_Lstar_astar_bstar": np.round(delta, 3).tolist(),
            "deltaE76_between_ROI_medians": round(float(np.linalg.norm(delta)), 3)}


def apply_palette(candidate, standing_reference, direction, *, geometry_image=None,
                  protect_mask=None, mask_output_dir=None, strength=1.0):
    """Return (RGBA image, report), calibrated separately for the three cloths.

    Candidate alpha and every RGBA byte outside the union of the cloth masks
    remain unchanged. Does not restore geometry/identity: caller must first
    constrain the generated result against its body guide and protection masks.
    Correction targets standing cloth medians, not a model-proposed dark colour.
    It can therefore brighten an over-dark raw Qwen vest as well as darken a
    pale runner. Low-frequency L contrast stays in [0.90,1.08], fine folds keep
    their original L residual before ICC quantization and gamut clipping.
    """
    direction = "right" if direction == "side" else direction
    if not 0 <= strength <= 1:
        raise ValueError("strength must be in [0,1]")
    source = _image(candidate)
    reference = _image(standing_reference)
    geometry = _image(geometry_image) if geometry_image is not None else source
    masks = build_masks(source, direction, geometry_image=geometry, protect_mask=protect_mask)
    original_masks = build_masks(geometry, direction, protect_mask=protect_mask)
    ref_masks = build_masks(reference, direction, reference=True)
    values, ref_values = lab8(source), lab8(reference)
    # No high-frequency component is replaced; the L correction field varies
    # only with the low-pass L and black-crease guard.
    low = ndi.gaussian_filter(values[..., 0], 1.2)
    ref_low = ndi.gaussian_filter(ref_values[..., 0], 1.2)
    source_bytes = np.asarray(source).copy()
    result = source.copy()
    union = np.zeros((768, 512), bool)
    report = {
        "direction": direction,
        "method": "separate conservative wine/sleeve/trouser ROIs; bounded low-frequency ICC Lab L affine plus signed a/b offset; original fine-L residual",
        "Lab_encoding": "Pillow ImageCms sRGB to ICC Lab D50; L8/2.55=Lstar, signed a/b decoded from NumPy bytes",
        "materials": {}, "strength": strength,
        "status": "numerical palette candidate; not artistic acceptance; no production writes",
    }
    out_dir = Path(mask_output_dir) if mask_output_dir is not None else None
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
    for material in MATERIALS:
        mask, ref_mask = masks[material], ref_masks[material]
        sample, ref_sample = _samples(mask), _samples(ref_mask)
        row = {
            "guide_or_original": material_stats(geometry, original_masks[material]),
            "candidate_before": material_stats(source, mask),
            "standing_reference": material_stats(reference, ref_mask),
        }
        if min(int(sample.sum()), int(ref_sample.sum())) < 60:
            row["status"] = "skipped: fewer than 60 conservative interior pixels"
            row["candidate_after"] = row["candidate_before"]
            report["materials"][material] = row
            continue
        sq = np.percentile(low[sample], [25, 50, 75])
        rq = np.percentile(ref_low[ref_sample], [25, 50, 75])
        scale = float(np.clip((rq[2] - rq[0]) / max(sq[2] - sq[0], 1), 0.90, 1.08))
        offset = float(rq[1] - scale * sq[1])
        chroma_delta = np.median(ref_values[ref_sample, 1:], axis=0) - np.median(values[sample, 1:], axis=0)
        chroma_delta = np.clip(chroma_delta, -7, 7)
        corrected = values.copy()
        # A fixed cap prevents a bad distribution fit from crushing the cloth.
        # The positive range also repairs the previous over-dark Qwen wine vest.
        l_delta = np.clip(scale * low + offset - low, -36, 36)
        black_guard = np.clip((values[..., 0] - 15) / 22, 0, 1)
        corrected[..., 0] += l_delta * black_guard * strength
        corrected[..., 1:] += chroma_delta * strength
        grade = from_lab8(corrected).convert("RGBA")
        grade.putalpha(source.getchannel("A"))
        result = Image.composite(grade, result, mask)
        union |= np.asarray(mask) > 0
        row.update({"status": "calibrated", "L_lowpass_sigma": 1.2,
                    "L_scale": scale, "L_offset": offset,
                    "L_delta_cap": [-36, 36], "chroma_delta_ab": chroma_delta.tolist(),
                    "candidate_after": material_stats(result, mask)})
        row["before_error_vs_standing"] = _median_error(row["candidate_before"], row["standing_reference"])
        row["after_error_vs_standing"] = _median_error(row["candidate_after"], row["standing_reference"])
        if out_dir is not None:
            mask.save(out_dir / f"{material}-edit-mask.png")
            ref_mask.save(out_dir / f"{material}-standing-sample-mask.png")
        report["materials"][material] = row
    result.putalpha(source.getchannel("A"))
    after_bytes = np.asarray(result)
    assert np.array_equal(after_bytes[..., 3], source_bytes[..., 3]), "alpha changed"
    assert np.array_equal(after_bytes[~union], source_bytes[~union]), "outside-mask pixel changed"
    protected = np.asarray(protection_mask(geometry, direction, protect_mask=protect_mask)) > 0
    assert np.array_equal(after_bytes[protected], source_bytes[protected]), "protected pixel changed"
    report.update({"alpha_bytes_identical": True, "outside_mask_RGBA_bytes_identical": True,
                   "protected_RGBA_bytes_identical": True,
                   "union_nonzero_pixel_count": int(union.sum()),
                   "limitations": [
                       "Material/geometry proxy masks are conservative, not manually traced semantic masks. Excluded seams and boundaries retain the input colour.",
                       "Exact weapon and ambiguous hand/pouch boundaries require caller-provided protect_mask on the final guide geometry.",
                       "Distribution differences include pose, baked shading and view. DeltaE76 between unpaired ROI medians is a diagnostic, not perceptual/artistic acceptance.",
                       "Preserving fine-L residual is before ICC quantization, mask blending and sRGB gamut clipping; exact RGB fold identity is not claimed.",
                   ]})
    if out_dir is not None:
        Image.fromarray((union * 255).astype(np.uint8)).save(out_dir / "cloth-union-mask.png")
        protection_mask(geometry, direction, protect_mask=protect_mask).save(out_dir / "hard-protect-mask.png")
    return result, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate", required=True)
    p.add_argument("--reference", required=True)
    p.add_argument("--direction", choices=["front", "back", "right", "side"], required=True)
    p.add_argument("--geometry")
    p.add_argument("--protect-mask")
    p.add_argument("--out", required=True)
    p.add_argument("--strength", type=float, default=1)
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    image, report = apply_palette(args.candidate, args.reference, args.direction,
                                  geometry_image=args.geometry, protect_mask=args.protect_mask,
                                  strength=args.strength, mask_output_dir=out)
    image.save(out / "palette-candidate.png")
    for key in ["candidate", "reference", "geometry", "protect_mask"]:
        path = getattr(args, key)
        if path:
            report[key + "_path"] = str(Path(path).resolve())
            report[key + "_sha256"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    (out / "palette-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for material, row in report["materials"].items():
        print(material, row["status"], row.get("before_error_vs_standing"), row.get("after_error_vs_standing"))


if __name__ == "__main__":
    main()
