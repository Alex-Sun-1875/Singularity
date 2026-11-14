"""Read current Cocos exploration phases at the established 400px/world scale.

No file writes, model calls or backup copies. Shared by bounded atlas adapters.
"""
from pathlib import Path
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
ACTOR = ROOT / "src/cocos/assets/resources/flat2d/characters/raphael"
MANIFEST = ACTOR / "manifest.json"
DIRECTIONS = ["down", "right", "up", "left"]
KEYS = {"idle": "explore_idle_W01", "walk": "explore_walk_W01", "run": "explore_run_W01"}


def read_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8-sig"))


def frame_record(manifest, state, direction, phase):
    action = manifest["actions"][KEYS[state]]
    di = DIRECTIONS.index(direction)
    image = action.get("frameImages", [action["image"]] * action["frames"])[phase]
    index = action.get("directionFrameIndices", [0, 1, 2, 3])[di] if state == "idle" else di * action["columns"] + action["frameIndices"][phase]
    rects = action.get("frameRectsByImage", {}).get(image.removesuffix(".png"), action["perFrameRects"])
    rect = rects[index]
    origins = action["perFrameOrigins"]
    origin = origins[direction][phase] if isinstance(origins, dict) else origins[index]
    scale = action["worldUnitsPerPixel"] * 400
    return {"state": state, "direction": direction, "phase": phase, "image": image,
            "index": index, "rect": rect, "origin": origin, "scale": scale,
            "absolute_anchor": [rect[0] + origin[0], rect[1] + origin[1]],
            "columns": action["columns"], "cell_size": [action["frameWidth"], action["frameHeight"]]}


def canvas(manifest, state, direction, phase, images=None):
    record = frame_record(manifest, state, direction, phase)
    path = ACTOR / record["image"]
    sheet = images[record["image"]] if images is not None else Image.open(path).convert("RGBA")
    x, y, w, h = record["rect"]
    crop = sheet.crop((x, y, x + w, y + h))
    scale = record["scale"]
    tx = 256 - record["origin"][0] * scale
    ty = 712 - record["origin"][1] * scale
    image = crop.transform((512, 768), Image.Transform.AFFINE,
        (1 / scale, 0, -tx / scale, 0, 1 / scale, -ty / scale), Image.Resampling.BICUBIC)
    record.update(canvas_translation=[tx, ty])
    return image, record


def phases(manifest=None):
    manifest = manifest or read_manifest()
    for state in ["idle", "walk", "run"]:
        for direction in DIRECTIONS:
            for phase in range(manifest["actions"][KEYS[state]]["frames"]):
                yield canvas(manifest, state, direction, phase)
