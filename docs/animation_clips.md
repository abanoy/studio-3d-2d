# Versioned independent animation pieces

The native standard model record has two compatible reader versions. Imported or
unsplit objects keep `format: studio_model_1`. A split/cut/paste promotes the edited
object to `studio_model_2`; other maps/models/groups keep their current records.
Both versions use the same GLB, native bindings, renderer, posing tools and world.
There is no source-ecosystem-specific animation branch or external-format exporter.

Version2 retains the existing identity/root/working pose/visibility/provenance fields.
Its top-level `pose_keys` is empty, avoiding ambiguous ownership. New fields:

- `animation_clips`: sorted, nonoverlapping pieces with stable `id`, project `start`,
  positive `length`, `source_in`, independently owned source `keys`, `base_pose`
  and `base_transform`. Project ranges are half-open; source sampling is integer.
  An optional `auto_extend` marks a newly authored take with a complete owned key
  range. Splitting clears it; sliced/cropped source curves stay fixed.
- `presence_offset`: preserves any existing delay between the old take's earliest
  key and its introduction. Ordinary imported takes use zero. Piece moves/removals
  update introduction relative to the earliest remaining piece. An explicit earlier
  manual key corrects introduction. This is not an animated visibility system.

A piece samples `source_in + project_frame - start`. Its source curve retains
keys outside the visible slice because those control easing inside the slice.
Splitting copies the complete source curve to both pieces and adjusts their slices;
it never approximates easing by inventing boundary keys. Later edits change only
one independently owned curve. This costs metadata rather than silently coupling
siblings. Source GLBs, native skeleton names and original files stay unchanged.

Between pieces, connect the preceding last included sample to the following first
sample, respecting the preceding source key's hold/linear/ease mode. Before first
introduction the world gates visibility; after the last piece its last state holds.
Empty piece arrays keep an editable hidden object. A manual key outside fixed pieces
introduces a separate authored take; later keys grow that take without changing fixed
source slices or resurrecting cropped control points. Growing a fresh take backward
shifts its own source keys and preserves all its existing samples. Boundary-key deletion
clears growth eligibility. This preserves both nearby and distant existing motion.

Bounds:32pieces/object,241keys/source curve,2048total source keys/object, source
addresses0–100000, no overlapping pieces and no output beyond the project end
boundary. Existing512bones,64objects,128MiBGLB and1MiBproject metadata bounds remain.
Large source curves can hit metadata limits earlier. A frame at the end boundary
may remain a control sample but is not an extra rendered picture.

HAS ZIPv1/schema4-world packaging stays unchanged; the per-object format version
makes older app readers reject unsupported piece records before replacing a live
project. Current readers accept both versions. Packed/linked saves and recovery
retain curves, source ranges, native provenance and working poses.

`animation_clips.gd` handles pure document operations and source-time location.
`model.gd` validates/samples both versions; PoseEditor records into the owning piece.
`clip_editor.gd` coordinates the actual context menu/clipboard/stable-ID Undo.
Clipboard motion records its rational FPS and rejects mismatched destination rates;
it does not silently reinterpret time across projects.
The same preview evaluator drives PNG/MP4, with independent camera/cels/audio.

Checks: `animation_clips_unit.gd` verifies exact source-curve sampling, boundary and
gap semantics, independent edits and malformed/budget rejection. The actual GPU
smoke covers menus, piece/whole-object drags, clipboard/edit/Undo, ordinary packed/
linked HAS, recovery, native MMD/GMod/SFM rigs and H264/AAC output. See the progress
memo for current run counts/results; tests are not a claim of physical-input feel,
all-rig/native-fidelity, arbitrary-size or hostile-file certification.
