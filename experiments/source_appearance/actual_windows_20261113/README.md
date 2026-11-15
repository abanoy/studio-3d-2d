# Actual Windows static appearance verification

At root `2904f3f18e4211f95ddd385953219b2e5460aee9`, the separately frozen worker
completed fourteen serial cases: twelve GLB bundles and two exact all-blank
refusals. `metadata/actual_results.json` records the per-case selected indices,
material/dependency/structure results and evidence hashes. The documentation and
benchmark distinguish this from GPU rendering, native visual fidelity, app
selection/adoption, Undo/HAS/movie and owner/device acceptance.

No native model, archive, texture, image payload, GLB, blend, HAS or movie is
included here. The source/fixture copies are byte-identical to the reviewed
executed sources. `source-checkpoint.json` records hashes. Existing model inputs
remain private and must be provided independently from the owner-authorized
originals. Do not fetch substitutes or copy another package's missing bump map.

## Recreate an owned replay layout

These helpers deliberately derive their writable task root from an owned
`<checkout>/output/<task>/source` location. **Do not run them directly from the
experiment archive.** Review all embedded machine paths before a new run.

1. Retrieve the saved repository checkpoint into an isolated checkout. Preserve
   existing owner work, installations and previous reviews/recovery.
2. Recreate `output/source-appearance-prototype/Studio` from exact base
   `85fa482b3ef1ed752e8a97191b5ea7b235cea7aa`, without `.git`, caches, outputs or
   private artifacts. Overlay the four files in `../overlay/`. Verify their
   recorded hashes from `../checkpoint.json`; do not modify the active app.
3. Create a fresh owned task layout and copy this `source/`, the fixture plan,
   command vectors, empty mount plan and twelve requests into the corresponding
   `output/<task>/` locations. The actual historical task name was
   `sfm-next-cases-20261112`. Current constants also name the prototype path.
4. Validate original archive SHA/size/mtime, the indexed resource allowlist and
   existing approved runtimes. The plan's raw SHA is
   `4a747c6bc883af7e69ca448a0d7ac60f76f14b78550682647f683449cd1d2aaf`.
   It selects exactly 296 resources / 181,460,484 bytes. Use only the existing
   approved Python, Blender 5.1.2 and pinned SourceIO fe242 runtime; installing
   replacements is a separate authorization. No game installation is needed for
   these complete standalone sources, and installed content cannot fill gaps.
5. Default `stage_resources.py` is read-only preflight. After reviewing its exact
   scope, `--execute` streams only allowlisted members into a fresh stage. It
   rejects links, unsafe/duplicate paths, encryption, changed CRC/size, overwrite
   and unlisted resource types. Keep failed/partial outputs.
6. Run `vmt_closure.py` with that actual staging receipt and its raw SHA. Nitori's
   one native missing `materials/hairbump.vtf` remains explicit; Keiki's observed
   texture references resolve. Both basic bridge base-texture inputs resolve.
7. Use `background_conversion_driver.py --prepare-inputs <fresh-lock.json>
   --expected-root-revision <exact-stable-40-character-commit>`, supplying the
   fresh staging/VMT receipt paths. Record the printed schema3 lock SHA; run
   default preflight with `--input-lock` / `--lock-sha256` first. The code, root
   functional files, prototype, inputs and runtime must stay frozen afterward.
8. After confirming no other job/agent owns the conversion lease, append
   `--run-conversions --lease-confirmed`. The fourteen cases are serial, ordinary
   baselines first, then defaults/variants, then exact refusals. A fresh output
   folder is mandatory; unexpected failure stops the series. Retain actual
   commands, private/self-attestation receipts, logs, bundles and preservation
   evidence. Do not use a visible fallback or reinterpret an old exit 2.

Historical locks and Windows modification stamps are evidence of the actual
run, not portable fresh fixtures. `metadata/historical-input-lock3.json.gz`
decompresses to SHA
`9a3d65108148a2e41eebb6a2dabfd556541aff27affe1cc48e4c099e21e00521`.
Do not reuse it after source/HEAD/path/runtime changes, alter original file
timestamps to match it, or present a newly rebound fixture as the old exact run.
If relocation changes reviewed absolute paths or original identities, record a
fresh explicitly reviewed fixture plan and corresponding owned guard hashes;
retain the historical plan and assertions. Old schema1/schema2 helpers and
negative controls also reference historical fixture paths. Restore/rebind their
metadata prerequisites transparently before rerunning them on another machine.

The preserved `tools/sfm_native_metadata_probe.py` and pinned SourceIO MDL49
header/material/bodypart/model/mesh/bone readers give the native metadata route.
For the column join, read each actual `mesh.material_index` as the native skin
reference column, then the requested skin row's material-table index. Resolve
the resulting native name using the actual CDMaterials paths and the pinned
`resolve_model_material` candidate order against only the owned resource index.
The resulting VMT SHA must match the actual converter report/dependency before
joining the actual GLB material, texture and embedded image. Raw bone names are
the signed relative string offset at each MDL49 216-byte bone record; preserve
the original bytes/hash and pinned Latin1 spelling rather than renaming them.
Actual native columns, search paths and results are in the compact metadata;
full private rest/bind and original payloads are deliberately omitted.

## Scope and next probe

The source-only worker remains unshipped. Nitori's base/glow geometry is exactly
coincident, and its native additive layer is ordinary PBR in the GLB. The 4×4
image named `black.vtf` actually contains opaque greys 0/40/120; do not infer
color from that filename. Exact material/image correspondence is established,
not native shader or pixel fidelity.

Keiki's actual Tools target has 1,180 nonzero used deltas in selections
000/001/010/011 and is absent from 100/101/110. Useful actual weighted native
pose candidates are Nitori hand 8 and Keiki box 23. See
[the small next probe](../../../docs/sfm_static_appearance_next_probe_2026-11-13.md) and
`metadata/next_probe_compact.json` for the small future render/adoption plan.

The wider 22-archive / 82-MDL / 71-definition corpus still needs separately
scoped coverage of other skins/bodygroups, nonfacial controls, native shader
features, jiggle, component binding, resources and runtime/animated variants.
Metadata presence and fourteen static worker cases do not close those cases.
