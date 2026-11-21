# Next SFM addition: skins and parts on an existing actor

Status: authored source and synthetic controls only; not run or adopted. All current1084 functional files, the running Full and existing source evidence remain unchanged.

## Missing capability confirmed

Import-time appearance choices already exist. Do not reimplement them: source_choice_dialog.gd builds skin/bodygroup controls and request(), source_appearance.choose/apply validates native indices and prepares one static appearance, and the November13 static-appearance receipt covers14 actual cases (12 prepared bundles and2 expected all-blank refusals). The present dialog explicitly says it does not change models already in the scene (source_choice_dialog.gd:190). The bridge selects only visible objects for GLB export and reports “no runtime variant switching”; editable.blend retains other imported objects. src/model.gd has no runtime skin/bodygroup selection state. The only skin/bodygroup references in src are the import dialog.

The addition is **Appearance… on a selected existing model**, with Skin and independent Parts menus, including real blank alternatives. A selection changes the same actor, geometry, skeleton and pose; it does not reconvert, replace its asset or fit a new height. The first version is a saved whole-model setting, not animated variant keys.

## Bounded supplied cases

1. Nitori tanktop glove: native MDL49 SHA44cece1f44dfc3d7b32b91b5acfdae53ec9f6f90a0220a422ace92e323da7b32,66 bones,3 distinct skin rows, one glove present/true-blank bodygroup. The existing metadata and static14-case evidence establish this candidate; no native files were read for this preparation.
2. Keiki chisels: native MDL49 SHAd8b32165bef2ec4f1c09acd19b3b136b3492b556fcfb9da98fb01826c5e279ff,31 bones, one skin row, independent tools/box/flame present/true-blank groups. This is the second case for combinations without a Cartesian explosion.

The metadata inventory contains27 distinct definitions with differing skin families and157 true-blank choices, but those counts are not runtime qualification. A choice named “blank” may contain real geometry. Preserve each native numeric row even when two skin rows look identical. Do not infer blanks, slots or variants by material/model names.

## Authored generic HAS contract and pure implementation

variant_plan.py is source independent. It consumes a separately authenticated GLB inventory and a complete variant manifest, and produces a complete before/after application plan without file, engine, decoder or resource operations. test_variant_plan.py has31 authored unittest methods, unrun by the author. The synthetic glove/accessory fixtures resemble only cardinalities; they are not the supplied assets.

The exact schema is in SCHEMA.md. Core APIs:

- validate_manifest(manifest, inventory): validate all identities/domains/coverage, return a detached canonical manifest.
- default_selection(manifest, inventory): explicit skin and every group default.
- plan_selection(manifest, inventory, selection): node visibility and per-instance surface-material assignments.
- plan_change(manifest, inventory, current, skin=…, groups=…): complete before/after plans; no caller mutation on success or refusal.

Indices are numeric, never labels. Every mesh surface has exactly one material ID for every skin. The declared default must equal the actual GLB inventory. Controlled mesh nodes are disjoint across choices and cannot be mesh ancestors: hiding a parent must not silently hide unrelated geometry. No shared mesh/material resource is edited by this planner. All-blank is valid at runtime because the complete asset stays present; the existing converter's all-blank export refusal remains unchanged.

## Smallest concrete port, in order

