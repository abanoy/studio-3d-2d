# Required posing and locomotion coverage review

The remaining labels were checked against their source sections rather than an
expanded feature wishlist. ADD5.3 asks for natural hand/arm IK on supported rigs,
crouch/root movement with appropriate foot holding, and graceful fallback for
missing/unusual rigs. It does not require a general full-body IK solver. ADD5.5
requires reusable editable paths/clips and a visible, correctable locomotion
suggestion; multi-view depth inference algorithms and accuracy remain OPEN.
General automatic terrain inference and automatic facing have no decided universal
acceptance contract in that section.

The current implementation supplies the required bounded workflows: default
natural limb dragging, planted/root editing, supported imported declarations,
manual opt-out/fallback, reusable authored paths/clips, staged optional walking,
manual corrections, Cancel, one-step Undo and persisted suggestions. Stationary
nested parents are now supported. Moving/tilted parents, sustained pivots and
unsupported route/rig combinations report limits before replacing usable state.
These limits and the explicit native/artist/device gates remain in the checklist.

The fresh private-display default IK suite passed31checks, including real gizmo
input, auto-key/Undo/Redo/Cancel, unsupported-rig/nonuniform-scale fallback,
transformed parents, preserved source, packed replay, independent drawing/audio
and48frame1080p24H264/AAC with measured audio onset1.0000417s. Optional native
samples were unavailable and explicitly skipped; none are counted as native proof.
Committed helper/direct fixtures separately supply70app checks including actual
crouch/foot holding, source-offline packed replay, recovery and exact rendering.
The committed grouped/ungrouped walking suites exercise staged editor behavior,
recovery, source/cache-offline cold readers and exact real movie inputs.

POSE-03 and MOTION-03 therefore have their required implementation paths. Broader
native fidelity remains IMPORT-02/03; artist/device/Windows observations retain
separate acceptance gates. Implementation labels are corrected without claiming
those external tests passed or treating OPEN inference details as requirements.
See [fresh IK evidence](benchmarks/required_ik_review_2026-11-07.json),
[helper/crouch evidence](benchmarks/helper_limb_ik_2026-11-07.json) and
[grouped walking evidence](benchmarks/grouped_walking_2026-11-07.json).
