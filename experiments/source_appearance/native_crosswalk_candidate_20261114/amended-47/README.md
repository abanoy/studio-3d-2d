# Output-only crosswalk amendment: selected scenes and complete GLB reconciliation

This is a **new output-only candidate**, preserving the frozen30CPU packet at
`output/source-jiggle-crosswalk-draft/20261114T0155`. Nothing was ported to main.
No production source, project documentation, HEAD, installed source/runtime or
native asset was changed. No Blender, SourceIO, Godot, GPU or native conversion
was imported or executed. All actual-runtime and adoption qualification remains
**UNRUN**.

The inherited restricted admission is unchanged: the normal profile is the exact
JunkoHair SHA `8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716`,
69complete native bones, injective short ASCII keys inside the pinned SourceIO
factory, raw native rest-word/parent checks, data/PoseBone owners/pointers and
complete rest-matrix proof. Tests use a separate authored three-bone profile.
The baseline README documents its14source pins, operator keywords/settings and
defaults. `SOURCE_AUDIT.json` is a byte-exact copy of that read-only source audit;
it is provenance from that observation, not a fresh runtime qualification.

## Findings addressed

Independent review demonstrated that the old `finish()` compared nodes/skins
without the selected `scene`, `scenes`, or reachability. Removing scene roots
could therefore leave the same observed crosswalk accepted. Review also found
unvalidated trailing GLB chunk bytes, unresolved/replaced mesh definitions, and
the need to observe independent exporter callback lists and rest during export.
Those are candidate findings; they are not failures in the currently verified
Studio feature, which does not use this candidate.

The amended code now:

- Captures the exact selected-scene index and all flat scene dictionaries at the
  late hook. It admits1–128scenes with a valid integer selected index, finite node
  domains, valid unique root references, no root that is already a child, unique
  parents and no cycles anywhere. Cycle traversal is iterative, including
  unreachable components.
- Requires the proven armature object and every mapped native joint to be
  reachable from the **selected** scene. Every admitted skin must have at least
  one reachable skinned mesh node; presence only in a nonselected scene cannot
  satisfy this gate. The normal selected-scene export is still an actual-runtime
  qualification target; bounded multiple-scene behavior is authored-only evidence.
- Requires mesh references to resolve in the flat mesh array. Target mesh
  primitives must retain POSITION/JOINTS_0/WEIGHTS_0 attribute-reference domains.
  It snapshots all mesh definitions and rejects removed/replaced final meshes.
  This does not validate accessor binary data or establish weighted deformation.
- Walks the complete GLB container to exact EOF: aligned bounded JSON first and
  at most one optional aligned BIN chunk. Incomplete/trailing bytes, duplicate
  JSON, unknown chunks and truncated/unaligned payloads refuse this narrow proof.
- Reconciles the final GLB's exact selected scene, scenes, nodes, skins and meshes
  against immutable late-hook snapshots, binding the result to the final GLB SHA.
  No partial row list is published.
- Adds `pre_export_hook(export_settings)` beside the three identity hooks. It
  latches nonempty pre/post callback lists or other export extensions before the
  exporter's callback loop, and rechecks native/Blender rest there, at the late
  hook and at `finish()`. It also rechecks callback/extension admission late.
  The installed dispatcher catches hooks: latching refuses the optional proof;
  it does **not** claim to abort the exporter or prevent callback code execution.
- Mirrors the pinned exporter's two JSON-cleanup passes for the observed
  structures. The nested `{'extensions':{'unused':{}}}` case removes the outer
  empty extension on the second pass. This is exactly two passes, not an
  arbitrary fixed-point cleanup. Extras remainfalse and no object is edited.

Scene-container SHA, selected roots and reachable target skin mesh-node records
are added to the inactive report. Source/Blender/native parent/rest identities
remain separate. HAS runtime binding remains `unattempted`; simulation remains
false. Standalone proof budget remains128KiB. Future integration must measure the
entire final nested256KiB report with the already retained native values present;
native values have priority and the complete optional proof must be omitted with
an explicit bounded reason if it does not fit. Never append after a prior budget
measurement or silently displace native values.

## CPU evidence and preservation

`cpu-attempt1.log` passes **47tests,0failures,0errors** with approved Python3.13
and `-B`. This amendment's first executed CPU attempt passed. The old packet's
earlier14-error JSON-order attempt and corrected30-pass evidence remain untouched
in that packet and are not relabeled as amended results.

`BASELINE_METHODS.json` independently compares function ASTs: all original30test
methods are byte-for-byte equivalent at AST level. Only shared authored fixtures
were enriched with real scene/mesh shapes and the additional preflight call.
The17added methods cover selected scene1, removed/changed roots and selected
indices, missing containers, nonselected unreachable targets, invalid roots,
unreachable cycles, immutable scene snapshots, missing/replaced meshes, target
skin attributes, a valid optional BIN, trailing1–7bytes, duplicate/truncated/
unknown/unaligned chunks, callback/extension admission, mutation restored after
the late hook and two-pass nested-empty normalization.

The frozen baseline module SHA remains
`1287d04e15bd7d8ee20b6eea137b820c68849aa7df2d2daf22502ccb0f213b81`;
its test SHA remains
`72d2dcfce34890b16f1062de835f236291a89b114912a87b2e8d874192d03913`.
`INDEX.json` binds this amendment's payload files and review record.

## Actual qualification still required

Actual pinned Blender callback discovery/order, flat Scene/Mesh/Node/Skin object
types and their final two-pass serialization are **UNRUN**. Actual Junko69-bone
rest/factory/export proof, unchanged geometry/material/weight fingerprints, bridge
integration, final combined report admission, Godot `has_source_bones` join,
Studio adoption, packed/linked/cold persistence, motion, fan behavior and native
fidelity are all **UNRUN**. Neither these mocks nor source inspection substitute
for those separately owned runtime checks after the current lease ends.

No models, media, runtime binaries or private artwork are included.
