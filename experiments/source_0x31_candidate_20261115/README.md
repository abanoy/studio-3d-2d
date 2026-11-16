# Bounded Source0x31 mathematical candidate — November 15, 2026

**NOT integrated, NOT an executed SDK comparison, NOT qualified against artist
SFM/GMod motion.** No Godot/Blender app, model importer, live rig or renderer was
launched. Original assets, raw reports, production, tests and installed sources
remain unchanged. The public vectors in this packet are authored synthetic
examples; no native mesh, rest matrices, skin arrays or private oracles are copied.

**Correction after independent root review:** the original advertised zero-cone
domain failed104/1000 tilted-rest cases. That complete original packet is frozen
in `attempt1-original/`; the root failure is retained separately. The corrected
candidate handles exact zero cone analytically and passes the unchanged boundary
gate plus forced/moving controls. Use the `*-zero-cone-fix.json` results and
`ZERO_CONE_CORRECTION.json` for the current candidate. See `CORRECTION.md`.

## Candidate scope

`candidate.py` accepts explicit mathematical parameters and positive orthonormal
goals. It does not consume native files, resolve bone identities or enable the
retained metadata. It rejects every flag combination except exact0x31: flexible,
angle-constrained, length-constrained. The inspected immutable reference is
[Valve SDK019e91c](https://github.com/ValveSoftware/source-sdk-2013/blob/019e91ccd650a34745934c65cdbbe89ffcc44ede/src/public/jigglebones.cpp).
Full official source remains in the prior protected local reference directory.

The target is base plus the local **+Z** column times length. TipMass contributes
global downward acceleration, not inverse mass. Lateral error/velocity drive the
yaw and pitch springs; along-axis coefficients are retained but inactive here.
Velocity updates before position. The angle correction uses the goal-tip-centered
sphere before fixed-length projection; longitudinal velocity is removed. A
positive rigid output basis is reconstructed from the resulting direction and
goal-up vector. Other constraints, base motion springs, boing and flipped spaces
are refused or outside the candidate.

This is Python-double arithmetic, with a clamped inverse-cosine input and explicit
degenerate/nonfinite refusal. It is not a bit-for-bit translation. The bounded
cone is below90degrees. In that domain the angle-correction sphere has radius
`L*sin(limit)` and centre distanceL from the base. Its maximum subtended angle is
the limit; the subsequent length projection preserves that direction. This is
also why a direct quaternion clamp would be a different update rule.
Exact zero cone is handled separately before inverse cosine: its permitted ray
is the goal-forward direction. That guard is explicit mathematical numerical
policy, not evidence that an executable native client takes the same path.

## Separate deterministic clock policy

Reset seeds the supplied current goals with zero velocity at tick0. Integration
starts at tick1 with exactly1/120second per step. Only sequential integer ticks
are accepted; skipped/reversed/discontinuous clocks require explicit reset/replay.
Each actor owns its states; each rule has independent position/velocity. Failed
validation or computation commits no rule-state or tick changes.

This intentionally does **not** reproduce SDK first-call minimum1ms, framerate
fallback counters or skipped-update history. It is a proposed HAS clock policy,
not a claim that the closed native clients use it. At24fps there are five ticks
per output frame; arbitrary rational preview/export sampling and seek policy
still need integration decisions and actual measurements.

## Actual CPU evidence

`verify_candidate.py` passes322 assertions. Counts include240 repeated along-
coefficient invariance checks; they are not322 independent product features.
The property scenarios run17,280 steps with the two Junko-like50/100 stiffness
profiles, damping5, length20, mass20 and the retained float angle limit. Strong
synthetic acceleration amplitudes3/12/50, four directions and moved/rotated goals
produce4,363 actual angular projections. All measured states remain finite,
at fixed length, inside the cone, with tangent velocity and orthonormal outputs.
These are bounded mathematical properties, not natural-motion/stability claims
for every accepted coefficient or real fan configuration.

Additional checks cover unsupported modes, invalid parameters/bases, exact clock
refusal, atomic two-rule failure, copied metadata, reset/replay, actor isolation
and cleared stopped state. Clearing a numerical state does not certify actual
Hair & clothes Off restoration in the application.

`verify_closed_form.py` provides a separate rational first-tick oracle, without
copying the projection implementation. From identity rest and acceleration
(3,4,-20), the120Hz step has velocity(1/40,1/30,-1/6) and unconstrained position
(1/4800,1/3600,20-1/720). Independent normalized-position/tangent formulas agree
within2.7755575615628914e-17. A moved goal independently yields force(10,-20,-20)
despite a large inactive along stiffness. This establishes those scalar examples,
not SDK-executed trajectory equivalence.

`verify_damping_and_gravity.py` independently derives the second tick from those
rational first-tick coordinates. Its yaw/pitch damping force agrees exactly;
the zero-damping control differs by the expected5-times-velocity term. Rotated
goal controls preserve Source-global(0,0,-20) acceleration. These scalar controls
would expose omitted damping or accidental gravity rotation with the model.

Metamorphic unit covariance covers the nonlinear candidate with synthetic
conversion scales0.01905/0.0381 and root scales1/2, maximum error
3.132987439350646e-15. A wrong unscaled mass produces a detectable difference.
This does not qualify an actual second conversion or a HAS runtime hierarchy.

## Unresolved integration boundaries

- Actual native→glTF→HAS identity and posed/world tip transport must pass first.
  Do not substitute native index, glTF node, skin slot or HAS skeleton index.
- The caller supplies goals independently. Procedural-parent ordering and
  parent→child recomposition are **not implemented** by this actor wrapper.
- A port must validate positive uniform world transforms before separating their
  unit basis and size; these strict mathematical goal checks are not a policy
  for silently repairing raw float32, mirrored or nonuniform model transforms.
- Similarity conversion scales lengths and tipMass acceleration together;
  angular and spring/damping coefficients stay unchanged. Fixed physical gravity
  instead of similarity-scaled native gravity is a distinct artistic policy.
- External acceleration is an explicit extension. These synthetic amplitudes
  are **not HAS fan speed units**. A HAS world field needs a declared acceleration
  policy, correct sample positions, miss/opposite/zero controls and no repeated
  axis/unit transform. Pure axial input need not bend a straight length-constrained
  rule; natural flutter needs an appropriate varying/lateral input.
- No collision system, body solver coexistence, authored FK overlay, rotational
  application, Record/Undo, Off/Cancel restoration, cold HAS playback or rendered
  export is exercised. Generic VRM/helper behavior remains unchanged.
- Standalone finite parameter bounds do not qualify all0x31 assets. Full-layout
  verification flags, native activation and raw metadata remain unchanged.
- No effect on the failed/unqualified native-normal fidelity observation.

Root should review this candidate and its mathematical assumptions before any
actual runtime port. Begin with one qualified FrontHair1 rule, then parent pairs,
and only then broader49-rule lifecycle work. Save every new failure separately.

## Reproduction

Run each verifier from this directory's checkout using approved Python with `-B`.
The result paths must be fresh. Preserve the checked results before a rerun;
the scripts deliberately refuse overwriting them. `RESULT.json`,
`CLOSED_FORM.json`, `DAMPING_GRAVITY.json` and `SYNTHETIC_TRACE.json` retain original public synthetic
evidence. `PROVENANCE.json` and `INDEX.json` bind code, inspected-source hashes
and scope; the original versions are frozen under `attempt1-original/`.
Current correction evidence uses the `-zero-cone-fix` result/trace suffix,
`ZERO_CONE_CORRECTION.json` and `PROVENANCE_ZERO_CONE_FIX.json`. The root index
covers the full current packet and the immutable historical subfolder.
No original SDK binary was compiled or executed.
