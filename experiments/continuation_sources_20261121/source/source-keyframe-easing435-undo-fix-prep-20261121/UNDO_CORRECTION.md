# Reproduced actual camera Undo defect

The original435 port remains unchanged. Its88 headless controls prove key-array Undo/Redo, not camera-view restoration. A stronger24-control fixture reproduced one failure in Classic Simple: all24 controls executed,23 passed, and Undo restored original keys while the renderer retained the baked preview position. Root process exited1, was reaped, and every admitted source/runtime input and the parent environment stayed unchanged. Exact result/logs/fixture are retained here. Other variants were correctly unrun after the first failed case.

This successor tags only its own Bake history command with camera_timing_bake. The ordinary app history path refreshes the authored camera only for this explicit keys command after restoring before/after keys. Existing free-camera behavior for all untagged camera edits is unchanged. The tag is session history, not saved animation metadata. The editor spy controls still require complete deep before/after dictionaries; additional real-app controls now require both Undo and Redo camera positions at the current frame.

This correction is not adopted into Main. Headless requalification and independent source review are pending for these exact successor bytes; visible camera/lens behavior, actual capture/movie, packed save/cold reopen, GUI input and performance remain separate unrun gates.
