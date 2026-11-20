# Current native point IDs: source-only next experiment

2026-11-20. This is a source review and proposed future qualification, not an
executed import, library append, exporter run, native-array read or identity pass.
Historical B identity, current B identity, normal fidelity and adoption remain
unqualified. The original failed normal gate and its strict `2e-5` bound remain.

## Smallest honest route

Create **new current meshes in a fresh SourceIO import** and observe their native
IDs at creation. Keep the original B files and historical observations untouched.
An exact saved/current B numeric match, or an exact `.blend` load, cannot recover
a missing native label for indistinguishable historical vertices. The new meshes
must be called a new owned derivative; they do not certify original B causality.

Source facts read from the installed approved SourceIO copy under
`output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647`
in the old acceptance checkout:

- `blender_bindings/models/mdl49/import_mdl.py::import_model` selects
  `vvd.lod_data[0]`, slices by `model.vertex_offset`/`vertex_count`, then applies
  the actual `vtx_vertices` returned by `common.merge_meshes`.
- `common.py::merge_strip_groups` reads VTX `original_mesh_vertex_index` and
  casts it to `np.uint32`. Its offset is the sum of strip vertex counts.
  `merge_meshes` returns a Python list extended with those NumPy uint32 values
  plus each MDL mesh's vertex start. Do not arbitrarily coerce unknown scalars.
- The importer calls `mesh_data.from_pydata(vertices['vertex'] * scale, [],
  np.flip(indices_array).reshape((-1, 3)))`, followed by `mesh_data.update()`.
  `FastMesh.from_pydata` allocates the vertex array and writes coordinates in
  input order using `foreach_set`; it does not store native point IDs.
- `library/models/mdl/structs/model.py::ModelV36Plus.from_buffer` divides the
  native byte offset by 48 for this MDL49 branch. Validate exact divisibility
  independently; do not infer offsets from positions.
- The existing setter observer in
  `experiments/normal_setter_boundary_sentinel_20261117/instrumentation.py`
  inserts callbacks immediately before/after the normal setter and before/after
  `mesh_data.validate()`. Its callback already receives actual `model`,
  `mesh_obj`, `mesh_data`, selected `vertices` and `vtx_vertices` references.
  Preserve its complete-function AST inverse and exact method restoration.

The first future qualification should retain those four stage observations in
RAM. At `before_setter`, bind the actual new Object/Mesh references to the
independently hash-checked native logical record. Require actual mapping type,
shape, exact integer values/order, ranges, uniqueness and cardinality before
conversion. Derive global LOD0 IDs as the independently verified model start plus
the observed mesh-relative indices, and derive raw IDs through the independently
decoded VVD fixup relation. Both complete lists must equal the independent
MDL/VVD/VTX producer's lists. No current/saved position, weight, normal, UV, name
similarity or eventual carrier value chooses an ID.

Use the exact unique native logical-model record only to select the already
hash-bound model. Refuse duplicate/repeated logical records, source IDs or raw
IDs, unexpected objects/meshes, changed ownership or unknown native profiles.

Retain exact initial position words and triangle index order, and require them
unchanged at `after_setter`, `before_validate` and `after_validate`. Validate
UVs, all three ordered positive group writes and observed current RNA weights
separately; the historical join does not prove today's storage behavior. Verify
the exact final returned container objects refer to those same observed meshes.

Only after this causal chain closes may the host add an owned FLOAT/POINT
`_HAS_NATIVE_NORMAL_ID` attribute with `LOD0 ID + 1`, check exact F32 readback,
and pass the same actual new Object/Mesh references to the gather binder. The
attribute transports an already established identity; reading it back cannot
establish that identity. Observe later validation/export changes too. A topology
or ownership change refuses; never repair correspondence by matching geometry.

## Material-preserving derivative without reopening native textures

There is a supported narrow geometry entry point: call the pinned MDL49
`import_model` directly with in-memory MDL/VVD/VTX parsers and the same
`NoMaterialIO.check(...) -> False` used by the retained setter probe. Use
`ModelOptions.default()` with explicit scale `.01905` and explicit false values
for import_textures, import_physics, import_animations,
import_include_animations, create_flex_drivers, bodygroup_vis_switches,
bodygroup_grouping, generate_wrinkle_map_node_group, load_refpose and
debug_stereo_balance. Refuse flexes, eyeballs and other unqualified source paths.

