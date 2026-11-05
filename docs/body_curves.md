# Independent body curves: validated foundation, editor connection pending

**Historical foundation notes:** normal model6 integration now supersedes the
pending gates below. See [independent body controls](body_animation.md) and the
latest progress memo for implementation, verification and canonical save status.
The sampled diagnostic files described here remain distinct from native model6.

Normal Studio body keys still contain whole-pose snapshots. A new right-arm key
can change an untouched left-arm eased curve: the probe in
`output/body-channel-probe.json` measures X at6 changing1.5625→2.5 after inserting
a key at12 between original0/24 controls. Expression keys are already independent
in model5; this remaining issue concerns root/bone pose controls.

`src/body_curves.gd` implements an experimental source-independent internal
`studio_body_curves_1` record. It is exercised separately and is **not installed
as the normal editor's evaluator or HAS writer**. Normal projects still use the
existing model1–5 contracts. Do not advertise this as completed per-part editing.

The record keeps each original source-time piece, full legacy key snapshots and
the set of legacy body channels. New controls are sparse per-part overrides;
deleting one legacy control masks only that part's source address. Other parts
continue to use the exact original snapshot values and interpolation. This avoids
copying every native bone name onto every old key. Root and bone position/rotation
remain one transform per part, with quaternion slerp; root includes uniform scale.
Independent per-axis editing is still required work.

Per-part introductions and source origins preserve a newly animated part's initial
transition. Legacy channels retain historical first-key clamping. Empty legacy
blocks retain their static bases and existing gap behavior. A new part's block
does not anchor unrelated curves. Only a pure block containing exactly the edited
parts can grow; a different part gets a separate piece when outside existing
blocks. Split retains source curves/origins and move changes only placement.
The original model dictionary, native identifiers and GLB remain untouched.

Validation bounds32pieces,512bones plus root,241controls per part/legacy array,
2048stored snapshot/override/deletion addresses and1MiB metadata. Reject malformed
sources before extraction, missing bindings, nonfinite transforms, invalid scales/
quaternions, overlapping pieces, duplicate/unsorted addresses, phantom deletions
and root/bone identity collisions. These are bounded prototype checks, not a
hostile-file or arbitrary-large-scene certification. Future project integration
must count this with the complete world, expressions and other project metadata.
Runtime caching of per-part source-point indexes and larger dense-take profiling
are also integration gates; current timing probes are not scene frame-rate claims.

`python tests/verify_body_curves.py` runs headless domain checks and an actual
hidden Windows GPU test. The original authored fixture has two independent skin
branches: editing the opposite part changes its rendered skin, while root/peer
matrices and an isolated peer image remain exact. Prepared MMD/GMod/SFM/VRM0/1
rigs use their actual native arm identities, deformation and provenance. Actual
native physics takes additionally compare every effective body transform at
half-frame intervals. Legacy sparse missing identities are compared to neutral
transforms, not mistaken for different physical poses.

The test saves/reopens the experimental JSON record. For an additional pipeline
diagnostic it samples ordinary existing pose keys and saves packed `.has` files,
then exports an authored1080p24/48frame MP4 with an independent cyan cel. **Those
diagnostic HAS files contain sampled ordinary motion, not editable independent
tracks.** Sampling through the old evaluator adds quaternion normalization: the
first diagnostic measured a maximum component difference1.19209289550781e-7.
Stored sampled payloads and pre-save versus reopened ordinary evaluation are
checked separately, without claiming that conversion is bit-exact to raw curves.
Normal integration must use the independent evaluator directly, not substitute
these diagnostic bakes for native editable tracks. All graphical tests use the
private desktop; original files are checked by SHA256 and modification time.

The experimental record is a body-data view, not a replacement model asset.
Future integration must map controls onto existing model/clip IDs and retain
expression curves, visibility, geometry references and unknown native metadata.
Do not replace complete Model/clip dictionaries with this body-only projection.

Next integration gates: explicitly version model data; retain exact reads of all
old versions; connect auto-key/IK/explicit Record and draft/cancel/no-op behavior;
per-part timeline frames/deletion/Undo; world/local capture accounting; coexistence
with model5 expressions, helper asset revisions and visibility; all-object packed/
linked/recovery persistence and direct render/export evaluation. Copy/cut/paste,
whole-object retiming, original zero-key/static legacy behavior and existing
multi-object tests must pass before switching the normal editor. Full HAS scope
and the owner's Simple/Advanced and no-visible-tests requirements remain intact.
