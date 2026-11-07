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

Whole-layer history paths still use their earlier conservative snapshots.
Automatic cold loading and idle release are described in cold_cel_rasters.md.
MEM-01 remains partial in the completion checklist; these changes do not complete
the larger-project memory requirements or justify raising prototype limits.


## Create, duplicate and delete

Create/Copy Cel and Delete Cel use the same stable affected-cel patches. Copy
inside a held drawing keeps its shortened exposure and the inserted independent
cel; blank creation in a gap keeps only its new cel; deletion keeps only the
removed cel. Thirty unrelated peers are no longer retained by these commands.
The legacy transient `cels` command remains readable for compatibility.

A real31-cel fixture reproduced a522,547,200-byte copy history charge that discarded
the preceding brush Undo. The fixed copy charges16,590,332 bytes, deletion8,295,628
and gap creation8,295,632. These conservative history charges are not process RAM.
The expanded verifier passes202 checks, including24new checks for each eager and
owned-cel variant. Earlier stroke Undo remains reachable, all pixels and exposure
boundaries are exact, peers retain identity, stale/wrong-sequence targets refuse,
child round trips work, and physics generation stays unchanged during Undo/Redo.
The existing live physics, packed cold reopen and H264 movie tests also pass.
The32-cel/64MiB/128-command limits and saved project formats are unchanged.

Evidence: [create/delete receipt](benchmarks/cel_create_delete_history_2026-11-06.json).
Whole-layer and global storage accounting remain open; no cap expansion or full
MEM-01/MEM-02 closure is claimed.
