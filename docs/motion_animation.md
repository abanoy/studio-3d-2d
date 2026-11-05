# Saved motion feeling: Model8 development increment

The development app now has **Pose → Motion feeling…**. Enable it, choose a gentle
or lively amount and Apply. The setting belongs to that model and has one Undo.
Simple shows the compact control; Advanced additionally lists up to256 generated
helper frames, their kind and native part name. Authored timeline diamonds are
black. Generated helpers remain derived data; they are not stored as authored keys.

In Simple mode, a model without a saved choice shows **Try motion feeling…**.
The first dialog has the suggested amount ready to apply. Closing it preserves
the original poses and history. Apply enables the trial with one undo step.
Reopening a model with a saved Off choice respects that choice.
The canonical owner-approved installation is the frozen Model7 update; this Model8
work remains a separate development/checkpoint increment pending broader regression.
No normal installation of Model8 is implied by the tests or by the Model7 approval.

The owner clarified that they will be the first actual artist using this app. The
goal is GMod familiarity with much simpler, quicker work than Stop Motion Helper,
and useful polish from a few main poses. This is a product acceptance target, not
a benchmark already proved. First-use review must test the whole import/pose/key/
preview/draw/export loop, whether defaults produce useful character motion, and
where interruptions or extra choices slow the owner down. Mechanical test counts
do not establish that usability or artistic quality. Keep this acceptance OPEN.

## Standard data and evaluation

`studio_model_8` retains independent body/expression tracks and continuous foot
contacts. It adds exactly one descriptor:

```json
"motion_assist": {
  "format": "studio_motion_assist_1",
  "enabled": true,
  "strength": 0.65
}
```

Earlier versions reject this descriptor, and older readers reject Model8. New
readers retain versions1–7 behavior. Model7 contact operations and Model6 body
operations preserve Model8 rather than downgrading it. Geometry, native parameters,
expressions, visibility and original assets continue to use the same standard model.

The shared Model sampler compiles immutable source-time plans once per data/frame-
rate revision. Derived body/root changes enter before standard contact solving.
Normal preview and final render use this same evaluator. Invalid settings, failed
compilation, coordinate limits and unreachable contacts remain explicit errors;
they are not hidden by silently removing assistance. Source-time mechanics and
provisional profile choices are documented in motion_assistance.md.

Authored body/root accessors remain separate. A draft begins from those underlying
curves. Unchanged peers still get their derived motion; an actually edited visible
target is not offset twice. Auto-key compares authored draft changes and creates
only the affected main controls. Committing one bone must never bake generated
root/peer motion. Fresh main keys invalidate/rebuild the derived plan. Dense captured
take intervals retain their original motion rather than gaining extra bouncing.

Changing settings defers while Physics/Hair or pending import startup is active,
and asks that an unrecorded draft be recorded first. It validates complete-range
reach and the existing world metadata budget before making one history change.
Save stores the descriptor and authoritative controls, never a flattened helper
take. Reopening regenerates assistance using saved project timing. Independent RGBA
paint and explicit camera keys stay separate.

## Evidence and unfinished work

`python tests/verify_motion_animation.py` checks the contract, validation, exact
authored samples/main keys/Off, source/peer preservation, draft/key isolation,
frame-rate rebuilding and dense captured-take behavior.

`python tests/verify_motion_animation_app.py` runs actual Simple/Advanced controls,
Apply/Undo/Redo, auto-key, Off and fixed-foot evaluation on Miku, GMod Reimu, SFM
Scout and VRM0/1. It saves a normal packed HAS, exports a normal H2641080p24/48-frame/
two-second MP4 and compares its own frame10 exactly. A separate app cold-opens the
HAS and checks portable data, all97 reverse sampled pose hashes, editable cyan paint
and the final image within the established mesh-edge bound. Private desktop
receipts are required. These use prepared native standard assets, not fresh native
decoder conversions or physical mouse/tablet input. The movie is silent.

This is focused evidence, not the full suite, clean-machine packaging or subjective
acting-quality acceptance. Actual Model8 live physics/recording interactions,
parented assisted models, all clip/clipboard/contact-editor lifecycles, linked HAS,
recovery/lessons and large-rig performance still need wider coverage. The existing
physics/contact regression for earlier versions remains required. Individual
generated-helper adjustments/pins, detailed curves, walking and the contextual
face editor are unfinished. Advanced inspection is currently read-only; global
amount is editable. The full MD/addendum objective remains active.


