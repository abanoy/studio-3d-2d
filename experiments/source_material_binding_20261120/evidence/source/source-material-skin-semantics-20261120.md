# Source material and skin-reference semantics

2026-11-20. Source-only research through the GitHub connector first, plus the
approved local SourceIO source. No native assets, parsers, Blender, processes or
Git commands were run. Only this note was written; existing candidates stay
unchanged. This establishes a future mapping contract with explicit evidence
boundaries, not a GMod MDL49 renderer qualification.

## Primary evidence and pins

| Primary source | Commit | Git content blob |
| --- | --- | --- |
| [Valve SDK studio.h](https://github.com/ValveSoftware/source-sdk-2013/blob/3e957b70b167929f120360115d359d1ecb4c1699/src/public/studio.h#L2228) | `3e957b70b167929f120360115d359d1ecb4c1699` | `9480d15d95a73f2214dd9fd619aa5ae922f81b3c` |
| [Valve motionmapper.h](https://github.com/ValveSoftware/source-sdk-2013/blob/3e957b70b167929f120360115d359d1ecb4c1699/src/utils/motionmapper/motionmapper.h#L130) | same SDK commit | `6b487e3cee357a4ee78580fafa6b1a272e97e48f` |
| [Valve GoldSrc model-viewer renderer](https://github.com/ValveSoftware/halflife/blob/b1b5cf5892918535619b2937bb927e46cb097ba1/utils/mdlviewer/studio_render.cpp#L621) | `b1b5cf5892918535619b2937bb927e46cb097ba1` | `bcaea00efe76d6152c06deb1276fbb1e2a647cfa` |

The SDK header distinguishes `numtextures`/`pTexture` from the replaceable skin
table, whose dimensions are `numskinfamilies` by `numskinref`. Its `pSkinref`
returns a short-array pointer. The motionmapper declaration explicitly documents
the table as indexed by skin then skin-reference, producing a texture index.
Thus equal counts do not collapse these two integer domains.

The official GoldSrc renderer provides an executable example of the lookup:
it selects a row using the chosen skin and table width, then uses that row's
mesh skin-reference value to select the texture. With selected skin zero it
uses the first row, not an assumed identity map. See the linked lines621–668.

**Boundary:** that renderer is GoldSrc, not Source MDL49. The pinned public
[SDK header explicitly sets STUDIO_VERSION48](https://github.com/ValveSoftware/source-sdk-2013/blob/3e957b70b167929f120360115d359d1ecb4c1699/src/public/studio.h#L70).
Its `mstudiomesh_t.material` field is an integer but does not itself document
the complete renderer lookup. The searched public SDK does not expose that
renderer implementation. Therefore applying the table interpretation to
MDL49 mesh.material is a clearly identified Source-family mapping candidate,
not a proof of the installed GMod engine's behavior, invalid-skin fallback,
material overrides or LOD replacement paths. Valve Developer Community pages
for the MDL format and `$texturegroup` were inaccessible during this research;
their contents are not used as evidence.

## What the approved SourceIO actually does

All files below belong to the approved574-file SourceIO catalogue in immutable
lock SHA256 `3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6`.

- `library/models/mdl/v49/mdl_file.py`, 5436 bytes, SHA256
  `a30f5fae981dedff47de4ce56152b876acd734bbb03e0df59ec9d320351f10ed`:
  loads a separate texture list, then each skin row as uint16 indices into that
  list, constructing `skin_groups` Material references.
- `library/models/mdl/structs/mesh.py`, 2210 bytes, SHA256
  `ea5c9d478b40924e8610c3d4699b894f6b4f56a375b0594ebfb581d80100ef71`:
  reads the raw mesh integer as `material_index`.
- `blender_bindings/models/mdl49/import_mdl.py`, 12880 bytes, SHA256
  `173a34ecae50e0b7a9d467908f238c02d5d7e19df3c7f52387534914d703233b`:
  indexes `mdl.materials[mat_id]` directly when assigning mesh slots. It does
  not first apply skin row0. It separately stores skin_groups and active_skin0
  metadata; those properties alone do not demonstrate a skin swap was applied.

Accordingly c04 metadata and the planned host's raw-import comparison describe
this **SourceIO direct-index behavior**. They must not be labeled native
default-skin correctness. No change to that parser or SDK is made here.

## Independently testable future pure contract

Use a new explicit policy/API, for example
`resolve_skin_references(metadata, selected_skin)`. Do not silently reinterpret
the existing `material_index` output. Root must authenticate metadata against
the native input pins separately.

1. Require exact bounded integer counts, a nonempty skin table, an exact integer
   selected family in range, rectangular rows of exactly numskinref entries,
   and each decoded entry in the texture-table domain. The SDK uses short;
   the existing uint16 reader's closed `<256` material range rejects negative/
   high-bit sentinels as well. No wrapping, clamping or invented empty-table
   identity fallback is admitted.
2. For each native mesh retain its structural identity
   `(bodypart, model, mesh)` and raw integer `r`. Require `0 <= r < numskinref`
   for this candidate. Resolve `t = skin_families[selected_skin][r]`; require
   `0 <= t < numtextures`. Preserve both `r` and `t` and the selected row.
3. Rows need not be permutations: repeated texture ordinals are an explicit
   many-to-one relation. Preserve raw references/order; do not sort, deduplicate,
   infer a bijection or match names/appearance to manufacture correspondence.
4. Independently record SourceIO's observed direct texture ordinal `r`, which
   additionally requires `r < numtextures`. Compare it with candidate `t`.
   Report exact agreement or difference; do not alter slots during this proof.
   A general native-reference candidate can allow `r >= numtextures` when its
   row resolves validly, whereas the current SourceIO direct-import profile
   cannot. These are distinct admission profiles.
5. Keep VTX face order, actual Blender slots, placeholder aliases and B material
   refs separate. The cbb4 triangle-material stream carries raw mesh integers;
   preserve its authenticated native provenance before applying this explicit
   lookup. A value-domain check alone cannot re-establish face correspondence.

Synthetic cases should include a nonidentity row0, another selected skin,
numskinref different from numtextures, a repeated target texture, raw/value
boundary failures, bool/negative/out-of-range selection and empty-table refusal.
No actual-engine flag follows from these pure tests.

## Exact Junko preflight and remaining boundary

Root's actual pure RAM preflight, recorded in
`output/source-material-default-skin-preflight-20261120.json`, reports four
texture records, four skin references, one family and four used raw mesh fields.
It independently checked both index domains and found
`skin_families[0][r] == r` for every used field. The metadata digest is
`2447c7862e4d5db64d3072e3a40699456e196558c12c9354312242312a96d290`;
row0 digest is `f2f991d74dfbb2edf7f4475dcb7d82989de00a71e44bb11d4a6fbb49442577b6`.
Only that public scalar/digest receipt was read here, not native arrays.

This derives agreement rather than assuming identity from equal dimensions.
It establishes equality of two integer policies for this exact family/selection,
not a different family, installed MDL49 renderer or historical B import branch.
The later cold host/binder must repeat the derivation from its freshly admitted
native refs; a copied success token or row digest is not its oracle.

Retain native/default-skin rendering semantics false until the relevant engine
boundary is qualified. Material dependency/append admission, resource reachability,
strict unchanged non-NORMAL B comparison and the unchanged `2e-5` normal gate
remain subsequent, independent work. None of this relabels B points or changes
the app's implementation/acceptance scores.
