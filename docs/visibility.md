# Visibility keys and project fades

Select a model, map or group. **Visible at this frame** records an on/off key at
the current master frame; the viewport context menu offers the same Show/Hide action.
The state persists until another explicit visibility key. Moving/splitting/copying
motion pieces never turns the object on. Visibility addresses remain in project
time even when a motion piece or its whole take moves. Reference-only remains an
independent static output exclusion. Original static flags remain the initial state
for old and new documents; no key is inserted merely by opening an old project.

**Options**, available in Simple, sets **Visibility fade (milliseconds)** for the
whole project. New projects default to300;0 is an instant cut. The setting is saved
in `video.visibility_fade_ms`, bounded0–10000. Missing values read as300. Each state
change starts a linear opacity transition at its exact key timestamp, in rational
project time, without rounding300ms to a frame count. A reversal starts from the
current opacity; repeated same-state keys do not restart the fade. At the key frame
an ordinary fade starts from its previous opacity; a zero-duration cut is immediate.

Remove visibility key here restores the preceding state; Undo restores the key.
Show/hide edits and project settings have Undo/Redo. Tiny green/red markers show
visibility keys on the collapsed object row. They are state markers, not fade clips.
More complete expanded channel/key controls remain future work.

Presence still gates before introduction, empty motion-piece arrays remain absent,
and hidden/reference-only ancestors retain their effect. Selecting a fully hidden
object shows only the existing editor ghost. A parent's opacity multiplies child
opacity once; material ownership stops at independently loaded instance boundaries.

The first visibility edit promotes that object to `studio_model_3`: the version2
source-piece contract plus a mandatory sorted `visibility_keys` array of at most241
`{frame,visible}` records. Version1/2 readers remain supported by the current app.
Older app binaries reject version3 instead of silently discarding animated visibility.
Version3 records share the same normalized GLB, bones, posing, world schema4, storage,
packed/linked HAS ZIPv1 and recovery. Other objects are not promoted. The internal
`set_flag` helper retains explicit static-initial-state editing for existing fixtures;
user-visible controls call `set_visibility_key`.

Compatibility/OpenGL ignores `GeometryInstance3D.transparency`. Fades therefore use
temporary instance-local BaseMaterial3D copies with alpha blending and multiplied
original albedo alpha. Opaque/fully hidden endpoints restore original override
references and rendering modes. Native GLB data/resources are not edited or saved
with transient opacity. Standard imported GLB materials are supported; arbitrary
custom ShaderMaterial, material overlays/extra passes, transparent sorting fidelity,
native shader effects and light/shadow fade equivalence are not certified. Source
materials already using alpha retain their base alpha, but sorting can change during
a partial fade. No switch to a different renderer or external dependency.

Primary pinned APIs: [GeometryInstance3D transparency](https://docs.godotengine.org/en/4.6/classes/class_geometryinstance3d.html#class-geometryinstance3d-property-transparency),
[BaseMaterial3D](https://docs.godotengine.org/en/4.6/classes/class_basematerial3d.html).

`tests/verify_visibility.py` exercises real app controls, rational timing, reversal,
piece gaps, Undo/Redo, actual OpenGL intermediate pixels, endpoint material restoration,
parent/child ownership, native MMD/GMod/SFM materials when locally available, packed/
linked/recovery, independent raster/WAV and preview/export PNG/MP4. Optional native
fixtures are private and skip when absent; authored checks remain mandatory. Results
and current verification phase are recorded in progress_memo.md. Tests do not certify
physical input feel, all native materials, subjective sound or clean-machine behavior.

Observed visual limitation: the Miku partial-fade capture exposes overlapping/internal mesh surfaces through the character. Per-surface alpha blending is verified, but it is not a single flattened silhouette dissolve. A future whole-object compositing/depth treatment should improve that appearance; native fade aesthetic acceptance is still open.

Fresh cloud verification on 2026-11-06 ran the existing scenario on the private
Linux software renderer:47checks pass. It covers persistent visibility through
clip gaps, rational300ms fades/reversals, immediate cuts, independent descendants,
packed/linked/direct recovery restores, legacy promotion and source preservation.
The48frame1080p24 H264/AAC movie retains exact preview/render input; decoded cue
onset is sample48002 at48kHz (expected48000). Three unavailable MMD/GMod/SFM
fixtures explicitly skip. This run uses same-process document reopening and a
direct checkpoint restore; it is separate from cold-process/SIGKILL recovery
verification and does not establish native fade aesthetics. Proof:
`/workspace/has-handoff-audit/visibility-current/verification.json`.
