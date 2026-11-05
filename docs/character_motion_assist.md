# Character motion assistance — owner clarification, 2026-11-01

This records intended behavior, not a claim of implementation. The normal editor
already has smooth easing, independent body/expression controls, limb IK and live
physics. Development contact tools add persistent feet and corrections. None of
those yet supplies the automatic character performance described here.

## Confirmed direction

Simple should produce a useful first character animation from a few deliberately
authored poses. The owner's main black keyframes are authoritative. Hidden helper
keys provide finer timing and character: anticipation, follow-through, overshoot,
bounce and settling. Changing the main poses or their times recalculates the
derived helpers. Advanced reveals them for inspection and adjustment. Movement
speed should influence assistance. This extends the addendum's motion help rather
than replacing ordinary posing, source imports or the shared HAS model.

The owner also requests a GMod-influenced, more contextual face editor. Existing
named positional expression controls and independent expression tracks are useful
building blocks, not the completed contextual face interface. Familiar eyes,
brows and mouth organization must map onto actual supported native channels while
preserving exact source identities and unknown channels. VRM expression groups,
MMD material/bone morphs and Source variants remain incomplete.

## Proposed implementation safeguards

- Keep authored controls and generated helpers separate. Helpers never move an
  authoritative pose or silently become ordinary authored black keys.
- Derive assistance from rational time, distance, speed and direction changes;
  use the same deterministic evaluation for arbitrary seeks, preview and export.
- Expose a simple strength/disable choice. Exact initial intensity and any default
  enablement remain a preference to test, not an owner-selected numerical value.
- Advanced can pin an intentionally edited helper so regeneration preserves it;
  clearly distinguish generated, pinned and main keys. This pin policy is a
  proposed reversible editing rule, not an already shipped feature.
- Planted feet and explicit constraints must survive assistance. Do not emulate
  personality by accidentally sliding feet, stretching anatomy or changing the
  camera/drawing/expression tracks. No physics simulation is required for a
  deterministic overshoot/settle suggestion.
- Saving must retain settings and manual corrections, version new data explicitly,
  and preserve old model output. Undo covers the whole user action and its derived
  result. Unsupported rigs retain their normal editable motion.

First useful increment: one bounded, optional body/root overshoot-and-settle
experiment on original geometry plus representative imported rigs, with exact
main-pose invariants, changing key times, deterministic reverse seeks and visual
comparison. Prove this before automatic multi-part acting or broad rig inference.
Quality of acting needs owner review; mechanical assertions alone cannot certify
a pleasing performance. Keep the full application goal and other MD requirements.
