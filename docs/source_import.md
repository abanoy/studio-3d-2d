# Source / Garry's Mod compatibility increment

Source assets now enter the **same self-contained GLB and `studio_model_1` contract
as MMD**. There is no second pose engine. This is a local preparation adapter, not
a Source game runtime. Originals remain read-only.

## In the studio

**Garry's Mod must already be installed to import native GMod files.** Studio does
not provide, install or download the game or Workshop add-ons. The preflight checks
the selected installation's GMod gameinfo/app ID and content VPK before staging or
starting Blender. This is a local installation-presence check, not Steam account
authentication. Ordinary GLB/MMD work and already converted standard projects do
not require the game.

Default locations:

- Game: `C:\Program Files (x86)\Steam\steamapps\common\GarrysMod`
- Workshop: `C:\Program Files (x86)\Steam\steamapps\workshop\content\4000`

The native file picker starts in the Workshop directory when present, falling back
to the installed game's content directory. Select a downloaded GMA/legacy-bin (or
loose MDL/BSP) inside an add-on's numbered folder. The preparation dialog offers
Browse controls for both roots and a Workshop file shortcut, so another Steam
library can be selected. These folder preferences persist locally in
`output/source-paths.cfg`, separately from project data. `HYBRID_GMOD` and
`HYBRID_GMOD_WORKSHOP` provide environment overrides; CLI also accepts `--gmod`
and `--workshop`.

The **Installed** navbar now opens a searchable in-app library of loose, VPK, GMA
and legacy-bin model/map members. Explicit dependency checkboxes can read resources
from other GMA packages or configured game/SFM directories without unpacking every
subscription. See [installed content](installed_content.md) for discovery paths,
ordering, real missing-resource improvements and current limits. No download occurs.
Private `output/` caches and converted game/sample assets are excluded from source
checkpoints and must remain excluded from future public distribution; the installed
game and Workshop folders remain read-only.

Use **Add model** for `.mdl`, `.gma` or legacy `.bin`; use **Add scene** for `.bsp`,
`.gma` or legacy `.bin`. Pick the archive member explicitly. The dialog offers a
unit scale and one optional additional content directory / `_dir.vpk`. Installed
GMod loose content and VPKs mount automatically from the configured directory.
Preparation runs in a separate Blender process; Cancel terminates that worker and
retains partial files. Existing scene/model data is replaced only after success.

Maps use a native player-start view when available. It is a temporary navigation
view: **Save camera key** explicitly at the desired frame before switching to Draw
or exporting. Otherwise Frame scene helps find the geometry. Source bones use the
same native-name tree, local/world handles, undo and explicit pose keys as MMD.

Each new `output/compatibility/source-*` bundle contains:

- `scene.glb`: embedded textures, default skin/bodygroups, native joints/weights;
- `parameters.json`: native bones, skin/bodygroup choices, flex/controller names
  and ranges where parsed, source identity, conversion settings and warnings;
- `editable.blend`: packed intermediate including imported bodygroup variants;
- `native/` or `archive/native/`: selected original/native resource copies;
- `resolved-native/`, `dependencies.json`: resolved loose/VPK/pak resources and
  their hashes/provider identities; `entities.json` for BSP native entity records;
- request, worker identity and `conversion.log` for diagnostics.

**Keep the whole bundle.** Managed studio projects copy the GLB and inline model
parameter report; they do not yet package every native source/intermediate.
Environment native reports also remain external. Editing the Blender intermediate
and re-exporting GLB is currently the way to change native bodygroup/skin choices.

## Tools and offline setup

Uses separately installed Blender **5.1.2** and local SourceIO **5.5.5**, revision
`fe24260b97ac03b899d9b5d4f0fd7b34772f3647`. The runtime version comes from the actual
module; the pinned README's older format-table version is not the runtime version.
The current machine's verified optional cache is at
`output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647`.
No add-on registration/install, Blender preference changes, Lua execution or GMod
modification is required. Factory startup, disable-autoexec, offline mode and an
isolated config directory are always passed. SourceIO's Steam autodiscovery and
ancestor-searching loose provider are bypassed in favor of explicit content mounts.

