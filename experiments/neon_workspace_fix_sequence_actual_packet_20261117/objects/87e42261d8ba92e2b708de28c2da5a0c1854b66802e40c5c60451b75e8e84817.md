# Root terminal audit for the f387 Windows run

Source-only preparation for `windows-neon-f387d0e-20261117T012410` in the Neon review checkout, commit `f387d0e9ddfb099140c0699d9f7ed430f5d7b949`. Preparation read only the frozen verifier/source and the run's already written source-before, launch and birth metadata. It did not read active state, source-after, final reports or logs, or invoke engines, CIM or Git.

After the root has independently observed terminal completion, execute the pinned helper once:

```powershell
& 'C:\Program Files\Python313\python.exe' -B 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\experiments\neon_f387_terminal_20261117\close_terminal.py' --root-terminal-confirmed --release-closed
```

The helper gates the exact coordinator and Python births, actual nested birth and full-launch schemas, approved runner, all 1028 before/after/current source names and hashes, and every sealed payload before querying process state. The observer checks exact identities rather than requiring reused numeric PIDs to disappear. It also requires no matching native runtime, Python helper or canonical coordinator in either main or review scope. It retains and reaps the observer process. It contains no process-termination call; a timeout never releases the lease.

A PASS requires this run's fresh complete final report, an exact normalized canonical-log suffix, 158 named groups, 36 successful core groups and 21 required movies. The native MMD check and both posed movies remain required. Every old result gate is retained byte-for-byte in `legacy_result_gates.py`; the only registry addition is the approved Neon group with its exact 12475 checks and source/private-closure flags. `SOURCE_DERIVATION.json` proves that deleting that ten-statement group from the current verifier yields the old verifier AST exactly.

A failed run never reads `output/verification.json` or treats an older full report as current. Its record remains a closed failed partial run, with actual suite exit and discovered nonzero physical jobs recorded. Unknown wrapper/monitor/desktop errors refuse release. Only the fresh report-registered, source-supported Krita cancellation may use exit 2 with its cancellation error. An early failure before that report exists does not invent a cancellation or require unrun groups.

Physical jobs are discovered from fresh root receipts and actual phase references, including helper-owned paths. Inline receipts must exactly match physical receipts. Identical copies of one desktop/child receipt count once; conflicting copies refuse admission. Counts are derived from this run, with no assumed historical job total. All placement, foreground and closure flags remain strict. Phase documents, receipts and terminal sources are checked before the first audit write and preserved byte-for-byte in the private audit output before a future run can overwrite them.

The helper writes `run/terminal-audit-attempt1` and, after a second fresh host/source check, `run/graphics-lease-closed.json`. The private audit includes raw consulted phase documents and the canonical log; do not publish that directory wholesale. A later compact archive must select safe scalar/source/receipt evidence separately. Existing files are never overwritten. If admission fails after creating partial audit output, retain it and prepare a separately reviewed successor attempt.

Seventeen synthetic CPU test methods passed both the preparer's run and an independent source peer's rerun. Their checks cover terminal schemas, type substitutions, source/birth mismatches, failed-run report exclusion, named group/native/movie gates, placement errors, cancellation registration, receipt-copy ownership and pre-write phase pin ordering. No host observer or native test was executed by the preparer or peer. `CPU_PREPARATION_REFUSAL1.json` retains an earlier test-fixture typo and exact CPU failure output; the fixture was corrected to the existing registry's `posed_model_video_0` key without changing any acceptance gate.
