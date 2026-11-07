# Verifying HAS before replacement

Save now reads the completed temporary HAS after flushing and syncing it, before
changing the current project file or its backup. It checks bounded ZIP structure,
exact header/inventory, entry type and sizes, then streams every payload through
SHA256 and CRC verification. Readback retains at most a1MiB input block rather
than expanded drawings or a second full archive. Cancellation remains available
between blocks. Failure leaves the temporary data for diagnosis and preserves
the prior save/backup.

Previously, a damaged completed temporary file could be promoted without checking
it. Three fault cases reproduced that behavior: changed pixels with a recomputed
ZIP CRC, a changed header and truncation. All now refuse before replacement.
A previous archive is also payload-verified before becoming the backup; a ZIP
whose CRCs pass but payload SHA differs cannot displace an existing valid backup.
Project/container versions and the packed/linked workflow are unchanged.

Run the portable fault/compatibility suite:

```sh
python -m unittest discover -s tests -p 'test_has*.py'
```

Fresh48tests pass. In addition to malformed readback and previous-payload cases,
the fault matrix injects ENOSPC during payload writing/sync/backup copying, denies
backup/final replacement, cancels during readback, and actually SIGKILLs an owned
Linux subprocess just before backup and final replacement. The current file and
backup remain intact and readable; completed temporary archives also reopen.
Windows skips the POSIX kill case and needs its own termination/locking checks.
These tests simulate disk-full errors; they do not exhaust the physical disk.

The actual app32-cel automatic load/edit/packed-save/recovery/H264-AAC round trip
also passed after adding new-archive readback, including source/manual preservation,
writer-cache-unavailable startup and real abrupt exit. The subsequent old-backup
SHA guard is covered by the final48Python cases. They are distinct scoped results,
not a whole-platform fault certification.

Readback adds a full sequential verification pass to each new archive and a valid
previous archive. It does not certify storage hardware or power-loss durability.
Directory manifests/PNG write fault coverage, directory-sync guarantees and native
Windows/platform testing remain part of STORE-04's open acceptance work.

Evidence: [save readback and faults](benchmarks/has_save_readback_2026-11-06.json).

The follow-up archive write audit also reproduced original-source truncation via
an existing `.has.backup.tmp` symbolic link. Save now refuses linked final,
backup and legacy temporary destinations before writing. Backup uses a fresh
unique temporary, streams/flushed-syncs its copy, checks SHA256 and atomically
replaces the backup entry. A legacy hard-linked temporary remains untouched.
The selected parent directory is resolved while the final filename is inspected
before following a link; an explicitly selected linked directory stays usable.

Save holds a nonblocking OS advisory lock for the complete pack/backup/replace
operation. A second cooperating writer receives a clear busy refusal before
packing. The empty `.has.lock` sidecar is persistent so two writers cannot lock
different inodes after an unlink/reopen race. The OS releases ownership when the
worker exits or is killed; no stale PID file needs removal. Linked, hard-linked,
nonempty and nonregular lock files refuse without changing their source.
This covers cooperating HAS workers, not directory saves or hostile external
filesystem mutation. POSIX lock/kill cases passed; the Windows lock branch still
needs native validation.

The current portable archive matrix passes53tests, adding linked destinations,
hard-linked legacy backup temporary, corrupted copied-backup readback, overlapping
real writer refusal and successful saves after graceful/SIGKILL lock release.
Existing fault injections now target the streamed backup helper and identify its
unique temporary; old-save/backup/pending-archive assertions remain. The real
32cel app suite also passes62checks plus16PNG compatibility cases through packed save/reopen, actual abrupt
recovery/fresh startup and H264/AAC output. Source assets/manual HAS stay exact.
See [backup and lock evidence](benchmarks/has_save_lock_2026-11-06.json).
