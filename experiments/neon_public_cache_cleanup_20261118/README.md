# Exact public cache cleanup preparation

This is a prepared plan, not a deletion result. It covers exactly eighteen public
GitHub response-cache files under this session's `output`: nine for `973039e`,
eight complete batches for `ddc24d7`, and its initial pre-fallback batch.
Their logical extent is 20,347,848 bytes. No raw cache bodies are included here.

`cleanup.py` defaults to read-only verification. Root may use `--delete` only
after publishing the exact `7d3a345f…` COMPLETE proof and independently reading it
back. Supply that publication's commit and Root's pinned standard COMPLETE
readback reference. The script checks both the committed Git proof bytes and
the independent reference before creating an exclusive per-file journal.

Only the eighteen exact regular files can be unlinked. Every identity is checked
again immediately before unlink; failure stops the loop and preserves the
journal. There is no recursive deletion, move, native run or process control.
Originals, private outputs, reviews and other caches are outside this plan.
