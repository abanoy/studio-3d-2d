# Model import simulation defaults OFF

Source-only candidate for the owner's explicit request, recorded2026-11-20: newly imported model instances must start with both Body Physics and Hair & clothes off. All imported joints, body definitions, constraints, spring chains and other retained metadata remain available for deliberate activation. This default is not a fix for poor responsiveness when motion is switched on.

No source in the active1084-file checkout or existing review has changed. The360 Full remains independent. The candidate is unparsed, unrun and not adopted.

## Small implementation

The only application behavior change is src/import_actions.gd placement(): physics_on_import changes from true to false. The entire file is otherwise byte-exact, including existing line endings. This covers the ordinary Add model, timeline Add, OS-drop and asynchronous source-preparation paths because they carry the same placement context. Low-level add_model already defaults to no interactive start, and adding a .has asset already lacks that new-import start flag. Hair & clothes was not automatically started for a new object; the real import checks now explicitly assert both controls off.

app.append_object still snapshots and restores existing explicit live peers independently from the new object's placement flag. PhysicsEditor.queue_import_start, enable_body, enable_hair, validation, source fingerprints, pending/modal/seek cancellation and normal Off/Record behavior are unchanged. A running body, hair-only peer or combined peer remains in its prior mode when another model is added; the new model stays off. There is no mutation of import reports or removal of native setup.

Existing HAS saves currently freeze live simulation before serialization. There is no serialized live-ON flag to create or reinterpret. This patch leaves save/open code unchanged: saved frozen poses, recorded keys, retained setup and provenance still restore; opening a file does not create a fresh live simulation. Existing transient peer restoration during structural imports remains explicit and unchanged.

## Authored validation

The three previous files are preserved byte-exact under bases. Their old automatic-on expectations and previous results remain historical evidence for the old policy. New expectations are justified by the new owner request, not by weakening the simulation checks.

- import_physics_defaults_unit.gd:16 authored inert request/peer-intent checks. It exercises the actual placement and intent methods with owned fixtures, including the exact false boolean, camera/height context, copied caller context, body/hair/combined restoration, retained data and an empty project. No actual solver or artist asset is claimed by these controls.
- import_physics_smoke.gd:42 static assertion sites, with additional generated native-plan checks. Ordinary import now explicitly checks both controls off, no running simulation and no queued start. Existing gravity, visible controls/colliders, no unsolicited keys/history/camera changes, Off frozen pose, Undo/Redo, independent peers, map selection, unsupported-rig refusal, modal ownership, explicit queue cancellation/seek, hair-only and combined VRM modes, Local Record, exact drawing, packed HAS and movie equality all remain exercised. The old auto-on operations become explicit activation before their physical assertions. Added cold-open check confirms the saved frozen pose/setup without fresh simulation.
- verify_import_physics.py:only its first descriptive docstring changes. Every runtime invocation, timeout, hidden-display rule, original hash/nsmtime check, engine-log failure predicate, real h264/frame/duration assertion and final source preservation check is byte-exact.

These tests have not been parsed or run. No pass count, gravity result, movie result, native model result or cold-open result is asserted by this packet.

## Root qualification after the active Full closes

Apply PATCHES.json only to a fresh disposable snapshot after confirming every current base size/hash and absent new unit path. Preserve all other source bytes, the current checkout and old review. Parse and run the16 request/intent controls first, then run the existing private-display import-physics verifier against the replacement smoke. Its original native-fixture and source preservation gates remain required. Exercise normal Add/timeline/drop, prepared Source/MMD/VRM, pending height review, .has asset import, existing body/hair peers and explicit toggles; record defaults separately from the still-needed ON performance fix. Run regression checks appropriate to any eventual adoption.

The candidate does not add a new preference, project format, solver profile or saved simulation state. A caller can still explicitly request and validate activation through the existing APIs; ordinary new-import defaults remain off.
