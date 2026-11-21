# Lighting increment handoff

Published branch: `worker/editable-lights-20261121`.
Completed increment: `edf98f6820f873d3ee2e8755b6595ab8ea269e2e`
(two commits: `714ba688`, then `edf98f68`; base `243e6a1e`).

Independent GitHub fetch into an empty object repository matched 1,164 functional
source/changed-evidence files, 12,306,652 bytes, raw bytes and Git blobs exactly.
See `benchmarks/lighting_publication_edf98f68.json`. This is source publication
verification, not another runtime test or a new full-checkout qualification.

The increment provides directional/point/spot authoring, a selectable named list,
property editing, visibility/removal, presets, Undo/Redo, native save/reopen and
the common preview/export path. Actual focused CPU103, Compatibility107 and
Forward+119 pass, including prepared native model/environment illumination and
two 1080p24 H.264 movies with exact preview/PNG/cold-reader pixels.

Retain the three scene_lighting modules. Integrate only the small hunks:

- app.gd: one editor member, setup after sequence_editor, tooltip/status wording.
- renderer.gd: one lighting member, setup after world creation, sync/ambient calls.
- lighting.gd: optional document validation after mode validation.
- run.py: opt-in --forward-plus flag, default launch unchanged.

Do not copy app/renderer wholesale. No world-runtime/model/material/export source
changed in this completed increment. Existing imported lights/materials stay intact.
Forward+ cubemap reflections/local fill are approximate; Compatibility has an
actionable limitation. The pinned Forward+ runtime emits texture-RID shutdown
warnings. Dynamic/reference-only reflection behavior remains unqualified.

The earlier has-lighting-20261121 checkout and paused rebase remain preserved.
Installed Studio, original assets and shared tools were not replaced. Private
models/captures/video remain in ignored output. Main was neither merged nor pushed.

A separate follow-up in the isolated checkout is developing opt-in SDFGI with
static-environment contributors, model receivers and explicit render settling.
That follow-up is not qualified by the completed increment's evidence. Its CPU
checks and future serial private-desktop tests are separate scopes.
