# GMod / MMD compatibility and posing direction

Owner direction, 2026-10-29: support both maps/environments and models from GMod and
MMD, preserve editable parameters through the standard scene representation, and
prefer the familiar GMod manipulation workflow. This is now a requested compatibility
track, superseding its optional/deferred status in the original spec. The core
camera → independent drawing → timeline → MP4 workflow remains intact.

## What actually works now

| Input | Current implementation | Remaining work |
|---|---|---|
| `.glb` | Multiple native instances, root/bone auto-keys, camera/cels/audio/HAS/export | Morph/physics and richer materials |
| `.pmd` / `.pmx` | Direct Add model/scene via installed local Blender/MMD Tools; actual Miku/street tested | Richer materials, IK/physics, large rigs and KKBP bundle assembly |
| `.gma` | Resource-only staging/CRC, native model/map conversion and installed browser; no Lua | Native shader/physics fidelity |
| legacy `.bin` | Bounded LZMA/GMA staging, CRC and native Source import | Unsupported archive versions and native fidelity |
| `.mdl` + `.vvd`/`.vtx`, `.vmt`/`.vtf` | Installed GMod/SFM conversion and dependency mounts through same model | Flex/bodygroups/native lighting/physics |
| compiled `.bsp` | Multiple maps, geometry/props/materials and automatic installed dependencies | Lightmaps/skies/native effects/physics |
| Hammer `.vmf` | Authoring-tool path recorded; not imported | Separate brush-map conversion/compile path; SourceIO does not claim VMF support |

Hammer++ and installed gmad are existing external tools. Their presence is not proof
of a GLB export path. The prototype never installs/runs GMod add-on Lua or changes
the GMod/Hammer/MMD/PmxEditor installation.

## Actual supplied samples

- Reimu GMA: 111 entries, 9 MDLs with VVD/VTX sidecars, materials/textures and one
  Lua file. Lua is counted only, never extracted or executed.
- `716412401162652161_legacy.bin`: LZMA-wrapped GMA containing
  `maps/gm_hakurei_shrine_stv3.bsp`.
- `883003003936997315_legacy.bin`: LZMA-wrapped GMA with 56 MDLs plus dependencies.
- `temp.gma`: `maps/nt_transit.bsp` plus auxiliary files.
- Miku PMD: 9,036 source vertices, 14,997 triangles, 17 materials, 122 source bones.
  Prepared GLB renders in the studio with 126 bones (includes importer-generated
  helpers) and 15 vertex morph channels. It survives managed save/reopen unchanged.
- Street PMX: 102,946 vertices, 63,680 triangles, 103 material surfaces, five referenced
  atlas images and one bone. It renders in the studio and survives save/reopen.
  Material appearance and single-sided facade/ground geometry still need validation;
  screenshots are not proof of fidelity to MMD or the supplied Prev.png.

Extra attached mask/sky/preview images are not automatically assigned to guessed
material channels. Only native model references are resolved. Actual asset reports,
native copies, GLBs, packed editable Blender intermediates and screenshots remain
under ignored `output/compatibility/`; third-party assets are not committed.

## Reproduce local preparation

```powershell
python tools/asset_audit.py "C:\a\tools\temp.gma"
python tools/prepare_mmd.py "C:\a\tools\mmd64\UserFile\Model\Miku_Hatsune.pmd" --output "output\my-new-miku"
```

Output must be a NEW directory. The wrapper stages the native source and safe relative
image dependencies, checks their hashes before/after conversion, and runs Blender
with factory startup, disabled auto-execution, offline mode and an isolated config
path. It writes `scene.glb`, `parameters.json`, `editable.blend`, native files and logs.
The built-in shared toon ramps are copied from the explicit MMD Data directory;
`--shared-toons`, `--mmd-tools`, `--blender`, and `--scale` are configurable.
Tested: Blender5.1.2 and installed MMD Tools4.5.11, scale0.08. No installation occurs.

Use **Import GLB** on the prepared `scene.glb`. **Frame 3D scene** positions the
temporary editor camera; insert a shot key explicitly to keep that view. The conversion
is not available as a native-format file picker in the app yet.

