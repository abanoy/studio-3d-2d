# Model7 continuous foot contacts

This source includes persistent contact ranges, direct foot/knee correction,
clip editing, physics transitions and native HAS/MP4 integration. The complete
worktree verifier passed93processes across bounded batches on frozen sources.
Installed-copy verification is a separate gate: see the latest progress memo and
`output/normal-source-state.json` in the owner's application folder for its actual
status. A candidate copy is not a verified release. Earlier sections below retain
the development history; they are not the current installation-status record.

Model7 extends Model6's independent body/expression/visibility data with optional
per-piece `foot_contacts` using `studio_foot_contacts_1`. Only explicit promotion
creates7; ordinary new body edits still create6. Old1–6 reads retain their evaluator.
Contact fields on earlier models refuse instead of being silently ignored. Native
geometry, bone IDs, reports, world4 and HAS ZIPv1 are unchanged. Older Studio builds
reject7, so this is not an older-binary-compatible writer.

Normal Model.sample now evaluates declared contacts from each frame's ordinary
body controls. It saves/restores exact skeleton position/quaternion/scale values
and the root. For parented objects it temporarily evaluates ancestors' LOCAL
transforms at the requested time, restores every ancestor, and does not change the
world's displayed frame. Dividing by a differently displayed parent's global matrix
introduced seek-order-dependent rounding; evaluating exact local transforms removes
that dependency. The world registry is held weakly, avoiding an ownership cycle.

Model.apply uses the same solved native FK result. Live pose overrides bypass the
contact solve there. Source splits retain source-time descriptors. Body edits and
expression edits preserve7. The development clipboard and physics transitions below
have focused verification; the complete activation gates still apply.

Unreachable contacts set an evaluation error. Actual final capture returns a clear
frame/object error and the exporter aborts before encoding an unconstrained movie.
Hidden/excluded instances do not block a final picture. Preview feedback, range
Release and manual foot/knee corrections provide ways to repair unreachable pins.

The focused `tests/verify_contact_animation.py` exercises ordinary world preparation,
root-key playback, fractional/reverse read-only evaluation, exact root/bone/ancestor
restoration, an animated translated/scaled parent, original/MMD/GMod/SFM/VRM0/1 rigs,
packed HAS reopen, identical half-frame poses after reopen, positive visible colored
skin, actual H2641080p24/48frame/2second MP4, byte-exact reopened/export PNG, and real
unreachable-contact export refusal. It is a development integration test, not full
contact-authoring acceptance or dense-scene performance proof.

Full-precision JSON parsing changes two original target Y double values by about
1.39e-17 in this fixture. Engine Vector3/quaternion targets and all49 resolved
half-frame poses after actual HAS reopen remain exact. Managed source/path relocation
is checked separately. Stored source controls are retained, not replaced by sampled
ordinary keys. No motion or endpoint tolerance was enlarged.

The worktree now also has Simple **Planted feet…**: choose the last inclusive
frame, Plant or Release from the current playhead, and Undo/Redo. Opening it does
not edit the document. Native leg capture and complete-range reach checks precede
installation. Root numeric/gizmo edits keep contacts, preserve independent authored
body keys and refuse unreachable moves. A drag retains its last valid preview;
Escape restores the original data. Animated drafts must be recorded first.
Queued or unfinished physics setup also defers opening the controls without
cancelling the simulation ticket. Unreachable loaded contacts show inspector
feedback and can be released over a chosen interval without removing earlier pins.

Range editing splits existing source slices and inserts contact-only gaps/tails
without body or expression controls. Explicit boundary pieces release a pin after
the last body block. Identical pin ID/targets can bridge a gap despite different
piece source addresses. Release changes only its interval. These operations keep
the original body interpolation rather than baking solved poses. The existing
32-piece/64-segment/1MiB limits can refuse an edit before installation; project
metadata estimation uses the existing recording policy's conservative overhead.

