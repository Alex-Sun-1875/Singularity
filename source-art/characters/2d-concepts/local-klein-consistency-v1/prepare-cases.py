"""Prepare bounded local-model trials; never write runtime assets."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
INPUTS = ROOT / "geometry-inputs"
GUIDES = ROOT / "guides"
GUIDES.mkdir(exist_ok=True)


def source(name):
    return Image.open(INPUTS / (name + ".png")).convert("RGB")


def alpha(name):
    return Image.open(INPUTS / (name + "-alpha.png")).convert("L")


def polygon(points, blur=2):
    mask = Image.new("L", (512, 768), 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(blur))


def save_case(name, original, guide, mask, reference, prompt, notes, single=False):
    folder = GUIDES / name
    folder.mkdir(exist_ok=True)
    guide.save(folder / "guide.png")
    mask.save(folder / "composite-mask.png")
    mask.filter(ImageFilter.MaxFilter(33)).save(folder / "noise-mask.png")
    original.save(folder / "before.png")
    if reference is not None:
        reference.save(folder / "reference.png")
    (folder / "prompt.txt").write_text(prompt, encoding="utf-8")
    return {"name": name, "directory": str(folder), "single_reference": single, "skip_steps": 0,
            "seed": 1707, "notes": notes, "status": "experimental, not installed"}


cases = []
original = source("explore-idle-back-p0")
start = np.array([283.0, 192.0])
tip = np.array([200.0, 373.0])
unit = (tip - start) / np.linalg.norm(tip - start)
factor = 1.4
matrix = np.eye(2) + (factor - 1) * np.outer(unit, unit)
inverse = np.linalg.inv(matrix)
offset = start - inverse @ start
coefficients = (*inverse[0], offset[0], *inverse[1], offset[1])
weapon_mask = Image.new("L", original.size, 0)
ImageDraw.Draw(weapon_mask).line([tuple(start), tuple(tip)], fill=255, width=17)
warped_mask = weapon_mask.transform(original.size, Image.Transform.AFFINE, coefficients, Image.Resampling.BICUBIC)
warped = original.transform(original.size, Image.Transform.AFFINE, coefficients, Image.Resampling.BICUBIC, fillcolor=(228, 228, 228))
guide = Image.composite(warped, original, warped_mask)
new_tip = start + factor * (tip - start)
mask = Image.new("L", original.size, 0)
ImageDraw.Draw(mask).line([tuple(start), tuple(new_tip)], fill=255, width=25)
mask = mask.filter(ImageFilter.GaussianBlur(2))
cases.append(save_case("sword-back", original, guide, mask, None,
    "Refine this rear-view character image while preserving its exact geometry. The sheathed longsword is mounted diagonally across his back. Its original gold pommel, dark grip, crossguard and upper shoulder attachment stay exactly where they are. The brown leather scabbard follows the existing diagonal toward the lower left and now reaches the upper thigh, about thirty percent longer overall. Keep that longer length from image 1. Repair only the scabbard texture, stitching, metal tip and its small attachment seams. Preserve the same head, silver curls, burgundy coat, embroidery, arms, trousers, legs, boots and neutral light gray background. One single rear-view standing man.",
    {"weapon_start_xy": start.tolist(), "old_tip_xy": tip.tolist(), "guide_tip_xy": new_tip.tolist(), "scabbard_axial_factor": factor, "intent": "approximately 30 percent longer complete sword; same grip position and width"}, single=True))

original = source("explore-run-right-p4")
guide = original.copy()
mask = polygon([(232,193),(293,187),(330,223),(337,273),(315,325),(324,406),(220,418),(198,369),(174,329),(176,275),(200,226)])
pixels = np.array(mask)
foreground = np.asarray(alpha("explore-run-right-p4")) > 16
pixels[~foreground] = 0
mask = Image.fromarray(pixels)
draw = ImageDraw.Draw(mask)
draw.line([(264,174),(217,396)], fill=0, width=21)
draw.ellipse((170,302,215,351), fill=0)
draw.ellipse((320,226,376,273), fill=0)
mask = mask.filter(ImageFilter.GaussianBlur(1))
cases.append(save_case("clothing-side", original, guide, mask, source("explore-idle-right-p0"),
    "Edit the running character in image 1. Image 2 is the approved costume color reference. Keep exactly the running pose, body size, limb positions, head, face, silver hair, sword and every clothing seam from image 1. Match only the garment colors to image 2: the fitted vest is the same deep muted wine burgundy, with unchanged fine gold embroidery. The sleeves are the same dark charcoal fabric with a restrained blue-purple cast, not bright blue and not pale gray. Preserve the original folds, stitching, collar, belt, pouch, cuffs and lighting detail. Do not redesign the clothes, increase saturation, add armor, or move any equipment. Return one right-facing runner on the same light gray background.",
    {"target": "standing costume palette; preserve garment shape and equipment", "reference": "explore-idle-right-p0"}))


def long_leg_guide(image):
    result = image.copy()
    result.paste(image.crop((0, 210, 512, 420)).resize((512,178), Image.Resampling.LANCZOS), (0,210))
    result.paste(image.crop((0, 420, 512, 712)).resize((512,324), Image.Resampling.LANCZOS), (0,388))
    return result


for direction in ("front", "back"):
    name = "explore-run-" + direction + "-p0"
    original = source(name)
    guide = long_leg_guide(original)
    guided_alpha = long_leg_guide(alpha(name).convert("RGB")).getchannel("R")
    union = Image.fromarray(np.maximum(np.asarray(guided_alpha), np.asarray(alpha(name))))
    mask = union.filter(ImageFilter.MaxFilter(33))
    mask_array = np.array(mask)
    mask_array[:210] = 0
    mask_array[723:] = 0
    mask = Image.fromarray(mask_array).filter(ImageFilter.GaussianBlur(2))
    # Faces/hair and their precise locations are frozen above the edit band.
    orientation = "directly toward the camera" if direction == "front" else "directly away from the camera, with his back visible"
    cases.append(save_case("run-" + direction, original, guide, mask, source("explore-idle-"+direction+"-p0"),
        "Refine the runner in image 1, preserving the tall slim proportions already laid out there. He runs "+orientation+". Image 2 supplies the approved identity, adult body proportions and costume palette, not a standing pose. Keep image 1's running phase, forward torso energy, alternating arms and bent trailing leg. Preserve the exact head size, head position, silver hairstyle and foot placement from image 1. The waist is high and the thighs and shins are long and slender; he must not look squat or short-legged. Smooth the small waist and knee transitions without shortening the legs or widening the torso. Match image 2's deep muted wine-burgundy coat, fine gold embroidery and dark charcoal sleeves. Preserve the sword attachment, pouch, belt, cuffs and brown boots. One full-body runner, same light gray background, no extra person or standing pose.",
        {"geometry_guide": "head and feet fixed; waist raised 32px; torso210px->178px; lower body292px->324px", "input": name, "reference": "explore-idle-"+direction+"-p0", "model_role": "masked local retouch of waist, clothes and leg transitions"}))

(ROOT / "cases.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
print(json.dumps([{ "name": case["name"], "notes": case["notes"] } for case in cases], indent=2))
