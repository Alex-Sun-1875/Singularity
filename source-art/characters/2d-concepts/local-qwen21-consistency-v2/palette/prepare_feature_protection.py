"""Replace whole-arm colour locks with independent feature locks, locally.

Reads current body/sword guides and masks; writes only beneath this palette/.
Does not invoke a model, server, network, vision tool or upload.
"""
from pathlib import Path
import hashlib
import json
import sys
sys.dont_write_bytecode = True

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from apply_palette import apply_palette, build_masks, protection_mask, RUN_HAND_BOXES

HERE = Path(__file__).resolve().parent
TRIAL = HERE.parent
OUT = HERE / "final-feature-protection"
CORE_BOXES = {
    "front": [(202, 290, 263, 339), (343, 368, 375, 420)],
    "back": [(141, 358, 176, 403)],
}


def mask(path):
    return np.asarray(Image.open(path).convert("L")) > 0


def save_mask(array, path):
    Image.fromarray((array * 255).astype(np.uint8)).save(path)


def boxes_mask(boxes):
    im = Image.new("L", (512, 768), 0)
    draw = ImageDraw.Draw(im)
    for box in boxes:
        draw.rectangle(box, fill=255)
    return np.asarray(im) > 0


def skin_gate(image, *, bright=False):
    rgb = np.asarray(image.convert("RGB"), np.float32)
    hsv = np.asarray(image.convert("HSV"), np.float32)
    r, g, b = np.moveaxis(rgb, -1, 0)
    h, s, v = np.moveaxis(hsv, -1, 0)
    gate = ((r > g + 7) & (g > b + 3) & (r - g < 70)
            & (g - b < (r - g) * 1.2) & (h < 25)
            & (s > 25) & (s < 175) & (v > 65))
    if bright:
        gate &= (r > 145) & (g > 95) & (b > 80) & (g - b < (r - g) * .8)
    return gate


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = {}
    for direction in ("front", "back"):
        body = TRIAL / "body" / direction
        guide_path = (body / "guide-rgba.png" if direction == "front"
                      else TRIAL / "sword/back-run/merged-guide-rgba.png")
        guide = Image.open(guide_path).convert("RGBA")
        original = Image.open(body / "original-rgba.png").convert("RGBA")
        all_old = mask(body / "all-protection-mask.png")
        arms = mask(body / "arms-hands-protection-mask.png")
        head = mask(body / "head-protection-mask.png")
        boots = mask(body / "boots-protection-mask.png")
        weapon = mask(body / "weapon-protection-mask.png")
        # Subtracting the arm owner alone is not sufficient at intersecting
        # features; head/boots/weapon are explicitly reinstated afterward.
        fixed_without_whole_arms = (all_old & ~arms) | head | boots | weapon
        if direction == "back":
            sword = TRIAL / "sword/back-run"
            old_new_sword = (mask(sword / "source-sword-mask.png")
                             | mask(sword / "middle-mask.png")
                             | mask(sword / "translated-cap-mask.png"))
            weapon |= ndi.binary_dilation(old_new_sword, iterations=2)
            # Read the aggregate sword mask as a cross-check; preserve any
            # newly protected non-arm/non-body feature it contains too.
            sword_palette_mask = mask(sword / "palette-protection-mask.png")
            weapon |= sword_palette_mask & ~all_old
            fixed_without_whole_arms |= weapon
        else:
            old_new_sword = weapon.copy()
        hands = boxes_mask(RUN_HAND_BOXES[direction])
        # Warm candidates inside the exact unchanged arm layer protect any
        # additional skin, wrist leather or gold cuff beyond the fixed boxes.
        warm_in_arms = arms & (skin_gate(guide) | skin_gate(original))
        warm_in_arms = ndi.binary_dilation(warm_in_arms, iterations=2) & arms
        hands |= warm_in_arms
        intrinsic = np.asarray(protection_mask(guide, direction)) > 0
        final = fixed_without_whole_arms | hands | intrinsic
        output = OUT / f"{direction}-feature-protect-mask.png"
        save_mask(final, output)
        save_mask(hands, OUT / f"{direction}-hands-wrists-mask.png")
        save_mask(warm_in_arms, OUT / f"{direction}-warm-skin-in-arms-mask.png")
        save_mask(weapon, OUT / f"{direction}-old-new-weapon-mask.png")
        save_mask(boots, OUT / f"{direction}-boots-mask.png")

        edit_masks = build_masks(guide, direction, geometry_image=guide, protect_mask=output)
        edit = np.logical_or.reduce([np.asarray(m) > 0 for m in edit_masks.values()])
        sleeve_edit = np.asarray(edit_masks["charcoal_sleeves"]) > 0
        assert int(sleeve_edit.sum()) > 250, (direction, "whole sleeves remain locked")
        for label, protected in [("hands_wrist", hands), ("arm_warm_skin", warm_in_arms),
                                 ("head", head), ("boots", boots), ("weapon", weapon),
                                 ("old_and_new_sword", old_new_sword)]:
            assert not np.any(edit & protected), (direction, label, "cloth edit intersects feature")
        # Pure bright skin evidence is intentionally narrower than the entire
        # ambiguous warm hand window; preserve the WHOLE window in the mask.
        pure_skin = boxes_mask(CORE_BOXES[direction]) & skin_gate(original, bright=True)
        original_array = np.asarray(original)
        guide_array = np.asarray(guide)
        assert int(pure_skin.sum()) > 50
        assert np.array_equal(guide_array[pure_skin], original_array[pure_skin]), (direction, "guide changed pure skin")
        reference_path = body / "reference-standing-rgba.png"
        candidate, calibration = apply_palette(guide, reference_path, direction,
                                                geometry_image=guide, protect_mask=output)
        corrected = np.asarray(candidate)
        assert np.array_equal(corrected[..., 3], guide_array[..., 3])
        assert np.array_equal(corrected[pure_skin], original_array[pure_skin])
        assert np.array_equal(corrected[hands], guide_array[hands])
        assert np.array_equal(corrected[weapon], guide_array[weapon])
        assert np.array_equal(corrected[head | boots], guide_array[head | boots])
        row = {
            "guide_path": str(guide_path),
            "guide_sha256": hashlib.sha256(guide_path.read_bytes()).hexdigest(),
            "feature_protect_mask": str(output),
            "feature_protect_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "method": "remove whole-arm lock only; independently restore original/new weapon, head, boots, complete hand/wrist boxes, arm warm skin, gold/warm details and alpha-edge protection",
            "sleeve_edit_nonzero_pixels": int(sleeve_edit.sum()),
            "sleeve_edit_pixels_inside_previously_locked_arm": int((sleeve_edit & arms).sum()),
            "hands_wrist_protected_pixels": int(hands.sum()),
            "pure_bright_skin_evidence_pixels": int(pure_skin.sum()),
            "skin_evidence_scope": "Bright skin gate inside previously audited hand cores. Full hand/wrist windows, including ambiguous shadows, are protected separately; colour gate is not claimed to segment all skin.",
            "pure_skin_guide_vs_original_RGBA_identical": True,
            "local_calibration_pure_skin_vs_original_RGBA_identical": True,
            "local_calibration_hands_wrists_vs_guide_RGBA_identical": True,
            "local_calibration_weapon_head_boots_vs_guide_RGBA_identical": True,
            "local_calibration_alpha_vs_guide_identical": True,
            "cloth_mask_overlap_with_protected_features": 0,
            "local_calibration_report": calibration,
            "no_model_network_vision_upload_or_production_write": True,
            "status": "feature protection numerically verified; material masks remain conservative proxies; artistic review pending",
        }
        records[direction] = row
        print(direction, output, "sleeve_pixels", row["sleeve_edit_nonzero_pixels"],
              "previous_arm_pixels_released", row["sleeve_edit_pixels_inside_previously_locked_arm"],
              "pure_skin_preserved", row["pure_bright_skin_evidence_pixels"])
    (OUT / "feature-protection-report.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
