# Windows encoder exit research

The observed stale-output PASS is plausibly explained by FFmpeg's older refusal behavior, without a Godot lost-exit bug. Official FFmpeg n7.1.1 returns `AVERROR_EXIT` after the observed existing-file diagnostic, and its main function maps that value to process exit 0. Current FFmpeg master instead returns `AVERROR(EEXIST)`. This version distinction matters. Sources: [overwrite refusal](https://raw.githubusercontent.com/FFmpeg/FFmpeg/n7.1.1/fftools/ffmpeg_opt.c) (682–705), [exit normalization](https://raw.githubusercontent.com/FFmpeg/FFmpeg/n7.1.1/fftools/ffmpeg.c) (934–942), [current master](https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/fftools/ffmpeg_opt.c) (782–805).

A read-only ASCII scan of the installed ffmpeg.exe identifies `N-118448-g43be8d0728-20250208`. Exact abbreviated-commit fetches were unavailable through the web tool; the source-to-installed match remains an inference, not binary/runtime certification. No encoder or Godot was launched by this research.

## Godot 4.6 Windows contract

`execute_with_pipe` creates a Windows process and retains its process/thread handles by PID. Its `blocking=false` concerns pipe reads, not exit-code interpretation. `is_process_running` queries `GetExitCodeProcess`: a completed child's DWORD is cached unchanged; repeated polls return false without destroying that cached code. `get_process_exit_code` returns the cache, otherwise queries the same handle; unknown, still-active or query-failure states yield -1. There is no nonzero-to-zero mapping in these functions. Ordinary polling does not reap the Windows child. The kill path separately removes the map entry and terminates with zero; encoder cancellation must remain an explicit failure. [Platform implementation](https://raw.githubusercontent.com/godotengine/godot/4.6-stable/platform/windows/os_windows.cpp), 1198–1315 and 1491–1566.

`ProcessInfo` defaults to running=true and code=-1. The GDScript binding forwards the methods directly. The IO object owns pipe handles and read/error state, with no process-exit mechanism. [Process record](https://raw.githubusercontent.com/godotengine/godot/4.6-stable/platform/windows/os_windows.h), 157–164; [binding](https://raw.githubusercontent.com/godotengine/godot/4.6-stable/core/core_bind.cpp), 379–385 and 421–427; [pipe object](https://raw.githubusercontent.com/godotengine/godot/4.6-stable/drivers/windows/file_access_windows_pipe.cpp), 35–50 and 74–119.

Microsoft distinguishes the API's successful BOOL from the returned child's DWORD; 259 denotes still active. Godot's source checks the BOOL and does not turn failure into successful exit0. [Microsoft contract](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getexitcodeprocess). Installed Godot's file metadata identifies 4.6.stable.official; exact runtime counterfactuals remain required.

## Local false-success chain

The preserved pre-fix encoder computes the fixed `movie.mp4` path and passes FFmpeg `-n`, but does not reject an existing output before spawning. It accepts code0 plus file existence. Both spike scripts reuse `output/spikes/movie.mp4`; the preserved movie predates this run (modified 2026-11-12T02:00:14Z, 138284 bytes), while the current log records the refusal and Exit0. Thus file existence proves neither this attempt's output nor the expected audio. The canonical AAC predicate correctly failed rather than accepting stale silent video. All original AAC/onset/stream assertions should remain.

Independent additional risk: `finished_path` is not cleared at attempt start. Reusing the same encoder after a successful attempt can expose the prior path on a later failure. Clearing it does not replace checking the returned error.

## Focused counterfactuals for root's exclusive lease

| Case | Fresh owned setup | Required result |
|---|---|---|
| Raw exit37 | Approved Python child writes a small stderr marker, then exits37; poll repeatedly before and after finish | Pipe PID remains the child's PID, exact code37 remains stable; independent Python subprocess/WinAPI observation agrees |
| Partial plus37 | Fake encoder accepts the existing argument array, writes bounded bytes to the last output argument, then exits37 | Encoder reports failure and leaves finished_path empty despite the new partial file; partial/log retained |
| No file plus0 | Child exits0 without creating output | Encoder reports missing output |
| Existing output | Precreate known bytes and record hashes | Product refuses before spawning, preserves exact bytes; actual FFmpeg refusal may itself be0 in this installed build |
| Zero garbage | Child writes bounded invalid MP4 bytes then exits0 | Characterizes that code+exists alone cannot certify valid media; use an explicit output-validation contract if this must be rejected |
| Reuse after success | Same instance: success, then partial/error or preexisting refusal | finished_path clears for failed attempt; no stale successful path |
| Fresh real movie | Distinct fresh silent and tone fixture folders | Real stream/frame/duration/rate predicates, AAC presence and decoded onset still pass independently |

The known source path predicts a genuine nonzero child is rejected even if it writes a partial file. That prediction has not been tested here. Do not replace process exit checking with broad log parsing. If runtime proves the engine reports37 as0, retain the direct-child/process identity evidence first and use a reliable supervised child exit receipt bound to that attempt, rather than guessing from stderr. If exit37 is preserved, the existing-output refusal/fresh fixtures address this observed bug directly; any media-integrity validation is a separate explicit contract.

Pipe reads are nonblocking and may be short; the current encoder only takes one final 65536-byte read and ignores pipe get_error. This can truncate evidence, but the inspected pipe implementation does not convert exit status. Draining bounded remaining stderr, and stdout if a child uses it, is an evidence/liveness concern distinct from the zero-code explanation.

`local-observations.json` hashes root's preserved pre-fix snapshot and the installed FFmpeg executable before/after the read-only probe. No main source, original output, registry, Steam or runtime files were written. Only this research output subtree was created.
