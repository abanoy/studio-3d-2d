# Frozen chain packet: preregistered counts and staging audit

Source-only audit. No Godot parser/runtime, GPU, process inspection or Git command was run. Every file listed by the original frozen `INDEX.json` remains byte-identical; the index itself remains `5f204a52d82a61174da1dbb33da3c132f636b5d8bc5eba39f7679279599782c0`. Only these new audit notes were added.

## Exact successful-path counts

`math_checks.gd`: **4,012 assertions**, from5 independent first-step vector checks,7 other initial/alias/refusal checks, then1,000 tilted zero-cone cases×2bones×2vector assertions =4,000. It completes1,002 actor steps/2,004 rule evaluations across1,001 actor objects. Three deliberately refused calls do not advance the clock. Any early returned error, missing count, non-PASS status or nonempty failure array must fail root verification.

`chain_harness.gd`: **21,087 assertions**,12 result rows,1,440 actor ticks and5,760 rule evaluations.

| Successful-path term | Count |
| --- | ---: |
| Per profile: all69 authored FK frames |69 |
| Per profile:120ticks×(4rules×3orientation/origin/tip checks+2unselected/authored checks) |1,680 |
| Per profile: final unaffected weighted region |1 |
| Per profile: Off frame24, Off frame12, all weighted restoration, current inactive binding |4 |
| Additional checks for each nonzero profile: two pair motion checks |2 |
| Control profile total |1,754 |
| Each nonzero profile total |1,756 |
| Six profiles/root: control+5nonzero |10,534 |
| Additional/root:4input profiles×2pairs, plus exact repeat |9 |
| One root case |10,543 |
| Two roots, then final source preservation |21,087 |

The inherited `check()` method increments once per invocation. The inherited `_initialize()` dynamically calls the overridden child `run()`. Child `run`, `root_case`, `owned_pose` and `finish` replace their parent bodies; the old native8 simulation and old parent finish do not add assertions. The child finish calls the inherited check method once. Import-context helpers, snapshot helpers, `source_unchanged`, boundary conversion and captures return values without hidden check increments. Failure branches can produce smaller counts and remain failed attempts.

There are54 CPU weighted captures in a complete native run:27/root (one union baseline+two pair baselines+six profiles×four captures). Static count guards/refusals are gates, not additional `check()` calls.

## Staging guidance

For a first synthetic math attempt, stage only the exact qualified `leaf_candidate.gd`, frozen `chain_solver.gd` and `math_checks.gd`. Use a root-owned tiny `SceneTree` wrapper to preload the check object and call `new().run()`. `math_checks.gd` extends RefCounted, so it is not itself a direct MainLoop entry for `--script`. Require exact4,012 checks and empty failures; retain the first actual parse/runtime observation unchanged.

For the native attempt, stage eight dependency files: qualified `leaf_candidate.gd`, `leaf_adapter.gd`, `weighted_capture.gd`, `leaf_harness.gd`, plus this packet's `chain_solver.gd`, `model_adapter.gd`, `chain_capture.gd`, `chain_harness.gd`. Use `chain_harness.gd` as the script entry. A separately staged `math_checks.gd` is optional for that native entry.

The frozen ready lease is an unapproved template. Create a **new reviewed source lock and new lease** for current production bytes; preserve the packet's earlier lock. Bind the approved engine, fresh aggregate result, full/FK/math/leaf proof receipts and authoritative closure. The exact pinned GLB must retain its adjacent parameters report. Native MDL/VVD remain read-only. The inherited guard runs via native17(parent7); the bridge separately verifies native26(parent25).

## Source review limits

No obvious parent/child constant or member collision, override-signature mismatch, preload cycle, global class registration, or direct material mutation was found. All inferred Dictionary-derived types remain unparsed, so actual first parse is authoritative.

The new bridge's accumulated69-bone scalar FK correction remains unmeasured. Its baseline gates can legitimately refuse; retain that result and investigate rather than relax2e-5. Strict1e-9 scalar basis validation follows the qualified float32 adapter. Only positive uniform scale and the fixed Model base-scale contract are admitted. Native25 remains authored/unsimulated, so this is a four-rule subset.

CPU capture checks actual Skin/mesh arrays, preserves mesh/material-related array identity, and hashes weighted positions held in RAM. It does not establish shader/material appearance, normals or GPU fidelity. The historical normal-fidelity2e-5 failure remains failed. No SDK-client traversal, artist motion, body/fan/Record/HAS or full native49-rule qualification is implied.
