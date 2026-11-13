# Isolated Godot Node CPU bridge

This output-only increment connects an actual GDScript Node to the preview-purpose Python controller in a minimal **headless** Godot 4.6 project. It proves process/pipe lifetime using synthetic CPU helper fixtures, without launching the main HAS project, a renderer, native models or a converter. The preceding 17-test controller packet remains unchanged. No main source, HEAD, Git, installed runtime or extension was changed.

The final suite has **12 tests, 0 failures, 0 errors**, completed in 9.181 seconds. It covers real Node start/poll/prepared transport, Unicode context and strict integer request roundtrip, Node free, tree removal, normal tree shutdown, abrupt Godot death, exact retained-controller termination, and an independently monitored controller blocked inside a service callback. It also checks actual process-creation failure, missing-runtime refusal, malformed nested ready data, unknown matching-sequence events, late events and repeated cleanup.

The process model is external observer → isolated headless Godot → controller → one Job-owned Python CPU worker. The observer captures the created Godot process's exact PID and creation FILETIME before publishing the Node's fresh trusted fixture configuration. **That configuration is a test bootstrap, not an implemented production bootstrap.** The controller retains that exact Godot host handle. A future app bootstrap seam is described in `NEXT_INTEGRATION.md`.

## Two ownership paths proved

The Node reserves cleanup ownership only from its own successful `OS.execute_with_pipe` return. It keeps the entry exclusive, consumes its reservation before calling `OS.kill` exactly once, and never retries even if the return is `FAILED`. In the pinned Windows backend, that first call uses the process map's retained native handle and closes its process/thread handles; the generic PID fallback is not used under this invariant. Failed launch reserves nothing. The source proof and Microsoft PID-lifetime evidence are recorded in `PRIMARY_EVIDENCE.json`.

The native handle-count experiment closed the Node's pipe handles and waited for controller/worker exit first. While Godot remained alive, it measured **266 handles before mapped release, 264 after, and 264 after a refused repeat**. The first call returned `FAILED` with cached exit 0, as expected for an already exited process; both internal handles were nevertheless released. A late event was refused and double free caused no second process cleanup. The external observer retained and verified controller and worker incarnations through these observations.

Abrupt Godot loss cannot run Node cleanup. The controller therefore has an independent watchdog watching its retained exact host handle and input EOF/error. If the service loop cannot finish within a 0.75-second grace, the watchdog calls `os._exit(74)` **only on its own controller process**. Windows then closes that controller's owned Job handle. The blocked-service test observed controller exit 74 and the already gated, non-stdin-reading worker's termination through retained handles. The watchdog performs no filesystem writes or PID termination and remains active until owned-child cleanup finishes, then stops/joins before the parent handle closes.

## Bounded bridge

The Node is single-use and Windows/pinned-engine-only. It sends one command at a time, caps each ASCII JSON frame at 2048 bytes, escapes Unicode, normalizes only validated integer selector fields, and refuses reserved envelope overrides. Reads accumulate bounded LF frames using available pipe bytes. It validates session, expected sequence/operation, generation/nonce/phase transitions, worker/request identity and checksum-bound preparation/cleanup before emitting events. Ready/command response deadlines are five seconds; the isolated fixture also has a 20-second outer bound.

Pipe close is explicit in `_exit_tree`; stopped events are ignored. The Node observes its own retained-map child for exit and caches exit before map release. A final close acknowledgement may be overtaken by native exit 0; that is recorded as a separate close observation, not a prepared result. The exact runtime's nonblocking-mode setter ignores failure internally, so this small-frame, one-outstanding-command fixture is **not proof of universal nonblocking writes for arbitrarily stalled peers**. Failed or short writes close transport without retrying a possibly delivered prefix.

`cpu-process-receipts.json` collates exact native process observations, cleanup flags, host/config provenance, malformed-event evidence, watchdog exit and handle counts. Full synthetic GLBs/jobs, `.godot` cache, and test-only wrappers remain outside the compact indexed publication. Worker observation handles have query/synchronize rights only. The controller-death fault uses a separately retained, creation-verified termination-capable controller handle; abrupt Godot death uses its exact created `Popen` handle. No generic PID termination is used.

## Retained failures and verification limits

The first full run failed before any controller launched due to a fixture lambda syntax error; `cpu-tests-fixture-parse-failure.*` preserves all 12 failed checks. Retained check-only capture then caught a `ready` name collision with Node's native signal; its log is retained. Treating a direct shell return/header as compiler success had been incorrect: Godot can return 0 while logging script compilation errors. The successful retained check-only result checks captured errors as well as exit.

The next full run passed the lifecycle and handle-count checks, while two negative-event tests failed in the harness after correctly observing expected bridge failure: its shared wait helper rejected that already expected failure file before the repeat-release assertion. `cpu-tests-expected-failure-wait.*` retains that run. Only expected-failure wait handling changed; no admission predicate or cleanup assertion was relaxed. The final full suite then passed all 12.

An initial direct invocation without an owned `--log-file` also failed trying to create restricted default `user://logs`, with an engine crash before fixture execution. All retained-process runs use an explicit owned log path. These are headless fixture/process results, not graphical, real-model, helper UI, original-physics, hidden-import/binding, Apply/Undo or complete product acceptance.

Rerun with the existing approved Python from the actual project root:

```powershell
& 'C:\Program Files\Python313\python.exe' -B output\wind-helper-godot-bridge-20261113\tests\test_godot_bridge.py
```

This writes fresh generated CPU artifacts and replaces the packet's test summary; copy a frozen publication before rerunning. It starts only the indexed isolated headless project, never main HAS.
