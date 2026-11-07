# Guarded directory manifest promotion

Directory Save now captures the starting manifest fingerprint before preparing
assets and cels. A small local Python worker holds a nonblocking OS lock while
checking that fingerprint and promoting the verified manifest. If another save
committed meanwhile, this candidate refuses and preserves the other generation.
A busy writer can be retried once the first finishes. The app stays dirty on
refusal. Preparation can leave unused owned files for diagnosis; it does not
replace the committed manifest.

Ordinary revision PNG directories include process/unique identity so independent
preparations cannot accidentally share ordinal filenames. Content-addressed
assets/cels retain their existing immutable identities. Child sequence staging
returns metadata without committing the parent's manifest; only its complete
root candidate reaches promotion. Project schemas and resource caps are unchanged.

The worker reads the bounded prepared JSON and verifies its supplied SHA before
and after syncing its file. It copies an eligible previous manifest into a fresh
backup temporary, flushes/syncs and reads it back before replacement. It syncs the
project directory around manifest promotion on supporting POSIX filesystems.
Existing malformed-primary repair retains the prior good backup; linked or
blocked destinations and hard-linked candidate files refuse. A hard-linked backup
entry is replaced without modifying its external source inode.

The empty persistent `project.json.lock` inode uses the existing shared OS lock
implementation; the OS releases it on normal exit or termination. It is not a
stale PID file to delete. Windows keeps its existing save behavior when directory
sync is unavailable; the native lock/termination branch still requires Windows
verification. Unsupported POSIX directory sync is reported in the worker result.
An actual I/O failure after promotion reports that the new generation was written.
A worker lost without a status makes the app ask to inspect the saved project;
it does not falsely promise the old manifest remained.

This guard excludes cooperating manifest promotions. It does not lock the user's
whole editing session or certify hostile external filesystem mutation. Payload
PNG/asset fsync, all newly created parent directories, private metadata directory
sync and physical power-loss testing remain open. These metadata sync results
must not be called complete directory/power-loss durability. The already required
local Python installation is used; no network service or new package is needed.

```sh
python -m unittest tests.test_directory_commit
python tests/verify_directory_commit.py --output /absolute/new/result
```

Twenty owned Python cases pass, including two real prepared writers with one
winner, stale generation, links/hard links, sync/readback/replacement faults,
whole-valued JSON schema compatibility, actual SIGKILL before backup/primary and
after promotion, and retry after OS lock release. Actual headless Godot Save
refuses a held lock, retries successfully, preserves a competing real worker's
frame7 against its stale frame3, and reports lost status while loading committed
frame9. Native/hardware acceptance is not implied.

Drawing-domain and private metadata regressions, the automatic32cel packed save/
cold recovery/H264-AAC workflow and nested adaptive/mask/active-child save/recovery
workflows pass on owned private cloud displays. See
[scoped evidence](benchmarks/directory_commit_2026-11-06.json).
