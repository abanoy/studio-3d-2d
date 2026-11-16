# Bounded empty built-in compatibility context — source successor

**GDScript UNPARSED / runtime UNRUN.** Root alone owns the next attempt3 lease.
Original source packets and actual failed attempts1/2 remain unchanged. This
packet narrowly accepts the observed empty engine-default-shaped import context;
it does not disable/remove any node or change physical simulation state.

The helper permits at most one modifier across the actor subtree, scanned with
get_children(true). If present it must satisfy every condition:

- exact native get_class() PhysicalBoneSimulator3D;
- direct child of the qualified Skeleton3D and internal to its children list;
- get_script()==null;
- is_simulating_physics exists and returns boolean false;
- zero PhysicalBone3D nodes anywhere in the actor subtree, including internal
  children. The69 skeleton pose bones are not a physical-body count.

Any other modifier, script, body, extra simulator, non-direct/non-internal child,
unavailable simulation query, live simulation or scan-budget excess is refused.
The existing native-parent7, rest-only=false and empty final-pose-owner guards
remain. The same helper runs initially and at each root-case end; changed
context is refused. Active=true alone is not physical simulation: actual
diagnostic2 reported that value together with false simulation and zero bodies.

Success rows record only scalar import-context flags/counts/class. They state
matches_engine_default_structure, not proven engine creation. The simulator's
private compatibility flag is **UNMEASURED**. We do not infer or change it.

All original check calls are byte-identical: numeric gates2e-5, geometry gate1e-5
per scale,68 unaffected bones,152/144/9509 influence counts, Off exact equality,
same12 profiles/1,440 ticks and expected7,289 successful checks. The latter is a
proposed unchanged count, not an observed success for this unrun successor.
No new check call is added for the helper; context failure uses refusal.

Actual diagnostic2 parsed successfully, then failed the original modifier guard
before dynamics. It measured exactly one internal direct PhysicalBoneSimulator3D,
active=true, is_simulating_physics=false and zero physical-body descendants;
parent7, rest-only=false and final-pose count0. Both headless children were
reaped, inputs preserved, no process killed and root released the lease. Those
failures remain failures. Their exact hashes are retained in STATIC_PREPARATION.

Root must source-review this successor, stage fresh files and generate fresh
full/FK/math/closure authority. The copied ROOT_LEASE_TEMPLATE remains deliberately
unapproved; original actor/source fixtures and200-file source lock are unchanged.
The original proposed geometry/live-pose scope is documented in
experiments/source_0x31_native_leaf_20261115/README.md; diagnostic history is in
experiments/source_0x31_native_leaf_diagnostic_20261115/README.md.

No engine/parser, browsing, CIM, Git, production/project/test or original asset
action was performed by this source-only preparation. No native coordinate arrays
or source media are published. Native SDK/artist parity, actual GUI/body/fan/Record/
HAS/render integration and the general native solver remain unqualified.
