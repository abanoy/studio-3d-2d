# Scratch v5 actual unit failure, zero batch credit

Root attempted the frozen9557 helper/5140 host. One of12 pure tests failed:
test_measured_row_uses_original_close. Eleven individual OK lines are preserved,
but the batch receives0 pass credit; no Blender/scratch job started and no native
model/export/repair/Full qualification is inferred. One Root Job closed active0,
both retained handles closed,1144 admitted inputs/Main/environment stayed exact
and lock was removed, as copied actual receipts show.

Source-level cause: measured_row deliberately converts rest to a tuple. The fake
close callback a==b compared it to a list reference and rejected equal numbers.
This concerns the synthetic callback, not the immutable production close predicate.
A separately versioned fixture changes positive/negative callbacks to compare
sequence contents; the original failed fixture/results remain unchanged.

Collector independently checked raw12-test/one-failure output, closure and all3
runtime source hashes. Only safe text was copied. No private capture/sidecar,
matrix,name/native-word arrays,SDK/assets/model or complete runtime was read/copied.
Collector executed no tests/Blender/GPU/Main/Full programs.
