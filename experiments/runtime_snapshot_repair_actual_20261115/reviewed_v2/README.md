# Runtime-only snapshot draft v2

Source-only, unapplied. Root owns application and all real Git/runtime tests. The failed original full run remains FAILED; no result in this packet upgrades it.

This successor preserves the sealed v1 packet at `experiments/world_selection_runtime_snapshot_20261115` (INDEX SHA256 `9208204d96ed27996a1670d1e7728d8cb06ec0c8aa282180ba93ee953b5dd870`). V1's missing optional dependency configuration and all-candidate filesystem resolution are explicitly corrected here; v1 is not rewritten.

`REVIEW.diff` proposes exactly three product file changes. `freeze_source(..., *, runtime_scope=False)` preserves the owner builder's full-source default and historical blob-only mode. Teardown alone opts in. The runtime catalogue retains all `src/tests/tools/data/examples` files, four root entrypoints, optional `dependencies.json`, two notices and the recursive closure of existing quoted `res://` resources/directories.

The identical Windows lexical checks are extracted into `validate_name`. Runtime mode applies them to every included candidate and checks all-name case collisions before reading any working source or Git blob. It resolves filesystem destinations only after dependency selection, for retained names. Default owner mode continues resolving/copying its whole included catalogue. Invalid out-of-scope revision entries remain refused. Atomic target reservation and exact revision blob parsing remain intact.

CPU-only `RuntimeScopeTests` pass **20/0**, retaining all 14 predecessor cases and adding six: optional configuration present/absent, historical config absent despite working presence, exact old config despite working modification, a 6,023-excluded-file destination-resolution spy, and unsafe excluded/case-colliding names refused before either working reads or `cat-file` requests. The seven original real-Git fixture tests are unchanged and were not executed by this agent.

Read-only inspection against the failed snapshot's candidate catalogue selects **1,024 files / 7,574,433 bytes**, rather than 6,023 files. It retains seven transitive web resources and the optional configuration, while excluding all 4,551 unrelated experiment files and 435 documents. This uses existing catalogue names/current unchanged source, not a fresh Git inventory or actual scoped run. `CPU_RESULT.json` records the limits and preservation hashes.

No timeout changed: outer 180 seconds, startup 60, teardown 110. The teardown GDScript/watchdog and all 28 assertions remain byte-for-byte unchanged. The current shared GDScript overlay still follows the historical baseline snapshot, retaining current `--revision` semantics. Generated/missing placeholders and empty `res://` add nothing; arbitrary dynamic paths outside retained trees require a reviewed literal directory/file or support seed.

Reproduce the permitted mocked CPU checks with:

```
python -B experiments/world_selection_runtime_snapshot_v2_20261115/audit_draft.py
```

It writes only experiment evidence and checked disposable fixtures in this experiment, with every Git subprocess response mocked. No engine, parser, CIM or Git process runs. A separate source-only reviewer found no blocker; its suggested zero-`cat-file` assertion was added. After review/application, root should run all **27** snapshot tests and the actual scoped teardown under the original 180-second outer budget, with source preservation and authoritative closure, before restarting a full suite.

`SOURCE_PROVENANCE.json` binds original/draft files; `INDEX.json` binds this packet except itself. Prior v1/attempt1 failure history remains recoverable in its original directory.
