# Independent peer review

**Result: GO for the bounded source/CPU candidate only.** No outstanding
source-fact extraction defect was found within its documented closed profile.
This is not native execution, full asset validity, actual B compatibility,
exporter correspondence, normal fidelity, repair or adoption qualification.

Reviewed final source identities:

- `native_point_expectation.py`: `2631269a552a5dcbeb7091f8b1c903ff4f35cbd1713beba7b622a62b3aa1a283`
- `test_native_point_expectation.py`: `02ffba742e179f2840d8487fea1f7939b4d0c7178d031bb4b65a17b19a6c5a38`

The independent review compared consumed MDL49/VVD4/VTX7 offsets and ordering
against the local pinned SourceIO source. Model/mesh starts, VVD fixup order,
strip-group point concatenation, sum-of-strip-vertex offsets and reversal of
the complete flat corner stream agree with those source rules. The scale and
UV rules preserve binary32 arithmetic; raw normal words retain signed zero.
The independent rational rounding oracle and fixed word expectations provide
evidence beyond the snapshot join's use of the producer's arithmetic helper.
Observed setter identities enter only the final exact order comparison.

Review caught source-loader refusal cases initially omitted by the candidate:
the strip bone-state-change offset is checked even for zero changes; an empty
material-replacement list still performs a seek; and empty mesh/strip-group
records can still seek to their declared offsets. These guards and explicit
regressions are now present. The profile was also narrowed to one traversed
VTX LOD and no material replacements, avoiding unexamined active LOD branches.
Sorted neighbor interval checks and the 16,384-table limit bound structural
overlap checks. No threshold or identity-matching relaxation was introduced.

An independent invocation of the current CPU suite ran **14 tests, zero
failures and zero errors** in 0.039 seconds:

`python -B -X utf8 -m unittest discover -s experiments/native_point_expectation_20261118 -p test_native_point_expectation.py -v`

The suite includes all 8,000 three-slot write histories, exact source-ID and
raw-row mapping, permutation refusal, F32/signed-zero cases, unsupported
profiles, native-family pin failures, malformed offsets, table bounds and the
existing exact private point join. These are synthetic source-reader tests;
the fixture is not evidence that a complete native asset can be imported.

The external host must supply expected file identities from its separately
admitted immutable lock. Matching a caller-supplied digest alone does not
establish that authority. Unconsumed MDL subsystems remain outside this point
reader's validity claim. The full expectation intentionally refuses more than
one distinct positive group per vertex: SourceIO proves write order and
REPLACE values, while exact multi-group Blender storage order is unproved.
Positive-zero identity matrices are source expectations subject to the later
word-exact saved/current join. Native update/validate behavior, original B's
profile and all later carrier/export/domain gates remain unobserved.

This review read source and synthetic fixture data only. It did not read
original native assets, owner artwork or private arrays; run native apps or
SourceIO import; query processes; use Git/network; or modify producer/tests,
old packets, application source or documentation. The original `2e-5` failure
remains failed and the unchanged `2.5e-7` native-unit profile remains enforced.
