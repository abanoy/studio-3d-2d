# Continuous foot contacts — contract and verification gates

Model7 supplies persistent contacts through the shared editor/playback/final
sampler. Simple Planted feet creates/releases ranges and opens direct correction;
Advanced adds exact targets and knee poles. The separate [direct authoring
option](foot_hold.md) still produces sparse FK and retains its interpolation
sliding limitation. Model6 cannot carry an ignored contact field: it rejects that
data. Models1–6 keep their previous evaluation; older Studio versions reject7.
See [integration and current installation status](contact_animation.md).

`foot_contacts.gd` validates the `studio_foot_contacts_1` descriptor: up to64
ordered, nonoverlapping half-open source-time ranges. Each range has a stable ID,
two exact three-bone chains, fixed world positions and normalized orientations.
The existing validated humanoid leg bindings and shared limb IK are used. Targets
are explicit captured positions, not inferred floor contact or collision geometry.

Provisional engineering semantics, not new owner decisions:

- A piece maps project time to source time using its existing start/source_in.
- A split retains the descriptor and source-time address. Moving it carries contact
  timing with its motion. A gap only retains a pin when both adjacent endpoints
  declare the identical contact; differing contacts release rather than invent one.
- Before introduction there is no contact. After a final planted piece, the last
  contact holds; an explicitly unplanted next piece releases it.
- Evaluate ordinary parent/root/body pose first, then solve both legs and world
  orientations from that exact frame's input. Never seed from the previous solved
  frame. Reverse-order scrubbing must produce identical results.
- A failed second leg restores the whole input skeleton and returns an error.
  It cannot publish a half-constrained frame or silently stretch a leg.

The optional `pose_override` argument to the existing limb solver supplies the
current full evaluated pose. Existing callers retain exactly their old default;
the experiment never swaps model dictionaries, writes keys or edits native files.

The Windows experiment uses six actual skins: original mannequin, Miku, GMod Reimu,
SFM Scout and both owner VRMs. It evaluates49 half-frame samples forward and backward
per skin, after JSON decoding the targets, checks endpoint/orientation constraints,
deterministic seeks, late-leg rollback, source/data isolation, range/gap semantics,
and visible midpoint GPU deformation. The same engine float32 vectors/quaternions
roundtrip exactly. Raw parsed double-array position components can differ by about
1.39e-17; that difference is reported, not called exact raw numeric preservation.

## Verification gates before normal activation

1. Versioned model acceptance/binding validation and lossless old readers; retain
   body/expression/visibility data through promotion. Bound total metadata before writes.
2. Source-time range creation/release/edit controls, clear reach feedback, Undo,
   direct root/limb corrections, meaningful selected-part key editing and draft rules.
3. Real clip split/move/cut/paste/whole-object retime and gap tests. Define reanchoring
   for another instance/project; do not blindly reuse foreign fixed world targets.
4. Shared Model/world evaluation for preview, hidden selection, current framing and
   final capture. Read-only samples and physically modified skeletons must agree.
5. Body Physics versus secondary-only transitions and Local/World Record: bake/remove
   only the owned contact interval atomically, preserving contacts outside the take.
6. Packed/linked/recovery/lesson checkpoints, separate-process reopen, actual scrubbing
   and exact preview/export movie checks. Surface unreachable contacts without silently
   exporting unconstrained frames. Benchmark compiled bindings and dense projects.

All six gates retain their original scope. Current evidence mapping:

| Gate | Actual source verification |
|---|---|
| 1 — versions, bindings, budgets | contact_animation44, contact_bindings36, old body24unit/72app, contact controls/correction and viewport overflow refusal; legacy world/HAS regressions |
| 2 — controls and corrections | contact_editor33, correction36/native5, viewport174writer/5cold-reader; reach, drafts, direct legs, Undo, poles and stale ownership |
| 3 — clip semantics | clipboard27 plus native identity76writer/4cold-reader; split/move/retime and same/foreign-instance reanchoring, capacity and Cut reuse |
| 4 — shared evaluation and rendering | animation44/native5, selection67/native5 with independent engine-baked silhouettes/bounds, parent20, transform129, physics48; reverse sampling and final reach refusal |
| 5 — simulation ownership | physics48/rawVRM plus ordinary recording17unit/57app; Body/Hair/combined OFF and Local/World interval/outside-pose preservation, dense freeze refusal |
| 6 — persistence, media and scale | persistence26writer +8linked/9packed/8recovery/9lesson in fresh processes; bindings36 dense five-native32block scene; viewport174/5 with own MP4/cold reverse poses |

The frozen-source full verifier includes these suites and the complete existing
editor/drawing/audio/physics/recovery/tutorial/media path:93processes, all original
assertions passed. This is full coverage across bounded batches, not one
uninterrupted command. Installed-copy checks and guarded promotion are separate;
consult the current installation marker/memo rather than an older WIP snapshot.

Walking/path assistance, overshoot, automatic ground inference, full-body anatomy,
all-rig fidelity and native/full cloth remain unfinished. Teacher crash-context
reattachment is not proved by lesson Store checkpoint tests. Those broader goals
are not closed by this contact feature's representative native coverage.

The integration uses the ordinary sampler/world renderer and actual packed HAS
and MP4 paths. See contact_animation.md, the current installation marker and latest
progress entry for source versus installed-copy evidence. Earlier WIP checkpoints
are retained independently and do not determine the current installation state.

The correction controls additionally use `studio_foot_contacts_2` for
explicit per-foot world knee targets and bend reversal. Version1 remains readable
and is retained when no new knee fields are needed. Older experimental readers
reject2; updated validation rejects knee fields hidden in1. See contact_animation.md
for Simple/Advanced controls, compatibility, actual evidence and remaining gates.
