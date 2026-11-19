# Independent review of the finite weight-storage probe

**Result: GO for the source/CPU preparation packet only.** No outstanding
defect was found in the reviewed finite probe and its stated boundaries.
Blender execution, native storage behavior, a universal storage rule, actual
source-row correspondence, fidelity, export repair and adoption remain
unqualified. This review does not authorize or perform the future native run.

Reviewed final identities:

- `weight_storage_contract.py`: `f71753e3b7183c5fab343bf8af504cd5613879bd95b89d5f338f54123180db18`
- `blender_weight_storage_probe.py`: `d7f75e11bd8a90d0f652f67ae92843629e5126b965c5e7c4262ab97d901bac95`
- `test_weight_storage_probe.py`: `c52d6391648fdb7689e6d227298456e827da5320b2d5600d9802eff41a2476e5`

The reviewer independently enumerated the proposed alphabets: four group IDs
and seven exact weight words across three slots give 21,952 cases and 47,040
positive writes. The expected distinct-group histogram for zero/one/two/three
stored groups is 512/6,740/11,700/3,000. Both zero signs, repeated groups,
minimum positive subnormal, decimal F32 values and high group index 68 are
covered. The event oracle independently describes earliest positive group
appearance and latest positive replacement; it remains a hypothesis to test.

The pinned local SourceIO importer establishes the API call order: groups in
native order, then vertex order, then all three slots, positive-only
`add([vertex], weight, 'REPLACE')`, followed by no-argument mesh validation.
The synthetic probe preserves this structure. It creates only its own mesh
and object, never links them into a scene, captures actual ordered group
iteration before and after the same validate call, and removes the exact
owned IDs in `finally`. It does not sort observations, discard zero
readbacks, normalize weights or substitute expected values.

Review caught two initial weaknesses, both corrected in the final source.
Request/script size checks originally followed unbounded reads; final reads
enforce pre-open size limits, single-link regular files, reparse/symlink
refusal, bounded reads and stable stat/fstat identities. F32 readback initially
rounded arbitrary Python floats; final readback requires a finite exact
binary32 round trip and preserves signed zero. The imported contract path
and exact two-file source directory are checked explicitly.

Expected and observed ordered-row hashes are computed separately. Every
finite case is compared in each phase, with total mismatch categories and at
most 12 synthetic examples per phase. Validation-time changes are separate
from immediate storage behavior. Write/validate failures retain failed status
and attempt cleanup; cleanup failure overrides a matching result. The public
matching-result parser checks a closed field set, exact types, complete
recomputed finite hashes/counts/histograms, request/run/source identities,
runtime descriptors and all false qualification flags. A status marker or
that parser's return cannot establish that native execution occurred.

An independent final CPU invocation ran **11 tests with zero failures and
zero errors** in 4.000 seconds:

`python -B -X utf8 -m unittest discover -s experiments/blender_weight_storage_probe_20261118 -p test_weight_storage_probe.py -v`

Explicit CPU fakes demonstrate detection of sorted groups, first-write
retention, subnormal flushing, validation-time reordering, operation failure
and cleanup failure. Tests also cover finite counts, the existing generalized
source ledger, missing/extra/reordered observations, invalid F32 values,
fresh owned requests, source pin/path guards, typed public-result mutations
and wrapper receipt fields. Fakes provide no evidence of real Blender storage.

The existing private-desktop wrapper source was inspected without execution.
Its child-desktop confirmation can come from thread lookup or an owned
window enumerated on the private desktop. With no private window observed,
confirmation must have come from thread lookup; with a window observed, its
receipt does not distinguish the two routes. The checker correctly accepts
the background no-window case while requiring explicit desktop confirmation,
clean closure and no foreground child or desktop switch. It supplies no
headless bypass or fabricated sentinel.

Root must externally verify copied scripts before importing them, verify the
approved runtime identity before and after, and bind a fresh request, child
command, actual execution, matching public result and wrapper receipt with
authoritative closure. The probe records but does not hash its running binary.
No such host, issued request or native launch was created by this packet or
review. The README states these duties and keeps the later launch recipe
explicitly unrun.

The finite cases do not exhaust all 69 group IDs or all positive F32 words.
Loose points do not prove triangle, save/reopen or owner-model behavior. Any
future actual source-row policy needs a separately justified input/domain
connection. The existing multi-group source expectation refusal is not
bypassed, and original failures and thresholds remain unchanged.

This reviewer read local source and synthetic CPU data only. No original
native/private array, artwork or owner scene was read; no Blender, SourceIO
import, exporter, window/desktop API, process query, Git action, installation
or upload was performed. Only this new peer note was written; producer/tests,
old packets, application source and documentation were not modified.
