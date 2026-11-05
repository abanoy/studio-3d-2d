# Expand and inspect animated parts

Objects start collapsed. Click the small arrow beside a keyed model/map/group to
show its animated parts. Root transforms, keyed bones and visibility have separate
rows. Static unkeyed objects have no empty disclosure control. Unused bones remain
available in the normal bone tree. The timeline's wider label column and English
estimates retain original native names/IDs in hover descriptions.

Click a part's label to select its object/bone without changing the frame or view.
Click along its row to inspect that frame; clicking a key selects the corresponding
part at that key. The bone tree and selected timeline row stay linked. A filtered
bone search clears when selecting a specific channel so that the requested bone
is accessible. Visibility selects its independent state row without toggling it.

Collapse restores ordinary object rows. Following objects, drawing/audio lanes and
the pinned camera/frame ruler stay aligned when rows expand or scroll. Only visible
channel labels/keys render; derived rows are cached while their model record stays
unchanged. New/Open clear expansion and stale row addresses. These are editor view
choices, not animation edits, Undo commands or saved project content.

Right-clicking a channel retains import-at-frame. Whole-piece cut/split/paste/delete
are disabled there; use the object's block row for those operations. A part-row
click does not start a motion-block drag. Export locks these controls as before.

New automatic pose keys include optional `authored_channels` hints containing the
stable root/bone IDs that changed. Editing another part at the same key retains
earlier hints. Explicit Record describes the root and stored sparse pose parts.
Hints are bounded, validated and checked against the real rig. They survive split,
clipboard, retiming, Undo, packed/linked storage and recovery through existing key
serialization. Existing formats/world/HAS versions and motion sampling are unchanged.
Older files without hints infer meaningful parts from nonneutral/changed snapshots;
neutral held takes still expose a Root row. Inferred rows are identified in tooltips.

Important current limitation: pose keys remain **shared whole-pose snapshots**.
This paragraph describes legacy models1–5. New body edits use model6 independent
part controls and rows; Advanced deletes just the selected part's key. See
[body animation](body_animation.md) for compatibility and remaining per-axis work.
Every snapshot controls every part, including implicit neutral values. The rows
therefore show those shared control points for each displayed part, rather than
pretending they are independent per-axis curves. Selecting a part and editing it
uses the existing auto-key/Undo behavior. Independent per-channel key dragging,
deletion, numeric curve editing, hierarchical channel groups and an Advanced list
of every inactive parameter remain future work. Legacy single-slot projects retain
their basic pose lane; their next normal Add promotes them to the multi-object world
where this expansion is available. No source-format conversion is required for that
promotion, and old projects remain readable/editable.

Tests: `python -u tests/verify_animated_channels.py` runs real routed disclosure and
native bone selection, split/retime mapping, filtering/highlighting, export locks,
many-row scrolling, cache invalidation/New, malformed hints, same-frame edits/Undo,
HAS/recovery, independent raster/WAV and MP4. Private prepared MMD/GMod/SFM fixtures
are optional; authored fixtures remain mandatory. See progress_memo.md for exact
counts, run phase and limitations. No physical mouse/tablet feel or all-rig/fidelity
certification is implied.