`import_textures=False` alone is not an external-material-IO guard:
`import_model` still calls `get_model_material_names` and creates placeholder
materials. The read source resolver calls `content_manager.check` for candidate
VMT paths; the closed NoMaterialIO object must satisfy only that admitted path
and refuse unexpected methods. Do not call the production bridge's later
VMT/VTF reconstruction: it clears material trees, resolves files, decodes pixels
and builds new packed images rather than preserving B's resources.

Before material-library append, retain an explicit source-native material index
to new-placeholder-reference to actual per-face slot relation. Independently
validate the native material descriptors/indices and the complete slot mapping;
the existing point-only producer does not itself qualify material identity.
`bpy_utils.add_material` deduplicates by material name AND full_path, whereas
`get_or_create_material` reuses by case-folded full_path. Distinct source indices
can therefore alias one slot. Refuse ambiguous aliases; never assume native
material index equals Blender slot or final glTF material index.

Remove/detach only the newly created placeholder materials after retaining this
relation, so their names cannot rename subsequently appended B materials. In a
separately admitted operation, load **only the exact required materials and
their packed-image dependencies** from an owned byte-identical B library using
the actual pinned `bpy.data.libraries.load(..., link=False)` API. Do not append
the old meshes, objects, armature or scenes. This avoids old object/mesh name
collisions and preserves the new importer-observed point references.

Bind returned Material objects by the explicit authenticated B-library request
relation and native slot relation, not a post-append global name lookup. Check
the exact returned names, ownership, library status, full_path equivalence
classes, node/socket graph, Image references, packed bytes and metadata. Reject
renaming/collisions, unknown dependencies or unresolved material relations.
Library append itself can load dependencies before exporter guards: it needs its
own source/runtime/closure review and bounded actual qualification. Do not assume
that link=False or packed image status proves no other file access.

Assign only these actual appended Material references to the new meshes' slots
using the independently checked relation. Preserve complete face material-index
order. Keep B resource names/raw path classes/packed data unchanged. Do not
rebuild shaders, unpack/re-encode source images or use the production bridge's
fallback gray conversion. Leave unrelated editor/Viewer data alone.

This is a deliberately new resource attachment operation, not proof of original
B's import branch/options. If the source-derived slot relation cannot uniquely
identify a required B material, retain a refusal instead of trying names or
attribute matching. Preserve source rigs/rests/transforms and compare them too;
fresh import is not permission to substitute an approximate armature.

## Separate gates before any correction

1. Fresh admitted cold Windows host; exact runtime/SourceIO/helper/catalogue
   pins, raw family hashes/size/stamps, private placement and owned output/TEMP.
   No new execution is authorized by this note itself.
2. Actual new mesh creation/stage/container ID observations and independent
   native checks above, including current weight observations; restore every
   scoped hook exactly and retain a failed attempt if any check differs.
3. Independently admitted material-library append and complete actual reachable
   material/socket/Image relation, with known before-first-read guards.
4. Actual one-export gather/cache/reference binding for those same new meshes.
   No warm-cache success, missing callbacks, no-new-split relaxation or silent
   retry. The separate hook prototype remains unqualified until Root tests it.
5. Strict input-domain checks and unchanged non-NORMAL semantic comparison of
   original B GLB against the new carrier derivative: decoded attributes,
   topology/order, UVs/colors, joints/weights/inverse binds, transforms/skins,
   hierarchy/metadata, material bindings and encoded images. A mismatch fails;
   do not reorder data, drop channels or rewrite materials to manufacture a pass.
6. Only then attempt the existing append-only NORMAL correction, retaining the
   exact signed-axis transport, original `2e-5` gate, independent preservation
   contracts and original failed baselines. No HAS adoption follows from a
   source review, synthetic tests, historical numeric match or carrier marker.

An exact B serialization proof would establish current/saved Blender index
continuity only. No original conversion-time native-ID field or authenticated
complete original option/creation trace was found in this source review. It
therefore remains an unavailable alternative for native historical causality.