Planted legs ask the user to use the dedicated correction controls below, or
release before direct bone manipulation. This avoids silently recording ineffective
leg keys. Independent hand/body controls remain available. Viewport pin/pole gizmos
and broader contact authoring remain unfinished.

`tests/verify_contact_editor.py` routes actual Simple controls, interval/no-op/stale
checks, source gaps/tails, root numeric/gizmo correction/Undo, draft/live guards,
ordinary packed HAS/paint and exact preview/movie pixels. The current handoff
records actual results. All of this remains a separate WIP, not normal installation.

## Block editing and placement — development continuation

Actual timeline Copy/Cut/Paste, block movement and whole-object retiming now retain
source-time contact ownership. A copy gets fresh logical pin identities. Targets
map from the copied root at block entry to the prospective pasted root at entry,
including authored parent transforms. Existing absolute root curves keep their
ordinary behavior; contact-only blocks use the receiver's root. The first successful
same-instance Cut relocation keeps logical identity only when its placement anchor
is unchanged and the original block is still absent. Later reuse creates a copy.
Clipboard context holds a weak source reference and survives New without retaining
the old scene. Missing context, foreign bones, unsupported scale, unreachable pins
or project metadata overflow refuse before publishing history. All project frames
are checked after contact retiming; a changed relationship to an animated parent
can make a proposed edit fail. Cut reuse and Undo have the acceptance below.

`verify_contact_clipboard.py` covers these ordinary menu actions, real transformed
parents, cross-project placement, exact Undo/Redo, JSON-decoded logical identity,
presence/visibility isolation, packed HAS and exact reopened/exported movie pixels.

## Live physics and recording — development continuation

Body Physics temporarily owns the live pose. OFF releases the foot lock at the
current integer draft frame, freezes that actual pose, and records both changes in
one Undo. Surrounding contact ranges remain authored. If the release needs too many
pieces, OFF refuses before disposing the live solver; its toggle stays on with
guidance. No simulation keys are created. Existing animated-draft behavior remains:
scrubbing resumes authored animation, rather than inventing a full freeze track.
Before stopping a Model7 solver, the complete frozen pose and release are validated
and counted with the full world's metadata, camera, audio and layers. A release
descriptor alone may fit while its FK pose exceeds the limit. That refusal now
retains the live solver and exact authored/history state; the existing conservative
1MiB estimate and overhead remain. This is not a physical disk-full guarantee.

Secondary-only OFF retains body contacts. Secondary-only Record carries their
exact targets into the new source-time take, including release gaps and recurring
contacts. Body or combined body/hair Record replaces contacts only inside its
sampled interval. Local retains unrecorded peers; World owns all captured bodies.
Outside fragments keep their contact data. Newly captured body parts receive their
original baseline at a retained following block's entry; otherwise a fallen hips
channel could hold through a contact-only tail and make its feet unreachable.
Existing channels keep their original curves. This correction also applies to
Model6 recording; the existing body and recording suites are affected checks.

`verify_contact_physics.py` uses actual gravity, Local/World recording, an over-limit
release, native VRM springs with measurable fan-driven hair, secondary-only and
combined transitions, atomic Undo/Redo, all outside-frame reach checks, packed HAS,
independent cyan paint and exact reopened/exported MP4 pixels. The raw native VRM
case is explicitly optional when the owner's private file is unavailable.

## Correcting a planted foot — development continuation

The same Planted feet window now offers Left/Right foot and six view-relative
nudges in Simple, plus Reverse knee bend. Each button applies over the displayed
current-frame-through-last-frame range, with one Undo. Advanced exposes nudge
distance, exact world position, Euler rotation and an optional fixed world knee
target. Apply and Close stay pinned while precise fields scroll. Opening/changing
fields does not author a correction. Unchanged displayed values retain the original
full-precision data; merely pressing Apply does not round imported targets.

