"""Local, bounded trouser-palette adapter; no model, network, or production writes.

The masks are conservative numeric material/geometry proxies, not visually approved
semantic masks. All coordinates refer to the existing 512x768 review canvases.
"""
from pathlib import Path
import json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageCms, ImageDraw

HERE = Path(__file__).resolve().parent
SRGB = ImageCms.createProfile("sRGB")
LAB = ImageCms.createProfile("LAB")
TO_LAB = ImageCms.buildTransformFromOpenProfiles(SRGB, LAB, "RGB", "LAB")
TO_RGB = ImageCms.buildTransformFromOpenProfiles(LAB, SRGB, "LAB", "RGB")

# Envelopes deliberately stop at each bent boot. Colour rejection further protects
# warm leather, skin and coat hems; geometry protects neutral boot shadows.
ENVELOPES = {
    "front": [[(178, 400), (326, 400), (327, 470), (313, 510),
               (302, 565), (295, 620), (244, 620), (248, 543),
               (229, 543), (179, 540)]],
    "back": [[(187, 400), (326, 400), (326, 495), (319, 544),
              (308, 553), (270, 534), (260, 630), (201, 630),
              (198, 501), (186, 446)]],
    "right": [[(189, 408), (340, 398), (373, 447), (389, 498),
               (407, 608), (389, 619), (336, 619), (318, 514),
               (277, 462), (245, 516), (207, 540), (147, 553),
               (115, 542), (117, 513), (169, 481)]],
}
REFERENCE_ENVELOPES = {
    "front": [[(179, 407), (330, 407), (329, 627), (177, 627)]],
    "back": [[(178, 407), (331, 407), (330, 627), (177, 627)]],
    # The standing side-view hand overlaps the upper thigh at x246..276.
    # Measure below it rather than assuming that neutral pixels there are trousers.
    "right": [[(202, 439), (300, 439), (269, 553), (262, 627), (200, 627)]],
}


def lab8(image):
    """Pillow ICC Lab D50: L 0..255; NumPy a/b signed-byte decoding."""
    data = np.asarray(ImageCms.applyTransform(image.convert("RGB"), TO_LAB)).astype(np.float32)
    data[..., 1:] = np.where(data[..., 1:] >= 128, data[..., 1:] - 256, data[..., 1:])
    return data


def from_lab8(values):
    data = np.array(values, dtype=np.float32, copy=True)
    data[..., 0] = np.clip(np.rint(data[..., 0]), 0, 255)
    data[..., 1:] = np.mod(np.clip(np.rint(data[..., 1:]), -128, 127), 256)
    return ImageCms.applyTransform(Image.fromarray(data.astype(np.uint8), "LAB"), TO_RGB)


def _falloff(values, full, zero):
    return np.clip((zero - values) / (zero - full), 0, 1)


def build_pants_mask(image, direction, reference=False):
    """Return an inward-feathered L mask with zero coverage outside the envelope.

    Neutral fabric is accepted with a/b gates; no full-frame colour selection or
    mask blur outside the eligible pixels. The known gray canvas is also rejected.
    """
    if direction not in ENVELOPES:
        raise ValueError(f"Unsupported direction: {direction}")
    if image.size != (512, 768):
        raise ValueError("Trouser ROIs are defined only for 512x768 canvases")
    im = image.convert("RGB")
    pixels = np.asarray(im).astype(np.float32)
    values = lab8(im)
    shape = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(shape)
    for polygon in (REFERENCE_ENVELOPES if reference else ENVELOPES)[direction]:
        draw.polygon(polygon, fill=255)
    envelope = np.asarray(shape) > 0
    foreground = np.max(np.abs(pixels - 228), axis=2) > 22
    foreground &= (values[..., 0] > 16) & (values[..., 0] < 205)
    # A one-pixel guard avoids shifting gray/alpha silhouette mixtures.
    foreground = ndimage.binary_erosion(foreground, iterations=1)
    a, b = values[..., 1], values[..., 2]
    material = _falloff(a, 6, 9) * _falloff(b, 4, 6)
    material *= np.clip((a + 5) / 2, 0, 1) * np.clip((b + 6) / 2, 0, 1)
    eligible = envelope & foreground & (material > 0)
    components, count = ndimage.label(eligible)
    sizes = np.bincount(components.ravel())
    allowed = sizes >= 20
    allowed[0] = False
    eligible &= allowed[components]
    # Feather only inward, including material boundaries, never into boots/skin.
    inward = np.clip(ndimage.distance_transform_edt(eligible) / 1.5, 0, 1)
    return Image.fromarray(np.rint(255 * material * inward * eligible).astype(np.uint8))


