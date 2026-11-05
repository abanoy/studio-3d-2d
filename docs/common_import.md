# FBX, OBJ and glTF preparation

Choose **Add scene** for an environment, or **Add model** for the independent
poseable model slot. The file pickers now accept `.fbx`, `.obj` and `.gltf` as well
as the existing formats. Choose **Prepare and import**. The editor stays responsive
while the local worker converts; Cancel retains the previous project. No GMod
installation, SourceIO or MMD add-on is required for these three formats.

The same existing self-contained **GLB / studio_model_1** result feeds renderer,
GMod-style pose controls, master timeline, drawing overlay, recovery, `.has` and
MP4. There is no second scene or pose system.

## Supported scope

- **Binary FBX**: the installed Blender5.1 importer accepts version7100 or later;
  actual authored7400 fixtures are tested. External textures within the asset folder
  and embedded image data are supported. ASCII FBX is rejected with a conversion
  instruction. Bones/weights/names supported by Blender import become the same
  selectable Studio rig. Native custom data/actions remain in the Blender bundle.
- **OBJ + MTL**: static geometry and supported materials/maps. Relative mtllib and
  texture names, names with spaces and common MTL map options are checked. OBJ has
  no skeleton: root placement/rotation/scale works, bone posing requires a rigged
  source. Working MTL map paths are remapped to checked staged images; pristine MTL
  bytes are preserved separately in `original/`. Other original files remain in
  `native/`. Working MTL paths can refer to this conversion's staging directory;
  the packed Blender file and resulting GLB are the portable intermediates.
- **glTF2.0 JSON**: local external `.bin`/image resources, percent-encoded paths,
  base64 data URIs, meshes/materials/skins. Existing `.glb` remains a direct import.
  Remote URLs, UNC resource URIs, query/fragment resources and files outside the
  chosen asset folder are rejected. Extensions are limited by installed Blender
  import/export and the Studio renderer; complete extension fidelity is not claimed.

Uniform scale defaults to1. FBX/glTF axis and units follow the importer's metadata.
OBJ defaults to Y-up/negative-Z forward; choose Z-up/Y-forward for Z-up sources.
If textures/buffers live beside a parent folder rather than under the selected
file's own directory, choose that common parent as **Asset folder**. The adapter
stages declared/actually used resources rather than copying an entire library.

This is a static-geometry/skinned-bind-pose increment. Imported animation actions
remain in `editable.blend`; they are not automatically played or mapped onto the
Studio timeline. Manually pose and record Studio keys as before. Facial controls,
constraints, IK, physics, procedural materials and lossless native round-trip are
not added. Imported cameras/lights do not replace the Studio camera/light setup.
PBR material approximation still applies.

## Bundles and preservation

Each preparation uses a new `output/compatibility/source-*` folder containing
staged native files, packed `editable.blend`, `scene.glb`, `parameters.json`, request,
worker identity and conversion log. The parameter report records source/dependency
hashes, scale/axis selection, Blender version, mesh/bone/image counts, bone hierarchy,
object/material names/settings and native action names. It is retained with the
standard model through normal saves. All originals are checked unchanged afterward.
A packed HAS contains the standardized GLB (with textures) and model report; retain
its separate bundle for original/native editing. Linked HAS references the prepared
GLB, not the original FBX/OBJ/glTF for automatic reconversion.

The parent worker uses the existing separately installed Blender with factory
startup, isolated config, offline mode and auto-execution disabled. No preference
file is saved. A temporary in-process file-preview setting suppresses Blender
thumbnail generation. No new add-ons/packages, asset downloads or global preferences.
This process isolation is not a hardened hostile native-file sandbox.

Bounds:source/external buffer128MiB, glTF JSON16MiB, MTL4MiB,2048dependencies/512MiB
per preparation, FBX external images64MiB,16million pixels/image and64million total
image pixels after import. Prepared GLB128MiB,512bones, parameter report256KiB.
Existing scene/model/cel/timeline limits remain. Blender import timeout300seconds;
Cancel terminates/waits for only its owned Blender worker. Partial outputs remain
for diagnosis. Large-file latency, malformed native parser memory behavior, arbitrary
exporters and clean-machine coverage remain unverified.