Only active contacts in the chosen interval change. The other foot's changing
targets, explicit release gaps, outside contacts, native bones and original body/
expression curves remain. Every altered active run gets an independent logical pin
ID. Entire-range reach and full-world metadata validate before one history command.
Stale frame/model/root, unrecorded animated drafts, export and live/pending physics
refuse rather than modify an outdated scene. A knee target on the leg's line refuses
with direction guidance. Manual knee reversal is explicit; it is not anatomical
inference or a promise against clothing/skin distortion.

Knee fields use nested `studio_foot_contacts_2`; old descriptors remain version1.
Only a track with `pole` or `flip_bend` needs2. Older experimental readers reject2
instead of silently ignoring the desired knee direction. Version1 cannot carry
these fields in the updated validator. Model7/world4/HAS ZIPv1 and old1–6 model
reading remain unchanged. Updated development builds are required for these WIP
files; the normal canonical app still does not accept Model7.

The shared limb solver accepts an optional world pole while retaining its original
default. Fixed poles and bend choices participate in contact identity, release/gap
evaluation, clipboard placement and secondary-only recording. Clipboard placement
transforms world pole points along with foot targets. Whole project timing moves
their ownership rather than changing their world locations.

`verify_contact_correction.py` routes actual Simple/Advanced controls, no-op and
Undo/Redo, untouched other-foot/body/camera data, release gaps, range/stale/live
refusals, strict validation/versioning, world-pole clipboard mapping and packed
HAS/movie. Miku, GMod Reimu, SFM Scout and VRM0/1 retain native IDs/provenance and
stable forward/reverse solved poses. `verify_contact_physics.py` also records an
actual VRM's secondary motion while retaining a version2 world knee target.
Viewport pin/pole dragging and wider native/parented/dense authoring still require
work and acceptance. These are fixed contact targets, not walking/path generation.

## Moving groups with planted descendants — development continuation

Valid parent and nested-parent moves retain the child's fixed world foot targets.
The normal world preview explicitly passes the selected ancestor's draft context
to contact evaluation. Ordinary read-only samples and final export retain authored
ancestor transforms, independent of an unfinished displayed drag. No implicit
child keys or target reanchoring are introduced by moving a group.

Numeric edits and gizmo drags check affected Model7 descendants as well as the
edited model. An unreachable move names the child, keeps the exact previous data
or last valid drag preview, and creates no history. Escape restores the complete
ancestor baseline. Auto-key also checks all project frames, since adding a root
control can change easing against a child's inverse motion at other timestamps.
Whole-group retiming and parent block edits use the same descendant reach policy
before committing. Temporary validation restores data, transforms, skeleton values
and prior preview error state. Unrelated instances do not enter the affected set.
Live/pending physics defers planted-parent edits rather than silently freezing it.

`verify_contact_parent.py` exercises child-before-parent nested groups, real numeric
and gizmo Move controls, exact Undo/Redo, draft/authored isolation, last-valid
rollback, future easing and parent timing refusals, child/peer/camera isolation,
packed HAS, independent cyan paint and exact reopened/exported MP4 pixels.
Nested rotation and positive uniform scale have the further native acceptance
below. Reparenting currently has no editor operation; dense groups and every
native hierarchy are not certified by these focused tests.

Still required before promotion to the normal application:

1. Wider pin/pole and inherited-group acceptance; ranges/root correction, dedicated
   correction controls and nested-group Move feedback now have WIP implementation.
2. Wider native/parented editing acceptance; same/different-instance/project
   reanchoring and repeated Cut/Paste/Undo now have focused WIP coverage.
3. Wider Body/Hair/Local/World Record lifecycle and parented/native combinations;
   focused interval ownership and full frozen-pose metadata checks have WIP coverage.
4. Wider lesson-teacher crash/resume and persistence acceptance; the fresh-process
   native-world checks below now cover linked/packed HAS, normal recovery and the
   lesson snapshot store API.
5. Wider preview reach/lifecycle acceptance and the appropriate full compatibility
   checks. Compiled binding performance and current-pose/hidden selection now have
   the focused native acceptance below.