def stats(image, mask):
    selected = np.asarray(mask) >= 220
    count = int(selected.sum())
    if count < 50:
        raise ValueError(f"Insufficient conservative trouser samples: {count}")
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)[selected]
    values = lab8(image)[selected]
    q = [5, 10, 25, 50, 75, 90, 95]
    result = {
        "interior_pixel_count": count,
        "mask_nonzero_pixel_count": int((np.asarray(mask) > 0).sum()),
        "quantile_percent": q,
        "RGB_quantiles": np.round(np.percentile(rgb, q, axis=0), 3).tolist(),
        "Lab8_signed_quantiles": np.round(np.percentile(values, q, axis=0), 3).tolist(),
        "Lstar_quantiles": np.round(np.percentile(values[:, 0], q) / 2.55, 3).tolist(),
    }
    return result


def match_pants(image, standing_reference, direction, *, mask_output=None):
    """Return (RGB image, JSON-ready report); only selected trousers are changed.

    Apply a bounded affine grade to low-frequency L, then restore the original
    high-frequency L residual. Fit on the fabric ROI only. Chroma gets a constant
    signed-Lab shift, retaining local cloth chroma variation. Deep black creases
    taper to zero correction below L8=16 to avoid lifting/flattening occlusion.
    """
    source = image.convert("RGB")
    reference = standing_reference.convert("RGB")
    mask = build_pants_mask(source, direction)
    ref_mask = build_pants_mask(reference, direction, reference=True)
    sample = np.asarray(mask) >= 220
    ref_sample = np.asarray(ref_mask) >= 220
    before, target = stats(source, mask), stats(reference, ref_mask)
    values, ref_values = lab8(source), lab8(reference)
    low = ndimage.gaussian_filter(values[..., 0], 1.2)
    ref_low = ndimage.gaussian_filter(ref_values[..., 0], 1.2)
    sq = np.percentile(low[sample], [25, 50, 75])
    rq = np.percentile(ref_low[ref_sample], [25, 50, 75])
    # Existing folds keep at least 80% of their broad contrast; no equalization.
    scale = float(np.clip((rq[2] - rq[0]) / max(sq[2] - sq[0], 1), .8, 1.1))
    offset = float(rq[1] - scale * sq[1])
    chroma_delta = np.median(ref_values[ref_sample, 1:], axis=0) - np.median(values[sample, 1:], axis=0)
    corrected = values.copy()
    ldelta = np.clip(scale * low + offset - low, -45, 35)
    black_guard = np.clip((values[..., 0] - 16) / 30, 0, 1)
    corrected[..., 0] += ldelta * black_guard
    corrected[..., 1:] += chroma_delta
    graded = from_lab8(corrected)
    result = Image.composite(graded, source, mask)
    result_array, source_array = np.asarray(result), np.asarray(source)
    exterior = np.asarray(mask) == 0
    if not np.array_equal(result_array[exterior], source_array[exterior]):
        raise AssertionError("Pixel changed outside trouser mask")
    if mask_output is not None:
        Path(mask_output).parent.mkdir(parents=True, exist_ok=True)
        mask.save(mask_output)
    report = {
        "direction": direction,
        "method": "trouser-ROI low-frequency bounded affine L + unchanged high-frequency L residual; constant signed a/b shift; inward material mask",
        "Lab_encoding": "Pillow ImageCms sRGB -> Lab D50; L 0..255; signed a/b bytes decoded to -128..127",
        "before": before, "standing_reference": target, "after": stats(result, mask),
        "luminance_lowpass_sigma": 1.2,
        "L_scale": scale, "L_offset": offset,
        "chroma_delta_ab": chroma_delta.tolist(),
        "outside_mask_pixels_identical": True,
        "mask_output": str(mask_output) if mask_output is not None else None,
        "limitations": [
            "Geometry/material proxy masks have not received visual approval. Narrow excluded seams/edges retain original pixels.",
            "Pose, perspective, bent-leg highlights and baked lighting differ; distribution matching does not recover intrinsic albedo.",
            "Standing right reference ROI starts below the overlaid hand; source and reference are unpaired fabric samples.",
            "High-frequency L is preserved before ICC quantization, mask blending and sRGB gamut clipping; exact RGB texture identity is not claimed.",
        ],
    }
    return result, report


