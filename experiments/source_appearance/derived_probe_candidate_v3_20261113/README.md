# Derived SFM probe v3: CPU checked, runtime unrun

V3 is a new five-source harness candidate under `output/sfm-static-appearance-probe-20261113-v3/source`. It leaves v2, the archived earlier candidate, retained actual runs and model assets untouched. The synthetic CPU suite passes **57 tests, zero failures/errors**, preserving the exact five sources during the run. An independent read-only source review found no concrete blocker. No v3 preparation, Godot parse, graphical rendering, application run or native-fidelity acceptance occurred.

## Preserved actual v2 failure

Actual v2 writer `1794556016763092400-40301e3c9fe24f5a9c7441715f6268ba` remains **failed: 311 checks, one failure**, on Nitori's ordinary app-image positive-content check. Root measured nine significant samples against the unchanged requirement of more than 100. New starts with unshaded mode and black background; this fixture is a gloves-only component with an as-supplied opaque black glow layer. Keiki's ordinary app case completed, but the reader did not run. All eight raw capture cases completed with maximum geometry error `6.003679686727992e-7`, below the unchanged `0.0002` threshold. Tools weights, box pose and hand pose changed pixels. These results do not establish native Source appearance fidelity or v2 application acceptance.

The v2 raw log contains 406 copies of one exact verbose importer diagnostic. Retrospective classification is recorded only to characterize that log, and does not turn the failed v2 run into an accepted run. The earlier relative-manifest attempt also remains failed and retained. `PRESERVED-V2-FAILURE.json` records the compact actual observations and labels machine-local folders explicitly.

## Bounded v3 changes

- After ordinary New and before the world/import history baseline, select **Studio light** through `lighting_choice.select(2)` and `change_lighting(2)`. Check the default New state, named selector, video setting, live renderer/light and separate video history step. Packed Open must retain the exact writer video and the explicit Studio setting. The same captured image still must exceed 100 samples at RGB contrast above 0.02; exact writer/reader pixels remain required. All model materials and the glow overlay remain unchanged.
- Compute and bind an independent byte-layout proof for every actual GLB during preparation, recompute it during preflight, and recompute again against exact current owned input bytes before classifying logs. Only the exact known verbose line is classified after all twelve proofs pass. Its count and original line numbers remain in receipts, and raw logs remain untouched. All other warning/error/failure/leak markers and lookalikes still reject the run.
- Normalize a supplied manifest argument to an absolute path once before its first preflight or launch. Early GDScript checks reject missing/relative manifest paths, malformed v3 identity, wrong argument count and invalid output/mode immediately instead of waiting for the watchdog.

The new manifest format is `has_sfm_derived_probe_candidate_3`. Fresh preparation at the final reviewed forty-character commit is mandatory. Existing v1/v2 manifests, private source copies, failed attempts and working-tree preparations are historical evidence, not reusable execution context.

## Independent layout boundary

`GLB.layout_proof()` derives roles from mesh attributes/morphs, indices, skins, animation samplers and images. It checks component/vertex alignment, accessor bounds, typed element sizes, targets, stride range/alignment/roles, and sparse payload roles/bounds/ordered in-range indices through the independent decoder. Multiple distinct vertex accessors sharing a view require declared stride; a sole packed vertex accessor uses its element size. Sparse index/value views forbid stride and target. Mixed roles, unknown binary extensions, unsupported matrix component packing and unsupported attribute formats refuse. This is a bounded layout proof for these fixtures, not complete glTF conformance certification.

All twelve retained derived GLBs passed a read-only CPU layout inspection. Nitori's four bundles each contain four sparse accessors. Packed vertex view counts range from five to 22; all actual vertex views have a single accessor and no declared stride. Their metadata-only proofs and pre/post original/source identities are in `ACTUAL12-LAYOUT-PROOF.json`; no raw vertices, images, model bytes or native assets are included.

The published [Khronos glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html), sections 3.6.1 and 3.6.2.4, permits packed single-accessor views and requires explicit stride for shared vertex accessor views. See also the [primary AsciiDoc role/stride rules](https://raw.githubusercontent.com/KhronosGroup/glTF/main/specification/2.0/Specification.adoc). The [Godot 4.6 importer](https://raw.githubusercontent.com/godotengine/godot/4.6-stable/modules/gltf/structures/gltf_accessor.cpp) emits this diagnostic through `print_verbose` whenever a vertex view lacks declared stride, then reads packed bytes. Full role/extent proof, rather than absence of an engine error, is the gate for this one diagnostic.

## Future root-owned execution

Root reviews this packet, publishes/checkpoints it as appropriate, then prepares a fresh v3 manifest at the selected stable commit using the approved Python. Default preflight must pass. Godot parsing or actual graphics require root's explicit runtime authorization and exclusive lease. The private wrapper, exact pinned interpreters, unique profiles, strict desktop receipts, all final preservation gates and stop-on-unexpected-failure policy remain intact.

The eight raw cases and two ordinary app cases are unchanged. Native shaders, additive glow, original flex/controller evaluation and runtime jiggle remain outside this derived render/adoption proof. Separate partial native-geometry oracle results retain their own successes and refusals. Broader 82-MDL extra-feature coverage remains planned; these two representative models do not replace that inventory.
