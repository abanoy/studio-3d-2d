# Draft HAS model-variant schema

This is an immutable manifest plus a small editable selection. It is not a source file reader or a proof of native correspondence. The future converter must bind these indices to actual exported resources, and the engine must bind them to actual scene-owned resources.

## Inventory: studio_variant_asset_inventory_1

Exact top-level fields: format, asset_sha256 (64 lowercase hex), material_count (1..256), mesh_nodes (1..4096). Each mesh row has exact fields node (glTF node index0..99999), parent_mesh (nearest mesh ancestor index or null), surface_materials (1..256 actual default material indices in primitive order). All mesh IDs are unique; parents must exist and form an acyclic graph. Total surfaces <=16384. This inventory comes from the actual authenticated asset, not user-authored guesses.

## Manifest: studio_model_variants_1

Exact fields:

| Field | Contract |
| --- | --- |
| format | studio_model_variants_1 |
| asset_sha256 | Must equal inventory.asset_sha256 and the loaded final GLB |
| default_skin | Numeric valid skin ID |
| skins |1..64 rows {id, name}; contiguous ID order, exact bounded display label |
| groups |0..32 rows {id, name, default, choices}; contiguous numeric IDs |
| choices |1..64 per group, <=512 total; {id, name, blank, nodes} |
| blank | True iff nodes is empty; never inferred from a name |
| nodes | Exact exported mesh-node IDs; unique across all choices/groups |
| surfaces | Exactly one row per inventory mesh surface: {node, surface, materials} |
| materials | Exactly one exported material ID per skin; default_skin entry equals actual inventory default |

Controlled mesh nodes cannot be ancestors of any other mesh, because a visibility write must affect only the selected node. Other mesh nodes can remain outside groups and keep their visibility. All surfaces still have explicit skin assignments, preventing partial material swaps. Shared mesh resources are possible; future runtime assignment is per-instance override only. Repeated skin material rows are permitted and retain their distinct numeric IDs.

All indices are exact integers (booleans/floats are refused). Names preserve whitespace, Unicode and case; ASCII control characters and invalid surrogates refuse. Every returned container is detached. Unknown fields/formats refuse. Encoded canonical manifest <=256KiB; this fits within, but does not replace, the project-wide metadata budget.

## Selection: studio_variant_selection_1

Exact fields: format, skin, groups. groups uses every canonical decimal group ID ("0", "1", …), mapped to one valid choice ID. Defaults are explicit. A skin-only model has groups={}. Runtime all-blank choices are permitted because no source geometry is discarded; this does not change the older static-converter refusal of an all-blank export.

Example synthetic glove selection:

~~~json
{"format":"studio_variant_selection_1","skin":2,"groups":{"0":1}}
~~~

This means skin row2 and bodygroup0 choice1. It does not imply that any supplied model uses these native-to-export indices.

## Plan

plan_selection returns studio_variant_apply_plan_1, asset_sha256, detached selection, sorted visibility rows {node, visible}, and complete sorted material rows {node, surface, material}. plan_change returns studio_variant_transition_plan_1 with detached before and after plans and a changed boolean. A valid skin plus invalid part produces no plan and changes no caller input.

The engine adapter must validate actual live bindings and cache ownership before writing, and roll back its owned changes if a write fails. Pure planning alone does not establish engine atomicity. The first UI selection is saved whole-model state, not an interpolated animation channel. Old documents without the new capability keep their existing paths; new variant documents need a new admitted model format so old readers cannot silently display all retained alternatives.
