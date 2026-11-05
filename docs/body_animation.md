# Independent body controls — model6

New manual body edits key each root/bone independently. Adding a right-arm key no
longer inserts a control into an untouched left arm or root. Expressions retain
their independent model5 controls. Position/rotation remain one transform per part,
with quaternion slerp and uniform root scale. Per-axis curves remain open.

Auto-key, hand/foot IK and explicit **Record pose key** share this contract.
Auto-key stores changed parts; Record also captures a rest control for parts that
are animated later. Advanced **Delete selected part key** removes only the selected
root/bone control at this frame, with Undo. Camera keys remain explicit. Visibility,
drawings and audio remain independent.

## Compatibility and source ownership

Models1–5 retain their original evaluation when opened. A body edit or selected-part
deletion promotes only that instance to `studio_model_6`; expressions alone still
use model5 where sufficient. Promotion retains original source snapshots once per
piece plus their legacy channel set. Sparse new controls override only their own
part. A deletion mask suppresses one legacy part/address without deleting a peer's
key. Historical interpolation is preserved before the requested edit. Native geometry,
IDs and metadata stay unchanged. Older binaries reject model6; use updated Studio.

`body_animation.gd` maps body controls onto existing complete Model/clip records;
the internal `studio_body_curves_1` view is not another asset or pose engine.
Expression and unknown clip fields are retained. `body_curve_runtime.gd` compiles
frame indexes once per data revision and shares legacy arrays. Preview, arbitrary
seeks and final rendering use it directly. Authored-key inspection snapshots are
derived data, not duplicated storage.

Global fields: `body_base_pose`, `body_base_transform`, per-part `body_starts`.
Piece fields: `body_origin`, `body_legacy_channels`, sparse `body_controls`,
`body_removed`, optional shared `body_rest_keys`. Rest controls avoid repeating all
bone names at every neutral Record. An unrecorded one-frame import placeholder is
a base, not a later return-to-rest key when an earlier key corrects introduction.

## Growing takes and deliberate slices

An unsliced growing take has `body_untrimmed=true`. Each part uses its own first/
last controls within the piece. Growing a shared block for an arm at14 must not move
the root's own endpoint or alter its interpolation to a later key at24. Backward
growth shifts retained source addresses together. Per-part introductions/source
origins preserve a new channel's initial transition.

Split and recording-range replacement fix retained source slices with
`body_untrimmed=false`. Both slices retain original controls outside the visible
range. Contiguous split samples stay exact; moving a slice changes its placement
and intentional gap endpoints. Copy/cut/paste, Shift-drag, drafts and Undo retain
the data. Presence and persistent visibility still govern whether it renders.

Physics capture stores compact full snapshots for its interval with a known channel
set, retaining expressions and earlier/later fragments. Packed/linked HAS and recovery
save editable model6 data directly; export never substitutes a sampled legacy bake.
World schema4 and HAS ZIPv1 stay unchanged; no external-format exporter is added.

## Limits and tests

Existing bounds remain32pieces,512bones plus root,241keys per array,2048combined
body/expression/rest/deletion addresses,1MiB complete project metadata, and existing
shape-operation limits. Validate source addresses, binding, finite values/scales and
deletion ownership before state replacement. No arbitrary-large-scene guarantee.

Project JSON now uses full float precision. Default JSON formatting rounded very
small recorded rotations and changed derived keys after reopening. Full precision
passes the unchanged strict three-fixture helper comparison; recording byte estimates
use the same precision so the1MiB limit is still real. Old JSON remains readable.
This uses [Godot4.6 JSON.stringify](https://docs.godotengine.org/en/4.6/classes/class_json.html#class-json-method-stringify),
with explicit exact-decode unit checks for tiny rotations and half-frame samples.

`python tests/verify_body_animation.py` tests normal numeric auto-key, peer/root
half-frame motion, rows, selected deletion/Undo, packed/linked/recovery and direct MP4
using actual MMD/GMod/SFM/VRM0/1 arm identities. Recorded native physics takes also
compare all effective part/root half-frames through the compiled evaluator. Existing
IK, clip, expression/helper/capture suites cover their normal paths. All graphics
stay on the private Windows desktop. See progress_memo.md for current command results
and canonical installation status; implemented code alone is not a passing test.

The earlier `verify_body_curves.py` foundation remains a separate comparison with
positively visible skin branches and pixel-exact isolated peer motion. Its sampled
diagnostic HAS files contain ordinary snapshots, not native model6 controls. Its
measured1.19209289550781e-7 diagnostic quaternion normalization is not a substitute
for exact independent persistence checks. Source hashes/mtime remain protected.
Warm simple two-control timings exclude first compilation/rendering/dense scenes.
Per-axis controls, dense scalability and full governing HAS scope remain open.
