# Phase1 Wind Review: proposed main driver

This is an output-only code proposal. No main/prototype file was edited, no native preparation worker ran, and no Godot/GPU process ran for this task. The driver has not been executed against main. Static and imported CPU validation are recorded separately; neither this proposal nor historical830-check evidence is a main acceptance result.

## Proposed minimal integration

1. Root finishes and publishes its current selection callback/lifecycle repair. Preserve the latest `src/world_selection.gd` and all newer regression fixes. **That file is not in the Wind packet and must not be restored from any old prototype.**
2. Reaudit current main against the published candidate's16 overlay files. Apply only those reviewed runtime/test changes; use the current main versions of all other tests/tools. This proposal never copies `run.py` or an old full Studio tree.
3. Add `proposed/tests/verify_wind_review.py` and `proposed/tests/wind_review_port_files.json` under actual main `tests/`. Append the definitions in `proposed/tests/native_fixture_plans.wind_review.append.py` to the existing `tests/native_fixture_plans.py`; retain its existing catalogue/recording resolvers.
4. Use the proposed shared `wind_review_gpu_common.gd` in place of the packet's common file. `common-adaptation.patch` shows the only changes: two explicit project-root/startup assertions, reporting the actual `res://` root, and assigning cache/layout paths immediately after app construction before yielding. The three GPU case bodies and all830 original assertions remain unchanged. Expected main counts become procedural62, VRM047, VRM147, Back hair49, lifecycle546, primary91: **842 total**, including12 new guards. Unit counts remain51/14/29.
5. Prepare the approved input manifest below. Run headless units, syntax preparation, then the serial six-job matrix on actual main with a released GPU lease. Existing regression/default canonical gates in the packet remain required after the port.

No earlier batch or bound-Callable selection candidate is assumed correct here. Root's runtime testing found that Godot4.6 treats differently bound payloads as duplicate connection identities; root handled that separately with unique request receivers, subsequently reporting published main0f8f7a0. My earlier static review missed that identity rule. This proposed driver freezes the actual current main sources, including the final selection repair, throughout its run.

## Driver contract

- Derives ROOT only from its installed `tests/` path. Imports actual main `run.py` and verifies both `run.ROOT` and every `--path`. Every GPU case additionally reports and asserts `ProjectSettings.globalize_path('res://')` equals main.
- Modes are required: `--mode headless` runs3 units; `--mode prepare` checks main app and all4 GPU scripts without running their bodies; `--mode graphical --lease-confirmed` runs units, preparation and all6 GPU jobs. A non-graphical result cannot satisfy the matrix gate.
- Every invocation reserves a fresh `output/wind-review/<mode>-<time_ns>` directory. No preexisting destination, traversal, symlink/reparse output, old review tree or old recovery tree is accepted. Process logs, engine logs, commands, requests, results, original identities, partial progress and receipts stay in that directory.
- Graphical jobs use actual `run.command` and exact main `tools/private_desktop.py`, with fresh per-case receipts. Exit0, child-desktop confirmation, no foreground child, job/desktop closure, zero assertions/errors/leaks, exact case counts and actual main-root reporting are required. No graphical process runs concurrently; the lease flag acknowledges the coordinator, it does not acquire or invent permission.
- All functional files in src/tests/tools/data/examples plus run.py/project.godot/main.tscn/launch.pyw/dependencies.json are frozen by SHA256/size/ns-mtime and HEAD before/after. This includes the new verifier and existing selection fixes. The16 port files are separately bound to reviewed exact bytes. Optional `--allow-checkout-eol` accepts only the supplied file's exact CRLF-to-LF identity and records both hashes plus that explicit reconstruction; it is not a functional-difference bypass.
- Native inputs and parameter reports use fixed approved SHA256 pins in the fixture resolver. The manifest selects paths only; it cannot supply replacement hashes. Missing or different inputs fail the graphical gate rather than silently skipping native cases. Rebuilt different bytes require a separate provenance review and pin update.
- Back hair uses the unchanged main `tools/secondary_helpers.py` inside the fresh run, retaining ribbon, native joints11/10/9,2 declarations, identical skin/binary/mesh/material/animation/accessor/bufferView data,0changed vertices and actual3regions/1369weighted vertices. These are shared-joint regions, not3independent wind groups.

## Input manifest and normal fixture conventions

