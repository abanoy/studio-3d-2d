# Failed full-run receipt provenance audit — 2026-11-20

The failed run had **53 actual private jobs**, not 1,121: **52 exited normally and one was the expected owned Krita cancellation**. All 53 receipts confirm a private window and child desktop, closed job and desktop, no foreground observation, no desktop switch, no monitor error, positive child PID and a receipt timestamp inside the recorded run. This verifies recorded receipt closure; no fresh OS process or desktop inventory was queried.

Of the 1,180 paths called new by the coordinator, **1,127 are byte-for-byte copies of original receipt files under this worktree's experiments/**. Their 1,068 historical desktop identities plus 59 duplicate paths explain the inflated count. Every copy was joined by its exact suffix after /shipped-source/experiments/ and compared as raw bytes and SHA256 against ROOT/experiments/. Every original hash, size and nanosecond modification time was rechecked unchanged after the audit. There were zero unmatched archive copies and no desktop overlap with the 53 actual jobs.

The product verification remains **FAILED**: revision 0329c4ff9876486e6f437e8c86402308ca5be4d7 exited 1 after 956.8793264 seconds. Its child was reaped. The recorded before/after snapshots contain the same 1,059 functional files, and the before raw Git-blob map equals the committed-source manifest. Wind Review refused `src/physics_recording.gd` at its reviewed-port source gate before its GPU jobs; `gpu_used` is false. No final full-pass report is used here.

## Correct classifier

Inventory genuine private-desktop receipts in **both ROOT/output and ROOT/experiments before launch**, keeping path/hash/size/desktop provenance. A receipt copied later into a frozen source snapshot is inherited evidence only when its original source path and exact bytes match that inventory. A same-desktop/different-byte case is a conflict to inspect. Keep partial genuine receipts in failure auditing; de-duplicate physical current jobs by desktop identity only after their physical fields agree. Copied file timestamps and first appearance beneath output do not establish a new launch.

The companion JSON contains sanitized per-path hashes, all 53 actual receipt flag checks and all 1,127 original/copy byte-identity proofs. Desktop names are represented by SHA256. No raw receipt dictionaries, native arrays, artwork/media, engine runs, process queries or Git queries were added by this audit. Only these two audit outputs were written.
