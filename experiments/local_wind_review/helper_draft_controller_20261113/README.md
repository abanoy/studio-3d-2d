# Preview-purpose CPU controller candidate

This bounded output-only increment hosts `DraftLease` and `OwnedPreviewJob` in an explicit Windows Python CLI. It adds a framed start/poll/cancel/close transport, a retained declared-host lifetime handle, and abrupt-controller-death observations. The preceding 16-test packet is unchanged. There is no Godot Node, app/UI connection, graphics, Blender, native conversion, main edit or feature acceptance in this increment.

The process model is **host → Python controller → one Job-owned Python CPU worker**. The host supplies its explicitly authorized PID and creation FILETIME; the controller opens one query/synchronize handle, verifies that exact incarnation and retains it for liveness observations. This is an explicit host identity, not proof that the selected process is its operating-system parent. The tests include a separately created declared host to make this distinction concrete. No host PID is terminated by the controller.

The controller starts no worker or preparation before a valid start. It checks source/context/request data before creating the draft, then checks host liveness/EOF again after validation, after lease creation, immediately before delivering the worker start gate, after launch and before exposing prepared results. A review caught the slow-validation race behind these extra checks. Controller source is fingerprinted at startup and rechecked at those boundaries. The unchanged worker adapter independently pins Python and worker/protocol/adapter/helper/Job-layout source bytes through successful completion admission.

Dedicated capped input and output queues keep pipe reads/writes away from the ownership loop. EOF, parent exit, malformed/overflowed transport, idle timeout and output backpressure cannot require response delivery before child cleanup. Prepared polls refresh the original context and actual receipt against the trusted pipe completion SHA; cached worker success alone is insufficient. Cancel, close, EOF and host loss invalidate building and prepared tickets before disposal.

## Evidence

The final suite reports **17 tests / 0 failures / 0 errors**, using real hidden Windows Python processes and self-authored synthetic GLBs. It imports and drives the indexed CLI and adapter code. The tests cover normal start/poll/prepare/close; no job before valid start; replay/stale-ticket isolation; changed context and prepared receipt; malformed/duplicate-key/nonfinite/non-ASCII commands; overlong unterminated framing; wrong host incarnation; controller and Python pin mismatch; prepared and active-worker EOF; declared-host exit; host loss during validation and receipt admission; unread stdout backpressure; and abrupt controller death on both sides of worker Job assignment.

The abrupt tests kill only each exact created controller through its retained `Popen` process handle. The observer opens only query/synchronize handles for already known worker PID+creation identities, validates those identities and retains the handles to observe termination. It never holds a duplicate Job handle or terminates a worker by PID.

- Before assignment, a test hook pauses the controller before Job assignment or the start gate. Terminating that controller closes its worker stdin writer. The exact observed worker ends without a candidate. Its recorded exit is 1 in this final run: a closed stderr pipe can alter the error-exit code, so the test requires bounded exact-handle termination and no preparation, not a guessed code 2.
- After assignment, a hook verifies the worker is inside the specific owned Job. The real worker completes its gate/build, then the test wrapper closes stdin and sleeps for 30 seconds without further stdin reads. The observer confirms it is alive, terminates the exact controller, then observes the worker end within the four-second bound. That demonstrates kill-on-last-Job-close rather than cooperative stdin EOF. Windows reports worker exit 0 in this case; this is an abrupt Job termination observation, not an admitted successful worker completion.
- With stdout deliberately left unread after the first two events, bounded output backpressure closes the live Job and process handles, invalidates the ticket and exits 2 without exposing preparation.

`cpu-process-receipts.json` collates exact observer/controller/declared-host/worker owner identities, native signaled/exit observations, handle closure, worker receipts and controller outcomes. Full synthetic generated GLBs and jobs remain under `cpu-results/` and are excluded from publication.

The first 12-test run passed. The expanded run exposed harness issues, retained as `cpu-tests-harness-failure.*`: its unpaced polling exhausted the intentional command budget before reaching a delayed receipt hook, and Windows returned an expected closed-pipe `OSError 22` that the harness did not yet handle while still closing other handles. Poll pacing and guaranteed observer/Popen cleanup were corrected; no controller acceptance check or budget was relaxed. The pre-observer-review 17-test pass is also retained. The final indexed test source then passed all 17 again.

Rerun from the actual project root using the existing approved runtime:

```powershell
& 'C:\Program Files\Python313\python.exe' -B output\wind-helper-draft-controller-20261113\tests\test_controller.py
```

Rerunning writes fresh synthetic outputs and replaces this packet's test summary. Copy a frozen publication first. It does not start Godot or native model conversion.

## Remaining boundary

The CLI is operational under a Python CPU host only. Actual Godot process ownership, nonblocking Node transport, hidden model import/binding snapshots, original pose/physics/visibility preservation, canvas cleanup and separately guarded Apply/Undo remain future work. [GODOT_NODE_BRIDGE_PLAN.md](GODOT_NODE_BRIDGE_PLAN.md) gives the next bounded seam. The host-liveness checks cover service and admission boundaries, not cancellation of an indefinitely blocked filesystem system call. This is local integrity and lifecycle engineering for trusted code, not an isolation boundary for hostile processes, assets or filesystem writers.

Primary references: [Godot 4.6 pipe API](https://docs.godotengine.org/en/4.6/classes/class_os.html#class-os-method-execute-with-pipe), [Windows Job ownership](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [retained-handle creation timestamps](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes), [Python subprocess semantics](https://docs.python.org/3.13/library/subprocess.html).
