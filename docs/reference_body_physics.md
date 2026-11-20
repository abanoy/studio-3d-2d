# Body Physics at the human-reference size

The addition extends the existing Physics toggle to models with an explicit
six-foot reference, including artist sizes 0.5 and 2. It uses the original actor,
bones, skin, shapes and materials. No new saved model representation is added.
Scoped mechanical/editor/native qualification passes; complete Windows
verification is next. See `benchmarks/reference_body_2026-11-20.json` and the
current pickup for exact executed scopes.

Collision planning uses metre coordinates for skin boxes, capsule/sphere
fallbacks, margins, nearest-child selection, span floors and anatomical joint
planes. For each original world bone W, the planned rigid world frame B has a
unit basis. The private body offset O = inverse(W) * B retains reciprocal scale.
The pinned engine can therefore reset W * O and reconstruct W from B * inverse(O)
without baking scale into original bone data. Joint axes alone are normalized;
the inverse-offset joint pivot is retained before the initial joint is created.

References whose skeleton or structural world bones are nonunit use this plan.
This includes a scaled skeleton whose source bone scales compensate to unit world
bones. Legacy reference-free models and genuinely unit reference rigs keep their
existing geometry/profile policy. Anatomical thresholds for the new plan also
use metres, so equivalent tiny/large raw coordinates keep the same hinge planes.

The planner is ephemeral and validates the complete plan before allocating
simulation nodes or shape resources. It retains the existing one-skeleton,
48-body, positive-uniform unsheared-scale and weighted-vertex budgets. Its
additional defensive bounds are world basis scales 0.001 through 1000, metric
span/relative bounds up to 10km, and absolute origins up to 100km. These ceilings
are refusal guards, not a precision certification at every admitted coordinate.
Qualification uses ordinary metre-size figures, small world origins, half/unit/
double sizes, equivalent raw-unit encodings and source/artist/static-parent
compensation. Unsupported states give an actionable refusal and preserve the
original authored/live state.

Body Physics Off retains its existing Freeze behavior. Hair & clothes Off
restores authored loose-part pose while an independent body simulation can keep
running. Local/World Record stores original canonical editable motion and artist
scale, removes the actual parent and intrinsic base once, and uses existing
fixed-tick/rational timing. For a humanoid beneath an animated parent, Record
retains the exact held affine world frame outside C*B0 and compensates the parent
at each destination frame. Changed parents/targets or unrepresentable local
transforms refuse without replacing authored animation. Normal
scale/pose/seek/reparent/asset operations retain
their existing freeze or rebuild policy; live scale animation, arbitrary runtime
mutation, nested simulated parent/child bodies and imported Source hair combined
with body physics are outside this addition's supported controls.

Reproduction sources:

- `tests/reference_body_plan_unit.gd`: geometry selection, thresholds and refusal.
- `tests/reference_body_physics_unit.gd`: independent fixture FK/skin/shape/joint
  expectations, real collision queries, engine reset/writeback and atomicity.
- `tests/reference_body_anatomy_unit.gd`: independent straight-limb anatomical
  planes across equivalent source units, with an exact legacy-profile control.
- `tests/verify_reference_body.py`: actual editor, contacts, body/hair lifetime,
  history, rational Record, packed cold reader and video.
- `tests/verify_reference_body_native.py`: exact pinned prepared VRM0/VRM1 pairs,
  six half/unit/double cases, body/Freeze/Record/source inventory and cold pixels.
  Prepared runtime checks do not certify original-native appearance or solvers.

All automated graphics use the existing private Windows desktop launcher. Private
native art remains local; only source and compact scalar evidence are published.

Executed scoped checks:1273 mechanical/recording checks; each Neon/classic
workflow72writer/21cold plus parent18writer/6cold; six prepared VRM cases each
23writer/9cold; original reference regression each44writer/3cold. All24 private
jobs close with confirmed placement and no foreground/switch. All1059 functional
and launch-driver files preserve bytes and nanosecond modification times.
Actual two-second reference and0.96-second25/2fps body movies pass encoder checks.

Persistence checks deliberately separate two exact observations. Python compares
every packed authored field against the writer definition, excluding only
source/path relocation, and verifies embedded source hashes. Godot compares
native float32 vector/quaternion bytes, exact channel IDs/fields/root scale,
source FK/skin bounds and exact cold pixels. Its JSON decoder changes a few
loaded double scalars below native Vector3 precision; stringifying those doubles
was an invalid oracle. Raw packed numbers remain exact. Failed diagnostic runs
are retained and no numeric epsilon or persistence workaround was introduced.
