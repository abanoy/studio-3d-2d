# Native selection waits for the displayed layout

The full default run at `eb7c069` regenerated its native fixtures, then failed
the MMD selection step. Its947functional hashes and revision stayed unchanged.
The subsequent pose-tree error and watchdog were consequences of that failed
selection. The failed full run and an earlier launcher-only failure are retained;
neither is an aggregate pass.

An output-only diagnostic reproduced the original failure without changing the
application. The Miku model was visible, the target pixel had the expected ID,
the request serial matched, and playback/export/navigation were inactive. The
test deselected in Pose mode and immediately synthesized its next click. Its
captured canvas extent was581.3333×327; the next rendered view was595.5555×335
after the inspector changed layout. The existing size guard correctly rejected
the stale request.

The native test now uses the same frame/presentation settling helper as its
generic fixture after deselection, before clicking the displayed layout. All
original41selection/deformation/material/source predicates and production
resize/projection rejection remain intact. The fresh MMD/GMod/SFM fixture replay
passes41/0 with a clean private-desktop exit and zero final-pixel differences.
No production code, picker tolerance or native fixture was changed by this fix.

The first full-suite launcher used an older PowerShell host that could not load
Get-FileHash and stopped before any test. The same unchanged coordinator then ran
successfully under this session's existing PowerShell7.6.9 until the actual
selection failure above. Use that known working host for the next fresh full run.

See [compact evidence](benchmarks/native_selection_displayed_layout_2026-11-13.json)
and the source diagnostics in `experiments/selection_native_layout_20261113`.
Keep raw model fixtures and process logs private. The complete default suite
still needs a new stable-source run; scoped checks do not close it.
