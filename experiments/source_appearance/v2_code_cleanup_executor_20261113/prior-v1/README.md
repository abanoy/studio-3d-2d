# Four historical v2 copies: bounded cleanup executor preparation

This new output packet prepares cleanup. No deletion, move, process termination,
Git mutation or graphics is performed during preparation or synthetic testing.
The executor defaults to a read-only preflight that writes one new local receipt.
The separate `-Execute` branch remains unrun and root must review, publish and
remotely verify its exact source before considering that branch.

The only possible deletion targets are the frozen plan's 4,308 individual ordinary
code files /33,607,832 bytes across the four exact historical writer/reader source
roots. Their original manifests and raw Git blobs at
`e9cc7cfb20266b4863bde134bcb30457547a343d` must agree exactly. No EOL conversion is
accepted. The plan retains 2,613 files /68,376,831 bytes. All directories, custom
override/harness files, generated/private state and non-code/media/metadata remain.
The executor has one `Remove-Item -LiteralPath` operation, without recursion,
wildcards, force, retry, moving, archiving, uploading or process termination.

`verify-git.py` uses one `git cat-file --batch` read to validate all1,032 distinct
raw objects, ordinary modes, paths, SHA256/lengths and original manifest membership.
Publication verification additionally uses an actual read-only `git ls-remote`
observation of origin/main, local ancestry to that remote tip and exact published
raw packet/gzip/executor/helper blobs. It never fetches, commits or pushes. If a
new remote tip is not locally available, publication verification refuses.

The executor checks exact paths, full nonreparse ancestry to the volume root,
hash/length/nsmtime, per-invocation native directory/file identity and exact whole
file/directory membership. All candidate and retained files are checked before
any removal; all retained files/evidence are checked again after removal. A new or
unlisted path is never selected and causes the exact membership proof to refuse.
Original directory IDs were not recorded in the frozen plan: directory IDs are
pinned by the initial scan and checked throughout that invocation, not represented
as a historical original-ID attestation.

Historical writer private Job/desktop closure is revalidated from preserved
receipts; reader absence remains absence, not closure. Fresh process audits use
command/executable paths plus native CWD and creation-time checks for every
positively owned process and every runtime/shell. WMI timestamps truncate to
microseconds; the native creation must map to the same WMI microsecond, then its
complete100ns tick value is checked inside each retained native process handle.
No historical PID exceptions are reused. An inaccessible live owned/runtime
identity refuses the gate. Other-account non-runtime access limits and arbitrary
open-file handles are explicitly reported; universal nonuse is not asserted.

During Execute, the full current process audit and file/ancestor/hash/stamp checks
repeat before each individual removal. This is intentionally expensive. The
journal flushes intent and completion for each file and records precise audited
PID/creation pairs; the receipt retains initial/failed/last detailed process
snapshots. An interruption can leave partial cleanup; the executor stops without
retrying or broadening and requires independent review before any later action.
Path-based checks and removal do not provide an atomic guarantee against a
hostile simultaneous path/process change. This is scoped cooperative session
cleanup, not a universal filesystem handle lock.

## Read-only preparation command

Run the approved PowerShell7 executable on `execute-sfm-v2-cleanup.ps1` with no
parameters. The same script with `-LibraryOnly` exposes the read-only predicates
for `test-safety.ps1`; that mode rejects `-Execute` and performs no cleanup.
Read-only process inventory may require the approved host context. The preparation
must retain failed receipts; a source-only/Git pass does not waive nonuse.

## Required later execution gates

Root must supply all five concrete values in addition to the explicit `-Execute`:

- `-ExpectedPublishedCheckpoint`: the exact reviewed40-digit commit, actually
  reachable from current remote main.
- `-PublishedPlanGitPrefix`: the checkpoint's directory containing the exact
  `PACKET.json` and `PLAN.json.gz` from the frozen plan packet.
- `-PublishedExecutorGitPrefix`: the checkpoint's directory containing the exact
  `execute-sfm-v2-cleanup.ps1` and `verify-git.py` from this new output packet.
- `-ExpectedExecutorSha256`: independently reviewed SHA256 of the PS source.
- `-ExpectedHelperSha256`: independently reviewed SHA256 of the Git helper.

The immutable plan gates are packet
`847609fa241f70f89c711a93ed0035a8a1fe69cf34bd998b9d418630db1cb70a`, gzip
`c772ec391c36db95b8a016125e41bc1588cdbc14ae542d6a64e66d66136f55a4`, raw
`e65b408acdf63eade874709b6dc37de43b6c244ff3f9fe5fc11cab222c43fa8a`
(7,532,146 bytes after decompression). None of those gates authorizes deletion by
itself. No execution command is run by this preparation task.

For publication, use the compact files listed in `PACKET.json`. Local process
audit receipts and synthetic fixture directories remain in this owned output;
`RESULTS.json` indexes their identities/outcomes without private payloads. The
failed first real dry-run's exact source is retained and hash-matches its receipt.
The pinned native inspector is adapted from the existing reviewed readback
executor, with long literal path support and exact creation-bound process reads.
