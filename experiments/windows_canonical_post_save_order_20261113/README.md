# Full Windows canonical pass after save ordering

This is source/metadata evidence for commit
`12071fe182a17d17e2a1547c7dbb97f6aa4dd160`, run
`canonical-owned-20261113T211216019`: **PASS / exit 0**, completed
2026-11-13 at 21:58:36.3690200 UTC after approximately 46 minutes 20 seconds.
All 968 before/after source-map entries match exactly. The earlier failed full
run at `1236796` remains separately failed; this pass does not prove the cause of
its intermittent Windows process-creation error.

`verification.json.gz` losslessly preserves the fresh 2,090,687-byte report,
raw SHA256 `c431e33c5374c7881683713cca1c22ee415fa98fe5b66973f3785731f6acb79c`.
The deterministic gzip is 785,510 bytes, SHA256
`7d27878353f349df5d71b65d94bdbc34c781989b19559b5f045dffa8582066f7`.
It was produced with Python 3.13.1 / zlib 1.3.1, level 9, mtime 0. The raw digest is
the primary identity; exact gzip bytes are runtime/library-bound.

The packet includes raw canonical state, launch and source maps;
`canonical/canonical.log.gz` preserves the entire raw log, with raw hash/length
in the outer index. Its normalized suffix is the exact fresh report, and its
122 nonblank prefix lines are preserved in `canonical/pass-markers.txt`.
No full raw JSON/log is duplicated unnecessarily.

## Actual result scopes

The full result has 154 top-level entries and 21 root encoded-movie checks, all
48 frames at 24 fps and 2 seconds, with canonical 1080p H.264 assertions passed.
Both tone and WASAPI editor audio onsets are 1.0 seconds. The new helper reports
CPU 208 and graphical 266 (focused 221 + peers 45), with zero overlays and all nine
preservation gates true. Background-save reports total 114 scoped checks; body
animation retains unit 24 + editor 72. Existing Wind graphical reports 845 checks
across six cases. Counts are scoped records, not an overlapping grand assertion
total. `summary/` preserves the independently prepared five-file summary plus
its exact valid subpacket index.

The new helper default registration requests no native case. A machine-suite
pass does not certify full native shader/flex/jiggle fidelity, private artist
comparisons, device observations or remaining human acceptance. No model,
texture, artwork, drawing raster, project, audio or video payload is included.
Metadata does retain paths, names, hashes and two authored expected-document
pose/shape snapshots; the content audit is preserved under `summary/content-audit`.

## Receipt audit and lease record

The final audit records 176 fresh successful root receipts and 190 unique physical
receipts/desktops overall (14 nested). Outcomes are 189 successful exit 0 and
**one expected Krita converter cancellation at exit 2**. The exact raw cancellation
outcome remains unchanged. The registered test explicitly requires that outcome
and its `cancelled` flag. All 190 satisfy private-desktop confirmation, no
foreground exposure or requested desktop switch, and closed Job/desktop; no
unexpected nonzero outcome, missing referenced receipt or conflicting duplicate
remains. Eleven inline occurrences covering nine desktops match physical JSON.

`receipt-audit/receipt-ready.json` preserves the preliminary scan, including its
then-unresolved and exit-0-only flags. It is historical and superseded by
`receipt-ready-final.json`, `receipt-inventory.json` and
`EXPECTED_CANCEL_ADDENDUM.md`; it is not the terminal audit outcome.

`canonical/graphics-lease-released.json` is the actual root-supplied release at
22:05:34.0598256 UTC, bound to the final audit, inventory, canonical state and
fresh `authoritative-host-before-review.json` hashes. The earlier host-termination
and desktop enumeration remain unchanged historical observations; enumeration
then showed only Default, with no HAS test desktop remaining. Copying this
record did not create a release or grant any current graphics permission. Root
subsequently handed graphics to the owner-review job; its results are separate.

## Provenance indexes and duplicate-byte mapping

The outer `INDEX.json` is the authoritative inventory of **every actual payload
file here**, excluding the index itself. It binds the README, recipes, nested
summary index, audit provenance and mapping. Its compressed-file rows also bind
the exact decompressed original hashes and lengths.

`receipt-audit/ORIGINAL_CONTEXT_INDEX.json` is the **unchanged original audit
folder index**, retained as provenance only. It is not claimed to index the
current local `receipt-audit` directory. Its source SHA256 is
`9d030cb221ab6d1363435e9bf4a1953905841b2a7bac947c2fd56f9e418c50a0`.
`ORIGINAL_CONTEXT_README.md` is likewise the unchanged original folder README;
its references to the original raw-file layout are historical context.

`receipt-audit/CONTEXT_MAPPING.json` accounts for all 16 original index entries.
Ten distinct files are retained in this packet. Six duplicate entries are
represented by the exact bytes already under `canonical/`, or losslessly by
`verification.json.gz`. Each mapping records original and outer identities,
representation and verified decompressed identity where needed. Thus the full
original audit index remains reconstructible without copying its 2 MB raw report,
state/source maps or duplicate host/desktop records again. Audit source code,
inventory, initial/final records, counts, input hashes, summary and addendum are
preserved. Reconstruct to a fresh owned folder; never rewrite the frozen packet.

`provenance/INITIAL_STAGING_RECEIPT.json` records the earlier initial subset and
its source input identities. It is a phase receipt, not another final inventory.
Recipes are source evidence of metadata staging only, not permission to run an
application or issue a graphics release.

No product source/docs/Git, original model, installed runtime, test, graphical
process or release was changed or launched while preparing this packet. The
receipt inventory, host observations and release are supplied by root and
preserved as actual evidence, rather than generated by this packaging task.
