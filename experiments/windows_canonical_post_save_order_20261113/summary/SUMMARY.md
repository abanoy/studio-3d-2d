# Canonical result after save ordering

The completed run at `12071fe182a17d17e2a1547c7dbb97f6aa4dd160` reports
**PASS / exit 0**, from 21:12:16.4001044 to 21:58:36.3690200 UTC on
2026-11-13: **2,779.968916 seconds**, approximately 46 minutes 20 seconds.
Its before/after source maps are exactly identical: **968 files each**.

The fresh `output/verification.json` has 154 top-level entries, 2,090,687 bytes,
and SHA256 `c431e33c5374c7881683713cca1c22ee415fa98fe5b66973f3785731f6acb79c`.

| Registered scope | Actual checks |
| --- | --- |
| New helper CPU | 208 = transport 11 + adapter 128 + host 69 |
| New helper graphical | 266 = focused 221 + peers 45 |
| Background save | 114 = domain 10 + ordering 32 + Python project 31 + Python faults 16 + writer 20 + reader 5 |
| Independent body animation | unit 24 + editor/persistence 72 |
| Existing Wind graphical | 845 across 6 cases |

All listed scopes passed. Both new helper modes identify `main_source_snapshot`,
zero overlays and all nine preservation gates true. The default registration
requests no native case and explicitly says native fidelity false. Its graphical
count is 266 for this revision, rather than the earlier 263 draft count.

There are **21 root encoded-movie checks**, all 48 frames at 24 fps and 2 seconds;
the canonical's format assertions also require 1920×1080 H.264. This summary did
not reopen media or run ffprobe. The existing 19 generated standard ffprobe JSON
reports show 9 AAC movies and 10 without audio; the two posed-movie entries carry
the canonical video assertions separately. Tone onset and the WASAPI editor
onset are both **1.0 seconds**. Editor RMS at 1.1 seconds is 5658.299233592635.
The fresh silent and tone fixtures have separate movie paths.

Counts are named report scopes, not a deduplicated total of every assertion in
the full suite. Body native fixture count is 5 plus the authored case; these
checks do not certify full native shader, flex, jiggle or visual fidelity.

## Metadata publication assessment

Independent bounded content inspection found no embedded private images, mesh
buffers/raw vertex arrays, base64 assets or credential-named fields. The report
is suitable as metadata-only evidence. It retains absolute local paths, names,
hashes, timings/hardware data and two authored expected-document snapshots with
poses, shapes, transforms and native metadata. It is not anonymized. See
`content-audit/CONTENT_AUDIT.md` and `RESULT.json` for exact scope and limits.

In-memory compression with approved Python 3.13.1 / zlib 1.3.1,
`gzip.compress(raw, compresslevel=9, mtime=0)`, produced 785,510 bytes with SHA256
`7d27878353f349df5d71b65d94bdbc34c781989b19559b5f045dffa8582066f7`.
Two independent in-memory calls produced identical bytes, and decompression
matched the exact raw report. Compressed bytes are bound to that runtime/library
combination; the raw report SHA is authoritative. No compressed report artifact
or release was created by this task.

This summary read completed JSON/source-assertion metadata only. It changed no
main source, Git state, report input or owner asset, ran no new test/graphics/
native worker, and did not create or release a graphics lease. A machine-suite
pass does not substitute for separate owner observations or native-fidelity
acceptance.
