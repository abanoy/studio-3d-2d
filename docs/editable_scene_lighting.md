# Editable scene lighting

Branch `worker/editable-lights-20261121`, isolated checkout
`has-editable-lights-20261121`, based on origin/main `243e6a1e`.
The earlier lighting checkout and paused rebase are preserved; their changes
were carried forward. Installed Studio, shared tools and original assets are unchanged.

## Use

Launch `python run.py` or `Start Studio.bat` in this checkout. Choose **Lights…**
beside the lighting menu, add Directional, Point or Spot and choose **Use Lit**.
Select a row, edit name/color/intensity/shadows and **Apply light**. Visibility
applies immediately. Expand **Placement and beam** for position, pitch/yaw/roll,
range, spot half-angle and aiming at the current selection. Each completed
operation is one Undo/Redo action; save normally to a portable HAS file.

Position uses scene units; rotation uses degrees and beams face local negative Z.
Point lights have no direction; directional lights have no range. Initial placement
uses selected geometry, nearby scene bounds or a point ahead of the camera in
empty/large scenes. Lamps remain independent of objects. Light animation, gizmos
and editing imported lamps remain future work.

Daylight, Warm key + cool fill, Stage spotlight and Soft character append editable
lights as one Undo action. Soft character is a low-contrast starting rig, not an
MToon/MMD shader emulation. Unshaded remains the flat view. No RTX/path-tracing preset.

Ambient fill normally supplies uniform illumination, an approximation of indirect light.
For optional **Room reflections and local fill**, launch `python run.py --forward-plus`.
Apply explicit ambient fill first (try 0.3), then enable the room mode. One live,
box-projected cubemap has center/size/strength controls; put its center in open air.
It approximates reflections/local image-based fill, costs extra render time,
changes no materials and does not trace light bounces or accurate mirrors. Editor
guide/picking layers are excluded; imported probes remain. Compatibility remains
the default, retains saved probe data and shows an actionable Forward+ limitation.

## Contract and addendum comparison

| Requirement | This increment |
| --- | --- |
| Simple-first (§1/10) | One Lights entry, expandable placement/reflection controls |
| Unshaded/Lit/Studio (§10) | Defaults retained; Lit uses imported/authored lights; Studio keeps legacy lamp/fill |
| Imported fidelity (§3) | Imported lights, shaders and baked lighting retained, no material substitution |
| Undo and portable HAS (§11) | Optional validated video data uses existing history/storage/sequence paths |
| Rich rendering (§10.2) | Raster shadows plus optional cubemap approximation; diffuse GI remains future work |

Optional `video.scene_lighting` has format `studio_scene_lighting_1`, ambient RGB/energy,
and up to 64 lights with stable ID, name, type, visibility, position, rotation_degrees,
RGB, energy, range, spot_angle and shadows. Optional `reflection` stores enabled,
position, size and intensity. No world/model/container schema is replaced. Old
readers may ignore the extra video field and cannot reproduce these lights.
Settings belong to the active sequence, like lighting_mode.

The list contains authored lights. Imported lamps retain their transforms,
visibility and energy inside assets. Unlit/custom/baked surfaces get actionable
relink/shader warnings; none is silently replaced to receive lighting. Baked lighting
is not rebaked. Compatibility normally permits 8 point + 8 spot lights per mesh,
8 visible directional lights, including imported sources. Current docs describe
2 probes per mesh in Compatibility, but this pinned runtime/driver produced no
reflection on the actual metallic prop. The authored probe is qualified only on
Forward+, not Mobile or Compatibility; this is an observed runtime limitation.
64 saved lights is an editing limit, not a promise that all affect one mesh.

## Focused checks

`python tests/verify_scene_lighting.py --cpu` checks actual app controls, runtime
nodes, history, directory saving and fresh-process packed/linked reopening in
Neon and Classic with isolated profiles. JSON fixture numbers use absolute 1e-10
comparison; IDs, keys, booleans and lengths remain exact.

