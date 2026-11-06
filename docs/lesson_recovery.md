# Recovering an active practice lesson

Ordinary recovery checkpoints now keep the active lesson together with the
practice scene. After an abrupt exit, normal startup restores its course,
session, step, completion observations, exercise baseline, temporary camera,
selection, drawing mode/layer, canvas alignment and collapsed instruction card.
The teacher continues observing the recovered scene. Previous uses the existing
whole-scene lesson checkpoints; Continue and Start fresh keep their existing
behavior. Recovery remains an unsaved copy until an explicit personal Save.

The optional `studio_lesson_recovery_1` object lives in
`editor.recovery.lesson`, not in normal saved HAS projects. It is limited to
16 KiB and validated against known versioned courses, integer step/completion
bounds, safe local session identifiers, finite view values and the existing
observation whitelist. It contains metadata, not more raster snapshots.
Project, journal and lesson-progress formats are unchanged. Ordinary Open does
not activate a teacher from embedded recovery metadata.

Only an existing valid local practice session can be reattached. If its separate
personal history is unavailable, or the lesson metadata is invalid, the recovered
scene remains editable and the status explains why the teacher was not restored.
Legacy snapshots without this field recover as before. A corrupt latest scene
falls back to an earlier valid scene and that generation's matching lesson
context. Startup reattachment does not rewrite lesson progress or manual HAS.

This uses the existing recovery timer, edit threshold and interaction guards.
It does not add a second periodic lesson autosave: changes after the latest
successful checkpoint may still be lost, and teacher-only navigation/observations
do not independently schedule a scene checkpoint. Previous depends on the local
lesson checkpoint folders remaining readable. Retention, concurrent lesson
writers, native Windows power-loss behavior and artist acceptance remain open.

Reproduce with pinned Godot and FFmpeg activated:

```sh
python tests/verify_lesson_recovery.py --isolated-display :103 --output /absolute/new/audit-folder
```

Linux requires an explicitly provisioned private display; the launcher refuses
shared-desktop fallback. Windows uses the existing private desktop launcher and
checks its receipts. Windows execution was not performed for this increment.

Fresh Linux software-rendering evidence: 43 domain checks, 6 writer checks and
63 checks across five normal-startup cases pass. The writer actually terminates
with SIGKILL; graceful shutdown hooks do not run. Cases cover newest generation,
corrupt-latest fallback, legacy metadata, invalid context and missing local
practice history. Real Previous/Continue/Fresh, idle hints, exact recovered
pixels, separate personal Save and a 48-frame H264 1080p24 movie pass. Manual HAS
and included source assets remain byte-identical. Original writer cache is not
used by the cold startup readers.

Proof: `/workspace/has-handoff-audit/lesson-recovery-cold-cache/verification.json`.
The before-fix run under `lesson-recovery-before` restores frame18 and its paint,
but fails the teacher-attachment assertion. An intermediate test accidentally
tried ordinary Open of the deliberately corrupted primary after fallback; the
test now opens the selected valid backup. Its failure log is retained.

Existing tutorial checks also pass: pose/draw and camera 52+5, physics 25+5,
and normal startup recovery 147 checks across 15 cases. Their real movies and
audio assertions remain intact. Python discovery runs 312 tests: 311 pass and
one existing optional independent MMD reader test skips. These scoped checks do
not establish full product or native/device/artist acceptance.
