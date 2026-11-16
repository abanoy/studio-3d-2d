# Reviewed current-manifest successors

Two current test manifests were advanced to the independently reviewed native-leaf integration in `src/physics_editor.gd`. Each changes only that runtime row's raw and LF SHA256 to `e351c0f5e2be18c33793a0ae6234b049095c923b35ca8ec1c6c7aaeb36bb8b6a`, plus an explicit pointer to this packet's `PROVENANCE.json`. The wind manifest retains 16 rows; helper preview retains 25. Their path sets, all 39 other row occurrences, driver code, hash/format/count guards and runtime assertion gates remain unchanged.

Before editing, actual calls to `verify_wind_review.runtime_hashes` and `verify_helper_preview.validate_port` rejected the old manifests at `src/physics_editor.gd`. The refusal sites are `tests/verify_wind_review.py:60` and `tests/verify_helper_preview.py:72`. Both raw and LF historical hashes were `5be5e4ec2b44320abc86997f3994bbc57fa3b4a7047b3565a5686f4b14913471`, so the existing checkout-EOL allowance could not admit the changed code. `PREFLIGHT_BEFORE.json` preserves both actual refusals. After the reviewed successors, those same metadata functions accepted all 41 row occurrences; `PREFLIGHT_AFTER.json` records that narrow result.

`before/` preserves the two complete original manifests byte-for-byte. `after/` preserves exact aliases of the two installed successors. The before/after functional catalogues contain 1,014 files and establish that these were the only two functional-file changes. The provenance links the exact independent source-review hashes. No historical evidence packet was changed, and the earlier review's index remains untouched.

The existing pure-Python helper-driver domain suite subsequently passed **120 checks, zero failures**, with protected test/driver source unchanged and zero subprocess attempts. Its internal fake-project preparation-drift report deliberately has `passed=false`; this is the expected counterfactual refusal exercised by a passing domain control. The exact completed result is `helper-driver-domain-result.json`, joined by `CPU_DOMAIN.json`.

This packet establishes metadata admission and the existing Python driver controls. It does not establish wind/helper engine or graphical acceptance, the new native state/live cases, or a fresh full default PASS. Those actual runtime scopes remain separately executed and pinned. Current default helper preview also requires committed functional `main_source_snapshot` bytes; this change does not enable working-source acceptance or weaken that guard.

New current-manifest SHA256 values:

- Wind: `23b870735c3f829bb442aad66cd42621450c038ff4ea39e1d5a4c29250f2df0b`.
- Helper preview: `ebc7ffc51ca71e848c054b737fd47c69483ba7c9c686f162a880944e527de578`.

No engine, GPU, GUI, process/CIM query, Git operation or native asset access occurred during this successor preparation. Only the explicitly authorized two current manifests and new experiment metadata were written.
