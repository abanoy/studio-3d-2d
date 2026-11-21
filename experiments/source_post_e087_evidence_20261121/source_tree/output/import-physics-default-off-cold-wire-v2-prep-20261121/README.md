# Stronger cold-wire engine precision control

Test-only successor to the frozen21657/edb9 wire smoke. All production behavior, cold comparison,42 static/54 runtime assertions and20 precondition counts remain unchanged. Exactly three control-fixture literals change: nonintegral baseline position1e-5; add7.5e-13; require that this remains accepted by the established1e-12 scalar oracle but is rejected by exact engine pose reconstruction and the combined saved-fields oracle. This demonstrates that the engine guard itself prevents the change. The original zero→1e-13 case was already refused by exact-zero handling and did not isolate that guard.

Reversing those three control literals yields byte-identical edb9 source. No parser/test/native/GPU execution was performed by the author; no application source was changed. Prior failures, diagnostic and wire source remain untouched. Root must execute this successor before claiming its controls pass.
