# Smallest actual native-normal carrier hook experiment

Status: **SOURCE REVIEW / ACTUAL EXPORT UNRUN**, 2026-11-20.

This note records a read-only source review and a proposed experiment. The review
read project Python and installed exporter source. It did not import Blender or
SourceIO, read native geometry/resource arrays, execute an exporter, run an
engine, query processes, use Git, or change functional source. Only this new note
was written. Existing normal-fidelity failures, binder qualification flags and
original assets remain unchanged.

Root separately reported that its RAM join at `17aba` matched the historical
ordered weights and point data for 9,661 points / 42,702 corners / 69 groups with
zero errors and all 14 pins unchanged. That is Root-reported evidence, not a run
by this reviewer. The stricter successor index was pending when this note was
requested. Bind the eventual exact join policy/index and result before using its
private point relation. This note does not upgrade that evidence to exporter,
native NORMAL, model fidelity or HAS adoption qualification.

## Recommendation

After the current full Body Physics verification and its physical closure finish,
implement an **experiment-only, one-cold-export host** around the existing frozen
CPU helpers. Keep production `tools/blender_source_bridge.py` and the original
packets unchanged. The first output is a separately named private `carrier.glb`,
not a replacement source or an adopted HAS model. A later correction is a second
separately named private derivative.

The missing identity connection is small and concrete: existing extractor
observation -> actual cached internal rows -> actual gather return list ->
owning glTF Mesh -> actual exporter reference assignment -> serialized GLB.
There are existing extension hooks for Mesh/material/texture/image observations;
the extractor, gather-return and reference-assignment observations require scoped
runtime instrumentation. No installed file needs patching.

## Source locations and recorded pins

Project-relative paths below are under
`C:/a/Programming/cloudflare/has-body-addition-20261120/`.

- `experiments/native_carrier_gather_binding_20261118/gather_binding.py`:
  `GatherBinding`, the existing CPU contract. Packet-recorded SHA256
  `617c062b516ecefa5fab0a6ec8f98163a3b13f76896969cb22102f859323b850`.
- Its `README.md`, `SOURCE_DERIVATION.json` and `test_gather_binding.py` describe
  exact event identity, cache hazards, budgets and synthetic negative controls.
- `experiments/native_normal_carrier_probe_20261117/observer_instrumentation.py`:
  `install_pinned_observer`, complete-class AST insertion/inverse, original
  runtime bytecode comparison and exact method-object restoration. Recorded
  SHA256 `15145030fab5b662be490e519ff59f870c4e9c0352766ff59bf3da3f12198f7b`.
- `experiments/native_normal_carrier_probe_20261117/exact_point_join.py`:
  `join_saved_point_ids`, the saved/current/setter/independent-expectation join.
- `experiments/native_point_expectation_20261118/native_point_expectation.py`:
  `derive_native_point_rows`, `_vtx`, `_vvd`, weight-write replay and the original
  narrow full expectation. Its `build_native_point_expectation` still refuses
  multiple distinct positive groups; do not bypass that restriction using a
  success marker. Use the explicitly pinned successor ordered-storage policy
  qualified by Root instead.
- `experiments/native_normal_carrier_strategy_20261117/normal_identity_carrier.py`:
  existing append-only word transport/correction and independent contracts;
  recorded SHA256 `37be746c21274e9844a532698078423a0b4f156dcb546135d18b0217daf0fb08`.
- `experiments/carrier_input_domain_20261118/input_domain.py` and
  `semantic_compare.py`: strict raw GLB JSON/domain bridge and comparator.
  The frozen comparator dependency is recorded as
  `c7e1e9d323bb7f35fffa38731a67b0099f173167bcb65d857a7cd6165698ff00`.
- `tools/source_bone_export.py::ExportObservation`, `ObservedCollector`, and
  `tools/source_jiggle_crosswalk.py::temporary_export_extension` provide the
  existing production source-pin/registration/latched-failure/restoration pattern.
- `tools/blender_source_bridge.py`: visible renderable selection, ordinary export
  call versus optional crosswalk wrapper, post-export lightmap tagging and report
  publication. Those branches are source observations, not historical B option
  provenance.
- `experiments/native_B_resource_ownership_runtime_20261118/survey_core.py` and
  `ownership_metadata.py`, and
  `experiments/native_B_resource_classification_rules_20261118/classification.py`:
  resource/node-image/ID-owner metadata and explicit unresolved scopes.
