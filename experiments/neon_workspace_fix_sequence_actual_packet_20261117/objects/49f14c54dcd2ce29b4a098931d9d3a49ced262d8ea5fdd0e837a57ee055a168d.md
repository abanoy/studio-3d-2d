# World rail teardown lifecycle fix — source proposal

The root's unchanged f387 run completed all 48 workspace assertions, then emitted TextServer `fd is null` errors from `WorldSelection.set_rail` through `WorkspaceLayout.refresh_world_mode` after the fixture freed the application. The strict wrapper correctly failed. A second unchanged-source run under a newly checked host driver reproduced the same result. Those failures remain retained; this packet does not relabel them as passes.

The source chain leaves `panels.world.resized` connected while the workspace manager exits, and both callbacks permit styling sibling controls during teardown. `set_rail` installs a freshly created SystemFont. This identifies a missing application lifecycle boundary. It does not establish a particular internal TextServer font-release mechanism.

The two proposed files add explicit active state at node entry and clear it first at exit; validate live owners and controls before any rail mutation; disconnect World resize before the original exit-time preference save; and reconnect once with a deferred forced refresh after reentry. Reparenting remains supported. The full font factory, Neon family order and weight 500, Japanese fallback, palette, widget styling and existing pick cleanup statements are preserved. No font cache, test error filter, application file or wind-manifest row changes are included.

Apply only the exact final proposals after source review. They supersede preliminary unsealed hashes shared during preparation:

- `world_selection.gd.proposed`: `fb2cfa70ab94dbf4d9a57c3f041cb10916aed7e828c94af14feee6ade0b790de`
- `workspace_layout.gd.proposed`: `7da378b1147266fbecdabf63422e19b1ee06024c40083d6fcf4ed8e93540bcfd`

The parent should first run the unchanged 48-check workspace wrapper with its unchanged error rejection, then existing Neon/resize/dock/nested suites. The additional `neon_world_rail_lifecycle.gd` fixture has **29 planned checks**, not an observed result. Stage it as `res://tests/neon_world_rail_lifecycle.gd` and supply a fresh output subdirectory under that checkout. Run the exact same fixture against original and corrected source under the root's approved private desktop. It checks actual font-family switches, pending-save flushing, off-tree callbacks, direct selection calls, one reconnect, working docking after reentry/reparent, queued deletion and immediate `app.free()` after real resize/restyle. Its wrapper must reject every original ERROR/FAIL/leak marker; no output filtering is proposed.

`prepare.py` proves an exact inverse to both original files and preserves their line endings. `audit_source.py` verifies all untouched GDScript function bodies, unchanged font factory and cleanup statements, and the fixture's planned check count. These are CPU/source checks. Neither the preparer nor peer ran a Godot parser, engine, CIM or Git, or edited the frozen review checkout. Original regression files remain unchanged.

`PREPARATION_REFUSAL1.json` records an intermediate source-audit refusal: an inverse-text checker required a common one-line replacement to be unique. It was corrected to verify the exact stored insertion position, without changing a runtime gate or product file.
