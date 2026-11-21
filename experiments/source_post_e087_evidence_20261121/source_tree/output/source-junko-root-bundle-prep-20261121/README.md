# Junko root-folder character bundle — original source proposal

The owner provided six loose SFM model families under one root. The bounded CPU audit found99 original files,32,525,911 bytes:6MDL,6VVD,18VTX and69 material/texture dependencies. All six primary models are MDL49; their matching VVD4 and DX90VTX7 checksums agree. This audit decoded bounded headers, bone parent/rest/bind metadata and raw VVD position bounds in RAM. It did not convert a model, import SourceIO, run Blender/Godot/GPU, write an original, or publish bone/geometry arrays.

BUNDLE_AUDIT.json is the compact six-family/hash/compatibility matrix. The complete99-file relative-path/hash/size/nsmtime inventory stays private at output/private-junko-folder-audit-20261121/ORIGINAL_INPUT_PINS.json; only its hash/count is published here. Existing approved independent cbb4 native reader and c04 metadata layout contracts were consulted, with actual pinned SourceIO Bone.from_buffer semantics for the rest fields. The execution was a bounded Node RAM read of those same layouts, not execution of either published Python parser. Their stricter closed renderable-geometry profiles must not be advertised as qualified for all six files: this audit is headers/rest metadata only.

## What the files actually contain

| Piece | Bones | Jiggle rules | LOD0 points | Skin families | Use |
|---|---:|---:|---:|---:|---|
| Body |145|2|18529|16|Base character|
| Hair |69|49|9661|1|Attachment; exact previously qualified8da hair family|
| Dress |112|28|7842|1|Reviewed outfit candidate|
| Skirt |136|102|2742|1|Reviewed outfit candidate|
| Miniskirt |136|102|2742|1|Reviewed outfit candidate|
| Character mask |19|0|584|1|Optional attachment|

These are six model entrypoints, not30 parts: VVD/DX90/DX80/SW/VMT/VTF remain dependencies. Native true-blank bodygroup choices and the body's16 skins are separate capabilities from showing/hiding an entire bundled piece. The current selected-only Source export does not become a retained-native-variant feature just because this folder has been grouped.

## Rest compatibility is not universal bone merging

Body↔dress has56 shared exact-name bones with identical parent names, native local position/quaternion words and native poseToBone words. Two of those shared bones are procedural owners. This is a strong rest-map candidate, not permission for two live solvers to overwrite the same joint.

Hair↔body has6 common bones with equal parent names but different rest/bind words; differences are small but must be explicitly bound/compensated and qualified. Mask↔body has7 common names with4 parent conflicts: local transforms can differ greatly when a model flattens its hierarchy even if global bind frames are close. Skirt↔miniskirt shares all136 names and parent relations, but135 native rest transforms differ materially. Never merge these skeletons by labels alone. Every pair's exact counts and diagnostic maximum differences are in the matrix; numeric diagnostics are not a fuzzy admission waiver.

Raw mesh bounds and bind metadata are consistent with parts occupying one Source coordinate space, but exact current converter/importer alignment is UNRUN. MDL contains no embedded metre-unit declaration. Use one explicit Source unit/axis policy for all six conversions, preserve their source origins, then verify actual mounted part alignment. Do not independently recenter, ground, rotate or height-normalize hair, mask or clothes.

## Smallest visible increment

