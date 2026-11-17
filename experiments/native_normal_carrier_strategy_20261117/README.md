# Exact native normal identity carrier — source strategy and CPU prototype

This packet contains source research, a synthetic correction prototype and aggregate read-only fixture observations. It has **not exported or corrected a native GLB**, run Blender/Win32/CIM/Git or changed application/candidate/installed source. The original raw-normal failure remains **FAILED_UNQUALIFIED**. The prototype's result is always `CANDIDATE_DERIVATIVE_UNQUALIFIED`; it is not a qualified repair.

## What the actual setter observation established

The parent's successful isolated setter run retained exact original VVD float32 words at the SourceIO setter input. Immediate Blender readback differed in 6,846/34,332 hair corners (maximum 0.0007408270) and 2,130/8,370 hat corners (maximum 0.0012586271). Before/after `validate()` hashes were identical; the untouched control was word-identical to the observed replay, and its saved-readback difference was exactly zero. The first observed loss is between API input and immediate readback. This does not identify a particular C++ encoder or establish that later exporter rounding is the same loss.

The original public report is pinned by `86126f272e52b60323e9a49443df7d320472c61cfae2eada3f88b90c57dd262b`. Private arrays remain outside this packet. `READONLY_NATIVE_PROFILE.json` records only hashes, counts and booleans after an independent RAM-only read: all 9,661 captured IDs are unique and cover LOD0, both setter word joins remain exact, and both saved exporter normal matrices are positive uniform identity. Native unit-length deviation is at most 2.1082098933e-7. The retained B GLB has two meshes/four primitives, no TANGENT or normal/tangent morph target and no reserved carrier; its hash is `4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d`.

## Smallest next transport

Use a positive one-based **FLOAT / POINT** mesh attribute named `_HAS_NATIVE_NORMAL_ID`, containing the exact native LOD0 vertex ID plus one. The profile is bounded to 200,000 vertices; these integers are exactly representable in F32. Native normals are recovered from the pinned raw VVD bytes in RAM after export, so signed zero and every other finite source word remain available. This is an identity carrier, not a self-contained normal payload.

The pinned exporter must receive `export_attributes=True`. `EXPORTER_AUDIT.md` verifies all 120 approved exporter identities and traces the actual APIs: underscore attributes are uppercased, POINT values are copied to loops using the existing vertex index, the whole dot including custom fields participates in deduplication, and generic attributes do not receive NORMAL rounding or coordinate transport. The dot already contains vertex identity; a carrier constant per existing point should not introduce splits. Actual ordering, indices and all non-NORMAL data must still be measured.

A plain FLOAT_VECTOR normal is insufficient for **word-exact** transport: the pinned exporter canonicalizes -0.0 to +0.0 in every float field before deduplication. INT attributes also become F32, losing arbitrary uint32 precision. If a self-contained word payload is needed, two FLOAT_VECTOR attributes can instead carry unsigned 16-bit high/low halves, each exactly representable as a positive integral F32. The prototype includes that codec and rejects nonintegral, nonfinite, out-of-range or negative-zero halves. Neither option uses nearest-normal selection; all eight ambiguous normal-word classes remain identity-addressed.

## Prototype and preservation contract

`normal_identity_carrier.py` is pure standard-library CPU code and writes no files. It independently reads normal uint32 words from exact SHA/checksum-pinned VVD bytes through the unchanged bounded LOD0 parser. A source map cannot be replaced by inferred word values while retaining the old identity: the raw bytes are rederived and type-exactly compared before correction.

The input carrier GLB SHA, expected global ID set, **supplied per-primitive identity order** and explicit signed-axis rotation are required. Coverage alone is insufficient: a complete permutation of IDs is rejected against the supplied relation. The synthetic manifest is known by construction; **no independently qualified native per-primitive manifest has yet been produced**. That is a required later gate, not something the prototype proves from the carrier itself.

Initial coordinate support is deliberately small: proper signed axis permutations only. The qualified original matrix class suggests the existing x,z,-y export swizzle for this fixture. The future export must verify the actual matrices and apply transport exactly once. The prototype permutes uint32 words and flips sign bits without decimal rounding or invented renormalization; original unit lengths must fit its explicit 2.5e-7 profile. Arbitrary matrices, nonuniform scale, reflection and out-of-profile normals are refused. Source-unit conversion stays separate and unchanged; the six-foot scale-1 contract remains inactive.

The prototype appends corrected F32 NORMAL buffer views/accessors, updates only primitive NORMAL references, strips only its reserved carrier attribute and adds a collision-checked provenance key. **Every prior BIN byte remains unchanged.** Existing accessor/view definitions, indices, UVs, joints/weights, position morphs, materials/images, nodes/skins, animation, owner metadata and source bytes remain type-exactly unchanged. Old normal/carrier bytes may remain as unused immutable storage; there is no destructive repacking. Normal/tangent morph targets are refused. Existing tangents must already be compatible and remain unchanged; this actual B profile has none.

Two independent checks have different jobs:

- `preservation_contract()` checks the allowed non-NORMAL mutation window, including JSON types. It does not itself validate new NORMAL storage.
- `corrected_normal_contract()` separately decodes the output NORMAL accessor and checks format/range/count and exact signed-axis words against the supplied identity relation.

The correction producer invokes both. This proves a synthetic append-only operation, not the correctness of a future Blender attribute export, native correspondence manifest, appearance or live runtime binding.

## Synthetic verification and peer correction

The CPU tests construct only synthetic VVD/GLB bytes, including eight coincident source-normal word classes, signed zero, skin/UV/tangent data, a position morph and unrelated metadata. They check exact recovery, source pin failures, no nearest fallback, complete-set permutation refusal, numeric/buffer/compression/morph/tangent guards, and preservation failures for old BIN/UV/skin/node/morph/metadata changes. Separate negative cases reject invalid new NORMAL storage/words and type-only changes such as `true` to `1` or an integer index to a float.

The original independent peer review is preserved in `PEER_REVIEW.md`. It caught Python equality accepting those type-only changes in the first preservation checker. The checker now uses typed recursive equality and has the explicit regression cases. The peer also separated global coverage from correspondence and non-NORMAL preservation from new NORMAL validity; both boundaries are explicit in the strengthened prototype. Earlier 13-test/16-test results are source observations only; final current-source CPU evidence belongs in `CPU_VALIDATION.json`.

## Next actual probe and qualification

See `FUTURE_PROBE_RECIPE.md`. A fresh isolated carrier export must preserve the original B material/scene setup, produce and verify an independent native identity relation, and compare every non-NORMAL channel with the retained original export before this correction is used. The existing material-free setter replay cannot serve as an appearance-preserving export source.

A new GLB hash requires new native bone/source binding qualification, explicit pose/key migration evidence if adopting it into an existing model, the five qualified native-joint workflow checks and appropriate HAS/cold-open/render/export preservation. No existing project source or profile should be silently replaced. Original failed reports, B assets and source/runtime identities remain intact. No PMX reconstruction, physics inference, six-foot normalization or runtime solver behavior is added here.