def audit_main():
    root = HERE.parent.parent
    geometry = json.loads((root / "geometry-inputs/inputs.json").read_text(encoding="utf-8"))
    inputs = {Path(item["inputPath"]).stem: item for item in geometry["inputs"] if "inputPath" in item}
    records, corrections = [], []
    mapping = [("right", "clothing-side", "explore-run-right-p4"),
               ("front", "run-front", "explore-run-front-p0"),
               ("back", "run-back", "explore-run-back-p0")]
    for direction, case, original_name in mapping:
        ref_name = f"explore-idle-{direction}-p0"
        reference = Image.open(inputs[ref_name]["inputPath"]).convert("RGB")
        current_path = root / "results" / case / "constrained-candidate.png"
        current = Image.open(current_path).convert("RGB")
        ref_mask = build_pants_mask(reference, direction, reference=True)
        ref_mask.save(HERE / f"standing-{direction}-pants-mask.png")
        for name, path, image, mask in [
            (ref_name, Path(inputs[ref_name]["inputPath"]), reference, ref_mask),
            (case, current_path, current, build_pants_mask(current, direction))]:
            records.append({"name": name, "path": str(path), "stats": stats(image, mask)})
        result, report = match_pants(current, reference, direction, mask_output=HERE / f"{case}-pants-mask.png")
        result.save(HERE / f"{case}-pants-candidate.png")
        report["input_source_geometry"] = {
            key: inputs[original_name][key] for key in
            ["canvasSize", "canvasAnchorXY", "nativeToCanvasAffine", "inputSHA256"]
        }
        report["source_candidate_path"] = str(current_path)
        corrections.append(report)
    payload = {
        "status": "local numerical audit/prototype only; no visual acceptance or production edits",
        "reference": "Corresponding standing direction, not whole-character normalization",
        "envelopes_XY": {"candidate": ENVELOPES, "standing": REFERENCE_ENVELOPES},
        "gate": "a<=6 full to 9 zero; b<=4 full to 6 zero; a>-5,b>-6; L8 16..205; gray canvas rejection; inward feather",
        "measurements": records, "adaptation": corrections,
    }
    (HERE / "pants-audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (HERE / "palette-parameters.json").write_text(json.dumps({r["direction"]: {
        k: r[k] for k in ["L_scale", "L_offset", "chroma_delta_ab", "luminance_lowpass_sigma"]
    } for r in corrections}, indent=2), encoding="utf-8")
    for row in corrections:
        before, target, after = [row[k]["Lab8_signed_quantiles"][3] for k in ["before", "standing_reference", "after"]]
        print(row["direction"], "Lab8 medians before/reference/after", before, target, after,
              "samples", row["before"]["interior_pixel_count"])


if __name__ == "__main__":
    audit_main()