- `experiments/native_normal_resource_survey_20261117/export_provenance.py`:
  original hash-only B references do **not** identify its original export branch.

Installed exporter root, read as source only:

`C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/`

The gather packet records these relevant source pins (not a fresh complete
runtime revalidation by this note):

| Relative exporter source | Recorded SHA256 |
| --- | --- |
| `blender/exp/primitive_extract.py` | `455a3566d833481b230141b457452b5bf4ff4a1661d4dd6765a568488e0a2769` |
| `blender/exp/primitives.py` | `7d7f2c6d9c5e64974f05ee40967d4415a00ee9b4ed91447889cee44d185c68a4` |
| `blender/exp/obj_data.py` | `1d0e3942a5c65dacbba2b51fb89688026a36c3fc81f89da683c9e2eb393203a8` |
| `blender/exp/nodes.py` | `6c77f1ec3f13bd4636ca72f766429abc9cd4353ff218fdb088db1e41f184b7c3` |
| `blender/exp/exporter.py` | `49c1e0174a65efd6d411b906cd154b6b04502c4840c9b31a7bfac87e0888f242` |
| `blender/exp/cache.py` | `12fc08e6403c9dd604f6884fdfdcf787ed5a898a2c6f4e2990f1826d6e265d98` |
| `blender/exp/export.py` | `d6ae39bf861fc3db7662bc8e7063aadfbe116b8a5de81b40ba027a679f8435a8` |
| `io/com/gltf2_io.py` | `d0bad0c89e40c0975ed9e435656151e353240134011f69602e473e0a5f1592f4` |

Also review and pin the actual loaded material modules used by the host:
`blender/exp/material/{materials,texture_info,texture,image,encode_image,search_node_tree}.py`
and `io/exp/user_extensions.py`. Complete current runtime/SourceIO/exporter
catalogues remain a separate host admission; the eight rows above are not a claim
that all 120 exporter identities were freshly checked.

## Exact point IDs, including coincident points

Native IDs originate from independently decoded MDL model/mesh starts, VTX
`original_mesh_vertex_index` order and the VVD LOD0 fixup/raw-row relation. Preserve
the importer rule that reverses the complete flattened corner stream before
reshaping triangles. Preserve exact F32 `.01905` position conversion, UV V-flip,
native bone group order and the independently qualified ordered REPLACE storage
rule. None of those facts comes from current normal readback or exported carrier
values.

Join the saved original B point order, the successful setter's observed point IDs
and initial loops, the current owned B copy, and the independently derived native
expectation using the exact typed join. Bind the two admitted current Blender
object/mesh references to those complete joins before installing hooks. Logical
names can identify an already hash-bound native model record, but names or
traversal order cannot manufacture a point correspondence.

Coincident positions or equal UV/weight/normal rows remain distinct source IDs.
Never collapse them, sort by geometry, choose a nearest normal/position, or resolve
ties by cache/creation arrival order. The pinned native index order and complete
historical/setter relation supply the identity. Refuse an unresolved relation or
repeated native IDs rather than infer one. Lossy Blender custom-normal readback
and final NORMAL values are never identity keys. The old signed-word ambiguity
must remain addressed by the independent source IDs.

## Minimal reversible hook connection

Use a fresh cold Blender process, one export, the exact admitted two object/mesh
references, their actual ordered material-slot tuples and expected primitive
counts. The existing binder limits remain: two objects, four primitives, 200,000
aggregate points, 1,000,000 observed corners, 64 slots/object, 65,536 table entries
and 128 MiB GLB. Do not expand its no-new-split profile to make a probe pass.

1. Install the existing `install_pinned_observer` for `PrimitiveCreator`. Its
   callback observes the exact `blender_idxs` assignment in the nonshared branch,
   together with material slot, topology and ordinal. Verify actual NumPy unsigned
   dtype/itemsize, shape, scalar type and ranges **before** `.tolist()` / `.item()`;
   arbitrary `int()` coercion is not admission. Supply those observations to
   `GatherBinding.observe_creator`.
2. Scope two return observations around the actual loaded module attributes
   `primitives.__gather_cache_primitives` and `primitives.gather_primitives`. Call
   each captured original exactly once. Retain the real returned cached row list
   and gathered primitive list; do not rebuild equivalent dictionaries/lists.
   Tie the call chain to the same admitted creator/mesh and exact materials tuple.
   The extraction cache key omits materials/skin UUID/groups, and the outer cache
   omits skin UUID/groups. A cache hit without the required cold creator event
   refuses. Do not clear warm caches or invent observations for a hit.
