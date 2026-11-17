# PMX physics preservation: next integration map

This is source-only preparation. No importer, file format, live physics or current Windows review is changed. The existing universal-model plan in `docs/RESUME_MASTER_PLAN.md` sections14–16 remains the roadmap. Native PMX qualification must precede production adoption; the sealed reader's capsule remains `UNQUALIFIED_SOURCE_CPU_ONLY`.

## Current path and exact loss boundary

| Boundary | Preserved today | Missing from the portable physics contract |
|---|---|---|
| `tools/prepare_mmd.py:33–96` | PMD/PMX audit identity, owned native model/texture copies, dependency hashes, explicit conversion scale; staged originals are retained | Audit does not traverse native physics tables. The request carries no body/joint capsule. Original-source rehash after conversion does not independently establish a source-table witness or a native-copy-to-capsule join. |
| `tools/blender_mmd_bridge.py:21–92` | Renderable meshes, rig bone names/parents, morph category names, expression declarations, materials, tools/source identity; packed `editable.blend` before material approximation | Native MMD properties may survive in the external Blender intermediate. This is archival upstream state, without a verified portable native body/joint table. GLB uses approximated materials. |
| `tools/blender_mmd_bridge.py:121–173` | GLB skin/mesh/exportable morphs; root extras carry source format/SHA and morph-category names. Asset extras contain supported expression and IK metadata. Existing JSON-only insertion retains the exported binary tail | No rigid shapes, source body modes, mass/damping/friction/restitution, collision groups/masks, joint frames/limits/springs are captured into the GLB/report. Current `mmd_ik.capture` uses the installed decoded reader and unique-name joins; that is not a substitute for a raw native-index physics crosswalk. |
| `src/pose_editor.gd:200–213` | `parameters.json` is copied into `metadata.native_parameters`; `external_bundle` is a reminder, not portable ownership of that directory | Report limit256KiB. Copying a full2MiB raw capsule here would refuse the model. |
| `src/world_document.gd:72–87`, `src/storage.gd:243–284`, `tools/has_project.py:390–433` | Model metadata stays in the project; GLB is copied/content-addressed as one managed asset. A selected asset can be packaged through the existing `.has` asset package | Project metadata limit1MiB; GLB limit128MiB; container total512MiB. A loose capsule JSON file is not automatically a declared project asset. Neither an external path nor a new sidecar alone makes it portable. |
| `src/secondary_rig.gd:146–201`, `src/physics_rig.gd:128–175` | VRM/HAS helper spring adapter and shared HAS body rules; Source secondary has its own separately qualified adapter | No PMX body/joint adapter. Preserving new data must not enable PMX simulation or change import activation. Ordinary Add model can already start compatible shared ragdolls through explicit import intent; that existing behavior is not native PMX physics. |

The source reader now preserves more raw information than the current importer report. For PMX2.0 within its restricted profile it retains:

- Source SHA/length, header raw words, encoding and index widths; ordered section counts/count words/boundaries; exact encoded model/bone/body/joint names with their offsets.
- Native bone indices, positions, parents, flags/layers, conditional tail/grant/fixed/local axes/external-parent/IK declarations and raw references. Duplicate or empty names remain separate native indices.
- Native body indices, bone references including accepted `-1`, collision group, unsigned16-bit mask, shape/mode, size/location/Euler rotation, mass, velocity/rotation attenuation, bounce and friction.
- Native joint indices/mode, source/destination body references, location/Euler rotation, linear/angular lower and upper limits, and linear/angular springs.
- All captured binary32 words as exact little-endian hex, signedzero/subnormal/nonfinite payloads and explicit nonfinite positions. These are opaque declarations, not valid physical values.

It does **not** retain vertex/weight/UV/texture/material/morph/display payloads as a capsule; it only traverses their restricted layouts. Source SHA is not proof that the right tables were located. PMD, PMX2.1/soft bodies, QDEF and unsupported layouts remain outside this reader profile. There is no material-coverage, skin/IK validity, unit conversion, source-to-HAS bone join, physical validity or simulation qualification.

## Recommended ownership and location

Choose an **asset-owned inactive archive**, rather than duplicating native tables per scene instance. Proposed names below are a design choice, not a registered format:

