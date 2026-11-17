# PMX physics: source gap and next increment

This is a source-only audit of the main HAS checkout. The accompanying
`SOURCE_MANIFEST.json` binds the exact files, hashes and function locations read.
No engine, native asset, graphics run, process inventory, test, Git operation or
owner-review change was performed. This report does not qualify native fidelity.

## Finding

HAS can animate loose parts through its own spring/helper workflow. It does not
currently reproduce native PMX rigid-body/joint physics. Preserving a complete
original PMX in the conversion folder is different from retaining its physics
declarations in the portable HAS representation or simulating them.

| Native information | Current preservation | Current runtime interpretation |
| --- | --- | --- |
| Complete PMD/PMX source bytes | `prepare_mmd.prepare` stages and hashes the original source; the conversion bundle retains it | Not read by the running HAS physics adapters |
| Imported MMD properties | `blender_mmd_bridge.run` saves a packed `editable.blend` before material approximation | Archival intermediate; this audit did not open it or verify each native field |
| Rigid-body bone reference, shape, size, pose and body mode | No explicit native physics table is emitted in the MMD report or GLB metadata | No PMX kinematic/dynamic/dynamic-with-bone mode mapping |
| Body mass, linear/angular damping, restitution and friction | Remain available in the original source; no explicit portable declaration table | HAS-generated body proxies use their own constants |
| Collision group and non-collision mask | No explicit native PMX table/mapping | HAS rigid bodies use layer 2/mask 3, direct-neighbor exclusions and HAS rest-overlap rules |
| Physics joint body references, frame, translation/rotation limits and spring coefficients | No explicit native joint table | No native PMX six-degree-of-freedom spring-joint adapter; generated ragdolls choose HAS hinge/cone profiles |
| PMX 2.1 soft-body declarations | Original source retained; no portable native soft-body table demonstrated | No PMX soft-body solver in the audited import/secondary path |
| Bone IK declarations | Supported chains explicitly captured by `mmd_ik.capture` into standard IK metadata, with skipped reasons | Used by supported pose/motion workflows; these are bone IK constraints, not physics joints |

`asset_audit.pmx_summary` stops after the material count. Its texture/geometry
inventory is not a physics-table reader or a complete PMX integrity validator.
The MMD bridge selects renderable meshes, armatures and roots for GLB export;
it does not explicitly serialize imported rigid-body/joint helper objects into
a standard physics contract. The report's existing warnings disclose native
physics limitations.

`pose_editor.definition` retains a supplied parameter report in model metadata,
with a 256 KiB report limit. `has_project.members` manages declared current GLB,
audio, image and effect assets. The native source and editable Blender snapshot
are not automatically included merely because `external_bundle` names their
folder. There is currently no full PMX physics table in that supplied report.

## What hair and clothing can actually do

- `secondary_rig.from_gltf` recognizes VRM 1 spring-bone declarations, VRM 0
  secondary animation and `has_secondary_helpers_1`. It has no PMX body/joint
  branch. Validated chains resolve to live HAS bone/path identities.
- `secondary_spring.construct` uses Godot spring-bone chains with per-joint
  stiffness, drag, gravity/direction and hit radius, plus sphere/capsule
  colliders and per-chain collider membership. This is a bone-driven spring
  approximation, not a fabric surface/PMX rigid-body solver.
- `secondary_helpers.build` creates a derived GLB with reviewed helper bones
  and a bounded redistribution of the selected anchor's skin weight.
  `build_existing` instead reuses an available linear skin-bone chain and adds
  an unweighted tail; it keeps existing skin/accessor/BIN data. Neither operation
  reconstructs original PMX mass, masks, joint frames or spring coefficients.
- Generated helper chains currently use stiffness 1, drag 0.45 and hit radius
  0.005. They do not author collider groups. `secondary_rig.from_gltf` explicitly
  rejects generated additions that declare colliders/groups or borrow native
  group indices. This is a concrete limitation for convincing cloth/body contact.
- `secondary_live.advance` feeds deterministic, spatially varying fan forces
  through fixed ticks and blends generic spring offsets into the authored pose.
  `physics_editor.disable_hair` disposes those offsets, clears previews and
  reapplies authored motion; Record explicitly keeps ordinary editable FK keys.
  The source implements Off restoration, but this audit made no new native
  observation of the owner's previously reported stuck deformation.
- The separate Source-native secondary backend is gated by its own offered
  native rules. Its presence does not provide PMX physics support.

## Gravity, units and scaling

The native MMD preparation scale defaults to 0.08 (`source_import.start` and
`prepare_mmd.main`); the importer applies it before GLB export. This is separate
from a later model root scale. No native PMX physics-unit conversion is applied
because no PMX physics adapter exists yet.

