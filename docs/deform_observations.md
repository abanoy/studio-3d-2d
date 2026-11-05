# Observed deform regions — development backend

`tools/shape_observations.py` compares every positional target with its neutral
mesh, then offers tentative same-model region matches from explicit labelled
seeds. This is a tested read-only backend, **not automatic editor classification
or a cross-model trained classifier**. Development now offers an
[Advanced study/review action](shape_study.md) with explicit adoption into the
existing manual catalogue. This develops the owner's request to observe deformations first.

Run `python tools/shape_observations.py model.glb new-report.json --seeds seeds.json`.
Omit seeds for measurements alone. It creates a new report, refuses overwrite,
and verifies source SHA afterwards. No conversion, source writes, external app,
upload, package installation or format exporter. Tests:
`python tests/test_shape_observations.py` (12tests, including cancellation); existing catalogue regression:
`python tests/verify_shape_catalog.py` through private Windows desktops.

## Evidence and interpretation

Each target retains exact node/mesh/target/native-name identity. Positive1 and
negative1 are independently added to the SAME neutral positions, with every other
weight zero. Reports contain changed-vertex count/mask SHA, affected bounds and
centroid, positive displacement mean/maximum and signed position bounds. This
follows [glTF positional delta semantics](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#meshes-morph-targets).
Signed mathematical probes do not declare a native control's permitted range.
The existing decoder handles dense/strided/sparse POSITION data.

Coordinates are per-node neutral mesh-local, not posed/head-normalized. Vertex
identities from different nodes never mix, including instances sharing a mesh.
Unsupported sparse base geometry refuses; nonposition-only controls are marked
unsupported, not unchanged. Other morph attributes are explicitly unevaluated.
Bone/material/UV/Source rule/ramp/stereo/delay/corrective semantics and emotes
remain open. Matching a region does not establish emotion or whole-face intent.

Seed JSON: `studio_deform_seeds_1`, exact `source_sha256`, and `controls` entries
with integer `node`/`target`, exact `native_name`, catalogue `area`, and explicit
`provenance`: Name estimate, Manual choice or Provisional observed annotation.
Missing/stale/duplicate identities refuse. Python never silently derives seeds
from names. The sample harness uses the actual shared `ShapeCatalog.estimate`;
one Miku brow seed uses a prior provisional observation, not artist certification.

Changed masks use mesh diagonal times1e-6 (floor1e-10). Binary-mask cosine scores
compare labelled controls on the SAME node, always excluding the query itself.
Tentative matching requires similarity>=.65, query coverage>=.7 and a .15 lead;
more than25% overlap with a second labelled area withholds the guess. These are
provisional cutoffs, not calibrated probabilities. Scores/seed IDs/provenance/
refusal reasons stay visible in the report. Explicit editor adoption is now
available through the shared catalogue; no silent inference installation.

Bounds:128MiBGLB/16MiBJSON, existing100kvertices/primitive,500kvertices/node,
2048targets/node,4096targets/study,64million vertex-target comparisons. No pruning
or partial-success report on overflow. Future UI integration needs worker lifecycle,
cancellation, review, cache identity and saved manual adoption. No hostile-parser
or general latency certification. Reports are private model-derived data; do not
bundle them in the public web preview or commit them as sample assets.

## Actual six-asset pass

Final `output/shape-observation-samples-v2.json` points to immutable unique reports
in `output/shape-observations/1793585548183587600`. Six original GLB SHA/mtime
unchanged:844targets,1688signed probes,7,980,914vertex-target comparisons.

| Prepared source | Targets | Explicit weak seeds | Unlabelled tentative matches |
| --- | ---: | ---: | ---: |
| Miku PMD | 15 | 7 | 8 |
| GMod Reimu | 52 | 50 | 0 |
| SFM Scout | 520 | 448 | 28 |
| VRM1 | 57 | 14 | 0 |
| VRM0 | 57 | 14 | 0 |
| Supplied Mima head | 143 | 103 | 38 |

646total matches include572labelled controls evaluated without their own seed;
all572agree with other **weak labels** here. This is consistency, not independent
accuracy. VRM0/1 are the same character; duplicate/related/corrective geometry also
precludes inflated generalization claims. Miku13predictions agree with13of15prior
provisional annotations,2unassigned; not artist-certified. Nonfacial matching has
authored tests, not broad real hair/cloth/prop validation. Nine native SFM delta
probes remain separate. Source study times about.4/.5/10.6/4.8/4.2/1.7seconds are
fixture measurements, not app latency, comparative speed or all-model guarantees.

## Bug found by observations

Initial evidence retained in `output/shape-observation-samples.json`: Scout's
`CloseLidUpL` incorrectly matched Brows through the weak compound seed
`BrowOutV_CloseLidUpL`. The shared name parser did not split CamelCase and skipped
all eye clues once it saw brow. It now splits ASCII CamelCase/acronym boundaries,
preserving original names/IDs. `OpenJaw` becomes Mouth, `CloseLidUpL` Eyes; brow+
lid/squint compounds stay Other. Literal Eye brows still means Brows. The geometric
query now withholds that mixed-region inference; its direct name estimate is Eyes.
Existing saved manual assignments retain authority. This is development source.

Fresh final regression:29unit/112app/5cold=146checks/0, authored plus all six assets,
two clean private GPU receipts, packed/linked HAS, exact Undo/Redo/native metadata
and own movie pixels. Actual H2641920x1080/24fps/48frames/2s. No new full suite or
normal installation. Frozen900check review and web site predate this parser change;
their artifacts remain unchanged, not reused as new proof.
Three new real Scout UI checks require its eyelid in Eyes, absent from Brows,
and its mixed brow/eyelid control in Other; the actual Eyes-filter image was
inspected. Earlier29/109/5passed before these added assertions and is retained.

Retained setup failures: first harness read Japanese UTF8 seed JSON as cp1252 and
exited before probing; explicit UTF8 fixed it. A read-only stdout inspection also
hit cp1252; escaped JSON fixed inspection. Initial10tests preceded the extra
unevaluated-attribute case; final11pass. No budget/assertion/tolerance relaxed.

Next visual before/after review and more independent native/nonfacial labels.
The new cancellable study/review action has explicit adoption into the shared catalogue.
Keep unknowns/manual overrides, native semantics and family-separated validation.
The full face-editor and MD/addendum goals remain unfinished.

Mima supplied three concrete speech-control aliases. In the retained v2 study,
"ah 1" moved 1,084 vertices and matched the changed region of "KK Mouth_uresi_ss_op"
with similarity .995. "ah 2" moved 1,149 and matched "disgusted tongue out" at
.982. "EEEE" moved 1,061 and matched "KK Mouth_e_s_op" at 1.000 rounded.
These are within-model region similarities against weak name seeds. The catalogue
uses only these exact normalized spellings as provisional Mouth name estimates.
Generic smile and surprise controls may affect more than the mouth and are not
inferred from these three cases. Manual assignments still take priority.
