# World rail placement successor — unrun draft

This candidate is prepared for parent review. It has not been applied to the frozen redesign checkout and no Godot process was launched.

The patch restricts the icon rail and fold/unfold action to the same placement the action can resize: World alone on the left edge. Narrow right, nested, tabbed and floating placements keep the full list. `apply_nesting()` re-evaluates rail mode after changing placement, including moves that preserve the panel width and therefore may not emit `resized`. Tree selection, the existing dock format and all timeline geometry remain unchanged.

Files:

- `workspace_layout.patch`: narrow unified patch against the frozen c2 source.
- `workspace_layout.proposed.gd`: full proposed source for review, with LF line endings.
- `PROVENANCE.json`: exact frozen source hash and proposal hash.
- `rail_placement_smoke.gd`: unrun Godot regression using the included synthetic Practice figure. It covers left fold/unfold, a right panel narrower than 140 px, a narrow nested leaf, an unsupported nested fold call, exact nested state reload, a shared tab group, floating and redocking. Each stage checks the same selected model and live Tree.

Future execution must use a separately approved successor checkout and the existing private Windows desktop runner. Copy the test into that successor's experiments directory and run it as a standalone Godot script with one fresh output path beneath the successor's `output/` directory. This draft intentionally contains no command that launches an engine, no owner asset paths and no screenshot capture.
