# Derived character motion: development experiment

The source-time utility below now also supports the separate Model8 editor/storage/
render integration described in [motion_animation.md](motion_animation.md). Its
original transient Preview API remains an experiment and still bypasses ordinary
final rendering. Model8 uses the shared Model evaluator instead, with focused
packed HAS/cold Open/MP4 evidence; broad activation gates remain open.

The owner wants a few authoritative black main keys to produce a useful first
performance. Anticipation, overshoot, recoil and settling should be generated
separately, recalculated after main-key edits, hidden in Simple and inspectable in
Advanced. Speed should influence the result. These are confirmed directions;
default intensity and the detailed editing rules still need practical review.

## Implemented here

`MotionAssist` compiles an immutable preview plan from a part's transform controls.
Seconds, translation distance and shortest quaternion rotation determine bounded
extra movement. It returns exact original main-key values, suppresses Hold/static
and very short transitions, and adds a short settling tail after the last moving
span. Generated helper records are separate copies with driver addresses; they
are not inserted into the authored controls. Retiming/rebuilding regenerates them.
Sampling is independent of playback direction and frame rate.

`MotionAssistPreview` borrows a standard model's live skeleton and invokes the
existing read-only Model7 foot-contact solve **after** applying derived offsets.
The original curve remains authoritative; unselected parts, root scale, native
metadata, visibility, expressions and independent screen-space paint are retained.
Only `evaluate_preview()` is the guarded public entry point: stale model data,
unavailable roots, invalid strength/time and unreachable contacts return errors.
Its internal inherited sampling methods are not an editor API. Failed configure
does not replace the previous valid preview. The first adapter requires complete
matching curves; half-frame comparisons reject mismatched easing/Holds and omitted
controls. This finite comparison remains a bounded check for the original explicit-
curve API, not a proof for arbitrary future curve types.

`configure_document()` now uses `MotionAssistTracks` to read actual legacy and
independent part records through the existing BodyCurveRuntime indexes. It retains
source keys, per-part easing, virtual/rest controls and removals. It does not
flatten the sampler into newly authored keys. A split uses the original source
phase; moving the slice carries that relative motion. Part-specific gap and
introduction intervals use the existing endpoint values and easing, with bounded
additional acting. Deliberate Holds stay exact. Nothing anticipates before the
object's first presence. Retained source addresses up to100000 remain independent
of the unchanged240-frame project limit.

Carried offsets and extra gap movement share one final translation/rotation bound.
The last complete take keeps its generated settling tail. Trimming through a
moving span fades the retained offset back to the held final pose over .24seconds,
without letting cropped future controls pull it onward. That boundary behavior is
a provisional engineering choice for review. Gap fade/acting never changes object
visibility. Helper records include part/piece/source addresses and actual bounded
values, sorted chronologically. IDs are derived inspection records, not a promise
of stable editable helper identities across legacy promotion or structural edits.

The experiment can render preview PNGs and a diagnostic MP4 through the existing
renderer/encoder. Normal final rendering intentionally ignores transient preview
hooks. A diagnostic movie does **not** prove ordinary Export or `.has` persistence
of generated assistance.

## Evidence and limits

Run `python tests/verify_motion_assist.py` and
`python tests/verify_motion_assist_tracks.py` for deterministic headless checks and
`python tests/verify_motion_assist_native.py` for hidden Windows GPU tests. The
latter needs the prepared five-native packed fixture from
`verify_contact_persistence.py`; it does not silently skip missing native inputs.
It covers Miku, GMod Reimu, SFM Scout, VRM1 and VRM0 with three authored controls,
continuous planted feet, 97 half-frame samples and 49 displayed integer frames.
It checks exact main poses, reverse seeks, Off restoration of both data and GPU
pixels, independent editable paint, stale-query refusals, original-source hashes,
and a 1080p24/48-frame/two-second diagnostic movie. The document adapter also tests
native splits/moves, exact relative solved poses, gap/tail reach and visible foot
pins on all five rigs. Tests stay on a private Windows
desktop. Reports/logs/receipts are in `output/motion-assist*-verification.json`.

The standalone experiment itself adds no normal editor/storage path. The separate
Model8 increment connects a toggle/amount, black main keys, read-only Advanced
inspection, settings, Undo and normal Save/Export. Individual helper adjustments,
manual pins, complete editor clip/clipboard lifecycle, automatic walking, collision
anticipation and contextual faces remain unfinished. Large dense rigs are not
profiled. Versions1–7 keep their behavior. No original model is rewritten.

The .65 strength, .12-second short-transition cutoff, .24-second tail and profile
weights are provisional engineering choices for this experiment, not settled
owner preferences. Anatomy, posing quality and performance style still require
visual review. Reach failure is explicit; there is no automatic foot unpinning,
silent amplitude reduction or FK bake. Stable manually pinned helper identities
are a proposed later editing rule, not a confirmed or implemented contract.

Next: broader Model8 editor/physics/clip/recovery acceptance and full regression;
then individual helper editing and richer acting. Preserve the full core workflow.
