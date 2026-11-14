# Geometry inputs for local Klein consistency trial

Read-only source audit, using the installed Pillow12.2.0 and NumPy2.4.4. No downloads, network requests, model calls, production assets or manifest writes.

`inputs.json` contains the production manifest SHA, eight runtime/source-art PNG pairs,104 frame measurements,24 model inputs, original native alpha files, source crop coordinates, affine transforms, output SHA256 values and canvas alpha bounds. `findings.json` records interpretation and target suggestions. `prepare-inputs.py` reproduces the files locally.

Every model input is512×768 RGB on light gray(228,228,228). Scale is400 pixels/world unit. Ground anchor is(256,712). Native scale is exactly the installed action UPP×400, shared by every direction and phase of that action. No figure is independently fit to its own bounding box. Native RGBA crops and original alpha are preserved separately; RGB input generation retains source antialiasing. No source PNG is rewritten.

Names: `explore`/`held`, `idle`/`run`, `front`/`right`/`back`, `p0`/`p2`/`p4`. The eighteen-image `overview.jpg` shows standing,run phase0,run phase4; `overview-run-p2.jpg` shows six run phase2 inputs. The latter is useful because front-facing feet are already retracted while side-facing feet remain near contact.

The geometry argues against a per-direction runtime scaling fix. Exploration run phase0 bbox heights(front/right/back) are1.543/1.530/1.504 world; phase4 is1.569/1.534/1.534. Front is not uniformly shorter. All-frame median alpha-top-above-anchor(front/right/back) is1.560/1.532/1.547 world, while front bbox median is lower because feet retract. Run phase2/front lowest foot is0.054 world above ground versus right-0.015; phase6/front is0.091 versus right0.007. The source pose/phase and apparent leg-to-torso proportions need review. Merely increasing front/back scale would also enlarge their heads and defeat accepted standing scale.

Silhouette leg-gap and chest-color measurements are explicitly proxies. They are not anatomical landmarks or approved color masks. Use the accepted standing material, head design and side-run proportions for local edits and visually inspect the actual outputs before installation.
