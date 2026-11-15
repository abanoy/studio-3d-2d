# Syncing saved project data and private metadata

On supporting POSIX filesystems, directory Save now flushes declared managed
assets and PNG files, then their directories and every newly created parent up
to the existing directory captured before preparation. It rechecks asset SHA256
while streaming bounded1MiB blocks. Cel pixel verification remains in the Godot
PNG writer. The inventory follows known scene/model/world/effect/audio/reference/
cel and nested-scene records; it never globs unrelated files or follows arbitrary
metadata paths. Managed child links refuse; explicitly chosen linked roots retain
their established behavior.

Private owner/resolved markers, journal manifests/catalogs/previews and lesson
progress use a bounded sync worker after their existing fresh-temporary readback.
It verifies bytes before and after file sync, syncs new parents before promotion
and the containing directory afterward. Hard-linked destinations are replaced
without changing the external inode; linked or unowned temporaries refuse.
The two save paths share one small Godot worker/status adapter. Missing, malformed,
contradictory or nonboolean success cannot be reported as a successful save.
Post-promotion errors keep the fact that a new file was written.

HAS Save also syncs owned externalized sidecars and their new parents, and its
archive directory around promotion. A managed sidecar directory/file that is a
symbolic link refuses before copying outside it. Existing external linked source
assets are read/hashed but are not rewritten. Disposable extraction/request/result
files are not authoritative saved project data and do not acquire this durability
claim.

These operations add synchronous filesystem/Python work. The Python installation
is already required; no package or network service is added. Project/container
schemas, drawing caps and native source bytes remain unchanged. Unsupported
platform/directory-sync paths report false capability flags, and real sync errors
remain failures. Windows directory/payload sync and physical storage behavior need
native testing; software-rendered cloud tests do not certify physical power-loss
survival or hostile filesystem mutation.

```sh
python -m unittest tests.test_metadata_commit tests.test_directory_payloads tests.test_directory_commit
python -m unittest discover -s tests -p 'test_has*.py'
python tests/verify_private_metadata.py --output /absolute/new/result
```

Forty unique private/directory sync cases and58HAS cases pass. They cover file and
parent-directory descriptors, immutable source preservation, unsafe/missing/
changed payloads, sync/replacement/readback faults, real competing workers and
SIGKILL outcomes. The private headless suite passes167checks, including12worker
protocol cases. Drawing-domain232checks and actual Godot concurrency/lost-status
scenarios also pass.

Actual app evidence includes62checks plus16PNG compatibility cases through the
32cel packed save/cold startup/real abrupt recovery/H264-AAC workflow;224nested
adaptive/mask/active-child/packed-linked/recovery checks; all5lesson startup cases
and23writer+11startup autosave checks. Manual HAS, original assets and editable
pixels remain exact. All GUI runs used owned private displays107/108 with Dummy
audio. Native fixtures, hardware/input comfort and Windows are not implied.

STORE-04 remains open for the directory rollback payload-validation audit and
native/physical acceptance. See [scoped sync evidence](benchmarks/save_sync_2026-11-06.json).

The current STORE-04 source review and executed fault/rollback receipt are in
[atomic safety](benchmarks/atomic_safety_current_2026-11-08.json). The bounded
software condition is verified; target Windows and physical storage observations
remain separate. This supersedes the earlier open-status paragraph above without
claiming an unsupported directory flush.