Keep all six original gates in foot_contacts.md and the full HAS goal. This WIP
does not complete walking/path help, overshoot, full-body anatomy or native cloth.

## Fresh-process native persistence and compiled bindings — development continuation

`verify_contact_persistence.py` writes one seven-object world: Miku, GMod Reimu,
SFM Scout, VRM0/1, a map/floor and a transformed animated group. It includes root
motion, version2 knee controls, a release interval, independent visibility,
camera keys, editable cyan paint and a real offset WAV. Four new normal app
processes open linked HAS, packed HAS, automatic startup recovery and a lesson
snapshot. They retain all485 reference half-frame poses exactly, portable native
metadata, timeline, audio and RGBA data. Startup recovery uses the production
startup dispatch, with only its storage location isolated. Lesson acceptance is
the snapshot store API and editor context, not the entire teacher's crash resume.

Only the test's own copied GLB input folder moves aside after the linked check;
packed/recovery/lesson reads then use managed assets. Original owner files stay
in place and their hashes remain unchanged. Writer and packed-reader movies are
actual H2641920x1080/24fps/48frames/2seconds with AAC onset1.0000417s. Each own
preview/export frame matches exactly. Separate scene rebuilds differ by three
RGB bytes at one mesh-edge pixel, mean0.000020978/255, within the existing bound;
cross-process frame identity is not claimed. That persistence suite's hidden
selection and Frame model assertions cover data/error isolation; the dedicated
native green-geometry checks below are separate.

Model's transient contact plan now avoids repeated native alias scans. Cache reuse
checks root identity, exact inventory order/humanoid metadata and the six live
parent/index/name bindings. New inventory invalidates it; unsupported resolution
is not cached permanently. Requested contact IDs and track validation still run.
The cache never saves a new field or changes solver math, targets or source assets.

`verify_contact_bindings.py` compares all485 poses to pre-optimization results,
checks order/metadata/hierarchy invalidation and restoration, and exercises five
native models with32blocks each over240frames. All1205 samples are reachable;
the333211-byte metadata world saves and reopens through ordinary packed HAS with
exact selected poses. In the final measured run200 cached lookups took3.09–3.97ms
versus121.14–424.35ms uncached. A model's49 full pose samples took56.71–84.19ms.
Dense241 samples took287.95–440.43ms per model. These are bounded local measurements, not
whole-app frame rate, large-scene capacity or every-rig performance guarantees.

The affected physics regression exposed a separate recording-boundary bug: a newly
captured hip with no earlier controls could hold its first fallen value backwards
through earlier contact/hair blocks. Record now adds the original baseline to the
nearest preceding block, as well as the existing following reset. If there is no
preceding block after introduction, a body-only one-frame baseline is added; normal
piece/metadata limits can refuse it. Existing channels/source curves remain intact.
The take owns its recorded integer interval; this does not change ordinary gap
interpolation. Deterministic unit checks and actual native combined capture/HAS/
movie verify the repair. This shared recording correction also applies to Model6.

## Reusable Cut clipboard and Undo — development continuation

Only the first successful paste can transfer the original contact identity. It
must return to the same live instance, keep the exact placement anchor and find
the original block still absent. Undoing Cut restores that block, so a subsequent
paste becomes an independent copy even if no earlier paste succeeded. A successful
foreign-instance paste consumes the transfer too; later return to the sender is
a copy. Each copied pin gets a fresh ID, releasing gaps between independent copies
instead of accidentally holding a planted foot throughout them.

Overlap, reach, full-world metadata and32-piece refusals keep the pending Cut,
clipboard and Undo untouched. The source motion remains reusable after success;
only its one-time identity-transfer flag changes. Clipboard is personal runtime
state, outside project Undo. Undo/Redo restores exact authored blocks and fresh IDs
without rewinding the clipboard. No model/contact/HAS version changes are needed.

