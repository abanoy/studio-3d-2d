# Closing an editor with a pending scene pick

Closing Studio immediately after requesting a scene selection could crash the
pinned Windows engine during shutdown. The drawing-selection writer printed
35 passing checks, then exited `0xC0000005`; its cold reader therefore never ran.
The failed suffix, unchanged replay, diagnostic runs and private dump are retained.
The dump contains private process memory and is not uploaded.

The scene picker directly awaited the global `frame_post_draw` signal. Its
suspended camera snapshot contained one `Transform3D`. A diagnostic confirmed
one pending pick and one coroutine callback at close, with no renderer readback,
physics simulation, project worker or selection-reveal callback outstanding.
Offline analysis of the exact engine independently found one outstanding medium
Variant allocation, used by Basis/Transform3D. Its allocator attempted to report
that retained allocation during static teardown and crashed entering the global
error mutex. The mutex's earlier destruction history is not established by this
limited dump; no engine or installed-tool replacement was needed.

Each pick now has a distinct request receiver owned by the selection Node.
Completion keeps that receiver alive locally, uses a weak link to its owner,
and preserves the existing serial, camera/view and interaction guards. Owner
exit disconnects and releases all remaining requests. Separate receivers also
preserve picks requested by an earlier listener during a draw: those requests
wait until the next draw. Bound arguments alone do not distinguish connections
in this pinned engine, as the [exact Callable implementation](https://raw.githubusercontent.com/godotengine/godot/89cea1439/core/variant/callable_bind.cpp)
confirms. The rejected bound-callback candidate and its five failures remain recorded.

## Actual verification

- New focused regression: **28 checks, zero failures**, four application
  lifetimes covering valid selection, multiple requests, cancellation, New,
  reentrant draw listeners, queued close, immediate Focus/Setup close and detach.
  Normal startup and test children exit zero with no warnings/leaks; private
  desktops, unchanged frozen source and callback/Node release checks pass.
- Exact previous `2904f3f` source with the same focused test: four assertions
  print as passing, but the child leaks its frame wait and exits
  `3221225477`. The wrapper correctly rejects that run.
- Final production source: unchanged world selection **41/0**, world editing
  **41/0**, SceneView **12,830 unit + 102 application checks**, and drawing
  selection **12 unit + 35 writer + 3 cold-reader checks** pass. Existing native
  MMD/Source/SFM selection and editing, saved pixels, independent raster
  reference and the drawing movie's 48-frame 1080p24 H.264 checks remain intact.

The first focused attempt caught type-inference errors in the new test harness;
only explicit WeakRef declarations changed. An earlier root regression launch
incorrectly added `--demo-room` to an empty-world test; its five failures are
retained separately. The corrected launch uses the canonical arguments. Neither
failed attempt is relabelled as a pass.

Run `python tests/verify_world_selection_teardown.py` for current working source.
Run `python tests/verify_world_selection_teardown.py --revision 2904f3f --case focus-free`
for the committed counterfactual. Both freeze source in fresh owned folders and
use private desktops; the original test is shared. The new wrapper is registered
in `tests/verify.py`.

The preceding suffix passed six wrappers, then stopped at drawing selection.
Nine later wrappers and the complete default aggregate still need fresh runs.
This scoped fix does not close native fidelity, artist/device or clean-install
acceptance. The ledger remains 55/62 accepted and 52/54 implemented.

See [compact evidence](benchmarks/selection_readback_shutdown_2026-11-13.json)
and `experiments/selection_readback_shutdown_20261113` for exact-binary research,
source diagnostics and retained limitations. Do not delete private review work,
native bundles, recovery, originals or the crash dump as disposable test output.