3. Use the existing `obj_data.py` `gather_mesh_hook(mesh, blender_data,
   blender_object, vertex_groups, modifiers, materials, export_settings)` to bind
   the actual owning Mesh and its primitive list with
   `GatherBinding.bind_gather`. Require exact object/mesh references: evaluated
   mesh substitution, shared mesh data, extra extraction passes, aliasing or
   repeated gathered Mesh objects refuse.
4. Scope a wrapper around
   `GlTF2Exporter._GlTF2Exporter__to_reference`. Call the original first, then
   observe its actual integer result for the retained Material/Mesh object.
   Record `record_material_reference` / `record_mesh_reference` at that point.
   Exporter traversal has already changed nested accessor/material fields to
   indices when Mesh is assigned, which is the binder's required boundary.
   Source slots are not final material indices; gather/creation order is not
   final mesh order. Reused Mesh reference events or distinct Material objects
   aliasing one final index refuse under this profile.
5. After export and all declared owned postprocessing, hash immutable output bytes
   and call `GatherBinding.finalize`. It must reconcile exact serialized
   primitive references/materials/order, POSITION counts and decoded unsigned
   topology. Only then is the private `(mesh_index, primitive_index) -> source IDs`
   relation ready for the separate carrier/correction checks. Reading carrier
   values back into the expected relation is forbidden.

Capture exact original function objects and registration state before installing
anything. Verify loaded module paths/source pins and original runtime code, use
strictly scoped `try/finally`, and restore the exact objects, not newly compiled
lookalikes. The existing extractor observer separately proves its full-class AST
inverse and restores exact original method objects. Verify restoration even after
an export exception. Check ownership of every replacement before restoration;
unexpected concurrent replacement is a failure. No installed source, preferences
or blend save is permitted. No second export retry or ordinary-export fallback
may turn a missing observation into success.

`io/exp/user_extensions.py` catches extension exceptions. The host collector must
latch failures and refuse outside the operator after return; a logged hook error
cannot be ignored because a GLB was written. Direct wrappers must preserve real
operator exceptions. Use one owned extension object. Current production bone
collector preflight requires exactly itself as the sole extension: do not register
an additional independent extension beside it. An isolated B-copy experiment can
use one carrier collector with the existing temporary-registration pattern; any
later production composition needs an explicitly reviewed combined collector.

## Material/socket/image reachability traps

The current survey records image nodes inside material/group trees, raw path
classes and ID-user reachability. It does **not** record socket links, active
material-output reachability or the exact image/channel path selected by the
exporter. ID users, a material name, an image's presence in `bpy.data.images`, or
an IMAGE_EDITOR witness are not proof of export use or global unreachability.
Classification deliberately leaves export dependency relevance unresolved.

For the smallest B-only host, preflight the actual selected face/material-slot
set and a bounded simple supported shader graph before export. Trace actual
socket/link/group context to the active material output, refusing cycles,
unsupported groups, muted/ambiguous output paths, UDIM and unqualified external
nodes rather than inventing broader traversal semantics. The pinned exporter
`search_node_tree.py` has active-output/group traversal, including documented
outputs[0] limitations; do not relabel it as a complete Blender shader evaluator.

Add read-only existing extension observations:

- `gather_material_hook`: Blender Material -> gathered base glTF Material.
- `gather_texture_info_hook`: actual socket tuple -> glTF texture-info object.
- `gather_texture_hook`: actual socket tuple -> Texture with actual Image ref.
- `gather_image_hook`: actual socket tuple and `ExportImage.fills` / `original`
  -> glTF Image. Retain exact source Image refs and channel mapping, including
  alpha/channel composition, not just a filename or the first texture node.

**Deepcopy trap:** `materials.py::get_final_material` may deep-copy the base
Material for nonzero texCoord assignments after `gather_material_hook`.
`get_new_material_texture_shared` then reconnects Texture refs. Do not assume the
hook Material is `primitive.material` by name/equal values. The smallest one-UV0
B profile can require observed identity equality and refuse a copy. Broader
support needs an additional scoped observation of the actual
`get_final_material` return, with the source Material/base Material/caching inputs
bound explicitly. Final Material/Texture/Image indices must come from actual
reference assignment, not slot indices.

