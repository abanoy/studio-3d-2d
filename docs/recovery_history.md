# Bounded recovery history

Advanced > Recovery > Recovery History shows retained states with UTC timestamps,
frame numbers and256x144 previews. Select a row to see its preview, then restore
as an unsaved copy. Replacing unsaved edits asks for confirmation. Ordinary Save
still chooses a HAS destination and never silently replaces the earlier manual
save. Saved/dismissed sessions stay browsable in Advanced; they remain excluded
from automatic startup recovery. Simple Recover offers only recent choices.

## One logical journal, shared scene data

Each managed session has a `journal.json` catalog with a versioned, checksummed
payload and a prior `journal.backup.json`. It references at most12 immutable
`history_<sha256>.json` scene metadata snapshots, sharing existing geometry, WAV
and content-addressed cel PNGs. This is a journal/catalog plus a shared content
pool, not repeated full copies or Git internals. Native model/world/HAS formats
are unchanged. Older Studio versions can still use current/prior project.json
files; they cannot browse the new history.

Both legacy generations are adopted before their first normal rotation. A
snapshot's bytes must match its hash filename before the ordinary full loader
validates assets, cels, audio, model bindings and timing. Index checksum/JSON errors
fall back quietly to the previous index; legacy current/prior files also remain.
Equal timestamps use revision ordering. A missing/corrupt thumbnail does not
invalidate a recoverable scene. Preview PNG byte size and header dimensions are
bounded before decoding.

Writes flush a temporary file before rename, commit the index after immutable
objects, then prune exact journal-owned metadata/preview filenames not referenced
by the current or rollback catalog. Normal operation retains12 states plus at
most one rollback generation; alias project files remain separately readable.
No recursive deletion or source-asset editing. Shared geometry/audio/cel garbage
collection is not yet implemented; retained old blobs can still fill the existing
512MiB global budget. The conservative preflight also reserves6MiB for journal
metadata/transient files. Concurrent quota locking and physical power-loss/full-
disk guarantees remain open. Cache data is private and is not included in HAS.

## Previews and responsiveness

A successful checkpoint queues preview work for a completed idle render frame.
The callback checks session, revision, frame, temporary camera and interaction
state again. Playback, live physics, exporting or intervening edits cancel it;
the checkpoint remains valid without a preview. It reads the existing3D viewport
and scales copies of active visible cels, without evaluating/recording a camera
key, changing Undo or touching original RGBA data. It represents scene/drawing
content in the temporary view, not the application chrome, canvas zoom/pan or all
selection overlays. Restore currently uses the saved shot; unkeyed navigation
and Undo history are not yet checkpointed.

The idle callback now reads the viewport and copies active cel images; it starts
one low-priority background worker for resizing, blending, PNG encoding and journal
I/O. New edits/playback can continue from independent data while it works. Another
checkpoint waits without consuming edits; explicit requests stay queued even if
automatic protection is off. New/Open can proceed and old-session failures do not
change their footer. Teardown joins the worker. See [preview worker](recovery_preview.md).

Earlier synchronous callbacks peaked near202ms and later around28ms; those remain
historical observations. GPU readback/image copies and the checkpoint itself are
still synchronous, so this is not a universal input-latency guarantee. Background
CPU/I/O and main-thread capture are measured separately in current reports. Shared-
asset cleanup, low-resolution/asynchronous readback and large-cache profiling remain
required. See the latest memo for final measurements and actual saved-copy status.
Time and completed-edit triggers share this journal; see [scheduling](recovery_schedule.md).

## Verification

`python -u tests/verify_recovery_history.py` checks real file retention, immutable
hashes, quiet index rollback, malformed payloads, failed index commits, unrelated
file preservation, preview bounds and revision ties. Real hidden app tests create
18 changing states, verify all stable previews, route the Advanced button/list/
Restore confirmation, check dialog bounds in a1200px window, preserve native
MMD/GMod/SFM/VRM0/1 data, save/reopen packed HAS, export a synchronized H264/AAC
movie and reject stale/busy preview work. Three fresh normal-startup processes
then verify newest and deeper fallback, including damaged current/prior states
AND a damaged current catalog. Native availability is reported explicitly.

The older startup matrix deliberately constructs a legacy two-generation cache;
it remains compatibility evidence, while this suite tests current journals.
Cross-process rebuilds keep the established small mesh-edge tolerance; a reopened
preview and its exported PNG must match exactly. All graphical tests use private
Windows desktops with no visible fallback. No clean-machine, arbitrary-GPU,
physical-input, subjective-audio/native-fidelity or hostile-file certification.

Primary API references: [Godot Image](https://docs.godotengine.org/en/4.6/classes/class_image.html)
and [RenderingServer](https://docs.godotengine.org/en/4.6/classes/class_renderingserver.html).


Restart-fixture identity: tests/windows_owner_guard.py retains a SYNCHRONIZE handle
to the actual stopped fixture writer across readers, verifies it has exited, and
closes it afterward. This prevents PID reuse from changing that test identity;
new production owner sidecars now also distinguish creation times, while
conservatively protecting unknown and legacy live owners. One pre-guard no-candidate run was retained without a confirmed
cause; later read-only inventory found valid older states. No restore assertion or
live-writer protection was removed. Windows identity lifetime reference:
https://learn.microsoft.com/windows/win32/api/processthreadsapi/ns-processthreadsapi-process_information

Later increments implement [proven-owned blob retention](recovery_blob_retention.md)
and [shared quota reservations](recovery_quota.md). Earlier remaining-work notes
above describe their original increment; arbitrary orphan cleanup and physical
power-loss/Windows target acceptance remain separate.
