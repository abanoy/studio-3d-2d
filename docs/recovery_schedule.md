# Recovery by time or completed edits

Recovery remains enabled by default, every one minute. In Advanced > Recovery,
choose By time (0.5–10 minutes) or After edits (1–1000 completed edits, initially25).
Simple keeps these controls hidden and uses the same protection. Preferences last
through New/Open in this app session, but reset at launch. They are not scene data.

A changed committed command counts once: a long stroke counts on release, not for
each motion segment. Creating a cel is a separate edit. Successful changed Undo
and Redo also count. Layer visibility counts when its actual value changes.
Navigation, selection, playback, mode/preferences and identical stored values do
not count. Counting stored values can include an explicit key with newly stored
fields even when its view appears unchanged. Existing Undo grouping is preserved.

The ordinary one-second timer checks the selected schedule. Pending work waits
until brush/camera/pose/timeline gestures, playback, live physics, export and
dialogs finish. A reached edit threshold stays pending while busy or disabled;
re-enabling can protect it on the next idle tick. Lowering a threshold can protect
edits already counted. Changing modes does not discard the pending count.

Only a successful checkpoint resets the count. A failed write retains the count
and previous valid state, reports failure and waits30seconds before an automatic
retry. Checkpoint now bypasses scheduling/disable/backoff, but still waits for safe
interaction state. Both modes use the existing journal and deferred idle preview.
An explicit request stays queued while a preview worker or interaction is active;
it runs when safe even if automatic recovery is disabled. New/Open and a fully
current manual Save clear the old request. Preview and checkpoint writers serialize.
They never clear the project unsaved marker or overwrite a manual HAS.

A successful manual Save resets the count and time deadline only when it saved
the current revision. Edits made after an asynchronous save snapshot remain dirty
and counted. New/Open begin a fresh document count. A failed Save does not consume
pending edits. Project/model/world/HAS schemas and legacy loading are unchanged.

During a lesson, minute-based protection can also save changed teacher state and
playhead after a manual Save has left the scene clean. It does not mark the scene
dirty, create Undo or count navigation as authored edits. Action mode keeps its
existing edit threshold; Checkpoint now can protect pending lesson state at once
when idle. Only a successful checkpoint acknowledges the teacher state, so failed
writes retain it for retry. See [lesson recovery](lesson_recovery.md).

`python -u tests/verify_recovery_schedule.py` runs the real hidden app. It routes
Advanced controls and a multi-segment stroke, checks meaningful changes/no-ops,
Undo/Redo, all interaction guards, the natural timer, disable/re-enable, explicit
checkpoint, failed write/backoff/retry, minute deadlines, New/Open, later async
Save edits, original manual bytes and controls reachable in a1200px window.
The failed-write case uses an owned empty directory at the temporary-file path;
it is not a physical disk-full/power-cut test. Deadline cases simulate elapsed
time; the idle timer case actually waits for the ordinary timer callback.

See the latest progress memo for completed source/saved-copy runs. Checkpoint writes,
preview readback/image copies and value comparisons remain synchronous; no universal
input-latency guarantee. Shared-asset cleanup/concurrent quota/PID reuse and other
limits in [history](recovery_history.md) and [startup](startup_recovery.md) remain.
