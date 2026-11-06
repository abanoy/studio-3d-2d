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

The visibility and World/Local recording commands also accept an isolated run
folder and use the configured FFmpeg/ffprobe paths:

```
python tests/verify_visibility.py --isolated-display :103 --output /tmp/has-visibility-new
python tests/verify_physics_recording.py --isolated-display :103 --output /tmp/has-recording-new
```

Each folder must be new. Both wrappers generate their own original WAV fixture,
keep preferences/recents/recovery/results local to the run, and preserve explicit
missing-native skips. Explicit `--output` avoids the historical shared report
files. Omitting it uses a unique folder and also refreshes the old default report
paths for downstream Windows suites. Windows graphical runs retain private
desktop receipt checks; Linux uses the display guard. The raw GDScript scenarios
still support their original no-argument full-verifier paths.

Fresh2026-11-06 private103 runs passed both explicit and default output modes:
47visibility and17domain+48recording checks with48frame H264/AAC, one-second
cue onset1.0000417s, source-WAV hashes unchanged and3/5native skips respectively.
Default reports matched their new per-run results. Full Python312run311pass with
one existing independent-reader skip. This is test portability/isolation work;
application behavior and saved formats are unchanged.