Audit tests: `python -m unittest discover -s tests -p test_asset_audit.py -v`.
The actual model-render fixture uses fresh preparation outputs named
`output/compatibility/street-tested` and `output/compatibility/miku-tested`, then
`python run.py --test legacy`. It requires the supplied local assets and optional
tools; they are deliberately absent from clean-checkout CI fixtures.

The adapter approximates MMD materials with simple PBR. Vertex morphs and skin/bone
channels export where supported; MMD IK, physics, display frames, material/bone morph
behavior and toon/sphere/edge rendering remain in the packed native intermediate.
Keep the entire preparation bundle. The app now copies GLB plus the parameter report contents into a saved
studio project; it does not yet manage the full packed blend/native dependency bundle.
Successful import never implies full native parameter editing or round-trip export.

## Parameter preservation contract (partly implemented)

Use a versioned asset definition plus per-instance overrides. Identity combines source
checksum, importer/version and native element identity, with readable aliases. Keep
native files and a readable preservation/loss report alongside the standard GLB.
Unknown parameters stay recoverable rather than being silently flattened or dropped.

Portable parameters: instance position/quaternion/scale, visibility, bone transforms,
vertex morph weights, material slots/colors/opacity/textures and reference-only flags.
Source-specific channels: skins, bodygroups, flex controllers, pose parameters,
submaterials, eye targets and physical-bone bindings. MMD-specific channels: native
bone metadata/IK, vertex/group/bone/material/UV morph definitions, rigid bodies/joints,
display groups and shading parameters. Exact mapping must be reported per asset.
Source and MMD physics are separate data; a skeleton alone does not create a ragdoll.

Normalize coordinates/units once, record the conversion, preserve native names and
source ranges/defaults, and store all edits in project data. The first shared model record now preserves the native parameter report and offers
root/bone controls, keys and reference exclusion. Full native bundle management,
physics/morph/bodygroup controls and lossless round-trip remain future work. See
[standard_model.md](standard_model.md) for tested behavior and bounds.

## Familiar posing and timing workflow

The owner's references are Ragdoll Mover, Stop Motion Helper and SheepyLord's importer.
Reviewed source revisions: RagdollMover `noworkshop_ver` @ `5fe82f4a7803242796bfcab489cb6871f0f03865`;
StopMotionHelper `main` @ `6a10ed0dcac4da8cc039779f58815408bb33730b`;
Gmod-Simple-Character-Model-Importer `main` @ `895aaacba752204370250ec305aa3598c48f138c`.

Target scene interaction: content browser/spawn selection, selectable objects and
bones, move/rotate/scale gizmos, local/world axes, pivot control, numeric fields,
snapping, locks, and separate reset operations. Preserve camera/draw mode isolation
and Space transport; GMod-style controls must not introduce accidental marks or keys.

Target animation interaction: choose entity/bones/parameter channels, pose, then
explicitly Record at the master frame. Dragging a gizmo is one undo operation;
recording a key is deliberate. Easing belongs to appropriate continuous channels;
bodygroup/skin changes are discrete holds. Camera/pose sample every frame while 2D
cels keep their independent exposures. IK and physics simulation follow basic manual
posing, not a requirement for the first gizmo. Existing SMH saves/dupes are not read.

StopMotionHelper's design centers state on one controller with entity-keyed modifier
data. Its bodygroup modifier holds a prior state between keys, providing a concrete
reference for discrete channels. Ragdoll Mover's current branch exposes local/world,
snapping, bone/child controls and brush handling; its short README's model-only
description is narrower than the inspected implementation. Do not infer compatibility
from README wording alone. These are workflow references; none of their Lua is copied.

The MMD-to-GMod importer is a useful alternative bridge for GMod use. Its README and
Workshop describe different generations (compiled output versus dynamic loading),
so pin/test an exact route before integration. MMD can enter this studio directly;
porting through Source is optional. No binary hook, replacement renderer, AI service
or automatic dependency bootstrap from those projects is adopted here.

## Evidence and primary references

