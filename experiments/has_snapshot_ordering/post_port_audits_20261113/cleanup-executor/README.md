# Exact publication-copy cleanup executor

This is the reviewed executor for the frozen 88-file / 498,427-byte plan only.
The preparation agent ran **read-only dry runs**, not `--execute`; it performed
no deletion or process scan. Root alone controls execution and its subsequent
aggregate verification. This static source packet is distinct from any later
execution journal/result.

Current source: `cleanup_copies.py`, SHA256
`a5dd37c3952f985e6bf63996449d99ed308dea3432fe8bf291635fe1b9c2ad19`.
Final read-only result: `DRY_RUN_1794608176187825500.json`, all exact file/Git
guards passed, 18 logs retained, zero deletions/process scans. Earlier source
versions and dry runs remain as explicitly historical evidence.

The independent review is `review/REVIEW.json`, SHA256
`276954e635227bacdae66e1d42995885b4dff7290420e374f20aaf068baf8308`, at
2026-11-13T22:16:25.966315+00:00. It binds the final executable SHA and original
plan SHA and reports no unresolved source findings. It does not authorize
deletion or claim current file/process use. The review corrected a null pending
journal index and lexical journal traversal; both older versions are retained,
not alternative approved executors.

The only targets are the frozen plan's 88 literal source/JSON-metadata files in
three task-owned publication-copy roots, backed by the exact committed
`12071fe182a17d17e2a1547c7dbb97f6aa4dd160` experiments blobs. The original plan's
SHA is `00c8ecafaa93c5dc92256e31cfb2841f347dbd84896da516bc1e3fe56400fa24`.
The saved remote proof is also hash-bound. Every path component must retain its
recorded identity and remain non-reparse; file hashes, bytes, nsmtime, device,
inode and single-link state must match for both source and backup. Git path,
blob and raw SHA256 guards run before removal. One checked `Path.unlink` is the
only removal call; no recursive, wildcard, directory, move, kill or old SFM
cleaner operation exists. All 18 full logs, every backup and all unlisted paths
remain protected.

## Root-only fresh execution

First refresh the authoritative host proof **after the review timestamp** and
compute its exact SHA. The executor requires the existing root proof schema,
source revision, coordinator/owned-runtime absence, empty owned matches and a
no-kill observation. Its age must stay within five minutes. It does not perform
its own process scan. For the intended one fresh run:

```
python -B cleanup_copies.py --execute \
  --review ABSOLUTE_PATH_TO_review/REVIEW.json \
  --review-sha256 276954e635227bacdae66e1d42995885b4dff7290420e374f20aaf068baf8308 \
  --process-proof ABSOLUTE_PATH_TO_FRESH_authoritative-host-termination-final.json \
  --process-proof-sha256 ROOT_VERIFIED_FRESH_SHA256
```

This is argument layout, not a shell-specific copy/paste command. Root uses the
already approved absolute Python executable and absolute argument paths. Without
`--execute`, the script verifies only and writes a fresh dry-run JSON here.

Every removal has a durable fsynced before/after journal in a fresh owned
`attempts` subfolder, with another exact-file check immediately before unlink.
Any changed/missing target or guard failure stops. Root plans **no `--resume`**.
If a partial run stops, preserve its journal and independently reconcile it;
do not broaden the plan or start a fresh run over ambiguous missing targets.
The parser refuses incomplete/malformed before/after pairs or failure entries.
Any later resume needs separate operator review and fresh authority; it is not
permission to repair or silently accept uncertainty.

Root will independently check all backups and 18 retained-log identities after
execution. No current process-use, deletion or post-cleanup claim is made by this
source packet. Its static `INDEX.json` excludes future `attempts` execution
journals, which must be preserved and indexed separately with root's result.
