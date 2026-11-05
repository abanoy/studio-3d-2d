# Background recovery previews

The normal app still captures a completed idle render frame with session/revision/
frame/view/interaction guards. On the main thread it reads the3D viewport and makes
independent copies of active visible cel images. One low-priority worker owns those
CPU images, resizes/blends them to256x144, encodes PNG and updates the existing
checksummed journal. It touches no live nodes, GPU textures, original cels, model
data or shot keys. After capture, later edits cannot alter the historical picture.

Normal app processing polls completion and joins only a finished thread, without
waiting on a live worker. The next checkpoint defers while the worker owns journal
writes, retaining dirty state/action counts. Explicit Checkpoint now stays queued
until the worker and any interaction finish, including with automatic recovery off.
New/Open and exact-current-revision Save clear queued requests for the old state.
There is only one active preview, with no growing image queue. Changing documents
does not wait; old-session failures cannot overwrite the new session's footer.
Normal teardown joins any remaining worker before freeing its owner. OS/file I/O
can delay that final join; the thread is not forcibly killed during an index write.

No journal/HAS/model/world schema change. Atomic index/rollback and metadata/hash
validation remain unchanged. A preview failure leaves its checkpoint recoverable,
with quiet footer feedback. Startup can restore a state whose preview never finished.
History reads can see the prior or committed atomic catalog; normal checkpoint and
preview writers do not concurrently mutate it.

`python -u tests/verify_recovery_preview.py` exercises the actual app and worker.
A test-only subclass holds the file-write boundary with a semaphore, while real
application frames, routed drawing and timeline playback continue. It verifies
snapshot isolation, one writer, queued manual checkpoint with automatic recovery
off, two intact historical entries, a real owned temporary-file failure, New while
an older worker is active, stale failure feedback and actual app teardown joining.
It preserves original manual HAS/GLB hashes. Holding the boundary simulates slow
file work; it is not a physical disk stall/power-cut test. The history suite also
waits for preview completion explicitly and runs18 real native combined snapshots,
normal older-state restore, HAS, synchronized MP4 and fresh-process fallback.

Current reports split main capture/copy time from worker time. Their sum remains
the legacy `last_recovery_preview_ms` diagnostic; it no longer means one UI pause.
Earlier synchronous202ms peaks are historical. GPU readback/full-size image copies
and the checkpoint itself remain synchronous; no universal input-latency/frame-rate
guarantee. Low-resolution/asynchronous GPU capture, asset cleanup/concurrent quota,
large-project profiling and other reliability work remain unfinished.

Thread/resource ownership follows the pinned [Godot4.6 thread-safety guidance](https://docs.godotengine.org/en/4.6/tutorials/performance/thread_safe_apis.html)
and [Thread lifecycle API](https://docs.godotengine.org/en/4.6/classes/class_thread.html).
No thread-safety checks are disabled and rendering/physics thread settings are unchanged.
