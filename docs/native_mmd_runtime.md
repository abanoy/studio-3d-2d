# Native MMD and Source runtime profiles

MMD model import uses a separately selected Blender and MMD Tools package.
`HYBRID_BLENDER` selects Blender; `HYBRID_MMD_TOOLS` selects the installed addon
folder containing `blender_manifest.toml`. Factory-startup workers stage the
addon's declared pure Python wheels in their owned output directory so packages
such as OpenCC can read their dictionary files. No model-supplied dependencies,
network downloads, global package installs or preference changes are performed.
Wheel paths, duplicates, symlinks and expanded budgets are checked before staging.

The tested MMD runtime is Blender4.3.2 and MMD Tools4.5.14, commit
`3451990faea2e0def110e7f6027f5c8575451e8b`. The addon stays outside this repository.
See the [native receipt](benchmarks/native_mmd_gma_2026-11-08.json).

Source conversion may use `HYBRID_SOURCE_BLENDER` when its native codecs need a
different compatible Blender runtime. It overrides `HYBRID_BLENDER` for Source
only; an explicit `--blender` argument still wins. This allows the tested offline
SourceIO container and host MMD Blender to coexist in one app session. Without the
Source override, the existing Blender selection remains unchanged. Standalone
files require no installed game. Empty workshop settings do not scan the current
project as an installed addon folder, and shallow game paths have no assumed
Steam-library ancestor. Installed browsing keeps its host validation.

The actual supplied native fixtures now cover13renderable PMD/PMX conversions,
three manually posed/portable/cold MMD characters, a PMX environment with an
independent overlay/movie, native MMD Tools-exported VPD/VMD review/apply/UndoRedo,
and a selected GMA character with generated HAS physics/freeze. The bone-only
`Dammy_Bone.pmd` explicitly refuses as a rendered model before conversion. It is
not silently accepted as an empty GLB.

Native Source `.phy` files are fingerprinted and retained in the preparation
folder, with a visible import-warning entry explaining that native collision
shapes and constraints are not applied. HAS Physics creates its own bodies. This
ancestry persists in packed HAS; it does not claim reproduction of Source physics.

The street PMX still lacks its five named atlas PNG file dependencies. Its
material-color fallback and missing-texture diagnostics are tested; the chat
images were not assigned filenames by appearance. `temp.gma` exceeds the32MiB
file-transfer limit and was not inspected. Complete BSP and VRM native acceptance,
target Windows/device tests and artist fidelity remain open. Owner assets and
rendered native artwork stay outside Git.
