# Exact publication-copy cleanup plan — no deletion

This is a distinct, nonrecursive **plan only**. It proposes 88 literal files,
498,427 bytes, solely from three task-owned `publication-candidate` folders.
Each source copy is byte-identical to its corresponding committed experiments
file in `12071fe182a17d17e2a1547c7dbb97f6aa4dd160`.

| Task-owned publication-copy root under `output` | Eligible files | Eligible bytes | Logs retained |
| --- | ---: | ---: | ---: |
| `has-snapshot-ordering-candidate-20261113/publication-candidate` | 32 | 154,728 | 8 |
| `source_currentdir_race_20261113/publication-candidate` | 10 | 29,479 | 2 |
| `sfm-static-choice-main-candidate-20261113/publication-candidate` | 46 | 314,220 | 8 |
| **Total** | **88** | **498,427** | **18** |

The 18 excluded `.log`/`.log.gz` copies total 53,593 bytes and stay retained
conservatively even though their Git backups also match. All raw run folders,
source working overlays, live/frozen project copies, fixtures, `.godot` caches,
native originals/stages, installed runtimes, review/recovery folders and the
upcoming review coordinator are outside this plan. No directory is a cleanup
target. The old SFM cleanup executor and its unresolved owner list were neither
read nor reused.

## Exact evidence

`PLAN.json` contains one explicit source/backup pair per eligible file: absolute
source path, repository-relative committed backup, byte count, SHA256, Git blob
ID, mode, file identities and nanosecond modification times. It separately lists
all 18 retained log pairs with their reason. No glob or inferred directory tree
is a future deletion authority.

The plan generator:

- Read all 106 explicit publication-copy files and their 106 experiments
  counterparts, with exact before/after bytes, size, nsmtime and file identity.
- Verified corresponding `100644` Git tree entries at the exact commit and read
  every original blob through one read-only `git cat-file --batch` call. Each
  blob's computed SHA256 matches both disk copies. The blob IDs are not merely
  assumed to identify matching content.
- Checked every component from the drive root through each candidate/backup
  path with `lstat`; symbolic links and Windows reparse points refuse. Every
  file is regular and single-linked, and stays contained in its explicit
  literal packet boundary. File/component identities are rechecked after reads.
- Confirmed HEAD stayed at the stated commit. Cached `origin/main` also equals
  that commit. Root already reported push/fetch/ls-remote verification; this
  plan performed no network operation or fresh remote verification.

Only source and JSON metadata (including compressed JSON proofs) are eligible.
Full logs are excluded. No native payload, project runtime or artwork is a
candidate. The publication indexes themselves are byte-bound eligible copies;
removing selected copies later would leave partial local publication folders,
so those folders must not subsequently be treated as complete runnable bundles.
Their complete committed counterparts and all original local evidence remain.

## Before any later cleanup

Root must independently revalidate the exact candidate bytes/stamps/identity,
containment, every no-reparse component and Git reconstruction, then establish
that none of these exact files is in current use. This plan makes **no process
use or ownership claim**: it ran no process scan, kill, test or graphics job.

Any later separately authorized cleanup must select only literal `source`
entries from this plan and operate one file at a time. It must refuse changes,
unknown paths, missing backups, links, new hard links and reused directories.
Do not recurse, remove directories, broaden the allowlist, execute the old SFM
cleaner, or touch logs/fixtures/overlays merely because they share a parent name.
No cleanup executor is included here.

## Reconstruction recipe

Retrieve the verified repository commit into an owned checkout. For each exact
row, read `backup_relative` from that commit (or its `blob_sha1` with
`git cat-file blob`), compute SHA256/byte length, and require the plan's expected
values before writing a fresh owned reconstruction file. Preserve raw bytes;
do not normalize line endings. Reconstruct only into an independently checked
owned target. The corresponding experiments path is the reviewable saved copy;
do not depend on the remaining output cache.

All work for this plan was confined to this new output directory. No source
copy, committed packet, main file, Git object/ref/index, tool or owner data was
changed, moved or deleted.
