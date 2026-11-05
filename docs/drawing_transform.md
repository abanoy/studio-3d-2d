# Resize and rotate selected drawing pixels

Draw → Select area[M] → drag a rectangle → **Resize / rotate…**. Simple offers
Size5–400percent and Rotation−180–180degrees. Positive angles turn clockwise.
Click Preview transform, review the result, then Apply transform or Cancel.
Each Apply is one ordinary pixel/tile Undo. Escape cancels a pending transform,
including while a numeric field is focused. Ctrl+Z cancels uncommitted work first.
Moving a selection still uses ordinary drop-to-commit; transforms use explicit
preview/Apply because resampling can change drawing edges.

Advanced adds separate width/height scales and Keep original pixels. Switching
Simple/Advanced only changes presentation: active independent scales/copy remain
effective and a Simple hint shows them. Enabling separate scales starts from the
current uniform size. Size/angle are relative to the current selected raster,
not an editable transform stack. Previewing new settings repeatedly uses the
unchanged source, so it does not accumulate blur before Apply. Subsequent applied
resampling can lose detail; Undo restores the exact previous RGBA.

The selected rectangle rotates around its stable integer pixel-grid center.
Bounds are rounded outward, with tiny numerical-roundoff tolerance at exact
quarter turns. Near an edge, the complete result shifts inside the frame. A
bounding box larger than the output frame refuses with guidance; it never cuts
the source or silently clips the result away. One raster pixel is the minimum
dimension. All-transparent selections and identity transforms are no-ops.

The worker inverse-maps output pixels with premultiplied-alpha bilinear color
sampling, clamped inside the selected rectangle. Arbitrary-angle edge coverage
uses2×2subsamples; exact orthogonal turns use one center sample and preserve
opaque integer pixel permutations. Hidden RGB beneath zero alpha cannot bleed
into visible fringes. Source-over blending operates in the existing stored RGBA8
channel space, not a new linear-light/color-managed pipeline. This is a bounded
CPU raster filter, not adaptive area/minification filtering or Krita-quality
resampling. Very small/thin details and repeated applied transforms can degrade.

Only the active held cel changes. Use Copy drawing here before editing an
individual exposure. Keep original merges transformed pixels into the same cel;
it does not create a separate object/layer. Original line art is preserved only
when it lives on a different layer. Other drawings, model/bone data, scene sources
and camera keys stay independent. Layer opacity is applied by compositing, not
baked into transformed raw alpha. The stored result remains ordinary RGBA pixels
in the existing shared scene/HAS format, so no schema/version change is needed.

Only detached byte arrays and numeric parameters enter the low-priority worker.
There is one job at a time; cancelled work finishes in the background and its
result is discarded. App teardown joins bounded work. UI controls remain usable
and actual UI frames during preparation are measured. Main-thread snapshot,
preview texture/composite and tile commit costs remain; no universal latency
claim. Cancel is available during preparation and preview. Pixel/frame/session/
revision/selection/visibility/settings guards reject stale work. Typing into a
field invalidates a candidate immediately; only genuinely edited text fields
are flushed, so deferred SpinBox display updates cannot revert numeric values.

Uncommitted candidates/borders stay outside saves/recovery/final rendering.
Normal painting, selection changes, seek/tool/mode/document replacement,
hidden layers, focus loss, playback/export or changed parameters discard them.
Real3D simulation can continue during preparation, Apply and drawing Undo.
No simulation keys, camera keys, source assets or native model standards change.

`python tests/verify_drawing_transform.py` checks an independent affine-matrix
inverse and mathematical premultiplied sampler over96 small cases.16 opaque
quarter-turn cases must match exactly; fractional/filter cases allow at most
one8bit step for engine vector-float quantization. Applied pixels, Undo/Redo,
reopened HAS and preview/movie comparisons remain byte-exact. Domain checks
cover identity, opaque quarter-turn reversal, transparent RGB, oversized/invalid
inputs, no clipping and a full-HD document. Private app checks route actual
field clicks/keystrokes and Preview/Apply/Cancel at1200pixels, test text/parameter/
brush staleness, independent scales/copy, live physics, opacity, New, linked/
recovery/cold packed Open and MP4. Persistence/movie tests restore the authored
world first; this test does not claim to bake live simulation.

Remaining: canvas transform handles, flips, lasso/masks/clipboard/cross-cel
operations, non-destructive transform stacks, keyed2D placement and richer
resampling/color management. Physical artist/tablet/keyboard/clean-PC and larger
production project acceptance remain unverified. See the dated memo for actual
run results and measurements. Verification here uses the Windows engine;
web/mobile export and thread availability have not been recertified.

Primary references: [W3C source-over compositing](https://www.w3.org/TR/compositing-1/#simplealphacompositing),
[Godot thread-safe APIs](https://docs.godotengine.org/en/4.6/tutorials/performance/thread_safe_apis.html),
[Godot LineEdit](https://docs.godotengine.org/en/4.6/classes/class_lineedit.html).