Use `tests/native_fixture_root.py` unchanged: default fixture root is actual main `output`, or explicitly set `HYBRID_NATIVE_FIXTURES` to another existing owned prepared-fixture directory. Add `wind-review-inputs.json` there, using the schema in `wind-review-inputs.example.json`. All paths are relative descendants of that fixture root. The optional `--inputs-manifest` must still select a file inside the same root.

Suggested portable layout:

```text
<fixture root>/wind-review-inputs.json
<fixture root>/wind-native/vrm0/{scene.glb,parameters.json}
<fixture root>/wind-native/vrm1/{scene.glb,parameters.json}
<fixture root>/wind-native/ribbon/{scene.glb,parameters.json,helpers.json}
```

`observed-input-identities.json` records this session's read-only mappings from known approved bundles to those roles. Those old paths are evidence only. They are not driver defaults, future prerequisites, installed Studio caches, or automatically searched sources. No model/audio/image payload is included in this proposal.

## Explicit commands after main integration

```powershell
$env:HYBRID_NATIVE_FIXTURES='C:\path\to\owned\prepared-fixtures'
python -B -u tests/verify_wind_review.py --mode headless
python -B -u tests/verify_wind_review.py --mode prepare
# Only when the coordinator has released the single GPU lease:
python -B -u tests/verify_wind_review.py --mode graphical --lease-confirmed
```

For canonical integration, invoke the explicit graphical mode serially from `tests/verify.py` with a timeout covering all6 jobs (for example2600s). Read the final `WIND_REVIEW_MAIN ` JSON line, then load its fresh `verification` path and require `mode=='graphical'`, `gpu_used==true`, `passed==true`, all6 ordered cases, and all source/input/receipt fields. Do not read a stale fixed report or add historical830 to another run's totals. A separate pure-headless invocation is useful for triage, but the graphical mode already includes units/preparation; repeating it is unnecessary absent a new change/failure.

## Limits retained

Phase1 previews already declared groups in one temporary candidate. Pending single/batch helper drafts before Apply, permanent Include in setup/exclusions, native SFM jiggle/flex/assembly equivalence and the owner's broader SFM assets remain separate. Lifecycle's recovery sink is an in-memory probe of real queued GPU readback admission/pixels/counters; it does not prove persisted preview-worker output. Recording exercises actual Local/World start/cancel ownership, not a newly encoded movie. PNG export does run. Physical wind, artist fidelity, tablet/audio devices and clean offline installation remain external acceptance gates.

The proposed common startup guard fails if Windows reuses a PID whose old test workspace file still exists; it does not delete or overwrite that old file. Cache/layout overrides are assigned before yielding, and recovery/recent/display overrides are assigned before app entry. This avoids adding a new production preference hook merely for the verifier. Exact source fixture replay remains prerequisite to a pass.

## Actual CPU-only validation

`cpu-tests.json` / `cpu-tests.log` record **15 imported-code tests,0failures,0errors,0skips**. The proposed driver and appended resolver were copied into an output-only shadow and imported there, rather than reimplementing their predicates in tests. Actual approved GLB/parameter identities were read for the positive resolver case; no assets were copied into the shadow.

The controls exercise actual runner-root binding and rejection, mandatory mode/lease, refusal of reused output/traversal/reparse metadata, reviewed runtime mutation, explicit EOL-only reconstruction, fixed native pins that a manifest cannot override, parameter/hash/size/ns-mtime/manifest freshness, command --path/private-launcher checks, source/HEAD drift and incomplete-matrix rejection. The actual execute_gpu wrapper was also exercised through synthetic external-process/fixture-preparation boundaries: exact6job order passes, while15 count/assertion/project/startup/receipt/exit/engine/missing-file failures stop after the first job. All synthetic process fixtures are labelled CPU-only; no GPU predicate or native worker ran.

The first expanded CPU trial placed its synthetic case folder outside the allowed `output/wind-review` family. The real guard correctly rejected it. Only that test-fixture location was corrected; the driver guard was retained. The failed JSON/log remain as `cpu-tests-expanded-fixture-failure.*`.

`validation.json` additionally records Python AST checks,16reviewed file bindings,44published/retained packet files matching, exact ribbon-request identity and original prepared metadata preservation. GDScript parsing is explicitly **unrun**. `validate_proposal.py` / `test_proposed_driver_cpu.py` are output-only development aids; their local positive-input observation is not a production cache fallback. For publication retain the compact handoff files indexed in FILE_INDEX.json, not generated `validation/cpu-shadow-*` copies or synthetic reports. Actual main integration must use the normal manifest layout above and rerun real headless/parse/GPU gates.
