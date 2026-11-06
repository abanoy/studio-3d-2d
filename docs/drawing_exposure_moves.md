# Drag drawing exposures on the timeline

Click a drawing block to choose its layer and a frame within its hold. Drag it
horizontally to move the complete exposure along that same layer. A small hand
motion remains a click. Zoom the timeline for precise placement; the ruler and
drawing blocks share the same frame mapping.

The preview changes only the timeline block. Release commits one Undo command.
The cel keeps its stable identity, original Image/RGBA pixels, opacity and hold
length. Other drawings, sound, camera animation and world data remain independent.
The source drawing is still editable at its new frames.

An overlapping destination shows an invalid outline and refuses on release.
Nothing is automatically shortened, overwritten or shifted. The scene boundary
clamps the complete exposure inside the existing duration. This is horizontal
same-layer movement; cross-layer transfers and ripple edits remain separate.

Escape, right-click, focus loss or Undo cancels the uncommitted preview. Changing
project timing or entering another sequence waits until the gesture finishes.
Successful project switches and export startup cancel pending previews. A stale source/scene revision refuses
rather than applying a gesture to a changed document. Recovery defers while a
gesture is active and saves the committed exposure afterward. The latched timeline
gesture receives Escape before Select/Pick Color; starting it clears uncommitted
pixel previews while retaining the chosen drawing tool.

The command stores only layer/cel identities and start frames (charged512bytes),
with no raster copies. Undo/Redo resolves the current layer by stable ID across
parent/child scene switches. Existing cel creation/exposure and layer-property
history likewise finds the live layer after a scene is rebuilt. Drawing timing
history preserves live3D preview state.

A related frame-control fix prevents entering a shorter child scene from emitting
an intermediate max-clamp event that replaces its saved playhead with the child
end boundary. Frame, maximum and control value now update together with signals
blocked during that internal synchronization. User frame entry stays interactive.

There is no new saved drawing format. Existing cel start/duration fields retain
their meanings; longer/nested projects use their existing schema8 wrapper.

`python tests/verify_cel_timing.py --isolated-display :102` requires an explicitly
provisioned private dummy Linux display; Windows uses the existing private
launcher. It checks free/touching/overlap/boundary ranges, actual preview/release/
cancellation/stale input, metadata-only history, exact RGBA and composition,
parent/child Undo, packed/linked cold readers and normal startup after SIGKILL.
Its complete1440frame1080p24 movie checks edited parent and child frames against
preview and independent AAC sound at56seconds. Software checks do not establish
native import fidelity, physical pointer/tablet feel or artist acceptance.

The final private run passes100checks. Its1440frame60second movie rendered and
encoded in 226.939seconds on this software instance, with exact preview/PNG matches
at1304/1390/1430 and decoded sound onset2688001 (expected2688000). See the
[scoped movie artifact](benchmarks/drawing_exposure_movie_2026-11-06.json).