## Per-part amounts (development, 2026-11-03)

Advanced Motion feeling now lets an animated part use its own amount. Zero keeps
that part on its authored motion; other parts keep their own amounts. Uncheck the
separate amount to inherit the overall slider again. Simple keeps the overall
slider and preserves Advanced choices. Apply is one Undo; Cancel edits no data.
These are part-level strengths, not individual helper timing edits or pinned keys.
Main keys remain authoritative and helpers regenerate from their source curves.

Nonempty overrides use studio_motion_assist_2 with part_strengths keyed by exact
part identity (including @root). Existing version1 remains accepted unchanged;
clearing all overrides returns to version1. Old readers reject version2 rather
than ignoring it. Both Model8 and independent-root Model9 use the settings. Global
Off preserves overrides; the Model9 dialog's earlier Off early-return is corrected.
Up to513 finite amounts0..1 are supported; clip/metadata limits still apply.

Sixteen evaluator checks cover97 forward/reverse samples, independent peers/root,
unchanged authored controls, invalid settings and inheritance. The actual Yukari
study passes25 app checks across Model8/9, Simple/Advanced, Undo/Redo, Off, packed
New/Open exact pixels and normal MP4. The previous five-native motion-app workflow
and its cold reader also pass. The new app wrapper takes a prepared three-pose
Yukari HAS as its explicit argument. This does not establish per-part settings on
all native rigs or every clip/recording/recovery workflow; those remain further
acceptance work. No normal installed app replacement.

The wrapper now also launches a separate process with a fresh asset cache for
version2. Six cold-reader checks pass: exact settings, all97 reverse sampled
pose/root hashes, native asset SHA, Advanced head override controls, exact rendered
frame and independently editable cyan ink. This verifies regeneration from the
packed project without relying on the writer's in-memory state. It does not prove
linked projects, missing external assets, crash recovery or subjective motion
quality. The writer retains25 passing checks and the normal two-second MP4 check.

## Individual helper editing foundation (development only)

The source evaluator now accepts optional helper_edits, mapping a helper identity
to phase (strictly between0 and1 in its driving span) and amount (0..1). Adjustments
can move or reduce an individual anticipation, overshoot, recoil or interior
settling control. Final settling endpoints stay fixed. The complete final ordering
must remain strictly increasing; stale identities, nonfinite values, crossed
controls and unsupported fields refuse atomically, retaining the previous plan.
Main poses stay exact. Existing position/rotation limits and Off still apply.

Derived identities now include both driving source frames and the control role,
rather than the segment's list index. Inserting an earlier pose cannot silently
redirect a later adjustment. Moving a driving frame changes the identity: this
low-level evaluator refuses stale edits. Future document operations must explicitly
remap or ask for review; they must not attach by nearest frame or list position.
No helper identities were serialized by versions1/2, so their files retain their
current interpretation. Untouched source-time spans keep their sampled values.

Sixteen new evaluator checks and95 existing motion checks pass on Windows Godot.
This is not yet a user-facing helper editor or a saved project feature. Routing
edits through piece/gap/root adapters, versioned persistence, main-key edits,
clip ownership, Undo/Redo and Advanced controls remain the next integration work.
Absolute pose pins and strengthening beyond generated amplitudes are not included.

## Tuning a generated movement in Advanced mode

Open Motion feeling, select a generated anticipation, overshoot, recoil or interior
settling row, then adjust Timing and Amount. Timing is relative to its driving
movement. Amount ranges from the authored interpolation to the full generated
offset. Reset this helper to automatic removes the adjustment. Apply groups the
changes into one undo step. Simple mode preserves these choices.

Studio stores tuned controls in studio_motion_assist_3 with their part, clip or
gap, driving frames and role. Independent model position and rotation have
separate addresses. Clearing all edits restores the earlier descriptor suitable
for the remaining settings. The final settle endpoint stays fixed. Moving or
deleting driving frames can invalidate an address. Automatic remapping and a
review interface for stale edits across clip operations remain unfinished.

The Yukari study exercised an arm overshoot at phase .75 and amount .30, verified
Undo/Redo, packed Open, fresh-process regenerated motion and a normal two-second
1080p24 MP4. The Advanced list currently displays at most 256 helpers.
