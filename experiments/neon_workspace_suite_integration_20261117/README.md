# Standard neon workspace verification integration — source packet

This packet prepares one new production verification group. The audit agent has **not installed it, run Godot, queried CIM/Git or changed a functional checkout**. The focused experiment results remain separate from future standard-suite evidence. A production wrapper result must come from a new actual run; this packet cannot backfill a pass.

## Production destinations

Copy only these five source files from this packet's `tests/` folder to the corresponding standard `tests/` destinations:

- `verify_neon_workspace.py`
- `neon_behavior_regression.gd`
- `neon_inset_scene_regression.gd`
- `neon_compact_timeline_reveal_smoke.gd`
- `neon_rail_placement_smoke.gd`

`tests/verify.proposed.py` is the proposed replacement for **`tests/verify.py`**, not an additional production test file. Alternatively apply `verify_insertion.patch` to the pinned original. `VERIFY_INSERTION_PROOF.json` records the input/proposed hashes, exact insertion inverse and unchanged AST of the original 36 core entries. The insertion adds only `results['neon_workspace']`, taking the previously observed complete result-key count from 157 to 158; the original core 36 are unchanged. It calls the new wrapper near `workspace_controls` with `--lease-confirmed --parse-scripts`, requires a fresh passing standard report and exact counts, then keeps every original verifier statement intact.

Do not copy `cpu_tests/`, proof files or `superseded-v2/` into production. They are preparation evidence. Preserve the packet bytes when staging; any deliberate line-ending conversion is a separate working-source derivative that needs its own hash record.

## Aliases and predicates

`ALIASES_PROOF.json` binds the four standard aliases to their sealed focused sources. Inset, compact and rail are byte-identical aliases. Behavior uses the final refresh-boundary v3 source (`48d778041385988d0ac306ebbcf7440ae9e03ff35660871d0bed4e3f2a2cfcf9`); only its `SCRIPT` resource constant changes to `res://tests/neon_behavior_regression.gd`. The exact inverse restores every original byte, including all 32 named predicates. The earlier v2 alias and proof are preserved under `superseded-v2/` and are not active inputs.

Expected complete counts are **inset 12,384 (576 configurations), behavior 32, compact 14, rail 45**, for a total of **12,475**. These match the independently derived static assertion counts and the parent's reported focused actual results. They remain required gates for each fresh production run; previous focused passes are not reused as production results.

## Wrapper behavior

`python tests/verify_neon_workspace.py --lease-confirmed --parse-scripts`:

1. Requires explicit lease attestation before any graphical command or output staging. Actual execution is Windows-only. `--lease-confirmed` means the caller has already obtained the exclusive graphics/runtime lease and closed prior owned jobs. The wrapper does not pretend to perform an authoritative host inventory.
2. Records actual functional membership, SHA256, size and nanosecond mtime before and after the attempt, including all files under `src/tests/tools/data/examples` except Python caches, plus the four root functional files. Any membership, content, size or timestamp change rejects the run. Attempt/source evidence remains even after a failed case.
3. Optionally parses **all four** aliases with standard `run.command`, headless `--check-only`, and bounded processes. `--parse-only` parses all four and produces a clearly labeled parse-only report; it cannot produce the passing production suite report and needs no graphics lease.
4. Runs the inset script headless, then behavior, compact and rail sequentially through standard `run.command`. Graphical commands must be actual private-desktop commands; the wrapper adds bounded time and 4,096 MiB memory limits. Every process has recorded command, PID, exit, duration and explicit wait/reap evidence.
5. Creates a fresh behavior job only after explicit lease confirmation. The job's exact fresh folder, actual alias SHA and current app SHA are pinned, with a three-minute expiry. The required `root_closed_all` field is explicitly labeled caller attestation. The script independently checks those pins, expiry and fresh output path.
6. Requires fresh result files and exact counts with zero failures. Behavior has no final JSON marker: the wrapper requires all 32 unique named PASS lines to match the fresh named-result set, plus exact app/script hashes, complete assertions and `refresh_preserved_faded_context=true`. Inset, compact and rail require exactly one final marker matching the result JSON. Insets additionally retain projection/ray limits; compact retains small-viewport and first/middle/last actual routed-selection gates.
7. Reads the three **physical** private receipts. Each must be fresh, exit zero, confirm private placement, observe no foreground/desktop-switch request, and report successful job and desktop closure without monitor/error/cancellation fields. This checks actual launcher cleanup; the parent still owns authoritative host closure and runtime release.

Only after all cases and source/physical-closure gates pass does the wrapper write the standard `output/neon-workspace-verification.json` and its fresh per-attempt `verification.json`. Before/after source maps remain in the owned attempt folder; the standard result holds their paths and hashes rather than duplicating the maps. Failed/partial attempts never replace the passing entry point. All fixtures are generated or included synthetic assets; no owner model is required by this new group.

## CPU verification

`cpu_tests/test_verify_neon_workspace.py` tests the wrapper with synthetic reports, mock processes and temporary files only. It covers complete counts, all named behavior lines and refresh boundary, exact markers, numeric bounds, real-input coverage fields, lease/job/path pins, stale/error/partial physical receipts, source membership/mtime changes, early refusal without a lease, timeout preservation and explicit process reap. It does not run an engine.

The first CPU attempt had one synthetic positive-fixture error: an immediately written NTFS mtime could precede a `time.time_ns()` sample taken immediately before the write. `CPU_ATTEMPT1.json` preserves it. The positive fixture now uses the actual observed mtime as its inclusive lower boundary; the independent stale-mtime negative case remains. The production freshness gate did not change. The final 20-method CPU run passed. Python sources were AST-parsed; GD runtime parsing/execution belongs to the parent's next actual production run.
