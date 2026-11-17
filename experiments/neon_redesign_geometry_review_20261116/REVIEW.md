# Neon redesign geometry and docking source review

Reviewed the supplied `c2d52ff` checkout at `C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff` against the main functional source captured by completed full-suite commit `52f63c944ded7a651da871524d23a345b606424d`. The full 1,047-line `docs/REDESIGN-PORT.md` was read. Source identities are recorded in `SOURCE_IDENTITIES.json`. No Git, CIM, engines, importers or clients were executed; neither checkout's functional files were modified. Commit labels are supplied by the parent; the file hashes identify the actual reviewed bytes.

## Findings

### P2 — Keep non-left World docks out of the left-only rail, or give them an unfold action

`src/workspace_layout.gd:282` enables rail mode from width/theme/not-floating alone. The unfold action is restricted to the left edge at `:260–261` and `:296`. `src/world_selection.gd:231–234` hides the hierarchy Tree in rail mode. A narrow World leaf moved to the right or to another split can therefore lose its full list with no direct unfold action. The divider can still recover it, so this is an arrangement/control regression rather than lost project data.

Reproduction: move Properties to the left, move World alone to the right, then narrow World below 140 px. The predicted rail has no unfold button. The intended contract in the port document and the workspace source comment says floating/tabbed-elsewhere arrangements use the list. Bound the rail predicate to its supported placement, or resize the actual World leaf from a placement-independent unfold action. The independent details are in `docking-audit.md`.

### P2 — Evict removed models from the new timeline summary cache

`src/app.gd:2815–2820` stores `[instance.data, frames]` under each model ID in `timeline_key_cache`. Entries are replaced when a live model's data identity changes, but the cache has no clear or removal anywhere in the reviewed source. Removed objects and models from earlier projects therefore retain their last complete data dictionaries for the rest of the application session. These dictionaries can contain long animation/channel arrays; repeatedly browsing projects or adding/removing animated models accumulates stale retained data even after the runtime is replaced.

Prune IDs absent from the current world, or reset the cache when the world identity changes. Keep the identity-based update for live IDs. A future regression should populate two distinct worlds, remove one model, refresh timeline summaries, and verify that only live world IDs remain in the cache. This is source-proven retention; no memory benchmark or engine test was run.

## Geometry and input assessment

- The nonzero `fit_inset` is symmetric and applied by `canvas_view.gd:86–103` to the same image rectangle used for drawing overlays and pointer/native-coordinate mapping. `setup_frame_size()` uses the integer Setup viewport extent, matching `scene_rect()`. The new overscan at `scene_view.gd:67–73` uses the corresponding frame height, so the centered perspective projection algebra remains aligned. No concrete mapping defect was found in this code path.
- The supported-camera guard at `scene_view.gd:80–84` retains Focus for non-centered/non-perspective cameras. The new copy helper does not introduce an unsupported orthographic Setup path.
- The 0.01 px acceptance margin at `canvas_view.gd:115–121` is in control-space pixels after the native-coordinate round trip. It is finite-gated and bounded by both the canvas and scene rectangle. Selection-mask sampling clamps its UV-derived pixel coordinates in `world_selection.gd:510`. No concrete off-scene selection regression was found from this tolerance.
- The neon timeline's added 12 px content inset changes both `x()` and `frame_at()` at `timeline_view.gd:311–318` using one shared width. Cel, object, audio and sequence hit/drag paths call those helpers; `sequence_timeline.gd` uses the same timeline mapping. The 190 px label boundary and row heights remain unchanged. No concrete inverse-mapping regression was found.
- Recursive dock-tree state serialization, tab/split pruning and migration retain the baseline algorithms; the full-height left nesting reuses the four split roles and is reversible. The 10 px strip input path preserves splitter priority and modal/Home/export guards in source. Floating windows and actual Windows pointer routing still require runtime evidence.

## Owner-contract design item: dimming in Setup

`canvas_view.gd:139–149` dims every area outside `image_rect()` whenever neon Setup is active, even with Frame off. Frame off leaves an 8% frame line; Frame on raises it to 45%. This is explicit in `REDESIGN-PORT.md:250–253`, `:321–323` and the later inset description, so it is intentional presentation behavior rather than a missing-condition implementation bug.

The owner's prior request favored seeing the whole setup view, with the focus helper optional. Preserve this as a design-contract decision: a separate dim-surround control, or connecting dimming to a clearly named frame/focus aid, would meet that preference while retaining the new composition layout. Do not silently treat the port document's intent as overriding the owner's request, and do not describe a visual preference as a measured geometry defect.

## Runtime coverage still needed

The existing `tests/scene_view_unit.gd` creates a canvas with zero inset and calls `copy_camera` without the new frame-size argument. Its previous PASS therefore does not exercise the new inset projection/ray branch. `inset_scene_regression.gd` is a **source-only, unexecuted draft** for the parent to run after the current exclusive graphics lease closes. It exercises actual Godot camera projection and ray APIs over nonzero insets, portrait/square/landscape outputs, fractional display extents, both keep-aspect modes, FOV extremes, camera roll, exact-edge acceptance and rejection beyond the tolerance. It uses synthetic points and no native assets. It has not been Godot-parsed or runtime-validated here.

Future parent invocation must use the existing approved isolated private-desktop mechanism with the redesign checkout as `--path`, the absolute draft script as `--script`, and a fresh owned output JSON after `--`. Preserve actual exit/receipt/reap and closure evidence. This review does not authorize overlapping the currently running redesign Windows suite, and does not claim the suite or this draft has passed.