1. Under a fresh owned preparation directory retain a canonical UTF8 capsule file and a private source/qualification receipt. Bind the admitted immutable source bytes, exact owned native copy and capsule by SHA. Keep source identity, raw tables and detailed receipts private.
2. After the existing bridge finishes, a new bounded pure-Python assembler can embed an envelope under `asset.extras.has_native_physics_archive`. The envelope carries its own version, capsule encoding, exact canonical capsule JSON **text**, and its SHA/byte length. Storing the exact text avoids an implicit Godot JSON decode/re-encode being treated as exact capsule-byte preservation. Measure the actual escaped GLB JSON size;2MiB decoded capsule is not a promise about envelope size or peak memory.
3. Keep only a small descriptor in `parameters.json`: archive format/location/digest, capture status, runtime support `false`, and a short warning. Do not place the full capsule, private original path, raw values, names or witness in that report. Bind the descriptor to the embedded text; reject a collision, mismatch or partial/truncated capsule.
4. Finalize the derived GLB hash before `Model.definition()` creates the new instance. Existing imported assets, authored poses and source originals are not rewritten. Geometry BIN tail, every unrelated typed JSON value and image bytes must remain exact. A new GLB checksum is expected for a new import; it is not the original source SHA.

`src/scene3d.gd:79–112` caps total GLB128MiB, checks the JSON length against remaining GLB bytes and parses all of it before Godot import. There is no smaller application JSON-chunk limit. Memory, import time, Godot's handling of a large inert asset extra, and decoded capsule/envelope budgets therefore need actual qualification; existing numerical caps alone do not prove capacity.

Source scan found no generic asset-info/extras-to-model copier in `src`. Current asset-extras consumers select `studio_expression_groups` (`expression_presets.gd:19–24`) and `studio_ik_constraints` (`scene3d.gd:155–157`); secondary parsing selects VRM/top-level HAS helper keys. `pose_editor.definition()` only copies the supplied report, and `world_runtime.snapshot():113–115` copies instance data. Application code therefore has no present path that copies this proposed asset-extra archive into project metadata. This is source evidence, not an observed Godot importer/peak-memory guarantee. Any future summary UI must use the bounded descriptor and must not dump/copy the whole envelope.

This design avoids requiring a new loose asset member solely for archival preservation. It remains a proposal until actual packed/linked/project/asset-package/cold-open tests prove exact retention. If the actual profile or budgets fail, refuse the requested capture with a clear reason; do not delete fields, shrink tables or silently report zero bodies. PMD/PMX2.1 and out-of-profile sources must remain explicitly `NOT_CAPTURED_UNSUPPORTED_PROFILE`, rather than obtaining a fabricated empty capsule. Existing conversion without an opt-in capture remains a separate supported route.

Default future preservation should be additive to an otherwise working import, with an explicit status when capture cannot be completed. A separate strict preservation request may refuse that request atomically; it must not silently replace or invalidate an existing model. The implementation must select and test this policy explicitly, rather than catching every parser failure as success.

| Situation | Truthful default import result | Strict preservation request |
|---|---|---|
| Existing PMD/PMX2.1/QDEF or another excluded layout | Existing conversion remains available: “Model imported. Original physics data could not be preserved for this format.” | Refuse requested preservation with the actual unsupported-profile reason. |
| Source/capsule/envelope too large for the preservation profile | Existing conversion can continue with “Model imported. Physics data was not preserved because it exceeds the current limit.” No truncation or empty-table claim. | Refuse requested preservation; do not raise caps automatically. |
| Invalid/truncated raw reader input or mismatched source identity | Preserve previous model, disclose failure; only the independently supported existing conversion route may be offered. Never hide a source-integrity failure as a successful capture. | Refuse atomically and retain failure evidence. |
| Nonfinite raw physics words within the qualified archival profile | Exact opaque words may be archived: “Physics data preserved; some source values need review. Native simulation is unsupported.” No float conversion or physical-validity pass. | Raw archival preservation can succeed if all capture gates pass; a finite simulation profile remains unqualified. |
| Capture intentionally not requested or native qualification unavailable | “Physics data was not captured. HAS's own physics remains available where supported.” Existing import behavior stays intact. | Request remains unavailable/refused until the exact qualification prerequisites are met. |

These messages describe owner-local asset data. Capsules, source identities, table details and private failure diagnostics are not public test evidence or material for generic UI dumps.

## Versions and compatibility

The raw reader format has `prototype` in its name. Do not silently rename/rewrite its payload or promote its qualification flag. Use a separately versioned archival envelope, with a separately recorded input/profile-specific witness if later earned. Imported, translated, inferred and artist-edited data need distinct ownership; this increment contains only raw imported declarations.

