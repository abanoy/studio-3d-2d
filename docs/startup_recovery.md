# Automatic startup recovery

Normal startup now tries the newest pending checkpoint automatically. A complete
asset, cel, audio, model and native-bone binding validation must succeed before
replacing the initial empty world. If it fails, Studio tries the next older
candidate, including the previous manifest. Invalid JSON/metadata is ignored at
discovery; asset and rig errors are caught by the normal Open path. No separate
recovery renderer or weakened loader is used.

The recovered document is dirty, has no manual-save identity and requires an
explicit Save destination. The last manual HAS is never overwritten by recovery.
Recovery copies are not deleted or resolved merely because startup restored one.
Saving the recovered copy resolves its source session as before. Recover still
offers retained older choices; Dismiss hides a matching session without deleting
files. Other live writers and resolved copies remain excluded. Windows owner
checks use a small read-only Python helper with SYNCHRONIZE rights and a zero-time
process-handle query. New checkpoints also store the writer's Windows creation
time as an exact decimal string in `session.json`. The helper requests limited
query rights to read that time from the same handle. A live PID with a different
creation time belongs to a different process, so the old session can be recovered.
A matching live writer remains protected. It queries only supplied owner PIDs, without enumerating,
reading memory, stopping processes or opening windows. The engine's child-process
query is insufficient for an unrelated writer. Unknown/access-denied owners are
left untouched, with a footer warning. If liveness is readable but creation time
is unavailable, an identified owner remains protected. Legacy PID-only records
retain their conservative old behavior; no old records are rewritten during scans.
Missing owner sidecars retain older ownerless-folder compatibility, while present
but malformed owner records are protected with a warning. The installed Python/HYBRID_PYTHON setting
is reused; no new package. Up to1024distinct foreign owners per query; excess
owners remain unknown rather than being treated as stopped. Discovery validates
finite nonnegative checkpoint timestamps and uses deterministic tie ordering.

The app caches its own creation token after the first checkpoint/history query,
avoiding another helper launch for each checkpoint. If that first query fails,
it uses a PID-only record until the next app launch. The token is never passed
through floating-point JSON numbers. This updates recovery ownership only, not
native model, world, project, HAS or journal formats. Old builds ignore the extra
owner field and retain their PID-only limitations.

Startup work is deferred until the UI exists, with session/revision/interaction
guards. It refuses to overwrite intervening edits or an open dialog. Candidate
failures are collected in `startup_recovery_result`; the user receives one quiet
footer message, without repeated error popups. If every candidate fails, clean New
remains installed and retained files remain available for review. Existing explicit
Open and manual Restore still report their ordinary errors.

## Verification

`python -u tests/verify_recovery_startup.py` creates an isolated original scene,
skinned animation, separate editable paint, camera keys, WAV and packed manual HAS.
Available prepared MMD/GMod/SFM/VRM0/1 models use the same world. It commits two
checkpoints, leaves a partial temporary manifest, then force-terminates only its
own engine. Fresh normal scene launches inherit the production `_ready` unchanged;
their test-only constructor assigns the isolated cache root before startup.
They do not invoke the restore method to manufacture a startup success.

Cases cover newest restore, broken latest JSON, missing geometry, wrong bone
binding after asset validation, missing audio, no valid generation, live-writer
exclusion, resolved-session exclusion, and explicit Save to a new HAS. They verify
native IDs/metadata/geometry hashes, exact portable scene values and editable
paint, camera/video/frame, independent audio timing, no partial failed world or
dialogs, stale deferred cancellation, original manual HAS bytes and retained
checkpoint files. One recovered H264/AAC movie has exact preview/source PNGs;
cross-process image rebuilds use the existing 384-channel/mean<0.002 edge bound.
All windows and native dialogs stay on the private Windows desktop.

Additional cases cover a live identified writer, a controlled PID/creation-time
mismatch using two actual process creation times, matching/mismatching current
reader identities, malformed stored tokens and an unavailable helper. These
exercise normal startup, not a manual restore. The mismatch is an owned fixture
simulation; the test does not force Windows to recycle a real process identifier.
`python -u tests/verify_recovery_identity.py` adds headless domain and actual
Windows sidecar/discovery checks, including unsigned-64 token bounds, unknown
owners, old PID-only records, corrupt sidecars and unchanged scene bytes.

The forced-exit proof checks that neither the post-termination code nor the scene
cleanup hook ran. A zero process exit alone is not graceful-exit evidence: the
pinned [Godot Windows implementation](https://github.com/godotengine/godot/blob/4.6-stable/platform/windows/os_windows.cpp)
uses exit code zero when forcibly terminating a process. The
[OS API reference](https://docs.godotengine.org/en/4.6/classes/class_os.html#class-os-method-kill)
describes process termination. No engine code was copied into Studio.
Microsoft documents [process handles](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocess)
and [immediate liveness checks](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).
Microsoft documents [PID reuse after process-object lifetime](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/ns-processthreadsapi-process_information)
and [creation-time query rights and FILETIME units](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes).

See the latest progress memo for actual completed runs and canonical-save status.
Earlier failed harness attempts remain retained, not reported as app passes.

## Remaining recovery work

This completes the default newest-valid attempt/fallback increment, not all of
addendum section13. The newer [bounded history](recovery_history.md) adds twelve
immutable metadata states, idle previews and Advanced browsing, while keeping
current/prior manifests readable. [Time or completed-edit scheduling](recovery_schedule.md)
uses the same checkpoint path.
Shared-asset cleanup, concurrent quota locking, legacy PID-only reuse ambiguity and
large-cache startup performance remain open. Loading is synchronous. No real disk-
full, hardware power-cut, hostile-native-parser or universal recovery guarantee.
Temporary camera navigation, uncommitted gestures and Undo history are not yet
checkpointed; changes since the last completed checkpoint can still be lost.
