# Project color swatches

In Draw, pick a color normally, then **Keep this color** beneath the color picker.
Click a saved swatch to reuse it for Pen or Fill. Hover shows its name and exact
eight-digit RGBA value. Transparency uses a checkerboard icon. Keeping an existing
color selects it rather than adding a duplicate. New and old files without a
palette start empty; Studio does not invent colors or change existing artwork.

Advanced shows the selected swatch's name, **Rename swatch**, **Replace with
current color**, and **Remove swatch**. Empty selection disables these actions.
Up to32 swatches fit a project. Names support Unicode and1–48characters.
Adding/editing/removing is a project edit with one bounded Undo action. Merely
choosing a swatch changes the current brush color without history or recovery
edits. A chosen color returns the eyedropper to Pen and cancels pending sampling;
changing fill color invalidates any older pending fill through the existing guard.
Swatch buttons keep keyboard focus available for the normal editor shortcuts.

Palette Undo does not clear live physics or reevaluate the shot. Colors/names
never recolor existing paint, source materials, models or saved camera keys.
Editing is deferred during playback/export/import/recording. Current tool color
is session state; the ordered named swatch collection belongs to the project.

The optional top-level `palette` array contains exactly `{name,rgba}` records,
bounded to32. RGBA is eight lowercase hexadecimal digits. Empty collections are
omitted, preserving old default saves. Save/Open, packed and linked HAS, the older
folder save path, recovery and lesson snapshots all retain it. GDScript and the
Python container worker validate before committing; invalid names, controls,
types/counts/hex or unknown swatch fields refuse. Invalid palette metadata cannot
qualify a manifest as a valid recovery/save backup. Source assets remain separate.

Project schemas1–5 and HAS ZIPv1 are unchanged. Earlier readers can still render
the ordinary cel pixels but do not expose these swatches and lose the palette
when resaving. Use the updated Studio to retain this authoring metadata. This is
additive project metadata, not a change to the shared3D model or an exporter.

`tests/verify_palette.py` exercises native swatch/Keep clicks, naming/alpha,
duplicate/no-op behavior, replace/remove Undo, pending sampler/fill interaction,
running physics, the limit, exact painting, five fresh persistence readers and
ordinary MP4. Eight engine domain checks and16 cross-runtime validation cases
cover strict metadata; three Python container tests cover packed/linked transport,
previous-save preservation and invalid-container refusal. Graphical jobs stay on
private Windows desktops. Actual outcomes and saved-copy status are in the dated
progress memo. The earlier161graphics-run regression anchors the pre-palette
source; it is not retroactively claimed for this newer increment.

Palette-file import/export, grouping/reordering and color-management profiles
remain separate future work. Swatches quantize the picker value to the same
RGBA8 precision used by the drawing canvas.