`verify_contact_identity.py` exercises prepared Miku126bones, GModReimu77,
SFMScout83 and both VRMs91bones each through the ordinary controller. Each covers
first relocation, repeated/third Paste, failure/retry, Undo/Redo, Undo before first
Paste and foreign-instance/sender reuse, with194 fractional reach samples. Miku
also tests actual metadata and piece-capacity refusal. All76 writer checks pass;
a new process adds4 checks, retaining all194 poses of the final VRM0 instance pair
exactly. That cold frame is pixel-identical, including independent cyan paint.
Packed HAS preserves portable native data and IDs; actual H2641080p24/48frame/2s
export matches its own preview frame exactly. This movie is silent; earlier audio
acceptance is separate. There is no fresh raw-format conversion or all-rig claim.

The initial test reproduced seven identity failures per rig. A separate portable
world assertion compared JSON strings, including int/float text representation;
parsed numeric/identity data had no differences. It now compares normalized JSON
values, with an independent Python equality check and exact resolved-pose hashes.
No reach, numeric or pixel tolerance was relaxed. Existing clipboard menu27,
correction36 and ordinary animation-block32unit/50app regressions also pass.

## Hidden planted geometry, inherited fades and normal-app fix

Selection previously captured a temporary faded material if its mask was built
during a visibility fade. A fully opaque surface could then be alpha-discarded
from both the visible outline and later hidden ghost. The source material is now
queried from the owning ModelOpacity's pre-fade/pre-lighting overrides, including
global material overrides and Mesh-inherited surface materials. Native texture
alpha/cutouts remain authoritative. This reads authored materials without editing
them or changing scene fades, original GLBs or final rendering.

`verify_contact_selection.py` rebuilds during alpha1/7.2 and tests prepared Miku,
GMod Reimu, SFM Scout and both VRMs under an animated transformed parent. It uses
independent engine morph/skin bakes rendered as static geometry on a separate test
layer. Thirty model snapshots and ten inherited-parent/group snapshots compare
their silhouettes, with actual green editor pixels and current-pose framing.
The final Model7 run passes67 checks. Raster differences are0–6pixels, confined
to the one-pixel contour; every independent posed vertex fits the framed camera.
Bound error is at most about5.13e-6 units. Reverse seeking restores an exact mask;
framing/selection retain data, dirty/history state and explicit camera keys. Actual
final frames exclude hidden ghosts exactly. The reference render settles after
pose updates so its engine bake does not read a prior render submission.

The same bug was reproduced in the normal app with a temporary Model6-only copy
of the fixture (all contact tracks removed):67 checks,50 failures. Only
`src/model_opacity.gd` and `src/world_selection.gd` were backed up and updated there.
Normal compatibility then passes67/0, with0–5 contour pixels and bound error at
most4.47e-6. Its five existing suites also pass: selection41, visibility53, current
skin/morph/live framing34, lighting32 and live appearance32. These five checks
also pass in the development worktree. Twelve final private GPU receipts cover
both variants. A separate headless normal validator still accepts6 and rejects7.
This is a compatible normal-app outline fix, not normal activation of foot contacts.
The source overlay manifest records the base plus exact two file hashes; earlier
327 normal source files otherwise remain intact, apart from append-only progress.

Initial experiments retained a test-only invalid layer21 request and an inferred
type error; the final reference uses supported layer18, excluded from the main
camera. A collector also rejected a successful indented JSON report; it adopted
only that verified terminal pose-bounds result and continued the remaining jobs.
No process was restarted because of silence. Failed diagnostics remain separate.
This covers the five representative rigs and inherited fades, not every native
shader, full cloth, large rig or alternate GPU. Viewport foot/pole dragging and
wider rotation/scale/reparent/live authoring still precede normal Model7 promotion.

## Native nested rotation/scale and live-edit protection — development continuation

