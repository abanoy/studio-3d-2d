# Independent CPU/source review

Reviewed the unsealed prototype without changing its implementation or tests. No engine, Win32, CIM, Git, installed exporter or native-array input was used. The 13 existing synthetic tests passed under Python 3.13 with `-B`.

Reviewed source identities:

- `normal_identity_carrier.py`: `6ae4353a928b05e5d9d4af1c7c429ddd9e1b0a2c7fcc588d49122f24cc3149ed`
- `test_normal_identity_carrier.py`: `a97c3ae3c58d1c9d4508a37b9d54a641d1bc584e46955cc76a9a145b39158e9d`

## Finding: make the independent preservation comparison type aware

`preservation_contract` at lines 155-172 uses ordinary Python container equality. That treats JSON booleans as equal to corresponding numeric values, and integer accessor/index fields as equal to floating values. Two additional synthetic probes each returned `True` from `preservation_contract` after changing the corrected fixture:

1. `extras.owner_metadata.retained`: `true` to `1`.
2. `meshes[0].primitives[0].indices`: the original integer accessor index to a JSON float with the same value.

The second mutation violates the glTF integer field type. The first changes unrelated owner metadata. Both should be refused by the claimed independent non-NORMAL preservation guard. The existing `correct_glb` construction does not itself make either change: it deep-copies the input, so this is a missing negative guard, not evidence that the current producer corrupted those fields.

Use a recursive comparison that preserves JSON value kinds, then use it for existing accessor/view prefixes and the remaining document. Add synthetic negative tests for boolean/number substitution and integer-only field conversion. Do not introduce a float tolerance or serialize both sides through a format that hides the mismatch.

## Other reviewed boundaries

The native map is re-derived from the pinned VVD bytes before correction; an independently supplied altered word table is refused. The correction appends aligned normal storage and preserves the complete existing BIN prefix and accessor/view definitions. The accessor reader bounds count, stride, local and global offsets, embedded buffer identity, nonsparse F32 storage and alignment. NORMAL/TANGENT morph channels are refused, while retained tangents must be finite, unit length, have signed unit handedness and remain approximately orthogonal to the replacement normal. No additional concrete memory-range or mutation-window defect was found in those paths.

A complete permutation of carrier IDs still satisfies the current set-coverage predicate and produces `source_word_transport_exact: true`. This is expected for a transport prototype: that field proves exact lookup/word transport for the supplied IDs, not that an exporter attached each ID to the correct source vertex. The status remains `CANDIDATE_DERIVATIVE_UNQUALIFIED`, and the exporter audit already requires independent carrier-to-native correspondence and coordinate validation before promotion. Retain that separation. A later native harness must reject an incorrect per-vertex relation even when every expected ID is present, and must independently verify every mesh/primitive and the actual transform.

The preservation helper also deliberately excludes appended accessor/view definitions from its document comparison. A second source reviewer reproduced acceptance of an out-of-range replacement NORMAL index or invalid appended NORMAL view. This does not reproduce an invalid output from `correct_glb`, which constructs the appended view/count/storage itself. It means the helper should remain a non-NORMAL preservation check rather than serve as the output-normal acceptance test. Independently decode each actual output NORMAL accessor, validate its range/type/count and finite unit words, and compare its words with the intended native transport in the later acceptance harness.

This review does not qualify native fidelity, exporter behavior, runtime rendering, skinning or physics. It leaves the earlier FAILED_UNQUALIFIED native-normal result unchanged.
