# Pending scene-pick shutdown investigation

The production fix is in `src/world_selection.gd`; the normal regression is
`tests/verify_world_selection_teardown.py`, registered in the default suite.
This folder preserves source diagnostics and exact-binary findings, not a second
runtime or an alternative passing implementation.

Reproduce the historical defect with the current shared test and exact previous
source:

```
python tests/verify_world_selection_teardown.py --revision 2904f3f --case focus-free
```

The real private child printed four passing assertions, then leaked its global
frame-signal coroutine and exited `0xC0000005`. Current source passes all four
lifetimes/28 assertions and clean shutdown. Never accept a footer in place of
a clean child exit and valid private-desktop receipts.

`run_verbose_diagnostic.py` and `run_verbose_pick_diagnostic.py` generate an
output-only copy of the unchanged historical drawing-selection test with extra
footer diagnostics. Run those only from a checkout whose original test SHA is
recorded; they use the current checkout's actual runtime. The second diagnostic
showed picking=1, one global FunctionState callback, zero native readbacks and
one unclaimed frame-signal StringName. No arbitrary settling delay or weakened
predicate was used as a repair.

`reference/` contains PE inspection, disassembly, allocator counts and primary
source links. The exact Godot executable is pinned by SHA; nearest-export names
are not function symbols. The private minidump and native models are excluded.
The old allocator's one outstanding medium value is corroborating evidence;
the dump alone cannot identify its owner or establish earlier mutex destruction.

The initial batched candidate passed the original drawing checks but had a
same-emission reentrancy risk. A per-request bound-callback candidate then failed
five of the new28 assertions because Godot4.6 ignores bound payload values when
comparing signal receivers. Unique owned request receivers fix both cases.
Failed frozen source/tests/logs remain in the session output, with hashes and
scope in the [benchmark](../../docs/benchmarks/selection_readback_shutdown_2026-11-13.json).

`run_existing_regressions.py` reproduces the canonical selection/object-edit
launches and SceneView wrapper with source hashing and actual private receipts.
The full default aggregate and later scopes remain separate work.