The existing numeric rotation, world-axis rotation ring and Advanced model scale
now have focused acceptance with Miku, GMod Reimu, SFM Scout and VRM0/1, each under
two rotated/scaled ancestors with an unrelated peer. Fixed world knee targets and
foot orientations remain authored. Safe parent edits key only that parent;
unreachable edits refuse with the affected native model's name. Actual ring drags
keep the last reachable preview, return to valid feedback when moved back, commit
one key/Undo on release, or restore the exact baseline on Escape. Read-only samples
continue using authored ancestors while a different drag preview is displayed.

Apply model scale previously bypassed the live guard and entered begin_draft,
which could consume pending import physics, freeze a body/release contacts or end
a Local recording before the scale was even validated. It now uses the same live
guard as other contact-affecting edits, before any draft/history mutation. Model
scale remains a root operation when a planted foot is selected; it does not borrow
the separate direct-leg-edit refusal. Export also defers scale. Legacy unplanted
model behavior and the underlying shared FK/contact solver are unchanged.

`verify_contact_transform.py` exercises the existing controls and actual native
body/Local-recording lifecycles, with a pending startup ticket preserved exactly.
Each native case checks the complete49frame range, child controls/poles/peers/key
isolation, Undo/Redo, numeric2degree yaw, scale1.2to1.21, unreachable90degree yaw/
.001scale and a1degree ring drag. The last native's nested world reopens through
real packed HAS with an exact pose, and its independent cyan paint matches own
preview/actual H2641080p24/48frame/2s MP4 frame12 exactly. Prepared source bytes
remain unchanged. No new raw-format conversion or broad anatomy/cloth claim.
Final129 checks pass (25 per native plus4 shared). Affected parent20, correction36,
physics48, body24unit/72app, world-edit37 and UI23 also pass:389 checks in total,
seven clean private GPU receipts and the body unit process. No full suite rerun.

Initial tests correctly reproduced three live-scale failures per rig. Three extra
Scout expectations were invalid: the fixture had recreated its GLB with identity
root rather than retaining its saved90degree root orientation. A private numeric
diagnostic measured2degree yaw requesting about.957units against.923units of leg
length; the refusal was correct. The setup now preserves every model's supplied
body baseline rotation/scale, without any source-family branch or converter change.
The same requested edits then pass; reach/orientation tolerances are unchanged.

This acceptance does not add grouping/reparent UI or define how arbitrary animated
world paths should survive a parent change. Parent IDs still load/validate through
the existing world format, and in-place instance edits still reject a parent-ID
change. User-facing reparenting, dense/mixed/native hierarchies, secondary/combined
scale lifecycle and viewport foot/pole controls remain further work. Keep all six
activation gates and the full MD scope; the normal app still only has the earlier
compatible two-file outline repair, not this Model7 development update.

## Direct viewport target gestures — development continuation

Planted feet now offers **Drag foot in view** in Simple and **Drag knee target in
view** in Advanced. Choose the foot and inclusive range first. World RGB axes
constrain movement; the center moves in the camera plane. The sidebar names the
foot and range; Done exits. Escape cancels a drag; a second Escape exits. Ctrl-left
retains camera navigation. Preview uses transient solved FK, leaving authored
model data and read-only samples unchanged. Release checks the full range and
project budget before one Undo correction. No ordinary FK keys are baked.

An unreachable movement retains the last valid preview. Returning within one
quarter of a displayed pixel restores the exact original target and makes no
edit. This avoids tiny accidental corrections caused by screen/canvas conversion.
Preview motion validates the current frame; full-range validation happens on
release. Existing release gaps, other-foot settings and body/expression curves
retain their correction semantics. Mode/context/physics changes invalidate the
gesture. These controls remain development WIP, not normal Model7 promotion.

The focused actual-editor test passes142 checks across Miku, GMod Reimu, SFM Scout
and VRM0/1 under nested transformed groups. It tests plane and world-axis gestures,
last-valid behavior, Escape/no-op, one Undo/Redo, exact body samples, right-foot
selection, knee poles, Ctrl-left priority and visible range/Done layout. It does not certify all three axes
from every view, every lifecycle, physical mouse feel or the complete contact gates.

