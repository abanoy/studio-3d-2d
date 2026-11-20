# Export/resource proposal RNA identity review

2026-11-20. Read-only source review; only this note was written. No application,
published proposal, test or runtime source was edited. No tests, Blender,
converters, native assets, Git commands or process probes were run. The actual
material-binding success does not qualify the future exporter/resource hook.

## Finding and source pins

The old resource proposal can falsely refuse an unchanged real graph/packed
image because Python wrapper identity is not universal RNA data identity.
Blender creates/reuses wrappers through `pyrna_struct_CreatePyObject`: reuse
requires an existing instance returned by `RNA_struct_instance`; without one it
allocates another wrapper. ID registers an instance callback for `ID.py_instance`.
NodeSocket, NodeLink and PackedFile lack that cache contract. Keep exact cached
ID identity and exporter Python-object identity; change only admitted non-ID
RNA comparisons in a versioned successor. Do not replace `is` globally by `==`.

Reviewed local source identities:

| Source | Bytes | SHA256 |
| --- | ---: | --- |
| experiments/source_export_hook_20261120/resource_gate_proposal.py | 25032 | 336119221fc6c96d78b69cf301e2d89b0130c48febaedb81fc1c0b0134211e14 |
| experiments/source_export_hook_20261120/export_hook_proposal.py | 33179 | 1b6e6b5fa4acb1e3bea1d37fd433f42c1294ed70a24047c4ea0e4c60b18afbae |
| experiments/native_carrier_gather_binding_20261118/gather_binding.py | 17534 | 617c062b516ecefa5fab0a6ec8f98163a3b13f76896969cb22102f859323b850 |
| experiments/native_normal_carrier_probe_20261117/observer_instrumentation.py | 7829 | 15145030fab5b662be490e519ff59f870c4e9c0352766ff59bf3da3f12198f7b |

Primary Blender reference: commit
`ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832` on the5.1 release branch. Blob pins
below were independently read through the GitHub connector by body_oracles;
the wrapper allocation/reuse implementation was also inspected in this review.
These reference sources do not attest the installed executable's build commit.

| Primary source / function | Git content blob |
| --- | --- |
| [bpy_rna.cc: pyrna_struct_CreatePyObject / allocation](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/python/intern/bpy_rna.cc) | ade15a1e1d0066226f3793320b65843f99963663 |
| [rna_access.cc: RNA_struct_instance](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/makesrna/intern/rna_access.cc) | 4a4c15888967232675eb350cc43766ab3b73ac7a |
| [rna_ID.cc: rna_ID_instance / registration](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/makesrna/intern/rna_ID.cc) | f1985d5d234c277043d4ce60bb965f1c6771a2bd |
| [rna_node_socket.cc: registration and socket.node owner](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/makesrna/intern/rna_node_socket.cc) | b6c050c373dfff1c6aa48c5d5214e76cb34fa7dc |
| [rna_nodetree.cc: NodeLink](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/makesrna/intern/rna_nodetree.cc) | 5bcaf64e0775497b1f1a9b0490cf6dbf046e2337 |
| [rna_packedfile.cc: PackedFile](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/makesrna/intern/rna_packedfile.cc) | a6e3e307c047fcb3f961182a38b8cdf33efd1515 |
| [rna_image.cc: packed getter / ImagePackedFile](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/makesrna/intern/rna_image.cc) | 5a7b8777521bfeb7b3e2b31942cf3b2b6bb84cff |

The packed getter inherits the actual Image owner when creating its PackedFile
RNA pointer. Socket.node similarly creates a node pointer owned by the actual
NodeTree ID. Those explicit owner relationships enable strict C identity; names
and filenames are not substitutes. Nodes should use the same non-ID policy even
when a particular node implementation happens to cache its Python wrapper.

## Exact old call sites

All line numbers below refer to the immutable local sources above.

