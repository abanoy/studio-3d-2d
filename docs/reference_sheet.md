# Character-sheet reference viewer

In Draw, open **Reference sheet…** and choose **Open PNG…**. The modeless window
shows your local character sheet beside the canvas. Wheel zooms around the pointer,
drag pans, and **Fit sheet** restores the whole image. Transparency is shown over
a checkerboard. The viewer preserves the sheet's aspect ratio.

Right-click a visible sheet pixel to choose its brush color, including alpha.
Sampling uses the original decoded pixel, independent of viewer zoom/pan,
checkerboard and guide opacity. Fully transparent pixels and margins keep the
previous color. Choosing a color is a brush setting; it adds no document history.
The next pen stroke uses it with the existing brush-opacity control.

Enable **Guide over Draw** to show a fitted, translucent copy over the drawing
canvas. Adjust **Guide opacity (%)** as needed. The guide consumes no drawing
input: drawing still creates ordinary editable cel pixels underneath it. Closing
the viewer keeps an enabled guide available; reopen the viewer to turn it off,
or **Clear** to release the sheet. It hides in Scene/Pose, playback, Home and
export, then returns when drawing resumes.

The viewer and guide are editor aids. They never enter the renderer's scene/ink
inputs, MP4 frames or transparent drawing-only PNG exports. Opening, panning,
zooming, changing opacity and reloading do not create document Undo commands or
mark the project dirty. Original PNG bytes remain unchanged.

External source changes wait for **Reload**. Invalid, missing or oversized files
keep the current sheet. Inputs are limited to a local PNG, 16 MiB compressed,
4 megapixels decoded, and 8192 pixels on either side. The bounded header is checked
before decoding, and source bytes are hashed. No scripts, network calls or extra
software are needed. Clearing or closing the viewer invalidates pending file
picker callbacks.

Sheets are session-only unless you enable **Keep PNG in project**. See
[project-managed reference sheets](project_reference_sheet.md) for packed/linked
saving, Undo, schema 7 and crash recovery. Without Keep, existing `.has` formats
remain unchanged and cold Open needs no reference PNG. Saved overlay placement,
multiple reference views, anatomical proportion tools and optional consistency
suggestions remain separate work. This does not replace a poseable 3D reference
or infer anatomy/depth.

The portable procedural check is:

```sh
python tests/verify_reference_sheet.py --isolated-display :99
```

Linux requires an explicitly provisioned private display. Windows retains the
private desktop launcher and receipts. The check uses an original synthetic PNG,
a real parent world, routed viewer/canvas input, exact document/pixel checks,
actual MP4 and transparent PNG exports, and cold `.has` reopening. It does not
establish physical-input, native-rig or artist acceptance.
