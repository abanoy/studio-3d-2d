# Qualification boundary addendum

This addendum narrows the interpretation of the unchanged sealed semantic comparator packet `edab37a065d3c29a316b7a1c1cab3a4263f5d4e716f97fa4192f541b391ea4fd`, source `c7e1e9d323bb7f35fffa38731a67b0099f173167bcb65d857a7cd6165698ff00`. It is a qualification note and synthetic regression record, not a validator feature or a change to that packet.

The comparator proves preservation of recognized, decoded non-NORMAL components, their order and typed metadata across bounded storage rearrangement. Its reference checks cover recognized table-reference types/ranges, accessor/view decoding bounds, and selected channel profiles. The earlier README phrase “Existing references are validated” must be read only in this narrower sense. It does not establish complete glTF validity or ownership-specific semantic domains.

Independent peer review reran all 26 original synthetic tests successfully and found no non-NORMAL mutation acceptance within the declared storage/gap rules. The peer also identified unchanged malformed inputs that the comparator admits:

| Witness preserved on both sides | Missing validity check |
| --- | --- |
| JOINTS_0 value 255 with a one-joint skin | Joint component values are not joined to each owning node's skin domain. |
| Repeated entries in skin.joints with matching inverse-bind count | Joint uniqueness is not checked. |
| Rotation animation targeting a VEC3 output | Output shape is not checked against each animation target path. |
| A cycle in node children | Scene-graph acyclicity is not checked. |

The addendum's synthetic tests retain these acceptances as explicit boundary witnesses; they do not classify them as valid assets. Separate negative checks still require changed non-NORMAL data to fail. No native asset was read and no GLB file was generated.

Before native use, require an independently qualified input domain for both original B and the carrier export, covering these ownership/graph/animation rules and other applicable glTF constraints. Bind that qualification to the exact input identities. Then require the independent per-primitive native-ID relation and the separate exact-NORMAL gate. A preserved invalid input, an unordered carrier-ID set or this comparator's `passed` field cannot replace any of those requirements. HAS adoption, source/bone/unit/rest/skin preservation and the inactive six-foot policy remain separate.
