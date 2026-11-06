# Affected-cel drawing history

Timeline Cut, Paste and Split now retain only their affected cel records. A Cut
keeps its removed cel, Paste keeps its inserted cel, and Split keeps the original
and its two halves. Unchanged peers and the layer dictionary are not retained by
these commands. Images remain independent editable resources with the existing
copy-on-write backing behavior.

Previously, splitting a 31-cel layer recorded both complete layer lists. The
existing conservative accounting charged 522,547,200 bytes and evicted the real
stroke that immediately preceded the split. The same owned fixture now charges
16,590,332 bytes and keeps that stroke Undo available. Cut/Paste charges in this
fixture are 8,295,628/8,295,632 bytes respectively.

These numbers measure history accounting and retained references, **not process
RAM, RSS, GPU memory or a whole-app speed improvement**. Each command charges
distinct raster resources once plus an estimated metadata allowance. Shared
images may still be charged again across separate commands. The existing 64 MiB/
128-entry history policy and global 32-cel limit remain unchanged.

Undo/Redo resolves stable layer IDs in the correct sequence owner, replaces only
the intended slots and leaves peer dictionaries/images alone. It verifies the
expected affected records before changing anything, normalizes validated integer
frame values, accepts rebuilt equal-pixel Images, and refuses stale/missing
targets, overlaps or a global-budget overflow. Failure leaves the document and
history stack intact. Patch history is transient; project formats are unchanged.

The normal drawing-history path refreshes the overlay without resetting live
physics. Seeking during a clip edit retains the editor's established freeze
policy; this is separate from Undo/Redo. An intermediate test incorrectly
compared physics generation across those deliberate seeks; the final assertions
isolate history operations and additionally exercise an actual running ragdoll.

Reproduce on an explicitly provisioned private Linux display with pinned tools:

```sh
python tests/verify_cel_clipboard.py --isolated-display :104 --output /absolute/new/audit-folder
```

Fresh results: 10 patch-domain checks, 18 near-limit history checks, 43 live-physics
history checks and 3 cold live-history reader checks, plus the existing 80 drawing
operation checks. The combined 154 checks pass, including exact GPU overlay,
ordinary packed Save, writer-cache-unavailable cold Open and H264 1080p24 movie
inputs. Parent/child round trips and wrong-owner/stale-history refusals pass.
Python discovery runs 312 tests: 311 pass and one existing optional independent
MMD-reader test skips. No native Windows/tablet/artist acceptance is claimed.

Before-fix evidence: `/workspace/has-handoff-audit/cel-patch-before/probe.log`.
Final evidence: `/workspace/has-handoff-audit/cel-patch-live/verification.json`.
The curated measurement is in
[cel_patch_history_2026-11-06.json](benchmarks/cel_patch_history_2026-11-06.json).

Other cel-creation/deletion and whole-layer history paths still use their earlier
conservative snapshots. Unique-art cold/lazy loading is also separate work.
MEM-01 remains partial in the completion checklist; these changes do not complete
the larger-project memory requirements or justify raising prototype limits.
