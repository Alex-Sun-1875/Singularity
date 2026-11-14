# Opening Scene Composition Implementation Plan

> **For agentic workers:** Execute in the existing shared workspace. SceneBuilder and new layout data are the scene implementer's exclusive files; preserve the other agents' work.

**Goal:** Give the first inn phone view and S01 street facades clear foreground, middle ground and background using the installed Poly Haven library.

**Architecture:** Keep WorldData task, spawn, exit and building coordinates fixed. New furniture is declarative layout data whose footprint feeds both Navigation and Bullet. Shared EnvironmentAssets meshes/materials remain library-owned.

**Tech Stack:** Existing Cocos 3.8.8 standard materials, native primitive structural pieces, shared CC0 Poly Haven furniture/props. No new dependency, asset download, shader or tests.

**Spec:** `docs/superpowers/specs/2026-11-04-chapter-visual-fidelity.md`, plus the parent's 2026-11-05 inn/street composition brief.

## Decisions

- The entry no longer stands on a twelve-metre red-brown rug. Short muted runners and local meeting rugs reveal the timber floor and separate the door, dining and hearth functions.
- Two unequal bare-wood round-table groups frame the start view. The yellow checkerboard dining-table asset is omitted from the opening; books, bowls and jugs form small purposeful groups.
- Existing two 180lm table lights move with their actual tables. Do not restore the former luminance/floodlight bug or add a lamp per decoration.
- Only S01 facades receive the new human-scale bays, eaves supports, window ledges and door-side work/living groups. New solid props get the same conservative rotated footprint in both navigation and Bullet. Floor inlays/trim remain non-blocking.
- Local BG3 artbook pages supplied composition principles (silhouette, layered occupied spaces, functional clusters), not source textures or geometry.

## Tasks

- [x] Add inn placements and source-only S01 frontage group definitions; make their solid footprints shared by navigation/physics.
- [x] Replace the opening rug/visible yellow-table arrangement; place the two existing lights over the new tables and vary tabletop use.
- [x] Add S01 facade bays, shallow stone/timber layers and a small number of purposeful frontage groups inside or beside existing building footprints.
- [x] Run existing TypeScript and affected navigation checks. Request the parent's release build; verify normal phone view and real-input inn/town passage. Save before/after evidence and report only the improved areas.

## Review focus

All five inn interactions and three exits must stay reachable; spawn and portal coordinates remain exact. Furniture must be grounded and food placed on actual tabletops. Door-side props must not enter doorway corridors. Near-camera objects must leave player feet readable. Repeated switching must dispose only scene-owned meshes/materials while preserving the shared environment library.
