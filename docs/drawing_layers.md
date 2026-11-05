# Drawing layers

In Draw, choose **Layers…**. The list shows the topmost layer first: it covers
the drawings below it. Select a row to choose the layer you will paint on.

- **New layer** inserts an empty layer above the selection.
- **New effects** makes an ordinary editable Effects layer in the same position.
- Enter a name and press **Rename** or Enter. Names can have 1–64 characters;
  new names must be distinct, ignoring case.
- **Move up / Move down** changes the stacking order, carrying all exposures.
- **Hide / Show** changes the whole layer. The main Show this layer switch does
  the same thing. Both affect preview and final output.
- **Remove…** asks before removing a layer containing drawings. Cancel keeps it.
  An empty layer removes immediately. At least one layer always remains.

All these edits support ordinary Undo and Redo. Selection alone is not an edit.
New still starts with Rough and Ink; Color layer below adds/selects Flats beneath
the current line art. The existing prototype limit is four layers and 32 full-HD
cels in total. Adding a layer does not allocate a cel until you draw or create one.
[Layer opacity](layer_opacity.md) has an explicit Apply control. Groups/blend modes
and larger/lazy-loaded documents are unfinished.

Layer names, order, visibility and exposure pixels use the existing project fields
and persist in packed/linked HAS, recovery and lesson scene snapshots. No format
migration is needed. Changing the layer stack cancels a pending fill. New/Open
invalidate an old layer dialog or removal confirmation. Playback/export block edits.

History keeps the original dictionaries and Images so older brush/cel commands
remain valid after order/removal Undo. Removing a populated layer charges retained
cel bytes to the existing 64 MiB/128-command history budget; oldest commands can
expire, and one oversized final command is retained under the existing policy.
This is not unlimited historical recovery. Saving the project preserves its
current layers, not the Undo stack.

Run `python tests/verify_layers.py` for the actual Windows private-desktop test:
real controls/painting, earlier brush history, stacking pixels, names/capacity,
stale confirmation, fill cancellation, packed/linked/recovery and MP4 agreement.
This is synthetic app input and GPU evidence, not a physical tablet usability test.
