"""Compare available raw Qwen outputs locally, without retouching or model calls.

Run after inference. Only writes comparison-raw.jpg and metrics.json beside this
script. Every image shares one display scale and its native top-left origin;
larger-than-expected raw canvases remain fully visible rather than being cropped
or individually fitted. Numerical geometry is not an artistic acceptance test.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PANEL_SIZE = (512, 768)
THUMB_SIZE = (256, 384)
NAMES = ("front-run", "back-sword")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_image(path):
    with Image.open(path) as source:
        source.load()
        image = source.copy()
        has_alpha = "A" in source.getbands() or "transparency" in source.info
        alpha = source.convert("RGBA").getchannel("A") if has_alpha else None
        record = {
            "path": str(path), "sha256": sha(path),
            "size": list(source.size), "mode": source.mode,
            "has_alpha": has_alpha,
            "alpha_extrema": list(alpha.getextrema()) if alpha else None,
            "alpha_bbox_any_xyxy": list(alpha.getbbox()) if alpha and alpha.getbbox() else None,
            "alpha_bbox_ge16_xyxy": None,
        }
        if alpha is not None:
            bounds = alpha.point(lambda value: 255 if value >= 16 else 0).getbbox()
            record["alpha_bbox_ge16_xyxy"] = list(bounds) if bounds else None
        return image.convert("RGBA"), record


def checkerboard():
    image = Image.new("RGBA", PANEL_SIZE, (232, 232, 232, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, PANEL_SIZE[1], 24):
        for x in range(0, PANEL_SIZE[0], 24):
            if (x // 24 + y // 24) % 2:
                draw.rectangle((x, y, x + 23, y + 23), fill=(214, 214, 214, 255))
    return image


def main():
    manifest = json.loads((HERE / "input-manifest.json").read_text(encoding="utf-8"))
    groups = {group["name"]: group for group in manifest["groups"]}
    rows, missing, snapshots = [], [], {}
    for name in NAMES:
        raw_path = HERE / "results" / name / "raw-model.png"
        if not raw_path.is_file():
            missing.append(str(raw_path))
            continue
        bindings = groups[name]["images"]
        target_path = Path(bindings[0]["preserved_rgba"]["path"])
        target, target_record = read_image(target_path)
        raw, raw_record = read_image(raw_path)
        reference = reference_record = None
        if len(bindings) > 1:
            reference_path = Path(bindings[1]["preserved_rgba"]["path"])
            reference, reference_record = read_image(reference_path)
        for record in (target_record, reference_record, raw_record):
            if record:
                snapshots[record["path"]] = record["sha256"]
        delta = {"canvas_size_raw_minus_target_wh": [raw.width - target.width, raw.height - target.height]}
        for key in ("alpha_bbox_any_xyxy", "alpha_bbox_ge16_xyxy"):
            a, b = raw_record[key], target_record[key]
            delta[key + "_raw_minus_target"] = [x - y for x, y in zip(a, b)] if a and b else None
        rows.append({"name": name, "images": (target, reference, raw),
                     "records": (target_record, reference_record, raw_record), "delta": delta})
    if not rows:
        raise SystemExit("No raw-model.png outputs found; no files written. Run again after inference.")

    # A single shared display transform also handles anomalous raw dimensions.
    # No per-image bbox fit, translation, pose alignment, cropping or stretching.
    images = [image for row in rows for image in row["images"] if image is not None]
    extent = (max(512, *(im.width for im in images)), max(768, *(im.height for im in images)))
    fit = min(512 / extent[0], 768 / extent[1])
    margin, gap, label_height = 12, 12, 40
    row_height = THUMB_SIZE[1] + label_height
    size = (margin * 2 + THUMB_SIZE[0] * 3 + gap * 2,
            margin * 2 + row_height * len(rows) + gap * (len(rows) - 1))
    comparison = Image.new("RGB", size, (244, 244, 244))
    draw = ImageDraw.Draw(comparison)
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    font = ImageFont.truetype(str(font_path), 13) if font_path.is_file() else ImageFont.load_default()
    small = ImageFont.truetype(str(font_path), 11) if font_path.is_file() else font
    for row_index, row in enumerate(rows):
        y = margin + row_index * (row_height + gap)
        for column, (title, image, record) in enumerate(zip(("Original", "Reference", "Qwen raw"), row["images"], row["records"])):
            x = margin + column * (THUMB_SIZE[0] + gap)
            draw.text((x, y), f"{row['name']} / {title}", font=font, fill=(25, 25, 25))
            caption = f"native {record['size'][0]}x{record['size'][1]}  {record['mode']}" if record else "No separate reference supplied"
            draw.text((x, y + 18), caption, font=small, fill=(70, 70, 70))
            panel = checkerboard()
            if image is not None:
                display_size = (max(1, round(image.width * fit)), max(1, round(image.height * fit)))
                display = image if display_size == image.size else image.resize(display_size, Image.Resampling.LANCZOS)
                panel.alpha_composite(display, (0, 0))
            if extent != PANEL_SIZE:
                # Show the original nominal 512x768 canvas in the common extent.
                ImageDraw.Draw(panel).rectangle((0, 0, max(0, round(512 * fit) - 1), max(0, round(768 * fit) - 1)),
                                               outline=(173, 88, 71, 255), width=2)
            thumbnail = panel.convert("RGB").resize(THUMB_SIZE, Image.Resampling.LANCZOS)
            comparison.paste(thumbnail, (x, y + label_height))
    assert comparison.width <= 1000 and comparison.height <= 1000
    output = HERE / "comparison-raw.jpg"
    comparison.save(output, quality=88, optimize=True)
    metrics = {
        "status": "raw-output diagnostic only; no artistic acceptance implied",
        "alpha_bbox_coordinates": "native image pixel XYXY; right and bottom exclusive; null means absent alpha or empty alpha",
        "warning": "Size/alpha bounds are geometry proxies, not anatomical landmarks or an artistic quality decision.",
        "cases": [{"case": row["name"], "target_original": row["records"][0],
                   "reference": row["records"][1], "raw_model": row["records"][2],
                   "raw_vs_target": row["delta"]} for row in rows],
        "missing_raw_outputs": missing,
        "preview": {"path": str(output), "size": list(comparison.size),
                    "panel_native_size": list(PANEL_SIZE), "panel_preview_size": list(THUMB_SIZE),
                    "shared_native_extent_wh": list(extent), "shared_display_scale": fit * 0.5,
                    "origin_policy": "native top-left for all; no per-image alignment or bbox fit",
                    "anomalous_canvas_policy": "extend the same observation range for all panels, then uniformly downsample the whole preview; no image crop or stretch",
                    "background": "light-grey checkerboard; opaque raw backgrounds remain visible"},
        "inputs_unchanged": all(sha(Path(path)) == digest for path, digest in snapshots.items()),
    }
    assert metrics["inputs_unchanged"]
    (HERE / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"comparison": str(output), "size": list(comparison.size),
                      "metrics": str(HERE / "metrics.json"), "cases": [row["name"] for row in rows]}, indent=2))


if __name__ == "__main__":
    main()
