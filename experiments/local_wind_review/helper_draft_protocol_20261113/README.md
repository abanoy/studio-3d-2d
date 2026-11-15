# Helper-before-Apply Wind Preview: bounded protocol candidate

This output-only increment supplies a **hidden candidate preparation protocol**, not a working helper-window wind feature. It changes no main/prototype source, Git state, installed application or original input. It starts no Godot, GPU, Blender, native converter or external helper process. Tests call the existing pure Python helper builders in-process on tiny self-authored GLBs only.

`candidate/tools/wind_helper_preview.py` is reviewable incremental source. It uses the current `secondary_helpers_batch.plan/build` for both one focused request and multiple checked setup requests; those functions in turn use the existing single helper builder. There is no replacement rigging algorithm. No code in this candidate calls install, managed_copy, restore_world, Apply, Undo, app physics or any application object.

Implemented in this candidate:

- Fresh private job envelope, generation, random nonce, original source SHA/size/full nanosecond stamp, exact raw request-file digest and bounded original actor/context identities. Object IDs and timestamps use strings to avoid JSON float precision loss.
- One complete normalized reviewed shape choice across all setup items. The builder receives all setup membership, independent of temporary wind choices. Precise corrected points/patches remain in deep-copied requests; source SHA rebasing occurs only inside the existing batch composer.
- Complete private candidate build followed by GLB-level proof of retained original node indexes/local transforms/parents, skin joint order/inverse binds and existing declarations. Reports are matched to each reviewed region and the existing builder's request-derived node/declaration identity, then map through explicit configured source nodes and created candidate nodes. Each operation records the matching report digest. Reordered report lists remain correctly mapped; foreign helper nodes are refused. These generated request-hash identifiers are not user-facing labels, and future imported group assignment must use actual source-node sequences, not names.
- Atomic hidden-only receipt, candidate identity, separate bounded binding proof and full generation/request/context/source agreement before admission. Build returns a separate in-memory completion containing the **exact full receipt digest**, generation, nonce and request digest. Admission requires that trusted completion; isolated or coordinated file mutations (including reports/setup counts) are refused against it. No success receipt is published on a partial build failure.
- A small CPU reference `DraftLease` state machine: stopped → building → prepared_hidden, synchronous invalidation, late-result refusal and no automatic render admission. It deliberately does not remove jobs or kill PIDs. Cancellation can leave an old worker publishing only into its own private folder; that result cannot be accepted by a later generation.
- A pure second-gate `imported_binding_map` predicate for future actual-Godot binding snapshots. Keys are original source-node indexes. It permits explicit imported ID remapping while requiring the same binding kinds/full base transforms and no aliased bone/node identities. Offset bindings may legitimately share their parent bone ID.

Actual CPU results are in `cpu-tests.json` and `cpu-tests.log`: **21 tests,0failures,0errors,0skips**. They import this new module and exercise real existing builders on controlled geometry. Cases include focused corrected points, disjoint batch, VRM0/1-style authored declarations, deduplicated shared existing joints, post-cancel publication, stale generation/context/raw bytes/ns-stamp, candidate/proof/path/mapping tampering, reordered/foreign reports, receipt-report/count/bool-generation edits, coordinated file edits, partial second-builder failure, retained bind changes and imported-table alias/rest refusal.

The trusted completion is an explicit boundary, not an authenticated filesystem. The future owned-worker adapter must capture the completion from its own successful worker result/pipe; computing the expected hash from the editable receipt immediately before admission defeats the check. A hostile actor controlling both completion transport and files is outside this protocol's integrity claim. That transport is not implemented here. The pure imported-binding predicate checks consistency of supplied complete tables; it does not discover missing snapshot coverage or prove those tables came from Godot.

An expanded shared-chain fixture initially gave its disconnected patch only the tip joint; the backend correctly refused calling that a complete unconfigured linear chain. The authored fixture was corrected to carry all chain influences, matching the existing shared-chain regression. The protocol/backend predicates were retained. Failed log/JSON are kept as `cpu-shared-fixture-failure.*`.

Independent read-only review found that the first candidate trusted editable receipt fields and paired reports positionally. The frozen candidate adds the trusted completion digest and request/candidate-chain association checks above, with direct positive/negative CPU controls. The reviewer reread those changes and found no new blocker; no renderer acceptance follows from that review.

**Not implemented or accepted here:** worker process ownership/polling, a Godot draft context/ticket, helper UI controls, non-freezing helper Open, actual GLTF import/binding snapshots, derived candidate group catalogue, original/live-pose transfer, primary overlap checks, canvas/pointer handoff, recovery/final capture hooks, main-view simulation, or Apply guarding. Consequently, no renderer/native/artist acceptance is claimed. The pure imported-table predicate is not an actual import observation. See `INTEGRATION_DESIGN.md` for the smallest concrete next increment and its gates.

The phase1 local-wind implementation and its current canvas cleanup remain authoritative. This candidate does not alter permanent exclusions, native Source jiggle, lighting, Discovery or body/asset schemas.

The CPU API sequence is `ticket = lease.begin(...)`, `prepared = build_candidate(ticket['job'], owned_root)`, then `lease.accept(current_context, prepared['completion'])`. A real adapter runs the middle step in one owned worker and transports its completion separately. Accepted state stays `prepared_hidden`; this module has no method that turns rendering or simulation on.

Reproduce CPU checks from the current source checkout:

```powershell
python -B output/wind-helper-draft-prototype-20261113/tests/test_preview_protocol.py
```

The tests use this checkout's `tools/secondary_helpers*.py` and existing authored fixture builders; no private cache or model is required. Keep their source hashes with the result. Publish only the compact source/design/test/receipt index, not generated `cpu-results/*` GLBs or synthetic private job folders.
