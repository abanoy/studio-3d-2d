# Two-phase snapshot ordering candidate — not shipped

Base: `1236796865e677b150a2d7e2add20f2aac5325fe`. Only two output-overlay
functional files change. Main sources, Git state and approved runtimes remain
unchanged. This candidate removes one avoidable overlap between the save
snapshot's directory-writing thread and Godot's child creation; it does not
establish the cause of the prior intermittent Windows failure or guarantee that
no other thread can change the process working directory.

`HasSnapshotWriter.prepare(project, request)` now captures detached metadata and
copy-on-write pixel state on the calling thread, without starting a Thread or
writing snapshot directories. `launch()` consumes that capture and starts the
existing `_run` work. `start(project, request)` remains compatible by delegating
to prepare then launch. `has_prepared` and `discard_prepared` expose the separate
unlaunched state. `finish` also discards prepared-only state without launching it.
The existing busy/poll/result and persistence contracts remain unchanged.

`HasProject.start` prepares before writing its request, then creates the project
worker, then launches the snapshot thread. The existing Python worker already
waits for operation-specific `snapshot_ready`, so early child creation does not
allow early packaging. Request-write and child-create failures call finish to
discard the capture. If Thread creation fails after the child exists, the code
retains ownership through the ordinary pid/exporting/progress flow, sets the
snapshot error and publishes cancellation; polling observes child completion
and emits one failure. Teardown discards unlaunched state and still cancels/drains
an active writer. No synchronous waiting for a live child is added to the UI.

Candidate hashes:

- `overlay/src/has_snapshot_writer.gd`: `61400dfcf743cf4bd1e0d99e3aec7e1c74f05d61108cfa64cf7afe3f7613111f`
- `overlay/src/has_project.gd`: `7e916f812ac48c7a1792d2beab604bd9da01c0d86f357ec3a29c8676a4951032`

`candidate.patch` is the narrow difference from the exact base. No other source
replacement is proposed, and no existing test predicate has been weakened.

## Actual verification

Final fresh headless run `runs/1794602846262952000-64b158a8` passed **32/0**,
with clean engine/stdout logs, exact source/runtime/HEAD preservation and reaped
Popen. It used literal `run.command()` redirected to a minimal owned project and
the approved absolute Godot runtime. No graphical/GPU, Blender, native assets or
main application instance ran.

The authored test exercises the actual capture/adopt and Thread code. It proves
that prepare starts no thread/writes; prelaunch edits cannot alter captured
pixels, metadata or nested request data; duplicate/busy states refuse; a capture
launches once; explicit discard and prepared-only finish release state; old
start still completes; forced Thread-start failure cleans state; and cancellation
publishes failed readiness and drains ownership. `HasProject` also compiles and
constructs without starting the app. Persistence is an explicitly inert observed
override: normal Storage writing, a real waiting packer and full app save/close
behavior remain separate acceptance checks.

Prior attempts remain preserved and are not reclassified:

- `1794602791903330600-27680230`: writer predicates 31/0, overall **failed** due to
  a missing unchanged shader preload in the isolated copy. Exact logs/project
  and driver source retained; fixed only dependency acquisition.
- `1794602808548787700-3d78d256`: clean 31/0 before adding `HasProject` compile
  coverage, still valid for those writer controls.
- `1794602837014647500-ccc3b661`: **failed** before tests because the new test
  called `can_instantiate` as a static class method. Corrected the harness to
  construct/free the unattached Node; functional candidate bytes unchanged.

Reproduce with approved Python: `python -B verify_candidate.py`. It refuses a
different main HEAD, copies the explicit transitive unchanged script/shader
dependencies into a fresh owned project, overlays the Writer candidate, checks
the source ordering and runs headlessly. For later repository use, reconcile the
base before reproducing rather than weakening its revision guard.

## Next acceptance

Independent source review should cover prepared-state ownership, Thread failure,
cancel and teardown. Before any main port, run the original unchanged snapshot
writer/domain and background save/large-save checks, plus the focused body
animation persistence case. A successful focused retry would establish its own
result, not retroactively pass the failed canonical run. Then verify the actual
post-port main source with a fresh canonical suite. Preserve the original
unknown Windows launch error, the passing 240-launch CWD probe and all candidate
failure evidence.
