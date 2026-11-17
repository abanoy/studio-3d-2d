# Six-foot basis successor: GDScript domain and closed boundaries

Status: isolated source draft. Python contract tests passed; **all GDScript files are unparsed and unrun**. No normalization, classification, schema9 loading, or importer has been activated in the application. Main functional files and the sealed predecessor remain untouched.

The predecessor is `experiments/six_foot_import_basis_candidate_20261116`, INDEX024b4a890003789bd251649eaddee9cbf7034f602ce54340135d62929f188c5e. Independent review found two direct-API issues: decimal division inherited ambient rounding, and string/integer control flags were truthy. This successor fixes both. It also closes the Python worker path until a matching runtime is qualified.

## Concrete code and actual CPU evidence

- `import_basis_v2.py` and exact alias `draft/tools/import_basis.py` use a fully explicit50-digit, nearest-ties-even Decimal context, including exponent/trap settings. Capability, fresh-raw and internal readiness flags must be actual booleans. The default `members_with_capability` worker route refuses active basis documents until internal runtime readiness is true. No request field or CLI switch enables readiness.
- `draft/tools/has_project.py` retains the previous exact facade/old-function/four-recursion rename. The worker calls the helper's default closed route. Its complete original Python AST still matches the original reader after reversing only the documented facade/import/name changes.
- `test_python_v2.py` actually passed29 methods, including271 rational height cases and cross-context height7 create/reopen under precision1/7/28/99, ROUND_DOWN/UP/HALF_EVEN and an Inexact trap. `test_reader_v2.py` actually passed9 methods against the copied worker reader, including refusal before the old resource body. Internal-ready positive paths are synthetic contract tests only.
- `decimal_string_reference.py` uses independent integer arithmetic. Its50-significant-digit rounding agrees with the fixed Decimal oracle for271 height cases and72 direct ratios, including carry/tie and extreme magnitudes. `PARITY_CPU_RESULT_v3.json` records the current434-case expected matrix. This is a CPU oracle preflight, **not** execution or parity qualification of GDScript.

The original392-case matrix and the396-case expansion are retained as preparation history. The434-case `PARITY_CORPUS_v3.json` is the current input. One intermediate generator run refused before writing because a local dictionary shadowed the fixture constructor; another hooks-builder run refused ambiguous source anchors. Both were corrected by explicit names/function-scoped anchors. They were source preparation failures, not application test results.

## Unrun GDScript domain

`import_basis_domain.gd` implements bounded canonical decimal parsing, exact string long division with50-digit ties-even rounding, record validation, scene-local capability wrapping/inspection, and `C * rawB0` composition. It uses no float division to authenticate the persisted factor. Its internal computed-ratio comparison allows256 characters because a valid96-character input can produce an out-of-range tiny value longer than96 characters; that value must be rejected without indexing an error dictionary. Public decimal inputs remain bounded to96 characters.

Legacy absence returns factor1 and retains the raw root, including existing legacy nonuniform roots. An active basis requires scene-local capability **and** explicit internal runtime readiness. Positive readiness in the standalone domain probe is a test fixture, not a production setting. Active root composition rejects nonfinite, reflected, nonuniform or sheared roots using the existing2e-5 transform guard. No native source scale, rest, IDs or GLB bytes are changed.

The schema domain keeps outer capability9 separate from model-format9 root animation. Each active sequence child has its own wrapper; parent permission cannot authorize a legacy child. Reference7 sequence children stay unsupported. The existing4-child/64-object admission is retained, and a legacy validation/resource pass remains mandatory. Capability inspection alone does not validate source availability, duplicate IDs, raster budgets, actual reference records, or classification.

`basis_domain_unit.gd` proposes **444** checks:434 pinned corpus rows plus10 synthetic transform/refusal checks. `basis_boundary_unit.gd` proposes **21** checks using a new synthetic empty GLB and real legacy `SceneIO`/`Model`, plus the draft early-refusal adapter. These scripts have not been parsed or launched. They do not exercise a connected application import flow or validate a real complete-human model.

