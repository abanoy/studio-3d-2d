# Pick a drawing color

In Draw, press **I** or choose **Pick color [I]**, then click a color in the picture.
The selected color appears in the existing color button and the tool returns to Pen.
The same click never paints. Escape returns to Pen without choosing a color.
Middle-button canvas panning and zoom retain their usual behavior.

The default **View + drawings** source samples the visible 3D view plus committed
drawings, including layer order, visibility, opacity and held cels. It uses your
current editor view, including temporary framing, rather than moving to a shot key.
Grid, green selection/hidden-object guides, bones, onion ghosts and unapplied fill
previews are excluded. The selected model/scene, view, keys and original pixels stay
unchanged. Picking a color is a personal drawing setting, not an Undo/autosave edit.
Painting with it is an ordinary editable drawing command.

Advanced reveals two additional sources:

- **Visible drawings** reads the composited 2D RGBA result without3D. It honors
  layer visibility and opacity. This can pick a partly transparent color.
- **Active drawing (original)** reads raw active-cel RGBA before layer opacity,
  even if the layer is hidden. It cannot read another frame outside that exposure.

Blank/fully transparent drawing pixels leave the old color intact. The tool stays
ready so you can choose a different point. Source choice is retained when returning
to Simple and shown in the instructions; it resets on a fresh app launch. It is
not stored in HAS. Painting into a faded layer still applies that layer's opacity.

Freeze live physics before picking from3D, so a moving body cannot supply a later,
different pixel. The drawing-only modes remain independent of live3D. Playback,
export, Home, text fields and dialogs keep their normal interaction barriers.

The3D source lazily creates an internal full-resolution read-only SubViewport sharing
the existing world and copying the editor camera's complete current projection. It
renders once per request, then stops. The app-owned grid uses reserved editor layer19;
selection proxies remain layer20. Both are excluded by the sampling camera. The main
view never hides the grid or switches camera, so sampling introduces no guide flash.
This is an internal readback helper, not a second project camera or a rendered asset.

Only the requested pixel is composed using the same native RGBA8 blend/alpha rounding
as the drawing stack. A3D pick still requires one full viewport render/readback and
may briefly pause on complex scenes; no universal latency guarantee is made. GPU
view-dependent custom effects/temporal rendering are not certified. Current imported
standard PBR/native-adapter models are tested. No source texture is edited or decoded
back to its original ecosystem.

One object-bound one-shot post-draw callback owns the pending pick. Newer clicks,
Escape, New/Open, edits, seek, changed view/source/color/layer, live physics or other
invalid contexts cancel it. Close disconnects the callback and releases the shared
world. A replaced request cannot disable its successor. No suspended Node coroutine
crosses deletion. UI guide settings and sampled-color state do not change project
schemas, recovery data or the final composite.

`python tests/verify_color_sampler.py` checks actual pixels, input mapping, keyboard
focus,3D/drawing/original sources, guide exclusion, data isolation, latest-request
handling, teardown, real prepared MMD/GMod/SFM skins and packed HAS/MP4. Optional
private native fixtures are explicitly skipped if absent. All graphical tests use
the private Windows desktop. See the latest progress memo for completed regression
counts and canonical-save status. This does not certify physical pen comfort, OS
monitor color management, persistent palettes, tablet pressure or native KRA support.
