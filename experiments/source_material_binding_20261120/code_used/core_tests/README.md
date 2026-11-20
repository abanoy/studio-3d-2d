# Fresh SourceIO material binding observer preparation

2026-11-20. **AUTHORED, UNRUN.** Source and fabricated-reference tests only.
The author did not execute these files, open native inputs, start Blender, query
processes, modify the SDK/application, use Git, or alter an existing packet.

`material_binding.py` uses only the standard library and performs no IO. It
observes an unchanged fresh import; it does not append materials, rebind slots,
switch skins, edit custom data, repair a model, create carriers, or export.
`test_material_binding.py` contains 34 synthetic test methods. Root owns all
execution and any later qualification claims.

## Independent inputs and bounded profile

The constructor accepts the private RAM outputs of these authenticated readers:

- unchanged cbb4 `derive_native_point_rows`: source identities, checksum,
  renderable model identities, point/corner cardinality and the complete ordered
  per-triangle raw-material stream;
- unchanged c04 `derive_material_metadata`: the same exact three source
  identities/checksum, native material records, skin rows and body/model/mesh
  metadata.

The host must authenticate both code files and the native three-file family
against the immutable approved lock. Self-consistent descriptors are insufficient
provenance. Neither old B geometry nor observed labels enter either derivation.
The observer copies its bounded expected facts, retaining only private arrays
and genuine refs in RAM. Maximums are 256 material records/skin families/body
parts, 1024 model records, 65536 mesh records, 200000 observed points and 333333
triangles in aggregate. Scalar indices must be exact Python `int`, including
rejection of booleans; metadata labels must be bounded printable ASCII.

This closed profile refuses duplicate material names, duplicate body names and
placeholder aliases across distinct native material ordinals. The SourceIO
`get_or_create_material` path may legitimately alias materials in other files;
such files are outside this observer's scope. A refusal does not authorize
repair, relabeling or normalization. The host independently rejects preexisting,
orphan or extra newly created Material/Mesh IDs and authenticates source types.

The cbb4 `materials` candidate already reverses the complete triangle order to
match the pinned importer. It is used unchanged. For each renderable model, the
expected slot order is the sorted set of used raw material indices, as in the
pinned importer's `np.unique` loop. Actual Material refs must connect the native
`MaterialV49.bpy_material`, Mesh material list, Object DATA slots and every
ordered MeshPolygon index. Equal names do not substitute for reference identity.

Native mesh `material` and a resolved native skin-family result are separate
domains. The observer independently requires every raw field in every renderable
MDL mesh to be within `skin_reference_count`, and requires
`skin_families[0][raw] == raw` on those fields. A nonidentity default row refuses
without repair. Other skin rows preserve order and repeated references; they
need not be permutations. This verifies the explicit candidate default-table
agreement only. The public SDK basis is MDL48; actual MDL49 engine rendering,
native skin switching and general native material fidelity remain unqualified.
See [the source semantics note](../source-material-skin-semantics-20261120.md).

## Host API

```python
observer = MaterialBinding(
    native, material_metadata,
    source_material_type=MaterialV49, source_model_type=ModelV36Plus,
    source_body_type=BodyPart, source_mesh_type=MeshV36Plus,
    object_type=bpy.types.Object, mesh_types=(FastMesh, bpy.types.Mesh),
    material_type=bpy.types.Material,
)
observer.observe(phase, model, obj, mesh, snapshot)
summary = observer.returned(container, [(obj, snapshot), ...])
```

The four phases are the current-ID observer's exact order:
`before_setter`, `after_setter`, `before_validate`, `after_validate`.
All early slots are empty, all early polygon material indices are zero and
`skin_groups` is absent. The late phases and final returned objects must expose
the complete expected slots/face stream and skin property. The host keeps the
existing independent current-ID/f32/69-group/weight and geometry observations
in the same one fresh import. This observer neither replaces nor qualifies those
checks. Both collectors must pass; exceptions swallowed by a caller still latch
this collector failed and prevent publication.

