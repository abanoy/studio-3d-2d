# Timeline animation blocks

Each map, model and group has a collapsed row. Click its name to select it. Purple
diamonds show root/bone keys; the pale band shows continued object presence.
The frame/camera ruler stays pinned while object, drawing and audio rows scroll.
Hover reveals full object names. Camera keys remain explicit and separate.

1. Pose/key the object at a few frames. Its initial block contains the complete take.
2. Right-click inside that block at a chosen frame and select **Split here**.
   The two pieces initially render the same motion as the original curve.
3. Drag a piece to move it independently. **Shift-drag** moves all pieces and
   first presence together. Release commits one Undo command; Escape/focus loss
   cancels. Releasing outside the timeline works.
4. Right-click a block to **Copy piece**, **Cut piece** or **Delete piece**.
   Right-click free space on the object's row to **Paste piece here**.
   Paste supports another instance of the same exact source GLB at the same rational
   frame rate, not automatic
   retargeting between unrelated rigs. Occupied/out-of-project destinations fail
   visibly and preserve the document; overlap previews are red.
5. Pose at a frame inside a piece: the edit auto-keys only that piece. A copied or
   split sibling keeps its own curve. A manual key outside fixed slices
   creates a new authored take, which grows naturally as more poses are added.
   It connects through gaps without exposing cropped control keys or changing
   existing pieces. Earlier manual keys correct introduction. No rest key is invented.

Between two pieces, the object remains present and connects their endpoint states
using the prior source interpolation (ease/linear; deliberate hold remains held).
Before first introduction it is absent, unless an explicit earlier manual key
extends it. After the final piece it holds the last state. Hidden flags and hidden
parents stay authoritative; motion gaps do not turn them on. Animated visibility
keys and the requested global300ms fades are still a separate pending increment.

Deleting all pieces keeps the object in the tree but absent from output. Select it
to edit its green ghost; a new manual key introduces a piece. Undo/Redo target the
original object even after selection changes. Stale drags cannot overwrite another
edit. Active drags defer recovery; timeline interaction locks during export.
Camera, drawing and audio timing stays independent throughout these operations.

The first split/cut/paste promotes that object's record to `studio_model_2`; the
underlying GLB and native bone identities stay unchanged. See [piece data and
limits](animation_clips.md). Existing unsplit records remain version1.
There is no time stretching, looping, ripple edit, cross-rig retargeting, expanded
animated-channel UI or native motion-clip importer yet. Older legacy single-slot
projects retain their old lane until promoted to a multi-object world by Add.

Verification uses actual app/menu/input/Undo/HAS/recovery/export operations and
optional private MMD/GMod/SFM rigs. Source files remain unchanged. Relative root/
pose samples at a split compare exactly; GPU edge comparisons retain the established
<=384changed-channel/mean<.002 bound. Preview/export of the current reopened world
is exact. Physical mouse/DPI feel and arbitrary large scenes remain unverified.

Current refinement: normal body edits use model6 independently keyed parts and
expressions retain model5 ownership. Growing one unsliced take keeps each part's
own curve endpoints; split/copy/move retain source slices. Explicit Record can
establish a starting rest pose for parts animated later. Advanced removes only a
selected part's key. Animated-part rows and persistent visibility/global fades now
work, superseding the earlier pending statements above. Per-axis curve editing,
stretch/ripple/loop and native motion import remain unfinished. See body_animation.md.