An inert optional archive is a candidate for keeping the current model/world/project/container versions because old readers can copy the unchanged GLB and ignore the extra. That is a hypothesis requiring actual old/current read/save checks, not a compatibility promise. Model versions1–9, current project schema wrappers through8 and container version1 have different responsibilities; no number is reserved here. Essential future runtime semantics must use explicit model/schema capability/version gates and an older-reader refusal, rather than relying on ignored extras. No new extension or source-format round-trip is selected.

## Native prerequisite and first runnable increment

Follow `experiments/pmx_native_read_qualification_protocol_20261117/PROTOCOL.md` before any production native capture. The protocol currently supplies no executable wrapper/oracle/comparator/runner. Required gates include a frozen independent raw-table oracle with independently authored fixtures; an exact typed comparator; exact immutable private source identity with read-only handles denying write/delete and reparse/identity/EOF checks; isolated pinned Python/import graph; bounded owned CPU job/time/memory/logs; private output routing and canary-tested public projection; and observed handle/process/job closure. The oracle must be sealed before the candidate result exists. MMD Tools' tolerant decoded result cannot replace that independent raw witness. Existing unqualified flags stay intact even after a separate input-specific witness.

The smallest **runnable source increment now** is an isolated synthetic CPU assembler/extractor: accept an authored capsule and tiny self-contained GLB; add the inactive envelope and bounded report descriptor; extract exact canonical text; prove unchanged BIN/unrelated JSON and refuse adversarial inputs. It can use the33-test reader as a regression dependency without loading any artist model, addon or engine. It must not call `prepare_mmd` on native inputs or wire the adapter into production before native admission.

After native qualification, the smallest owner-visible import increment is preservation plus a clear result such as **“Physics data preserved. Native simulation is unsupported.”** Counts/details can be shown only in a bounded local inspector explicitly designed for the owner; public evidence still follows the qualification protocol's stricter projection. No simulation toggle, automatic reconstruction or bone assignment follows from capture.

Concrete future source edits would be a new bounded archive helper, an opt-in call in `prepare_mmd.prepare()` after verified conversion and before returning its GLB, and a small report status/warning. Leave `physics_rig`, `secondary_rig`, `source_secondary`, model evaluation and scale normalization untouched. Preserve the current conversion report schema/kind and existing warnings; a separately versioned nested descriptor must not change `mmd_pose_import` assumptions.

## Meaningful verification for that increment

- Retain all33 current reader methods. Add exact independent authored expectations for every body/joint field, mixed-width references, duplicate Japanese/empty names, `-1`, mask32769/65535 and nonfinite/signedzero words; retain every unsupported/truncated/budget refusal. Never obtain expected native tables by slicing at candidate-returned offsets.
- Assembler/extractor tests: strict format/type/key/UTF/duplicate-key/size checks; capsule SHA/source SHA/source-copy mismatch; occupied extra key; missing/extra/reordered references; complete capsule byte equality after extraction; exact BIN/image/non-archive JSON preservation including signedzero and number types. Unknown metadata stays inert; no source-to-HAS crosswalk is manufactured.
- Budget/privacy tests: escaped envelope size, whole GLB128MiB, report256KiB and whole project1MiB boundaries;64 instances do not duplicate capsule payload in metadata; secret canaries never reach warnings/public projections. On refusal/cancel/save failure the previous project, originals and prior derived files remain unchanged.
- Later root-owned actual tests: native witness first, then existing MMD conversion parity; body/shape/helper/pose unchanged; no new native physics activation or keys; packed and linked saves, selected `.has` package, relocation/cold-open and old/current save preserve exact embedded text/SHA. Confirm zero loss of native groups/masks/body modes/frames/limits/springs. Observe resource and process closure. A native preservation pass still does not prove PMX simulation.

## Separate optional roadmap

Only later consider a source-index-to-export-node-to-HAS-ID crosswalk with duplicate-name negatives; finite physical-profile admission; explicit units/basis/scale transformations retaining original values; reviewed translation into HAS bodies/joints; runtime reference behavior; and editable Apply/Undo. Six-foot-at-user-scale1, cloth/soft-body solving, learned inference and reconstruction of missing MDL data remain separate inactive work. Current `scale=0.08` preparation is not the six-foot normalization contract. Do not multiply raw physics values or infer native units/frames as part of archival capture.

This packet records a plan and source evidence. It adds no native qualification, portable-capacity, compatibility, simulation, reconstruction or completion claim.