Each snapshot is an exact ordinary `dict` with these nine fields. Containers
below are exact tuples created from bounded direct API reads; do not coerce
integers, strings, names or Material references into the expected values.

| Field | Private snapshot value |
| --- | --- |
| `source_materials` | `(nativeMatRef, name, flags, used, bpyMatRef, bpyMatRef.name, bpyMatRef.get('full_path'))` for each native ordinal |
| `source_skins` | tuple of tuples of actual `mdl.skin_groups` native Material refs |
| `source_parts` | `(partRef, part.name, models)` in native body order; each model is `(modelRef, model.name, vertex_offset, vertex_count, meshes)`; each mesh is `(nativeMeshRef, material_index, vertex_index_start, vertex_count)` |
| `slots` | actual Material refs in `mesh.materials` order |
| `object_slots` | actual `slot.material` refs in `obj.material_slots` order |
| `faces` | `(polygon.index, loop_start, loop_total, material_index)` for every polygon in order |
| `skin_groups` | `None` early; late tuple of `(exact_key, tuple(values))` from actual IDProperty group; values are all genuine Material IDs or all exact strings |
| `active_skin` | actual exact string `'0'` |
| `model_type` | actual exact string `'s1'` |

Within each row, fields are verified against the independently decoded native
facts and the actual reference's fields. Source refs, placeholders and selected
logical model refs must remain identical through every phase and final return.
The Object and Mesh must be actual non-evaluated IDs (`original is self`), with
`obj.data is mesh`. Object slots must be DATA-linked and identical to Mesh slots.
The host must additionally verify genuine collection/element types and bound
counts before constructing these snapshots. No name-based `bpy.data.*.get`
lookup may supply a ref. In the NoMaterialIO profile the exact placeholder
`full_path` is `native_name.lstrip('/').casefold()`.

For late `skin_groups`, exact Material IDs are preferred. If the original
importer took its existing exception fallback, every string must equal the
unique actual Material name for that skin-cell reference. Case changes,
mixed representations, renamed lookalikes and wrong same-named Material IDs
refuse. Actual Object property keys/values are also read back and compared to
the snapshot; no actual skin switch is performed. A model's storage branch must
remain identical through validation and return.

`returned` requires the original renderable object order and exact native
body/model order in `container.bodygroups`, including `None` for blank models.
It rechecks all snapshots and closes the single collector. No references or
private names appear in its compact summary: only counts, stream digests,
storage-branch labels and explicit scope flags.

## Test intent and actual run boundary

The fixture has two materials, two renderable models plus a blank body option,
three native meshes, a nontrivial three-face raw stream `[1,0,1]`, and a second
model whose raw material 1 maps to its sole actual slot 0. A nondefault skin
contains repeated references. Tests cover pointer and exact-string branches,
native family mixing, default nonidentity/ref-domain refusal, actual reference
substitution, hidden snapshot drift, slot/face ordering, booleans, DATA overrides,
skin branch drift, missing/replayed boundaries, swallowed failures, final blank
bodygroups and absence of observer mutation/private summary labels.

Root-only prospective CPU invocation (not run by the author):

```powershell
& 'C:\Program Files\Python313\python.exe' -B -m unittest discover -s 'C:\a\Programming\cloudflare\has-body-addition-20261120\output\source-material-binding-prep-20261120' -p 'test_material_binding.py' -v
```

The separate new host preparation is
`output/source-material-binding-host-20261120`. It must retain the prior
four-stage current-ID/ordered-weight evidence, bind this module and metadata
reader as two additional immutable reads (592, not the older 590), and preserve
the original no-owner-scene/private-desktop/preservation constraints. Root runs
that host only after source and synthetic reviews. No actual API success is
claimed by this preparation.

Historical B causality, B dependency closure/material-library reads, textures,
image pixels, non-NORMAL semantic equivalence, the original strict `2e-5` normal
gate, current normal fidelity, carrier/exporter binding, general storage rules
and HAS application adoption remain separate and false here.
