# Record physics in Simple

Enable **Physics** on the models/props you want to simulate. The grid is only a
guide; use a real map or Advanced > Sample room for a floor. Choose a start frame,
then use the compact controls below the viewport toolbar:

- **Local record** captures the model selected when Record starts. Selecting or
  grabbing another body afterward does not change that scope.
- **World record** captures every model/prop currently simulating, including live
  boxes struck by a ragdoll. Enable Physics on those boxes first. Static objects,
  camera keys, drawings and audio remain independent.
- **Record** starts at the next fixed physics tick. **Stop recording** keeps the
  take. Reaching the project end stops automatically. Undo restores the entire take
  together; Redo restores it with physics off.
- Escape discards the unfinished take and returns to authored animation. If you
  are holding a body, the first Escape releases it; Escape again discards the take.
  Undo during capture also discards only that unfinished take.

Capture ends before a manual seek, Save, playback/export or switching to Draw.
Scene/Pose viewing and selecting another model keep the current scope and capture.
Starting Record from Draw enters the 3D workspace automatically.
Losing focus releases the grab while recording continues to Stop/project end.
New/Open discard pending
capture when replacing the world, following the existing dirty-project workflow.
Captured motion is installed as ordinary editable animation pieces; split, drag,
copy/paste and manual pose edits continue to work. The recorded range replaces
motion inside that range. Existing authored curves outside it retain source-time
ownership. Inferred gaps use the same ordinary bridge/hold rules as other pieces.
Visibility keys and reference-only flags are preserved independently.

Local does not save the other live objects' final positions: those objects return
to their authored state when capture ends. World saves all the active simulation
targets selected at the start. Enabling additional physics objects during capture
is blocked; stop first. If authored target data changes unexpectedly, the take is
rejected rather than overwriting those edits.

Playback, scrubbing and MP4 use saved frame samples, not a new physics run. The
master integer frame/rational FPS clock samples the120Hz simulation; fractional
tick boundaries interpolate neighboring pose/root states. Only simulated bones
plus the initial authored pose are retained, without repeating unchanged helpers.
Live capture audio is silent; ordinary recorded playback/export uses the existing
synchronized WAV/AAC track. Real mouse/tablet comfort and all native rigs remain
subject to owner feedback.

Current limits remain240project frames,241keys per curve,2048keys/32pieces per
model and1MiB project metadata. New saves use compact JSON in the existing schema;
old indented projects remain readable. Capture maintains an incremental byte budget
and validates the complete result before commit. If the limit is reached, the
longest valid sampled prefix is kept with a visible message; later motion is not
saved. Long or crowded recordings need further compact-track work. No hidden
budget increase, native export-back format or separate ecosystem pose engine.

Approximate collision/joint settings and manual activation remain as described in
[physics controls](physics.md). Automatic-on imports, native physics fidelity,
moving-map collision and simultaneous nested live bodies are still open. This
increment is recorded interactive physics, not an imported native motion player.

Verification covers Local versus World with real ragdoll-box contacts, atomic Undo,
repeated scrubbing, packed HAS and exact reopened-preview/MP4 pixels, independent
RGBA/WAV/camera data, non-divisor rational FPS, interruption/cancellation/stale-state
and real metadata-limit saves. Optional owner MMD/GMod/SFM/VRM assets stay private.
Fixed-tick and rendering evidence do not certify physical hardware input or sound.

Primary API references: Godot4.6
[RigidBody3D damping](https://docs.godotengine.org/en/4.6/classes/class_rigidbody3d.html),
[JSON serialization](https://docs.godotengine.org/en/4.6/classes/class_json.html),
[PhysicalBone3D](https://docs.godotengine.org/en/4.6/classes/class_physicalbone3d.html).
No engine implementation code was copied.


Secondary motion now uses this same normal Record path. Hair & clothes alone
captures the posed body's authored motion plus simulated chains; with Physics
it captures the combined ragdoll/secondary result. World can include a dynamic
fan prop as well. Secondary-only authored anchors and fan transforms are sampled
between integer keys at the physics rate, avoiding a per-video-frame staircase.
Setting changes on a fan already captured by Record are locked until Stop.
Secondary cancellation, seek-prefix commit, Save-prefix/reopen, full two-second
Local/World takes and native VRM0/1 provenance are covered in verify_fan_motion.py.
Existing audio/metadata/dense-take limits apply. See secondary_motion.md.

Development Model7 contact transitions remain separately checkpointed rather than
installed over the normal canonical app. Body/combined takes remove foot contacts
only within their captured interval; secondary-only takes retain exact pins and
release gaps. Outside contact fragments remain editable. Newly captured body parts
return to their prior baseline at a retained following block's entry, preserving a
later contact-only block instead of holding a fallen hips channel through it.
The original channels keep their curves. This shared independent-body recording
correction also applies to Model6. See contact_animation.md and the current progress
memo for actual tests and outstanding activation gates; no new completed-feature
or canonical-install claim follows from this development note.

## Independent movement tracks (development acceptance, 2026-11-03)

The existing contact recording workflow now also tests Model9. Actual Local and
World body capture keeps the format and exact position/rotation/scale samples
outside the take; Local leaves the other model untouched. Physics OFF, one-frame
contact release, atomic Undo/Redo and overflow refusals remain covered.

The retained native VRM also exercises fan-driven hair-only and combined body/hair
recording, editable knee targets, fractional foot stability, packed HAS reopening,
independent paint and the actual MP4 frame. Component mode requires this fixture;
it cannot silently pass with the native case skipped. Fifty component and48
older-model checks pass, each with a private-desktop receipt and verified1080p24
48-frame movie. Both variants also passed in the full verifier run completed on 2026-11-03. This does not certify all native rigs, long takes or cloth fidelity.

During Local capture the scope control names the recorded model, even when a
different prop is selected or grabbed. During World capture it shows the number
of targets. Its tooltip lists the names and the frame where recording started.

Before capture, Record checks the selected scope. Hover to see the Local actor
or the World object count and starting frame. If Local has no selected simulated
object, or the playhead is at the movie end, the disabled control explains why.
Changing scope refreshes readiness immediately.

Fresh2026-11-06 cloud verification:17recording-domain and48procedural application
checks pass on private Linux software rendering. Local locks its target while
peers are selected/grabbed; World captures actual ragdoll/prop contacts atomically.
Three measured contacts and1.96437units horizontal displacement occurred in this
run. Saved playback/scrubbing and exact preview/export pixels pass, as do partial
Stop, Escape, focus interruption, stale authoring, budget-limited prefix, Save
during capture and teardown. Fractional-rate constant-velocity error was below
0.000001units; this is a scoped deterministic-tick fixture, not universal physics
accuracy. The48frame1080p24 H264/AAC movie decodes its cue at sample48002 versus
expected48000. Three native preparations and two VRMs explicitly skip. Sources
remain unchanged. Proof /workspace/has-handoff-audit/recording-current/verification.json.
This existing Model6 scenario is distinct from historical native/Model9 evidence
and does not establish broader joint/cloth fidelity or subjective ragdoll quality.
