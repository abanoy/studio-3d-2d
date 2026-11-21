# Isolated Junko rest representation probe

SOURCE ONLY / UNRUN. Prior actual factory-boundary run proved the major drift appears immediately after EditBone.matrix assignment; actual load_refpose was false and its branch did not run. The assigned matrix agrees with independent native rest to9.558e-8, while the getter differs4.774e-5. Subsequent EDIT writes contributed zero and OBJECT transition4.292e-6. No cause beyond this boundary or repair has been qualified.

This standalone approved Blender5.1 CPU probe uses the exact pinned private capture. No SDK/SourceIO load or conversion occurs. It creates22 independent bones in one owned scratch scene/armature: the original pre-assignment head/tail/roll baseline, then seven display lengths for ordinary setter, setter followed by align_roll, and the installed glTF importer's explicit axes/length/align_roll method. The exact assigned matrix is retained unchanged.

The original baseline must reproduce both captured EditBone getter and DataBone matrix bit-exactly and still fail the existing pinned C.close native-rest predicate. Otherwise the probe refuses; it cannot assume independent scratch bones match the original armature. Candidate errors are measured against both the assignment and independent native rest using that same unchanged predicate. No candidate is applied to any real model.

Native matrices stay private. Public output contains only per-case method/length/errors/pass flags and context-cleanup status. All owned scene/object/armature data must be deleted; original object matrices/data identities, scene/armature/object membership, window scene, active object and selection must be restored exactly. Inputs are reread byte-exact.

Pure12 tests only exercise synthetic inputs, schedule and measurements; no Blender/SDK/native data or child processes. Scratch22 remains a separate actual Blender component, not native export, follow, skin, physics, renderer or Full qualification.
