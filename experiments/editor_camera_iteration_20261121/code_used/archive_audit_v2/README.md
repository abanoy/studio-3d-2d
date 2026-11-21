# Editor/camera archive audit

This read-only stdlib checker neither executes source files nor launches applications, tests, Git, native tools, or network calls. It writes no files; stdout is a compact PASS/FAIL result. Root authorized its first CPU audit after finalizing the initial archive inventory: exit0/PASS,1,046 payload files,45 frozen inner manifests and25 current functional targets. See bases/v1/ACTUAL_CPU_AUDIT.json for the original checker run. Root will add this audit source and rerun against the successor final CONTENTS pin; the first pass does not qualify a later changed inventory.

Required final contract: `CONTENTS.json.files` contains unique relative `path`, integer `bytes`, and lowercase SHA256 rows for every file in the finished packet except `CONTENTS.json` itself. Additional row provenance such as `source` remains metadata. `PENDING_CONTENTS*` inventories must stay local and outside the finished packet. Include this checker and its metadata before producing the final inventory if recoverability of the audit itself is desired.

Run from any directory with the installed Python interpreter:

```text
"C:\Program Files\Python313\python.exe" -B "C:\a\Programming\cloudflare\has-body-addition-20261120\output\source-editor-camera-archive-audit-v2-prep-20261121\check_archive.py" --packet "C:\a\Programming\cloudflare\has-body-addition-20261120\experiments\editor_camera_iteration_20261121" --contents-sha256 <EXACT_FINAL_CONTENTS_SHA256> --main-root "C:\a\Programming\cloudflare\has-body-addition-20261120"
```

The same command can check the completed local output packet by changing only `--packet`. Optional `--verify-origins` also hashes declared `source` files relative to `--main-root`; leave it off for a recovered checkout whose historical output originals no longer exist. Archive and current25-target checking always run.

The checks cover the exact file set, byte hashes, case/path collisions, Windows path aliases, symbolic links/reparse points/hardlinks, UTF8 source/text extensions, embedded binary data URI payloads, and a bounded structural screen for private mesh/weight arrays. Exact retained MIT Godot C++ files and their exact upstream license are intentional allowed source. Ordinary source code, synthetic camera fixtures and UI screen geometry are retained. This mechanical screen complements the source/evidence curation review; it does not certify the meaning of arbitrary prose or independently re-run actual historical results.

Every real inner `SOURCE_PINS.json` must close exactly over its directory and agree with outer CONTENTS. Historical files named e.g. `PREDECESSOR_SOURCE_PINS.json` remain retained provenance, not falsely treated as a new manifest of their containing directory. The checker compares current Main to the archived combined23-target manifest and the two port-binding targets, including recovery payload bytes. It does not reinterpret old source-only adoption flags or claim a new Full1102 run. Final readbacks repeat hashes and identities. Modification times exclude access times so read-only file access cannot invalidate the check.

Root has qualified the current feature increment independently: combined939, ordinary editor111/camera515, Wind94+5+845 and Helper120/208/266. This archive audit proves neither those historical executions nor a current Full; their scoped retained receipts remain separate evidence.

Version2 adds only an explicit directory-enumeration error handler to the checker. Any unreadable extra directory now refuses instead of being silently skipped. No unreadable directory was observed during the original actual audit. The entire frozen4-file predecessor is retained in bases/v1. Version2 has not yet been executed; Root will qualify its final inventory after copy.
