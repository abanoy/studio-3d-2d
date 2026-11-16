# Minimum actual probe for the unresolved Source normals

The original native-normal result remains **FAILED / UNQUALIFIED** at the unchanged Euclidean vector-distance gate `2e-5`. The already measured maximum is `0.00121654672362075`, with `8364/9661` above the gate. This plan creates no new normal measurement, executes no prepared probe, and changes no acceptance status. It advances the open IMPORT-03 investigation without treating existing position, skeleton, dynamics or GUI successes as normal fidelity.

The discrepancy already exists in **native VVD → raw emitted GLB**. The independent reader parses float32 VVD normals at record offset28, applies the direction-only map `C(x,y,z)=(x,z,-y)`, and compares directly with the GLB binary `NORMAL` accessor. It does not import the GLB into Godot. Consequently, a Godot normal import/render change cannot cause or fix that recorded raw-export error. Godot/HAS posed normals and rendered/artist appearance remain separate unmeasured domains.

| Boundary | Existing evidence | Remaining uncertainty |
| --- | --- | --- |
| Native VVD float32 → selected native witness | 9661 consumed once; complete position/weight/UV-compatible multiset coverage;4 repeated-attribute ambiguities | No unique native-index identity for repeated attributes; native matching includes a nearest-normal tie break |
| Native normal length | Maximum length error `2.1082098933256077e-7`; unit normalization fixes0 failed rows | Packed/SDK normal compression is not a valid explanation for these directly read float32 records |
| Native → hypothetical round4/normalize export | 7966 predictions within `2e-7`; maximum prediction residual `0.0012081099462259133` | Round4 alone cannot explain the maximum: recorded unit-vector bound is about `0.0001732051` |
| Saved Blender corner normal → reconstructed exporter → original GLB | Prepared capture and comparison sources only; runtime UNRUN | Actual saved corner values, candidate coherence and boundary errors have not been observed |
| Blender custom-normal encoding/decoding | Pinned official-source provenance describes short2 fan-space storage/approximate angle calculation | Candidate cause only; no original setter payload or exact encoder reproduction |
| Raw GLB → Godot/HAS/render | Not part of the failed raw comparison | Still requires separate qualification after the earlier boundary is understood |

The old initial instrumentation used a stale last-candidate normal and is invalid. The saved diagnostic selects `source_vertices[vi]` and checks agreement with the selected stored error. Keep that invalid attempt and the original failed strict gate classified as they are.

## Run the smallest existing probe later

Reuse these exact prepared files, rather than starting a new conversion or installing anything:

1. `experiments/resume_coordinates_20261115/capture_blender_normals_UNRUN.py` — load a copy of the retained **pre-export** `editable.blend`; read visible mesh `obj.data.corner_normals`, geometry/weights/UV metadata privately; reconstruct the installed exporter's normal stages. It does not invoke SourceIO, export a GLB, save a blend or explicitly evaluate a depsgraph.
2. `experiments/resume_coordinates_20261115/compare_private_normals_UNRUN.py` — stdlib analysis joining that private capture to the unchanged qualified native VVD and original raw GLB. It writes aggregate counts, errors and hashes only.

The existing source bridge saves `editable.blend` after view-layer update and before visible-object export selection. Its retained copy omits an explicit `export_apply` override; the inspected approved exporter defaults that option to false and uses `blender_object.data` on that route. This supports inspecting saved `obj.data` first. It does not prove the original evaluated mesh or in-process setter state: the exporter also validates mesh data, and the capture does not execute that path. A mismatch must be diagnosed, not assigned to the importer by assumption.

The hash-only local inspection in `INPUT_METADATA.json` confirms the retained files still exist and match the earlier qualified input identities. It also pins the2.42MB saved blend and current approved Blender/exporter/SourceIO source bytes. No native array was printed or retained in this plan. The original prepared packet has only AST checks for its capture/comparison; this plan did not turn those into Blender runtime tests.

Root execution prerequisites are already enforced by the prepared capture: a fresh complete-default **PASS**, authoritative closure, exact current HEAD, future lease expiry, no private-array publishing, and a fresh output directory. The failed dbf full and the later scoped shutdown PASS do not satisfy that complete-default requirement. This is a future root-owned runtime action, not a new owner/manual request. Do not create a lease or mark the probe run from this plan.

The lease format is `has_blender_normal_probe_lease_1`, phase `ROOT_APPROVED_AFTER_FULL_PASS`. Its exact12 locks are `blend`, `mdl`, `vvd`, `glb`, `parameters`, `blender_exe`, `probe`, `exporter_extract`, `exporter_constants`, `sourceio_import`, `full_receipt`, `closure_receipt`. Root must inspect the full/closure receipts and current source/process state independently; the prepared capture checks their locked hashes but does not independently interpret receipt contents. Point the blend lock at an owned copy with the same pinned SHA, keep the source/original locked and unchanged, and use the current root-authorized post-PASS receipts/HEAD/expiry.

