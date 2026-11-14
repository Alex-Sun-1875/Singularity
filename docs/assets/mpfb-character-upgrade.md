# MPFB character appearance pass

## Current integration — 2026-11-05

The current production set is ten actors with **11 actions each, including
`walk`, and 53 bones**. The latest integration excludes the calibration frame,
bakes the root transform and records **6,265,190 bytes** of runtime textures.
See [library-integration-record.json](../../source-art/characters/cocos/library-integration-record.json)
for the current actor count, export decisions, portrait SHA-256 values and
existing-check results. Mobile walk/run and weapon behavior are separately
recorded in [final-mobile-motion.json](../../src/cocos/test-results/final-mobile-motion.json).

The appearance pass and numerical results below describe the **earlier
2026-11-04 stage**. In particular, “10 actions”, 460,930 triangles and 6,288,315
texture bytes are historical values. They must not be quoted as the final
integrated asset totals. Source fidelity and real-device performance remain
separate acceptance work.

The ten v5 actors now use MPFB 2.0.18 as an active authoring step, rather than
only keeping the tool on disk. `cocos_mpfb_appearance.py` calls the upstream
`TargetService.bulk_load_targets`, `TargetService.bake_targets`, and
`HumanService.add_mhclo_asset` services. The latter uses MPFB's MHCLO fitting
and asset loader. The game continues loading the existing actor bundles and
the same FBX paths.

## Reused assets and licenses

| Source | Used here | License |
| --- | --- | --- |
| [MPFB 2.0.18](https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18), released 2026-10-11 | Target loading, MHCLO loading/fitting, editable morph baking | Tool: GPL-3.0-or-later |
| [MPFB bundled targets](https://github.com/makehumancommunity/mpfb2/tree/v2.0.18/src/mpfb/data/targets) | Small cheek, chin, nose, mouth and age refinements, selected per identity | CC0-1.0 |
| [MakeHuman system assets](https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html) | `hair/short02`, `hair/short04`, `hair/bob02`; `eyelashes/eyelashes01`; young and middle-age Caucasian skin maps | CC0-1.0 |

MPFB requires Blender 4.2 or later; this pipeline runs the pinned Blender
4.5.15 LTS. The [upstream license](https://github.com/makehumancommunity/mpfb2/blob/v2.0.18/LICENSE.md)
separates the GPL program from CC0 meshes, targets, textures and generated
output. The game ships asset derivatives, not the MPFB Python program.
System `.mhclo` and `.mhmat` headers record the September 2020 CC0 release and
the original copyright holders Data Collection AB, Joel Palmius and Jonas
Hauquier. The original CC0 asset license text is included alongside the actors.

`Setup-CharacterTools.ps1` installs only below `src/.tools`. The bootstrap
registers the pinned source package for a background Blender session and
redirects MPFB data, config and extension storage into the workspace. It does
not save Blender user preferences or install a global extension. No MakeHuman
server, network generation or user account is needed for authoring.

Pinned archive SHA256 values:

- MPFB tag archive: `ada7c4ff11e79cf6ed9b441bccabc52c9359f2848b988f66e89c14c30b21fed7`.
- MakeHuman system asset pack: `b542127a8e25547c7c29c19f2d1d2adb9a664c80396ecd694095dbc8028a0107`.

## What changed

`mpfb-appearance-presets.json` records all ten target mixes and upstream asset
choices. They refine the existing frozen faces by roughly 1–3 mm, without
replacing the v5 faces or changing body proportions. The refined source skin
keeps an editable `MPFB_face_refinement` shape key. Export-only processing
bakes this through MPFB so the Cocos model does not depend on morph support.

The smooth ellipsoid scalp has been replaced with MPFB-fitted system hair
meshes. Existing brown curls, broad blonde bob waves, high ponytail, half-up
waves and short/swept locks retain their authored silhouettes. Their lock
cross sections are slightly reduced, and a cropped, recolored CC0 strand
texture replaces the former nearly solid hair color. Upstream UVs and alpha
textures remain on the fitted hair. Runtime cards use alpha testing and
two-sided rendering; they add two material surfaces per actor including lashes.
The generic bob's eye-covering front sheet is trimmed beneath the existing
crown waves on Mira and Evelyn, keeping both eyes visible as in v5; removed
face counts are recorded in the appearance report.

Lorn, Evelyn, the captain and the two heavier raider roles use age-appropriate
system skin detail. Raphael, Mira, Nightqi, Kael and the archer retain their
young skin identities. Existing clothes, equipment and colors are preserved;
the shared leather/fabric PBR materials continue through `SurfaceMaterials`.

All 53 named bones, their rest positions and all ten actions remain intact.
The pass hashes every existing action curve before and after editing and
records the result in `mpfb-appearance-report.json` and each actor manifest.
`mpfb-preservation-report.json` additionally compares all ten final sources
against the actual pre-pass sources: bone names, parent relationships, rest
matrices, actor transforms and action curves match exactly.
Hair and lashes bind to the existing `head` bone. Their source `.mhclo`
weights or subrigs cannot add bones or overwrite the current animations.

## Rebuild and review

Run after the existing source refinement/ground-contact steps and before LoD:

```powershell
& tools/model-pipeline/Setup-CharacterTools.ps1
& src/.tools/blender-4.5.15-windows-x64/blender.exe --background --factory-startup --python tools/model-pipeline/cocos_mpfb_appearance.py
& src/.tools/blender-4.5.15-windows-x64/blender.exe --background --factory-startup --python tools/model-pipeline/cocos_optimize_exports.py
& src/.tools/blender-4.5.15-windows-x64/blender.exe --background --factory-startup --python tools/model-pipeline/cocos_verify_characters.py
python tools/model-pipeline/cocos_test_assets.py
& src/.tools/blender-4.5.15-windows-x64/blender.exe --background --factory-startup --python tools/model-pipeline/cocos_verify_characters.py -- --render --runtime
python tools/model-pipeline/cocos_comparison_pages.py --mpfb
```

The appearance pass may be run again without accumulating facial offsets or
repeatedly shrinking locks. Both it and the exporter accept
`-- --character raphael` (or a comma-separated list). Existing high-resolution
authoring maps stay in `source-art/characters/cocos/textures`. New runtime
hair-card maps are 256px for the two principals and 128px for the others;
lashes are 128px. Other established budgets remain in force.

Before images are in `previews/mpfb-before`, final actual reimported FBX images
in `previews/runtime`, and paired hero/Mira review boards in
`previews/mpfb-comparison`. The same verifier camera, lighting, framing and
render settings produce each before/after view. These are actual asset
renders, not concept images or generated promises.

Final verification on 2026-11-04: all ten actual FBX reimports have 53 bones,
10 actions, resolved sibling textures and held death poses. The independent
21-sample dodge/death check found a minimum foot height of +0.22 mm. Maximum
movement between death hold samples is 0.00000044 m. The existing three Python
asset checks pass. Combined runtime geometry is 460,930 triangles and PNG
maps total 6,288,315 bytes, within the existing 6,500,000-byte check. New test
cases, test scaffolding and dependencies were not added. Cocos import/build
is verified separately by the integration task.

## Limits

This is a practical editable appearance upgrade, not BG3 production parity.
The underlying existing combat animation and clothing construction are
unchanged. Volume locks still read as stylized geometry at close range;
system hair cards provide a reusable base rather than a bespoke groom.
Skin uses the mature diffuse assets, not a full scanned micro-normal/SSS set.
No Larian model, texture, groom or animation is shipped. The local BG3 artbook
is visual direction only.
