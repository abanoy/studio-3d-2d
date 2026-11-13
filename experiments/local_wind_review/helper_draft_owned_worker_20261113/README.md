# Owned helper preview worker: next CPU candidate

This output-only increment adds a Windows Python controller and exactly one Job-owned Python CPU child to the prior preview-purpose protocol. It is not hosted in Godot, connected to the helper window, or accepted as a visible feature. No main source, existing prototype, renderer, native converter, or previous indexed packet was changed.

`candidate/tools/wind_preview_owned.py` owns the child through its retained CPython 3.13 process handle and a non-inherited Windows Job. `wind_preview_worker.py` waits on stdin until assignment succeeds, then calls the existing helper builders through the copied preview protocol. The copied `wind_helper_preview.py` is byte-identical to the previous packet (SHA256 `1d9111aee40fcd4e976ac487d6ec8e6266382ae1b49cb5410aee398d89a00c46`).

The controller records and verifies exact PID plus creation FILETIME, generation, nonce, request hash, worker/protocol/adapter/helper/Job-layout source hashes, and the approved Python executable path and SHA256. Different Python paths require an explicit approved fingerprint. Before admission it rechecks the launch-bound code and Python bytes. These are local integrity checks for a trusted controller; they do not authenticate a hostile process or protect against a hostile writer racing file reads.

The child emits exactly one bounded ASCII completion record through stdout. Both stdout and stderr are concurrently drained into capped buffers (16 KiB and 256 KiB), discarding excess while flagging failure. Admission requires native successful exit, clean EOF, empty stderr, matching ownership/source/executable/draft identity, original-source/receipt checks, and confirmed closed Job and process handles. A buffered valid frame followed by a hang or nonzero exit cannot admit a candidate. The expected receipt digest remains in parent pipe memory, rather than being recovered from the editable receipt itself.

Cancellation uses the retained process handle and assigned Job only. A stale PID/creation/generation/nonce cancellation token is refused before touching a replacement. Job kill-on-close, active-process limit 1 and a 1 GiB memory limit bound the CPU child; no generic PID lookup or kill exists. Before assignment, the worker cannot build without its gate and EOF stops it. There is no Godot/private-desktop launcher call: the existing private-desktop module supplies only its native Job structure layout.

## CPU evidence

`cpu-tests.json` and `cpu-tests.log` record **16 tests, 0 failures, 0 errors**, using real hidden Windows Python children and synthetic two-panel GLBs. The grouped framing test exercises nine separate child faults. Tests import this candidate adapter, worker and protocol, rather than duplicating their predicates. They cover successful two-member preparation; foreign imported worker refusal before helper calls; stale/exact cancellation; changed context; timeout; assignment failure; completion followed by exit 7 or a hang; old-generation completion and replacement cancellation isolation; changed original source stamp, receipt, code hash and Python fingerprint; duplicate/trailing/invalid completion, foreign PID/creation/generation, both pipe caps and unexpected stderr; failed Job close refusing admission and later cleanup; and blocked descendant creation.

`cpu-owned-receipts.json` preserves the successful run's exact native owner tokens, exit and cleanup evidence for every recorded job. Full synthetic jobs remain only under `cpu-results/` and are excluded from the compact publication. Tests inject wrapper children to exercise transport faults; the normal command always points to the indexed worker.

The initial expanded run had 14 passing tests and one test harness error: Windows `CreateProcess` rejected the longest generated working-directory path (WinError 267). Its log and report are retained as `cpu-tests-failed-path.*`. The harness now uses short hashed testcase directories and retains each full name in `testcase.json`. No Windows long-path setting or platform limit was changed. This is an explicit corrected harness run, not a hidden retry.

To rerun from the actual main project root with the existing approved Python:

```powershell
& 'C:\Program Files\Python313\python.exe' -B output\wind-helper-draft-prototype-20261113-next\tests\test_owned_worker.py
```

This writes fresh synthetic CPU outputs and updates this packet's test summary, so copy the indexed packet before rerunning a frozen publication. It starts no Godot, graphics, Blender or native model conversion.

## Boundaries and next step

The concrete GDScript hosting seam and remaining gates are in `INTEGRATION_SEAMS.md`. The current unit of ownership is **one Python controller plus one Job-owned child**, not a Godot-owned worker process. An actual app launch/cancel/teardown/pipe bridge must be implemented and independently verified before main integration. Closing this adapter after a successful preparation only closes process ownership; it does not invalidate the prepared `DraftLease`. The future Node must synchronously invalidate prepared tickets on helper close, edit, save or other context change. Abrupt controller death before/after Job assignment was reasoned from the gate/Job design but was not exercised here. No real Godot imported binding snapshot, preview simulation, original-physics preservation, canvas cleanup, Apply/Undo or rendered acceptance is claimed.

Microsoft documents [Job ownership and kill-on-close](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) and [creation FILETIME from a retained process handle](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes). Python documents [subprocess pipe draining and Windows termination semantics](https://docs.python.org/3.13/library/subprocess.html). The adapter's tested private `_handle` boundary is deliberately restricted to the existing CPython 3.13 runtime.
