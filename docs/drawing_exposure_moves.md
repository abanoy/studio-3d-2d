# Move drawings and resize holds on the timeline

Click a drawing block to choose its layer and a frame within its hold. Drag it
horizontally to move the complete exposure along that same layer. A small hand
motion remains a click. Zoom the timeline for precise placement; the ruler and
drawing blocks share the same frame mapping.

The preview changes only the timeline block. Release commits one Undo command.
During a move, the cel keeps its stable identity, original Image/RGBA pixels,
opacity and hold length. Other drawings, sound, camera animation and world data remain independent.
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

## Changing a hold length

The existing Advanced “Set held cel exposure” control now records only stable
layer/cel IDs and before/after durations, charged 512 bytes per edit. It uses the
same range validation and live-layer lookup as drawing moves. The existing
clamp at the next cel or scene end is retained. An unchanged value adds no Undo
action. Invalid lengths, active drawing gestures and export refuse the edit.
The original Images remain in place; no cel-array snapshots or full-raster
history charge are needed for a duration-only change.

Duration Undo/Redo remains local to its owning sequence and preserves live3D
preview. A focused three-cel1080p test retains earlier drawing history across48
hold edits, adding24576bytes, and checks all48 Undo/Redo operations against exact
cel IDs, ranges, Images and original RGBA. This reduces history pressure rather
than raising the64MiB history budget or changing the saved cel format.

## Dragging the right edge in Simple

Drag the short mark at a drawing block’s right edge to shorten or extend its
hold. The cursor changes to a horizontal resize arrow. The start frame and
original pixels stay fixed. The preview range/label changes first; release
commits one duration-only Undo action. Holds remain at least one frame and stop
at the next drawing or scene end, using the existing exposure-control rules.

The handle appears only when the true end is visible and the block has room for
a separate body target. Zoom in for narrow blocks, or use the numeric exposure
control in Advanced. An offscreen edge cannot become a handle at the viewport
boundary. The body still moves the whole exposure.

Escape, right-click, focus loss or Undo cancels the preview; small hand motion
stays a click. Navigation waits during the gesture. Stale document/owner changes
refuse release. Recovery and sequence switching use the same gesture guards as
body dragging. Child edits use the child clock and stable history identities.

The combined edge/move verifier now passes161checks, including30edge-GUI and
child edge Undo/Redo across scene switches. The complete60second movie and
cold/crash checks pass; see [scoped artifact](benchmarks/drawing_exposure_edges_2026-11-06.json).
The earlier100check result above records the body-move increment.
