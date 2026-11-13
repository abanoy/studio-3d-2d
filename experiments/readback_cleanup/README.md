# Exact old readback snapshot cleanup

These sources preserve the reviewed, machine-specific PowerShell runner and its
read-only Git verifier. They are outside the normal app and default test suite.
The exact individual-file plan was published at `c6782d2`; its compressed copy is
`docs/benchmarks/readback_reconstructible_cleanup_plan_2026-11-12.json.gz`.

The runner must be copied byte-for-byte beside the raw plan and helper in the
original checkout's `output` directory. Default mode is read-only preflight;
`-Execute` is an explicit mutation switch. The caller must supply the exact
recorded plan SHA256. This historical runner refuses different paths, hashes,
directory identities and process identities. Do not adapt it into general
recursive cleanup or rerun it after targets have been removed.

It verifies Git reconstruction recipes, every candidate and retained file,
directory identities and no observed session/test use before deleting any file.
Deletion uses only native PowerShell `Remove-Item -LiteralPath` on exact files;
there is no recursive deletion, moving or directory removal. Source trees become
intentionally sparse. Retained unique overlays and parent evidence stay in place.

Process checks include available command lines and positively identified owned
working directories. Five exact protected helper PID/name/creation-time identities
have independently reviewed access-denied exceptions; unknown owned/custom
runtimes still block. Inaccessible system/service ownership is reported. This
does not prove universal ownership, current-directory or arbitrary open-handle
freedom. Final preflight and actual deletion status must come from their receipts,
not from these source files or a planned count.

Private assets, originals, tools, owner reviews/recovery, both protected canonical
copies and all unlisted or future copies are excluded. No artwork is in this
source checkpoint.
