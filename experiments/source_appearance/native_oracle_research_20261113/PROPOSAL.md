# Installed native Source oracle: bounded proposal

Research only. No viewer/game/compiler, GUI, GPU or model runtime was launched;
no extraction, download, install, registry access, Steam write or main/Git edit
occurred. Root's canonical run retains the GPU lease and source freeze at
`eb7c069af72220c26471e7ceaf8b8055c40e6268`.

## Actual installed candidates

| Candidate | Architecture / version resource | SHA256 |
| --- | --- | --- |
| `SourceFilmmaker/game/bin/hlmv.exe` | x86; no file-version resource reported | `313d4333131f15c751fce9ea5919ff59f6a9b3e4f0c5426a5d05751fa1f655e0` |
| `GarrysMod/bin/hlmv.exe` | x86; 2026.09.16 | `a5668ee91b6996826632fea061fd43f176e227d56c8fc0e964f4936b2486f6e2` |
| `GarrysMod/bin/win64/hlmv.exe` | x64; 2026.09.16 | `68ab93356be69724408feafea194afe4705333fb88031e292557584e76182ae3` |

These paths are relative to `C:/Program Files (x86)/Steam/steamapps/common`.
The explicit 42-file inventory contains PE architecture, version resources,
hashes/stamps, relevant gameinfo lines and material-system companions. Each
existing selected file was hashed/stamped before and after its read and stayed
unchanged. `studiomdl` is a compiler, not the proposed renderer.

SFM ships material-system, DX9 shader, studio-render/cache and filesystem DLLs
and a Valve-authored SDK launch template using `hlmv.exe -game "%moddir%"`.
This local primary evidence verifies the `-game` template, superseding the
earlier web-only note's uncertainty about that one argument. It establishes no
skin, bodygroup, flex, batch-exit or screenshot command syntax.

Only eight header bytes were read from two shipped SFM models:
`tf/models/player/hwm/scout.mdl` and `hl2/models/alyx.mdl`; both say IDST version
49. That makes **SFM's own HLMV the first compatibility candidate**, but is not
proof that this executable can load either supplied unchanged model. No model
was loaded and no geometry from those stock models was decoded or copied.

SFM's installed usermod gameinfo also mounts tf_movies, tf, left4dead2_movies,
hl2 and workshop. GMod's gameinfo mounts addon/game VPK content and notes that
mount.cfg controls additional content. Using those ordinary roots would leave
implicit resource fallback. An oracle must use a fresh owned game root and
explicit mounts; it must not silently borrow textures from installed content.

## What official sources do and do not establish

Valve's public [Source SDK studio.h](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/public/studio.h)
declares model version **48**. It does not certify the installed MDL49 reader
ABI. Do not patch a version byte, decompile/recompile, or substitute GLB to make
native compatibility appear to pass. The public SDK's
[native model wrapper](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/public/tier3/mdlutils.h)
and [model panel](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/public/matsys_controls/mdlpanel.h)
show native skin/body/flex and bone-matrix drawing interfaces. Those are C++
APIs, not installed HLMV command-line controls.

Valve's [bodygroup implementation](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/game/shared/animation.cpp)
packs independent native fields using each body's base and model count. The
HAS request tuple `010` is therefore not a command-line packed body integer.
Native controls must select the exact named/indexed groups and parts.

Valve's [flex controller code](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/game/server/baseflex.cpp)
normalizes native ranges, and a failed name lookup can return index zero.
Its [client flex code](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/game/client/c_baseflex.cpp)
evaluates rules into descriptor weights. Enumerate and verify the actual
controller instead of treating any zero result as a successful lookup.

The retained native inventory does supply a stronger exact-file lead than the
earlier descriptor-only column probe: Keiki chisels has one **Tools controller
0, range 0..1**, with **descriptor 0 fetched from controller 0**. This is recorded
in `docs/benchmarks/sfm_native_feature_inventory_2026-11-12.json`, matched to MDL
SHA256 `d8b32165bef2ec4f1c09acd19b3b136b3492b556fcfb9da98fb01826c5e279ff`.
The adjacent actual conversion report agrees. Actual native UI enumeration and
operation still need validation. The raw GLB Tools target alone was insufficient.

The current official SDK tree does not contain HLMV source, and Valve Developer
Community HLMV/MDL pages returned HTTP 403 here. There is **no verified installed
HLMV screenshot/batch/skin/bodygroup/flex CLI or headless render route** in this
research. A material-context
[ReadPixels API](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/public/materialsystem/imaterialsystem.h)
supports only a source-level inference that a separate matching native harness
could capture pixels. That would require a separately scoped implementation and
matching MDL49 runtime, not building today's MDL48 SDK and calling it equivalent.
The [official SFM FAQ](https://www.sourcefilmmaker.com/faq/) makes installed SFM a
plausible native host if HLMV cannot supply required controls; no unattended
SFM scripting/capture or unchanged exact-model compatibility was proved here.

## First future run, after a separate lease

1. Review the exact installed SFM viewer/runtime hashes and the future writable
   profile/log/capture behavior. A private desktop is not registry/profile
   isolation. Establish an owned disposable profile/mount/runtime route and
   explicit allowed writes before launching; stop if this cannot be kept away
   from owner preferences and Steam. This task does not authorize that launch.
2. Keep the original MDL/VVD/VTX and VMT/VTF hashes/layout. Reuse the approved
   staged resource closure into an independently fresh owned mod; no new
   extraction is needed now. Nitori's missing native `materials/hairbump.vtf`
   stays missing. Do not copy another package's map or permit a hidden installed
   fallback. Record any debug/environment materials needed by the viewer itself.
3. Under the root's exclusive graphics lease, open one unchanged MDL49 per case
   and verify successful native load, actual visible mesh/material names,
   selectors and native missing-resource warnings. An error model, incompatible
   version or wholly absent component stops the matrix. Model-path/capture
   syntax is a discovery gate; do not execute guessed screenshot flags.
4. If that gate passes, capture **three Nitori skins** with glove part 0 and
   both base/glow primitives intact. Capture **seven Keiki nonempty tuples**
   000/001/010/011/100/101/110 using native tools/box/flame part selectors.
   Then add Tools controller 0 at .5 and 1 to its 000 zero baseline after
   confirming the exact native controller/rule mapping: twelve image states.
   Fix camera, resolution, light/environment, LOD, sequence/cycle and playback.
   Keep a per-state selector/capture/material-resolution receipt.
5. Treat those native images as native appearance/component/flex observations,
   not bit-exact Source-versus-PBR color equivalence. Nitori's native additive,
   environment/Phong/warp/bump behavior differs from the current derived GLB's
   ordinary opaque PBR overlay. Compare explicit material identity, component
   presence, silhouette and the stated deformation; preserve failures.

This first matrix still does **not** certify native skin weights. Both fixtures
have only a one-frame reference sequence, and Keiki chisels has no pose
parameters. Sequence/pose-parameter controls do not establish arbitrary hand or
box bone rotation. A later native bone pose requires a proved SFM control route
or a separately reviewed matching native bone-matrix harness. Direct native
VVD/VTX/vertex-delta checks also remain separate from screenshots.

If unattended capture cannot be established, record that limit. A private
observed native viewer check can still be useful, but is not an automated
numerical native oracle. No owner interruption or manual review request is
needed during this research.

The existing 29-control derived probe remains useful for renderer/app contracts;
it does not become native shader/weight fidelity proof because a native viewer
executable was found. The broader 82-MDL extra-feature corpus remains in scope.