## Closed production boundaries before activation

`source_boundary_guards.gd` and its exact `draft/src/import_basis_boundary.gd` alias refuse every active basis or capability marker. They expose no readiness switch. `PRE_ACTIVATION_GUARDS_v2.patch` is the current unapplied, unparsed exact-source draft with ten guarded insertions across eight files:

- `Model.validate` refuses before model9 delegation and binding validation.
- `Storage.readable_manifest`, `decode_project`, and `save_project` refuse unsupported active data/markers before interpretation, raster allocation, or save-side writes.
- `Renderer.prepare_model` refuses before raw loading/inventory.
- `app.append_object_data` refuses before live-motion freezing, placement, managed copying or world installation.
- Shape comparison and wind preview check the original actor before making a new `Model.definition` that would discard its asset fields.
- Helper preparation and installation refuse before source re-import or derivative source replacement. Authenticated basis-preserving helper lineage remains unimplemented.

`PRE_ACTIVATION_SOURCE_v2.json` pins each original source, each proposed source hash and an inverse edit recipe that restores every original byte. The first patch/source pair is retained as source preparation history: source review caught its null helper-source dereference before any parse/run, and v2 preserves the existing null-refusal path by inspecting an empty dictionary when no source actor exists. Nothing in either patch composes a basis or normalizes an import. The successor is a proposed first defensive increment; staging/parse/runtime/full tests must precede any promotion.

Neutral `SceneIO.load_glb` stays raw and has no normalization behavior. Root capture, initial placement, asset-derived previews, helpers and immutable-instance fields must all be integrated before later activation. Standardization must never be put unconditionally into SceneIO. The future active root helper must receive immutable rawB0 exactly once; `Model.apply` continues `U(t) * base_root`, and placement uses `U * C` because its local bounds already includeB0. Source native conversion remains exactly0.01905; actual world scale carriesC once.

## Worker bridge finding

Peer evidence is `experiments/six_foot_boundary_review_20261116`, INDEXb9cc057f09c810ada2c455e4e236e7fa270482f442cefbcbecd8124cb1f7a07d. Its actual predecessor-only synthetic CPU tests showed that Python pack/unpack preserve original schema9 manifest bytes; current normal HAS open/import reaches `Storage.decode_project` and refuses9 before live installation. There was no observed silent downgrade in that normal bridge. However, accepting9 in a Python-only worker could create a file current Godot cannot open. The v2 worker therefore defaults to refusal.

Legacy3–8 active model fields are a separate hazard: old model readers ignore extra data, and the existing save path can preserve that field while emitting a legacy schema. The proposed early Model/Storage guards address that boundary. The peer's Storage/Model counterexample script remains a separate unrun probe; no result is inferred from its source.

## Root-owned later execution

After the full verification lease is terminal and closed, root can stage this packet without changing main. Keep its `experiments/...` relative path so the standalone preloads resolve. Parse the domain and both probe scripts first. Launch probes through the existing private/owned runner with a fresh output directory, source/runtime SHA pins, process/desktop closure and no concurrent engine lease.

The domain job format is `has_six_foot_domain_job_1`, phase `ROOT_APPROVED_SIX_FOOT_DOMAIN`, with `root_closed_all=true`, an expiry, script SHA, `PARITY_CORPUS_v3.json` path/SHA, and a new owned output folder. The boundary job uses format `has_six_foot_boundary_job_1` and phase `ROOT_APPROVED_SIX_FOOT_BOUNDARY`, with the same closure/expiry/script/output controls. The outer root launcher must qualify paths, files, module hashes, processes and ownership; the scripts are not a substitute for that launcher.

Neither a future444/21 result nor the actual29/9 CPU results would qualify automatic human classification, full application activation, real model stature measurement, helper lineage, PMX physics, all49 rules, same-actor body coupling, or actual native simulation under a nonidentity basis. Those remain explicit later gates. Per-model preserve intent and partial/map/tool exclusions remain in the tested Python candidate; the GDScript draft contains no classifier or fresh-import activation to bypass them.
