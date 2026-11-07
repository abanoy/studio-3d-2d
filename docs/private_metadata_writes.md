# Recovery and lesson metadata writes

Recovery owner/resolved markers, journal manifests/catalogs/previews and lesson
progress now use `atomic_metadata.gd`. The writer checks its owned directory
boundary, refuses linked managed descendants and final/legacy temporary paths,
and writes through a fresh temporary inode. It flushes, reopens and checks byte
length and SHA256 before replacing the destination. Errors preserve the previous
file. Metadata is bounded to 1 MiB, matching existing JSON reader limits; preview
and lesson-context limits remain stricter in their existing callers.

An owned fixture reproduced source truncation in all three former writers when a
fixed `.tmp` path was a symbolic link. They returned success after overwriting
the sentinel. The fixed writers refuse that layout. Existing hard-linked final
or legacy temporary files preserve the external source inode; only an eligible
final directory entry is atomically replaced. Stale ordinary `.tmp` files remain
untouched. A legacy temporary directory still obstructs saving safely.

Recovery checkpoint creation checks its managed session directory before writing
owner/project/history data. Lesson Save checks managed course/session/checkpoint
ancestors before its project writer. Journal commit preflights primary and backup
paths before rotation. Existing process identity protection, retained history,
checksummed fallback and ordinary lesson Continue/Previous behavior remain.

```sh
python tests/verify_private_metadata.py --output /absolute/new/domain-result
python tests/verify_lesson_recovery.py --isolated-display :107 --output /absolute/new/recovery-result
python tests/verify_lesson_autosave.py --isolated-display :107 --output /absolute/new/autosave-result
```

The scoped Linux domain run passes 32 private-write faults, 33 journal, 43 lesson
context and 47 process identity checks. Graphical suites run only on a provisioned
private display: actual abrupt termination, newest/older startup, legacy/invalid/
missing lesson context, Continue/Previous/Fresh, recovery preview, normal save and
H264 export pass. Manual HAS files and included assets remain unchanged. The
metadata fault fixture explicitly skips on Windows; native reparse/locking and
physical power-loss behavior are not certified by these Linux results.

This does not serialize multiple concurrent writers or certify hostile filesystem
mutation between checks and rename. File flush/readback does not establish
physical durability or directory sync. STORE-04 remains partial/open for those
remaining requirements. See [scoped evidence](benchmarks/private_metadata_2026-11-06.json).
