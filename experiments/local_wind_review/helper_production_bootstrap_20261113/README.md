# Host bootstrap and bounded request files

This output-only candidate removes the previous Node's need for observer-supplied host PID/creation configuration. An actual isolated headless Node now derives its own live PID and executable path, checks the pinned approved Godot image hash, and starts the trusted Python controller. The controller opens one query/synchronize host handle, reads creation FILETIME and `QueryFullProcessImageNameW` from that same handle, verifies the approved absolute image path/on-disk SHA256, and rechecks liveness. Ready reports that retained identity. The still-live Node compares host PID with its own `OS.get_process_id()`, creation-string shape and its own image path/hash before any valid start.

The external observer is now **verification only**: no host identity, image or creation fields appear in the normal Node configuration. It independently captures the created Godot handle and verifies ready's PID/creation/image against it. The fixture still receives runtime paths, a fresh owned output root and test commands from its harness; this is not a main-HAS UI integration.

The final suite reports **18 tests, 0 failures, 0 errors**, in 31.446 seconds. It retains the prior lifecycle/resource tests and adds actual host-image pin refusal, wrong ready host PID/image/missing creation, four bad request references, cancellation/stale submission isolation and a fresh large-file success. No main project, model import, renderer, GPU, native converter, Git operation, installed runtime or extension was used or changed.

## Large requests, small controls

Both ends now enforce **2048-byte control frames**. Start publishes a reviewed ASCII JSON submission below the controller-created `owned_root/requests`, limited to the existing 1 MiB request budget, then sends only its exact path, raw SHA256, byte count, source path/SHA and context SHA. Poll sends the current context digest, so valid Unicode-heavy contexts do not become oversized pipe writes. The separate trusted worker completion still carries the generated worker-request and full receipt digests; a mutable submission or receipt file is never its own expected completion token.

The real large-request cases used **12,934-byte submission files**, with 5,594 context bytes. An inline poll would have been 5,781 bytes. Actual start controls were **849 bytes**, and polls **258–259 bytes**. Those files prepared successfully after malformed-reference and stale/cancel controls. The packet retains the actual metrics, not an extrapolation from string constants.

The controller refuses a reference outside its dedicated direct request directory, links/reparse paths, oversized/growing files, wrong exact size/SHA, duplicate/nonfinite/non-ASCII JSON, wrong session/purpose/PRE-start generation/nonce, mismatched context bytes and decoded context, or changed original source path/size/SHA. It reads at most MAX_REQUEST+1 after the size precheck. Source identity and the same request reference are refreshed before first and cached preparation exposure. Filenames use a bounded per-attempt counter, preserving retries without replacing earlier attempts.

## Lifetime and evidence

The exact pinned Windows map invariant remains unchanged: only this Node's successful `OS.execute_with_pipe` return reserves one exclusively owned map entry; consume the reservation before exactly one mapped `OS.kill`, cache exit first and never retry even `FAILED`. The generic PID fallback is not used under that invariant. The handle-count case measured **267 → 265 → 265** for first release and a refused repeat. Native process handles prevent PID reuse while held.

The independent controller watchdog still watches the retained exact host and input EOF/error. If service cleanup blocks after loss, it exits **only its own process** with code 74 after the grace, causing Windows to close the owned worker Job. Actual Node free/tree exit, ordinary and abrupt Godot exit, controller death, malformed events, double release/free and blocked-service watchdog cases all pass. Creation-verified external handles observe process termination; worker handles cannot terminate a process.

`cpu-process-receipts.json` contains the compact exact process records, host verification, request/transport metrics and resource counts. Generated GLBs/jobs/test wrappers and `.godot` cache stay outside the indexed publication. All prior bridge packet files are hash-verified unchanged, and the three underlying protocol/worker/adapter sources are copied byte-identically.

The first full run had 16 passing tests and two harness failures after large candidates prepared: identical rejected attempts legitimately shared a SHA, while the harness assumed a SHA identified only one filesystem path. The preserved `cpu-tests-content-equivalence-failure.*` records that run. The harness now requires all matching copies to be byte-identical and uses the latest attempt; no product predicate changed. The final full run passed all 18.

This verifies an isolated production-shaped bootstrap and CPU transport, not main-app helper hosting, hidden model imports/bindings, original pose/physics/visibility, canvas cleanup, Apply/Undo or rendered acceptance. Image SHA refers to queried image-path bytes on disk, not attestation of loaded memory or hostile-code isolation. General arbitrarily stalled-peer write behavior remains outside the small-control proof.

Rerun from the actual project root with the existing approved Python:

```powershell
& 'C:\Program Files\Python313\python.exe' -B output\wind-helper-production-bootstrap-20261113\tests\test_bootstrap.py
```

Rerunning writes fresh owned CPU fixtures and replaces the packet's summary. Copy a frozen publication first. It starts only the isolated headless project.