`python tests/verify_scene_lighting.py` uses the existing private Windows desktop
launcher for actual pixels, shadows, routed clicks, packed reopening and H.264 export.
Optional `--native-model PATH --native-environment PATH` tests prepared local GLBs
read-only, without converters/downloads. Captures/media/raw receipts stay in ignored
output. Add `--forward-plus` for cubemap checks. Final CPU103, Compatibility107
and Forward+119 pass. Each graphical mode exports a 1920×1080/24fps/48-frame H.264
movie with exact preview/export PNG and fresh-reader pixels. Final results are in
`benchmarks/editable_scene_lighting_2026-11-21.json`. No full-suite, cross-driver,
arbitrary native-shader or artist acceptance claim. Earlier desktop-denied attempts
remain historical. The final tests retain unchanged thresholds. A tiny center
patch initially faced empty black space; visual inspection corrected the prop
sample to its lower hemisphere reflecting the lit floor. Whole-room brightness
alone was insufficient to establish reflection support.

Forward+ emits texture-RID warnings on engine shutdown:14 in the two-theme writer
and7 in its reader; the minimal engine-only probe also emitted7. No ongoing-session
leak or performance conclusion is established. Animated reflection timing,
reference-only-object reflections, arbitrary imported probes and multiple GPUs
remain unqualified. Cubemaps do not replace physically correct diffuse GI.

## Integration

Retain the three separate scene_lighting document/runtime/editor modules. Apply
only these hunks; never replace the primary worker's app/renderer files wholesale:

| File | Hooks |
| --- | --- |
| src/app.gd | scene_lighting_editor member; setup after sequence_editor.setup; lighting tooltip/status wording |
| src/renderer.gd | scene_lighting member; setup after world attachment; sync at start of apply_lighting; apply_ambient after mode switch |
| src/lighting.gd | Delegate optional scene_lighting validation after existing mode validation |
| run.py | Optional --forward-plus flag; insert renderer override before --path; default launch unchanged |

No world-runtime/model/material/export edits. Scene setup shares the renderer world;
nested sequence renderers already use their own video settings. Camera easing,
posed bounds and bundled parts hooks are preserved.

## Practical non-RTX effects

| Effect | This branch and practical followup |
| --- | --- |
| Shadows | Directional/Omni/Spot raster shadow maps; no RTX requirement |
| Ambient | Explicit uniform color/energy, not bounced light |
| Reflections | Optional Forward+ live room cubemap/local fill; no ray-traced mirrors |
| Indirect diffuse | Not implemented; Forward+ SDFGI/VoxelGI or prepared LightmapGI are possible |
| Slower offline | Existing sequential PNG/MP4 pipeline; extra encoding time alone adds no quality |
| Path tracing | Not implemented; needs an actual separate renderer integration |

Next practical diffuse-indirect step: opt-in Forward+ SDFGI in a small colored-wall
room, keeping Compatibility default. Mark only detached runtime environment geometry
static. Test environment-to-skinned-model tint, camera cuts, convergence and movie
frames. SDFGI handles dynamic lights but not dynamic occluders/emissive contributors.
Measure startup, memory and settling before exposing a quality choice. LightmapGI
plus dynamic-object probes is a good static-room alternative, requiring UV2/bake
preparation and cache invalidation. Neither should be called path tracing.

Advanced Light Entities informs the editable-lamp workflow. Xenthio's RTX Remixed
integrates PBR conversion and Remix and now directs users to SourcePT; this does
not provide a Godot RTX switch. No reference code/runtime was copied or installed.

Official sources consulted November 21, 2026:

- [Godot 4.6 lights/shadows](https://docs.godotengine.org/en/4.6/tutorials/3d/lights_and_shadows.html)
- [Renderer capabilities](https://docs.godotengine.org/en/4.6/tutorials/rendering/renderers.html)
- [ReflectionProbe and live-update cost](https://docs.godotengine.org/en/4.6/classes/class_reflectionprobe.html)
- [SDFGI limitations](https://docs.godotengine.org/en/4.6/tutorials/3d/global_illumination/using_sdfgi.html)
- [LightmapGI](https://docs.godotengine.org/en/4.6/tutorials/3d/global_illumination/using_lightmap_gi.html)
- [Advanced Light Entities](https://steamcommunity.com/workshop/filedetails/?id=493751477)
- [RTX Remixed](https://github.com/Xenthio/garrys-mod-rtx-remixed)
