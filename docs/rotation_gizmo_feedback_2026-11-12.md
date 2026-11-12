# Rotation rings — deferred owner feedback

Recorded November 12, 2026 as an addition to the paused-work notes. The owner
has not asked to resume implementation. No code changes, app launches or tests
were performed for this report.

**Resumed update:** the owner has now resumed work. Ring direction and focused
overlay bounds have software fixes:131checks pass, while the same checks with
the two old source files produce27real failures (including all24projected arc
cases). Actual overlay pixels confirm clipping. See
[evidence](benchmarks/rotation_gizmo_fix_2026-11-12.json). The additional
camera-facing ring is still pending; no owner/device approval is inferred.

## Requested behavior

- **Correct the RGB ring direction.** The owner reports rotation feels reversed,
  affecting at least the **top ring**, and requests inverting the affected
  direction. The exact axis, view and cause have not been reproduced. Do not
  assume every ring needs its sign flipped; start with the reported top ring
  and check the remaining axes and views.
- **Add a camera-facing relative rotation ring.** It should always face the
  camera and let the user rotate left/right relative to the current view.
  Intended interpretation for implementation review: a view-aligned ring for
  clockwise/counterclockwise rotation about the camera's viewing axis, alongside
  the existing RGB axis rings. The owner cites **SMH and SFM** as interaction
  references; their behavior was not independently inspected for this note.

## Work only after an explicit resume

Reproduce the direction problem from different camera positions and with the
existing local/world axis modes. Make dragging the affected ring follow the
intended visible rotation direction without changing unrelated controls.
Implement the additional view-aligned ring so it follows camera orientation
and offers a clear hit target distinct from the RGB rings. Check left/right
drags, rotated cameras, sign consistency, crossing angle boundaries, existing
axis rings and Undo/Redo. Verify ordinary pose/key editing and save/reopen as
relevant, using private Windows desktops and preserving original poses/projects.

This is a recorded request, not a diagnosed or fixed defect or a completed
acceptance result. Existing pause, owner-participation limits, unfinished
aggregate and ledger counts remain unchanged.