| File/function | Proposed change | Required boundary |
| --- | --- | --- |
| tools/prepare_source.py argument/request construction; src/source_import.gd.launch | Add an explicit retain-variants option for supported Source model profiles; default path stays byte-for-byte ordinary | Maps, archives with ambiguous selected members and unsupported profile combinations refuse before export |
| NEW tools/source_variant_export.py collector | Capture genuine SourceIO container.bodygroups by native bodypart/model ordinal, exact Object/Mesh refs, true zero geometry, per-object surface slots and available skin Material refs | Reuse source_appearance.catalogue's identity/ambiguity guards; preserve raw native indices and case. No label lookup. Initial producer admits only identity native default skin and unambiguous existing-column mapping, as existing static selector does |
| tools/blender_source_bridge.py import and export selection | In the explicit new branch, export every nonblank variant once, using one existing armature, not one exported file per combination | Snapshot visibility/selection, restore in finally; never overwrite editable.blend, originals or current actor. Existing known-Junko NORMAL profile remains unchanged; new variant mode is explicitly incompatible until separately qualified |
| NEW producer/export hook | Bind each captured Object to an actually exported glTF mesh node and its exact primitive order; bind all alternate skin Material refs to actually exported material indices | Must retain all material/image resources, including those unused by the default skin. Current strict unused-material=False/known-Junko resource profile cannot simply be flipped. Qualify a separate finite opt-in profile; a metadata list alone does not retain resources |
| parameters.json publication / PoseEditor.definition | Publish generic metadata.model_variants after final GLB checksum; initialize explicit saved variant selection | No self-referential GLB checksum inside its own JSON. Sidecar manifest SHA binds final GLB; ordinary HAS packing copies metadata and one GLB |
| src/scene3d.gd.load_glb | Retain exact GLTFState node-index→generated MeshInstance and material-index→Material references beside current source-bone/shape metadata | Use actual state mapping/membership, not names or nearest geometry; confirm inactive material resources survive import. Build a source inventory and validate manifest before showing the actor |
| NEW src/model_variants.gd; src/model.gd.inventory/apply_current | Port the pure planner to GDS and prebind all refs once; apply instance visibility and set_surface_override_material only | Prevalidate entire transition; snapshot owned overrides/visibility for rollback. Preserve Mesh/Skin/Skeleton resources, weights, morph targets, native-bone IDs, pose keys, imported B0, parent/artist transforms and six-foot/reference scaling |
| src/model_opacity.gd authored_material/set_appearance | Release temporary opacity/unshaded copies before swapping base skin overrides, then rebuild with the same evaluated alpha/mode | Existing set_appearance(1.0,false) restores originals; explicitly preserve/reapply previous alpha/mode. Selection/picking must see the new authored cutouts. Never mutate shared BaseMaterial3D or Mesh surface materials |
| NEW Appearance editor, attached by src/pose_editor.gd | Simple Skin and Parts dropdowns; exact labels with numeric metadata; Blank may be labelled “Hidden” in UI without replacing native name | Use restore_state for one normal model/world Undo; no reconversion, skeleton replacement, physics auto-start or timeline-key mode. Refuse during export; stop/freeze active live simulation before a state change |
| Model.validate + tools/has_project.py + cold readers | Add explicit model-version/capability admission for saved variants and selection; preserve metadata through packed/linked storage | The current highest model version is studio_model_9. Assign the next version on landing; do not reuse9. Older readers must reject new variant documents rather than display every retained mesh at once |

No product code is changed by this packet. A new all-variant exporter is required before the schema can be offered to users; this preparation does not pretend that its integer inventory proves native/exporter correspondence.

## Visible acceptance after Root can run the new branch

- Nitori: switch among all3 skins and glove present/blank on one actor; same root/skeleton/native IDs, source SHA, geometry/weights/morph arrays and poses before/after; material changes reach the intended surfaces, with all resources local.
- Keiki: switch independent tools/box/flame, test combinations and all-blank, restore defaults and Undo/Redo. The native Tools morph stays editable while parts are hidden and returns unchanged when shown.
- Two instances of one asset: appearance changes affect only the selected instance. Unshaded/Lit, cutout picking, opacity fades, body/hair Off restoration, frame bounds and normal movie sampling use the same selection state.
- Packed and linked HAS: save, take source/intermediate/resources offline, cold open in a new private process; same selected variants, exact metadata/identity and preview/export pixels under the existing pixel policy. Retained GLB is self-contained for every admitted skin, not just the default.
- Old projects and ordinary single-appearance imports retain their current behavior and format. New metadata corruption, missing nodes/materials, foreign asset SHA, unsupported hierarchy or excessive budgets refuse without partial changes. Do not promote generic Source shader, native solver, appearance-fidelity or all-corpus acceptance.

The31 pure controls cover deterministic before/after plans and refusal/atomicity only. No Blender, Godot, native model, parser, GUI, process, Git, installation or network run was performed for this packet. Root may run its pure controls later with python -B -m unittest discover -s output/source-next-sfm-variants-prep-20261120 -p test_variant_plan.py -v after the active Full closes.
