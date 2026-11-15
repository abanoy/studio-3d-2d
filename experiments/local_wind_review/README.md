# Unshipped local-wind experiment

This source-only checkpoint preserves an isolated experiment. The normal app does
not load this directory. Do not overwrite installed Studio or merge it into a
working artist project. Graphical motion, input, capture, native and lifetime
verification remain unrun. The headless checks are not a feature acceptance claim.

Start from a new owned checkout at the exact `base_commit` in `checkpoint.json`.
Copy the `overlay` files into that checkout, preserving their paths and bytes.
Use the approved Godot 4.6 standard and Python runtimes. Run the three scripts
`tests/wind_review_unit.gd`, `tests/wind_review_hooks_unit.gd` and
`tests/wind_review_review_unit.gd` through that checkout's `run.command` with
`headless=True`. Also parse `src/app.gd` with `--check-only`. Recorded results:
51 + 14 + 29 checks, zero failures. The same new 29-check oracle failed21 times
against the preserved earlier prototype, with no engine/parser/leak errors.

The four `wind_review_gpu_*` scripts have only been parsed. Follow the matrix in
`reference/GPU-PLAN.md` before any production port. The saved private wrapper is
a session reproduction aid: recreate its two-level owned output layout, review
its input paths and stage the checksum-bound originals before use. Graphics
always require `run.command` private Windows desktops and a single GPU lease.
Do not treat its old machine paths as permission to modify other directories.

The separate pending-helper integration is described in `reference/PLAN-PHASE2.md`.
Persistent normal Hair & clothes exclusions and native Source jiggle equivalence
are not supplied. Original/private assets and saved projects are not in this tree.

Later first GPU attempt and stronger test overlay: apply
`oracle_strengthening_20261112/tests` over the original overlay before graphics.
Its independent nonempty owned-mesh set, known nonzero excluded recorded pose and
both-simulator continuation checks parse successfully. Runtime9files are unchanged.
The first procedural GPU case then failed fixture adoption (56checks/1failure);
no native/lifecycle/primary jobs ran. Distinct-child preservation is unproven.
See docs/benchmarks/wind_review_first_gpu_2026-11-12.json. Preserve the failure;
diagnose the actual append error before changing the fixture. No graphical
acceptance or production port is established.

The later completed matrix passes830actual private-GPU checks across all six
cases; see docs/benchmarks/wind_review_gpu_matrix_2026-11-12.json. Source-only
`production_port_candidate_20261112` contains the exact830-tested overlay,
retrieval chain, fixture corrections and bounded integration/regression plan.
It remains a candidate: no normal-app port or full canonical result is claimed.
Preserve the earlier56/1failure and all scope limits. Both main runtime EOL
recipes and newer parent-owned QA corrections must survive any actual port.
