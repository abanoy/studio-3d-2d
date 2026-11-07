# Inactive onion-guide resources

Hiding an onion guide previously left both GPU texture references and the selected
cel dictionaries attached to the editor. New could therefore remove a document and
its history while the disabled guide still kept an old drawing's pixels alive.

The editor now clears its two textures, selection dictionaries and upload tokens
when guides are inactive: disabled, playback/export, another workspace, a hidden
layer, Home or a fill preview. It hides the nodes and queues redraw only when a
texture actually changes. Re-enabling guides recreates the exact current neighbors.
Visible idle/held frames continue to reuse their textures, and painting the current
drawing does not rebuild unchanged neighbors.

This removes stale strong references; it does not measure driver VRAM or assert
synchronous physical GPU deallocation. Two full-HD RGBA guide images have nominal
16,588,800-byte pixel storage, but driver allocation/overhead is platform-dependent.
No source drawing is changed and the personal toggle remains outside project data.

The existing onion workflow adds checks for null texture/selection state during
playback and after disabling, and a weak-reference check that New releases the old
selected source Image. Existing source isolation, shader colors, zoom/pan, fill
preview, incremental uploads, Undo/Redo, packed/recovery Open and movie equality
assertions remain. The portable runner preserves Windows private-desktop receipt
checks and requires an explicit owned private display on Linux.

See [before/fixed evidence](benchmarks/onion_resource_lifetime_2026-11-06.json).
Global drawing-memory admission, derived/GPU accounting and native hardware remain
separate acceptance work.
