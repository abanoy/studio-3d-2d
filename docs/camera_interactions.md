# Camera keys and lens gestures

In the timeline's **Camera** row:

- Click a diamond to select its key and move the playhead there.
- Drag a diamond to an empty frame to change its timing. Its saved view and other
  key settings stay together. Release commits one edit; Undo restores it.
- Double-click an empty position to add a key using the view currently shown.
  Double-click a diamond to remove that key.
- Escape or right-click cancels an active key drag. Losing focus also cancels it.

A camera track must keep at least one key, so add another before removing its last
key. Retiming onto an occupied frame refuses the move; it never overwrites that
key. New keys and retiming destinations must be within the current scene. A scene
supports up to 241 camera keys.

**Ctrl + wheel** over the timeline ruler or tracks zooms around the pointer.
**Shift + wheel** pans horizontally; **Fit** shows the whole scene. A held editing
gesture must finish or be cancelled before timeline zoom/pan can change. These
controls also travel with a floating Timeline panel.

In the 3D view, hold **right mouse button + wheel** to change the temporary camera
lens. Wheel up narrows the field of view; wheel down widens it. The lens stays
between 15° and 120°. A loaded lens outside that range must first be set within
the editor range before wheel zoom is available. This changes field of view while
keeping camera position and orientation. Releasing the right button returns the
pointer to its capture origin.

Use **Save camera key** to keep that lens and view at the current frame. Merely
navigating or adjusting the lens does not create a camera key. Apply or reload an
unapplied [numeric camera draft](numeric_camera.md) before using the lens gesture
or saving a key.

With [Orbit around selection](orbit_navigation.md), **Ctrl + wheel** continues to
move nearer/farther without changing the lens. Ctrl + right drag remains orbit
panning. A left-button fly gesture and two-button roll keep their existing behavior.

Close conflicting dialogs, finish imports and turn live **Physics / Hair & clothes**
off before editing Camera keys. Lens gestures are unavailable during playback/export
or while another editing operation owns input.
See [timeline navigation](timeline_navigation.md) for the shared range controls.
