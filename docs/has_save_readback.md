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
