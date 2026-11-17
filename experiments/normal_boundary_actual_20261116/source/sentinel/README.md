# Hidden placement proof for the background normal probe

This is an **unexecuted derivative**, not a successful normal capture. The first
root attempt completed numerical capture but failed the existing isolation gate
because background Blender supplied no observable GUI thread or owned window.
Its exit2, receipt and private output remain a failed attempt. No comparison is
authorized from that failure.

The new capture creates a real, zero-size, disabled top-level system `STATIC`
window in its current thread. `WS_POPUP|WS_DISABLED` and
`WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW` are checked; `WS_VISIBLE` and `WS_CHILD` are
absent. Owner PID/thread, hidden state and zero rectangle are checked. The code
never shows, activates or changes a desktop. It holds the window through the
unchanged capture and destroys it in `finally`; cleanup failure stays nonzero.
Interactive Blender refuses before any window is created. The original offline
and disabled-autoexec checks remain byte-exact inside the original main.

This is real placement instrumentation. The unchanged private-desktop monitor
still independently finds the actual child PID's HWND on the expected private
desktop, and still refuses wrong placement or foreground activity. There is no
fake `--headless` argument and no wrapper/tool/main-app edit. The HWND proves
background-process placement only; it is not Blender GUI or render evidence.
Microsoft documents enumeration of all top-level desktop windows in
[EnumDesktopWindows](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumdesktopwindows),
the system-class and style interface in
[CreateWindowExW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createwindowexw),
and same-thread destruction in
[DestroyWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-destroywindow).

All six original capture functions, including the complete numerical/private
main body, are AST-exact; main's raw source bytes are also exact. Five support,
comparison, staging and test files are copied byte-exact from sealed predecessor
`49e7f506…73856`. Only imports, the inline placement context and an entry wrapper
are added. After successful cleanup, the wrapper appends the public
`background_isolation_sentinel` policy field. It does not alter any original
capture field or private numerical result. The original capture marker alone
still cannot certify isolation.

Root uses the copied `stage_after_full_pass.py` with a fresh attempt2 path.
The original12 locks pin all inline capture code and the four analysis pins
remain exact. The copied generic staging description is unchanged; for this
derivative `ROOT_ADDITIONAL_REQUIREMENTS.json` adds strict
`private_window_seen=true`, the public cleaned-sentinel field and separate
stdout marker. Keep every prior receipt/source/input/runtime/full-release gate.
Only root may create a lease, run Blender, observe closure or start comparison.

Source/fault tests use a synthetic ctypes API object and never invoke Win32,
Blender, CIM or Git. They exercise hidden creation, ownership refusal, ordinary
and exceptional cleanup, failure refusal and interactive-mode refusal. The
inherited fourteen support tests remain synthetic. Their results do not prove
that Windows or the monitor observed this new HWND; actual attempt2 must do so.

`SETUP_REFUSALS.json` retains a source-edit shell quoting refusal and an incorrect
copied wrapper-hash expectation caught by the first synthetic test. The corrected
test anchors the expected wrapper hash to the exact full-source manifest instead.
No product code, numerical tolerance or placement assertion was relaxed.
