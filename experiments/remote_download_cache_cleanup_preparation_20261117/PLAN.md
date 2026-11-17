# Exact public download-cache cleanup — root review only

Preparation reconciled 71 untracked files, 14,151,060 logical bytes, against 1,402 exact published readback records. **Nothing has been deleted. The cleanup entry script has never been invoked.** Root alone may review and execute the single PowerShell script after checking its final sealed SHA and PLAN.json SHA. No additional user question is required for this already authorized disposable-cache scope.

## Authorized targets

- `output/1ce-all-remote-batch-{000,020,...,560}.json`: 29 files, 565 response rows, 5,241,797 cache bytes.
- `output/09fb-all-remote-batch-{000,020,...,820}.json`: 42 files, 837 response rows, 8,909,263 cache bytes.

PLAN.json lists every exact relative filename, size, modification time, SHA256 and decoded member identity. The PowerShell source independently generates these same 71 exact names and refuses any membership/order change. Every deletion target must resolve to an immediate regular file inside the fixed workspace's `output` directory, with no reparse component and no tracked Git path. No enumeration result, wildcard or recursive delete supplies a deletion target.

The separate `output/1ce-progress-memo-remote-blob.json` is a **read-only verification dependency and remains untouched**. The original1ce verifier used this explicit UTF8 fallback for the oversized progress memo's empty contents response. The09fb batch records include their own 12 `fallback_utf8` fields, including empty-file cases. These branches are checked exactly against each published record's method, size, SHA256 and Git blob ID. No fallback or decoded-byte match is invented.

All e8 caches, other output files, source, private data, models, media, tools and review checkouts are outside the deletion scope. No directory is deleted or moved. Actual cleanup reports will be new files in a separate owned `output/remote-cache-cleanup-1ce-09fb-20261117-attemptN` directory, never this preparation folder.

## Published backup proof

The latest verified main HEAD is `e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a`. The complete independent readbacks have exact pinned raw identities:

| Readback commit | Rows | Readback document SHA256 |
| --- | ---: | --- |
|1ce433bd7484e2e1652fafa5a5d2d58b0f0c1329|565|e6c89005e71a05ab7713902b60fb6f24c76049ba5ec2c3f76d4279d0d27998f2|
|09fb70ed86b5a704caba34e60be6b24e12aa68a6|837|5a46fd420b208954375a217ec93f40fa2e0ac3b11a3dc3ffdbff210c92478dda|
|e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a|534|efb5fb94aee5e143deb0cb4dff17141ba1d35c29079694fdc830f92ac5a6157c|

The1ce proof body is itself an exact09fb-published blob, and the09fb proof body is an exacte8-published blob. Local read-only Git object checks verify both embedded proof bodies and the direct commit parents e8→09fb→1ce. The latest534-file independent readback is the explicitly supplied root anchor; this script does no network operation or new publication. It requires current HEAD to remain e8 before preflight and each removal. A later HEAD or changed proof/cache identity refuses the old plan instead of guessing equivalence.

## Execution sequence and evidence

1. Default entry refuses immediately. Executing root supplies `-Execute`, exact `-ExpectedPlanSha256` and exact `-ExpectedScriptSha256`. The script checks its own bytes, plan, fixed workspace and fresh bounded report path before entering the operation. It never delegates deletion to another shell.
2. Create a fresh owned report directory with `EXECUTION_REQUESTED.json`. Validate all proofs, committed proof chain, exact71 target membership, untracked status, stable file identities and every decoded base64/UTF8 record before any deletion. Flush `PREFLIGHT_VERIFIED.json` to disk.
3. For each single admitted filename, recheck HEAD, untracked status, full path/reparse boundary, size, modification time and SHA256. Flush a `predelete-NNN.json` identity record before calling the script's sole `Remove-Item -LiteralPath` statement. Observe absence and flush `deleted-NNN.json` afterward. The predelete record explicitly says it is not an observed deletion.
4. Stop at the first exception or reappearing name. Never retry a changed/recreated path or widen the target scope. `RESULT.json` records completion or partial failure, attempted path, confirmed deletion/absence records and their logical byte count. It separately records whether the last Remove-Item started/returned and whether absence was actually observed; an uncertain attempted-file effect is never reported as no deletion. Recheck the retained proofs/auxiliary and all71 absences for full completion.

The script's only child processes are retained, local read-only Git commands with no shell and a30-second wait. On timeout it may terminate only its own retained Git process object, waits at most another5seconds and retains an exact PID/kill/reap failure record. It does not observe, terminate or otherwise interact with application/full-suite processes. File deletion remains a name-based PowerShell operation after a fresh identity check, not an atomic handle-bound transaction; root must keep these obsolete cache names free of concurrent writers. A process/OS crash can leave the durable per-file journal without a final result. Root must inspect that evidence before preparing any successor attempt; there is no blind resume.

## Validation and handoff

`prepare_plan.py` performed read-only cache/proof/Git checks and wrote only this preparation. It never deletes. Its observation records all71 current targets as untracked and unchanged during preparation. The PowerShell parser reports zero errors, one literal-only removal and zero recursive switches. Synthetic PowerShell tests extract only six named pure helper definitions plus the literal scope generator; they do not invoke or dot-source the cleanup entry, read caches, run Git or delete a file.

The exact command must use the **final** source/plan pins in ROOT_COMMAND.json after peer review. This packet is a concrete reviewable preparation, not an execution receipt. Native/active full-run outputs, original models/artwork and installed tools were not read or changed for it. The earlier automatic review rejection of a review-branch upload is unrelated and is not retried or bypassed here.
