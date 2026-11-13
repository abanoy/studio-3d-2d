# Bounded Source native geometry oracle — format review

2026-11-13. Documentation-only review. No SourceIO/native reader was imported or executed; no model/converter/app/viewer/GPU runtime, download, extraction, or production/Git edit occurred. The parent owns the independent stdlib implementation and must pass synthetic controls before reading actual geometry.

## Evidence and version boundary

Primary Valve sources: [optimize.h](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/public/optimize.h), [studio.h](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/public/studio.h), and [VRAD's native index traversal](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/utils/vrad/vradstaticprops.cpp). Valve's public studio header declares model version 48; the supplied models are version 49. Therefore this is a bounded compatibility hypothesis for common disk structures, not broad MDL49 format authority.

Corroborating documentation was read from the approved local SourceIO pin `fe24260b97ac03b899d9b5d4f0fd7b34772f3647`: `library/models/vtx/v6/structs/header.py`, v7 structs/bodypart/model/lod/mesh/strip/strip_group, v7/vtx.py; VVD header/fixup/__init__; MDL structs/header/model/mesh/bodygroup/bone; and `blender_bindings/models/mdl49/import_mdl.py` and `models/common.py`. These are references only, never imported, called, or copied into the oracle.

## VTX7 legacy packed layout

Offsets below are arithmetic derived from Valve's packed declarations and independently corroborated by the pinned reader's sequential reads. Little endian. `i/u/h/H/B/b/f` mean signed32/unsigned32/signed16/unsigned16/unsigned8/signed8/float32. Sizes include no implicit alignment.

| Record(size) | Fields at byte offsets |
|---|---|
| File(36) | 0:i version;4:i cache;8:H maxStripBones;10:H maxTriBones;12:i maxVertexBones;16:i checksum;20:i LODs;24:i replacementOffset;28:i bodyparts;32:i bodypartOffset |
| Bodypart(8) | 0:i models;4:i modelOffset |
| Model(8) | 0:i LODs;4:i LODOffset |
| LOD(12) | 0:i meshes;4:i meshOffset;8:f switchPoint |
| Mesh(9) | 0:i groups;4:i groupOffset;8:B flags |
| Stripgroup(25) | 0:i vertices;4:i vertexOffset;8:i indices;12:i indexOffset;16:i strips;20:i stripOffset;24:B flags |
| Vertex(9) | 0:3B weightSlots;3:B bones;4:H origMeshVertID;6:3b boneIDs |
| Strip(27) | 0:i indices;4:i indexOffset;8:i vertices;12:i vertexOffset;16:h bones;18:B flags;19:i changes;23:i changeOffset |
| BoneChange(8) | 0:i hardwareID;4:i newBoneID |
| ReplacementList(8) | 0:i replacements;4:i replacementOffset |
| Replacement(6) | 0:h materialID;2:i nameOffset |

All `...Offset` byte pointers above are relative to their owning record, except File offsets, whose owner is the file header at zero. A strip's indexOffset and vertexOffset are element offsets into the stripgroup's arrays, not byte pointers. Index array entries are unsigned16. Name pointers in replacement entries are relative to that replacement entry. Require version7, three maxVertexBones, matching checksum, bounded counts and valid ranges. See the primary [packed declarations](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/public/optimize.h).

**Important branch ambiguity:** Valve's flags name bit1 (0x02) as triangle strip. The pinned v7 reader instead names 0x02/0x04 regular/extraordinary quad lists, and retries with an extra eight bytes per stripgroup/strip after parse errors. Do not port this heuristic. Accept only the legacy layout and exact strip flags 0x01 (triangle list) for the first oracle. Version7 alone does not distinguish later extended layouts. If layout coverage or structural invariants are ambiguous, fail closed rather than claiming general v7 support.

The stripgroup flags distinguish flexed, hardware-skinned and delta-flexed groups (0x01/0x02/0x04); Valve also declares a runtime-only suppression flag0x08. Record flags, reject unknown disk combinations, and keep flex flags separate from this base-geometry proof. Mesh flags0x01/0x02 describe teeth/eyes, not topology.

## Exact triangle and vertex addressing

Valve's VRAD traversal at lines1791–1813,1962–2002 directly demonstrates the chain:

`stripgroup.indices[strip.indexOffset + i] -> stripgroup.vertices[index].origMeshVertID -> MDL mesh vertex data`

It does **not** add `strip.vertexOffset` to the group index value. It keeps triangle triples in stored order and rejects non-trilists in this path. This corroborates the intended bounded decoder, but is not a general triangle-strip/restart decoder. [Primary implementation](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/utils/vrad/vradstaticprops.cpp).

Iterate each strip's declared range and require its index count divisible by3. Validate every group index and resulting original mesh vertex ID. Track range coverage; do not blindly flatten all group indices and silently include unused ranges, duplicates, or overlap. For the first parser, require nonoverlapping complete strip coverage and reject degenerates instead of deleting them silently. A 0xffff value is not automatically a primitive restart: in this scope it is an ordinary index if in range, otherwise an error. No restart convention was established.

Use model and mesh origins separately: fixed-up VVD row is `model.vertexindex_bytes/48 + mesh.vertexoffset_vertices + origMeshVertID`. Require model byte offset divisible by48, mesh range within its model, model range within fixed-up LOD0, and matching MDL/VTX bodypart/model/mesh counts. The two offsets must not be confused or added twice.

For GLB comparison, preserve multiplicity and material ownership. Cyclic rotation of a triangle's three complete corner records may be canonicalized; reversal must remain distinguishable under the single declared coordinate/winding contract. Do not discard UVs/weights from a corner signature or search arbitrary axis flips/scales/permutations until a match appears. Identical corner data can merge/split at export: a triangle multiset proves base geometric/attribute equivalence, not preservation of original vertex identity or future morph behavior.

## VVD4 and MDL common disk prefixes

The local pinned reader corroborates VVD header64, fixup12, vertex48 and tangent16 sizes. VVD absolute header offsets: magic0, version4, checksum8, LODcount12, eightLODcounts16..47, fixupCount48, fixupOffset52, vertexDataOffset56, tangentDataOffset60. Require IDSV/version4, exact common checksum,1..8LODs, bounded sizes. Refuse compressed IDCV, extra attributes and unexplained data layouts in this first proof.

Vertex48: weights0/4/8 (float32); global bone bytes12..14; influenceCount15; position16/20/24; normal28/32/36; UV40/44. Tangents, when used, are four float32s in their own block. Read the native influence count, not the pinned dtype's misleading `pad` field label. Require1..3 influences, valid used global bone IDs, finite nonnegative weights and a fixed numerical sum tolerance; unused nonzero weights must not be silently accepted.

Fixup12: signed32 LOD/sourceVertexID/count at0/4/8. Build the LOD0 table in fixup order, concatenating source ranges whose LOD>=0. Require nonnegative valid LODs/ranges, no overlaps or omissions for this scope, bounded target count, and final count exactly header LOD0 count. With no fixups, copy the first LOD0 rows. Tangents use the same source-row mapping. This follows the official `Studio_LoadVertexes` implementation, which must not be replaced by sorting fixups or treating source indices as already mesh-ordered. [Valve header/implementation](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/public/studio.h), around lines1793–1866 and2975–3059.

Pinned MDL49 documentation supports the following required prefix offsets (do not use host C++ pointer sizes): header checksum8,length76,flags152,boneCount156/boneOffset160,textureCount204/textureOffset208,texturePathCount212/texturePathOffset216,skinColumns220/families224/tableOffset228,bodypartCount232/bodypartOffset236. Require IDST/version49 and declared file length equal actual size. Treat checksum as an exact32bit token, not a content hash; keep SHA256 separately.

MDL bodypart16: nameOffset0,modelCount4,base8,modelOffset12. Model148: name[64]0,type64,radius68,meshCount72/meshOffset76,vertexCount80,vertexBytes84,tangentBytes88,attachmentCount92/offset96,eyeballCount100/offset104; later pointer/reserved fields are not dereferenced. Mesh116: materialColumn0,modelRelativeBackPointer4,vertexCount8,meshVertexOffset12,flexCount16/flexOffset20,materialType24,param28,meshID32,center36; later runtime/reserved fields are not dereferenced. Relative pointers belong to their respective records. The pinned model reader divides version>36 vertexBytes by48; the independent implementation should retain both raw bytes and checked row index.

For native bone-name/parent correspondence, the common216byte disk bone record has nameOffset0,parent4,six signed32 controllerIDs8..31,position32,quaternion44,Euler60,positionScale72,rotationScale84,poseToBone3x4matrix96,alignmentQuaternion144,flags160,procedureType164/procedureOffset168,physicsBone172,surfaceNameOffset176,contents180,reserved184..215. Validate bounded relative C strings and a cycle-free parent tree. The pinned reader happens to read controllerIDs as six float32s; do not copy that semantic mismatch into the independent parser. The official declaration uses integer IDs. Preserve raw name bytes and the explicitly chosen encoding, especially for existing non-ASCII names; do not rename them from semantic guesses.

A native mesh material field is a skin-table column. Resolve the requested family to a material-table index separately, preserving native column/family/index provenance. Fail if a LOD0 VTX material replacement is nonempty until its semantics are explicitly implemented; do not quietly prefer MDL material names over a replacement.

## Weight/bone palette limits

Native VVD weights use global MDL bone indices. VTX weightSlots index those native weight slots. VTX boneIDs are global only for software skinning; hardware-skinned IDs identify hardware palette slots. Do not compare them directly to GLB joint palette indices. The BoneChange record exposes hardwareID/newBoneID, but a full renderer's palette lifetime/reset behavior was not established by this review.

The smallest valid independent weight claim is therefore native VVD global name/index/weight tuples for each VTX-addressed corner versus GLB joint-name/weight tuples, with exact unique bone-name/parent correspondence. It does not need a guessed hardware palette. If also validating palette consistency, require explicit initialization for every used slot, preserve per-strip state changes, reject unbound/conflicting references and state clearly which persistence rule was proved. Otherwise label hardware-state equivalence UNTESTED.

The pinned importer uses all positive native VVD weights by native bone name, reverses its flattened triangle array, flips V for Blender UVs, and exports through Blender. These observations explain possible representation differences but are not an independent source of expected native geometry. Establish the frozen worker's declared scale/basis/UV/winding contract once, before comparison; never tune it based on failed actual matches. Preserve raw native and raw GLB records in the comparison path.

## Synthetic controls before actual inputs

- Nonzero model and mesh origins; group indices deliberately inconsistent with adding strip.vertexOffset; multiple strips/groups and complete coverage.
- Fixup permutation that changes row order, zero-fixup path, missing/overlapping/out-of-range ranges, mismatched counts/checksums and truncated blocks.
- Valid1/2/3-influence rows; nonidentity GLB palette order; reordered VTX weight slots; invalid used bone IDs/counts/NaNs/weights; uninitialized hardware palette rejected when that optional claim is attempted.
- A triangle whose reversed winding, changedUV or changedweight must fail even when position bounds are unchanged; duplicate/coincident triangles must preserve multiplicity.
- Alternate blank bodygroup choices, nonzero selected skin family, differing material columns, and empty/allblank geometry classified separately.
- Reject unsupported strip flags, ambiguous extended layout, compressed VVD, unexpected LOD0 material replacements, huge counts and offsets outside the owning file.

These checks define a base geometry/UV/native weight/topology scope. They do not establish Source shader appearance, native flex-rule evaluation, physics, animation, native GPU deformation or viewer fidelity. Actual12-case results remain UNRUN in this review.
