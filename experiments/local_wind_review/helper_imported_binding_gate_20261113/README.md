# Actual imported binding gate: bounded headless result

This output-only gate now validates complete source-node binding snapshots from actual Godot4.6 imports, before a future hidden main-view wind preview. It uses unchanged `4fa5efc175c0da53fcd61087e9685c89f4614db3` source, existing pure-Python helper builders, exact owned input copies and no converters. Main source, archived prototypes, originals and installed runtimes were not modified.

**22 synthetic CPU controls pass.** Two synthetic source/candidate pairs then pass actual headless imports with source-default morph weight0.25 and independently reviewed override0.5. The final retained run has these results:

| Checksum-bound retained bundle | Complete original source nodes | Actual imported kinds | Retained declarations | Derived-helper result |
|---|---:|---|---|---|
| VRM0 |100/100|91 bones,9 nodes|12 chains,22 colliders|No bounded usable new-helper proposal among the first64 assessed regions; no derived transfer claimed|
| VRM1 |110/110|91 bones,12 offsets,7 nodes|12 chains,22 colliders|Same explicit no-proposal limit; actual offset bindings were checked|
| `backhair` alias, staged ribbon GLB |103/103|81 bones,22 nodes|1 chain,0 colliders|Existing-joint builder adds endpoint source node103; all103 original bindings/local/global bases transfer exactly to the104-node candidate|

The manifest's `backhair` key points to the staged ribbon source. It is not evidence of a separate fourth input. The endpoint candidate SHA256 is `4bfc8d8ae5d4330d0e02d358f74f60ca989d43b2a61a3e59b937e8fa03b79c55`. Its added endpoint is an offset with a real imported node identity and an explicit parent bone; it does not acquire an independent rotating-bone ID merely because it is newly added.

All eight final headless child imports exited0 with no admitted warning/error/leak markers. All65 final retained preservation gates pass: original six bundle files plus manifest/staging receipts,46 isolated source files, Python/Godot executables, the source-copy receipt, all six gate source files, source membership and frozen root context. No GPU, main-view preview, physics behavior, live body/contact interoperation, native shader/jiggle fidelity or artist acceptance was tested.

## What makes this a complete binding check

The Python inventory independently traverses the entire GLB node table, active scene graph, skin joints/skeleton roots, native VRM0/VRM1 spring/center/collider references and generated helper declarations. The Godot snapshot separately parses the actual GLB and emits the same full source-node audit. Required active/declaration nodes must have a mapped actual binding. A supplied partial table cannot declare itself complete.

Bone mappings originate from SceneIO's source-index-keyed `has_source_bones` metadata and are verified against actual `Model.inventory` entries. Nonbone mappings come only from unique live `has_shape_source_node` tags. There is no display-name or palette/order guess. Every row records kind, explicit runtime identity, full local and global base matrices, original source-node index and source parent. Added helper nodes also require actual imported identities. Missing, duplicate, aliased, unsupported or problemed coverage refuses.

Actual Skeleton3D parents are joined back to source nodes using the observed skeleton path/bone index, then compared with the expected nearest source ancestor bone and with the candidate. Thus an identity-transform importer reparent cannot pass merely because neutral matrices happen to match. Offset rows verify their actual BoneAttachment parent, live node-local matrix and parent-bone/local global composition. Declared offsets additionally require equality with the secondary adapter's actual imported TRS descriptor. All comparisons of binding/local/global bases remain exact.

Static morph settings are mandatory gate inputs. Expected defaults/overrides are independently derived from the GLB inventory, and every actual imported morph row must exist with the right source-node identity and effective weights. Actual MeshInstance3D values are compared exactly after the explicit float32 API conversion; this is not a numerical tolerance. The official [Godot mesh implementation](https://raw.githubusercontent.com/godotengine/godot/4.6-stable/scene/3d/mesh_instance_3d.cpp), methods `get_blend_shape_value`/`set_blend_shape_value`, stores float values. The [BoneAttachment3D contract](https://docs.godotengine.org/en/4.6/classes/class_boneattachment3d.html) exposes the actual skeleton/bone index and transform update used by the offset check.

The archived `imported_binding_map` remains unchanged and is called only after these complete inventory/actual-import checks. It permits explicit original→candidate runtime-ID remapping while requiring matching binding kinds/base matrices and nonaliased bone/node identities. Offset IDs may legitimately share their explicit parent bone; each offset still has a distinct observed node identity.

## Controls and retained evidence

Synthetic negatives cover missing original rows in both tables, missing helper rows, wrong source indexes/inventory, wrong local/global bases, runtime/ID aliases, identity-parent reparenting, wrong bone kinds, missing/changed offset descriptors or attachments, no-op/missing/wrong morph rows, nonfinite/short matrices, problemed snapshots and duplicate coverage ledgers. Missing protected files and wrong root context retain a failed receipt before nonzero exit. Timeout controls retain partial logs without retry. Unexpected retained-case failures exit nonzero; ordinary no-proposal outcomes have an explicit distinct status.

The first15-control/initial successful observations remain retained separately. Independent review identified missing morph/actual-parent/offset assertions and failure-receipt gaps; those observations were not promoted to the strengthened contract. The final replay uses a fresh `isolated-v2` source copy and fresh result folders. The original `isolated` source and receipts remain unchanged.

`metadata/summary.json` gives the compact results and local-only proof folders. `metadata/complete_binding_observations.json.gz` contains70 metadata/log records: complete binding tables/base matrices, source-copy identities, exact commands, raw logs, preservation receipts, selections/refusals and historical observations. It contains no GLB/model bytes, image payloads or decoded vertex arrays. Raw owned inputs/candidates remain PC-only.

## Reproducibility boundary

These source recipes are archived for review. Copy them into the exact disposable `output/wind-helper-bindings-20261113/source` layout before adapting or running them; do not run from this publication folder. `support.py` freezes the literal dependency closure and unchanged builders/protocol/fixture factory from the pinned Git commit into a new owned project, with a unique Godot profile. It currently requires that exact root HEAD. A later current-code replay needs a freshly reviewed source freeze and new run folders, preserving these results. No tool installation, Steam access, SourceIO, Blender or model reconversion is used.
