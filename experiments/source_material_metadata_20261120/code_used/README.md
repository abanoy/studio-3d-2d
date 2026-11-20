# Source material metadata oracle preparation

2026-11-20. **AUTHORED, UNRUN.** This directory contains a pure RAM-only candidate
and fabricated byte tests. No native file, private asset, Blender, engine,
process, Git operation or test execution was used to author it. Existing
application sources, cbb4 helper, packets and documentation were not changed.

## API and scope

`material_metadata.derive_material_metadata(native_refs)` accepts exactly
`mdl`, `vvd`, `vtx` descriptors, each exactly `{raw: bytes, bytes: int,
sha256: lowercase_sha256}`. It recomputes every digest and size. Root must first
authenticate those descriptors against the immutable native input lock: a
self-consistent descriptor is not independent provenance. The future Junko
worker should retain the existing exact three-file pins, not replace them with
new hashes calculated from arbitrary input.

The returned `has_private_mdl49_material_skin_metadata_candidate_1` dictionary
contains checksum/source identities and private metadata: native material-table
ordinals, exact printable-ASCII names, flags/used, descriptor hashes, ordered
search paths, uint16 skin-family references, and bodypart/model/mesh material
ordinals in native order. Duplicate names, duplicate paths and empty paths are
preserved; they are not collapsed into Blender slot identities. Returned names
and arrays stay private/RAM. Public summaries should expose counts/digests and
the explicit false qualification flags only.

The parser independently checks MDL49 IDST/version/declared length, matching
VVD4 IDSV and standard VTX7 checksums, model VVD ranges, metadata counts,
bounded relative/absolute offsets, nonoverlapping owned tables, terminated
strings outside those tables, 64-byte material records, 4-byte path references,
uint16 skin cells, 16-byte bodyparts, 148-byte models and 116-byte mesh records.
VVD vertex/tangent/fixup table extents and VTX body/model/LOD0/mesh header
correspondence are checked without reading vertex values or strip groups.

This is **not a complete MDL/VVD/VTX validator**. Other MDL sections, material
pointer/reserved-word meanings, VVD fixup contents/normal values and VTX
triangles/hardware state are unqualified. Only the metadata tables actually read
here receive overlap ownership checks. Keep the independent complete native
point candidate and all existing admission gates alongside this reader.

No observed Blender mesh, B snapshot, resource manifest or output label enters
the API. There is no face-binding API yet. The unchanged cbb4 producer already
returns each model's `materials` triangle candidate in reversed complete
triangle order. A later Root worker can consume that separately authenticated
RAM candidate and compare actual face/slot references; this reader does not
claim it has independently rederived or qualified that VTX face stream.

## Source basis and pins

Read-only approved SourceIO tree:
`C:/a/Programming/cloudflare/has-neon-review-20261116-c2d52ff/output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647`.
Its complete574-file catalogue belongs to immutable lock SHA256
`3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6`.

| Source | Bytes | SHA256 |
| --- | ---: | --- |
| `library/models/mdl/structs/header.py` | 29180 | `03fe4f685c3818785c9b5ff81356f91aa9ab8160d1a17ca27e57520a1c37f57f` |
| `library/models/mdl/structs/material.py` | 1919 | `2513cf53c3fbefc1e290351c73cb56b5a0387eac7ede9f900f2d5b72e31d09ab` |
| `library/models/mdl/structs/model.py` | 5674 | `d11d7e0235e2607f8d4ca2e5e32ca482969035277f274b57f713df8e8ba0c176` |
| `library/models/mdl/structs/mesh.py` | 2210 | `ea5c9d478b40924e8610c3d4699b894f6b4f56a375b0594ebfb581d80100ef71` |
| `library/models/mdl/v49/mdl_file.py` | 5436 | `a30f5fae981dedff47de4ce56152b876acd734bbb03e0df59ec9d320351f10ed` |
| `blender_bindings/models/common.py` | 23149 | `2522f2a451f082edcfcf66c3b445782716e24feb45f8b43d5d6e459f6408f750` |
| `blender_bindings/models/mdl49/import_mdl.py` | 12880 | `173a34ecae50e0b7a9d467908f238c02d5d7e19df3c7f52387534914d703233b` |
| `blender_bindings/utils/bpy_utils.py` | 7221 | `4c8bb4a31ed7cac3278567632673acf53befd84dc852635dff813a20f38332e4` |
| `library/utils/file_utils.py` | 20519 | `6d91d0eae0ea912aff31dc210f24665bf4303f71c00ebc3b4245aaf775185ba0` |

Also read the unchanged independent candidate:
`experiments/native_point_expectation_bone_state_fix_20261118/native_point_expectation.py`,
27615 bytes, SHA256
`cbb4eca98a6cf5045211dc10bd8e060b79492ec306d61a4d29679fc0d5cc184d`.
The layout decoder is independently authored with `struct` bounds/ownership
checks; it does not import or execute the SourceIO parser or cbb4 helper.

## Closed profile and next checks

Ceilings: 128MiB/input, 200000 aggregate model vertices, 256 materials/paths/
skin families/bodyparts, 1024 models, 65536 aggregate meshes, 4096 tables per
reader and 256-byte metadata strings. Refuse static props, flexes, eyeballs,
non-ASCII/negative-relative strings, extra VVD data, VTX material replacements,
multiple VTX LODs, unknown input schemas and out-of-domain material indices.
Some valid Source files may be outside this deliberately narrow profile.

The synthetic fixture manually lays out two materials, two models/three meshes,
reversed/nontrivial skin indices and duplicate/empty search paths. Explicit
offsets do not use parser constants. Its geometry payload is intentionally not
a valid complete native mesh, making the metadata-only scope testable. Negative
cases cover integrity/schema/signatures, checksum mixing, bounds/overlap/string
failures, skin/material domains, model/mesh spans and unsupported profile paths.

Prospective **Root-only** CPU command, after source review (not executed here):

```powershell
& 'C:\Program Files\Python313\python.exe' -B -m unittest discover -s 'C:\a\Programming\cloudflare\has-body-addition-20261120\output\source-material-oracle-prep-20261120' -p 'test_material_metadata.py' -v
```

Only after Root tests the reader and separately authenticates actual native
input bytes may a later host qualify native-material -> actual placeholder ->
actual slot -> face order. Material-only B dependency admission, returned library
refs, export/gather binding, strict unchanged non-NORMAL comparison and the
original `2e-5` normal gate remain separate. Historical B identity, current B
relabeling, generic model support and HAS adoption remain unqualified.
