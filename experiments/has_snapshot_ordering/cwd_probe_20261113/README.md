# Headless current-directory concurrency probe

Actual result: **the suspected launch failure was not reproduced**. This does
not prove the race absent or explain the canonical body-animation failure.

At main `1236796865e677b150a2d7e2add20f2aac5325fe`, the isolated minimal Godot 4.6
project launched the approved absolute Python with `-I -B -c pass` serially:

| Phase | Launches | Launch failures | Directory churn iterations |
| --- | ---: | ---: | ---: |
| Control | 40 | 0 | 0 |
| Concurrent short-directory open/change | 80 | 0 | 6,401 |
| Concurrent 390-character-directory open/change | 80 | 0 | 4,968 |
| Control after threads | 40 | 0 | 0 |

All 240 children exited 0; no timeout or mapped-handle cleanup failure occurred.
The headless Godot process exited 0 in 8.697 seconds and its retained Popen was
reaped. Main source/HEAD and both approved runtime hashes were preserved.

Raw evidence remains in
`runs/1794602441029208700-3d929ffb`: request/command, engine/stdout logs, detailed
per-child results, process ownership and pre/post source/runtime proof. Only
fresh owned directories were created; no original/native models were read, no
main/Git changes were made, and no graphical/GPU/Blender/native worker ran.

The driver uses the actual unchanged `run.py` helper's literal `run.command()`
with its ROOT explicitly redirected to this minimal test project, `--headless`,
the approved exact Godot path and absolute log path. It starts at most one Python
child at a time, waits for its exit and then calls `OS.kill` only while that
owned PID still has the original Godot process-map entry. At this Godot version,
`kill` erases the map and closes original handles even when TerminateProcess
returns false for an already-exited process. The observed close return 1 is
therefore retained separately from the verified map removal; it is not treated
as a successful termination. Each child had already exited 0.

Godot 4.6 exposes no `OS.get_cwd`. The before/after samples use
`DirAccess.open(".").get_current_dir()` and are **intrusive observations**, not
atomic launch-time WinAPI CWD measurements. They observed the project path
(140 characters), the short path (138), and long path (390) during their
respective phases, with only the project path in both controls. WinAPI error
codes are unavailable through this Godot create-process API; this experiment
captured no 267 error and makes no such claim.

The source hypothesis is real: [DirAccessWindows::change_dir](https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/drivers/windows/dir_access_windows.cpp#L151)
temporarily changes process CWD under GLOBAL_LOCK; [OS_Windows::create_process](https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/platform/windows/os_windows.cpp#L1557)
reads CWD and calls CreateProcessW without that lock. HAS starts a snapshot
Thread before spawning its project worker. These facts identify a possible
concurrency seam; the passing probe does not establish its effect in HAS.

The Windows implementation supplies a null application name and inherits the
calling environment. Bare executables consequently use Windows search rules;
this probe deliberately uses the approved absolute executable so executable
lookup is not the variable. [Microsoft CreateProcessW reference](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw).

Reproduce with the approved Python and `-B run_probe.py`. Every attempt receives
a fresh owned run folder and preserves prior evidence. This is a bounded
diagnostic, not product/native-fidelity or whole-application acceptance.
