# Runtime-only teardown snapshot draft

Status: source-only, unapplied. The parent owns review, application, real Git-fixture tests and any runtime execution. This packet launches no engine, parser, process inventory or Git command.

The failed full run remains FAILED. Its teardown child subsequently finished all 28 assertions and closed with exit 0. The observed outer 180-second timeout included freezing 6,023 source files and rehashing the entire snapshot after startup. That catalogue included 4,551 experiment files and 436 document files. This supports a snapshot setup/provenance bottleneck; it is not a new full-suite pass or a proof excluding every possible timing cause.

`REVIEW.diff` changes only three proposed product files:

- `tools/build_owner_review_snapshot.py`: keyword-only `runtime_scope=False` preserves existing owner-builder and full revision behavior. Opt-in keeps `src/tests/tools/data/examples`, the four application entrypoints, two notice files, and the recursive closure of existing quoted `res://` resources in the original validated candidate catalogue. Existing directory literals include existing descendants. Output/cache exclusions, Windows path checks, case collision refusal, immutable revision blobs and atomic destination reservation remain enforced.
- `tests/verify_world_selection_teardown.py`: opts in and records the scope. The current shared teardown GDScript is still overlaid after the historical baseline is frozen. The old-revision counterfactual therefore retains its current common-test semantics.
- `tests/test_owner_review_snapshot.py`: preserves the seven existing Git-fixture tests and adds 14 mocked-Git source-boundary/revision cases. The canonical verifier already invokes this file, so it needs no new test hook.

`CPU_RESULT.json` records 14/0 mocked tests and exact preservation of the five inspected original files. Dependency inspection against the failed snapshot's existing catalogue selects 1,023 files / 7,571,891 bytes, including seven external web resource files and both notices. It excludes all 4,551 unrelated experiment files and 435 unrelated documents. This is a read-only catalogue/source calculation, not a fresh Git snapshot or runtime measurement.

The draft does not alter the outer 180-second budget, startup 60-second budget, teardown 110-second budget, watchdog, teardown GDScript or its 28 assertions. References absent from the candidate catalogue, format placeholders, empty `res://` and excluded generated output paths add no source. Dynamic paths outside the retained trees require an explicit existing directory/file literal or a separately reviewed support seed; this packet does not pretend to statically infer arbitrary executable path construction.

Reproduce the permitted CPU draft check with the approved Python and `-B`:

```
python -B experiments/world_selection_runtime_snapshot_20261115/audit_draft.py
```

It runs only the `RuntimeScopeTests` class against checked disposable fixture directories inside this experiment. Git subprocess responses are mocked. The seven existing Git-fixture tests were not run by this agent. Root should review/apply the three draft files, run all 21 snapshot tests, then run the actual scoped teardown under the unchanged outer timeout and preservation/closure gates before retrying a full suite.

`attempt1` preserves the initial draft and its two revision-test failures. The generator's CRLF-sensitive substitution left an unused blob batch in that draft; newline normalization corrected the generator. The final draft passes both revision cases without dropping assertions or weakening blob/path checks. No production file was changed during either attempt.

`SOURCE_PROVENANCE.json` binds original and draft hashes. `INDEX.json` binds this packet except itself. The draft is ready for parent review; it is not evidence of an actual scoped GPU run or a completed full suite.
