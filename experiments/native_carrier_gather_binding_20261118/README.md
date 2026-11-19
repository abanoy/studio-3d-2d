# Observation-to-final-primitive binding: CPU candidate

This packet implements the next narrow identity bridge without running Blender,
an exporter or a native asset. It changes none of the five frozen parent packets.
The original raw-normal failure remains FAILED_UNQUALIFIED. There are no hooks,
launcher, path readers, writers, native probes or adoption operations in the
production module. Synthetic GLB bytes exist in RAM only.

`GatherBinding` retains actual object references and uses `is`. Names and numeric
Python `id` values never establish a cross-stage relation. Host admissions contain
the exact Blender object/mesh references, the independent exact-point-join source
IDs, the actual source material-slot tuple and an expected primitive count.
The adapter does not qualify where those admissions or events came from.

The future host must supply these events from separately reviewed, pinned hooks:

1. `observe_creator(creator, branch, blender_indices, material_slot,
   topology_indices, ordinal)` consumes the sealed extractor observation. Its
   creator must hold the admitted `blender_object` and `blender_mesh` references.
   Only the cold, nonshared triangle path is admitted. NumPy inputs are deliberately
   refused in this observation call: the host must first check exact unsigned dtype, dimensionality
   and bounds, then use `.tolist()` / `.item()`. Arbitrary `int()` coercion is unsafe.
2. `bind_gather(creator, materials, cached_internal_primitives,
   gathered_primitives, gltf_mesh)` binds the actual cache-return row objects,
   returned primitive list and owning Mesh object. It checks source slot order and
   the same attribute dictionaries / index-accessor references used by gathering.
   Cold-cache hits, aliases, missing observations, repeated gathers, evaluated mesh
   substitutions and primitive reuse refuse. Mesh and primitive names do no work.
   Cached source material fields themselves remain untouched: exact NumPy uint32
   scalars are admitted through checked scalar metadata and the lossless integer
   protocol. Float, Boolean, signed/wider integer and array values refuse. Actual
   runtime-type provenance still belongs to the future pinned host.
3. `record_material_reference(material, index)` and
   `record_mesh_reference(mesh, index)` consume actual exporter reference-assignment
   events. A source material slot is not a final GLB material index. The latter is
   bound through the actual gathered glTF Material object. Repeated references to
   the same Material at the same index are allowed; reused Mesh references are not.
   Final primitive object ordering, attribute dictionary identity and assigned
   material indices are checked before detached serialized references are retained.
4. `finalize(raw_glb, expected_sha256)` requires a host-pinned immutable GLB, strict
   lexical JSON / exact two-chunk parsing, exact final mesh/primitive references,
   POSITION row counts and decoded unsigned topology in order. It returns
   `{(mesh_index, primitive_index): tuple(one_based_source_ids)}`, the unchanged
   correction consumer's required schema, plus a scalar/hash/count summary.

The final GLB mesh order may differ from creation order. Explicit reference events
select its indices; no traversal zip or name join is used. The topology decoder
uses the frozen semantic comparator's checked accessor decoder, including offsets
and strides. Carrier attribute *references* are bound, but carrier payload values
are never read or used to select identities. A deliberate carrier-value permutation
therefore preserves this CPU identity result and still qualifies no native binding.

Bounds: at most two admitted objects, four total primitives, 200,000 aggregate
source points, 1,000,000 cumulative observed corners, 64 source material slots per
object, 65,536 entries per resource table and 128 MiB GLB bytes. This closes the
existing no-new-split B profile: global source coverage must be exact and unique.
Morph/extension/extra primitive payloads, non-triangle modes and repeated Mesh
reference events refuse. Serialized graph ownership/instancing validity remains a
separate input-domain gate.
These CPU limits do not bound a future exporter/native process.

This is a binding contract, not full GLB validity, semantic preservation or normal
fidelity. It does not decode the carrier payload or validate POSITION contents,
skin domains, graphs, resource ownership or actual native correspondence. The
separate frozen input-domain and original-versus-carrier semantic gates must pass;
the exact native NORMAL-word gate and preservation contract still follow any
future correction. Rest/bone/source/unit identities, the five-joint workflow,
HAS/cold-open behavior and adoption remain separate. The source-unit and inactive
six-foot/scale-1 contracts are unchanged.

`actual_hooks_observed`, `actual_native_GLTF_binding_qualified`, input-domain,
normal-fidelity and adoption flags always remain false. The actual wrappers,
runtime-source/inverse/restoration proofs, frozen export-option provenance,
resource/placement/context gates and Root-owned native execution remain pending.

Source trace and exact pins are in SOURCE_DERIVATION.json. In particular,
`primitives.py` has two different cache keys: the extraction key omits materials
and the skin UUID; the outer primitive key includes material identities but omits
the skin UUID/groups. A warm/aliased cache must not manufacture observer evidence.
The exporter assigns final indices while traversing and mutating the gathered
object graph. The binder observes those results rather than predicting them.

Run from the repository root:
`python -B -X utf8 -m unittest discover -s experiments/native_carrier_gather_binding_20261118 -p test_gather_binding.py -v`.
Sixteen synthetic methods cover identity/order/cache/material/topology/type and
budget failures. The successful case intentionally uses duplicate object/mesh
names, reversed final mesh order and material indices unlike source slots.
CPU_VALIDATION.json records the actual run and review limits. The two cached-slot
regressions use the already installed NumPy with synthetic scalars/arrays; they
import no Blender or exporter module. All arrays,
objects and generated GLB bytes used by tests are synthetic; no native/private
data was read. This packet belongs to a separate next checkpoint.
