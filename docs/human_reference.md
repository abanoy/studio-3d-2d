# Six-foot human reference

Enable **Options > Offer character height matching on model import**, import a
complete character, then select **Six-foot reference — Scale 1** in the review.
The target locks to 1.8288 metres and Add installs the character at artist Scale 1.
In Simple mode, the selected model's **Human reference** card offers relative
size and Apply. Ordinary scale Undo/Redo and animation rules still apply.

The visible neutral feet-to-head extent is measured using the existing coverage,
axis and proportion guards. Hair, shoes and hats affect that extent. It is not
an anatomical stature estimate or a trained classifier. Incomplete heads and
other parts cannot opt in; uncertain complete figures require an explicit choice.
Props/maps have their existing separate size workflows. Source files remain
unchanged, including original conversion units and imported root transforms.

The measured asset reference is independent of artist scale. Runtime composes
artist transform * reference factor * original imported root. Import constructors
capture that root once; Open, physics, helper previews and relative edits do not
measure again. Existing projects without an active reference retain their old
behavior. Simple controls hide when the reference model is deselected or removed.

`asset_basis` stores canonical bounded decimal measurements, exact source hashes,
the deterministic six-foot factor and the explicit decision. A scene-local outer
project schema 9 requires capability `studio_import_basis_1`; timing/reference
wrappers retain their existing inner versions. Older readers can refuse rather
than silently opening the asset at the wrong size. Every active nested scene
needs its own capability. JSON numeric versions and legacy schema 1/2 guards are
tested independently in Python and Godot. Existing container/resource limits
and atomic save/rollback checks remain intact.

An existing-joint helper can inherit the reference only after an independent
before/after GLB comparison proves unchanged root/rest/skin/morph/material data
and exact unchanged BIN bytes. Only the checked additive unweighted endpoints
and their matching spring declarations are allowed. The proof binds current
file hashes and is recomputed before adoption; stale candidates are refused.
The resulting source identity chain stays separate from the original measured
identity. Generating weighted helpers for a reference model currently refuses
because that preservation proof is not implemented. Legacy weighted helpers
remain available. No unsupported derivative is silently remeasured.

Body Physics now supports the qualified reference-size path, including artist
sizes0.5/1/2, using metre collision planning and reciprocal body offsets. The
original rig/source data stay intact; Freeze, Record, generic hair composition,
history and packed replay use ordinary canonical poses. Unsupported numerical
or structural states refuse before allocation. Existing reference-free body
physics retains its behavior. See [the body contract](reference_body_physics.md)
for bounds and exact executed scope. This replaces the November19 interim
nonunit-scale refusal; earlier guard reports remain historical.

Run `python -B tests/verify_human_reference.py --theme neon` or `--theme light`.
The checks use authored synthetic figures at two original sizes, measure Scale
1/.5/2 geometry, preserve originals, exercise Undo/Redo and packed/linked save,
start a separate cold reader, and export a two-second 1080p H264 movie with an
independent editable drawing. Preview and export input images are compared;
encoded-video pixel equivalence and native-model fidelity are separate claims.
The historical guarded native avatar reference check passed25 size/Undo/save/
reopen/body-boundary checks on the existing VRM0 preparation, with original/staged hashes
and mtimes preserved. The earlier23-check review remains historical.
This does not certify the model's appearance against its original application.
The ordinary height/native regression suite remains separate. Full results and
failed attempts are recorded in the current benchmark/pickup after execution.

Source08ad583 also passes the complete Windows default:163 result groups,36 core
groups and20 final media entries, with1045 functional files unchanged and200
unique private jobs closed. Its optional old PMD pose branch was absent; a
separate exact-source private replay passes45 checks and two movies. Those scopes
remain separate. See [terminal evidence](benchmarks/human_reference_full_2026-11-19.json).

Not included: automatic default normalization, assembly of separate parts,
changing an existing character's reference, broad native-fidelity certification,
weighted-helper reconstruction, unrestricted body-physics scales, or the larger
planned HAS model capability audit.