| resource_gate_proposal.py location | Non-ID comparison to change in a successor |
| --- | --- |
| _unique_refs line21; _graph119, socket uniqueness241 | Python id() over node/link/socket wrappers does not prove unique C structs. Split this helper by domain; keep ID-image/material uses unchanged. |
| _graph141–152 | Alpha detection and complete edge matching compare socket/node getters with is. Compare exact admitted endpoint C keys, node ownership and directed edges instead. |
| _packed_png168–182 | image.packed_file is parts[0].packed_file can be false for equal underlying PackedFile pointers. Keep the original Image ID identity, compare typed packed C keys owned by that same Image, and retain both wrappers. |
| check_unchanged209–225 | Node/link lists, endpoint tuples, node/default socket refs and packed part/file snapshot refs can be freshly wrapped. Use typed ordered C-key snapshots plus unchanged complete metadata/bytes. Material/tree/Image IDs, Python classes and booleans retain their existing identity rules. |
| _same_key26; _socket_key232–245; material333–334 | Exporter's search.NodeSocket is a plain Python wrapper, but its .socket is RNA. Keep the exact exporter wrapper class and root group_path list/NodeTree ID checks; join only the underlying socket via its admitted owner/type/pointer key. The tuple's Image ID stays is and channel kind stays exact value. |

`export_hook_proposal.py` forwards these socket tuples to the resource gate; it
does not itself need a blanket identity rewrite. Its `same_refs` at53 is used
for legitimate Python collectors/material ID tuples as well as imported by the
old resource graph. Introduce a separate typed RNA helper at the affected graph
sites rather than weakening that generic function.

Keep the following checks unchanged:

- Material/Image/Object/Mesh/NodeTree ID refs, .original, slots and actual
  datablock ownership, including _entry376 and creator object/mesh430–431;
- exporter module/class/function objects, exact installed wrapper ownership,
  code/globals/closure/source pins and finally restoration;
- ExportImage/Fill descriptor objects, emitted glTF Image/Texture/TextureInfo/
  Material/Mesh objects, cache dictionaries/lists, PrimitiveCreator and its
  captured NumPy arrays;
- groups/modifiers/materials is checks at415–416 and456: these identify the
  same actual forwarded call arguments, not a new lookup of RNA properties;
- supporting GatherBinding's ID material slots and Python creator/cache/glTF
  list/object identities, and observer_instrumentation's AST anchors, original
  functions/classes and exact restoration.

No direct non-ID RNA re-get identity site was found in those supporting two
modules. Their provenance, point-identity and exporter API obligations remain.

## Proposed strict canonical policy

For each non-ID wrapper require a genuine admitted bpy class, an exact allowed
concrete type, a valid original local owner ID and an exact integer
`0 < as_pointer() < 2**64` (bool refused). A private key consists of the owner
ID compared with `is`, concrete RNA type and numeric C pointer. Retain the
original wrapper and owner refs throughout this one controlled operation;
never publish these addresses or use them as native geometry IDs.

Add relationship constraints to that base key: node/link membership must occur
exactly once in its admitted tree collection; each socket must belong to the
admitted node and correct input/output collection, with the same bounded
identifier/order/default metadata; link endpoint keys must match the complete
directed graph. PackedFile and ImagePackedFile keys must belong to the same
admitted Image, preserve the single-part relation and all filepath/view/tile
metadata, and retain identical admitted size/hash/bytes. A different owner,
type, pointer, relation or payload refuses, even if names/appearance match.

A C pointer alone is insufficient: it has no generation counter. Keep the
readonly/frozen graph lifecycle, no mutation/handlers/rebuilds, collection and
metadata rechecks, strong owning refs and existing refusal behavior. This
policy does not prove historical causality across deletion/reallocation.
Unexpected invalidation/mutation must refuse; never recover by names or index
zipping and never accept Python structural equality as a replacement.

Before any real export, add meaningful synthetic proxies whose getters return
fresh wrappers over the same owner/type/C pointer (positive), plus equal
pointer with wrong owner/type, changed endpoints, missing/duplicate membership,
changed packed aliases/size/hash and invalid/bool pointer negatives. Keep fake
ID and glTF lookalike replacements failing their existing is checks. Then Root
must qualify the installed API in a fresh owned private job; CPU-only success
cannot certify actual wrapper behavior.

All existing namespace/class/runtime/source admission, sole-collector callback
inventory, failure latch, full AST inverse, exact function restoration,
encoded/decoded resource budgets, MIME/channel/WebP/unused-image restrictions,
point-ID admission, unchanged non-NORMAL comparison and strict2e-5 normal gate
remain in force. This note qualifies no current B resource, exporter behavior,
generic model support, normal fidelity or HAS application adoption.