For another machine, obtain the pinned source from its
[primary repository archive](https://github.com/REDxEYE/SourceIO/archive/fe24260b97ac03b899d9b5d4f0fd7b34772f3647.zip),
verify archive SHA256
`cd44e1d053ac853c5d1628da9faa27a594337ebacb3587744dfa5d60758623de`,
and set `HYBRID_SOURCEIO` to the extracted directory containing `__init__.py` and
`library/`. It contains a platform-specific native decoder. No converter download
occurs at application runtime. `HYBRID_BLENDER` and `HYBRID_PYTHON` override the
installed executable paths. Optional tools are not required for ordinary GLB use.
See [the pinned license](https://github.com/REDxEYE/SourceIO/blob/fe24260b97ac03b899d9b5d4f0fd7b34772f3647/LICENSE)
and `docs/licenses.md` before distributing dependencies.

CLI examples (run from this studio directory; output must be a NEW directory):

```powershell
python tools/prepare_source.py C:/a/tools/touhou_reimu_bikini.gma --catalog
python tools/prepare_source.py C:/a/tools/touhou_reimu_bikini.gma --member models/ragdoll/reimu_hakurei_bikini_ragdoll.mdl --output output/compatibility/my-model
python tools/prepare_source.py 'C:/Program Files (x86)/Steam/steamapps/common/GarrysMod/garrysmod/maps/gm_construct.bsp' --output output/compatibility/my-map
python tools/prepare_source.py C:/a/tools/716412401162652161_legacy.bin --output output/compatibility/my-shrine
```

CLI accepts repeatable `--content` mounts and `--gmod` for another game location.
Scale defaults to SourceIO's **0.01905** units per Source unit; it is configurable,
not a claim of universal real-world model dimensions. Source Z-up is converted by
Blender's exporter to glTF/Godot Y-up. Player starts use the same axis conversion.

## Tested scope and limits

The supplied Reimu GMA and its raw ragdoll MDL convert: 77 bones, 21 decoded base
textures, 14 exported default-variant meshes. Native ValveBiped arm deformation,
undo, recorded animation, metadata/save/reopen and MP4 are exercised in the real
Godot app. GMA extraction verifies every entry CRC, including skipped Lua.

Installed `gm_construct.bsp` converts with 314 meshes, 72 textures, all 191 props
resolved and 2451 compile-time tool faces removed. Textured geometry and a native
player-start camera render in Godot. The supplied shrine legacy-bin also converts,
but only 112 of 525 props resolve from the available content; missing resources
are listed. It needs additional content mounts for a complete scene. No assets are
silently downloaded to fill those gaps. Other supplied archives are not certified.

PBR materials approximate `$basetexture`, alpha and culling. Source shader proxies,
animated VTF frames, material blending, water/refraction, lightmaps, decals, native
lighting and composed 3D skyboxes are unsupported. Maps use the studio's lighting;
skybox geometry may still exist at its original separate location. Tool surfaces
are excluded. Native entity records survive as data, not running gameplay. Physics,
IK, native sequences, live flex/bodygroup/skin UI, VMF/Hammer authoring and lossless
Source round-trip are deferred. Existing one-model/512-bone/128MiB-GLB limits apply.

Archive bounds: 512MiB decompressed, 128MiB LZMA decoder memory, safe resource-only
paths, case-insensitive duplicate/device-name rejection. The measured Steam sample
has a length + `0xBEEFCACE` footer; only that exact form or no footer is accepted.
Resolved dependencies total at most512MiB; textures at most16 megapixels each and
512MiB decoded floats total; maps at most5000 props. Native decoding still uses
third-party Python/native code and is **not** a hardened hostile-file sandbox.

Run `python -m unittest discover -s tests -p 'test_source_archive.py'` for eight
bounded staging tests; `python run.py --test source` requires the private supplied
GMA and installed GMod content plus prepared `source-map-v3` fixture. This explicitly
fails if private fixtures are missing. `python tests/verify.py` remains the ordinary
regression suite and does not require optional SourceIO/private GMod assets.

`python tests/verify_source.py` runs the optional Source suite and ffprobe checks
for both model and map movies (1080p24,48frames,2seconds). Actor and map export
frame24 match their runtime reference captures exactly. Repeated map captures are
identical; after a separate GLB reimport, two pixels differed in the current GPU
test (six channel bytes, mean absolute error0.000063 out of255). Camera transforms,
asset bytes and separate cel content are checked independently; the reimport check
allows at most384 changed channel bytes and mean error<0.002. This small observed
variation is not a promise of pixel identity across import order, drivers or GPUs.


Verification of installed-game defaults (2026-10-29): canonical
`python -u tests/verify_source.py` exits0 with8archive tests,6installation/path
tests and32real Godot checks. Checks cover the actual Workshop file-picker start,
custom folder picker, persisted roots, visible Prepare/Cancel buttons, and missing
GMod blocking before staging/Blender while preserving the live scene. Native model
and map MP4s remain1080p24/48frames/2seconds by ffprobe, with exact frame24 capture
agreement. Full canonical `python -u tests/verify.py` also exits0, including actual
Miku/audio/recovery/UI regressions. A visual review caught an oversized setup dialog;
its scrollable content and accessible buttons are now explicitly checked. No
second real Steam library, clean-machine, physical input or arbitrary DPI claim.
