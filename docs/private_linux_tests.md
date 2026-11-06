# Private Linux graphical tests

Provision a separate local X server before using a verifier's
`--isolated-display :102` option. The number is an example; verify that the
selected server belongs to this test session. Do not point this option at the
owner's display. The existing Windows private-desktop launcher remains in use
on Windows.

Every verifier exposing this option calls `run.configure_private_display()`.
For direct Python harnesses, call it before constructing commands or copying
`os.environ`, then launch through `run.command()`. Graphical commands check an
X11 connection, require the selected DISPLAY to remain unchanged, and pin the
X11 engine driver before the script argument separator. Missing X11 refuses
before launch. Headless commands still work without that server.

Godot 4.6 can attempt Wayland after an X11 failure even with an explicit X11
driver. Configuration therefore also creates an empty owned mode-0700 runtime
directory and selects an absent Wayland socket in it. This isolates fallback
if the X server disappears after the connection check. The directory is removed
when the Python runner exits. No owner desktop environment setting is changed;
these environment changes belong to the test runner and its children. Ordinary
interactive launches do not enable this guard.

Validation on 2026-11-06: 15 focused Python tests; full Python discovery ran 312
checks with 311 passes and one existing independent-MMD-reader skip. Actual
engine probes used the private X11 server, refused a missing server before
launch, and ran headless with that server absent. A simulated loss after the
preflight check failed to launch and made no connection to a controlled socket
representing an inherited Wayland session. The actual cel-tool GUI probe passed
10 checks; the updated reference-color verifier passed 13 checks and encoded a
movie. These probes do not establish physical mouse/tablet or Windows acceptance.

Session proof is outside the checkout under
`/workspace/has-handoff-audit/private-display-final/verification.json`,
`private-display-final-color`, and `private-display-python-all.log`.
