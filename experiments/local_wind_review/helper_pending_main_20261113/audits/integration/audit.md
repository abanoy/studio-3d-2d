# Pending-helper integration audit

Read-only main integration review; no source edits and no graphical launch.

## P2: Popup Escape does not reach the preview stop handler

`src/secondary_helper_editor.gd:91` connects only `close_requested`. Root `app._input` reaches the preview through `global_patch_event`, but events delivered to the popup belong to its own Viewport. The isolated headless probe sent Escape into an actual Window: its child observer received one event, while the owning app observer received zero. The separately implemented Wind Review already forwards `Window.window_input` explicitly.

Connect the loose-part Window's `window_input` signal to a helper callback that forwards **key events only** to `pending_preview.global_event` and marks the popup event handled when consumed. Forwarding popup mouse events unchanged would mix popup-local positions with the main canvas coordinate path.

Regression: exercise the actual popup signal boundary while preparing and/or running, then require stopped state, unchecked master, restored source-owned geometry, one transport release, and no late candidate resurrection. Retain the existing root-input Escape checks separately.

## Evidence and scope

`window-input-probe-process.log` records the accepted waited subprocess native exit0 result: `app_seen=0`, `popup_child_seen=1`. `window-input-probe-engine-python.log` is its engine log. The initial direct PowerShell invocation produced only the banner and is retained as **unusable**, not a test pass. No unknown process was killed; root will perform the authoritative host check before the next graphical test.

No additional concrete regression was found during static review of stop/changed cycles, teardown, peer ownership, temporary checks versus Apply inclusion, hidden import/transfer, runtime resolution, and retained worker cleanup. This is a scoped review, not a fresh functional pass. Exact inspected source, probe and runtime hashes are in `audit.json` and `INDEX.json`.
