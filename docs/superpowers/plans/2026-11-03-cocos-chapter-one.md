# Cocos first chapter implementation ledger

Approved plan: complete v5 M1/M2 in Cocos 3.8.8 for TapTap minigames, R1 S01–S20
and 33 roads, town T1–T6, U1-01–05 and U2-01. All user decisions in this chat
are binding. Development root: src/cocos. Local source-art assets only.

## Tasks
- [x] Cocos project, physics, rendering and input
- [x] TypeScript rules, equipment, combat, quests and durable saves
- [x] R1/underground content and navigation
- [x] Locally authored FBX characters, materials and animation (test assets)
- [x] Runtime UI and full command playthrough in real Cocos
- [x] Model comparisons and multi-frame Cocos motion evidence
- [x] Official TapTap adapter and real-AppID build entry
- [ ] Final concept-level art parity, regional baking and full multi-level LOD
- [ ] TapTap package and device verification (real AppID unavailable)

## Rulings and evidence
- Work in the user-specified checkout on codex/cocos-chapter-one; prior untracked
  source assets are required and would be absent from a clean linked worktree.
- Parent src/AGENTS.md is Maker-generated. User explicitly authorized Cocos;
  src/cocos/AGENTS.md records the applicable Cocos workflow.
- No Tap minigame AppID exists. Local Cocos work proceeds; real Tap device
  verification requires a genuine project identity. No ID will be fabricated.
- Existing Lua nine rule tests, flow/save tests and 53-bone character motion
  test passed in the planning turn; they are migration references only.
- Parallel asset/content/rule workers have disjoint file ownership; root owns
  runtime integration, editor/build configuration and final verification.
- Restore preserves the saved position and resources, clearing transient attacks;
  it does not silently heal at a checkpoint. Death retry uses checkpoints.
- Touch uses one movement pointer plus one action pointer; dragging into the
  cancel zone cancels bow/oil/spell preparation before a subsequent dodge.
- Terrain has actual water barriers, complete/broken bridges and continuous ramps;
  one height field drives mesh, navigation and character feet. Bullet capsule
  movement results constrain the pure rules' player coordinates.
- 75 TypeScript tests, core/full typechecking and 3 binary FBX/asset checks pass.
  Browser results live under src/cocos/test-results (ignored build evidence).
  The real Cocos command pilot completed 11 areas, cart guards/captain, underground
  dinner/workers and gate/cooperation with no HP/inventory/flag grants.
- Each actor has a lazy AssetBundle. Builder default is Web merge_dep and
  wechatgame subpackage, verified against installed 3.8.8 config transformation.
  Bundle manifests resolve shared material dependencies before prefab loading.
- Model sources preserve high-resolution geometry/textures; game FBXs have 53
  bones, 10 clips and <=4 weights. Source/concept comparison explicitly records
  remaining face/hair/cloth/detail/animation differences. These are test assets.
- No public publishing, cloud model generation, Git commit/push, old-source cleanup
  or fabricated Tap identity occurred.