The spring runner builds unit-scale scratch skeletons at actual world positions,
scales hit radii and collider dimensions by the bound model's uniform scale, and
rejects nonuniform/reflected/degenerate transforms through the regular-basis
guards. It forwards gravity magnitude/direction and stiffness/drag directly from
the VRM/HAS definition; those are not PMX damping or joint-spring units. Fan
strength is a relative HAS control: `airflow.unsteady_force` uses a 0.03 factor
and a bounded force, with smoothing in the generic live runner.

Generated ragdoll masses are 3 for detected hips/spine and 1 otherwise; friction
0.8, bounce 0, linear damping 0.15 and angular damping 0.6. Prop proxies use mass
1, linear damping 0.15 and angular damping 1.5. Project settings select Jolt and
120 Hz; the audited project/body path sets no PMX-specific gravity or native
gravity-scale conversion. Consequently neither size matching nor common numeric
parameter names establish native PMX behavior.

The height code defines six feet as 1.8288 metres. Current `import_height_review`
preselects Fit for an unambiguous, upright humanoid with plausible leg ratio,
allows the owner to change that choice, and applies ordinary root scale with
measurement provenance. It does not create the requested six-foot-at-scale-1
import basis. Section 16 of the master plan still describes the older
off-by-default choice; actual source is authoritative for this audit. A future
physics translator must keep source-unit scale, normalization basis and editable
instance scale separate; it must not silently rescale mass, gravity or spring
constants merely by multiplying geometric lengths.

## Evidence boundaries

Fresh work here consists only of source reads and SHA256 binding. No test was
run and no current full-suite/native acceptance result is inferred.

Historical `native_mmd_gma_2026-11-08.json` records an MMD generated-physics check
with 12 checks/0 failures and explicitly limits its scope to generated HAS
physics/freeze, not native MMD simulation reproduction. Its result is historical
and platform-specific; it is not a fresh Windows PMX solver result.

Current test source covers shared spring-chain adaptation, scale/contact
controls, FK recording, Undo, packed reopen and movie output
(`secondary_motion_smoke`, `verify_secondary_helpers`). Optional MMD helper
fixtures exercise weighted native bindings, not native PMX bodies/joints. The
authored PMX IK and expression fixtures define no physics body/joint corpus.
The native-import verifier checks conversion/shared model/save/render behavior.
None of those source-level scopes demonstrates a native PMX physics table
round-trip or an independent PMX solver comparison.

## First small, reversible increment

Add **inactive, bounded native PMX physics declaration preservation** to the
existing MMD parameter report, before any solver translation. It directly closes
the first loss point requested in master-plan sections 14–15 and keeps current
hair/body behavior unchanged.

1. Add a pure capture/validation helper accepting the decoded native model.
   Invoke it from the existing isolated MMD preparation worker; do not add an
   application-time native-file reader or a new tool installation. Start with
   PMX rigid-body and joint tables; explicitly mark soft-body data unsupported
   rather than claiming preservation by omission. PMD adaptation is a separate
   follow-up unless native PMD-to-PMX provenance can be retained exactly.
2. Preserve source SHA, source format/version, source-unit values and exact
   native indices/names. Capture body type/shape/size/pose/mass/damping/friction/
   restitution/group/mask and joint type/body refs/frame/limits/springs. Record
   `applied: false` and preservation versus runtime support separately. Stable
   HAS bone bindings require exact validated identity; retain an unresolved
   native reference and reason instead of guessing from duplicate names.
3. Validate exact JSON types, finite values, index domains, count/byte budgets
   and supported declaration types. Fit the complete additive capsule within
   the existing report/project metadata budgets. If it cannot fit or a type is
   not understood, retain the original bundle and report an explicit incomplete/
   unsupported status; never call a truncated table fully preserved. Keep GLB
   geometry/BIN, source files, current schema and live solver path unchanged.
4. First run CPU tests on small authored data for every captured field, signed
   mask behavior, all body modes, sentinel/unbound references, joint limits,
   wrong types, NaN/Inf, excessive counts, unsupported types and size refusal.
   Assert loss disclosure and byte-stable geometry/source. Then schedule actual
   isolated native conversion, portable/cold HAS metadata retention and existing
   behavior regressions under the owner's runtime rules. None is run by this
   packet.

Only after exact declarations survive portable save should a separate proposal
translate one explicitly supported joint/body subset, with independent native
reference motion, source/normalized scale cases, collision membership, Off
restoration and Record/Undo/export qualification. No solver, trained estimator,
200-item normalization catalog, schema-9 activation or model rebasing is part
of this audit or the first preservation increment.

The master's old-test archiving policy remains applicable: publish only allowed
code/compact evidence, verify remote retrieval, then consider proven disposable
session data. This packet contains no native art, geometry, rendered media or
private model coordinates and performs no upload or deletion.
