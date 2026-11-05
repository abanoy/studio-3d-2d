# Animated imported shapes

Select an imported model and choose **Shapes / expressions…** in the pose panel.
Choose a part and a named shape, enter an Amount and **Apply at this frame**.
Auto-key is on by default. Set an amount at the starting frame, then another at a
later frame; scrub or play to see the transition. Existing Advanced interpolation
offers ease, linear and hold. Undo reverses one applied edit. Camera keys stay
explicit, and original models are not modified.

**Use base amount here** keys the model's static base value at this frame.
**Use all base amounts here** does this for every shape already animated on this
instance. Advanced Auto-key off keeps a same-frame draft; **Record pose key**
includes that draft. Scrubbing/export uses authored curves. Whole-project base
shape controls remain Advanced and separate from per-frame authoring.
**Remove this shape key here** removes only the selected expression's control at
the current frame. Its remaining curve is sampled immediately; Undo restores it.

Simple shows familiar part labels and a small local dictionary's English estimates
for known Japanese expressions, marked ≈. Search accepts English or original names.
Advanced and tooltips preserve internal names; none of these labels rename assets,
bones or target indices. Unknown expressions retain their original names.

Expand an object's timeline row and click its shape channel/key to open that
control at the selected frame. Expression controls use the piece's source time
independently of root/bone snapshots. Splitting preserves samples, dragging carries relative
timing, gaps connect under the existing interpolation and final values hold.
Copy/paste works between instances of the same model at the same frame rate.
Pasted pieces carry their resolved source amounts; the receiving instance retains
its own base outside the pasted piece. Visibility stays independent.

The first edit promotes only the edited instance to **studio_model_5**. Readers
still accept versions1–4 without changing their output. Older Studio binaries
reject version5; use the updated app for these projects. World schema4 and HAS
ZIPv1 do not change. Packed/linked HAS and normal recovery include the curves,
native metadata and original standardized geometry. This is not export-back.

Version5 stores `shape_base`, `shape_pose` and optional `shape_names`, indexed by
canonical decimal source-node and target identities. `shape_base` records each
channel's static amount when first animated; older snapshots lacking that channel
inherit it. Pieces carry dedicated `shape_keys` with absolute `shapes` amounts and
may carry `base_shapes`. A keyed channel controls its absolute amount throughout evaluation,
including holds. Later changes to static base do not silently rewrite authored
amounts. Explicit Use base amount here adopts the current base as a new key.

Playback updates GPU weights and conservative per-frame bounds. Raw targets are
decoded once on first use and only needed targets are cached. Exact effective CPU
vertices are evaluated on demand for helper review/placement/physics fitting.
Physics fits/colliders are built at activation; later expression changes do not
continuously rebuild live collision shapes. Record retains authored expressions
alongside simulated bones/roots; expression bytes count toward capture limits.
All stored channels/amounts/bindings validate before replacing live data. The union
of animated channels shares the existing2M vertex-target operations per primitive/
8M per operation cap; this conservative gate can refuse very large channel sets
even when different channels are used at different times. Amounts remain finite
and bounded to absolute100. Existing2048 override/key and1MiB project limits apply.

Current limits: root/bone controls remain shared pose snapshots; no VRM
expression-group/preset composition, native MMD material/bone morphs, Source
bodygroups/skin variants, driver/constraint recreation or automatic lip sync.
Native shading remains approximate. First-use target decoding can pause an Apply;
warm evaluation measurements exclude rendering, input and first-use preparation.
These are partial importer-fidelity improvements, not complete native semantics.

Model4 files retain their historical shared-snapshot evaluation when read. The
earlier example (ease X0 at0 to X10 at24, expression key at12) remains X2.5 at6
if that control was already saved in model4. Editing an expression explicitly
upgrades that instance by extracting the old expression snapshots into separate
controls, preserving its existing body and expression curves before the new edit.
New expression keys in model5 never insert body controls: X at6 remains1.5625 in
the same two-body-key example. Body-only blocks are ignored by expression curves;
expression-only blocks are ignored by body curves. Different expression channels
also retain independent controls/interpolation, including shared-frame edits.

`shape_draft_frame` separates expression drafts from body drafts; `shape_starts`
retains per-channel introduction addresses across later edits and whole-object
retiming. Optional source `shape_origin`/`shape_leading_hold` preserve sliced and
legacy endpoint behavior. A new target outside another expression's block receives
a separate piece to preserve that target's gap boundaries, within the existing
32-piece limit. Root/bone per-axis control ownership is still unfinished.

These fields continue to work in model6 after a body edit or explicit Record.
Model6 retains independent `shape_keys`; it does not downgrade when expressions
or visibility are edited. See body_animation.md for version6 source ownership.

Verification: `python tests/verify_shape_animation.py` includes domain checks and
actual hidden Windows UI/GPU, clipboard/Undo, native MMD/GMod/SFM/VRM0/1, weighted
helper Local Record, packed/linked HAS, recovery, separate drawing and MP4 checks.
Final commands/results and limitations are recorded in progress_memo.md.
