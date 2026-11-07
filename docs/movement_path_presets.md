# Reusable waypoint paths

Select a model in Pose and open **Movement path…**. Give its route a name and
choose **Save path preset…**. This writes a separate data-only `.haspaths.json`
file; saving a preset does not commit staged movement to the scene.

On another model, choose **Load path preset…**. Review the blue path before
**Apply path**. Cancel discards the preview. Apply replaces the whole position
channel from the target model's introduction, anchored to its authored starting
position in its group's coordinates. It preserves the target's body poses,
turn, size, expressions and foot-contact records. Existing planted feet must
still be reachable: Apply runs the existing binding and full-range contact checks.
Undo restores the previous model in one action; Redo restores the applied route.

These files contain relative position points and their hold/linear/ease modes,
not bones, scripts, meshes or referenced file paths. They can therefore be shared
between different skeletons. They do **not** generate walking steps, adapt feet
to terrain, align a character's turn to a path, infer depth, transform a moving
parent's world-space route, or carry generated motion assistance. Walking can now be enabled separately on a supported flat, straight route in
Movement path; see [optional walking](path_locomotion.md). Terrain, turning and
broader inference remain separate work under addendum §5.5 and its OPEN details. Native independent
model/map package extensions remain OPEN; this accessory uses JSON like the
existing body-pose accessory, without choosing those package extensions.

The exact rational frame rate must match (equivalent fractions are accepted).
The route must fit after introduction; there is no silent retiming or truncation.
Supported presets have 2–256 authored points, length 1–240 frames, and a 64 KiB
file limit. The first point has offset zero and the last owns the declared end.
Only ordinary curves that retain their sampled interpolation can be exchanged.
Trimmed/gap layouts that cannot represent a route while preserving its peer
channels are refused, with the existing document kept. There is no dense bake.

Preset import validates timing, fields, point order, bounds, names and modes
before staging. It follows no external paths. Save writes an owned temporary
file and renames it after successful flushing. Known scene sources and their
original native `parameters.json` reports are protected. File dialogs become
stale after the staged route, scene revision, selection or editor session changes.
The preset is separate from the `.has`: an applied route persists as ordinary
editable Model9 position controls, so it does not depend on retaining the preset.

Run the focused procedural suite on Windows with its private desktop launcher,
or on Linux with an explicitly provisioned private display:

```sh
python tests/verify_movement_path_presets.py --isolated-display :99
```

The suite checks strict data exchange, distinct original arm/leg skeletons,
staged controls, stale dialogs, peer-channel preservation, Undo/Redo, original
source bytes, packed/linked cold Open, recovery and exact MP4 input. It also
probes the actual H264 movie. This is software-rendered procedural verification;
it does not establish native rig, hardware, physical-input or artist acceptance.