## Verification and sources

Run `python -u tests/verify_generic.py`. It authors its own textured two-bone fixture
in isolated Blender, exports binary FBX with separate/embedded textures, external
and data-URI glTF, and OBJ/MTL. Actual Godot tests exercise preparation controls,
texture/rig import, axes/scale, skin deformation/undo, actor/environment isolation,
HAS reopen, independent drawing/camera/pose keys, MP4 frame agreement, missing
sidecars and cancellation. Fixture/dependency hashes and file inventories remain
unchanged. This is original test geometry, not downloaded artwork.

Technical behavior was checked against installed Blender5.1.2 RNA/operator enums
and its shipped `io_scene_fbx/import_fbx.py`, `bpy_extras/image_utils.py` and glTF
exporter. Public Blender manual/API requests returned402 in this environment;
no inaccessible page is treated as verification. Reference entry points:
[Blender FBX manual](https://docs.blender.org/manual/en/latest/addons/import_export/scene_fbx.html),
[Blender glTF manual](https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html).
No vendor implementation was copied into the application.


## Common-format verification checkpoint - 2026-10-29

Final canonical verify_generic.py exits0:9Python dependency/preflight fixtures and
41real Godot checks. Authored textured two-bone assets exercise FBX7400 with separate
and embedded images, glTF2.0 with external and data-URI resources, and OBJ/MTL with
space-containing texture names. Default imported height2units, exact default scale1,
chosen OBJ scale2/height4, native Tip selection, visible skin deformation and exact
pose undo all pass. OBJ environment replacement preserves the independent actor,
drawings and shot keys. Packed HAS reopen and camera/pose/cel MP4 succeed; H264
1920x1080,24/1,48frames,2.000s, exact frame24 preview/export bytes. Original fixture
files/hashes/inventories remain unchanged. Missing glTF buffers fail before staging/
Blender; ASCII FBX rejection and cancellation preserve current work.

Inspection found Blender's glTF bone-display Icosphere in the imported scene. The
adapter now excludes custom bone-display objects from GLB while retaining them in
the editable Blender rig. Tests inspect actual exported GLB JSON as well as reports:
one source mesh, without helper geometry. File-image counts exclude renderer-only
images. Actual dialog/rig PNGs inspected. A bounded scroll fixes an oversized import
dialog; corrected a SpinBox grid default to exactly1. In-process preview preference
avoids Blender thumbnail writes. The installed exporter supports AUTO/JPEG/WEBP/NONE,
not a PNG enum; AUTO is used and verified with the actual assets.

Canonical full verify.py exits0:unit24, GPU spikes, editor39, encoder failure/cancel,
audio24/Dummy,UI23,recovery14+13,pose44 actualMiku; AAC onset1.000s/RMS5658.30 retained.
Canonical verify_has.py exits0:12container fixtures/22actual checks, packed/linked/
relink/recovery/native metadata plus H264/AAC; onset1.0000417s. Canonical native
verify_source.py exits0:8archive+6path fixtures,32real checks and model/map1080p24/
48frame/2second movies. After helper exclusion, the affected generic and HAS suites
reran successfully. No new production renderer/timeline/storage branch or dependency.

Binary FBX only; native clips are retained in editable.blend rather than mapped to
Studio keys. OBJ is unrigged. PBR/material/constraint/physics/morph and exporter-
specific losses remain documented. Stale author-machine FBX texture paths try a
same-named image beside the source; unresolved images fail rather than silently
reading arbitrary external locations. Global texture searches are not performed.
No universal asset/extension/fidelity, hostile-file, clean-machine or physical-input
certification. Source originals/spec/art unchanged; no tool installation, game/
Workshop download, publishing/deployment, or unrelated project edits.
