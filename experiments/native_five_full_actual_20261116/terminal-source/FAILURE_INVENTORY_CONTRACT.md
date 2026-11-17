# Future actual failed-run inventory contract

This is a schema description, not an inventory or a failure observation. Root must
assemble/review actual current metadata only if a failure occurs. The helper
requires the following fields:

- `format`: `has_current_failed_full_private_receipt_audit_1`;
  `root_reviewed_current_run:true`, `full_suite_passed:false`,
  `final_full_report_used:false`, exact source_commit and absolute run_directory.
- `state_sha256`, `host_proof_sha256`, `source_before_sha256`,
  `source_after_sha256`, and observation_window_end_utc exactly equal to the fresh
  authoritative host observation. The source hashes are pinned in context.ps1.
- Actual `physical_receipts`, `unique_desktops`, `normal_exit0` and
  `registered_cancel_exit2` counts; all derive from rows, never a historical total.
- `rows`: exact source_path/source_sha256, complete receipt object,
  after_failed_state_finish boolean and absolute preserved_raw_copy under owned
  output. All private flags, timestamps, hashes and copied bytes are rechecked.
- `late_receipts`: a list, possibly empty, of exact owned-output path, SHA256 and
  child_pid for every receipt actually written after terminal failure and before
  fresh host observation. Extra/omitted/non-late pins refuse.
- `registered_cancellations`: a list, possibly empty, of path, SHA256,
  registration=`krita_import_cancel` and phase_report_sha256. Only the current
  source assertion and fresh output/krita-import-verification.json can register
  the exact cancelled receipt. Exit2 also requires cancelled=true, the exact
  Owned converter cancelled error, no monitor error, all private closure flags.

The partial inventory completeness audit is a separate root responsibility;
this helper revalidates its exact observed rows and scope, not unseen phases.
Missing run/source/host fields, unknown cancellation, an unclosed process or
source drift retains the lease and requires a separately reviewed successor.
