# Optional character height review - development

Enable **Options > Offer character height matching on model import**. It starts
off every launch. Off means no extra height analysis or adjustment. The choice
survives New/Open during that launch and travels with the import request through
native conversion and the shared model-import path.

Review happens before world installation, placement or automatic Physics. It shows
visible neutral extent and an editable target, initially **1.8288 metres (6 feet)**.
This choice uses one Studio world unit per metre; the source adapter's unit
conversion is separate. Hair, hats and shoes affect visible extent. Uncheck Fit
to keep the original size, or Cancel to add nothing. Maps bypass this review.

A fit suggestion requires an unambiguous head/two validated legs, visible skin
coverage in all three regions, an upright body axis and a provisional leg/extent
ratio between .35 and .62. Each region needs at least 2 percent of skin weight mass.
These thresholds are engineering estimates, not a learned classifier or proof of
intended stature. Short/long/uncertain figures start unchecked. A complete unusual
figure can still fit by explicit choice; an incomplete part cannot. A full skeleton
alone does not qualify. Uniform root scale preserves proportions and source data.

Measurement follows the feet-to-head axis; a sideways model is flagged and starts
unchecked. Fitting does not rotate it. Advanced reveals ratio/coverage/original scale
and source identity. Switching modes retains the same measurement and pending
choice; scrollable content keeps Add/Cancel pinned.

## Persistence and lifecycle

Accepted scale is ordinary standard-model root scale, applied before placement and
inherited by physics/helpers. Placement accounts for root rotation and uniform
scale. One world Undo removes the whole import; Redo restores it. No pose/camera
keys are invented. Import timing, independent drawing and peers retain their
existing contracts. Packed/linked saves and cold Open do not rerun fitting.

`metadata.import_height` (`studio_import_height_1`) records original root scale,
source SHA, measured extent, target/factor, axis, ratio and coverage as exact decimal
text, plus float32 scale bits. This prevents repeated JSON parsing from rewriting
the measurement record. Runtime uses ordinary numeric scale, with no new model,
world or HAS version. Metadata records the import choice; it never commands a
second fit on Open or after later edits. Original GLBs remain unchanged.

Cancel/New/Open/scene changes and changed sources prevent late installation.
Deferred requests use generation guards, including immediate cancel/reopen.
Duplicate imports defer while review is pending. A native converter can show its
existing limitations message; accepting that message does not install the model.
Default Physics starts after accepting height review. Pending app teardown releases
the temporary renderer/window without a suspended Node coroutine.

Source hashing/import/measurement run synchronously after opting in and may pause
on large assets. A disposable standard model uses existing shape geometry and skin
matrices. Query refuses above 200,000 vertices; existing GLB/bone/skin limits remain.
There is no source-family pose engine, cloud call, game/addon execution, external
model exporter or original-source write.

## Actual verification

`python tests/verify_character_height.py` passes 104 editor checks, four cold-reader
checks and nine actual native-import/physics/lifecycle checks:117 total, zero failures.
Authored fixtures include full/short-legged/long-legged figures and a head retaining
a complete skeleton. Actual preparations are Miku, GMod Reimu, SFM Scout, VRM0/1 and
Mima head. All full figures reach target within the unchanged 2e-5 world-unit bound;
standalone heads remain ineligible. Tests cover opt-out/map bypass, exact data/view/
keys/Undo, timing, cancellation/reopen, Simple/Advanced, packed/linked HAS, exact
engine scale/provenance, no double fit and editable cyan drawing. Ordinary H264
1920x1080/24fps/48-frame/two-second MP4 matches its own reopened frame12 exactly.
Three accepted private GPU receipts prove placement/cleanup with no foreground
child observed. Actual review screenshots inspected; no physical input certification.

First target assertions queried future-frame models while hidden at 0. Sampling
at introduction retains the same bound and adds explicit absence proof. Initial
persistence exposed decimal reparsing differences up to about 4e-16 in numerical
measurements; decimal-text provenance fixes that rewrite. A remaining assertion
compared integer placement counters to JSON numeric variants. Canonical full-
precision JSON comparisons retain every stored value; actual engine scale bits
and target geometry are checked independently. Failed logs remain separate.

Affected placement/import/physics/camera/HAS/UI suites run separately. Entire full
verifier wiring does not mean a fresh whole-suite pass. Normal installed Model7
and the frozen web preview remain unchanged until a separately reviewed update.

Ten affected groups pass 396 checks (21 placement, 58 camera, 17 timing, 41 import
physics, 51 native, 50 common-format, 46 Source, 44 browser, 45 HAS and 23 UI).
Together with the new 117, that is 513 accepted scoped checks, with 13 accepted
private GPU receipts. The original regression controller exited 1 on a stale
browser assertion that treated LayerEditor's reusable hidden "Remove drawing
layer?" confirmation as an import prompt, then confirmed it indiscriminately.
A diagnostic run identified its exact title/visibility. The corrected test checks
visible confirmations after the deferred import action and never confirms an
unrelated dialog. No production fix was needed; installed Workshop import,
physics, map and separate-addon material resolution all pass in the final run.

The seven successful prefix groups were retained; only browser and the remaining
HAS/UI groups ran in continuation. Its source audit records the exact test-only
changes (full-runner wiring and the browser assertion); production inputs are
unchanged across both runs. The original failure and diagnostic receipt remain
separate. An initial continuation helper path-separator assertion failed before
launching any app; Windows-normalized paths corrected that collector. No pixel,
movement, target-height or reach tolerance was relaxed. This is a scoped result,
not a clean exit for the original aggregate or a fresh full-suite certification.

Development now also offers [static map calibration and a six-foot guide](map_calibration.md).
Remaining: animated/attached map calibration, automatic character assembly,
artist-certified proportion detection, resizing existing
animated objects/contact reanchoring and a later per-object reset workflow. Native
fidelity, physical tablet/clean-machine/full-disk/power-cut and large-model latency
acceptance remain unverified. This is one import increment within the full goal.
