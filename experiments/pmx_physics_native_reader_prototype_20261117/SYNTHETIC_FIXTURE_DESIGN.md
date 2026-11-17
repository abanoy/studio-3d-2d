# Independent full-prefix fixture builder

Only `synthetic_pmx.py` and this note are owned by the fixture author. The
parent owns the reader and its tests. No parser is imported or called by this
builder, and no native asset, installed reader, engine, CIM, Git or review file
is read or changed.

The layout comes from pinned installed source `fb9aafe369025f221bc5a1c952d868260b1a4bb950dc33bca62645b4da454e5a`
and the independent sealed design at `pmx20_binary_layout_review_20261117`
(INDEX `d36d64477be854e9ae1808f2d67a55ac2e26fd8ad4c7395e5050aa1fca196b4b`).
The independent 339-byte fixed-offset oracle remains a separate test source.

`build_fixture(...)` constructs one synthetic PMX2.0 byte string and expectations:
three weighted vertices by default and one triangle; one named texture (never opened); two
materials exercising both shared and unshared toon branches; two duplicate-name
bones; requested morph types0..8; a display frame with bone/morph selectors; one
rigid body and one joint. Source geometry/skin/IK semantics and dependency
completeness are intentionally unqualified. In particular, all-zero bone-morph
quaternions remain authored zero words; a parser must not copy the upstream
repair to identity.

All six index widths follow `index_size`. Encoding0/1 chooses UTF16LE/UTF8.
Every BDEF/SDEF branch and additional-UV payload has a separate size equation.
`vertex_count` permits 3..256 at width1 and 3..1024 at wider widths, with the
triangle ending at `vertex_count-1`. Width1/count130 therefore authors the
unsigned face index129 while bone words remain signed. Extra vertex positions
repeat the same three authored positions and do not imply mesh validity.
`bone_flags` and `tail_bone` control bone0; the tail selector is authoritative for
bit0, while bone1 remains a simple offset-tail child. Both grant flags consume a
single grant payload. The IK branch contains one limited and one unlimited link.
Unknown flag bits can be authored to test the reader's explicit refusal policy.

The return's `fields`, record boundaries and section starts are captured while
writing, then checked against independent record-size equations. They do not
come from parser output. Names include Japanese text and retain exact encoded
bytes. Every field offers an offset/length/raw hex, so tests can mutate selectors,
counts, widths, references or truncate at exact boundaries without needing a
second parser. Morph offset equations include material `M+113`, not `M+112`.
Mutation labels include `vertex.0.deform`, `vertex.0.bone0`, `material.0.flags`,
`material.0.shared_toon`, `bone.0.flags`, `bone.0.IK.link0.limited` when enabled,
`morph.0.type`, `morph.0.offset_count`, its type-specific reference label,
`display.special`, `display.bone.tag`, `display.bone.index`, and every section's
`*.count`. The complete exact label list is returned in `fields`.

Physics payloads are literal four-byte words, not floats passed through a JSON
or native decode/re-encode. The body includes negative zero, the smallest positive
subnormal and a quiet NaN payload; the joint includes negative zero, a subnormal
and positive infinity. Expected word-index classifications are explicit.
These words are byte-preservation challenges, not valid simulation parameters.
No float validity or physical plausibility is claimed.

The builder permits physics reference values that fit their signed word, and
signed-byte unknown joint modes, so tests can exercise -2, positive out-of-range
and unknown-enum refusal. It does not call those choices valid. Unsupported
deform/morph layouts are produced by mutating the recorded tag offsets rather
than inventing a payload width. Inputs reject bool/int aliases and excessive
fixture morph lists. No product format, solver, scale or normal conversion exists.