Lifecycle expansion verifies Draw/Home dismiss idle controls, pending physics
discards only the transient target preview while retaining its startup ticket,
and seeking finishes one correction at the original frame with exact Undo. A
current-frame reachable target that becomes unreachable later in the range refuses
the entire release, clearing transient FK without changing data/history. The first
132-check run reproduced stale controls in Draw on all five rigs. Target context
validation now runs before the ordinary Pose-only gizmo guard; final142 passes.

The expanded viewport writer now passes145 checks, including normal packed Save
while a real target drag is still active. Save commits exactly one correction
before snapshotting and clears the transient preview. The last native scene also
exports H2641080p24/48frames/2s with independent editable cyan paint and exact own
preview/export frame12. A separate clean app process passes5 additional checks:
exact portable scene, all97 solved half-frame pose hashes in reverse order,
original editable paint, no live target UI/state, and final image agreement. This
run measured zero changed image channels across processes; the existing bounded
mesh-edge rebuild criterion remains, not a universal pixel-identity promise.
No production code changed in this persistence-test increment. Full-suite wiring,
broader dense/mixed lifecycle and guarded normal promotion remain outstanding.

## Stale preview ownership, capacity and full-suite integration

An unrelated drawing-layer edit can invalidate a target gesture without otherwise
evaluating3D. The target hook was removed correctly, but the displayed skeleton
could retain the old preview until the next scene evaluation. A real diagnostic
measured a remaining .00883525world-unit foot offset. Stale cleanup now reapplies
the current scene after removing only its own preview. A replacement preview from
another owner remains installed and visible; authored data is not overwritten.

Final focused coverage is174writer +5fresh-reader checks, all passing. Five native
cases now include that visible restoration and replacement ownership. A separate
near-limit fixture proves both that the existing world fits and that the proposed
correction actually exceeds the1MiB estimate, then exercises atomic refusal.
An initial fixture changed an already split target and did not overflow; it was
correctly accepted. The corrected fixture begins with unsplit contact ranges and
positively measures the proposed overflow. The metadata policy was not changed.
Save/cold reopen/H264 movie assertions remain. Cold comparison measured3RGBchannels
at one edge pixel, mean.00006221065/255, within the existing bound; exact portable
data,97pose hashes and own preview/export frame stay required.

`tests/verify.py` now invokes all twelve contact integration wrappers, in dependency
order: evaluator, controls, clipboard, physics, parent, correction, fresh native
persistence, bindings, identities, selection, transforms and viewport. The local
integration run requires the documented owner sample assets. These tests are
additional to the previous complete editor/audio/drawing/physics/recovery/course
and media checks, not a replacement for them. Broad acceptance is still pending.
The first bounded session completed23processes before the stale-display fix and
is retained as pre-fix evidence only. The freshv2 session uses corrected sources;
no pre-fix results are adopted into it. Keep source inputs unchanged while that
session runs. A batch exit75 is a boundary between finished tests, not completion.

## New near-straight knee capture hints (development, 2026-11-03)

New foot plants estimate a forward knee direction from the two hips and ankles
when the current knee is within2% of leg length of the straight hip/ankle line.
This avoids treating tiny sideways rest offsets as the direction of a deep crouch.
A clear current bend is retained. Degenerate or ambiguous landmarks produce no
hint. Estimation follows world rotation and positive uniform scale.

Hints are ordinary editable world-space poles in the existing contact version2;
Advanced corrections and bend reversal remain available. Old saved contacts are
not migrated or reinterpreted. This is a conservative capture-time heuristic,
not anatomical constraints, collision prevention or automatic walking.

Sixteen mathematical checks,33 ordinary Plant/Release checks and36 correction
checks pass. Five native rigs keep knees on their own sides in the crouch fixture,
with pinned feet, Undo and saved poses. Native path review remains120/121 passing:
Miku has a one-pixel reopen difference despite identical displayed bones/camera.
This image discrepancy is not waived. Final source is development-only.
