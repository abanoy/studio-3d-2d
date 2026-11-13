# Background manual project saves

Manual HAS Save now captures detached metadata and drawing resources, then writes
and verifies the PNG snapshot on a low-priority CPU worker. The Python packer waits
for an atomic, checked readiness packet before reading the completed snapshot.
The existing positive process ID, modal progress window, Cancel action, verified
archive publication, compare-and-swap and backup behavior remain in use.

The Windows launch-order hardening now separates `prepare()` from `launch()`.
Preparation captures the same detached state before child creation; the snapshot
filesystem thread starts after the real Python packer exists. The packer still
waits for checked readiness. A thread startup failure cancels that waiting child
and follows the normal single failure/completion path, preserving the prior save
and newer dirty edits. The old `start()` API remains available.

The worker owns its raster cache and never receives live scene nodes, owners or
renderer state. Later edits stay dirty; saving an older document cannot attach its
identity to a new document. Cancellation and shutdown drain current file work.
Snapshot preparation has a 600-second guard; packaging keeps its separate
120-second allowance. Linked dependencies include root and child audio, world
assets and kept reference images. Existing project schemas are unchanged.

On the same actual 400-drawing prepared-video project whose earlier synchronous
Save took 76.036 seconds, the final Save call returned in 21 ms and snapshot capture
took 3.851 ms. Worker staging took 78.763 seconds and total save took 80.022 seconds,
while 1,898 application frames ran. The maximum observed frame gap was 184.622 ms.
This improves responsiveness; it does not claim faster total serialization.
All 400 pixel hashes survived a fresh reader with the writer cache unavailable.
The previous target stayed intact until publication and its exact backup passed.

The main registered raster accounting was 34,694,651 bytes, below its unchanged
335,544,320-byte admission. Separate writer process sampled RSS peaked at
493,457,408 bytes, with observed HWM 501,743,616 bytes. These are Godot-process
measurements, not whole-session, process-family or GPU memory guarantees.

Final isolated Linux checks: 10 worker ownership, 28 Python HAS, 16 save-fault,
17 live writer and 5 cold reader checks; 8 large writer and 4 large reader checks;
70 nested/reference/audio/crash/startup/lesson checks; and 96 existing recovery
ownership/worker/app/preview/scheduling checks. All passed. The nested case also
verified a real 48-frame 1080p24 H264/AAC output and exact source preservation.

An initial nested regression exposed a test artifact truncated by deliberate
SIGKILL: its expected JSON was not explicitly flushed and closed. The fixture now
flushes, closes and verifies the complete artifact before killing itself; all
original application assertions remain. The posed-reference wrapper now reads the
actual Python test count instead of requiring the former count of 23.

Initial Open still blocks during project loading. Long-session cache cleanup,
retention and concurrent quota policies, physical Windows/storage/device latency,
and native-format fidelity remain separate work. The full aggregate verifier's
Windows-only Krita harness remains unrun on Linux. No formal MEM acceptance is
closed by these scoped results.

Run `tests/verify_has_background_save.py`, `tests/verify_has_background_large.py`,
`tests/verify_project_reference.py` and `tests/verify_recovery_writer.py` with an
explicitly isolated display and fresh absolute output directory. See the
[recorded evidence](benchmarks/background_manual_saves_2026-11-07.json).

## November 13 Windows checks

Current main passes the original 10 writer-domain predicates, 32 new staged-capture
controls, 31 Python HAS and 16 save-fault cases, 20 actual writer checks (17 original
plus three launch-order/failure checks) and five cold-reader checks. Two private
desktop jobs exit zero and close cleanly. The actual held save returns in 9 ms;
this small fixture is separate from the historical 400-drawing measurements above.
Native body animation also passes its original 24 units and 72 app checks across
five native profiles plus the authored fixture, including packed/linked persistence
and a real 48-frame 1080p24 movie.

The full run at `1236796` remains **failed**: Windows refused the final VRM0 linked
save-helper creation. An unchanged focused retry passed. The engine message does
not expose the precise Windows error; a 240-child directory-churn probe also did
not reproduce it. This ordering change removes an avoidable overlap with our own
snapshot thread; it does not establish the original failure's cause or serialize
every other filesystem thread. The next full runner explicitly selects the already
approved absolute Python runtime. See [actual results and retained failures](benchmarks/windows_snapshot_launch_order_2026-11-13.json).
