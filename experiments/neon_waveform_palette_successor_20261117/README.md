# Waveform visibility and approved-theme expectation successor

This is a **source-only, unparsed and unrun proposal**. The root owns all native qualification and will preserve those receipts separately. No application palette or compact timeline height is changed by this packet. No engine, CIM, Git, real Windows API, installed tool source or private/native array was accessed during this palette task.

The historical waveform test first sampled an Audio row outside its visible timeline. The sealed input-only predecessor reveals that actual row but deliberately retains the classic color expectation. This successor keeps that reveal, adds safe pixel bounds, and selects the approved source-defined waveform color for the active interface theme.

## Exact preservation

- Historical original: SHA256 `28b9be24ede2068f562458584830df2a65d8ff6db0c1f863e1f97f3606f59621`.
- Input-only predecessor: SHA256 `2333fb6e213e2d74d7aa71fb845d6bb23e2038f034b6dd98ee94958d18964b2f`.
- New proposal: SHA256 `9775d5a497b64025fc93d958aa1a900316288b5fb2fb7fb34f77f3340ec3aa66`.
- Removing only the palette/bounds insertions restores the input-only bytes. Removing only its sealed reveal block then restores the exact historical original bytes.
- All 13 original `check(...)` source lines remain byte-identical. `Color("467d45")`, the three RGB differences with `<.02`, the 3×3 search, and `bars==4` remain unchanged.
- One new assertion requires every sampled 3×3 neighborhood to fit the image and both visible track scroll viewports. The test now completes 14 checks. An invalid neighborhood skips all pixel reads and makes the added assertion fail; it cannot be promoted as a passing four-bar result.

The first preparation refused to treat the root-staged input-only checkout file as the historical original. `PREPARATION_REFUSAL1.json` preserves that mismatch and its exact-inverse resolution. `HISTORICAL_ORIGINAL.gd` is the hash-verified reconstructed fixture, not a redefinition of the checkout's later state.

## Color derivation from source

The reviewed application uses Compatibility rendering (`project.godot:27–28`). In the approved source:

- `src/timeline_view.gd:523` draws the opaque timeline background, BAR `#0c0d11` (`src/studio_theme.gd:17`).
- `timeline_view.gd:463–464` gives both ordinary and selected Audio blocks fill RGBA `(0.239, 0.863, 0.592, 0.12)`. The selected block additionally has a one-pixel SAVED border, `#3ddc97` (`studio_theme.gd:44`).
- `timeline_view.gd:716` draws the block before the waveform. Lines 722 and 729 draw the non-muted wave with RGBA `(0.239, 0.863, 0.592, 0.85)`.
- `studio_theme.gd:114–129` passes the requested background/border colors into `StyleBoxFlat`; its antialiasing is enabled.

The pinned Godot 4.6 release is commit [89cea143987d564363e15d207438530651d943ac](https://github.com/godotengine/godot/commit/89cea143987d564363e15d207438530651d943ac). Its Compatibility renderer uses ordinary source-alpha RGB blending for the default Canvas blend mode. This supports the source-over calculations below. [GLES3 blend implementation](https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/drivers/gles3/rasterizer_canvas_gles3.cpp#L686-L692). The Canvas shader receives the draw color and writes the resulting color to the framebuffer. [Canvas shader](https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/drivers/gles3/shaders/canvas.glsl#L522-L524), [fragment output](https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/drivers/gles3/shaders/canvas.glsl#L799).

Let `W=(.239,.863,.592)` and `B=(12,13,17)/255`. At a fully covered interior wave pixel:

`RGB = .85*W + .15*(.12*W + .88*B)`

This is `(0.21366376470588236, 0.7558134117647058, 0.522656)`, or nearest RGB8 `(54,193,133)`. The proposal evaluates the same fixed-source constants with `Color.blend()`; it does not read the product's current style colors or infer an expected color from a screenshot.

## First transient at the selected left border

The generated source has its first impulse at sample zero (`tests/verify_waveform_levels.py:18`). Its cache bucket can begin just before the clip start. The renderer clamps that bucket's x coordinate to the actual clip rectangle's left edge (`timeline_view.gd:726–727`), which puts it on the selected block's one-pixel border rather than the translucent interior.

For a fully covered border pixel, let `S=(61,220,151)/255`. The expected RGB is `.85*W + .15*S`, giving `(0.23903235294117647, 0.8629617647058824, 0.5920235294117647)`, nearest RGB8 `(61,220,151)`.

The proposal chooses this border expectation only when `audio_selected==0` and the exact source bucket-left coordinate is at or before `audio_rect(0).position.x`, matching the renderer's clamp. All other nonzero samples use the interior expectation. This branch depends on source draw geometry and selection state; no observed pixel value selects or changes the expectation. Classic light/dark retains the opaque `467d45` expectation.

Thin-line rasterization and fractional StyleBoxFlat edge coverage can still affect the first boundary pixel. The root-owned native run must determine whether the unchanged 3×3 neighborhood contains a fully covered source-derived border pixel within the unchanged `.02` tolerance. If it does not, preserve that failure and investigate the coverage geometry. Do not widen the RGB tolerance, accept generic green, reduce the four-bar requirement or derive a replacement color from the captured pixels.

## Files

- `waveform_levels_smoke.proposed.gd`: complete proposal for the root's separate reviewed checkout.
- `waveform_reveal_bounds_palette.patch`: historical original → complete successor.
- `palette_bounds_from_input_only.patch`: input-only predecessor → complete successor.
- `SOURCE_PROOF.json`: exact hashes, source references, formulas, preservation checks and remaining runtime limitation.
- `PREPARATION_REFUSAL1.json`: preserved provenance mismatch.
- `HISTORICAL_ORIGINAL.gd`: reconstructed exact original fixture.
- `INDEX.json`: source packet inventory; no native result is claimed by this index.
