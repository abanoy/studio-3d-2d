# World hierarchy and selection

In **Scene / camera** or **Pose model**, click a visible model to select it. A green
outline follows the actual posed mesh, and the posing tools open without changing
the view. Select an environment or model from the **World** tree on the left, then
use **Frame selected** to find it. Opening a saved project starts with no selection
and the camera at the saved frame's shot. **Draw** retains normal painting behavior.

Hold **Alt** to reveal all joints and connecting bones. Release Alt to hide the full
skeleton; the selected bone and its move/rotate handles remain accessible. The owner
explicitly chose momentary hold/release behavior. Bone search/tree selection also work.
Focus loss or Escape clears reveal and pending camera gestures.

- Short **left click** selects; a drag beyond4window pixels uses camera movement.
- Short **right click** on empty space deselects. On a model it opens Frame selected,
  Reset pose and Hide/Show model. Environment context offers Frame and Deselect.
- **Right drag** still adjusts POV. Both primary buttons roll; middle retains its
  contextual camera-dolly/canvas-pan behavior. **Ctrl+LMB** immediately enters free
  camera, including over pose handles. WASD/QE flight and Shift speed remain available.
- Clicking a joint or dragging its handle poses the current model. Completed edits
  auto-key by default. Reset pose restores imported bone offsets, preserving root
  placement, and participates in the same key/Undo command. Imported neutral pose is
  not guaranteed to be a humanoid T-pose for every rig; no IK/retargeting is inferred.

Hidden models remain selectable in World. A selected hidden model has a translucent
green ghost, including through occluding environment geometry. That editor overlay
does not change visibility or appear in the movie. Deselecting hides the ghost again.
Show/Hide remains the existing static model flag; animated visibility is upcoming work.

## Implementation and scope

`world_selection.gd` owns the hierarchy, click/drag arbitration, context actions and
editor-only selection state. It renders960x540 object IDs from a helper SubViewport
sharing the renderer's actual `find_world_3d()`. Mesh/skin resources and native skeleton
poses are shared; source materials/layers are left untouched. Blend-shape values copy
to the selection instances. Layer20 is reserved internally and excluded by the shot
camera. The mask camera is a technical helper, not a second animated shot camera.

An original canvas shader outlines the selected ID; selected hidden geometry uses a
separate depth-independent ID shader for the ghost. Ordinary hidden mesh variants
stay excluded when their visible parent model is selected. Standard albedo alpha
cutouts use the source texture/opacity (threshold0.2). Complex native/procedural shader
semantics and perfect transparency coverage are not promised. Clicks read the ID
texture after a render frame; superseding input/new assets invalidate old requests.
Normal unselected idle does not continuously render this mask; selection does.

Normal documents still use one environment/model. For a prepared schema4 world,
selection now builds its complete parented hierarchy and assigns up to64distinct GPU
ID colors. Map/group roots use the same transform handles as actors. Pose history
uses stable instance IDs across selection switches, and hidden-parent objects remain
editable as ghosts. See [world_editor.md](world_editor.md). Normal append imports,
New/Open replacement and recovery restore are the remaining integration gate; no
claim that normal multi-object creation is already complete. Physics/IK remain open.

## Verification

`tests/world_selection_smoke.gd` uses the actual app, GPU ID texture, skinned fixture,
context popup and rendered green pixels. It checks selection, camera/cel isolation,
Alt, hidden ghost/x-ray, pose/reset/undo, source materials/layers/hashes, clean New,
environment selection and actual prepared MMD/GMod/SFM pick/deformation. The core
runner now rejects shader compilation errors as well as script errors and leaks.

Across a mode reselection, the authored fixture's final captures differ in three
color channels at one mesh edge (mean0.00002424/255), with no highlight in output.
The test uses the existing bounded GPU edge criterion (<=384changed channels and
mean<0.002/255), plus explicit shot-layer exclusion. This is not universal exact pixel
identity. Environment selection captures are exact. Actual MP4/save/audio/recovery
regressions remain in the full suite. Physical mouse/tablet and owner usability are
still separate acceptance work.

Primary APIs: [SubViewport](https://docs.godotengine.org/en/4.6/classes/class_subviewport.html),
[MeshInstance3D](https://docs.godotengine.org/en/4.6/classes/class_meshinstance3d.html),
[Camera3D](https://docs.godotengine.org/en/4.6/classes/class_camera3d.html).
