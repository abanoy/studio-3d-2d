# Movement-path fixture successor: reveal and managed raster API

This is a new source-only successor; the earlier sealed timeline audit remains intact. It combines its reviewed five pre-click row reveals with one additional fixture API correction:

```gdscript
ink.stroke(ink.edit_image(ink.cel_at(app.layers[1],0)).image, ...)
```

The old standalone test accessed `ink.cel_at(...).image` directly. The current managed-raster cel dictionary does not guarantee an `image` field. `Drawing.edit_image()` returns the editable image through the established ownership path, as used by the current scene-view smoke. Every original assertion, stroke coordinate/color/radius, history/pixel/export check and other statement remains unchanged apart from the already reviewed reveal additions. The one-call inverse restores the exact earlier reveal source, including CRLF.

`SOURCE_PROOF.json` verifies that `src/drawing.gd`, `src/cel_raster_owner.gd` and the original `tests/movement_path_smoke.gd` in the redesign checkout are byte-identical to their completed full52 source catalogue entries. The stale direct dictionary API therefore predates the redesign; its failure is not evidence that Neon changed the production Drawing/cel API. The parent's actual original run and three routed-channel failures remain preserved separately.

`movement_path_smoke.gd` is the complete proposed test source. `managed_raster_only.patch` shows the additional one-call correction against the sealed reveal predecessor; `combined_input_and_raster.patch` shows both input and raster corrections against the untouched original. Parent must review and apply only after the original bounded probe closes, then run the ordinary standalone wrapper with its existing assertions and physical private-desktop closure checks.

No Godot parsing/execution, CIM/Git command or functional checkout edit occurred in preparing this packet. This is a fixture correction proposal, not a passing runtime result or a product feature claim.
