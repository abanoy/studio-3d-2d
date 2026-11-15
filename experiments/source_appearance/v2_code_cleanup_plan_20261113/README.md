# Four retired v2 source copies: cleanup plan only

This packet lists exact file candidates within only the writer-source and reader-source directories of these two closed historical v2 runs:

- `1794555713647050600-5718442689ac488f931dce81ca1c3101`
- `1794556016763092400-40301e3c9fe24f5a9c7441715f6268ba`

Every candidate must be listed with the same hash in its original run manifest and match the exact regular Git blob at `e9cc7cfb20266b4863bde134bcb30457547a343d`. The planner validates every directory/file path and its ancestors for containment and absence of reparse points, classifies the whole observed membership, then verifies every observed file identity/membership again. It only reads the historical source copies and Git objects; it cannot delete, move, restore or kill a process.

The code-focused policy is intentionally conservative. It retains all `output`, `.godot`, cache, generated and private-path contents; all unique or unlisted source; the custom harness/override files; and all non-code assets/media/metadata even if a public procedural asset is Git-reconstructible. No directory is a cleanup candidate. Old v2 original sources, v3/future files, review packages, recovery data, native models and runtimes outside the four exact roots are out of scope.

`PLAN.json` records every candidate's exact absolute path, Git path/object/mode, SHA256, length, timestamp and reconstruction recipe. Retained files also have identities and explicit reasons. Historical writer private-desktop receipts are preserved by identity and require closed jobs/desktops and no observed child foreground window. Absence of reader command/receipt is recorded as absence, not a closed-job attestation. This packet does not establish current process nonuse; root must independently revalidate that immediately before any later exact-file cleanup.

Before cleanup, root must publish and remotely verify this exact packet and historical Git data, revalidate process nonuse and all paths/identities/membership, and use only the frozen candidate paths. New, changed, retained and unlisted files must survive. No recursive directory removal, wildcard selection, broadening retry or automatic cleanup is included.

To reconstruct a removed candidate later, read its recorded Git blob as raw bytes with `git cat-file blob <exact_object_id>` into a fresh owned reconstruction destination corresponding to the recorded source root and Git path. Verify the exact recorded SHA256 and byte length before use. Reconstructing source does not recreate generated/private state, custom harness files or the original unique profile; those are retained separately. The planner itself never reconstructs anything.

`source/plan_four.py` is the reviewed-scope read-only recipe; `PLAN.json` is a frozen plan, not an authorization to execute cleanup. Source and failed-run evidence remain preserved.

The completed plan identifies **4,308 files /33,607,832 bytes** as candidates: exactly1,077 files /8,401,958 bytes per source copy. It retains **2,613 files /68,376,831 bytes**, including all twelve custom override/harness files across the four roots. Both writer receipts attest historical job/desktop closure; both reader copies have no retained phase command/receipt. All observed file identities and directory memberships remained unchanged across two full reads. No live-process nonuse claim is made.

For publication, `PLAN.json.gz` is a deterministic lossless copy of the local7,532,146-byte `PLAN.json`; decompression was byte-verified. The raw plan SHA256 is `e65b408acdf63eade874709b6dc37de43b6c244ff3f9fe5fc11cab222c43fa8a`. `SUMMARY.json` provides per-root totals, unique exceptions and closure-evidence status.
