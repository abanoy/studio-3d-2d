The extra cached-exit-code sentinel guard in my unrun ownership draft is incorrect for a legitimate Windows exit0xFFFFFFFF. Remove that one guard before porting. The frozen candidate itself was not changed by this review.

The [pinned Windows getter](https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/platform/windows/os_windows.cpp#L1517-L1566) returns int, including its DWORD/cached exit value. Consequently0xFFFFFFFF is exposed as-1, which collides with the missing/running/query-failure sentinel. That return value cannot prove map absence.

Exact draft control flow:

- source/src/source_import.gd:105 returns from _release_completed_preparation when that value equals-1, leaving _preparation_map_reserved=true and the old _preparation_map_pid intact.
- _process at279-282 nevertheless continues and assigns public pid=-1, then follows the existing status/adoption behavior.
- A subsequent import is not blocked: launch at210 checks only public pid>0. A new successful actual _spawn_preparation at94-95 overwrites the private map PID/reservation. The old completed entry is then unreachable through this component. Thus the draft leaks the old session resource; it does not block the next import.

The correct narrow invariant is already available: the actual base creator reserves its own successful child only in exact pinned Windows Godot, and this component is that reservation's sole map consumer. Polling/exit-code queries do not consume it. Once that known child has stopped, clear the reservation before its one mapped release regardless of the cached exit value. Keep the existing live-child running guard, sole-owner/pinned-engine guard and no-retry behavior. Do not introduce an absent-map inference from signed exit values, generic raw-PID fallback, a live-preparer kill, or a new teardown architecture.

Proposed additional unrun fixture control for the later authorized lease: add one gated authored Python refusal mode which writes its fresh controlled status and exits with SystemExit(-1). Observe its actual PID live while gated and the component's reservation; after its controlled exit, the getter should report-1. Actual _process must still call the real mapped release seam once, clear both reservation fields/public pid, decline adoption, and leave project/history state unchanged. Repeat helper/poll/teardown calls must cause no second release. With the current sentinel guard, the reservation/release assertions would fail; after removing it, this exercises the intended invariant. It adds one ordinary completion case, provisionally nine checks, to the previously planned44.

The-1 getter before and after release is inherently ambiguous, so that negative-exit case alone must not claim observable map disappearance. Pair it with the existing actual0/1/2 exit controls, which observe their cached code before release and-1 afterward, and the exact pinned source behavior. Record the real release-call path/return without requiring OK from TerminateProcess on an already-exited child. No deliberate second kill or PID-reuse probe is needed.

This is static review only. No runtime, Godot, Python worker, WinAPI probe, main/docs/HEAD mutation or change to the frozen candidate occurred. The current canonical lease remains untouched.