Preflight resource ownership before image encoding occurs: late image hooks are
observations, not permission to read an undiscovered resource. Resolve `//`
against the **original B directory**, not the disposable copy. Copy exact approved
encoded dependencies only into owned storage; preserve original basenames and raw
filepath equivalence classes. `image.py::__gather_name` uses filepath equality and
basenames, so hash-naming every copy can change semantic image names. Distinct raw
path classes must stay distinct. Packed images with empty paths retain their
empty paths and packed bytes. Preserve packed hashes, names, alpha/color-space
metadata and FILE image status; do not unpack/save/recreate the originals.

An internal viewer must not be discarded merely because the existing survey
labels an editor witness. Establish the narrowed export non-reachability policy
from the selected material/socket graph, controlled background/no-render context
and actual exporter image events. Preserve unresolved scopes in reporting. Keep
TEMP/TMP and all potential encoding destinations owned. Read no pixels for
identity; where the ordinary exporter must encode an approved image, treat that
as a separately bounded actual export operation and check encoded output bytes.

## Proposed first actual recipe and separate gates

1. Admit the exact completed successor full-source context and fresh exclusive
   physical closure, complete source/runtime/native/reference pins and exact
   ordered-storage join successor. Retain before/after original file
   hash/size/nanosecond-time identities. Use the approved hidden desktop launcher,
   retained Popen wait/reap, logs, placement sentinel and job/desktop closure;
   never use a visible fallback.
2. Open only a verified disposable copy of material-preserving original B
   `editable.blend`, with scripts/UI loading disabled and the approved offline
   background context. Do not substitute the material-free setter replay.
   Reproduce the bridge's visible renderable selection and retain the exact
   original meshes/armature/materials. Refuse unsupported modifiers, shapes,
   instance ambiguity or changes from the exact point join.
3. Prepare approved resource copies/remaps only in memory. Snapshot selection,
   frame, object/mesh IDs, matrices/rest/skin/weights/UVs, materials/node links,
   image metadata/packed hashes and attribute inventories. Refuse a case-folded
   collision with `_HAS_NATIVE_NORMAL_ID`. Add only a `FLOAT` / `POINT` attribute
   containing independently joined native LOD0 ID + 1, and verify exact F32
   readback. No normal setter, geometry/weight edit, source-unit change or
   six-foot normalization is involved.
4. Perform one separately named export using an explicitly frozen new option
   profile, `export_attributes=True`, `export_shared_accessors=False` and explicit
   no compression/quantization, plus the declared GLB/selection/material/skin/
   hierarchy/morph/light settings. Observe actual export settings in preflight.
   Historical B branch/options remain UNKNOWN unless actual invocation evidence
   is found. A passing strict B-to-carrier semantic comparison can establish
   equivalence of this new profile for this asset; it does not reconstruct
   historical option provenance. Restore hooks, registration, owned attributes
   and remaps in finally; verify all original identities and unchanged scene
   channels. The exporter itself calls mesh validation: any resulting source
   state/topology change must be detected, not excused.
5. Qualify both exact raw inputs with the strict GLB/domain bridge. Run unchanged
   `compare_qualified_non_normal` against retained B and carrier. Require exact
   decoded non-NORMAL component bytes/order/types, positions/topology, UV/color,
   joints/weights/inverse binds, supported position morphs, materials and encoded
   images, nodes/skins/rest/animation and unrelated metadata. Require the actual
   binder relation and the unchanged two-mesh/four-primitive/no-new-split coverage.
   A mismatch is a retained failed experiment, not a reason to loosen tolerances
   or reorder/split rows into agreement.
6. Only after those gates, run the existing append-only CPU correction into a
   new derivative. Supply exact native/carrier hashes and independent primitive
   relation, and verify actual proper signed-axis transport once. Retain all old
   BIN bytes, remove only the owned carrier reference, append corrected NORMAL
   storage and check both independent preservation and exact output-word/storage
   contracts plus the original unchanged native-normal threshold. Keep original
   failed B and reports intact.
7. Derivative adoption remains later work: new-checksum native bone/source/rest/
   skin bindings, the 69 links/five-joint workflow, pose/key migration where
   relevant, Hair & clothes Off/reset, fan/body/Record, packed/linked cold HAS and
   ordinary preview/movie checks. No native solver, broader Source fidelity or
   artist/device acceptance follows from a normal accessor result.

Public evidence may contain source, pins, counts, bounds, hashes, scalar errors,
explicit refusal statuses and sanitized closure receipts only. Keep source IDs,
correspondence arrays, native streams, positions/normals/UV/weights, resource paths,
textures, blend/GLB/HAS files and images private. This note supplies no new actual
export evidence or authority to overlap the still-running full verification.
