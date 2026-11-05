# Align a character-sheet guide

In **Reference sheet…**, zoom and pan until the pose or detail you want fills the
viewer. Choose **Use viewed region** to fit that visible part over Draw. The PNG
stays whole: this chooses a texture region for the editing guide.

Open **Align guide…** to change **Guide size (%)** and X/Y offsets in output-image
pixels. Positive X moves right; positive Y moves down. The guide follows canvas
zoom and pan while retaining its position relative to the 1920 × 1080 drawing.
Adjust **Guide opacity (%)** independently. **Whole sheet** restores the full
source, centered at 100% size and zero offsets. If you pan the sheet completely
out of view, Use viewed region keeps the last valid guide and asks you to bring
part of the sheet back.

These are session controls: they add no document Undo commands or dirty revision,
change no original/managed PNG pixels, and do not alter the kept reference's
identity. Clearing a kept reference still has one Undo; Undo Clear restores both
its source and the personal crop/alignment you were using. Invalid history
geometry is refused before changing the reference.

Saving a kept reference includes the full original PNG. Reopening restores its
full source with the guide reset and off. Saved alignment, multiple guide views,
rotation and automatic pose/depth inference remain separate work. No new project
format is needed for these editor controls.

The guide shares the existing texture and draws a source region; it does not
allocate a second cropped full-resolution image. Movies and transparent drawing
exports continue to use ordinary scene/ink inputs and exclude the guide.

```sh
python tests/verify_reference_alignment.py --isolated-display :100
```

Fresh private Linux checks cover actual region display, size/offset geometry,
canvas registration, source preservation, Undo Clear, invalid/empty regions,
kept-reference Save/Open and exact movie source frames. Color sampling and the
complete kept-reference crash/normal-startup/lesson suites also pass. These are
procedural software-rendering checks; physical-input and artist comfort remain
separate acceptance gates.
