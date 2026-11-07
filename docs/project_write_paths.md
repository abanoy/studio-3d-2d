# Preserving sources during directory saves

Directory Save refuses symbolic links in its managed child directories and final
manifest/backup/PNG destinations. It walks descendant path components before
writing; the explicitly chosen project root may itself be a link. Managed asset
copying also rejects a linked final file.

Previously, an existing `project.json.tmp` link could make Save truncate an
original file outside the project folder and then promote that link as the
manifest. An owned sentinel fixture reproduced both changes. The same fixture
now refuses before writing and preserves the original and previous manifest.

Manifest, PNG and managed-copy temporaries now have fresh unique names and do
not truncate existing temporary inodes, including hard-linked originals. Backup
copies also use a fresh temporary, verify bytes and replace the directory entry.
This preserves originals even when an old backup is a hard link. Normal stale
`project.json.tmp` files remain untouched; the existing temporary-directory
obstruction still refuses safely. No saved project schema or resource cap changes.

New PNGs are decoded and matched to their authoritative pixel checksum before
replacement. New manifest bytes are compared exactly and validated before the
previous manifest is backed up/replaced. Backups receive a SHA256 comparison.
Existing content-addressed PNG verification and failed-data preservation remain.
This adds readback work; it does not certify physical storage durability.

The permanent cold-raster domain verifier includes17Linux path tests (225combined
checks): linked manifest/temporary/backup/directories/PNG/managed file, hard-linked
temporaries/backups/PNG repair, stale temporary preservation, safe chosen root,
and a real owned read-only directory. Windows reports this Linux fixture as
skipped and still needs its native reparse/locking checks.

```sh
python tests/verify_cel_raster_snapshot.py --output /absolute/new/domain-result
```

The automatic32cel real app/recovery/movie suite and224nested adaptive/mask checks
also pass on an owned private display. They cover packed/linked/active-child saves,
source preservation, exact editable pixels, actual abrupt exit/fresh startup and
H264/AAC output. These suites overlap and do not establish native-format fidelity.
See [write-path evidence](benchmarks/project_write_paths_2026-11-06.json).

STORE-04 remains open for directory sync/power-loss, native Windows, concurrent-writer robustness. Private recovery/lesson metadata writers now have
[their own scoped fix and verification](private_metadata_writes.md). These
checks do not certify hostile concurrent filesystem mutation.
