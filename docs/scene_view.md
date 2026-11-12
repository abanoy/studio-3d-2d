# Scene setup and camera framing

In **Scene / camera** or **Pose model**, **Scene setup** fills the available
scene area. It uses the same camera direction as the shot while showing the
space beyond the output frame. This remains one main view.

Choose **Camera focus** for the fitted output-shaped view. **Frame** shows the
camera output boundary; **3×3** adds a rule-of-thirds composition grid. Guides
stay out of rendered images and movies. In Focus, handles are clipped to the
displayed image. In Setup, handles and selection outlines can follow visible
objects beyond the output frame, with input bounded to the actual scene area.

The view choices are personal interface preferences. They do not change shot
keys, model poses, project output size, drawings or Undo history, and they return
when Studio reopens. Draw retains its own paper zoom and pan. Setup uses camera
navigation instead of moving the paper; Pose middle-drag navigates in Setup,
while Focus keeps its earlier paper-pan behavior.

The renderer keeps its native camera and output dimensions. Setup uses a separate
editor view of the same world, with matched projection and native coordinate
mapping. The unused scene pass is suspended; captures and recovery thumbnails
explicitly request fresh native pixels. A harmless interface translation does
not discard an in-flight selection. A changed camera, projection, view mode or
scene extent invalidates an outdated pick.

HAS currently authors centered perspective cameras. Unsupported off-center or
other projections fall back to Focus. This is not a multi-camera layout or new
output-resolution support. See [output sizes](output_size.md) for the current
1080p/720p/540p delivery profiles; 4K, arbitrary aspects and animated resolution
remain separate work.

Run `python tests/verify_scene_view.py` for projection/bounds and private app
checks, and `python tests/verify_secondary_picking.py` for focused and off-frame
loose-part selection. The tests cover wide/tall views, camera roll, visible
outside-frame geometry, queued picks, selection outlines, rotation/Undo/cancel,
guide-only pixels, exact unchanged native captures, independent drawing pixels,
fresh recovery readback and preference reload. This software coverage does not
establish native visual fidelity, artist comfort or GPU performance guarantees.
