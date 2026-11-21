# Retained SFM variant exporter candidate

Source/test authoring only. No current1084 code, HEAD, running Full, existing packet, owner asset or private receipt JSON is changed. The26 synthetic methods are unrun. The copied generic planner is the exact41cc24c4 source previously frozen with31 controls; those are separate scopes.

## What is implemented here

retained_variants.py contains concrete SourceIO capture, reversible owned-scene export selection, material/node/joint/skin hooks, final GLB reconciliation and generic HAS manifest construction. It imports no Blender/SourceIO module, starts no process, reads no file and registers no extension. A future qualified host supplies actual types/callbacks and the ordinary export call.

The ordinary route is unchanged: prepare(request, ...) returns None before catalogue/container access when retain_variants is absent or False. True explicitly requests the new route; malformed flags, unsupported source profiles, mixed appearance requests and invalid captures refuse. There is no fallback after a requested new route fails.

Only the fixed Nitori glove (44cece1f…,66bones/3skins/one present+blank group) and Keiki chisels (d8b32165…,31bones/one skin/three present+blank groups) are accepted. Profiles come from the committed corpus inventory, not newly read native assets. SourceIO bodypart/model ordinals, container.bodygroups entries and Object/Mesh/Material references must join the native table catalogue. Native default skin must be identity and each actual default slot must identify one unique native column; ambiguous/nonidentity cases remain refused.

All target skin Material refs are exposed as capture.required_materials. This is not just the default mesh material set. The bridge must rebuild ordinary VMT/PBR graphs for this entire set, then admit all actual graphs/resources before any resolver calls. Otherwise alternative SourceIO placeholders would appear as falsely supported skins. A material name is never used to bind exported resources.

During an export, visible_export(bpy) selects/unhides only the captured objects and original armature in a fresh owned scene. It restores selection, visibility, render flags and active object in finally. It writes no geometry, weights, skeleton, pose or material slot. A restoration failure latches capture state, preserves an already active primary exception and prevents later qualification.

The owned collector injects standard optional KHR_materials_variants mappings on its own temporary glTF primitives, using actual gathered Material objects and actual ChildOfRootExtension refs. The ordinary SDK traversal therefore retains alternative materials/images. No Blender preference or native custom-property variant setup is written. Root must qualify this new extension/resource profile separately; the default known-Junko NORMAL/resource profile stays unchanged.

Direct gather_node_hook/gather_material_hook/gather_mesh_hook/gather_joint_hook/gather_skin_hook observations bind final actual glTF lists by object identity. Duplicate display names are irrelevant. Every native joint and observed source skin must remain in the active scene, with complete same-native joint inventory and nearest native parent hierarchy. The final GLB scene/nodes/meshes/skins must match the captured final hook, and each primitive's retained skin mapping must agree with exact flat material indices. Missing materials, dropped meshes, foreign nodes, altered skeletons or required extension declarations refuse.

finish(raw_glb) returns {manifest, inventory, selection, summary}. manifest uses studio_model_variants_1, inventory uses studio_variant_asset_inventory_1, and selection uses studio_variant_selection_1. These are the exact generic41cc schema shared with the runtime candidate. IDs are final GLB indices and the manifest binds the final GLB SHA, so it belongs in parameters/HAS metadata after export, not self-referentially inside that GLB. A separate new model document capability/version must stop older readers silently showing all retained alternatives.

## Required host interface

- types: actual bpy.types.Object/Material/Mesh, SourceIO FastMesh, MdlV49 and ModelContainer classes, source/module admitted before construction.
- geometry_guard(): an already qualified complete32-byte fingerprint over every captured mesh's point order/positions/indices/weights/morphs plus skeleton/base/pose identities. It must exclude only the temporary visibility/selection and the deliberate ordinary material-graph rebuild. A no-op callback is not a production proof; synthetic controls use one explicitly.
- bone_proof: actual source_jiggle_crosswalk.NativeProof from prove_native_blender(raw,sha,mdl,armature,scale,actual_source_pins,Profile(sha,bone_count)). This reuses the existing source-pinned short-ASCII native/rest identity proof with an explicit new fixed profile, not the Junko default. Actual qualification of these two profiles is pending.
- gltf_types: actual Node/Mesh/MeshPrimitive/Material/Skin/Gltf plus Extension/ChildOfRootExtension classes from the pinned installed exporter.
- material_resolver(material, mesh, settings): authenticated ordinary SDK gather_material + get_final_material for the actual UV0 graph/attribute context. It returns the same observed base Material object; clone/nonzero-UV cases are refused in this first profile.
- resource_guard(material): admit the actual complete rebuilt local graph/image closure for that exact reference before resolution; every required material must pass. No guessed file/name matching or arbitrary True production shim.
- final_resource_guard(document, bindings): mandatory reconciliation of every final serialized material/texture/image against the actual recorded graph/resources. bindings are private triples of actual Blender Material, observed glTF Material and final material index. A count-only or unconditional True production callback is not a qualification. The separate finite optional-KHR resource host still needs to be implemented/qualified.
- contract: existing source_jiggle_crosswalk pure final JSON/graph helpers; planner: the copied exact41cc generic module.

