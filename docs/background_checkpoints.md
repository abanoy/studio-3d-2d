# Background recovery checkpoints

Recovery checkpoint serialization now uses one low-priority worker. Main-thread
capture duplicates scene metadata and independent Image resources without encoding
or compressing live pixels. Cold descriptors and payload bytes are copied once per
shared snapshot; hot Images use independent copy-on-write resources. Root and child
scenes preserve independent owners. Unexpected live Object resources refuse capture.
The worker adopts only the captured drawings into its own admitted raster cache.
It does not read or mutate the live document's owners, cache, nodes or GPU state.

The existing recovery writer, source integrity, bounded PNG preflight, atomic
publication, journal and 512 MiB disk budget remain. Only one checkpoint or preview
writer owns journal updates at a time. Explicit Checkpoint now requests made during
work remain queued; no growing queue of full drawing snapshots is created. Live
edits remain available. Successful completion consumes only the actions captured
by that checkpoint; later edits stay pending and dirty. Failed writes retain the
last checkpoint and pending actions, with the existing retry policy.

New/Open use a new session. Completion of an older session cannot change the new
session's schedule, footer or checkpoint revision. An exact-current manual Save
also advances a schedule generation. Its late older checkpoint is resolved after
commit, without consuming edits made after Save. Checkpoint previews still require
the captured revision, frame and view to match, so newer scene content cannot be
attached as an older state's thumbnail. Closing joins the owned worker before
freeing its owner; slow storage can delay that final close.

The temporary worker snapshot is a separate admitted context. Main and worker
retention can overlap. This is not a whole-process or GPU memory bound. Capture
still copies compressed payload bytes and obtains scene metadata on the main
thread; GPU thumbnail readback is separate. Manual project Save now has a separate [background snapshot worker](background_manual_saves.md).
Lesson Previous/Continue serialization remains separate.

Verification uses isolated cloud displays and owned procedural fixtures. Ownership tests pass nine assertions;
worker filesystem/failure tests pass eight. The actual isolated app passes thirteen
checks covering held file work, real rendering/drawing, queued requests, action
accounting, manual-Save races, failed writes, New and teardown, including closing after manual Save while an older checkpoint
is still running. The actual400-drawing run captures in34.874ms, then processes4,519application
frames during114,308ms of background checkpoint work. All eight writer, five
fresh-reader and eight normal-startup assertions pass after real SIGKILL; sources
and writer cache are unavailable to the fresh readers. Its101-frame1080p24H264/AAC
movie preserves exact preview input and sample48,001audio onset. The existing
32-drawing incompressible-art crash/media regression and292raster-domain checks
pass. Largest observed individual process RSS/HWM across the400workflow is
455,798,784bytes; this is process-only measurement, not a hard whole-session/GPU
guarantee.

The96-check snapshot/worker/app/preview/scheduling suite passes, including all
41scheduling and25preview assertions. Lesson unit43/writer7/startup21/19/7/8/8
checks pass across all five actual abrupt-recovery cases. Native540p metadata25/
writer32/reader6 and225nested graph/audio/storage/runtime/editor/cold/startup
checks pass, including actual masked-sequence crash recovery. The54migrated
scripts parse; this does not claim every native-fixture runtime suite passed.

Run `python tests/verify_recovery_writer.py --isolated-display :110 --output
/absolute/new/result` with a private owned display. See
[recorded evidence](benchmarks/background_checkpoints_2026-11-07.json). The
unchanged full verifier remains blocked in a Windows-only native Krita harness
on Linux, separately from these targeted passes. The final close-after-manual-Save
guard was added after the400/native/nested runs and passes the final96-check
suite; the receipt distinguishes those source snapshots.
