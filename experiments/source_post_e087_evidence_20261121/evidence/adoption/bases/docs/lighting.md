# Project lighting

Future owner lighting requests and read-only reference research are recorded in
[lighting_feedback_2026-11-12.md](lighting_feedback_2026-11-12.md), especially
shared indirect lighting on models and props. That roadmap is deferred while
work is paused and does not extend the implemented modes described here.

The small lighting menu beside the Scene/Draw/Pose selector is available in Simple.

- **Unshaded** is the default for a new empty project. It shows base colors and
  textures without scene light/shadow interaction; added emission is disabled in
  this view so it does not brighten the base twice.
- **Lit** uses the lights supplied by the imported scene and the asset's original
  material shading. A scene without lights can be dark. Authored unlit or emissive
  materials retain their native behavior.
- **Studio light** keeps the original ambient/directional preview illumination.
  Older projects with no lighting setting retain this appearance. The explicit
  Advanced Sample room also uses it to preserve that demonstration.

The selection is a project setting, not a personal interface preference or an
animation key. It affects preview and final PNG/MP4 consistently. Changing it is one
Undo edit and retains temporary camera position, shot keys, poses, media and time.
Switching Simple/Advanced does not change it. Packed/linked HAS and recovery store
`video.lighting_mode`, one of `unshaded`, `lit`, `studio`; absence means legacy
`studio`. Invalid modes fail before project installation/writes. Container/world/
model versions remain unchanged; older Studio builds can ignore this new video field
and reproduce their previous lighting instead, so use updated Studio for the view.

## Material and scene safety

The existing instance-owned fade material layer composes Unshaded and visibility
opacity together. Native material/mesh/texture resources are not changed. Copies
retain texture bindings, culling and transparency/cutout settings; Lit restores the
exact original override references when not fading. Native emission is retained
when returning to Lit/Studio light. Shared mesh/material users and child instances
keep their own settings; parent fades are still applied once.

Only BaseMaterial3D/StandardMaterial3D/ORMMaterial3D are adapted. Custom shaders keep
their authored behavior; this is not a general shader translator. Existing partial
alpha/native overlapping-surface limitations remain. Unshaded does not alter skin,
morphs, physics, provenance or source files. The white fading reference grid stays
editor-only and unshaded independently of this setting.

Existing standard glTF punctual lights can import through the normal GLB loader;
an actual embedded directional-light fixture proves Lit response. This does not
complete native Source BSP lightmaps, Source shader/proxy recreation, MToon fidelity,
light creation/editing UI, photorealism or ray tracing. Those remain open importer/
rendering requirements. No lightmap is invented for an unlit map, and Lit adds no
hidden studio lamp. Studio light remains an explicit usable fallback.

## Verification

`python tests/verify_lighting.py` runs on the private Windows desktop. It checks
material/emission/alpha and shared-resource isolation, cutout restoration, new/old
defaults, imported light intensity versus exact Unshaded pixels, dark/light Lit
output, camera/key/data isolation, Undo, Simple/Advanced, bad-mode preservation,
packed/linked HAS, recovery, independent cyan cel, direct preview/MP4 agreement,
native MMD/GMod/SFM and available VRM0/1, and original hashes/mtime. The full verifier
also includes it. See progress_memo.md for actual current results and saved-copy status.

Primary references: [Godot4.6 BaseMaterial3D shading modes](https://docs.godotengine.org/en/4.6/classes/class_basematerial3d.html#enum-basematerial3d-shadingmode),
[Environment ambient illumination](https://docs.godotengine.org/en/4.6/classes/class_environment.html).
GPU checks are not owner visual approval, cross-driver/native-shader fidelity or
clean-machine certification.

Live Hair & clothes updates reuse the last ordinary world evaluation's project
lighting and inherited parent opacity. Importing another model and restarting a
live peer retains that context too. Explicit standalone Model.apply calls still
use their supplied settings/defaults. This transient cache does not enter HAS or
alter source materials. It does not add animated live-parent opacity evaluation.

`python tests/verify_live_appearance.py` exercises the actual Hair & clothes control
in Unshaded/Lit/Studio, a half-faded parent, normal Add peer restart and both available
VRM samples. It checks visible rendered color, settings, authored-data/shot/view
isolation and original file hashes. See the latest progress entry for actual results.


Source preparation now emits approximate static point/spot/sun entity lights;
see [implementation and limits](source_import.md#static-source-entity-lights).
Baked BSP lightmaps and full native lighting fidelity remain open.
