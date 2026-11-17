# PMX decoded-capture peer review

Source/CPU review GO for sealed packet `544208654bebc2b74909afae6391dadc32d27f3374291406b7923c12abfe2f56`, capture source `6a0af8e9209ce0e782f140da37405fda9d3bd82d02b241c432dbac32c83ad78e`. No preservation, typed-loss-disclosure or stated-budget blocker was found within its deliberately limited decoded-object scope. The original packet is unchanged.

The closed 11-payload set, all byte lengths/digests and six upstream/main source bindings were checked independently. The original 22 synthetic tests passed. Six additional peer tests passed: exact capsule-budget boundary; boolean rejection for every limit; negative zero through all supported float/vector fields and JSON; empty tables with header-only bytes; changed supplied source payloads; and unsupported values described without being copied.

Named body/joint fields match the pinned constructor contract and are copied without unit, basis, scale, name or solver conversion. Integer/reference/mask checks preserve types; finite exact binary32 values and signed zero survive transport. Bounds are enforced before a capsule is returned, and an over-budget result is refused rather than truncated. Unknown body/joint/model attributes and unsupported modes make decoded coverage incomplete. Bone preservation is intentionally only an index/name catalogue; other bone features and known non-physics model tables are outside that coverage flag.

Read-only inspection of the exact installed reader source confirms the disclosed losses: all negative rigid bone words collapse to None; truncated joint fields can receive fallback vectors; top-level loading can swallow struct.error; names use replacement decoding. The reader was not imported or executed. The fingerprint checks only the fixed header, not native table integrity or whether the supplied decoded model came from those bytes.

Every returned capture remains `native_file_join: UNQUALIFIED`, `native_file_preservation_complete: false`, `applied: false` and `runtime_support: NONE`, including apparently complete, empty and unknown-coverage cases. PMX 2.1 retains unsupported soft-body coverage with unknown count. `decoded_supported_fields_complete` does not establish native-file preservation, physical validity, HAS bone binding, portable retention or live simulation.

No native asset read, engine/CIM/Git operation, installed-reader execution, main/review source edit or general PMX decoder was part of this audit. The original packet's separate native-reader/join and later integration qualification requirements remain necessary.
