# World rail transition transaction: source proposal

The guarded setter can refuse while World children temporarily leave the scene
during reparenting. Previously `refresh_world_mode` committed its own cached
`world_rail` first. A later refresh could see that cache equal the desired mode
and skip the still-unapplied selection transition. Root reports a completed
diagnostic with layout mode false, selection mode true, hidden Tree, and every
relevant control live after settling. That actual diagnosis is supplied by root;
this packet performs no runtime or native observation.

The proposed `set_rail` returns false from its existing liveness guards, true
from a valid unchanged-mode no-op, and true after applying a transition. Existing
callers may ignore its return. `refresh_world_mode` commits its cache and styles
the dock only after this acceptance. Its fast path also checks the selection's
mode, allowing recovery from a preexisting cache mismatch. `float_panel` queues
one forced World refresh after its reparent/show/layout work has completed; the
same existing liveness guards handle teardown or an off-tree callback.

Only `set_rail`, `refresh_world_mode` and `float_panel` change. Font caching,
font names/weights/fallbacks, lifecycle flags and every guard expression remain
unchanged. Mode remains assigned inside the setter before its existing styling
operations, preserving its synchronous reentry behavior. No guard is waived,
and there is no polling loop or unbounded retry.

`prepare.py` read the exact pinned review sources and wrote only the two
`.proposed` files plus `SOURCE_PROOF.json` here. It verified an exact inverse and
byte equality of every other function, then rechecked the review hashes.
No engine, CIM, native input, Git or review/main runtime write occurred. This is
source preparation, not a CPU simulation or a runtime acceptance test.

Root must qualify the actual floating World transition using the unchanged
45-check rail fixture, 29-check lifecycle fixture and 48-check controls, then
the five-case 12,504-check workspace suite. Exercise a temporarily unavailable
held control: refusal must leave the layout cache unchanged, and a subsequent
live refresh must apply the requested mode. Existing formal counts/predicates,
strict diagnostics and physical job/desktop closure remain mandatory. This
packet does not qualify the fix, a full suite, native normals or owner review.
