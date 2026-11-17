# Six-foot import basis: isolated executable prototype

Status: CPU-tested contract and Python container-reader candidate. Not installed in HAS; no model classifier, actual importer, GDScript parser, renderer, native converter, or engine was run. The accepted predecessor is `experiments/six_foot_import_basis_plan_20261115/PLAN.md`.

The prototype makes six feet exactly1.8288m at artist scale1 for an already authenticated, reviewed complete-human import. It adds a separate intrinsic `asset_basis`; it does not change the original converted GLB, source SHA, skeleton/rest data, artist placement, pose keys, or Source conversion0.01905. Standardization is a single uniform multiplier about the original asset origin. Parent and artist scales continue multiplying normally.

## Executable work

- `import_basis_candidate.py` implements the strict record validator, deterministic50-significant-digit decimal ratio, fresh-import candidate conversion, explicit per-model preserve/complete-human override, schema9 capability writer/reader gates, and an exact synthetic `C * B0` root-composition prototype. It performs no file IO or geometry inference.
- `draft/tools/import_basis.py` is the exact tested helper proposed for a future Python port. The factor guard0.001–10000 is a provisional prototype guard matching the existing artist-scale numeric domain; it is a limit to review, not a new owner requirement or an instruction to alter artist scale.
- `draft/tools/has_project.py` adds one facade around the existing resource validator. It preserves the entire old function body, renaming that function and all **four** recursive calls together. Its only other edit is the helper import. Reversing the precise recipe restores every original source byte; an independent Python AST comparison also proves all original code is preserved. The source patch is `has_project_reader.patch`.
- `test_import_basis_candidate.py` passed26 test methods, including271 heights checked against an independent rational oracle. `test_reader_draft.py` passed10 methods executing both the real original Python reader and the isolated successor against synthetic metadata. Counts describe CPU test methods and cases, not HAS/engine assertions.

The historical first24-method CPU result is retained as `CPU_RESULT.json`; `CPU_RESULT_v2.json` is the current26-method result. The first draft-preparation attempt refused before writing because an LF anchor did not match the original CRLF source; `PREPARATION_FAILURE.json` records the cause. The corrected builder preserves original line endings.

## Capability and interpretation

An active basis requires outer project schema9, `import_basis_capability=studio_import_basis_1`, and `basis_content_schema_version` identifying the existing3–8 stack underneath. Factor1 still requires the capability: active interpretation must be explicit even when that particular factor happens to be identity. Missing or redundant wrappers and unknown fields are refused.

Each sequence child with an active basis needs its own wrapper. A parent also wraps when any child requires the feature. Parent permission never authorizes an unwrapped child. Removing only the new wrapper must leave the exact existing sequence child admission4/5, optionally under the existing timing8 wrapper. Reference7 sequence children remain unsupported. The new gate retains the existing shared64-object ceiling and4-child ceiling; it does not replace the complete old sequence/resource validator.

The current old Python reader was actually called: it accepts a legacy-version world with an extra active basis field while ignoring that field, and rejects schema9. This confirms the version gate is necessary. The existing GDScript `Storage` schema checks also do not admit9; that is a source finding, not an executed old-Godot test.

The successor first validates all scene-local basis records and wrapper scopes. It then makes a transient validation copy with only the new wrappers removed so the unchanged legacy resource validator can enforce its original paths, schema stacks, timing, reference, sequence and resource rules. The original schema9 manifest remains intact. The transient copy must never be saved, returned as a decoded active document, or sent to a renderer. The GDScript reader still needs its own explicit scene-local permission before any activation.

Decimal text is canonical, bounded, finite and positive; exponential notation, signs, leading/trailing redundant zeros and unknown values are refused. The factor is recomputed at a specified decimal precision and must match the stored text exactly. The rounded decimal factor gives a tiny finite arithmetic error for nonterminating ratios; it is not claimed to equal an infinite rational expansion. Python/GDScript parity of this rule is still required before a shared production port.

## Per-model intent and exclusions

`prepare_fresh_import` only constructs a dictionary. A source-matching assessment must already establish a reviewed neutral complete human and a positive uniform source root. This prototype implements no classifier and does not prove such an assessment merely because its SHA matches. The current `CharacterHeight.query` visible-extrema/coverage heuristic is not promoted into that authority.

Known partials, hair/head-only inputs, maps, props, tools, multiple figures, uncertain classifications, environment/group records and explicit preserve-original intent keep their original basis. A complete-human override accepts a separately reviewed complete-human assessment; it does not override known-part exclusions. Nonfresh HAS/legacy input is not normalized. Already standardized input is validated and copied without remeasurement or multiplication. Prior diagnostic `metadata.import_height` remains inactive, including its already-applied legacy artist scale.

The bounded fresh path requires artist scale1 and no existing pose keys, refusing to flatten authored controls. A changed source/derivative SHA is refused because authenticated derivative lineage is not implemented. In particular, Helper Apply must stay unavailable for normalized models until its preservation proof is integrated; blindly replacing the basis SHA is invalid.

## First safe implementation increment

The first safe port is **contract plus container capability only**, with automatic import activation disabled. The isolated Python facade is concrete code for that increment. Port an equivalent GDScript validator before `Model.validate`'s model9 delegation, then add schema9 admission/writer wrapping to `Storage.readable_manifest`, `save_project`, and `decode_project` with scene-local permission. Adapt `Extended.required` and `child_schema` to inspect beneath the new wrapper while preserving their old underlying gates. Add current container/package, timing/reference/sequence and old-reader fixtures. Do not ship files with active bases until both readers and writers agree.

The first later **activation** boundary is the fresh raw-model transaction before `app.append_object_data` placement/default-physics commit. Keep request/generation, project/world revision, source SHA and cancellation checks around that transaction. Existing HAS import, load, Undo, recovery and source-only inspection bypass standardization.

Runtime composition belongs in one `Model.configure_import_root(rawB0,definition)` helper: cache immutable rawB0, validate once, set `base_root=C*B0`, then let existing `Model.apply` use `U(t)*base_root`. `Renderer.prepare_model`, `WorldRuntime.prepare` and auxiliary raw constructors need that same helper. Placement already containsB0 in `local_bounds`, so it needs `U*C`, not a secondB0. Add `asset_basis` to immutable world-instance asset fields. Disposable comparison/wind previews must preserve the basis explicitly; an absolute `live_world_transform` is an assignment, not another multiplier.

Source native lengths remain `rawLength * 0.01905 * actualWorldUniformScale`. The actual world factor includes the basis; multiplying0.01905 by the basis again is a tested double-scaling error. No native profile/crosswalk SHA is rewritten. A real nonidentity basis still needs fresh five-rule physics, Off/Record/seek/save, placement, preview, helper lineage and cold-HAS tests. All49 simulation, PMX physics reconstruction and full body coupling remain separate work.

`SOURCE_LOCK.json` records the actual architecture and predecessor files inspected. `INDEX.json` records this packet's payload hashes. The packet contains only public source, synthetic numeric fixtures and metadata; no owner model, geometry/rest arrays, images, audio or private expected state is included.