1. Add an explicit Load models in this root folder command. Discover bounded unique MDL families and their dependencies, show the six entries, and run ordinary existing conversion separately into an owned prepare-all transaction. No directory traversal alias, case-collision or missing-sidecar guessing. Roll back the new bundle if any required conversion fails; keep the installed world unchanged.
2. Produce one inert, geometry-free GLB for the character World root. Existing WorldDocument requires an actual managed asset/hash even for kind=group; do not create a fake source-less World row or turn the body into a group that loses model tools. The body's actor remains a regular model sibling under that root.
3. Parent all six model actors to this root at the shared converted source origin. Preserve each actor's exact source identity, mesh/skin resources, local root, bone inventory, existing morph data and live-motion ownership. WorldRuntime already inventories each actor BEFORE attaching children, so this route can keep inventories separate. Moving/scaling the root moves the bundle once; it does not drive child bones.
4. Show a Parts list/context action for the selected character. Body and hair are the conservative initial visible set. Keep mask optional; import dress/skirt/miniskirt but leave outfit visibility pending an explicit reviewed set. A set can intentionally layer more than one piece. Do not load all alternatives visibly by default or delete the hidden assets.
5. Show/Hide at frame routes through the existing per-model visibility keys. An outfit-set switch is one existing world_objects Undo transaction affecting only the selected clothing actors. Attach/Detach in this first stage means root grouping with world transform preserved, not bone attachment. Never modify poses/physics/morphs as an outfit switch side effect.
6. Root scale is a single bundle operation. If a six-foot normalization is later requested, measure/classify the complete body once and apply one common factor. Today's ImportBasis explicitly permits active asset_basis only on kind=model, so do not forge a verified-complete-human record on hair or a group, remove an existing basis silently, or double-apply a body basis plus root factor. A first static bundle can use ordinary explicit root scale and leave standardization reference proof untouched. Full bundle reference semantics need a separately validated capability.

## Pure planning candidate

bundle_plan.py has no filesystem/SDK/conversion/application imports. It accepts this exact six-family audit, explicit host-owned actor IDs, one group ID and common unit policy, and returns an UNAPPLIED static plan. It selects MDL entrypoints only; keeps all six parts; permits explicit outfit sets; and emits ordinary per-frame visibility operations without mutating the plan or assets. It does not return a forged World document, invent an empty-group asset, load a model, merge a bone, or mark a conversion/storage capability qualified. Its digest detects accidental plan mutation; it is not a signature or a substitute for actual asset/source admission.

The25 unittest methods cover discovery vs sidecars, case ambiguity, missing/extra families, one root scale, no independent height normalization, outfit defaults/review, optional mask, stable pose/morph/physics ownership, immutable handoff, source/header/ID/unit refusals, frame-key operation scope and no promotion of exact-rest metadata to bone merge. Root command after an available CPU lane: python -B -m unittest discover -s output/source-junko-root-bundle-prep-20261121 -p test_bundle_plan.py -v . Author executed none.

## Concrete function/file map for a future product port

- src/source_import.gd: start/generic_dialog/launch/_process: add a separate root-folder queue with one source-unit policy; don't change single-model defaults.
- tools/prepare_source.py and existing Source archive/mount resolution: ordinary per-MDL conversion and material closure; preserve original family bytes and full source provenance. No new parser replaces them.
- src/world_document.gd: object/validate/assets: construct the real inert-root group plus six valid existing model records; respect MAX_OBJECTS64.
- src/world_runtime.gd: prepare topological parenting/inventory before child attachment: atomic bundle preparation, rollback, root transform and per-actor ownership.
- src/world_selection.gd: select_entity/choose_at/context_action and World tree rows: Parts list and Manage parts menu for bundle root/member selection.
- src/pose_editor.gd existing visibility-key operations and app existing world_objects history: Show/Hide at frame and one-command outfit switch, then packed/linked independent cold-save tests.
- src/import_basis.gd + project/HAS admission: only if adding new bundle-wide reference/bone-link semantics; current group/static visibility can remain ordinary legacy-compatible World data.

## Later posed bone-following capability

One World parent only moves the child's root. A body arm/head pose will not automatically drive independent clothes/hair skeletons. Add bone following only after exact source-node/native binding and parent/rest map checks, bind-offset compensation where needed, and an explicit driven-vs-child-owned joint policy. Common passive attachment bones may be driven; hair/dress procedural chains, local morphs and independent authored keys cannot be overwritten. Two shared procedural owners in dress/body require explicit ownership. Unqualified/conflicting bones remain independent, not silently guessed. Add cycle/feedback refusal, atomic preflight, pose/solver composition and contact tests.

Persisted bone links must have a new explicit schema/capability marker and older readers must reject unsupported semantics rather than open a static approximation. Coordinate the existing prepared outer schema10 capability mechanism rather than reusing permissive metadata. A legacy static group needs no fictional bone-link marker. Until actual conversion/alignment, UI/history, pose-follow and cold storage pass, all application/bone-link qualification flags remain false.