Use the existing hidden private-desktop execution policy, retained process identity and bounded runtime management. The planned Blender argument order is `--background --factory-startup --offline-mode --disable-autoexec <owned-copy.blend> --python-exit-code 1 --python <prepared-capture.py> -- --lease <root-lease.json>`; flags must disable file auto-execution before the blend loads. The approved preparation tool already uses offline and Python-exception exit flags. Require both an actual exit0 and the expected capture artifact/status; exit0 alone must not stand in for a completed probe. Root chooses a bounded timeout and records it before launch; this preparation invents no runtime PID, timing or exit result. Keep stdout/stderr/private receipt, actual exit and reaping, input hashes before/after, and authoritative root closure. A headless/background argument by itself is not a substitute for the private-desktop requirement.

Stage the copied blend and lease in an owned private `output/<run>/inputs` directory. Give capture a separately fresh `output/<run>/capture` path (its parent must already exist; the target must not). Keep `PRIVATE_NORMALS.json` there. `PUBLIC_CAPTURE.json` publishes counts and hashes only. Run the existing comparator from the checkout root with `--private <capture/PRIVATE_NORMALS.json>` and a fresh `--output` **inside `experiments/resume_coordinates_20261115`**, as required by its existing path guard. Later copy only the reviewed aggregate result into a public actual-evidence packet; do not copy the private arrays or blend.

## Check coherence before interpreting cause

The expected profile is2 exported visible meshes,4 original GLB primitives,9661 exported vertices, all69 native bones and no native flex names/controllers. The capture currently allows up to32 visible meshes and does not hard-assert that exact profile. Root must check the observed counts and complete original4-primitive correspondence before interpreting boundary statistics. Corner count can exceed vertex count because vertices participate in multiple faces; that is not extra exported geometry by itself.

The comparator's `COHERENT_BOUNDARY_MEASUREMENT` means **zero unmatched exported vertices, complete9661 witnesses and maximum reconstructed-exporter prediction error below `2e-6`**. This is a pipeline-coherence condition, separate from the unchanged native normal `2e-5` fidelity gate. An incoherent measurement must stay `BOUNDARY_PREDICTION_OR_MATCH_FAILED`. The sources themselves are UNRUN; any Blender RNA/API/UV/morph/transform refusal is evidence to preserve, not permission to skip a check.

The Blender-corner match is also a witness relation: it selects the nearest predicted normal among position/weight/UV-compatible corners, does not consume corner IDs, and reports multiple candidates. It can understate a difference across alternate corners. The existing comparator is sufficient for exploratory localization, but cannot prove unique corner attribution. If a causal decision depends on ambiguous rows, a separately reviewed successor should report unique normal-equivalence classes and best/worst residuals across **all** compatible candidates; it must preserve the original matching/error gates and public aggregate-only output. No such successor is implemented or executed here.

| Later observation | Valid next conclusion/action |
| --- | --- |
| Export prediction coherent; native→stored Blender reproduces the large residual | Difference is already present by the saved Blender snapshot. Next inspect the SourceIO normal setter/custom-normal storage boundary with an explicit in-memory setter trace. This does not yet prove short2 quantization specifically. |
| Native→stored Blender is small; stored→GLB differs and exporter prediction is coherent | Investigate the measured rounding/normal-transform path per row. The recorded round4 bound cannot explain the historical0.0012165 maximum alone; check that the same maximum row/domain and all ambiguity cases are covered. |
| Prediction not coherent or correspondence incomplete | Investigate saved-versus-exported mesh, selection/UV/weight domains, original settings/validation or candidate ambiguity. Do not claim a native importer cause or widen either threshold. |
| Saved Blender route does not expose the required custom-normal payload | Preserve that limitation. A subsequent root-reviewed scratch setter/exporter instrumentation may be needed; it is not already-qualified evidence. |
| Raw normal fidelity still fails after localization | Keep IMPORT-03 partial and the strict native gate FAILED; plan the bounded source fix and fresh exact-input qualification separately. |

A second actual conversion scale, posed/GPU normals, native shaders/artist comparison and broad importer fidelity remain separate gates. No media, native geometry, normals, rest arrays, oracle arrays or complete tool source trees belong in this notes packet.

`PROVENANCE.json` records the inspected source/record identities and relevant line anchors. `INDEX.json` seals this notes/probe-plan packet. All work here was read-only source/metadata inspection and hashing, plus these experiment notes; no engine, CIM/process query, Git command, network, installed-tool change, core edit or normal-gate rerun occurred.
