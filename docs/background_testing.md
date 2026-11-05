# Background graphical tests — 2026-10-30

Owner requirement: agent tests/screenshots must not show windows or take focus on
the owner's desktop. `run.command()` now routes Windows graphical tests through
`tools/private_desktop.py` and installed `pythonw.exe`. Normal manual Studio
launches remain interactive. Headless unit tests use the windowed engine with
`--headless`; the version check suppresses a console window too.

The launcher creates a fresh private Win32 desktop, starts the actual windowed
Godot executable there, and never calls SwitchDesktop or an activation/input API.
The private desktop handle does not request the desktop-switch right. The Godot
console executable is a wrapper spawning another process; use the matching
windowed engine so the actual GUI owner can be verified. Standard output/error
pipes still carry test markers. There is no visible fallback if setup fails.

Windows desktop enumeration verifies that the engine's own windows are on that
desktop; foreground-PID observation checks for accidental activation. Only owned
test windows/PIDs are recorded, not user window titles or screen contents.
`output/private-desktop/*.json` receipts contain placement, exit and cleanup results.
A kill-on-close job contains the owned process tree, including native workers.
It is test infrastructure, not a hostile-file or security isolation claim.

The initial restricted context denied desktop creation before launching anything.
Use an approved host execution context for graphical checks; do not bypass that
failure by showing windows. Ordinary headless mode disables rendering and cannot
prove GPU captures. This approach retains the Windows/OpenGL renderer and hardware.

Actual worktree evidence: private GPU probe rendered on Intel Arc140V,640x360,
91sampled colors, plus a native popup image with expected color; private-window
placement and cleanup confirmed, no foreground test PID observed. The real Studio
helper-review workflow also passed37checks with screenshots, actual weighted skin,
Record, packed/linked HAS and H264/AAC1080p24 output from the private desktop.
Those helper changes are separate development work, not implied shipping scope of
this launcher fix. Saved-copy checks are recorded in progress_memo.md.

Focus observation is sampled; native desktop placement is the architectural
separation. Physical keyboard/tablet interaction and the user's manual foreground
experience are not certified by injected tests. No system settings, registry,
display modes, user windows or default desktop configuration are changed.

Primary sources: [desktop creation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createdesktopw),
[startup desktop](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/ns-processthreadsapi-startupinfow),
[desktop enumeration](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumdesktopwindows),
[job process-tree cleanup](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[Godot headless behavior](https://docs.godotengine.org/en/4.6/classes/class_displayserver.html).