Eight asset-audit unit tests pass. The real Godot compatibility smoke passes 13 checks
covering runtime rendering, non-destructive scene framing, skeleton/morph presence
and managed save/reopen. Existing full unit/GPU/editor/audio/encoder verification also
passes. No Source BSP/MDL conversion, physics simulation, native pose editing or
visual-fidelity acceptance was performed. First MMD attempts caught missing shared
toon ramps and lazy image loading; both were resolved for the tested fixtures.

- [Facepunch GMA reader](https://github.com/Facepunch/gmad/blob/master/include/AddonReader.h): format reference for the independent inventory reader.
- [MMD Tools](https://github.com/MMD-Blender/blender_mmd_tools): external import engine, GPL-3.0-or-later; code/add-on not bundled.
- [SourceIO format matrix](https://github.com/REDxEYE/SourceIO/blob/master/README.md): candidate for Source BSP/MDL, not yet used locally.
- [Ragdoll Mover controls](https://github.com/PEAK-Incompetence/RagdollMover/blob/5fe82f4a7803242796bfcab489cb6871f0f03865/lua/weapons/gmod_tool/stools/ragdollmover.lua): inspected workflow reference.
- [SMH design](https://github.com/PEAK-Incompetence/StopMotionHelper/blob/6a10ed0dcac4da8cc039779f58815408bb33730b/docs/design.md) and [bodygroup channel](https://github.com/PEAK-Incompetence/StopMotionHelper/blob/6a10ed0dcac4da8cc039779f58815408bb33730b/lua/smh/modifiers/bodygroup.lua).
- [SheepyLord importer](https://github.com/SheepyLord/Gmod-Simple-Character-Model-Importer), [Workshop reference](https://steamcommunity.com/sharedfiles/filedetails/?id=3738916298): assessed, not installed or executed.

No root license was found in the inspected Ragdoll Mover/SMH trees; code reuse would
need its own permission review. SheepyLord's root MIT license was read, but bundled
tools and asset rights require separate records if adopted. This work uses original
adapter/inventory code and separately installed Blender/MMD Tools, with their notices
recorded in docs/licenses.md. The supplied assets remain local test material.


## 2026-10-29 posing increment

Manual skin posing is now implemented through one source-independent model record,
not a PMD-specific editor. A model can stand beside the existing environment; its
bones and root animate on the master timeline, while 2D cels stay independent.
Actual Miku native-arm deformation, interpolation, save/reopen and MP4 are tested.
Direct Source decoding is still absent; no native GMod model was posed in this test.
Source conversion must feed the same contract, with explicit native parameter/loss
metadata. See standard_model.md for the working controls and exact remaining limits.


## Latest Source import increment

The earlier absence statements above describe prior checkpoints. Source MDL/BSP
now convert through pinned SourceIO in isolated Blender into the same standard GLB
and studio_model_1 used by MMD. Native file/member selection, cancellation, explicit
content mounts, dependency copies/hashes and warning reports are implemented.
Actual supplied Reimu and installed gm_construct are tested; the shrine converts
partially with missing content listed. See source_import.md for current instructions,
exact tested scope and limits. No GMod Lua/add-ons or gameplay run in the app.


Verification for the Source checkpoint (2026-10-29): canonical
`python -u tests/verify_source.py` exits0: eight staging unit tests and25 real
Godot checks. Both actual Source model animation and Source map camera/cel movies
are H2641920x1080,24fps,48frames,2.000seconds by ffprobe. Each exported frame24
matches its runtime reference capture exactly. Raw BSP/GMA hashes remain unchanged.
Map reimport preserves camera/cel data; two pixels differ after a separate GLB load
(six channel bytes, mean error0.000063/255); the explicitly bounded GPU reimport
check documents this instead of claiming universal exact render identity.

Canonical full `python -u tests/verify.py` also exits0: unit24, editor39, GPU spikes,
encoder failures/cancel, audio24/Dummy fallback, UI23, recovery14+13 and pose44,
including actual Miku. Existing H264/AAC timing remains48frames/2seconds with onset
1.000s and RMS5658.30. These are synthetic/analytical checks, not physical mouse,
tablet, subjective listening, clean-machine or native shader fidelity acceptance.
