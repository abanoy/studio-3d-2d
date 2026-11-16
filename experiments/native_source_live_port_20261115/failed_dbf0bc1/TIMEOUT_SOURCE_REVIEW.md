# Failed full: wrapper budget and scoped snapshot proposal

The canonical run at `dbf0bc1145f74b5bbff814ec6a417ccd23ce0885` remains **FAILED**, suite exit1, at `2026-11-16T02:43:59.4000841Z`. All 36 initial core groups passed. The outer `tests/verify.py:165` call exhausted its 180-second budget for `verify_world_selection_teardown.py`. The current 1,014 functional source files and HEAD remained unchanged.

Actual metadata from `output/world-selection-teardown/1794796856711017300` distinguishes the stages:

| Event | Actual UTC |
| --- | --- |
| Snapshot/provenance completed | `02:42:06.9819700` |
| Normal-startup command saved | `02:42:07.3205230` |
| Normal-startup result saved, home/simple/empty true | `02:42:18.0764788` |
| Normal-startup log saved | `02:42:18.5343766` |
| Actual teardown command saved | `02:43:55.6889675` |
| Outer full state failed | `02:43:59.4000841` |
| Actual teardown result:28checks/0fail, all four cases | `02:44:06.8044379` |
| Actual teardown private job/desktop closed, exit0 | `02:44:07.2070420` |
| Separate root host closure observed | `02:47:42.3887530` |

There was about 70 seconds of snapshot preparation before startup and about 97 seconds between startup completion and the actual teardown command. The child itself reported 11.324 seconds. The wrapper's `execute()` rehashes every frozen snapshot file after startup before returning; this is on the outer 180-second budget. The current snapshot contains 6,023 source/archive files, versus 4,842 in the preceding successful full. The builder's default working mode includes tracked and untracked files outside its excluded top-level generated directories, so growing experiment archives and newly prepared untracked metadata become copy/hash work even while the main functional source set stays frozen.

This evidence locates the budget exhaustion primarily in snapshot/setup verification. It does not establish an actual GPU-pick hang or a particular OS/storage/antivirus cause. The late child passed all unchanged teardown checks. Because its parent verifier was terminated by the outer timeout before collecting the result, its final `process.log`/completed wrapper verification/latest pointer were not written. The stale prior `world-selection-teardown-latest.json` must not substitute for them. The late result cannot upgrade the full run.

The host proof's `no_process_killed=true` describes that observational helper/root action. Python's `subprocess.run` timeout path can automatically terminate its direct verifier wrapper; that is a source/trace inference, and the wrapper PID was not captured. Child71828 finished normally. No claim that no runtime process anywhere was terminated is made.

## Minimal reviewed fix

Add an explicit opt-in `scope='functional_runtime'` to `tools.build_owner_review_snapshot.freeze_source`, preserving its default full-archive behavior and its existing positional `root,target,revision` contract. Only automated World Selection Teardown opts in initially. Keep the current 180-second outer, 60-second startup, 110-second process and 90-second in-engine watchdog limits, and preserve all 28 assertions. Do not silently switch other owner-review or counterfactual consumers.

The selected runtime scope is `src`, `tests`, `tools`, `data`, `examples`, plus `main.tscn`, `project.godot`, `run.py`, `launch.pyw`, and `dependencies.json` when present. The current selection has **1,015 files**: the existing 1,014 functional catalogue plus dependency configuration. Apply this path filter before copying/hashing files and before reading Git blobs. Exclude experiment archives, docs and unrelated untracked metadata from this opt-in scope. Preserve the existing whole-tree path safety, case-collision checks, fresh destination reservation, bytecode/cache exclusion and exact hashes for every selected file.

`RESOURCE_SCOPE_AUDIT.json` records a static source scan of all current `src/*.gd` files plus the actual teardown/startup entry scripts, scene and project configuration. All **221 existing literal file resources** are inside the proposed scope; `examples/tutorials` is an existing covered directory. Generated `res://output/*` paths remain fresh runtime artifacts. The dynamic prefixes are `res://` itself and `res://tools/`; the latter's workers are inside the selected tools tree. UI icons/gradients are generated SVG in `src/studio_theme.gd`, and selection shaders are under `src`. No external assets/icons/fonts/addons/docs/experiments resource directory was found required by this current entry chain. This static audit is not a blanket claim about arbitrary imported assets or every historical revision.

For `revision=None`, preserve selected current working bytes and record the scope explicitly in provenance. For an explicit old revision, keep the exact Git-tree/blob path, filtering the selected revision's paths without reading working runtime files. The current shared teardown test remains the deliberate existing overlay, and its source hash must remain visible. Optional old top-level files may be absent where the original builder allowed that. Known supported old revisions need their resource coverage checked; refuse unsupported out-of-scope dependencies rather than silently dropping them or claiming universal historical compatibility.

Useful CPU controls: default archive still includes a self-authored experiment sentinel; opt-in runtime excludes it; selected files/entrypoints/dependency bytes remain exact; malformed/case-colliding destinations still refuse; explicit old revision ignores modified/untracked working runtime files; the current shared-test overlay remains exact. Then, only after the failed lease is closed, root can run a fresh scoped current teardown retry with phase timings and actual private receipts. Its result is a scoped retry, not a replacement PASS for the failed full. A later coherent full requires the new reviewed frozen revision.

## Failure lease closure preparation

`PARTIAL_RECEIPT_AUDIT.json` verifies **46 unique actual private receipts, all exit0 and private/job/desktop closed**: 42 direct checkout receipts plus two command-derived teardown receipts and two current completed native-readback receipts. No current registered Krita cancellation occurred in this executed prefix. The late child receipt is explicitly 7.8069579 seconds after the failed suite finish and is included through the measured host-closure window, not disguised as an in-suite completion. No final 157-group report was read or used.

`release_failed_graphics.ps1` is **UNEXECUTED**, syntax-only parsed. It binds the exact failed state, neutral terminal context, current source/HEAD, raw host proof and this receipt audit; rechecks physical/retained receipt bytes and all private closure flags; then requires fresh absence of checkout-owned native commands, Python/private helpers and known wrapper coordinators. It has no kill or force option and preserves the owner's separate review. It writes the distinct `graphics-lease-closed-after-failure.json` with `full_suite_passed=false`. Root must independently review and execute it. The existing PASS-only helpers remain unchanged.

The owner hair-selection check is deferred with no observed manual result. No new manual check was requested by this review. No engine, process/CIM query, Git operation or functional edit was performed by this reviewer during the failure audit.