The collector must be the single owned extension registered through the already reviewed temporary_export_extension context, with actual runtime aliases and source pins authenticated by the new host. An operator is called exactly once; latches are checked after it returns even if the SDK dispatcher swallowed callback exceptions. This helper alone does not qualify that host, callback authentication, shader equivalence, native point reconstruction or render fidelity.

## Concrete bridge splice after Root qualifications

1. Add explicit retain_variants CLI/request/UI option; absent/False uses the current static branch without constructing this helper. Reject simultaneous explicit static appearance and unsupported normal/variant combinations before export.
2. After ordinary SourceIO import and default skin0, obtain the bounded native catalogue from the selected immutable MDL. Build complete geometry/native proofs and call prepare. Keep all originals/source/runtime preservation in the existing worker boundaries.
3. For the new route only, union capture.required_materials into used_materials before the bridge's ordinary VMT graph loop. Retain an actual-reference ready/resource guard, not report-name lookups.
4. In the new export branch, keep every nonblank variant once, original armature, skins, morphs, rest position and original hierarchy. No mesh/skeleton cloning or Cartesian selection exports. Wrap the single exporter call in visible_export and one owned extension registration. Save editable.blend before temporary changes, as the current pipeline does.
5. finish the actual final GLB, recheck all sources, then publish metadata.model_variants and default variant_selection. Plan's runtime adapter binds actual GLTFState node/material order before parenting and uses per-instance overrides/visibility only.
6. Root runs synthetic controls, an actual isolated Nitori/Keiki conversion and resource closure check, then actual UI/Undo/packed+linked cold/movie and source/mesh/bone/morph preservation checks before any production adoption. Default import/static fixtures and the exact b843 known-Junko path remain separately unchanged.

## Primary timing and terminology correction

The earlier frozen PLAN used the shorthand “unused-material=False”. The installed exporter actually exposes unused_images/unused_textures controls, not an unused-material retention option. This source uses standard KHR_materials_variants references to retain materials. It does not toggle Blender's global variants preference or create source model variant properties.

Primary installed source: nodes.py gather_node_hook; obj_data.py gather_mesh_hook(mesh,data,obj,vertex_groups,modifiers,materials); materials.py gather_material_hook and get_final_material; primitives.py's own optional KHR_materials_variants/ChildOfRootExtension construction; exporter.py child-of-root traversal; export.py final flatten hook and ordinary JSON cleanup. Exact reviewed source hashes are in SOURCE_INPUTS.json.

Synthetic tests intentionally simulate ordinary traversal and use a nonrenderable tiny BIN, with no assets. They test type/reference/ordinal admission, default no-work behavior, reversible visibility, lost/foreign resources, full skeleton/scene coverage and final JSON reconciliation. They are not an actual exporter invocation. Root may run python -B -m unittest discover -s output/source-sfm-variant-export-prep-20261120 -p test_retained_variants.py -v only after its active Full closes. No author execution occurred.


Version2 test-only correction2026-11-21: original whole six-file proposal is byte-exact in bases/v1; failed real CPU result/exporter SyntaxError log are in bases/cpu-v1. The source-only authoring used a replacement-string operation that interpreted dollar/apostrophe tokens inside two assertRaisesRegex lines and inserted duplicate tail text. This successor directly concatenates the intended literal regex/finish/assertions, restores all26 existing test names and retains the explicit reference-order and source-material immutability assertions. Only malformed test source/metadata changes; retained_variants.py and variant_plan.py remain exact455b0847/41cc24c4. No tests were executed by the author. Root must bind this new folder/test pin in a separate coordinator revision; the old failed proposal/result remain immutable. Source-only prepare has not qualified actual native export.
